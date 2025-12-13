import json

import streamlit as st

from src.formatters import format_currency
from src.paper_trader import PaperTrader


def show_settings_page():
    """設定ページ"""
    st.title("⚙️ 設定")

    st.markdown("---")

    # 初期資金
    st.subheader("💰 初期資金")
    pt = PaperTrader()
    st.info(f"現在の初期資金: {format_currency(pt.initial_capital)}")
    st.caption("※ 初期資金を変更するには、ペーパートレードをリセットしてください")

    st.markdown("---")

    # リスク設定
    st.subheader("🎯 リスク設定")

    risk_level = st.radio("リスク許容度を選択", ["安全重視（推奨）", "バランス", "積極的"], index=0)

    if risk_level == "安全重視（推奨）":
        st.success("✅ 損失を最小限に抑えます。初心者におすすめです。")
    elif risk_level == "バランス":
        st.info("⚖️ リスクとリターンのバランスを取ります。")
    else:
        st.warning("⚠️ 高いリターンを狙いますが、損失リスクも高まります。")

    st.markdown("---")

    # 通知設定
    st.subheader("🔔 通知設定")

    # 現在の設定を読み込む
    config_path = "config.json"
    current_config = {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            current_config = json.load(f)
    except FileNotFoundError:
        pass

    notifications = current_config.get("notifications", {})
    line_config = notifications.get("line", {})

    enable_line = st.checkbox("LINE通知を受け取る", value=line_config.get("enabled", False))

    line_token = st.text_input(
        "LINEトークン", value=line_config.get("token", ""), type="password", disabled=not enable_line
    )
    st.caption("トークンの取得方法: https://notify-bot.line.me/")

    st.markdown("---")

    # 保存ボタン
    if st.button("💾 設定を保存", type="primary", use_container_width=True):
        # 設定更新
        if "notifications" not in current_config:
            current_config["notifications"] = {}

        current_config["notifications"]["line"] = {"enabled": enable_line, "token": line_token}

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(current_config, f, indent=4, ensure_ascii=False)
            st.success("✅ 設定を保存しました！")
            st.balloons()
        except Exception as e:
            st.error(f"保存エラー: {e}")


show_settings_page()
