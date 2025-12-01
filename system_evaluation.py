"""
AGStock システム性能評価レポート生成

包括的な性能評価を実行してレポートを生成
"""
import time
import psutil
import os
from datetime import datetime
from src.paper_trader import PaperTrader
from performance_tracker import PerformanceTracker


def evaluate_system_performance():
    """システム全体の性能評価"""
    print("\n" + "="*70)
    print("🔍 AGStock システム性能評価")
    print("="*70)
    
    report = []
    report.append(f"\n生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. ペーパートレード実績
    print("\n1️⃣  ペーパートレード実績を分析中...")
    pt = PaperTrader()
    balance = pt.get_current_balance()
    positions = pt.get_positions()
    history = pt.get_trade_history()
    
    report.append("\n" + "="*70)
    report.append("📊 ペーパートレード実績")
    report.append("="*70)
    report.append(f"\n💰 総資産: ¥{balance['total_equity']:,.0f}")
    report.append(f"💵 現金: ¥{balance['cash']:,.0f}")
    report.append(f"📋 保有銘柄数: {len(positions)}銘柄")
    
    # 取引統計
    if not history.empty and 'realized_pnl' in history.columns:
        closed = history[history['realized_pnl'] != 0]
        if not closed.empty:
            wins = len(closed[closed['realized_pnl'] > 0])
            losses = len(closed[closed['realized_pnl'] < 0])
            total = len(closed)
            win_rate = (wins / total * 100) if total > 0 else 0
            
            report.append(f"\n🎯 取引実績:")
            report.append(f"  総取引数: {total}件")
            report.append(f"  勝率: {win_rate:.1f}%")
            report.append(f"  勝ち: {wins}件 / 負け: {losses}件")
    
    # 2. パフォーマンス指標
    print("\n2️⃣  パフォーマンス指標を計算中...")
    try:
        tracker = PerformanceTracker()
        perf = tracker.get_period_performance(period_days=30)
        
        if perf.get('has_data'):
            report.append("\n" + "="*70)
            report.append("📈 30日間パフォーマンス")
            report.append("="*70)
            report.append(f"\n総リターン: {perf['total_return']:.2f}%")
            report.append(f"年率ボラティリティ: {perf['volatility']:.2f}%")
            report.append(f"シャープレシオ: {perf['sharpe_ratio']:.2f}")
            report.append(f"最大ドローダウン: {perf['max_drawdown']:.2f}%")
    except Exception as e:
        report.append(f"\nパフォーマンス計算エラー: {e}")
    
    # 3. システムリソース使用状況
    print("\n3️⃣  システムリソースを確認中...")
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    cpu_percent = process.cpu_percent(interval=1.0)
    
    report.append("\n" + "="*70)
    report.append("💻 システムリソース")
    report.append("="*70)
    report.append(f"\nメモリ使用量: {memory_info.rss / 1024 / 1024:.1f} MB")
    report.append(f"CPU使用率: {cpu_percent:.1f}%")
    
    # 4. 実装機能の確認
    print("\n4️⃣  実装機能を確認中...")
    features = {
        "モーニングブリーフ": os.path.exists("morning_brief.py"),
        "パフォーマンストラッカー": os.path.exists("performance_tracker.py"),
        "スマートアラート": os.path.exists("smart_alerts.py"),
        "高度なバックテスト": os.path.exists("advanced_backtester.py"),
        "フルオート投資": os.path.exists("auto_invest.py"),
        "統合実行スクリプト": os.path.exists("run_all.py"),
        "効率的スケジューラー": os.path.exists("scheduler.py"),
    }
    
    report.append("\n" + "="*70)
    report.append("✨ 実装済み機能")
    report.append("="*70)
    implemented = sum(1 for v in features.values() if v)
    total_features = len(features)
    report.append(f"\n実装率: {implemented}/{total_features} ({implemented/total_features*100:.0f}%)")
    
    for feature, exists in features.items():
        status = "✅" if exists else "❌"
        report.append(f"  {status} {feature}")
    
    # 5. 総合評価
    report.append("\n" + "="*70)
    report.append("🏆 総合評価")
    report.append("="*70)
    
    # スコア計算
    scores = []
    
    # パフォーマンススコア (0-100)
    if perf.get('has_data'):
        perf_score = 50  # ベース
        if perf['sharpe_ratio'] > 0:
            perf_score += min(30, perf['sharpe_ratio'] * 10)
        if perf['total_return'] > 0:
            perf_score += min(20, perf['total_return'] / 2)
        scores.append(("パフォーマンス", min(100, max(0, perf_score))))
    
    # 機能実装スコア
    feature_score = (implemented / total_features) * 100
    scores.append(("機能実装", feature_score))
    
    # リソース効率スコア
    resource_score = 100
    if memory_info.rss > 500 * 1024 * 1024:  # 500MB以上
        resource_score -= 20
    if cpu_percent > 50:
        resource_score -= 20
    scores.append(("リソース効率", max(0, resource_score)))
    
    # 総合スコア
    total_score = sum(s[1] for s in scores) / len(scores)
    
    report.append(f"\n総合スコア: {total_score:.1f}/100")
    for name, score in scores:
        report.append(f"  {name}: {score:.1f}/100")
    
    # 評価ランク
    if total_score >= 90:
        rank = "S (優秀)"
    elif total_score >= 80:
        rank = "A (良好)"
    elif total_score >= 70:
        rank = "B (普通)"
    elif total_score >= 60:
        rank = "C (要改善)"
    else:
        rank = "D (大幅改善必要)"
    
    report.append(f"\n評価ランク: {rank}")
    
    report.append("\n" + "="*70)
    
    # レポート出力
    full_report = "\n".join(report)
    print(full_report)
    
    # ファイルに保存
    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/performance_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(full_report)
    
    print(f"\n✅ レポート保存: {report_path}")
    
    return total_score, report_path


if __name__ == "__main__":
    evaluate_system_performance()
