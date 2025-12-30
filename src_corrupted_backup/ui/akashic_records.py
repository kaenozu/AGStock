import streamlit as st
import pandas as pd
from src.db.manager import DatabaseManager
from src.ui.styles import DS
def render_akashic_records():
#     """
#     Renders the Akashic Records (Database Viewer) UI.
#         st.markdown(
#         f"""
    <div style="margin-bottom: 2rem;">
        <h1 style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 2rem; margin-right: 0.5rem;">📚</span> Akashic Records
        </h1>
        <div style="color: {DS.COLORS['text_secondary']}; font-size: 1.1rem;">
            Infinite archive of trading history, council debates, and market observations.
        </div>
    </div>
#     """,
#         unsafe_allow_html=True,
#     )
#         db = DatabaseManager()
#         tab1, tab2, tab3 = st.tabs(["📜 Trade History", "🔬 Market Scans", "🏛️ Council Archives"])
#         with tab1:
    pass
#             st.subheader("Trade History")
#         try:
    pass
#             query = "SELECT * FROM trade_logs ORDER BY timestamp DESC LIMIT 100"
#             df_trades = pd.read_sql(query, db.db.bind)
#                 if not df_trades.empty:
    pass
#                     st.dataframe(
#                     df_trades,
#                     use_container_width=True,
#                     column_config={
#                         "timestamp": st.column_config.DatetimeColumn("Time", format="D MMM, HH:mm"),
#                         "price": st.column_config.NumberColumn("Price", format="¥%.2f"),
#                         "pnl": st.column_config.NumberColumn("PnL", format="¥%.2f"),
#                     },
#                 )
#             else:
    pass
#                 st.info("No trade history found in the records yet.")
#         except Exception as e:
    pass
#             st.error(f"Error fetching trade history: {e}")
#         with tab2:
    pass
#             st.subheader("Market Scan Logs")
#         try:
    pass
#             query = "SELECT * FROM market_scans ORDER BY timestamp DESC LIMIT 200"
#             df_scans = pd.read_sql(query, db.db.bind)
#                 if not df_scans.empty:
    pass
#                     # Colorize signal
# """
def highlight_signal(val):
    pass
#                     """
#                     Highlight Signal.
#                         Args:
    pass
#                             val: Description of val
#                         Returns:
    pass
#                             Description of return value
#                                         color = (
#                         DS.COLORS["success"]
#                         if val == 1
#                         else DS.COLORS["danger"] if val == -1 else DS.COLORS["text_secondary"]
#                     )
#                     return f"color: {color}"
#                     st.dataframe(
#                     df_scans,
#                     use_container_width=True,
#                     column_config={
#                         "timestamp": st.column_config.DatetimeColumn("Time", format="D MMM, HH:mm"),
#                     },
#                 )
#             else:
    pass
#                 st.info("No market scans recorded yet.")
#         except Exception as e:
    pass
#             st.error(f"Error fetching market scans: {e}")
#         with tab3:
    pass
#             st.subheader("Council of Avatars Archives")
#         try:
    pass
#             # Join with distinct ticker/timestamp to show summary?
# # For now just raw dump of recent votes
#             query = "SELECT * FROM council_votes ORDER BY timestamp DESC LIMIT 500"
#             df_votes = pd.read_sql(query, db.db.bind)
#                 if not df_votes.empty:
    pass
#                     ticker_filter = st.selectbox("Filter by Ticker", ["ALL"] + list(df_votes["ticker"].unique()))
#                     if ticker_filter != "ALL":
    pass
#                         df_votes = df_votes[df_votes["ticker"] == ticker_filter]
#                     st.dataframe(df_votes, use_container_width=True)
#             else:
    pass
#                 st.info("The Council has not yet spoken for the records.")
#         except Exception as e:
    pass
#             st.error(f"Error fetching council archives: {e}")
#         db.close()
# """
