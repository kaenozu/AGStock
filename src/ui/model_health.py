import streamlit as st

from src.services.model_health import compute_health, write_retrain_flag


def render_model_health():
    st.header("🩺 モデル健全性メーター")
    st.caption("ヒット率・ドリフト・DDを簡易モニタリング。閾値超えなら軽量再学習を促します。")

    use_demo = st.session_state.get("use_demo_data", False)
    if st.button("健全性をチェック", type="primary"):
        with st.spinner("メトリクス算出中..."):
            res = compute_health(use_demo=use_demo)
            st.session_state["model_health_res"] = res

    res = st.session_state.get("model_health_res")
    if not res:
        st.info("チェックを実行してください。")
        return

    status = res.get("status", "unknown")
    color = {"healthy": "green", "degraded": "orange", "alert": "red"}.get(status, "gray")
    st.markdown(f"**状態**: :{color}[{status.upper()}] — {res.get('reason','')}")

    cols = st.columns(4)
    with cols[0]:
        st.metric("短期ヒット率", f"{res.get('short_win',0):.0%}")
    with cols[1]:
        st.metric("長期ヒット率", f"{res.get('long_win',0):.0%}")
    with cols[2]:
        st.metric("ドリフト", f"{res.get('drift',0)*100:.2f}%")
    with cols[3]:
        st.metric("最大DD", f"{res.get('max_dd',0):.1%}")

    if status in {"degraded", "alert"}:
        if st.button("軽量再学習を提案する", type="secondary"):
            reason = f"{status} — {res.get('reason','')}"
            path = write_retrain_flag(reason)
            st.success(f"再学習フラグを書き込みました: {path}")
