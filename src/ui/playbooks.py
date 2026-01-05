import streamlit as st

from src.services.playbook_runner import run_close_playbook, run_morning_playbook, run_noon_playbook


def _render_result(result: dict):
    if not result:
        return
    kpis = result.get("kpis", {})
    cols = st.columns(3)
    with cols[0]:
        st.metric("総資産", f"{kpis.get('equity', 0):,.0f}")
    with cols[1]:
        st.metric("現金", f"{kpis.get('cash', 0):,.0f}")
    with cols[2]:
        st.metric("エクスポージャー", f"{kpis.get('exposure', 0):.0%}")
    for item in result.get("checklist", []):
        st.write(f"- {item}")
    if result.get("report_path"):
        st.caption(f"レポート保存先: {result['report_path']}")


def render_playbook_cards():
    st.subheader("🕒 時間帯プレイブック (朝/昼/引け)")
    st.caption("定型のルーチンをワンクリック実行。デモモードでも動作します。")
    use_demo = st.session_state.get("use_demo_data", False)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🌅 朝プレイブック", use_container_width=True, type="primary"):
            with st.spinner("朝の健康診断を実行中..."):
                res = run_morning_playbook(use_demo=use_demo)
                st.session_state["playbook_result_morning"] = res
        _render_result(st.session_state.get("playbook_result_morning"))

    with col2:
        if st.button("🌞 昼プレイブック", use_container_width=True):
            with st.spinner("リバランスチェック中..."):
                res = run_noon_playbook(use_demo=use_demo)
                st.session_state["playbook_result_noon"] = res
        _render_result(st.session_state.get("playbook_result_noon"))

    with col3:
        if st.button("🌙 引けプレイブック", use_container_width=True):
            with st.spinner("日次レポートを生成中..."):
                res = run_close_playbook(use_demo=use_demo)
                st.session_state["playbook_result_close"] = res
        _render_result(st.session_state.get("playbook_result_close"))
