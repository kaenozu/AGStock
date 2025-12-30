import logging
from typing import List, Dict, Any, Optional
from src.agents.base_agent import BaseAgent
from src.schemas import AgentAnalysis, TradingDecision
import google.generativeai as genai

logger = logging.getLogger(__name__)


class SpecializedAgent(BaseAgent):
    """
    A dynamically spawned agent with a specific persona and focus.
    """

    def __init__(self, name: str, persona: str, focus: str):
        super().__init__(name, role="Specialized Analyst")
        self.persona = persona
        self.focus = focus

    def analyze(self, data: Dict[str, Any]) -> AgentAnalysis:
        ticker = data.get("ticker", "Unknown")
        prompt = f"""
あなたは以下の役割（ペルソナ）を持つ投資エージェントです。
役割: {self.persona}
注力ポイント: {self.focus}

以下の銘柄データを分析し、あなたの役割に忠実な判断を下してください。
銘柄: {ticker}
データ概略: {str(data)[:2000]} 

【出力要件】
1. 判断（TradingDecision）: BUY, SELL, または HOLD
2. 理由（reasoning）: なぜその判断に至ったか
3. 自信度（confidence）: 0.0 - 1.0

あなたのペルソナになりきって答えてください。
"""


# try:
#             model = genai.GenerativeModel("gemini-1.5-flash")
