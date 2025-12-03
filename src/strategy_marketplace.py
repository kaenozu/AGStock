"""
Strategy Marketplace - 戦略マーケットプレイス
戦略の公開、検索、評価、ダウンロード
"""
import sqlite3
import pandas as pd
from typing import Optional
from dataclasses import dataclass
import json
import base64


@dataclass
class Strategy:
    """戦略"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    author_id: int = 0
    category: str = "technical"  # technical, fundamental, ml, hybrid
    price: float = 0.0  # 0 = free
    rating: float = 0.0
    downloads: int = 0
    is_public: bool = True
    code: str = ""  # Base64エンコードされたコード
    backtest_results: str = ""  # JSON
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class StrategyMarketplace:
    """戦略マーケットプレイス"""
    
    def __init__(self, db_path: str = "social_trading.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 戦略
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                author_id INTEGER NOT NULL,
                category TEXT DEFAULT 'technical',
                price REAL DEFAULT 0.0,
                rating REAL DEFAULT 0.0,
                downloads INTEGER DEFAULT 0,
                is_public INTEGER DEFAULT 1,
                code TEXT,
                backtest_results TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (author_id) REFERENCES traders(id)
            )
        ''')
        
        # レビュー
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES strategies(id),
                FOREIGN KEY (user_id) REFERENCES traders(id),
                UNIQUE(strategy_id, user_id)
            )
        ''')
        
        # ダウンロード履歴
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                price_paid REAL DEFAULT 0.0,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES strategies(id),
                FOREIGN KEY (user_id) REFERENCES traders(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def publish_strategy(self, strategy: Strategy) -> int:
        """戦略を公開"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO strategies (
                name, description, author_id, category, price,
                is_public, code, backtest_results
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            strategy.name,
            strategy.description,
            strategy.author_id,
            strategy.category,
            strategy.price,
            strategy.is_public,
            strategy.code,
            strategy.backtest_results
        ))
        
        strategy_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return strategy_id
    
    def search_strategies(self,
                         query: str = None,
                         category: str = None,
                         min_rating: float = 0.0,
                         max_price: float = None,
                         sort_by: str = 'downloads',
                         limit: int = 50) -> pd.DataFrame:
        """戦略を検索"""
        conn = sqlite3.connect(self.db_path)
        
        sql = '''
            SELECT 
                s.id,
                s.name,
                s.description,
                s.category,
                s.price,
                s.rating,
                s.downloads,
                t.username as author,
                s.created_at
            FROM strategies s
            JOIN traders t ON s.author_id = t.id
            WHERE s.is_public = 1
        '''
        
        params = []
        
        if query:
            sql += ' AND (s.name LIKE ? OR s.description LIKE ?)'
            params.extend([f'%{query}%', f'%{query}%'])
        
        if category:
            sql += ' AND s.category = ?'
            params.append(category)
        
        if min_rating > 0:
            sql += ' AND s.rating >= ?'
            params.append(min_rating)
        
        if max_price is not None:
            sql += ' AND s.price <= ?'
            params.append(max_price)
        
        # ソート
        valid_sorts = ['downloads', 'rating', 'created_at', 'price']
        if sort_by not in valid_sorts:
            sort_by = 'downloads'
        
        sql += f' ORDER BY s.{sort_by} DESC LIMIT ?'
        params.append(limit)
        
        df = pd.read_sql_query(sql, conn, params=tuple(params))
        conn.close()
        
        return df
    
    def get_strategy(self, strategy_id: int) -> Optional[Strategy]:
        """戦略取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM strategies WHERE id = ?', (strategy_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Strategy(
                id=row[0],
                name=row[1],
                description=row[2],
                author_id=row[3],
                category=row[4],
                price=row[5],
                rating=row[6],
                downloads=row[7],
                is_public=bool(row[8]),
                code=row[9],
                backtest_results=row[10],
                created_at=row[11],
                updated_at=row[12]
            )
        return None
    
    def download_strategy(self, strategy_id: int, user_id: int) -> Optional[str]:
        """
        戦略をダウンロード
        
        Returns:
            戦略コード（Base64デコード済み）
        """
        strategy = self.get_strategy(strategy_id)
        
        if not strategy:
            return None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # ダウンロード履歴記録
        cursor.execute('''
            INSERT INTO strategy_downloads (strategy_id, user_id, price_paid)
            VALUES (?, ?, ?)
        ''', (strategy_id, user_id, strategy.price))
        
        # ダウンロード数更新
        cursor.execute('''
            UPDATE strategies
            SET downloads = downloads + 1
            WHERE id = ?
        ''', (strategy_id,))
        
        conn.commit()
        conn.close()
        
        # コードをデコード
        try:
            code = base64.b64decode(strategy.code).decode('utf-8')
            return code
        except:
            return strategy.code
    
    def add_review(self,
                  strategy_id: int,
                  user_id: int,
                  rating: int,
                  comment: str = "") -> bool:
        """レビュー追加"""
        if rating < 1 or rating > 5:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO strategy_reviews (
                    strategy_id, user_id, rating, comment
                ) VALUES (?, ?, ?, ?)
            ''', (strategy_id, user_id, rating, comment))
            
            # 平均評価を更新
            cursor.execute('''
                UPDATE strategies
                SET rating = (
                    SELECT AVG(rating)
                    FROM strategy_reviews
                    WHERE strategy_id = ?
                )
                WHERE id = ?
            ''', (strategy_id, strategy_id))
            
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()
    
    def get_reviews(self, strategy_id: int) -> pd.DataFrame:
        """レビュー取得"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                r.rating,
                r.comment,
                t.username,
                r.created_at
            FROM strategy_reviews r
            JOIN traders t ON r.user_id = t.id
            WHERE r.strategy_id = ?
            ORDER BY r.created_at DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=(strategy_id,))
        conn.close()
        
        return df
    
    def get_popular_strategies(self, limit: int = 10) -> pd.DataFrame:
        """人気戦略取得"""
        return self.search_strategies(sort_by='downloads', limit=limit)
    
    def get_top_rated_strategies(self, limit: int = 10) -> pd.DataFrame:
        """高評価戦略取得"""
        return self.search_strategies(min_rating=4.0, sort_by='rating', limit=limit)
    
    def get_free_strategies(self, limit: int = 20) -> pd.DataFrame:
        """無料戦略取得"""
        return self.search_strategies(max_price=0.0, limit=limit)
    
    def encode_strategy_code(self, code: str) -> str:
        """戦略コードをエンコード"""
        return base64.b64encode(code.encode('utf-8')).decode('utf-8')
    
    def get_author_strategies(self, author_id: int) -> pd.DataFrame:
        """作者の戦略一覧取得"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                id, name, description, category, price,
                rating, downloads, created_at
            FROM strategies
            WHERE author_id = ?
            ORDER BY created_at DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=(author_id,))
        conn.close()
        
        return df


if __name__ == "__main__":
    # テスト
    marketplace = StrategyMarketplace("test_social.db")
    
    # 戦略公開
    strategy_code = """
class MyStrategy:
    def generate_signals(self, data):
        # シンプルな移動平均クロス
        data['SMA_20'] = data['Close'].rolling(20).mean()
        data['SMA_50'] = data['Close'].rolling(50).mean()
        data['signal'] = 0
        data.loc[data['SMA_20'] > data['SMA_50'], 'signal'] = 1
        data.loc[data['SMA_20'] < data['SMA_50'], 'signal'] = -1
        return data
"""
    
    encoded_code = marketplace.encode_strategy_code(strategy_code)
    
    strategy = Strategy(
        name="シンプルSMAクロス戦略",
        description="20日と50日の移動平均クロスを使ったシンプルな戦略",
        author_id=1,
        category="technical",
        price=0.0,
        code=encoded_code,
        backtest_results=json.dumps({
            "total_return": 25.5,
            "sharpe_ratio": 1.2,
            "max_drawdown": -8.5
        })
    )
    
    strategy_id = marketplace.publish_strategy(strategy)
    print(f"Published strategy: {strategy_id}")
    
    # 検索
    results = marketplace.search_strategies(query="SMA")
    print(f"Search results:\n{results}")
    
    # レビュー追加
    marketplace.add_review(strategy_id, 2, 5, "とても良い戦略です！")
    
    # レビュー取得
    reviews = marketplace.get_reviews(strategy_id)
    print(f"Reviews:\n{reviews}")
