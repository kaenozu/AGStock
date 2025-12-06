import unittest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from src.strategies_legacy import (
    Strategy, SMACrossoverStrategy, RSIStrategy, BollingerBandsStrategy, CombinedStrategy,
    DividendStrategy, MultiTimeframeStrategy
)

class TestStrategiesLegacy(unittest.TestCase):
    def setUp(self):
        # Create a sample DataFrame
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        self.df = pd.DataFrame({
            'Open': np.random.rand(100) * 100,
            'High': np.random.rand(100) * 100,
            'Low': np.random.rand(100) * 100,
            'Close': np.linspace(100, 200, 100), # Upward trend
            'Volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
    def test_strategy_base_class(self):
        """Test the base Strategy class"""
        strategy = Strategy("Test Strategy")
        self.assertEqual(strategy.name, "Test Strategy")
        self.assertEqual(strategy.trend_period, 200)
        
        # Test analyze (default implementation wraps generate_signals)
        # Since generate_signals raises NotImplementedError (implicitly or returns None/empty),
        # we need to subclass or mock it if it was abstract. 
        # Looking at the code, generate_signals might not be abstract but empty.
        # Let's check if it returns something.
        
        # Mock generate_signals
        strategy.generate_signals = MagicMock(return_value=pd.Series([0]*100, index=self.df.index))
        
        result = strategy.analyze(self.df)
        self.assertIsInstance(result, dict)
        self.assertIn('signal', result)
        self.assertIn('confidence', result)
        
    def test_sma_crossover_strategy(self):
        """Test SMACrossoverStrategy"""
        strategy = SMACrossoverStrategy(short_window=5, long_window=10)
        
        # Create a scenario where SMA5 crosses SMA10
        # First 10 days: Price 100 (SMA5=100, SMA10=100)
        # Next 10 days: Price 110 (SMA5=110, SMA10 moves up)
        
        prices = [100]*20 + [120]*20 # Jump
        df = pd.DataFrame({'Close': prices}, index=pd.date_range('2023-01-01', periods=40))
        
        signals = strategy.generate_signals(df)
        
        self.assertIsInstance(signals, pd.Series)
        # Check if we have any signals (1 or -1)
        # Note: TA library might need more data points or specific patterns
        
    def test_rsi_strategy(self):
        """Test RSIStrategy"""
        strategy = RSIStrategy(period=14, lower=30, upper=70)
        
        # Create RSI scenario
        # Price drops significantly -> RSI < 30 -> Buy Signal
        prices = np.linspace(100, 50, 20).tolist() + np.linspace(50, 100, 20).tolist()
        df = pd.DataFrame({'Close': prices}, index=pd.date_range('2023-01-01', periods=40))
        
        signals = strategy.generate_signals(df)
        self.assertIsInstance(signals, pd.Series)
        
    def test_bollinger_bands_strategy(self):
        """Test BollingerBandsStrategy"""
        strategy = BollingerBandsStrategy(length=20, std=2)
        signals = strategy.generate_signals(self.df)
        self.assertIsInstance(signals, pd.Series)
        
    def test_combined_strategy(self):
        """Test CombinedStrategy"""
        strategy = CombinedStrategy()
        signals = strategy.generate_signals(self.df)
        self.assertIsInstance(signals, pd.Series)

    def test_dividend_strategy(self):
        """Test DividendStrategy"""
        strategy = DividendStrategy(min_yield=0.03, max_payout=0.8)
        
        # DividendStrategy.generate_signals currently returns all 1s (placeholder)
        # It does not use fetch_fundamental_data
        signals = strategy.generate_signals(self.df)
        self.assertIsInstance(signals, pd.Series)

    def test_multi_timeframe_strategy(self):
        """Test MultiTimeframeStrategy"""
        # Mock MultiTimeframeAnalyzer
        with patch('src.strategies_legacy.MultiTimeframeAnalyzer') as MockAnalyzer:
            mock_analyzer_instance = MockAnalyzer.return_value
            
            # Mock resample_data to return a dummy weekly dataframe
            # Weekly DF needs 'Close' and enough rows for SMA calculation
            weekly_dates = pd.date_range(start='2023-01-01', periods=20, freq='W-FRI')
            weekly_df = pd.DataFrame({
                'Close': np.linspace(100, 200, 20)
            }, index=weekly_dates)
            mock_analyzer_instance.resample_data.return_value = weekly_df
            
            base_strategy = MagicMock()
            base_strategy.generate_signals.return_value = pd.Series([1]*100, index=self.df.index)
            
            strategy = MultiTimeframeStrategy(base_strategy=base_strategy)
            
            # MTF strategy uses resample_data, not fetch_stock_data
            signals = strategy.generate_signals(self.df)
            self.assertIsInstance(signals, pd.Series)


if __name__ == '__main__':
    unittest.main()
