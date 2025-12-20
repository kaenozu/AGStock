"""
Print current risk guard state and thresholds.
"""

import json
from pathlib import Path
from typing import Any, Dict

from src.risk_guard import RiskGuard


def load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    state_path = Path("risk_state.json")
    state = load_state(state_path)

    initial_value = state.get("daily_start_value", 1_000_000)
    guard = RiskGuard(
        initial_portfolio_value=initial_value,
        daily_loss_limit_pct=state.get("daily_loss_limit_pct", -5.0),
        max_position_size_pct=state.get("max_position_size_pct", 10.0),
        max_vix=state.get("max_vix", 40.0),
        max_drawdown_limit_pct=state.get("max_drawdown_limit_pct", -20.0),
    )
    # overwrite counters from state if present
    guard.consecutive_losses = state.get("consecutive_losses", guard.consecutive_losses)

    print("=== Risk Snapshot ===")
    print(f"state file      : {state_path.resolve()}")
    print(f"daily start     : {guard.daily_start_value:,.2f}")
    print(f"high water mark : {guard.high_water_mark:,.2f}")
    print(f"daily loss lim  : {guard.daily_loss_limit_pct}%")
    print(f"drawdown limit  : {guard.max_drawdown_limit_pct}%")
    print(f"max position    : {guard.max_position_size_pct}%")
    print(f"max VIX         : {guard.max_vix}")
    print(f"consec losses   : {guard.consecutive_losses}/{guard.max_consecutive_losses}")
    print(f"circuit breaker : {guard.circuit_breaker_triggered}")
    print(f"drawdown halt   : {guard.drawdown_triggered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
