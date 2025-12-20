"""
Send data quality summary to notification channels (Slack/Discord/LINE via SmartNotifier).
"""

import argparse
import sys
from pathlib import Path
from typing import List

from src.data_loader import fetch_stock_data
from src.data_quality_guard import assess_quality, should_block_trading
from src.smart_notifier import SmartNotifier


def build_summary(tickers: List[str], period: str) -> List[str]:
    data = fetch_stock_data(tickers, period=period, interval="1d", use_async=False)
    lines: List[str] = []
    for ticker, df in data.items():
        metrics = assess_quality(df)
        reason = should_block_trading(metrics)
        status = "BLOCK" if reason else "OK"
        lines.append(
            f"{ticker:10} | missing={metrics['missing_ratio']:.2%} "
            f"| zmax={metrics['max_abs_zscore']:.1f} "
            f"| jump={metrics['max_price_jump_pct']:.1f}% "
            f"| {status}{': ' + reason if reason else ''}"
        )
    return sorted(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Notify data quality summary via SmartNotifier.")
    parser.add_argument("--config", default="config.json", help="Path to config.json for notifier settings")
    parser.add_argument("--tickers", nargs="*", default=["^N225", "^GSPC", "AAPL"], help="Tickers to scan")
    parser.add_argument("--period", default="6mo", help="History period (default: 6mo)")
    args = parser.parse_args()

    notifier = SmartNotifier(config_path=args.config)
    summary = build_summary(args.tickers, args.period)
    if not summary:
        print("No data to report")
        return 0

    ok = notifier.send_data_quality_summary(summary_lines=summary, title="Data Quality Summary")
    print("Sent" if ok else "No channel configured; printed summary below:")
    if not ok:
        for line in summary:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
