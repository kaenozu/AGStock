import streamlit as st

from src.ui.settings import render_settings_tab
from src.ui.strategy_arena import render_strategy_arena
from src.ui.rl_training_ui import render_rl_training_ui
from src.ui.gen_lab import render_gen_lab


def render_lab_hub():
    """Renders the Laboratory / Settings Hub"""
    st.header("🧪 戦略研究所 & 設定 (Lab)")
    st.caption("新しいアルゴリズムの実験や、システムの詳細設定を行います。")

    tabs = st.tabs(["⚔️ 戦略アリーナ", "⚙️ システム設定", "🏋️ AIジム", "✨ 生成ラボ"])

    with tabs[0]:
        render_strategy_arena()

    with tabs[1]:
        render_settings_tab()

    with tabs[2]:
        render_rl_training_ui()
        
    with tabs[3]:
        render_gen_lab()
