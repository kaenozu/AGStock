import logging
from typing import Any, Dict, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TradingEnvironment:
    #     """
    #     強化学習用の取引環境 (Gymnasiumライクなインターフェース)
    #     """

    def __init__(self, df: pd.DataFrame, initial_balance: float = 1000000.0):
        self.df = df.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.commission_rate = 0.001  # 0.1%
        self.action_space_size = 3
        self.feature_cols = [
            c
            for c in df.columns
            if c not in ["Date", "Open", "High", "Low", "Close", "Volume", "Target"]
        ]
        self.feature_cols = (
            df[self.feature_cols].select_dtypes(include=[np.number]).columns.tolist()
        )
        self.state_size = 2 + len(self.feature_cols)
        self.reset()

    def reset(self) -> np.ndarray:
        #         """環境を初期化し、初期状態を返す"""
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0  # 0: No position, 1: Long
        self.entry_price = 0.0
        self.total_profit = 0.0
        self.trades = []
        return self._get_state()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        #         """行動を実行し、次状態、報酬、終了フラグ、情報を返す"""
        current_price = self.df.loc[self.current_step, "Close"]
        reward = 0.0
        done = False

        if action == 1:  # BUY
            if self.position == 0:
                self.position = 1
                self.entry_price = current_price
                reward -= current_price * self.commission_rate
        elif action == 2:  # SELL
            if self.position == 1:
                profit = current_price - self.entry_price
                cost = current_price * self.commission_rate
                realized_pnl = profit - cost
                self.balance += realized_pnl
                self.total_profit += realized_pnl
                reward += realized_pnl
                self.position = 0
                self.trades.append(
                    {
                        "step": self.current_step,
                        "type": "SELL",
                        "price": current_price,
                        "pnl": realized_pnl,
                    }
                )

        self.current_step += 1
        if self.current_step >= len(self.df) - 1:
            done = True

        next_state = self._get_state()
        info = {
            "balance": self.balance,
            "total_profit": self.total_profit,
            "position": self.position,
        }
        return next_state, reward, done, info

    def _get_state(self) -> np.ndarray:
        #         """現在の状態ベクトルを取得"""
        if self.current_step >= len(self.df):
            return np.zeros(self.state_size)

        features = self.df.loc[self.current_step, self.feature_cols].values
        features = np.nan_to_num(features)
        position_state = np.array([self.position])

        pnl_ratio = 0.0
        if self.position == 1:
            current_price = self.df.loc[self.current_step, "Close"]
            pnl_ratio = (current_price - self.entry_price) / self.entry_price
        pnl_state = np.array([pnl_ratio])

        state = np.concatenate([position_state, pnl_state, features])
        return state
