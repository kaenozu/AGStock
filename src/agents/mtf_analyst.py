"""
MTF Analyst Agent
Provides multi-timeframe analysis (Weekly vs Daily) to the Investment Committee.
Ensures 'Bird's Eye' trend alignment.
"""

import logging
from typing import Any, Dict

import pandas as pd

from src.agents.base_agent import BaseAgent
from src.multi_timeframe import MultiTimeframeAnalyzer
from src.schemas import AgentAnalysis, TradingDecision

logger = logging.getLogger(__name__)


class MTFAnalyst(BaseAgent):
    """
    Analyzes higher timeframe (Weekly) trends to filter lower timeframe (Daily) signals.
    """

    def __init__(self):
        super().__init__("MTFAnalyst", "🌐")
        self.mtf_analyzer = MultiTimeframeAnalyzer()

    def analyze(self, data: Dict[str, Any]) -> AgentAnalysis:
        """
        Performs Weekly trend analysis on the provided price history.
        """
        ticker = data.get("ticker", "Unknown")
        # Higher level committee might not always pass raw history, 
        # but for MTF it's required.
        history_df = data.get("history_df")

        if history_df is None or history_df.empty:
            return AgentAnalysis(
                agent_name=self.name,
                decision=TradingDecision.HOLD,
                reasoning="分析に必要な価格履歴データが提供されていません。",
                confidence=0.0
            )

        try:
            # Resample to Weekly
            weekly_df = self.mtf_analyzer.resample_data(history_df, "W-FRI")
            
            if len(weekly_df) < 20:
                return AgentAnalysis(
                    agent_name=self.name,
                    decision=TradingDecision.HOLD,
                    reasoning=f"週足データが不足しています ({len(weekly_df)} weeks)。",
                    confidence=0.3
                )

            # Calculate MTF indicators
            weekly_df["SMA_20"] = weekly_df["Close"].rolling(window=20).mean()
            weekly_df["SMA_50"] = weekly_df["Close"].rolling(window=50).mean()
            
            last_close = weekly_df["Close"].iloc[-1]
            last_sma20 = weekly_df["SMA_20"].iloc[-1]
            last_sma50 = weekly_df["SMA_50"].iloc[-1]
            
            is_bullish = last_sma20 > last_sma50 and last_close > last_sma20
            is_bearish = last_sma20 < last_sma50 and last_close < last_sma20
            
            if is_bullish:
                decision = TradingDecision.BUY
                reasoning = (
                    f"週足（長期）は明確な上昇トレンドです（SMA20 > SMA50）。"
                    f"現在の価格（{last_close:.1f}）はSMA20の上にあり、長期的な追い風が吹いています。"
                )
                confidence = 0.8
            elif is_bearish:
                decision = TradingDecision.SELL
                reasoning = (
                    f"週足（長期）は下降トレンドの渦中にあります（SMA20 < SMA50）。"
                    f"価格は主要移動平均線を下回っており、下落圧力が継続しています。"
                )
                confidence = 0.8
            else:
                decision = TradingDecision.HOLD
                reasoning = "週足トレンドが不明確です。長期的な方向感が出るまで待機を推奨します。"
                confidence = 0.5

            return AgentAnalysis(
                agent_name=self.name,
                decision=decision,
                reasoning=reasoning,
                confidence=confidence
            )

        except Exception as e:
            logger.error(f"MTF Analyst evaluation failed: {e}")
            return AgentAnalysis(
                agent_name=self.name,
                decision=TradingDecision.HOLD,
                reasoning=f"分析エラーが発生しました: {str(e)}",
                confidence=0.0
            )
