"""
AI投資委員会 (Investment Committee)
複数の専門AIエージェントによる合議制意思決定システム
"""
import logging
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime
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
        try:
            from src.rag.experience_memory import ExperienceMemory
            self.memory = ExperienceMemory()
        except ImportError:
            self.memory = None

    def hold_meeting(self, market_context: Dict) -> Dict:
        """UI互換性のためのラップメソッド。集合知を考慮して判断を下す。"""
        ticker = market_context.get("ticker", "General Market")
        ai_score = market_context.get("ai_score", 0.5)
        
        # 過去の集合知を取得
        wisdom = ""
        if self.memory:
            wisdom = self.memory.get_collective_wisdom(market_context)
            logger.info(f"Retrieved wisdom: {wisdom}")

        # 既存の合議ロジックを実行
        result = self.debate(ticker, ai_score, market_context)
        
        # 集合知を結果に追加
        result["collective_wisdom"] = wisdom
        result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result["final_decision"] = result["decision"]
        result["rationale"] = f"集合知に基づく判断: {wisdom[:100]}..." if wisdom else "現在のデータに基づく判断。"
        
        # エージェント名をUIに合わせる
        for a in result["analyses"]:
            a["agent_name"] = a["agent_name"]
            a["role"] = "Expert Analyst"
            a["reasoning"] = a["reason"]

        return result

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