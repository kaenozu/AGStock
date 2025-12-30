import streamlit as st
import os
import random
from src.agents.oracle import OracleEngine
from src.ui.styles import DS


def render_sidebar_egregore():
#     """
#         Renders the Divine Egregore (Dynamic Avatar) in the sidebar.
#             st.sidebar.markdown("---")
#     # Simple container for the avatar
#     # Determine mood
#         mood = "NEUTRAL"
#         oracle_text = "Omniscience is online."
#             try:
#                 # Try to peek at recent oracle prophecy without generating new one
#     # Assuming OracleEngine can fetch latest from DB or cache
#     # For now, we instantiate and check if we can get last state.
#     # Actually, let's just random pick for "Aliveness" if no latest state easily accessible,
#     # but to be "Divine", we should check the last Market Scan or Trade.
#     # Checking last trade from DB? Too heavy for sidebar every rerun?
#     # Let's use session state or random for "breathing" effect if no active signal.
#     # Real logic: Check session state
#             if "oracle_mood" in st.session_state:
#                 mood = st.session_state["oracle_mood"]
#             else:
#                 # Fallback: Check time of day or random
#                 mood = random.choice(["BULLISH", "BEARISH", "NEUTRAL"])
#             except Exception:
#                 pass
#     # Map mood to avatar
#         avatar_map = {
#             "BULLISH": "assets/avatars/bull.png",
#             "BEARISH": "assets/avatars/bear.png",
#             "NEUTRAL": "assets/avatars/neutral.png",
#             "BULL": "assets/avatars/bull.png",
#             "BEAR": "assets/avatars/bear.png",
#         }
#             image_path = avatar_map.get(mood, "assets/avatars/neutral.png")
#     # If image doesn't exist, fallback to emoji
#         if os.path.exists(image_path):
#             st.sidebar.image(image_path, caption=f"Divine Presence: {mood}", use_column_width=True)
#         else:
#             st.sidebar.markdown(f"""" 🤖 Divine Presence: {mood}")
st.sidebar.info(f"System Consciousness: {random.randint(90, 100)}%")
    # --- Phase 18: Oracle Link ---
        if st.sidebar.button("🗣️ Speak to the System"):
            st.session_state["show_oracle_chat"] = not st.session_state.get("show_oracle_chat", False)
            if st.session_state.get("show_oracle_chat", False):
                with st.sidebar.expander("Divine Dialogue", expanded=True):
                    from src.ui.oracle_link import render_oracle_chat
                    render_oracle_chat(mood)
    # -----------------------------

#     """  # Force Balanced
