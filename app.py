import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.constants import NIKKEI_225_TICKERS, TICKER_NAMES
from src.data_loader import fetch_stock_data, get_latest_price
from src.strategies import SMACrossoverStrategy, RSIStrategy, BollingerBandsStrategy, CombinedStrategy
from src.backtester import Backtester
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
    CombinedStrategy()
]

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
                    # Check for signals in the last 5 days
                    # Note: 'signals' in res are the raw signals.
                    # The backtester executes on Next Day Open.
                    # So if we have a signal today, we act tomorrow.
                    
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
                        # Format date for display
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
            # Filter for Buy/Sell signals only for the "Actionable" table
            actionable_df = results_df[results_df['Action'] != 'HOLD'].copy()
            actionable_df = actionable_df.sort_values(by="Return", ascending=False)
            
            st.subheader(f"🔥 本日の推奨シグナル ({len(actionable_df)}件)")
            st.info("過去のバックテストで高いリターンを出した戦略が、現在シグナルを出している銘柄です。")
            
            # Format for display
            display_df = actionable_df[['Ticker', 'Name', 'Action', 'Signal Date', 'Strategy', 'Return', 'Max Drawdown', 'Last Price']].copy()
            display_df['Return'] = display_df['Return'].apply(lambda x: f"{x*100:.1f}%")
            display_df['Max Drawdown'] = display_df['Max Drawdown'].apply(lambda x: f"{x*100:.1f}%")
            display_df['Last Price'] = display_df['Last Price'].apply(lambda x: f"¥{x:,.0f}")
            
            st.dataframe(display_df, use_container_width=True)
            
            # Detail View
            st.divider()
            st.subheader("📊 詳細分析")
            
            selected_ticker_row = st.selectbox("銘柄を選択して詳細を表示", 
                                             options=actionable_df['Ticker'].unique(),
                                             format_func=lambda x: f"{x} - {TICKER_NAMES.get(x, '')}")
            
            if selected_ticker_row:
                # Find the best strategy for this ticker from our results
                best_strat_row = actionable_df[actionable_df['Ticker'] == selected_ticker_row].iloc[0]
                strategy_name = best_strat_row['Strategy']
                
                # Re-run to get details
                df = data_map[selected_ticker_row]
                # Find strategy object
                strat = next(s for s in strategies if s.name == strategy_name)
                res = backtester.run(df, strat, stop_loss=0.05, take_profit=0.10)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("期間収益率", f"{res['total_return']*100:.1f}%")
                col2.metric("勝率", f"{res['win_rate']*100:.1f}%")
                col3.metric("最大ドローダウン", f"{res['max_drawdown']*100:.1f}%")

                # Plot Price
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close Price'))
                
                # Add Buy/Sell markers (Entry/Exit points from trades)
                trades = res['trades']
                if trades:
                    # Separate Long and Short trades
                    long_entries = [t for t in trades if t['type'] == 'Long']
                    short_entries = [t for t in trades if t['type'] == 'Short']
                    
                    # Long Entry (Green Up)
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

                    # Short Entry (Purple Down)
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
                
                # Plot Equity Curve
                st.subheader("資産推移 (Equity Curve)")
                fig_eq = go.Figure()
                fig_eq.add_trace(go.Scatter(x=res['equity_curve'].index, y=res['equity_curve'], mode='lines', name='Equity', line=dict(color='gold')))
                fig_eq.update_layout(title="資産の増減シミュレーション", xaxis_title="Date", yaxis_title="Equity (JPY)")
                st.plotly_chart(fig_eq, use_container_width=True)
                
        else:
            st.warning("現在、有効なシグナルが出ている銘柄はありませんでした。")

else:
    st.info("上のボタンを押して分析を開始してください。")
