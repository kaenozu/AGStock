import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data.feedback_store import FeedbackStore
from src.agents.strategy_arena import StrategyArena


def render_intelligence_dashboard():
    pass
#     """
#         Renders the AI Intelligence Dashboard: Leaderboard, Lessons Learned, and Dynamic Weights.
#                     st.title("🧠 AI Intelligence Insights")
#         st.markdown("AIエージェントの予測精度、自己反省ログ、および動的な意思決定ウェイトを可視化します。")
#             store = FeedbackStore()
#         arena = StrategyArena()
#     # 1. Agent Leaderboard Section
#         st.subheader("🏆 AI Agent Leaderboard")
#         leaderboard = store.get_agent_leaderboard()
#             if leaderboard:
    pass
#                 # Prepare data for plotting
#             agent_names = {
#                 "visual_pred": "Visual (Chart) Analyst",
#                 "social_pred": "Social (Heat) Analyst",
#                 "tech_pred": "Tech (Quantitative) Analyst",
#             }
#                 cols = st.columns(len(leaderboard))
#             plot_data = []
#                 for i, (key, stats) in enumerate(leaderboard.items()):
    pass
#                     name = agent_names.get(key, key)
#                 acc = stats["accuracy"]
#                 total = stats["total_signals"]
#                     with cols[i]:
    pass
#                         st.metric(label=name, value=f"{acc*100:.1f}%", delta=f"{total} signals", delta_color="normal")
#                     plot_data.append({"Agent": name, "Accuracy (%)": acc * 100, "Total Signals": total})
#     # Chart
#             df_lb = pd.DataFrame(plot_data)
#             fig = px.bar(
#                 df_lb,
#                 x="Agent",
#                 y="Accuracy (%)",
#                 color="Accuracy (%)",
#                 color_continuous_scale="Viridis",
#                 text_auto=".1f",
#                 title="Agent Accuracy Comparison",
#             )
#             fig.update_layout(template="plotly_dark", height=400)
#             st.plotly_chart(fig, use_container_width=True)
#         else:
    pass
#             st.info("リーダーボードのデータがまだありません。いくつかの取引が完了するまでお待ちください。")
#     # 2. Dynamic Weights Section
#         st.subheader("⚖️ Dynamic Voting Weights")
#         weights_data = arena.get_weights()
#             if weights_data:
    pass
#                 st.markdown("直近のパフォーマンスに基づき、各エージェントの意見がどれだけ重視されているかを示します。")
#     # Horizontal bar chart for weights
#             names = list(weights_data.keys())
#             vals = list(weights_data.values())
#                 fig_weight = go.Figure(go.Bar(x=vals, y=names, orientation="h", marker=dict(color=vals, colorscale="Blues")))
#             fig_weight.update_layout(
#                 template="plotly_dark", height=300, title="Current Decision Weights", xaxis_title="Weight Multiplier"
#             )
#             st.plotly_chart(fig_weight, use_container_width=True)
#         else:
    pass
#             st.write("デフォルトの重み(1.0)が使用されています。")
#     # 3. Reflection Log Timeline
#         st.subheader("🧐 AI Reflection & Lessons Learned")
#     # Fetch recent failures with reflections
#         try:
    pass
#             import sqlite3
#     import json
#                 with sqlite3.connect(store.db_path) as conn:
    pass
#                     conn.row_factory = sqlite3.Row
#                 cursor = conn.cursor()
#                 cursor.execute(
#                                     SELECT timestamp, ticker, decision, outcome, return_1w, lesson_learned, reflection_log
#                     FROM decision_feedback
#                     WHERE lesson_learned IS NOT NULL
#                     ORDER BY timestamp DESC LIMIT 10
#                             )
#                 lessons = [dict(row) for row in cursor.fetchall()]
#                 if lessons:
    pass
#                     for l in lessons:
    pass
#                         with st.expander(f"📌 {l['timestamp'][:10]} | {l['ticker']} ({l['decision']}) - {l['outcome']}"):
    pass
#                         st.markdown(f"**結果**: 1週間後の収益率 {l['return_1w']*100:.2f}%")
#                         st.info(f"💡 **教訓**: {l['lesson_learned']}")
#                         st.markdown(f"**分析詳細**:\n{l['reflection_log']}")
#             else:
    pass
#                 st.write("まだ反省ログが生成されていません。夜間の `run_self_reflection` をお待ちください。")
#         except Exception as e:
    pass
#             st.error(f"反省ログの読み込み中にエラーが発生しました: {e}")
#     # 4. Strategy Evolution Selection
#         st.markdown("---")
#         st.subheader("🧬 戦略進化ラボ (Strategy Evolution Lab)")
#         st.markdown("AIが自動生成した新しい戦略コードを確認・検証できます。")
#             evolved_dir = "src/strategies/evolved"
#     import os
#             if not os.path.exists(evolved_dir):
    pass
#                 os.makedirs(evolved_dir, exist_ok=True)
#             files = [f for f in os.listdir(evolved_dir) if f.endswith(".py") and f != "__init__.py"]
#             if files:
    pass
#                 selected_file = st.selectbox("閲覧する進化した戦略を選択:", files)
#             if selected_file:
    pass
#                 file_path = os.path.join(evolved_dir, selected_file)
#                 with open(file_path, "r", encoding="utf-8") as f:
    pass
#                     code_content = f.read()
#                     st.code(code_content, language="python")
#                 st.caption(f"Path: {file_path}")
#         else:
    pass
#             st.info("現在、進化した戦略ファイルはありません。次回の進化サイクルをお待ちください。")
#     # 5. RL Training Monitor
#         st.markdown("---")
#         st.subheader("🤖 RL Training Monitor")
#     # Just checking for Q-table files in root or logs
#         q_files = [f for f in os.listdir(".") if f.startswith("q_table_") and f.endswith(".json")]
#         if q_files:
    pass
#             tabs = st.tabs([f.replace("q_table_", "").replace(".json", "") for f in q_files])
#             for i, qf in enumerate(q_files):
    pass
#                 with tabs[i]:
    pass
#                     try:
    pass
#                         import json
#                             with open(qf, "r") as f:
    pass
#                                 q_data = json.load(f)
#                         st.write("Current Q-Table (State -> [Trust, Override]):")
#                         st.json(q_data)
#                     except Exception as e:
    pass
#                         st.error(f"Failed to load Q-Table: {e}")
#         else:
    pass
#             st.write("No RL Agent Q-Tables found yet.")
#     if __name__ == "__main__":
    pass
#         render_intelligence_dashboard()
# 
#     """  # Force Balanced
