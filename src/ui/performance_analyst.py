import streamlit as st
import plotly.express as px
from agstock.src.analytics import PortfolioAnalytics


def render_performance_analyst():
    st.subheader("\ud83d\udcc8 ポートフォリオ・パフォーマンス分析")
    st.markdown("資産推移、ドローダウン、およびリターン特性を可視化します。")

    analytics = PortfolioAnalytics()
    df = analytics.get_equity_curve_data()
    summary = analytics.get_performance_summary()

    if df.empty:
        st.warning("分析データがありません。取引を開始してください。")
        return

    # 1. Key Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("\u7dcf\u8cc7\u7523", f"\u00a5{summary['current_equity']:,.0f}")
    with col2:
        st.metric("\u7d2f\u8a08\u53ce\u76ca\u7387", f"{summary['total_return_pct']:.2f}%")
    with col3:
        st.metric(
            "\u6700\u5927\u30c9\u30ed\u30fc\u30c0\u30a6\u30f3",
            f"{summary['max_drawdown_pct']:.2f}%",
            delta_color="inverse",
        )
    with col4:
        st.metric(
            "\u30b7\u30e3\u30fc\u30d7\u30ec\u30b7\u30aa",
            f"{summary['sharpe_ratio']:.2f}",
        )

    # 2. Equity Curve Chart
    fig_equity = px.line(
        df,
        y="total_equity",
        title="\u8cc7\u7523\u63a8\u79fb (Equity Curve)",
        labels={"total_equity": "\u7dcf\u8cc7\u7523 (JPY)", "date": "\u65e5\u4ed8"},
    )
    fig_equity.update_layout(hovermode="x unified")
    st.plotly_chart(fig_equity, use_container_width=True)

    # 3. Drawdown Chart
    fig_dd = px.area(
        df,
        y="drawdown",
        title="\u30c9\u30ed\u30fc\u30c0\u30a6\u30f3 (Drawdown %)",
        labels={"drawdown": "\u4e0b\u843d\u7387 (%)", "date": "\u65e5\u4ed8"},
        color_discrete_sequence=["#ef553b"],
    )
    fig_dd.update_layout(hovermode="x unified")
    st.plotly_chart(fig_dd, use_container_width=True)

    # 4. Monthly Heatmap
    st.markdown("### \ud83d\uddd3\ufe0f \u6708\u6b21\u53ce\u76ca\u30d2\u30fc\u30c8\u30de\u30c3\u30d7 (%)")
    monthly_ret = analytics.get_monthly_returns()
    if not monthly_ret.empty:
        fig_heat = px.imshow(
            monthly_ret,
            labels=dict(x="\u6708", y="\u5e74", color="\u53ce\u76ca\u7387 (%)"),
            x=[f"{m}\u6708" for m in monthly_ret.columns],
            y=monthly_ret.index.astype(str),
            color_continuous_scale="RdYlGn",
            text_auto=".1f",
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("\u6708\u6b21\u53ce\u76ca\u30c7\u30fc\u30bf\u304c\u4e0d\u8db3\u3057\u3066\u3044\u307e\u3059\u3002")
