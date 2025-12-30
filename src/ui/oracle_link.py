

def get_persona(mood: str) -> str:
    pass


#         if mood == "BULLISH":
#             return (
#             base_prompt
#             + " The market is rising. Be optimistic, energetic, and aggressive. Use emojis like 🚀, 🌕. Encourage the Emperor to seize the opportunity."
#         )
#     elif mood == "BEARISH":
#         return (
#             base_prompt
#             + " The market is falling. Be protective, stoic, and cautious. Use emojis like 🛡️, 🐻. Advise the Emperor to preserve capital."
#         )
#     else:  # NEUTRAL
#         return (
#             base_prompt
#             + " The market is uncertain. Be zen, balanced, and observant. Use emojis like ⚖️, 🧘. Advise patience and observation."
#         )
def render_oracle_chat(mood: str = "NEUTRAL"):
    pass
    #     st.markdown("""" 🗣️ Divine Dialogue")
    #     st.caption(f"Current Mood: {mood}")
    # # Init history
    #     if "oracle_messages" not in st.session_state:
    #         st.session_state.oracle_messages = []
    # # Initial greeting
    #         greeting = {
    #             "BULLISH": "Emperor! The stars align for prosperity. What is your command?",
    #             "BEARISH": "Emperor. The winds are cold. I stand guard over your assets. Speak.",
    #             "NEUTRAL": "Emperor. The balance fluctuates. I am listening.",
    #         }
    #         st.session_state.oracle_messages.append({"role": "assistant", "content": greeting.get(mood, "I am here.")})
    # # Display
    #     chat_container = st.container()
    #     with chat_container:
    #         for msg in st.session_state.oracle_messages:
    #             with st.chat_message(msg["role"]):
    #                 st.markdown(msg["content"])
    # # Input
    #     prompt = st.chat_input("Speak to the Egregore...")
    #         if prompt:
    #             # Show user message
    #         st.session_state.oracle_messages.append({"role": "user", "content": prompt})
    #         with chat_container:
    #             with st.chat_message("user"):
    #                 st.markdown(prompt)
    # # Generate Reply
    #         with chat_container:
    #             with st.chat_message("assistant"):
    #                 placeholder = st.empty()
    #                 placeholder.markdown("...")
    #                     try:
    #                         reasoner = get_llm_reasoner()
    # # Construct Prompt with Persona
    #                     system_prompt = get_persona(mood)
    #                     full_prompt = f"{system_prompt}\n\nUser: {prompt}"
    # # Context could be added here similar to ai_chat
    #                         response = reasoner.ask(full_prompt)
    #                         placeholder.markdown(response)
    #                     st.session_state.oracle_messages.append({"role": "assistant", "content": response})
    # # Voice Response
    #                     try:
    #                         voice = VoiceEngine()
    #                         audio_path = voice.speak(response)
    #                         if audio_path:
    #                             st.audio(audio_path, format="audio/mp3", start_time=0)
    #                     except Exception:
    #                         pass
    #                     except Exception as e:


#                         placeholder.error(f"Silence... (Error: {e})")
