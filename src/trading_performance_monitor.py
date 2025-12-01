"""
トレーディングパフォーマンス監視システム

日次・週次での取引パフォーマンスを自動的に追跡し、レポートを生成します。
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class TradingPerformanceMonitor:
    """
    トレーディングパフォーマンス監視クラス
    
    日次・週次での取引パフォーマンスを記録し、レポートを生成します。
    """
    
    def __init__(self, db_path: str = 'data/trading_performance.db'):
        """
        初期化
        
        Args:
            db_path: データベースファイルパス
        """
        self.db_path = db_path
        self._init_db()
        
        logger.info(f"TradingPerformanceMonitor initialized with db: {db_path}")
    
    def _init_db(self):
        """データベースを初期化"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 日次パフォーマンステーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_performance (
                date TEXT PRIMARY KEY,
                total_assets REAL,
                cash REAL,
                stock_value REAL,
                daily_return REAL,
                num_positions INTEGER,
                num_trades INTEGER,
                realized_pnl REAL,
                unrealized_pnl REAL,
                sharpe_ratio REAL,
                max_drawdown REAL
            )
        ''')
        
        # 取引履歴テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                ticker TEXT,
                action TEXT,
                quantity INTEGER,
                price REAL,
                pnl REAL,
                strategy TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("Database initialized")
    
    def record_daily_performance(self, date: str, metrics: Dict[str, Any]):
        """
        日次パフォーマンスを記録
        
        Args:
            date: 日付（YYYY-MM-DD形式）
            metrics: パフォーマンス指標の辞書
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO daily_performance
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            date,
            metrics.get('total_assets', 0),
            metrics.get('cash', 0),
            metrics.get('stock_value', 0),
            metrics.get('daily_return', 0),
            metrics.get('num_positions', 0),
            metrics.get('num_trades', 0),
            metrics.get('realized_pnl', 0),
            metrics.get('unrealized_pnl', 0),
            metrics.get('sharpe_ratio', 0),
            metrics.get('max_drawdown', 0)
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded daily performance for {date}")
    
    def record_trade(
        self,
        date: str,
        ticker: str,
        action: str,
        quantity: int,
        price: float,
        pnl: float = 0.0,
        strategy: str = ''
    ):
        """
        取引を記録
        
        Args:
            date: 日付
            ticker: 銘柄コード
            action: アクション（BUY/SELL）
            quantity: 数量
            price: 価格
            pnl: 損益
            strategy: 戦略名
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trade_history (date, ticker, action, quantity, price, pnl, strategy)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (date, ticker, action, quantity, price, pnl, strategy))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded trade: {action} {quantity} {ticker} @ {price}")
    
    def get_daily_performance(self, date: str) -> Optional[Dict[str, Any]]:
        """
        指定日のパフォーマンスを取得
        
        Args:
            date: 日付（YYYY-MM-DD形式）
        
        Returns:
            パフォーマンス指標の辞書
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM daily_performance WHERE date = ?
        ''', (date,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        columns = [
            'date', 'total_assets', 'cash', 'stock_value', 'daily_return',
            'num_positions', 'num_trades', 'realized_pnl', 'unrealized_pnl',
            'sharpe_ratio', 'max_drawdown'
        ]
        
        return dict(zip(columns, row))
    
    def get_performance_summary(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        期間のパフォーマンスサマリーを取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
        
        Returns:
            パフォーマンスサマリー
        """
        conn = sqlite3.connect(self.db_path)
        
        df = pd.read_sql_query('''
            SELECT * FROM daily_performance
            WHERE date BETWEEN ? AND ?
            ORDER BY date
        ''', conn, params=(start_date, end_date))
        
        conn.close()
        
        if df.empty:
            return {}
        
        # 総リターン
        total_return = (df['total_assets'].iloc[-1] / df['total_assets'].iloc[0] - 1) * 100
        
        # 平均日次リターン
        avg_daily_return = df['daily_return'].mean()
        
        # Sharpe Ratio
        sharpe_ratio = df['sharpe_ratio'].iloc[-1] if 'sharpe_ratio' in df.columns else 0
        
        # 最大ドローダウン
        max_drawdown = df['max_drawdown'].min() if 'max_drawdown' in df.columns else 0
        
        # 総取引数
        total_trades = df['num_trades'].sum()
        
        # 総実現損益
        total_realized_pnl = df['realized_pnl'].sum()
        
        summary = {
            'period': f"{start_date} ~ {end_date}",
            'total_return': total_return,
            'avg_daily_return': avg_daily_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': int(total_trades),
            'total_realized_pnl': total_realized_pnl,
            'final_assets': df['total_assets'].iloc[-1],
            'num_days': len(df)
        }
        
        return summary
    
    def generate_daily_report(self, date: str) -> str:
        """
        日次レポートを生成
        
        Args:
            date: 日付（YYYY-MM-DD形式）
        
        Returns:
            レポート文字列
        """
        perf = self.get_daily_performance(date)
        
        if perf is None:
            return f"No performance data for {date}"
        
        report = f"""
=== AGStock 日次パフォーマンスレポート ===
日付: {date}

【資産状況】
総資産: ¥{perf['total_assets']:,.0f} ({perf['daily_return']:+.2f}%)
現金: ¥{perf['cash']:,.0f}
株式評価額: ¥{perf['stock_value']:,.0f}

【取引実績】
新規取引: {perf['num_trades']}件
実現損益: ¥{perf['realized_pnl']:+,.0f}
未実現損益: ¥{perf['unrealized_pnl']:+,.0f}

【保有ポジション】
銘柄数: {perf['num_positions']}

【リスク指標】
Sharpe Ratio: {perf['sharpe_ratio']:.2f}
最大ドローダウン: {perf['max_drawdown']:.2f}%
"""
        
        return report
    
    def generate_weekly_report(self, end_date: str) -> str:
        """
        週次レポートを生成
        
        Args:
            end_date: 終了日（YYYY-MM-DD形式）
        
        Returns:
            レポート文字列
        """
        # 7日前から終了日までの期間
        end = datetime.strptime(end_date, '%Y-%m-%d')
        start = end - timedelta(days=6)
        start_date = start.strftime('%Y-%m-%d')
        
        summary = self.get_performance_summary(start_date, end_date)
        
        if not summary:
            return f"No performance data for period {start_date} ~ {end_date}"
        
        # 取引統計を取得
        conn = sqlite3.connect(self.db_path)
        trades_df = pd.read_sql_query('''
            SELECT * FROM trade_history
            WHERE date BETWEEN ? AND ?
        ''', conn, params=(start_date, end_date))
        conn.close()
        
        # 勝率計算
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        total_trades = len(trades_df)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # 平均利益/損失
        avg_profit = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if len(trades_df[trades_df['pnl'] < 0]) > 0 else 0
        
        # Profit Factor
        total_profit = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
        total_loss = abs(trades_df[trades_df['pnl'] < 0]['pnl'].sum())
        profit_factor = (total_profit / total_loss) if total_loss > 0 else 0
        
        report = f"""
=== AGStock 週次パフォーマンスレポート ===
期間: {start_date} ~ {end_date}

【パフォーマンス】
週次リターン: {summary['total_return']:+.2f}%
Sharpe Ratio: {summary['sharpe_ratio']:.2f}
最大ドローダウン: {summary['max_drawdown']:.2f}%

【取引統計】
総取引数: {total_trades}件
勝率: {win_rate:.1f}%
平均利益: ¥{avg_profit:,.0f}
平均損失: ¥{avg_loss:,.0f}
Profit Factor: {profit_factor:.2f}

【資産状況】
最終資産: ¥{summary['final_assets']:,.0f}
総実現損益: ¥{summary['total_realized_pnl']:+,.0f}
"""
        
        # ベストトレードを追加
        if not trades_df.empty and 'pnl' in trades_df.columns:
            best_trade = trades_df.loc[trades_df['pnl'].idxmax()]
            report += f"""
【ベストトレード】
{best_trade['ticker']}: ¥{best_trade['pnl']:+,.0f}
"""
        
        return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Trading Performance Monitoring System")
    print("=" * 60)
    print("このモジュールは以下を実装します:")
    print("1. 日次トレーディングパフォーマンスの記録")
    print("2. 取引履歴の記録")
    print("3. 日次レポートの生成")
    print("4. 週次レポートの生成")
    print("5. パフォーマンスサマリーの取得")
