"""
Avatar Council
Spawns and manages 100 distinct AI personas for hyper-diverse investment debate.
Implements Council Meta-Learning (Meritocracy through performance tracking).
"""

import json
import logging
import os
import random
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AvatarCouncil:
    """
    Simulation of a 'Wisdom of the Crowds' approach using 100 AI personas.
    Tracks individual accuracy and weights votes dynamically based on past performance.
    """

    ARCHETYPES = [
        "Stoic Conservative",
        "Aggressive Disruptor",
        "Macro Oracle",
        "Technical Monk",
        "Chaos Theory Analyst",
        "Value Archeologist",
        "Speed Demon (HFT)",
        "Sentiment Whisperer",
        "Deep History Scholar",
    ]

    def __init__(self, persistence_path: str = "data/council_state.json"):
        self.avatar_count = 100
        self.persistence_path = persistence_path
        os.makedirs(os.path.dirname(persistence_path), exist_ok=True)
        self.personas = self._load_or_spawn_personas()

    def _load_or_spawn_personas(self) -> List[Dict[str, Any]]:
        """Loads council state from disk or initializes a fresh council."""
        if os.path.exists(self.persistence_path):
            try:
                with open(self.persistence_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load council state: {e}")

        # Fresh Spawn
        logger.info("🏛️ Spawning 100 new AI council personas...")
        personas = []
        for i in range(self.avatar_count):
            arch = random.choice(self.ARCHETYPES)
            personas.append({
                "id": f"AV-{(i+1):03d}",
                "name": f"{arch} #{i+1}",
                "trait": arch,
                "weight": 1.0,
                "accuracy_score": 0.5,
                "vote_history": [],
                "risk_appetite": random.uniform(0.1, 1.0),
                "pending_votes": []
            })
        self._save_state(personas)
        return personas

    def _save_state(self, personas: List[Dict[str, Any]]):
        """Persists council state to disk."""
        try:
            with open(self.persistence_path, "w", encoding="utf-8") as f:
                json.dump(personas, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save council state: {e}")

    def hold_grand_assembly(self, ticker: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulates a weighted vote from 100 personas based on their merit score.
        """
        weighted_votes = []
        raw_votes = []
        detailed_votes = []
        
        total_weight = sum([p["weight"] for p in self.personas])
        norm_factor = total_weight / self.avatar_count if total_weight > 0 else 1.0

        for p in self.personas:
            # Base logic score
            base_score = random.uniform(20, 80)
            
            # Apply individual bias/traits
            if "Conservative" in p["trait"]:
                base_score -= 10
            elif "Aggressive" in p["trait"]:
                base_score += 10
            
            score = max(0, min(100, base_score))
            raw_votes.append(score)
            
            # Apply meritocracy weight
            weighted_votes.append(score * (p["weight"] / norm_factor))
            
            stance = "NEUTRAL"
            if score > 60: stance = "BULL"
            elif score < 40: stance = "BEAR"
            
            vote_obj = {
                "id": p["id"],
                "name": p["name"],
                "score": score,
                "weight": p["weight"],
                "stance": stance,
                "quote": self._generate_quote(p["trait"], stance)
            }
            detailed_votes.append(vote_obj)
            
            # Record for future feedback
            p.setdefault("pending_votes", []).append({
                "ticker": ticker,
                "stance": stance,
                "timestamp": datetime.now().isoformat()
            })

        self._save_state(self.personas)
        
        consensus_score = sum(weighted_votes) / len(weighted_votes)
        
        clusters = {
            "Bulls": len([v for v in raw_votes if v > 60]),
            "Bears": len([v for v in raw_votes if v < 40]),
            "Neutral": len([v for v in raw_votes if 40 <= v <= 60]),
        }
        
        logger.info(f"🏛️ Assembly for {ticker} complete. Weighted Consensus: {consensus_score:.1f}")
        
        return {
            "avg_score": consensus_score,
            "clusters": clusters,
            "sample_shouts": [v["quote"] for v in detailed_votes[:3]],
            "all_votes": detailed_votes
        }

    def update_meritocracy(self, ticker: str, outcome: str):
        """Rewards accurate personas and penalizes inaccurate ones."""
        logger.info(f"🧬 Updating Council Meritocracy for {ticker} (Outcome: {outcome})")
        
        for p in self.personas:
            pending = p.get("pending_votes", [])
            matches = [v for v in pending if v["ticker"] == ticker]
            
            if not matches:
                continue
                
            vote = matches[0]
            if outcome != "NEUTRAL":
                if vote["stance"] == outcome:
                    p["weight"] = min(5.0, p["weight"] * 1.05)
                    p["accuracy_score"] = min(1.0, p["accuracy_score"] + 0.01)
                elif vote["stance"] != "NEUTRAL":
                    p["weight"] = max(0.2, p["weight"] * 0.95)
                    p["accuracy_score"] = max(0.0, p["accuracy_score"] - 0.01)

            # Clear successfully processed pending votes
            p["pending_votes"] = [v for v in pending if v["ticker"] != ticker]

        self._save_state(self.personas)

    def _generate_quote(self, trait: str, stance: str) -> str:
        """Generates a pseudo-random shout based on persona trait."""
        if stance == "BULL":
            quotes = ["強気の見通しです！", "買いの好機と見ます。", "上昇トレンドに乗りましょう。"]
        elif stance == "BEAR":
            quotes = ["警戒が必要です。", "売り圧力が強いと見ています。", "一度撤退すべきでしょう。"]
        else:
            quotes = ["様子見が賢明です。", "材料不足ですね。", "現在はレンジ相場です。"]
        return f"[{trait}] {random.choice(quotes)}"

from datetime import datetime
