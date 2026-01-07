"""
AI Investment Committee UI
Visualizes the debate between AI agents.
"""

import time

import streamlit as st

from src.agents.committee import InvestmentCommittee
from src.data_loader import fetch_market_summary
from src.paper_trader import PaperTrader
from src.data.macro_loader import MacroLoader


def render_committee_ui():
    """Renders the AI Committee Tab"""
    st.header("🏛️AI投資委員会 (The Boardroom)")
    st.caption("AIエージェントたちがあなたのポートフォリオと市場状況を議論し、投資判断を下します。")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📋 議題 (Agenda)")
        ticker_input = st.text_input("銘柄コード (例: 7203.T)", "7203.T")

        st.markdown("### 🤵 参加エージェント)")
        st.write("1. **📈 Market Analyst**: チャートニカル・ファンダメンタルズ分析)")
        st.write("2. **🛡️Risk Manager**: リスク管理・ポートフォリオバランス分析")
        st.write("3. **🌐 Macro Strategist**: グローバルマクロ・相関分析")
        st.write("4. **🏛️Chairperson**: 議長・最終意思決定")

        start_btn = st.button("委員会を開催する", type="primary", use_container_width=True)

        # Macro Radar Dashboard
        st.markdown("---")
        st.subheader("🌐 マクロ相関レーダー")
        macro = MacroLoader().fetch_macro_data()
        if "error" not in macro:
            score = macro["macro_score"]
            if score > 70:
                st.success(f"市場安定度: {score:.0f}/100 (BULLISH)")
            elif score < 40:
                st.error(f"市場安定度: {score:.0f}/100 (CAUTION)")
            else:
                st.warning(f"市場安定度: {score:.0f}/100 (NEUTRAL)")

            mc1, mc2 = st.columns(2)
            with mc1:
                st.metric(
                    "VIX", f"{macro['vix']['value']:.1f}", f"{macro['vix']['change_pct']:+.1f}%", delta_color="inverse"
                )
                st.metric(
                    "米10年債",
                    f"{macro['yield_10y']['value']:.2f}%",
                    f"{macro['yield_10y']['change_pct']:+.1f}%",
                    delta_color="inverse",
                )
            with mc2:
                st.metric("USD/JPY", f"{macro['usdjpy']['value']:.2f}", f"{macro['usdjpy']['change_pct']:+.1f}%")
                st.metric("SOX指数", f"{macro['sox']['value']:.0f}", f"{macro['sox']['change_pct']:+.1f}%")

    with col2:
        st.subheader("💬 議事録 (Minutes)")

        if start_btn:
            # Prepare context
            with st.spinner("委員会を招集してます.."):
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
                    debate_log = committee.conduct_debate(ticker_input, market_stats, current_position)

                    # Stream the debate
                    chat_container = st.container()
                    with chat_container:
                        for entry in debate_log:
                            with st.chat_message(entry["agent"], avatar=entry["avatar"]):
                                st.write(f"**{entry['agent']}**")
                                st.write(entry["message"])
                            time.sleep(1.5)  # Simulate typing/thinking delay

                    # Final Decision Highlight
                    final_decision = debate_log[-1]["decision"]
                    if final_decision == "BUY":
                        st.success("### 🎯 決定 買い (BUY) 推奨")
                    elif final_decision == "SELL":
                        st.error("### 🛑 決定 売り (SELL) 推奨")
                    else:
                        st.warning("### ✋決定 様子見 (HOLD)")

                except Exception as e:
                    st.error(f"委員会中にエラーが発生しました: {e}")
        else:
            st.info("👈 左側のパネルで銘柄を指定し、「委員会を開催する」ボタンを押してください。")
            st.image("https://placehold.co/600x400?text=AI+Committee+Waiting...", caption="Meeting Room Empty")
