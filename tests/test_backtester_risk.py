import os
import sys
import unittest

import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.backtester import Backtester
from src.strategies import Strategy

class MockStrategy(Strategy):
    def __init__(self, signals):
        super().__init__("Mock")
        self.signals = signals

    def generate_signals(self, df):
        return self.signals

class TestBacktesterRisk(unittest.TestCase):
    def setUp(self):
        dates = pd.date_range(start="2023-01-01", periods=5)
        # Price goes UP: 100 -> 110 -> 120 -> 130 -> 140
        self.df = pd.DataFrame({
            "Open": [100, 110, 120, 130, 140],
            "High": [105, 115, 125, 135, 145],
            "Low": [95, 105, 115, 125, 135],
            "Close": [110, 120, 130, 140, 150],
            "Volume": [1000]*5
        }, index=dates)

    def test_position_size(self):
        # Signal 1 on Day 1.
        signals = pd.Series([0, 1, 0, 0, 0], index=self.df.index)
        strategy = MockStrategy(signals)
        
        # Full Position (disable stop_loss/take_profit for clean test)
        bt_full = Backtester(position_size=1.0, commission=0, slippage=0)
        res_full = bt_full.run(self.df, strategy, stop_loss=None, take_profit=None)
        
        # Half Position
        bt_half = Backtester(position_size=0.5, commission=0, slippage=0)
        res_half = bt_half.run(self.df, strategy, stop_loss=None, take_profit=None)
        
        # Return should be roughly half
        self.assertGreater(res_full['total_return'], res_half['total_return'])
        # Check if it's within reasonable range (0.4 to 0.6 ratio)
        ratio = res_half['total_return'] / res_full['total_return']
        self.assertTrue(0.4 <= ratio <= 0.6, f"Ratio {ratio} is not close to 0.5")

if __name__ == "__main__":
    unittest.main()
