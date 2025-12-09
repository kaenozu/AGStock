
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

if __name__ == "__main__":
    main()
