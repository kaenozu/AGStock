from typing import Any, Dict

from src.agents.base_agent import BaseAgent
from src.schemas import AgentAnalysis, RiskConfig, TradingDecision


class RiskManager(BaseAgent):
    """
    Evaluates portfolio risk and vetoes risky trades or suggests hedging.
    """

    def __init__(self, config: RiskConfig = None):
        super().__init__(name="RiskManager", role="Risk Control")
        # Default risk controls if none provided
        self.max_drawdown_limit = 0.10  # 10% max drawdown tolerance
        self.vix_threshold = 30.0

    def analyze(self, data: Dict[str, Any]) -> AgentAnalysis:
        portfolio = data.get("portfolio", {})
        vix = data.get("vix", 20.0)

        current_drawdown = portfolio.get("drawdown_pct", 0.0)
        cash_ratio = portfolio.get("cash_ratio", 1.0)

        reasoning_parts = []
        is_safe = True

        # 1. Check VIX
        if vix > self.vix_threshold:
            reasoning_parts.append(f"VIX is high ({vix:.1f})")
            is_safe = False

        # 2. Check Drawdown
        if current_drawdown < -self.max_drawdown_limit:
            reasoning_parts.append(f"Drawdown {current_drawdown:.1%} exceeds limit")
            is_safe = False

        # Decision Logic
        if not is_safe:
            decision = TradingDecision.SELL  # Reduce exposure
            confidence = 0.9
            reasoning = "Risk limits exceeded: " + "; ".join(reasoning_parts)
        elif cash_ratio < 0.1:
            decision = TradingDecision.HOLD
            confidence = 0.7
            reasoning = "Low cash reserves, avoiding new positions."
        else:
            decision = (
                TradingDecision.HOLD
            )  # Risk Manager default is to hold unless risk is high
            confidence = 0.5
            reasoning = "Risk levels acceptable."

        analysis = self._create_response(decision, confidence, reasoning)
        self.log_analysis(analysis)
        return analysis
