from typing import Dict

import pandas as pd
import ta

from .base import Strategy


class MLStrategy(Strategy):
    def __init__(self, name: str = "AI Random Forest", trend_period: int = 0) -> None:
        super().__init__(name, trend_period)
        from sklearn.ensemble import RandomForestClassifier

        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.feature_names = ["RSI", "SMA_Ratio", "Volatility", "Ret_1", "Ret_5"]

    def explain_prediction(self, df: pd.DataFrame) -> Dict[str, float]:
        """Return feature importance for the latest prediction"""
        if self.model is None:
            return {}
        try:
            importances = self.model.feature_importances_
            return dict(zip(self.feature_names, importances))
        except Exception:
            return {}

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or "Close" not in df.columns:
            return pd.Series(dtype=int)

        data = df.copy()

        # 1. Technical Indicators
        data["RSI"] = ta.momentum.RSIIndicator(close=data["Close"], window=14).rsi()
        data["SMA_20"] = data["Close"].rolling(window=20).mean()
        data["SMA_50"] = data["Close"].rolling(window=50).mean()
        data["SMA_Ratio"] = data["SMA_20"] / data["SMA_50"]

        # 2. Volatility
        data["Volatility"] = data["Close"].rolling(window=20).std() / data["Close"]

        # 4. Returns Lag
        data["Ret_1"] = data["Close"].pct_change(1)
        data["Ret_5"] = data["Close"].pct_change(5)

        # Drop NaNs created by indicators
        data.dropna(inplace=True)

        if len(data) < 50:
            return pd.Series(0, index=df.index)

        # --- Target Creation ---
        # Target: 1 if Next Day Return > 0, else 0
        data["Target"] = (data["Close"].shift(-1) > data["Close"]).astype(int)

        # Drop last row (NaN target)
        valid_data = data.iloc[:-1].copy()

        features = self.feature_names
        X = valid_data[features]
        y = valid_data["Target"]

        # --- Train/Test Split ---
        split_idx = int(len(X) * 0.7)

        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        if len(X_train) < 10:
            return pd.Series(0, index=df.index)

        self.model.fit(X_train, y_train)

        # Predict
        predictions = self.model.predict(X_test)

        signals = pd.Series(0, index=df.index)
        test_indices = X_test.index
        pred_series = pd.Series(predictions, index=test_indices)
        signals.loc[test_indices] = pred_series.apply(lambda x: 1 if x == 1 else -1)

        return signals

    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return (
                "AI（ランダムフォレスト）が過去のパターンから「上昇」を予測しました。"
            )
        elif signal == -1:
            return (
                "AI（ランダムフォレスト）が過去のパターンから「下落」を予測しました。"
            )
        return "AIによる明確な予測は出ていません。"
