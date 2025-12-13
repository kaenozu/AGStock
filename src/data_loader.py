"""Data loading utilities for AGStock."""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from typing import (Any, Awaitable, Callable, Dict, Mapping, Optional,
                    Sequence, TypeVar)

import pandas as pd
import streamlit as st
import yfinance as yf

from src.constants import (CRYPTO_PAIRS, DEFAULT_REALTIME_BACKOFF_SECONDS,
                           DEFAULT_REALTIME_TTL_SECONDS, FUNDAMENTAL_CACHE_TTL,
                           FX_PAIRS, JP_STOCKS, MARKET_SUMMARY_CACHE_KEY,
                           MARKET_SUMMARY_TTL, MINIMUM_DATA_POINTS,
                           STALE_DATA_MAX_AGE)
from src.data_manager import DataManager
from src.helpers import retry_with_backoff

logger = logging.getLogger(__name__)

try:
    from src.async_data_loader import AsyncDataLoader

    ASYNC_AVAILABLE = True
except ImportError:
    AsyncDataLoader = None  # type: ignore[assignment]
    ASYNC_AVAILABLE = False
    logger.warning("Async data loader not available; falling back to sync mode.")

try:
    from src.cache_manager import CacheManager

    HAS_PERSISTENT_CACHE = True
except ImportError:
    CacheManager = None  # type: ignore[assignment]
    HAS_PERSISTENT_CACHE = False

T = TypeVar("T")

CRYPTO_PAIRS = [
    "BTC-USD",
    "ETH-USD",
    "XRP-USD",
    "SOL-USD",
    "DOGE-USD",
    "BNB-USD",
    "ADA-USD",
    "MATIC-USD",
    "DOT-USD",
    "LTC-USD",
]

FX_PAIRS = [
    "USDJPY=X",
    "EURUSD=X",
    "GBPUSD=X",
    "AUDUSD=X",
    "USDCAD=X",
    "USDCHF=X",
    "EURJPY=X",
    "GBPJPY=X",
]

JP_STOCKS = [
    "7203.T",
    "9984.T",
    "6758.T",
    "8035.T",
    "6861.T",
    "6098.T",
    "4063.T",
    "6367.T",
    "6501.T",
    "7974.T",
    "9432.T",
    "8306.T",
    "7267.T",
    "4502.T",
    "6954.T",
]


# シングルトンキャッシュインスタンスの作成
def _create_cache_instance():
    """キャッシュマネージャーのインスタンスを作成"""
    if HAS_PERSISTENT_CACHE and CacheManager is not None:
        try:
            return CacheManager()
        except Exception as e:
            logger.error(f"Cache manager initialization failed: {e}")
            return None
    return None


_cache_instance: Optional[CacheManager] = _create_cache_instance()
_realtime_cache: Dict[str, tuple[float, pd.DataFrame]] = {}
try:
    _DEFAULT_REALTIME_TTL = int(os.getenv("REALTIME_TTL_SECONDS", str(DEFAULT_REALTIME_TTL_SECONDS)))
except Exception:
    _DEFAULT_REALTIME_TTL = DEFAULT_REALTIME_TTL_SECONDS


def _get_cache() -> Optional[CacheManager]:
    """キャッシュマネージャーのインスタンスを取得"""
    return _cache_instance


def _should_use_async_loader(use_async: bool, tickers: Sequence[str]) -> bool:
    return use_async and ASYNC_AVAILABLE and len(tickers) > 1


def _run_coroutine(coro_factory: Callable[[], Awaitable[T]]) -> T:
    """
    非同期処理を安全に実行するためのヘルパー関数
    既存のイベントループに対応し、安全に非同期処理を実行する
    """
    try:
        # 既存のイベントループを取得
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # イベントループが実行中の場合は新しいループを作成
            new_loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(new_loop)
                return new_loop.run_until_complete(coro_factory())
            finally:
                new_loop.close()
                asyncio.set_event_loop(loop)  # 元のイベントループを復元
        else:
            # イベントループが実行中でなければ直接実行
            return loop.run_until_complete(coro_factory())
    except RuntimeError:
        # イベントループが存在しない場合、新しいループで実行
        return asyncio.run(coro_factory())


def _attempt_async_fetch(
    tickers: Sequence[str],
    period: str,
    interval: str,
) -> Optional[Dict[str, pd.DataFrame]]:
    if not ASYNC_AVAILABLE or AsyncDataLoader is None:
        return None

    loader = AsyncDataLoader()

    async def _runner() -> Dict[str, pd.DataFrame]:
        return await loader.fetch_multiple_async(list(tickers), period, interval)

    try:
        return _run_coroutine(_runner)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Async fetch failed, using sync fallback: %s", exc)
        return None


def _load_cached_ticker(
    db: DataManager,
    ticker: str,
    start_date: datetime,
) -> tuple[Optional[pd.DataFrame], bool]:
    cached_df = db.load_data(ticker, start_date=start_date)
    if cached_df.empty:
        return None, True

    latest_date = cached_df.index[-1]
    is_fresh = latest_date >= datetime.now() - STALE_DATA_MAX_AGE
    has_enough_data = len(cached_df) > MINIMUM_DATA_POINTS
    needs_refresh = not (is_fresh and has_enough_data)
    return cached_df, needs_refresh


def _download_and_cache_missing(
    tickers: Sequence[str],
    period: str,
    interval: str,
    start_date: datetime,
    db: DataManager,
) -> Dict[str, pd.DataFrame]:
    if not tickers:
        return {}

    try:
        logger.info("Downloading %d tickers via yfinance", len(tickers))
        raw = yf.download(
            tickers,
            period=period,
            interval=interval,
            group_by="ticker",
            auto_adjust=True,
            threads=True,
        )
    except Exception as exc:
        logger.error("Error downloading data for %s: %s", tickers, exc)
        from .errors import DataLoadError

        raise DataLoadError(
            message=f"Failed to download data for tickers: {tickers}",
            ticker=",".join(tickers) if tickers else None,
            details={"period": period, "interval": interval, "original_error": str(exc)},
        ) from exc

    if raw.empty:
        return {}

    processed = process_downloaded_data(raw, tickers)
    updated: Dict[str, pd.DataFrame] = {}

    for ticker, df in processed.items():
        if df.empty:
            continue
        try:
            db.save_data(df, ticker)
            refreshed = db.load_data(ticker, start_date=start_date)
            if not refreshed.empty:
                updated[ticker] = refreshed
        except Exception as exc:
            logger.error("Error saving/loading data for %s: %s", ticker, exc)
            from .errors import DataLoadError

            raise DataLoadError(
                message=f"Failed to save/load data for ticker: {ticker}",
                ticker=ticker,
                details={"original_error": str(exc)},
            ) from exc

    return updated


def process_downloaded_data(
    raw_data: pd.DataFrame,
    tickers: Sequence[str],
    column_map: Optional[Mapping[str, str]] = None,
) -> Dict[str, pd.DataFrame]:
    """Normalize the structure returned by yfinance.download into per-ticker dataframes."""
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
    """Convert a period string such as '2y' or '1mo' into a start datetime."""
    now = datetime.now()
    if period.endswith("y"):
        years = int(period[:-1])
        return now - timedelta(days=years * 365)
    if period.endswith("mo"):
        months = int(period[:-2])
        return now - timedelta(days=months * 30)
    if period.endswith("d"):
        days = int(period[:-1])
        return now - timedelta(days=days)
    return now - timedelta(days=730)


@st.cache_data(ttl=3600, show_spinner=False)
@retry_with_backoff(retries=3, backoff_in_seconds=2)
def fetch_stock_data(
    tickers: Sequence[str],
    period: str = "2y",
    interval: str = "1d",
    use_async: bool = True,
) -> Dict[str, pd.DataFrame]:
    """Fetch price history for one or more tickers."""
    if not tickers:
        return {}

    if _should_use_async_loader(use_async, tickers):
        async_result = _attempt_async_fetch(tickers, period, interval)
        if async_result is not None:
            return async_result

    logger.info("Using sync loader for %d tickers", len(tickers))

    db = DataManager()
    start_date = parse_period(period)
    result: Dict[str, pd.DataFrame] = {}
    need_refresh: list[str] = []

    for ticker in tickers:
        cached_df, needs_refresh = _load_cached_ticker(db, ticker, start_date)
        if cached_df is not None:
            result[ticker] = cached_df
        if needs_refresh:
            need_refresh.append(ticker)

    downloaded = _download_and_cache_missing(need_refresh, period, interval, start_date, db)
    result.update(downloaded)

    return result


def fetch_external_data(period: str = "2y") -> Dict[str, pd.DataFrame]:
    """Fetch external market indicators (VIX, USDJPY, etc.)."""
    external_tickers = {
        "VIX": "^VIX",
        "USDJPY": "JPY=X",
        "SP500": "^GSPC",
        "NIKKEI": "^N225",
        "GOLD": "GC=F",
        "OIL": "CL=F",
        "US10Y": "^TNX",
    }

    yf_tickers = list(external_tickers.values())
    raw_data = fetch_stock_data(yf_tickers, period=period)

    data: Dict[str, pd.DataFrame] = {}
    ticker_map = {v: k for k, v in external_tickers.items()}

    for yf_ticker, df in raw_data.items():
        alias = ticker_map.get(yf_ticker)
        if alias:
            data[alias] = df

    return data


def get_latest_price(df: pd.DataFrame) -> float:
    """Return the most recent closing price from a dataframe."""
    if df is None or df.empty:
        return 0.0
    return float(df["Close"].iloc[-1])


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_macro_data(period: str = "2y") -> Dict[str, pd.DataFrame]:
    """Legacy macro data fetcher (kept for compatibility)."""
    return fetch_external_data(period)


def fetch_fundamental_data(ticker: str) -> Optional[Dict[str, Any]]:
    """Fetch fundamental metrics for a given ticker with cache support."""
    cache = _get_cache()
    cache_key = f"fundamental::{ticker.upper()}"

    if cache:
        cached = cache.get(cache_key)
        if cached:
            return cached

    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
    except Exception as exc:
        logger.error("Error fetching fundamentals for %s: %s", ticker, exc)
        return None

    result = {
        "trailingPE": info.get("trailingPE"),
        "priceToBook": info.get("priceToBook"),
        "returnOnEquity": info.get("returnOnEquity"),
        "marketCap": info.get("marketCap"),
        "forwardPE": info.get("forwardPE"),
        "dividendYield": info.get("dividendYield"),
    }

    if cache:
        cache.set(cache_key, result, ttl_seconds=FUNDAMENTAL_CACHE_TTL)

    return result


def fetch_market_summary() -> tuple[pd.DataFrame, Dict[str, Any]]:
    """Fetch a lightweight market summary with persistent caching."""
    cache = _get_cache()

    if cache:
        cached_payload = cache.get(MARKET_SUMMARY_CACHE_KEY)
        if cached_payload:
            try:
                summary_df = pd.DataFrame(cached_payload.get("summary_data", []))
                stats = cached_payload.get("stats", {})
                return summary_df, stats
            except Exception as exc:
                logger.warning("Cached market summary decode failed: %s", exc)

    market_df_dict = fetch_external_data(period="1mo")
    summary_data: list[Dict[str, float]] = []
    stats: Dict[str, Any] = {}

    for ticker_name, df in market_df_dict.items():
        if df is None or df.empty or "Close" not in df.columns:
            continue

        current_price = float(df["Close"].iloc[-1])
        prev_price = float(df["Close"].iloc[-2]) if len(df) > 1 else current_price
        change_pct = (current_price - prev_price) / prev_price if prev_price else 0.0

        stats[ticker_name] = {
            "price": current_price,
            "change_percent": change_pct,
        }

        summary_data.append(
            {
                "ticker": ticker_name,
                "price": current_price,
                "change_percent": change_pct,
            }
        )

    summary_df = pd.DataFrame(summary_data)

    if cache:
        cache.set(
            MARKET_SUMMARY_CACHE_KEY,
            {"stats": stats, "summary_data": summary_data},
            ttl_seconds=MARKET_SUMMARY_TTL,
        )

    return summary_df, stats


DEFAULT_BACKOFF = int(os.getenv("REALTIME_BACKOFF_SECONDS", str(DEFAULT_REALTIME_BACKOFF_SECONDS)))


@retry_with_backoff(retries=2, backoff_in_seconds=DEFAULT_BACKOFF)
def fetch_realtime_data(
    ticker: str,
    period: str = "5d",
    interval: str = "1m",
    ttl_seconds: Optional[int] = None,
) -> pd.DataFrame:
    """ライトウェイトなリアルタイム価格取得（ライブ取引用）。短期キャッシュ付き。"""
    if not ticker:
        return pd.DataFrame()

    ttl = ttl_seconds if ttl_seconds is not None else _DEFAULT_REALTIME_TTL

    cache_key = f"{ticker}::{period}::{interval}"
    now = time.time()
    cached = _realtime_cache.get(cache_key)
    if cached:
        cached_ts, cached_df = cached
        if now - cached_ts <= ttl:
            return cached_df.copy()

    try:
        df = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
        )
    except Exception as exc:
        logger.error("Realtime fetch failed for %s: %s", ticker, exc)
        return pd.DataFrame()

    if df is None or df.empty:
        return pd.DataFrame()

    if isinstance(df, pd.Series):
        df = df.to_frame()

    df.dropna(inplace=True)
    _realtime_cache[cache_key] = (now, df)
    return df.copy()
