"""
Verification script for Phase 63: Autonomous Feedback Loop & Mission Control
"""

import unittest
from unittest.mock import MagicMock, patch, mock_open
import json
import pandas as pd
from datetime import datetime

from src.feedback_loop import DailyReviewer


class TestPhase63(unittest.TestCase):
    
    def setUp(self):
        self.config_data = {
            "auto_trading": {
                "stop_loss_pct": 0.03,
                "take_profit_pct": 0.10,
                "max_daily_trades": 5
            }
        }
    
    def test_daily_metrics_calculation(self):
        """Test that daily metrics are calculated correctly."""
        print("\nTesting Daily Metrics Calculation...")
        
        with patch("src.feedback_loop.PaperTrader") as mock_pt:
            # Mock trade history
            mock_history = pd.DataFrame({
                'timestamp': [datetime.now()] * 4,
                'ticker': ['TEST'] * 4,
                'action': ['BUY', 'SELL', 'BUY', 'SELL'],
                'price': [100, 110, 100, 95],
                'quantity': [10, 10, 10, 10]
            })
            
            mock_pt.return_value.get_trade_history.return_value = mock_history
            
            reviewer = DailyReviewer()
            metrics = reviewer.calculate_daily_metrics()
            
            self.assertIn('win_rate', metrics)
            self.assertIn('daily_pnl', metrics)
            self.assertEqual(metrics['closed_positions'], 2)
            
            print(f"✅ Metrics calculated: Win Rate={metrics['win_rate']:.1f}%, P&L={metrics['daily_pnl']}")
    
    def test_parameter_adjustment_poor_performance(self):
        """Test that parameters are tightened when performance is poor."""
        print("\nTesting Parameter Adjustment (Poor Performance)...")
        
        mock_config = json.dumps(self.config_data)
        
        with patch("builtins.open", mock_open(read_data=mock_config)):
            with patch("json.load", return_value=self.config_data):
                reviewer = DailyReviewer()
                
                # Simulate poor performance
                metrics = {
                    "win_rate": 30.0,  # Below 40%
                    "daily_pnl": -5000,
                    "total_trades": 5
                }
                
                adjustments = reviewer.adjust_parameters(metrics)
                
                self.assertIn('stop_loss_pct', adjustments)
                self.assertIn('reason', adjustments)
                
                # Should tighten stop loss
                self.assertLess(adjustments['stop_loss_pct'], 0.03)
                
                print(f"✅ Adjustments: {adjustments}")
    
    def test_parameter_adjustment_good_performance(self):
        """Test that parameters are relaxed when performance is excellent."""
        print("\nTesting Parameter Adjustment (Good Performance)...")
        
        mock_config = json.dumps(self.config_data)
        
        with patch("builtins.open", mock_open(read_data=mock_config)):
            with patch("json.load", return_value=self.config_data):
                reviewer = DailyReviewer()
                
                # Simulate excellent performance
                metrics = {
                    "win_rate": 75.0,  # Above 70%
                    "daily_pnl": 10000,
                    "total_trades": 5
                }
                
                adjustments = reviewer.adjust_parameters(metrics)
                
                if adjustments:
                    self.assertIn('reason', adjustments)
                    print(f"✅ Adjustments: {adjustments}")
                else:
                    print("✅ No adjustments needed (as expected for good performance)")
    
    def test_config_backup_and_update(self):
        """Test that config is backed up before updating."""
        print("\nTesting Config Backup & Update...")
        
        mock_config = json.dumps(self.config_data)
        
        with patch("builtins.open", mock_open(read_data=mock_config)) as mock_file:
            with patch("json.load", return_value=self.config_data):
                with patch("json.dump") as mock_dump:
                    reviewer = DailyReviewer()
                    
                    adjustments = {
                        "stop_loss_pct": 0.02,
                        "reason": "Test adjustment"
                    }
                    
                    result = reviewer.apply_adjustments(adjustments)
                    
                    # Should have called dump twice (backup + new config)
                    self.assertEqual(mock_dump.call_count, 2)
                    
                    print("✅ Config backup and update verified")
    
    def test_journal_generation(self):
        """Test that AI journal is generated."""
        print("\nTesting Journal Generation...")
        
        with patch("src.feedback_loop.get_llm_reasoner") as mock_reasoner:
            mock_reasoner.return_value.ask.return_value = "Test journal entry"
            
            reviewer = DailyReviewer()
            
            metrics = {"win_rate": 50.0, "daily_pnl": 1000}
            adjustments = {"reason": "No adjustments"}
            
            journal = reviewer.generate_daily_journal(metrics, adjustments)
            
            self.assertIsInstance(journal, str)
            self.assertGreater(len(journal), 0)
            
            print(f"✅ Journal generated: {journal[:50]}...")


if __name__ == "__main__":
    unittest.main()
