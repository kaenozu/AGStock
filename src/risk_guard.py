import json
import logging
<<<<<<< HEAD
import os
from datetime import datetime
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

=======
import datetime

logger = logging.getLogger(__name__)

class RiskGuard:
    def __init__(self, config: dict = None, v_threshold: float = 2.5, **kwargs):
        self.config = config or {}
        self.v_threshold = v_threshold  # 標準偏差の何倍を超えたら異常とするか
        self.initial_portfolio_value = kwargs.get("initial_portfolio_value", 1000000.0)
        self.daily_start_value = self.initial_portfolio_value
        self.high_water_mark = self.initial_portfolio_value
        self.daily_loss_limit_pct = kwargs.get("daily_loss_limit_pct", -5.0)
        self.max_drawdown_limit_pct = kwargs.get("max_drawdown_limit_pct", -10.0)
        self.max_position_size_pct = kwargs.get("max_position_size_pct", 20.0)
        self.max_vix = kwargs.get("max_vix", 30.0)
        self.state_file = kwargs.get("state_file", None)
        self.circuit_breaker_triggered = False
        self.drawdown_triggered = False
        self.last_reset_date = datetime.date.today()

    def validate_trade(self, trade_request: dict) -> tuple:
        """取引の妥当性を検証"""
        # 簡易実装
        return True, "Valid"

    def validate_order(self, amount: float, portfolio_value: float) -> tuple:
        """注文の妥当性を検証"""
        if self.circuit_breaker_triggered:
            return False, "Circuit breaker triggered"
        
        # ポジションサイズ制限のチェック
        if portfolio_value > 0:
            pos_size_pct = (amount / portfolio_value) * 100
            if pos_size_pct > self.max_position_size_pct:
                return False, f"Position size {pos_size_pct:.1f}% exceeds limit {self.max_position_size_pct:.1f}%"
        
        return True, "Valid"

    def check_daily_loss_limit(self, current_value: float) -> bool:
        """日次損失制限をチェック"""
        if self.daily_start_value <= 0: return False
        loss_pct = (current_value - self.daily_start_value) / self.daily_start_value * 100
        triggered = loss_pct <= self.daily_loss_limit_pct
        if triggered:
            self.circuit_breaker_triggered = True
            self.save_state()
        return triggered

    def check_drawdown_limit(self, current_value: float) -> bool:
        """ドローダウン制限をチェック"""
        if current_value > self.high_water_mark:
            self.high_water_mark = current_value
        if self.high_water_mark <= 0: return False
        dd_pct = (current_value - self.high_water_mark) / self.high_water_mark * 100
        triggered = dd_pct <= self.max_drawdown_limit_pct
        if triggered:
            self.circuit_breaker_triggered = True
            self.drawdown_triggered = True
            self.save_state()
        return triggered

    def should_halt_trading(self, current_value: float, vix_level: float = 0.0) -> tuple:
        """取引を停止すべきか判断"""
        if vix_level > self.max_vix:
            return True, f"VIX too high: {vix_level}"
        return False, "Safe"
>>>>>>> 9ead59c0c8153a0969ef2e94b492063a605db31f

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

<<<<<<< HEAD
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
=======
    def save_state(self):
        """状態を保存"""
        if not self.state_file: return
        import json
        state = {
            "circuit_breaker_triggered": self.circuit_breaker_triggered,
            "drawdown_triggered": self.drawdown_triggered,
            "high_water_mark": self.high_water_mark,
            "daily_start_value": self.daily_start_value,
            "last_reset_date": str(self.last_reset_date)
        }
        try:
            with open(self.state_file, "w") as f:
                json.dump(state, f)
        except Exception as e:
            logger.error(f"Error saving risk state: {e}")

    def load_state(self):
        """状態を復元"""
        if not self.state_file: return
        import json
        import os
        if not os.path.exists(self.state_file): return
        try:
            with open(self.state_file, "r") as f:
                state = json.load(f)
                self.circuit_breaker_triggered = state.get("circuit_breaker_triggered", False)
                self.drawdown_triggered = state.get("drawdown_triggered", False)
                self.high_water_mark = state.get("high_water_mark", self.initial_portfolio_value)
                self.daily_start_value = state.get("daily_start_value", self.initial_portfolio_value)
        except Exception as e:
            logger.error(f"Error loading risk state: {e}")

    def get_dynamic_stop_loss(self, ticker: str, volatility: float) -> float:
        """銘柄のボラティリティに合わせて最適な損切りラインを算出"""
        # 低ボラティリティならタイトに、高ボラティリティなら広めに（ただし最大7%）
        stop_pct = min(max(volatility * 2.0, 0.02), 0.07)
        return stop_pct
>>>>>>> 9ead59c0c8153a0969ef2e94b492063a605db31f

