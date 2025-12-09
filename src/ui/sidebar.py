"""
Sidebar UI Module
Handles the rendering of the sidebar, including settings and filters.
"""
import streamlit as st
import json
from src.constants import MARKETS, TICKER_NAMES
from src.schemas import load_config as load_config_schema

def load_config():
    """Load config utilizing schema validation (fallback to defaults if error)."""
    config_obj = load_config_schema("config.json")
    return config_obj.model_dump()

def render_sidebar():
    """
    Renders the sidebar and returns the configuration dictionary.
    """
    st.sidebar.header("設定")

    # Market Selection
    selected_market = st.sidebar.selectbox("市場選択 (Market)", ["Japan", "US", "Europe", "Crypto", "All"], index=0)
    ticker_group = st.sidebar.selectbox("対象銘柄", [f"{selected_market} 主要銘柄", "カスタム入力"])

    custom_tickers = []
    if ticker_group == "カスタム入力":
        custom_input = st.sidebar.text_area("銘柄コードを入力 (カンマ区切り)", "7203.T, 9984.T")
        if custom_input:
            custom_tickers = [t.strip() for t in custom_input.split(",")]

    period = st.sidebar.selectbox("分析期間", ["1y", "2y", "5y"], index=1)

    # Trading Unit Setting
    st.sidebar.divider()
    st.sidebar.subheader("取引設定")
    use_fractional_shares = st.sidebar.checkbox("単元未満株 (1株〜) で取引", value=False, help="ONにすると、1株単位（S株/ミニ株）でシミュレーションします。少額資金での運用に適しています。")
    trading_unit = 1 if use_fractional_shares else 100

    # Notification Settings
    st.sidebar.divider()
    with st.sidebar.expander("📢 通知設定"):
        st.write("スキャン完了後に自動通知を送信します。")

        # Load current config via safe loader
        config = load_config()

        # LINE Notify
        line_conf = config.get("notifications", {}).get("line", {})
        if line_conf is None: line_conf = {}
        line_enabled = st.checkbox("LINE Notify を有効化", value=line_conf.get("enabled", False))
        line_token = st.text_input("LINE Notify Token", value=line_conf.get("token", ""), type="password", help="https://notify-bot.line.me/ja/ からトークンを取得してください")

        # Discord
        discord_conf = config.get("notifications", {}).get("discord", {})
        if discord_conf is None: discord_conf = {}
        discord_enabled = st.checkbox("Discord Webhook を有効化", value=discord_conf.get("enabled", False))
        discord_webhook = st.text_input("Discord Webhook URL", value=discord_conf.get("webhook_url", ""), type="password", help="Discordサーバー設定からWebhook URLを取得してください")

        # Save button
        if st.button("設定を保存", key="save_notification_config"):
            if "notifications" not in config:
                config["notifications"] = {}
            if "line" not in config["notifications"]:
                config["notifications"]["line"] = {}
            if "discord" not in config["notifications"]:
                config["notifications"]["discord"] = {}
                
            config["notifications"]["line"]["enabled"] = line_enabled
            config["notifications"]["line"]["token"] = line_token
            config["notifications"]["discord"]["enabled"] = discord_enabled
            config["notifications"]["discord"]["webhook_url"] = discord_webhook

            # Save back to JSON (we still write to JSON directly for persistence)
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            st.success("✅ 通知設定を保存しました！")

    # AI Committee Settings
    st.sidebar.divider()
    with st.sidebar.expander("🤖 AI委員会設定"):
        ai_conf = config.get("ai_committee", {})
        if ai_conf is None: ai_conf = {}
        
        ai_enabled = st.checkbox("AI委員会を有効化", value=ai_conf.get("enabled", False), help="AIエージェントによる取引審査を行います。APIコストが発生する可能性があります。")
        ai_strict_mode = st.checkbox("厳格モード (Strict Mode)", value=ai_conf.get("strict_mode", False), help="リスク管理エージェントの拒否権を強化します。", disabled=not ai_enabled)

        if st.button("AI設定を保存", key="save_ai_config"):
            if "ai_committee" not in config:
                config["ai_committee"] = {}
            config["ai_committee"]["enabled"] = ai_enabled
            config["ai_committee"]["strict_mode"] = ai_strict_mode
            
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            st.success("✅ AI設定を保存しました！")

    # Risk Management
    st.sidebar.divider()
    st.sidebar.subheader("リスク管理")
    allow_short = st.sidebar.checkbox("空売りを許可", value=False)
    position_size_pct = st.sidebar.slider("ポジションサイズ (%)", min_value=10, max_value=100, value=100, step=10)
    position_size = position_size_pct / 100

    # Fundamental Filters
    st.sidebar.divider()
    st.sidebar.subheader("ファンダメンタルズ (財務)")
    enable_fund_filter = st.sidebar.checkbox("財務フィルタを有効化", value=False)
    max_per = st.sidebar.number_input("PER (倍) 以下", value=15.0, step=1.0, disabled=not enable_fund_filter)
    max_pbr = st.sidebar.number_input("PBR (倍) 以下", value=1.5, step=0.1, disabled=not enable_fund_filter)
    min_roe = st.sidebar.number_input("ROE (%) 以上", value=8.0, step=1.0, disabled=not enable_fund_filter)

    # Live Mode
    st.sidebar.divider()
    if st.sidebar.checkbox("🔄 自動更新 (Live Mode)", value=False, help="60秒ごとにページを自動更新します。"):
        import time
        time.sleep(60)
        st.rerun()
        
    return {
        "selected_market": selected_market,
        "ticker_group": ticker_group,
        "custom_tickers": custom_tickers,
        "period": period,
        "use_fractional_shares": use_fractional_shares,
        "trading_unit": trading_unit,
        "allow_short": allow_short,
        "position_size": position_size,
        "enable_fund_filter": enable_fund_filter,
        "max_per": max_per,
        "max_pbr": max_pbr,
        "min_roe": min_roe
    }
