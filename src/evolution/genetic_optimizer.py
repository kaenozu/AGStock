"""Genetic Optimizer for RL Agent evolution."""
import logging
from typing import List, Any

from src.data.feedback_store import FeedbackStore

logger = logging.getLogger(__name__)


class GeneticOptimizer:
    """
    Optimizes RL Agents by mutating their hyperparameters based on performance.
    Phase 83: Multi-Agent RL Arena Evolution.
    """

    def __init__(self):
        self.fs = FeedbackStore()

    def evolve_agents(self, agents: List[Any]):
        """Evolve agents based on performance."""
        leaderboard = self.fs.get_agent_leaderboard()
        if not leaderboard:
            return

        for agent in agents:
            # Check if it is an RL Wrapper (has epsilon, q_table)
            if not hasattr(agent, "epsilon"):
                continue

            # Map agent name to leaderboard key
            target_key = None
            if "MarketAnalyst" in agent.name:
                target_key = "tech_pred"
            elif "Visual" in agent.name:
                target_key = "visual_pred"
            elif "Social" in agent.name:
                target_key = "social_pred"

            if target_key and target_key in leaderboard:
                stats = leaderboard[target_key]
                acc = stats.get("accuracy", 0.5)

                # Evolution Logic
                original_eps = agent.epsilon

                # If accuracy is good, reduce exploration
                if acc > 0.6:
                    agent.epsilon = max(0.01, agent.epsilon * 0.95)
                # If accuracy is poor, increase exploration
                elif acc < 0.4:
                    agent.epsilon = min(0.3, agent.epsilon * 1.1)

                if original_eps != agent.epsilon:
                    logger.info(f"Evolved {agent.name} epsilon: {original_eps:.3f} -> {agent.epsilon:.3f}")
