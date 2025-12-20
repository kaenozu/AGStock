"""
Run a fast smoke test suite.

Intended for PR/quick checks; keeps runtime short by selecting a small set of critical tests.
"""

import argparse
import subprocess
import sys
from pathlib import Path


DEFAULT_TESTS = [
    "tests/test_auth.py",
    "tests/test_ml_pipeline.py",
    "tests/test_optimization_coverage.py",
    "tests/test_optimization_transformer.py",
    "tests/test_performance_metrics_coverage.py",
    "tests/test_benchmark_comparator_coverage.py",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run smoke tests (fast subset).")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional test paths to override default smoke set.",
    )
    parser.add_argument(
        "--maxfail",
        default="1",
        help="Stop after N failures (pytest --maxfail). Default: 1",
    )
    args = parser.parse_args()

    tests = args.paths or DEFAULT_TESTS
    repo_root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, "-m", "pytest", f"--maxfail={args.maxfail}", *tests]
    print(f"[smoke] running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=repo_root)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
