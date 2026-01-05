"""
AI Chat Interface (Ghostwriter)
"""

import json
import asyncio
import threading

import streamlit as st

from src.llm_reasoner import get_llm_reasoner
from src.paper_trader import PaperTrader
from src.realtime import RealtimeDataClient


def render_ai_chat():
    """Renders the Ghostwriter chat interface."""
    st.header("💬 AI Chat (Ghostwriter with Context)")
    st.write("AGStockのアシスタント「Ghostwriter」が、市場動向とポートフォリオについてお答えします。")

    # 1. Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Initial greeting
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "こんにちは。本日の市場動向とポートフォリオについて、何か気になることはありますか？",
            }
        )

    # 2. Initialize Realtime Data Client
    if "realtime_client" not in st.session_state:
        st.session_state.realtime_client = RealtimeDataClient()
        st.session_state.realtime_data = {}

        # Start client in separate thread
        def start_client():
            asyncio.run(st.session_state.realtime_client.connect())

        client_thread = threading.Thread(target=start_client, daemon=True)
        client_thread.start()

        # Register data handler
        async def handle_market_data(data):
            st.session_state.realtime_data = data
            # Force Streamlit to rerun to update UI
            st.rerun()

        st.session_state.realtime_client.register_data_handler("market_data", handle_market_data)

    # 2. Display Chat Messages
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # 2.5. Handle External Input Triggers (e.g., from Market Scan)
    if st.session_state.get("chat_initial_input"):
        # Pre-fill the widget state
        st.session_state["chat_input_text"] = st.session_state.pop("chat_initial_input")

    # 3. Handle User Input (Form based for Tab compatibility)
    st.divider()
    with st.form(key="chat_form", clear_on_submit=True):
        col_in, col_btn = st.columns([6, 1])
        with col_in:
            prompt = st.text_input(
                "質問を入力してください... (例: トヤタの動向をお願い)",
                key="chat_input_text",
            )
        with col_btn:
            # Align button
            st.write("")
            st.write("")
            submitted = st.form_submit_button("送信", use_container_width=True)

    if submitted and prompt:
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # We need to rerun to show the latest message immediately in the container above?
        # Or just render it now. Rerunning is safer for persistent state view.
        # But let's try rendering it locally first to avoid full reload flicker.
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate Response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("Thinking...")

                try:
                    # Gather Context
                    # 1. Portfolio Data
                    pt = PaperTrader()
                    balance = pt.get_current_balance()
                    positions = pt.get_positions().to_dict(orient="records")

                    # 2. Market Data
                    from src.data_loader import fetch_market_summary

                    market_summary_df, _ = fetch_market_summary()
                    market_context = (
                        market_summary_df.to_dict(orient="records")
                        if not market_summary_df.empty
                        else "No market data available"
                    )

                    # 3. Committee Decision (Placeholder for now)
                    committee_context = "No recent committee meeting held."

                    # 4. Oracle 2026 Prophecies
                    try:
                        from src.oracle.oracle_2026 import Oracle2026

                        oracle = Oracle2026()
                        oracle_scenarios = oracle.speculate_scenarios()
                        oracle_resilience = oracle.assess_portfolio_resilience([])
                        oracle_context = f"Scenarios: {json.dumps(oracle_scenarios, ensure_ascii=False)}\nResilience: {json.dumps(oracle_resilience, ensure_ascii=False)}"
                    except:
                        oracle_context = "Oracle engine not available."

                    # 5. 2025 Retrospective
                    try:
                        from src.sovereign_retrospective import SovereignRetrospective

                        sr = SovereignRetrospective()
                        retrospective_insights = sr.analyze_2025_failures()
                        retro_context = json.dumps(retrospective_insights, ensure_ascii=False)
                    except:
                        retro_context = "Retrospective data not available."

                    # 4. Realtime Data
                    realtime_context = "No realtime data available."
                    if st.session_state.realtime_data:
                        realtime_context = json.dumps(st.session_state.realtime_data, ensure_ascii=False)

                    context_data = f"""
## User Portfolio
                    - Cash: {balance.get('cash', 0):,.0f} JPY
                    - Total Equity: {balance.get('total_equity', 0):,.0f} JPY
                    - Unrealized PnL: {balance.get('unrealized_pnl', 0):,.0f} JPY
                    - Positions: {json.dumps(positions, ensure_ascii=False)}

## Market Overview (Latest)
                    {json.dumps(market_context, ensure_ascii=False)}

## AI Committee
                    {committee_context}

## Realtime Data
                    {realtime_context}

## Oracle 2026 (Future Scenarios)
                    {oracle_context}

## 2025 Retrospective (Past Failures & Evolution)
                    {retro_context}
                    """

                    reasoner = get_llm_reasoner()

                    # Call LLM
                    response = reasoner.chat_with_context(
                        user_message=prompt,
                        history=st.session_state.messages[:-1],
                        context_data=context_data,
                    )

                    message_placeholder.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # Divine Voice Synthesis
                    if st.session_state.get("enable_divine_voice", False):
                        with st.spinner("神託を音声に変換中..."):
                            try:
                                from gtts import gTTS
                                import io
                                
                                # 短すぎる場合はスキップ、長すぎる場合は冒頭のみなど調整可
                                tts_text = response[:500] # 長すぎるとAPI制限やUX低下の恐れがあるため制限
                                
                                tts = gTTS(text=tts_text, lang='ja')
                                mp3_fp = io.BytesIO()
                                tts.write_to_fp(mp3_fp)
                                st.audio(mp3_fp, format='audio/mp3', autoplay=True)
                            except Exception as e:
                                st.error(f"音声合成エラー（Divine Voice）: {e}")

                except Exception as e:
                    error_msg = f"申し訳ありません、エラーが発生しました: {str(e)}"
                    message_placeholder.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

        st.rerun()

    # 4. Add Realtime Data Display
    with st.sidebar:
        st.divider()
        st.session_state["enable_divine_voice"] = st.toggle("🔊 Divine Voice (音声読み上げ)", value=False)
        
    if st.session_state.realtime_data:
        st.sidebar.subheader("📡 リアルタイム市場データ")
        realtime_data = st.session_state.realtime_data.get("data", {})
        for symbol, data in realtime_data.items():
            st.sidebar.write(f"**{symbol}**")
            st.sidebar.write(f"価格: {data.get('price', 0):.2f}")
            st.sidebar.write(f"変化: {data.get('change', 0):.2f}%")
            st.sidebar.write(f"出来高: {data.get('volume', 0):,}")
            st.sidebar.divider()
