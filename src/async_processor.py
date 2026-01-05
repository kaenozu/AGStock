"""
非同期データ処理とパフォーマンス最適化モジュール
API呼び出しの最適化とキャッシュ戦略を実装
"""

import asyncio
import aiohttp
import logging
import time
import threading
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import hashlib
from functools import wraps, lru_cache
import weakref
from collections import defaultdict
import queue

from .error_handling import handle_exceptions, memory_monitor, PerformanceError, ErrorCategory
from .secure_config import get_secure_config
from .input_validator import rate_limit

logger = logging.getLogger(__name__)


@dataclass
class APIRequest:
    """APIリクエスト情報"""

    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    timeout: float = 30.0
    retry_count: int = 3
    cache_ttl: int = 300  # 5分
    priority: int = 1  # 1=低, 2=中, 3=高


@dataclass
class APIResponse:
    """APIレスポンス情報"""

    status_code: int
    data: Any
    headers: Dict[str, str]
    response_time: float
    cached: bool = False
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class CacheManager:
    """キャッシュマネージャー"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._access_times: Dict[str, datetime] = {}
        self._lock = threading.RLock()

        # 統計情報
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str) -> Optional[Any]:
        """キャッシュから取得"""
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None

            data, expiry = self._cache[key]

            # 有効期限チェック
            if datetime.now() > expiry:
                del self._cache[key]
                if key in self._access_times:
                    del self._access_times[key]
                self.misses += 1
                return None

            # アクセス時間を更新
            self._access_times[key] = datetime.now()
            self.hits += 1
            return data

    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """キャッシュに設定"""
        with self._lock:
            # キャッシュサイズチェック
            if len(self._cache) >= self.max_size:
                self._evict_lru()

            expiry = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
            self._cache[key] = (data, expiry)
            self._access_times[key] = datetime.now()

    def _evict_lru(self) -> None:
        """LRUでキャッシュを削除"""
        if not self._access_times:
            return

        # 最も古いアクセス時間のキーを探す
        oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])

        if oldest_key in self._cache:
            del self._cache[oldest_key]
        del self._access_times[oldest_key]
        self.evictions += 1

    def clear(self) -> None:
        """キャッシュをクリア"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()

    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得"""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "evictions": self.evictions,
            }

    def _generate_key(self, request: APIRequest) -> str:
        """リクエストからキャッシュキーを生成"""
        key_data = {
            "url": request.url,
            "method": request.method,
            "params": request.params,
            "data": request.data,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()


class RateLimiter:
    """APIレートリミッター"""

    def __init__(self, max_requests_per_second: int = 10, max_requests_per_minute: int = 100):
        self.max_rps = max_requests_per_second
        self.max_rpm = max_requests_per_minute

        self._requests_per_second = queue.Queue(maxsize=max_requests_per_second)
        self._requests_per_minute = queue.Queue(maxsize=max_requests_per_minute)

        self._second_thread = threading.Thread(target=self._reset_second_counter, daemon=True)
        self._minute_thread = threading.Thread(target=self._reset_minute_counter, daemon=True)

        self._second_thread.start()
        self._minute_thread.start()

    def _reset_second_counter(self) -> None:
        """秒カウンターをリセット"""
        while True:
            time.sleep(1)
            while not self._requests_per_second.empty():
                self._requests_per_second.get()

    def _reset_minute_counter(self) -> None:
        """分カウンターをリセット"""
        while True:
            time.sleep(60)
            while not self._requests_per_minute.empty():
                self._requests_per_minute.get()

    async def acquire(self) -> None:
        """リクエスト許可を取得"""
        # 秒制限チェック
        if self._requests_per_second.full():
            await asyncio.sleep(0.1)
            return await self.acquire()

        # 分制限チェック
        if self._requests_per_minute.full():
            sleep_time = 60 - (time.time() % 60)
            await asyncio.sleep(sleep_time)
            return await self.acquire()

        # 許可を取得
        self._requests_per_second.put(1)
        self._requests_per_minute.put(1)


class AsyncAPIClient:
    """非同期APIクライアント"""

    def __init__(self, max_concurrent_requests: int = 10):
        self.max_concurrent_requests = max_concurrent_requests
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.cache_manager = CacheManager()
        self.rate_limiter = RateLimiter()

        # セッション管理
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()

        # 統計情報
        self.request_count = 0
        self.total_response_time = 0.0
        self.error_count = 0

    async def _get_session(self) -> aiohttp.ClientSession:
        """HTTPセッションを取得"""
        if self._session is None or self._session.closed:
            async with self._session_lock:
                if self._session is None or self._session.closed:
                    timeout = aiohttp.ClientTimeout(total=30)
                    self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """セッションをクローズ"""
        if self._session and not self._session.closed:
            await self._session.close()

    @handle_exceptions(category=ErrorCategory.API)
    async def request(self, request: APIRequest) -> APIResponse:
        """APIリクエストを実行"""
        async with self.semaphore:
            return await self._execute_request(request)

    async def _execute_request(self, request: APIRequest) -> APIResponse:
        """リクエストを実行"""
        start_time = time.time()

        # キャッシュチェック
        cache_key = self.cache_manager._generate_key(request)
        cached_response = self.cache_manager.get(cache_key)

        if cached_response:
            logger.debug(f"キャッシュヒット: {request.url}")
            return APIResponse(
                status_code=200,
                data=cached_response,
                headers={},
                response_time=time.time() - start_time,
                cached=True,
            )

        # レート制限
        await self.rate_limiter.acquire()

        # リクエスト実行
        session = await self._get_session()

        for attempt in range(request.retry_count + 1):
            try:
                async with session.request(
                    method=request.method,
                    url=request.url,
                    headers=request.headers,
                    params=request.params,
                    json=request.data,
                    timeout=aiohttp.ClientTimeout(total=request.timeout),
                ) as response:
                    data = await self._parse_response(response)
                    response_time = time.time() - start_time

                    # 成功時の処理
                    if response.status == 200:
                        # キャッシュに保存
                        self.cache_manager.set(cache_key, data, request.cache_ttl)

                        # 統計更新
                        self.request_count += 1
                        self.total_response_time += response_time

                        return APIResponse(
                            status_code=response.status,
                            data=data,
                            headers=dict(response.headers),
                            response_time=response_time,
                            cached=False,
                        )
                    else:
                        raise PerformanceError(
                            f"APIエラー: {response.status}",
                            metric="status_code",
                            threshold=response.status,
                        )

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == request.retry_count:
                    self.error_count += 1
                    raise PerformanceError(f"APIリクエスト失敗: {e}", metric="api_error")

                # リトライ待機
                await asyncio.sleep(2**attempt)
                logger.warning(f"APIリクエストリトライ ({attempt + 1}/{request.retry_count}): {e}")

    async def _parse_response(self, response: aiohttp.ClientResponse) -> Any:
        """レスポンスをパース"""
        content_type = response.headers.get("content-type", "").lower()

        if "application/json" in content_type:
            return await response.json()
        elif "text/" in content_type:
            return await response.text()
        else:
            return await response.read()

    async def batch_requests(self, requests: List[APIRequest]) -> List[APIResponse]:
        """バッチリクエストを実行"""
        tasks = [self.request(req) for req in requests]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        avg_response_time = self.total_response_time / self.request_count if self.request_count > 0 else 0

        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.request_count if self.request_count > 0 else 0,
            "avg_response_time": avg_response_time,
            "cache_stats": self.cache_manager.get_stats(),
        }


class DataProcessor:
    """非同期データプロセッサー"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.api_client = AsyncAPIClient()

        # 処理キュー
        self._task_queue = asyncio.Queue()
        self._processing = False
        self._worker_tasks: List[asyncio.Task] = []

    async def start_processing(self) -> None:
        """データ処理を開始"""
        if self._processing:
            return

        self._processing = True

        # ワーカータスクを開始
        for i in range(self.max_workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self._worker_tasks.append(task)

        logger.info(f"データ処理を開始: {self.max_workers}ワーカー")

    async def stop_processing(self) -> None:
        """データ処理を停止"""
        self._processing = False

        # ワーカータスクを停止
        for task in self._worker_tasks:
            task.cancel()

        await asyncio.gather(*self._worker_tasks, return_exceptions=True)

        # APIクライアントをクローズ
        await self.api_client.close()

        # スレッドプールをシャットダウン
        self.executor.shutdown(wait=True)

        logger.info("データ処理を停止")

    async def submit_task(self, task_func: Callable, *args, **kwargs) -> Any:
        """タスクを submit"""
        task_item = {
            "func": task_func,
            "args": args,
            "kwargs": kwargs,
            "future": asyncio.Future(),
        }

        await self._task_queue.put(task_item)
        return await task_item["future"]

    async def _worker(self, worker_id: str) -> None:
        """ワーカー処理"""
        logger.info(f"ワーカー開始: {worker_id}")

        while self._processing:
            try:
                # タスクを取得
                task_item = await asyncio.wait_for(self._task_queue.get(), timeout=1.0)

                # タスクを実行
                try:
                    result = await self._execute_task(task_item)
                    task_item["future"].set_result(result)
                except Exception as e:
                    task_item["future"].set_exception(e)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"ワーカーエラー ({worker_id}): {e}")

        logger.info(f"ワーカー停止: {worker_id}")

    async def _execute_task(self, task_item: Dict) -> Any:
        """タスクを実行"""
        func = task_item["func"]
        args = task_item["args"]
        kwargs = task_item["kwargs"]

        # 同期関数の場合はスレッドプールで実行
        if not asyncio.iscoroutinefunction(func):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.executor, func, *args, **kwargs)
        else:
            # 非同期関数の場合は直接実行
            return await func(*args, **kwargs)

    @memory_monitor(threshold_mb=512)
    async def process_market_data(self, symbols: List[str]) -> Dict[str, Any]:
        """市場データを処理"""
        # APIリクエストを作成
        requests = []
        for symbol in symbols:
            request = APIRequest(
                url=f"https://api.example.com/market/{symbol}",
                cache_ttl=60,  # 1分キャッシュ
                priority=2,
            )
            requests.append(request)

        # バッチリクエスト実行
        responses = await self.api_client.batch_requests(requests)

        # 結果を集計
        results = {}
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"データ取得エラー ({symbols[i]}): {response}")
                continue

            if isinstance(response, APIResponse) and response.status_code == 200:
                results[symbols[i]] = response.data

        return results


# グローバルインスタンス
data_processor = DataProcessor()
api_client = AsyncAPIClient()


def get_data_processor() -> DataProcessor:
    """データプロセッサーを取得"""
    return data_processor


def get_api_client() -> AsyncAPIClient:
    """APIクライアントを取得"""
    return api_client


def async_cache(ttl: int = 300):
    """非同期キャッシュデコレーター"""

    def decorator(func):
        cache = {}

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # キャッシュキー生成
            key = str(args) + str(sorted(kwargs.items()))
            key_hash = hashlib.md5(key.encode()).hexdigest()

            # キャッシュチェック
            if key_hash in cache:
                data, timestamp = cache[key_hash]
                if time.time() - timestamp < ttl:
                    return data

            # 実行とキャッシュ
            result = await func(*args, **kwargs)
            cache[key_hash] = (result, time.time())

            return result

        return wrapper

    return decorator


def batch_process(batch_size: int = 10):
    """バッチ処理デコレーター"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 最初の引数がリストの場合
            if args and isinstance(args[0], list):
                items = args[0]
                results = []

                # バッチ処理
                for i in range(0, len(items), batch_size):
                    batch = items[i : i + batch_size]
                    batch_result = await func(batch, *args[1:], **kwargs)
                    results.extend(batch_result if isinstance(batch_result, list) else [batch_result])

                return results
            else:
                return await func(*args, **kwargs)

        return wrapper

    return decorator


# 初期化
async def initialize_async_processing():
    """非同期処理を初期化"""
    await data_processor.start_processing()
    logger.info("非同期処理システムを初期化しました")
