import streamlit as st

from src.services.trade_journal import generate_journal


def render_trade_journal():
    st.header("📔 AIトレード日誌 & 次の一手")
    st.caption("取引履歴とエクイティから自動で日誌を生成し、次のアクションを提案します。")

    use_demo = st.session_state.get("use_demo_data", False)
    if st.button("日誌を生成", type="primary"):
        with st.spinner("日誌をまとめています..."):
            res = generate_journal(use_demo=use_demo)
            st.session_state["journal_result"] = res

    res = st.session_state.get("journal_result")
    if not res:
        st.info("右上のボタンで最新の日誌を生成してください。")
        return

    metrics = res.get("metrics", {})
    cols = st.columns(4)
    with cols[0]:
        st.metric("勝率", f"{metrics.get('win_rate', 0):.0%}")
    with cols[1]:
        st.metric("PF", f"{metrics.get('profit_factor', 0):.2f}")
    with cols[2]:
        st.metric("最大DD", f"{metrics.get('max_dd', 0):.1%}")
    with cols[3]:
        st.metric("平均勝ち/負け", f"{metrics.get('avg_win', 0):,.0f} / {metrics.get('avg_loss', 0):,.0f}")

    st.subheader("次の一手 (提案)")
    for item in res.get("next_actions", []):
        st.write(f"- {item}")

    if res.get("report_path"):
        st.caption(f"Markdown保存先: {res['report_path']}")
