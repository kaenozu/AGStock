"""
Send combined risk snapshot + data quality summary via SmartNotifier.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from src.data_loader import fetch_stock_data
from src.data_quality_guard import assess_quality, should_block_trading
from src.risk_guard import RiskGuard
from src.smart_notifier import SmartNotifier


def summarize_risk(state_path: Path) -> List[str]:
    state: Dict[str, Any] = {}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    initial_value = state.get("daily_start_value", 1_000_000)
    guard = RiskGuard(
        initial_portfolio_value=initial_value,
        daily_loss_limit_pct=state.get("daily_loss_limit_pct", -5.0),
        max_position_size_pct=state.get("max_position_size_pct", 10.0),
        max_vix=state.get("max_vix", 40.0),
        max_drawdown_limit_pct=state.get("max_drawdown_limit_pct", -20.0),
    )
    guard.consecutive_losses = state.get("consecutive_losses", guard.consecutive_losses)

    lines = [
        f"state: {state_path.resolve()}",
        f"daily_start={guard.daily_start_value:,.0f} HWM={guard.high_water_mark:,.0f}",
        f"loss_limit={guard.daily_loss_limit_pct}% dd_limit={guard.max_drawdown_limit_pct}% pos_limit={guard.max_position_size_pct}% VIX<{guard.max_vix}",
        f"consec_losses={guard.consecutive_losses}/{guard.max_consecutive_losses} circuit={guard.circuit_breaker_triggered} drawdown_halt={guard.drawdown_triggered}",
    ]
    return lines


def summarize_quality(tickers: List[str], period: str) -> List[str]:
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
    parser = argparse.ArgumentParser(description="Notify combined risk + data quality summary.")
    parser.add_argument("--config", default="config.json", help="Path to config.json for notifier settings")
    parser.add_argument("--tickers", nargs="*", default=["^N225", "^GSPC", "AAPL"], help="Tickers to scan")
    parser.add_argument("--period", default="6mo", help="History period (default: 6mo)")
    parser.add_argument("--risk-state", default="risk_state.json", help="Risk state file path")
    args = parser.parse_args()

    notifier = SmartNotifier(config_path=args.config)
    sections: List[str] = []

    risk_lines = summarize_risk(Path(args.risk_state))
    sections.append("[Risk]")
    sections.extend(risk_lines)

    quality_lines = summarize_quality(args.tickers, args.period)
    sections.append("[Data Quality]")
    sections.extend(quality_lines)

    body = "\n".join(sections)
    ok = notifier.send_text(body, title="Ops Summary")
    if not ok:
        print("No channel configured; summary below:")
        print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
