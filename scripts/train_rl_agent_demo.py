import logging
import pandas as pd
import numpy as np
import sys
import os
import matplotlib.pyplot as plt

# Ensure src is in path
sys.path.append(os.getcwd())

from src.rl.environment import TradingEnvironment
from src.rl.agent import DQNAgent

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_market_data(length=1000):
    """Generate synthetic market data with trends and noise"""
    x = np.linspace(0, 100, length)
    # Trend + Sine Wave + Noise
    prices = 100 + (x * 0.5) + 10 * np.sin(x * 0.2) + np.random.normal(0, 2, length)
    
    df = pd.DataFrame({
        "Open": prices,
        "High": prices + 2,
        "Low": prices - 2,
        "Close": prices,
        "Volume": np.random.randint(1000, 5000, length)
    })
    return df

def train_agent():
    logger.info("🚀 Starting RL Training Demo...")
    
    # 1. Prepare Data
    df = generate_market_data()
    logger.info(f"Generated market data: {len(df)} candles")

    # 2. Init Environment
    # Fee: 0.1%
    env = TradingEnvironment(df, initial_balance=100000, transaction_cost_pct=0.001)
    
    # 3. Init Agent
    try:
        agent = DQNAgent(env.state_size, env.action_space_size)
    except Exception as e:
        logger.error(f"Failed to init Agent (Torch missing?): {e}")
        return

    # 4. Training Loop
    episodes = 20 # Short run for demo
    batch_size = 32
    
    scores = []
    
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
            
        # Experience Replay
        if len(agent.memory) > batch_size:
            agent.replay()
            
        scores.append(total_reward)
        logger.info(f"Episode: {e+1}/{episodes} | Reward: {total_reward:.2f} | End Balance: {info['balance']:.0f} | Portfolio: {info['portfolio_value']:.0f} | Epsilon: {agent.epsilon:.2f}")

    # 5. Save
    model_path = "models/dqn_demo_agent.pth"
    agent.save(model_path)
    logger.info(f"💾 Model saved to {model_path}")
    
    logger.info("✅ Training Demo Complete!")

if __name__ == "__main__":
    train_agent()
