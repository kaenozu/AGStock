"""
Test Phase 30-3: Advanced Risk Management
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

import pandas as pd

from src.data_loader import fetch_stock_data
from src.dynamic_stop import DynamicStopManager
from src.kelly_criterion import KellyCriterion
from src.portfolio_manager import PortfolioManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_risk_management():
    print("=" * 80)
    print("Testing Phase 30-3: Advanced Risk Management")
    print("=" * 80)

    # 1. Test Kelly Criterion
    print("\n1. Testing Kelly Criterion...")
    kelly = KellyCriterion(half_kelly=True, max_position_size=0.2)

    # Case 1: Win Rate 60%, Win/Loss 1.5
    size1 = kelly.calculate_size(0.6, 1.5)
    print(f"  Win Rate 60%, W/L 1.5 -> Size: {size1:.2f} (Expected: ~0.16)")

    # Case 2: Win Rate 40%, Win/Loss 2.0
    size2 = kelly.calculate_size(0.4, 2.0)
    print(f"  Win Rate 40%, W/L 2.0 -> Size: {size2:.2f} (Expected: ~0.05)")

    # Case 3: Losing Strategy
    size3 = kelly.calculate_size(0.4, 1.0)
    print(f"  Win Rate 40%, W/L 1.0 -> Size: {size3:.2f} (Expected: 0.00)")

    # 2. Test Portfolio Manager
    print("\n2. Testing Portfolio Manager...")
    pm = PortfolioManager(max_correlation=0.7, max_sector_exposure=0.5)

    # Mock Correlation Matrix
    corr_data = {"A": [1.0, 0.8, 0.2], "B": [0.8, 1.0, 0.3], "C": [0.2, 0.3, 1.0]}
    corr_matrix = pd.DataFrame(corr_data, index=["A", "B", "C"])

    current_portfolio = ["A"]

    # Check B (High correlation with A)
    can_add_b = pm.check_new_position("B", current_portfolio, corr_matrix)
    print(f"  Can add B (High Corr with A)? {can_add_b} (Expected: False)")

    # Check C (Low correlation with A)
    can_add_c = pm.check_new_position("C", current_portfolio, corr_matrix)
    print(f"  Can add C (Low Corr with A)? {can_add_c} (Expected: True)")

    # 3. Test Dynamic Stop Manager
    print("\n3. Testing Dynamic Stop Manager...")
    dsm = DynamicStopManager(atr_period=14, atr_multiplier=2.0)

    # Mock Data
    dates = pd.date_range(start="2023-01-01", periods=20)
    prices = [100, 101, 102, 101, 103, 105, 104, 106, 108, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100]
    df = pd.DataFrame({"Close": prices, "High": [p + 1 for p in prices], "Low": [p - 1 for p in prices]}, index=dates)

    ticker = "TEST"
    entry_price = 100
    dsm.register_entry(ticker, entry_price)
    print(f"  Entry at {entry_price}, Initial Stop: {dsm.stops[ticker]:.2f}")

    # Simulate price movement
    for i in range(len(df)):
        price = df["Close"].iloc[i]
        # Use data up to current point for ATR
        current_df = df.iloc[: i + 1]

        new_stop = dsm.update_stop(ticker, price, current_df)
        is_hit = dsm.check_exit(ticker, price)

        if i % 5 == 0 or is_hit:
            print(f"  Day {i}: Price {price}, Stop {new_stop:.2f}, Hit? {is_hit}")

        if is_hit:
            print(f"  STOP HIT at {price} on Day {i}")
            break

    # 4. Integration Test (Simulation)
    print("\n4. Integration Test (Simulation)...")
    tickers = ["7203.T", "6758.T"]
    try:
        data_map = fetch_stock_data(tickers, period="1y")

        for ticker in tickers:
            if ticker not in data_map:
                continue

            df = data_map[ticker]
            print(f"\n  Simulating {ticker} ({len(df)} days)...")

            # Simple Strategy: Buy on Day 0, Hold with Trailing Stop
            dsm = DynamicStopManager(atr_period=14, atr_multiplier=2.0)
            entry_price = df["Close"].iloc[0]
            dsm.register_entry(ticker, entry_price)

            exit_price = df["Close"].iloc[-1]
            exit_date = df.index[-1]

            for i in range(1, len(df)):
                price = df["Close"].iloc[i]
                current_df = df.iloc[: i + 1]

                dsm.update_stop(ticker, price, current_df)
                if dsm.check_exit(ticker, price):
                    exit_price = dsm.stops[ticker]  # Executed at stop price (approx)
                    # In reality, executed at next open or close, but let's say stop price
                    # Or better, use current Low if Low < Stop
                    if df["Low"].iloc[i] < dsm.stops[ticker]:
                        exit_price = dsm.stops[ticker]
                    else:
                        exit_price = price

                    exit_date = df.index[i]
                    print(f"    Stopped out at {exit_price:.2f} on {exit_date.date()}")
                    break

            ret = (exit_price - entry_price) / entry_price
            bh_ret = (df["Close"].iloc[-1] - entry_price) / entry_price

            print(f"    Strategy Return: {ret*100:.2f}%")
            print(f"    Buy & Hold Return: {bh_ret*100:.2f}%")

            if ret > bh_ret:
                print("    ✅ Risk Management Improved Result")
            else:
                print("    ⚠️ Risk Management Lower Return (but maybe safer)")

    except Exception as e:
        print(f"Error in integration test: {e}")


if __name__ == "__main__":
    test_risk_management()
