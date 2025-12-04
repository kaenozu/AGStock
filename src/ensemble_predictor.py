"""
アンサンブル予測モジュール
複数のモデル（LSTM, SMA等）の予測を組み合わせて、より堅牢な予測を提供します。
"""
import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from src.future_predictor import FuturePredictor

logger = logging.getLogger(__name__)

class EnsemblePredictor:
    def __init__(self):
        self.lstm_predictor = FuturePredictor()
        self.weights = {
            'lstm': 0.7,
            'sma': 0.3
        }
        
    def predict_trajectory(self, df: pd.DataFrame, days_ahead: int = 5) -> Dict:
        """
        アンサンブル予測を実行
        """
        try:
            # 1. LSTM予測
            lstm_result = self.lstm_predictor.predict_trajectory(df, days_ahead)
            
            if "error" in lstm_result:
                logger.warning(f"LSTM prediction failed: {lstm_result['error']}")
                # LSTM失敗時はSMAのみで予測（フォールバック）
                return self._predict_sma(df, days_ahead)
            
            lstm_preds = np.array(lstm_result['predictions'])
            
            # 2. SMA予測（単純移動平均の延長）
            # 直近5日間の平均変化率を使って将来を予測
            sma_result = self._predict_sma(df, days_ahead)
            sma_preds = np.array(sma_result['predictions'])
            
            # 3. アンサンブル（加重平均）
            final_preds = (lstm_preds * self.weights['lstm']) + (sma_preds * self.weights['sma'])
            
            # 結果の整形
            current_price = df['Close'].iloc[-1]
            peak_price = max(final_preds)
            peak_day_idx = list(final_preds).index(peak_price)
            
            trend = "FLAT"
            if final_preds[-1] > current_price * 1.01:
                trend = "UP"
            elif final_preds[-1] < current_price * 0.99:
                trend = "DOWN"
                
            return {
                "current_price": current_price,
                "predictions": final_preds.tolist(),
                "peak_price": peak_price,
                "peak_day": peak_day_idx + 1,
                "trend": trend,
                "change_pct": (final_preds[-1] - current_price) / current_price * 100,
                "details": {
                    "lstm_trend": lstm_result['trend'],
                    "sma_trend": sma_result['trend']
                }
            }
            
        except Exception as e:
            logger.error(f"Ensemble prediction error: {e}")
            return {"error": str(e)}
    
    def _predict_sma(self, df: pd.DataFrame, days_ahead: int) -> Dict:
        """
        単純移動平均に基づく予測（ベースライン）
        直近のモメンタムを単純に延長する
        """
        current_price = df['Close'].iloc[-1]
        
        # 直近5日間の平均変化率
        recent_returns = df['Close'].pct_change().tail(5).mean()
        
        # 変化率が極端にならないようにクリップ (-3% ~ +3%)
        recent_returns = np.clip(recent_returns, -0.03, 0.03)
        
        predictions = []
        price = current_price
        
        for _ in range(days_ahead):
            price = price * (1 + recent_returns)
            predictions.append(price)
            
        trend = "FLAT"
        if predictions[-1] > current_price * 1.01:
            trend = "UP"
        elif predictions[-1] < current_price * 0.99:
            trend = "DOWN"
            
        return {
            "current_price": current_price,
            "predictions": predictions,
            "peak_price": max(predictions),
            "trend": trend,
            "change_pct": (predictions[-1] - current_price) / current_price * 100
        }
