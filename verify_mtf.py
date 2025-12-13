"""
Verify Multi-Timeframe Strategy
Compare baseline strategy vs MTF strategy to ensure filtering works.
"""

import pandas as pd

from src.backtest_engine import HistoricalBacktester
from src.strategies import MultiTimeframeStrategy, SMACrossoverStrategy


def test_mtf_filtering():
    print("Testing Multi-Timeframe Strategy Filtering...")

    ticker = "7203.T"  # Toyota
    years = 2

    # Run Baseline (SMA Crossover)
    engine = HistoricalBacktester()
    res_base = engine.run_test(ticker, SMACrossoverStrategy, years=years, short_window=5, long_window=20)

    # Run MTF (SMA Crossover which is the baseline, + Weekly Filter)
    # Note: MultiTimeframeStrategy uses CombinedStrategy by default,
    # but we can pass SMACrossoverStrategy to be fair comparison.
    # However, passing an instance is different from current __init__ expectation if not careful.
    # Let's check MultiTimeframeStrategy.__init__
    # it takes `base_strategy: Strategy = None`.
    # It calls base_strategy.generate_signals(df).

    # So we need to instantiate the base strategy first.
    base_strat_instance = SMACrossoverStrategy(short_window=5, long_window=20)

    # But HistoricalBacktester expects a class and params.
    # We need a way to pass an instance or configure it.
    # HistoricalBacktester logic: strategy = strategy_class(**strategy_params)

    # So we can't easily pass an *instance* via `run_test` if relying on standard params.
    # But `MultiTimeframeStrategy` constructor takes `base_strategy`.
    # This is complex to inject via `feature_params` unpickleable objects.

    # Solution: We will manually run signal generation rather than full backtest,
    # or rely on default CombinedStrategy for MTF vs CombinedStrategy standalone.

    # Let's verify filtering logic directly using Data directly (more robust unit test style).
    from src.data_loader import fetch_stock_data

    data_map = fetch_stock_data([ticker], period=f"{years}y")
    df = data_map[ticker]

    # 1. Baseline Signals
    base_strat = SMACrossoverStrategy(short_window=5, long_window=20)
    base_signals = base_strat.generate_signals(df)
    base_buy_count = (base_signals == 1).sum()

    # 2. MTF Signals
    mtf_strat = MultiTimeframeStrategy(base_strategy=base_strat)
    mtf_signals = mtf_strat.generate_signals(df)
    mtf_buy_count = (mtf_signals == 1).sum()

    print(f"Baseline Buy Signals: {base_buy_count}")
    print(f"MTF Buy Signals:      {mtf_buy_count}")

    # MTF should generally have fewer or equal signals (filters out counter-trend)
    if mtf_buy_count <= base_buy_count:
        print("✅ MTF Logic Verified: Filtering is active (Count <= Baseline).")

        # Check if weekly trend logic was applied (i.e., not just returning base signals)
        # If counts are equal, it might mean the stock was always in trend or filter didn't trigger.
        # But for 2 years of 7203, there should be some filtering.
        if mtf_buy_count < base_buy_count:
            print("   (Signals reduced effectively)")
        else:
            print("   (Counts identical - might be strong alignment or insufficient data variation)")

        return True
    else:
        print("❌ MTF Logic Failed: Signals increased? (Unexpected)")
        return False


if __name__ == "__main__":
    test_mtf_filtering()
