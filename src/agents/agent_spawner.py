"""
Agent Spawner
Dynamically spawns specialized agents based on market conditions or user requests.
"""

import logging
import os
from typing import Any, Dict, List

import google.generativeai as genai

from src.agents.base_agent import BaseAgent
from src.schemas import AgentAnalysis, TradingDecision

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

        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return AgentAnalysis(
                    agent_name=self.name,
                    decision=TradingDecision.HOLD,
                    reasoning="API Key missing for specialized agent.",
                    confidence=0.0
                )

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            text = response.text

            decision = TradingDecision.HOLD
            if "BUY" in text.upper():
                decision = TradingDecision.BUY
            elif "SELL" in text.upper():
                decision = TradingDecision.SELL

            return AgentAnalysis(
                agent_name=self.name,
                decision=decision,
                reasoning=text[:500],
                confidence=0.7  # Placeholder confidence
            )

        except Exception as e:
            logger.error(f"Specialized Agent {self.name} failed: {e}")
            return AgentAnalysis(
                agent_name=self.name,
                decision=TradingDecision.HOLD,
                reasoning=f"Error: {e}",
                confidence=0.0
            )


class AgentSpawner:
    """Factory for creating specialized agents."""

    def __init__(self):
        self.active_agents: List[SpecializedAgent] = []

    def spawn_agent(self, name: str, persona: str, focus: str) -> SpecializedAgent:
        """Creates and registers a new specialized agent."""
        agent = SpecializedAgent(name, persona, focus)
        self.active_agents.append(agent)
        logger.info(f"✨ Spawned new agent: {name} ({persona})")
        return agent

    def clear_agents(self):
        self.active_agents = []
