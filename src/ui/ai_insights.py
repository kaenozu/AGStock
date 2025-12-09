import streamlit as st
import pandas as pd
from datetime import datetime
from src.agents.committee import InvestmentCommittee
from src.paper_trader import PaperTrader
from src.schemas import TradingDecision

def render_ai_insights():
    st.title("🤖 AI投資委員会 (AI Investment Committee)")
    st.markdown("複数の専門AIエージェントが市場データを多角的に分析し、合議制で投資判断を下します。")

    # Initialize Committee
    committee = InvestmentCommittee() # Config is handled internally or passed if needed
    
    # Context Data Gathering (Mocking for UI skeleton, real integration later)
    # In a real scenario, we'd fetch this from data_loader
    pt = PaperTrader()
    balance = pt.get_current_balance()
    portfolio = pt.get_positions()
    
    market_context = {
        "market_stats": {"trend": "UP", "volatility": "LOW"}, # Placeholder
        "news_text": "Tech sector rallies on strong earnings reports.", # Placeholder
        "portfolio": {
            "cash_ratio": balance.get('cash', 0) / balance.get('total_equity', 1),
            "drawdown_pct": -0.02 # Placeholder
        },
        "vix": 18.5 # Placeholder
    }

    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("📢 委員会を招集する (分析開始)", type="primary"):
            with st.spinner("AIエージェントが激論を交わしています..."):
                result = committee.hold_meeting(market_context)
                st.session_state['ai_result'] = result
    
    # Display Results
    if 'ai_result' in st.session_state:
        result = st.session_state['ai_result']
        decision = result['final_decision']
        
        # 1. Final Verdict
        st.divider()
        st.subheader("🏛️ 委員会の最終決定")
        
        color_map = {
            "BUY": "green",
            "SELL": "red",
            "HOLD": "orange"
        }
        color = color_map.get(decision, "gray")
        
        st.markdown(f"""
        <div style="padding: 20px; border-radius: 10px; border: 2px solid {color}; text-align: center; background-color: rgba(0,0,0,0.2);">
            <h1 style="color: {color}; margin: 0;">{decision}</h1>
            <p style="font-size: 1.2em; margin-top: 10px;">{result['rationale']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. Agent Breakdown
        st.subheader("🗣️ 各エージェントの意見")
        
        analyses = result['analyses']
        cols = st.columns(len(analyses))
        
        for idx, analysis in enumerate(analyses):
            with cols[idx]:
                role_icon = "📈" if "Market" in analysis['agent_name'] else "🛡️"
                st.markdown(f"### {role_icon} {analysis['agent_name']}")
                st.caption(analysis['role'])
                
                d_color = color_map.get(analysis['decision'], "gray")
                st.markdown(f"**判断**: :{d_color}[{analysis['decision']}]")
                st.markdown(f"**信頼度**: {analysis['confidence']*100:.0f}%")
                st.info(analysis['reasoning'])
        
        st.caption(f"分析時刻: {result['timestamp']}")
