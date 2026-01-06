"""
リスク・ガード (Risk Guard)
ブラックスワン検知と動的な損切り最適化
"""
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class RiskGuard:
    def __init__(self, v_threshold: float = 2.5):
        self.v_threshold = v_threshold  # 標準偏差の何倍を超えたら異常とするか

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