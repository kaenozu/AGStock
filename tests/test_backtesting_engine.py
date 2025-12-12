"""BacktestEngineのテストモジュール。"""
import pytest
import pandas as pd
import numpy as np
from src.backtesting.engine import BacktestEngine
from src.strategies import SMACrossoverStrategy


@pytest.fixture
def sample_data():
    """サンプル株価データを作成するフィクスチャ"""
    dates = pd.date_range(start="2023-01-01", end="2023-02-01", freq="D")
    df = pd.DataFrame({
        "Open": np.random.rand(len(dates)) * 100 + 100,
        "High": np.random.rand(len(dates)) * 100 + 102,
        "Low": np.random.rand(len(dates)) * 100 + 98,
        "Close": np.random.rand(len(dates)) * 100 + 100,
        "Volume": np.random.rand(len(dates)) * 1000000 + 500000,
    }, index=dates)
    return df


@pytest.fixture
def backtest_engine():
    """BacktestEngineのインスタンスを作成するフィクスチャ"""
    return BacktestEngine(
        initial_capital=1_000_000,
        commission=0.001,
        slippage=0.001
    )


def test_backtest_engine_initialization(backtest_engine):
    """BacktestEngineが正しく初期化されることを確認"""
    assert backtest_engine.initial_capital == 1_000_000
    assert backtest_engine.commission == 0.001


def test_run_backtest_single_asset(backtest_engine, sample_data):
    """単一資産のバックテストが正常に実行されることを確認"""
    strategy = SMACrossoverStrategy(short_window=5, long_window=20)
    result = backtest_engine.run(
        data=sample_data,
        strategy=strategy
    )

    assert result is not None
    assert "total_return" in result
    assert "final_value" in result
    assert "equity_curve" in result
    assert "trades" in result
    assert "win_rate" in result
    assert "sharpe_ratio" in result