import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.optimizer import Optimizer

class TestOptimizer(unittest.TestCase):
    def setUp(self):
        # Create mock data
        dates = pd.date_range(start="2023-01-01", periods=200)
        # Create a sine wave pattern to ensure some trades happen
        x = np.linspace(0, 10 * np.pi, 200)
        prices = 100 + 10 * np.sin(x) + np.random.normal(0, 1, 200)
        
        data = {
            "Open": prices,
            "High": prices + 1,
            "Low": prices - 1,
            "Close": prices,
            "Volume": np.random.randint(1000, 10000, 200)
        }
        self.df = pd.DataFrame(data, index=dates)

    def test_optimize_rsi(self):
        optimizer = Optimizer(self.df, "RSI Reversal")
        params, value = optimizer.optimize(n_trials=2)
        self.assertIsInstance(params, dict)
        self.assertIn("period", params)
        self.assertIn("lower", params)

    def test_optimize_combined(self):
        optimizer = Optimizer(self.df, "Combined")
        params, value = optimizer.optimize(n_trials=2)
        self.assertIsInstance(params, dict)
        self.assertIn("rsi_period", params)
        self.assertIn("bb_length", params)

if __name__ == "__main__":
    unittest.main()
