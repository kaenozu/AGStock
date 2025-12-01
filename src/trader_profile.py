"""
Trader Profile - トレーダープロファイル管理
パフォーマンス追跡、ランキング、フォロワー管理
"""
import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class TraderProfile:
    """トレーダープロファイル"""
    id: Optional[int] = None
    username: str = ""
    display_name: str = ""
    bio: str = ""
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    follower_count: int = 0
    following_count: int = 0
    is_public: bool = True
    allow_copy: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TraderProfileManager:
    """トレーダープロファイル管理"""
    
    def __init__(self, db_path: str = "social_trading.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # トレーダープロファイル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS traders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                display_name TEXT,
                bio TEXT,
                total_return REAL DEFAULT 0.0,
                sharpe_ratio REAL DEFAULT 0.0,
                max_drawdown REAL DEFAULT 0.0,
                win_rate REAL DEFAULT 0.0,
                total_trades INTEGER DEFAULT 0,
                follower_count INTEGER DEFAULT 0,
                following_count INTEGER DEFAULT 0,
                is_public INTEGER DEFAULT 1,
                allow_copy INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # フォロー関係
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS follows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                follower_id INTEGER NOT NULL,
                leader_id INTEGER NOT NULL,
                copy_percentage REAL DEFAULT 10.0,
                max_investment REAL DEFAULT 100000.0,
                auto_copy INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (follower_id) REFERENCES traders(id),
                FOREIGN KEY (leader_id) REFERENCES traders(id),
                UNIQUE(follower_id, leader_id)
            )
        ''')
        
        # パフォーマンス履歴
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trader_id INTEGER NOT NULL,
                date DATE NOT NULL,
                daily_return REAL,
                cumulative_return REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                FOREIGN KEY (trader_id) REFERENCES traders(id),
                UNIQUE(trader_id, date)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_profile(self, profile: TraderProfile) -> int:
        """プロファイル作成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO traders (
                username, display_name, bio, is_public, allow_copy
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            profile.username,
            profile.display_name,
            profile.bio,
            profile.is_public,
            profile.allow_copy
        ))
        
        trader_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return trader_id
    
    def get_profile(self, trader_id: int) -> Optional[TraderProfile]:
        """プロファイル取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM traders WHERE id = ?', (trader_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return TraderProfile(
                id=row[0],
                username=row[1],
                display_name=row[2],
                bio=row[3],
                total_return=row[4],
                sharpe_ratio=row[5],
                max_drawdown=row[6],
                win_rate=row[7],
                total_trades=row[8],
                follower_count=row[9],
                following_count=row[10],
                is_public=bool(row[11]),
                allow_copy=bool(row[12]),
                created_at=row[13],
                updated_at=row[14]
            )
        return None
    
    def update_performance(self, trader_id: int, metrics: Dict):
        """パフォーマンス更新"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE traders
            SET total_return = ?,
                sharpe_ratio = ?,
                max_drawdown = ?,
                win_rate = ?,
                total_trades = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            metrics.get('total_return', 0.0),
            metrics.get('sharpe_ratio', 0.0),
            metrics.get('max_drawdown', 0.0),
            metrics.get('win_rate', 0.0),
            metrics.get('total_trades', 0),
            trader_id
        ))
        
        conn.commit()
        conn.close()
    
    def get_leaderboard(self, 
                       metric: str = 'total_return',
                       limit: int = 100) -> pd.DataFrame:
        """リーダーボード取得"""
        conn = sqlite3.connect(self.db_path)
        
        valid_metrics = ['total_return', 'sharpe_ratio', 'win_rate']
        if metric not in valid_metrics:
            metric = 'total_return'
        
        query = f'''
            SELECT 
                id,
                username,
                display_name,
                total_return,
                sharpe_ratio,
                max_drawdown,
                win_rate,
                total_trades,
                follower_count
            FROM traders
            WHERE is_public = 1
            ORDER BY {metric} DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        
        return df
    
    def follow_trader(self, 
                     follower_id: int,
                     leader_id: int,
                     copy_percentage: float = 10.0,
                     max_investment: float = 100000.0,
                     auto_copy: bool = True) -> bool:
        """トレーダーをフォロー"""
        if follower_id == leader_id:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO follows (
                    follower_id, leader_id, copy_percentage, 
                    max_investment, auto_copy
                ) VALUES (?, ?, ?, ?, ?)
            ''', (follower_id, leader_id, copy_percentage, max_investment, auto_copy))
            
            # フォロワー数更新
            cursor.execute('''
                UPDATE traders 
                SET follower_count = follower_count + 1
                WHERE id = ?
            ''', (leader_id,))
            
            cursor.execute('''
                UPDATE traders 
                SET following_count = following_count + 1
                WHERE id = ?
            ''', (follower_id,))
            
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def unfollow_trader(self, follower_id: int, leader_id: int) -> bool:
        """フォロー解除"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM follows
            WHERE follower_id = ? AND leader_id = ?
        ''', (follower_id, leader_id))
        
        if cursor.rowcount > 0:
            # フォロワー数更新
            cursor.execute('''
                UPDATE traders 
                SET follower_count = follower_count - 1
                WHERE id = ?
            ''', (leader_id,))
            
            cursor.execute('''
                UPDATE traders 
                SET following_count = following_count - 1
                WHERE id = ?
            ''', (follower_id,))
            
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False
    
    def get_followers(self, trader_id: int) -> pd.DataFrame:
        """フォロワー一覧取得"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                t.id,
                t.username,
                t.display_name,
                f.copy_percentage,
                f.max_investment,
                f.created_at
            FROM follows f
            JOIN traders t ON f.follower_id = t.id
            WHERE f.leader_id = ?
            ORDER BY f.created_at DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=(trader_id,))
        conn.close()
        
        return df
    
    def get_following(self, trader_id: int) -> pd.DataFrame:
        """フォロー中一覧取得"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                t.id,
                t.username,
                t.display_name,
                t.total_return,
                t.sharpe_ratio,
                f.copy_percentage,
                f.auto_copy,
                f.created_at
            FROM follows f
            JOIN traders t ON f.leader_id = t.id
            WHERE f.follower_id = ?
            ORDER BY f.created_at DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=(trader_id,))
        conn.close()
        
        return df
    
    def record_daily_performance(self, 
                                trader_id: int,
                                date: str,
                                metrics: Dict):
        """日次パフォーマンス記録"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO performance_history (
                trader_id, date, daily_return, cumulative_return,
                sharpe_ratio, max_drawdown
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            trader_id,
            date,
            metrics.get('daily_return', 0.0),
            metrics.get('cumulative_return', 0.0),
            metrics.get('sharpe_ratio', 0.0),
            metrics.get('max_drawdown', 0.0)
        ))
        
        conn.commit()
        conn.close()
    
    def get_performance_history(self, 
                               trader_id: int,
                               days: int = 30) -> pd.DataFrame:
        """パフォーマンス履歴取得"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT *
            FROM performance_history
            WHERE trader_id = ?
            ORDER BY date DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(trader_id, days))
        conn.close()
        
        return df


if __name__ == "__main__":
    # テスト
    manager = TraderProfileManager("test_social.db")
    
    # プロファイル作成
    profile = TraderProfile(
        username="trader1",
        display_name="トップトレーダー",
        bio="10年の経験を持つプロトレーダー"
    )
    trader_id = manager.create_profile(profile)
    print(f"Created trader: {trader_id}")
    
    # パフォーマンス更新
    manager.update_performance(trader_id, {
        'total_return': 45.5,
        'sharpe_ratio': 1.8,
        'max_drawdown': -12.3,
        'win_rate': 65.0,
        'total_trades': 150
    })
    
    # リーダーボード
    leaderboard = manager.get_leaderboard()
    print(f"Leaderboard:\n{leaderboard}")
