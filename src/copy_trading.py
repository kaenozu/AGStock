"""
Copy Trading - コピートレードシステム
リーダーの取引を自動的にフォロワーにコピー
"""
import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class CopyTrade:
    """コピー取引"""
    id: Optional[int] = None
    follower_id: int = 0
    leader_id: int = 0
    original_trade_id: int = 0
    ticker: str = ""
    action: str = ""  # BUY or SELL
    quantity: int = 0
    price: float = 0.0
    copy_ratio: float = 0.1
    status: str = "pending"  # pending, executed, failed
    created_at: Optional[str] = None
    executed_at: Optional[str] = None


class CopyTradingEngine:
    """コピートレードエンジン"""
    
    def __init__(self, db_path: str = "social_trading.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # コピー取引履歴
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS copy_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                follower_id INTEGER NOT NULL,
                leader_id INTEGER NOT NULL,
                original_trade_id INTEGER,
                ticker TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                copy_ratio REAL DEFAULT 0.1,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                executed_at TIMESTAMP,
                FOREIGN KEY (follower_id) REFERENCES traders(id),
                FOREIGN KEY (leader_id) REFERENCES traders(id)
            )
        ''')
        
        # コピー設定
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS copy_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                follower_id INTEGER NOT NULL,
                leader_id INTEGER NOT NULL,
                enabled INTEGER DEFAULT 1,
                copy_percentage REAL DEFAULT 10.0,
                max_investment_per_trade REAL DEFAULT 50000.0,
                max_total_investment REAL DEFAULT 100000.0,
                min_confidence REAL DEFAULT 0.5,
                allowed_tickers TEXT,
                excluded_tickers TEXT,
                FOREIGN KEY (follower_id) REFERENCES traders(id),
                FOREIGN KEY (leader_id) REFERENCES traders(id),
                UNIQUE(follower_id, leader_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_copy_settings(self,
                            follower_id: int,
                            leader_id: int,
                            copy_percentage: float = 10.0,
                            max_investment_per_trade: float = 50000.0,
                            max_total_investment: float = 100000.0,
                            min_confidence: float = 0.5,
                            allowed_tickers: List[str] = None,
                            excluded_tickers: List[str] = None) -> int:
        """コピー設定作成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        allowed_str = json.dumps(allowed_tickers) if allowed_tickers else None
        excluded_str = json.dumps(excluded_tickers) if excluded_tickers else None
        
        cursor.execute('''
            INSERT OR REPLACE INTO copy_settings (
                follower_id, leader_id, copy_percentage,
                max_investment_per_trade, max_total_investment,
                min_confidence, allowed_tickers, excluded_tickers
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            follower_id, leader_id, copy_percentage,
            max_investment_per_trade, max_total_investment,
            min_confidence, allowed_str, excluded_str
        ))
        
        settings_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return settings_id
    
    def should_copy_trade(self,
                         follower_id: int,
                         leader_id: int,
                         ticker: str,
                         trade_value: float,
                         confidence: float = 1.0) -> Tuple[bool, str]:
        """
        取引をコピーすべきか判定
        
        Returns:
            (should_copy, reason)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 設定取得
        cursor.execute('''
            SELECT * FROM copy_settings
            WHERE follower_id = ? AND leader_id = ? AND enabled = 1
        ''', (follower_id, leader_id))
        
        settings = cursor.fetchone()
        
        if not settings:
            conn.close()
            return False, "コピー設定が無効"
        
        # 設定を解析
        max_per_trade = settings[4]
        max_total = settings[5]
        min_conf = settings[6]
        allowed_tickers = json.loads(settings[7]) if settings[7] else None
        excluded_tickers = json.loads(settings[8]) if settings[8] else None
        
        # 信頼度チェック
        if confidence < min_conf:
            conn.close()
            return False, f"信頼度不足 ({confidence:.2f} < {min_conf:.2f})"
        
        # 銘柄チェック
        if allowed_tickers and ticker not in allowed_tickers:
            conn.close()
            return False, f"許可されていない銘柄: {ticker}"
        
        if excluded_tickers and ticker in excluded_tickers:
            conn.close()
            return False, f"除外銘柄: {ticker}"
        
        # 取引額チェック
        if trade_value > max_per_trade:
            conn.close()
            return False, f"1取引あたりの上限超過 ({trade_value:.0f} > {max_per_trade:.0f})"
        
        # 総投資額チェック
        cursor.execute('''
            SELECT SUM(quantity * price) as total
            FROM copy_trades
            WHERE follower_id = ? AND leader_id = ? AND status = 'executed'
        ''', (follower_id, leader_id))
        
        result = cursor.fetchone()
        current_total = result[0] if result[0] else 0.0
        
        if current_total + trade_value > max_total:
            conn.close()
            return False, f"総投資額上限超過 ({current_total + trade_value:.0f} > {max_total:.0f})"
        
        conn.close()
        return True, "OK"
    
    def copy_trade(self,
                  leader_id: int,
                  ticker: str,
                  action: str,
                  quantity: int,
                  price: float,
                  confidence: float = 1.0,
                  original_trade_id: int = None) -> List[int]:
        """
        リーダーの取引をフォロワーにコピー
        
        Returns:
            作成されたコピー取引のIDリスト
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # フォロワー取得
        cursor.execute('''
            SELECT follower_id, copy_percentage
            FROM follows
            WHERE leader_id = ? AND auto_copy = 1
        ''', (leader_id,))
        
        followers = cursor.fetchall()
        copy_trade_ids = []
        
        for follower_id, copy_percentage in followers:
            # コピー比率計算
            copy_ratio = copy_percentage / 100.0
            copy_quantity = max(1, int(quantity * copy_ratio))
            trade_value = copy_quantity * price
            
            # コピー可否判定
            should_copy, reason = self.should_copy_trade(
                follower_id, leader_id, ticker, trade_value, confidence
            )
            
            if not should_copy:
                print(f"Skipping copy for follower {follower_id}: {reason}")
                continue
            
            # コピー取引作成
            cursor.execute('''
                INSERT INTO copy_trades (
                    follower_id, leader_id, original_trade_id,
                    ticker, action, quantity, price, copy_ratio, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            ''', (
                follower_id, leader_id, original_trade_id,
                ticker, action, copy_quantity, price, copy_ratio
            ))
            
            copy_trade_ids.append(cursor.lastrowid)
        
        conn.commit()
        conn.close()
        
        return copy_trade_ids
    
    def execute_copy_trade(self, copy_trade_id: int, paper_trader) -> bool:
        """
        コピー取引を実行
        
        Args:
            copy_trade_id: コピー取引ID
            paper_trader: PaperTraderインスタンス
            
        Returns:
            成功/失敗
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # コピー取引取得
        cursor.execute('SELECT * FROM copy_trades WHERE id = ?', (copy_trade_id,))
        trade = cursor.fetchone()
        
        if not trade or trade[9] != 'pending':
            conn.close()
            return False
        
        follower_id = trade[1]
        ticker = trade[4]
        action = trade[5]
        quantity = trade[6]
        price = trade[7]
        
        try:
            # ペーパートレード実行
            if action == 'BUY':
                paper_trader.buy(ticker, quantity, price)
            elif action == 'SELL':
                paper_trader.sell(ticker, quantity, price)
            
            # ステータス更新
            cursor.execute('''
                UPDATE copy_trades
                SET status = 'executed', executed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (copy_trade_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            # エラー時
            cursor.execute('''
                UPDATE copy_trades
                SET status = 'failed'
                WHERE id = ?
            ''', (copy_trade_id,))
            
            conn.commit()
            conn.close()
            return False
    
    def get_copy_history(self, 
                        follower_id: int = None,
                        leader_id: int = None,
                        limit: int = 100) -> pd.DataFrame:
        """コピー履歴取得"""
        conn = sqlite3.connect(self.db_path)
        
        query = 'SELECT * FROM copy_trades WHERE 1=1'
        params = []
        
        if follower_id:
            query += ' AND follower_id = ?'
            params.append(follower_id)
        
        if leader_id:
            query += ' AND leader_id = ?'
            params.append(leader_id)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=tuple(params))
        conn.close()
        
        return df
    
    def get_copy_performance(self, follower_id: int, leader_id: int) -> Dict:
        """コピーパフォーマンス取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN status = 'executed' THEN 1 ELSE 0 END) as executed_trades,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_trades,
                SUM(quantity * price) as total_investment
            FROM copy_trades
            WHERE follower_id = ? AND leader_id = ?
        ''', (follower_id, leader_id))
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'total_trades': result[0] or 0,
            'executed_trades': result[1] or 0,
            'failed_trades': result[2] or 0,
            'total_investment': result[3] or 0.0
        }


if __name__ == "__main__":
    # テスト
    engine = CopyTradingEngine("test_social.db")
    
    # コピー設定作成
    settings_id = engine.create_copy_settings(
        follower_id=2,
        leader_id=1,
        copy_percentage=10.0,
        max_investment_per_trade=50000.0
    )
    print(f"Created copy settings: {settings_id}")
    
    # 取引コピー
    copy_ids = engine.copy_trade(
        leader_id=1,
        ticker="7203.T",
        action="BUY",
        quantity=100,
        price=1500.0
    )
    print(f"Created copy trades: {copy_ids}")
    
    # 履歴取得
    history = engine.get_copy_history(follower_id=2)
    print(f"Copy history:\n{history}")
