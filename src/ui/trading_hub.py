import streamlit as st

from src.ui.portfolio_panel import render_portfolio_panel
from src.ui.trading_panel import render_trading_panel
from src.ui_renderers import render_market_scan_tab


def render_trading_hub(sidebar_config, strategies):
    """Renders the consolidated Trading Action Hub"""
    st.header("💼 トレーディング・デスク (Action)")
    st.caption("市場スキャンからポートフォリオ管理、発注まで、取引に関するアクションを行います。")

    tabs = st.tabs(["📊 市場スキャン", "📈 ポートフォリオ", "📝 ペーパートレード (発注)"])

    with tabs[0]:
        # Use the full implementation from ui_renderers
        render_market_scan_tab(
            ticker_group=sidebar_config.get("ticker_group", "Japan 主要銘柄"),
            selected_market=sidebar_config.get("selected_market", "Japan"),
            custom_tickers=sidebar_config.get("custom_tickers", []),
            period=sidebar_config.get("period", "2y"),
            strategies=strategies,
            allow_short=sidebar_config.get("allow_short", False),
            position_size=sidebar_config.get("position_size", 1.0),
            enable_fund_filter=sidebar_config.get("enable_fund_filter", False),
            max_per=sidebar_config.get("max_per", 15.0),
            max_pbr=sidebar_config.get("max_pbr", 1.5),
            min_roe=sidebar_config.get("min_roe", 8.0),
            trading_unit=sidebar_config.get("trading_unit", 100),
        )

    with tabs[1]:
        render_portfolio_panel(sidebar_config, strategies)

    with tabs[2]:
        render_trading_panel(sidebar_config)
