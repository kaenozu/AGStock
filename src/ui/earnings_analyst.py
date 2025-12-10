
import streamlit as st
import pandas as pd
from src.analysis.pdf_reader import PDFExtractor, EarningsAnalyzer

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
                    st.info(f"テキスト抽出完了: {len(text)} 文字")
                    
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
