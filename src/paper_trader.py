import sqlite3
import pandas as pd
import datetime
from typing import Dict
from src.data_loader import fetch_stock_data


class PaperTrader:
    def __init__(self, db_path: str = "paper_trading.db", initial_capital: float = None):
        self.db_path = db_path

        # Load initial capital from config.json if not specified
        if initial_capital is None:
            try:
                import json
                from pathlib import Path
                config_path = Path(__file__).parent.parent / 'config.json'
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    initial_capital = config.get('paper_trading', {}).get('initial_capital', 1000000)
                else:
                    initial_capital = 1000000  # デフォルト100万円
            except Exception:
                initial_capital = 1000000  # エラー時もデフォルト100万円

        self.initial_capital = initial_capital
        self.conn = sqlite3.connect(db_path)
        self._initialize_database()

    def _initialize_database(self):
        """Create tables if they don't exist"""
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

        # Check if columns exist (migration for existing DB)
        try:
            cursor.execute('SELECT stop_price, highest_price FROM positions LIMIT 1')
        except sqlite3.OperationalError:
            # Columns don't exist, add them
            try:
                cursor.execute('ALTER TABLE positions ADD COLUMN stop_price REAL DEFAULT 0')
                cursor.execute('ALTER TABLE positions ADD COLUMN highest_price REAL DEFAULT 0')
            except Exception as e:
                print(f"Migration error: {e}")

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

    def get_current_balance(self) -> Dict[str, float]:
        """Get current cash and total equity"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT cash, total_equity FROM balance ORDER BY date DESC LIMIT 1')
        row = cursor.fetchone()

        # Get positions to calculate invested amount and unrealized PnL
        positions = self.get_positions()
        invested_amount = 0
        unrealized_pnl = 0

        if not positions.empty:
            invested_amount = (positions['quantity'] * positions['entry_price']).sum()
            unrealized_pnl = positions['unrealized_pnl'].sum() if 'unrealized_pnl' in positions.columns else 0

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
            'invested_amount': 0,
            'unrealized_pnl': 0
        }

    def get_positions(self) -> pd.DataFrame:
        """Get current open positions with calculated market values"""
        df = pd.read_sql_query('SELECT * FROM positions', self.conn)

        # 計算カラムの初期化（空の場合のエラー防止）
        if df.empty:
            for col in ['market_value', 'unrealized_pnl', 'unrealized_pnl_pct']:
                df[col] = pd.Series(dtype='float64')
            return df

        # Add calculated columns for dashboard
        df['market_value'] = df['quantity'] * df['current_price']
        df['unrealized_pnl'] = (df['current_price'] - df['entry_price']) * df['quantity']
        df['unrealized_pnl_pct'] = ((df['current_price'] - df['entry_price']) / df['entry_price']) * 100
        return df

    def get_trade_history(self, limit: int = 50) -> pd.DataFrame:
        """Get recent trade history"""
        return pd.read_sql_query(f'SELECT * FROM orders ORDER BY date DESC LIMIT {limit}', self.conn)

    def get_equity_history(self) -> pd.DataFrame:
        """Get historical equity balance"""
        return pd.read_sql_query('SELECT * FROM balance ORDER BY date ASC', self.conn)

    def update_positions_prices(self):
        """Update current prices and unrealized P&L for all positions"""
        positions = self.get_positions()
        if positions.empty:
            return

        tickers = positions['ticker'].tolist()
        data_map = fetch_stock_data(tickers, period="5d")

        cursor = self.conn.cursor()
        for _, pos in positions.iterrows():
            ticker = pos['ticker']
            if ticker in data_map and not data_map[ticker].empty:
                current_price = data_map[ticker]['Close'].iloc[-1]
                unrealized_pnl = (current_price - pos['entry_price']) * pos['quantity']

                cursor.execute('''
                    UPDATE positions
                    SET current_price = ?, unrealized_pnl = ?
                    WHERE ticker = ?
                ''', (current_price, unrealized_pnl, ticker))

        self.conn.commit()

    def execute_trade(self, ticker: str, action: str, quantity: int, price: float, reason: str = "Signal") -> bool:
        """
        Execute a buy or sell trade.

        Args:
            ticker (str): Stock ticker symbol
            action (str): "BUY" or "SELL"
            quantity (int): Number of shares
            price (float): Execution price
            reason (str): Reason for the trade

        Returns:
            bool: True if trade executed successfully, False otherwise
        """
        cursor = self.conn.cursor()
        today = datetime.date.today().isoformat()

        balance = self.get_current_balance()

        if action == "BUY":
            cost = quantity * price
            if cost > balance['cash']:
                print(f"Insufficient cash to buy {quantity} shares of {ticker}")
                return False

            # Deduct cash
            new_cash = balance['cash'] - cost

            # Check if position exists
            cursor.execute('SELECT quantity, entry_price FROM positions WHERE ticker = ?', (ticker,))
            existing = cursor.fetchone()

            if existing:
                # Average down
                old_qty, old_price = existing
                new_qty = old_qty + quantity
                new_avg_price = ((old_qty * old_price) + (quantity * price)) / new_qty
                cursor.execute('''
                    UPDATE positions
                    SET quantity = ?, entry_price = ?, current_price = ?
                    WHERE ticker = ?
                ''', (new_qty, new_avg_price, price, ticker))
            else:
                # New position
                # Initialize stop_price and highest_price (will be updated by risk manager)
                cursor.execute('''
                    INSERT INTO positions (ticker, quantity, entry_price, entry_date, current_price, unrealized_pnl, stop_price, highest_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (ticker, quantity, price, today, price, 0.0, 0.0, price))

            # Update balance
            cursor.execute('UPDATE balance SET cash = ? WHERE date = (SELECT MAX(date) FROM balance)', (new_cash,))

            # Log successful buy
            print(f"[BUY] Executed: {ticker} x {quantity} @ {price}")

        elif action == "SELL":
            # Check if we have the position
            cursor.execute('SELECT quantity, entry_price FROM positions WHERE ticker = ?', (ticker,))
            existing = cursor.fetchone()

            if not existing or existing[0] < quantity:
                print(f"Insufficient shares to sell {quantity} of {ticker}")
                return False

            old_qty, entry_price = existing
            proceeds = quantity * price
            realized_pnl = (price - entry_price) * quantity

            new_cash = balance['cash'] + proceeds

            if old_qty == quantity:
                # Close position
                cursor.execute('DELETE FROM positions WHERE ticker = ?', (ticker,))
            else:
                # Reduce position
                new_qty = old_qty - quantity
                cursor.execute('UPDATE positions SET quantity = ? WHERE ticker = ?', (new_qty, ticker))

            # Update balance
            cursor.execute('UPDATE balance SET cash = ? WHERE date = (SELECT MAX(date) FROM balance)', (new_cash,))

            # Log successful sell
            print(f"[SELL] Executed: {ticker} x {quantity} @ {price} (PnL: {realized_pnl})")

        # Log the trade
        now = datetime.datetime.now().isoformat()
        realized_pnl_value = realized_pnl if action == "SELL" else 0

        cursor.execute('''
            INSERT INTO orders (date, timestamp, ticker, action, quantity, price, realized_pnl, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (today, now, ticker, action, quantity, price, realized_pnl_value, reason))

        self.conn.commit()
        return True

    def update_daily_equity(self) -> float:
        """
        Calculate and record total equity for the day.

        Returns:
            float: Total equity value
        """
        self.update_positions_prices()

        balance = self.get_current_balance()
        positions = self.get_positions()

        total_position_value = positions['unrealized_pnl'].sum() + (positions['quantity'] * positions['entry_price']).sum() if not positions.empty else 0
        total_equity = balance['cash'] + total_position_value

        today = datetime.date.today().isoformat()
        cursor = self.conn.cursor()

        # Check if today's record exists
        cursor.execute('SELECT COUNT(*) FROM balance WHERE date = ?', (today,))
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO balance VALUES (?, ?, ?)', (today, balance['cash'], total_equity))
        else:
            cursor.execute('UPDATE balance SET total_equity = ? WHERE date = ?', (total_equity, today))

        self.conn.commit()

        return total_equity

    def update_position_stop(self, ticker: str, stop_price: float, highest_price: float):
        """
        Update stop price and highest price for a position.

        Args:
            ticker (str): Stock ticker symbol
            stop_price (float): New stop price
            highest_price (float): New highest price
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE positions
            SET stop_price = ?, highest_price = ?
            WHERE ticker = ?
        ''', (stop_price, highest_price, ticker))
        self.conn.commit()

    def close(self):
        """Close database connection."""
        self.conn.close()
