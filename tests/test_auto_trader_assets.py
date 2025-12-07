"""
Test Multi-Asset Integration in FullyAutomatedTrader
Verify that get_target_tickers respects the asset configuration.
"""
import json
import os
import sys
from unittest.mock import MagicMock

# Mock streamlit to avoid runtime errors
mock_st = MagicMock()
def mock_cache_data(**kwargs):
    def decorator(func):
        return func
    return decorator
mock_st.cache_data = mock_cache_data
sys.modules["streamlit"] = mock_st

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fully_automated_trader import FullyAutomatedTrader
from src.data_loader import CRYPTO_PAIRS, FX_PAIRS
from src.constants import NIKKEI_225_TICKERS

# Mock config for testing
TEST_CONFIG_PATH = "tests/test_config.json"

def setup_module():
    """Create a temporary config file."""
    config = {
        "paper_trading": {"initial_capital": 1000000},
        "auto_trading": {"max_daily_trades": 5},
        "assets": {
            "japan_stocks": True,
            "us_stocks": False,
            "europe_stocks": False,
            "crypto": True,  # Enable Crypto
            "fx": True       # Enable FX
        }
    }
    with open(TEST_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f)

def teardown_module():
    """Remove the temporary config file."""
    if os.path.exists(TEST_CONFIG_PATH):
        os.remove(TEST_CONFIG_PATH)

def test_get_target_tickers_with_crypto_fx():
    """Test if Crypto and FX tickers are included when enabled."""
    trader = FullyAutomatedTrader(config_path=TEST_CONFIG_PATH)
    
    tickers = trader.get_target_tickers()
    
    # Check for Crypto
    has_crypto = any(t in CRYPTO_PAIRS for t in tickers)
    assert has_crypto, "Crypto tickers should be included"
    
    # Check for FX
    has_fx = any(t in FX_PAIRS for t in tickers)
    assert has_fx, "FX tickers should be included"
    
    # Check for Japan Stocks
    has_japan = any(t in NIKKEI_225_TICKERS for t in tickers)
    assert has_japan, "Japan stocks should be included"
    
    print(f"Total tickers: {len(tickers)}")
    print(f"Sample tickers: {tickers[:5]}")

if __name__ == "__main__":
    setup_module()
    try:
        test_get_target_tickers_with_crypto_fx()
        print("✅ Multi-Asset Integration Test Passed")
    except Exception as e:
        print(f"❌ Test Failed: {e}")
    finally:
        teardown_module()
