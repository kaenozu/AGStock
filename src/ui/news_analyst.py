"""
AI News Analyst UI
"""

import logging

import streamlit as st

from src.llm_reasoner import get_llm_reasoner
from src.news_collector import get_news_collector

logger = logging.getLogger(__name__)


def render_news_analyst():
    """Renders the AI News Analyst tab."""
    st.header("📰 AI ニュースアナリスト")
    st.caption("最新ニュースをAIが読み込み、市場センチメントを分析します。")

    # --- API Key Check & Setup ---
    reasoner = get_llm_reasoner()

    # Simple check: Is provider Gemini? (Implies Key is set, or we default to Ollama but usually we want Gemini for this)
    # Actually, let's check if api_key is present.
    if not reasoner.api_key:
        with st.expander("⚠️ 初期設定 (APIキーが必要です)", expanded=True):
            st.warning("この機能を使用するには、Google Gemini APIキーが必要です。")

            st.info("💡 **設定方法**")
            st.markdown(
                "画面上部の **「⚙️ 設定」** タブを開き、APIキーを入力してください。"
            )

            if st.button("設定タブへ移動不可 (手動で切り替えてください)"):
                st.caption(
                    "Streamlitの仕様上、ここから直接タブ切り替えはできません。上のタブをクリックしてください。"
                )

        return  # Stop rendering until key is set

    # Create Sub-tabs
    tab_news, tab_earnings = st.tabs(["🌐 ニュース分析", "📑 決算書分析 (PDF)"])

    # --- Tab 1: News Analysis (Existing Logic) ---
    with tab_news:
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader("📡 最新ニュースフィード")
            if st.button(
                "ニュースを取得 & 分析開始", type="primary", use_container_width=True
            ):
                with st.spinner(
                    "ニュースを収集し、AIが分析中... (これには数秒〜1分かかります)"
                ):
                    try:
                        # 1. Fetch News
                        collector = get_news_collector()
                        news_list = collector.fetch_market_news(limit=10)

                        if not news_list:
                            st.error(
                                "ニュースを取得できませんでした。ネットワーク接続を確認してください。"
                            )
                            return

                        st.success(f"{len(news_list)} 件のニュースを取得しました。")

                        # 2. Analyze with LLM
                        reasoner = get_llm_reasoner()
                        analysis_result = reasoner.analyze_news_sentiment(news_list)

                        # Store in session state to persist
                        st.session_state["news_analysis_result"] = analysis_result
                        st.session_state["news_list"] = news_list

                    except Exception as e:
                        st.error(f"分析中にエラーが発生しました: {e}")
                        logger.error(f"News Analysis Error: {e}")

            # Display News List
            news_list = st.session_state.get("news_list", [])
            if news_list:
                for news in news_list:
                    with st.expander(f"📄 {news['title']}"):
                        st.write(f"**Published**: {news['published']}")
                        st.write(f"**Source**: {news['source']}")
                        st.write(f"[リンク]({news['link']})")
                        if news["summary"]:
                            st.write(news["summary"])

        with col_right:
            st.subheader("🧠 AI分析レポート")

            result = st.session_state.get("news_analysis_result")

            if result:
                # Score Gauge
                score = result.get("sentiment_score", 0)

                # Color logic
                if score > 3:
                    label = "強気 (BULLISH)"
                elif score < -3:
                    label = "弱気 (BEARISH)"
                else:
                    label = "中立 (NEUTRAL)"

                st.metric(
                    label="AI市場センチメント", value=f"{score:+.1f} / 10", delta=label
                )

                # Progress bar visual
                st.progress((score + 10) / 20)  # Map -10..10 to 0..1

                st.markdown("### 📝 分析理由")
                st.info(result.get("reasoning", "No reasoning provided."))

                st.markdown("### 🔑 注目トピック")
                topics = result.get("key_topics", [])
                for topic in topics:
                    st.write(f"- {topic}")

                st.markdown("### 💡 投資家へのアドバイス")
                st.warning(result.get("trading_implication", "No advice provided."))

            else:
                st.info("👈 左側のボタンを押して分析を開始してください。")
                st.write("AIが以下のRSSフィードから最新情報を読み取ります:")
                st.write("- Yahoo Finance Business")
                st.write("- Reuters Japan Business")

    # --- Tab 2: Earnings Analysis (New) ---
    with tab_earnings:
        st.subheader("📑 決算短信・レポート分析")
        st.caption("PDFの決算資料をアップロードすると、AIが要約・評価します。")

        uploaded_file = st.file_uploader("決算資料 (PDF) をアップロード", type=["pdf"])

        if uploaded_file and st.button("決算分析を実行"):
            with st.spinner("PDFを読み込み、AIが分析中..."):
                try:
                    # 1. Extract Text
                    from src.rag.pdf_loader import PDFLoader

                    pdf_text = PDFLoader.extract_text_from_file(uploaded_file)

                    if not pdf_text or pdf_text.startswith("Error extracting PDF"):
                        st.error(
                            "テキストを抽出できませんでした。画像ベースPDFや破損ファイルの可能性があります。"
                        )
                    elif len(pdf_text) < 100:
                        st.error(
                            "テキストを抽出できませんでした（画像ベースのPDFの可能性があります）。"
                        )
                    else:
                        st.info(f"テキスト抽出完了: {len(pdf_text)} 文字")
                        if len(pdf_text) < 200:
                            st.warning(
                                "抽出テキストが短いです。OCR済みのPDFを推奨します。"
                            )

                        # 2. Analyze
                        # Dynamically add method if needed or use ask() for now,
                        # but best to add a dedicated method to Reasoner.
                        # For now, we will construct prompt here to avoid changing Reasoner immediately if fine.
                        # Actually task says "Update src/ui/news_analyst.py or new tab".

                        reasoner = get_llm_reasoner()
                        # We need to implement analyze_earnings_report in reasoner for JSON structure
                        if hasattr(reasoner, "analyze_earnings_report"):
                            analysis = reasoner.analyze_earnings_report(pdf_text)
                            st.session_state["earnings_analysis"] = analysis
                        else:
                            st.warning("推論エンジンの更新が必要です。")

                except Exception as e:
                    st.error(f"Error: {e}")

        # Display Logic
        earnings_result = st.session_state.get("earnings_analysis")
        if earnings_result:
            st.divider()
            st.subheader("📊 決算分析結果")

            e_score = earnings_result.get("score", 0)
            st.metric("決算スコア", f"{e_score} / 10")

            st.markdown("### 📝 要約")
            st.write(earnings_result.get("summary", ""))

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### ✅ 良い点")
                for item in earnings_result.get("good_points", []):
                    st.write(f"- {item}")
            with col2:
                st.markdown("### ⚠️ 懸念点")
                for item in earnings_result.get("bad_points", []):
                    st.write(f"- {item}")

            st.markdown("### 🔮 今後の見通し")
            st.info(earnings_result.get("outlook", ""))
