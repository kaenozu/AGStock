import os
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd

from src.live_trading import LiveTradingEngine, PaperBroker, Position
from src.strategies import Order, OrderType


class TestPaperBroker(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_paper_state.json"
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        self.broker = PaperBroker(initial_capital=100000, state_file=self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_initial_state(self):
        self.assertEqual(self.broker.cash, 100000)
        self.assertEqual(self.broker.positions, {})

    def test_buy_order(self):
        order = Order(ticker="TEST", action="BUY", quantity=10, type=OrderType.MARKET, price=0)
        self.broker.execute_order(order, current_price=100, timestamp=datetime.now())

        self.assertEqual(self.broker.cash, 99000)  # 100000 - (10 * 100)
        self.assertIn("TEST", self.broker.positions)
        self.assertEqual(self.broker.positions["TEST"].quantity, 10)
        self.assertEqual(self.broker.positions["TEST"].average_entry_price, 100)

    def test_sell_order(self):
        # Setup position
        self.broker.positions["TEST"] = Position("TEST", 10, 100, 100)
        self.broker.cash = 99000

        order = Order(ticker="TEST", action="SELL", quantity=5, type=OrderType.MARKET, price=0)
        self.broker.execute_order(order, current_price=110, timestamp=datetime.now())

        self.assertEqual(self.broker.cash, 99550)  # 99000 + (5 * 110)
        self.assertEqual(self.broker.positions["TEST"].quantity, 5)

    def test_persistence(self):
        self.broker.cash = 50000
        self.broker.save_state()

        new_broker = PaperBroker(state_file=self.test_file)
        self.assertEqual(new_broker.cash, 50000)


class TestLiveTradingEngine(unittest.TestCase):
    @patch("src.live_trading.LiveTradingEngine.fetch_realtime_data")
    def test_run_cycle(self, mock_fetch):
        # Mock data
        df = pd.DataFrame({"Close": [100, 101, 102]}, index=pd.date_range("2023-01-01", periods=3))
        mock_fetch.return_value = df

        # Mock strategy
        mock_strategy = MagicMock()
        mock_strategy.generate_signals.return_value = pd.Series([0, 0, 1])  # Buy signal at end

        broker = PaperBroker(state_file="test_engine_state.json")
        engine = LiveTradingEngine(broker, {"TEST": mock_strategy}, ["TEST"])

        engine.run_cycle()

        # Check if broker executed buy
        # Signal is 1 (BUY), default qty 10
        self.assertIn("TEST", broker.positions)
        self.assertEqual(broker.positions["TEST"].quantity, 10)

        if os.path.exists("test_engine_state.json"):
            os.remove("test_engine_state.json")

    def test_vix_fallback_sequence(self):
        """カスタムシンボル失敗時に^VIXへフォールバックし、さらにキャッシュを使う"""
        calls = []

        class FakeTicker:
            def __init__(self, symbol):
                calls.append(symbol)
                self.symbol = symbol

            def history(self, period, interval):
                if self.symbol == "CUSTOM":
                    return pd.DataFrame()  # simulate empty -> failure
                if self.symbol == "^VIX":
                    return pd.DataFrame({"Close": [12.3]})
                raise ValueError("unexpected symbol")

        with patch("src.live_trading.yf.Ticker", FakeTicker):
            broker = PaperBroker(state_file="test_engine_state.json")
            engine = LiveTradingEngine(broker, {}, [], vol_symbol="CUSTOM")
            vix = engine._get_vix_level()
            assert vix == 12.3
            assert calls == ["CUSTOM", "^VIX"]

            # Next call when providers fail should return cached last value
            def raising_history(self, period, interval):
                raise RuntimeError("fail")

            FakeTicker.history = raising_history
            vix_cached = engine._get_vix_level()
            assert vix_cached == 12.3

        if os.path.exists("test_engine_state.json"):
            os.remove("test_engine_state.json")


if __name__ == "__main__":
    unittest.main()
