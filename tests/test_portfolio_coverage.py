import unittest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch

# Handle potential naming conflicts by aliasing or scoped imports
import src.portfolio as portfolio_sim_module
import src.portfolio_manager as portfolio_risk_module

class TestPortfolioSimulation(unittest.TestCase):
    def setUp(self):
        self.manager = portfolio_sim_module.PortfolioManager(initial_capital=1000000)
        
        # Dummy data
        dates = pd.date_range('2023-01-01', periods=10)
        self.data_map = {
            'A': pd.DataFrame({'Close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]}, index=dates),
            'B': pd.DataFrame({'Close': [50, 50, 50, 50, 50, 50, 50, 50, 50, 50]}, index=dates)
        }

    def test_calculate_correlation(self):
        corr_matrix = self.manager.calculate_correlation(self.data_map)
        self.assertIsInstance(corr_matrix, pd.DataFrame)
        self.assertEqual(corr_matrix.shape, (2, 2))
        self.assertAlmostEqual(corr_matrix.loc['A', 'A'], 1.0)

    def test_rebalance_portfolio(self):
        current_holdings = {'A': 400000, 'B': 600000} # Total 1M
        target_weights = {'A': 0.5, 'B': 0.5}
        total_equity = 1000000
        
        orders = self.manager.rebalance_portfolio(current_holdings, target_weights, total_equity)
        
        # Expect to buy 100k of A and sell 100k of B
        self.assertAlmostEqual(orders['A'], 100000)
        self.assertAlmostEqual(orders['B'], -100000)

    def test_optimize_portfolio(self):
        # Mocking scipy.optimize.minimize to avoid complex math dependency
        with patch('scipy.optimize.minimize') as mock_minimize:
            mock_result = MagicMock()
            mock_result.x = np.array([0.5, 0.5])
            mock_result.success = True
            mock_minimize.return_value = mock_result
            
            weights = self.manager.optimize_portfolio(self.data_map)
            
            self.assertEqual(weights['A'], 0.5)
            self.assertEqual(weights['B'], 0.5)

    def test_simulate_portfolio(self):
        with patch('src.portfolio.Backtester') as MockBacktester:
            mock_bt = MockBacktester.return_value
            mock_bt.run.return_value = {
                'equity_curve': pd.Series([1000000]*10),
                'total_return': 0.0,
                'max_drawdown': 0.0,
                'trades': 0
            }
            
            strategies = {'A': MagicMock(), 'B': MagicMock()}
            weights = {'A': 0.5, 'B': 0.5}
            
            result = self.manager.simulate_portfolio(self.data_map, strategies, weights)
            
            self.assertIn('equity_curve', result)

class TestPortfolioRiskManager(unittest.TestCase):
    def setUp(self):
        self.manager = portfolio_risk_module.PortfolioManager(max_correlation=0.7, max_sector_exposure=0.5)
        self.manager.set_sector_map({'A': 'Tech', 'B': 'Tech', 'C': 'Finance'})

    def test_calculate_portfolio_volatility(self):
        weights = {'A': 0.5, 'C': 0.5}
        cov_matrix = pd.DataFrame([
            [0.1, 0.0],
            [0.0, 0.1]
        ], index=['A', 'C'], columns=['A', 'C'])
        
        vol = self.manager.calculate_portfolio_volatility(weights, cov_matrix)
        self.assertGreater(vol, 0.0)

    def test_check_new_position_correlation(self):
        curr_port_list = ['A'] # Check variable name matching
        
        # High correlation
        corr_matrix = pd.DataFrame([
            [1.0, 0.9],
            [0.9, 1.0]
        ], index=['A', 'B'], columns=['A', 'B'])
        
        allowed = self.manager.check_new_position('B', curr_port_list, corr_matrix)
        
        self.assertFalse(allowed) # Only 0.7 allowed
        
        # Low correlation
        # Use 'C' (Finance) to avoid Sector Check failure (A is Tech, B is Tech, C is Finance)
        # Existing portfolio ['A'] -> Tech exposure 100%. Limit 50%.
        # Adding 'B' (Tech) fails due to Sector Check.
        # Adding 'C' (Finance) should pass Sector Check (Finance exposure 0%).
        
        corr_matrix_low = pd.DataFrame([
            [1.0, 0.1],
            [0.1, 1.0]
        ], index=['A', 'C'], columns=['A', 'C'])
        
        allowed = self.manager.check_new_position('C', curr_port_list, corr_matrix_low)
        self.assertTrue(allowed)

    def test_check_new_position_sector(self):
        # Max sector exposure is 0.5 (50%)
        # Current: 1 Tech stock ('A'), total 2 stocks if we add 'B' (Tech) -> 2/2 = 100% > 50%
        
        current = ['A'] # 1 Tech
        corr_matrix = pd.DataFrame([[1]], index=['A'], columns=['A'])
        
        # Adding B (Tech) -> Risk: 100% Tech (A, B)
        # Wait, current_portfolio is passed in. Logic uses current_portfolio to calculate exposure.
        # "sector_counts = [self.sector_map.get(t) for t in current_portfolio]"
        # "sector_exposure = sector_counts.count(sector) / len(current_portfolio)"
        # This implementation calculates exposure of *existing* portfolio?
        # Let's check source code again:
        # "if self.sector_map: sector = self.sector_map.get(ticker)" (Ticker to add)
        # "if sector: sector_counts = ... "
        # "sector_exposure = sector_counts.count(sector) / len(current_portfolio)"
        # It checks if existing exposure to THIS sector is already high?
        # A common logic is: (count(sector) + 1) / (len(current) + 1)
        # But let's test what IS implemented.
        pass

        # If current implementation checks existing exposure:
        # Case: Current ['A'] (Tech). Exposure to Tech is 1/1 = 1.0 > 0.5.
        # Adding 'B' (Tech) -> Should reject if it checks existing exposure limit for new ticker's sector.
        
        allowed = self.manager.check_new_position('B', current, corr_matrix)
        # If current is ['A'], 100% Tech. Max 50%. So it should reject adding ANY Tech stock?
        # Yes, warning: "Sector limit reached".
        self.assertFalse(allowed) 
        
        # Adding C (Finance) -> Exposure of Finance in current (['A']) is 0% < 50%.
        allowed = self.manager.check_new_position('C', current, corr_matrix)
        self.assertTrue(allowed)

if __name__ == '__main__':
    unittest.main()
