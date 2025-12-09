import logging
from typing import Dict, Mapping, Sequence, Any, Optional
import streamlit as st
import asyncio
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from src.data_manager import DataManager

logger = logging.getLogger(__name__)

# Asset Classes
CRYPTO_PAIRS = [
    "BTC-USD", "ETH-USD", "XRP-USD", "SOL-USD", "DOGE-USD",
    "BNB-USD", "ADA-USD", "MATIC-USD", "DOT-USD", "LTC-USD"
]

FX_PAIRS = [
    "USDJPY=X", "EURUSD=X", "GBPUSD=X", "AUDUSD=X", "USDCAD=X",
    "USDCHF=X", "EURJPY=X", "GBPJPY=X"
]

JP_STOCKS = [
    "7203.T", "9984.T", "6758.T", "8035.T", "6861.T",
    "6098.T", "4063.T", "6367.T", "6501.T", "7974.T",
    "9432.T", "8306.T", "7267.T", "4502.T", "6954.T"
]

# 非同期ローダーのインポート（オプション）
try:
    from src.async_data_loader import AsyncDataLoader
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False
    logger.warning("Async data loader not available")


def process_downloaded_data(
    raw_data: pd.DataFrame,
    tickers: Sequence[str],
    column_map: Mapping[str, str] | None = None,
) -> Dict[str, pd.DataFrame]:
    """
    yfinanceのダウンロード結果をティッカーごとに分割してクリーンアップする。
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
        return now - timedelta(days=730)


from src.utils import retry_with_backoff

@st.cache_data(ttl=3600, show_spinner=False)
@retry_with_backoff(retries=3, backoff_in_seconds=2)
def fetch_stock_data(
    tickers: Sequence[str],
    period: str = "2y",
    interval: str = "1d",
    use_async: bool = True
) -> Dict[str, pd.DataFrame]:
    """
    Fetch stock data for multiple tickers.
    """
    if not tickers:
        return {}

    # 非同期ローダーを使用（利用可能かつ有効な場合）
    if use_async and ASYNC_AVAILABLE and len(tickers) > 1:
        try:
            # 新しいイベントループを作成（Streamlitのスレッド問題回避）
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            loader = AsyncDataLoader()
            return loop.run_until_complete(loader.fetch_multiple_async(list(tickers), period, interval))
        except Exception as e:
            logger.warning(f"Async fetch failed, falling back to sync: {e}")
            # フォールバック

    # 同期処理
    logger.info(f"Using sync loader for {len(tickers)} tickers")
    db = DataManager()
    start_date = parse_period(period)
    result = {}
    need_download = []

    # Step 1: Try to load from database
    for ticker in tickers:
        cached_df = db.load_data(ticker, start_date=start_date)

        if not cached_df.empty:
            latest_date = cached_df.index[-1]
            # データが新鮮で、かつ十分な量があるかチェック
            is_fresh = latest_date >= datetime.now() - timedelta(days=2)
            has_enough_data = len(cached_df) > 50  # 少なくとも50件はあるべき

            if is_fresh and has_enough_data:
                result[ticker] = cached_df
            else:
                need_download.append(ticker)
                # フォールバックとして保持するが、ダウンロード成功時に上書きされる
                result[ticker] = cached_df
        else:
            need_download.append(ticker)

    # Step 2: Bulk download for tickers that need updates
    if need_download:
        try:
            logger.info(f"Downloading data for {len(need_download)} tickers: {need_download}")
            # キャッシュを回避するために ignore_tz=True などを検討したが、まずはログ出力
            raw = yf.download(need_download, period=period, group_by='ticker', auto_adjust=True, threads=True)

            if not raw.empty:
                logger.info(f"Downloaded raw data shape: {raw.shape}")
                processed = process_downloaded_data(raw, need_download)

                for ticker, df in processed.items():
                    logger.info(f"Processed {ticker}: {len(df)} rows")
                    if not df.empty:
                        db.save_data(df, ticker)
                        result[ticker] = db.load_data(ticker, start_date=start_date)

        except Exception as e:
            logger.error(f"Error downloading data for {need_download}: {e}")

    return result


def fetch_external_data(period: str = "2y") -> Dict[str, pd.DataFrame]:
    """
    Fetches external market data (VIX, USD/JPY, etc.)
    """
    external_tickers = {
        'VIX': '^VIX',       # Volatility Index
        'USDJPY': 'JPY=X',   # USD/JPY Exchange Rate
        'SP500': '^GSPC',    # S&P 500
        'NIKKEI': '^N225',   # Nikkei 225
        'GOLD': 'GC=F',      # Gold Futures
        'OIL': 'CL=F',       # Crude Oil Futures
        'US10Y': '^TNX'      # US 10-Year Treasury Yield
    }

    # Use fetch_stock_data logic (async/cache)
    # Map back to internal names
    yf_tickers = list(external_tickers.values())
    raw_data = fetch_stock_data(yf_tickers, period=period)

    data = {}
    ticker_map = {v: k for k, v in external_tickers.items()}

    for yf_ticker, df in raw_data.items():
        if yf_ticker in ticker_map:
            data[ticker_map[yf_ticker]] = df

    return data


def get_latest_price(df: pd.DataFrame) -> float:
    """Returns the latest close price from a dataframe."""
    if df is None or df.empty:
        return 0.0
    return df['Close'].iloc[-1]


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_macro_data(period: str = "2y") -> Dict[str, pd.DataFrame]:
    """Legacy macro data fetcher (kept for compatibility)"""
    return fetch_external_data(period)


def fetch_fundamental_data(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetches fundamental data for a single ticker.
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
