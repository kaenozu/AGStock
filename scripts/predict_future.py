import datetime
import os
import sys

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam

# Add project root to path
sys.path.append(os.getcwd())
sys.stdout.reconfigure(encoding="utf-8")

from src.data_loader import fetch_stock_data


def predict_future_trajectory(ticker, days_ahead=5):
    print(f"\nAnalyzing {ticker} for next {days_ahead} days...")

    # 1. Fetch Data
    data_map = fetch_stock_data([ticker], period="2y")
    df = data_map.get(ticker)

    if df is None or df.empty:
        print("No data found.")
        return

    # 2. Prepare Data
    data = df.copy()
    data["Volume"] = data["Volume"].replace(0, np.nan).ffill()
    data["Volatility"] = data["Close"].rolling(window=20).std() / data["Close"]
    data.dropna(inplace=True)

    feature_cols = ["Close", "Volume", "Volatility"]
    dataset = data[feature_cols].values

    # 3. Train Model (Simplified for speed)
    lookback = 60
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(dataset)

    X, y = [], []
    for i in range(lookback, len(scaled_data)):
        X.append(scaled_data[i - lookback : i])
        y.append(scaled_data[i, 0])  # Predict Close

    X, y = np.array(X), np.array(y)

    model = Sequential()
    model.add(LSTM(units=50, return_sequences=False, input_shape=(X.shape[1], X.shape[2])))
    model.add(Dropout(0.2))
    model.add(Dense(units=1))
    model.compile(optimizer=Adam(learning_rate=0.001), loss="mean_squared_error")

    print("Training AI model...")
    model.fit(X, y, epochs=10, batch_size=32, verbose=0)

    # 4. Predict Future (Recursive)
    last_sequence = scaled_data[-lookback:]
    current_sequence = last_sequence.copy()

    future_predictions = []

    print("Simulating future prices...")
    for _ in range(days_ahead):
        # Predict next step
        input_seq = np.expand_dims(current_sequence, axis=0)
        pred_scaled = model.predict(input_seq, verbose=0)[0][0]

        # Inverse transform to get price
        dummy = np.zeros((1, len(feature_cols)))
        dummy[0, 0] = pred_scaled
        # Use last known volume/volatility for dummy inverse (approx)
        dummy[0, 1] = dataset[-1, 1]
        dummy[0, 2] = dataset[-1, 2]

        pred_price = scaler.inverse_transform(dummy)[0, 0]
        future_predictions.append(pred_price)

        # Update sequence for next step
        # Create new row with predicted price and last known other features (simplified)
        new_row = np.array([pred_scaled, current_sequence[-1, 1], current_sequence[-1, 2]])
        current_sequence = np.vstack([current_sequence[1:], new_row])

    # 5. Output Results
    current_price = df["Close"].iloc[-1]
    print(f"Current Price: {current_price:,.2f}")

    peak_price = -1
    peak_day = -1

    start_date = df.index[-1]

    for i, price in enumerate(future_predictions):
        date = start_date + datetime.timedelta(days=i + 1)
        # Skip weekends
        while date.weekday() >= 5:
            date += datetime.timedelta(days=1)

        change = (price - current_price) / current_price * 100
        trend = "UP" if price > current_price else "DOWN"

        print(f"  Day {i+1} ({date.strftime('%m/%d')}): {price:,.2f} ({change:+.2f}%) {trend}")

        if price > peak_price:
            peak_price = price
            peak_day = i + 1
            peak_date = date

    if peak_price > current_price:
        print(f"\n📈 Expected Peak: Day {peak_day} ({peak_date.strftime('%m/%d')}) @ {peak_price:,.2f}")
    else:
        print(f"\n📉 Trend is Down. No peak expected in next {days_ahead} days.")


if __name__ == "__main__":
    # Check for held stocks
    tickers = ["8308.T", "NVDA", "AMZN", "9432.T"]  # Example held stocks
    for t in tickers:
        try:
            predict_future_trajectory(t)
        except Exception as e:
            print(f"Error predicting {t}: {e}")
