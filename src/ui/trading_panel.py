"""
Trading Panel UI Module
Handles the Paper Trading interface (manual trading, positions, history).
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.paper_trader import PaperTrader
from src.data_loader import fetch_stock_data
from src.formatters import format_currency
from src.constants import MARKETS, TICKER_NAMES

def render_trading_panel(sidebar_config):
    """
    Renders the Paper Trading tab content.
    """
    st.header("ペーパートレーディング (仮想売買)")
    st.write("リアルタイムの株価データを用いて、仮想資金でトレードの練習ができます。")

    pt = PaperTrader()

    # Refresh Button
    if st.button("最新価格で評価額を更新"):
        with st.spinner("現在値を更新中..."):
            pt.update_daily_equity()
            st.success("更新完了")

    # Dashboard
    balance = pt.get_current_balance()

    col1, col2, col3 = st.columns(3)
    col1.metric("現金残高 (Cash)", format_currency(balance['cash']))
    col2.metric("総資産 (Total Equity)", format_currency(balance['total_equity']))

    pnl = balance['total_equity'] - pt.initial_capital
    pnl_pct = (pnl / pt.initial_capital) * 100
    col3.metric("全期間損益", format_currency(pnl), delta=f"{pnl_pct:+.1f}%")

    st.divider()

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("現在の保有ポジション")
        positions = pt.get_positions()
        if not positions.empty:
            # Format for display
            pos_display = positions.copy()
            # Calculate PnL pct if 'current_price' is available (it should be if update_daily_equity runs, 
            # or minimally from last update. PaperTrader.get_positions usually returns current_price)
            if 'current_price' in pos_display.columns:
                pos_display['unrealized_pnl_pct'] = (pos_display['current_price'] - pos_display['entry_price']) / pos_display['entry_price']
            else:
                # Fallback if current price missing
                pos_display['unrealized_pnl_pct'] = 0.0

            # Apply styling
            st.dataframe(pos_display.style.format({
                'entry_price': '¥{:,.0f}',
                'current_price': '¥{:,.0f}',
                'unrealized_pnl': '¥{:,.0f}',
                'unrealized_pnl_pct': '{:.1%}'
            }), use_container_width=True)
        else:
            st.info("現在保有しているポジションはありません。")

    with col_right:
        st.subheader("手動注文")
        with st.form("order_form"):
            ticker_input = st.text_input("銘柄コード (例: 7203.T)")
            action_input = st.selectbox("売買", ["BUY", "SELL"])
            # Unit size logic from sidebar config
            trading_unit_step = sidebar_config.get("trading_unit", 100)
            
            qty_input = st.number_input("数量", min_value=1, step=trading_unit_step, value=trading_unit_step)

            submitted = st.form_submit_button("注文実行")
            if submitted and ticker_input:
                # Get current price
                price_data = fetch_stock_data([ticker_input], period="1d")
                if ticker_input in price_data and not price_data[ticker_input].empty:
                    current_price = price_data[ticker_input]['Close'].iloc[-1]

                    if pt.execute_trade(ticker_input, action_input, qty_input, current_price, reason="Manual"):
                        st.success(f"{action_input}注文が完了しました: {ticker_input} @ {current_price}")
                        st.rerun()
                    else:
                        st.error("注文に失敗しました（資金不足または保有株不足）。")
                else:
                    st.error("価格データの取得に失敗しました。")

    st.divider()
    st.subheader("取引履歴")
    history = pt.get_trade_history()
    if not history.empty:
        st.dataframe(history, use_container_width=True)
    else:
        st.info("取引履歴はありません。")
    
    # --- Equity Curve Visualization (Added from previous app.py logic) ---
    st.divider()
    st.subheader("資産推移")
    equity_history = pt.get_equity_history()
    if not equity_history.empty:
        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(
            x=equity_history['date'],
            y=equity_history['total_equity'],
            mode='lines',
            name='Total Equity',
            line=dict(color='gold', width=2)
        ))
        fig_equity.add_hline(
            y=pt.initial_capital,
            line_dash="dash",
            line_color="gray",
            annotation_text="初期資金"
        )
        fig_equity.update_layout(
            title="資産推移（Paper Trading）",
            xaxis_title="日付",
            yaxis_title="資産 (円)",
            hovermode='x unified'
        )
        st.plotly_chart(fig_equity, use_container_width=True)
    else:
        st.info("まだ推移データがありません。")

    # --- Alert Config (Placeholder) ---
    st.divider()
    st.subheader("🔔 アラート設定")
    st.write("価格変動アラートを設定できます（将来実装予定）。")
    
    # Use selected market ticker list for suggestion
    selected_market = sidebar_config.get("selected_market", "Japan")
    markets_list = MARKETS.get(selected_market, MARKETS["Japan"])

    alert_ticker = st.selectbox(
        "監視する銘柄",
        options=markets_list[:10],
        format_func=lambda x: f"{x} - {TICKER_NAMES.get(x, '')}"
    )

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        alert_type = st.selectbox("アラートタイプ", ["価格上昇", "価格下落"])
    with col_a2:
        threshold = st.number_input("閾値 (%)", min_value=1.0, max_value=50.0, value=5.0, step=0.5)

    if st.button("アラートを設定"):
        st.success(f"✓ {alert_ticker} の{alert_type}アラート（{threshold}%）を設定しました（デモ）")
