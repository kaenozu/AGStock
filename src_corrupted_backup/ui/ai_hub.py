import streamlit as st
import pandas as pd
import plotly.express as px
# Lazy imports moved inside function
def render_ai_hub():
    st.header("🤖 AI分析センター (AI Hub)")
    st.caption("最新ニュース、投資委員会、AIチャットなど、すべてのAI機能にここからアクセスできます。")
        main_tabs = st.tabs(["🏛️ Analysis & Strategy", "📰 Market Intelligence", "🌌 Cosmic Lab & Security"])
        with main_tabs[0]:
            sub_tab = st.radio(
            "Select Analysis Module:",
            [
                "AI 投資委員会 (Boardroom)",
                "Council Hall (100 Avatars)",
                "AI CFO コンソール",
                "AI 知能ダッシュボード",
                "💬 AI チャット",
            ],
            horizontal=True,
        )
            if "委員会" in sub_tab:
                from src.ui.committee_ui import render_committee_ui
                render_committee_ui()
        elif "Council" in sub_tab:
            from src.ui.council_hall_panel import render_council_hall
                render_council_hall()
        elif "CFO" in sub_tab:
            from src.ui.cfo_panel import render_cfo_panel
                render_cfo_panel()
        elif "知能" in sub_tab:
            from src.ui.intelligence_dashboard import render_intelligence_dashboard
                render_intelligence_dashboard()
        elif "チャット" in sub_tab:
            from src.ui.ai_chat import render_ai_chat
                render_ai_chat()
        with main_tabs[1]:
            sub_tab = st.radio(
            "Select Insight Module:",
            ["ニュース・センチメント", "決算・適時開示", "セクター熱力図 & 統治", "Future Sight (予報)"],
            horizontal=True,
        )
            if "ニュース" in sub_tab:
                from src.ui.news_analyst import render_news_analyst
                render_news_analyst()
        elif "決算" in sub_tab:
            from src.ui.earnings_analyst import render_earnings_analyst
                render_earnings_analyst()
_render_filing_watcher_ui()
elif "セクター" in sub_tab:
            render_sector_heatmap()
            render_executive_control()
        elif "Future" in sub_tab:
            st.subheader("🔮 AI Future Sight")
from src.data_loader import fetch_stock_data
from src.ui.future_sight_panel import render_future_sight_chart
t_in = st.text_input("Ticker", "7203.T", key="fs_in")
            if t_in:
                df_map = fetch_stock_data([t_in], period="60d")
                if t_in in df_map:
                    render_future_sight_chart(t_in, df_map[t_in])
        with main_tabs[2]:
            sub_tab = st.radio(
            "Select Advanced Module:",
            ["Alternative Chronos (並行世界)", "3D 市場地形図", "Terminus Vault (防衛)", "Temporal Rift & Cosmic"],
            horizontal=True,
        )
            if "Chronos" in sub_tab:
                from src.ui.chronos_panel import render_chronos_lab
                render_chronos_lab()
        elif "3D" in sub_tab:
            from src.ui.topography_panel import render_topography_panel
                render_topography_panel()
        elif "Terminus" in sub_tab:
            from src.ui.vault_panel import render_terminus_vault
                render_terminus_vault()
        elif "Temporal" in sub_tab:
            pass
#             st.write(""""# 🌌 Temporal Rift & Cosmic Status")
from src.ui.cosmic_panel import render_cosmic_dashboard
render_cosmic_dashboard()
from src.ui.temporal_rift_panel import render_temporal_rift
from src.data_loader import fetch_stock_data
tr_ticker = st.text_input("Temporal Analysis Ticker", "7203.T", key="tr_t")
            if tr_ticker:
                df_rift = fetch_stock_data([tr_ticker], period="60d")
                if tr_ticker in df_rift:
                    render_temporal_rift(tr_ticker, df_rift[tr_ticker])
def render_sector_heatmap():
    pass
#     """
#     Render Sector Heatmap.
#         st.subheader("📊 セクター別決算スコア (Sector Heatmap)")
#     st.caption("最近の決算分析結果をセクター別に集計し、市場の『波』を可視化します。")
from src.data.earnings_history import EarningsHistory
eh = EarningsHistory()
    data = eh.get_all_history()
    if not data:
        st.info("集計対象の決算データがまだありません。")
        return
        df = pd.DataFrame(data)
    if "sector" not in df.columns or "score" not in df.columns:
        st.warning("ヒートマップ生成に必要なデータ（セクター/スコア）が不足しています。")
        return
        sector_summary = df.groupby("sector")["score"].mean().reset_index()
        fig = px.bar(
        sector_summary,
        x="sector",
        y="score",
        color="score",
        color_continuous_scale="RdYlGn",
        title="セクター別平均スコア",
    )
    st.plotly_chart(fig, use_container_width=True)
# """
def render_executive_control():
    pass
#     """
#     Render Executive Control.
#         st.subheader("⚖️ Executive Governance Monitor")
#     st.caption("AIによる経営陣のガバナンス評価および言行不一致リスクを監視します。")
#     st.info("現在、市場全体のガバナンス・リスクは **NORMAL** です。")
#     st.metric("Governance Integrity Index", "84/100", "+2%")
# """
def _render_filing_watcher_ui():
    pass
#     """
#     Render Filing Watcher Ui.
#         st.subheader("📡 適時開示ウォッチ (RAG Deep Hunter)")
from src.rag.filing_watcher import FilingWatcher
fw = FilingWatcher()
    target_ticker = st.text_input("ウォッチ対象銘柄", "7203.T", key="fw_ticker")
    if st.button("深層解析実行", key="fw_btn"):
        with st.spinner("過去の開示ベースラインと照合中..."):
            result = fw.watch_ticker(target_ticker)
            if "error" in result:
                st.error(result["error"])
            else:
                st.success(f"解析完了: {result['status']}")
                st.markdown(f"**AIの洞察**: {result['insight']}")


