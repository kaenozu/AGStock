import yfinance as yf
import pandas as pd
import streamlit as st
from src.cache_config import install_cache

# Install cache to prevent excessive API calls
install_cache()

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def fetch_stock_data(tickers, period="2y"):
    """
    Fetches historical stock data for a list of tickers.
    
    Args:
        tickers (list): List of ticker symbols (e.g., ['7203.T', '9984.T'])
        period (str): Data period to download (default: '2y')
        
    Returns:
        dict: A dictionary where keys are tickers and values are DataFrames.
    """
    if not tickers:
        return {}
    
    data_dict = {}
    
    # Download in bulk is faster usually, but yfinance returns a multi-index dataframe
    # which can be tricky. Let's try bulk download first.
    try:
        # group_by='ticker' makes it easier to separate
        df = yf.download(tickers, period=period, group_by='ticker', auto_adjust=True, threads=True)
        
        for ticker in tickers:
            # Extract individual dataframe
            if len(tickers) > 1:
                stock_df = df[ticker].copy()
            else:
                stock_df = df.copy()
                
            # Basic cleaning
            stock_df.dropna(inplace=True)
            
            if not stock_df.empty:
                data_dict[ticker] = stock_df
                
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return {}

    return data_dict

def get_latest_price(df):
    """Returns the latest close price from a dataframe."""
    if df is None or df.empty:
        return 0.0
    return df['Close'].iloc[-1]
