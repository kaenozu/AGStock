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


def fetch_stock_data(tickers: Sequence[str], period: str = "2y") -> Dict[str, pd.DataFrame]:
    """複数ティッカーの株価データを取得する。"""
    if not tickers:
        return {}

    try:
        raw = yf.download(tickers, period=period, group_by='ticker', auto_adjust=True, threads=True)
    except Exception as exc:  # pragma: no cover - 例外経路はテストでモック化
        logger.error("Error fetching data: %s", exc)
        return {}

    return process_downloaded_data(raw, tickers)


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
