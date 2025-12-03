"""
Test Phase 35: Multi-Asset Support
Verify Crypto and FX data loading and currency formatting.
"""
from src.data_loader import fetch_stock_data, CRYPTO_PAIRS, FX_PAIRS
from src.formatters import format_currency

def test_crypto_data_loading():
    """Test fetching crypto data."""
    # Fetch BTC-USD
    tickers = ["BTC-USD"]
    data_map = fetch_stock_data(tickers, period="5d")
    
    assert "BTC-USD" in data_map
    df = data_map["BTC-USD"]
    assert not df.empty
    assert "Close" in df.columns
    # Crypto trades 24/7, so should have recent data
    assert len(df) >= 3

def test_fx_data_loading():
    """Test fetching FX data."""
    # Fetch USDJPY=X
    tickers = ["USDJPY=X"]
    data_map = fetch_stock_data(tickers, period="5d")
    
    assert "USDJPY=X" in data_map
    df = data_map["USDJPY=X"]
    assert not df.empty
    assert "Close" in df.columns

def test_currency_formatting():
    """Test currency formatting for different symbols."""
    # JPY
    assert format_currency(1000, symbol="¥") == "¥1,000"
    
    # USD
    assert format_currency(1000, symbol="$") == "$1,000"
    
    # USD with cents
    assert format_currency(10.50, symbol="$", decimals=2) == "$10.50"

def test_asset_class_constants():
    """Verify asset class constants are defined."""
    assert len(CRYPTO_PAIRS) > 0
    assert "BTC-USD" in CRYPTO_PAIRS
    
    assert len(FX_PAIRS) > 0
    assert "USDJPY=X" in FX_PAIRS

if __name__ == "__main__":
    # Manual run
    try:
        test_crypto_data_loading()
        print("✅ Crypto data loading passed")
        test_fx_data_loading()
        print("✅ FX data loading passed")
        test_currency_formatting()
        print("✅ Currency formatting passed")
        test_asset_class_constants()
        print("✅ Asset class constants passed")
    except Exception as e:
        print(f"❌ Test failed: {e}")
