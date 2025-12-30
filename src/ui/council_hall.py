import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any


def render_council_hall(council_agent, ticker: str, data: Dict[str, Any]):
    st.header(f"🏛️ The Council Hall: {ticker}")
    st.caption("100 Autonomous Avatars Debating in Real-Time")


# 1. Get Council Data
# In a real flow, this might come from 'data' context, or we invoke it here if missing
if "council_results" in data and data["council_results"]:
    results = data["council_results"]
    #     else:
    # Fallback invocation for demo/direct usage
    st.info("Summoning the Council...")
    results = council_agent.hold_grand_assembly(ticker, data)
    all_votes = results.get("all_votes", [])
    #     if not all_votes:
    st.error("Council is silent. (No votes returned)")
#         return
# 2. Prepare Data for Visualization (10x10 Grid)
df = pd.DataFrame(all_votes)
# Add Grid Coordinates
df["x"] = df.index % 10
df["y"] = df.index // 10
# 3. Metrics (Hive Mind)
avg_score = results.get("avg_score", 50)
clusters = results.get("clusters", {})
#         col1, col2, col3, col4 = st.columns(4)
#     with col1:
#         st.metric("Hive Mind Consensus", f"{avg_score:.1f}/100")
#     with col2:
#         st.metric("🐂 Bulls", clusters.get("Bulls", 0))
#     with col3:
#         st.metric("🐻 Bears", clusters.get("Bears", 0))
#     with col4:
#         st.metric("😐 Neutral", clusters.get("Neutral", 0))
# 4. Visualization (10x10 Avatar Grid)
# Color scale: Red (0) -> Gray (50) -> Green (100)
#     fig = px.scatter(
#         df,
#         x="x",
#         y="y",
#         color="score",
#         symbol="stance",
#         symbol_map={"BULL": "triangle-up", "BEAR": "triangle-down", "NEUTRAL": "circle"},
#         size_max=20,
#         color_continuous_scale=["red", "gray", "lime"],
#         range_color=[0, 100],
#         hover_name="name",
#         hover_data={"trait": True, "score": True, "quote": True, "x": False, "y": False},
#         title="Avatar Grid State (10x10)",
#     )
#         fig.update_traces(marker=dict(size=25, line=dict(width=1, color="DarkSlateGrey")))
#     fig.update_layout(
#         xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
#         yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, autorange="reversed"),  # Top-down
#         plot_bgcolor="rgba(0,0,0,0)",
#         height=500,
#         width=500,
#     )
#         c1, c2 = st.columns([2, 1])
#         with c1:
#             st.plotly_chart(fig, use_container_width=True)
#         with c2:
#             st.subheader("🗣️ Voices of the Council")
# Filter Logic
filter_opt = st.radio("Filter Voices", ["All", "Bulls", "Bears"], horizontal=True)
filtered_df = df
#         if filter_opt == "Bulls":
#             filtered_df = df[df["score"] > 60]
#         elif filter_opt == "Bears":
#             filtered_df = df[df["score"] < 40]
# Display top 5 loudest in category
for i, row in filtered_df.head(5).iterrows():
    with st.chat_message(
        "user" if row["score"] > 50 else "assistant"
    ):  # Just to alternate icons/colors
        st.write(f"**{row['name']}**: {row['quote']}")
        st.caption(f"Score: {row['score']:.1f}")
#         st.divider()
# Raw Data Expander
with st.expander("📂 Access Full Council Ledger"):
    st.dataframe(df)
