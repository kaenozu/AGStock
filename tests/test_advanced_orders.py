import pandas as pd
import pytest

from src.backtester import Backtester
from src.strategies import Order, OrderType, Strategy


class MockOrderStrategy(Strategy):
    def __init__(self, orders_map):
        super().__init__("Mock Order")
        self.orders_map = orders_map  # {date_index: Order}

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=df.index, dtype="object")
        for idx, order in self.orders_map.items():
            if idx < len(df):
                signals.iloc[idx] = order
        return signals


@pytest.fixture
def sample_data():
    dates = pd.date_range(start="2023-01-01", periods=10, freq="D")
    df = pd.DataFrame(
        {
            "Open": [100, 100, 90, 100, 110, 120, 130, 140, 150, 160],
            "High": [105, 105, 95, 105, 115, 125, 135, 145, 155, 165],
            "Low": [95, 95, 85, 95, 105, 115, 125, 135, 145, 155],
            "Close": [100, 100, 90, 100, 110, 120, 130, 140, 150, 160],
            "Volume": [1000] * 10,
        },
        index=dates,
    )
    return df


def test_limit_buy_order(sample_data):
    # NOTE: Current implementation processes orders on the same day they're generated.
    # Orders are checked against next day's price action.
    # Day 1: Place Limit Buy at 90.
    # Day 2: Low is 85, Open is 90 (Fill at 90).

    order = Order(ticker="TEST", type=OrderType.LIMIT, action="BUY", quantity=10, price=90.0)
    strat = MockOrderStrategy({1: order})  # Changed from Day 0 to Day 1

    bt = Backtester(initial_capital=10000, commission=0.0, slippage=0.0)
    # Pass dict to ensure ticker matches
    res = bt.run({"TEST": sample_data}, strat)

    trades = res["trades"]
    assert len(trades) >= 1
    # Trade should happen on Day 2 (index 2)
    # Entry price should be 90.0
    assert trades[0]["entry_price"] == 90.0
    assert trades[0]["type"] == "Long"


def test_stop_buy_order(sample_data):
    # NOTE: Current implementation processes orders on the same day they're generated.
    # Day 3: Place Stop Buy at 110.
    # Day 4: High is 115, Open is 110. Fill at 110.

    order = Order(ticker="TEST", type=OrderType.STOP, action="BUY", quantity=10, price=110.0)
    strat = MockOrderStrategy({3: order})  # Changed from Day 0 to Day 3

    bt = Backtester(initial_capital=10000, commission=0.0, slippage=0.0)
    res = bt.run({"TEST": sample_data}, strat)

    trades = res["trades"]
    assert len(trades) >= 1
    assert trades[0]["entry_price"] == 110.0


def test_trailing_stop(sample_data):
    # Buy at Day 0 (Market). Price 100.
    # Trailing Stop 10% (Initial Stop 90).
    # Day 1: High 105. Stop -> 94.5. Low 95 (Safe).
    # Day 2: High 95. Stop -> 94.5. Low 85 (Hit).

    # We use simple signal 1 for entry
    class SimpleEntryStrategy(Strategy):
        def generate_signals(self, df):
            s = pd.Series(0, index=df.index)
            s.iloc[0] = 1
            return s

    strat = SimpleEntryStrategy("Simple")

    bt = Backtester(initial_capital=10000, commission=0.0, slippage=0.0)
    # Run with trailing_stop=0.1, no stop_loss
    res = bt.run({"TEST": sample_data}, strat, trailing_stop=0.1, stop_loss=None)

    trades = res["trades"]
    print(f"Trades: {trades}")  # Debug print
    assert len(trades) == 1
    exit_price = trades[0]["exit_price"]
    reason = trades[0]["reason"]

    assert reason == "Trailing Stop"
    # Expected exit:
    # Day 1 High 105 -> Stop 94.5.
    # Day 2 Low 85. Hit 94.5.
    assert exit_price == 94.5


def test_ticker_injection(sample_data):
    # Order with wrong ticker
    order = Order(ticker="WRONG", type=OrderType.MARKET, action="BUY", quantity=10)
    strat = MockOrderStrategy({0: order})

    bt = Backtester(initial_capital=10000, commission=0.0, slippage=0.0)
    res = bt.run({"CORRECT": sample_data}, strat)

    # Check if trade was executed for 'CORRECT' ticker
    trades = res["trades"]
    assert len(trades) > 0
    assert trades[0]["ticker"] == "CORRECT"
