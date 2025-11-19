import sqlite3
import pandas as pd
import datetime
from typing import Dict, List, Optional
from src.data_loader import fetch_stock_data
from src.strategies import Strategy
from src.constants import TICKER_NAMES

class PaperTrader:
    def __init__(self, db_path: str = "paper_trading.db", initial_capital: float = 10000000):
        self.db_path = db_path
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
                unrealized_pnl REAL
            )
        ''')
        
        # Orders/Trades history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                ticker TEXT,
                action TEXT,
                quantity INTEGER,
                price REAL,
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
        if row:
            return {'cash': row[0], 'total_equity': row[1]}
        return {'cash': self.initial_capital, 'total_equity': self.initial_capital}
    
    def get_positions(self) -> pd.DataFrame:
        """Get current open positions"""
        return pd.read_sql_query('SELECT * FROM positions', self.conn)
    
    def get_trade_history(self, limit: int = 50) -> pd.DataFrame:
        """Get recent trade history"""
        return pd.read_sql_query(f'SELECT * FROM orders ORDER BY date DESC LIMIT {limit}', self.conn)
    
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
    
    def execute_trade(self, ticker: str, action: str, quantity: int, price: float, reason: str = "Signal"):
        """Execute a buy or sell trade"""
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
                cursor.execute('''
                    INSERT INTO positions VALUES (?, ?, ?, ?, ?, ?)
                ''', (ticker, quantity, price, today, price, 0.0))
            
            # Update balance
            cursor.execute('UPDATE balance SET cash = ? WHERE date = (SELECT MAX(date) FROM balance)', (new_cash,))
            
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
        
        # Log the trade
        cursor.execute('''
            INSERT INTO orders (date, ticker, action, quantity, price, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (today, ticker, action, quantity, price, reason))
        
        self.conn.commit()
        return True
    
    def update_daily_equity(self):
        """Calculate and record total equity for the day"""
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
    
    def close(self):
        """Close database connection"""
        self.conn.close()
