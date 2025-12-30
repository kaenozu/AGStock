import logging
import sqlite3
from datetime import datetime
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)


class DataManager:
    def __init__(self, db_path: str = "stock_data.db"):
        pass
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        #         """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Create table for OHLCV data
        cursor.execute()
        # Create index for faster queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ticker_date ON stock_data (ticker, date)"
        )
        conn.close()

    def save_data(self, df: pd.DataFrame, ticker: str):
        pass
        if df is None or df.empty:
            return
            conn = sqlite3.connect(self.db_path)
        # Prepare data for insertion
        data_to_save = df.copy()
        data_to_save = data_to_save.reset_index()
        # Ensure columns exist and rename if necessary (yfinance usually gives Date, Open, High, Low, Close, Volume)
        # We map them to lowercase for DB consistency
        # Handle index name
        if "Date" not in data_to_save.columns and "date" not in data_to_save.columns:
            if "index" in data_to_save.columns:
                data_to_save = data_to_save.rename(columns={"index": "date"})
            else:
                # If index was unnamed, reset_index might have created 'index' or just used the first column?
                # Usually it creates 'index' if name is None.
                pass
            column_map = {
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        data_to_save = data_to_save.rename(columns=column_map)
        data_to_save["ticker"] = ticker
        # Convert date to string for SQLite compatibility
        if "date" in data_to_save.columns:
            data_to_save["date"] = pd.to_datetime(data_to_save["date"]).dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        # Keep only relevant columns
        cols = ["ticker", "date", "open", "high", "low", "close", "volume"]
        data_to_save = data_to_save[cols]

    # Convert date to string for SQLite compatibility if needed, but pandas to_sql handles timestamps well usually.
    # However, for explicit control, we can ensure it's datetime.
    # Use 'replace' or 'append'. Since we have a primary key, 'append' might fail on duplicates.
    # We want 'upsert'. SQLite 3.24+ supports ON CONFLICT.
    # Pandas to_sql doesn't support upsert natively easily without a temp table or method customization.
    # For simplicity and robustness, we can delete existing range and insert new, or use a loop.
    # Given the volume, let's try a custom method for upsert.
    #     """
    #     def load_data(
    #         self, ticker: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    #     """

    # Restore Capitalized columns for compatibility with existing code
    def get_latest_date(self, ticker: str) -> Optional[datetime]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        result = cursor.fetchone()
        conn.close()
        # SQLite stores timestamps as strings often, pandas parses them.
        # Here we need to parse if it comes back as string.
        return None

    def vacuum_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("VACUUM")
            conn.close()
            logger.info(f"Database {self.db_path} vacuumed successfully.")
        except Exception as e:
            logger.error(f"Error vacuuming database: {e}")
