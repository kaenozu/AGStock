"""
リスク・ガード (Risk Guard)
ブラックスワン検知と動的な損切り最適化
"""
import numpy as np
import pandas as pd
import logging
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

    def detect_black_swan(self, market_data: pd.DataFrame) -> bool:
        """急激なボラティリティ拡大によるブラックスワンの兆候を検知"""
        if market_data is None or len(market_data) < 20: return False
        
        recent_vol = market_data["Close"].pct_change().std()
        avg_vol = market_data["Close"].pct_change().rolling(60).std().iloc[-1]
        
        if recent_vol > avg_vol * self.v_threshold:
            logger.critical("🚨 ブラックスワンの予兆を検知！市場パニックの可能性があります。")
            return True
        return False

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

    def check_portfolio_health(self, holdings: list) -> str:
        """ポートフォリオ全体の健康診断"""
        if not holdings: return "Healthy (No positions)"
        # 銘柄間の相関チェックなどのロジック（簡略化）
        return "Stable"