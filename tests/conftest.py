import sys
import types
from unittest.mock import MagicMock

# Mock streamlit to prevent caching issues during testing
# This must be done before any module imports streamlit
if "streamlit" not in sys.modules:
    mock_st = types.ModuleType("streamlit")
    
    # Make cache_data a flexible pass-through decorator
    def mock_cache_data(*args, **kwargs):
        # Case 1: Called as @st.cache_data (no parens) -> args[0] is the function
        if len(args) == 1 and callable(args[0]):
            return args[0]
        
        # Case 2: Called as @st.cache_data(...) (with parens) -> returns a decorator
        def decorator(func):
            return func
        return decorator
    
    mock_st.cache_data = mock_cache_data
    # Add other common streamlit attributes used at import time if necessary
    mock_st.session_state = {}
    mock_st.sidebar = MagicMock()
    mock_st.columns = MagicMock(return_value=[MagicMock(), MagicMock()])
    
    sys.modules["streamlit"] = mock_st

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_stock_data():
    """サンプル株価データフレームを生成"""
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")

    # シンプルなトレンドデータを生成
    np.random.seed(42)
    base_price = 1000
    prices = base_price + np.cumsum(np.random.randn(100) * 10)

    df = pd.DataFrame(
        {
            "Open": prices + np.random.randn(100) * 5,
            "High": prices + np.abs(np.random.randn(100) * 10),
            "Low": prices - np.abs(np.random.randn(100) * 10),
            "Close": prices,
            "Volume": np.random.randint(1000000, 10000000, 100),
        },
        index=dates,
    )

    return df


@pytest.fixture
def trending_up_data():
    """上昇トレンドのサンプルデータ"""
    dates = pd.date_range(start="2023-01-01", periods=50, freq="D")
    prices = 1000 + np.arange(50) * 10  # 明確な上昇トレンド

    df = pd.DataFrame(
        {
            "Open": prices,
            "High": prices + 5,
            "Low": prices - 5,
            "Close": prices,
            "Volume": np.random.randint(1000000, 10000000, 50),
        },
        index=dates,
    )

    return df


@pytest.fixture
def trending_down_data():
    """下降トレンドのサンプルデータ"""
    dates = pd.date_range(start="2023-01-01", periods=50, freq="D")
    prices = 1500 - np.arange(50) * 10  # 明確な下降トレンド

    df = pd.DataFrame(
        {
            "Open": prices,
            "High": prices + 5,
            "Low": prices - 5,
            "Close": prices,
            "Volume": np.random.randint(1000000, 10000000, 50),
        },
        index=dates,
    )

    return df


@pytest.fixture
def empty_dataframe():
    """空のデータフレーム"""
    return pd.DataFrame()


@pytest.fixture
def sma_strategy():
    """SMA Crossover戦略のインスタンス"""
    from src.strategies import SMACrossoverStrategy

    return SMACrossoverStrategy(short_window=5, long_window=25)


@pytest.fixture
def rsi_strategy():
    """RSI戦略のインスタンス"""
    from src.strategies import RSIStrategy

    return RSIStrategy(period=14, lower=30, upper=70)


@pytest.fixture
def bollinger_strategy():
    """Bollinger Bands戦略のインスタンス"""
    from src.strategies import BollingerBandsStrategy

    return BollingerBandsStrategy(length=20, std=2)


@pytest.fixture
def backtester():
    """Backtesterのインスタンス"""
    from src.backtester import Backtester

    return Backtester(initial_capital=1000000)
