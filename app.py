import plotly.io as pio
import streamlit as st

from src.cache_config import install_cache
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
    except:
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
        st.session_state["risk_manager"] = AdvancedRiskManager()
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

    # Build tab labels with badges
    trading_badge = f" ({signal_count})" if signal_count > 0 else ""

    tab_list = ["🏠 ダッシュボード", "📈 運用パフォーマンス", "🤖 AI分析センター", f"💼 トレーディング{trading_badge}", "🧪 戦略研究所", "🏆 シャドウ・トーナメント", "🚀 Mission Control"]

    tabs = st.tabs(tab_list)

    # 0. Dashboard (Home)
    with tabs[0]:
        create_simple_dashboard()

    # 1. Performance Analytics
    with tabs[1]:
        from src.ui.performance_analyst import render_performance_analyst
        render_performance_analyst()

    # 2. AI Hub
    with tabs[2]:
        from src.ui.ai_hub import render_ai_hub

        render_ai_hub()

    # 3. Trading Hub
    with tabs[3]:
        from src.ui.trading_hub import render_trading_hub
        render_trading_hub(sidebar_config, strategies)

    # 4. Lab Hub
    with tabs[4]:
        from src.ui.lab_hub import render_lab_hub
        render_lab_hub()
    
    # 5. Tournament
    with tabs[5]:
        from src.ui.tournament_ui import render_tournament_ui
        render_tournament_ui()

    # 6. Mission Control
    with tabs[6]:
        render_mission_control()

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
