from typing import Any, Dict
import logging
from src.agents.base_agent import BaseAgent
from src.schemas import AgentAnalysis, TradingDecision

logger = logging.getLogger(__name__)


class MacroStrategist(BaseAgent):
    """
    Agent specialized in analyzing global macro trends and their impact on equity markets.
    """

    def __init__(self):
        super().__init__(name="MacroStrategist", role="Global Macro Strategy")

    def analyze(self, data: Dict[str, Any]) -> AgentAnalysis:
        """
        Analyzes macro data provided in the 'macro_data' field.
        """
        macro_data = data.get("macro_data", {})
        if "error" in macro_data:
            return self._create_response(
                TradingDecision.HOLD,
                0.5,
                f"Macro analysis skipped due to data error: {macro_data['error']}",
            )

        score = macro_data.get("macro_score", 50.0)
        vix = macro_data.get("vix", {}).get("value", 20.0)
        macro_data.get("usdjpy", {}).get("value", 150.0)
        sox_change = macro_data.get("sox", {}).get("change_pct", 0.0)

        # Decision logic based on macro stability
        decision = TradingDecision.HOLD
        confidence = 0.5

        reasons = []
        if score > 75:
            decision = TradingDecision.BUY
            confidence = min(0.9, 0.4 + (score / 100))
            reasons.append(
                "Global macro environment is highly stable and supportive of risk-on assets."
            )
        elif score < 40:
            decision = TradingDecision.SELL
            confidence = min(0.9, 0.4 + ((100 - score) / 100))
            reasons.append(
                "Global macro volatility is high (VIX/Yield spikes). Extreme caution advised."
            )
        else:
            decision = TradingDecision.HOLD
            confidence = 0.6
            reasons.append(
                "Macro indicators are in a neutral range. Focus on individual stock strength."
            )

        # Specific factors
        if vix > 25:
            reasons.append(f"VIX is elevated at {vix:.1f}, indicating market fear.")
        if abs(sox_change) > 2:
            sentiment = "positive" if sox_change > 0 else "negative"
            reasons.append(
                f"Strong {sentiment} momentum in Semiconductors (SOX: {sox_change:+.1f}%)."
            )

        reasoning = " ".join(reasons)

        analysis = self._create_response(decision, confidence, reasoning)
        self.log_analysis(analysis)
        return analysis
