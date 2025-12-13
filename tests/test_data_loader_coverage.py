import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from src.data_loader import (CRYPTO_PAIRS, FX_PAIRS, JP_STOCKS,
                             fetch_stock_data, get_latest_price, parse_period,
                             process_downloaded_data)


class TestProcessDownloadedData(unittest.TestCase):
    """Tests for process_downloaded_data function"""

    def test_empty_input(self):
        """Test with empty dataframe"""
        result = process_downloaded_data(pd.DataFrame(), ["AAPL"], {})
        self.assertEqual(result, {})

    def test_none_input(self):
        """Test with None input"""
        result = process_downloaded_data(None, ["AAPL"], {})
        self.assertEqual(result, {})

    def test_empty_tickers(self):
        """Test with empty ticker list"""
        df = pd.DataFrame({"Close": [100, 101]})
        result = process_downloaded_data(df, [], {})
        self.assertEqual(result, {})

    def test_single_ticker(self):
        """Test with single ticker"""
        df = pd.DataFrame({"Close": [100, 101, 102], "Volume": [1000, 1100, 1200]})
        result = process_downloaded_data(df, ["AAPL"])

        self.assertIn("AAPL", result)
        self.assertEqual(len(result["AAPL"]), 3)

    def test_multi_index_dataframe(self):
        """Test with multi-index columns (multiple tickers)"""
        # Create multi-index dataframe like yfinance returns
        tickers = ["AAPL", "GOOGL"]
        data = {
            ("Close", "AAPL"): [150, 151, 152],
            ("Close", "GOOGL"): [2800, 2810, 2820],
            ("Volume", "AAPL"): [1000, 1100, 1200],
            ("Volume", "GOOGL"): [500, 550, 600],
        }
        df = pd.DataFrame(data)
        df.columns = pd.MultiIndex.from_tuples(df.columns)

        result = process_downloaded_data(df, tickers)

        self.assertIn("AAPL", result)
        self.assertIn("GOOGL", result)
        self.assertEqual(len(result["AAPL"]), 3)

    def test_column_map(self):
        """Test with column mapping"""
        data = {("Close", "AAPL_MAPPED"): [150, 151, 152], ("Volume", "AAPL_MAPPED"): [1000, 1100, 1200]}
        df = pd.DataFrame(data)
        df.columns = pd.MultiIndex.from_tuples(df.columns)

        column_map = {"AAPL": "AAPL_MAPPED"}
        result = process_downloaded_data(df, ["AAPL"], column_map)

        self.assertIn("AAPL", result)

    def test_dropna(self):
        """Test that NaN values are dropped"""
        df = pd.DataFrame({"Close": [100, np.nan, 102], "Volume": [1000, 1100, np.nan]})
        result = process_downloaded_data(df, ["AAPL"])

        # Should only have one row without NaN
        self.assertIn("AAPL", result)
        self.assertTrue(len(result["AAPL"]) < 3)


class TestParsePeriod(unittest.TestCase):
    """Tests for parse_period function"""

    def test_parse_years(self):
        """Test parsing year periods"""
        result = parse_period("2y")
        expected = datetime.now() - timedelta(days=365 * 2)
        self.assertAlmostEqual(result.timestamp(), expected.timestamp(), delta=60)

    def test_parse_months(self):
        """Test parsing month periods"""
        result = parse_period("6mo")
        expected = datetime.now() - timedelta(days=30 * 6)
        self.assertAlmostEqual(result.timestamp(), expected.timestamp(), delta=86400)

    def test_parse_days(self):
        """Test parsing day periods"""
        result = parse_period("7d")
        expected = datetime.now() - timedelta(days=7)
        self.assertAlmostEqual(result.timestamp(), expected.timestamp(), delta=60)

    def test_default_period(self):
        """Test default period for unknown format"""
        result = parse_period("unknown")
        expected = datetime.now() - timedelta(days=730)  # 2 years default
        self.assertAlmostEqual(result.timestamp(), expected.timestamp(), delta=60)


class TestFetchStockData(unittest.TestCase):
    """Tests for fetch_stock_data function"""

    @patch("src.data_loader.yf.download")
    @patch("src.data_loader.DataManager")
    def test_fetch_single_ticker(self, mock_dm_class, mock_download):
        """Test fetching single ticker"""
        mock_df = pd.DataFrame(
            {"Close": [100, 101, 102], "Volume": [1000, 1100, 1200]}, index=pd.date_range("2023-01-01", periods=3)
        )

        mock_download.return_value = mock_df
        mock_dm = MagicMock()
        mock_dm.load_data.return_value = pd.DataFrame()  # No cached data
        mock_dm_class.return_value = mock_dm

        result = fetch_stock_data(["AAPL"], "1mo", use_async=False)

        self.assertIsInstance(result, dict)

    @patch("src.data_loader.yf.download")
    @patch("src.data_loader.DataManager")
    def test_fetch_multiple_tickers(self, mock_dm_class, mock_download):
        """Test fetching multiple tickers"""
        # Create multi-index dataframe
        data = {("Close", "AAPL"): [150, 151], ("Close", "GOOGL"): [2800, 2810]}
        mock_df = pd.DataFrame(data)
        mock_df.columns = pd.MultiIndex.from_tuples(mock_df.columns)

        mock_download.return_value = mock_df
        mock_dm = MagicMock()
        mock_dm.load_data.return_value = pd.DataFrame()
        mock_dm_class.return_value = mock_dm

        result = fetch_stock_data(["AAPL", "GOOGL"], "1mo", use_async=False)

        self.assertIsInstance(result, dict)


class TestGetLatestPrice(unittest.TestCase):
    """Tests for get_latest_price function"""

    def test_get_latest_price_success(self):
        """Test successful price retrieval from DataFrame"""
        df = pd.DataFrame({"Close": [100, 101, 102], "Volume": [1000, 1100, 1200]})

        price = get_latest_price(df)

        self.assertEqual(price, 102)

    def test_get_latest_price_empty_df(self):
        """Test with empty DataFrame"""
        df = pd.DataFrame()

        price = get_latest_price(df)

        self.assertEqual(price, 0.0)

    def test_get_latest_price_none(self):
        """Test with None input"""
        price = get_latest_price(None)

        self.assertEqual(price, 0.0)

    def test_get_latest_price_single_row(self):
        """Test with single row DataFrame"""
        df = pd.DataFrame({"Close": [150.25]})

        price = get_latest_price(df)

        self.assertEqual(price, 150.25)


class TestConstants(unittest.TestCase):
    """Test module-level constants"""

    def test_crypto_pairs_defined(self):
        """Test CRYPTO_PAIRS is defined and non-empty"""
        self.assertIsInstance(CRYPTO_PAIRS, list)
        self.assertGreater(len(CRYPTO_PAIRS), 0)
        self.assertIn("BTC-USD", CRYPTO_PAIRS)

    def test_fx_pairs_defined(self):
        """Test FX_PAIRS is defined and non-empty"""
        self.assertIsInstance(FX_PAIRS, list)
        self.assertGreater(len(FX_PAIRS), 0)
        self.assertIn("USDJPY=X", FX_PAIRS)

    def test_jp_stocks_defined(self):
        """Test JP_STOCKS is defined and non-empty"""
        self.assertIsInstance(JP_STOCKS, list)
        self.assertGreater(len(JP_STOCKS), 0)
        self.assertIn("7203.T", JP_STOCKS)  # Toyota


if __name__ == "__main__":
    unittest.main()
