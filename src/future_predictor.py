import pandas as pd
import numpy as np
import datetime
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
import logging
from src.features import add_technical_indicators

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
            if df is None or df.empty or len(df) < 20:
                return {"error": f"データ不足 (データ数: {len(df) if df is not None else 0})"}

            # 1. Prepare Data
            data = df.copy()
            data['Volume'] = data['Volume'].replace(0, np.nan).ffill()
            
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
            
            data['Volatility'] = data['Close'].rolling(window=vol_window).std() / data['Close']
            
            # 欠損値処理（テクニカル指標計算でNaNが出るため）
            data.dropna(inplace=True)
            
            if len(data) < 5:
                 return {"error": f"有効データ不足 (前処理後: {len(data)}件)"}

            # 使用する特徴量を定義
            # 存在しないカラムは除外
            potential_features = ['Close', 'Volume', 'Volatility', 'RSI', 'MACD', 'BB_Mid']
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
                X.append(scaled_data[i-adjusted_lookback:i])
                y.append(scaled_data[i, 0]) # Target is Close price (index 0)
                
            X, y = np.array(X), np.array(y)
            
            if len(X) == 0:
                return {"error": "学習データ不足 (Lookback期間不足)"}
            
            model = Sequential()
            model.add(LSTM(units=50, return_sequences=False, input_shape=(X.shape[1], X.shape[2])))
            model.add(Dropout(0.2))
            model.add(Dense(units=1))
            model.compile(optimizer=Adam(learning_rate=0.001), loss='mean_squared_error')
            
            # Train quietly
            model.fit(X, y, epochs=10, batch_size=32, verbose=0) # Epochs increased to 10
            
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
