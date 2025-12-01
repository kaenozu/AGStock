import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import MagicMock, patch
from src.auto_trader_ui import render_todays_summary

def test_render_todays_summary_no_data():
    with patch('src.auto_trader_ui.PaperTrader') as MockPT:
        mock_pt = MockPT.return_value
        mock_pt.get_trade_history.return_value = pd.DataFrame()
        
        with patch('streamlit.info') as mock_info:
            render_todays_summary()
            mock_info.assert_called_with("取引データなし")

def test_render_todays_summary_with_data():
    with patch('src.auto_trader_ui.PaperTrader') as MockPT:
        mock_pt = MockPT.return_value
        
        # テストデータ作成
        today = datetime.now()
        data = {
            'timestamp': [today, today],
            'ticker': ['7203', '9984'],
            'action': ['BUY', 'SELL'],
            'quantity': [100, 100],
            'price': [2000, 5000],
            'realized_pnl': [0, 1000]
        }
        df = pd.DataFrame(data)
        mock_pt.get_trade_history.return_value = df
        
        with patch('streamlit.columns') as mock_cols:
            col1 = MagicMock()
            col2 = MagicMock()
            mock_cols.return_value = [col1, col2]
            
            with patch('streamlit.expander'):
                with patch('streamlit.dataframe'):
                    render_todays_summary()
            
            # メトリックが表示されたか確認
            col1.metric.assert_called()
            col2.metric.assert_called()

def test_render_todays_summary_missing_timestamp():
    """KeyError: 'timestamp' の修正確認用テスト"""
    with patch('src.auto_trader_ui.PaperTrader') as MockPT:
        mock_pt = MockPT.return_value
        
        # timestampカラムがないデータ
        data = {
            'ticker': ['7203'],
            'action': ['BUY']
        }
        df = pd.DataFrame(data)
        mock_pt.get_trade_history.return_value = df
        
        with patch('streamlit.info') as mock_info:
            render_todays_summary()
            # エラーにならずに「本日の取引はまだありません」などが表示されるはず
            # （timestampがない=日付判定できない=本日の取引なしとみなす実装の場合）
            mock_info.assert_called()
