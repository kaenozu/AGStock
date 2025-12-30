"""
Comprehensive Integration Tests for AGStock
Tests end-to-end workflows with real market data.
"""
import unittest
import sys
import os
import asyncio
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.realtime.realtime_engine import RealTimeEngine, DynamicStopLoss
from src.utils.error_handler import safe_execute, ErrorRecovery
from src.utils.performance import PerformanceMonitor
import pandas as pd
import numpy as np

class TestRealTimeEngine(unittest.TestCase):
    """Test real-time trading engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = RealTimeEngine(config={
            "update_interval": 0.1,
            "history_window": 50,
            "anomaly_threshold": 2.5
        })
    
    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        self.assertFalse(self.engine.is_running)
        self.assertEqual(len(self.engine.price_history), 0)
    
    def test_anomaly_detection(self):
        """Test anomaly detection logic."""
        ticker = "TEST.T"
        
        # Build normal price history
        self.engine.price_history[ticker] = []
        for i in range(30):
            self.engine.price_history[ticker].append({
                "timestamp": datetime.now(),
                "price": 100 + np.random.normal(0, 1)
            })
        
        # Test normal price (no anomaly)
        anomaly = self.engine._detect_anomaly(ticker, 101.0)
        self.assertIsNone(anomaly)
        
        # Test anomalous price (spike)
        anomaly = self.engine._detect_anomaly(ticker, 120.0)
        self.assertIsNotNone(anomaly)
        self.assertEqual(anomaly["type"], "SPIKE")
    
    def test_signal_generation(self):
        """Test trading signal generation."""
        ticker = "TEST.T"
        
        # Build upward trending prices
        self.engine.price_history[ticker] = []
        for i in range(15):
            self.engine.price_history[ticker].append({
                "timestamp": datetime.now(),
                "price": 100 + i * 0.5  # Upward trend
            })
        
        signal = self.engine._check_signal(ticker)
        self.assertIsNotNone(signal)
        self.assertEqual(signal["action"], "BUY")
    
    def test_statistics_calculation(self):
        """Test real-time statistics."""
        ticker = "TEST.T"
        
        # Add price data
        self.engine.price_history[ticker] = []
        for i in range(20):
            self.engine.price_history[ticker].append({
                "timestamp": datetime.now(),
                "price": 100 + i
            })
        
        stats = self.engine.get_statistics(ticker)
        self.assertEqual(stats["ticker"], ticker)
        self.assertEqual(stats["data_points"], 20)
        self.assertGreater(stats["mean_price"], 100)

class TestDynamicStopLoss(unittest.TestCase):
    """Test dynamic stop-loss system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.stop_loss = DynamicStopLoss(
            initial_stop_pct=0.02,
            initial_target_pct=0.05
        )
    
    def test_add_position(self):
        """Test adding a position."""
        self.stop_loss.add_position("TEST.T", 100.0, 100)
        
        position = self.stop_loss.get_position_status("TEST.T")
        self.assertIsNotNone(position)
        self.assertEqual(position["entry_price"], 100.0)
        self.assertEqual(position["quantity"], 100)
    
    def test_stop_loss_trigger(self):
        """Test stop-loss triggering."""
        self.stop_loss.add_position("TEST.T", 100.0, 100)
        
        # Price drops below stop
        result = self.stop_loss.update("TEST.T", 97.0)
        self.assertEqual(result, "STOP_LOSS")
    
    def test_take_profit_trigger(self):
        """Test take-profit triggering."""
        self.stop_loss.add_position("TEST.T", 100.0, 100)
        
        # Price rises above target
        result = self.stop_loss.update("TEST.T", 106.0)
        self.assertEqual(result, "TAKE_PROFIT")
    
    def test_trailing_stop(self):
        """Test trailing stop activation."""
        self.stop_loss.add_position("TEST.T", 100.0, 100)
        
        # Price rises significantly
        self.stop_loss.update("TEST.T", 104.0)
        
        position = self.stop_loss.get_position_status("TEST.T")
        self.assertTrue(position["trailing_stop_active"])
        self.assertGreater(position["stop_loss"], 100.0 * 0.98)

class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete trading workflows."""
    
    def test_data_fetch_and_analysis(self):
        """Test data fetching and analysis pipeline."""
        import yfinance as yf
        
        # Fetch data
        ticker = "AAPL"
        data = yf.download(ticker, period="5d", progress=False)
        
        self.assertFalse(data.empty)
        self.assertIn("Close", data.columns)
    
    def test_strategy_execution_pipeline(self):
        """Test strategy execution from data to signal."""
        from src.strategies.base import Strategy
        
        # Create mock data
        df = pd.DataFrame({
            'Close': [100, 102, 101, 105, 107],
            'Volume': [1000, 1100, 950, 1200, 1050]
        })
        
        # Test that base strategy interface works
        strategy = Strategy("Test")
        self.assertEqual(strategy.name, "Test")
    
    def test_error_recovery_in_workflow(self):
        """Test error recovery during workflow."""
        def flaky_operation():
            import random
            if random.random() < 0.7:
                raise ConnectionError("Simulated failure")
            return "success"
        
        # Should eventually succeed with retries
        result = ErrorRecovery.retry_with_backoff(
            flaky_operation,
            max_retries=10,
            backoff_factor=0.1
        )
        self.assertEqual(result, "success")

class TestPerformanceBenchmarks(unittest.TestCase):
    """Performance benchmarks for critical operations."""
    
    def test_data_processing_speed(self):
        """Test data processing performance."""
        monitor = PerformanceMonitor()
        
        @monitor.time_function("data_processing")
        def process_large_dataset():
            df = pd.DataFrame(np.random.randn(10000, 10))
            return df.describe()
        
        result = process_large_dataset()
        stats = monitor.get_stats("data_processing")
        
        # Should complete in reasonable time
        self.assertLess(stats["avg"], 1.0)  # Less than 1 second
    
    def test_signal_generation_speed(self):
        """Test signal generation performance."""
        monitor = PerformanceMonitor()
        
        @monitor.time_function("signal_generation")
        def generate_signals():
            df = pd.DataFrame({
                'Close': np.random.randn(1000) + 100,
                'Volume': np.random.randint(1000, 10000, 1000)
            })
            # Simulate signal calculation
            df['SMA'] = df['Close'].rolling(20).mean()
            return df
        
        result = generate_signals()
        stats = monitor.get_stats("signal_generation")
        
        # Should be fast
        self.assertLess(stats["avg"], 0.5)

class TestSystemResilience(unittest.TestCase):
    """Test system resilience and fault tolerance."""
    
    def test_graceful_degradation(self):
        """Test system handles failures gracefully."""
        def primary_data_source():
            raise ConnectionError("Primary source down")
        
        def fallback_data_source():
            return {"status": "fallback", "data": [1, 2, 3]}
        
        result = ErrorRecovery.fallback_chain(
            primary_data_source,
            fallback_data_source
        )
        
        self.assertEqual(result["status"], "fallback")
    
    def test_concurrent_operations(self):
        """Test system handles concurrent operations."""
        import concurrent.futures
        
        def process_ticker(ticker):
            import time
            time.sleep(0.1)
            return f"Processed {ticker}"
        
        tickers = ["AAPL", "GOOGL", "MSFT", "AMZN"]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(process_ticker, tickers))
        
        self.assertEqual(len(results), 4)

def run_integration_tests(verbosity=2):
    """Run all integration tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRealTimeEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestDynamicStopLoss))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceBenchmarks))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemResilience))
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 AGStock Integration Tests")
    print("="*60 + "\n")
    
    success = run_integration_tests()
    
    print("\n" + "="*60)
    if success:
        print("✅ All integration tests passed!")
    else:
        print("❌ Some tests failed. Please review the output above.")
    print("="*60)
    
    sys.exit(0 if success else 1)
