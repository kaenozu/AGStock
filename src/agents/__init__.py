"""Agents package - Re-exports from both package modules and src/agent_classes.py"""

# From package modules
from src.agents.base_agent import BaseAgent
from src.agents.committee import InvestmentCommittee
from src.agents.market_analyst import MarketAnalyst
from src.agents.risk_manager import RiskManager as RiskManagerAgent

# From the top-level src/agent_classes.py module
from src.agent_classes import (
    AgentVote,
    Agent,
    TechnicalAnalyst,
    FundamentalAnalyst,
    MacroStrategist,
    RiskManager,
    PortfolioManager,
)

__all__ = [
    # Package modules
    "BaseAgent",
    "InvestmentCommittee",
    "MarketAnalyst",
    "RiskManagerAgent",
    # From src/agent_classes.py
    "AgentVote",
    "Agent",
    "TechnicalAnalyst",
    "FundamentalAnalyst",
    "MacroStrategist",
    "RiskManager",
    "PortfolioManager",
]
