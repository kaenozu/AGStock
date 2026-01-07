import pytest
import pandas as pd
import numpy as np
import logging
from unittest.mock import MagicMock, patch
from src.data_loader import process_downloaded_data

# Define constant here since we can't easily import it without src structure sometimes in test envs
# Assuming MINIMUM_DATA_POINTS is around 252 or similar from src/constants.py
# We will mock it or just rely on the logic being generic.
# But `process_downloaded_data` imports MINIMUM_DATA_POINTS from src.constants if used directly? 
# Wait, process_downloaded_data uses the global constant. We should patch it.

@pytest.fixture
def mock_min_data_points():
    return 50

def test_process_downloaded_data_strict_filtering(mock_min_data_points):
    """Test that tickers with insufficient data are excluded."""
    
    # Create a DataFrame with 2 tickers: one sufficient, one insufficient
    dates_long = pd.date_range("2024-01-01", periods=100)
    dates_short = pd.date_range("2024-01-01", periods=10)
    
    val_long = np.random.randn(100)
    val_short = np.random.randn(10)
    
    # Simulate yfinance structure (MultiIndex columns) or single index depending on logic
    # For simplicity, let's create two separate DFs and mock the input if needed, 
    # but process_downloaded_data takes a raw_data DF.
    
    # Construct raw_data similar to yf.download(group_by='ticker')
    # Ticker A: Long, Ticker B: Short
    
    # It's easier if we pass flat DF if we use single ticker logic test, 
    # but the function iterates tickers.
    
    # Construct raw_data using concat to ensure MultiIndex structure is correct
    df_block = pd.DataFrame(val_long, index=dates_long, columns=["Close"])
    df_block.columns = pd.MultiIndex.from_product([["BLOCK"], df_block.columns])
    
    df_skip = pd.DataFrame(val_short, index=dates_short, columns=["Close"])
    df_skip.columns = pd.MultiIndex.from_product([["SKIP"], df_skip.columns])
    
    # Outer join to align dates
    raw_data = pd.concat([df_block, df_skip], axis=1)
    
    tickers = ["BLOCK", "SKIP"]
    
    # Patch the constant in the module
    with patch("src.data_loader.MINIMUM_DATA_POINTS", mock_min_data_points):
        processed = process_downloaded_data(raw_data, tickers)
        
    assert "BLOCK" in processed
    assert "SKIP" not in processed
    assert len(processed["BLOCK"]) == 100

def test_process_downloaded_data_outlier_detection(caplog):
    """Test that outliers trigger a warning."""
    
    dates = pd.date_range("2024-01-01", periods=100)
    vals = np.ones(100) * 100.0
    
    # Create a massive jump
    vals[50] = 200.0 # +100% return
    
    raw_data = pd.DataFrame(vals, index=dates, columns=["Close"])
    tickers = ["JUMP"]
    
    with patch("src.data_loader.MINIMUM_DATA_POINTS", 10):
        with caplog.at_level(logging.WARNING):
            process_downloaded_data(raw_data, tickers)
            
    assert "extreme price jumps" in caplog.text
    assert "JUMP" in caplog.text

if __name__ == "__main__":
    pytest.main([__file__])
