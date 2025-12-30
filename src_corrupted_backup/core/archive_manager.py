import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import hashlib
logger = logging.getLogger(__name__)
class ArchiveManager:
#     """
#     The Eternal Archive - Preserves all decision-making context for posterity.
#     Creates an immutable record of the AI's evolution and learning journey.
#     """
def __init__(self, archive_dir: str = "data/eternal_archive"):
        pass
        self.archive_dir = archive_dir
        self.decisions_dir = os.path.join(archive_dir, "decisions")
        self.knowledge_dir = os.path.join(archive_dir, "knowledge")
        self.predictions_dir = os.path.join(archive_dir, "predictions")
            for directory in [self.decisions_dir, self.knowledge_dir, self.predictions_dir]:
                os.makedirs(directory, exist_ok=True)
    def archive_decision(
                self,
        ticker: str,
#         """
#         decision: str,
#         context: Dict[str, Any],
#         agents_debate: List[Dict[str, Any]],
#         final_confidence: float,
#     ) -> str:
#         """
Archives a complete decision with full context.
        Returns the archive ID (hash-based immutable reference).
                timestamp = datetime.now()
# Create immutable archive entry
        archive_entry = {
            "archive_version": "1.0-ETERNAL",
            "timestamp": timestamp.isoformat(),
            "ticker": ticker,
            "decision": decision,
            "confidence": final_confidence,
            "context": {
                "market_data": context.get("market_stats", {}),
                "technical_indicators": context.get("technical", {}),
                "macro_environment": context.get("macro", {}),
                "news_sentiment": context.get("news", {}),
                "paradigm": context.get("paradigm", "UNKNOWN"),
            },
            "deliberation": {
                "agents_involved": [a.get("agent_name") for a in agents_debate],
                "debate_log": agents_debate,
                "consensus_strength": self._calculate_consensus(agents_debate),
            },
            "metadata": {
                "dynasty_phase": context.get("dynasty_objective", "FOUNDATION"),
                "strategy_generation": context.get("active_strategies", []),
            },
        }
# Generate immutable ID
archive_id = self._generate_archive_id(archive_entry)
        archive_entry["archive_id"] = archive_id
# Save to file system
date_path = timestamp.strftime("%Y/%m")
        save_dir = os.path.join(self.decisions_dir, date_path)
        os.makedirs(save_dir, exist_ok=True)
            filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{ticker}_{archive_id[:8]}.json"
        filepath = os.path.join(save_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(archive_entry, f, indent=2, ensure_ascii=False)
            logger.info(f"📚 [ARCHIVE] Decision archived: {archive_id[:12]}... ({ticker})")
        return archive_id
#     """
#     def archive_prediction(
#                 self,
#         ticker: str,
#         """
        prediction_type: str,
        predicted_value: float,
        prediction_horizon: str,
        model_name: str,
        confidence: float,
    ) -> str:
        pass
#         """
#         Archives a prediction for future verification.
#                 timestamp = datetime.now()
#             prediction_entry = {
#             "prediction_id": hashlib.sha256(f"{ticker}{timestamp.isoformat()}{model_name}".encode()).hexdigest(),
#             "timestamp": timestamp.isoformat(),
#             "ticker": ticker,
#             "type": prediction_type,
#             "predicted_value": predicted_value,
#             "horizon": prediction_horizon,
#             "model": model_name,
#             "confidence": confidence,
#             "verification_status": "PENDING",
#             "actual_outcome": None,
#             "verification_date": None,
#         }
#             date_path = timestamp.strftime("%Y/%m")
#         save_dir = os.path.join(self.predictions_dir, date_path)
#         os.makedirs(save_dir, exist_ok=True)
#             filename = f"pred_{timestamp.strftime('%Y%m%d_%H%M%S')}_{ticker}.json"
#         filepath = os.path.join(save_dir, filename)
#             with open(filepath, "w", encoding="utf-8") as f:
#                 json.dump(prediction_entry, f, indent=2, ensure_ascii=False)
#             return prediction_entry["prediction_id"]
#     """
def verify_predictions(self, current_market_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
#         """
#         Verifies past predictions against actual outcomes.
#         Returns verification statistics.
#                 verified_count = 0
#         correct_predictions = 0
#         total_error = 0.0
# # Scan prediction files that are ready for verification
#         for root, dirs, files in os.walk(self.predictions_dir):
#             for file in files:
#                 if not file.startswith("pred_"):
#                     continue
#                     filepath = os.path.join(root, file)
#                 try:
#                     with open(filepath, "r", encoding="utf-8") as f:
#                         pred = json.load(f)
#                         if pred.get("verification_status") == "VERIFIED":
#                             continue
# # Check if prediction horizon has passed
#                     pred_time = datetime.fromisoformat(pred["timestamp"])
#                     horizon_hours = self._parse_horizon(pred["horizon"])
#                         if (datetime.now() - pred_time).total_seconds() / 3600 >= horizon_hours:
#                             # Verify prediction
#                         ticker = pred["ticker"]
#                         actual = current_market_data.get(ticker, {}).get("Close")
#                             if actual:
#                                 pred["actual_outcome"] = actual
#                             pred["verification_status"] = "VERIFIED"
#                             pred["verification_date"] = datetime.now().isoformat()
#                             pred["error"] = abs(pred["predicted_value"] - actual)
# # Update file
#                             with open(filepath, "w", encoding="utf-8") as f:
#                                 json.dump(pred, f, indent=2, ensure_ascii=False)
#                                 verified_count += 1
#                             if pred["error"] / actual < 0.05:  # Within 5%
#                                 correct_predictions += 1
#                             total_error += pred["error"]
#                     except Exception as e:
#                         logger.error(f"Error verifying prediction {file}: {e}")
#             return {
#             "verified_count": verified_count,
#             "accuracy_rate": correct_predictions / verified_count if verified_count > 0 else 0.0,
#             "average_error": total_error / verified_count if verified_count > 0 else 0.0,
#         }
#     """
def extract_knowledge_patterns(self, lookback_days: int = 90) -> Dict[str, Any]:
        pass
#         """
#         Analyzes archived decisions to extract universal patterns.
#                 patterns = {
#             "successful_paradigms": {},
#             "agent_performance": {},
#             "common_failure_modes": [],
#             "optimal_conditions": {},
#         }
# # Scan recent decisions
#         cutoff_date = datetime.now().timestamp() - (lookback_days * 86400)
#             for root, dirs, files in os.walk(self.decisions_dir):
#                 for file in files:
#                     if not file.endswith(".json"):
#                     continue
#                     filepath = os.path.join(root, file)
#                 try:
#                     with open(filepath, "r", encoding="utf-8") as f:
#                         decision = json.load(f)
#                         decision_time = datetime.fromisoformat(decision["timestamp"]).timestamp()
#                     if decision_time < cutoff_date:
#                         continue
# # Extract patterns (simplified)
#                     paradigm = decision["context"].get("paradigm", "UNKNOWN")
#                     if paradigm not in patterns["successful_paradigms"]:
#                         patterns["successful_paradigms"][paradigm] = {"count": 0, "avg_confidence": 0.0}
#                         patterns["successful_paradigms"][paradigm]["count"] += 1
#                     patterns["successful_paradigms"][paradigm]["avg_confidence"] += decision["confidence"]
#                     except Exception as e:
#                         logger.error(f"Error extracting patterns from {file}: {e}")
# # Normalize averages
#         for paradigm in patterns["successful_paradigms"]:
#             count = patterns["successful_paradigms"][paradigm]["count"]
#             if count > 0:
#                 patterns["successful_paradigms"][paradigm]["avg_confidence"] /= count
#             return patterns
#     """
def _generate_archive_id(self, entry: Dict[str, Any]) -> str:
#         """Generates immutable hash-based ID for archive entry."""
content = json.dumps(entry, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    def _calculate_consensus(self, debate: List[Dict[str, Any]]) -> float:
#         """Calculates how unified the agents were in their decision."""
if not debate:
            return 0.0
            decisions = [a.get("decision", "HOLD") for a in debate]
        most_common = max(set(decisions), key=decisions.count)
        consensus = decisions.count(most_common) / len(decisions)
        return consensus
    def _parse_horizon(self, horizon: str) -> float:
#         """Converts horizon string to hours."""
if "day" in horizon.lower():
            return float(horizon.split()[0]) * 24
        elif "hour" in horizon.lower():
            return float(horizon.split()[0])
        elif "week" in horizon.lower():
            return float(horizon.split()[0]) * 24 * 7
        return 24.0  # Default 1 day


# """
