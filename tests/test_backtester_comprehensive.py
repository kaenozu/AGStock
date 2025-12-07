"""
Backtesterの包括的なテスト
"""
import pytest
import pandas as pd
import numpy as np
from src.backtester import Backtester
from src.strategies import Strategy, Order, OrderType


@pytest.fixture
def sample_data():
    """サンプルの価格データを提供"""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # 緩やかな上昇トレンド
    prices = 100 + np.linspace(0, 20, 100) + np.random.randn(100)
    
    df = pd.DataFrame({
        'Open': prices,
        'High': prices + 2,
        'Low': prices - 2,
        'Close': prices,
        'Volume': 1000000
    }, index=dates)
    
    return df


class MockStrategy(Strategy):
    """テスト用のモック戦略"""
    def __init__(self, signals, name="MockStrategy"):
        super().__init__(name=name)
        self.signals = signals
        
    def generate_signals(self, data):
        # データ長に合わせてシグナルを調整
        return pd.Series(self.signals[:len(data)], index=data.index)


def test_init():
    """初期化のテスト"""
    bt = Backtester(initial_capital=50000, commission=0.0)
    assert bt.initial_capital == 50000
    assert bt.commission == 0.0


def test_run_basic_long(sample_data):
    """基本的なロング取引のテスト"""
    bt = Backtester(initial_capital=10000, commission=0.0, slippage=0.0)
    
    # 最初の日で買い、最後の日で売り
    signals = [0] * 100
    signals[0] = 1
    signals[-2] = -1
    
    strategy = MockStrategy(signals)
    
    result = bt.run(sample_data, strategy)
    
    assert result['total_return'] > 0
    assert result['total_trades'] == 1
    assert len(result['trades']) == 1
    assert result['trades'][0]['type'] == 'Long'


def test_run_basic_short(sample_data):
    """基本的なショート取引のテスト"""
    bt = Backtester(initial_capital=10000, commission=0.0, slippage=0.0, allow_short=True)
    
    # 下降トレンドデータを作成
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    prices = 100 - np.linspace(0, 20, 100)
    df = pd.DataFrame({
        'Open': prices, 'High': prices+1, 'Low': prices-1, 'Close': prices
    }, index=dates)
    
    # 最初の日で売り、最後の日で買い戻し
    signals = [0] * 100
    signals[0] = -1
    signals[-2] = 1
    
    strategy = MockStrategy(signals)
    
    result = bt.run(df, strategy)
    
    assert result['total_return'] > 0
    assert result['total_trades'] == 1
    assert result['trades'][0]['type'] == 'Short'


def test_stop_loss(sample_data):
    """ストップロスのテスト"""
    bt = Backtester(initial_capital=10000, commission=0.0)
    
    # 急落するデータ
    dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
    prices = [100, 100, 90, 80, 70, 60, 50, 40, 30, 20]
    df = pd.DataFrame({
        'Open': prices, 'High': prices, 'Low': prices, 'Close': prices
    }, index=dates)
    
    signals = [0] * 10
    signals[0] = 1 # 1日目に買いシグナル -> 2日目Open(100)で約定
    
    strategy = MockStrategy(signals)
    
    # ストップロス 5%
    result = bt.run(df, strategy, stop_loss=0.05)
    
    assert len(result['trades']) == 1
    assert result['trades'][0]['reason'] == 'Stop Loss'
    # 100で買って95以下になったら売るはず
    # 3日目のLowが90なので、ここで引っかかる


def test_take_profit(sample_data):
    """利確のテスト"""
    bt = Backtester(initial_capital=10000, commission=0.0)
    
    # 急騰するデータ
    dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
    prices = [100, 100, 110, 120, 130, 140, 150, 160, 170, 180]
    df = pd.DataFrame({
        'Open': prices, 'High': prices, 'Low': prices, 'Close': prices
    }, index=dates)
    
    signals = [0] * 10
    signals[0] = 1
    
    strategy = MockStrategy(signals)
    
    # 利確 10%
    result = bt.run(df, strategy, take_profit=0.1)
    
    assert len(result['trades']) == 1
    assert result['trades'][0]['reason'] == 'Take Profit'


def test_trailing_stop(sample_data):
    """トレーリングストップのテスト"""
    bt = Backtester(initial_capital=10000, commission=0.0)
    
    # 上がってから下がるデータ
    dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
    prices = [100, 110, 120, 115, 110, 105, 100, 90, 80, 70]
    df = pd.DataFrame({
        'Open': prices, 'High': prices, 'Low': prices, 'Close': prices
    }, index=dates)
    
    signals = [0] * 10
    signals[0] = 1
    
    strategy = MockStrategy(signals)
    
    # トレーリングストップ 5%
    # 120まで上がった後、120 * 0.95 = 114 を割ったら売り
    result = bt.run(df, strategy, trailing_stop=0.05)
    
    assert len(result['trades']) == 1
    assert result['trades'][0]['reason'] == 'Trailing Stop'
    assert result['trades'][0]['exit_price'] > 100 # 利益が出ているはず


def test_multi_asset(sample_data):
    """複数銘柄のテスト"""
    bt = Backtester(initial_capital=20000)
    
    data_map = {
        'Asset1': sample_data,
        'Asset2': sample_data.copy()
    }
    
    signals = [0] * 100
    signals[0] = 1
    signals[-2] = -1
    
    strategy_map = {
        'Asset1': MockStrategy(signals),
        'Asset2': MockStrategy(signals)
    }
    
    result = bt.run(data_map, strategy_map)
    
    assert result['total_trades'] == 2
    assert isinstance(result['signals'], dict)


def test_empty_data():
    """空データのテスト"""
    bt = Backtester()
    assert bt.run(pd.DataFrame(), MockStrategy([])) is None
    assert bt.run(None, MockStrategy([])) is None


def test_order_object_market(sample_data):
    """Orderオブジェクト（成行）のテスト"""
    bt = Backtester(initial_capital=10000)
    
    # Orderオブジェクトを生成する戦略
    class OrderStrategy(Strategy):
        def __init__(self, name="OrderStrategy"):
            super().__init__(name=name)
            
        def generate_signals(self, data):
            signals = pd.Series([None] * len(data), index=data.index)
            # 1日目に買い注文
            signals.iloc[0] = Order(ticker="Asset", action="BUY", quantity=10, type=OrderType.MARKET)
            # 最後から2日目に売り注文
            signals.iloc[-2] = Order(ticker="Asset", action="SELL", quantity=10, type=OrderType.MARKET)
            return signals
            
    result = bt.run(sample_data, OrderStrategy())
    
    assert result['total_trades'] == 1
    assert result['trades'][0]['type'] == 'Long'


def test_order_object_limit_buy(sample_data):
    """指値買い注文のテスト"""
    bt = Backtester(initial_capital=10000)
    
    # 100から始まって急落するデータ
    dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
    # 2日目に94まで下がるようにする
    prices = [100, 94, 90, 85, 80]
    df = pd.DataFrame({
        'Open': prices, 'High': prices, 'Low': prices, 'Close': prices
    }, index=dates)
    
    class LimitBuyStrategy(Strategy):
        def __init__(self, name="LimitBuyStrategy"):
            super().__init__(name=name)
            
        def generate_signals(self, data):
            signals = pd.Series([None] * len(data), index=data.index)
            # 95円で指値買い
            signals.iloc[0] = Order(ticker="Asset", action="BUY", quantity=10, type=OrderType.LIMIT, price=95.0)
            # 最後に売り
            signals.iloc[-2] = Order(ticker="Asset", action="SELL", quantity=10, type=OrderType.MARKET)
            return signals
            
    result = bt.run(df, LimitBuyStrategy())
    
    # 3日目(95)か4日目(90)で約定するはず
    assert len(result['trades']) == 1
    # 約定価格は指値以下
    assert result['trades'][0]['entry_price'] <= 95.0


def test_position_sizing_dict():
    """辞書によるポジションサイジングのテスト"""
    bt = Backtester(initial_capital=10000, position_size={'Asset1': 0.5, 'Asset2': 0.2})
    
    assert bt._size_position('Asset1', 10000, 100) == 50.0 # 5000 / 100
    assert bt._size_position('Asset2', 10000, 100) == 20.0 # 2000 / 100
    assert bt._size_position('Asset3', 10000, 100) == 0.0 # デフォルト0
