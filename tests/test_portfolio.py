import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.portfolio import PortfolioManager
from src.strategies import RSIStrategy

class TestPortfolio(unittest.TestCase):
    def setUp(self):
        # Create mock data for 3 stocks
        dates = pd.date_range(start="2023-01-01", periods=100)
        
        self.data_map = {}
        for ticker in ['STOCK_A', 'STOCK_B', 'STOCK_C']:
            self.data_map[ticker] = pd.DataFrame({
                "Open": np.random.rand(100) * 100 + 100,
                "High": np.random.rand(100) * 100 + 110,
                "Low": np.random.rand(100) * 100 + 90,
                "Close": np.random.rand(100) * 100 + 100,
                "Volume": np.random.rand(100) * 1000
            }, index=dates)

    def test_correlation_calculation(self):
        pm = PortfolioManager()
        corr_matrix = pm.calculate_correlation(self.data_map)
        
        # Should return a 3x3 matrix
        self.assertEqual(corr_matrix.shape, (3, 3))
        # Diagonal should be 1.0 (perfect correlation with itself)
        self.assertTrue(np.allclose(np.diag(corr_matrix.values), 1.0))

    def test_portfolio_simulation(self):
        pm = PortfolioManager(initial_capital=1000000)
        
        weights = {'STOCK_A': 0.4, 'STOCK_B': 0.3, 'STOCK_C': 0.3}
        strategies = {ticker: RSIStrategy() for ticker in weights.keys()}
        
        result = pm.simulate_portfolio(self.data_map, strategies, weights)
        
        self.assertIsNotNone(result)
        self.assertIn('equity_curve', result)
        self.assertIn('total_return', result)
        self.assertIn('max_drawdown', result)

if __name__ == "__main__":
    unittest.main()
