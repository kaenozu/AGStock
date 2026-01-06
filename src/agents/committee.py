"""
AI投資委員会 (Investment Committee)
複数の専門AIエージェントによる合議制意思決定システム
"""
import logging
from dataclasses import dataclass
from typing import List, Dict
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class AgentAnalysis:
    agent_name: str
    decision: str  # BUY, SELL, HOLD
    confidence: float
    reason: str

class InvestmentCommittee:
    def __init__(self):
        self.agents = ["慎重派(Risk-Averse)", "積極派(Aggressive)", "テクニカル重視(Technical)"]

    def debate(self, ticker: str, ai_score: float, market_data: Dict) -> Dict:
        """各エージェントの意見を集約し、最終的な投資判断を下す"""
        analyses = []
        
        # 1. 慎重派エージェント
        vol = market_data.get("volatility", 0)
        if vol > 0.02 or ai_score < 0.6:
            analyses.append(AgentAnalysis("Conservative", "HOLD", 0.8, "ボラティリティが高いため静観を推奨。"))
        else:
            analyses.append(AgentAnalysis("Conservative", "BUY", 0.5, "リスク許容範囲内での上昇を期待。"))

        # 2. 積極派エージェント
        if ai_score > 0.55:
            analyses.append(AgentAnalysis("Aggressive", "BUY", 0.9, f"AIスコア {ai_score:.2f} を信頼し、積極的にエントリー。"))
        else:
            analyses.append(AgentAnalysis("Aggressive", "SELL", 0.6, "トレンドの弱まりを検知。"))

        # 3. テクニカル重視エージェント
        rsi = market_data.get("rsi", 50)
        if rsi < 30:
            analyses.append(AgentAnalysis("Technical", "BUY", 0.7, "売られすぎ水準からのリバウンド期待。"))
        elif rsi > 70:
            analyses.append(AgentAnalysis("Technical", "SELL", 0.7, "買われすぎ水準。"))
        else:
            analyses.append(AgentAnalysis("Technical", "HOLD", 0.5, "指標は中立。"))

        # 合議ロジック（重み付き投票）
        buy_votes = sum(a.confidence for a in analyses if a.decision == "BUY")
        sell_votes = sum(a.confidence for a in analyses if a.decision == "SELL")
        
        final_decision = "HOLD"
        if buy_votes > sell_votes and buy_votes > 1.2:
            final_decision = "BUY"
        elif sell_votes > buy_votes and sell_votes > 1.2:
            final_decision = "SELL"

        return {
            "ticker": ticker,
            "decision": final_decision,
            "analyses": [vars(a) for a in analyses],
            "consensus_score": max(buy_votes, sell_votes) / 3.0
        }