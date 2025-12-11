import sqlite3
import pandas as pd
import datetime
from typing import Dict, Optional
import json
import logging
from pathlib import Path
from src.data_loader import fetch_stock_data
from src.helpers import retry_with_backoff

logger = logging.getLogger(__name__)

class PaperTrader:
    def __init__(self, db_path: str = "paper_trading.db", initial_capital: float = None):
        self.db_path = db_path

        # Load initial capital from config.json if not specified
        if initial_capital is None:
            try:
                # Use standard JSON load directly here to avoid circular dependencies with schemas
                # or just as a fallback.
                config_path = Path("config.json")
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    initial_capital = config.get('paper_trading', {}).get('initial_capital', 1000000)
                else:
                    initial_capital = 1000000  # Default 1M JPY
            except Exception as e:
                logger.error(f"Error loading initial capital: {e}")
                initial_capital = 1000000

        self.initial_capital = float(initial_capital)
        self.conn = sqlite3.connect(db_path)
        self._initialize_database()

    def _initialize_database(self):
        """Create tables if they don't exist"""
        try:
            cursor = self.conn.cursor()

            # Account balance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS balance (
                    date TEXT PRIMARY KEY,
                    cash REAL,
                    total_equity REAL
                )
            ''')

            # Positions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    ticker TEXT PRIMARY KEY,
                    quantity INTEGER,
                    entry_price REAL,
                    entry_date TEXT,
                    current_price REAL,
                    unrealized_pnl REAL,
                    stop_price REAL DEFAULT 0,
                    highest_price REAL DEFAULT 0
                )
            ''')

            # Migration: Check columns
            try:
                cursor.execute('SELECT stop_price, highest_price FROM positions LIMIT 1')
            except sqlite3.OperationalError:
                logger.warning("Migrating database: adding stop_price and highest_price columns")
                cursor.execute('ALTER TABLE positions ADD COLUMN stop_price REAL DEFAULT 0')
                cursor.execute('ALTER TABLE positions ADD COLUMN highest_price REAL DEFAULT 0')

            # Orders/Trades history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    timestamp TEXT,
                    ticker TEXT,
                    action TEXT,
                    quantity INTEGER,
                    price REAL,
                    realized_pnl REAL DEFAULT 0,
                    reason TEXT
                )
            ''')

            self.conn.commit()

            # Initialize balance if empty
            cursor.execute('SELECT COUNT(*) FROM balance')
            if cursor.fetchone()[0] == 0:
                today = datetime.date.today().isoformat()
                cursor.execute('INSERT INTO balance VALUES (?, ?, ?)',
                            (today, self.initial_capital, self.initial_capital))
                self.conn.commit()
        except Exception as e:
            logger.error(f"Database initialization error: {e}")

    def get_current_balance(self) -> Dict[str, float]:
        """Get current cash and total equity"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT cash, total_equity FROM balance ORDER BY date DESC LIMIT 1')
        row = cursor.fetchone()

        # Get positions to calculate invested amount and unrealized PnL
        positions = self.get_positions()
        invested_amount = 0.0
        unrealized_pnl = 0.0

        if not positions.empty:
            invested_amount = (positions['quantity'] * positions['entry_price']).sum()
            unrealized_pnl = positions['unrealized_pnl'].sum() if 'unrealized_pnl' in positions.columns else 0.0

        if row:
            return {
                'cash': row[0],
                'total_equity': row[1],
                'invested_amount': invested_amount,
                'unrealized_pnl': unrealized_pnl
            }
