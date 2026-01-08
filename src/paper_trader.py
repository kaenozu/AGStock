"""ペーパートレード機能を提供するモジュール。

このモジュールは、実際の資金を使用せずに取引戦略をテストするための仮想環境を提供します。
SQLiteデータベースを使用してポジション、残高、および注文履歴を管理します。
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Union, Any, Optional
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class PaperTrader:
    """ペーパートレード機能を提供するクラス。"""

    def __init__(self, db_path: str = "paper_trading.db", initial_capital: float = None):
        self.db_path = db_path

        # Load initial capital from config.json if not specified
        if initial_capital is None:
            try:
                config_path = Path("config.json")
                if config_path.exists():
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    initial_capital = config.get("paper_trading", {}).get("initial_capital", 1000000)
                else:
                    initial_capital = 1000000  # Default 1M JPY
            except Exception as e:
                logger.error(f"Error loading initial capital: {e}")
                initial_capital = 1000000  # Fallback to 1M JPY

        self.initial_capital = float(initial_capital)
        self.conn = sqlite3.connect(db_path)
        self._initialize_database()

    def _initialize_database(self):
        """Initialize the SQLite database with required tables."""
        cursor = self.conn.cursor()
        
        # パフォーマンス向上のための設定
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")

        # Create accounts table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY,
                initial_capital REAL,
                current_balance REAL
            )
        """
        )

        # Create positions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY,
                ticker TEXT UNIQUE,
                quantity INTEGER,
                avg_price REAL,
                current_price REAL DEFAULT 0.0,
                entry_price REAL DEFAULT 0.0,
                entry_date TEXT,
                stop_price REAL DEFAULT 0.0,
                highest_price REAL DEFAULT 0.0
            )
        """
        )

        # Create orders table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                ticker TEXT,
                action TEXT,
                quantity INTEGER,
                price REAL,
                strategy_name TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        # インデックス追加
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_ticker_time ON orders (ticker, timestamp)")

        # Create balance table for equity history
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS balance (
                date TEXT PRIMARY KEY,
                total_equity REAL,
                cash REAL,
                invested REAL
            )
        """
        )
        # 日付インデックス
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_balance_date ON balance (date)")

        # Initialize account balance if not exists
        cursor.execute("SELECT COUNT(*) FROM accounts")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """
                INSERT INTO accounts (initial_capital, current_balance)
                VALUES (?, ?)
            """,
                (self.initial_capital, self.initial_capital),
            )

        self.conn.commit()

    def optimize_database(self):
        """データベースの最適化を実行"""
        try:
            self.conn.execute("ANALYZE")
            self.conn.execute("VACUUM")
            logger.info("PaperTrader database optimized.")
        except Exception as e:
            logger.error(f"DB optimization error: {e}")

    def get_balance(self) -> float:
        """Get the current cash balance."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT current_balance FROM accounts LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else 0.0

    def get_position(self, ticker: str) -> Dict[str, Union[int, float]]:
        """Get the current position for a given ticker."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT quantity, avg_price FROM positions WHERE ticker = ?", (ticker,))
        result = cursor.fetchone()
        if result:
            return {"quantity": result[0], "avg_price": result[1]}
        return {"quantity": 0, "avg_price": 0.0}

    def get_positions(self) -> pd.DataFrame:
        """Get all open positions as a DataFrame."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT ticker, quantity, avg_price, stop_price, highest_price FROM positions WHERE quantity > 0")
        data = cursor.fetchall()
        
        if not data:
            return pd.DataFrame(columns=["ticker", "quantity", "avg_price", "stop_price", "highest_price", "entry_price", "unrealized_pnl"])
            
        df = pd.DataFrame(data, columns=["ticker", "quantity", "avg_price", "stop_price", "highest_price"])
        df["entry_price"] = df["avg_price"]
        df["unrealized_pnl"] = 0.0
        df["highest_price"] = df.apply(lambda row: row["highest_price"] if row["highest_price"] > 0 else row["avg_price"], axis=1)
        return df

    def update_position_stop(self, ticker: str, stop_price: float, highest_price: float) -> bool:
        """Update stop price and highest price for a position."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE positions SET stop_price = ?, highest_price = ? WHERE ticker = ?",
                (stop_price, highest_price, ticker)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating position stop: {e}")
            return False

    def get_trade_history(self, limit: int = 1000, start_date: Optional[datetime] = None) -> pd.DataFrame:
        """Get trade history as DataFrame."""
        cursor = self.conn.cursor()
        if start_date:
            query = "SELECT timestamp, ticker, action, quantity, price, strategy_name FROM orders WHERE timestamp >= ? ORDER BY timestamp DESC LIMIT ?"
            cursor.execute(query, (start_date.isoformat(), limit))
        else:
            query = "SELECT timestamp, ticker, action, quantity, price, strategy_name FROM orders ORDER BY timestamp DESC LIMIT ?"
            cursor.execute(query, (limit,))
            
        data = cursor.fetchall()
        
        if not data:
            return pd.DataFrame(columns=["timestamp", "ticker", "action", "quantity", "price", "strategy_name", "realized_pnl"])
            
        df = pd.DataFrame(data, columns=["timestamp", "ticker", "action", "quantity", "price", "strategy_name"])
        df["realized_pnl"] = 0.0 # Simplified
        return df

    def get_current_balance(self) -> Dict[str, float]:
        """Get balance summary including estimated total equity."""
        cash = self.get_balance()
        positions = self.get_positions()
        
        invested = 0.0
        # In a real scenario, we'd fetch latest prices. For summary, use avg_price as fallback.
        if not positions.empty:
            invested = (positions["quantity"] * positions["avg_price"]).sum()
            
        return {
            "cash": cash,
            "total_equity": cash + invested,
            "invested_amount": invested,
            "unrealized_pnl": 0.0
        }

    def execute_order(self, order: Any) -> bool:
        """Execute a trade order."""
        try:
            balance = self.get_balance()
            position = self.get_position(order.ticker)

            cost = order.quantity * order.price
            if order.action == "BUY":
                if cost > balance:
                    logger.warning(f"Insufficient balance for order: {order}")
                    return False

                new_balance = balance - cost
                cursor = self.conn.cursor()
                cursor.execute("UPDATE accounts SET current_balance = ? WHERE id = 1", (new_balance,))

                new_quantity = position["quantity"] + order.quantity
                if position["quantity"] > 0:
                    new_avg_price = (
                        (position["quantity"] * position["avg_price"]) + (order.quantity * order.price)
                    ) / new_quantity
                else:
                    new_avg_price = order.price

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO positions (ticker, quantity, avg_price, highest_price)
                    VALUES (?, ?, ?, ?)
                """,
                    (order.ticker, new_quantity, new_avg_price, max(new_avg_price, order.price)),
                )

            elif order.action == "SELL":
                if order.quantity > position["quantity"]:
                    logger.warning(f"Trying to sell more than owned: {order}")
                    return False

                proceeds = order.quantity * order.price
                new_balance = balance + proceeds
                cursor = self.conn.cursor()
                cursor.execute("UPDATE accounts SET current_balance = ? WHERE id = 1", (new_balance,))

                new_quantity = position["quantity"] - order.quantity
                if new_quantity == 0:
                    cursor.execute("DELETE FROM positions WHERE ticker = ?", (order.ticker,))
                else:
                    cursor.execute(
                        "UPDATE positions SET quantity = ? WHERE ticker = ?",
                        (new_quantity, order.ticker),
                    )

            # Log order
            cursor.execute(
                """
                INSERT INTO orders (ticker, action, quantity, price, strategy_name)
                VALUES (?, ?, ?, ?, ?)
            """,
                (order.ticker, order.action, order.quantity, order.price, getattr(order, "strategy", None)),
            )

            self.conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error executing order: {e}")
            self.conn.rollback()
            return False

    def execute_trade(self, ticker: str, action: str, quantity: int, price: float, reason: str = "", strategy: str = None) -> bool:
        """Simplified trade execution."""
        class SimpleOrder:
            def __init__(self, t, a, q, p, s):
                self.ticker = t
                self.action = a
                self.quantity = q
                self.price = p
                self.strategy = s
        
        return self.execute_order(SimpleOrder(ticker, action, quantity, price, strategy))

    def update_daily_equity(self):
        """Update daily equity snapshot in database."""
        try:
            summary = self.get_current_balance()
            today = datetime.now().strftime("%Y-%m-%d")
            
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO balance (date, total_equity, cash, invested)
                VALUES (?, ?, ?, ?)
            """,
                (today, summary["total_equity"], summary["cash"], summary["invested_amount"]),
            )
            self.conn.commit()
            logger.info(f"Daily equity updated for {today}: {summary['total_equity']:,.0f}")
        except Exception as e:
            logger.error(f"Error updating daily equity: {e}")

    def get_equity_history(self) -> pd.DataFrame:
        """Get historical equity data."""
        try:
            query = "SELECT date, total_equity, cash, invested FROM balance ORDER BY date ASC"
            df = pd.read_sql_query(query, self.conn)
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                df.set_index("date", inplace=True)
            return df
        except Exception as e:
            logger.error(f"Error fetching equity history: {e}")
            return pd.DataFrame()

    def get_portfolio_value(self, prices: Dict[str, float]) -> float:
        """Calculate total portfolio value based on current prices."""
        total_value = self.get_balance()
        positions = self.get_positions()

        for _, row in positions.iterrows():
            ticker = row["ticker"]
            if ticker in prices:
                total_value += row["quantity"] * prices[ticker]
            else:
                total_value += row["quantity"] * row["avg_price"]

        return total_value

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()