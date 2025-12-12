
"""
AI Chat Interface (Ghostwriter)
"""
import streamlit as st
import json
from src.llm_reasoner import get_llm_reasoner
from src.paper_trader import PaperTrader
from src.agents.committee import InvestmentCommittee

def render_ai_chat():
    """Renders the Ghostwriter chat interface."""
    st.header("町 AI Chat (Ghostwriter with Context)")
    st.write("AGStock縺ｮ繧｢繧ｷ繧ｹ繧ｿ繝ｳ繝医隈hostwriter縲阪′縲∝ｸょｴ蛻・梵繧・・繝ｼ繝医ヵ繧ｩ繝ｪ繧ｪ縺ｫ縺､縺・※縺顔ｭ斐∴縺励∪縺吶・)
    
    # 1. Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Initial greeting
        st.session_state.messages.append({
            "role": "assistant",
            "content": "縺薙ｓ縺ｫ縺｡縺ｯ・∵悽譌･縺ｮ蟶ょｴ繧・・繝ｼ繝医ヵ繧ｩ繝ｪ繧ｪ縺ｫ縺､縺・※縲∽ｽ輔°豌励↓縺ｪ繧九％縺ｨ縺ｯ縺ゅｊ縺ｾ縺吶°・・
        })

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
            prompt = st.text_input("雉ｪ蝠上ｒ蜈･蜉帙＠縺ｦ縺上□縺輔＞... (萓・ 繝医Κ繧ｿ縺ｮ蛻・梵繧偵♀鬘倥＞)", key="chat_input_text")
        with col_btn:
            # Align button
            st.write("") 
            st.write("")
            submitted = st.form_submit_button("騾∽ｿ｡", use_container_width=True)

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
                    positions = pt.get_positions().to_dict(orient='records')
                    
                    # 2. Market Data
                    from src.data_loader import fetch_market_summary
                    market_summary_df, _ = fetch_market_summary()
                    market_context = market_summary_df.to_dict(orient='records') if not market_summary_df.empty else "No market data available"

                    # 3. Committee Decision (Placeholder for now)
                    committee_context = "No recent committee meeting held."
                    
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
                    """
                    
                    reasoner = get_llm_reasoner()
                    
                    # Call LLM
                    response = reasoner.chat_with_context(
                        user_message=prompt,
                        history=st.session_state.messages[:-1], 
                        context_data=context_data
                    )
                    
                    message_placeholder.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"逕ｳ縺苓ｨｳ縺ゅｊ縺ｾ縺帙ｓ縲√お繝ｩ繝ｼ縺檎匱逕溘＠縺ｾ縺励◆: {str(e)}"
                    message_placeholder.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        st.experimental_rerun()
