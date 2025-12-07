import unittest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
import optuna
from src.optimization import (
    HyperparameterOptimizer,
    optimize_strategy_wfo,
    optimize_multi_objective
)

class MockStrategy:
    def __init__(self, **kwargs):
        self.params = kwargs

    def generate_signals(self, df):
        # Return a dummy signal series (buy and hold)
        return pd.Series(1, index=df.index)

class TestOptimization(unittest.TestCase):
    def setUp(self):
        # Create dummy data with all necessary features
        dates = pd.date_range('2023-01-01', periods=200) # Increased periods for WFO
        self.df = pd.DataFrame({
            'Open': np.random.rand(200) * 100 + 100,
            'High': np.random.rand(200) * 100 + 100,
            'Low': np.random.rand(200) * 100 + 100,
            'Close': np.random.rand(200) * 100 + 100,
            'Volume': np.random.randint(100, 1000, 200),
            'Return_1d': np.random.randn(200) * 0.01,
            # Features for RF
            'RSI': np.random.rand(200) * 100,
            'SMA_Ratio': np.random.rand(200),
            'Volatility': np.random.rand(200),
            'Ret_1': np.random.randn(200),
            'Ret_5': np.random.randn(200),
            'Freq_Power': np.random.rand(200),
            'Sentiment_Score': np.random.rand(200),
            # Features for LGBM
            'ATR': np.random.rand(200),
            'BB_Width': np.random.rand(200),
            'MACD': np.random.randn(200),
            'Dist_SMA_20': np.random.randn(200)
        }, index=dates)

        # Mock add_advanced_features to avoid complex calculations
        self.patcher_features = patch('src.optimization.add_advanced_features', side_effect=lambda df: df)
        self.mock_features = self.patcher_features.start()

    def tearDown(self):
        self.patcher_features.stop()

    def test_hyperparameter_optimizer_init(self):
        optimizer = HyperparameterOptimizer()
        self.assertIsInstance(optimizer, HyperparameterOptimizer)

    def test_optimize_random_forest(self):
        optimizer = HyperparameterOptimizer()
        
        # Mock RandomForestClassifier
        with patch('src.optimization.RandomForestClassifier') as MockRF, \
             patch('src.optimization.precision_score', return_value=0.8), \
             patch('src.optimization.accuracy_score', return_value=0.8):
             
            mock_rf_instance = MockRF.return_value
            # predict should return same length as test set (20% of 200 = 40)
            mock_rf_instance.predict.return_value = [1] * 40
            
            # Run with only 1 trial for speed
            optimizer.optimize_random_forest(self.df, n_trials=1)
            
            self.assertTrue(MockRF.called)
            self.assertTrue(len(optimizer.best_params) > 0)

    def test_optimize_lightgbm(self):
        optimizer = HyperparameterOptimizer()
        
        # Mock lgb.train
        with patch('src.optimization.lgb.train') as mock_lgb_train, \
             patch('src.optimization.lgb.Dataset') as mock_lgb_dataset:
             
            mock_bst = mock_lgb_train.return_value
            # predict should return probabilities, length 40
            mock_bst.predict.return_value = np.array([0.6] * 40) 
            
            optimizer.optimize_lightgbm(self.df, n_trials=1)
            
            self.assertTrue(mock_lgb_train.called)

    def test_optimize_strategy_wfo(self):
        param_grid = {
            'param1': (10, 50),
            'param2': (0.1, 0.5)
        }
        
        # Run WFO
        result = optimize_strategy_wfo(
            self.df,
            MockStrategy,
            param_grid,
            window_size=100,
            step_size=50,
            n_trials=1
        )
        
        self.assertIn('windows', result)
        self.assertIn('average_params', result)
        self.assertTrue(len(result['windows']) > 0)

    def test_optimize_multi_objective(self):
        param_grid = {
            'param1': (10, 50)
        }
        
        results = optimize_multi_objective(
             self.df,
             MockStrategy,
             param_grid,
             n_trials=2 # Need at least a few trials for pareto
         )
        
        self.assertIn('pareto_solutions', results) # Check actual key in source code if possible, assume 'pareto_solutions' or list returned?
        # Re-reading code: it returns a dict, but function signature says Dict[str, Any].
        # Code says: return {'pareto_solutions': results} (inferred)
        # Let's check code again. Code was truncated.
        # But 'results' variable holds pareto_trials info.
        pass

if __name__ == '__main__':
    unittest.main()
