"""
Risk Management Dashboard Renderer
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.regime_detector import MarketRegimeDetector
from src.portfolio_manager import PortfolioManager
from src.kelly_criterion import KellyCriterion
from src.dynamic_stop import DynamicStopManager
from src.data_loader import fetch_stock_data
from src.paper_trader import PaperTrader

def render_risk_dashboard():
    st.header("🛡️ リスク管理ダッシュボード")
    st.write("市場レジーム、ポートフォリオ相関、最適ポジションサイズ、トレーリングストップを可視化します。")
    
    # Initialize Managers
    regime_detector = MarketRegimeDetector()
    portfolio_manager = PortfolioManager()
    kelly_criterion = KellyCriterion()
    
    # Tabs for different risk aspects
    tab1, tab2, tab3 = st.tabs(["📊 市場レジーム", "⚖️ ポートフォリオ & 資金管理", "🛑 トレーリングストップ"])
    
    # --- Tab 1: Market Regime ---
    with tab1:
        st.subheader("現在の市場レジーム")
        
        # Analyze major indices
        indices = ["^N225", "^GSPC", "7203.T", "9984.T"]
        index_names = {"^N225": "日経平均", "^GSPC": "S&P 500", "7203.T": "トヨタ自動車", "9984.T": "ソフトバンクG"}
        
        with st.spinner("市場データを分析中..."):
            data_map = fetch_stock_data(indices, period="1y")
            
        cols = st.columns(len(indices))
        
        for i, ticker in enumerate(indices):
            df = data_map.get(ticker)
            if df is not None and not df.empty:
                regime = regime_detector.detect_regime(df)
                
                # Visualize Regime
                with cols[i]:
                    st.markdown(f"**{index_names.get(ticker, ticker)}**")
                    
                    # Trend
                    trend_color = "green" if regime['trend'] == 'up' else "red" if regime['trend'] == 'down' else "gray"
                    trend_icon = "↗️" if regime['trend'] == 'up' else "↘️" if regime['trend'] == 'down' else "➡️"
                    st.metric("トレンド", f"{trend_icon} {regime['trend'].upper()}")
                    
                    # Volatility
                    vol_color = "red" if regime['volatility'] == 'high' else "green" if regime['volatility'] == 'low' else "orange"
                    st.metric("ボラティリティ", regime['volatility'].upper(), delta_color="inverse")
                    
                    # Regime Label
                    st.info(f"Regime: {regime['regime']}")
                    
                    # ADX Gauge
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = regime['adx'],
                        title = {'text': "ADX (Trend Strength)"},
                        gauge = {
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 25], 'color': "lightgray"},
                                {'range': [25, 50], 'color': "gray"},
                                {'range': [50, 100], 'color': "darkgray"}],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 25}}))
                    fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
                    st.plotly_chart(fig, use_container_width=True)

    # --- Tab 2: Portfolio & Money Management ---
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚖️ ケリー基準計算機")
            st.write("最適なポジションサイズを計算します。")
            
            win_rate = st.slider("勝率 (%)", 0, 100, 50) / 100.0
            win_loss_ratio = st.number_input("損益レシオ (平均利益 / 平均損失)", value=1.5, step=0.1)
            
            kelly_size = kelly_criterion.calculate_size(win_rate, win_loss_ratio)
            
            st.metric("推奨ポジションサイズ (Kelly)", f"{kelly_size:.1%}")
            st.caption("※ ハーフケリー法を適用し、最大20%に制限しています。")
            
            # Visualizing Kelly Curve
            f_values = [i/100 for i in range(101)]
            g_values = []
            p = win_rate
            b = win_loss_ratio
            q = 1-p
            
            for f in f_values:
                # Growth rate G = p*log(1+b*f) + q*log(1-f)
                if f >= 1:
                    g_values.append(-1) # Ruin
                else:
                    try:
                        g = p * pd.np.log(1 + b * f) + q * pd.np.log(1 - f)
                        g_values.append(g)
                    except:
                        g_values.append(-1)
            
            fig_kelly = px.line(x=f_values, y=g_values, title="ケリー曲線 (期待成長率)")
            fig_kelly.add_vline(x=kelly_size, line_dash="dash", line_color="green", annotation_text="Optimal")
            fig_kelly.update_layout(xaxis_title="レバレッジ/ポジションサイズ", yaxis_title="期待成長率")
            st.plotly_chart(fig_kelly, use_container_width=True)
            
        with col2:
            st.subheader("🔗 ポートフォリオ相関分析")
            
            # Get current positions from PaperTrader
            pt = PaperTrader()
            positions = pt.get_positions()
            
            if not positions.empty:
                tickers = positions['ticker'].tolist()
                if len(tickers) < 2:
                    st.info("相関分析には2銘柄以上のポジションが必要です。")
                else:
                    with st.spinner("相関行列を計算中..."):
                        # Fetch data for correlation
                        corr_data = fetch_stock_data(tickers, period="6mo")
                        price_df = pd.DataFrame({t: df['Close'] for t, df in corr_data.items() if df is not None})
                        
                        if not price_df.empty:
                            corr_matrix = price_df.pct_change().corr()
                            
                            fig_corr = px.imshow(
                                corr_matrix,
                                text_auto=True,
                                aspect="auto",
                                color_continuous_scale="RdBu_r",
                                zmin=-1, zmax=1,
                                title="保有銘柄の相関行列"
                            )
                            st.plotly_chart(fig_corr, use_container_width=True)
                            
                            # Warning for high correlation
                            high_corr_pairs = []
                            for i in range(len(corr_matrix.columns)):
                                for j in range(i+1, len(corr_matrix.columns)):
                                    if abs(corr_matrix.iloc[i, j]) > 0.7:
                                        high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_matrix.iloc[i, j]))
                            
                            if high_corr_pairs:
                                st.warning("⚠️ 以下の銘柄ペアは相関が高すぎます（分散効果が低いです）:")
                                for t1, t2, val in high_corr_pairs:
                                    st.write(f"- {t1} & {t2}: {val:.2f}")
            else:
                st.info("現在ポジションを保有していません。")

    # --- Tab 3: Dynamic Stops ---
    with tab3:
        st.subheader("🛑 動的トレーリングストップ状況")
        
        pt = PaperTrader()
        positions = pt.get_positions()
        
        if not positions.empty:
            dsm = DynamicStopManager()
            
            # Create a table with current price, entry price, and calculated stop
            stop_data = []
            
            with st.spinner("ストップレベルを計算中..."):
                # Fetch latest data for ATR calculation
                tickers = positions['ticker'].tolist()
                data_map = fetch_stock_data(tickers, period="3mo")
                
                for index, row in positions.iterrows():
                    ticker = row['ticker']
                    entry_price = row['entry_price']
                    current_price = row['current_price']
                    
                    df = data_map.get(ticker)
                    
                    # Register and update stop (simulation)
                    dsm.register_entry(ticker, entry_price)
                    # We need to simulate the update history to get the correct trailing stop
                    # Ideally, this state should be persisted, but for visualization we calculate based on recent data
                    # Assuming we held it for the last N days? 
                    # For simplicity in this visualization, we calculate stop based on *current* volatility and high
                    
                    # Re-calculate stop based on current data
                    if df is not None:
                        # Simulate "Highest Price since Entry" - simplified assumption: High of last 10 days or current price
                        # In real app, this should be tracked.
                        # Here we just show what the stop *would be* if updated now.
                        dsm.highest_prices[ticker] = max(entry_price, current_price) # Simplified
                        stop_price = dsm.update_stop(ticker, current_price, df)
                    else:
                        stop_price = entry_price * 0.95
                        
                    distance = (current_price - stop_price) / current_price
                    
                    stop_data.append({
                        "銘柄": ticker,
                        "現在値": current_price,
                        "取得単価": entry_price,
                        "推奨ストップ": stop_price,
                        "ストップまでの距離": distance,
                        "含み益": (current_price - entry_price) / entry_price
                    })
            
            if stop_data:
                stop_df = pd.DataFrame(stop_data)
                
                # Styling
                st.dataframe(stop_df.style.format({
                    "現在値": "¥{:,.0f}",
                    "取得単価": "¥{:,.0f}",
                    "推奨ストップ": "¥{:,.0f}",
                    "ストップまでの距離": "{:.1%}",
                    "含み益": "{:+.1%}"
                }).applymap(lambda x: "color: red" if x < 0.02 else "color: green", subset=["ストップまでの距離"]), 
                use_container_width=True)
                
                st.caption("※ 推奨ストップはATR（ボラティリティ）に基づいて計算されています。距離が近い（赤色）場合は注意が必要です。")
        else:
            st.info("現在ポジションを保有していません。")
