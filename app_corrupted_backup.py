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

# Load CSS (v3 with modern design system)
try:
    with open("assets/style_v3.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    try:
        with open("assets/style_v2.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        try:
            with open("assets/style.css") as f:
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
        st.session_state["risk_manager"] = AdvancedRiskManager()
        # Initialize warning flags
        st.session_state["risk_crash_warning"] = None
    except Exception as e:
        st.error(f"Failed to initialize Risk Manager: {e}")
        st.session_state["risk_manager"] = None


def main():
    # Sidebar
    sidebar_config = render_sidebar()

    # Create Main Tabs (The 4 Pillars)
    main_tabs = st.tabs([
        "🏠 Command Center", 
        "🧠 AI Omniscience", 
        "⚔️ Operations", 
        "🧪 Genesis Lab"
    ])

    # --- TAB 1: COMMAND CENTER (司令室) ---
    with main_tabs[0]:
        st.header("🏠 Command Center")
        # Sub-tabs
        cc_tabs = st.tabs(["📊 Dashboard", "🚀 Mission Control", "📈 Performance", "🔮 Oracle Chamber", "👑 Oracle Dynasty", "📚 Eternal Archive"])
        
        with cc_tabs[0]: # Dashboard
            from src.ui.briefing_panel import render_briefing_panel
            render_briefing_panel()
            create_simple_dashboard()
            
        with cc_tabs[1]: # Mission Control
            from src.ui.mission_control import render_mission_control
            render_mission_control()
            
        with cc_tabs[2]: # Performance
            from src.ui.performance_analyst import render_performance_analyst
            render_performance_analyst()

        with cc_tabs[3]: # Oracle Chamber
            from src.ui.oracle_chamber import render_oracle_chamber
            render_oracle_chamber()

        with cc_tabs[4]: # Oracle Dynasty
            from src.ui.dynasty_hub import render_dynasty_hub
            render_dynasty_hub()

        with cc_tabs[5]: # Eternal Archive
            from src.ui.archive_explorer import render_archive_explorer
            render_archive_explorer()

    # --- TAB 2: AI OMNISCIENCE (全知) ---
    with main_tabs[1]:
        st.header("🧠 AI Omniscience")
        # Sub-tabs
        ai_tabs = st.tabs(["🏛️ Council Hall", "👁️ Divine Sight", "🤖 Analysis Center", "📚 Akashic Records", "🌆 Holographic Universe"])
        
        with ai_tabs[0]: # Council Hall
            from src.ui.council_hall import render_council_hall
            if "investment_committee" not in st.session_state:
                from src.agents.committee import InvestmentCommittee
                from src.schemas import AppConfig, RiskConfig
                conf = AppConfig(risk=RiskConfig(max_position_size=0.1, stop_loss_pct=0.05))
                st.session_state["investment_committee"] = InvestmentCommittee(conf)
            
            committee = st.session_state["investment_committee"]
            ticker = sidebar_config.get("custom_tickers", ["7203.T"])[0] if sidebar_config.get("custom_tickers") else "7203.T"
            
            if hasattr(committee, "council"):
                render_council_hall(committee.council, ticker, {})
            else:
                st.warning("Council of Avatars module not initialized in Committee.")
                
        with ai_tabs[1]: # Divine Sight
            from src.ui.divine_sight import render as render_divine_sight
            render_divine_sight()
            
        with ai_tabs[2]: # AI Hub (Analysis)
            from src.ui.ai_hub import render_ai_hub
            render_ai_hub()

        with ai_tabs[3]: # Akashic Records (DB)
            from src.ui.akashic_records import render_akashic_records
            render_akashic_records()
            
        with ai_tabs[4]: # Hologram
            from src.ui.hologram import render_hologram_deck
            render_hologram_deck()

    # --- TAB 3: OPERATIONS (実戦) ---
    with main_tabs[2]:
        st.header("⚔️ Operations")
        # Check for new signals for badge
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
        trading_badge = f" ({signal_count})" if signal_count > 0 else ""

        op_tabs = st.tabs([f"💼 Trading{trading_badge}", "💰 Portfolio"])
        
        with op_tabs[0]: # Trading Hub
            from src.ui.trading_hub import render_trading_hub
            render_trading_hub(sidebar_config, strategies)
            
        with op_tabs[1]: # Portfolio (Reusing simple dashboard portfolio view or creating dedicated)
            # For now, let's just use the Portfolio Panel if available, or placeholder
            from src.ui.portfolio_panel import render_portfolio_panel
            render_portfolio_panel()

    # --- TAB 4: GENESIS LAB (創世記) ---
    with main_tabs[3]:
        st.header("🧪 Genesis Lab")
        lab_tabs = st.tabs(["🥋 Training Dojo", "🏗️ Strategy Lab", "🧬 Model Lab", "🌌 Parallel Worlds", "🧬 The Singularity"])
        
        with lab_tabs[0]: # Dojo
            from src.ui.dojo import render as render_dojo
            render_dojo()
            
        with lab_tabs[1]: # Strategy Lab
            from src.ui.strategy_arena import render_strategy_arena
            render_strategy_arena(strategies)
            
        with lab_tabs[2]: # Model Lab (Lab Hub)
            from src.ui.lab_hub import render_lab_hub
            render_lab_hub()

        with lab_tabs[3]: # Parallel Worlds
            from src.ui.parallel_worlds import render_parallel_worlds
            render_parallel_worlds()

        with lab_tabs[4]: # Singularity Core
            from src.ui.singularity import render_singularity_core
            render_singularity_core()

    # 6. Real-time Monitor (Sidebar)
    with st.sidebar.expander("⚡ リアルタイム監視", expanded=False):
        st.markdown("簡易モニタリング起動中...")
        try:
            import time
            from src.realtime.streamer import get_streamer
            watchlist = ["7203.T", "9984.T", "6758.T"]
            streamer = get_streamer(watchlist)

            if st.button("更新 (1分足チェック)"):
                streamer._fetch_latest()
                data = streamer.latest_data
                for ticker, info in data.items():
                    price = info["price"]
                    vol = info["volume"]
                    st.metric(label=ticker, value=f"{price:,.0f}", delta=None)
                    st.caption(f"Vol: {vol:,.0f} at {info['time'].strftime('%H:%M:%S')}")
            else:
                st.caption("ボタンを押して最新データを取得")
        except Exception as e:
            st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
