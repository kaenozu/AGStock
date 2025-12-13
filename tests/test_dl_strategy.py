import os
import sys

import numpy as np
import pandas as pd

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.strategies import DeepLearningStrategy


def test_dl_strategy():
    print("Testing DeepLearningStrategy...")

    # Create dummy data
    dates = pd.date_range(start="2020-01-01", periods=200)
    data = pd.DataFrame(
        {
            "Close": np.random.randn(200).cumsum() + 100,
            "Open": np.random.randn(200).cumsum() + 100,
            "High": np.random.randn(200).cumsum() + 105,
            "Low": np.random.randn(200).cumsum() + 95,
            "Volume": np.random.randint(1000, 10000, 200),
        },
        index=dates,
    )

    # Initialize strategy with low epochs for speed
    strategy = DeepLearningStrategy(lookback=20, epochs=1, trend_period=0)

    print("Generating signals...")
    try:
        signals = strategy.generate_signals(data)

        print(f"Signals generated. Length: {len(signals)}")
        print(signals.value_counts())

        if len(signals) == len(data):
            print("SUCCESS: Signal length matches data length.")
        else:
            print("FAILURE: Signal length mismatch.")

    except Exception as e:
        print(f"FAILURE: Exception occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_dl_strategy()
