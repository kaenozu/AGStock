"""
Earnings Analyst UI
決算分析のStreamlitインターフェース
"""

import json
import logging
from datetime import datetime

import pandas as pd
import streamlit as st

from src.rag.pdf_loader import PDFLoader
from src.rag.earnings_rag import EarningsRAG
from src.rag.earnings_analyzer import EarningsAnalyzer
from src.data.earnings_history import EarningsHistory

logger = logging.getLogger(__name__)


def render_earnings_analyst():
    """決算分析UIのメインレンダリング"""
    st.header("🤖 決算分析 (Earnings Hunter)")
    st.markdown("決算短信(PDF)をアップロードすると、AIが瞬時に分析し、投資判断を提供します。")

    tabs = st.tabs(["📊 新規分析", "📜 分析履歴", "⚙️ 設定"])

    with tabs[0]:
        _render_new_analysis()

    with tabs[1]:
        _render_history()
    
    with tabs[2]:
        _render_settings()


def _render_new_analysis():
    """新規分析タブ"""
    st.subheader("📄 PDFアップロード")
    
    uploaded_file = st.file_uploader(
        "決算PDFをアップロード",
        type="pdf",
        help="決算短信、決算説明資料などのPDFファイルをアップロードしてください"
    )

    # オプション設定
    col1, col2 = st.columns(2)
    with col1:
        use_rag = st.checkbox("RAG（高度な検索）を使用", value=True, help="ベクトル検索で関連情報を抽出します")
    with col2:
        extract_tables = st.checkbox("テーブルを抽出", value=True, help="財務データのテーブルを抽出します")

    if uploaded_file is not None:
        st.success(f"✅ ファイル読み込み成功: {uploaded_file.name}")
        
        # ファイル情報表示
        file_size = uploaded_file.size / 1024  # KB
        st.caption(f"ファイルサイズ: {file_size:.1f} KB")

        if st.button("🚀 AI分析を開始", type="primary", use_container_width=True):
            with st.spinner("AIが資料を精読中... (これには数秒〜1分程度かかります)"):
                try:
                    # 1. PDF読み込み
                    st.info("📖 PDFを読み込み中...")
                    pdf_loader = PDFLoader()
                    pdf_data = pdf_loader.load_pdf(uploaded_file, extract_tables=extract_tables)
                    
                    if not pdf_data.get("text"):
                        st.error("❌ テキスト抽出に失敗しました。画像ベースのPDFの可能性があります。")
                        return
                    
                    # メタデータ表示
                    metadata = pdf_data.get("metadata", {})
                    st.success(f"📊 企業: {metadata.get('company', '不明')} | 日付: {metadata.get('date', '不明')}")
                    
                    # 2. RAGインデックス化（オプション）
                    rag_engine = None
                    doc_id = None
                    if use_rag:
                        st.info("🔍 RAGエンジンでインデックス化中...")
                        rag_engine = EarningsRAG()
                        doc_id = f"{metadata.get('company', 'UNKNOWN')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        success = rag_engine.index_document(pdf_data, doc_id)
                        if success:
                            st.success("✅ RAGインデックス化完了")
                        else:
                            st.warning("⚠️ RAGインデックス化に失敗しました。通常モードで続行します。")
                            rag_engine = None
                    
                    # 3. LLM分析
                    st.info("🤖 AIが分析中...")
                    analyzer = EarningsAnalyzer()
                    result = analyzer.analyze(pdf_data, rag_engine, doc_id)
                    
                    if "error" in result:
                        st.error(f"❌ 分析エラー: {result['error']}")
                        return
                    
                    # 4. 履歴保存
                    try:
                        history = EarningsHistory()
                        history_entry = {
                            "company_name": metadata.get("company", "Unknown"),
                            "period": metadata.get("date", "Unknown"),
                            "timestamp": datetime.now().isoformat(),
                            "score": _calculate_score(result),
                            "analysis": result,
                            "doc_id": doc_id
                        }
                        history.save_analysis(history_entry)
                        st.success("💾 分析結果を保存しました")
                    except Exception as e:
                        logger.warning(f"Failed to save history: {e}")
                    
                    # 5. 結果表示
                    st.success("✅ 分析完了！")
                    _display_analysis_result(result, pdf_data)

                except Exception as e:
                    st.error(f"❌ 分析中にエラーが発生しました: {e}")
                    logger.error(f"Analysis error: {e}", exc_info=True)
                    
                    # デバッグ情報
                    with st.expander("🔧 デバッグ情報"):
                        st.exception(e)


def _render_history():
    """分析履歴タブ"""
    st.subheader("📜 過去の分析履歴")
    
    try:
        history = EarningsHistory()
        items = history.get_history()

        if not items:
            st.info("📭 分析履歴はありません。")
            return
        
        # フィルター
        companies = list(set([item.get("company_name", "Unknown") for item in items]))
        selected_company = st.selectbox("企業でフィルター", ["すべて"] + companies)
        
        # フィルタリング
        if selected_company != "すべて":
            items = [item for item in items if item.get("company_name") == selected_company]

        st.caption(f"表示件数: {len(items)}")
        
        # 履歴表示
        for item in items:
            score = item.get("score", 0)
            company = item.get("company_name", "Unknown")
            period = item.get("period", "Unknown")
            timestamp = item.get("timestamp", "")[:10]
            
            # スコアに応じたアイコン
            if score >= 80:
                icon = "🚀"
            elif score >= 50:
                icon = "⚖️"
            else:
                icon = "📉"
            
            with st.expander(f"{icon} {company} ({period}) - スコア: {score}/100 - {timestamp}"):
                if item.get("analysis"):
                    _display_analysis_result(item["analysis"], {})
                else:
                    st.warning("詳細データがありません")

    except Exception as e:
        st.error(f"履歴の読み込みに失敗しました: {e}")
        logger.error(f"History load error: {e}", exc_info=True)


def _render_settings():
    """設定タブ"""
    st.subheader("⚙️ 設定")
    
    st.markdown("### API設定")
    api_key_status = "✅ 設定済み" if st.session_state.get("GEMINI_API_KEY") else "❌ 未設定"
    st.info(f"Gemini API Key: {api_key_status}")
    
    st.markdown("### RAG設定")
    st.text_input("ChromaDB保存先", value="./data/chroma_earnings", disabled=True)
    
    st.markdown("### モデル設定")
    model_options = ["gemini-1.5-pro", "gemini-1.5-flash"]
    selected_model = st.selectbox("使用するモデル", model_options)
    st.caption("Flash: 高速・低コスト | Pro: 高精度")
    
    if st.button("設定を保存"):
        st.success("設定を保存しました（現在はデモモード）")


def _display_analysis_result(result: dict, pdf_data: dict):
    """分析結果の表示"""
    
    # 投資判断サマリー
    st.markdown("## 📊 投資判断")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        recommendation = result.get("recommendation", "HOLD")
        rec_emoji = {"BUY": "🟢", "HOLD": "🟡", "SELL": "🔴"}.get(recommendation, "⚪")
        st.metric("判断", f"{rec_emoji} {recommendation}")
    
    with col2:
        confidence = result.get("confidence", 0.5)
        st.metric("信頼度", f"{confidence:.0%}")
        st.progress(confidence)
    
    with col3:
        sentiment = result.get("sentiment", "NEUTRAL")
        sent_emoji = {"POSITIVE": "😊", "NEUTRAL": "😐", "NEGATIVE": "😞"}.get(sentiment, "😐")
        st.metric("センチメント", f"{sent_emoji} {sentiment}")
    
    st.divider()
    
    # 理由
    st.markdown("### 💡 判断理由")
    reasoning = result.get("reasoning", "理由が提供されていません")
    st.info(reasoning)
    
    st.divider()
    
    # 業績サマリー
    summary = result.get("summary", {})
    if summary:
        st.markdown("### 📈 業績サマリー")
        cols = st.columns(3)
        
        metrics_map = {
            "revenue_growth": ("売上成長率", "{:.1%}"),
            "operating_profit_growth": ("営業利益成長率", "{:.1%}"),
            "net_profit_growth": ("純利益成長率", "{:.1%}")
        }
        
        for idx, (key, (label, fmt)) in enumerate(metrics_map.items()):
            if key in summary:
                value = summary[key]
                with cols[idx]:
                    formatted_value = fmt.format(value) if isinstance(value, (int, float)) else str(value)
                    delta_color = "normal" if value >= 0 else "inverse"
                    st.metric(label, formatted_value)
    
    st.divider()
    
    # 主要トピックとリスク
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ 主要トピック")
        key_topics = result.get("key_topics", [])
        if key_topics:
            for topic in key_topics:
                st.markdown(f"- {topic}")
        else:
            st.caption("トピックが抽出されませんでした")
    
    with col2:
        st.markdown("### ⚠️ リスク要因")
        risk_factors = result.get("risk_factors", [])
        if risk_factors:
            for risk in risk_factors:
                st.markdown(f"- {risk}")
        else:
            st.caption("リスク要因が抽出されませんでした")
    
    # テーブルデータ
    tables = pdf_data.get("tables", [])
    if tables:
        st.divider()
        st.markdown("### 📊 抽出されたテーブル")
        for idx, table in enumerate(tables[:3]):  # 最初の3つのみ
            with st.expander(f"テーブル {idx + 1}"):
                st.dataframe(table, use_container_width=True)
    
    # 詳細データ
    with st.expander("🔍 詳細データ（JSON）"):
        st.json(result)


def _calculate_score(result: dict) -> int:
    """
    分析結果からスコアを計算
    
    Args:
        result: 分析結果
    
    Returns:
        0-100のスコア
    """
    score = 50  # ベーススコア
    
    # 投資判断によるスコア調整
    recommendation = result.get("recommendation", "HOLD")
    if recommendation == "BUY":
        score += 30
    elif recommendation == "SELL":
        score -= 30
    
    # センチメントによるスコア調整
    sentiment = result.get("sentiment", "NEUTRAL")
    if sentiment == "POSITIVE":
        score += 20
    elif sentiment == "NEGATIVE":
        score -= 20
    
    # 信頼度による調整
    confidence = result.get("confidence", 0.5)
    score = int(score * (0.7 + 0.3 * confidence))
    
    # 0-100に制限
    return max(0, min(100, score))


if __name__ == "__main__":
    st.set_page_config(page_title="Earnings Hunter", layout="wide")
    render_earnings_analyst()
