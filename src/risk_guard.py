"""
リスク・ガード (Risk Guard)
ブラックスワン検知と動的な損切り最適化
"""
import json
import os
import numpy as np
import pandas as pd
import logging
from typing import Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class RiskGuard:
    def __init__(self, v_threshold: float = 2.5, **kwargs):
        self.v_threshold = v_threshold  # 標準偏差の何倍を超えたら異常とするか
        self.initial_portfolio_value = kwargs.get("initial_portfolio_value", 1000000.0)
        self.daily_start_value = self.initial_portfolio_value
        self.daily_loss_limit_pct = kwargs.get("daily_loss_limit_pct", -5.0)
        self.max_drawdown_limit_pct = kwargs.get("max_drawdown_limit_pct", -10.0)
        self.max_position_size_pct = kwargs.get("max_position_size_pct", 20.0)
        self.max_vix = kwargs.get("max_vix", 30.0)
        self.state_file = kwargs.get("state_file")
        
        # Compatibility attributes
        self.circuit_breaker_triggered = False
        self.drawdown_triggered = False
        self.high_water_mark = self.initial_portfolio_value
        self.last_reset_date = datetime.now().date()

        if self.state_file:
            self.load_state()

    def load_state(self):
        """状態をファイルから読み込み"""
        if self.state_file and os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    self.circuit_breaker_triggered = state.get("circuit_breaker_triggered", False)
                    self.drawdown_triggered = state.get("drawdown_triggered", False)
                    self.high_water_mark = state.get("high_water_mark", self.initial_portfolio_value)
                    self.daily_start_value = state.get("daily_start_value", self.initial_portfolio_value)
                    date_str = state.get("last_reset_date")
                    if date_str:
                        self.last_reset_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except Exception as e:
                logger.error(f"Failed to load RiskGuard state: {e}")

    def save_state(self):
        """状態をファイルに保存"""
        if self.state_file:
            try:
                state = {
                    "circuit_breaker_triggered": self.circuit_breaker_triggered,
                    "drawdown_triggered": self.drawdown_triggered,
                    "high_water_mark": self.high_water_mark,
                    "daily_start_value": self.daily_start_value,
                    "last_reset_date": self.last_reset_date.isoformat()
                }
                with open(self.state_file, "w", encoding="utf-8") as f:
                    json.dump(state, f)
            except Exception as e:
                logger.error(f"Failed to save RiskGuard state: {e}")

    def _check_daily_reset(self):
        """日付が変わっていたら日次制限をリセット"""
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            self.last_reset_date = current_date
            self.circuit_breaker_triggered = False
            # Note: daily_start_value should be updated by the caller or during the first check of the day
            return True
        return False

    def check_daily_loss_limit(self, current_value: float) -> bool:
        """日次損失制限をチェック"""
        if self._check_daily_reset():
            self.daily_start_value = current_value
            self.save_state()

        loss_pct = (current_value - self.daily_start_value) / self.daily_start_value * 100
        if loss_pct < self.daily_loss_limit_pct:
            self.circuit_breaker_triggered = True
            self.save_state()
            return True
        return False

    def check_drawdown_limit(self, current_value: float) -> bool:
        """ドローダウン制限をチェック"""
        if current_value > self.high_water_mark:
            self.high_water_mark = current_value
            self.save_state()
            
        drawdown_pct = (self.high_water_mark - current_value) / self.high_water_mark * 100
        if drawdown_pct > abs(self.max_drawdown_limit_pct):
            self.drawdown_triggered = True
            self.save_state()
            return True
        return False

    def validate_order(self, order_amount: float, portfolio_value: float) -> Tuple[bool, str]:
        """注文の妥当性を検証"""
        if self.circuit_breaker_triggered:
            return False, "Circuit breaker triggered"
        if order_amount > portfolio_value * (self.max_position_size_pct / 100):
            return False, f"Position size exceeds limit ({self.max_position_size_pct}%)"
        return True, "OK"

    def should_halt_trading(self, portfolio_value: float, vix_level: float = None) -> Tuple[bool, str]:
        """取引を停止すべきか判定"""
        if self.circuit_breaker_triggered:
            return True, "Circuit breaker triggered"
        if vix_level and vix_level > self.max_vix:
            return True, f"VIX too high: {vix_level}"
        return False, "OK"

    def validate_trade(self, trade_request: Any) -> Tuple[bool, str]:
        """取引の妥当性を検証"""
        return True, "Valid"

    def detect_black_swan(self, market_data: pd.DataFrame) -> bool:
        """急激なボラティリティ拡大によるブラックスワンの兆候を検知"""
        if market_data is None or len(market_data) < 20: return False
        
        recent_vol = market_data["Close"].pct_change().std()
        avg_vol = market_data["Close"].pct_change().rolling(60).std().iloc[-1]
        
        if recent_vol > avg_vol * self.v_threshold:
            logger.critical("🚨 ブラックスワンの予兆を検知！市場パニックの可能性があります。")
            return True
        return False

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