"""
Production RL Training Script
Trains the DQN Agent on historical data and saves the optimized model.
"""

import logging
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from src.data_loader import fetch_stock_data
from src.features import add_advanced_features
from src.rl.agent import DQNAgent
from src.rl.environment import TradingEnvironment

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def train_agent(ticker: str = "7203.T", episodes: int = 20, period: str = "2y"):
    logger.info(f"🚀 Starting RL Training for {ticker} over {period}...")
    
    # 1. Data Preparation
    try:
        df = fetch_stock_data(ticker, period=period)
        if df.empty:
            logger.error("No data fetched. Aborting.")
            return
        
        df = add_advanced_features(df)
        df = df.fillna(method="ffill").fillna(0)
    except Exception as e:
        logger.error(f"Data prep failed: {e}")
        return

    # 2. Env & Agent Initialization
    env = TradingEnvironment(df)
    agent = DQNAgent(env.state_size, env.action_space_size)
    
    performance_history = []
    logger.info(f"State Size: {env.state_size}, Action Space: {env.action_space_size}")

    # 3. Training Loop
    start_time = datetime.now()
    for e in range(episodes):
        state = env.reset()
        total_reward = 0
        done = False
        
        while not done:
            action = agent.act(state)
            next_state, reward, done, info = env.step(action)
            
            # Learn from transition
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            
            # Experience Replay
            if len(agent.memory) > agent.batch_size:
                agent.replay()
        
        agent.update_target_model()
        final_value = env.portfolio_value
        pnl_pct = (final_value - env.initial_balance) / env.initial_balance * 100
        performance_history.append(pnl_pct)
        
        logger.info(
            f"Episode {e+1:02d}/{episodes} | "
            f"Reward: {total_reward:7.2f} | "
            f"End Value: ¥{final_value:,.0f} ({pnl_pct:+.1f}%) | "
            f"Epsilon: {agent.epsilon:.2f}"
        )

    duration = datetime.now() - start_time
    logger.info(f"✅ Training completed in {duration.total_seconds():.1f}s")

    # 4. Save Artifacts
    if not os.path.exists("models"):
        os.makedirs("models")
        
    model_path = "models/rl_dqn.pth"
    agent.save(model_path)
    logger.info(f"💾 Model saved to {model_path}")

    # 🏷️ Save simple training log for Dashboard
    log_path = "data/rl_training_log.csv"
    os.makedirs("data", exist_ok=True)
    log_df = pd.DataFrame({
        "episode": range(1, episodes + 1),
        "pnl_pct": performance_history,
        "timestamp": datetime.now().isoformat()
    })
    log_df.to_csv(log_path, index=False)
    logger.info("📊 Training log saved for dashboard insights.")

if __name__ == "__main__":
    # In practice, we could train on multiple tickers
    train_agent(episodes=15) # Quick training session
