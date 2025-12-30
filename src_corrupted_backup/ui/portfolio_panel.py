# """
# Portfolio Panel UI Module
# Handles the Portfolio Simulation tab.
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.constants import NIKKEI_225_TICKERS, TICKER_NAMES
from src.data_loader import fetch_stock_data
from src.portfolio import PortfolioManager, CorrelationEngine
# """
# 
# 
def render_portfolio_panel(sidebar_config, strategies):
    pass
#     """
#         Renders the Portfolio Simulation tab content.
#             Args:
    pass
#                 sidebar_config: Config dict from sidebar.
#             strategies: List of initialized strategies available in the system.
#             st.header("ポートフォリオ・シミュレーション")
#         st.write("複数の銘柄を組み合わせた場合のリスクとリターンをシミュレーションします。")
#     # Selection logic based on sidebar
#         ticker_group = sidebar_config.get("ticker_group")
#         custom_tickers = sidebar_config.get("custom_tickers", [])
#         period = sidebar_config.get("period", "2y")
#             if ticker_group == "カスタム入力":
    pass
#                 available_tickers = custom_tickers
#         else:
    pass
#             # Default to Nikkei
#             available_tickers = NIKKEI_225_TICKERS
#             selected_portfolio = st.multiselect(
#             "ポートフォリオに組み入れる銘柄を選択 (3つ以上推奨)",
#             options=available_tickers,
#     default=available_tickers[:5] if len(available_tickers) >= 5 else available_tickers,
#             format_func=lambda x: f"{x} - {TICKER_NAMES.get(x, '')}",
#         )
#             initial_capital = st.number_input("初期投資額 (円)", value=10000000, step=1000000)
#             if st.button("ポートフォリオを分析する"):
    pass
#                 if len(selected_portfolio) < 2:
    pass
#                     st.error("少なくとも2つの銘柄を選択してください。")
#             else:
    pass
#                 with st.spinner("ポートフォリオ分析を実行中..."):
    pass
#                     pm = PortfolioManager(initial_capital=initial_capital)
#                     ce = CorrelationEngine(lookback_period="3mo")  # Phase 82
#                     data_map_pf = fetch_stock_data(selected_portfolio, period=period)
#     # 1. Correlation Matrix & Risk Alerts
#                     st.subheader("相関・リスク分析 (Phase 82)")
#     # Use new engine for correlation
#                     corr_matrix = ce.calculate_correlations(selected_portfolio)
#                         if not corr_matrix.empty:
    pass
#                             # Risk Alerts
#                         positions = [{"ticker": t} for t in selected_portfolio]
#                         alerts = ce.analyze_portfolio_risk(positions)
#                             if alerts:
    pass
#                                 with st.expander("⚠️ ポートフォリオ・リスクアラート", expanded=True):
    pass
#                                     for alert in alerts:
    pass
#                                     if alert["type"] == "HIGH_CORRELATION":
    pass
#                                         st.error(f"**高相関警告**: {alert['message']}")
#                                     elif alert["type"] == "HEDGE_DETECTED":
    pass
#                                         st.success(f"**分散有効**: {alert['message']}")
#                             fig_corr = px.imshow(
#                             corr_matrix,
#                             text_auto=True,
#                             color_continuous_scale="RdBu_r",
#                             zmin=-1,
#                             zmax=1,
#                             title="Correlation Matrix",
#                         )
#                         st.plotly_chart(fig_corr, use_container_width=True)
#                     else:
    pass
#                         st.warning("相関データの取得に失敗しました。")
#     # 2. Portfolio Backtest
#                     st.subheader("ポートフォリオ資産推移")
#     # ... (rest of the logic remains similar but we use pm for simulation)
#     # Strategy Selection
#                     st.subheader("戦略の選択")
#                     pf_strategies = {}
#                     cols = st.columns(3)
#                     strat_names = [s.name for s in strategies]
#     # Note: This logic assumes 'strategies' are populated.
#     # CombinedStrategy is usually a safe default.
#     default_strat_index = 3 if len(strat_names) > 3 else 0
#                         for i, ticker in enumerate(selected_portfolio):
    pass
#                             with cols[i % 3]:
    pass
#                                 selected_strat_name = st.selectbox(
#                                 f"{TICKER_NAMES.get(ticker, ticker)}",
#                                 strat_names,
#                                 index=default_strat_index,
#                                 key=f"strat_{ticker}",
#                             )
#                             pf_strategies[ticker] = next(s for s in strategies if s.name == selected_strat_name)
#                         st.divider()
#     # Weight Optimization
#                     weight_mode = st.radio(
#                         "配分比率 (Weights)", ["均等配分 (Equal)", "最適化 (Max Sharpe)"], horizontal=True
#                     )
#                         weights = {}
#                     if weight_mode == "均等配分 (Equal)":
    pass
#                         weight = 1.0 / len(selected_portfolio)
#                         weights = {t: weight for t in selected_portfolio}
#                     else:
    pass
#                         with st.spinner("シャープレシオ最大化ポートフォリオを計算中..."):
    pass
#                             weights = pm.optimize_portfolio(data_map_pf)
#                             st.success("最適化完了")
#                                 st.write("推奨配分比率:")
#                             w_df = pd.DataFrame.from_dict(weights, orient="index", columns=["Weight"])
#                             w_df["Weight"] = w_df["Weight"].apply(lambda x: f"{x * 100:.1f}%")
#                             st.dataframe(w_df.T)
#                         pf_res = pm.simulate_portfolio(data_map_pf, pf_strategies, weights)
#                         if pf_res:
    pass
#                             col1, col2 = st.columns(2)
#                         col1.metric("トータルリターン", f"{pf_res['total_return'] * 100:.1f}%")
#                         col2.metric("最大ドローダウン", f"{pf_res['max_drawdown'] * 100:.1f}%")
#                             fig_pf = go.Figure()
#                         fig_pf.add_trace(
#                             go.Scatter(
#                                 x=pf_res["equity_curve"].index,
#                                 y=pf_res["equity_curve"],
#                                 mode="lines",
#                                 name="Portfolio",
#                                 line=dict(color="gold", width=2),
#                             )
#                         )
#                         fig_pf.update_layout(
#                             title="ポートフォリオ全体の資産推移", xaxis_title="Date", yaxis_title="Total Equity (JPY)"
#                         )
#                         st.plotly_chart(fig_pf, use_container_width=True)
#                     else:
    pass
#                         st.error("シミュレーションに失敗しました。データが不足している可能性があります。")
#     """
