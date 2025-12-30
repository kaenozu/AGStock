import streamlit as st
import plotly.express as px
from src.analytics import PortfolioAnalytics


def render_performance_analyst():
    #     """
    #         Render Performance Analyst.
    #             st.subheader("📈 ポートフォリオ・パフォーマンス分析")
    #         st.markdown("資産推移、ドローダウン、およびリターン特性を可視化します。")
    #             analytics = PortfolioAnalytics()
    #         df = analytics.get_equity_curve_data()
    #         summary = analytics.get_performance_summary()
    #             if df.empty:
        pass
    #                 st.warning("分析データがありません。取引を開始してください。")
    #             return
    #     # 1. Key Metrics row
    #         col1, col2, col3, col4 = st.columns(4)
    #         with col1:
        pass
    #             st.metric("総資産", f"¥{summary['current_equity']:,.0f}")
    #         with col2:
        pass
    #             st.metric("累積収益率", f"{summary['total_return_pct']:.2f}%")
    #         with col3:
        pass
    #             st.metric("最大ドローダウン", f"{summary['max_drawdown_pct']:.2f}%", delta_color="inverse")
    #         with col4:
        pass
    #             st.metric("シャープレシオ", f"{summary['sharpe_ratio']:.2f}")
    #     # 2. Equity Curve Chart
    #         fig_equity = px.line(
    #             df, y="total_equity", title="資産推移 (Equity Curve)", labels={"total_equity": "総資産 (JPY)", "date": "日付"}
    #         )
    #         fig_equity.update_layout(hovermode="x unified")
    #         st.plotly_chart(fig_equity, use_container_width=True)
    #     # 3. Drawdown Chart
    #         fig_dd = px.area(
    #             df,
    #             y="drawdown",
    #             title="ドローダウン (Drawdown %)",
    #             labels={"drawdown": "下落率 (%)", "date": "日付"},
    #             color_discrete_sequence=["#ef553b"],
    #         )
    #         fig_dd.update_layout(hovermode="x unified")
    #         st.plotly_chart(fig_dd, use_container_width=True)
    #     # 4. Monthly Heatmap
    #         st.markdown("""" 🗓️ 月次収益ヒートマップ (%)")
    monthly_ret = analytics.get_monthly_returns()
    if not monthly_ret.empty:
        fig_heat = px.imshow(
            monthly_ret,
            labels=dict(x="月", y="年", color="収益率 (%)"),
            x=[f"{m}月" for m in monthly_ret.columns],
            y=monthly_ret.index.astype(str),
            color_continuous_scale="RdYlGn",
            text_auto=".1f",
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("月次収益データが不足しています。")


#     """  # Force Balanced
