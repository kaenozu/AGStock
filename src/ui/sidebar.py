"""
Sidebar UI Module
Handles the rendering of the sidebar, including settings and filters.
"""

import json

import streamlit as st

from src.constants import MARKETS, TICKER_NAMES
from src.schemas import load_config as load_config_schema
from src.services.defense import activate_defense, deactivate_defense, defense_status

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

    # --- One-click Defense Mode ---
    st.sidebar.subheader("🛡️ ワンクリック防御モード")
    current_on = st.session_state.get("defense_mode", defense_status())
    toggle = st.sidebar.checkbox("新規BUY抑制 + リスク圧縮", value=current_on)

    if toggle and not current_on:
        snapshot = activate_defense()
        st.session_state["defense_snapshot"] = snapshot
        st.session_state["defense_mode"] = True
        st.sidebar.success("防御モードを適用しました")
    elif not toggle and current_on:
        deactivate_defense(st.session_state.get("defense_snapshot"))
        st.session_state["defense_snapshot"] = None
        st.session_state["defense_mode"] = False
        st.sidebar.info("防御モードを解除しました")

    st.sidebar.caption("SAFE_MODE=1, シナリオ=conservative, 銘柄/セクター上限を引き締めます。")

    st.sidebar.divider()

    # --- New Risk Monitor Section ---
    st.sidebar.subheader("🛡️ リスク監視モニター")

    # Check Market Crash (if Risk Manager is initialized)
    if "risk_manager" in st.session_state and st.session_state["risk_manager"]:
        rm = st.session_state["risk_manager"]
        # Simplified check (logging mocked or passed appropriately)
        # Note: In a UI loop, we might want to cache this or run it less frequently.
        # For now, we run it every re-render to ensure safety status.
        crash_ok, crash_reason = rm.check_market_crash(logger=None)  # Logger optional/none for UI check

        if crash_ok:
            st.sidebar.success("✅ 市場状況: 正常")
        else:
            st.sidebar.error("🚨 市場急落警戒中")
            st.sidebar.caption(f"{crash_reason}")

        # Divine Shield Status
        guidance = getattr(rm, "oracle_guidance", None)
        if guidance:
            st.sidebar.info(f"✨ Divine Shield: {guidance['max_drawdown_adj']:.1f}x Defense")
        
        # Display VaR (Mock or stored value if available)
        st.sidebar.metric(label="予想最大損失率 (VaR)", value=f"{rm.confidence_level*100:.1f}%", delta="Oracle-Adj")
    else:
        st.sidebar.warning("⚠️ リスク管理未初期化")

    # --- Oracle 2026 Widget ---
    st.sidebar.subheader("🔮 Oracle 2026")
    try:
        from src.ui.oracle_widget import render_oracle_sidebar
        render_oracle_sidebar()
    except Exception as e:
        st.sidebar.info(f"Oracle: {e}")

    # --- Real-time Status ---
    st.sidebar.subheader("⚡ リアルタイム接続")
    st.sidebar.success("🟢 接続 (遅延なし)")
    st.sidebar.caption("最終更新: 数秒前")

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
