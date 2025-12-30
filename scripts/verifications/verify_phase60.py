
import unittest
from unittest.mock import MagicMock, patch
import json
import os
import time
from datetime import datetime

# Import target modules
from scheduler import update_status, STATUS_FILE
from src.smart_alerts import SmartAlerts

class TestPhase60(unittest.TestCase):
    def setUp(self):
        # Remove status file if exists
        if os.path.exists(STATUS_FILE):
            os.remove(STATUS_FILE)
        
        # Create dummy config
        self.config = {
            "alerts": {
                "active_mode": True,
                "daily_loss_threshold": -3.0,
                "vix_threshold": 30.0
            },
            "notifications": {"line": {"token": "dummy"}}
        }
        with open("verify_config.json", "w") as f:
            json.dump(self.config, f)

    def tearDown(self):
        if os.path.exists("verify_config.json"):
            os.remove("verify_config.json")
        if os.path.exists(STATUS_FILE):
            os.remove(STATUS_FILE)

    def test_system_status_tracking(self):
        print("\nTesting System Status Tracking...")
        update_status("test_job", "success", "Test Message")
        
        self.assertTrue(os.path.exists(STATUS_FILE))
        
        with open(STATUS_FILE, "r") as f:
            data = json.load(f)
            
        self.assertIn("jobs", data)
        self.assertIn("test_job", data["jobs"])
        self.assertEqual(data["jobs"]["test_job"]["status"], "success")
        print("✅ Status file updated correctly")

    @patch("src.trading.fully_automated_trader.FullyAutomatedTrader")
    @patch("src.smart_alerts.fetch_stock_data")
    @patch("src.smart_alerts.get_latest_price")
    def test_active_defense_vix(self, mock_get_price, mock_fetch, MockTrader):
        print("\nTesting Active Defense (VIX)...")
        # Setup mocks
        mock_trader_instance = MockTrader.return_value
        
        # Initialize SmartAlerts with active mode
        alerts = SmartAlerts("verify_config.json")
        
        # Mock VIX spike
        with patch("src.smart_alerts.yf.Ticker") as MockTicker:
            mock_hist = MagicMock()
            # DataFrame with heavy VIX
            import pandas as pd
            mock_hist.history.return_value = pd.DataFrame({
                "Close": [30.0, 50.0] # Jump to 50
            })
            MockTicker.return_value = mock_hist
            
            alerts.check_vix_spike()
            
            # Verify emergency stop called
            mock_trader_instance.emergency_stop.assert_called()
            print("✅ Emergency stop triggered for VIX > 45")

    @patch("src.trading.fully_automated_trader.FullyAutomatedTrader")
    def test_active_defense_daily_loss(self, MockTrader):
        print("\nTesting Active Defense (Daily Loss)...")
        mock_trader_instance = MockTrader.return_value
        
        alerts = SmartAlerts("verify_config.json")
        
        # Mock PaperTrader history showing big loss
        with patch.object(alerts.pt, "get_equity_history") as mock_hist:
            import pandas as pd
            # -10% drop
            mock_hist.return_value = pd.DataFrame([
                {"equity": 100000},
                {"equity": 90000} 
            ])
            
            alerts.check_daily_loss()
            
            mock_trader_instance.emergency_stop.assert_called()
            print("✅ Emergency stop triggered for Daily Loss > 5%")

if __name__ == "__main__":
    unittest.main()
