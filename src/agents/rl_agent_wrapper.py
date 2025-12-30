"""RL Agent Wrapper - Wraps agents with Reinforcement Learning layer."""
import numpy as np
import logging
import json
import os
from typing import Dict, Any, List, Optional
from src.agents.base_agent import BaseAgent
from src.schemas import AgentAnalysis, TradingDecision

logger = logging.getLogger(__name__)


class RLAgentWrapper:
    """
    Wraps a standard heuristic-based agent with a Reinforcement Learning layer.
    The RL layer learns to 'trust' or 'override' the base agent based on market state.
    """
    
    def __init__(
        self, 
        base_agent: BaseAgent, 
        name_suffix: str = "", 
        learning_rate: float = 0.1, 
        discount_factor: float = 0.9
    ):
        self.agent = base_agent
        self.name = f"{base_agent.name}{name_suffix}"
        self.q_table_path = f"q_table_{self.name}.json"
        self.q_table = self._load_q_table()
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = 0.1  # Exploration rate
        self.last_state: Optional[str] = None
        self.last_action: Optional[int] = None
    
    def _load_q_table(self) -> Dict[str, List[float]]:
        """Load Q-table from file if exists."""
        if os.path.exists(self.q_table_path):
            try:
                with open(self.q_table_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load Q-table: {e}")
        return {}
    
    def _save_q_table(self):
        """Save Q-table to file."""
        try:
            with open(self.q_table_path, 'w') as f:
                json.dump(self.q_table, f)
        except Exception as e:
            logger.warning(f"Failed to save Q-table: {e}")
    
    def _get_state_key(self, data: Dict[str, Any]) -> str:
        """Convert data to discrete state key."""
        vix = data.get("vix", 20)
        if vix > 30:
            return "high_volatility"
        elif vix > 20:
            return "medium_volatility"
        return "low_volatility"
    
    def _get_q_values(self, state: str) -> List[float]:
        """Get Q-values for state, initializing if needed."""
        if state not in self.q_table:
            self.q_table[state] = [0.0, 0.0]  # [Q_TRUST, Q_OVERRIDE]
        return self.q_table[state]
    
    def analyze(self, data: Dict[str, Any]) -> AgentAnalysis:
        """Analyze with RL-enhanced decision making."""
        # Get base agent's opinion
        try:
            base_analysis = self.agent.analyze(data)
        except Exception as e:
            logger.error(f"Base agent {self.agent.name} failed: {e}")
            return AgentAnalysis(
                agent_name=self.name,
                role=getattr(self.agent, "role", "RL Wrapper"),
                decision=TradingDecision.HOLD,
                reasoning=f"Agent Error: {e}",
                confidence=0.0,
            )
        
        # Discretize state
        state = self._get_state_key(data)
        self.last_state = state
        
        # Decision: 0 = Trust Agent, 1 = Override (Force HOLD)
        if np.random.random() < self.epsilon:
            action = np.random.choice([0, 1])
        else:
            q_values = self._get_q_values(state)
            action = int(np.argmax(q_values))
        
        self.last_action = action
        
        if action == 1:  # Override
            return AgentAnalysis(
                agent_name=self.name,
                role=getattr(self.agent, "role", "RL Wrapper"),
                decision=TradingDecision.HOLD,
                reasoning=f"RL Override: Risk-off mode in {state}",
                confidence=0.5,
            )
        
        # Trust base agent
        return base_analysis
    
    def update(self, reward: float, new_data: Dict[str, Any]):
        """Update Q-table based on reward."""
        if self.last_state is None or self.last_action is None:
            return
        
        new_state = self._get_state_key(new_data)
        q_values = self._get_q_values(self.last_state)
        new_q_values = self._get_q_values(new_state)
        
        # Q-learning update
        old_value = q_values[self.last_action]
        next_max = max(new_q_values)
        new_value = old_value + self.lr * (reward + self.gamma * next_max - old_value)
        
        self.q_table[self.last_state][self.last_action] = new_value
        self._save_q_table()
