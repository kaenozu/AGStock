import unittest
import pandas as pd
import numpy as np
from src.portfolio import PortfolioManager

class TestPortfolioOptimization(unittest.TestCase):
    def setUp(self):
        self.pm = PortfolioManager()
        
        # Create dummy data for 3 assets
        # Asset A: Low return, Low volatility
        # Asset B: High return, High volatility
        # Asset C: Negative correlation with B
        
        dates = pd.date_range(start="2020-01-01", periods=252, freq="D")
        
        np.random.seed(42)
        
        # Returns
        r_a = np.random.normal(0.0005, 0.01, 252) # ~12% return, 16% vol
        r_b = np.random.normal(0.001, 0.02, 252)  # ~25% return, 32% vol
        r_c = -0.5 * r_b + np.random.normal(0.0005, 0.01, 252) # Hedge
        
        # Prices
        p_a = 100 * (1 + r_a).cumprod()
        p_b = 100 * (1 + r_b).cumprod()
        p_c = 100 * (1 + r_c).cumprod()
        
        self.data_map = {
            "A": pd.DataFrame({"Close": p_a}, index=dates),
            "B": pd.DataFrame({"Close": p_b}, index=dates),
            "C": pd.DataFrame({"Close": p_c}, index=dates)
        }

    def test_optimize_portfolio(self):
        weights = self.pm.optimize_portfolio(self.data_map)
        
        # Check weights sum to 1
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=4)
        
        # Check all assets are present
        self.assertEqual(len(weights), 3)
        self.assertIn("A", weights)
        self.assertIn("B", weights)
        self.assertIn("C", weights)
        
        # Check bounds
        for w in weights.values():
            self.assertGreaterEqual(w, 0.0)
            self.assertLessEqual(w, 1.0001)

if __name__ == '__main__':
    unittest.main()
