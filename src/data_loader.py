import logging
from typing import Dict, Mapping, Sequence, Any, Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def process_downloaded_data(
    raw_data: pd.DataFrame,
    tickers: Sequence[str],
    column_map: Mapping[str, str] | None = None,
) -> Dict[str, pd.DataFrame]:
    """
    yfinanceのダウンロード結果をティッカーごとに分割してクリーンアップする。

    Args:
        raw_data (pd.DataFrame): yfinanceから取得した生データ。
        tickers (Sequence[str]): 出力したいティッカー名のリスト。
        column_map (Mapping[str, str] | None): 出力名とyfinance上のシンボル名のマッピング。

    Returns:
        Dict[str, pd.DataFrame]: ティッカーごとに分割・NaN除去されたデータ。
    """
    if raw_data is None or raw_data.empty or not tickers:
        return {}

    column_map = column_map or {}
    is_multi_index = isinstance(raw_data.columns, pd.MultiIndex)
    processed: Dict[str, pd.DataFrame] = {}

    for ticker in tickers:
        source_key = column_map.get(ticker, ticker)

        if is_multi_index:
            if source_key not in raw_data.columns.get_level_values(0):
                continue
            df = raw_data[source_key].copy()
        else:
            if len(tickers) > 1:
                # 複数ティッカーを想定した単純DataFrameは扱えないためスキップ
                if source_key not in raw_data.columns:
                    continue
                df = raw_data[[source_key]].copy()
            else:
                df = raw_data.copy()

        if isinstance(df, pd.Series):
            df = df.to_frame()

        df.dropna(inplace=True)
        if not df.empty:
            processed[ticker] = df

    return processed


from datetime import datetime, timedelta
from src.data_manager import DataManager

def parse_period(period: str) -> datetime:
    """Convert period string (e.g., '2y', '1mo') to start datetime."""
    now = datetime.now()
    if period.endswith('y'):
        years = int(period[:-1])
        return now - timedelta(days=years * 365)
    elif period.endswith('mo'):
        months = int(period[:-2])
        return now - timedelta(days=months * 30)
    elif period.endswith('d'):
        days = int(period[:-1])
        return now - timedelta(days=days)
    else:
        # Default fallback
        return now - timedelta(days=730)

def fetch_stock_data(tickers: Sequence[str], period: str = "2y") -> Dict[str, pd.DataFrame]:
    """
    Fetch stock data for multiple tickers, using local cache when possible.
    Uses bulk download for efficiency when multiple tickers need updates.
    """
    if not tickers:
        return {}

    db = DataManager()
    start_date = parse_period(period)
    result = {}
    need_download = []
    
    # Step 1: Try to load from database
    for ticker in tickers:
        cached_df = db.load_data(ticker, start_date=start_date)
        
        if not cached_df.empty:
            latest_date = cached_df.index[-1]
            # Check if data is up-to-date (within last 2 days to account for weekends)
            if latest_date >= datetime.now() - timedelta(days=2):
                result[ticker] = cached_df
            else:
                need_download.append(ticker)
                result[ticker] = cached_df  # Keep cached data as fallback
        else:
            need_download.append(ticker)
    
    # Step 2: Bulk download for tickers that need updates
    if need_download:
        try:
            logger.info(f"Downloading data for {len(need_download)} tickers: {need_download}")
            # Use bulk download for efficiency
            raw = yf.download(need_download, period=period, group_by='ticker', auto_adjust=True, threads=True)
            
            if not raw.empty:
                processed = process_downloaded_data(raw, need_download)
                
                # Save to database and update results
                for ticker, df in processed.items():
                    if not df.empty:
                        db.save_data(df, ticker)
                        # Reload from DB to ensure consistency
                        result[ticker] = db.load_data(ticker, start_date=start_date)
            
        except Exception as e:
            logger.error(f"Error downloading data for {need_download}: {e}")
            # Fall back to cached data if download fails
    
    return result


def get_latest_price(df: pd.DataFrame) -> float:
    """Returns the latest close price from a dataframe."""
    if df is None or df.empty:
        return 0.0
    return df['Close'].iloc[-1]


def fetch_macro_data(period: str = "2y") -> Dict[str, pd.DataFrame]:
    """為替や株価指数などのマクロ指標データをまとめて取得する。"""
    tickers = {
        "USDJPY": "JPY=X",
        "SP500": "^GSPC",
        "US10Y": "^TNX",
        "US02Y": "^IRX",  # 2-Year Treasury (for yield curve)
        "VIX": "^VIX",    # Volatility Index
        "OIL": "CL=F",    # Crude Oil Futures
        "GOLD": "GC=F",   # Gold Futures
    }

    try:
        raw = yf.download(list(tickers.values()), period=period, group_by='ticker', auto_adjust=True, threads=True)
    except Exception as exc:  # pragma: no cover - 例外経路はテストでモック化
        logger.error("Error fetching macro data: %s", exc)
        return {}

    return process_downloaded_data(raw, tickers.keys(), tickers)


def fetch_fundamental_data(ticker: str) -> Optional[Dict[str, Any]]:
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
        logger.error("Error fetching fundamentals for %s: %s", ticker, e)
        return None
