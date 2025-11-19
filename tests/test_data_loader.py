import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.data_loader import fetch_stock_data, get_latest_price


class TestFetchStockData:
    """fetch_stock_data関数のテスト"""
    
    @patch('src.data_loader.yf.download')
    def test_fetch_single_ticker(self, mock_download):
        """単一ティッカーのデータ取得テスト"""
        # モックデータを作成
        mock_data = pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [105, 106, 107],
            'Low': [95, 96, 97],
            'Close': [102, 103, 104],
            'Volume': [1000000, 1100000, 1200000]
        }, index=pd.date_range('2023-01-01', periods=3))
        
        mock_download.return_value = mock_data
        
        result = fetch_stock_data(['7203.T'], period='1y')
        
        assert isinstance(result, dict)
        assert '7203.T' in result
        assert isinstance(result['7203.T'], pd.DataFrame)
        assert len(result['7203.T']) == 3
    
    @patch('src.data_loader.yf.download')
    def test_fetch_multiple_tickers(self, mock_download):
        """複数ティッカーのデータ取得テスト"""
        # 複数ティッカーのモックデータ
        tickers = ['7203.T', '9984.T']
        
        # yfinanceは複数ティッカーの場合、マルチインデックスを返す
        mock_data = pd.DataFrame({
            ('7203.T', 'Open'): [100, 101],
            ('7203.T', 'High'): [105, 106],
            ('7203.T', 'Low'): [95, 96],
            ('7203.T', 'Close'): [102, 103],
            ('7203.T', 'Volume'): [1000000, 1100000],
            ('9984.T', 'Open'): [200, 201],
            ('9984.T', 'High'): [205, 206],
            ('9984.T', 'Low'): [195, 196],
            ('9984.T', 'Close'): [202, 203],
            ('9984.T', 'Volume'): [2000000, 2100000],
        }, index=pd.date_range('2023-01-01', periods=2))
        
        # マルチインデックスカラムを設定
        mock_data.columns = pd.MultiIndex.from_tuples(mock_data.columns)
        mock_download.return_value = mock_data
        
        result = fetch_stock_data(tickers, period='1y')
        
        assert isinstance(result, dict)
        assert '7203.T' in result
        assert '9984.T' in result
    
    def test_fetch_empty_ticker_list(self):
        """空のティッカーリストでの処理テスト"""
        result = fetch_stock_data([], period='1y')
        assert isinstance(result, dict)
        assert len(result) == 0
    
    @patch('src.data_loader.yf.download')
    def test_fetch_with_nan_values(self, mock_download):
        """NaN値を含むデータの処理テスト"""
        # NaN値を含むモックデータ
        mock_data = pd.DataFrame({
            'Open': [100, None, 102],
            'High': [105, 106, None],
            'Low': [95, 96, 97],
            'Close': [102, 103, 104],
            'Volume': [1000000, 1100000, 1200000]
        }, index=pd.date_range('2023-01-01', periods=3))
        
        mock_download.return_value = mock_data
        
        result = fetch_stock_data(['7203.T'], period='1y')
        
        # NaN行が削除されることを確認
        assert '7203.T' in result
        # dropna()が呼ばれるので、NaNを含む行は削除される
        assert len(result['7203.T']) < 3
    
    @patch('src.data_loader.yf.download')
    def test_fetch_with_exception(self, mock_download):
        """例外発生時の処理テスト"""
        mock_download.side_effect = Exception("Network error")
        
        result = fetch_stock_data(['7203.T'], period='1y')
        
        # エラー時は空の辞書を返す
        assert isinstance(result, dict)
        assert len(result) == 0
    
    @patch('src.data_loader.yf.download')
    def test_fetch_with_different_periods(self, mock_download):
        """異なる期間でのデータ取得テスト"""
        mock_data = pd.DataFrame({
            'Open': [100],
            'High': [105],
            'Low': [95],
            'Close': [102],
            'Volume': [1000000]
        }, index=pd.date_range('2023-01-01', periods=1))
        
        mock_download.return_value = mock_data
        
        # 異なる期間でテスト
        for period in ['1y', '2y', '5y']:
            result = fetch_stock_data(['7203.T'], period=period)
            assert '7203.T' in result
            
            # yf.downloadが呼ばれたことを確認（引数の詳細は確認しない）
            assert mock_download.called


class TestGetLatestPrice:
    """get_latest_price関数のテスト"""
    
    def test_get_latest_price_normal(self):
        """正常なデータフレームから最新価格を取得"""
        df = pd.DataFrame({
            'Close': [100, 101, 102, 103, 104]
        })
        
        price = get_latest_price(df)
        assert price == 104
    
    def test_get_latest_price_single_row(self):
        """1行のデータフレームから価格を取得"""
        df = pd.DataFrame({
            'Close': [100]
        })
        
        price = get_latest_price(df)
        assert price == 100
    
    def test_get_latest_price_empty_dataframe(self):
        """空のデータフレームで0.0を返す"""
        df = pd.DataFrame()
        
        price = get_latest_price(df)
        assert price == 0.0
    
    def test_get_latest_price_none(self):
        """Noneが渡された場合に0.0を返す"""
        price = get_latest_price(None)
        assert price == 0.0
    
    def test_get_latest_price_with_float(self):
        """浮動小数点の価格を正しく取得"""
        df = pd.DataFrame({
            'Close': [100.5, 101.75, 102.25]
        })
        
        price = get_latest_price(df)
        assert price == 102.25
    
    def test_get_latest_price_with_index(self):
        """インデックス付きデータフレームから価格を取得"""
        df = pd.DataFrame({
            'Close': [100, 101, 102]
        }, index=pd.date_range('2023-01-01', periods=3))
        
        price = get_latest_price(df)
        assert price == 102
