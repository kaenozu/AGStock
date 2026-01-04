import datetime
import streamlit as st
import plotly.io as pio
from typing import Dict, Any

from src.cache_config import install_cache
from src.constants import MARKETS, NIKKEI_225_TICKERS, TICKER_NAMES
from src.logger_config import setup_logging
from src.simple_dashboard import create_simple_dashboard
from src.strategies import (
    BollingerBandsStrategy,
    CombinedStrategy,
    DeepLearningStrategy,
    EnsembleStrategy,
    LightGBMStrategy,
    MLStrategy,
    RSIStrategy,
    SMACrossoverStrategy,
    load_custom_strategies,
)
from src.ui.enhanced_components import (
    loading_spinner,
    metric_card,
    status_badge,
    collapsible_section,
    skeleton_loader,
)
from src.ui.responsive_navigation import render_responsive_nav
from src.ui.quick_overview import render_quick_overview
from src.ui.sidebar import render_sidebar
from src.ui.ai_hub import render_ai_hub
from src.ui.trading_hub import render_trading_hub
from src.ui.performance_analyst import render_performance_analyst
from src.ui.strategy_arena import render_strategy_arena
from src.ui.tournament_ui import render_tournament_ui
from src.ui.mission_control import render_mission_control
from src.ui.divine_reflection import render_divine_reflection

# Setup
setup_logging()
st.set_page_config(
    page_title="AGStock AI Trading System",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Plotly Theme - Pro Dark
pio.templates.default = "plotly_dark"

# Install cache
install_cache()


# Enhanced CSS with mobile support
def load_enhanced_css():
    """Load enhanced CSS with mobile-first responsive design"""
    css = """
    /* AGStock Enhanced Design System 4.0 */
    
    :root {
        --primary: #00D9FF;
        --primary-dark: #00A8CC;
        --success: #22c55e;
        --danger: #ef4444;
        --warning: #f59e0b;
        --background: #0f172a;
        --surface: #1e293b;
        --text: #f8fafc;
        --text-secondary: #94a3b8;
        --border: rgba(255, 255, 255, 0.1);
        --radius: 12px;
        --shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        --transition: all 0.3s ease;
    }
    
    /* Mobile-first responsive design */
    .stApp {
        background: linear-gradient(135deg, var(--background) 0%, #0a0f1a 100%);
    }
    
    /* Enhanced containers */
    .main-header {
        background: var(--surface);
        padding: 1.5rem;
        border-radius: var(--radius);
        border: 1px solid var(--border);
        margin-bottom: 2rem;
        backdrop-filter: blur(12px);
    }
    
    .content-card {
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: var(--transition);
    }
    
    .content-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow);
    }
    
    /* Enhanced metrics */
    .metric-enhanced {
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: var(--radius);
        padding: 1.25rem;
        text-align: center;
        transition: var(--transition);
    }
    
    .metric-enhanced:hover {
        background: rgba(59, 130, 246, 0.15);
        transform: scale(1.02);
    }
    
    /* Mobile optimizations */
    @media (max-width: 768px) {
        .stTabs [data-baseweb="tab-list"] {
            flex-wrap: nowrap;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
        
        .content-card {
            padding: 1rem;
            margin-bottom: 0.75rem;
        }
        
        .metric-enhanced {
            padding: 0.75rem;
            font-size: 0.9rem;
        }
        
        .main-header {
            padding: 1rem;
            margin-bottom: 1rem;
        }
    }
    
    /* Loading animations */
    .loading-skeleton {
        background: linear-gradient(90deg, #2d3748 25%, #4a5568 50%, #2d3748 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        border-radius: var(--radius);
        height: 100px;
    }
    
    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    /* Status indicators */
    .status-online { color: var(--success); }
    .status-warning { color: var(--warning); }
    .status-error { color: var(--danger); }
    
    /* Action buttons */
    .action-btn {
        background: var(--primary);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: var(--radius);
        font-weight: 600;
        transition: var(--transition);
        cursor: pointer;
    }
    
    .action-btn:hover {
        background: var(--primary-dark);
        transform: translateY(-1px);
    }
    
    /* Enhanced sidebar for mobile */
    @media (max-width: 768px) {
        .css-1d391kg {
            width: 100% !important;
        }
    }
    """

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# Initialize strategies with caching
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


# Risk manager initialization
def initialize_risk_manager():
    if "risk_manager" not in st.session_state:
        try:
            from src.advanced_risk import AdvancedRiskManager
            from src.oracle.oracle_2026 import Oracle2026

            rm = AdvancedRiskManager()
            oracle = Oracle2026()

            guidance = oracle.get_risk_guidance()
            rm.apply_oracle_guidance(guidance)

            st.session_state["risk_manager"] = rm
            st.session_state["oracle_2026"] = oracle
            st.session_state["risk_crash_warning"] = None
        except Exception as e:
            st.error(f"リスク管理初期化エラー: {e}")
            st.session_state["risk_manager"] = None


def render_main_header():
    """Render enhanced main header with key metrics"""
    with st.container():
        st.markdown('<div class="main-header">', unsafe_allow_html=True)

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown("## 🌍 AGStock AI Trading System")
            st.caption(
                "日本・米国・欧州の主要株式を対象としたプロ仕様のAIトレーディングシステム"
            )

        with col2:
            # System status
            status_color = "status-online"
            status_text = "システム正常"

            if "risk_manager" in st.session_state and st.session_state["risk_manager"]:
                rm = st.session_state["risk_manager"]
                crash_ok, _ = rm.check_market_crash(logger=None)
                if not crash_ok:
                    status_color = "status-warning"
                    status_text = "警戒モード"

            st.markdown(
                f'<div class="{status_color}">🟢 {status_text}</div>',
                unsafe_allow_html=True,
            )

        with col3:
            # Last update time
            st.caption(f"最終更新: {datetime.datetime.now().strftime('%H:%M:%S')}")
            if st.button("🔄 更新", key="main_refresh", help="手動更新"):
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


def render_simplified_tabs():
    """Render simplified and categorized tabs"""

    # Get signal count for badge
    signal_count = 0
    try:
        import json
        import os

        if os.path.exists("scan_results.json"):
            with open("scan_results.json", "r", encoding="utf-8") as f:
                scan_data = json.load(f)
                results = scan_data.get("results", [])
                signal_count = len([r for r in results if r.get("Action") != "HOLD"])
    except Exception:
        signal_count = 0

    # Simplified tab structure with logical grouping
    tab_config = [
        {
            "name": "🏠 ダッシュボード",
            "key": "dashboard",
            "description": "概要と基本情報",
        },
        {
            "name": f"💼 トレーディング{f' ({signal_count})' if signal_count > 0 else ''}",
            "key": "trading",
            "description": "取引とポートフォリオ",
        },
        {"name": "🤖 AI分析", "key": "ai", "description": "AI予測と分析"},
        {
            "name": "📊 パフォーマンス",
            "key": "performance",
            "description": "運用成績と分析",
        },
        {"name": "🧪 詳細設定", "key": "advanced", "description": "詳細機能と設定"},
    ]

    tab_names = [tab["name"] for tab in tab_config]
    tabs = st.tabs(tab_names)

    return tabs, tab_config


def main():
    """Enhanced main application with improved UX"""

    # Load enhanced CSS
    load_enhanced_css()

    # Initialize components
    initialize_risk_manager()
    strategies = get_strategies()

    # Render main header
    render_main_header()

    # Quick overview for desktop users
    if st.session_state.get("show_quick_overview", True):
        with st.expander("🌟 クイック概要", expanded=False):
            render_quick_overview()

    # Render responsive navigation
    render_responsive_nav()

    # Get sidebar config
    sidebar_config = render_sidebar()

    # Render simplified tabs
    tabs, tab_config = render_simplified_tabs()

    # Tab content with loading states
    with tabs[0]:  # Dashboard
        with loading_spinner("ダッシュボードを読み込み中..."):
            create_simple_dashboard()

    with tabs[1]:  # Trading
        with loading_spinner("トレーディング情報を読み込み中..."):
            render_trading_hub(sidebar_config, strategies)

    with tabs[2]:  # AI Hub
        with loading_spinner("AI分析センターを読み込み中..."):
            render_ai_hub()

    with tabs[3]:  # Performance
        with loading_spinner("パフォーマンスデータを読み込み中..."):
            render_performance_analyst()

    with tabs[4]:  # Advanced
        # Sub-tabs for advanced features
        sub_tabs = st.tabs(
            ["🧪 戦略研究所", "🏆 トーナメント", "🚀 Mission Control", "🏛️ Divine Hub"]
        )

        with sub_tabs[0]:
            render_strategy_arena()
        with sub_tabs[1]:
            render_tournament_ui()
        with sub_tabs[2]:
            render_mission_control()
        with sub_tabs[3]:
            render_divine_reflection()

    # Real-time monitor (enhanced)
    with st.sidebar.expander("⚡ リアルタイム監視", expanded=False):

        @st.fragment(run_every="30s")
        def render_realtime_stream():
            st.markdown("マーケット監視中 (30s自動更新)")
            try:
                from src.realtime.streamer import get_streamer

                watchlist = ["7203.T", "9984.T", "6758.T", "AAPL", "NVDA"]
                streamer = get_streamer(watchlist)
                streamer._fetch_latest()
                data = streamer.latest_data

                cols = st.columns(len(watchlist) if len(watchlist) <= 3 else 3)
                for i, (ticker, info) in enumerate(data.items()):
                    with cols[i % len(cols)]:
                        st.metric(
                            label=ticker,
                            value=f"{info['price']:,.1f}",
                            delta=f"{info.get('change', 0):+.2f}%",
                        )

                st.caption(f"更新: {datetime.datetime.now().strftime('%H:%M:%S')}")
            except Exception as e:
                status_badge("error", f"ストリームエラー: {e}")

        render_realtime_stream()

    # Footer with system info
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("🤖 Hyper-Auto Mode")
    with col2:
        st.caption("🛡️ リスク管理: 有効")
    with col3:
        st.caption("📊 データ: リアルタイム")


if __name__ == "__main__":
    main()
