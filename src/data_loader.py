import logging
from typing import Dict, Mapping, Sequence

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
    """
    if not tickers:
        return {}

    db = DataManager()
    start_date = parse_period(period)
    result = {}
    
    # Identify what needs to be fetched
    tickers_to_download = []
    
    for ticker in tickers:
        latest_date = db.get_latest_date(ticker)
        
        if latest_date is None:
            # No data, fetch full period
            tickers_to_download.append(ticker)
        elif latest_date < datetime.now() - timedelta(days=1):
            # Data exists but might be stale, fetch from latest_date
            # For simplicity in bulk download, we might just re-download the missing tail for all
            # But yfinance bulk download is easiest with a single start date.
            # Mixed strategies are complex.
            # Strategy: 
            # 1. Load what we have from DB.
            # 2. If end of DB data < required end (now), fetch incremental.
            
            # For now, to keep bulk download efficiency, let's try to fetch only if significantly outdated
            # or if the requested period goes further back than what we have.
            
            # Actually, simplest robust approach for now:
            # Check if we have data covering the requested period.
            # If not, or if we need new data, download.
            
            # Incremental update per ticker is safer but slower than bulk.
            # Let's stick to the original plan:
            # 1. Try to load from DB.
            # 2. If missing/insufficient, download from API.
            pass

    # Simplified Logic for Robustness:
    # We will iterate tickers, check DB. If up-to-date, use it. If not, add to download list.
    # But wait, bulk download is much faster.
    
    # Hybrid approach:
    # 1. Load all available data from DB.
    # 2. Identify tickers that need update (latest_date < yesterday).
    # 3. Bulk download for those tickers from their earliest missing date? 
    #    No, bulk download needs common start.
    
    # Revised Strategy:
    # Always try to fetch "new" data for ALL tickers from the earliest "latest_date" among them?
    # Or just use yfinance caching? No, we want our own DB.
    
    # Let's do this:
    # 1. For each ticker, check latest_date.
    # 2. If latest_date is old, fetch data from latest_date to Now.
    # 3. Save to DB.
    # 4. Load requested period from DB.
    
    for ticker in tickers:
        latest_date = db.get_latest_date(ticker)
        
        # Determine fetch start date
        if latest_date:
            fetch_start = latest_date + timedelta(days=1)
        else:
            fetch_start = start_date
            
        if fetch_start < datetime.now():
            try:
                # Fetch individual ticker to support different start dates
                # This is slower than bulk but correct for incremental updates
                new_data = yf.download(ticker, start=fetch_start, progress=False, threads=False)
                if not new_data.empty:
                    db.save_data(new_data, ticker)
            except Exception as e:
                logger.error(f"Error updating {ticker}: {e}")
        
        # Load from DB
        df = db.load_data(ticker, start_date=start_date)
        if not df.empty:
            result[ticker] = df
            
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
    }

    try:
        raw = yf.download(list(tickers.values()), period=period, group_by='ticker', auto_adjust=True, threads=True)
    except Exception as exc:  # pragma: no cover - 例外経路はテストでモック化
        logger.error("Error fetching macro data: %s", exc)
        return {}

    return process_downloaded_data(raw, tickers.keys(), tickers)


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
        logger.error("Error fetching fundamentals for %s: %s", ticker, e)
        return None
