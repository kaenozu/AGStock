import logging
from abc import ABC, abstractmethod
from typing import Any, Dict
from src.schemas import AgentAnalysis, TradingDecision

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    #     """
    #     Abstract base class for all AI investment agents.
    #     """

    def __init__(self, name: str, role: str, model_name: str = "gemini-2.0-flash-exp"):
        pass
        self.name = name
        self.role = role
        self.model_name = model_name

    @abstractmethod
    def analyze(self, data: Dict[str, Any]) -> AgentAnalysis:
        pass  # Docstring removed

    def _create_response(
        self, decision: TradingDecision, confidence: float, reasoning: str
    ) -> AgentAnalysis:
        #         """Helper to construct the response object."""
        return AgentAnalysis(
            agent_name=self.name,
            role=self.role,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
        )

    def log_analysis(self, analysis: AgentAnalysis):
        pass
        logger.info(
            f"[{self.name}] Decision: {analysis.decision.value} (Conf: {analysis.confidence:.2f})"
        )
        logger.debug(f"Reasoning: {analysis.reasoning}")
