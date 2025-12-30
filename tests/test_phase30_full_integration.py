"""
Phase 30 Full Integration Test
Verifies the integration of Risk Management Dashboard, Kelly Criterion, and Dynamic Stops
within the FullyAutomatedTrader and PaperTrader ecosystem.
"""
import unittest
import pandas as pd
import numpy as np
import os
from unittest.mock import MagicMock, patch
from src.paper_trader import PaperTrader
from src.trading.fully_automated_trader import FullyAutomatedTrader

class TestPhase30FullIntegration(unittest.TestCase):
    def setUp(self):
        # Use a temporary DB for testing
        self.test_db = "test_phase30_integration.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
            
        self.pt = PaperTrader(db_path=self.test_db, initial_capital=1000000)
        
        # Mock config
        self.config_path = "test_config.json"
        with open(self.config_path, "w") as f:
            f.write('{"paper_trading": {"initial_capital": 1000000}}')
            
        self.trader = FullyAutomatedTrader(config_path=self.config_path)
        self.trader.pt = self.pt # Inject test paper trader
        self.trader.engine.pt = self.pt # Inject into engine too
        
    def tearDown(self):
        self.pt.close()
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

    def test_kelly_position_sizing_integration(self):
        """Verify that scan_market uses Kelly Criterion for sizing"""
        print("\nTesting Kelly Criterion Integration...")
        
        # Mock fetch_stock_data to return a bullish signal setup
        # We need enough data for LightGBM or other strategies to run, 
        # but here we just want to verify the sizing logic in scan_market.
        # It's easier to mock the strategy signal generation or the data.
        
        # Let's mock get_target_tickers to return just one ticker
        self.trader.get_target_tickers = MagicMock(return_value=["7203.T"])
        
        # Mock data
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        df = pd.DataFrame({
            'Open': np.linspace(1000, 1100, 100),
            'High': np.linspace(1010, 1110, 100),
            'Low': np.linspace(990, 1090, 100),
            'Close': np.linspace(1000, 1100, 100),
            'Volume': np.random.randint(1000000, 10000000, 100)
        }, index=dates)
        
        # Mock _fetch_data_with_retry
        self.trader._fetch_data_with_retry = MagicMock(return_value={"7203.T": df})
        
        # Mock strategy generation to force a BUY signal
        # We need to patch the strategies list inside scan_market or mock the classes
        # Easier: Mock the strategies list in the loop. 
        # But scan_market creates instances inside.
        # Let's patch LightGBMStrategy.generate_signals
        
        with patch('src.strategies.LightGBMStrategy.generate_signals') as mock_sig:
            # Return a series with 1 at the end
            mock_sig.return_value = pd.Series([0]*99 + [1], index=dates)
            
            # Also need to mock fetch_fundamental_data to pass filter
            with patch('fully_automated_trader.fetch_fundamental_data') as mock_fund:
                mock_fund.return_value = {'marketCap': 10000000000, 'trailingPE': 15}
                
                # Run scan_market
                signals = self.trader.scan_market()
                
                self.assertTrue(len(signals) > 0)
                signal = signals[0]
                self.assertEqual(signal['ticker'], "7203.T")
                self.assertEqual(signal['action'], "BUY")
                
                # Check if quantity is calculated and reasonable
                # Kelly for 55% win rate, 1.5 ratio is ~25% (half kelly ~12.5%)
                # 1M capital * 12.5% = 125,000. Price 1100.
                # Qty ~ 113 shares -> 100 shares.
                print(f"Generated Signal: {signal}")
                self.assertIn('quantity', signal)
                self.assertGreater(signal['quantity'], 0)
                
                # Execute signal
                self.trader.execute_signals(signals)
                
                # Verify position in DB
                positions = self.pt.get_positions()
                self.assertIn("7203.T", positions['ticker'].values)
                pos = positions[positions['ticker'] == "7203.T"].iloc[0]
                
                # Verify stop_price and highest_price are initialized
                # Note: execute_trade initializes them to 0 and price respectively
                # But wait, execute_trade initializes stop_price to 0.0.
                # It should be updated by evaluate_positions later.
                self.assertEqual(pos['stop_price'], 0.0)
                self.assertEqual(pos['highest_price'], 1100.0) # Entry price

    def test_dynamic_stop_update(self):
        """Verify that evaluate_positions updates stop price using DynamicStopManager"""
        print("\nTesting Dynamic Stop Update...")
        
        # Setup a position manually
        self.pt.execute_trade("7203.T", "BUY", 100, 1000.0, reason="Test Setup")
        
        # Verify initial state
        positions = self.pt.get_positions()
        pos = positions[positions['ticker'] == "7203.T"].iloc[0]
        self.assertEqual(pos['stop_price'], 0.0)
        
        # Mock fetch_stock_data for evaluate_positions
        # Scenario 1: Price goes up to 1100. Stop should move up.
        dates = pd.date_range('2024-01-01', periods=20, freq='D')
        df_up = pd.DataFrame({
            'Open': np.linspace(1000, 1100, 20),
            'High': np.linspace(1010, 1110, 20),
            'Low': np.linspace(990, 1090, 20),
            'Close': np.linspace(1000, 1100, 20),
            'Volume': 1000000
        }, index=dates)
        
        # fully_automated_trader モジュール内の fetch_stock_data をパッチ
        with patch('fully_automated_trader.fetch_stock_data', return_value={"7203.T": df_up}):
            # Run evaluate_positions
            self.trader.evaluate_positions()
            
            # Check DB
            positions = self.pt.get_positions()
            pos = positions[positions['ticker'] == "7203.T"].iloc[0]
            
            print(f"Updated Position after rise: Stop={pos['stop_price']}, High={pos['highest_price']}")
            
            # Highest should be 1100
            self.assertEqual(pos['highest_price'], 1100.0)
            # Stop should be > 0 (initialized and trailed)
            self.assertGreater(pos['stop_price'], 0.0)
            # Stop should be around 1100 - 3*ATR. ATR approx 20? So ~1040?
            
            first_stop = pos['stop_price']
            
        # Scenario 2: Price drops to 1050 (above stop). Stop should NOT move down.
        df_drop = pd.DataFrame({
            'Open': [1050]*5,
            'High': [1060]*5,
            'Low': [1040]*5,
            'Close': [1050]*5,
            'Volume': 1000000
        }, index=pd.date_range('2024-01-21', periods=5, freq='D'))
        
        with patch('fully_automated_trader.fetch_stock_data', return_value={"7203.T": df_drop}):
            self.trader.evaluate_positions()
            
            positions = self.pt.get_positions()
            pos = positions[positions['ticker'] == "7203.T"].iloc[0]
            
            print(f"Updated Position after drop: Stop={pos['stop_price']}, High={pos['highest_price']}")
            
            # Highest should still be 1100 (didn't exceed)
            self.assertEqual(pos['highest_price'], 1100.0)
            # Stop should be same as before (never moves down)
            self.assertEqual(pos['stop_price'], first_stop)

        # Scenario 3: Price crashes to 900 (below stop). Should exit.
        df_crash = pd.DataFrame({
            'Open': [900]*5,
            'High': [910]*5,
            'Low': [890]*5,
            'Close': [900]*5,
            'Volume': 1000000
        }, index=pd.date_range('2024-01-26', periods=5, freq='D'))
        
        with patch('fully_automated_trader.fetch_stock_data', return_value={"7203.T": df_crash}):
            actions = self.trader.evaluate_positions()
            
            print(f"Actions generated: {actions}")
            self.assertTrue(len(actions) > 0)
            self.assertEqual(actions[0]['action'], 'SELL')
            self.assertIn('Stop Loss Hit', actions[0]['reason'])

if __name__ == '__main__':
    unittest.main()
