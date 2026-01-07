"""ペーパートレード機能を提供するモジュール。

このモジュールは、実際の資金を使用せずに取引戦略をテストするための仮想環境を提供します。
SQLiteデータベースを使用してポジション、残高、および注成履歴を管理します。
"""

import json
import logging
import sqlite3
import datetime
from pathlib import Path
from typing import Dict, Union, Any, List, Tuple

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
        
        # Ensure data consistency on startup
        self.recalculate_balance()

    def recalculate_balance(self):
        """
        Recalculates the current cash balance based on initial capital and order history.
        This fixes potential data corruption where orders exist but balance wasn't updated.
        """
        try:
            cursor = self.conn.cursor()
            
            # Since we don't have a deposits table, we'll assume the 'initial_capital' 
            # in the accounts table is the starting point.
            
            cursor.execute("SELECT initial_capital FROM accounts WHERE id=1")
            res = cursor.fetchone()
            if not res: return
            start_cap = res[0]
            
            # Sum up all BUYs and SELLs
            cursor.execute("SELECT action, quantity, price FROM orders")
            orders = cursor.fetchall()
            
            calculated_balance = start_cap
            
            for action, qty, price in orders:
                if price is None: continue
                amount = qty * price
                if action == "BUY":
                    calculated_balance -= amount
                elif action == "SELL":
                    calculated_balance += amount
            
            # Update the accounts table
            cursor.execute("UPDATE accounts SET current_balance = ? WHERE id = 1", (calculated_balance,))
            self.conn.commit()
            logger.info(f"Balance recalculated from history: {calculated_balance:,.0f} JPY")
            
        except Exception as e:
            logger.error(f"Failed to recalculate balance: {e}")

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

    def get_equity_history(self, days: int = None) -> pd.DataFrame:
        """Get historical equity balance as a DataFrame. Optional days limit."""
        try:
            # Check if balance table exists first
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='balance'")
            if not cursor.fetchone():
                return pd.DataFrame(columns=["date", "total_equity"])

            query = "SELECT date, total_equity FROM balance ORDER BY date ASC"
            df = pd.read_sql_query(query, self.conn)

            if days and not df.empty:
                # Basic limit if needed, but for now return all or filter here
                df = df.tail(days)

            return df
        except Exception as e:
            logger.error(f"Error getting equity history: {e}")
            return pd.DataFrame(columns=["date", "total_equity"])

    def get_positions(self) -> pd.DataFrame:
        """Get all current positions as a DataFrame with market data.

        Returns:
            pd.DataFrame: DataFrame with columns [ticker, quantity, avg_price, current_price,
                                                market_value, unrealized_pnl, unrealized_pnl_pct, sector]
        """
        try:
            cursor = self.conn.cursor()
            cursor = self.conn.cursor()
            # Select all columns to ensure we get entry_price if available
            cursor.execute("SELECT * FROM positions WHERE quantity > 0")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

            if not rows:
                return pd.DataFrame()

            positions = []
            tickers = [r[0] for r in rows]
            
            # Fetch current prices (using external data loader)
            # Avoid circular import if possible, or import inside method
            try:
                from src.data_loader import fetch_stock_data
                # Batch fetch prices for better performance
                data_map = fetch_stock_data(tickers, period="1mo") # Fetch 1mo for volatility
                prices = {}
                volatilities = {}
                for ticker in tickers:
                    df = data_map.get(ticker)
                    if df is not None and not df.empty:
                        # Price
                        prices[ticker] = float(df["Close"].iloc[-1])
                        
                        # Volatility (Std Dev of Returns for last 20 days)
                        # Approximating ATR-like movement power
                        rets = df["Close"].pct_change().dropna()
                        vol = rets.std() * df["Close"].iloc[-1] # Convert % vol to Price units
                        volatilities[ticker] = float(vol) if not pd.isna(vol) else 0.0
                    else:
                        prices[ticker] = 0.0
                        volatilities[ticker] = 0.0
            except Exception as e:
                logger.warning(f"Batch fetch failed for some tickers: {e}")
                prices = {t: 0.0 for t in tickers}
                volatilities = {t: 0.0 for t in tickers}

            # Create list of dictionaries directly from rows and columns
            temp_positions = []
            for row in rows:
                temp_positions.append(dict(zip(columns, row)))

            for pos in temp_positions:
                ticker = pos.get("ticker")
                qty = pos.get("quantity")
                
                # Robustly determine average/entry price
                # Prefer entry_price if available and valid, otherwise avg_price
                avg_p = pos.get("avg_price")
                entry_p = pos.get("entry_price")
                
                effective_avg_price = 0.0
                if entry_p is not None and entry_p > 0:
                    effective_avg_price = float(entry_p)
                elif avg_p is not None and avg_p > 0:
                    effective_avg_price = float(avg_p)

                curr_p = prices.get(ticker, effective_avg_price)
                if curr_p is None: curr_p = 0.0

                m_val = qty * curr_p
                
                if effective_avg_price > 0:
                    u_pnl = m_val - (qty * effective_avg_price)
                    u_pnl_pct = u_pnl / (qty * effective_avg_price)
                else:
                    u_pnl = 0.0
                    u_pnl_pct = 0.0
                
                positions.append({
                    "ticker": ticker,
                    "quantity": qty,
                    "avg_price": effective_avg_price,
                    "entry_price": effective_avg_price, # Alias for UI compatibility
                    "entry_date": pos.get("entry_date"),
                    "volatility": volatilities.get(ticker, 0.0), # Daily Price Move StdDev
                    "current_price": curr_p,
                    "market_value": m_val,
                    "unrealized_pnl": u_pnl,
                    "unrealized_pnl_pct": u_pnl_pct,
                    "sector": "Market" 
                })
            
            return pd.DataFrame(positions)

        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return pd.DataFrame()

    def get_current_balance(self) -> Dict[str, float]:
        """Get comprehensive balance overview."""
        cash = self.get_balance()
        positions_df = self.get_positions()
        
        if not positions_df.empty:
            market_value = positions_df["market_value"].sum()
            unrealized_pnl = positions_df["unrealized_pnl"].sum()
        else:
            market_value = 0.0
            unrealized_pnl = 0.0
            
        total_equity = cash + market_value
        
        # Calculate daily PnL (Simplified: change in equity vs yesterday? 
        # For now, just using unrealized as a proxy or 0 if no history)
        daily_pnl = 0.0 
        
        return {
            "total_equity": total_equity,
            "cash": cash,
            "unrealized_pnl": unrealized_pnl,
            "daily_pnl": daily_pnl
        }

    def get_trade_history(self, limit: int = 100) -> pd.DataFrame:
        """Get trade history as DataFrame."""
        try:
            query = """
                SELECT timestamp, ticker, action, quantity, price, 
                       (quantity * price) as amount 
                FROM orders 
                ORDER BY timestamp DESC 
                LIMIT ?
            """
            df = pd.read_sql_query(query, self.conn, params=(limit,))
            if not df.empty:
                 # Calculate realized PnL roughly? 
                 # orders table doesn't track pnl per trade easily without FIFO matching.
                 # We will return raw columns for now. simple_dashboard expects 'realized_pnl' column
                 # We'll add dummy realized_pnl column if missing
                 df["realized_pnl"] = 0.0 
            return df
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            return pd.DataFrame()

    def get_daily_summary(self) -> list:
        """Get daily summary (date, pnl, trade_count)."""
        # Return dummy list for now as we don't have a daily_summary table in this version
        return [(datetime.datetime.now().date().isoformat(), 0.0, 0)]

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

# END
