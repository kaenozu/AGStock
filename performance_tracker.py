"""
パフォーマンストラッカー - 自動集計・レポート生成

日次/週次/月次でパフォーマンスを追跡し、美しいレポートを生成
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from typing import Dict, List
import json

from src.paper_trader import PaperTrader
from src.benchmark_comparator import BenchmarkComparator


class PerformanceTracker:
    """パフォーマンストラッカー"""
    
    def __init__(self):
        self.pt = PaperTrader()
        self.comparator = BenchmarkComparator()
    
    def get_period_performance(self, period_days: int = 30) -> Dict:
        """期間パフォーマンスを取得"""
        equity_history = self.pt.get_equity_history()
        
        if equity_history.empty or len(equity_history) < 2:
            return {"has_data": False}
        
        # 期間データ
        start_date = datetime.now() - timedelta(days=period_days)
        period_data = equity_history[equity_history['date'] >= start_date]
        
        if len(period_data) < 2:
            return {"has_data": False}
        
        # 計算
        start_equity = period_data.iloc[0]['equity']
        end_equity = period_data.iloc[-1]['equity']
        total_return = ((end_equity - start_equity) / start_equity) * 100
        
        # 日次リターン
        period_data = period_data.copy()
        period_data['daily_return'] = period_data['equity'].pct_change()
        
        # リスク指標
        volatility = period_data['daily_return'].std() * np.sqrt(252) * 100  # 年率
        sharpe = (total_return / volatility) if volatility > 0 else 0
        
        # 最大ドローダウン
        cummax = period_data['equity'].cummax()
        drawdown = ((period_data['equity'] - cummax) / cummax) * 100
        max_drawdown = drawdown.min()
        
        return {
            "has_data": True,
            "period_days": period_days,
            "start_date": period_data.iloc[0]['date'],
            "end_date": period_data.iloc[-1]['date'],
            "start_equity": start_equity,
            "end_equity": end_equity,
            "total_return": total_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "data": period_data
        }
    
    def get_trade_statistics(self) -> Dict:
        """取引統計"""
        history = self.pt.get_trade_history()
        
        if history.empty:
            return {"has_data": False}
        
        # realized_pnlがある取引のみ
        if 'realized_pnl' in history.columns:
            closed_trades = history[history['realized_pnl'] != 0]
        else:
            return {"has_data": False}
        
        if closed_trades.empty:
            return {"has_data": False}
        
        total_trades = len(closed_trades)
        wins = len(closed_trades[closed_trades['realized_pnl'] > 0])
        losses = len(closed_trades[closed_trades['realized_pnl'] < 0])
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
        
        avg_win = closed_trades[closed_trades['realized_pnl'] > 0]['realized_pnl'].mean() if wins > 0 else 0
        avg_loss = abs(closed_trades[closed_trades['realized_pnl'] < 0]['realized_pnl'].mean()) if losses > 0 else 0
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
        
        return {
            "has_data": True,
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor
        }
    
    def generate_equity_chart(self, period_days: int = 30, save_path: str = "reports/equity_chart.png"):
        """資産推移チャート生成"""
        perf = self.get_period_performance(period_days)
        
        if not perf['has_data']:
            return None
        
        data = perf['data']
        
        fig, ax = plt.subplots(figsize=(12, 6), facecolor='white')
        
        ax.plot(data['date'], data['equity'], color='#00d4ff', linewidth=2.5)
        ax.fill_between(data['date'], data['equity'], alpha=0.3, color='#00d4ff')
        
        ax.set_title(f'資産推移 ({period_days}日間)', fontsize=16, fontweight='bold')
        ax.set_xlabel('')
        ax.set_ylabel('総資産 (円)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # フォーマット
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'¥{x:,.0f}'))
        
        plt.tight_layout()
        
        # 保存
        import os
        os.makedirs("reports", exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return save_path
    
    def generate_monthly_report(self) -> str:
        """月次レポート生成"""
        # 30日間のパフォーマンス
        perf_30 = self.get_period_performance(30)
        
        # 取引統計
        trade_stats = self.get_trade_statistics()
        
        # 現在の状況
        balance = self.pt.get_current_balance()
        positions = self.pt.get_positions()
        
        # レポート作成
        report = f"""
{'='*60}
📊 AGStock 月次パフォーマンスレポート
{'='*60}
生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 30日間パフォーマンス
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        if perf_30['has_data']:
            report += f"""総リターン:      {perf_30['total_return']:+.2f}%
年率ボラティリティ: {perf_30['volatility']:.2f}%
シャープレシオ:    {perf_30['sharpe_ratio']:.2f}
最大ドローダウン:  {perf_30['max_drawdown']:.2f}%
開始資産:         ¥{perf_30['start_equity']:,.0f}
終了資産:         ¥{perf_30['end_equity']:,.0f}
"""
        else:
            report += "データ不足\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 取引統計
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        if trade_stats['has_data']:
            report += f"""総取引数:        {trade_stats['total_trades']}件
勝ちトレード:    {trade_stats['wins']}件
負けトレード:    {trade_stats['losses']}件
勝率:            {trade_stats['win_rate']:.1f}%
平均利益:        ¥{trade_stats['avg_win']:,.0f}
平均損失:        ¥{trade_stats['avg_loss']:,.0f}
プロフィットファクター: {trade_stats['profit_factor']:.2f}
"""
        else:
            report += "取引なし\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💼 現在のポートフォリオ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
総資産:          ¥{balance['total_equity']:,.0f}
現金:            ¥{balance['cash']:,.0f}
投資額:          ¥{balance['invested_amount']:,.0f}
含み損益:        ¥{balance['unrealized_pnl']:+,.0f}
保有銘柄数:      {len(positions)}銘柄
"""
        
        if not positions.empty:
            report += "\n保有銘柄TOP5:\n"
            top5 = positions.nlargest(5, 'market_value')
            for idx, pos in top5.iterrows():
                ticker = pos.get('ticker', idx)
                qty = pos.get('quantity', 0)
                pnl_pct = ((pos.get('current_price', 0) - pos.get('entry_price', 1)) / pos.get('entry_price', 1)) * 100
                report += f"  {ticker:<10} {qty:>6}株  {pnl_pct:+.1f}%\n"
        
        report += f"\n{'='*60}\n"
        
        return report
    
    def save_report(self, report: str, filename: str = "monthly_report.txt"):
        """レポートを保存"""
        import os
        os.makedirs("reports", exist_ok=True)
        
        filepath = f"reports/{filename}"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)
        
        return filepath
    
    def export_to_excel(self, filename: str = "performance_data.xlsx"):
        """Excelエクスポート"""
        import os
        os.makedirs("reports", exist_ok=True)
        
        filepath = f"reports/{filename}"
        
        # データ準備
        equity_history = self.pt.get_equity_history()
        trade_history = self.pt.get_trade_history()
        positions = self.pt.get_positions()
        
        # Excel書き込み
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            if not equity_history.empty:
                equity_history.to_excel(writer, sheet_name='資産推移', index=False)
            
            if not trade_history.empty:
                trade_history.to_excel(writer, sheet_name='取引履歴', index=False)
            
            if not positions.empty:
                positions.to_excel(writer, sheet_name='保有ポジション')
        
        return filepath


def main():
    """メイン実行"""
    tracker = PerformanceTracker()
    
    # 月次レポート生成
    print("月次レポート生成中...")
    report = tracker.generate_monthly_report()
    print(report)
    
    # 保存
    report_path = tracker.save_report(report)
    print(f"\nレポート保存: {report_path}")
    
    # チャート生成
    chart_path = tracker.generate_equity_chart(30)
    if chart_path:
        print(f"チャート保存: {chart_path}")
    
    # Excel エクスポート
    excel_path = tracker.export_to_excel()
    print(f"Excelエクスポート: {excel_path}")


if __name__ == "__main__":
    main()
