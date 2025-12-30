"""
パフォーマンスレポートとリスクチェック機能の動作確認スクリプト
"""
import sys
import pandas as pd
from src.paper_trader import PaperTrader
from src.performance import PerformanceAnalyzer
from src.portfolio_risk import PortfolioRiskAnalyzer

def test_performance_features():
    """パフォーマンス機能のテスト"""
    print("=" * 60)
    print("パフォーマンス機能テスト")
    print("=" * 60)
    
    analyzer = PerformanceAnalyzer()
    
    # 1. 日次リターン
    print("\n1. 日次リターン計算...")
    daily_returns = analyzer.get_daily_returns()
    if not daily_returns.empty:
        print(f"   ✓ {len(daily_returns)}日分のデータ取得")
        print(f"   最新: {daily_returns.iloc[-1]['date'].strftime('%Y-%m-%d')} - {daily_returns.iloc[-1]['daily_return']:.2f}%")
    else:
        print("   ℹ データなし（取引履歴が必要）")
    
    # 2. 月次ヒートマップデータ
    print("\n2. 月次ヒートマップデータ...")
    monthly_data = analyzer.get_monthly_heatmap_data()
    if not monthly_data.empty:
        print(f"   ✓ {len(monthly_data)}ヶ月分のデータ取得")
        print(f"   年: {monthly_data['year'].unique()}")
    else:
        print("   ℹ データなし（取引履歴が必要）")
    
    # 3. パフォーマンスサマリー
    print("\n3. パフォーマンスサマリー...")
    summary = analyzer.get_performance_summary()
    print(f"   総取引回数: {summary['total_trades']}")
    print(f"   勝率: {summary['win_rate']:.1f}%")
    print(f"   累計損益: ¥{summary['total_return']:,.0f}")
    
    if summary['best_month']:
        best = summary['best_month']
        print(f"   最高月: {best['year']}年{best['month']}月 (+¥{best['return']:,.0f})")
    
    return True

def test_risk_features():
    """リスク機能のテスト"""
    print("\n" + "=" * 60)
    print("リスク機能テスト")
    print("=" * 60)
    
    pt = PaperTrader()
    positions = pt.get_positions()
    
    if positions.empty:
        print("\n⚠️ ポジションがありません。リスク分析をスキップします。")
        pt.close()
        return True
    
    risk_analyzer = PortfolioRiskAnalyzer()
    
    # 1. 集中度計算
    print("\n1. 集中度計算...")
    concentration = risk_analyzer.calculate_concentration(positions)
    print(f"   Herfindahl Index: {concentration['herfindahl_index']:.4f}")
    print(f"   最大ポジション: {concentration['top_ticker']} ({concentration['top_position_pct']:.1%})")
    print(f"   集中フラグ: {'⚠️ 警告' if concentration['is_concentrated'] else '✓ OK'}")
    
    # 2. 集中度スコア
    print("\n2. 集中度スコア（レーダーチャート用）...")
    score = risk_analyzer.calculate_concentration_score(positions)
    print(f"   スコア: {score:.1f}/100")
    
    # 3. セクター分散
    print("\n3. セクター分散分析...")
    print("   （セクター情報取得中...）")
    sector_div = risk_analyzer.check_sector_diversification(positions)
    print(f"   セクター数: {sector_div['num_sectors']}")
    
    if sector_div['sector_distribution']:
        print("   セクター分布:")
        for sector, pct in sorted(sector_div['sector_distribution'].items(), key=lambda x: x[1], reverse=True):
            print(f"     - {sector}: {pct:.1%}")
    
    if sector_div['is_sector_concentrated']:
        print(f"   ⚠️ {sector_div['top_sector']} セクターが {sector_div['top_sector_pct']:.1%} を占めています")
    
    # 4. リスク警告
    print("\n4. リスク警告...")
    alerts = risk_analyzer.get_risk_alerts(positions)
    if alerts:
        for alert in alerts:
            icon = "⚠️" if alert['level'] == 'warning' else "ℹ️"
            print(f"   {icon} {alert['message']}")
    else:
        print("   ✓ 警告なし")
    
    pt.close()
    return True

def main():
    """メイン実行"""
    print("\n🔍 パフォーマンス & リスク機能 動作確認\n")
    
    try:
        # パフォーマンステスト
        perf_ok = test_performance_features()
        
        # リスクテスト
        risk_ok = test_risk_features()
        
        print("\n" + "=" * 60)
        if perf_ok and risk_ok:
            print("✅ すべてのテストが正常に完了しました")
            print("\n次のステップ:")
            print("1. ブラウザで http://localhost:8503 を開く")
            print("2. Shift + F5 でスーパーリロード")
            print("3. 🏠 ダッシュボードで以下を確認:")
            print("   - ポートフォリオ診断のリスク警告")
            print("   - 📊 月次パフォーマンス セクション")
        else:
            print("⚠️ 一部のテストで問題が発生しました")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
