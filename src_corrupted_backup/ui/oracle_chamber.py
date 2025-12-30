import streamlit as st
from src.agents.oracle import OracleEngine
from src.ui.styles import DS
def render_oracle_chamber():
#         """
#         st.markdown(
#         f"""
    <div style="margin-bottom: 2rem;">
        <h1 style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 2rem; margin-right: 0.5rem;">🔮</span> The Oracle Chamber
        </h1>
        <div style="color: {DS.COLORS['text_secondary']}; font-size: 1.1rem;">
            Daily narrative generated from the collective wisdom of the Akashic Records.
        </div>
    </div>
#     """,
#         unsafe_allow_html=True,
#     )
#         if st.button("Invoke the Oracle (Generate Prophecy)"):
#             with st.spinner("The Oracle connects to the Akashic Records..."):
#                 oracle = OracleEngine()
#             prophecy = oracle.generate_prophecy()
# # Styling based on mood
#             bg_color = "rgba(40, 40, 40, 0.5)"
#             border_color = DS.COLORS["border"]
#             icon = "⚖️"
#                 if prophecy["mood"] == "BULLISH":
#                     border_color = DS.COLORS["success"]
#                 bg_color = "rgba(20, 80, 40, 0.2)"
#                 icon = "🐂"
#             elif prophecy["mood"] == "BEARISH":
#                 border_color = DS.COLORS["danger"]
#                 bg_color = "rgba(80, 20, 20, 0.2)"
#                 icon = "🐻"
#                 st.markdown(
#                 f"""
            <div style="
                background: {bg_color};
                border: 2px solid {border_color};
                border-radius: 12px;
                padding: 2rem;
                margin-top: 1rem;
                text-align: center;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
                <h2 style="color: {DS.COLORS['text']}; margin-bottom: 1rem;">{prophecy['title']}</h2>
                <div style="
                    font-size: 1.2rem; 
                    line-height: 1.8; 
                    color: {DS.COLORS['text_secondary']};
                    font-style: italic;
                    white-space: pre-wrap;
                ">{prophecy['body']}</div>
            </div>
#             """,
#                 unsafe_allow_html=True,
#             )
# # --- Phase 11: The Voice of God ---
#             try:
    pass
#                 from src.core.voice import VoiceEngine
#                     voice = VoiceEngine()
#                 text_to_speak = f"{prophecy['title']}... {prophecy['body']}"
#                 audio_path = voice.speak(text_to_speak)
#                 if audio_path:
    pass
#                     st.audio(audio_path, format="audio/mp3")
#             except Exception as e:
    pass
#                 st.warning(f"Voice generation failed: {e}")
# # ----------------------------------
# # --- Phase 12: Divine Messenger ---
#             if st.button("📡 Broadcast to World (Discord/LINE)"):
    pass
#                 from src.core.messenger import MessengerService
#                     messenger = MessengerService()
#                 messenger.broadcast_prophecy(prophecy)
#                 st.success("The prophecy has been revealed to the world.")
# # ----------------------------------
#         else:
    pass
#             st.info("Press the button to summon the Oracle.")
# 
# 
