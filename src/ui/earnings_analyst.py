import pandas as pd
import streamlit as st
import os

from src.analysis.pdf_reader import EarningsAnalyzer, PDFExtractor
from src.analysis.multimodal_analyzer import MultimodalAnalyzer
from src.rag.pdf_loader import PDFLoader


def render_earnings_analyst():
    st.header("🤖 マルチモーダル決算分析 (Vision & Audio)")
    st.markdown("決算短信(PDF)に加え、説明会の音声や動画もAIが分析します。")

    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_pdf = st.file_uploader("決算PDFをアップロード", type="pdf")
    
    with col2:
        uploaded_media = st.file_uploader("音声・動画をアップロード (MP3, MP4)", type=["mp3", "mp4"])

    if uploaded_pdf or uploaded_media:
        if st.button("AIマルチモーダル分析を開始"):
            with st.spinner("AIが決算資料とメディアを統合分析中..."):
                try:
                    results = {}
                    transcript = ""
                    
                    # 1. PDF Analysis
                    if uploaded_pdf:
                        text = PDFExtractor.extract_text(uploaded_pdf)
                        transcript = text # Use text as transcript for simplicity if no audio
                        pdf_analyzer = EarningsAnalyzer()
                        pdf_res = pdf_analyzer.analyze_report(text)
                        results["pdf"] = pdf_res
                        st.info("PDF分析完了")

                    # 2. Multimodal Analysis (Gemini)
                    analyzer = MultimodalAnalyzer()
                    
                    # Save media temporarily for processing
                    audio_path = None
                    video_path = None
                    
                    if uploaded_media:
                        temp_path = f"data/{uploaded_media.name}"
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_media.getbuffer())
                            
                        if uploaded_media.type == "audio/mpeg":
                            audio_path = temp_path
                        else:
                            video_path = temp_path
                    
                    mm_res = analyzer.analyze_earnings_presentation(
                        video_path=video_path,
                        audio_path=audio_path,
                        transcript=transcript if transcript else None
                    )
                    
                    # Cleanup
                    if audio_path and os.path.exists(audio_path): os.remove(audio_path)
                    if video_path and os.path.exists(video_path): os.remove(video_path)

                    # 3. Display Integrated Result
                    st.divider()
                    st.subheader("📊 統合分析レポート")
                    
                    m_col1, m_col2, m_col3 = st.columns(3)
                    sentiment = mm_res.get("overall_sentiment", 0.5)
                    m_col1.metric("総合感情スコア", f"{sentiment:.2f}")
                    m_col2.metric("信頼度", f"{mm_res.get('confidence_score', 0.0):.2f}")
                    
                    sentiment_label = "ポジティブ" if sentiment > 0.6 else "ネガティブ" if sentiment < 0.4 else "ニュートラル"
                    m_col3.info(f"判定: {sentiment_label}")

                    if mm_res.get("insights"):
                        st.markdown("#### 💡 AIインサイト")
                        for insight in mm_res["insights"]:
                            st.write(f"- {insight}")
                    
                    if "pdf" in results:
                        with st.expander("PDF詳細分析を表示"):
                            st.markdown(results["pdf"]["raw_analysis"])

                except Exception as e:
                    st.error(f"分析エラーが発生しました: {str(e)}")
                    st.exception(e)


if __name__ == "__main__":
    render_earnings_analyst()
