import os
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.strategies import MLStrategy


class TestMLStrategy(unittest.TestCase):
    def setUp(self):
        # Create enough data for ML (needs > 100 rows)
        dates = pd.date_range(start="2022-01-01", periods=200)
        self.df = pd.DataFrame(
            {
                "Open": np.random.rand(200) * 100,
                "High": np.random.rand(200) * 100,
                "Low": np.random.rand(200) * 100,
                "Close": np.random.rand(200) * 100,
                "Volume": np.random.rand(200) * 1000,
            },
            index=dates,
        )

        # Make Close follow a trend to make it learnable?
        # Random data is fine just to check if it crashes.

    def test_initialization(self):
        strategy = MLStrategy()
        self.assertEqual(strategy.name, "AI Random Forest")

    def test_generate_signals(self):
        strategy = MLStrategy()
        signals = strategy.generate_signals(self.df)

        self.assertEqual(len(signals), len(self.df))
        # Check if signals are -1, 0, 1
        unique_signals = signals.unique()
        for s in unique_signals:
            self.assertIn(s, [-1, 0, 1])

    def test_insufficient_data(self):
        short_df = self.df.iloc[:50]
        strategy = MLStrategy()
        signals = strategy.generate_signals(short_df)
        # Should return all 0s or empty
        self.assertTrue((signals == 0).all())


if __name__ == "__main__":
    unittest.main()
