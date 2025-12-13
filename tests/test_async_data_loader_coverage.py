import asyncio
import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd

from src.async_data_loader import (AsyncDataLoader, fetch_stock_data_async,
                                   get_async_loader)


class TestAsyncDataLoader(unittest.TestCase):
    """Tests for AsyncDataLoader class"""

    @patch("src.async_data_loader.DataManager")
    def setUp(self, mock_dm_class):
        """Set up test fixtures"""
        self.mock_dm = MagicMock()
        self.mock_dm.load_data.return_value = pd.DataFrame()
        mock_dm_class.return_value = self.mock_dm
        self.loader = AsyncDataLoader()

    @patch("src.async_data_loader.DataManager")
    def test_init(self, mock_dm_class):
        """Test AsyncDataLoader initialization"""
        loader = AsyncDataLoader(db_path="test.db")
        self.assertIsNotNone(loader.db)
        mock_dm_class.assert_called_once_with("test.db")

    def test_parse_period(self):
        """Test _parse_period method"""
        end_date = datetime(2023, 12, 31)

        # Test 1 year
        result = self.loader._parse_period("1y", end_date)
        expected = end_date - timedelta(days=365)
        self.assertEqual(result.date(), expected.date())

        # Test 6 months
        result = self.loader._parse_period("6mo", end_date)
        expected = end_date - timedelta(days=180)
        self.assertEqual(result.date(), expected.date())

        # Test unknown period (defaults to 1y)
        result = self.loader._parse_period("unknown", end_date)
        expected = end_date - timedelta(days=365)
        self.assertEqual(result.date(), expected.date())

    @patch("src.async_data_loader.yf.Ticker")
    def test_download_yfinance_success(self, mock_ticker_class):
        """Test _download_yfinance with successful download"""
        mock_df = pd.DataFrame(
            {"Open": [100, 101], "High": [105, 106], "Low": [99, 100], "Close": [102, 103], "Volume": [1000, 1100]}
        )

        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_df
        mock_ticker_class.return_value = mock_ticker

        result = self.loader._download_yfinance("AAPL", "1mo")

        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn("Close", result.columns)
        mock_ticker.history.assert_called_once()

    @patch("src.async_data_loader.yf.Ticker")
    def test_download_yfinance_empty(self, mock_ticker_class):
        """Test _download_yfinance with empty result"""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_class.return_value = mock_ticker

        result = self.loader._download_yfinance("INVALID", "1mo")

        self.assertIsNone(result)

    @patch("src.async_data_loader.yf.Ticker")
    def test_download_yfinance_error(self, mock_ticker_class):
        """Test _download_yfinance with exception"""
        mock_ticker_class.side_effect = Exception("Network error")

        result = self.loader._download_yfinance("AAPL", "1mo")

        self.assertIsNone(result)

    @patch("src.async_data_loader.DataManager")
    @patch("src.async_data_loader.yf.Ticker")
    def test_fetch_multiple_sync(self, mock_ticker_class, mock_dm_class):
        """Test fetch_multiple_sync method"""
        mock_df = pd.DataFrame({"Close": [100, 101]})
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_df
        mock_ticker_class.return_value = mock_ticker

        mock_dm = MagicMock()
        mock_dm.load_data.return_value = pd.DataFrame()
        mock_dm_class.return_value = mock_dm

        loader = AsyncDataLoader()
        result = loader.fetch_multiple_sync(["AAPL"], "1mo", max_concurrent=2)

        self.assertIsInstance(result, dict)


class TestAsyncLoaderGlobalFunctions(unittest.TestCase):
    """Test global functions in async_data_loader"""

    @patch("src.async_data_loader.AsyncDataLoader")
    def test_get_async_loader(self, mock_loader_class):
        """Test get_async_loader singleton"""
        mock_instance = MagicMock()
        mock_loader_class.return_value = mock_instance

        # Clear global instance
        import src.async_data_loader as adl

        adl._async_loader = None

        # First call should create instance
        loader1 = get_async_loader()
        # Second call should return same instance
        loader2 = get_async_loader()

        # Should only create once
        self.assertEqual(mock_loader_class.call_count, 1)

    @patch("src.async_data_loader.AsyncDataLoader")
    def test_fetch_stock_data_async(self, mock_loader_class):
        """Test fetch_stock_data_async entry point"""
        mock_loader = MagicMock()
        mock_loader.fetch_multiple_sync.return_value = {"AAPL": pd.DataFrame()}
        mock_loader_class.return_value = mock_loader

        # Clear global
        import src.async_data_loader as adl

        adl._async_loader = None

        result = fetch_stock_data_async(["AAPL"], "1y", max_concurrent=5)

        self.assertIsInstance(result, dict)
        mock_loader.fetch_multiple_sync.assert_called_once_with(["AAPL"], "1y", 5)


if __name__ == "__main__":
    unittest.main()
