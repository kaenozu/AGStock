import logging
import json
import os
from typing import Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class RiskGuard:
    """
    Safety mechanism to prevent catastrophic losses in live trading.
    Persists state to ensure risk limits are enforced across restarts.
    """
    def __init__(
        self,
        initial_portfolio_value: float,
        daily_loss_limit_pct: float = -5.0,
        max_position_size_pct: float = 10.0,
        max_vix: float = 40.0,
        max_drawdown_limit_pct: float = -20.0,
        state_file: str = "risk_state.json"
    ):
        # Risk parameters
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.max_position_size_pct = max_position_size_pct
        self.max_vix = max_vix
        self.max_drawdown_limit_pct = max_drawdown_limit_pct
        self.state_file = state_file

        # State variables
        self.daily_start_value = initial_portfolio_value
        self.last_reset_date = datetime.now().date()
        self.circuit_breaker_triggered = False
        self.high_water_mark = initial_portfolio_value
        self.drawdown_triggered = False

        # Load state if exists
        self.load_state()

        # If loading for the first time or after reset, ensure high_water_mark is at least initial
        if self.high_water_mark < initial_portfolio_value:
            self.high_water_mark = initial_portfolio_value

    def _get_state_data(self) -> dict:
        """現在の状態データを取得"""
        return {
            'daily_start_value': self.daily_start_value,
            'last_reset_date': self.last_reset_date.strftime('%Y-%m-%d'),
            'circuit_breaker_triggered': self.circuit_breaker_triggered,
            'high_water_mark': self.high_water_mark,
            'drawdown_triggered': self.drawdown_triggered
        }

    def load_state(self):
        """Load risk state from file."""
        if not os.path.exists(self.state_file):
            return

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # Load state values with defaults
            self.daily_start_value = state.get('daily_start_value', self.daily_start_value)

            last_date_str = state.get('last_reset_date')
            if last_date_str:
                self.last_reset_date = datetime.strptime(last_date_str, '%Y-%m-%d').date()

            self.circuit_breaker_triggered = state.get('circuit_breaker_triggered', False)
            self.high_water_mark = state.get('high_water_mark', self.high_water_mark)
            self.drawdown_triggered = state.get('drawdown_triggered', False)

            logger.info(f"Risk state loaded. Daily Start: {self.daily_start_value}, HWM: {self.high_water_mark}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse risk state file {self.state_file}: {e}")
            from .errors import RiskManagementError
            raise RiskManagementError(
                message=f"Failed to parse risk state file: {self.state_file}",
                risk_type="STATE_LOAD_ERROR",
                details={"file_path": self.state_file, "original_error": str(e)}
            ) from e
        except Exception as e:
            logger.error(f"Failed to load risk state: {e}")
            from .errors import RiskManagementError
            raise RiskManagementError(
                message="Failed to load risk state",
                risk_type="STATE_LOAD_ERROR",
                details={"file_path": self.state_file, "original_error": str(e)}
            ) from e

    def save_state(self):
        """Save risk state to file."""
        try:
            state = self._get_state_data()
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save risk state: {e}")
            from .errors import RiskManagementError
            raise RiskManagementError(
                message="Failed to save risk state",
                risk_type="STATE_SAVE_ERROR",
                details={"file_path": self.state_file, "original_error": str(e)}
            ) from e

    def reset_daily_tracking(self, current_value: float):
        """Reset daily tracking at market open."""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_start_value = current_value
            self.last_reset_date = today
            self.circuit_breaker_triggered = False  # Reset daily circuit breaker
            # Note: drawdown_triggered is NOT reset daily
            
            self.save_state()
            logger.info(f"Daily tracking reset. Starting value: ${current_value:,.2f}")
    
    def check_daily_loss_limit(self, current_value: float) -> bool:
        """
        Check if daily loss limit has been breached.
        Returns True if trading should be halted.
        """
        self.reset_daily_tracking(current_value)
        
        daily_pnl_pct = ((current_value - self.daily_start_value) / self.daily_start_value) * 100
        
        if daily_pnl_pct <= self.daily_loss_limit_pct:
            if not self.circuit_breaker_triggered:
                logger.critical(f"🚨 DAILY LOSS LIMIT BREACHED: {daily_pnl_pct:.2f}% (Limit: {self.daily_loss_limit_pct}%)")
                self.circuit_breaker_triggered = True
                self.save_state()
            return True
        
        return False
    
    def check_drawdown_limit(self, current_value: float) -> bool:
        """
        Check if max drawdown limit has been breached.
        Returns True if trading should be halted.
        """
        # Update High Water Mark
        if current_value > self.high_water_mark:
            self.high_water_mark = current_value
            self.save_state()
            
        drawdown_pct = ((current_value - self.high_water_mark) / self.high_water_mark) * 100
        
        if drawdown_pct <= self.max_drawdown_limit_pct:
            if not self.drawdown_triggered:
                logger.critical(f"🚨 MAX DRAWDOWN LIMIT BREACHED: {drawdown_pct:.2f}% (Limit: {self.max_drawdown_limit_pct}%)")
                self.drawdown_triggered = True
                self.save_state()
            return True
            
        return False
    
    def check_position_size(self, order_value: float, portfolio_value: float) -> bool:
        """
        Check if order size exceeds maximum position size.
        Returns True if order should be rejected.
        """
        position_pct = (order_value / portfolio_value) * 100
        
        if position_pct > self.max_position_size_pct:
            logger.warning(f"⚠️ Position size {position_pct:.2f}% exceeds limit {self.max_position_size_pct}%")
            return True
        
        return False
    
    def check_volatility(self, vix_level: Optional[float]) -> bool:
        """
        Check if market volatility is too high.
        Returns True if trading should be halted.
        """
        if vix_level is None:
            return False
        
        if vix_level > self.max_vix:
            logger.warning(f"⚠️ VIX {vix_level:.2f} exceeds limit {self.max_vix}")
            return True
        
        return False
    
    def should_halt_trading(
        self,
        current_portfolio_value: float,
        vix_level: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Comprehensive check of all risk limits.
        Returns (should_halt, reason)
        """
        # Check daily loss
        if self.check_daily_loss_limit(current_portfolio_value):
            return True, f"Daily loss limit breached ({self.daily_loss_limit_pct}%)"
            
        # Check max drawdown
        if self.check_drawdown_limit(current_portfolio_value):
            return True, f"Max drawdown limit breached ({self.max_drawdown_limit_pct}%)"
        
        # Check volatility
        if self.check_volatility(vix_level):
            return True, f"VIX too high ({vix_level:.2f} > {self.max_vix})"
        
        return False, ""
    
    def validate_order(
        self,
        order_value: float,
        portfolio_value: float
    ) -> Tuple[bool, str]:
        """
        Validate if an order is safe to execute.
        Returns (is_valid, reason)
        """
        if self.circuit_breaker_triggered:
            return False, "Circuit breaker triggered - trading halted for today"
            
        if self.drawdown_triggered:
            return False, "Max drawdown limit breached - trading halted indefinitely"
        
        if self.check_position_size(order_value, portfolio_value):
            return False, f"Position size exceeds {self.max_position_size_pct}% limit"
        
        return True, ""
