"""ペーパートレード機能を提供するモジュール。

このモジュールは、実際の資金を使用せずに取引戦略をテストするための仮想環境を提供します。
SQLiteデータベースを使用してポジション、残高、および注文履歴を管理します。
"""

import json
import logging
import sqlite3
import datetime
from pathlib import Path
<<<<<<< HEAD
from typing import Dict, Union, Any, List, Tuple

import pandas as pd


=======
from typing import Dict, Union, Any, Optional
import pandas as pd
from datetime import datetime
>>>>>>> 9ead59c0c8153a0969ef2e94b492063a605db31f

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
        """Close database connection."""
        if self.conn:
<<<<<<< HEAD
            self.conn.close()

# END
=======
            self.conn.close()
>>>>>>> 9ead59c0c8153a0969ef2e94b492063a605db31f
