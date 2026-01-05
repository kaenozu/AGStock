import datetime
import plotly.io as pio
import streamlit as st

from src.cache_config import install_cache
# 新機能インポート
try:
    from src.ui.shortcuts import KeyboardShortcuts
    SHORTCUTS_AVAILABLE = True
except ImportError:
    SHORTCUTS_AVAILABLE = False
from src.constants import MARKETS, NIKKEI_225_TICKERS, TICKER_NAMES
from src.logger_config import setup_logging
from src.simple_dashboard import create_simple_dashboard
from src.strategies import (BollingerBandsStrategy, CombinedStrategy,
                            DeepLearningStrategy, EnsembleStrategy,
                            LightGBMStrategy, MLStrategy, RSIStrategy,
                            SMACrossoverStrategy, load_custom_strategies)
from src.ui.ai_chat import render_ai_chat
from src.ui.ai_insights import render_ai_insights
from src.ui.dashboard_main import render_market_scan_tab
from src.ui.earnings_analyst import render_earnings_analyst  # Phase 28
from src.ui.news_analyst import render_news_analyst  # New Import
from src.ui.portfolio_panel import render_portfolio_panel
# UI Modules
from src.ui.sidebar import render_sidebar
from src.ui.strategy_arena import render_strategy_arena
from src.ui.trading_panel import render_trading_panel
from src.ui.mission_control import render_mission_control  # Phase 63

# Setup Logging
setup_logging()

# Page Configuration (Must be first)
st.set_page_config(page_title="AGStock AI Trading System", layout="wide")

# Plotly Theme - Pro Dark
import plotly.io as pio
pio.templates.default = "plotly_dark"


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
        EnsembleStrategy(),
    ]
    strategies.extend(load_custom_strategies())
    return strategies


strategies = get_strategies()

# Initialize Strategies (Cached)

st.title("🌍 AGStock AI Trading System (Pro)")
st.markdown("日本・米国・欧州の主要株式を対象とした、プロ仕様のバックテストエンジン搭載。")

# Load CSS (Glassmorphism 2.0 Design System)
try:
    with open("src/ui/index.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    try:
        with open("assets/style_v3.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

# Inject keyboard shortcuts
try:
    from src.ui.shortcuts import KeyboardShortcuts
    KeyboardShortcuts.inject_listener()
except Exception as e:
    pass  # Silently fail if shortcuts not available


# Initialize Global Risk Manager
if "risk_manager" not in st.session_state:
    try:
        from src.advanced_risk import AdvancedRiskManager
        from src.oracle.oracle_2026 import Oracle2026
        
        rm = AdvancedRiskManager()
        oracle = Oracle2026()
        
        # Apply divine guidance on startup
        guidance = oracle.get_risk_guidance()
        rm.apply_oracle_guidance(guidance)
        
        st.session_state["risk_manager"] = rm
        st.session_state["oracle_2026"] = oracle
        # Initialize warning flags
        st.session_state["risk_crash_warning"] = None
    except Exception as e:
        st.error(f"Failed to initialize Risk Manager: {e}")
        st.session_state["risk_manager"] = None


def main():
    # Sidebar
    sidebar_config = render_sidebar()

    # Create Tabs
    # Create Tabs (Simplified)

    # --- Dashboard Router Implementation ---
    from src.ui.dashboard_router import DashboardRouter

    # Check for new signals (notification badge)
    import json
    import os
    signal_count = 0
    try:
        if os.path.exists("scan_results.json"):
            with open("scan_results.json", "r", encoding="utf-8") as f:
                scan_data = json.load(f)
                results = scan_data.get("results", [])
                signal_count = len([r for r in results if r.get("Action") != "HOLD"])
    except Exception:
        signal_count = 0

    # Get Tab Definitions
    tab_defs = DashboardRouter.get_tabs(signal_count)
    tab_labels = [t[0] for t in tab_defs]
    
    # Create Streamlit Tabs
    tabs = st.tabs(tab_labels)
    
    # Render Tabs via Router
    for i, (label, render_func) in enumerate(tab_defs):
        with tabs[i]:
            try:
                # Dependency Injection for specific tabs
                if "トレーディング" in label:
                    render_func(sidebar_config, strategies)
                else:
                    render_func()
            except Exception as e:
                st.error(f"Error rendering tab {label}: {e}")
                st.exception(e)

    # 6. Real-time Monitor (Enhanced)
    with st.sidebar.expander("⚡ リアルタイム監視 (β)", expanded=True):
        @st.fragment(run_every="30s")
        def render_realtime_stream():
            st.markdown("マーケット監視中 (30s自動更新)")
            try:
                from src.realtime.streamer import get_streamer
                watchlist = ["7203.T", "9984.T", "6758.T", "AAPL", "NVDA"]
                streamer = get_streamer(watchlist)
                streamer._fetch_latest()  # Force update
                data = streamer.latest_data
                
                cols = st.columns(2)
                for i, (ticker, info) in enumerate(data.items()):
                    with cols[i % 2]:
                        st.metric(label=ticker, value=f"{info['price']:,.1f}", 
                                  delta=f"{info.get('change', 0):+.2f}%")
                
                st.caption(f"Last Update: {datetime.datetime.now().strftime('%H:%M:%S')}")
            except Exception as e:
                st.error(f"Stream Error: {e}")

        render_realtime_stream()



if __name__ == "__main__":
    main()
