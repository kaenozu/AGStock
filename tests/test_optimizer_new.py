"""
Optimizerのテスト
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.optimizer import Optimizer


@pytest.fixture
def sample_data():
    """サンプルの価格データを提供"""
    dates = pd.date_range(start='2023-01-01', periods=200, freq='D')
    np.random.seed(42)
    
    base_price = 100
    trend = np.linspace(0, 20, 200)
    noise = np.random.randn(200) * 2
    prices = base_price + trend + noise
    
    data = {
        'Open': prices * 0.99,
        'High': prices * 1.02,
        'Low': prices * 0.98,
        'Close': prices,
        'Volume': [1000000] * 200
    }
    df = pd.DataFrame(data, index=dates)
    return df


def test_optimizer_init(sample_data):
    """初期化のテスト"""
    optimizer = Optimizer(sample_data, "SMA Crossover")
    
    assert optimizer.df is sample_data
    assert optimizer.strategy_name == "SMA Crossover"
    assert optimizer.backtester is not None


def test_objective_sma_crossover(sample_data):
    """SMA Crossover戦略の目的関数テスト"""
    optimizer = Optimizer(sample_data, "SMA Crossover")
    
    # モックのtrialを作成
    trial = Mock()
    trial.suggest_int.side_effect = [10, 50, 200]  # short, long, trend
    trial.suggest_float.side_effect = [0.05, 0.15]  # stop_loss, take_profit
    
    # バックテスターの結果をモック
    with patch.object(optimizer.backtester, 'run') as mock_run:
        mock_run.return_value = {
            'total_trades': 10,
            'total_return': 15.5
        }
        
        result = optimizer.objective(trial)
        
        assert result == 15.5
        assert mock_run.called


def test_objective_invalid_sma_windows(sample_data):
    """無効なSMAウィンドウの場合のテスト"""
    optimizer = Optimizer(sample_data, "SMA Crossover")
    
    trial = Mock()
    # short_window >= long_windowの無効なケース
    trial.suggest_int.side_effect = [50, 20, 200]
    
    result = optimizer.objective(trial)
    
    assert result == -1.0


def test_objective_rsi_strategy(sample_data):
    """RSI戦略の目的関数テスト"""
    optimizer = Optimizer(sample_data, "RSI Reversal")
    
    trial = Mock()
    trial.suggest_int.side_effect = [14, 30, 70, 200]  # period, lower, upper, trend
    trial.suggest_float.side_effect = [0.05, 0.15]
    
    with patch.object(optimizer.backtester, 'run') as mock_run:
        mock_run.return_value = {
            'total_trades': 8,
            'total_return': 12.3
        }
        
        result = optimizer.objective(trial)
        
        assert result == 12.3


def test_objective_bollinger_bands_strategy(sample_data):
    """Bollinger Bands戦略の目的関数テスト"""
    optimizer = Optimizer(sample_data, "Bollinger Bands")
    
    trial = Mock()
    trial.suggest_int.side_effect = [20, 200]  # length, trend
    trial.suggest_float.side_effect = [2.0, 0.05, 0.15]  # std, stop_loss, take_profit
    
    with patch.object(optimizer.backtester, 'run') as mock_run:
        mock_run.return_value = {
            'total_trades': 12,
            'total_return': 18.7
        }
        
        result = optimizer.objective(trial)
        
        assert result == 18.7


def test_objective_combined_strategy(sample_data):
    """Combined戦略の目的関数テスト"""
    optimizer = Optimizer(sample_data, "Combined")
    
    trial = Mock()
    trial.suggest_int.side_effect = [14, 20, 200]  # rsi_period, bb_length, trend
    trial.suggest_float.side_effect = [2.0, 0.05, 0.15]  # bb_std, stop_loss, take_profit
    
    with patch.object(optimizer.backtester, 'run') as mock_run:
        mock_run.return_value = {
            'total_trades': 15,
            'total_return': 20.5
        }
        
        result = optimizer.objective(trial)
        
        assert result == 20.5


def test_objective_unknown_strategy(sample_data):
    """未知の戦略の場合のテスト"""
    optimizer = Optimizer(sample_data, "Unknown Strategy")
    
    trial = Mock()
    
    result = optimizer.objective(trial)
    
    assert result == -1.0


def test_objective_insufficient_trades(sample_data):
    """取引数が不足している場合のテスト"""
    optimizer = Optimizer(sample_data, "SMA Crossover")
    
    trial = Mock()
    trial.suggest_int.side_effect = [10, 50, 200]
    trial.suggest_float.side_effect = [0.05, 0.15]
    
    with patch.object(optimizer.backtester, 'run') as mock_run:
        # 取引数が3未満
        mock_run.return_value = {
            'total_trades': 2,
            'total_return': 5.0
        }
        
        result = optimizer.objective(trial)
        
        assert result == -1.0


def test_objective_no_result(sample_data):
    """バックテスト結果がない場合のテスト"""
    optimizer = Optimizer(sample_data, "SMA Crossover")
    
    trial = Mock()
    trial.suggest_int.side_effect = [10, 50, 200]
    trial.suggest_float.side_effect = [0.05, 0.15]
    
    with patch.object(optimizer.backtester, 'run') as mock_run:
        mock_run.return_value = None
        
        result = optimizer.objective(trial)
        
        assert result == -1.0


def test_optimize(sample_data):
    """最適化実行のテスト"""
    optimizer = Optimizer(sample_data, "SMA Crossover")
    
    with patch('src.optimizer.optuna.create_study') as mock_create_study:
        mock_study = Mock()
        mock_study.best_params = {'short_window': 10, 'long_window': 50}
        mock_study.best_value = 15.5
        mock_create_study.return_value = mock_study
        
        best_params, best_value = optimizer.optimize(n_trials=10)
        
        assert best_params == {'short_window': 10, 'long_window': 50}
        assert best_value == 15.5
        mock_study.optimize.assert_called_once()


def test_optimize_logging_suppression(sample_data):
    """ログ抑制のテスト"""
    optimizer = Optimizer(sample_data, "SMA Crossover")
    
    with patch('src.optimizer.optuna.logging.set_verbosity') as mock_set_verbosity, \
         patch('src.optimizer.optuna.create_study') as mock_create_study:
        
        mock_study = Mock()
        mock_study.best_params = {}
        mock_study.best_value = 0
        mock_create_study.return_value = mock_study
        
        optimizer.optimize(n_trials=5)
        
        # ログレベルがWARNINGに設定されることを確認
        mock_set_verbosity.assert_called_once()
