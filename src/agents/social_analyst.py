import logging
from typing import Dict, Any
from agstock.src.agents.base_agent import BaseAgent
from agstock.src.schemas import AgentAnalysis, TradingDecision
from agstock.src.llm_reasoner import get_llm_reasoner
from agstock.src.news_collector import get_news_collector

logger = logging.getLogger(__name__)


class SocialAnalyst(BaseAgent):
    """
    Social Sentiment & Heat Analyst (Phase 73)
    Analyzes 'crowd heat' and potential social-driven risks.
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="SocialAnalyst", role="Social Sentiment Analysis")
        self.reasoner = get_llm_reasoner()
        self.news_collector = get_news_collector()
        self.config = config or {}

    def analyze(self, data: Dict[str, Any]) -> AgentAnalysis:
        """Standard analysis interface required by BaseAgent."""
        ticker = data.get("ticker", "Unknown")
        heat_data = self.analyze_heat(ticker)

        # Convert heat data to simple decision info
        score = heat_data.get("heat_level", 5.0)  # 0-10
        # If heat is too high (hype) -> risk -> caution
        # If heat is very low -> neglected?

        # Simple logic: High heat + Negative Sentiment -> SELL
        # High heat + Positive Sentiment -> BUY (Momentum)

        sentiment = heat_data.get("sentiment", "NEUTRAL")

        decision = TradingDecision.HOLD
        if score > 7.0:
            if sentiment in ["POSITIVE", "EXTREME_HYPE"]:
                decision = TradingDecision.BUY
            elif sentiment in ["NEGATIVE", "PANIC"]:
                decision = TradingDecision.SELL

        return self._create_response(
            decision=decision,
            confidence=min(score / 10.0, 1.0),
            reasoning=f"Social Heat: {score:.1f}/10, Sentiment: {sentiment}. {heat_data.get('reasoning', '')}",
        )

    def analyze_heat(self, ticker: str) -> Dict[str, Any]:
        """
        Analyze social heat and 'buzz' for a specific ticker.
        """
        # Fetch news as a proxy for social heat in this implementation
        news = self.news_collector.fetch_news_for_ticker(ticker, limit=10)
        news_text = "\n".join([f"- {n['title']}: {n['summary']}" for n in news])

        prompt = f"""
        Analyze the 'Social Heat' for {ticker} based on recent news and headlines.
        Identify if there is extreme hype, panic, or a 'meme stock' behavior.

        News Headlines:
        {news_text}

        Respond in JSON format:
        {{
            "heat_level": 0.0 to 10.0,
            "sentiment": "EXTREME_HYPE", "POSITIVE", "NEUTRAL", "NEGATIVE", "PANIC",
            "is_crowded": true/false,
            "social_risk": "HIGH", "MEDIUM", "LOW",
            "reasoning": "summary in Japanese"
        }}
        """

        try:
            result = self.reasoner.generate_json(prompt)
            return result or self._fallback_response()
        except Exception as e:
            logger.error(f"SocialAnalyst error for {ticker}: {e}")
            return self._fallback_response()

    def _fallback_response(self) -> Dict[str, Any]:
        return {
            "heat_level": 5.0,
            "sentiment": "NEUTRAL",
            "is_crowded": False,
            "social_risk": "LOW",
            "reasoning": "データ不足により分析不可",
        }
