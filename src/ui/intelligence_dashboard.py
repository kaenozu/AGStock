"""
AI Intelligence Dashboard
Renders insights into the AI's collective decision making, agent performance, and self-reflection logs.
"""

import os
import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.data.feedback_store import FeedbackStore
from src.agents.strategy_arena import StrategyArena


def render_intelligence_dashboard():
    """renders the AI Intelligence Dashboard UI component."""
    st.title("🧠 AI Intelligence Insights")
    st.markdown("AIエージェントの予測精度、自己反省ログ、および動的な意思決定ウェイトを可視化します。")
    
    store = FeedbackStore()
    arena = StrategyArena()
    
    # --- 1. Agent Leaderboard Section ---
    st.subheader("🏆 AI Agent Leaderboard")
    leaderboard = store.get_agent_leaderboard()
    
    if leaderboard:
        agent_names = {
            "market_analyst": "📈 Market Analyst",
            "risk_manager": "🛡️ Risk Manager",
            "macro_strategist": "🌐 Macro Strategist",
            "vision_pred": "👁️ Vision Analyst",
            "social_pred": "💬 Social Analyst"
        }
        
        plot_data = []
        cols = st.columns(len(leaderboard))
        
        for i, (key, stats) in enumerate(leaderboard.items()):
            name = agent_names.get(key, key)
            acc = stats.get("accuracy", 0.0)
            total = stats.get("total_signals", 0)
            
            with cols[i]:
                st.metric(label=name, value=f"{acc*100:.1f}%", delta=f"{total} signals")
            
            plot_data.append({"Agent": name, "Accuracy (%)": acc * 100, "Total": total})
            
        df_lb = pd.DataFrame(plot_data)
        fig = px.bar(
            df_lb,
            x="Agent",
            y="Accuracy (%)",
            color="Accuracy (%)",
            color_continuous_scale="Viridis",
            text_auto=".1f",
            title="Agent Historical Accuracy"
        )
        fig.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 リーダーボードの統計データがまだありません。いくつかの取引サイクルが完了するまでお待ちください。")

    # --- 2. Dynamic Weights Section ---
    st.markdown("---")
    st.subheader("⚖️ Dynamic Voting Weights")
    weights = arena.get_weights()
    
    if weights:
        st.markdown("直近のパフォーマンスに基づき、各エージェントの意見が合議体でどれだけ重視されているか（メリットシステム）を示します。")
        names = list(weights.keys())
        vals = list(weights.values())
        
        fig_weight = go.Figure(go.Bar(
            x=vals, y=names, orientation="h",
            marker=dict(color=vals, colorscale="Blues")
        ))
        fig_weight.update_layout(
            template="plotly_dark", height=300,
            title="Current Decision Weights",
            xaxis_title="Weight Multiplier (Multi-Armed Bandit)"
        )
        st.plotly_chart(fig_weight, use_container_width=True)
    
    # --- 3. Reflection Log Timeline ---
    st.markdown("---")
    st.subheader("🧐 AI Reflection & Lessons Learned")
    try:
        with sqlite3.connect(store.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, ticker, decision, outcome, return_1w, lesson_learned, reflection_log
                FROM decision_feedback
                WHERE lesson_learned IS NOT NULL
                ORDER BY timestamp DESC LIMIT 10
            """)
            lessons = [dict(row) for row in cursor.fetchall()]
            
        if lessons:
            for l in lessons:
                with st.expander(f"📌 {l['timestamp'][:10]} | {l['ticker']} ({l['decision']})"):
                    st.write(f"**結果**: {l['outcome']} (1週間後収益率: {l['return_1w']*100:.2f}%)")
                    st.info(f"💡 **教訓**: {l['lesson_learned']}")
                    st.markdown(f"**分析詳細**:\n{l['reflection_log']}")
        else:
            st.info("自己反省ログはまだ生成されていません。夜間の自動バッチ処理をお待ちください。")
    except Exception as e:
        st.error(f"反省ログの読み込みに失敗しました: {e}")

    st.markdown("---")
    render_rl_monitor()
    
    # --- 4. Strategy Evolution Gallery ---
    st.markdown("---")
    st.subheader("🧬 Strategy Evolution Gallery")
    evolved_dir = "src/strategies/evolved"
    if os.path.exists(evolved_dir):
        files = [f for f in os.listdir(evolved_dir) if f.endswith(".py") and f != "__init__.py"]
        if files:
            selected = st.selectbox("閲覧する進化した戦略:", files)
            if selected:
                with open(os.path.join(evolved_dir, selected), "r", encoding="utf-8") as f:
                    st.code(f.read(), language="python")
        else:
            st.info("AIによって生成（進化）された新しい戦略ファイルはまだありません。")
    else:
        st.info("進化ラボは現在クローズしています。")

def render_rl_monitor():
    """Visualizes the RL agent's learning progress."""
    st.subheader("🤖 RL Training Monitor")
    log_path = "data/rl_training_log.csv"
    
    if os.path.exists(log_path):
        try:
            df = pd.read_csv(log_path)
            st.markdown("強化学習エージェントが過去のシミュレーション環境でどれだけ成長したかを示します。")
            
            # Learning Curve
            fig = px.line(df, x="episode", y="pnl_pct", 
                         title="Learning Curve (PNL % per Episode)",
                         markers=True)
            fig.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig, use_container_width=True)
            
            # Stats
            avg_pnl = df["pnl_pct"].mean()
            max_pnl = df["pnl_pct"].max()
            st.caption(f"Average PnL: {avg_pnl:+.2f}% | Best Episode: {max_pnl:+.2f}%")
            
        except Exception as e:
            st.error(f"RLログの読み込みに失敗しました: {e}")
    else:
        st.info("RLエージェントの学習ログが見つかりません。`python train_rl_agent.py` を実行して学習を開始してください。")

if __name__ == "__main__":
    render_intelligence_dashboard()
