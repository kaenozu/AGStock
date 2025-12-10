import streamlit as st
from src.ui.strategy_arena import render_strategy_arena
from src.ui.settings import render_settings_tab

def render_lab_hub():
    """Renders the Laboratory / Settings Hub"""
    st.header("🧪 戦略研究所 & 設定 (Lab)")
    st.caption("新しいアルゴリズムの実験や、システムの詳細設定を行います。")
    
    tabs = st.tabs(["⚔️ 戦略アリーナ", "⚙️ システム設定"])
    
    with tabs[0]:
        render_strategy_arena()
        
    with tabs[1]:
        render_settings_tab()
