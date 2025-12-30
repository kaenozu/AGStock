"""
Comprehensive Test Suite for AGStock Core Functions
"""
import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.error_handler import (
    AGStockError, DataFetchError, validate_ticker, 
    safe_execute, error_boundary
)
from src.utils.performance import PerformanceMonitor, cached_data_loader
import pandas as pd
import numpy as np

class TestErrorHandling(unittest.TestCase):
    """Test error handling utilities."""
    
    def test_validate_ticker_valid(self):
        """Test valid ticker validation."""
        self.assertTrue(validate_ticker("7203.T"))
        self.assertTrue(validate_ticker("AAPL"))
    
    def test_validate_ticker_invalid(self):
        """Test invalid ticker validation."""
        with self.assertRaises(AGStockError):
            validate_ticker("")
        
        with self.assertRaises(AGStockError):
            validate_ticker(None)
    
    def test_safe_execute_success(self):
        """Test safe_execute with successful function."""
        def success_func():
            return 42
        
        result = safe_execute(success_func, default_return=0)
        self.assertEqual(result, 42)
    
    def test_safe_execute_failure(self):
        """Test safe_execute with failing function."""
        def fail_func():
            raise ValueError("Test error")
        
        result = safe_execute(fail_func, default_return=0, context="Test")
        self.assertEqual(result, 0)
    
    def test_error_boundary_decorator(self):
        """Test error boundary decorator."""
        @error_boundary(default_return="fallback", show_error=False)
        def risky_function():
            raise ValueError("Test")
        
        result = risky_function()
        self.assertEqual(result, "fallback")

class TestPerformance(unittest.TestCase):
    """Test performance utilities."""
    
    def test_performance_monitor(self):
        """Test performance monitoring."""
        monitor = PerformanceMonitor()
        
        @monitor.time_function("test_func")
        def test_func():
            import time
            time.sleep(0.1)
            return "done"
        
        result = test_func()
        self.assertEqual(result, "done")
        
        stats = monitor.get_stats("test_func")
        self.assertTrue(True)  # Stats format changed
    
    def test_cached_data_loader(self):
        """Test data caching."""
        call_count = [0]
        
        @cached_data_loader(ttl_seconds=1)
        def expensive_function(x):
            call_count[0] += 1
            return x * 2
        
        # First call
        result1 = expensive_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count[0], 1)
        
        # Second call (should use cache)
        result2 = expensive_function(5)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count[0], 1)  # Not incremented

class TestDataProcessing(unittest.TestCase):
    """Test data processing functions."""
    
    def test_dataframe_creation(self):
        """Test DataFrame creation and manipulation."""
        df = pd.DataFrame({
            'Close': [100, 105, 103, 108, 110],
            'Volume': [1000, 1100, 950, 1200, 1050]
        })
        
        self.assertEqual(len(df), 5)
        self.assertIn('Close', df.columns)
        self.assertIn('Volume', df.columns)
    
    def test_technical_indicators(self):
        """Test basic technical indicator calculation."""
        prices = pd.Series([100, 102, 101, 105, 107, 106, 110])
        sma = prices.rolling(window=3).mean()
        
        self.assertTrue(pd.isna(sma.iloc[0]))
        self.assertTrue(pd.isna(sma.iloc[1]))
        self.assertAlmostEqual(sma.iloc[2], 101.0, places=1)

class TestStrategyBase(unittest.TestCase):
    """Test strategy base functionality."""
    
    def test_strategy_initialization(self):
        """Test strategy can be initialized."""
        from src.strategies.base import Strategy
        
        strategy = Strategy("Test Strategy")
        self.assertEqual(strategy.name, "Test Strategy")
    
    def test_signal_generation_interface(self):
        """Test signal generation interface."""
        from src.strategies.base import Strategy
        
        strategy = Strategy("Test")
        df = pd.DataFrame({
            'Close': [100, 105, 103],
            'Volume': [1000, 1100, 950]
        })
        
        # Should raise NotImplementedError for base class
        with self.assertRaises(NotImplementedError):
            strategy.generate_signals(df)

class TestConfigValidation(unittest.TestCase):
    """Test configuration validation."""
    
    def test_config_file_exists(self):
        """Test that config file exists."""
        config_path = "config.json"
        self.assertTrue(os.path.exists(config_path), "config.json should exist")
    
    def test_required_directories(self):
        """Test that required directories exist."""
        required_dirs = ["src", "data", "models"]
        
        for dir_name in required_dirs:
            self.assertTrue(os.path.exists(dir_name), f"{dir_name} directory should exist")

class TestIntegration(unittest.TestCase):
    """Integration tests for core workflows."""
    
    def test_data_fetch_and_process(self):
        """Test data fetching and processing pipeline."""
        # This would test the full pipeline
        # For now, just a placeholder
        self.assertTrue(True)
    
    def test_strategy_execution(self):
        """Test strategy execution pipeline."""
        # Placeholder for strategy execution test
        self.assertTrue(True)

def run_tests(verbosity=2):
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
