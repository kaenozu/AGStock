import threading
import time
import logging
import numpy as np
from typing import Optional, Dict, Any, List
import pandas as pd
from src.rl.agent import DQNAgent
from src.rl.environment import StockTradingEnv
from src.data_loader import fetch_stock_data
logger = logging.getLogger(__name__)
class TrainingSessionManager:
#     """
#     Manages a background training session for an RL agent.
#     Allows starting, stopping, and monitoring progress from the UI.
#     _instance = None
#     """
def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TrainingSessionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    def __init__(self):
        if self._initialized:
            return
            self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.is_running = False
# State
self.progress = 0.0
        self.current_episode = 0
        self.total_episodes = 0
        self.metrics: List[Dict[str, Any]] = []  # {episode, reward, loss, epsilon}
        self.status_message = "Idle"
        self.agent: Optional[DQNAgent] = None
            self.last_trade_history: List[Dict[str, Any]] = []  # For Replay Cinema
            self._initialized = True
    def start_training(self, ticker: str, episodes: int = 50, window_size: int = 10):
        pass
        if self.is_running:
            logger.warning("Training already in progress.")
            return
            self.stop_event.clear()
        self.metrics = []
        self.last_trade_history = []
        self.current_episode = 0
        self.total_episodes = episodes
        self.progress = 0.0
        self.status_message = f"Preparing data for {ticker}..."
        self.is_running = True
            self.thread = threading.Thread(target=self._training_loop, args=(ticker, episodes, window_size), daemon=True)
        self.thread.start()
    def stop_training(self):
#         """Signals the training thread to stop."""
if self.is_running:
            self.stop_event.set()
            self.status_message = "Stopping..."
    def _training_loop(self, ticker: str, episodes: int, window_size: int):
        pass
        try:
            # 1. Fetch Data
            data_map = fetch_stock_data([ticker], period="2y")
            df = data_map.get(ticker)
                if df is None or len(df) < window_size + 100:
                    self.status_message = f"Insufficient data for {ticker}"
                self.is_running = False
                return
# 2. Setup Env & Agent
env = StockTradingEnv(df)
            state_size = env.observation_space.shape[0]
            action_size = env.action_space.n
# Using try-except for agent init in case torch is missing
try:
                self.agent = DQNAgent(state_size, action_size)
            except ImportError:
                self.status_message = "PyTorch not found. Cannot train."
                self.is_running = False
                return
                self.status_message = f"Training started ({episodes} episodes)..."
# 3. Training Loop
for e in range(1, episodes + 1):
                if self.stop_event.is_set():
                    self.status_message = "Training stopped by user."
                    break
                    state = env.reset()
# state = np.reshape(state, [1, state_size]) # Removed reshape
total_reward = 0
                avg_loss = 0
                steps = 0
# Keep track of trades in this episode
episode_trades = []
                    done = False
                while not done:
                    # Get price info for recording
                    current_price = env.df.iloc[env.current_step]["Close"]
                    current_time = env.df.index[env.current_step]
                        action = self.agent.act(state)
                    next_state, reward, done, _ = env.step(action)
# next_state = np.reshape(next_state, [1, state_size]) # Removed reshape
self.agent.remember(state, action, reward, next_state, done)
                    state = next_state
                        total_reward += reward
                    steps += 1
# Record Trade for Cinema
if action in [1, 2]:  # BUY or SELL
                        episode_trades.append(
                            {
                                "step": env.current_step,
                                "price": current_price,
                                "action": "BUY" if action == 1 else "SELL",
                                "date": str(current_time),
                            }
                        )
# Replay (Learn)
if len(self.agent.memory) > self.agent.batch_size:
                        loss = self.agent.replay()
                        if loss:
                            avg_loss += loss
# Episode complete
avg_loss = avg_loss / steps if steps > 0 else 0
# Update history if this episode was good (or just save the last one for now)
# Ideally save the best, but saving last allows seeing the "latest" behavior.
self.last_trade_history = episode_trades
# Record metrics
metric = {"episode": e, "reward": total_reward, "loss": avg_loss, "epsilon": self.agent.epsilon}
                self.metrics.append(metric)
                self.agent.training_history.append(metric)  # Sync with agent's internal history
                    self.current_episode = e
                self.progress = e / episodes
                self.status_message = f"Training: Ep {e}/{episodes} | Reward: {total_reward:.2f}"
# Quick update target occasionally (e.g. every 5 eps)
if e % 5 == 0:
                    self.agent.update_target_model()
# 4. Finish
if not self.stop_event.is_set():
                self.status_message = "Training Complete!"
# Save model
save_path = f"models/rl/dqn_{ticker}_latest.pth"
                self.agent.save(save_path)
                logger.info(f"Training finished. Model saved to {save_path}")
            except Exception as e:
                logger.error(f"Training failed: {e}")
            self.status_message = f"Error: {e}"
        finally:
            self.is_running = False
    def get_status(self) -> Dict[str, Any]:
#         """Returns the current status snapshot for UI."""
        return {
            "is_running": self.is_running,
            "progress": self.progress,
            "current_episode": self.current_episode,
            "total_episodes": self.total_episodes,
            "status_message": self.status_message,
            "metrics": self.metrics,
            "trade_history": self.last_trade_history,  # New field
        }


# """
