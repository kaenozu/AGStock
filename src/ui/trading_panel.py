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
    st.header("繝壹・繝代・繝医Ξ繝ｼ繝・ぅ繝ｳ繧ｰ (莉ｮ諠ｳ螢ｲ雋ｷ)")
    st.write("繝ｪ繧｢繝ｫ繧ｿ繧､繝縺ｮ譬ｪ萓｡繝・・繧ｿ繧堤畑縺・※縲∽ｻｮ諠ｳ雉・≡縺ｧ繝医Ξ繝ｼ繝峨・邱ｴ鄙偵′縺ｧ縺阪∪縺吶・)

    pt = PaperTrader()

    # Refresh Button
    if st.button("譛譁ｰ萓｡譬ｼ縺ｧ隧穂ｾ｡鬘阪ｒ譖ｴ譁ｰ"):
        with st.spinner("迴ｾ蝨ｨ蛟､繧呈峩譁ｰ荳ｭ..."):
            pt.update_daily_equity()
            st.success("譖ｴ譁ｰ螳御ｺ・)

    # Dashboard
    balance = pt.get_current_balance()

    col1, col2, col3 = st.columns(3)
    col1.metric("迴ｾ驥第ｮ矩ｫ・(Cash)", format_currency(balance['cash']))
    col2.metric("邱剰ｳ・肇 (Total Equity)", format_currency(balance['total_equity']))

    pnl = balance['total_equity'] - pt.initial_capital
    pnl_pct = (pnl / pt.initial_capital) * 100
    col3.metric("蜈ｨ譛滄俣謳咲寢", format_currency(pnl), delta=f"{pnl_pct:+.1f}%")

    st.divider()

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("迴ｾ蝨ｨ縺ｮ菫晄怏繝昴ず繧ｷ繝ｧ繝ｳ")
        positions = pt.get_positions()
        if not positions.empty:
            # Format for display
            pos_display = positions.copy()
            
            # Add Company Name
            pos_display['name'] = pos_display['ticker'].map(lambda x: TICKER_NAMES.get(x, x))

            # Calculate metrics
            if 'current_price' in pos_display.columns:
                pos_display['unrealized_pnl_pct'] = (pos_display['current_price'] - pos_display['entry_price']) / pos_display['entry_price']
            else:
                pos_display['unrealized_pnl_pct'] = 0.0
                
            pos_display['acquisition_cost'] = pos_display['entry_price'] * pos_display['quantity']
            
            # Select and Reorder columns - Market Value is usually returned by get_positions as 'market_value'
            # If not, calculate it
            if 'market_value' not in pos_display.columns:
                 pos_display['market_value'] = pos_display['current_price'] * pos_display['quantity']

            target_cols = ['name', 'ticker', 'quantity', 'entry_price', 'current_price', 'acquisition_cost', 'market_value', 'unrealized_pnl', 'unrealized_pnl_pct']
            existing_cols = [c for c in target_cols if c in pos_display.columns]
            pos_display = pos_display[existing_cols]

            # Rename for display
            # Map robustly based on what exists
            col_map = {
                'name': '驫俶氛蜷・, 'ticker': '繧ｳ繝ｼ繝・, 'quantity': '菫晄怏謨ｰ驥・, 
                'entry_price': '蜿門ｾ怜腰萓｡', 'current_price': '迴ｾ蝨ｨ蛟､', 
                'acquisition_cost': '蜿門ｾ鈴≡鬘・, 'market_value': '譎ゆｾ｡隧穂ｾ｡鬘・,
                'unrealized_pnl': '隧穂ｾ｡謳咲寢', 'unrealized_pnl_pct': '謳咲寢邇・
            }
            pos_display = pos_display.rename(columns=col_map)

            # Apply styling
            st.dataframe(pos_display.style.format({
                '蜿門ｾ怜腰萓｡': 'ﾂ･{:,.0f}',
                '迴ｾ蝨ｨ蛟､': 'ﾂ･{:,.0f}',
                '蜿門ｾ鈴≡鬘・: 'ﾂ･{:,.0f}',
                '譎ゆｾ｡隧穂ｾ｡鬘・: 'ﾂ･{:,.0f}',
                '隧穂ｾ｡謳咲寢': 'ﾂ･{:,.0f}',
                '謳咲寢邇・: '{:.1%}'
            }), use_container_width=True)
        else:
            st.info("迴ｾ蝨ｨ菫晄怏縺励※縺・ｋ繝昴ず繧ｷ繝ｧ繝ｳ縺ｯ縺ゅｊ縺ｾ縺帙ｓ縲・)

    with col_right:
        st.subheader("謇句虚豕ｨ譁・)
        with st.form("order_form"):
            ticker_input = st.text_input("驫俶氛繧ｳ繝ｼ繝・(萓・ 7203.T)")
            action_input = st.selectbox("螢ｲ雋ｷ", ["BUY", "SELL"])
            # Unit size logic from sidebar config
            trading_unit_step = sidebar_config.get("trading_unit", 100)
            
            qty_input = st.number_input("謨ｰ驥・, min_value=1, step=trading_unit_step, value=trading_unit_step)

            submitted = st.form_submit_button("豕ｨ譁・ｮ溯｡・)
            if submitted and ticker_input:
                # Get current price
                price_data = fetch_stock_data([ticker_input], period="1d")
                if ticker_input in price_data and not price_data[ticker_input].empty:
                    current_price = price_data[ticker_input]['Close'].iloc[-1]

                    if pt.execute_trade(ticker_input, action_input, qty_input, current_price, reason="Manual"):
                        st.success(f"{action_input}豕ｨ譁・′螳御ｺ・＠縺ｾ縺励◆: {ticker_input} @ {current_price}")
                        st.experimental_rerun()
                    else:
                        st.error("豕ｨ譁・↓螟ｱ謨励＠縺ｾ縺励◆・郁ｳ・≡荳崎ｶｳ縺ｾ縺溘・菫晄怏譬ｪ荳崎ｶｳ・峨・)
                else:
                    st.error("萓｡譬ｼ繝・・繧ｿ縺ｮ蜿門ｾ励↓螟ｱ謨励＠縺ｾ縺励◆縲・)

    st.divider()
    st.subheader("蜿門ｼ募ｱ･豁ｴ")
    history = pt.get_trade_history()
    if not history.empty:
        st.dataframe(history, use_container_width=True)
    else:
        st.info("蜿門ｼ募ｱ･豁ｴ縺ｯ縺ゅｊ縺ｾ縺帙ｓ縲・)
    
    # --- Equity Curve Visualization (Added from previous app.py logic) ---
    st.divider()
    st.subheader("雉・肇謗ｨ遘ｻ")
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
            annotation_text="蛻晄悄雉・≡"
        )
        fig_equity.update_layout(
            title="雉・肇謗ｨ遘ｻ・・aper Trading・・,
            xaxis_title="譌･莉・,
            yaxis_title="雉・肇 (蜀・",
            hovermode='x unified'
        )
        st.plotly_chart(fig_equity, use_container_width=True)
    else:
        st.info("縺ｾ縺謗ｨ遘ｻ繝・・繧ｿ縺後≠繧翫∪縺帙ｓ縲・)

    # --- Alert Config (Placeholder) ---
    st.divider()
    st.subheader("粕 繧｢繝ｩ繝ｼ繝郁ｨｭ螳・)
    st.write("萓｡譬ｼ螟牙虚繧｢繝ｩ繝ｼ繝医ｒ險ｭ螳壹〒縺阪∪縺呻ｼ亥ｰ・擂螳溯｣・ｺ亥ｮ夲ｼ峨・)
    
    # Use selected market ticker list for suggestion
    selected_market = sidebar_config.get("selected_market", "Japan")
    markets_list = MARKETS.get(selected_market, MARKETS["Japan"])

    alert_ticker = st.selectbox(
        "逶｣隕悶☆繧矩釜譟・,
        options=markets_list[:10],
        format_func=lambda x: f"{x} - {TICKER_NAMES.get(x, '')}"
    )

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        alert_type = st.selectbox("繧｢繝ｩ繝ｼ繝医ち繧､繝・, ["萓｡譬ｼ荳頑・", "萓｡譬ｼ荳玖誠"])
    with col_a2:
        threshold = st.number_input("髢ｾ蛟､ (%)", min_value=1.0, max_value=50.0, value=5.0, step=0.5)

    if st.button("繧｢繝ｩ繝ｼ繝医ｒ險ｭ螳・):
        st.success(f"笨・{alert_ticker} 縺ｮ{alert_type}繧｢繝ｩ繝ｼ繝茨ｼ・threshold}%・峨ｒ險ｭ螳壹＠縺ｾ縺励◆・医ョ繝｢・・)
