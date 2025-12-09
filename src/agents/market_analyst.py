from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.schemas import AgentAnalysis, TradingDecision
from src.llm_reasoner import get_llm_reasoner

class MarketAnalyst(BaseAgent):
    """
    Analyzes market data, news, and technical indicators to determine market sentiment.
    """
    def __init__(self):
        super().__init__(name="MarketAnalyst", role="Technical & Sentiment Analysis")
        self.reasoner = get_llm_reasoner()

    def analyze(self, data: Dict[str, Any]) -> AgentAnalysis:
        news_text = data.get("news_text", "No meaningful news.")
        market_stats = data.get("market_stats", {})
        
        # Use existing LLM logic but map to strictly typed AgentAnalysis
        # Note: prompt crafting logic is delegated to llm_reasoner for consistency,
        # but here we specifically interpret it as a trading signal.
        
        # For Phase 3 prototype, we use the existing analyze_market_impact
        # and map its "sentiment" to TradingDecision.
        
        impact = self.reasoner.analyze_market_impact(news_text, market_stats)
        
        # Mapping rules
        sentiment = impact.get("sentiment", "NEUTRAL").upper()
        if sentiment == "BULLISH":
            decision = TradingDecision.BUY
            confidence = 0.8
        elif sentiment == "BEARISH":
            decision = TradingDecision.SELL
            confidence = 0.8
        else:
            decision = TradingDecision.HOLD
            confidence = 0.5
            
        reasoning = f"Sentiment: {sentiment}. Key Drivers: {', '.join(impact.get('key_drivers', []))}. {impact.get('reasoning', '')}"
        
        analysis = self._create_response(decision, confidence, reasoning)
        self.log_analysis(analysis)
        return analysis
