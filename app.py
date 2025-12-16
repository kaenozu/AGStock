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
        EnsembleStrategy(),
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

    tab_list = ["🏠 ダッシュボード", "🤖 AI分析センター", f"💼 トレーディング{trading_badge}", "🧪 戦略研究所"]

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
                streamer._fetch_latest()  # Force update
                data = streamer.latest_data
                for ticker, info in data.items():
                    price = info["price"]
                    vol = info["volume"]
                    st.metric(label=ticker, value=f"{price:,.0f}", delta=None)
                    st.caption(f"Vol: {vol:,.0f} at {info['time'].strftime('%H:%M:%S')}")
            else:
                st.caption("ボタンを押して最新データを取得")

            # Health status
            if getattr(streamer, "last_update", None):
                st.caption(
                    f"最終更新: {streamer.last_update.strftime('%H:%M:%S')} / 失敗回数: {streamer.failure_count}"
                )
            if getattr(streamer, "last_error", None):
                st.warning(f"前回エラー: {streamer.last_error}")

        except Exception as e:
            st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
