import json
import logging
import os
from datetime import datetime
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class RiskGuard:
    def __init__(
        self,
        initial_portfolio_value: float,
        daily_loss_limit_pct: float = -5.0,
        max_position_size_pct: float = 10.0,
        max_vix: float = 40.0,
        max_drawdown_limit_pct: float = -20.0,
        max_latency_ms: float = 1000.0,
        max_slippage_pct: float = 1.5,
        max_consecutive_losses: int = 5,
        state_file: str = 'data/risk_state.json',
    ):
        self.initial_portfolio_value = initial_portfolio_value
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.max_position_size_pct = max_position_size_pct
        self.max_vix = max_vix
        self.max_drawdown_limit_pct = max_drawdown_limit_pct
        self.max_latency_ms = max_latency_ms
        self.max_slippage_pct = max_slippage_pct
        self.max_consecutive_losses = max_consecutive_losses
        self.state_file = state_file

        # State variables
        self.daily_start_value = initial_portfolio_value
        self.last_reset_date = datetime.now().date()
        self.circuit_breaker_triggered = False
        self.drawdown_triggered = False
        self.high_water_mark = initial_portfolio_value
        self.consecutive_losses = 0

        self.load_state()
        self._reset_daily_stats_if_needed(initial_portfolio_value)

    def _reset_daily_stats_if_needed(self, current_portfolio_value: float):
        today = datetime.now().date()
        if today > self.last_reset_date:
            self.last_reset_date = today
            self.daily_start_value = current_portfolio_value
            self.circuit_breaker_triggered = False
            self.save_state()

    def check_daily_loss_limit(self, current_portfolio_value: float) -> bool:
        daily_pnl_pct = ((current_portfolio_value - self.daily_start_value) / self.daily_start_value) * 100
        if daily_pnl_pct < self.daily_loss_limit_pct:
            self.circuit_breaker_triggered = True
            self.save_state()
            return True
        return False

    def check_drawdown_limit(self, current_portfolio_value: float) -> bool:
        if current_portfolio_value > self.high_water_mark:
            self.high_water_mark = current_portfolio_value
            self.save_state()

        drawdown_pct = ((current_portfolio_value - self.high_water_mark) / self.high_water_mark) * 100
        if drawdown_pct < self.max_drawdown_limit_pct:
            self.drawdown_triggered = True
            self.save_state()
            return True
        return False

    def check_position_size(self, order_value: float, portfolio_value: float) -> bool:
        position_size_pct = (order_value / portfolio_value) * 100
        return position_size_pct > self.max_position_size_pct

    def check_operational_health(self, latency_ms: Optional[float], slippage_pct: Optional[float]) -> Tuple[bool, str]:
        if latency_ms is not None and latency_ms > self.max_latency_ms:
            return True, f'Latency too high: {latency_ms:.0f}ms > {self.max_latency_ms}ms'
        if slippage_pct is not None and slippage_pct > self.max_slippage_pct:
            return True, f'Slippage too high: {slippage_pct:.2f}% > {self.max_slippage_pct}%'
        if self.consecutive_losses >= self.max_consecutive_losses > 0:
            return True, f'Too many consecutive losses: {self.consecutive_losses} >= {self.max_consecutive_losses}'
        return False, ''

    def check_volatility(self, vix_level: Optional[float]) -> bool:
        if vix_level is None:
            return False
        if vix_level > self.max_vix:
            logger.warning(f' VIX {vix_level:.2f} exceeds limit {self.max_vix}')
            return True
        return False

    def should_halt_trading(
        self,
        current_portfolio_value: float,
        vix_level: Optional[float] = None,
        latency_ms: Optional[float] = None,
        slippage_pct: Optional[float] = None,
        consecutive_losses: Optional[int] = None,
    ) -> Tuple[bool, str]:
        if consecutive_losses is not None:
            self.consecutive_losses = consecutive_losses
            self.save_state()
        if self.check_daily_loss_limit(current_portfolio_value):
            return True, f'Daily loss limit breached ({self.daily_loss_limit_pct}%)'
        if self.check_drawdown_limit(current_portfolio_value):
            return True, f'Max drawdown limit breached ({self.max_drawdown_limit_pct}%)'
        if self.check_volatility(vix_level):
            return True, f'VIX too high ({vix_level:.2f} > {self.max_vix})'
        should_stop, reason = self.check_operational_health(latency_ms, slippage_pct)
        if should_stop:
            return True, reason
        return False, ''

    def validate_order(self, order_value: float, portfolio_value: float) -> Tuple[bool, str]:
        if self.circuit_breaker_triggered:
            return False, 'Circuit breaker triggered - trading halted for today'
        if self.drawdown_triggered:
            return False, 'Max drawdown limit breached - trading halted indefinitely'
        if self.check_position_size(order_value, portfolio_value):
            return False, f'Position size exceeds {self.max_position_size_pct}% limit'
        return True, ''

    def save_state(self):
        try:
            state = {
                'daily_start_value': self.daily_start_value,
                'last_reset_date': self.last_reset_date.strftime('%Y-%m-%d'),
                'circuit_breaker_triggered': self.circuit_breaker_triggered,
                'drawdown_triggered': self.drawdown_triggered,
                'high_water_mark': self.high_water_mark,
                'consecutive_losses': self.consecutive_losses,
            }
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            logger.error(f'Failed to save risk state: {e}')

    def load_state(self):
        if not os.path.exists(self.state_file):
            return
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            self.daily_start_value = state.get('daily_start_value', self.daily_start_value)
            last_date_str = state.get('last_reset_date')
            if last_date_str:
                self.last_reset_date = datetime.strptime(last_date_str, '%Y-%m-%d').date()
            self.circuit_breaker_triggered = state.get('circuit_breaker_triggered', False)
            self.drawdown_triggered = state.get('drawdown_triggered', False)
            self.high_water_mark = state.get('high_water_mark', self.high_water_mark)
            self.consecutive_losses = state.get('consecutive_losses', 0)
        except json.JSONDecodeError as e:
            logger.error(f'Failed to parse risk state file {self.state_file}: {e}')

