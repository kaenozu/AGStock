import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.constants import NIKKEI_225_TICKERS, TICKER_NAMES
from src.data_loader import fetch_stock_data, get_latest_price
from src.strategies import SMACrossoverStrategy, RSIStrategy, BollingerBandsStrategy
from src.backtester import Backtester

st.set_page_config(page_title="AI Stock Predictor", layout="wide")

st.title("📈 日本株 AI 予測アナライザー")
st.markdown("過去のデータから統計的に最も期待値の高い売買シグナルを検出します。")

# Sidebar
st.sidebar.header("設定")
ticker_group = st.sidebar.selectbox("対象銘柄", ["日経225 (主要銘柄)"])
period = st.sidebar.selectbox("分析期間", ["1y", "2y", "5y"], index=1)

# Initialize Strategies
strategies = [
    SMACrossoverStrategy(5, 25),
    RSIStrategy(14, 30, 70),
    BollingerBandsStrategy(20, 2)
]

if st.button("市場をスキャンして推奨銘柄を探す", type="primary"):
    with st.spinner("データを取得し、全戦略をバックテスト中..."):
        # 1. Fetch Data
        tickers = NIKKEI_225_TICKERS
        data_map = fetch_stock_data(tickers, period=period)
        
        results = []
        progress_bar = st.progress(0)
        
        # 2. Run Analysis
        backtester = Backtester()
        
        for i, ticker in enumerate(tickers):
            df = data_map.get(ticker)
            if df is None or df.empty:
                continue
                
            for strategy in strategies:
                res = backtester.run(df, strategy)
                if res:
                    # Check for signals in the last 5 days
                    recent_signals = res['signals'].iloc[-5:]
                    last_signal_date = None
                    action = "HOLD"
                    
                    # Find the most recent non-zero signal
                    for date, signal in recent_signals.items():
                        if signal == 1:
                            action = "BUY"
                            last_signal_date = date
                        elif signal == -1:
                            action = "SELL"
                            last_signal_date = date
                            
                    # If no recent signal, check if we are currently in a "holding" position based on the strategy
                    # (This depends on how backtester tracks positions, but for now let's stick to explicit signals)
                    
                    if action != "HOLD":
                        # Format date for display
                        date_str = last_signal_date.strftime('%Y-%m-%d')
                        
                        results.append({
                            "Ticker": ticker,
                            "Name": TICKER_NAMES.get(ticker, ticker),
                            "Strategy": strategy.name,
                            "Return": res['total_return'],
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
            display_df = actionable_df[['Ticker', 'Name', 'Action', 'Signal Date', 'Strategy', 'Return', 'Last Price']].copy()
            display_df['Return'] = display_df['Return'].apply(lambda x: f"{x*100:.1f}%")
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
                ticker_results = actionable_df[actionable_df['Ticker'] == selected_ticker_row]
                if ticker_results.empty:
                    st.warning("選択された銘柄のデータがありません。")
                else:
                    best_strat_row = ticker_results.iloc[0]
                    strategy_name = best_strat_row['Strategy']
                    
                    # Re-run to get details
                    if selected_ticker_row not in data_map:
                        st.error(f"銘柄 {selected_ticker_row} のデータが見つかりません。")
                    else:
                        df = data_map[selected_ticker_row]
                        # Find strategy object
                        strat = next(s for s in strategies if s.name == strategy_name)
                        res = backtester.run(df, strat)
                        
                        if res is None:
                            st.error("バックテストの実行に失敗しました。")
                        else:
                            # Plot
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close Price'))
                            
                            # Add Buy/Sell markers
                            signals = res['signals']
                            buys = df[signals == 1]
                            sells = df[signals == -1]
                            
                            fig.add_trace(go.Scatter(x=buys.index, y=buys['Close'], mode='markers', 
                                                   marker=dict(color='green', size=10, symbol='triangle-up'), name='Buy Signal'))
                            fig.add_trace(go.Scatter(x=sells.index, y=sells['Close'], mode='markers', 
                                                   marker=dict(color='red', size=10, symbol='triangle-down'), name='Sell Signal'))
                            
                            fig.update_layout(title=f"{TICKER_NAMES.get(selected_ticker_row, selected_ticker_row)} - {strategy_name}",
                                            xaxis_title="Date", yaxis_title="Price")
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            st.metric("期間収益率", f"{res['total_return']*100:.1f}%")
                
        else:
            st.warning("現在、有効なシグナルが出ている銘柄はありませんでした。")

else:
    st.info("上のボタンを押して分析を開始してください。")
