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
    pass


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
    #     def __init__(self):
    if self._initialized:
        return
        self.thread: Optional[threading.Thread] = None
    self.stop_event = threading.Event()
    self.is_running = False


# State
self.progress = 0.0
self.current_episode = 0
#         self.total_episodes = 0
#         self.metrics: List[Dict[str, Any]] = []  # {episode, reward, loss, epsilon}
#         self.status_message = "Idle"
#         self.agent: Optional[DQNAgent] = None
#             self.last_trade_history: List[Dict[str, Any]] = []  # For Replay Cinema
#             self._initialized = True
#     def start_training(self, ticker: str, episodes: int = 50, window_size: int = 10):
#         pass
#         if self.is_running:
#             logger.warning("Training already in progress.")
#             return
#             self.stop_event.clear()
#         self.metrics = []
#         self.last_trade_history = []
#         self.current_episode = 0
#         self.total_episodes = episodes
#         self.progress = 0.0
#         self.status_message = f"Preparing data for {ticker}..."
#         self.is_running = True
#             self.thread = threading.Thread(target=self._training_loop, args=(ticker, episodes, window_size), daemon=True)
#         self.thread.start()
#     def stop_training(self):
#         pass
#         """Signals the training thread to stop."""
if self.is_running:
    self.stop_event.set()
    self.status_message = "Stopping..."
    #     def _training_loop(self, ticker: str, episodes: int, window_size: int):
    #         pass
    #         try:
    # 1. Fetch Data
    data_map = fetch_stock_data([ticker], period="2y")
    df = data_map.get(ticker)
#                 if df is None or len(df) < window_size + 100:
#                     self.status_message = f"Insufficient data for {ticker}"
#                 self.is_running = False
#                 return
# 2. Setup Env & Agent
env = StockTradingEnv(df)
state_size = env.observation_space.shape[0]
#             action_size = env.action_space.n
# Using try-except for agent init in case torch is missing
# try:
#                 self.agent = DQNAgent(state_size, action_size)
