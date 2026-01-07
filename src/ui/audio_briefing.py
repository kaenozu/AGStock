
import streamlit as st
import os
import json
from gtts import gTTS
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def render_audio_briefing():
    st.header("🎙️ AI Daily Briefing (Daily Voice)")
    st.markdown("今日の市場状況とAIの推奨戦略を音声で要約します。")

    if st.button("🔊 ブリーフィングを生成する"):
        with st.spinner("AIがスクリプトを作成し、音声を生成中..."):
            try:
                # 1. Gather Context
                # For demo, we use scan results if available
                context = "市場は現在安定しています。"
                if os.path.exists("scan_results.json"):
                    with open("scan_results.json", "r", encoding="utf-8") as f:
                        data = json.load(f)
                        results = data.get("results", [])
                        buys = [r['Ticker'] for r in results if r['Action'] == 'BUY']
                        if buys:
                            context = f"本日の買い推奨銘柄は {', '.join(buys[:3])} など計 {len(buys)} 件です。"
                
                # 2. Generate Script via Gemini
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    st.error("APIキーが見つかりません。")
                    return

                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                あなたはAGStockのAIアナリストです。
                以下の情報を元に、投資家向けの朝の音声ブリーフィング原稿（日本語）を作成してください。
                親しみやすく、かつプロフェッショナルな口調で、1分程度で読み上げられる分量にしてください。
                
                情報: {context}
                """
                
                response = model.generate_content(prompt)
                script = response.text
                
                st.subheader("📝 ブリーフィング原稿")
                st.write(script)
                
                # 3. Generate Audio via gTTS
                tts = gTTS(text=script, lang='ja')
                audio_path = "data/briefing.mp3"
                if not os.path.exists("data"): os.makedirs("data")
                tts.save(audio_path)
                
                # 4. Play Audio
                st.audio(audio_path, format="audio/mp3")
                st.success("ブリーフィングの生成が完了しました。")
                
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    render_audio_briefing()
