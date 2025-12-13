import os
import sys

import yfinance as yf

sys.path.append(os.getcwd())

from src.cache_config import install_cache
from src.regime_detector import RegimeDetector

install_cache()


def main():
    ticker = "7203.T"
    print(f"Fetching data for {ticker}...")
    df = yf.download(ticker, period="1y", auto_adjust=True, progress=False)

    if df.empty:
        print("Error: No data fetched.")
        return

    print(f"Data fetched: {len(df)} rows.")

    detector = RegimeDetector()
    regime = detector.detect_regime(df)

    info = detector.get_regime_signal(df)

    print("\n=== Market Regime Detection Report ===")
    print(f"Ticker: {ticker}")
    # Handle potential Series/DataFrame output from yfinance
    close_val = df["Close"].iloc[-1]
    if hasattr(close_val, "item"):
        close_val = close_val.item()
    elif hasattr(close_val, "values"):
        close_val = close_val.values[0]

    print(f"Current Price: {close_val:.2f}")
    print(f"Current Regime: {info['regime_name']}")
    print(f"Description: {info['description']}")
    print(
        f"Indicators: SMA50={info['indicators']['SMA_Short']:.2f}, SMA200={info['indicators']['SMA_Long']:.2f}, ADX={info['indicators']['ADX']:.2f}"
    )

    # Check past 5 points to see transition
    print("\nRecent Regimes:")
    for i in range(5, 0, -1):
        idx = -i
        sub_df = df.iloc[: len(df) + idx + 1]  # Simulation of past
        # Note: simplistic simulation, rolling windows need care but for checking change it's ok
        # Actually better to slice properly.
        sub_df = df.iloc[: len(df) - (i - 1)]
        r = detector.detect_regime(sub_df)
        print(f"Day -{i-1}: {r.value}")


if __name__ == "__main__":
    main()
