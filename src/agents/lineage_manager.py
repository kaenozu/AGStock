import logging
import json
import os
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class LineageManager:
    """
    Manages the 'AI Dynasty' - child agents spawned for specialized tasks.
    Tracks lineage, performance, and resource allocation per agent.
    """

    def __init__(self, storage_path: str = "data/lineage.json"):
        self.storage_path = storage_path
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self.dynasty = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        """Load dynasty data from storage."""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save(self):
        """Save dynasty data to storage."""
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.dynasty, f, indent=4)

    def spawn_child(self, name: str, focus: str, capital_allocation: float):
        """Spawn a new child agent."""
        child = {
            "id": f"GEN-{len(self.dynasty) + 1}",
            "name": name,
            "focus": focus,
            "spawned_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "capital_allocation": capital_allocation,
            "performance_mtd": 0.0,
            "status": "ACTIVE",
        }
        self.dynasty.append(child)
        self._save()
        logger.info(f"👶 [DYNASTY] Child spawned: {name} (Focus: {focus})")
        return child

    def get_dynasty_status(self) -> List[Dict[str, Any]]:
        """Get current dynasty status."""
        return self.dynasty

    def rebalance_dynasty(self, total_capital: float):
        """Simulates reallocation of life-force (capital) based on performance."""
        if not self.dynasty:
            return
        # Simple redistribution logic based on MTD performance
        for child in self.dynasty:
            if child["performance_mtd"] < -5.0:
                child["status"] = "HIBERNATING"
                child["capital_allocation"] *= 0.5
            elif child["performance_mtd"] > 5.0:
                child["capital_allocation"] *= 1.2
        self._save()
