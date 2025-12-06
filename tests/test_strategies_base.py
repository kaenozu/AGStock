"""
戦略基底クラステスト

src/strategies/base.py のテスト
"""
import pytest
import pandas as pd
import numpy as np
from src.strategies.base import Strategy, Order, OrderType

class ConcreteStrategy(Strategy):
    """テスト用の具象戦略クラス"""
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        # 単純なシグナル生成: Close > Open なら買い、それ以外は売り
        signals = pd.Series(0, index=df.index)
        signals[df['Close'] > df['Open']] = 1
        signals[df['Close'] < df['Open']] = -1
        return signals

@pytest.fixture
def sample_data():
    """テスト用データ"""
    dates = pd.date_range(start='2023-01-01', periods=10)
    data = {
        'Open': [100, 105, 102, 110, 108, 115, 112, 120, 118, 125],
        'High': [105, 110, 108, 115, 112, 120, 118, 125, 122, 130],
        'Low': [95, 100, 98, 105, 102, 110, 108, 115, 112, 120],
        'Close': [102, 100, 105, 108, 110, 112, 115, 118, 120, 122],
        'Volume': [1000] * 10
    }
    return pd.DataFrame(data, index=dates)

def test_order_dataclass():
    """Orderデータクラスのテスト"""
    order = Order(
        ticker="AAPL",
        type=OrderType.MARKET,
        action="BUY",
        quantity=100
    )
    assert order.ticker == "AAPL"
    assert order.type == OrderType.MARKET
    assert order.action == "BUY"
    assert order.quantity == 100
    assert order.price is None

def test_strategy_init():
    """Strategy初期化テスト"""
    strategy = Strategy("TestStrategy", trend_period=50)
    assert strategy.name == "TestStrategy"
    assert strategy.trend_period == 50

def test_apply_trend_filter(sample_data):
    """トレンドフィルタテスト"""
    strategy = Strategy("TestStrategy", trend_period=5)
    
    # シグナル作成 (全て買い)
    signals = pd.Series(1, index=sample_data.index)
    
    # トレンドフィルタ適用
    # Close > SMA(5) の場合のみ買いシグナルが残るはず
    filtered = strategy.apply_trend_filter(sample_data, signals)
    
    sma = sample_data['Close'].rolling(window=5).mean()
    expected = signals.copy()
    expected[sample_data['Close'] <= sma] = 0
    # 最初の4つはSMA計算できないのでNaN -> False扱いになるか、rollingの挙動による
    # pandas rolling meanの初めの4つはNaN
    # Close > NaN は False
    
    # NaN比較の挙動を確認するため、手動で計算
    # index 0-3: NaN
    # index 4: (102+100+105+108+110)/5 = 105. Close=110 > 105 (Buy kept)
    
    # NaNの部分は条件がFalseになるので0になるはず
    
    pd.testing.assert_series_equal(filtered[4:], expected[4:])

def test_apply_trend_filter_disabled(sample_data):
    """トレンドフィルタ無効化テスト"""
    strategy = Strategy("TestStrategy", trend_period=0)
    signals = pd.Series(1, index=sample_data.index)
    filtered = strategy.apply_trend_filter(sample_data, signals)
    pd.testing.assert_series_equal(filtered, signals)

def test_generate_signals_not_implemented():
    """generate_signals未実装エラーテスト"""
    strategy = Strategy("BaseStrategy")
    with pytest.raises(NotImplementedError):
        strategy.generate_signals(pd.DataFrame())

def test_analyze(sample_data):
    """analyzeメソッドテスト"""
    strategy = ConcreteStrategy("Concrete")
    result = strategy.analyze(sample_data)
    
    assert 'signal' in result
    assert 'confidence' in result
    # 最後のデータ: Open=125, Close=122 -> Close < Open -> Sell (-1)
    assert result['signal'] == -1
    assert result['confidence'] == 1.0

def test_analyze_empty():
    """空データでのanalyzeテスト"""
    strategy = ConcreteStrategy("Concrete")
    # カラムを持つ空のDataFrameを作成
    empty_df = pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
    result = strategy.analyze(empty_df)
    assert result['signal'] == 0
    assert result['confidence'] == 0.0

def test_get_signal_explanation():
    """シグナル説明テスト"""
    strategy = Strategy("Test")
    assert strategy.get_signal_explanation(1) == "買いシグナル"
    assert strategy.get_signal_explanation(-1) == "売りシグナル"
    assert strategy.get_signal_explanation(0) == "様子見"
