import streamlit as st
# Lazy loading sub-panels
def render_lab_hub():
    st.header("🧪 戦略研究所 & 設定 (Lab)")
    st.caption("新しいアルゴリズムの実験や、システムの詳細設定を行います。")
        tabs = st.tabs(["⚔️ 戦略アリーナ", "⚙️ システム設定", "🏋️ AIジム", "✨ 生成ラボ", "🛡️ レジリエンス"])
        with tabs[0]:
            from src.ui.strategy_arena import render_strategy_arena
            render_strategy_arena()
        with tabs[1]:
            from src.ui.settings import render_settings_tab
            render_settings_tab()
        with tabs[2]:
            from src.ui.rl_training_ui import render_rl_training_ui
            render_rl_training_ui()
        with tabs[3]:
            from src.ui.gen_lab import render_gen_lab
            render_gen_lab()
        with tabs[4]:
            from src.ui.resilience_ui import render_resilience_tab
            render_resilience_tab()
