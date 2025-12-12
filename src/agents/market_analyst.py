from typing import Dict, Any
import pandas as pd
from src.agents.base_agent import BaseAgent
from src.schemas import AgentAnalysis, TradingDecision
from src.llm_reasoner import get_llm_reasoner
from src.regime_detector import RegimeDetector

class MarketAnalyst(BaseAgent):
    """
    Analyzes market data, news, and technical indicators to determine market sentiment.
    """
    def __init__(self):
        super().__init__(name="MarketAnalyst", role="Technical & Sentiment Analysis")
        self.reasoner = get_llm_reasoner()
        self.regime_detector = RegimeDetector()

    def analyze(self, data: Dict[str, Any]) -> AgentAnalysis:
        news_text = data.get("news_text", "No meaningful news.")
        market_stats = data.get("market_stats", {})
        
        # 1. Detect Regime (if history available)
        # Note: 'data' needs to contain raw DataFrame for technical analysis
        # For now, we assume 'market_df' or similar is passed.
        # If not, we skip regime detection or fetch inside (expensive).
        # We'll use get_regime_signal logic if DF is present.
        
        regime_info = None
        market_df = data.get("market_df")
        # Ensure market_df is actually a DataFrame before checking .empty
        if market_df is not None and isinstance(market_df, pd.DataFrame) and not market_df.empty:
            regime_info = self.regime_detector.get_regime_signal(market_df)
        
        # 2. LLM Analysis
        impact = self.reasoner.analyze_market_impact(news_text, market_stats)
        
        # Mapping rules
        sentiment = impact.get("sentiment", "NEUTRAL").upper()
        
        # Adjust sentiment based on Regime
        regime_msg = ""
        if regime_info:
            regime_name = regime_info['regime_name']
            regime_val = regime_info['regime']
            regime_msg = f" [Market Regime: {regime_name}]"
            
            # Logic: If Bear Market, discount Bullish news
            if "BEAR" in regime_name.upper() and sentiment == "BULLISH":
                sentiment = "NEUTRAL (Dampened by Bear Trend)"
        
        if "BULLISH" in sentiment:
            decision = TradingDecision.BUY
            confidence = 0.8
        elif "BEARISH" in sentiment:
            decision = TradingDecision.SELL
            confidence = 0.8
        else:
            decision = TradingDecision.HOLD
            confidence = 0.5
            
        reasoning = f"Sentiment: {sentiment}. Key Drivers: {', '.join(impact.get('key_drivers', []))}. {impact.get('reasoning', '')}{regime_msg}"
        
        analysis = self._create_response(decision, confidence, reasoning)
        self.log_analysis(analysis)
        return analysis
