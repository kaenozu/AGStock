from typing import Any, Dict

import pandas as pd

from src.agents.base_agent import BaseAgent
from src.llm_reasoner import get_llm_reasoner
from src.regime_detector import RegimeDetector
from src.schemas import AgentAnalysis, TradingDecision


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

        # 2. Consume Quantitative Prediction Report
        prediction_report = data.get("prediction_report", {})
        ensemble_decision = prediction_report.get("ensemble_decision", "UNKNOWN")
        ensemble_conf = prediction_report.get("confidence", 0.0)
        
        # 3. LLM Analysis
        impact = self.reasoner.analyze_market_impact(news_text, market_stats)
        sentiment = impact.get("sentiment", "NEUTRAL").upper()

        # Adjust sentiment based on Regime
        regime_msg = ""
        if regime_info:
            regime_name = regime_info["regime_name"]
            regime_val = regime_info["regime"]
            regime_msg = f" [Market Regime: {regime_name}]"

            # Logic: If Bear Market, discount Bullish news
            if "BEAR" in regime_name.upper() and sentiment == "BULLISH":
                sentiment = "NEUTRAL (Dampened by Bear Trend)"

        # 4. Synthesize Decision (LLM + Quantitative)
        # If Ensemble is strong (e.g. > 0.7), it heavily influences the decision
        final_decision = TradingDecision.HOLD
        final_confidence = 0.5
        
        qt_signal = "NEUTRAL"
        if ensemble_decision == "UP":
            qt_signal = "BULLISH"
        elif ensemble_decision == "DOWN":
            qt_signal = "BEARISH"
            
        # Decision Logic:
        # If Quantitative and Qualitative (LLM) agree -> High Confidence
        # If Disagree -> Lower confidence, lean towards Quantitative if confidence is high
        
        if "BULLISH" in sentiment and qt_signal == "BULLISH":
            final_decision = TradingDecision.BUY
            final_confidence = min(0.95, 0.6 + ensemble_conf * 0.4)
        elif "BEARISH" in sentiment and qt_signal == "BEARISH":
            final_decision = TradingDecision.SELL
            final_confidence = min(0.95, 0.6 + ensemble_conf * 0.4)
        elif qt_signal == "BULLISH" and ensemble_conf > 0.75:
             # Strong Quant override
            final_decision = TradingDecision.BUY
            final_confidence = ensemble_conf
            sentiment = f"Mixed (LLM: {sentiment}, Quant: STRONG BULLISH)"
        elif qt_signal == "BEARISH" and ensemble_conf > 0.75:
             # Strong Quant override
            final_decision = TradingDecision.SELL
            final_confidence = ensemble_conf
            sentiment = f"Mixed (LLM: {sentiment}, Quant: STRONG BEARISH)"
        else:
            # Fallback to simple matching or HOLD
            if "BULLISH" in sentiment:
                final_decision = TradingDecision.BUY
                final_confidence = 0.6
            elif "BEARISH" in sentiment:
                final_decision = TradingDecision.SELL
                final_confidence = 0.6

        components_str = ", ".join([f"{k}:{v}" for k, v in prediction_report.get("components", {}).items()])
        quant_reasoning = f"Quant Models: {ensemble_decision} ({ensemble_conf:.2f}). Details: [{components_str}]."
        
        reasoning = f"Sentiment: {sentiment}. {quant_reasoning} Key Drivers: {', '.join(impact.get('key_drivers', []))}. {regime_msg}"

        analysis = self._create_response(final_decision, final_confidence, reasoning)
        self.log_analysis(analysis)
        return analysis
