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
        return {
            'cash': self.initial_capital,
            'total_equity': self.initial_capital,
            'invested_amount': 0.0,
            'unrealized_pnl': 0.0
        }
    def get_positions(self) -> pd.DataFrame:
        """Get current open positions with calculated market values"""
        try:
            df = pd.read_sql_query('SELECT * FROM positions', self.conn)
        except Exception:
            return pd.DataFrame()

        if df.empty:
            # Return empty with expected columns
            empty_df = pd.DataFrame(columns=['ticker', 'quantity', 'entry_price', 'current_price', 
                                       'unrealized_pnl', 'market_value', 'unrealized_pnl_pct'])
            # Ensure index is set even for empty df if downstream expects it
            return empty_df.set_index('ticker', drop=False) if not empty_df.empty else empty_df

        # Add calculated columns
        df['market_value'] = df['quantity'] * df['current_price']
        df['unrealized_pnl'] = (df['current_price'] - df['entry_price']) * df['quantity']
        # Avoid division by zero
        df['unrealized_pnl_pct'] = df.apply(
            lambda x: ((x['current_price'] - x['entry_price']) / x['entry_price'] * 100) if x['entry_price'] != 0 else 0,
            axis=1
        )
        return df.set_index('ticker', drop=False)

    def get_trade_history(self, limit: int = 50) -> pd.DataFrame:
        """Get recent trade history"""
        try:
            return pd.read_sql_query(f'SELECT * FROM orders ORDER BY date DESC LIMIT {limit}', self.conn, parse_dates=['date', 'timestamp'])
        except Exception:
            return pd.DataFrame()

    def get_equity_history(self) -> pd.DataFrame:
        """Get historical equity balance"""
        try:
            return pd.read_sql_query('SELECT * FROM balance ORDER BY date ASC', self.conn, parse_dates=['date'])
        except Exception:
            return pd.DataFrame()

    @retry_with_backoff(retries=3, backoff_in_seconds=1)
    def update_positions_prices(self):
        """Update current prices and unrealized P&L for all positions. Uses retry logic."""
        positions = self.get_positions()
        if positions.empty:
            return

        tickers = positions['ticker'].tolist()
        if not tickers:
            return
            
        try:
            data_map = fetch_stock_data(tickers, period="5d") # Short period is enough for current price
            
            cursor = self.conn.cursor()
            updated = False
            
            for _, pos in positions.iterrows():
                ticker = pos['ticker']
                if ticker in data_map and not data_map[ticker].empty:
                    current_price = data_map[ticker]['Close'].iloc[-1]
                    if hasattr(current_price, 'item'):
                        current_price = current_price.item()
                    
                    unrealized_pnl = (float(current_price) - float(pos['entry_price'])) * int(pos['quantity'])

                    cursor.execute('''
                        UPDATE positions
                        SET current_price = ?, unrealized_pnl = ?
                        WHERE ticker = ?
                    ''', (current_price, unrealized_pnl, ticker))
                    updated = True
            
            if updated:
                self.conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to update position prices: {e}")
            raise e # Propagation for retry

    def execute_trade(self, ticker: str, action: str, quantity: int, price: float, reason: str = "Signal") -> bool:
        """Execute a buy or sell trade."""
        try:
            cursor = self.conn.cursor()
            today = datetime.date.today().isoformat()
            now = datetime.datetime.now().isoformat()

            balance = self.get_current_balance()
            quantity = int(quantity)
            price = float(price)

            if action == "BUY":
                cost = quantity * price
                if cost > balance['cash']:
                    logger.warning(f"Insufficient cash to buy {quantity} shares of {ticker}")
                    return False

                new_cash = balance['cash'] - cost

                cursor.execute('SELECT quantity, entry_price FROM positions WHERE ticker = ?', (ticker,))
                existing = cursor.fetchone()

                if existing:
                    # Average down
                    old_qty, old_price = existing
                    new_qty = old_qty + quantity
                    # Weighted average price
                    new_avg_price = ((old_qty * old_price) + (quantity * price)) / new_qty
                    
                    cursor.execute('''
                        UPDATE positions
                        SET quantity = ?, entry_price = ?, current_price = ?
                        WHERE ticker = ?
                    ''', (new_qty, new_avg_price, price, ticker))
                else:
                    # New position
                    cursor.execute('''
                        INSERT INTO positions (ticker, quantity, entry_price, entry_date, current_price, unrealized_pnl, stop_price, highest_price)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (ticker, quantity, price, today, price, 0.0, 0.0, price))

                # Update balance
                cursor.execute('UPDATE balance SET cash = ? WHERE date = (SELECT MAX(date) FROM balance)', (new_cash,))
                logger.info(f"[BUY] Executed: {ticker} x {quantity} @ {price}")

            elif action == "SELL":
                cursor.execute('SELECT quantity, entry_price FROM positions WHERE ticker = ?', (ticker,))
                existing = cursor.fetchone()

                if not existing or existing[0] < quantity:
                    logger.warning(f"Insufficient shares to sell {quantity} of {ticker}")
                    return False

                old_qty, entry_price = existing
                proceeds = quantity * price
                realized_pnl = (price - entry_price) * quantity

                new_cash = balance['cash'] + proceeds

                if old_qty == quantity:
                    cursor.execute('DELETE FROM positions WHERE ticker = ?', (ticker,))
                else:
                    new_qty = old_qty - quantity
                    cursor.execute('UPDATE positions SET quantity = ? WHERE ticker = ?', (new_qty, ticker))

                # Update balance
                cursor.execute('UPDATE balance SET cash = ? WHERE date = (SELECT MAX(date) FROM balance)', (new_cash,))
                logger.info(f"[SELL] Executed: {ticker} x {quantity} @ {price} (PnL: {realized_pnl})")

            # Log trade
            realized_pnl_value = realized_pnl if action == "SELL" else 0
            cursor.execute('''
                INSERT INTO orders (date, timestamp, ticker, action, quantity, price, realized_pnl, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (today, now, ticker, action, quantity, price, realized_pnl_value, reason))

            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            return False

    def update_daily_equity(self) -> float:
        """Calculate and record total equity for the day."""
        try:
            self.update_positions_prices()

            balance = self.get_current_balance()
            
            # Recalculate simply from balance and positions just in case
            # But get_current_balance already does logic. 
            # Ideally we trust get_current_balance['total_equity'] but we better update DB record.
            
            # get_current_balance reads from DB 'balance' table (cash) + calculated position value
            # So let's maximize consistency
            total_equity = balance['total_equity']

            today = datetime.date.today().isoformat()
            cursor = self.conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM balance WHERE date = ?', (today,))
            if cursor.fetchone()[0] == 0:
                cursor.execute('INSERT INTO balance VALUES (?, ?, ?)', (today, balance['cash'], total_equity))
            else:
                cursor.execute('UPDATE balance SET total_equity = ? WHERE date = ?', (total_equity, today))

            self.conn.commit()
            return total_equity
        except Exception as e:
            logger.error(f"Daily equity update failed: {e}")
            return 0.0

    def update_position_stop(self, ticker: str, stop_price: float, highest_price: float):
        """Update stop price and highest price for a position."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE positions
                SET stop_price = ?, highest_price = ?
                WHERE ticker = ?
            ''', (stop_price, highest_price, ticker))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Stop update failed: {e}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
