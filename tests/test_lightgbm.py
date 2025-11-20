import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from src.strategies import LightGBMStrategy

class TestLightGBMStrategy(unittest.TestCase):
    def setUp(self):
        # Create dummy data
        dates = pd.date_range(start="2020-01-01", periods=500, freq="D")
        self.df = pd.DataFrame({
            "Open": np.random.rand(500) * 100,
            "High": np.random.rand(500) * 100,
            "Low": np.random.rand(500) * 100,
            "Close": np.random.rand(500) * 100,
            "Volume": np.random.randint(1000, 10000, 500)
        }, index=dates)
        
        # Ensure High is highest and Low is lowest
        self.df['High'] = self.df[['Open', 'Close']].max(axis=1) + 1
        self.df['Low'] = self.df[['Open', 'Close']].min(axis=1) - 1

    @patch('src.strategies.fetch_macro_data')
    def test_generate_signals(self, mock_fetch_macro):
        # Mock macro data
        dates = self.df.index
        mock_macro_df = pd.DataFrame({"Close": np.random.rand(len(dates)) * 100}, index=dates)
        
        mock_fetch_macro.return_value = {
            "USDJPY": mock_macro_df,
            "SP500": mock_macro_df,
            "US10Y": mock_macro_df
        }
        
        strategy = LightGBMStrategy(lookback_days=100)
        signals = strategy.generate_signals(self.df)
        
        self.assertIsInstance(signals, pd.Series)
        self.assertEqual(len(signals), len(self.df))
        
        # Check values are -1, 0, 1
        unique_vals = signals.unique()
        for val in unique_vals:
            self.assertIn(val, [-1, 0, 1])
            
        # Check that early signals are 0 (training period)
        # We train on lookback_days (100)
        # So first 100 days should be 0
        self.assertTrue((signals.iloc[:100] == 0).all())
        
        # Check that we have signals after lookback
        # There might be some 0s if no signal, but not ALL 0s
        self.assertFalse((signals.iloc[150:] == 0).all())

if __name__ == '__main__':
    unittest.main()
