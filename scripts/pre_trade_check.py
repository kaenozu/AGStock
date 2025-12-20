"""
Pre-trade warm-up check.

- Validate config.json schema (best-effort without failing if jsonschema is missing)
- Inspect current risk state
- Run lightweight data-quality scan for a few tickers
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.data_loader import fetch_stock_data
from src.data_quality_guard import assess_quality, should_block_trading
from src.risk_guard import RiskGuard


def load_config(path: Path) -> Tuple[Dict[str, Any], List[str]]:
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, [f"config file not found: {path}"]
    except Exception as exc:
        return {}, [f"failed to load config: {exc}"]

    try:
        from scripts.validate_config import validate_with_jsonschema  # type: ignore
    except Exception:
        def validate_with_jsonschema(cfg: Dict[str, Any]) -> List[str]:  # type: ignore
            return []

    errors = validate_with_jsonschema(cfg)
    return cfg, errors


def summarize_risk_state(state_path: Path = Path("risk_state.json")) -> Dict[str, Any]:
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
    return {
        "daily_start_value": guard.daily_start_value,
        "high_water_mark": guard.high_water_mark,
        "daily_loss_limit_pct": guard.daily_loss_limit_pct,
        "max_drawdown_limit_pct": guard.max_drawdown_limit_pct,
        "max_position_size_pct": guard.max_position_size_pct,
        "max_vix": guard.max_vix,
        "consecutive_losses": guard.consecutive_losses,
        "max_consecutive_losses": guard.max_consecutive_losses,
        "circuit_breaker": guard.circuit_breaker_triggered,
        "drawdown_halt": guard.drawdown_triggered,
        "state_file": str(state_path.resolve()),
    }


def check_data_quality(tickers: List[str], period: str) -> List[str]:
    results: List[str] = []
    data = fetch_stock_data(tickers, period=period, interval="1d", use_async=False)
    for ticker, df in data.items():
        metrics = assess_quality(df)
        reason = should_block_trading(metrics)
        status = "BLOCK" if reason else "OK"
        results.append(
            f"{ticker:10} | missing={metrics['missing_ratio']:.2%} "
            f"| zmax={metrics['max_abs_zscore']:.1f} "
            f"| jump={metrics['max_price_jump_pct']:.1f}% "
            f"| {status}{': ' + reason if reason else ''}"
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-trade warm-up check")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    parser.add_argument("--tickers", nargs="*", default=["^N225", "^GSPC", "AAPL"], help="Tickers to scan for quality")
    parser.add_argument("--period", default="6mo", help="History period for quality scan (default: 6mo)")
    args = parser.parse_args()

    print("=== Pre-trade check ===")

    cfg_path = Path(args.config)
    _, cfg_errors = load_config(cfg_path)
    if cfg_errors:
        print("[CONFIG] FAIL")
        for e in cfg_errors:
            print("  -", e)
    else:
        print("[CONFIG] OK")

    risk = summarize_risk_state()
    print("[RISK] state file:", risk["state_file"])
    print(
        f"       daily_start={risk['daily_start_value']:,.0f} "
        f"HWM={risk['high_water_mark']:,.0f} "
        f"loss_limit={risk['daily_loss_limit_pct']}% "
        f"dd_limit={risk['max_drawdown_limit_pct']}% "
        f"pos_limit={risk['max_position_size_pct']}% "
        f"VIX<{risk['max_vix']}"
    )
    print(
        f"       consecutive_losses={risk['consecutive_losses']}/{risk['max_consecutive_losses']} "
        f"circuit={risk['circuit_breaker']} drawdown_halt={risk['drawdown_halt']}"
    )

    print(f"[DATA] quality scan ({args.period})")
    for line in check_data_quality(args.tickers, args.period):
        print("  " + line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
