"""
AI Investment Committee UI
Visualizes the debate between AI agents.
"""
import streamlit as st
import time
from src.agents.committee import InvestmentCommittee
from src.paper_trader import PaperTrader
from src.data_loader import fetch_market_summary

def render_committee_ui():
    """Renders the AI Committee Tab"""
    st.header("🏛️ AI投資委員会 (The Boardroom)")
    st.caption("AIエージェントたちがあなたのポートフォリオと市場状況を議論し、投資判断を下します。")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📋 議題 (Agenda)")
        ticker_input = st.text_input("銘柄コード (例: 7203.T)", "7203.T")
        
        st.markdown("### 🤵 参加エージェント")
        st.write("1. **📈 Market Analyst**: テクニカル・ファンダメンタルズ分析担当")
        st.write("2. **🛡️ Risk Manager**: リスク管理・ポートフォリオバランス担当")
        st.write("3. **🏛️ Chairperson**: 議長・最終意思決定者")
        
        start_btn = st.button("委員会を開催する", type="primary", use_container_width=True)
        
    with col2:
        st.subheader("💬 議事録 (Minutes)")
        
        if start_btn:
            # Prepare context
            with st.spinner("委員会を招集しています..."):
                try:
                    committee = InvestmentCommittee()
                    
                    # Fetch actual data for Regime Detection
                    from src.data_loader import fetch_stock_data
                    market_df = fetch_stock_data(ticker_input, period="1y")

                    # Fetch minimal data for simulation
                    market_summary_df, _ = fetch_market_summary()
                    market_stats = {
                        "price": market_df['Close'].iloc[-1] if not market_df.empty else 2500,
                        "vix": 18.5, # In real app, fetch from ^VIX
                        "market_trend": "Neutral",
                        "market_df": market_df # Pass DF for Analyst to use RegimeDetector
                    }
                    if not market_summary_df.empty:
                        # Simple logic to get N225 trend
                        n225 = market_summary_df[market_summary_df['ticker'] == '^N225']
                        if not n225.empty:
                            market_stats["market_trend"] = "Bullish" if n225.iloc[0]['change_percent'] > 0 else "Bearish"
                    
                    # Visualize Regime if possible
                    from src.regime_detector import RegimeDetector
                    regime_det = RegimeDetector()
                    if not market_df.empty:
                        regime_info = regime_det.get_regime_signal(market_df)
                        st.info(f"🐻🐮 **市場環境 (Regime)**: {regime_info['regime_name']}\n\nRunning Logic: {regime_info['description']}")

                    
                    # Fetch Position
                    pt = PaperTrader()
                    positions = pt.get_positions()
                    current_position = None
                    if not positions.empty and ticker_input in positions.index:
                        current_position = positions.loc[ticker_input].to_dict()
                        
                    # Conduct Debate
                    debate_log = committee.conduct_debate(ticker_input, market_stats, current_position)
                    
                    # Stream the debate
                    chat_container = st.container()
                    with chat_container:
                        for entry in debate_log:
                            with st.chat_message(entry["agent"], avatar=entry["avatar"]):
                                st.write(f"**{entry['agent']}**")
                                st.write(entry["message"])
                            time.sleep(1.5) # Simulate typing/thinking delay
                            
                    # Final Decision Highlight
                    final_decision = debate_log[-1]["decision"]
                    if final_decision == "BUY":
                        st.success(f"### 🎯 決定: 買い (BUY) 推奨")
                    elif final_decision == "SELL":
                        st.error(f"### 🛑 決定: 売り (SELL) 推奨")
                    else:
                        st.warning(f"### ✋ 決定: 様子見 (HOLD)")
                        
                except Exception as e:
                    st.error(f"委員会中にエラーが発生しました: {e}")
        else:
            st.info("👈 左側のパネルで銘柄を指定し、「委員会を開催する」ボタンを押してください。")
            st.image("https://placehold.co/600x400?text=AI+Committee+Waiting...", caption="Meeting Room Empty")

