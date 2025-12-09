
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
from src.ui.portfolio_panel import render_portfolio_panel
from src.simple_dashboard import create_simple_dashboard
from src.ui.ai_insights import render_ai_insights
from src.logger_config import setup_logging
from src.ui.ai_chat import render_ai_chat # Added this import for the new main function

# Setup Logging
setup_logging()

# Install cache
install_cache()

# Initialize Strategies
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

# Page Configuration
st.set_page_config(page_title="AGStock AI Tradng System", layout="wide")

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
    # Note: Backtest and Performance Analysis were in previous versions. 
    # I will include them to match imports.
    tab_list = [
        "🏠 ホーム", 
        "📊 市場スキャン", 
        "🤖 AI投資委員会", 
        "💬 AIチャット",
        "📈 ポートフォリオ", 
        "📝 ペーパートレード"
    ]
    
    tabs = st.tabs(tab_list)
    
    # 0. Home
    with tabs[0]:
        create_simple_dashboard()

    # 1. Market Scan
    with tabs[1]:
        render_market_scan_tab(sidebar_config)

    # 2. AI Insights
    with tabs[2]:
        render_ai_insights()

    # 3. AI Chat
    with tabs[3]:
        render_ai_chat()

    # 4. Portfolio
    with tabs[4]:
        render_portfolio_panel(sidebar_config, strategies)

    # 5. Paper Trading
    with tabs[5]:
        render_trading_panel(sidebar_config)

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

