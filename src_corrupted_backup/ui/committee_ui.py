# """
# AI Investment Committee UI
# Visualizes the debate between AI agents.
import time
import streamlit as st
from src.agents.committee import InvestmentCommittee
from src.data_loader import fetch_market_summary
from src.paper_trader import PaperTrader
from src.data.macro_loader import MacroLoader
# """
def render_committee_ui():
    st.header("🏛️AI投資委員会 (The Boardroom)")
    st.caption("AIエージェントたちがあなたのポートフォリオと市場状況を議論し、投資判断を下します。")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("📋 議題 (Agenda)")
        ticker_input = st.text_input("銘柄コード (例: 7203.T)", "7203.T")
#             st.markdown("""" 🤵 参加エージェント)")
#         st.write("1. **📈 Market Analyst**: チャートニカル・ファンダメンタルズ分析)")
#         st.write("2. **🛡️Risk Manager**: リスク管理・ポートフォリオバランス分析")
#         st.write("3. **🌐 Macro Strategist**: グローバルマクロ・相関分析")
#         st.write("4. **🏛️Chairperson**: 議長・最終意思決定")
#             start_btn = st.button("委員会を開催する", type="primary", use_container_width=True)
# # Macro Radar Dashboard
#         st.markdown("---")
#         st.subheader("🌐 マクロ相関レーダー")
#         macro = MacroLoader().fetch_macro_data()
#         if "error" not in macro:
    pass
#             score = macro["macro_score"]
#             if score > 70:
    pass
#                 st.success(f"市場安定度: {score:.0f}/100 (BULLISH)")
#             elif score < 40:
    pass
#                 st.error(f"市場安定度: {score:.0f}/100 (CAUTION)")
#             else:
    pass
#                 st.warning(f"市場安定度: {score:.0f}/100 (NEUTRAL)")
#                 mc1, mc2 = st.columns(2)
#             with mc1:
    pass
#                 st.metric(
#                     "VIX", f"{macro['vix']['value']:.1f}", f"{macro['vix']['change_pct']:+.1f}%", delta_color="inverse"
#                 )
#                 st.metric(
#                     "米10年債",
#                     f"{macro['yield_10y']['value']:.2f}%",
#                     f"{macro['yield_10y']['change_pct']:+.1f}%",
#                     delta_color="inverse",
#                 )
#             with mc2:
    pass
#                 st.metric("USD/JPY", f"{macro['usdjpy']['value']:.2f}", f"{macro['usdjpy']['change_pct']:+.1f}%")
#                 st.metric("SOX指数", f"{macro['sox']['value']:.0f}", f"{macro['sox']['change_pct']:+.1f}%")
#         with col2:
    pass
#             st.subheader("💬 議事録 (Minutes)")
#             if start_btn:
    pass
#                 # Prepare context
#             with st.spinner("委員会を招集してます.."):
    pass
#                 try:
    pass
#                     committee = InvestmentCommittee()
# # Fetch actual data for Regime Detection
from src.data_loader import fetch_stock_data
market_data_dict = fetch_stock_data([ticker_input], period="1y")
# Extract DataFrame from dict
market_df = market_data_dict.get(ticker_input) if market_data_dict else None
# Fetch minimal data for simulation
market_summary_df, _ = fetch_market_summary()
                    market_stats = {
                        "price": (
                            market_df["Close"].iloc[-1] if (market_df is not None and not market_df.empty) else 2500
                        ),
                        "vix": 18.5,  # In real app, fetch from ^VIX
                        "market_trend": "Neutral",
                    }
                    if not market_summary_df.empty:
                        # Simple logic to get N225 trend
                        n225 = market_summary_df[market_summary_df["ticker"] == "^N225"]
                        if not n225.empty:
                            market_stats["market_trend"] = (
                                "Bullish" if n225.iloc[0]["change_percent"] > 0 else "Bearish"
                            )
# Visualize Regime if possible
from src.regime_detector import RegimeDetector
regime_det = RegimeDetector()
                    if market_df is not None and not market_df.empty:
                        regime_info = regime_det.get_regime_signal(market_df)
                        st.info(
                            f"🐻🐮 **市場環境 (Regime)**: {regime_info['regime_name']}\n\nRunning Logic: {regime_info['description']}"
                        )
# Fetch Position
pt = PaperTrader()
                    positions = pt.get_positions()
                    current_position = None
                    if not positions.empty and ticker_input in positions.index:
                        current_position = positions.loc[ticker_input].to_dict()
# Conduct Debate
debate_log = committee.conduct_debate(
                        ticker_input, market_stats, current_position, market_df=market_df
                    )
# Phase 29: Paradigm Metamorphosis Status
paradigm = committee.current_paradigm
                    if paradigm != "UNKNOWN":
                        pass
#                         st.markdown(f"""" 🎭 現在のパラダイム: `{paradigm}`")
# # Try to find shift report in last_meeting_result (though review_candidate sets it)
# # For simple UI, we'll just show the description from ParadigmManager
from src.evolution.paradigm_switcher import ParadigmManager
pm = ParadigmManager()
                        desc = pm.PARADIGMS.get(paradigm, {}).get("description", "相場環境の変動を監視中...")
                        st.caption(f"🧭 {desc}")
# Stream the debate
chat_container = st.container()
                    with chat_container:
                        for entry in debate_log:
                            with st.chat_message(entry["agent"], avatar=entry["avatar"]):
                                st.write(f"**{entry['agent']}**")
                                st.write(entry["message"])
# Phase 92: Display the 'Visual Perspective' if from VisualOracle
if entry["agent"] == "VisualOracle":
                                    from src.evolution.chart_vision import ChartVisionEngine
# We can re-generate the base64 for just the UI display
vision_img = ChartVisionEngine().get_image_base64(market_df)
                                    st.image(
                                        f"data:image/png;base64,{vision_img}", caption="AI が視覚的に解析したチャート"
                                    )
                                time.sleep(1.0)  # Faster for UX
# Final Decision Highlight
final_decision = debate_log[-1]["decision"]
                    if final_decision == "BUY":
                        pass
#                         st.success(f"""" 🎯 決定 買い (BUY) 推奨")
#                     elif final_decision == "SELL":
#                         st.error(f"""" 🛑 決定 売り (SELL) 推奨")
else:
                        pass
#                         st.warning(f"""" ✋決定 様子見 (HOLD)")
# # Phase 700: Council of 100 Visualization
#                     st.markdown("---")
#                     st.subheader("🏛️ アバター評議会 (Council of 100) 統計")
# # We look for AvatarCouncil in debate_log or call it directly if not found
#                     council_entry = next((e for e in debate_log if e["agent"] == "AvatarCouncil"), None)
#                     if council_entry:
    pass
#                         # Parsing clusters from message if possible, or just using placeholders if we don't store raw stats
# # Since conduct_debate returns a list of dicts, we could've stored more info.
# # For now, let's display the message as a highlighted quote.
#                         st.info(council_entry["message"])
# # Mock display of distribution
#                         c1, c2, c3 = st.columns(3)
# # We extract numbers from message like "Clusters: 42 Bulls, 30 Bears, 28 Neutral"
import re
msg = council_entry["message"]
                        bulls = re.search(r"(\d+) Bulls", msg)
                        bears = re.search(r"(\d+) Bears", msg)
                        neutrals = re.search(r"(\d+) Neutral", msg)
                            if bulls and bears and neutrals:
                                c1.metric("Bulls (強気)", f"{bulls.group(1)}", "+")
                            c2.metric("Bears (弱気)", f"{bears.group(1)}", "-", delta_color="inverse")
                            c3.metric("Neutral (中立)", f"{neutrals.group(1)}")
                    except Exception as e:
                        st.error(f"委員会中にエラーが発生しました: {e}")
        else:
            st.info("👈 左側のパネルで銘柄を指定し、「委員会を開催する」ボタンを押してください。")
            st.image("https://placehold.co/600x400?text=AI+Committee+Waiting...", caption="Meeting Room Empty")

# """  # Force Balanced
# """
