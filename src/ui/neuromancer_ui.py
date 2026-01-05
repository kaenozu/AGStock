import streamlit as st
import time
from agstock.src.agents.neuromancer import Neuromancer


def render_neuromancer_ui():
    """
    Neuromancer Interface: AIとの対話型司令室
    """
    st.markdown(
        """
        <style>
        .stChatMessage {
            border-radius: 15px;
            padding: 10px;
        }
        .user-msg {
            background-color: #2b313e;
        }
        .ai-msg {
            background-color: #1a1c24;
            border-left: 3px solid #00ffcc;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("🧠 Neuromancer Link")
    st.caption("Direct Neural Interface with Sovereign AI")

    # セッション状態の初期化
    if "neuromancer" not in st.session_state:
        st.session_state["neuromancer"] = Neuromancer()
        st.session_state["chat_history"] = [
            {"role": "assistant", "content": "リンク接続完了。マスター、本日の指令を。"}
        ]

    agent = st.session_state["neuromancer"]
    history = st.session_state["chat_history"]

    # --- 能動的発話（シミュレーション） ---
    # 実際の運用ではバックグラウンドスレッドからの通知を受け取るが、
    # ここではランダムにAIが独り言を話す確率を入れる
    if len(history) > 0 and history[-1]["role"] == "user":
        # ユーザーの発言直後は必ず応答
        pass
    else:
        # 10%の確率でAIが環境認識コメントを投げる（リラン時）
        import random

        if random.random() < 0.1:
            # 簡易的な市場データモック
            mock_data = {"vix": random.uniform(15, 35), "daily_pnl": random.uniform(-6000, 8000)}
            thought = agent.perceive_world(mock_data)
            # 同じ発言の繰り返し防止
            if history[-1]["content"] != thought:
                history.append({"role": "assistant", "content": thought})

    # チャット履歴の表示
    for msg in history:
        with st.chat_message(msg["role"], avatar="🧠" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

    # ユーザー入力
    if prompt := st.chat_input("AIへの指令を入力..."):
        # ユーザーメッセージ追加
        history.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # AI応答
        response = agent.respond_to_user(prompt)
        time.sleep(0.5)  # 思考時間を演出

        history.append({"role": "assistant", "content": response})
        with st.chat_message("assistant", avatar="🧠"):
            st.markdown(response)

        st.rerun()

    # サイドバーにAIの状態表示
    with st.sidebar:
        st.markdown("---")
        st.subheader("Neuromancer Status")
        st.metric("Mood", agent.indices.mood)
        st.progress(agent.indices.energy / 100, text=f"Energy: {agent.indices.energy}%")
        st.caption(f"Loyalty: {agent.indices.loyalty}")
