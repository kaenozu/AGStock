"""
NISA Manager - NISA口座管理
つみたてNISA、一般NISA、ジュニアNISAの枠管理
"""
import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class NISAType(Enum):
    """NISA種類"""
    TSUMITATE = "tsumitate"  # つみたてNISA
    GENERAL = "general"      # 一般NISA
    JUNIOR = "junior"        # ジュニアNISA
    NEW_NISA = "new_nisa"    # 新NISA（2024年〜）


@dataclass
class NISALimit:
    """NISA上限"""
    annual_limit: float
    lifetime_limit: Optional[float] = None


class NISAManager:
    """NISA管理クラス"""
    
    # NISA上限（2024年以降の新NISA制度）
    NISA_LIMITS = {
        NISAType.NEW_NISA: {
            'growth': NISALimit(annual_limit=2400000, lifetime_limit=12000000),
            'tsumitate': NISALimit(annual_limit=1200000, lifetime_limit=18000000),
            'total': NISALimit(annual_limit=3600000, lifetime_limit=18000000)
        },
        NISAType.TSUMITATE: NISALimit(annual_limit=400000, lifetime_limit=8000000),
        NISAType.GENERAL: NISALimit(annual_limit=1200000),
        NISAType.JUNIOR: NISALimit(annual_limit=800000)
    }
    
    def __init__(self, db_path: str = "nisa.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # NISA口座
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nisa_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                nisa_type TEXT NOT NULL,
                year INTEGER NOT NULL,
                used_amount REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, nisa_type, year)
            )
        ''')
        
        # NISA取引
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nisa_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                amount REAL NOT NULL,
                trade_date DATE NOT NULL,
                FOREIGN KEY (account_id) REFERENCES nisa_accounts(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_or_create_account(self,
                             user_id: int,
                             nisa_type: NISAType,
                             year: int = None) -> int:
        """NISA口座取得または作成"""
        if year is None:
            year = datetime.now().year
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 既存口座確認
        cursor.execute('''
            SELECT id FROM nisa_accounts
            WHERE user_id = ? AND nisa_type = ? AND year = ?
        ''', (user_id, nisa_type.value, year))
        
        result = cursor.fetchone()
        
        if result:
            account_id = result[0]
        else:
            # 新規作成
            cursor.execute('''
                INSERT INTO nisa_accounts (user_id, nisa_type, year)
                VALUES (?, ?, ?)
            ''', (user_id, nisa_type.value, year))
            account_id = cursor.lastrowid
            conn.commit()
        
        conn.close()
        return account_id
    
    def get_remaining_limit(self,
                           user_id: int,
                           nisa_type: NISAType,
                           year: int = None) -> Dict[str, float]:
        """残り枠取得"""
        if year is None:
            year = datetime.now().year
        
        account_id = self.get_or_create_account(user_id, nisa_type, year)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 使用済み金額取得
        cursor.execute('''
            SELECT used_amount FROM nisa_accounts WHERE id = ?
        ''', (account_id,))
        
        result = cursor.fetchone()
        used_amount = result[0] if result else 0.0
        
        conn.close()
        
        # 上限取得
        if nisa_type == NISAType.NEW_NISA:
            limits = self.NISA_LIMITS[nisa_type]
            return {
                'growth_limit': limits['growth'].annual_limit,
                'growth_used': min(used_amount, limits['growth'].annual_limit),
                'growth_remaining': max(0, limits['growth'].annual_limit - used_amount),
                'tsumitate_limit': limits['tsumitate'].annual_limit,
                'total_limit': limits['total'].annual_limit,
                'total_used': used_amount,
                'total_remaining': max(0, limits['total'].annual_limit - used_amount)
            }
        else:
            limit = self.NISA_LIMITS[nisa_type].annual_limit
            return {
                'annual_limit': limit,
                'used': used_amount,
                'remaining': max(0, limit - used_amount)
            }
    
    def can_buy_in_nisa(self,
                       user_id: int,
                       nisa_type: NISAType,
                       amount: float,
                       year: int = None) -> Tuple[bool, str]:
        """NISA枠で購入可能か判定"""
        remaining = self.get_remaining_limit(user_id, nisa_type, year)
        
        if nisa_type == NISAType.NEW_NISA:
            available = remaining['total_remaining']
        else:
            available = remaining['remaining']
        
        if amount <= available:
            return True, "OK"
        else:
            return False, f"NISA枠不足（残り¥{available:,.0f}、必要¥{amount:,.0f}）"
    
    def record_nisa_trade(self,
                         user_id: int,
                         nisa_type: NISAType,
                         ticker: str,
                         action: str,
                         quantity: int,
                         price: float,
                         year: int = None) -> bool:
        """NISA取引記録"""
        amount = quantity * price
        
        # 購入の場合のみ枠チェック
        if action == 'BUY':
            can_buy, reason = self.can_buy_in_nisa(user_id, nisa_type, amount, year)
            if not can_buy:
                print(f"NISA購入不可: {reason}")
                return False
        
        account_id = self.get_or_create_account(user_id, nisa_type, year)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 取引記録
        cursor.execute('''
            INSERT INTO nisa_trades (
                account_id, ticker, action, quantity, price, amount, trade_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            account_id, ticker, action, quantity, price, amount,
            datetime.now().date()
        ))
        
        # 使用額更新
        if action == 'BUY':
            cursor.execute('''
                UPDATE nisa_accounts
                SET used_amount = used_amount + ?
                WHERE id = ?
            ''', (amount, account_id))
        elif action == 'SELL':
            cursor.execute('''
                UPDATE nisa_accounts
                SET used_amount = used_amount - ?
                WHERE id = ?
            ''', (amount, account_id))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_nisa_holdings(self,
                         user_id: int,
                         nisa_type: NISAType,
                         year: int = None) -> pd.DataFrame:
        """NISA保有銘柄取得"""
        account_id = self.get_or_create_account(user_id, nisa_type, year)
        
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                ticker,
                SUM(CASE WHEN action = 'BUY' THEN quantity ELSE -quantity END) as quantity,
                AVG(CASE WHEN action = 'BUY' THEN price ELSE NULL END) as avg_price,
                SUM(CASE WHEN action = 'BUY' THEN amount ELSE -amount END) as total_amount
            FROM nisa_trades
            WHERE account_id = ?
            GROUP BY ticker
            HAVING quantity > 0
        '''
        
        df = pd.read_sql_query(query, conn, params=(account_id,))
        conn.close()
        
        return df
    
    def optimize_nisa_allocation(self,
                                user_id: int,
                                target_investments: List[Dict]) -> List[Dict]:
        """
        NISA枠の最適配分
        
        Args:
            user_id: ユーザーID
            target_investments: 投資候補 [{'ticker': str, 'amount': float, 'priority': int}, ...]
            
        Returns:
            最適配分
        """
        # 新NISA枠取得
        remaining = self.get_remaining_limit(user_id, NISAType.NEW_NISA)
        available = remaining['total_remaining']
        
        # 優先度でソート
        sorted_investments = sorted(
            target_investments,
            key=lambda x: x.get('priority', 0),
            reverse=True
        )
        
        allocations = []
        allocated_amount = 0.0
        
        for investment in sorted_investments:
            amount = investment['amount']
            
            if allocated_amount + amount <= available:
                # 全額NISA枠で購入可能
                allocations.append({
                    'ticker': investment['ticker'],
                    'amount': amount,
                    'nisa_amount': amount,
                    'taxable_amount': 0.0,
                    'use_nisa': True
                })
                allocated_amount += amount
            elif allocated_amount < available:
                # 一部NISA枠で購入
                nisa_amount = available - allocated_amount
                taxable_amount = amount - nisa_amount
                
                allocations.append({
                    'ticker': investment['ticker'],
                    'amount': amount,
                    'nisa_amount': nisa_amount,
                    'taxable_amount': taxable_amount,
                    'use_nisa': True
                })
                allocated_amount = available
            else:
                # 課税口座のみ
                allocations.append({
                    'ticker': investment['ticker'],
                    'amount': amount,
                    'nisa_amount': 0.0,
                    'taxable_amount': amount,
                    'use_nisa': False
                })
        
        return allocations


if __name__ == "__main__":
    # テスト
    manager = NISAManager("test_nisa.db")
    
    # 残り枠確認
    remaining = manager.get_remaining_limit(1, NISAType.NEW_NISA)
    print(f"新NISA残り枠: ¥{remaining['total_remaining']:,.0f}")
    
    # NISA取引
    success = manager.record_nisa_trade(
        user_id=1,
        nisa_type=NISAType.NEW_NISA,
        ticker="7203.T",
        action="BUY",
        quantity=100,
        price=1500.0
    )
    print(f"NISA購入: {'成功' if success else '失敗'}")
    
    # 保有銘柄
    holdings = manager.get_nisa_holdings(1, NISAType.NEW_NISA)
    print(f"NISA保有:\n{holdings}")
