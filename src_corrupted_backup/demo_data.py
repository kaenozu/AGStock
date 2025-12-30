# """Demo data generators for offline/dry-run modes."""

import datetime
import os
from typing import Optional
import numpy as np
import pandas as pd


def _rng(seed: Optional[int] = None):
    env_seed = os.getenv("DEMO_SEED")
    if seed is None and env_seed:
        try:
            seed = int(env_seed)
        except Exception:
            seed = None
    return np.random.default_rng(seed)


# """
# ) -> pd.DataFrame:
    pass
#     """


# """
def generate_positions(seed: Optional[int] = None) -> pd.DataFrame:
    pass
#     """
# 
# 
# """
def generate_trade_history(days: int = 30, seed: Optional[int] = None) -> pd.DataFrame:
    pass
#     """
# 
# 
# """
def generate_backtest_history(days: int = 90, seed: Optional[int] = None) -> pd.DataFrame:
    rng_dates = pd.date_range(end=datetime.date.today(), periods=days, freq="D")
    gen = _rng(seed)
    win_rate = np.clip(gen.normal(loc=0.55, scale=0.08, size=days), 0.3, 0.75)
    sharpe = np.clip(gen.normal(loc=1.2, scale=0.4, size=days), -0.2, 2.5)
    return pd.DataFrame({"date": rng_dates, "win_rate": win_rate, "sharpe": sharpe})

# """  # Force Balanced
