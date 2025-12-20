import streamlit as st

from src.services import scenario as scenario_service


def render_scenario_sandbox():
    st.header("🧪 シナリオ・サンドボックス (What-if)")
    st.caption("指数下落、為替変動、セクターショックを即時計算し、推奨ヘッジを提示します。")

    use_demo = st.session_state.get("use_demo_data", False)
    options = {v["label"]: k for k, v in scenario_service.SCENARIOS.items()}
    choice = st.selectbox("シナリオを選択", list(options.keys()), index=0)

    if st.button("シミュレート", type="primary"):
        with st.spinner("シナリオを適用中..."):
            res = scenario_service.simulate(use_demo=use_demo, key=options[choice])
            st.session_state["scenario_result"] = res

    res = st.session_state.get("scenario_result")
    if not res:
        st.info("シナリオを選択してシミュレートしてください。")
        return

    if not res.get("has_data"):
        st.warning(res.get("message", "データがありません"))
        return

    st.subheader(res.get("label", ""))
    st.caption(res.get("note", ""))
    delta = res.get("delta", 0)
    delta_pct = res.get("delta_pct", 0)
    st.metric("ポートフォリオ影響", f"{delta:,.0f}", f"{delta_pct*100:.2f}%")

    positions = res.get("positions")
    if positions is not None and not positions.empty:
        st.dataframe(
            positions[["ticker", "quantity", "current_price", "shocked_price", "value", "shocked_value"]],
            use_container_width=True,
        )

    sector_pnl = res.get("sector_pnl")
    if sector_pnl is not None:
        st.bar_chart(sector_pnl)

    st.info(f"推奨ヘッジ: {res.get('hedge')}")
