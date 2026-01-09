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

        # 3. Consume Earnings Report
        earnings_report = data.get("earnings_report")
        earnings_msg = ""
        earnings_impact = 0.0  # -1 to 1 impact

        if earnings_report:
            rec = earnings_report.get("recommendation", "HOLD")
            conf = earnings_report.get("confidence", 0.5)
            reason = earnings_report.get("reasoning", "")
            sentiment_e = earnings_report.get("sentiment", "NEUTRAL")

            earnings_msg = f" [Earnings: {rec} (Conf: {conf:.2f}), {sentiment_e}. Reason: {reason}]"

            if rec == "BUY":
                earnings_impact = 0.5 * conf
            elif rec == "SELL":
                earnings_impact = -0.5 * conf

        # 4. LLM Analysis
        impact = self.reasoner.analyze_market_impact(news_text, market_stats)
        sentiment = impact.get("sentiment", "NEUTRAL").upper()

        # Adjust sentiment based on Regime
        regime_msg = ""
        if regime_info:
            regime_name = regime_info["regime_name"]
            regime_info["regime"]
            regime_msg = f" [Market Regime: {regime_name}]"

            # Logic: If Bear Market, discount Bullish news
            if "BEAR" in regime_name.upper() and sentiment == "BULLISH":
                sentiment = "NEUTRAL (Dampened by Bear Trend)"

        # 5. Synthesize Decision (LLM + Quantitative + Earnings)
        final_decision = TradingDecision.HOLD
        final_confidence = 0.5

        qt_signal = "NEUTRAL"
        if ensemble_decision == "UP":
            qt_signal = "BULLISH"
        elif ensemble_decision == "DOWN":
            qt_signal = "BEARISH"

        # Composite score calculation
        sentiment_score = 1.0 if "BULLISH" in sentiment else -1.0 if "BEARISH" in sentiment else 0.0
        quant_score = (1.0 if qt_signal == "BULLISH" else -1.0 if qt_signal == "BEARISH" else 0.0) * ensemble_conf

        total_score = (sentiment_score * 0.3) + (quant_score * 0.4) + (earnings_impact * 0.3)

        if total_score > 0.3:
            final_decision = TradingDecision.BUY
            final_confidence = min(0.95, 0.5 + abs(total_score))
        elif total_score < -0.3:
            final_decision = TradingDecision.SELL
            final_confidence = min(0.95, 0.5 + abs(total_score))
        else:
            final_decision = TradingDecision.HOLD
            final_confidence = 1.0 - abs(total_score)

        components_str = ", ".join([f"{k}:{v}" for k, v in prediction_report.get("components", {}).items()])
        quant_reasoning = f"Quant Models: {ensemble_decision} ({ensemble_conf:.2f}). Details: [{components_str}]."

        # Self-Learning context
        lessons_learned = data.get("lessons_learned", "")
        lessons_msg = f"\n[Self-Learning Lessons: {lessons_learned}]" if lessons_learned else ""

        reasoning = (
            f"Sentiment: {sentiment}. {quant_reasoning} {earnings_msg} "
            f"Key Drivers: {', '.join(impact.get('key_drivers', []))}. {regime_msg}{lessons_msg}"
        )

        analysis = self._create_response(final_decision, final_confidence, reasoning)
        self.log_analysis(analysis)
        return analysis
