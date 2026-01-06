import time
import pandas as pd
import numpy as np
import streamlit as st
import logging

from src.rl.environment import TradingEnvironment
from src.rl.agent import DQNAgent

logger = logging.getLogger(__name__)


def generate_demo_market_data(length=1000):
    """Generate synthetic market data for training demo"""
    x = np.linspace(0, 100, length)
    # Trend + Sine Wave + Noise
    prices = 100 + (x * 0.5) + 10 * np.sin(x * 0.2) + np.random.normal(0, 2, length)

    df = pd.DataFrame(
        {
            "Open": prices,
            "High": prices + 2,
            "Low": prices - 2,
            "Close": prices,
            "Volume": np.random.randint(1000, 5000, length),
        }
    )
    return df


def render_rl_training_ui():
    """Renders the AI Training Gym UI"""
    st.header("🏋️ AIトレーニングジム (RL Gym)")
    st.caption("強化学習エージェントの育成プロセスを可視化します。")

    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("トレーニング設定")
        episodes = st.slider("エピソード数", min_value=5, max_value=100, value=20)
        initial_balance = st.number_input("初期資金", value=100000)
        transaction_cost = st.number_input("取引コスト (%)", value=0.001, format="%.4f")

        start_btn = st.button("🚀 トレーニング開始", type="primary")

        st.info("※デモ用に生成された市場データを使用します。")

    with col2:
        if start_btn:
            run_training_session(episodes, initial_balance, transaction_cost)
        else:
            st.markdown(
                """
### ここで何ができる？

            AIエージェント（DQNモデル）が、市場データの中で**「試行錯誤」**しながら成長する様子を観察できます。

            - **Reward (報酬)**: 高いほど良い行動をとっています。
            - **Epsilon (探索率)**: 初めはランダムに動き、徐々に学習した知識を使うようになります。

            左側のボタンを押して、AIの成長を見守りましょう！
            """
            )


def run_training_session(episodes, initial_balance, transaction_cost):
    st.subheader("📊 トレーニング進捗")

    # 1. Init Data & Env
    with st.spinner("環境を構築中..."):
        df = generate_demo_market_data()
        env = TradingEnvironment(df, initial_balance=initial_balance, transaction_cost_pct=transaction_cost)

        # Init Agent
        try:
            agent = DQNAgent(env.state_size, env.action_space_size)
        except Exception as e:
            st.error(f"Agent Initialization Error: {e}")
            return

    # 2. UI Elements for updates
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Charts
    chart_placeholder = st.empty()
    metrics_placeholder = st.empty()

    rewards_history = []
    portfolio_history = []

    # 3. Training Loop
    for e in range(episodes):
        state = env.reset()
        total_reward = 0
        done = False

        while not done:
            action = agent.act(state)
            next_state, reward, done, info = env.step(action)

            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward

        # Experience Replay (Train)
        agent.replay()

        # Log Stats
        rewards_history.append(total_reward)
        final_portfolio = info["portfolio_value"]
        portfolio_history.append(final_portfolio)

        # Update UI
        progress = (e + 1) / episodes
        progress_bar.progress(progress)

        status_text.markdown(f"**Episode {e + 1}/{episodes}** | Epsilon: `{agent.epsilon:.2f}`")

        # Update Chart (Dual Axis ideally, but Streamlit line_chart is simple)
        # We plot Rewards
        chart_data = pd.DataFrame({"Reward (学習成果)": rewards_history})
        chart_placeholder.line_chart(chart_data)

        # Metrics
        latest_pnl = (final_portfolio - initial_balance) / initial_balance * 100
        metrics_placeholder.markdown(
            f"""
        - **Last Reward**: {total_reward:.2f}
        - **Current Portfolio**: {final_portfolio:,.0f} (+{latest_pnl:.2f}%)
        """
        )

        # Slight delay for visual effect
        time.sleep(0.1)

    st.success("🎉 トレーニング完了！ モデルが更新されました。")

    # Save Model
    try:
        agent.save("models/rl_gym_trained.pth")
        st.caption("モデル保存完了: `models/rl_gym_trained.pth`")
    except Exception as e:
        st.error(f"保存失敗: {e}")
