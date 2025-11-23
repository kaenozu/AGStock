import sqlite3
import pandas as pd
import logging
from datetime import datetime
from typing import Optional, List, Dict
import os

logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self, db_path: str = "stock_data.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table for OHLCV data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_data (
                ticker TEXT,
                date TIMESTAMP,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                PRIMARY KEY (ticker, date)
            )
        """)
        
        # Create index for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticker_date ON stock_data (ticker, date)")
        
        conn.commit()
        conn.close()

    def save_data(self, df: pd.DataFrame, ticker: str):
        """
        Save DataFrame to SQLite.
        Expects index to be DatetimeIndex.
        """
        if df is None or df.empty:
            return

        conn = sqlite3.connect(self.db_path)
        
        # Prepare data for insertion
        data_to_save = df.copy()
        data_to_save = data_to_save.reset_index()
        
        # Ensure columns exist and rename if necessary (yfinance usually gives Date, Open, High, Low, Close, Volume)
        # We map them to lowercase for DB consistency
        
        # Handle index name
        if 'Date' not in data_to_save.columns and 'date' not in data_to_save.columns:
            if 'index' in data_to_save.columns:
                data_to_save = data_to_save.rename(columns={'index': 'date'})
            else:
                # If index was unnamed, reset_index might have created 'index' or just used the first column?
                # Usually it creates 'index' if name is None.
                pass

        column_map = {
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }
        data_to_save = data_to_save.rename(columns=column_map)
        data_to_save['ticker'] = ticker
        
        # Convert date to string for SQLite compatibility
        if 'date' in data_to_save.columns:
            data_to_save['date'] = pd.to_datetime(data_to_save['date']).dt.strftime('%Y-%m-%d %H:%M:%S')

        # Keep only relevant columns
        cols = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']
        data_to_save = data_to_save[cols]
        
        # Convert date to string for SQLite compatibility if needed, but pandas to_sql handles timestamps well usually.
        # However, for explicit control, we can ensure it's datetime.
        
        try:
            # Use 'replace' or 'append'. Since we have a primary key, 'append' might fail on duplicates.
            # We want 'upsert'. SQLite 3.24+ supports ON CONFLICT.
            # Pandas to_sql doesn't support upsert natively easily without a temp table or method customization.
            # For simplicity and robustness, we can delete existing range and insert new, or use a loop.
            # Given the volume, let's try a custom method for upsert.
            
            data_tuples = list(data_to_save.itertuples(index=False, name=None))
            
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO stock_data (ticker, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticker, date) DO UPDATE SET
                    open=excluded.open,
                    high=excluded.high,
                    low=excluded.low,
                    close=excluded.close,
                    volume=excluded.volume
            """, data_tuples)
            
            conn.commit()
            logger.info(f"Saved {len(data_to_save)} records for {ticker} to {self.db_path}")
            
        except Exception as e:
            logger.error(f"Error saving data for {ticker}: {e}")
        finally:
            conn.close()

    def load_data(self, ticker: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Load data from SQLite.
        Returns DataFrame with DatetimeIndex.
        """
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT date, open, high, low, close, volume FROM stock_data WHERE ticker = ?"
        params = [ticker]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
            
        query += " ORDER BY date ASC"
        
        try:
            df = pd.read_sql_query(query, conn, params=params, parse_dates=['date'])
            if not df.empty:
                df.set_index('date', inplace=True)
                # Restore Capitalized columns for compatibility with existing code
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            return df
        except Exception as e:
            logger.error(f"Error loading data for {ticker}: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    def get_latest_date(self, ticker: str) -> Optional[datetime]:
        """Get the latest date available for a ticker."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(date) FROM stock_data WHERE ticker = ?", (ticker,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            # SQLite stores timestamps as strings often, pandas parses them.
            # Here we need to parse if it comes back as string.
            try:
                return pd.to_datetime(result[0])
            except:
                return None
        return None
