"""
個人投資家向けシンプルダッシュボード

一目でわかる資産状況とリスク管理画面
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List

from src.paper_trader import PaperTrader
from src.formatters import format_currency_jp

# AI戦略のインポート
from src.strategies import LightGBMStrategy
from src.data_loader import fetch_stock_data, fetch_external_data

@st.cache_data(ttl=3600, show_spinner=False)
def get_ai_predictions(tickers: List[str]) -> Dict[str, Dict]:
    """
    AI予測を実行し、結果をキャッシュする
    
    Args:
        tickers: 銘柄リスト
        
    Returns:
        {ticker: {'signal': int, 'latest_price': float, 'change': float}}
    """
    results = {}
    
    try:
        # データ取得（キャッシュ利用）
        data_map = fetch_stock_data(tickers, period="1y")
        
        # マクロデータ取得
        try:
            external_data = fetch_external_data(period="1y")
        except:
            external_data = {}

        for ticker in tickers:
            df = data_map.get(ticker)
            if df is not None and not df.empty:
                # 最新価格
                latest_price = df['Close'].iloc[-1]
                change = (latest_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2]
                
                # AI予測 (LightGBM + マクロ)
                strategy = LightGBMStrategy(lookback_days=100)
                
                # マクロデータ結合（簡易版）
                if 'US10Y' in external_data:
                    us10y = external_data['US10Y']['Close'].rename('US10Y')
                    df = df.join(us10y, how='left').fillna(method='ffill').fillna(0)
                    if 'US10Y' in df.columns:
                        df['US10Y_Ret'] = df['US10Y'].pct_change().fillna(0)
                        df['US10Y_Corr'] = df['Close'].rolling(20).corr(df['US10Y']).fillna(0)

                try:
                    signals = strategy.generate_signals(df)
                    if not signals.empty:
                        signal = int(signals.iloc[-1])
                    else:
                        signal = 0
                except:
                    signal = 0
                
                results[ticker] = {
                    'signal': signal,
                    'latest_price': latest_price,
                    'change': change
                }
    except Exception as e:
        st.error(f"AI予測エラー: {e}")
        
    return results

def create_simple_dashboard():
    """シンプルダッシュボードを表示"""
    
    # カスタムCSS
    st.markdown("""
    <style>
    /* カードデザイン */
    .stCard {
        background-color: #1E2130;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    
    /* AI推奨バッジ */
    .ai-badge {
        background: linear-gradient(45deg, #00D9FF, #0088FF);
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.8em;
    }
    
    /* メトリクス */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #FAFAFA !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🚀 AI投資ダッシュボード")
    
    # 1. AI市場予測（最優先表示）
    render_ai_insights()
    
    st.divider()
    
    # 2. 資産サマリー
    render_asset_summary()
    
    st.divider()
    
    # 3. リスク状況
    render_risk_status()

def render_ai_insights():
    """AIによる市場予測と推奨"""
    st.subheader("🤖 AI市場予測 (Phase 17 Model)")
    
    col1, col2 = st.columns(2)
    
    # ターゲット銘柄
    tickers = ["^N225", "^GSPC"] # 日経平均, S&P500
    
    with st.spinner("AIが市場を分析中..."):
        # キャッシュされた予測結果を取得
        predictions = get_ai_predictions(tickers)
        
        for i, ticker in enumerate(tickers):
            with col1 if i == 0 else col2:
                data = predictions.get(ticker)
                
                if data:
                    signal = data['signal']
                    latest_price = data['latest_price']
                    change = data['change']
                    
                    # 表示
                    name = "日経平均" if ticker == "^N225" else "S&P 500"
                    
                    if signal == 1:
                        sentiment = "強気 (買い)"
                        color = "green"
                        icon = "🐂"
                        bg_color = "rgba(0, 255, 0, 0.1)"
                    elif signal == -1:
                        sentiment = "弱気 (売り)"
                        color = "red"
                        icon = "🐻"
                        bg_color = "rgba(255, 0, 0, 0.1)"
                    else:
                        sentiment = "中立 (様子見)"
                        color = "gray"
                        icon = "⚖️"
                        bg_color = "rgba(128, 128, 128, 0.1)"
                        
                    st.markdown(f"""
                    <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; border: 1px solid {color};">
                        <h3 style="margin:0; color: {color};">{icon} {name}</h3>
                        <p style="font-size: 1.5em; font-weight: bold; margin: 5px 0;">{sentiment}</p>
                        <p style="margin:0;">現在値: ¥{latest_price:,.0f} <span style="color: {'green' if change>0 else 'red'};">({change:+.2%})</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning(f"{ticker} のデータ取得に失敗しました")

def render_asset_summary():
    """資産状況のシンプル表示"""
    pt = PaperTrader()
    balance = pt.get_current_balance()
    equity_history = pt.get_equity_history()
    
    st.subheader("💰 資産状況")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        total_equity = balance['total_equity']
        initial = pt.initial_capital
        pnl = total_equity - initial
        pnl_pct = pnl / initial
        
        st.metric(
            "総資産",
            format_currency_jp(total_equity),
            f"{pnl_pct:+.2%} (¥{pnl:+,.0f})"
        )
        
        st.caption(f"現金余力: {format_currency_jp(balance['cash'])}")
        
    with col2:
        if not equity_history.empty:
            equity_history['date'] = pd.to_datetime(equity_history['date'])
            recent = equity_history.tail(30)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=recent['date'],
                y=recent['total_equity'],
                mode='lines',
                fill='tozeroy',
                line=dict(color='#00D9FF', width=2),
                fillcolor='rgba(0, 217, 255, 0.1)'
            ))
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=150,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False, showticklabels=False)
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def render_risk_status():
    """リスク状況のシンプル表示"""
    pt = PaperTrader()
    positions = pt.get_positions()
    balance = pt.get_current_balance()
    
    if positions.empty:
        st.info("現在保有しているポジションはありません。")
        return

    st.subheader("🛡️ 保有銘柄とリスク")
    
    # 簡易リスト表示
    for _, pos in positions.iterrows():
        pnl_pct = pos['unrealized_pnl_pct']
        color = "green" if pnl_pct > 0 else "red"
        
        st.markdown(f"""
        <div style="display: flex; justify_content: space-between; align-items: center; padding: 10px; background-color: #262730; border-radius: 5px; margin-bottom: 5px;">
            <div>
                <span style="font-weight: bold;">{pos['ticker']}</span>
                <span style="font-size: 0.8em; color: gray;">{pos['quantity']}株</span>
            </div>
            <div style="text-align: right;">
                <div style="font-weight: bold;">¥{pos['current_price']:,.0f}</div>
                <div style="color: {color}; font-size: 0.9em;">{pnl_pct:+.2%}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    create_simple_dashboard()
