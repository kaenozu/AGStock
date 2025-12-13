import os
import sys

import numpy as np
import pandas as pd

# Add project root to path
sys.path.append(os.getcwd())

from src.data_loader import (fetch_macro_data, fetch_stock_data,
                             get_latest_price)
from src.features import add_advanced_features, add_macro_features
from src.strategies import LightGBMStrategy, MLStrategy


def check_predictions_detailed():
    tickers = ["8308.T", "7186.T", "9432.T", "AMZN", "NVDA"]

    print(f"Fetching data for {tickers}...")
    data_map = fetch_stock_data(tickers, period="2y")
    macro_data = fetch_macro_data(period="5y")

    lgbm = LightGBMStrategy(lookback_days=365, threshold=0.005)
    ml = MLStrategy()

    print("\n--- Detailed Prediction Analysis ---")

    for ticker in tickers:
        df = data_map.get(ticker)
        if df is None or df.empty:
            print(f"{ticker}: No data found")
            continue

        latest_price = get_latest_price(df)
        print(f"\n[{ticker}] Price: {latest_price:,.2f}")

        # --- LightGBM Analysis ---
        try:
            # Run generate_signals to train the model
            _ = lgbm.generate_signals(df)

            # Prepare latest features
            df_feat = df.copy()
            if df_feat.index.tz is not None:
                df_feat.index = df_feat.index.tz_localize(None)

            df_feat = add_advanced_features(df_feat)
            df_feat = add_macro_features(df_feat, macro_data)

            latest_features = df_feat[lgbm.feature_cols].iloc[[-1]]

            if lgbm.model:
                prob = lgbm.model.predict(latest_features)[0]
                trend = "UP" if prob > 0.5 else "DOWN"
                strength = abs(prob - 0.5) * 200  # 0-100 scale roughly

                print(f"  LightGBM Probability: {prob:.2%} ({trend})")
                if 0.45 <= prob <= 0.55:
                    print(f"    -> Signal is NEUTRAL (Thresholds: <45% SELL, >55% BUY)")
                    print(f"    -> Interpretation: Weak {trend} trend, holding pattern.")
                else:
                    print(f"    -> Signal is {trend} (Strong)")
            else:
                print("  LightGBM: Model not trained (insufficient data?)")

        except Exception as e:
            print(f"  LightGBM Error: {e}")

        # --- ML (Random Forest) Analysis ---
        try:
            # Run generate_signals to train the model
            _ = ml.generate_signals(df)

            # Re-create features locally to predict_proba
            data = df.copy()
            import ta

            data["RSI"] = ta.momentum.RSIIndicator(close=data["Close"], window=14).rsi()
            data["SMA_20"] = data["Close"].rolling(window=20).mean()
            data["SMA_50"] = data["Close"].rolling(window=50).mean()
            data["SMA_Ratio"] = data["SMA_20"] / data["SMA_50"]
            data["Volatility"] = data["Close"].rolling(window=20).std() / data["Close"]
            data["Ret_1"] = data["Close"].pct_change(1)
            data["Ret_5"] = data["Close"].pct_change(5)
            data.dropna(inplace=True)

            if not data.empty:
                features = ["RSI", "SMA_Ratio", "Volatility", "Ret_1", "Ret_5"]
                X_latest = data[features].iloc[[-1]]

                if hasattr(ml.model, "predict_proba"):
                    probs = ml.model.predict_proba(X_latest)[0]
                    # Class 0: Down/Flat, Class 1: Up (Target was shift(-1) > current)
                    up_prob = probs[1]

                    print(f"  RF Model Probability: {up_prob:.2%} (UP)")
                    if up_prob > 0.5:
                        print(f"    -> Prediction: UP")
                    else:
                        print(f"    -> Prediction: DOWN")
                else:
                    pred = ml.model.predict(X_latest)[0]
                    print(f"  RF Model Prediction: {'UP' if pred==1 else 'DOWN'}")
            else:
                print("  RF Model: Insufficient data for features")

        except Exception as e:
            print(f"  RF Model Error: {e}")


if __name__ == "__main__":
    check_predictions_detailed()
