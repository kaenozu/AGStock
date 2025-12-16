"""デモモード用の簡易ロードテスト。"""

import statistics
import time

from src import demo_data


def run(iterations: int = 50):
    durations = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        demo_data.generate_positions()
        demo_data.generate_trade_history()
        demo_data.generate_equity_history()
        durations.append(time.perf_counter() - t0)
    p50 = statistics.median(durations)
    p95 = statistics.quantiles(durations, n=100)[94]
    print(f"Runs: {iterations} | p50: {p50*1000:.1f} ms | p95: {p95*1000:.1f} ms")


if __name__ == "__main__":
    run()
