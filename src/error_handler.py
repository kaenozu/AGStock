"""
エラーハンドリング強化ユーティリティ

API制限、ネットワークエラー、データエラーに対する堅牢な処理
"""
import time
import functools
import logging
from typing import Callable, Any
import requests


# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def retry_on_error(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    エラー時リトライデコレーター
    
    Args:
        max_retries: 最大リトライ回数
        delay: 初回待機時間（秒）
        backoff: 待機時間の倍率
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                
                except requests.exceptions.RequestException as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}"
                        )
                        logger.info(f"Retrying in {current_delay:.1f} seconds...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries + 1} attempts")
                
                except Exception as e:
                    logger.error(f"{func.__name__} encountered unexpected error: {e}")
                    raise
            
            # 最後の例外を再送出
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def safe_execute(func: Callable, default: Any = None, log_errors: bool = True) -> Any:
    """
    安全実行ラッパー
    
    エラーが発生してもデフォルト値を返す
    
    Args:
        func: 実行する関数
        default: エラー時のデフォルト値
        log_errors: エラーをログに記録するか
    
    Returns:
        関数の戻り値またはデフォルト値
    """
    try:
        return func()
    except Exception as e:
        if log_errors:
            logger.error(f"Error in {func.__name__}: {e}")
        return default


class CircuitBreaker:
    """サーキットブレーカーパターン実装"""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        """
        Args:
            failure_threshold: 連続失敗回数の閾値
            timeout: オープン状態の持続時間（秒）
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        関数を実行（サーキットブレーカー経由）
        
        Args:
            func: 実行する関数
            *args, **kwargs: 関数の引数
        
        Returns:
            関数の戻り値
        
        Raises:
            Exception: サーキットがOPEN状態の場合
        """
        if self.state == "OPEN":
            if time.time() - self.last_failure_time >= self.timeout:
                logger.info("Circuit breaker: OPEN -> HALF_OPEN")
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            
            if self.state == "HALF_OPEN":
                logger.info("Circuit breaker: HALF_OPEN -> CLOSED")
                self.state = "CLOSED"
                self.failure_count = 0
            
            return result
        
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                logger.error(f"Circuit breaker: CLOSED -> OPEN (failures: {self.failure_count})")
                self.state = "OPEN"
            
            raise e
    
    def reset(self):
        """サーキットブレーカーをリセット"""
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker reset")


class RateLimiter:
    """レート制限"""
    
    def __init__(self, calls_per_minute: int = 60):
        """
        Args:
            calls_per_minute: 1分あたりの最大呼び出し回数
        """
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    def wait_if_needed(self):
        """必要に応じて待機"""
        now = time.time()
        
        # 1分以上前の記録を削除
        self.calls = [t for t in self.calls if now - t < 60]
        
        if len(self.calls) >= self.calls_per_minute:
            sleep_time = 60 - (now - self.calls[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Waiting {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
        
        self.calls.append(now)


# グローバルインスタンス
api_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60.0)
api_rate_limiter = RateLimiter(calls_per_minute=60)


def main():
    """テスト"""
    
    # リトライテスト
    @retry_on_error(max_retries=3, delay=0.5)
    def failing_function():
        print("Attempting...")
        raise requests.exceptions.ConnectionError("Test error")
    
    try:
        failing_function()
    except:
        print("✅ Retry test completed")
    
    # サーキットブレーカーテスト
    cb = CircuitBreaker(failure_threshold=2, timeout=2.0)
    
    def sometimes_fails():
        import random
        if random.random() < 0.7:
            raise Exception("Random failure")
        return "Success"
    
    for i in range(5):
        try:
            result = cb.call(sometimes_fails)
            print(f"Attempt {i+1}: {result}")
        except Exception as e:
            print(f"Attempt {i+1}: Failed - {e}")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
