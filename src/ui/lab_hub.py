import streamlit as st

from src.ui.model_health import render_model_health
from src.ui.scenario_sandbox import render_scenario_sandbox
from src.ui.settings import render_settings_tab
from src.ui.strategy_arena import render_strategy_arena


def render_lab_hub():
    """Renders the Laboratory / Settings Hub"""
    st.header("🧪 戦略研究所 & 設定 (Lab)")
    st.caption("新しいアルゴリズムの実験や、システムの詳細設定を行います。")

    tabs = st.tabs(["⚔️ 戦略アリーナ", "⚙️ システム設定", "🩺 健全性メーター", "🧪 シナリオサンドボックス"])

    with tabs[0]:
        render_strategy_arena()

    with tabs[1]:
        render_settings_tab()

    with tabs[2]:
        render_model_health()

    with tabs[3]:
        render_scenario_sandbox()
