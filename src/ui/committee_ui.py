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
    st.header("鋤・・AI謚戊ｳ・ｧ泌藤莨・(The Boardroom)")
    st.caption("AI繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医◆縺｡縺後≠縺ｪ縺溘・繝昴・繝医ヵ繧ｩ繝ｪ繧ｪ縺ｨ蟶ょｴ迥ｶ豕√ｒ隴ｰ隲悶＠縲∵兜雉・愛譁ｭ繧剃ｸ九＠縺ｾ縺吶・)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("搭 隴ｰ鬘・(Agenda)")
        ticker_input = st.text_input("驫俶氛繧ｳ繝ｼ繝・(萓・ 7203.T)", "7203.T")
        
        st.markdown("### ､ｵ 蜿ょ刈繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・)
        st.write("1. **嶋 Market Analyst**: 繝・け繝九き繝ｫ繝ｻ繝輔ぃ繝ｳ繝繝｡繝ｳ繧ｿ繝ｫ繧ｺ蛻・梵諡・ｽ・)
        st.write("2. **孱・・Risk Manager**: 繝ｪ繧ｹ繧ｯ邂｡逅・・繝昴・繝医ヵ繧ｩ繝ｪ繧ｪ繝舌Λ繝ｳ繧ｹ諡・ｽ・)
        st.write("3. **鋤・・Chairperson**: 隴ｰ髟ｷ繝ｻ譛邨よэ諤晄ｱｺ螳夊・)
        
        start_btn = st.button("蟋泌藤莨壹ｒ髢句ぎ縺吶ｋ", type="primary", use_container_width=True)
        
    with col2:
        st.subheader("町 隴ｰ莠矩鹸 (Minutes)")
        
        if start_btn:
            # Prepare context
            with st.spinner("蟋泌藤莨壹ｒ諡幃寔縺励※縺・∪縺・.."):
                try:
                    committee = InvestmentCommittee()
                    
                    # Fetch actual data for Regime Detection
                    from src.data_loader import fetch_stock_data
                    market_data_dict = fetch_stock_data([ticker_input], period="1y")
                    # Extract DataFrame from dict
                    market_df = market_data_dict.get(ticker_input) if market_data_dict else None

                    # Fetch minimal data for simulation
                    market_summary_df, _ = fetch_market_summary()
                    market_stats = {
                        "price": market_df['Close'].iloc[-1] if (market_df is not None and not market_df.empty) else 2500,
                        "vix": 18.5, # In real app, fetch from ^VIX
                        "market_trend": "Neutral"
                    }
                    if not market_summary_df.empty:
                        # Simple logic to get N225 trend
                        n225 = market_summary_df[market_summary_df['ticker'] == '^N225']
                        if not n225.empty:
                            market_stats["market_trend"] = "Bullish" if n225.iloc[0]['change_percent'] > 0 else "Bearish"
                    
                    # Visualize Regime if possible
                    from src.regime_detector import RegimeDetector
                    regime_det = RegimeDetector()
                    if market_df is not None and not market_df.empty:
                        regime_info = regime_det.get_regime_signal(market_df)
                        st.info(f"製整 **蟶ょｴ迺ｰ蠅・(Regime)**: {regime_info['regime_name']}\n\nRunning Logic: {regime_info['description']}")

                    
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
                        st.success(f"### 識 豎ｺ螳・ 雋ｷ縺・(BUY) 謗ｨ螂ｨ")
                    elif final_decision == "SELL":
                        st.error(f"### 尅 豎ｺ螳・ 螢ｲ繧・(SELL) 謗ｨ螂ｨ")
                    else:
                        st.warning(f"### 笨・豎ｺ螳・ 讒伜ｭ占ｦ・(HOLD)")
                        
                except Exception as e:
                    st.error(f"蟋泌藤莨壻ｸｭ縺ｫ繧ｨ繝ｩ繝ｼ縺檎匱逕溘＠縺ｾ縺励◆: {e}")
        else:
            st.info("争 蟾ｦ蛛ｴ縺ｮ繝代ロ繝ｫ縺ｧ驫俶氛繧呈欠螳壹＠縲√悟ｧ泌藤莨壹ｒ髢句ぎ縺吶ｋ縲阪・繧ｿ繝ｳ繧呈款縺励※縺上□縺輔＞縲・)
            st.image("https://placehold.co/600x400?text=AI+Committee+Waiting...", caption="Meeting Room Empty")

