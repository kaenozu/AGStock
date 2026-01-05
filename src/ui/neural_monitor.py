
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from src.regime_detector import RegimeDetector
from src.data_loader import fetch_stock_data

def render_neural_monitor():
    st.header("🧠 Neural Monitor (AI Brain State)")
    st.caption("AIシステムが市場環境（Market Regime）をどのように認識しているかを可視化します。")
    
    col_sel, col_stat = st.columns([1, 2])
    with col_sel:
        ticker = st.selectbox("監視対象インデックス", ["^N225", "^GSPC", "USDJPY=X", "7203.T", "9984.T"], index=0)
    
    # Analyze
    try:
        data_map = fetch_stock_data([ticker], period="1y")
        df = data_map.get(ticker)
        
        if df is None or df.empty:
            st.error(f"データ取得に失敗しました: {ticker}")
            return
            
        if isinstance(df, tuple):
            df = df[0]
            
        detector = RegimeDetector()
        current_regime = detector.detect_regime(df)
        strategy = detector.get_regime_strategy(current_regime)
        
        # Score calculation for Gauge
        # 0(Bear/Panic) <-> 50(Range) <-> 100(Bull/Stable)
        score = 50
        color = "gray"
        
        if current_regime == "trending_up":
            score = 85
            color = "green"
        elif current_regime == "trending_down":
            score = 15
            color = "red"
        elif current_regime == "high_volatility":
            score = 25
            color = "orange"
        elif current_regime == "low_volatility":
            score = 60
            color = "lightgreen"
        elif current_regime == "ranging":
            score = 50
            color = "gray"
            
        # Layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"### Current State: **{current_regime.upper()}**")
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "AI Sentiment Score (0-100)"},
                gauge = {
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                    'bar': {'color': color},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 30], 'color': 'rgba(255, 0, 0, 0.3)'},
                        {'range': [30, 70], 'color': 'rgba(128, 128, 128, 0.3)'},
                        {'range': [70, 100], 'color': 'rgba(0, 255, 0, 0.3)'}],
                    'threshold': {
                        'line': {'color': "white", 'width': 4},
                        'thickness': 0.75,
                        'value': score}}))
            
            fig.update_layout(height=400, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("💡 AI Strategy")
            st.markdown(f"""
            **Mode**: `{strategy['strategy']}`
            
            **推奨アクション**:
            - Position Size: **{strategy['position_size']}x**
            - Stop Loss: **{strategy['stop_loss']*100}%**
            - Take Profit: **{strategy['take_profit']*100}%**
            """)
            
            st.divider()
            
            st.write("#### Technical Base")
            close = df["Close"].iloc[-1]
            ma50 = df["Close"].rolling(50).mean().iloc[-1]
            ma200 = df["Close"].rolling(200).mean().iloc[-1]
            
            st.metric("Price", f"{close:,.0f}")
            st.metric("MA50", f"{ma50:,.0f}", delta=f"{close-ma50:,.0f}")
            st.metric("MA200", f"{ma200:,.0f}", delta=f"{close-ma200:,.0f}")

    except Exception as e:
        st.error(f"Analysis Error: {e}")
