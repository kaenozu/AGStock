import streamlit as st
from src.evolution.briefing_generator import BriefingGenerator
from datetime import datetime


def render_briefing_panel():
    #     """
    #         Renders the AI Private Banking Briefing panel on the dashboard.
    #             generator = BriefingGenerator()
    #         data = generator.get_last_briefing()
    #             st.markdown("""" 🏛️ AI Private Banking Briefing")
    with st.container():
        if data.get("timestamp"):
            ts = datetime.fromisoformat(data["timestamp"]).strftime("%Y/%m/%d %H:%M")
        st.caption(f"Last updated: {ts}")
        st.markdown(data["content"])
        st.divider()

    #             st.markdown(""""# ✨ 超越的助言 (Transcendent Advice)")
    #             st.info(
    #                 "AGStock は現在、125.5/100 の『超越的昇華』状態にあります。現実の指標だけでなく、並行世界の歴史とブロックチェーンに刻まれた魂が、あなたの資産を多層的に守護しています。"
    #             )
    #                 if st.button("🔄 今すぐ最新の報告を生成"):
    pass
    #                     with st.spinner("AIバンカーが最新のデータを分析中..."):
    pass
    #                         new_content = generator.generate_briefing()
    #                     st.rerun()
    #     # --- Phase 14: Voice Integration ---
    #             try:
    pass
    #                 from src.core.voice import VoiceEngine
    #                     if st.button("🔊 報告を読み上げ (Voice)"):
    pass
    #                         voice = VoiceEngine()
    #     # Clean markdown slightly for TTS? For now direct feed.
    #                     audio_path = voice.speak(data["content"])
    #                     if audio_path:
    pass
    #                         st.audio(audio_path, format="audio/mp3")
    #                 except Exception:
    pass
    #                     pass
    #          -----------------------------------
    #     if __name__ == "__main__":
    pass


#         render_briefing_panel()
#
#     """  # Force Balanced
