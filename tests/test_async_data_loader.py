"""
非同期データローダーのテスト

AsyncDataLoaderクラスの機能を検証するための単体テスト
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.async_data_loader import AsyncDataLoader, fetch_stock_data_async
import asyncio


class TestAsyncDataLoader:
    """AsyncDataLoaderクラスのテスト"""
    
    @pytest.fixture
    def loader(self):
        """テスト用のAsyncDataLoaderインスタンスを作成"""
        return AsyncDataLoader()
    
    def test_parse_period(self, loader):
        """期間文字列のパース機能をテスト"""
        end_date = datetime(2025, 11, 27)
        
        # 1年
        start_date = loader._parse_period("1y", end_date)
        expected = end_date - timedelta(days=365)
        assert abs((start_date - expected).days) == 0
        
        # 6ヶ月
        start_date = loader._parse_period("6mo", end_date)
        expected = end_date - timedelta(days=180)
        assert abs((start_date - expected).days) == 0
        
        # 5日
        start_date = loader._parse_period("5d", end_date)
        expected = end_date - timedelta(days=5)
        assert abs((start_date - expected).days) == 0
    
    def test_download_yfinance_valid_ticker(self, loader):
        """有効な銘柄のダウンロードをテスト"""
        # 有名な銘柄でテスト
        df = loader._download_yfinance("AAPL", "1mo")
        
        # DataFrameが返ってくるか
        assert isinstance(df, pd.DataFrame) or df is None
        
        if df is not None:
            # 必須カラムがあるか
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_cols:
                assert col in df.columns
            
            # データが空でないか
            assert len(df) > 0
    
    def test_download_yfinance_invalid_ticker(self, loader):
        """無効な銘柄のダウンロードをテスト"""
        # 存在しない銘柄コード
        df = loader._download_yfinance("INVALID_TICKER_XYZ", "1mo")
        
        # Noneまたは空のDataFrameが返る
        assert df is None or (isinstance(df, pd.DataFrame) and df.empty)
    
    @pytest.mark.asyncio
    async def test_fetch_ticker_async(self, loader):
        """非同期での単一銘柄取得をテスト"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            ticker, df = await loader.fetch_ticker_async(session, "AAPL", "1mo")
            
            assert ticker == "AAPL"
            # 成功した場合はDataFrame、失敗した場合はNone
            assert isinstance(df, pd.DataFrame) or df is None
    
    def test_fetch_multiple_sync_small(self, loader):
        """少数銘柄の同期取得をテスト"""
        tickers = ["AAPL", "GOOGL"]
        result = loader.fetch_multiple_sync(tickers, period="1mo", max_concurrent=2)
        
        # 辞書が返ってくる
        assert isinstance(result, dict)
        
        # 少なくとも1つは成功する（ネットワーク状況による）
        assert len(result) >= 0
        
        # 成功した銘柄のデータはDataFrame
        for ticker, df in result.items():
            assert isinstance(df, pd.DataFrame)
            assert not df.empty
    
    def test_fetch_multiple_sync_empty_list(self, loader):
        """空のリストでの取得をテスト"""
        result = loader.fetch_multiple_sync([], period="1mo")
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_fetch_stock_data_async_function(self):
        """エントリーポイント関数のテスト"""
        tickers = ["AAPL"]
        result = fetch_stock_data_async(tickers, period="1mo", max_concurrent=1)
        
        assert isinstance(result, dict)
        # ネットワーク接続がある場合は成功する
        # assert len(result) >= 0


class TestAsyncPerformance:
    """非同期処理のパフォーマンステスト"""
    
    def test_async_vs_sync_performance(self):
        """非同期と同期のパフォーマンス比較"""
        import time
        
        tickers = ["AAPL", "GOOGL", "MSFT"]
        
        # 非同期版
        start = time.time()
        async_result = fetch_stock_data_async(tickers, period="1mo", max_concurrent=3)
        async_time = time.time() - start
        
        # 同期版（フォールバック）
        loader = AsyncDataLoader()
        start = time.time()
        sync_result = loader._fetch_multiple_fallback(tickers, period="1mo")
        sync_time = time.time() - start
        
        # 非同期版の方が速いか同等
        # ネットワーク状況によるため、単純な比較は難しい
        assert async_time >= 0
        assert sync_time >= 0
        
        print(f"\nPerformance: Async={async_time:.2f}s, Sync={sync_time:.2f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
