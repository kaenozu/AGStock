"""
Prophet予測モデル
Facebook開発の時系列予測モデル
トレンドと季節性を自動的に分離
"""

import logging

import numpy as np
import pandas as pd
from prophet import Prophet

logger = logging.getLogger(__name__)


class ProphetPredictor:
    def __init__(self):
        self.model = None

    def predict_trajectory(self, df: pd.DataFrame, days_ahead: int = 5) -> dict:
        """
        Prophetで価格推移を予測
        """
        try:
            if df is None or df.empty or len(df) < 30:
                return {"error": f"データ不足 (データ数: {len(df) if df is not None else 0})"}

            # 1. Prophet用にデータを整形
            # Prophet requires 'ds' (datetime) and 'y' (value) columns
            prophet_df = pd.DataFrame({"ds": df.index, "y": df["Close"].values})

            # 2. モデルの学習
            # ログ出力を抑制
            self.model = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False)

            # Prophet内部のログを抑制
            import io
            import sys

            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            try:
                self.model.fit(prophet_df)
            finally:
                sys.stdout = old_stdout

            # 3. 未来予測
            future = self.model.make_future_dataframe(periods=days_ahead)
            forecast = self.model.predict(future)

            # 直近days_ahead件の予測を取得
            predictions = forecast["yhat"].tail(days_ahead).tolist()

            # 4. 結果の整形
            current_price = df["Close"].iloc[-1]
            peak_price = max(predictions)
            peak_day_idx = predictions.index(peak_price)

            trend = "FLAT"
            if predictions[-1] > current_price * 1.01:
                trend = "UP"
            elif predictions[-1] < current_price * 0.99:
                trend = "DOWN"

            return {
                "current_price": current_price,
                "predictions": predictions,
                "peak_price": peak_price,
                "peak_day": peak_day_idx + 1,
                "trend": trend,
                "change_pct": (predictions[-1] - current_price) / current_price * 100,
            }

        except Exception as e:
            logger.error(f"Prophet prediction error: {e}")
            return {"error": str(e)}
