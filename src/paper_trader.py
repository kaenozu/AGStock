"""ペーパートレード機能を提供するモジュール。

このモジュールは、実際の資金を使用せずに取引戦略をテストするための仮想環境を提供します。
SQLiteデータベースを使用してポジション、残高、および注成履歴を管理します。
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Union, Any
import pandas as pd


logger = logging.getLogger(__name__)


class PaperTrader:
    """ペーパートレード機能を提供するクラス。

    このクラスは、SQLiteデータベースを使用してポジション、残高、および注文履歴を管理します。
    実際の資金を使用せずに取引戦略をテストするための仮想環境を提供します。

    Attributes:
        db_path (str): SQLiteデータベースファイルのパス。
        initial_capital (float): 初期資本金。
        conn (sqlite3.Connection): データベース接続オブジェクト。
    """

    def __init__(self, db_path: str = "paper_trading.db", initial_capital: float = None, **kwargs):
        self.db_path = db_path
        self.use_realtime_fallback = kwargs.get("use_realtime_fallback", False)

        # Load initial capital from config.json if not specified
        if initial_capital is None:
            try:
                # Use standard JSON load directly here to avoid circular dependencies with schemas
                # or just as a fallback.
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

        # Create positions table (Expanded for compatibility)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY,
                ticker TEXT UNIQUE,
                quantity INTEGER,
                avg_price REAL,
                entry_price REAL,
                entry_date TEXT,
                current_price REAL,
                unrealized_pnl REAL,
                stop_price REAL,
                highest_price REAL
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
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

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

    def get_balance(self) -> float:
        """Get the current cash balance."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT current_balance FROM accounts LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else 0.0

    def get_current_balance(self, use_realtime_fallback: bool = False) -> Dict[str, float]:
        """Get current balance details including total equity."""
        balance = self.get_balance()
        positions = self.get_positions(use_realtime_fallback=use_realtime_fallback)
        
        pos_value = 0.0
        if not positions.empty:
            if "market_value" in positions.columns:
                pos_value = positions["market_value"].sum()
            elif "quantity" in positions.columns and "current_price" in positions.columns:
                pos_value = (positions["quantity"] * positions["current_price"]).sum()
            else:
                pos_value = (positions["quantity"] * positions["avg_price"]).sum()
                
        return {"cash": balance, "total_equity": balance + pos_value}

    def get_positions(self, use_realtime_fallback: bool = None) -> pd.DataFrame:
        """Get all current positions as a DataFrame."""
        if use_realtime_fallback is None:
            use_realtime_fallback = self.use_realtime_fallback

        query = "SELECT * FROM positions WHERE quantity > 0"
        df = pd.read_sql_query(query, self.conn)
        
        if df.empty:
            return pd.DataFrame(columns=["ticker", "quantity", "avg_price", "entry_price", "current_price", "market_value"])

        if use_realtime_fallback:
            from src.data_loader import fetch_realtime_data
            for idx, row in df.iterrows():
                ticker = row["ticker"]
                try:
                    rt_data = fetch_realtime_data(ticker)
                    if not rt_data.empty:
                        curr_price = rt_data["Close"].iloc[-1]
                        df.at[idx, "current_price"] = curr_price
                except Exception as e:
                    logger.warning(f"Failed to fetch realtime data for {ticker}: {e}")

        # Add calculated columns
        df["market_value"] = df["quantity"] * df["current_price"]
        
        # Set index to ticker for compatibility with some tests
        df.set_index("ticker", inplace=True, drop=False)
        return df

    def update_daily_equity(self):
        """Update daily equity by recalculating from positions (compatibility)."""
        # This is a dummy for now but needs to exist
        pass

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_trade_history(self, limit: int = 100, start_date=None) -> pd.DataFrame:
        """Get trade history as a DataFrame."""
        import pandas as pd

        query = "SELECT * FROM orders"
        if start_date:
            query += f" WHERE timestamp >= '{start_date}'"
        query += f" ORDER BY timestamp DESC LIMIT {limit}"
        df = pd.read_sql_query(query, self.conn)
        if not df.empty and "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def execute_trade(self, ticker: str, action: str, quantity: int, price: float, reason: str = None) -> bool:
        """Execute a trade (compatibility wrapper)."""

        class SimpleOrder:
            def __init__(self, t, a, q, p):
                self.ticker = t
                self.action = a
                self.quantity = q
                self.price = p

        return self.execute_order(SimpleOrder(ticker, action, quantity, price))

    def update_position_stop(self, ticker: str, stop_price: float, highest_price: float):
        """Update stop price and highest price for a position."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE positions SET stop_price = ?, highest_price = ? WHERE ticker = ?",
            (stop_price, highest_price, ticker)
        )
        self.conn.commit()

    def get_position(self, ticker: str) -> Dict[str, Union[int, float]]:
        """Get the current position for a given ticker.

        Args:
            ticker (str): Stock ticker symbol.

        Returns:
            Dict[str, Union[int, float]]: Dictionary containing position data.
                                          Returns {'quantity': 0, 'avg_price': 0.0} if no position.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM positions WHERE ticker = ?", (ticker,))
        result = cursor.fetchone()
        if result:
            # column names from description
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, result))
        return {"quantity": 0, "avg_price": 0.0}

    def execute_order(self, order: Any) -> bool:
        """Execute a trade order.

        Args:
            order (Order): Order object containing ticker, action, quantity, and price.

        Returns:
            bool: True if the order was executed successfully, False otherwise.
        """
        try:
            balance = self.get_balance()
            position = self.get_position(order.ticker)

            cost = order.quantity * order.price
            if order.action == "BUY":
                if cost > balance:
                    logger.warning(f"Insufficient balance for order: {order}")
                    return False

                # Update balance
                new_balance = balance - cost
                cursor = self.conn.cursor()
                cursor.execute("UPDATE accounts SET current_balance = ? WHERE id = 1", (new_balance,))

                # Update position (average down/cost)
                new_quantity = position["quantity"] + order.quantity
                if position["quantity"] > 0:
                    new_avg_price = (
                        (position["quantity"] * position["avg_price"]) + (order.quantity * order.price)
                    ) / new_quantity
                else:
                    new_avg_price = order.price

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO positions (ticker, quantity, avg_price, entry_price, current_price, entry_date, highest_price, stop_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        order.ticker,
                        new_quantity,
                        new_avg_price,
                        new_avg_price,
                        order.price,
                        datetime.now().isoformat(),
                        new_avg_price,
                        0.0,
                    ),
                )

            elif order.action == "SELL":
                if order.quantity > position["quantity"]:
                    logger.warning(f"Trying to sell more than owned: {order}")
                    return False

                # Update balance
                proceeds = order.quantity * order.price
                new_balance = balance + proceeds
                cursor = self.conn.cursor()
                cursor.execute("UPDATE accounts SET current_balance = ? WHERE id = 1", (new_balance,))

                # Update position
                new_quantity = position["quantity"] - order.quantity
                if new_quantity == 0:
                    cursor.execute("DELETE FROM positions WHERE ticker = ?", (order.ticker,))
                else:
                    cursor.execute(
                        """
                        UPDATE positions SET quantity = ?
                        WHERE ticker = ?
                    """,
                        (new_quantity, order.ticker),
                    )

            # Log order
            cursor.execute(
                """
                INSERT INTO orders (ticker, action, quantity, price)
                VALUES (?, ?, ?, ?)
            """,
                (order.ticker, order.action, order.quantity, order.price),
            )

            self.conn.commit()
            logger.info(f"Executed order: {order}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Database error executing order: {e}")
            self.conn.rollback()
            return False
        except KeyError as e:
            logger.error(f"Missing key in order data: {e}. Order: {order}")
            return False
        except TypeError as e:
            logger.error(f"Type error in order data: {e}. Order: {order}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error executing order: {e}")
            self.conn.rollback()
            return False

    def get_portfolio_value(self, prices: Dict[str, float]) -> float:
        """Calculate the total portfolio value based on current prices.

        Args:
            prices (Dict[str, float]): Dictionary mapping tickers to current prices.

        Returns:
            float: Total portfolio value (cash + position value).
        """
        balance = self.get_balance()
        total_value = balance

        cursor = self.conn.cursor()
        cursor.execute("SELECT ticker, quantity FROM positions WHERE quantity > 0")
        positions = cursor.fetchall()

        for ticker, quantity in positions:
            if ticker in prices:
                total_value += quantity * prices[ticker]

        return total_value

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()


# END
