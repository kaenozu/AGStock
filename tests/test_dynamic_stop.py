"""
DynamicStopManagerのテスト
"""
import pytest
import pandas as pd
import numpy as np
from src.dynamic_stop import DynamicStopManager


@pytest.fixture
def stop_manager():
    """DynamicStopManagerインスタンスを提供"""
    return DynamicStopManager(atr_period=14, atr_multiplier=2.0)


@pytest.fixture
def sample_price_data():
    """サンプルの価格データを提供"""
    dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
    np.random.seed(42)
    
    # ランダムウォークで価格を生成
    base_price = 100
    returns = np.random.randn(30) * 2
    prices = base_price + np.cumsum(returns)
    
    data = {
        'Open': prices * 0.99,
        'High': prices * 1.02,
        'Low': prices * 0.98,
        'Close': prices,
        'Volume': [1000000] * 30
    }
    df = pd.DataFrame(data, index=dates)
    return df


def test_init():
    """初期化のテスト"""
    manager = DynamicStopManager(atr_period=20, atr_multiplier=3.0)
    assert manager.atr_period == 20
    assert manager.atr_multiplier == 3.0
    assert manager.stops == {}
    assert manager.entry_prices == {}
    assert manager.highest_prices == {}


def test_register_entry_with_initial_stop(stop_manager):
    """エントリー登録：初期ストップ指定あり"""
    ticker = "AAPL"
    entry_price = 150.0
    initial_stop = 145.0
    
    stop_manager.register_entry(ticker, entry_price, initial_stop)
    
    assert stop_manager.entry_prices[ticker] == entry_price
    assert stop_manager.highest_prices[ticker] == entry_price
    assert stop_manager.stops[ticker] == initial_stop


def test_register_entry_without_initial_stop(stop_manager):
    """エントリー登録：初期ストップ指定なし（デフォルト5%）"""
    ticker = "AAPL"
    entry_price = 150.0
    
    stop_manager.register_entry(ticker, entry_price)
    
    assert stop_manager.entry_prices[ticker] == entry_price
    assert stop_manager.highest_prices[ticker] == entry_price
    assert stop_manager.stops[ticker] == entry_price * 0.95  # 5%下


def test_update_stop_price_increase(stop_manager, sample_price_data):
    """ストップ更新：価格上昇時"""
    ticker = "AAPL"
    entry_price = 100.0
    stop_manager.register_entry(ticker, entry_price)
    
    # 価格が上昇
    current_price = 110.0
    new_stop = stop_manager.update_stop(ticker, current_price, sample_price_data)
    
    # ストップが上昇していることを確認
    assert new_stop > entry_price * 0.95
    assert stop_manager.highest_prices[ticker] == current_price


def test_update_stop_price_decrease(stop_manager, sample_price_data):
    """ストップ更新：価格下落時（ストップは下がらない）"""
    ticker = "AAPL"
    entry_price = 100.0
    stop_manager.register_entry(ticker, entry_price)
    
    # 最初に価格上昇
    stop_manager.update_stop(ticker, 110.0, sample_price_data)
    first_stop = stop_manager.stops[ticker]
    
    # その後価格下落
    new_stop = stop_manager.update_stop(ticker, 105.0, sample_price_data)
    
    # ストップは下がらない
    assert new_stop == first_stop


def test_update_stop_profit_locking(stop_manager, sample_price_data):
    """ストップ更新：利益確定（5%以上の利益でブレークイーブンに移動）"""
    ticker = "AAPL"
    entry_price = 100.0
    stop_manager.register_entry(ticker, entry_price)
    
    # 5%以上の利益
    current_price = 106.0
    new_stop = stop_manager.update_stop(ticker, current_price, sample_price_data)
    
    # ストップがブレークイーブン以上に設定される
    breakeven_stop = entry_price * 1.005
    assert new_stop >= breakeven_stop


def test_update_stop_no_entry(stop_manager, sample_price_data):
    """ストップ更新：エントリー登録なし"""
    ticker = "AAPL"
    current_price = 100.0
    
    new_stop = stop_manager.update_stop(ticker, current_price, sample_price_data)
    
    # エントリーがないので0.0を返す
    assert new_stop == 0.0


def test_update_stop_with_atr_column(stop_manager):
    """ストップ更新：ATRカラムが既に存在する場合"""
    ticker = "AAPL"
    entry_price = 100.0
    stop_manager.register_entry(ticker, entry_price)
    
    # ATRカラム付きのデータフレーム
    dates = pd.date_range(start='2023-01-01', periods=20, freq='D')
    df = pd.DataFrame({
        'High': [105] * 20,
        'Low': [95] * 20,
        'Close': [100] * 20,
        'ATR': [3.0] * 20
    }, index=dates)
    
    current_price = 110.0
    new_stop = stop_manager.update_stop(ticker, current_price, df)
    
    # ATR=3.0, multiplier=2.0なので、stop = 110 - 3*2 = 104
    expected_stop = 110.0 - (3.0 * 2.0)
    assert abs(new_stop - expected_stop) < 0.1


def test_update_stop_insufficient_data(stop_manager):
    """ストップ更新：データ不足の場合"""
    ticker = "AAPL"
    entry_price = 100.0
    stop_manager.register_entry(ticker, entry_price)
    
    # データが少ない
    df = pd.DataFrame({
        'High': [105],
        'Low': [95],
        'Close': [100]
    })
    
    current_price = 110.0
    new_stop = stop_manager.update_stop(ticker, current_price, df)
    
    # ATRが計算できないので、パーセンテージベースのストップ（5%）
    expected_stop = 110.0 * 0.95
    assert abs(new_stop - expected_stop) < 0.1


def test_update_stop_none_dataframe(stop_manager):
    """ストップ更新：DataFrameがNoneの場合"""
    ticker = "AAPL"
    entry_price = 100.0
    stop_manager.register_entry(ticker, entry_price)
    
    current_price = 110.0
    new_stop = stop_manager.update_stop(ticker, current_price, None)
    
    # ATRが計算できないので、パーセンテージベースのストップ
    expected_stop = 110.0 * 0.95
    assert abs(new_stop - expected_stop) < 0.1


def test_check_exit_hit(stop_manager):
    """出口チェック：ストップロスヒット"""
    ticker = "AAPL"
    entry_price = 100.0
    stop_manager.register_entry(ticker, entry_price, initial_stop=95.0)
    
    current_price = 94.0
    should_exit, reason = stop_manager.check_exit(ticker, current_price)
    
    assert should_exit is True
    assert "Stop Loss Hit" in reason


def test_check_exit_not_hit(stop_manager):
    """出口チェック：ストップロスヒットせず"""
    ticker = "AAPL"
    entry_price = 100.0
    stop_manager.register_entry(ticker, entry_price, initial_stop=95.0)
    
    current_price = 96.0
    should_exit, reason = stop_manager.check_exit(ticker, current_price)
    
    assert should_exit is False
    assert reason == ""


def test_check_exit_no_stop(stop_manager):
    """出口チェック：ストップが設定されていない"""
    ticker = "AAPL"
    current_price = 100.0
    
    should_exit, reason = stop_manager.check_exit(ticker, current_price)
    
    assert should_exit is False
    assert reason == ""


def test_multiple_positions(stop_manager, sample_price_data):
    """複数ポジションの管理"""
    tickers = ["AAPL", "GOOGL", "MSFT"]
    entry_prices = [150.0, 2800.0, 300.0]
    
    # 複数のポジションを登録
    for ticker, entry_price in zip(tickers, entry_prices):
        stop_manager.register_entry(ticker, entry_price)
    
    # それぞれのストップを更新
    current_prices = [160.0, 2900.0, 310.0]
    for ticker, current_price in zip(tickers, current_prices):
        stop_manager.update_stop(ticker, current_price, sample_price_data)
    
    # すべてのポジションが管理されていることを確認
    assert len(stop_manager.stops) == 3
    assert len(stop_manager.entry_prices) == 3
    assert len(stop_manager.highest_prices) == 3


def test_trailing_stop_behavior(stop_manager, sample_price_data):
    """トレーリングストップの動作確認"""
    ticker = "AAPL"
    entry_price = 100.0
    stop_manager.register_entry(ticker, entry_price)
    
    # 価格が段階的に上昇
    prices = [105, 110, 115, 120]
    stops = []
    
    for price in prices:
        stop = stop_manager.update_stop(ticker, price, sample_price_data)
        stops.append(stop)
    
    # ストップが段階的に上昇していることを確認
    for i in range(1, len(stops)):
        assert stops[i] >= stops[i-1]
    
    # 最終的なストップが初期ストップより高い
    assert stops[-1] > entry_price * 0.95
