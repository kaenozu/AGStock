import streamlit as st
import os
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

from src.utils.voice_oracle import VoiceOracle

load_dotenv()

# 設定
st.set_page_config(page_title="AI投資アシスタント", page_icon="🤖", layout="wide")

class GeminiAssistant:
# ... (rest of class)
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None

    def get_response(self, prompt, history):
        if not self.model:
            return "APIキーが設定されていません。.envファイルを確認してください。"
        
        chat = self.model.start_chat(history=history)
        
        system_instruction = """
        あなたはAGStock AI投資アシスタントです。
        ユーザーの投資に関する質問に答え、ポートフォリオ分析や市場の見通しを提供します。
        専門的でありながら、親しみやすく分かりやすい日本語で回答してください。
        必要に応じて、リスク管理の重要性についても触れてください。
        """
        
        full_prompt = f"{system_instruction}\n\nUser: {prompt}"
        response = chat.send_message(full_prompt)
        return response.text

def main():
    st.title("🤖 AI投資アシスタント (Gemini 2.0)")
    st.markdown("次世代AIがあなたの投資をサポートします。")

    assistant = GeminiAssistant()
    oracle = VoiceOracle()

    # サイドバー
    with st.sidebar:
        st.subheader("🛠️ 設定")
        voice_enabled = st.toggle("音声出力を有効にする", value=True)
        if st.button("会話履歴をクリア"):
            st.session_state.gemini_messages = []
            st.rerun()
        
        st.divider()
        st.info("このアシスタントは Gemini 2.0 Flash を使用してリアルタイムに投資のアドバイスを提供します。")

    if "gemini_messages" not in st.session_state:
        st.session_state.gemini_messages = []

    # 会話履歴の表示
    for message in st.session_state.gemini_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ユーザー入力
    if prompt := st.chat_input("投資について相談する..."):
        # ユーザーメッセージを表示
        st.session_state.gemini_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI応答を生成
        with st.chat_message("assistant"):
            # history transformation for Gemini SDK
            history = []
            for m in st.session_state.gemini_messages[:-1]:
                role = "user" if m["role"] == "user" else "model"
                history.append({"role": role, "parts": [m["content"]]})
            
            try:
                response = assistant.get_response(prompt, history)
                st.markdown(response)
                st.session_state.gemini_messages.append({"role": "assistant", "content": response})
                
                # 音声出力
                if voice_enabled:
                    oracle.speak(response)
            except Exception as e:
                st.error(f"Error: {e}")

if __name__ == "__main__":
    main()