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
    import time
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # group_by='ticker' makes it easier to separate
            df = yf.download(tickers, period=period, group_by='ticker', auto_adjust=True, threads=True)
            
            if df.empty:
                raise ValueError("Empty dataframe returned")

            for ticker in tickers:
                # Extract individual dataframe
                if len(tickers) > 1:
                    try:
                        stock_df = df[ticker].copy()
                    except KeyError:
                        continue # Ticker not found in result
                else:
                    stock_df = df.copy()
                    
                # Basic cleaning
                stock_df.dropna(inplace=True)
                
                if not stock_df.empty:
                    data_dict[ticker] = stock_df
            
            return data_dict # Success
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2 # Exponential backoff
            else:
                st.error(f"Error fetching data after {max_retries} attempts: {e}")
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
    import time
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # Fetch one by one to be safe or bulk
            # Bulk is fine
            df = yf.download(list(tickers.values()), period=period, group_by='ticker', auto_adjust=True, threads=True)
            
            if df.empty:
                raise ValueError("Empty dataframe returned")
            
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
            
            return data_dict # Success
                
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                st.error(f"Error fetching macro data after {max_retries} attempts: {e}")
                return {}
        
    return data_dict

def fetch_fundamental_data(ticker: str) -> Dict:
    """
    Fetches fundamental data for a single ticker.
    Returns a dictionary with keys: trailingPE, priceToBook, returnOnEquity, marketCap, forwardPE, dividendYield.
    Returns None if data is unavailable.
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        
        return {
            "trailingPE": info.get("trailingPE"),
            "priceToBook": info.get("priceToBook"),
            "returnOnEquity": info.get("returnOnEquity"),
            "marketCap": info.get("marketCap"),
            "forwardPE": info.get("forwardPE"),
            "dividendYield": info.get("dividendYield")
        }
    except Exception as e:
        print(f"Error fetching fundamentals for {ticker}: {e}")
        return None
