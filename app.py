import datetime
import plotly.io as pio
import streamlit as st

# Must be the first Streamlit command
st.set_page_config(page_title="AGStock Pro", layout="wide", page_icon="📈", initial_sidebar_state="collapsed")

# Hide Sidebar completely (CSS injection)
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="collapsedControl"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True,
)

from src.cache_config import install_cache
# 新機能インポート
try:
    from src.ui.shortcuts import KeyboardShortcuts
    SHORTCUTS_AVAILABLE = True
except ImportError:
    SHORTCUTS_AVAILABLE = False
from src.constants import MARKETS, NIKKEI_225_TICKERS, TICKER_NAMES
from src.logger_config import setup_logging

@st.cache_resource
def get_strategies():
    # Lazy import to avoid slow startup
    from src.strategies import (BollingerBandsStrategy, CombinedStrategy,
                                DeepLearningStrategy, EnsembleStrategy,
                                LightGBMStrategy, MLStrategy, RSIStrategy,
                                SMACrossoverStrategy, load_custom_strategies)

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
    import logging
    logging.getLogger(__name__).debug(f"Keyboard shortcuts not available: {e}")

# Initialize Global Risk Manager (Lazy Loaded)
@st.cache_resource
def get_risk_manager():
    try:
        from src.advanced_risk import AdvancedRiskManager
        rm = AdvancedRiskManager()
        return rm
    except Exception as e:
        print(f"Risk Manager Init Failed: {e}")
        return None

def initialize_session_state():
    if "risk_manager" not in st.session_state:
        rm = get_risk_manager()
        st.session_state["risk_manager"] = rm
        st.session_state["risk_crash_warning"] = None

def main():
    # Lazy Init
    initialize_session_state()
    strategies = get_strategies() # Load strategies only when main runs

    # Sidebar
    from src.ui.sidebar import render_sidebar
    sidebar_config = render_sidebar()

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
                # Only count actionable signals
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
                # メインタブには戦略を渡す
                if "メイン" in label:
                    render_func(sidebar_config, strategies)
                else:
                    render_func()
            except Exception as e:
                st.error(f"Error rendering tab {label}: {e}")
                import traceback
                st.code(traceback.format_exc())

    # 6. Real-time Monitor (Enhanced)
    with st.sidebar.expander("⚡ リアルタイム監視 (β)", expanded=True):
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
