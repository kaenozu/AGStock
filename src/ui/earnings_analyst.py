import pandas as pd
import streamlit as st

from agstock.src.analysis.pdf_reader import EarningsAnalyzer, PDFExtractor
from agstock.src.rag.pdf_loader import PDFLoader


def render_earnings_analyst():
    st.header("🤖 決算分析 (Earnings Hunter)")
    st.markdown("決算短信(PDF)をアップロードすると、AIが瞬時に分析します。")

    uploaded_file = st.file_uploader("決算PDFをアップロード", type="pdf")

    if uploaded_file is not None:
        st.success(f"ファイル読み込み成功: {uploaded_file.name}")

        if st.button("AI分析を開始"):
            with st.spinner("AIが資料を精読中... (これには数秒〜1分程度かかります)"):
                try:
                    # 1. Extract Text
                    text = PDFExtractor.extract_text(uploaded_file)
                    if not text or text.startswith("Error extracting PDF"):
                        st.error("テキストを抽出できませんでした。画像ベースのPDFや破損ファイルの可能性があります。")
                        return

                    text_len = len(text)
                    st.info(f"テキスト抽出完了: {text_len} 文字")
                    if text_len < 200:
                        st.warning(
                            "抽出テキストが非常に短いです。画像ベースのPDFの可能性があります。OCR済みのPDFをお試しください。"
                        )

                    # 2. Analyze
                    analyzer = EarningsAnalyzer()
                    result = analyzer.analyze_report(text)

                    # 3. Display Result
                    st.markdown("### 📊 AI分析レポート")
                    st.markdown(result["raw_analysis"])

                except Exception as e:
                    st.error(f"分析エラーが発生しました: {str(e)}")
                    st.exception(e)


if __name__ == "__main__":
    render_earnings_analyst()
