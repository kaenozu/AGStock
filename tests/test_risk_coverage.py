import json
import os
import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, mock_open, patch

from src.risk_guard import RiskGuard
from src.risk_limiter import RiskLimiter


class TestRiskGuard(unittest.TestCase):
    def setUp(self):
        self.state_file = "test_risk_state.json"
        self.patcher_open = patch("builtins.open", new_callable=mock_open)
        self.mock_open = self.patcher_open.start()

        self.patcher_exists = patch("os.path.exists")
        self.mock_exists = self.patcher_exists.start()

        # Default behavior: file does not exist
        self.mock_exists.return_value = False

    def tearDown(self):
        self.patcher_open.stop()
        self.patcher_exists.stop()

    def test_init_creates_default_state(self):
        rg = RiskGuard(initial_portfolio_value=1000000, state_file=self.state_file)
        self.assertEqual(rg.daily_start_value, 1000000)
        self.assertEqual(rg.high_water_mark, 1000000)
        self.assertFalse(rg.circuit_breaker_triggered)

    def test_check_daily_loss_limit(self):
        rg = RiskGuard(initial_portfolio_value=1000000, daily_loss_limit_pct=-5.0, state_file=self.state_file)

        # 4% loss - OK
        should_halt = rg.check_daily_loss_limit(960000)
        self.assertFalse(should_halt)

        # 6% loss - Breach
        should_halt = rg.check_daily_loss_limit(940000)
        self.assertTrue(should_halt)
        self.assertTrue(rg.circuit_breaker_triggered)

    def test_check_drawdown_limit(self):
        rg = RiskGuard(initial_portfolio_value=1000000, max_drawdown_limit_pct=-10.0, state_file=self.state_file)

        # Loss compared to HWM (1M) is small
        should_halt = rg.check_drawdown_limit(950000)
        self.assertFalse(should_halt)

        # New HWM
        should_halt = rg.check_drawdown_limit(1100000)
        self.assertEqual(rg.high_water_mark, 1100000)
        self.assertFalse(should_halt)

        # 15% drop from new HWM (1.1M * 0.85 = 935k)
        # 1.1M -> 900k is > 10% drop
        should_halt = rg.check_drawdown_limit(900000)
        self.assertTrue(should_halt)
        self.assertTrue(rg.drawdown_triggered)

    def test_validate_order_halts_on_trigger(self):
        rg = RiskGuard(initial_portfolio_value=1000000, state_file=self.state_file)
        rg.circuit_breaker_triggered = True

        is_valid, reason = rg.validate_order(10000, 1000000)
        self.assertFalse(is_valid)
        self.assertIn("Circuit breaker", reason)


class TestRiskLimiter(unittest.TestCase):
    def setUp(self):
        self.config = {
            "risk_limits": {
                "max_position_size": 0.2,  # Matches src/risk_limiter.py
                "max_daily_trades": 10,
                "max_daily_loss_pct": -5.0,  # Matches src/risk_limiter.py
                "max_total_exposure": 0.8,  # Matches src/risk_limiter.py
                "min_cash_reserve": 0.1,  # Matches src/risk_limiter.py
                "emergency_stop_loss_pct": -15.0,  # Matches src/risk_limiter.py
            }
        }

    def test_init_loads_config(self):
        with patch("builtins.open", mock_open(read_data=json.dumps(self.config))), patch(
            "os.path.exists", return_value=True
        ):
            rl = RiskLimiter("config.json")
            self.assertEqual(rl.risk_limits["max_position_size"], 0.2)

    def test_validate_trade(self):
        with patch("builtins.open", mock_open(read_data=json.dumps(self.config))), patch(
            "os.path.exists", return_value=True
        ):

            rl = RiskLimiter()

            # Valid trade
            trade_info = {"position_value": 10000, "ticker": "1234"}
            portfolio_state = {
                "total_equity": 100000,
                "invested_amount": 50000,
                "cash": 50000,
                "daily_pnl_pct": 0.0,
                "daily_trades": 0,
                "total_pnl_pct": 0.0,
            }

            is_valid, reasons = rl.validate_trade(trade_info, portfolio_state)

            # Debug failure by printing reasons
            failed_reasons = [r for r in reasons if r != "OK"]
            self.assertEqual(failed_reasons, [], msg=f"Validation failed with: {failed_reasons}")

            self.assertTrue(is_valid)

            # Invalid trade (too large)
            trade_info_large = {"position_value": 50000, "ticker": "1234"}  # 50% > 20%
            is_valid, reasons = rl.validate_trade(trade_info_large, portfolio_state)
            self.assertFalse(is_valid)
            # Check for Japanese error message or generic failure
            self.assertTrue(any("ポジションサイズ" in r for r in reasons))


if __name__ == "__main__":
    unittest.main()
