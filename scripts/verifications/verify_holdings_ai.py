
import sqlite3
import pandas as pd
from src.agents.ai_veto_agent import AIVetoAgent
from src.agents.social_analyst import SocialAnalyst

def main():
    conn = sqlite3.connect("paper_trading.db")
    df = pd.read_sql_query("SELECT ticker, entry_price FROM positions", conn)
    conn.close()

    if df.empty:
        print("現在保有している銘柄はありません。")
        return

    ai_veto = AIVetoAgent()
    social = SocialAnalyst()

    print(f"\n=== 新システムによる保有銘柄の再検証 ({len(df)}銘柄) ===\n")

    for _, row in df.iterrows():
        ticker = row['ticker']
        entry = row['entry_price']
        
        print(f"[{ticker}] (取得単価: ¥{entry:,.0f}) 分析中...")
        
        # 1. AI Veto Check
        is_safe, veto_reason = ai_veto.review_signal(ticker, "HOLD", entry, "Current Holding Review")
        
        # 2. Social Heat Check
        social_data = social.analyze_heat(ticker)
        
        print(f"  - AI Veto判定: {'✅ 承認' if is_safe else '❌ 拒否'}")
        print(f"  - 理由: {veto_reason}")
        print(f"  - ソーシャル熱量: {social_data.get('heat_level', 0):.1f}/10.0")
        print(f"  - ソーシャルリスク: {social_data.get('social_risk', 'LOW')}")
        print(f"  - 社会的センチメント: {social_data.get('sentiment', 'NEUTRAL')}")
        print("-" * 30)

if __name__ == "__main__":
    main()
