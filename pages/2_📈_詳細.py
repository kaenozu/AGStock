import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.formatters import format_currency
from src.paper_trader import PaperTrader


def show_detail_page():
    """詳細ページ"""
    pt = PaperTrader()

    st.title("📈 詳細")

    st.markdown("---")

    # 資産推移グラフ
    st.subheader("📊 資産の推移")

    equity_history = pt.get_equity_history()

    if not equity_history.empty:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=equity_history["date"],
                y=equity_history["total_equity"],
                mode="lines+markers",
                name="総資産",
                line=dict(color="#667eea", width=3),
                marker=dict(size=6),
            )
        )

        # 初期資金ライン
        fig.add_hline(y=pt.initial_capital, line_dash="dash", line_color="gray", annotation_text="初期資金")

        fig.update_layout(
            height=400,
            hovermode="x unified",
            showlegend=False,
            plot_bgcolor="white",
            xaxis=dict(title="日付", showgrid=True, gridcolor="#f0f0f0"),
            yaxis=dict(title="資産 (円)", showgrid=True, gridcolor="#f0f0f0"),
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("まだデータがありません")

    st.markdown("---")

    # 取引履歴
    st.subheader("📝 最近の取引")

    history = pt.get_trade_history()

    if not history.empty:
        recent = history.tail(10).sort_values("date", ascending=False)

        for idx, trade in recent.iterrows():
            date = pd.to_datetime(trade["date"]).strftime("%m/%d %H:%M")
            ticker = trade["ticker"]
            action = trade["action"]
            quantity = trade.get("quantity", 0)
            price = trade.get("price", 0)
            realized_pnl = trade.get("realized_pnl", 0)

            if action == "BUY":
                emoji = "🟢"
                action_text = "購入"
            else:
                emoji = "🔴"
                action_text = "売却"

            pnl_text = ""
            if action == "SELL" and realized_pnl != 0:
                pnl_text = f" ({format_currency(realized_pnl, show_sign=True)})"

            st.markdown(
                f"""
            <div style="padding: 1rem; margin: 0.5rem 0; background: #f9fafb; border-radius: 8px; color: #1f2937;">
                {emoji} {date} - {ticker} {action_text} {quantity}株 @ {format_currency(price)}{pnl_text}
            </div>
            """,
                unsafe_allow_html=True,
            )
    else:
        st.info("取引履歴がありません")


show_detail_page()
