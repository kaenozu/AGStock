import streamlit as st
import os
import json
from datetime import datetime
import pandas as pd
from src.core.archive_manager import ArchiveManager
from src.core.knowledge_extractor import KnowledgeExtractor
from src.ui.design_system import apply_premium_style


def render_archive_explorer():
    #     """
    #     The Eternal Archive Explorer - Browse the complete history of AI decisions.
    #         apply_premium_style()
    #         st.title("📚 The Eternal Archive")
    #     st.markdown(
    #             <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; margin-bottom: 25px;'>
    #         <h2 style='color: white; margin: 0;'>永遠の記録庫</h2>
    #         <p style='color: #e5e7eb; margin: 5px 0 0 0;'>全ての意思決定の完全な記録と、そこから抽出された普遍的な知見</p>
    #     </div>
    #     """,
    unsafe_allow_html = (True,)
    #     )
    archive = ArchiveManager()
    #     extractor = KnowledgeExtractor()
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📖 決定の履歴", "🧠 知見の抽出", "🔮 予測の検証", "📊 統計分析"]
    )
    with tab1:
        st.subheader("意思決定のタイムライン")


# Date range selector
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("開始日", datetime.now().replace(day=1))
    #         with col2:
    end_date = st.date_input("終了日", datetime.now())
# Load decisions
decisions = load_decisions_in_range(archive, start_date, end_date)
if decisions:
    st.metric("期間内の決定数", len(decisions))
# Display decisions
# for dec in reversed(decisions[-50:]):  # Latest 50
with st.expander(
    f"{dec.get('timestamp', '')[:10]} | {dec.get('ticker')} | {dec.get('decision')}"
):
    col_a, col_b = st.columns(2)
    #                         with col_a:
    #                             st.write("**決定詳細**")
    #                         st.write(f"信頼度: {dec.get('confidence', 0):.1%}")
    #                         st.write(f"パラダイム: {dec.get('context', {}).get('paradigm', 'N/A')}")
    #                         st.write(f"コンセンサス: {dec.get('deliberation', {}).get('consensus_strength', 0):.1%}")
    #                         with col_b:
    #                             st.write("**参加エージェント**")
    #                         agents = dec.get("deliberation", {}).get("agents_involved", [])
    #                         for agent in agents:
    #                             st.write(f"- {agent}")
    #                         st.write("**市場コンテキスト**")
    st.json(dec.get("context", {}).get("market_data", {}))
    #         else:
    #             st.info("指定期間内に記録された決定はありません。")
    #         with tab2:
    #             st.subheader("普遍的な法則の抽出")
    #             if st.button("🧠 知見を抽出 (最新90日)"):
    #                 with st.spinner("AIが過去の決定を分析中..."):
    decisions = load_decisions_in_range(
        archive, datetime.now().replace(day=1), datetime.now()
    )
    if len(decisions) > 10:
        insights = extractor.extract_universal_laws(decisions)
        if insights.get("universal_laws"):
            st.success(
                f"✅ {len(insights['universal_laws'])} 個の普遍的法則を発見しました"
            )
            for law in insights["universal_laws"]:
                st.info(
                    f"📖 **{law.get('law')}**\n\n信頼度: {law.get('confidence', 0):.0%} | 証拠数: {law.get('evidence_count', 0)}"
                )
            if insights.get("meta_insights"):
                pass
#                                 st.markdown("""" 🎯 戦略的推奨")
#                             st.write(insights["meta_insights"])
#                     else:
#     pass
#                         st.warning("十分なパターンが見つかりませんでした。")
#                 else:
#     pass
#                     st.warning("分析には最低10件の決定記録が必要です。")
# # Display existing knowledge
#         st.markdown("---")
#         st.subheader("蓄積された知見")
#             knowledge_path = os.path.join(archive.archive_dir, "knowledge", "universal_patterns.json")
#         if os.path.exists(knowledge_path):
#     pass
#             with open(knowledge_path, "r", encoding="utf-8") as f:
#     pass
#                 knowledge = json.load(f)
#                 st.write(f"**最終更新**: {knowledge.get('last_updated', 'N/A')[:10]}")
#                 laws = knowledge.get("universal_laws", [])
#             if laws:
#     pass
#                 for law in laws[-10:]:  # Latest 10
#                     st.write(f"- {law.get('law')} (信頼度: {law.get('confidence', 0):.0%})")
#         else:
#     pass
#             st.info("まだ知見が抽出されていません。上のボタンから抽出を開始してください。")
#         with tab3:
#     pass
#             st.subheader("予測の検証")
#             if st.button("🔍 予測を検証"):
#     pass
#                 with st.spinner("過去の予測を検証中..."):
#     pass
#                     # Mock market data for verification
#                 verification_results = archive.verify_predictions({})
#                     col1, col2, col3 = st.columns(3)
#                 with col1:
#     pass
#                     st.metric("検証済み予測", verification_results.get("verified_count", 0))
#                 with col2:
#     pass
#                     st.metric("的中率", f"{verification_results.get('accuracy_rate', 0):.1%}")
#                 with col3:
#     pass
#                     st.metric("平均誤差", f"{verification_results.get('average_error', 0):.2f}")
#             st.info("予測検証機能は、時間経過後に自動的に実行されます。")
#         with tab4:
#     pass
#             st.subheader("アーカイブ統計")
# # Calculate statistics
#         stats = calculate_archive_statistics(archive)
#             col1, col2, col3, col4 = st.columns(4)
#         with col1:
#     pass
#             st.metric("総決定数", stats.get("total_decisions", 0))
#         with col2:
#     pass
#             st.metric("総予測数", stats.get("total_predictions", 0))
#         with col3:
#     pass
#             st.metric("アーカイブサイズ", f"{stats.get('archive_size_mb', 0):.1f} MB")
#         with col4:
#     pass
#             st.metric("最古の記録", stats.get("oldest_record", "N/A")[:10])
# # Paradigm distribution
#         if stats.get("paradigm_distribution"):
#     pass
#             st.markdown("""" パラダイム分布")
paradigm_df = pd.DataFrame(
    list(stats["paradigm_distribution"].items()), columns=["パラダイム", "件数"]
)
st.bar_chart(paradigm_df.set_index("パラダイム"))


def load_decisions_in_range(archive: ArchiveManager, start_date, end_date) -> list:
    pass


#     """Loads decisions within date range."""
decisions = []
for root, dirs, files in os.walk(archive.decisions_dir):
    for file in files:
        if not file.endswith(".json"):
            pass
        continue
        filepath = os.path.join(root, file)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            dec = json.load(f)
            dec_date = datetime.fromisoformat(dec["timestamp"]).date()
        if start_date <= dec_date <= end_date:
            decisions.append(dec)
    except Exception:
        continue


#         return sorted(decisions, key=lambda x: x["timestamp"])
def calculate_archive_statistics(archive: ArchiveManager) -> dict:
    #     """Calculates overall archive statistics."""
    stats = {
        "total_decisions": 0,
        "total_predictions": 0,
        "archive_size_mb": 0.0,
        "oldest_record": None,
        "paradigm_distribution": {},
    }


# Count decisions
for root, dirs, files in os.walk(archive.decisions_dir):
    for file in files:
        if file.endswith(".json"):
            stats["total_decisions"] += 1
            #                     filepath = os.path.join(root, file)
            stats["archive_size_mb"] += os.path.getsize(filepath) / (1024 * 1024)
#                     try:
#                         with open(filepath, "r", encoding="utf-8") as f:
#                             dec = json.load(f)
#                         timestamp = dec.get("timestamp")
#                     if not stats["oldest_record"] or timestamp < stats["oldest_record"]:
#                         stats["oldest_record"] = timestamp
#                         paradigm = dec.get("context", {}).get("paradigm", "UNKNOWN")
#                     stats["paradigm_distribution"][paradigm] = stats["paradigm_distribution"].get(paradigm, 0) + 1
#                 except Exception:
#                     continue
# Count predictions
for root, dirs, files in os.walk(archive.predictions_dir):
    for file in files:
        if file.startswith("pred_"):
            stats["total_predictions"] += 1
#         return stats
