import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import sys
import os

import logging
# Add src to path
sys.path.append(os.path.abspath("."))

from src.strategies.orchestrator import StrategyOrchestrator
from src.strategies.meta_registry import REGIME_STRATEGY_MAP, UNIVERSAL_STRATEGIES
from src.strategies.technical import SMACrossoverStrategy
from src.trading.fully_automated_trader import FullyAutomatedTrader

class TestPhase62(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        self.orchestrator = StrategyOrchestrator()
        
    def test_strategy_instantiation(self):
        print("\nTesting Strategy Instantiation...")
        try:
            s = SMACrossoverStrategy()
            print(f"✅ Successfully instantiated {s.name}")
        except Exception as e:
            print(f"❌ Failed to instantiate SMACrossoverStrategy: {e}")
            raise e

    def test_orchestrator_logic(self):
        print("\nTesting Strategy Orchestrator...")
        
        from src.strategies.meta_registry import get_strategies_for_regime
        classes = get_strategies_for_regime("trending_up")
        print(f"DEBUG: Classes for trending_up: {[c.__name__ for c in classes]}")
        
        # Test Trending Up
        squad_trending = self.orchestrator.get_active_squad("trending_up")
        names_trending = [s.name for s in squad_trending]
        print(f"Trending Squad: {names_trending}")
        
        # Should contain Universal + SMACrossover
        self.assertTrue(any("SMACrossover" in n for n in names_trending))
        self.assertTrue(any("Ensemble" in n for n in names_trending))
        
        # Test Ranging
        squad_ranging = self.orchestrator.get_active_squad("ranging")
        names_ranging = [s.name for s in squad_ranging]
        print(f"Ranging Squad: {names_ranging}")
        
        # Should contain Bollinger or RSI
        self.assertTrue(any("RSI" in n for n in names_ranging) or any("Bollinger" in n for n in names_ranging))
        
        # Validate difference
        self.assertNotEqual(set(names_trending), set(names_ranging), "Squads should differ by regime")
        print("✅ Orchestrator logic verified")

    @patch("src.trading.fully_automated_trader.PaperTrader")
    @patch("src.trading.fully_automated_trader.BackupManager")
    @patch("src.trading.fully_automated_trader.SmartNotifier")
    @patch("src.trading.fully_automated_trader.ExecutionEngine")
    def test_trader_integration(self, mock_engine, mock_notifier, mock_backup, mock_pt):
        print("\nTesting Trader Integration...")
        
        # Mock Config
        with patch("builtins.open", unittest.mock.mock_open(read_data='{"auto_trading": {"ai_enabled": false}}')):
            with patch("json.load", return_value={"auto_trading": {"ai_enabled": false}}):
                trader = FullyAutomatedTrader("dummy_config.json")
                
        # Mock dependencies for scan_market
        trader.get_target_tickers = MagicMock(return_value=["TEST_TICKER"])
        trader._fetch_data_with_retry = MagicMock(return_value={
            "TEST_TICKER": pd.DataFrame({"Close": [100, 101, 102], "High": [102]*3, "Low": [99]*3, "Volume": [1000]*3})
        })
        trader._get_vix_level = MagicMock(return_value=20.0)
        
        # Mock Regime Detector to force a regime
        trader.regime_detector.detect_regime = MagicMock(return_value="trending_up")
        
        # Run scan
        # We want to verify orchestrator was called
        trader.orchestrator.get_active_squad = MagicMock(wraps=trader.orchestrator.get_active_squad)
        
        signals = trader.scan_market()
        
        trader.regime_detector.detect_regime.assert_called()
        trader.orchestrator.get_active_squad.assert_called_with("trending_up")
        print("✅ Integrated scan_market called orchestrator")

if __name__ == "__main__":
    unittest.main()
