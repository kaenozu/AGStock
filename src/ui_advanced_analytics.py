"""
Advanced Analytics UI Module
Streamlit UI for advanced backtesting, portfolio optimization, and performance attribution.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.advanced_backtest import AdvancedBacktester
from src.portfolio_optimizer import PortfolioOptimizer
from src.performance_attribution import PerformanceAttribution
from src.data_loader import fetch_stock_data
from src.paper_trader import PaperTrader

def render_advanced_analytics_tab():
    st.header("📊 高度分析 & 最適化")
    st.write("高度なバックテスト、ポートフォリオ最適化、パフォーマンス分析を実行します。")
    
    tab1, tab2, tab3 = st.tabs(["🔬 高度バックテスト", "⚖️ ポートフォリオ最適化", "📈 パフォーマンス帰属"])
    
    with tab1:
        render_advanced_backtest()
    
    with tab2:
        render_portfolio_optimization()
    
    with tab3:
        render_performance_attribution()

def render_advanced_backtest():
    st.subheader("🔬 高度バックテストエンジン")
    
    # Parameters
    col1, col2 = st.columns(2)
    with col1:
        ticker = st.text_input("銘柄コード", "7203.T", key="backtest_ticker")
        period = st.selectbox("期間", ["1y", "2y", "3y", "5y"], index=2, key="backtest_period")
    
    with col2:
        train_days = st.number_input("訓練期間（日）", value=252, min_value=60, max_value=1000)
        test_days = st.number_input("テスト期間（日）", value=63, min_value=20, max_value=252)
    
    if st.button("🚀 ウォークフォワード分析を実行", type="primary"):
        with st.spinner("分析中..."):
            try:
                # Fetch data
                data_map = fetch_stock_data([ticker], period=period)
                data = data_map.get(ticker)
                
                if data is None or data.empty:
                    st.error("データ取得に失敗しました")
                    return
                
                # Simple strategy for demonstration
                def simple_strategy(df, mode='test', params=None):
                    if mode == 'train':
                        return {'sma_period': 20}
                    else:
                        sma = df['Close'].rolling(window=params['sma_period']).mean()
                        signals = (df['Close'] > sma).astype(int)
                        return signals
                
                # Run walk-forward analysis
                backtester = AdvancedBacktester()
                results = backtester.walk_forward_analysis(
                    data,
                    simple_strategy,
                    train_period_days=train_days,
                    test_period_days=test_days
                )
                
                # Display results
                st.success("✅ 分析完了")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("平均リターン", f"{results['avg_return']:.2%}")
                col2.metric("平均シャープレシオ", f"{results['avg_sharpe']:.2f}")
                col3.metric("勝率", f"{results['consistency']:.1%}")
                
                # Results table
                st.dataframe(results['results'], use_container_width=True)
                
                # Chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=results['results']['test_start'],
                    y=results['results']['return'],
                    mode='lines+markers',
                    name='テスト期間リターン'
                ))
                fig.update_layout(
                    title="ウォークフォワード分析結果",
                    xaxis_title="テスト開始日",
                    yaxis_title="リターン",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"エラー: {e}")
    
    st.markdown("---")
    st.subheader("🎲 モンテカルロシミュレーション")
    
    if st.button("モンテカルロシミュレーションを実行"):
        with st.spinner("シミュレーション中..."):
            try:
                pt = PaperTrader()
                history = pt.get_trade_history()
                
                if history.empty:
                    st.warning("取引履歴がありません")
                    return
                
                # Calculate returns
                # Simplified: use realized P&L
                if 'realized_pnl' in history.columns:
                    returns = history['realized_pnl'] / 1000000  # Normalize
                    returns = pd.Series(returns.values)
                else:
                    st.warning("P&Lデータがありません")
                    return
                
                backtester = AdvancedBacktester()
                mc_results = backtester.monte_carlo_simulation(returns, n_simulations=1000)
                
                st.success("✅ シミュレーション完了")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("平均最終資産", f"¥{mc_results['mean_final_value']:,.0f}")
                col2.metric("中央値", f"¥{mc_results['median_final_value']:,.0f}")
                col3.metric("利益確率", f"{mc_results['prob_profit']:.1%}")
                
                # Distribution chart
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=mc_results['simulations']['final_value'],
                    nbinsx=50,
                    name='最終資産分布'
                ))
                fig.update_layout(
                    title="モンテカルロシミュレーション結果",
                    xaxis_title="最終資産",
                    yaxis_title="頻度",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"エラー: {e}")

def render_portfolio_optimization():
    st.subheader("⚖️ ポートフォリオ最適化")
    
    # Ticker selection
    default_tickers = ["7203.T", "6758.T", "9984.T", "4063.T"]
    tickers_input = st.text_input(
        "銘柄コード（カンマ区切り）",
        ",".join(default_tickers)
    )
    tickers = [t.strip() for t in tickers_input.split(",")]
    
    method = st.selectbox(
        "最適化手法",
        ["Markowitz (シャープレシオ最大化)", "リスクパリティ", "Black-Litterman"]
    )
    
    if st.button("🎯 最適化を実行", type="primary"):
        with st.spinner("最適化中..."):
            try:
                # Fetch data
                data_map = fetch_stock_data(tickers, period="1y")
                
                # Calculate returns
                returns_dict = {}
                for ticker, data in data_map.items():
                    if data is not None and not data.empty:
                        returns_dict[ticker] = data['Close'].pct_change().dropna()
                
                if not returns_dict:
                    st.error("データ取得に失敗しました")
                    return
                
                returns = pd.DataFrame(returns_dict).dropna()
                
                # Optimize
                optimizer = PortfolioOptimizer()
                
                if "Markowitz" in method:
                    result = optimizer.markowitz_optimization(returns)
                elif "リスクパリティ" in method:
                    result = optimizer.risk_parity(returns)
                else:  # Black-Litterman
                    # Dummy market caps
                    market_caps = pd.Series({t: 1.0 for t in returns.columns})
                    views = {}  # No views for now
                    result = optimizer.black_litterman(returns, market_caps, views)
                
                if not result:
                    st.error("最適化に失敗しました")
                    return
                
                st.success("✅ 最適化完了")
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("期待リターン", f"{result['expected_return']:.2%}")
                col2.metric("ボラティリティ", f"{result['volatility']:.2%}")
                col3.metric("シャープレシオ", f"{result['sharpe_ratio']:.2f}")
                
                # Weights chart
                weights = result['weights']
                fig = go.Figure(data=[go.Pie(
                    labels=weights.index,
                    values=weights.values,
                    hole=0.3
                )])
                fig.update_layout(title="最適ポートフォリオ配分", height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Weights table
                st.dataframe(
                    pd.DataFrame({
                        '銘柄': weights.index,
                        '配分': [f"{w:.1%}" for w in weights.values]
                    }),
                    hide_index=True,
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"エラー: {e}")
                import traceback
                st.error(traceback.format_exc())

def render_performance_attribution():
    st.subheader("📈 パフォーマンス帰属分析")
    
    pt = PaperTrader()
    history = pt.get_trade_history()
    
    if history.empty:
        st.info("取引履歴がありません")
        return
    
    # Calculate portfolio returns
    if 'timestamp' in history.columns and 'realized_pnl' in history.columns:
        history['timestamp'] = pd.to_datetime(history['timestamp'])
        history = history.set_index('timestamp')
        
        # Daily P&L
        daily_pnl = history.groupby(history.index.date)['realized_pnl'].sum()
        portfolio_returns = pd.Series(daily_pnl.values / 1000000, index=pd.to_datetime(daily_pnl.index))
    else:
        st.warning("十分なデータがありません")
        return
    
    # Risk-adjusted metrics
    attribution = PerformanceAttribution()
    metrics = attribution.risk_adjusted_metrics(portfolio_returns)
    
    st.subheader("リスク調整後パフォーマンス")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("累積リターン", f"{metrics.get('total_return', 0):.2%}")
    col2.metric("年率リターン", f"{metrics.get('annualized_return', 0):.2%}")
    col3.metric("ボラティリティ", f"{metrics.get('volatility', 0):.2%}")
    col4.metric("シャープレシオ", f"{metrics.get('sharpe_ratio', 0):.2f}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("ソルティノレシオ", f"{metrics.get('sortino_ratio', 0):.2f}")
    col2.metric("最大ドローダウン", f"{metrics.get('max_drawdown', 0):.2%}")
    col3.metric("カルマーレシオ", f"{metrics.get('calmar_ratio', 0):.2f}")
    
    # Cumulative returns chart
    cum_returns = (1 + portfolio_returns).cumprod()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cum_returns.index,
        y=cum_returns.values,
        mode='lines',
        name='累積リターン',
        fill='tozeroy'
    ))
    fig.update_layout(
        title="累積リターン推移",
        xaxis_title="日付",
        yaxis_title="累積リターン",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
