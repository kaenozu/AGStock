import streamlit as st

from src.ui.ai_chat import render_ai_chat
from src.ui.committee_ui import render_committee_ui
from src.ui.earnings_analyst import render_earnings_analyst  # Phase 28
from src.ui.news_analyst import render_news_analyst
from src.ui.journal import render_trade_journal


def render_ai_hub():
    """Renders the consolidated AI Analyzer Hub"""
    st.header("🤖 AI分析センター (AI Hub)")
    st.caption("最新ニュース、投資委員会、AIチャットなど、すべてのAI機能にここからアクセスできます。")

    tabs = st.tabs(["🏛️ AI投資委員会", "📰 ニュース分析", "💬 AIチャット", "📑 決算分析", "📔 トレード日誌"])

    with tabs[0]:
        render_committee_ui()

    with tabs[1]:
        render_news_analyst()

    with tabs[2]:
        render_ai_chat()

    with tabs[3]:
        render_earnings_analyst()

    with tabs[4]:
        render_trade_journal()
