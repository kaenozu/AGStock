import sys
import types
from unittest.mock import MagicMock

# Mock streamlit to prevent caching issues during testing
# This must be done before any module imports streamlit

# Create mock streamlit module
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

# Make cache_resource similar
def mock_cache_resource(*args, **kwargs):
    if len(args) == 1 and callable(args[0]):
        return args[0]
    def decorator(func):
        return func
    return decorator

mock_st.cache_data = mock_cache_data
mock_st.cache_resource = mock_cache_resource
# Add other common streamlit attributes used at import time if necessary
mock_st.session_state = {}
mock_st.sidebar = MagicMock()
mock_st.columns = MagicMock(return_value=[MagicMock(), MagicMock()])
mock_st.tabs = MagicMock(return_value=[MagicMock(), MagicMock()])
mock_st.expander = MagicMock()
mock_st.container = MagicMock()
mock_st.empty = MagicMock()
mock_st.markdown = MagicMock()
mock_st.write = MagicMock()
mock_st.header = MagicMock()
mock_st.subheader = MagicMock()
mock_st.info = MagicMock()
mock_st.warning = MagicMock()
mock_st.error = MagicMock()
mock_st.success = MagicMock()
mock_st.button = MagicMock(return_value=False)
mock_st.selectbox = MagicMock(return_value="")
mock_st.multiselect = MagicMock(return_value=[])
mock_st.slider = MagicMock(return_value=0)
mock_st.number_input = MagicMock(return_value=0)
mock_st.text_input = MagicMock(return_value="")
mock_st.text_area = MagicMock(return_value="")
mock_st.checkbox = MagicMock(return_value=False)
mock_st.radio = MagicMock(return_value="")
mock_st.plotly_chart = MagicMock()
mock_st.dataframe = MagicMock()
mock_st.metric = MagicMock()
mock_st.spinner = MagicMock()
mock_st.progress = MagicMock()
mock_st.set_page_config = MagicMock()
mock_st.title = MagicMock()

# Replace streamlit module (always, to ensure consistency)
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


@pytest.fixture(scope="function", autouse=True)
def mock_yfinance(monkeypatch):
    """
    ネットワーク依存を避けるため、yfinance をモックしてテストを安定化。
    """
    try:
        import yfinance as yf  # type: ignore
    except ImportError:
        import types

        yf = types.SimpleNamespace()
        monkeypatch.setitem(sys.modules, "yfinance", yf)

    import pandas as pd
    import numpy as np

    def _fake_history(period="1y", *args, **kwargs):
        dates = pd.date_range(end=pd.Timestamp.today(), periods=60, freq="D")
        base = np.linspace(100, 110, len(dates))
        data = pd.DataFrame(
            {"Open": base, "High": base * 1.01, "Low": base * 0.99, "Close": base, "Volume": 1_000_000},
            index=dates,
        )
        return data

    class _FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, period="1y", *args, **kwargs):
            return _fake_history(period, *args, **kwargs)

    # モックを適用（存在しない場合も raising=False でスキップ）
    monkeypatch.setattr("yfinance.Ticker", _FakeTicker, raising=False)
    monkeypatch.setattr("yfinance.download", lambda ticker, period="1y", progress=False, **_: _fake_history(period), raising=False)
