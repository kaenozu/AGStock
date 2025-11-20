import yfinance as yf
import pandas as pd
import streamlit as st
from typing import List, Dict

def fetch_stock_data(tickers: List[str], period: str = "2y") -> Dict[str, pd.DataFrame]:
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

def get_latest_price(df: pd.DataFrame) -> float:
    """Returns the latest close price from a dataframe."""
    if df is None or df.empty:
        return 0.0
    return df['Close'].iloc[-1]

def fetch_macro_data(period: str = "2y") -> Dict[str, pd.DataFrame]:
    """
    Fetches macro economic data: USD/JPY, S&P 500, US 10Y Yield.
    """
    tickers = {
        "USDJPY": "JPY=X",
        "SP500": "^GSPC",
        "US10Y": "^TNX"
    }
    
    data_dict = {}
    try:
        # Fetch one by one to be safe or bulk
        # Bulk is fine
        df = yf.download(list(tickers.values()), period=period, group_by='ticker', auto_adjust=True, threads=True)
        
        for name, ticker in tickers.items():
            if len(tickers) > 1:
                if ticker in df.columns.levels[0]: # Check if ticker exists in top level index
                    macro_df = df[ticker].copy()
                else:
                    continue
            else:
                macro_df = df.copy()
            
            macro_df.dropna(inplace=True)
            if not macro_df.empty:
                data_dict[name] = macro_df
                
    except Exception as e:
        st.error(f"Error fetching macro data: {e}")
        return {}
        
    return data_dict
