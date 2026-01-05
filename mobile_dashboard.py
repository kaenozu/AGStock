#!/usr/bin/env python3
"""
AGStock Mobile-Optimized Dashboard
モバイル対応UIダッシュボード
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import requests
from typing import Dict, Any, List
import base64
import os


# モバイル検出
def is_mobile():
    """モバイルブラウザ判定"""
    user_agent = st.experimental_get_query_params().get("user_agent", [""])[0]
    mobile_keywords = ["Mobile", "Android", "iPhone", "iPad", "iPod"]
    return any(keyword in user_agent for keyword in mobile_keywords)


# Push通知クラス
class PushNotifier:
    """プッシュ通知管理クラス"""

    def __init__(self):
        self.push_services = {
            "line": self.send_line_notification,
            "discord": self.send_discord_notification,
            "email": self.send_email_notification,
        }

    def send_line_notification(self, message: str, token: str = None) -> bool:
        """LINE通知送信"""
        try:
            if not token:
                # 設定からトークン取得
                with open("config.json", "r") as f:
                    config = json.load(f)
                token = config.get("line_notify_token")

            if not token:
                st.warning("LINE通知トークンが設定されていません")
                return False

            url = "https://notify-api.line.me/api/notify"
            headers = {"Authorization": f"Bearer {token}"}
            data = {"message": message}

            response = requests.post(url, headers=headers, data=data)
            return response.status_code == 200

        except Exception as e:
            st.error(f"LINE通知エラー: {e}")
            return False

    def send_discord_notification(self, message: str, webhook_url: str = None) -> bool:
        """Discord通知送信"""
        try:
            if not webhook_url:
                with open("config.json", "r") as f:
                    config = json.load(f)
                webhook_url = config.get("discord_webhook_url")

            if not webhook_url:
                st.warning("Discord Webhook URLが設定されていません")
                return False

            data = {"content": message}
            response = requests.post(webhook_url, json=data)
            return response.status_code == 204

        except Exception as e:
            st.error(f"Discord通知エラー: {e}")
            return False

    def send_email_notification(
        self, subject: str, message: str, email_config: Dict = None
    ) -> bool:
        """メール通知送信"""
        try:
            import smtplib
            from email.mime.text import MIMEText

            if not email_config:
                with open("config.json", "r") as f:
                    config = json.load(f)
                email_config = config.get("email", {})

            smtp_server = email_config.get("smtp_server")
            smtp_port = email_config.get("smtp_port", 587)
            username = email_config.get("username")
            password = email_config.get("password")
            to_email = email_config.get("to_email")

            if not all([smtp_server, username, password, to_email]):
                st.warning("メール設定が不完全です")
                return False

            msg = MIMEText(message)
            msg["Subject"] = subject
            msg["From"] = username
            msg["To"] = to_email

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            server.quit()

            return True

        except Exception as e:
            st.error(f"メール通知エラー: {e}")
            return False


# レスポンシブUIコンポーネント
def mobile_metric_card(
    title: str, value: str, subtitle: str = None, delta: str = None, color: str = "blue"
):
    """モバイル対応メトリックカード"""
    card_html = f"""
    <div style="
        background: linear-gradient(135deg, {color}15, {color}05);
        border: 1px solid {color}30;
        border-radius: 10px;
        padding: 15px;
        margin: 5px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        <div style="font-size: 14px; color: #666; margin-bottom: 5px;">{title}</div>
        <div style="font-size: 24px; font-weight: bold; color: {color};">{value}</div>
        {'<div style="font-size: 12px; color: #888;">{subtitle}</div>' if subtitle else ""}
        {f'<div style="font-size: 12px; color: {"green" if delta.startswith("+") else "red"};">{delta}</div>' if delta else ""}
    </div>
    """
    return card_html


def create_mobile_chart(
    data: pd.DataFrame, chart_type: str, title: str, height: int = 300
):
    """モバイル対応チャート作成"""
    if chart_type == "line":
        fig = px.line(
            data, x="timestamp", y="value", title=title, template="plotly_white"
        )
    elif chart_type == "bar":
        fig = px.bar(
            data, x="category", y="value", title=title, template="plotly_white"
        )
    else:
        fig = go.Figure()

    # モバイル向け最適化
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        font=dict(size=10),
        showlegend=False,
    )

    return fig


def get_portfolio_summary() -> Dict[str, Any]:
    """ポートフォリオ概要取得"""
    try:
        with open("data/portfolio.json", "r") as f:
            portfolio = json.load(f)

        total_value = sum(
            pos.get("current_value", 0) for pos in portfolio.get("positions", [])
        )
        total_cost = sum(
            pos.get("cost_basis", 0) for pos in portfolio.get("positions", [])
        )
        pnl = total_value - total_cost
        pnl_pct = (pnl / total_cost * 100) if total_cost > 0 else 0

        return {
            "total_value": total_value,
            "total_cost": total_cost,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "positions_count": len(portfolio.get("positions", [])),
        }

    except Exception as e:
        st.error(f"ポートフォリオデータ取得エラー: {e}")
        return {
            "total_value": 0,
            "total_cost": 0,
            "pnl": 0,
            "pnl_pct": 0,
            "positions_count": 0,
        }


def get_recent_alerts(limit: int = 5) -> List[Dict]:
    """最近のアラート取得"""
    try:
        alert_file = "data/alerts.json"
        if os.path.exists(alert_file):
            with open(alert_file, "r") as f:
                alerts = json.load(f)
            return alerts[-limit:]
        return []
    except:
        return []


def mobile_quick_actions():
    """モバイルクイックアクション"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔄 更新", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("📊 詳細", use_container_width=True):
            st.session_state.show_details = not st.session_state.get(
                "show_details", False
            )

    with col3:
        if st.button("🔔 通知", use_container_width=True):
            st.session_state.show_notifications = True

    with col4:
        if st.button("⚙️ 設定", use_container_width=True):
            st.session_state.show_settings = True


def main():
    """メイン実行関数"""
    # モバイル検出と設定
    mobile = is_mobile()

    # ページ設定
    page_config = {
        "page_title": "AGStock Mobile",
        "page_icon": "📱",
        "layout": "wide" if not mobile else "centered",
        "initial_sidebar_state": "expanded" if not mobile else "collapsed",
    }

    st.set_page_config(**page_config)

    # カスタムCSS（モバイル対応）
    mobile_css = """
    <style>
    .st-emotion-cache-1kyxreq { padding: 1rem; }
    .st-emotion-cache-1oe5lae { margin-bottom: 1rem; }
    
    @media (max-width: 768px) {
        .st-emotion-cache-1kyxreq { padding: 0.5rem; }
        .st-emotion-cache-1oe5lae { margin-bottom: 0.5rem; }
        .element-container { margin-bottom: 0.5rem; }
    }
    </style>
    """
    st.markdown(mobile_css, unsafe_allow_html=True)

    # タイトル
    st.title("📱 AGStock Mobile Dashboard")
    st.markdown("---")

    # クイックアクション
    mobile_quick_actions()

    # プッシュ通知設定
    notifier = PushNotifier()

    # ポートフォリオ概要
    portfolio = get_portfolio_summary()

    # メインダッシュボード（モバイル対応レイアウト）
    if mobile:
        # モバイルレイアウト
        st.subheader("💰 ポートフォリオ概要")

        # メトリックカード
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                mobile_metric_card(
                    "総資産価値",
                    f"¥{portfolio['total_value']:,.0f}",
                    f"銘柄数: {portfolio['positions_count']}",
                    color="blue",
                ),
                unsafe_allow_html=True,
            )

        with col2:
            delta_color = "green" if portfolio["pnl"] >= 0 else "red"
            delta_text = (
                f"+{portfolio['pnl_pct']:.1f}%"
                if portfolio["pnl"] >= 0
                else f"{portfolio['pnl_pct']:.1f}%"
            )
            st.markdown(
                mobile_metric_card(
                    "損益",
                    f"¥{portfolio['pnl']:,.0f}",
                    delta=delta_text,
                    color=delta_color,
                ),
                unsafe_allow_html=True,
            )

        # 最近のアラート
        st.subheader("🚨 最近のアラート")
        alerts = get_recent_alerts()

        if alerts:
            for alert in alerts:
                alert_type = alert.get("type", "info")
                emoji = {"warning": "⚠️", "error": "🚨", "info": "ℹ️"}.get(
                    alert_type, "📢"
                )
                st.markdown(
                    f"""
                <div style="
                    background: {"#fff3cd" if alert_type == "warning" else "#f8d7da" if alert_type == "error" else "#d1ecf1"};
                    border-left: 4px solid {"#856404" if alert_type == "warning" else "#721c24" if alert_type == "error" else "#0c5460"};
                    padding: 10px;
                    margin: 5px 0;
                    border-radius: 5px;
                ">
                    <strong>{emoji} {alert.get("title", "アラート")}</strong><br>
                    <small>{alert.get("message", "")}</small><br>
                    <small style="color: #666;">{alert.get("timestamp", "")}</small>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("📋 現在アラートはありません")

        # クイック取引操作
        st.subheader("⚡ クイック操作")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💰 資産状況確認", use_container_width=True):
                st.session_state.page = "portfolio"

        with col2:
            if st.button("📈 市場分析", use_container_width=True):
                st.session_state.page = "market"

    else:
        # デスクトップレイアウト（従来のダッシュボード）
        st.subheader("💰 ポートフォリオ概要")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("総資産価値", f"¥{portfolio['total_value']:,.0f}")

        with col2:
            st.metric(
                "損益", f"¥{portfolio['pnl']:,.0f}", f"{portfolio['pnl_pct']:.1f}%"
            )

        with col3:
            st.metric("保有銘柄数", portfolio["positions_count"])

        with col4:
            st.metric("本日の変動", "+¥12,345", "+2.3%")  # ダミーデータ

        # 通知設定セクション
        with st.expander("🔔 プッシュ通知設定", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**LINE通知**")
                line_token = st.text_input("LINE Notify Token", type="password")
                if st.button("LINE通知テスト"):
                    if notifier.send_line_notification(
                        "🧪 テスト通知 from AGStock", line_token
                    ):
                        st.success("✅ LINE通知送信成功")
                    else:
                        st.error("❌ LINE通知送信失敗")

            with col2:
                st.write("**緊急通知設定**")
                emergency_threshold = st.slider(
                    "損失警告閾値 (%)", min_value=1, max_value=20, value=5
                )
                profit_target = st.slider(
                    "利益目標通知 (%)", min_value=1, max_value=20, value=10
                )

    # モバイル専用機能
    if mobile:
        # 画面下部の固定ナビゲーション
        st.markdown(
            """
        <div style="
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            border-top: 1px solid #ddd;
            padding: 10px;
            z-index: 999;
            display: flex;
            justify-content: space-around;
        ">
            <div style="text-align: center; font-size: 12px;">
                <div>📊</div>
                <div>ダッシュ</div>
            </div>
            <div style="text-align: center; font-size: 12px;">
                <div>💼</div>
                <div>ポート</div>
            </div>
            <div style="text-align: center; font-size: 12px;">
                <div>📈</div>
                <div>市場</div>
            </div>
            <div style="text-align: center; font-size: 12px;">
                <div>⚙️</div>
                <div>設定</div>
            </div>
        </div>
        
        <div style="margin-bottom: 80px;"></div>
        """,
            unsafe_allow_html=True,
        )

    # サイドバー（デスクトップのみ）
    if not mobile:
        with st.sidebar:
            st.subheader("📱 モバイル機能")
            st.info("""
            **モバイル対応機能:**
            - レスポンシブUI
            - プッシュ通知
            - クイック操作
            - タッチ最適化
            """)

            st.subheader("🔔 通知テスト")
            if st.button("テスト通知送信"):
                message = f"📱 テスト通知\\n時刻: {datetime.now().strftime('%H:%M:%S')}\\n総資産: ¥{portfolio['total_value']:,.0f}"

                # 設定に基づいて通知送信
                if notifier.send_line_notification(message):
                    st.success("✅ LINE通知送信")
                else:
                    st.warning("❌ 通知送信失敗")


if __name__ == "__main__":
    main()
