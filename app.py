
import streamlit as st
import plotly.io as pio
from src.constants import NIKKEI_225_TICKERS, TICKER_NAMES, MARKETS
from src.cache_config import install_cache
from src.strategies import (
    SMACrossoverStrategy, RSIStrategy, BollingerBandsStrategy, CombinedStrategy, 
    MLStrategy, LightGBMStrategy, DeepLearningStrategy, EnsembleStrategy, 
    load_custom_strategies
)

# UI Modules
from src.ui.sidebar import render_sidebar
from src.ui.dashboard_main import render_market_scan_tab
from src.ui.trading_panel import render_trading_panel
from src.ui.portfolio_panel import render_portfolio_panel

from src.simple_dashboard import create_simple_dashboard
from src.ui.ai_insights import render_ai_insights
from src.logger_config import setup_logging
from src.ui.ai_chat import render_ai_chat
from src.ui.strategy_arena import render_strategy_arena
from src.ui.news_analyst import render_news_analyst # New Import
from src.ui.earnings_analyst import render_earnings_analyst # Phase 28

# Setup Logging
setup_logging()

# Page Configuration (Must be first)
st.set_page_config(page_title="AGStock AI Trading System", layout="wide")

# Install cache
install_cache()

# Initialize Strategies (Cached)
@st.cache_resource
def get_strategies():
    strategies = [
        SMACrossoverStrategy(),
        RSIStrategy(),
        BollingerBandsStrategy(),
        CombinedStrategy(),
        MLStrategy(),
        LightGBMStrategy(),
        DeepLearningStrategy(),
        EnsembleStrategy()
    ]
    strategies.extend(load_custom_strategies())
    return strategies

strategies = get_strategies()

# Initialize Strategies (Cached)

st.title("🌍 AGStock AI Trading System (Pro)")
st.markdown("日本・米国・欧州の主要株式を対象とした、プロ仕様のバックテストエンジン搭載。")

# Load CSS
try:
    with open("assets/style_v2.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    try:
        with open("assets/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass

def main():
    # Sidebar
    sidebar_config = render_sidebar()
    
    # Create Tabs
    # Create Tabs (Simplified)
    
    # Check for new signals (notification badge)
    import os
    import json
    signal_count = 0
    try:
        if os.path.exists("scan_results.json"):
            with open("scan_results.json", "r", encoding="utf-8") as f:
                scan_data = json.load(f)
                results = scan_data.get("results", [])
                signal_count = len([r for r in results if r.get("Action") != "HOLD"])
    except Exception:
        signal_count = 0
    
    # Build tab labels with badges
    trading_badge = f" ({signal_count})" if signal_count > 0 else ""
    
    tab_list = [
        "🏠 ダッシュボード", 
        "🤖 AI分析センター", 
        f"💼 トレーディング{trading_badge}", 
        "🧪 戦略研究所"
    ]
    
    tabs = st.tabs(tab_list)
    
    # 0. Dashboard (Home)
    with tabs[0]:
        create_simple_dashboard()

    # 1. AI Hub
    with tabs[1]:
        from src.ui.ai_hub import render_ai_hub
        render_ai_hub()

    # 2. Trading Hub
    with tabs[2]:
        from src.ui.trading_hub import render_trading_hub
        render_trading_hub(sidebar_config, strategies)

    # 3. Lab Hub (Strategy & Settings)
    with tabs[3]:
        from src.ui.lab_hub import render_lab_hub
        render_lab_hub()

    # 6. Real-time Monitor (New Feature)
    # Ideally should be a separate page or overlay, but adding as expnader or section for now
    with st.sidebar.expander("⚡ リアルタイム監視", expanded=False):
        st.markdown("簡易モニタリング起動中...")
        try:
             import time
             from src.realtime.streamer import get_streamer
             # Stream top 3 tickers just for demo
             watchlist = ["7203.T", "9984.T", "6758.T"]
             streamer = get_streamer(watchlist)
             
             if st.button("更新 (1分足チェック)"):
                 streamer._fetch_latest() # Force update
                 data = streamer.latest_data
                 for ticker, info in data.items():
                     price = info['price']
                     vol = info['volume']
                     st.metric(label=ticker, value=f"{price:,.0f}", delta=None)
                     st.caption(f"Vol: {vol:,.0f} at {info['time'].strftime('%H:%M:%S')}")
             else:
                 st.caption("ボタンを押して最新データを取得")
                 
        except Exception as e:
            st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
