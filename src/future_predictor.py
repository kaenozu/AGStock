from datetime import timedelta
from typing import Dict, List, Optional, Tuple
import logging

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow import keras
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam

from src.base_predictor import BasePredictor
from src.features import add_technical_indicators

logger = logging.getLogger(__name__)


class FuturePredictor:
    def __init__(self):
        self.lookback = 60
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None
        self.params = self._load_optimized_params()

    def _load_optimized_params(self) -> Dict[str, Any]:
        """Load optimized parameters if they exist."""
        try:
            import os
            import json
            if os.path.exists("model_params.json"):
                with open("model_params.json", "r", encoding="utf-8") as f:
                    all_params = json.load(f)
                    return all_params.get("lstm", {})
        except Exception:
            pass
        return {}

    def prepare_model(self, X, y):
        """モデル準備"""
        pass

    def fit(self, X, y):
        """モデル学習"""
        # X: (samples, features) DataFrame
        # y: (samples,) Target values
        try:
            # Prepare data for LSTM (samples, lookback, features)
            data_np = X.values if hasattr(X, "values") else X
            target_np = y.values if hasattr(y, "values") else y
            
            # Simple scaling
            scaled_X = self.scaler.fit_transform(data_np)
            
            # Create sequences
            # Since X and y are aligned (X[t] -> y[t]), and we want to predict y[t] using X[t-lookback:t]
            # But EnhancedEnsemblePredictor passes shifted y?
            # y is shift(-1) of pct_change. So X[t] predicts y[t].
            # For LSTM, we usually use sequence.
            
            # X_seq, y_seq = [], []
            if len(scaled_X) <= self.lookback:
                 logger.warning("Not enough data for LSTM fit")
                 return

            for i in range(self.lookback, len(scaled_X)):
                X_seq.append(scaled_X[i-self.lookback:i])
                y_seq.append(target_np[i])
            
            X_seq, y_seq = np.array(X_seq), np.array(y_seq)
            
            if len(X_seq) == 0:
                 return

            self.model = Sequential()
            
            # Use optimized params
            hidden_dim = self.params.get("hidden_dim", 50)
            num_layers = self.params.get("num_layers", 1)
            dropout_rate = self.params.get("dropout", 0.2)
            lr = self.params.get("learning_rate", 0.001)

            for i in range(num_layers):
                is_last = (i == num_layers - 1)
                self.model.add(LSTM(units=hidden_dim, return_sequences=not is_last, input_shape=(X_seq.shape[1], X_seq.shape[2])))
                self.model.add(Dropout(dropout_rate))
            
            self.model.add(Dense(units=1))
            self.model.compile(optimizer=Adam(learning_rate=lr), loss="mean_squared_error")
            
            epochs = self.params.get("epochs", 5)
            batch_size = self.params.get("batch_size", 32)
            self.model.fit(X_seq, y_seq, epochs=epochs, batch_size=batch_size, verbose=0)
            
        except Exception as e:
            logger.error(f"FuturePredictor fit error: {e}")

    def predict(self, X):
        """予測実行"""
        if self.model is None:
            return np.zeros(len(X))
        
        try:
             data_np = X.values if hasattr(X, "values") else X
             scaled_X = self.scaler.transform(data_np)
             
             X_seq = []
             # For prediction, we need to handle sequences.
             # If X is provided for multiple points, we treat each as the end of a sequence?
             # This is tricky without history.
             # Assuming X contains history.
             if len(scaled_X) <= self.lookback:
                 return np.zeros(len(X))
                 
             for i in range(len(scaled_X)):
                 if i < self.lookback:
                     X_seq.append(np.zeros((self.lookback, scaled_X.shape[1]))) # Padding
                 else:
                     X_seq.append(scaled_X[i-self.lookback:i])
             
             X_seq = np.array(X_seq)
             pred = self.model.predict(X_seq, verbose=0)
             return pred.flatten()
             
        except Exception as e:
            logger.error(f"FuturePredictor predict error: {e}")
            return np.zeros(len(X))

    def predict_point(self, current_features):
        """単一点予測"""
        # 単一点といってもLSTMには履歴が必要
        # current_featuresだけで予測は不可能
        return 0.0

    def predict_trajectory(self, df: pd.DataFrame, days_ahead: int = 5) -> dict:
        """
        指定された銘柄の向こう数日間の価格推移を予測する
        """
        try:
            if df is None or df.empty or len(df) < 20:
                return {"error": f"データ不足 (データ数: {len(df) if df is not None else 0})"}

            # 1. Prepare Data
            data = df.copy()
            data["Volume"] = data["Volume"].replace(0, np.nan).ffill()

            # テクニカル指標を追加
            try:
                data = add_technical_indicators(data)
            except Exception as e:
                logger.warning(f"テクニカル指標追加エラー: {e}")
                # エラー時は最低限の指標で続行

            # データ数に応じてボラティリティ計算を調整
            vol_window = 20
            if len(data) < 40:
                vol_window = 5

            data["Volatility"] = data["Close"].rolling(window=vol_window).std() / data["Close"]

            # 欠損値処理（テクニカル指標計算でNaNが出るため）
            data.dropna(inplace=True)

            if len(data) < 5:
                return {"error": f"有効データ不足 (前処理後: {len(data)}件)"}

            # 使用する特徴量を定義
            # 存在しないカラムは除外
            potential_features = ["Close", "Volume", "Volatility", "RSI", "MACD", "BB_Mid"]
            feature_cols = [c for c in potential_features if c in data.columns]

            dataset = data[feature_cols].values

            # データ数に応じてLookbackを調整
            adjusted_lookback = min(self.lookback, len(dataset) // 2)
            if adjusted_lookback < 5:
                return {"error": "データが少なすぎて予測できません"}

            # 2. Train Model (Simplified)
            scaled_data = self.scaler.fit_transform(dataset)

            X, y = [], []
            for i in range(adjusted_lookback, len(scaled_data)):
                X.append(scaled_data[i - adjusted_lookback : i])
                y.append(scaled_data[i, 0])  # Target is Close price (index 0)

            X, y = np.array(X), np.array(y)

            if len(X) == 0:
                return {"error": "学習データ不足 (Lookback期間不足)"}

            model = Sequential()
            model.add(LSTM(units=50, return_sequences=False, input_shape=(X.shape[1], X.shape[2])))
            model.add(Dropout(0.2))
            model.add(Dense(units=1))
            model.compile(optimizer=Adam(learning_rate=0.001), loss="mean_squared_error")

            # Train quietly
            model.fit(X, y, epochs=10, batch_size=32, verbose=0)  # Epochs increased to 10

            # 3. Predict Future
            last_sequence = scaled_data[-adjusted_lookback:]
            current_sequence = last_sequence.copy()
            future_predictions = []

            for _ in range(days_ahead):
                input_seq = np.expand_dims(current_sequence, axis=0)
                pred_scaled = model.predict(input_seq, verbose=0)[0][0]

                # ダミー配列を作成して逆変換
                dummy = np.zeros((1, len(feature_cols)))
                dummy[0, 0] = pred_scaled
                # 他の特徴量は直近の値を維持（簡易的な未来予測）
                for i in range(1, len(feature_cols)):
                    dummy[0, i] = dataset[-1, i]

                pred_price = self.scaler.inverse_transform(dummy)[0, 0]
                future_predictions.append(pred_price)

                # 次のステップのためのシーケンス更新
                # Closeは予測値、他は直近値を維持
                new_row = np.zeros(len(feature_cols))
                new_row[0] = pred_scaled
                for i in range(1, len(feature_cols)):
                    new_row[i] = current_sequence[-1, i]

                current_sequence = np.vstack([current_sequence[1:], new_row])

            # 4. Analyze Result
            current_price = df["Close"].iloc[-1]
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
                "change_pct": (future_predictions[-1] - current_price) / current_price * 100,
            }

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {"error": str(e)}
