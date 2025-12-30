# """Data loading utilities for AGStock."""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, Mapping, Optional, Sequence, TypeVar

import pandas as pd
import streamlit as st
import yfinance as yf

from src.constants import (
    CRYPTO_PAIRS,
    DEFAULT_REALTIME_BACKOFF_SECONDS,
    DEFAULT_REALTIME_TTL_SECONDS,
    FUNDAMENTAL_CACHE_TTL,
    FX_PAIRS,
    JP_STOCKS,
    MARKET_SUMMARY_CACHE_KEY,
    MARKET_SUMMARY_TTL,
    MINIMUM_DATA_POINTS,
    STALE_DATA_MAX_AGE,
)
from src.data_manager import DataManager

logger = logging.getLogger(__name__)


class MarketDataLoader:
    #     """市場データを取得・管理するクラス"""

    def __init__(self):
        self.data_manager = DataManager()

    def get_stock_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        #         """指定した銘柄の株価データを取得します。"""
        try:
            df = yf.download(ticker, period=period)
            if df.empty:
                logger.warning(f"No data found for {ticker}")
                return pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()

    @retry_with_backoff(retries=3)
    def fetch_realtime(self, ticker: str) -> pd.DataFrame:
        #         """リアルタイムデータを取得します。"""
        return yf.download(ticker, period="1d", interval="1m")


def fetch_macro_data(period: str = "1mo") -> Dict[str, pd.DataFrame]:
    #     """マクロ経済指標を取得します。"""
    res = {}
    for ticker in ["^GSPC", "JPY=X"]:
        res[ticker] = yf.download(ticker, period=period)
    return res
