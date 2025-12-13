import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd

from src.base import (BaseManager, BaseRiskManager, BaseStrategy, EventBus,
                      RiskMetrics, TradeSignal)


class TestTradeSignal(unittest.TestCase):
    """Tests for TradeSignal dataclass"""

    def test_trade_signal_creation(self):
        """Test creating a TradeSignal"""
        signal = TradeSignal(
            ticker="AAPL",
            action="BUY",
            quantity=100,
            price=150.0,
            confidence=0.85,
            timestamp=datetime.now(),
            reason="Strong uptrend",
        )

        self.assertEqual(signal.ticker, "AAPL")
        self.assertEqual(signal.action, "BUY")
        self.assertEqual(signal.quantity, 100)
        self.assertEqual(signal.confidence, 0.85)

    def test_trade_signal_with_metadata(self):
        """Test TradeSignal with metadata"""
        metadata = {"indicator": "RSI", "value": 75}
        signal = TradeSignal(
            ticker="GOOGL",
            action="SELL",
            quantity=50,
            price=2800.0,
            confidence=0.9,
            timestamp=datetime.now(),
            reason="Overbought",
            metadata=metadata,
        )

        self.assertEqual(signal.metadata["indicator"], "RSI")
        self.assertEqual(signal.metadata["value"], 75)


class TestRiskMetrics(unittest.TestCase):
    """Tests for RiskMetrics dataclass"""

    def test_risk_metrics_creation(self):
        """Test creating RiskMetrics"""
        metrics = RiskMetrics(
            volatility=0.25, max_drawdown=-0.15, sharpe_ratio=1.5, var_95=0.05, beta=1.2, timestamp=datetime.now()
        )

        self.assertEqual(metrics.volatility, 0.25)
        self.assertEqual(metrics.sharpe_ratio, 1.5)
        self.assertEqual(metrics.beta, 1.2)


class TestBaseManager(unittest.TestCase):
    """Tests for BaseManager abstract class"""

    def test_base_manager_initialization(self):
        """Test BaseManager with config"""

        class TestManager(BaseManager):
            def _initialize(self):
                pass

        config = {"key1": "value1", "key2": "value2"}
        manager = TestManager(config)

        self.assertEqual(manager.config, config)
        self.assertIsNotNone(manager.logger)

    def test_validate_config_success(self):
        """Test config validation passes"""

        class TestManager(BaseManager):
            def _initialize(self):
                pass

        manager = TestManager({"key1": "val1", "key2": "val2"})
        result = manager.validate_config(["key1", "key2"])

        self.assertTrue(result)

    def test_validate_config_failure(self):
        """Test config validation fails with missing keys"""

        class TestManager(BaseManager):
            def _initialize(self):
                pass

        manager = TestManager({"key1": "val1"})
        result = manager.validate_config(["key1", "key2", "key3"])

        self.assertFalse(result)


class TestBaseStrategy(unittest.TestCase):
    """Tests for BaseStrategy abstract class"""

    def test_base_strategy_initialization(self):
        """Test BaseStrategy initialization"""

        class TestStrategy(BaseStrategy):
            def generate_signals(self, data):
                return []

        params = {"period": 14, "threshold": 0.7}
        strategy = TestStrategy("TestStrat", params)

        self.assertEqual(strategy.name, "TestStrat")
        self.assertEqual(strategy.parameters, params)

    def test_validate_data_success(self):
        """Test data validation passes"""

        class TestStrategy(BaseStrategy):
            def generate_signals(self, data):
                return []

        strategy = TestStrategy("Test")
        df = pd.DataFrame({"Close": [100, 101], "Volume": [1000, 1100]})
        result = strategy.validate_data(df, ["Close", "Volume"])

        self.assertTrue(result)

    def test_validate_data_failure(self):
        """Test data validation fails with missing columns"""

        class TestStrategy(BaseStrategy):
            def generate_signals(self, data):
                return []

        strategy = TestStrategy("Test")
        df = pd.DataFrame({"Close": [100, 101]})
        result = strategy.validate_data(df, ["Close", "Volume", "Open"])

        self.assertFalse(result)


class TestBaseRiskManager(unittest.TestCase):
    """Tests for BaseRiskManager abstract class"""

    def test_base_risk_manager_initialization(self):
        """Test BaseRiskManager initialization"""

        class TestRiskManager(BaseRiskManager):
            def calculate_position_size(self, account_balance, signal):
                return 0

            def get_risk_metrics(self):
                return None

        manager = TestRiskManager(max_risk=0.03)

        self.assertEqual(manager.max_risk, 0.03)

    def test_validate_signal_success(self):
        """Test signal validation passes"""

        class TestRiskManager(BaseRiskManager):
            def calculate_position_size(self, account_balance, signal):
                return 0

            def get_risk_metrics(self):
                return None

        manager = TestRiskManager()
        signal = TradeSignal(
            ticker="AAPL",
            action="BUY",
            quantity=100,
            price=150.0,
            confidence=0.8,
            timestamp=datetime.now(),
            reason="Test",
        )

        result = manager.validate_signal(signal)
        self.assertTrue(result)

    def test_validate_signal_invalid_confidence(self):
        """Test signal validation fails with invalid confidence"""

        class TestRiskManager(BaseRiskManager):
            def calculate_position_size(self, account_balance, signal):
                return 0

            def get_risk_metrics(self):
                return None

        manager = TestRiskManager()
        signal = TradeSignal(
            ticker="AAPL",
            action="BUY",
            quantity=100,
            price=150.0,
            confidence=1.5,  # Invalid
            timestamp=datetime.now(),
            reason="Test",
        )

        result = manager.validate_signal(signal)
        self.assertFalse(result)

    def test_validate_signal_invalid_action(self):
        """Test signal validation fails with invalid action"""

        class TestRiskManager(BaseRiskManager):
            def calculate_position_size(self, account_balance, signal):
                return 0

            def get_risk_metrics(self):
                return None

        manager = TestRiskManager()
        signal = TradeSignal(
            ticker="AAPL",
            action="INVALID",  # Invalid
            quantity=100,
            price=150.0,
            confidence=0.8,
            timestamp=datetime.now(),
            reason="Test",
        )

        result = manager.validate_signal(signal)
        self.assertFalse(result)


class TestEventBus(unittest.TestCase):
    """Tests for EventBus class"""

    def test_eventbus_initialization(self):
        """Test EventBus initialization"""
        bus = EventBus()
        self.assertEqual(bus._subscribers, {})

    def test_subscribe_and_publish(self):
        """Test subscribing to and publishing events"""
        bus = EventBus()
        callback_data = []

        def callback(data):
            callback_data.append(data)

        bus.subscribe("test_event", callback)
        bus.publish("test_event", "test_data")

        self.assertEqual(callback_data, ["test_data"])

    def test_multiple_subscribers(self):
        """Test multiple subscribers to same event"""
        bus = EventBus()
        results1 = []
        results2 = []

        bus.subscribe("event", lambda d: results1.append(d))
        bus.subscribe("event", lambda d: results2.append(d))

        bus.publish("event", "data")

        self.assertEqual(results1, ["data"])
        self.assertEqual(results2, ["data"])

    def test_unsubscribe(self):
        """Test unsubscribing from events"""
        bus = EventBus()
        results = []

        def callback(data):
            results.append(data)

        bus.subscribe("event", callback)
        bus.publish("event", "data1")

        bus.unsubscribe("event", callback)
        bus.publish("event", "data2")

        # Should only have data1, not data2
        self.assertEqual(results, ["data1"])

    def test_publish_exception_handling(self):
        """Test event bus handles callback exceptions"""
        bus = EventBus()

        def bad_callback(data):
            raise Exception("Test error")

        bus.subscribe("event", bad_callback)
        # Should not raise, just log error
        bus.publish("event", "data")


if __name__ == "__main__":
    unittest.main()
