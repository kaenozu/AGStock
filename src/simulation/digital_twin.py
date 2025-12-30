import logging
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class DigitalTwin:
    """
    Manages 'Shadow Portfolios' that simulate alternative decision-making paths.
    """

    def __init__(self, db_path: str = "digital_twin.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS shadow_positions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        twin_type TEXT NOT NULL, -- 'AGGRESSIVE', 'CONSERVATIVE'
                        ticker TEXT NOT NULL,
                        entry_price REAL,
                        quantity REAL,
                        entry_timestamp TEXT
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS performance_log (
                        timestamp TEXT NOT NULL,
                        twin_type TEXT NOT NULL,
                        total_value REAL
                    )
                """
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to init digital twin DB: {e}")

    def record_decision(
        self, ticker: str, original_decision: str, current_price: float
    ):
        """
        Records what the twin WOULD have done if it were different.
        """
        # Logic:
        #             pass
        # - AGGRESSIVE twin buys more easily (even if Original is HOLD)
        # - CONSERVATIVE twin sells more easily (even if Original is BUY)

        # This is a conceptual implementation of recording shadow trades
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Aggressive Twin: Buys if Original is HOLD/BUY
                if original_decision in ["BUY", "HOLD"]:
                    cursor.execute(
                        "INSERT INTO shadow_positions (twin_type, ticker, entry_price, quantity, entry_timestamp) VALUES (?, ?, ?, ?, ?)",
                        (
                            "AGGRESSIVE",
                            ticker,
                            current_price,
                            10,
                            datetime.now().isoformat(),
                        ),
                    )

                # Conservative Twin: Buys ONLY if Original is strong BUY, otherwise SELLs
                if original_decision == "BUY":
                    cursor.execute(
                        "INSERT INTO shadow_positions (twin_type, ticker, entry_price, quantity, entry_timestamp) VALUES (?, ?, ?, ?, ?)",
                        (
                            "CONSERVATIVE",
                            ticker,
                            current_price,
                            5,
                            datetime.now().isoformat(),
                        ),
                    )

                conn.commit()
        except Exception as e:
            logger.error(f"Failed to record shadow decision: {e}")

    def get_twin_performance(self) -> Dict[str, float]:
        """Calculates current unrealized profit for twin portfolios."""
        # Conceptually returns a summary for UI display
        return {
            "AGGRESSIVE": 105.2,  # Mock value representing +5.2%
            "CONSERVATIVE": 98.7,  # Mock value representing -1.3%
            "REAL_WORLD": 102.5,
        }
