"""
Interactive AI Chat UI (RAG)
"""
import streamlit as st
from src.ai_analyst import AIAnalyst
from src.paper_trader import PaperTrader
from src.prompts import CHAT_SYSTEM_PROMPT

def render_ai_chat():
    st.header("💬 AI投資委員会チャット")
    st.write("ポートフォリオやシステムについて質問してください。")
    
    analyst = AIAnalyst()
    
    if not analyst.enabled:
        st.warning("⚠️ OpenAI APIキーが設定されていません。")
        return
    
    # Initialize chat history in session state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # Display chat history
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("質問を入力してください..."):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate context from system data
        with st.spinner("AI投資委員会が回答を準備中..."):
            context = _build_context()
            
            # Generate response
            full_prompt = f"{context}\n\nUser Question: {prompt}"
            response = analyst.generate_response(
                system_prompt=CHAT_SYSTEM_PROMPT,
                user_prompt=full_prompt,
                temperature=0.7
            )
        
        # Add assistant message
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
    
    # Clear chat button
    if st.button("🗑️ チャット履歴をクリア"):
        st.session_state.chat_messages = []
        st.rerun()

def _build_context() -> str:
    """Build context from current system state."""
    pt = PaperTrader()
    balance = pt.get_current_balance()
    positions = pt.get_positions()
    
    context = "## Current System State\n\n"
    context += "### Portfolio\n"
    context += f"- Total Equity: ¥{balance['total_equity']:,.0f}\n"
    context += f"- Cash: ¥{balance['cash']:,.0f}\n"
    context += f"- Number of Positions: {len(positions)}\n\n"
    
    if not positions.empty:
        context += "### Current Positions\n"
        for _, row in positions.iterrows():
            pnl_pct = (row['current_price'] - row['entry_price']) / row['entry_price']
            context += f"- {row['ticker']}: {row['quantity']} shares @ ¥{row['entry_price']:,.0f}, "
            context += f"Current: ¥{row['current_price']:,.0f} ({pnl_pct:+.1%})\n"
    
    return context
