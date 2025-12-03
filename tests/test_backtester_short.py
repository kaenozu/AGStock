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

class TestBacktesterShort(unittest.TestCase):
    def setUp(self):
        dates = pd.date_range(start="2023-01-01", periods=5)
        # Price goes DOWN: 100 -> 90 -> 80 -> 70 -> 60
        self.df = pd.DataFrame({
            "Open": [100, 90, 80, 70, 60],
            "High": [105, 95, 85, 75, 65],
            "Low": [95, 85, 75, 65, 55],
            "Close": [90, 80, 70, 60, 50],
            "Volume": [1000]*5
        }, index=dates)

    def test_short_selling_profit(self):
        # Signal -1 on Day 1.
        signals = pd.Series([0, -1, 0, 0, 0], index=self.df.index)
        strategy = MockStrategy(signals)
        
        # Allow Short
        backtester = Backtester(allow_short=True, commission=0, slippage=0)
        res = backtester.run(self.df, strategy, stop_loss=0.5, take_profit=0.5)
        
        # Should have entered Short
        # Entry at Day 2 Open (80)
        # Price drops to 50.
        # Return should be positive.
        
        self.assertGreater(res['total_return'], 0)
        # Check if position is -1 at the end
        self.assertEqual(res['positions'].iloc[-1], -1)

    def test_no_short_selling(self):
        signals = pd.Series([0, -1, 0, 0, 0], index=self.df.index)
        strategy = MockStrategy(signals)
        
        # No Short
        backtester = Backtester(allow_short=False)
        res = backtester.run(self.df, strategy)
        
        # Should not enter
        self.assertEqual(res['total_trades'], 0)
        self.assertEqual(res['total_return'], 0)

if __name__ == "__main__":
    unittest.main()
