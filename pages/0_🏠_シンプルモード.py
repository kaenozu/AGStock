"""
シンプルモード用Streamlitページ
初心者向けの直感的なインターフェース
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# 設定
st.set_page_config(
    page_title="AGStock シンプルモード",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# カスタムCSS
st.markdown(
    """
<style>
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    border-radius: 10px;
    color: white;
    margin: 10px 0;
    text-align: center;
}
.quick-action-btn {
    background: #4CAF50;
    color: white;
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    cursor: pointer;
    margin: 5px;
}
.simple-mode-header {
    text-align: center;
    margin-bottom: 30px;
}
</style>
""",
    unsafe_allow_html=True,
)

# 状態管理
if "simple_mode_initialized" not in st.session_state:
    st.session_state.simple_mode_initialized = True
    st.session_state.portfolio_value = 1000000
    st.session_state.daily_change = 0.0
    st.session_state.total_return = 0.12


def show_simple_header():
    """シンプルモードのヘッダーを表示"""
    st.markdown(
        """
    <div class="simple-mode-header">
        <h1>🏠 AGStock シンプルモード</h1>
        <p>自動売買を簡単に始めましょう</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_portfolio_summary():
    """ポートフォリオ概要を表示"""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>総資産</h3>
            <h2>¥{st.session_state.portfolio_value:,.0f}</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        change_color = "green" if st.session_state.daily_change >= 0 else "red"
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>今日の変動</h3>
            <h2 style="color: {change_color}">{st.session_state.daily_change:+.1%}</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>総リターン</h3>
            <h2>{st.session_state.total_return:+.1%}</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )


def show_quick_actions():
    """クイックアクションボタン"""
    st.subheader("🚀 クイックアクション")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 ポートフォリオ確認", use_container_width=True):
            st.success("ポートフォリオ詳細ページに移動します")
            # ここでページ遷移を実装

    with col2:
        if st.button("⚡ クイック取引", use_container_width=True):
            st.success("クイック取引画面を開きます")
            # クイック取引モーダルを表示

    with col3:
        if st.button("📈 パフォーマンス確認", use_container_width=True):
            st.success("パフォーマンスレポートを表示します")


def show_simple_chart():
    """シンプルな価格チャート"""
    # サンプルデータ
    dates = pd.date_range(end=datetime.now(), periods=30, freq="D")
    prices = 1000000 * (
        1
        + pd.Series(range(30)) * 0.001
        + pd.Series(range(30)).apply(lambda x: x % 5 * 0.0005)
    )

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
        title="30日間のポートフォリオ価値",
        xaxis_title="日付",
        yaxis_title="価値 (円)",
        height=300,
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)


def show_quick_trade_panel():
    """クイック取引パネル"""
    st.subheader("⚡ クイック取引")

    with st.form("quick_trade_form"):
        col1, col2 = st.columns(2)

        with col1:
            ticker = st.text_input("銘柄コード", placeholder="例: 7203", value="7203")
            action = st.selectbox("取引", ["買付", "売却"])

        with col2:
            amount = st.number_input(
                "金額 (円)", min_value=1000, value=10000, step=1000
            )
            quantity = st.number_input("数量", min_value=1, value=100, step=10)

        submitted = st.form_submit_button("取引実行", type="primary")

        if submitted:
            if ticker and amount > 0:
                st.success(f"{action}注文を実行しました: {ticker} - ¥{amount:,}")

                # 実際の取引ロジックを呼び出す
                # result = execute_quick_trade(ticker, action, amount, quantity)

            else:
                st.error("銘柄コードと金額を入力してください")


def show_simple_holdings():
    """シンプルな保有銘柄表示"""
    st.subheader("📊 保有銘柄")

    # サンプルデータ
    holdings = pd.DataFrame(
        {
            "銘柄": ["トヨタ自動車", "ソニーグループ", "ソフトバンク"],
            "コード": ["7203", "6758", "9984"],
            "数量": [100, 50, 30],
            "評価額": [1500000, 800000, 600000],
            "損益": [+50000, -20000, +15000],
            "損益率": [+3.3, -2.4, +2.6],
        }
    )

    # 損益に応じた色付け
    def color_pnl(val):
        color = "green" if val >= 0 else "red"
        return f"color: {color}"

    styled = holdings.style.applymap(color_pnl, subset=["損益", "損益率"])
    st.dataframe(styled, use_container_width=True, hide_index=True)


def show_simple_status():
    """システム状態をシンプルに表示"""
    with st.expander("システム状態", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.metric("取引エンジン", "✅ 正常")
            st.metric("データ接続", "✅ 正常")

        with col2:
            st.metric("最終更新", f"{datetime.now().strftime('%H:%M')}")
            st.metric("実行中戦略", "2")


def show_help_panel():
    """ヘルプパネル"""
    with st.expander("📖 使い方", expanded=False):
        st.markdown("""
        ### シンプルモードの使い方
        
        1. **ポートフォリオ確認**: 現在の資産状況を確認
        2. **クイック取引**: ワンクリックで取引を実行
        3. **パフォーマンス確認**: 運用成績を確認
        
        ### よくある質問
        
        **Q: 取引を開始するには？**
        A: 「クイック取引」から銘柄と金額を入力し実行
        
        **Q: リスクは？**
        A: 自動で損切りを設定し、リスクを管理
        
        **Q: 詳細設定は？**
        A: 上部メニューから「詳細モード」に切り替え
        """)


def main():
    """メイン関数"""
    show_simple_header()

    # タブ表示
    tab1, tab2, tab3 = st.tabs(["📊 ダッシュボード", "⚡ 取引", "📈 分析"])

    with tab1:
        show_portfolio_summary()
        st.markdown("---")
        show_quick_actions()
        st.markdown("---")
        show_simple_chart()
        show_simple_holdings()
        show_simple_status()
        show_help_panel()

    with tab2:
        show_quick_trade_panel()

    with tab3:
        st.subheader("📈 簡単分析")

        # パフォーマンス概要
        col1, col2 = st.columns(2)
        with col1:
            st.metric("月間リターン", "+2.3%")
            st.metric("年間リターン", "+12.5%")
        with col2:
            st.metric("シャープレシオ", "1.25")
            st.metric("最大ドローダウン", "-5.2%")

        st.markdown("---")

        # 資産配円グラフ
        fig = go.Figure(
            data=[go.Pie(labels=holdings["銘柄"], values=holdings["評価額"], hole=0.3)]
        )
        fig.update_layout(title="資産配分")
        st.plotly_chart(fig, use_container_width=True)


# サンプルデータ
holdings = pd.DataFrame(
    {
        "銘柄": ["トヨタ自動車", "ソニーグループ", "ソフトバンク"],
        "コード": ["7203", "6758", "9984"],
        "数量": [100, 50, 30],
        "評価額": [1500000, 800000, 600000],
        "損益": [+50000, -20000, +15000],
        "損益率": [+3.3, -2.4, +2.6],
    }
)

if __name__ == "__main__":
    main()
