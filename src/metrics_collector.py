"""
Metrics Collector Module
Collects and tracks system metrics for monitoring.
"""
import psutil
import sqlite3
from datetime import datetime
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self, db_path: str = "metrics.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize metrics database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # API metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                endpoint TEXT,
                duration_ms REAL,
                success INTEGER,
                error_message TEXT
            )
        ''')
        
        # Trade metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                ticker TEXT,
                action TEXT,
                quantity INTEGER,
                price REAL,
                success INTEGER
            )
        ''')
        
        # System metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                cpu_percent REAL,
                memory_percent REAL,
                disk_percent REAL
            )
        ''')
        
        # Error metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                error_type TEXT,
                error_message TEXT,
                module TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_api_latency(self, endpoint: str, duration_ms: float, success: bool = True, error: Optional[str] = None):
        """Record API call latency."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO api_metrics (timestamp, endpoint, duration_ms, success, error_message)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), endpoint, duration_ms, int(success), error))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error recording API metric: {e}")
    
    def record_trade_execution(self, ticker: str, action: str, quantity: int, price: float, success: bool = True):
        """Record trade execution."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trade_metrics (timestamp, ticker, action, quantity, price, success)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), ticker, action, quantity, price, int(success)))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error recording trade metric: {e}")
    
    def record_system_metrics(self):
        """Record current system metrics."""
        try:
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_metrics (timestamp, cpu_percent, memory_percent, disk_percent)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now().isoformat(), cpu, memory, disk))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error recording system metrics: {e}")
    
    def record_error(self, error_type: str, error_message: str, module: str = "unknown"):
        """Record error occurrence."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO error_metrics (timestamp, error_type, error_message, module)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now().isoformat(), error_type, error_message, module))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error recording error metric: {e}")
    
    def get_api_success_rate(self, hours: int = 24) -> float:
        """Get API success rate for the last N hours."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT AVG(success) FROM api_metrics
                WHERE timestamp > datetime('now', '-' || ? || ' hours')
            ''', (hours,))
            
            result = cursor.fetchone()[0]
            conn.close()
            
            return result if result else 0.0
            
        except Exception as e:
            logger.error(f"Error getting API success rate: {e}")
            return 0.0
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """Get recent errors."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, error_type, error_message, module
                FROM error_metrics
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            errors = cursor.fetchall()
            conn.close()
            
            return errors
            
        except Exception as e:
            logger.error(f"Error getting recent errors: {e}")
            return []

if __name__ == "__main__":
    # Test
    collector = MetricsCollector()
    
    # Record some test metrics
    collector.record_api_latency("yfinance", 150.5, success=True)
    collector.record_trade_execution("7203.T", "BUY", 100, 1000.0, success=True)
    collector.record_system_metrics()
    
    print(f"API Success Rate (24h): {collector.get_api_success_rate():.1%}")
