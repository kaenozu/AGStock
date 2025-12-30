import datetime
import json
import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd
from src.constants import (DEFAULT_PAPER_TRADER_REFRESH_INTERVAL,
PAPER_TRADER_REALTIME_FALLBACK_DEFAULT)
from src.data_loader import fetch_stock_data
from src.helpers import retry_with_backoff
logger = logging.getLogger(__name__)
class PaperTrader:
    def __init__(self,
                db_path: str = "paper_trading.db",
#                 """
#                 initial_capital: float = None,
#                 use_realtime_fallback: Optional[bool] = None,
#                 ):
#                     pass
#             self.db_path = db_path
#         self._last_price_update_ts: float = 0.0
# # Load initial capital from config.json if not specified
#         if initial_capital is None:
#             try:
#                 # Use standard JSON load directly here to avoid circular dependencies with schemas
# # or just as a fallback.
#                 config_path = Path("config.json")
#                 if config_path.exists():
#                     with open(config_path, "r", encoding="utf-8") as f:
#                         config = json.load(f)
#                     initial_capital = config.get("paper_trading", {}).get("initial_capital", 1000000)
#                 else:
#                     initial_capital = 1000000  # Default 1M JPY
#             except Exception as e:
#                 logger.error(f"Error loading initial capital: {e}")
#                 initial_capital = 1000000
#             self.initial_capital = float(initial_capital)
#         self.conn = sqlite3.connect(db_path)
#         self.use_realtime_fallback = self._resolve_realtime_flag(use_realtime_fallback)
#         self._initialize_database()
#     def _resolve_realtime_flag(self, flag: Optional[bool]) -> bool:
#         pass
#     def _min_refresh_interval(self) -> int:
#         """
Min Refresh Interval.
                Returns:
                    Description of return value
                        try:
                            val = int(os.getenv("PAPER_TRADER_REFRESH_INTERVAL", str(DEFAULT_PAPER_TRADER_REFRESH_INTERVAL)))
        except Exception:
            val = DEFAULT_PAPER_TRADER_REFRESH_INTERVAL
        return max(val, 10)
#     """
#     def _calculate_position_value(self, pos: pd.Series) -> Tuple[float, float, float]:
#         """
各ポジションの市場価値、投資額、未実現損益を計算
                qty = float(pos.get("quantity", 0) or 0)
        entry_price = float(pos.get("entry_price") or pos.get("avg_price") or 0.0)
        current_price = pos.get("current_price", entry_price)
# current_price が欠損/0の時は entry_price で代替
try:
            current_price = float(current_price)
        except Exception:
            current_price = entry_price
        if pd.isna(current_price) or current_price == 0:
            current_price = entry_price
            market_value = qty * current_price
        invested_amount = qty * entry_price
            stored_unrealized = pos.get("unrealized_pnl")
        if stored_unrealized is None or pd.isna(stored_unrealized):
            unrealized_pnl = (current_price - entry_price) * qty
        else:
            unrealized_pnl = float(stored_unrealized)
            return market_value, invested_amount, unrealized_pnl
#     """
#     def _calculate_equity_snapshot(self, positions: pd.DataFrame, cash: float) -> Tuple[float, float, float]:
#         """現金と保有ポジションから総資産/投下資本/含み損益を計算"""
#         invested_amount = 0.0
#         market_value = 0.0
#         unrealized_pnl = 0.0
#             if not positions.empty:
#                 for _, pos in positions.iterrows():
#                     pos_market_value, pos_invested_amount, pos_unrealized_pnl = self._calculate_position_value(pos)
#                 market_value += pos_market_value
#                 invested_amount += pos_invested_amount
#                 unrealized_pnl += pos_unrealized_pnl
#             total_equity = cash + market_value
#         return total_equity, invested_amount, unrealized_pnl
#     def _get_latest_balance(self) -> Tuple[Optional[str], float, float]:
#         """balanceテーブルの最新レコードを取得"""
#         cursor = self.conn.cursor()
#         cursor.execute("SELECT date, cash, total_equity FROM balance ORDER BY date DESC LIMIT 1")
#         row = cursor.fetchone()
#         if row:
#             date, cash, total_equity = row
#             return str(date), float(cash), float(total_equity) if total_equity is not None else float(cash)
#         return None, self.initial_capital, self.initial_capital
#     def _upsert_balance(self, date_str: str, cash: float, total_equity: float) -> None:
#         """balanceテーブルに当日のスナップショットを保存"""
#         cursor = self.conn.cursor()
#         cursor.execute("SELECT COUNT(*) FROM balance WHERE date = ?", (date_str,))
#         exists = cursor.fetchone()[0] > 0
#         if exists:
#             cursor.execute(
#                 "UPDATE balance SET cash = ?, total_equity = ? WHERE date = ?", (cash, total_equity, date_str)
#             )
#         else:
#             cursor.execute("INSERT INTO balance VALUES (?, ?, ?)", (date_str, cash, total_equity))
#         self.conn.commit()
#     def _initialize_database(self):
#         """Create tables if they don't exist"""
#         try:
#             cursor = self.conn.cursor()
# # Account balance table
#             cursor.execute(
#                                 CREATE TABLE IF NOT EXISTS balance (
#                     date TEXT PRIMARY KEY,
#                     cash REAL,
#                     total_equity REAL
#                 )
#                         )
# # Positions table
#             cursor.execute(
#                                 CREATE TABLE IF NOT EXISTS positions (
#                     ticker TEXT PRIMARY KEY,
#                     quantity INTEGER,
#                     entry_price REAL,
#                     entry_date TEXT,
#                     current_price REAL,
#                     unrealized_pnl REAL,
#                     stop_price REAL DEFAULT 0,
#                     highest_price REAL DEFAULT 0
#                 )
#                         )
# # Migration: Check columns
#             try:
#                 cursor.execute("SELECT stop_price, highest_price FROM positions LIMIT 1")
#             except sqlite3.OperationalError:
#                 logger.warning("Migrating database: adding stop_price and highest_price columns")
#                 cursor.execute("ALTER TABLE positions ADD COLUMN stop_price REAL DEFAULT 0")
#                 cursor.execute("ALTER TABLE positions ADD COLUMN highest_price REAL DEFAULT 0")
# # Orders/Trades history
#             cursor.execute(
#                                 CREATE TABLE IF NOT EXISTS orders (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     date TEXT,
#                     timestamp TEXT,
#                     ticker TEXT,
#                     action TEXT,
#                     quantity INTEGER,
#                     price REAL,
#                     realized_pnl REAL DEFAULT 0,
#                     reason TEXT
#                 )
#                         )
#                 self.conn.commit()
# # Initialize balance if empty
#             cursor.execute("SELECT COUNT(*) FROM balance")
#             if cursor.fetchone()[0] == 0:
#                 today = datetime.date.today().isoformat()
#                 cursor.execute(
#                     "INSERT INTO balance VALUES (?, ?, ?)", (today, self.initial_capital, self.initial_capital)
#                 )
#                 self.conn.commit()
#         except Exception as e:
#             logger.error(f"Database initialization error: {e}")
#     def get_current_balance(self, use_realtime_fallback: Optional[bool] = None) -> Dict[str, float]:
#         """Get current cash and total equity"""
#         last_date, cash, stored_total = self._get_latest_balance()
#         realtime_flag = self.use_realtime_fallback if use_realtime_fallback is None else bool(use_realtime_fallback)
#         positions = self.get_positions(use_realtime_fallback=realtime_flag)
#         total_equity, invested_amount, unrealized_pnl = self._calculate_equity_snapshot(positions, cash)
# # DBに保存されている総資産が実計算とずれている場合は同期
#         if last_date and abs(total_equity - stored_total) > 1e-6:
#             try:
#                 self._upsert_balance(last_date, cash, total_equity)
#             except Exception as e:
#                 logger.error(f"Failed to sync balance snapshot: {e}")
# # Calculate Daily PnL (Current Equity - Previous Day's Equity)
#         daily_pnl = 0.0
#         try:
#             cursor = self.conn.cursor()
#             today_str = datetime.date.today().isoformat()
# # Get the most recent balance record strictly before today
#             cursor.execute("SELECT total_equity FROM balance WHERE date < ? ORDER BY date DESC LIMIT 1", (today_str,))
#             row = cursor.fetchone()
#             if row:
#                 prev_equity = float(row[0])
#                 daily_pnl = total_equity - prev_equity
#             else:
#                 # If no previous history, compare with initial capital or just 0
#                 daily_pnl = total_equity - self.initial_capital
#         except Exception as e:
#             logger.warning(f"Failed to calculate daily PnL: {e}")
#             return {
#             "cash": cash,
#             "total_equity": total_equity,
#             "invested_amount": invested_amount,
#             "unrealized_pnl": unrealized_pnl,
#             "daily_pnl": daily_pnl,
#         }
#     def get_positions(self, use_realtime_fallback: bool = False) -> pd.DataFrame:
#         """Get current open positions with calculated market values"""
#         try:
#             df = pd.read_sql_query("SELECT * FROM positions", self.conn)
#         except Exception:
#             return pd.DataFrame()
#             if df.empty:
#                 # Return empty with expected columns
#             empty_df = pd.DataFrame(
#                 columns=[
#                     "ticker",
#                     "quantity",
#                     "entry_price",
#                     "current_price",
#                     "unrealized_pnl",
#                     "market_value",
#                     "unrealized_pnl_pct",
#                 ]
#             )
# # Ensure index is set even for empty df if downstream expects it
#             return empty_df.set_index("ticker", drop=False) if not empty_df.empty else empty_df
# # Add calculated columns
#     def _safe_price(row, fallback_prices: Dict[str, float]):
#             pass
#         price = row.get("current_price", 0.0)
#             try:
#                 price = float(price or 0.0)
#             except Exception:
#                 price = 0.0
#             if pd.isna(price) or price <= 0:
#                 price = fallback_prices.get(str(row.get("ticker")), 0.0)
#             if pd.isna(price) or price <= 0:
#                 try:
#                     price = float(row.get("entry_price", 0.0) or 0.0)
#                 except Exception:
#                     price = 0.0
#             return price
#             fallback_prices: Dict[str, float] = {}
#         if use_realtime_fallback:
#             from src.data_loader import fetch_realtime_data
#                 for t in df["ticker"].tolist():
#                     try:
#                         rt = fetch_realtime_data(t, period="5d", interval="1d")
#                     if rt is not None and not rt.empty and "Close" in rt.columns:
#                         fallback_prices[t] = float(rt["Close"].iloc[-1])
#                 except Exception as exc:
#                     logger.debug(f"Realtime price fallback failed for {t}: {exc}")
#             df["current_price"] = df.apply(lambda r: _safe_price(r, fallback_prices), axis=1)
#             if use_realtime_fallback and fallback_prices:
#                 try:
#                     cursor = self.conn.cursor()
#                 for _, row in df.iterrows():
#                     ticker = row["ticker"]
#                     if ticker in fallback_prices:
#                         cp = float(row["current_price"])
#                         unreal = (cp - float(row["entry_price"])) * int(row["quantity"])
#                         cursor.execute(
#                             "UPDATE positions SET current_price = ?, unrealized_pnl = ? WHERE ticker = ?",
#                             (cp, unreal, ticker),
#                         )
#                 self.conn.commit()
#             except Exception as exc:
#                 logger.debug(f"Persisting realtime prices failed: {exc}")
#         df["market_value"] = df["quantity"] * df["current_price"]
#         df["unrealized_pnl"] = (df["current_price"] - df["entry_price"]) * df["quantity"]
# # Avoid division by zero
#         df["unrealized_pnl_pct"] = df.apply(
#             lambda x: (
#                 ((x["current_price"] - x["entry_price"]) / x["entry_price"] * 100) if x["entry_price"] != 0 else 0
#             ),
#             axis=1,
#         )
#         return df.set_index("ticker", drop=False)
def get_trade_history(self, limit: int = 50, start_date: Optional[datetime.date] = None) -> pd.DataFrame:
#         """Get trade history. If start_date is provided, it takes priority over limit."""
try:
            if start_date:
                query = "SELECT * FROM orders WHERE date >= ? ORDER BY date DESC"
                params = (start_date.isoformat(),)
            else:
                safe_limit = max(int(limit), 1)
                query = f"SELECT * FROM orders ORDER BY date DESC LIMIT {safe_limit}"
                params = ()
                return pd.read_sql_query(query, self.conn, params=params, parse_dates=["date", "timestamp"])
        except Exception:
            return pd.DataFrame()
    def get_equity_history(self, days: int = None) -> pd.DataFrame:
#         """Get historical equity balance. Optional days limit."""
try:
            query = "SELECT * FROM balance ORDER BY date ASC"
            params = ()
                if days:
                    # Filter by last N days
                target_date = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
                query = "SELECT * FROM balance WHERE date >= ? ORDER BY date ASC"
                params = (target_date,)
                return pd.read_sql_query(query, self.conn, params=params, parse_dates=["date"])
        except Exception:
            return pd.DataFrame()
@retry_with_backoff(retries=3, backoff_in_seconds=1)
def update_positions_prices(self):
#         """Update current prices and unrealized P&L for all positions. Uses retry logic."""
# Rate-limit heavy refresh to avoid excessive API/DB load
refresh_interval = self._min_refresh_interval()
        now_ts = time.time()
        if self._last_price_update_ts and (now_ts - self._last_price_update_ts) < refresh_interval:
            logger.debug(
                "Positions price refresh skipped (rate limit). elapsed=%.2fs, interval=%ss",
                now_ts - self._last_price_update_ts,
                refresh_interval,
            )
            return
            positions = self.get_positions(use_realtime_fallback=self.use_realtime_fallback)
        if positions.empty:
            return
            tickers = positions["ticker"].tolist()
        if not tickers:
            return
            try:
                data_map = fetch_stock_data(tickers, period="5d")  # Short period is enough for current price
                cursor = self.conn.cursor()
            updated = False
                for _, pos in positions.iterrows():
                    ticker = pos["ticker"]
                if ticker in data_map and not data_map[ticker].empty:
                    current_price = data_map[ticker]["Close"].iloc[-1]
                    if hasattr(current_price, "item"):
                        current_price = current_price.item()
                        unrealized_pnl = (float(current_price) - float(pos["entry_price"])) * int(pos["quantity"])
                        cursor.execute(
                                                UPDATE positions
                        SET current_price = ?, unrealized_pnl = ?
                        WHERE ticker = ?
#                     """,
#                         (current_price, unrealized_pnl, ticker),
#                     )
#                     updated = True
#                 if updated:
#                     self.conn.commit()
#                 self._last_price_update_ts = now_ts
#             else:
#                 self._last_price_update_ts = now_ts
#             logger.debug(
#                 f"Positions price refresh completed. last_update={self._last_price_update_ts}, refreshed={updated}"
#             )
#             except Exception as e:
#                 logger.error(f"Failed to update position prices: {e}")
#             raise e  # Propagation for retry
# """
def execute_trade(self, ticker: str, action: str, quantity: int, price: float, reason: str = "Signal", initial_stop_price: float = 0.0) -> bool:
#         """Execute a buy or sell trade."""
try:
            cursor = self.conn.cursor()
            today = datetime.date.today().isoformat()
            now = datetime.datetime.now().isoformat()
                balance = self.get_current_balance()
            quantity = int(quantity)
            price = float(price)
                if action == "BUY":
                    cost = quantity * price
                if cost > balance["cash"]:
                    logger.warning(f"Insufficient cash to buy {quantity} shares of {ticker}")
                    return False
                    new_cash = balance["cash"] - cost
                    cursor.execute("SELECT quantity, entry_price, stop_price FROM positions WHERE ticker = ?", (ticker,))
                existing = cursor.fetchone()
                    if existing:
                        # Average down
                    old_qty, old_price = existing
                    new_qty = old_qty + quantity
# Weighted average price
new_avg_price = ((old_qty * old_price) + (quantity * price)) / new_qty
                        cursor.execute(
                                                UPDATE positions
                        SET quantity = ?, entry_price = ?, current_price = ?, stop_price = ?
                        WHERE ticker = ?
#                     """,
#                         (new_qty, new_avg_price, price, max(initial_stop_price,
#                         existing[2] if len(existing) > 2 else 0.0), ticker),
#                     )
#                 else:
#                     # New position
#                     cursor.execute(
#                                                 INSERT INTO positions (ticker, quantity, entry_price, entry_date, current_price, unrealized_pnl, stop_price, highest_price)
#                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#                     """,
                        (ticker, quantity, price, today, price, 0.0, initial_stop_price, price),
                    )
# Update balance
cursor.execute("UPDATE balance SET cash = ? WHERE date = (SELECT MAX(date) FROM balance)", (new_cash,))
                logger.info(f"[BUY] Executed: {ticker} x {quantity} @ {price}")
                elif action == "SELL":
                    cursor.execute("SELECT quantity, entry_price FROM positions WHERE ticker = ?", (ticker,))
                existing = cursor.fetchone()
                    if not existing or existing[0] < quantity:
                        logger.warning(f"Insufficient shares to sell {quantity} of {ticker}")
                    return False
                    old_qty, entry_price = existing
                proceeds = quantity * price
                realized_pnl = (price - entry_price) * quantity
                    new_cash = balance["cash"] + proceeds
                    if old_qty == quantity:
                        cursor.execute("DELETE FROM positions WHERE ticker = ?", (ticker,))
                else:
                    new_qty = old_qty - quantity
                    cursor.execute("UPDATE positions SET quantity = ? WHERE ticker = ?", (new_qty, ticker))
# Update balance
cursor.execute("UPDATE balance SET cash = ? WHERE date = (SELECT MAX(date) FROM balance)", (new_cash,))
                logger.info(f"[SELL] Executed: {ticker} x {quantity} @ {price} (PnL: {realized_pnl})")
# Log trade
realized_pnl_value = realized_pnl if action == "SELL" else 0
            cursor.execute(
                                INSERT INTO orders (date, timestamp, ticker, action, quantity, price, realized_pnl, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#             """,
#                 (today, now, ticker, action, quantity, price, realized_pnl_value, reason),
#             )
#                 self.conn.commit()
#             return True
#             except Exception as e:
#                 logger.error(f"Trade execution failed: {e}")
#             return False
# """
def update_daily_equity(self) -> float:
#         """Calculate and record total equity for the day."""
try:
            self.update_positions_prices()
_, cash, _ = self._get_latest_balance()
positions = self.get_positions(use_realtime_fallback=self.use_realtime_fallback)
            total_equity, _, _ = self._calculate_equity_snapshot(positions, cash)
                today = datetime.date.today().isoformat()
            self._upsert_balance(today, cash, total_equity)
            return total_equity
        except Exception as e:
            logger.error(f"Daily equity update failed: {e}")
            return 0.0
    def update_position_stop(self, ticker: str, stop_price: float, highest_price: float):
        pass
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                                UPDATE positions
                SET stop_price = ?, highest_price = ?
                WHERE ticker = ?
#             """,
#                 (stop_price, highest_price, ticker),
#             )
#             self.conn.commit()
#         except Exception as e:
#             logger.error(f"Stop update failed: {e}")
# """
def get_daily_summary(self, limit: int = 7) -> list:
#         """Get daily summary (date, pnl, trades)"""
summary = []
        try:
            # 1. Get Equity History to calc PnL
            df_equity = pd.read_sql_query(
                f"SELECT date, total_equity FROM balance ORDER BY date DESC LIMIT {limit + 1}",
                self.conn
            ).sort_values("date")
                if df_equity.empty:
                    return []
                df_equity["prev_equity"] = df_equity["total_equity"].shift(1)
            df_equity["daily_pnl"] = df_equity["total_equity"] - df_equity["prev_equity"]
# Fill NaN for first record (if no prev) with 0 or diff from initial capital
# For simpler view, we drop the first one if it's purely for diff,
# but user wants 'limit' days.
# 2. Get Trade Counts
            df_trades = pd.read_sql_query(
                f"SELECT date, COUNT(*) as trade_count FROM orders GROUP BY date",
                self.conn
            )
            trade_map = dict(zip(df_trades["date"], df_trades["trade_count"]))
# 3. Combine
# We take the last 'limit' records
target_df = df_equity.iloc[1:] if len(df_equity) > 1 else df_equity
            target_df = target_df.tail(limit)
                for _, row in target_df.iterrows():
                    d = row["date"]
                pnl = row["daily_pnl"] if pd.notna(row["daily_pnl"]) else 0.0
                count = trade_map.get(d, 0)
                summary.append((d, pnl, count))
            except Exception as e:
                logger.error(f"Failed to get daily summary: {e}")
            return summary
    def close(self):
#         """Close database connection."""
if self.conn:
            self.conn.close()
