"""最新モデル/データスナップショットを復元するユーティリティ."""

import argparse
from pathlib import Path

from src.ml_pipeline import DataVersionManager, ModelRegistry


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore latest model and (optionally) latest data snapshot.")
    parser.add_argument("--model", default="walkforward_blend", help="Model name to restore.")
    parser.add_argument("--export-data", type=Path, help="Export restored data to CSV path.")
    args = parser.parse_args()

    registry = ModelRegistry()
    latest = registry.get_latest_model(args.model)
    if not latest:
        print(f"No model found for {args.model}")
    else:
        model, meta = latest
        print(f"Restored model {args.model} version {meta.get('version')} from {meta.get('path')}")
        print(f"Metrics: {meta.get('metrics')}")
        # model object is loaded for interactive use; we don't persist it here.

    if args.export_data:
        dvm = DataVersionManager()
        df = dvm.restore_latest()
        if df is None:
            print("No data snapshot found.")
        else:
            df.to_csv(args.export_data, index=False)
            print(f"Data snapshot exported to {args.export_data} ({len(df)} rows)")


if __name__ == "__main__":
    main()
