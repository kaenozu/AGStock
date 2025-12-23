"""
AI投資委員会の動作確認スクリプト
"""
import sys
from src.agents.committee import InvestmentCommittee
from src.data_loader import fetch_stock_data

def test_committee():
    """委員会機能のテスト"""
    print("=" * 60)
    print("AI投資委員会 動作確認")
    print("=" * 60)
    
    try:
        # 1. 委員会初期化
        print("\n1. 委員会を初期化中...")
        committee = InvestmentCommittee()
        print("   ✓ 委員会初期化完了")
        
        # 2. データ取得
        print("\n2. 市場データ取得中...")
        ticker = "7203.T"
        market_data_dict = fetch_stock_data([ticker], period="1y")
        market_df = market_data_dict.get(ticker) if market_data_dict else None
        
        if market_df is None or market_df.empty:
            print("   ⚠️ データ取得失敗。デモデータで続行...")
            market_stats = {
                "price": 2500,
                "vix": 18.5,
                "market_trend": "Neutral",
                "market_df": None
            }
        else:
            print(f"   ✓ データ取得成功: {len(market_df)}行")
            market_stats = {
                "price": market_df['Close'].iloc[-1],
                "vix": 18.5,
                "market_trend": "Neutral"
            }
        
        # 3. 議論開始
        print("\n3. 委員会議論を開始...")
        debate_log = committee.conduct_debate(ticker, market_stats, None)
        
        print(f"   ✓ 議論完了: {len(debate_log)}件の発言")
        
        # 4. 結果表示
        print("\n" + "=" * 60)
        print("議事録")
        print("=" * 60)
        
        for i, entry in enumerate(debate_log, 1):
            print(f"\n{i}. {entry['avatar']} {entry['agent']}")
            print(f"   決定: {entry['decision']}")
            print(f"   発言: {entry['message'][:100]}...")
        
        # 5. 最終決定
        final_decision = debate_log[-1]['decision']
        print("\n" + "=" * 60)
        print(f"最終決定: {final_decision}")
        print("=" * 60)
        
        print("\n✅ テスト成功！エラーは発生しませんでした。")
        return True
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_committee()
    sys.exit(0 if success else 1)
