import unittest
from unittest.mock import MagicMock
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.execution import ExecutionEngine
from src.paper_trader import PaperTrader

class TestExecution(unittest.TestCase):
    def setUp(self):
        self.mock_paper_trader = MagicMock(spec=PaperTrader)
        self.mock_paper_trader.initial_capital = 1000000.0
        self.mock_paper_trader.get_current_balance.return_value = {
            'cash': 1000000.0,
            'total_equity': 1000000.0
        }
        self.engine = ExecutionEngine(self.mock_paper_trader)
        # Mock config for tests
        self.engine.mini_stock_enabled = True
        self.engine.mini_stock_config = {
            "enabled": True, "unit_size": 1, "spread_rate": 0.0022, "min_order_amount": 500
        }
    
    def test_fee_calculation_mini_stock(self):
        """ミニ株の手数料計算（寄付は無料、リアルタイムはスプレッド）"""
        # 寄付
        fee = self.engine.calculate_trading_fee(10000, is_mini_stock=True, order_type="寄付")
        self.assertEqual(fee, 0.0)
        
        # リアルタイム
        fee = self.engine.calculate_trading_fee(10000, is_mini_stock=True, order_type="リアルタイム")
        self.assertEqual(fee, 10000 * 0.0022)

    def test_position_size_cap(self):
        """ポジションサイズが資金を超えないこと"""
        # Confidence 1.0, Max 20% -> 200,000 JPY
        # Price 1000 -> 200 shares
        shares = self.engine.calculate_position_size("TEST.T", 1000.0, confidence=1.0)
        # unit size check (japan stock defaults to 100 if mini stock is not active for it?)
        # Logic says: if is_japan_stock and mini_stock_enabled -> unit_size from config (1)
        # So 200,000 / 1000 = 200 shares
        self.assertEqual(shares, 200)

    def test_position_size_min_order(self):
        """最低注文金額未満なら0株"""
        # Min order is 500. Price 200. Max 20% is huge, but let's say target is small.
        # But calculate_position_size calculates based on equity %.
        
        # Force a small equity to test min order?
        self.mock_paper_trader.get_current_balance.return_value = {
            'cash': 1000.0, 'total_equity': 1000.0
        }
        self.engine.max_position_size_pct = 0.1 # 100 JPY target
        
        # Target 100 JPY < Min 500 JPY
        shares = self.engine.calculate_position_size("TEST.T", 50.0)
        self.assertEqual(shares, 0)

if __name__ == '__main__':
    unittest.main()
