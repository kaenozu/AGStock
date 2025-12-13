import time

import numpy as np
import pandas as pd

from src.features import add_frequency_features


def _naive_frequency_features(df: pd.DataFrame, window: int) -> pd.Series:
    log_ret = np.log(df["Close"] / df["Close"].shift(1)).fillna(0)

    def get_dominant_freq_power(x):
        n = len(x)
        window_func = np.hanning(n)
        x_windowed = x * window_func
        f_transform = np.fft.fft(x_windowed)
        power_spectrum = np.abs(f_transform)[: n // 2]
        if len(power_spectrum) > 1:
            return np.max(power_spectrum[1:])
        return 0.0

    return log_ret.rolling(window=window).apply(get_dominant_freq_power, raw=True)


def test_add_frequency_features_is_faster_than_naive():
    np.random.seed(42)
    window = 20
    rows = 5000
    idx = pd.date_range("2020-01-01", periods=rows, freq="min")
    df = pd.DataFrame({"Close": np.random.rand(rows) * 100 + 100}, index=idx)

    start = time.perf_counter()
    naive_freq = _naive_frequency_features(df, window=window)
    naive_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    optimized_df = add_frequency_features(df, window=window)
    optimized_elapsed = time.perf_counter() - start

    pd.testing.assert_series_equal(
        optimized_df["Freq_Power"].iloc[window - 1 :],
        naive_freq.iloc[window - 1 :],
        rtol=1e-9,
        atol=1e-12,
        check_names=False,
    )

    assert optimized_elapsed < naive_elapsed * 0.6, (
        f"Optimized implementation should be noticeably faster than naive version. "
        f"Naive: {naive_elapsed:.4f}s, Optimized: {optimized_elapsed:.4f}s"
    )
