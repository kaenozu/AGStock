import numpy as np
import pandas as pd

from src.patterns import detect_double_bottom, detect_head_and_shoulders_bottom


def create_double_bottom_data():
    """Creates synthetic data for Double Bottom."""
    prices = [100, 95, 90, 85, 80, 85, 90, 95, 90, 85, 81, 85, 90, 95, 100]
    df = pd.DataFrame({"High": prices, "Low": prices, "Close": prices})
    # Add some noise and length
    prefix = [100] * 20
    suffix = [100] * 5
    full_prices = prefix + prices + suffix
    df = pd.DataFrame({"High": full_prices, "Low": full_prices, "Close": full_prices})
    return df


def create_head_and_shoulders_data():
    """Creates synthetic data for Inverse Head & Shoulders."""
    # Left Shoulder (Low 85), Head (Low 80), Right Shoulder (Low 85)
    # Need more points between extrema for window=5 detection

    # Down to Left Shoulder
    p1 = np.linspace(100, 85, 10).tolist()
    # Up to Neckline
    p2 = np.linspace(85, 95, 10)[1:].tolist()
    # Down to Head
    p3 = np.linspace(95, 80, 10)[1:].tolist()
    # Up to Neckline
    p4 = np.linspace(80, 95, 10)[1:].tolist()
    # Down to Right Shoulder
    p5 = np.linspace(95, 85, 10)[1:].tolist()
    # Up breakout
    p6 = np.linspace(85, 100, 10)[1:].tolist()

    prices = p1 + p2 + p3 + p4 + p5 + p6

    prefix = [100] * 20
    full_prices = prefix + prices
    df = pd.DataFrame({"High": full_prices, "Low": full_prices, "Close": full_prices})
    return df


def test_patterns():
    print("Testing Double Bottom...")
    df_db = create_double_bottom_data()
    res_db = detect_double_bottom(df_db)
    if res_db:
        print(f"SUCCESS: Detected {res_db['pattern']}")
    else:
        print("FAILURE: Double Bottom not detected")

    print("\nTesting Head & Shoulders...")
    df_hs = create_head_and_shoulders_data()
    print(f"Data length: {len(df_hs)}")

    from src.patterns import find_local_extrema

    ext = find_local_extrema(df_hs, window=5)
    print(f"Extrema found:\n{ext[ext['is_min']]}")

    res_hs = detect_head_and_shoulders_bottom(df_hs)
    if res_hs:
        print(f"SUCCESS: Detected {res_hs['pattern']}")
    else:
        print("FAILURE: Head & Shoulders not detected")


if __name__ == "__main__":
    test_patterns()
