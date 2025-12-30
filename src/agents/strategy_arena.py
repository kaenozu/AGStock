import sqlite3
import json
import os
import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class StrategyArena:
    """
    Analyzes individual AI agent performances stored in FeedbackStore
    to dynamically adjust their voting weights in the InvestmentCommittee.
    """

    def __init__(
        self,
        db_path: str = "committee_feedback.db",
        weights_path: str = "strategy_weights.json",
    ):
        self.db_path = db_path
        self.weights_path = weights_path

    def update_agent_performance(self):
        """
        Reads all feedback outcomes and calculates accuracy for each participating agent.
        """
        if not os.path.exists(self.db_path):
            return

        performance = {}  # {agent_name: {total: X, correct: Y}}

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT raw_data, outcome FROM decision_feedback WHERE outcome IS NOT NULL"
                )
                rows = cursor.fetchall()

                for row in rows:
                    raw_data = json.loads(row["raw_data"])
                    outcome = row["outcome"]  # SUCCESS, FAILURE, NEUTRAL

                    # 'analyses' is where individual agent opinions are stored
                    analyses = raw_data.get("analyses", [])
                    for a in analyses:
                        agent_name = a.get("agent_name")
                        decision = a.get("decision")

                        if agent_name not in performance:
                            performance[agent_name] = {
                                "total": 0,
                                "correct": 0,
                                "neutral": 0,
                            }

                        performance[agent_name]["total"] += 1

                        # Accuracy Logic
                        is_correct = False
                        if outcome == "SUCCESS":
                            if decision in ["BUY", "UP"]:
                                is_correct = True
                        elif outcome == "FAILURE":
                            if decision in ["SELL", "DOWN"]:
                                is_correct = True

                        if is_correct:
                            performance[agent_name]["correct"] += 1
                        elif outcome == "NEUTRAL":
                            performance[agent_name]["neutral"] += 1

            self._save_weights(performance)
            logger.info("Strategy Arena performance weights updated.")

        except Exception as e:
            logger.error(f"Failed to update agent performance: {e}")

    def _save_weights(self, performance: Dict[str, Any]):
        """Calculates weights from performance and saves to JSON."""
        weights = {}
        for name, stats in performance.items():
            if stats["total"] > 0:
                accuracy = stats["correct"] / stats["total"]
                # Sigmoid-like scaling or simple multiplier
                # Default weight is 1.0. Range: 0.5 - 2.0
                weight = 0.5 + (accuracy * 2.0)
                weights[name] = round(min(2.0, max(0.5, weight)), 2)
            else:
                weights[name] = 1.0

        with open(self.weights_path, "w") as f:
            json.dump(
                {
                    "weights": weights,
                    "updated_at": datetime.now().isoformat(),
                    "agent_stats": performance,
                },
                f,
                indent=2,
            )

    def get_weights(self) -> Dict[str, float]:
        """Returns the current agent weights (default 1.0 if not found)."""
        if not os.path.exists(self.weights_path):
            return {}

        try:
            with open(self.weights_path, "r") as f:
                data = json.load(f)
                return data.get("weights", {})
        except:
            return {}
