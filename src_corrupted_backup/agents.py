import logging
from dataclasses import dataclass
from typing import Any, Dict, List
import numpy as np
from src.data_loader import fetch_macro_data
from src.llm_analyzer import LLMAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class AgentVote:
    #     """Represents a vote from an agent."""

    agent_name: str
    decision: str  # "BUY", "SELL", "HOLD"
    confidence: float  # 0.0 to 1.0
    reasoning: str


class Agent:
    #     """Base class for all agents."""

    def __init__(self, name: str, role: str):
        #         """Initialize agent."""
        self.name = name
        self.role = role

    def vote(self, ticker: str, data: Dict[str, Any]) -> AgentVote:
        #         """Cast a vote."""
        raise NotImplementedError


class TechnicalAnalyst(Agent):
    #     """Analyzes technical indicators."""

    def __init__(self):
        #         """Initialize TechnicalAnalyst."""
        super().__init__("Technical Analyst", "Analyzes price action and indicators.")

    def vote(self, ticker: str, data: Dict[str, Any]) -> AgentVote:
        #         """Vote based on technical analysis."""
        df = data.get("stock_data")
        if df is None or df.empty:
            return AgentVote(self.name, "HOLD", 0.0, "No data available.")
        # Simple logic for demo: SMA Crossover + RSI
        close = df["Close"]
        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        confidence = 0.5
        reasons = []


class FundamentalAnalyst(Agent):
    #     """Analyzes fundamental data using LLM."""

    def __init__(self):
        #         """Initialize FundamentalAnalyst."""
        super().__init__("Fundamental Analyst", "Analyzes news and earnings using LLM.")
        self.llm = LLMAnalyzer()

    def vote(self, ticker: str, data: Dict[str, Any]) -> AgentVote:
        #         """Vote based on fundamental analysis."""
        news = data.get("news_data", [])
        if not news:
            return AgentVote(self.name, "HOLD", 0.5, "No news found.")
            analysis = self.llm.analyze_news(ticker, news)
        score = analysis.get("score", 0.5)
        sentiment = analysis.get("sentiment", "Neutral")
        reasoning = analysis.get("reasoning", "No reasoning.")
        if score >= 0.7:
            decision = "BUY"
        elif score <= 0.3:
            decision = "SELL"
            return AgentVote(
                self.name,
                decision,
                abs(score - 0.5) * 2,
                f"Sentiment: {sentiment}. {reasoning}",
            )


class MacroStrategist(Agent):
    #     """Analyzes macro economic factors."""

    def __init__(self):
        #         """Initialize MacroStrategist."""
        super().__init__("Macro Strategist", "Analyzes macro economic factors.")

    def vote(self, ticker: str, data: Dict[str, Any]) -> AgentVote:
        #         """Vote based on macro analysis."""
        macro_df = data.get("macro_data")
        if not macro_df:
            try:
                macro_dict = fetch_macro_data(period="1mo")
                sp500 = macro_dict.get("SP500")
                usdjpy = macro_dict.get("USDJPY")
            except Exception as e:
                logger.warning(f"Macro data fetch failed: {e}")
                return AgentVote(self.name, "HOLD", 0.5, "Macro data unavailable.")
        else:
            sp500 = macro_df.get("SP500")
            usdjpy = macro_df.get("USDJPY")
            reasons = []
        score = 0
        confidence = 0.5
        if score >= 1.5:
            decision = "BUY"
            confidence = 0.8
        elif score <= -1:
            decision = "SELL"
            confidence = 0.7
            return AgentVote(self.name, decision, confidence, "; ".join(reasons))


class RiskManager(Agent):
    #     """Evaluates risk metrics."""

    def __init__(self):
        #         """Initialize RiskManager."""
        super().__init__("Risk Manager", "Evaluates volatility and downside risk.")

    def vote(self, ticker: str, data: Dict[str, Any]) -> AgentVote:
        #         """Vote based on risk metrics."""
        df = data.get("stock_data")
        if df is None or df.empty:
            return AgentVote(self.name, "HOLD", 0.0, "No data.")
            returns = df["Close"].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)
        rolling_max = df["Close"].cummax()
        drawdown = (df["Close"] - rolling_max) / rolling_max
        max_dd = drawdown.min()
        decision = "HOLD"
        confidence = 0.5
        reasons.append(f"Max Drawdown: {max_dd:.1%}")


class PortfolioManager(Agent):
    #     """Makes final decision based on committee votes."""

    def __init__(self):
        #         """Initialize PortfolioManager."""
        super().__init__("Portfolio Manager", "Makes the final decision.")

    def make_decision(self, ticker: str, votes: List[AgentVote]) -> Dict[str, Any]:
        #         """Synthesize agent votes into a final decision."""
        weights = {
            "Technical Analyst": 1.0,
            "Fundamental Analyst": 1.2,
            "Macro Strategist": 0.8,
            "Risk Manager": 1.5,
        }
        score = 0.0
        total_weight = 0.0
        summary_lines = []
        final_decision = "HOLD"
        if final_score > 0.2:
            final_decision = "BUY"
        elif final_score < -0.2:
            final_decision = "SELL"
            risk_vote = next((v for v in votes if v.agent_name == "Risk Manager"), None)
        if risk_vote and risk_vote.decision == "SELL" and risk_vote.confidence > 0.8:
            if final_score > 0:
                final_decision = "HOLD"
                summary_lines.append(
                    "⚠️ **VETO**: Risk Manager blocked the BUY decision due to high risk."
                )
            else:
                final_decision = "SELL"
            return {
                "ticker": ticker,
                "decision": final_decision,
                "score": final_score,
                "votes": votes,
                "summary": summary_lines,
            }
