"""ペーパートレード機能を提供するモジュール。

このモジュールは、実際の資金を使用せずに取引戦略をテストするための仮想環境を提供します。
SQLiteデータベースを使用してポジション、残高、および注成履歴を管理します。
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Union, Any


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

    def __init__(self, db_path: str = "paper_trading.db", initial_capital: float = None):
        self.db_path = db_path

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

        # Create positions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY,
                ticker TEXT UNIQUE,
                quantity INTEGER,
                avg_price REAL
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
        """Get the current cash balance.

        Returns:
            float: Current cash balance.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT current_balance FROM accounts LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else 0.0

    def get_position(self, ticker: str) -> Dict[str, Union[int, float]]:
        """Get the current position for a given ticker.

        Args:
            ticker (str): Stock ticker symbol.

        Returns:
            Dict[str, Union[int, float]]: Dictionary containing 'quantity' and 'avg_price'.
                                          Returns {'quantity': 0, 'avg_price': 0.0} if no position.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT quantity, avg_price FROM positions WHERE ticker = ?", (ticker,))
        result = cursor.fetchone()
        if result:
            return {"quantity": result[0], "avg_price": result[1]}
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
                    INSERT OR REPLACE INTO positions (ticker, quantity, avg_price)
                    VALUES (?, ?, ?)
                """,
                    (order.ticker, new_quantity, new_avg_price),
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
