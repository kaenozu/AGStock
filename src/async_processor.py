"""
Async Data & Analysis Processor
データ取得と分析を高度に並列化するプロセッサ
"""

import asyncio
import logging
from typing import Dict, List, Any, Callable
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class AsyncProcessor:
    """非同期並列処理管理クラス"""

    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.loop = asyncio.get_event_loop()

    async def run_parallel_tasks(self, tasks: List[Callable], *args) -> List[Any]:
        """複数のタスクを並列に実行し、結果を待つ"""
        loop = asyncio.get_running_loop()
        futures = [
            loop.run_in_executor(self.executor, task, *args)
            for task in tasks
        ]
        return await asyncio.gather(*futures)

    def run_sync(self, coro):
        """非同期関数を同期的に実行（既存コードからの移行用）"""
        return self.loop.run_until_complete(coro)

    async def fetch_and_analyze_parallel(
        self, 
        tickers: List[str], 
        fetch_func: Callable, 
        analyze_func: Callable
    ) -> Dict[str, Any]:
        """
        全銘柄のデータ取得と分析を完全に並列化する
        """
        async def process_single(ticker):
            try:
                # 1. データ取得 (Thread pool)
                df = await self.loop.run_in_executor(self.executor, fetch_func, [ticker])
                ticker_df = df.get(ticker)
                if ticker_df is None or ticker_df.empty:
                    return ticker, None
                
                # 2. 分析実行 (Thread pool)
                analysis = await self.loop.run_in_executor(self.executor, analyze_func, ticker_df)
                return ticker, {"data": ticker_df, "analysis": analysis}
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
                return ticker, None

        tasks = [process_single(t) for t in tickers]
        results = await asyncio.gather(*tasks)
        return {t: res for t, res in results if res is not None}

# シングルトンインスタンス
processor = AsyncProcessor()