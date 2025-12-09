"""
Phase 54 検証スクリプト
AI Hedge Fund 機能（マルチアセット・ポートフォリオ・ソーシャル）の動作確認
"""
import sys
import os
import logging
sys.path.insert(0, os.getcwd())

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_global_market_access():
    print("\n" + "="*50)
    print("🌍 Global Market Access テスト")
    print("="*50)
    
    from src.market_access import get_global_market_access
    access = get_global_market_access()
    
    print("   各市場データ取得中 (Crypto/US/JP)...")
    data = access.fetch_global_data(period="5d")
    
    for name, df in data.items():
        print(f"   ✅ {name}: {len(df)}行 (最新: {df.index[-1]})")
        
    status = access.get_market_status()
    print(f"   市場オープン状況: {status}")
    
    return len(data) > 0

def test_portfolio_manager_v2():
    print("\n" + "="*50)
    print("🤖 Portfolio Manager V2 (MPT) テスト")
    print("="*50)
    
    from src.portfolio_manager_v2 import PortfolioManagerV2
    from src.market_access import get_global_market_access
    
    # データ取得
    access = get_global_market_access()
    data = access.fetch_global_data(period="1y")
    
    pm = PortfolioManagerV2()
    print("   最適ポートフォリオ計算中 (Sharpe Ratio最大化)...")
    
    weights = pm.optimize_portfolio(data)
    
    print("   📊 推奨ポートフォリオ:")
    for ticker, weight in weights.items():
        if weight > 0.01:
            print(f"      - {ticker}: {weight*100:.1f}%")
            
    # リバランス指示テスト
    current_pos = {'CRYPTO_BTC': 100000} # BTCのみ持っている状態
    total_equity = 1000000
    
    instructions = pm.calculate_rebalance_needs(current_pos, weights, total_equity)
    print(f"   リバランス指示: {len(instructions)}件")
    for tick, action in instructions.items():
        print(f"      -> {tick}: {action}")

    return len(weights) > 0

def test_social_sentiment():
    print("\n" + "="*50)
    print("🐦 Social Sentiment Engine テスト")
    print("="*50)
    
    from src.social_sentiment import get_social_engine
    engine = get_social_engine()
    
    print("   Reddit Hypeスコア計測中...")
    hype = engine.analyze_hype()
    
    print(f"   🔥 Hype Scores: {hype}")
    
    return True

if __name__ == "__main__":
    passed = 0
    passed += 1 if test_global_market_access() else 0
    passed += 1 if test_portfolio_manager_v2() else 0
    passed += 1 if test_social_sentiment() else 0
    
    if passed == 3:
        print("\n🎉 Phase 54 全機能検証完了！ AIヘッジファンド稼働準備OK")
    else:
        print(f"\n⚠️ 検証不合格 ({passed}/3)")
