"""
Sidebar UI Module
Handles the rendering of the sidebar, including settings and filters.
"""

import json

import streamlit as st

from src.constants import MARKETS, TICKER_NAMES
from src.schemas import load_config as load_config_schema

from src import demo_data  # noqa: F401  # imported for side-effects if needed

def load_config():
    """Load config utilizing schema validation (fallback to defaults if error)."""
    config_obj = load_config_schema("config.json")
    return config_obj.model_dump()


def render_sidebar():
    """
    Renders a minimal sidebar for Hyper-Autonomous Mode.
    All trading parameters are determined automatically by the AI.
    """
    st.sidebar.header("🤖 Hyper-Auto Mode")

    st.sidebar.success("✅ システムが全自動で運用中")

    st.sidebar.markdown(
        """
    **AIが自動設定:**
    - 📊 市場: 日本株 (N225)
    - 🎯 銘柄: 自動選定
    - 📅 期間: 最適化済み
    - 💹 単位: 単元株
    """
    )

    st.sidebar.divider()

    # Demo mode toggle
    use_demo = st.sidebar.checkbox("🧪 デモモード (オフライン向け)", value=st.session_state.get("use_demo_data", False))
    st.session_state["use_demo_data"] = use_demo

    # Dark Mode Toggle
    dark_mode = st.sidebar.checkbox("🌙 ダークモード", value=True)
    if dark_mode:
        st.markdown(
            """
        <style>
        .stApp { background-color: #0e1117; color: #fafafa; }
        </style>
        """,
            unsafe_allow_html=True,
        )

    st.sidebar.info("⚙️ 詳細設定は「🧪 戦略研究所」→「システム設定」から")

    # Return defaults (AI-selected values)
    return {
        "selected_market": "Japan",
        "ticker_group": "Japan 主要銘柄",
        "custom_tickers": [],
        "period": "2y",
        "use_fractional_shares": False,
        "trading_unit": 100,
        "allow_short": False,
        "position_size": 1.0,
        "enable_fund_filter": False,
        "max_per": 15.0,
        "max_pbr": 1.5,
        "min_roe": 8.0,
    }
