"""
Mobile-optimized main page for AGStock
PWA ready with responsive design
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time

# PWA configuration
st.set_page_config(
    page_title="AGStock Mobile",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="auto",
)


# Custom CSS for mobile
def load_mobile_css():
    with open("static/mobile.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Mobile navigation
def show_mobile_navigation():
    st.markdown(
        """
    <div class="mobile-header">
        <div class="mobile-nav">
            <a href="/" class="nav-brand">📱 AGStock</a>
            <div class="nav-menu">
                <a href="#dashboard" class="nav-item active">📊</a>
                <a href="#trading" class="nav-item">⚡</a>
                <a href="#ai" class="nav-item">🤖</a>
                <a href="#profile" class="nav-item">👤</a>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_portfolio_summary_mobile():
    """Mobile-optimized portfolio summary"""
    st.markdown('<div class="mobile-card">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="metric-mobile">', unsafe_allow_html=True)
        st.markdown(
            '<div class="metric-value">¥1,050,000</div>', unsafe_allow_html=True
        )
        st.markdown('<div class="metric-label">総資産</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-mobile">', unsafe_allow_html=True)
        st.markdown(
            '<div class="metric-value metric-change positive">+2.5%</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="metric-label">今日</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def show_quick_actions_mobile():
    """Mobile quick actions"""
    st.markdown('<div class="mobile-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="mobile-card-title">クイックアクション</h3>', unsafe_allow_html=True
    )

    if st.button(
        "📊 ポートフォリオ",
        key="mobile_portfolio",
        use_container_width=True,
        help="現在のポートフォリオを確認",
    ):
        st.success("ポートフォリオ画面に移動します")

    if st.button(
        "⚡ クイック取引",
        key="mobile_trading",
        use_container_width=True,
        help="ワンクリックで取引",
    ):
        st.success("クイック取引を開始します")

    if st.button(
        "🤖 AIアシスタント", key="mobile_ai", use_container_width=True, help="AIに相談"
    ):
        st.success("AIアシスタント画面に移動します")

    if st.button(
        "🔔 通知", key="mobile_notify", use_container_width=True, help="通知を確認"
    ):
        st.success("通知画面に移動します")

    st.markdown("</div>", unsafe_allow_html=True)


def show_mobile_chart():
    """Mobile-optimized chart"""
    st.markdown('<div class="chart-mobile">', unsafe_allow_html=True)

    # Sample data for mobile
    dates = pd.date_range(end=datetime.now(), periods=30, freq="D")
    prices = [1000000 + i * 1000 for i in range(30)]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=prices,
            mode="lines",
            name="ポートフォリオ価値",
            line=dict(color="#667eea", width=2),
        )
    )

    fig.update_layout(
        title="30日間の推移",
        height=200,
        showlegend=False,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)


def show_holdings_mobile():
    """Mobile holdings list"""
    st.markdown('<div class="list-mobile">', unsafe_allow_html=True)

    holdings = [
        {"ticker": "7203", "name": "トヨタ", "price": "¥2,800", "change": "+1.2%"},
        {"ticker": "6758", "name": "ソニー", "price": "¥12,000", "change": "-0.5%"},
        {
            "ticker": "9984",
            "name": "ソフトバンク",
            "price": "¥8,000",
            "change": "+2.1%",
        },
    ]

    for holding in holdings:
        change_class = "positive" if "+" in holding["change"] else "negative"
        st.markdown(
            f"""
        <div class="list-item-mobile">
            <div>
                <div class="mobile-card-title">{holding["name"]}</div>
                <div class="mobile-card-subtitle">{holding["ticker"]}</div>
            </div>
            <div style="text-align: right;">
                <div>{holding["price"]}</div>
                <div class="metric-change {change_class}">{holding["change"]}</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def show_quick_trade_mobile():
    """Mobile quick trade form"""
    st.markdown('<div class="form-mobile">', unsafe_allow_html=True)

    with st.form("mobile_trade_form"):
        st.markdown(
            '<label class="form-label-mobile">銘柄コード</label>',
            unsafe_allow_html=True,
        )
        ticker = st.text_input("", placeholder="例: 7203", key="mobile_ticker_input")

        st.markdown(
            '<label class="form-label-mobile">取引</label>', unsafe_allow_html=True
        )
        trade_type = st.selectbox("", ["買付", "売却"], key="mobile_trade_type")

        st.markdown(
            '<label class="form-label-mobile">金額</label>', unsafe_allow_html=True
        )
        amount = st.number_input(
            "",
            min_value=1000,
            value=10000,
            step=1000,
            key="mobile_amount_input",
            format="¥%,d",
        )

        if st.form_submit_button("取引実行", use_container_width=True, type="primary"):
            if ticker and amount > 0:
                st.success(f"{trade_type}注文を送信しました: {ticker} {amount:,}")

    st.markdown("</div>", unsafe_allow_html=True)


def show_mobile_tabs():
    """Mobile tabs interface"""
    tab1, tab2, tab3 = st.tabs(["📊 概要", "⚡ 取引", "🔔 通知"])

    with tab1:
        show_portfolio_summary_mobile()
        show_quick_actions_mobile()
        show_mobile_chart()
        show_holdings_mobile()

    with tab2:
        show_quick_trade_mobile()

        # Trading history
        st.markdown('<div class="list-mobile">', unsafe_allow_html=True)
        st.markdown(
            '<h3 class="mobile-card-title">最近の取引</h3>', unsafe_allow_html=True
        )

        trades = [
            {
                "time": "09:30",
                "ticker": "7203",
                "type": "買付",
                "amount": "¥280,000",
                "status": "✅",
            },
            {
                "time": "14:15",
                "ticker": "6758",
                "type": "売却",
                "amount": "¥600,000",
                "status": "✅",
            },
            {
                "time": "15:30",
                "ticker": "9984",
                "type": "買付",
                "amount": "¥80,000",
                "status": "🔄",
            },
        ]

        for trade in trades:
            st.markdown(
                f"""
            <div class="list-item-mobile">
                <div>
                    <div>{trade["time"]} {trade["ticker"]}</div>
                    <div class="mobile-card-subtitle">{trade["type"]}</div>
                </div>
                <div style="text-align: right;">
                    <div>{trade["amount"]}</div>
                    <div>{trade["status"]}</div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="list-mobile">', unsafe_allow_html=True)
        st.markdown('<h3 class="mobile-card-title">通知</h3>', unsafe_allow_html=True)

        notifications = [
            {
                "time": "10:15",
                "type": "価格",
                "message": "7203が指定価格到達",
                "priority": "high",
            },
            {
                "time": "14:30",
                "type": "ポートフォリオ",
                "message": "日次レポート作成完了",
                "priority": "medium",
            },
            {
                "time": "15:45",
                "type": "市場",
                "message": "日経平均終値更新",
                "priority": "low",
            },
        ]

        for notif in notifications:
            priority_color = (
                "status-error"
                if notif["priority"] == "high"
                else "status-warning"
                if notif["priority"] == "medium"
                else "status-success"
            )
            st.markdown(
                f"""
            <div class="list-item-mobile">
                <div>
                    <div class="status-badge {priority_color}">{notif["type"]}</div>
                    <div class="mobile-card-subtitle">{notif["message"]}</div>
                </div>
                <div style="text-align: right; font-size: 12px; color: #7f8c8d;">
                    {notif["time"]}
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)


def show_mobile_bottom_nav():
    """Mobile bottom navigation"""
    st.markdown(
        """
    <div style="position: fixed; bottom: 0; left: 0; right: 0; background: white; 
                border-top: 1px solid #ecf0f1; padding: 8px 0; z-index: 1000;">
        <div style="display: flex; justify-content: space-around; align-items: center;">
            <a href="#home" style="text-decoration: none; color: #667eea; font-size: 12px; text-align: center;">
                🏠<br>ホーム
            </a>
            <a href="#portfolio" style="text-decoration: none; color: #7f8c8d; font-size: 12px; text-align: center;">
                📊<br>ポートフォリオ
            </a>
            <a href="#trading" style="text-decoration: none; color: #7f8c8d; font-size: 12px; text-align: center;">
                ⚡<br>取引
            </a>
            <a href="#ai" style="text-decoration: none; color: #7f8c8d; font-size: 12px; text-align: center;">
                🤖<br>AI
            </a>
            <a href="#profile" style="text-decoration: none; color: #7f8c8d; font-size: 12px; text-align: center;">
                👤<br>設定
            </a>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_pwa_install_prompt():
    """PWA install prompt for mobile"""
    if "isMobile" in st.session_state:
        st.markdown(
            """
        <div id="install-prompt" style="position: fixed; top: 60px; left: 20px; 
                    background: linear-gradient(135deg, #667eea, #764ba2); color: white; 
                    padding: 12px 20px; border-radius: 25px; 
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 1001;
                    font-size: 14px; font-weight: 600; cursor: pointer;">
            📱 アプリをインストール
        </div>
        """,
            unsafe_allow_html=True,
        )


def main():
    """Main mobile page"""
    # Load mobile CSS
    try:
        load_mobile_css()
    except FileNotFoundError:
        st.warning("Mobile CSS not found")

    # Check if mobile
    is_mobile = st.session_state.get("isMobile", False)

    if is_mobile:
        show_mobile_navigation()
        show_pwa_install_prompt()

    st.title("📱 AGStock Mobile")
    st.markdown(
        "<p style='text-align: center; color: #7f8c8d; margin-bottom: 20px;'>いつでもどこでも投資を管理</p>",
        unsafe_allow_html=True,
    )

    # Main content
    show_mobile_tabs()

    if is_mobile:
        show_mobile_bottom_nav()

    # Service Worker registration (for PWA)
    if is_mobile:
        st.markdown(
            """
        <script>
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/sw.js').then(registration => {
                console.log('ServiceWorker registered');
            }).catch(error => {
                console.log('ServiceWorker registration failed:', error);
            });
        }
        </script>
        """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
