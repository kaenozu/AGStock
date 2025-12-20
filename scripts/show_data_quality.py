"""
Quick data quality report for selected tickers.
"""

import argparse
import sys
from pathlib import Path
from typing import List

from src.data_loader import fetch_stock_data
from src.data_quality_guard import assess_quality, should_block_trading


def main() -> int:
    parser = argparse.ArgumentParser(description="Show data quality metrics per ticker.")
    parser.add_argument("--tickers", nargs="*", default=["7203.T", "9984.T", "AAPL"], help="Tickers to check")
    parser.add_argument("--period", default="6mo", help="Period to fetch (yfinance syntax, default 6mo)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    data = fetch_stock_data(args.tickers, period=args.period, interval="1d", use_async=False)

    rows: List[str] = []
    for ticker, df in data.items():
        metrics = assess_quality(df)
        reason = should_block_trading(metrics)
        rows.append(
            f"{ticker:8} | missing={metrics['missing_ratio']:.2%} "
            f"| zmax={metrics['max_abs_zscore']:.1f} "
            f"| jump={metrics['max_price_jump_pct']:.1f}% "
            f"| {'BLOCK:' + reason if reason else 'OK'}"
        )

    print("Data quality summary:")
    for line in sorted(rows):
        print("  " + line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
