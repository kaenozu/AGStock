import logging
from typing import Any, Dict, Tuple
from .base_agent import BaseAgent
from src.llm_reasoner import get_llm_reasoner
from src.news_collector import get_news_collector

logger = logging.getLogger(__name__)


class AIVetoAgent(BaseAgent):
    """
    AI Veto Agent (Phase 72)
    Provides a qualitative check on numerical trading signals using Gemini 2.0.
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="AIVetoAgent", role="Qualitative Signal Filtering")
        self.reasoner = get_llm_reasoner()
        self.news_collector = get_news_collector()
        self.config = config or {}

    def review_signal(
        self, ticker: str, action: str, price: float, reason: str
    ) -> Tuple[bool, str]:
        """
        Review a trading signal and decide whether to approve or veto it.

        Args:
            ticker: Ticker symbol
            action: 'BUY' or 'SELL'
            price: Current price
            reason: Reason given by numerical strategy

        Returns:
            Tuple[bool, str]: (Approved?, Veto Reason/Approval Msg)
        """
        # 1. Fetch Ticker-Specific News
        news = self.news_collector.fetch_news_for_ticker(ticker, limit=10)
        news_text = ""
        for n in news:
            news_text += f"Title: {n['title']}\nSummary: {n['summary']}\nSource: {n['source']}\n---\n"

        if not news_text:
            return (
                True,
                "No specific news found. Signal approved based on numerical data alone.",
            )

        # 2. Gemini Analysis
        prompt = f"""
        Trading Signal to Review:
            pass
        Ticker: {ticker}
        Action: {action}
        Price: {price}
        Numerical Reason: {reason}

        Recent News for {ticker}:
            pass
        {news_text}

        Evaluate if this {action} signal for {ticker} is safe or risky based on the latest news.
        Look for scandals, fraud, negative earnings, or sector-wide crashes.

        Respond in JSON format:
            pass
        {{
            "decision": "APPROVE" or "VETO",
            "confidence": 0.0 to 1.0,
            "reasoning": "brief explanation in Japanese",
            "risk_level": "LOW", "MEDIUM", or "HIGH"
        }}
        """

        try:
            # Using LLMReasoner for structured analysis
            result = self.reasoner.generate_json(prompt)

            if result:
                decision = result.get("decision", "APPROVE")
                veto_reason = result.get("reasoning", "No specific reason provided.")
                risk = result.get("risk_level", "LOW")

                if decision == "VETO":
                    return False, f"AI拒否権発動 ({risk}): {veto_reason}"
                else:
                    return True, f"AIにより承認 ({risk}): {veto_reason}"

            return True, "AI分析結果が空のため、デフォルトで承認します。"

        except Exception as e:
            logger.error(f"Error in AIVetoAgent analysis: {e}")
            return True, f"AI分析エラーのため承認: {e}"

    def analyze(self, data: Dict[str, Any]) -> Any:
        # Compatibility with BaseAgent structure
        ticker = data.get("ticker")
        action = data.get("action")
        price = data.get("price")
        reason = data.get("reason")
        return self.review_signal(ticker, action, price, reason)
