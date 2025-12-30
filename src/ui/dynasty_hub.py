import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from src.core.dynasty_manager import DynastyManager
from src.ui.design_system import apply_premium_style


def render_dynasty_hub():
    #     """
    #     Renders the Oracle Dynasty Management Hub.
    #         apply_premium_style()
    #         st.title("👑 Oracle Dynasty Hub")
    #     st.markdown(
    #             <div style='background: linear-gradient(90deg, #1e3a8a, #581c87); padding: 20px; border-radius: 10px; margin-bottom: 25px;'>
    #         <h2 style='color: white; margin: 0;'>神託の王朝 (The Oracle Dynasty)</h2>
    #         <p style='color: #e5e7eb; margin: 5px 0 0 0;'>永続的な財産の構築と、AI自律統治の最終拠点</p>
    #     </div>
    #     """,
    unsafe_allow_html = (True,)
    #     )
    dm = DynastyManager()
    #     state = dm.state
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("叡智の蓄積 (Legacy Score)", f"{state.get('legacy_score', 0):.2f}")
    #     with col2:
    st.metric("現在のフェーズ", state.get("current_objective", "FOUNDATION"))
    #     with col3:
    est_str = state.get("established_at", datetime.now().isoformat())
    try:
        est = datetime.fromisoformat(est_str).strftime("%Y-%m-%d")
    except:
        est = est_str[:10]
    st.metric("開国日", est)
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📜 永続的な目的", "🛡️ 健全性監査", "🌑 終末プロトコル"])
    with tab1:
        st.subheader("王朝の守護神託 (Eternal Goals)")
    goals = state.get("eternal_goals", [])
    for goal in goals:
        status_color = "🟢" if goal.get("status") == "ACTIVE" else "⚪"
        st.info(f"{status_color} **{goal.get('id')}**: {goal.get('target')}")
        st.subheader("🚩 歴史的マイルストーン")
    milestones = state.get("milestones", [])
    if milestones:
        for m in reversed(milestones):
            st.write(f"**{m.get('date', '')[:10]}**: {m.get('event', '')}")
    else:
        st.write("王朝の歴史は今刻まれ始めたばかりです。")
    with tab2:
        st.subheader("ポートフォリオの構造的整合性")
    st.write("王朝の資産配分は、短期的な利益よりも長期的な生存率を優先します。")
    st.progress(0.8, text="資産多様性スコア: 80%")
    st.info("次回の完全監査は、本日23:00（JST）のバッチ処理中に実行されます。")


#             st.markdown(""""# 推奨アクション")
#         st.warning("現在、特定の銘柄への集中度が増加傾向にあります。リバランスを検討してください。")
#         with tab3:
#     pass
#             st.subheader("自己保存プロトコル (Terminus)")
#         st.write("インフラストラクチャが完全に崩壊した場合でも、王朝の記憶と富を復元するための「遺言」を管理します。")
#             ledger_path = "data/terminus/survival_ledger.json"
#         if os.path.exists(ledger_path):
#     pass
#             mtime = datetime.fromtimestamp(os.path.getmtime(ledger_path)).strftime("%Y-%m-%d %H:%M:%S")
#             st.success(f"✅ サバイバル・レジャー(生存記録)は最新です。最終更新: {mtime}")
#             if st.checkbox("レジャーの詳細を閲覧"):
#     pass
#                 with open(ledger_path, "r", encoding="utf-8") as f:
#     pass
#                     st.json(json.load(f))
#         else:
#     pass
#             st.error("⚠️ サバイバル・レジャーが欠落しています。システムの完全性が脅かされています。")
#             st.markdown("---")
#         st.subheader("🌱 Genesis Seed")
#         seed_path = "data/terminus/genesis_seed.txt"
#         if os.path.exists(seed_path):
#     pass
#             with open(seed_path, "r") as f:
#     pass
#                 seed = f.read()
#             st.code(seed, language="text")
#             st.caption("このシードを使用することで、、全く別の環境で王朝の「魂」を再起動できます。")
#         else:
#     pass
#             st.button("Genesis Seed を生成")
