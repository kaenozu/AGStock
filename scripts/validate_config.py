"""
Simple config validator.

- Validates config JSON structure with lightweight checks.
- If `jsonschema` is installed, uses it; otherwise falls back to manual checks.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _manual_validate(cfg: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    def expect(key: str, typ, required: bool = False):
        if key not in cfg:
            if required:
                errors.append(f"Missing required key: {key}")
            return
        if not isinstance(cfg[key], typ):
            errors.append(f"Invalid type for {key}: expected {typ}, got {type(cfg[key])}")

    expect("volatility_symbols", list)
    expect("market_indices", dict)
    expect("risk_limits", dict, required=True)
    expect("trading_settings", dict)

    risk_limits = cfg.get("risk_limits", {})
    for key in ("max_daily_loss_pct", "max_position_size_pct", "max_volatility_threshold"):
        if key in risk_limits and not isinstance(risk_limits[key], (int, float)):
            errors.append(f"risk_limits.{key} must be number")

    return errors


def validate_with_jsonschema(cfg: Dict[str, Any]) -> List[str]:
    try:
        import jsonschema
    except ImportError:
        return _manual_validate(cfg)

    schema = {
        "type": "object",
        "properties": {
            "volatility_symbols": {"type": "array", "items": {"type": "string"}},
            "market_indices": {"type": "object"},
            "risk_limits": {
                "type": "object",
                "properties": {
                    "max_daily_loss_pct": {"type": "number"},
                    "max_position_size_pct": {"type": "number"},
                    "max_volatility_threshold": {"type": "number"},
                },
            },
            "trading_settings": {"type": "object"},
        },
        "required": ["risk_limits"],
    }
    try:
        jsonschema.validate(cfg, schema)
        return []
    except jsonschema.exceptions.ValidationError as exc:  # type: ignore[attr-defined]
        return [f"Schema validation error: {exc.message}"]


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("config.json")
    if not path.exists():
        print(f"[FAIL] Config file not found: {path}")
        return 1

    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[FAIL] Failed to load JSON: {exc}")
        return 1

    errors = validate_with_jsonschema(cfg)
    if errors:
        print("[FAIL] Config validation failed:")
        for err in errors:
            print(f" - {err}")
        return 2

    print(f"[OK] Config valid: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
