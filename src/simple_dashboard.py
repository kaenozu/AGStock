"""
個人投資家向けシンプルダッシュボード (Ultra Simple Version)

一目でわかる資産状況 - Zero-Touch Mode
"""

from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.paper_trader import PaperTrader


def format_currency_jp(amount: float) -> str:
    """日本円を万円形式で表示"""
    if amount >= 100000000:
        return f"¥{amount/100000000:.2f}億"
    elif amount >= 10000:
        return f"¥{amount/10000:.1f}万"
    else:
        return f"¥{amount:,.0f}"


def _show_market_status():
    """市場開閉状況を表示"""
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    weekday = now.weekday()  # 0=Monday, 6=Sunday

    markets = []

    # 東京証券取引所 (9:00-11:30, 12:30-15:00 JST)
    if weekday < 5:  # 平日
        if (9 <= hour < 11) or (hour == 11 and minute < 30) or (12 <= hour < 15 and not (hour == 12 and minute < 30)):
            markets.append("東証: 営業中")
        else:
            markets.append("東証: 休場中")
    else:
        markets.append("東証: 休場日")

    # NY証券取引所 (14:30-21:00 JST)
    if weekday < 5:  # 平日
        if (14 <= hour < 21) or (hour == 14 and minute >= 30):
            markets.append("NYSE: 営業中")
        else:
            markets.append("NYSE: 休場中")
    else:
        markets.append("NYSE: 休場日")

    # モード表示
    for market in markets:
        if "営業中" in market:
            st.success(market)
        else:
            st.info(market)


def _show_portfolio_summary():
    """ポートフォリオ概要を表示"""
    pt = PaperTrader()
    try:
        balance = pt.get_current_balance()
        positions = pt.get_positions()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("総資産", format_currency_jp(balance["total_equity"]))
        with col2:
            st.metric("現金", format_currency_jp(balance["cash"]))
        with col3:
            st.metric(
                "評価損益",
                format_currency_jp(balance["unrealized_pnl"]),
                delta=format_currency_jp(balance["daily_pnl"]),
            )
        with col4:
            st.metric("保有銘柄数", len(positions))

        # ポジション詳細
        if not positions.empty:
            st.subheader("保有銘柄")
            positions_display = positions.copy()
            positions_display["保有額"] = positions_display["current_price"] * positions_display["quantity"]
            positions_display["評価損益"] = positions_display["unrealized_pnl"]
            positions_display["評価損益率"] = positions_display["unrealized_pnl_pct"]

            # 列名を日本語に変換して表示
            display_df = positions_display[
                ["ticker", "company_name", "quantity", "current_price", "保有額", "評価損益", "評価損益率"]
            ].copy()
            display_df.columns = ["銘柄コード", "銘柄名", "数量", "現在価格", "保有額", "評価損益", "評価損益率"]

            # 数値のフォーマット
            display_df["現在価格"] = display_df["現在価格"].apply(lambda x: f"¥{x:,.0f}")
            display_df["保有額"] = display_df["保有額"].apply(format_currency_jp)
            display_df["評価損益"] = display_df["評価損益"].apply(format_currency_jp)
            display_df["評価損益率"] = display_df["評価損益率"].apply(lambda x: f"{x:.2%}")

            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("現在保有銘柄はありません")

    finally:
        pt.close()


def _show_performance_chart():
    """パフォーマンスチャートを表示"""
    pt = PaperTrader()
    try:
        # 直近30日分のデータを取得
        equity_data = pt.get_equity_history(days=30)

        if equity_data:
            df = pd.DataFrame(equity_data, columns=["date", "equity"])
            df["date"] = pd.to_datetime(df["date"])

            # グラフ作成
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["equity"],
                    mode="lines+markers",
                    name="総資産",
                    line=dict(color="#1f77b4", width=2),
                )
            )

            fig.update_layout(title="資産推移 (直近30日)", xaxis_title="日付", yaxis_title="総資産 (円)", height=400)

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("パフォーマンスデータがありません")
    finally:
        pt.close()


def _show_daily_summary():
    """日次サマリーを表示"""
    pt = PaperTrader()
    try:
        daily_summary = pt.get_daily_summary()
        if daily_summary:
            # 最新の日付のデータを表示
            latest = daily_summary[-1]
            date, pnl, trades = latest

            st.subheader("本日のサマリー")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("日付", date)
            with col2:
                st.metric("損益", format_currency_jp(pnl))
            with col3:
                st.metric("取引数", trades)
        else:
            st.info("本日の取引データがありません")
    finally:
        pt.close()


def main():
    """メインダッシュボード"""
    st.set_page_config(page_title="AGStock - ダッシュボード", page_icon="📈", layout="wide")

    st.title("個人投資家向けシンプルダッシュボード")

    # 市場状況
    with st.expander("市場状況", expanded=True):
        _show_market_status()

    # ポートフォリオ概要
    with st.expander("ポートフォリオ概要", expanded=True):
        _show_portfolio_summary()

    # パフォーマンスチャート
    with st.expander("パフォーマンス", expanded=True):
        _show_performance_chart()

    # 日次サマリー
    with st.expander("日次サマリー", expanded=False):
        _show_daily_summary()


if __name__ == "__main__":
    main()
