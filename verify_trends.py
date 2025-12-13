"""
Verify Trends
マルチタイムフレームトレンドの挙動を確認する
"""

import os
import sys

sys.path.insert(0, os.getcwd())

from src.dashboard_utils import get_multi_timeframe_trends

print("Fetching Trends for ^N225...")
trends = get_multi_timeframe_trends("^N225")
print(f"Trends: {trends}")
