import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.constants import NIKKEI_225_TICKERS, TICKER_NAMES
from src.data_loader import fetch_stock_data, get_latest_price
from src.strategies import SMACrossoverStrategy, RSIStrategy, BollingerBandsStrategy, CombinedStrategy, MLStrategy, LightGBMStrategy
from src.backtester import Backtester
from src.portfolio import PortfolioManager
from src.paper_trader import PaperTrader
from src.cache_config import install_cache

# Install cache
install_cache()

st.set_page_config(page_title="AI Stock Predictor", layout="wide")

st.title("📈 日本株 AI 予測アナライザー (Pro)")
st.markdown("現実的なコストとリスクを考慮した、プロ仕様のバックテストエンジン搭載。")

# Sidebar
st.sidebar.header("設定")
ticker_group = st.sidebar.selectbox("対象銘柄", ["日経225 (主要銘柄)", "カスタム入力"])

custom_tickers = []
if ticker_group == "カスタム入力":
    custom_input = st.sidebar.text_area("銘柄コードを入力 (カンマ区切り)", "7203.T, 9984.T")
    if custom_input:
        custom_tickers = [t.strip() for t in custom_input.split(",")]

period = st.sidebar.selectbox("分析期間", ["1y", "2y", "5y"], index=1)

st.sidebar.divider()
st.sidebar.subheader("リスク管理")
allow_short = st.sidebar.checkbox("空売りを許可する (Short Selling)", value=False)
position_size = st.sidebar.slider("ポジションサイズ (Position Size)", 0.1, 1.0, 1.0, 0.1)

# Initialize Strategies
strategies = [
    SMACrossoverStrategy(5, 25),
    RSIStrategy(14, 30, 70),
    BollingerBandsStrategy(20, 2),
    CombinedStrategy(),
    MLStrategy(),
    LightGBMStrategy()
]

# Main Tabs
tab1, tab2, tab3 = st.tabs(["📊 Market Scan", "💼 Portfolio Simulation", "📝 Paper Trading"])

# --- Tab 1: Market Scan ---
with tab1:
    st.header("市場全体スキャン")
    st.write("指定した銘柄群に対して全戦略をバックテストし、有望なシグナルを検出します。")

    if st.button("市場をスキャンして推奨銘柄を探す", type="primary"):
        with st.spinner("データを取得し、全戦略をバックテスト中..."):
            # 1. Fetch Data
            if ticker_group == "カスタム入力":
                tickers = custom_tickers
            else:
                tickers = NIKKEI_225_TICKERS
                
            if not tickers:
                st.error("銘柄が指定されていません。")
                st.stop()
                
            data_map = fetch_stock_data(tickers, period=period)
            
            results = []
            progress_bar = st.progress(0)
            
            # 2. Run Analysis
            backtester = Backtester(allow_short=allow_short, position_size=position_size)
            
            for i, ticker in enumerate(tickers):
                df = data_map.get(ticker)
                if df is None or df.empty:
                    continue
                    
                for strategy in strategies:
                    # Run with default risk management
                    res = backtester.run(df, strategy, stop_loss=0.05, take_profit=0.10)
                    if res:
                        recent_signals = res['signals'].iloc[-5:]
                        last_signal_date = None
                        action = "HOLD"
                        
                        # Find the most recent non-zero signal
                        for date, signal in recent_signals.items():
                            if signal == 1:
                                action = "BUY"
                                last_signal_date = date
                            elif signal == -1:
                                if allow_short:
                                    action = "SELL (SHORT)"
                                else:
                                    action = "SELL"
                                last_signal_date = date
                                
                        if action != "HOLD":
                            date_str = last_signal_date.strftime('%Y-%m-%d')
                            results.append({
                                "Ticker": ticker,
                                "Name": TICKER_NAMES.get(ticker, ticker),
                                "Strategy": strategy.name,
                                "Return": res['total_return'],
                                "Max Drawdown": res['max_drawdown'],
                                "Action": action,
                                "Signal Date": date_str,
                                "Last Price": get_latest_price(df)
                            })
                
                progress_bar.progress((i + 1) / len(tickers))
                
            # 3. Display Results
            results_df = pd.DataFrame(results)
            
            if not results_df.empty:
                actionable_df = results_df[results_df['Action'] != 'HOLD'].copy()
                actionable_df = actionable_df.sort_values(by="Return", ascending=False)
                
                st.subheader(f"🔥 本日の推奨シグナル ({len(actionable_df)}件)")
                
                display_df = actionable_df[['Ticker', 'Name', 'Action', 'Signal Date', 'Strategy', 'Return', 'Max Drawdown', 'Last Price']].copy()
                display_df['Return'] = display_df['Return'].apply(lambda x: f"{x*100:.1f}%")
                display_df['Max Drawdown'] = display_df['Max Drawdown'].apply(lambda x: f"{x*100:.1f}%")
                display_df['Last Price'] = display_df['Last Price'].apply(lambda x: f"¥{x:,.0f}")
                
                st.dataframe(display_df, use_container_width=True)
                
                # One-Click Order Button
                st.subheader("🚀 アクション")
                if st.button("推奨シグナルをペーパートレードに反映 (Buy 100株)", type="primary"):
                    pt = PaperTrader()
                    success_count = 0
                    for _, row in actionable_df.iterrows():
                        ticker = row['Ticker']
                        action = row['Action']
                        price = row['Last Price']
                        
                        # Only handle BUY for now for simplicity, or handle SELL if holding
                        trade_action = "BUY" if action == "BUY" else "SELL"
                        
                        # Execute
                        if pt.execute_trade(ticker, trade_action, 100, price, reason=f"Auto-Signal: {row['Strategy']}"):
                            success_count += 1
                    
                    if success_count > 0:
                        st.success(f"{success_count}件の注文を約定しました！ 'Paper Trading' タブで確認してください。")
                    else:
                        st.warning("注文は実行されませんでした（資金不足またはシグナルなし）。")
                
                # Detail View
                st.divider()
                st.subheader("📊 詳細分析")
                
                selected_ticker_row = st.selectbox("銘柄を選択して詳細を表示", 
                                                 options=actionable_df['Ticker'].unique(),
                                                 format_func=lambda x: f"{x} - {TICKER_NAMES.get(x, '')}")
                
                if selected_ticker_row:
                    best_strat_row = actionable_df[actionable_df['Ticker'] == selected_ticker_row].iloc[0]
                    strategy_name = best_strat_row['Strategy']
                    
                    df = data_map[selected_ticker_row]
                    strat = next(s for s in strategies if s.name == strategy_name)
                    res = backtester.run(df, strat, stop_loss=0.05, take_profit=0.10)
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("期間収益率", f"{res['total_return']*100:.1f}%")
                    col2.metric("勝率", f"{res['win_rate']*100:.1f}%")
                    col3.metric("最大ドローダウン", f"{res['max_drawdown']*100:.1f}%")

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close Price'))
                    
                    trades = res['trades']
                    if trades:
                        long_entries = [t for t in trades if t['type'] == 'Long']
                        short_entries = [t for t in trades if t['type'] == 'Short']
                        
                        if long_entries:
                            fig.add_trace(go.Scatter(
                                x=[t['entry_date'] for t in long_entries], 
                                y=[t['entry_price'] for t in long_entries], 
                                mode='markers', 
                                marker=dict(color='green', size=10, symbol='triangle-up'), 
                                name='Long Entry'
                            ))
                            fig.add_trace(go.Scatter(
                                x=[t['exit_date'] for t in long_entries], 
                                y=[t['exit_price'] for t in long_entries], 
                                mode='markers', 
                                marker=dict(color='red', size=10, symbol='triangle-down'), 
                                name='Long Exit'
                            ))

                        if short_entries:
                            fig.add_trace(go.Scatter(
                                x=[t['entry_date'] for t in short_entries], 
                                y=[t['entry_price'] for t in short_entries], 
                                mode='markers', 
                                marker=dict(color='purple', size=10, symbol='triangle-down'), 
                                name='Short Entry'
                            ))
                            fig.add_trace(go.Scatter(
                                x=[t['exit_date'] for t in short_entries], 
                                y=[t['exit_price'] for t in short_entries], 
                                mode='markers', 
                                marker=dict(color='blue', size=10, symbol='triangle-up'), 
                                name='Short Exit'
                            ))
                    
                    fig.update_layout(title=f"{TICKER_NAMES.get(selected_ticker_row, selected_ticker_row)} - {strategy_name}",
                                    xaxis_title="Date", yaxis_title="Price")
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.subheader("資産推移 (Equity Curve)")
                    fig_eq = go.Figure()
                    fig_eq.add_trace(go.Scatter(x=res['equity_curve'].index, y=res['equity_curve'], mode='lines', name='Equity', line=dict(color='gold')))
                    fig_eq.update_layout(title="資産の増減シミュレーション", xaxis_title="Date", yaxis_title="Equity (JPY)")
                    st.plotly_chart(fig_eq, use_container_width=True)
                    
            else:
                st.warning("現在、有効なシグナルが出ている銘柄はありませんでした。")

# --- Tab 2: Portfolio Simulation ---
with tab2:
    st.header("ポートフォリオ・シミュレーション")
    st.write("複数の銘柄を組み合わせた場合のリスクとリターンをシミュレーションします。")
    
    # Selection
    if ticker_group == "カスタム入力":
        available_tickers = custom_tickers
    else:
        available_tickers = NIKKEI_225_TICKERS
        
    selected_portfolio = st.multiselect("ポートフォリオに組み入れる銘柄を選択 (3つ以上推奨)", 
                                      options=available_tickers,
                                      default=available_tickers[:5] if len(available_tickers) >=5 else available_tickers,
                                      format_func=lambda x: f"{x} - {TICKER_NAMES.get(x, '')}")
    
    initial_capital = st.number_input("初期投資額 (円)", value=10000000, step=1000000)
    
    if st.button("ポートフォリオを分析する"):
        if len(selected_portfolio) < 2:
            st.error("少なくとも2つの銘柄を選択してください。")
        else:
            with st.spinner("ポートフォリオ分析を実行中..."):
                pm = PortfolioManager(initial_capital=initial_capital)
                data_map_pf = fetch_stock_data(selected_portfolio, period=period)
                
                # 1. Correlation Matrix
                st.subheader("相関行列 (Correlation Matrix)")
                st.write("銘柄間の値動きの連動性を示します。1に近いほど同じ動き、-1に近いほど逆の動きをします。分散投資には相関が低い（色が薄い）組み合わせが有効です。")
                corr_matrix = pm.calculate_correlation(data_map_pf)
                
                if not corr_matrix.empty:
                    fig_corr = px.imshow(corr_matrix, 
                                       text_auto=True, 
                                       color_continuous_scale='RdBu_r', 
                                       zmin=-1, zmax=1,
                                       title="Correlation Matrix")
                    st.plotly_chart(fig_corr, use_container_width=True)
                
                # 2. Portfolio Backtest
                st.subheader("ポートフォリオ資産推移")
                
                # Assign strategies
                st.subheader("戦略の選択")
                pf_strategies = {}
                
                # Create a container for strategy selectors
                cols = st.columns(3)
                for i, ticker in enumerate(selected_portfolio):
                    with cols[i % 3]:
                        # Default to CombinedStrategy (index 3 in our list)
                        strat_names = [s.name for s in strategies]
                        selected_strat_name = st.selectbox(
                            f"{TICKER_NAMES.get(ticker, ticker)}", 
                            strat_names, 
                            index=3,
                            key=f"strat_{ticker}"
                        )
                        # Find the strategy instance
                        pf_strategies[ticker] = next(s for s in strategies if s.name == selected_strat_name)
                
                st.divider()
                
                # Weight Optimization
                weight_mode = st.radio("配分比率 (Weights)", ["均等配分 (Equal)", "最適化 (Max Sharpe)"], horizontal=True)
                
                weights = {}
                if weight_mode == "均等配分 (Equal)":
                    weight = 1.0 / len(selected_portfolio)
                    weights = {t: weight for t in selected_portfolio}
                else:
                    with st.spinner("シャープレシオ最大化ポートフォリオを計算中..."):
                        weights = pm.optimize_portfolio(data_map_pf)
                        st.success("最適化完了")
                        
                        # Display Weights
                        st.write("推奨配分比率:")
                        w_df = pd.DataFrame.from_dict(weights, orient='index', columns=['Weight'])
                        w_df['Weight'] = w_df['Weight'].apply(lambda x: f"{x*100:.1f}%")
                        st.dataframe(w_df.T)

                pf_res = pm.simulate_portfolio(data_map_pf, pf_strategies, weights)
                
                if pf_res:
                    col1, col2 = st.columns(2)
                    col1.metric("トータルリターン", f"{pf_res['total_return']*100:.1f}%")
                    col2.metric("最大ドローダウン", f"{pf_res['max_drawdown']*100:.1f}%")
                    
                    fig_pf = go.Figure()
                    fig_pf.add_trace(go.Scatter(x=pf_res['equity_curve'].index, y=pf_res['equity_curve'], mode='lines', name='Portfolio', line=dict(color='gold', width=2)))
                    
                    # Add individual components (optional, maybe too messy)
                    # for t, res in pf_res['individual_results'].items():
                    #     fig_pf.add_trace(go.Scatter(x=res['equity_curve'].index, y=res['equity_curve'] * (initial_capital * weights[t]), mode='lines', name=t, opacity=0.3))
                        
                    fig_pf.update_layout(title="ポートフォリオ全体の資産推移", xaxis_title="Date", yaxis_title="Total Equity (JPY)")
                    st.plotly_chart(fig_pf, use_container_width=True)
                else:
                    st.error("シミュレーションに失敗しました。データが不足している可能性があります。")

# --- Tab 3: Paper Trading ---
with tab3:
    st.header("ペーパートレーディング (仮想売買)")
    st.write("リアルタイムの株価データを用いて、仮想資金でトレードの練習ができます。")
    
    pt = PaperTrader()
    
    # Refresh Button
    if st.button("最新価格で評価額を更新"):
        with st.spinner("現在値を更新中..."):
            pt.update_daily_equity()
            st.success("更新完了")
    
    # Dashboard
    balance = pt.get_current_balance()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("現金残高 (Cash)", f"¥{balance['cash']:,.0f}")
    col2.metric("総資産 (Total Equity)", f"¥{balance['total_equity']:,.0f}")
    
    pnl = balance['total_equity'] - pt.initial_capital
    pnl_color = "normal"
    if pnl > 0: pnl_color = "normal" # Streamlit handles color in delta
    col3.metric("全期間損益", f"¥{pnl:,.0f}", delta=f"{pnl/pt.initial_capital*100:.1f}%")
    
    st.divider()
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("現在の保有ポジション")
        positions = pt.get_positions()
        if not positions.empty:
            # Format for display
            pos_display = positions.copy()
            pos_display['unrealized_pnl_pct'] = (pos_display['current_price'] - pos_display['entry_price']) / pos_display['entry_price']
            
            # Apply styling
            st.dataframe(pos_display.style.format({
                'entry_price': '¥{:,.0f}',
                'current_price': '¥{:,.0f}',
                'unrealized_pnl': '¥{:,.0f}',
                'unrealized_pnl_pct': '{:.1%}'
            }), use_container_width=True)
        else:
            st.info("現在保有しているポジションはありません。")
            
    with col_right:
        st.subheader("手動注文")
        with st.form("order_form"):
            ticker_input = st.text_input("銘柄コード (例: 7203.T)")
            action_input = st.selectbox("売買", ["BUY", "SELL"])
            qty_input = st.number_input("数量", min_value=100, step=100, value=100)
            
            submitted = st.form_submit_button("注文実行")
            if submitted and ticker_input:
                # Get current price
                price_data = fetch_stock_data([ticker_input], period="1d")
                if ticker_input in price_data and not price_data[ticker_input].empty:
                    current_price = price_data[ticker_input]['Close'].iloc[-1]
                    
                    if pt.execute_trade(ticker_input, action_input, qty_input, current_price, reason="Manual"):
                        st.success(f"{action_input}注文が完了しました: {ticker_input} @ {current_price}")
                        st.rerun()
                    else:
                        st.error("注文に失敗しました（資金不足または保有株不足）。")
                else:
                    st.error("価格データの取得に失敗しました。")

    st.divider()
    st.subheader("取引履歴")
    history = pt.get_trade_history()
    if not history.empty:
        st.dataframe(history, use_container_width=True)
    else:
        st.info("取引履歴はありません。")
