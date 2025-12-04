import pandas as pd
import numpy as np
import datetime
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
import logging

logger = logging.getLogger(__name__)

class FuturePredictor:
    def __init__(self):
        self.lookback = 60
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        
    def predict_trajectory(self, df: pd.DataFrame, days_ahead: int = 5) -> dict:
        """
        指定された銘柄の向こう数日間の価格推移を予測する
        """
        try:
            if df is None or df.empty or len(df) < 100:
                return {"error": "データ不足"}

            # 1. Prepare Data
            data = df.copy()
            data['Volume'] = data['Volume'].replace(0, np.nan).ffill()
            data['Volatility'] = data['Close'].rolling(window=20).std() / data['Close']
            data.dropna(inplace=True)
            
            feature_cols = ['Close', 'Volume', 'Volatility']
            dataset = data[feature_cols].values
            
            # 2. Train Model (Simplified)
            scaled_data = self.scaler.fit_transform(dataset)
            
            X, y = [], []
            for i in range(self.lookback, len(scaled_data)):
                X.append(scaled_data[i-self.lookback:i])
                y.append(scaled_data[i, 0])
                
            X, y = np.array(X), np.array(y)
            
            if len(X) == 0:
                return {"error": "学習データ不足"}
            
            model = Sequential()
            model.add(LSTM(units=50, return_sequences=False, input_shape=(X.shape[1], X.shape[2])))
            model.add(Dropout(0.2))
            model.add(Dense(units=1))
            model.compile(optimizer=Adam(learning_rate=0.001), loss='mean_squared_error')
            
            # Train quietly
            model.fit(X, y, epochs=5, batch_size=32, verbose=0)
            
            # 3. Predict Future
            last_sequence = scaled_data[-lookback:]
            current_sequence = last_sequence.copy()
            future_predictions = []
            
            for _ in range(days_ahead):
                input_seq = np.expand_dims(current_sequence, axis=0)
                pred_scaled = model.predict(input_seq, verbose=0)[0][0]
                
                dummy = np.zeros((1, len(feature_cols)))
                dummy[0, 0] = pred_scaled
                dummy[0, 1] = dataset[-1, 1]
                dummy[0, 2] = dataset[-1, 2]
                
                pred_price = self.scaler.inverse_transform(dummy)[0, 0]
                future_predictions.append(pred_price)
                
                new_row = np.array([pred_scaled, current_sequence[-1, 1], current_sequence[-1, 2]])
                current_sequence = np.vstack([current_sequence[1:], new_row])
                
            # 4. Analyze Result
            current_price = df['Close'].iloc[-1]
            peak_price = max(future_predictions)
            peak_day_idx = future_predictions.index(peak_price)
            
            trend = "FLAT"
            if future_predictions[-1] > current_price * 1.01:
                trend = "UP"
            elif future_predictions[-1] < current_price * 0.99:
                trend = "DOWN"
                
            return {
                "current_price": current_price,
                "predictions": future_predictions,
                "peak_price": peak_price,
                "peak_day": peak_day_idx + 1,
                "trend": trend,
                "change_pct": (future_predictions[-1] - current_price) / current_price * 100
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {"error": str(e)}
