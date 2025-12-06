"""
AutoRebalancerの包括的なテスト
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from src.auto_rebalancer import AutoRebalancer


@pytest.fixture
def mock_paper_trader():
    with patch('src.auto_rebalancer.PaperTrader') as mock:
        yield mock


@pytest.fixture
def mock_fetch_stock_data():
    with patch('src.auto_rebalancer.fetch_stock_data') as mock:
        yield mock


@pytest.fixture
def rebalancer(mock_paper_trader):
    return AutoRebalancer(correlation_threshold=0.8)


def test_init(rebalancer):
    """初期化のテスト"""
    assert rebalancer.correlation_threshold == 0.8
    assert rebalancer.pt is not None


def test_check_rebalance_needed_no_positions(rebalancer, mock_paper_trader):
    """ポジションなしの場合"""
    mock_paper_trader.return_value.get_positions.return_value = pd.DataFrame()
    
    needed, pairs = rebalancer.check_rebalance_needed()
    
    assert needed is False
    assert len(pairs) == 0


def test_check_rebalance_needed_high_correlation(rebalancer, mock_paper_trader, mock_fetch_stock_data):
    """高相関ペアがある場合"""
    # ポジション設定
    mock_paper_trader.return_value.get_positions.return_value = pd.DataFrame({
        'ticker': ['AAPL', 'MSFT'],
        'quantity': [10, 10],
        'current_price': [150, 250]
    })
    
    # 価格データ設定（完全に相関するようにする）
    dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
    prices = np.linspace(100, 200, 10)
    df = pd.DataFrame({'Close': prices}, index=dates)
    
    mock_fetch_stock_data.return_value = {
        'AAPL': df,
        'MSFT': df # 同じデータなので相関1.0
    }
    
    needed, pairs = rebalancer.check_rebalance_needed()
    
    assert needed is True
    assert len(pairs) == 1
    assert pairs[0][0] == 'AAPL'
    assert pairs[0][1] == 'MSFT'
    assert pairs[0][2] > 0.99


def test_suggest_replacement(rebalancer, mock_fetch_stock_data):
    """代替銘柄提案のテスト"""
    # 候補プールからの選択ロジックをテスト
    # データ取得をモックして、相関が低いものを返すようにする
    
    # 候補プール: 6758.T, 9984.T, ...
    # 避ける銘柄: 6758.T
    
    # fetch_stock_dataの戻り値を設定
    # 候補1(9984.T)は相関が高い、候補2(6861.T)は相関が低いとする
    
    dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
    base_prices = np.linspace(100, 200, 10)
    
    # 既存保有銘柄の動き
    holding_df = pd.DataFrame({'Close': base_prices}, index=dates)
    
    # 候補1: 同じ動き（高相関）
    cand1_df = pd.DataFrame({'Close': base_prices}, index=dates)
    
    # 候補2: 逆の動き（負の相関）
    cand2_df = pd.DataFrame({'Close': base_prices[::-1]}, index=dates)
    
    mock_fetch_stock_data.return_value = {
        'HOLDING': holding_df,
        '9984.T': cand1_df,
        '6861.T': cand2_df,
        # 他の候補も適当に
        '4063.T': cand1_df,
        '6367.T': cand1_df,
        '4502.T': cand1_df
    }
    
    replacement = rebalancer.suggest_replacement('TO_REPLACE', avoid_tickers=['HOLDING'])
    
    # 6861.Tが選ばれるはず（相関が最も低い）
    assert replacement == '6861.T'


def test_execute_rebalance_dry_run(rebalancer, mock_paper_trader, mock_fetch_stock_data):
    """リバランス実行（ドライラン）のテスト"""
    # check_rebalance_neededをモックして高相関ペアを返すようにする
    with patch.object(rebalancer, 'check_rebalance_needed') as mock_check:
        mock_check.return_value = (True, [('AAPL', 'MSFT', 0.95)])
        
        # suggest_replacementをモック
        with patch.object(rebalancer, 'suggest_replacement') as mock_suggest:
            mock_suggest.return_value = 'GOOGL'
            
            # ポジション情報
            mock_paper_trader.return_value.get_positions.return_value = pd.DataFrame({
                'ticker': ['AAPL', 'MSFT'],
                'quantity': [10, 5],
                'current_price': [150, 200]
            })
            # AAPL: 1500, MSFT: 1000 -> MSFTが売られるはず
            
            actions = rebalancer.execute_rebalance(dry_run=True)
            
            assert len(actions) == 1
            assert actions[0]['sell']['ticker'] == 'MSFT'
            assert actions[0]['buy']['ticker'] == 'GOOGL'
            
            # トレードは実行されないはず
            mock_paper_trader.return_value.execute_trade.assert_not_called()


def test_execute_rebalance_real(rebalancer, mock_paper_trader, mock_fetch_stock_data):
    """リバランス実行（実実行）のテスト"""
    with patch.object(rebalancer, 'check_rebalance_needed') as mock_check:
        mock_check.return_value = (True, [('AAPL', 'MSFT', 0.95)])
        
        with patch.object(rebalancer, 'suggest_replacement') as mock_suggest:
            mock_suggest.return_value = 'GOOGL'
            
            mock_paper_trader.return_value.get_positions.return_value = pd.DataFrame({
                'ticker': ['AAPL', 'MSFT'],
                'quantity': [10, 5],
                'current_price': [150, 200]
            })
            
            # GOOGLの価格データ
            mock_fetch_stock_data.return_value = {
                'GOOGL': pd.DataFrame({'Close': [100]}, index=[pd.Timestamp.now()])
            }
            
            actions = rebalancer.execute_rebalance(dry_run=False)
            
            # 売却と購入が実行されるはず
            assert mock_paper_trader.return_value.execute_trade.call_count == 2
            
            # 売り: MSFT
            args_sell, _ = mock_paper_trader.return_value.execute_trade.call_args_list[0]
            assert args_sell[0] == 'MSFT'
            assert args_sell[1] == 'SELL'
            
            # 買い: GOOGL
            args_buy, _ = mock_paper_trader.return_value.execute_trade.call_args_list[1]
            assert args_buy[0] == 'GOOGL'
            assert args_buy[1] == 'BUY'
