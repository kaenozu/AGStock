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
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            # Simple simulation of result parsing
            text = response.text.upper()
            decision = TradingDecision.HOLD
            if "BUY" in text: decision = TradingDecision.BUY
            elif "SELL" in text: decision = TradingDecision.SELL
            
            return AgentAnalysis(
                agent_name=self.name,
                role=self.role,
                decision=decision,
                reasoning=response.text[:500],
                confidence=0.7
            )
        except Exception as e:
            logger.error(f"Specialized agent {self.name} failed: {e}")
            return AgentAnalysis(
                agent_name=self.name,
                role=self.role,
                decision=TradingDecision.HOLD,
                reasoning=f"Error during analysis: {e}",
                confidence=0.0
            )

class AgentSpawner:
    """
    Spawns specialized agents based on market regime and score.
    """
    
    def spawn_agents_for_regime(self, market_score: float) -> List[SpecializedAgent]:
        """
        Creates specialized agents adapted to the current market state.
        """
        logger.info(f"Spawning agents for market score: {market_score}")
        agents = []

        if market_score < 40:
            # Crisis mode
            agents.append(SpecializedAgent(
                name="BearMarketGuard",
                persona="極めて保守的なリスク回避のスペシャリスト。資産を守ることを最優先する。",
                focus="ボラティリティの低さと財務バランスシートの健全性。"
            ))
        elif market_score > 75:
            # Bull mode
            agents.append(SpecializedAgent(
                name="MomentumHunter",
                persona="勢いのあるグロース株を好むアグレッシブな投資家。トレンドの初動を捉えるのが得意。",
                focus="移動平均の乖離率と市場の熱量（センチメント）。"
            ))
        
        # Always add a sector specialist if data allows (conceptual)
        agents.append(SpecializedAgent(
            name="AlphaSearcher",
            persona="データに隠れた歪みを探すクオンツ。既存エージェントが見逃している微細な予兆を捉える。",
            focus="価格と取引量の不一致、ニュースの異常値。"
        ))

        return agents
