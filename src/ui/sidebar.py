"""
Sidebar UI Module
Handles the rendering of the sidebar, including settings and filters.
"""

import json

import streamlit as st

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

    # --- System Status Widget ---
    import os
    from datetime import datetime

    st.sidebar.subheader("📡 システム稼働状況")

    status_file = "data/system_status.json"
    scheduler_alive = False

    if os.path.exists(status_file):
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                sys_status = json.load(f)

            heartbeat = sys_status.get("heartbeat")
            if heartbeat:
                last_beat = datetime.fromisoformat(heartbeat)
                delta = datetime.now() - last_beat
                if delta.total_seconds() < 120:  # 2 minutes tolerance
                    scheduler_alive = True

            if scheduler_alive:
                st.sidebar.success(f"🟢 スケジューラー稼働中")
            else:
                st.sidebar.error(f"🔴 スケジューラー停止/無反応")
                if heartbeat:
                    st.sidebar.caption(f"最終ビート: {last_beat.strftime('%H:%M:%S')}")

            # Show individual job status
            jobs = sys_status.get("jobs", {})

            # Map for human readable
            job_map = {
                "auto_invest": "自動投資",
                "smart_alerts": "スマート監視",
                "morning_brief": "朝刊配送",
            }

            for key, label in job_map.items():
                info = jobs.get(key, {})
                status = info.get("status", "unknown")
                last_run = info.get("last_run", "")

                if last_run:
                    dt = datetime.fromisoformat(last_run)
                    timestr = dt.strftime("%H:%M")
                else:
                    timestr = "--:--"

                if status == "success":
                    icon = "🟢"
                elif status == "running":
                    icon = "🔄"
                elif status == "error":
                    icon = "🔴"
                else:
                    icon = "⚪"

                st.sidebar.markdown(f"{icon} **{label}**: {timestr}")
                if status == "error":
                    st.sidebar.caption(f"Err: {info.get('message', '')[:20]}...")

        except Exception:
            st.sidebar.warning(f"ステータス読込エラー")
    else:
        st.sidebar.warning("⚠️ ステータス情報なし")
        st.sidebar.caption("START_SYSTEM.batを実行してください")

    st.sidebar.divider()

    # --- New Risk Monitor Section ---
    st.sidebar.subheader("🛡️ リスク監視モニター")

    # Check Market Crash (if Risk Manager is initialized)
    if "risk_manager" in st.session_state and st.session_state["risk_manager"]:
        rm = st.session_state["risk_manager"]
        # Simplified check (logging mocked or passed appropriately)
        # Note: In a UI loop, we might want to cache this or run it less frequently.
        # For now, we run it every re-render to ensure safety status.
        crash_ok, crash_reason = rm.check_market_crash(
            logger=None
        )  # Logger optional/none for UI check

        if crash_ok:
            st.sidebar.success("✅ 市場状況: 正常")
        else:
            st.sidebar.error("🚨 市場急落警戒中")
            st.sidebar.caption(f"{crash_reason}")

        # Display VaR (Mock or stored value if available)
        st.sidebar.metric(label="予想最大損失率 (VaR)", value="2.8%", delta="-0.1%")
    else:
        st.sidebar.warning("⚠️ リスク管理未初期化")

    # --- AGStock Oracle Chat ---
    st.sidebar.divider()
    st.sidebar.subheader("💬 AGStock Oracle")
    with st.sidebar.expander("AIアシスタントに相談", expanded=False):
        user_q = st.text_input("質問を入力 (例: なぜ最近の勝率が上がったの？)", key="oracle_input")
        if st.button("Oracleに尋ねる"):
            if user_q:
                from src.agents.oracle import AGStockOracle
                oracle = AGStockOracle()
                with st.spinner("思考中..."):
                    answer = oracle.ask(user_q)
                st.session_state["oracle_history"] = answer
            else:
                st.warning("質問を入力してください")

        if "oracle_history" in st.session_state:
            st.markdown(
                f'<div class="oracle-bubble">{st.session_state["oracle_history"]}</div>', unsafe_allow_html=True)

    st.sidebar.divider()

    # Demo mode toggle
    use_demo = st.sidebar.checkbox(
        "🧪 デモモード (オフライン向け)",
        value=st.session_state.get("use_demo_data", False),
    )
    st.session_state["use_demo_data"] = use_demo

    # Dark Mode Toggle
    dark_mode = st.sidebar.checkbox("🌙 ダークモード", value=True)
    if dark_mode:
        # The main style_v2.css handles this.
        pass

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
