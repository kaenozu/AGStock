import logging

import numpy as np
import pandas as pd

from src.data_loader import fetch_stock_data
from src.features import add_advanced_features
from src.rl.agent import DQNAgent
from src.rl.environment import TradingEnvironment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_mock():
    print("Fetching data for training...")
    df = fetch_stock_data("7203.T", period="2y")  # Toyota as sample
    if df.empty:
        print("No data fetched.")
        return

    print("Adding features...")
    df = add_advanced_features(df)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df_numeric = df[numeric_cols].fillna(0)

    print("Initializing Environment and Agent...")
    env = TradingEnvironment(df_numeric)
    agent = DQNAgent(env.state_size, env.action_space_size)

    print("Starting training (5 episodes)...")
    episodes = 5
    for e in range(episodes):
        state = env.reset()
        done = False
        total_reward = 0

        while not done:
            action = agent.act(state)
            next_state, reward, done, _ = env.step(action)
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            agent.replay()

        agent.update_target_model()
        print(f"Episode {e+1}/{episodes} - Reward: {total_reward:.2f}, Epsilon: {agent.epsilon:.2f}")

    print("Saving model...")
    agent.save("models/rl_dqn.pth")
    print("Done.")


if __name__ == "__main__":
    train_mock()
