import numpy as np
import pandas as pd

from src.strategies import DeepLearningStrategy


def create_synthetic_data(length=1000):
    """
    Creates synthetic price data (sine wave + noise)
    """
    x = np.linspace(0, 50, length)
    # Sine wave with trend
    price = 100 + 10 * np.sin(x) + 0.5 * x + np.random.normal(0, 1, length)
    volume = 1000 + 100 * np.abs(np.sin(x)) + np.random.normal(0, 50, length)

    df = pd.DataFrame(
        {"Close": price, "Volume": volume, "High": price + 1, "Low": price - 1, "Open": price},
        index=pd.date_range(start="2020-01-01", periods=length, freq="D"),
    )

    return df


def verify_dl_strategy():
    print("=== Verifying Deep Learning Strategy (Walk-Forward) ===")

    # 1. Create Data
    df = create_synthetic_data(length=500)
    print(f"Data created: {len(df)} rows")

    # 2. Initialize Strategy
    # Use small windows for fast verification
    strategy = DeepLearningStrategy(lookback=30, epochs=2, batch_size=16, train_window_days=100, predict_window_days=10)

    # 3. Run Strategy
    print("Running strategy...")
    signals = strategy.generate_signals(df)

    # 4. Analyze Results
    print(f"Signals generated: {len(signals)}")
    buy_signals = signals[signals == 1].count()
    sell_signals = signals[signals == -1].count()
    print(f"Buy Signals: {buy_signals}")
    print(f"Sell Signals: {sell_signals}")

    # 5. Check for Leakage (Heuristic)
    # If leakage exists, the model might predict perfectly on random noise or future data.
    # Here we check if it produces signals at all in the valid range.
    # Signals should only start after train_window + lookback

    first_signal_idx = signals[signals != 0].first_valid_index()
    if first_signal_idx:
        print(f"First signal date: {first_signal_idx}")
        days_skipped = (first_signal_idx - df.index[0]).days
        print(f"Days skipped: {days_skipped} (Expected >= 130)")

        if days_skipped < 130:  # 100 train + 30 lookback
            print("WARNING: Signals generated too early! Possible leakage or index error.")
        else:
            print("PASS: Signals generated after training window.")
    else:
        print("WARNING: No signals generated.")

    # 6. Visual Check (Optional)
    # plt.figure(figsize=(12, 6))
    # plt.plot(df.index, df['Close'], label='Price')
    # plt.scatter(signals[signals==1].index, df.loc[signals==1, 'Close'], marker='^', color='g', label='Buy')
    # plt.scatter(signals[signals==-1].index, df.loc[signals==-1, 'Close'], marker='v', color='r', label='Sell')
    # plt.legend()
    # plt.show()


if __name__ == "__main__":
    verify_dl_strategy()
