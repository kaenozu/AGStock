import json
import os
from datetime import date, datetime
from unittest.mock import patch

from src.risk_guard import RiskGuard


class TestRiskGuard:

    TEST_STATE_FILE = "test_risk_state.json"

    def setup_method(self):
        if os.path.exists(self.TEST_STATE_FILE):
            os.remove(self.TEST_STATE_FILE)

    def teardown_method(self):
        if os.path.exists(self.TEST_STATE_FILE):
            os.remove(self.TEST_STATE_FILE)

    def test_initialization(self):
        rg = RiskGuard(initial_portfolio_value=100000.0, state_file=self.TEST_STATE_FILE)
        assert rg.daily_start_value == 100000.0
        assert rg.daily_loss_limit_pct == -5.0
        assert rg.circuit_breaker_triggered == False
        assert rg.high_water_mark == 100000.0

    def test_daily_loss_limit_breach(self):
        rg = RiskGuard(initial_portfolio_value=100000.0, daily_loss_limit_pct=-5.0, state_file=self.TEST_STATE_FILE)

        # -4% loss -> OK
        should_halt = rg.check_daily_loss_limit(96000.0)
        assert should_halt == False
        assert rg.circuit_breaker_triggered == False

        # -5.1% loss -> Halt
        should_halt = rg.check_daily_loss_limit(94900.0)
        assert should_halt == True
        assert rg.circuit_breaker_triggered == True

        # Verify persistence
        with open(self.TEST_STATE_FILE, "r") as f:
            state = json.load(f)
            assert state["circuit_breaker_triggered"] == True

    def test_drawdown_limit(self):
        rg = RiskGuard(initial_portfolio_value=100000.0, max_drawdown_limit_pct=-10.0, state_file=self.TEST_STATE_FILE)

        # Increase value -> Update HWM
        rg.check_drawdown_limit(110000.0)
        assert rg.high_water_mark == 110000.0

        # Drop to 100000 (-9.09% from HWM) -> OK
        should_halt = rg.check_drawdown_limit(100000.0)
        assert should_halt == False

        # Drop to 98000 (-10.9% from HWM) -> Halt
        should_halt = rg.check_drawdown_limit(98000.0)
        assert should_halt == True
        assert rg.drawdown_triggered == True

    def test_persistence(self):
        # 1. Create instance and trigger circuit breaker
        rg1 = RiskGuard(initial_portfolio_value=100000.0, daily_loss_limit_pct=-5.0, state_file=self.TEST_STATE_FILE)
        rg1.check_daily_loss_limit(94000.0)  # Trigger
        assert rg1.circuit_breaker_triggered == True

        # 2. Create new instance (simulate restart)
        rg2 = RiskGuard(initial_portfolio_value=100000.0, daily_loss_limit_pct=-5.0, state_file=self.TEST_STATE_FILE)

        # 3. Verify state is restored
        assert rg2.circuit_breaker_triggered == True
        assert rg2.daily_start_value == 100000.0

        # 4. Verify validation fails due to restored state
        is_valid, msg = rg2.validate_order(1000.0, 94000.0)
        assert is_valid == False
        assert "Circuit breaker triggered" in msg

    def test_daily_reset_logic(self):
        rg = RiskGuard(initial_portfolio_value=100000.0, state_file=self.TEST_STATE_FILE)

        # Mock datetime to simulate date change
        with patch("src.risk_guard.datetime") as mock_datetime:
            # Day 1
            mock_datetime.now.return_value.date.return_value = date(2025, 1, 1)
            mock_datetime.strptime = datetime.strptime  # Keep original strptime
            rg.last_reset_date = date(2025, 1, 1)

            # Check with current value (no change)
            rg.check_daily_loss_limit(100000.0)
            assert rg.daily_start_value == 100000.0

            # Day 2 (Date changed)
            mock_datetime.now.return_value.date.return_value = date(2025, 1, 2)

            # Check with new value -> should reset daily_start_value
            current_val = 105000.0
            rg.check_daily_loss_limit(current_val)

            assert rg.last_reset_date == date(2025, 1, 2)
            assert rg.daily_start_value == 105000.0

            # Verify persistence of new date
            with open(self.TEST_STATE_FILE, "r") as f:
                state = json.load(f)
                assert state["last_reset_date"] == "2025-01-02"
                assert state["daily_start_value"] == 105000.0

    def test_position_size_check(self):
        rg = RiskGuard(initial_portfolio_value=100000.0, max_position_size_pct=10.0, state_file=self.TEST_STATE_FILE)

        # 10% order -> OK
        is_valid, msg = rg.validate_order(10000.0, 100000.0)
        assert is_valid == True

        # 11% order -> Fail
        is_valid, msg = rg.validate_order(11000.0, 100000.0)
        assert is_valid == False
        assert "Position size exceeds" in msg

    def test_volatility_check(self):
        rg = RiskGuard(initial_portfolio_value=100000.0, max_vix=30.0)

        should_halt, msg = rg.should_halt_trading(100000.0, vix_level=25.0)
        assert should_halt == False

        should_halt, msg = rg.should_halt_trading(100000.0, vix_level=35.0)
        assert should_halt == True
        assert "VIX too high" in msg
