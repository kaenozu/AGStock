from src.multi_timeframe import MultiTimeframeAnalyzer
from src.dynamic_ensemble import DynamicEnsemble
import importlib
import inspect
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import ta
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam

# Phase 29: 高度な特徴量のインポート
try:
    from src.features import add_advanced_features, add_macro_features
except ImportError:
    # フォールバック: 関数が存在しない場合は何もしない
    def add_advanced_features(df):
        return df

    def add_macro_features(df, macro_data):
        return df


try:
    from src.data_loader import fetch_macro_data
except ImportError:

    def fetch_macro_data(period="5y"):
        return {}


logger = logging.getLogger(__name__)


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


@dataclass
class Order:
    ticker: str
    type: OrderType
    action: str  # 'BUY' or 'SELL'
    quantity: float
    price: Optional[float] = None  # Limit or Stop price
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop_pct: Optional[float] = None  # For trailing stop logic
    expiry: str = "GTC"  # Good Till Cancelled or DAY


class Strategy:
    def __init__(self, name: str, trend_period: int = 200) -> None:
        self.name = name
        self.trend_period = trend_period

    def apply_trend_filter(self, df: pd.DataFrame, signals: pd.Series) -> pd.Series:
        if self.trend_period <= 0:
            return signals

        trend_sma = df["Close"].rolling(window=self.trend_period).mean()

        filtered_signals = signals.copy()

        # Filter Longs: Can only Buy if Close > SMA(200)
        long_condition = df["Close"] > trend_sma
        filtered_signals.loc[(signals == 1) & (~long_condition)] = 0

        # Filter Shorts: Can only Short if Close < SMA(200)
        short_condition = df["Close"] < trend_sma
        filtered_signals.loc[(signals == -1) & (~short_condition)] = 0

        return filtered_signals

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Standard interface for strategies to return signal and confidence.
        Default implementation wraps generate_signals.
        """
        signals = self.generate_signals(df)
        if signals.empty:
            return {"signal": 0, "confidence": 0.0}

        # Get the latest signal (for the last available date)
        last_signal = signals.iloc[-1]

        return {
            "signal": int(last_signal),
            "confidence": 1.0 if last_signal != 0 else 0.0,
        }

    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return "買いシグナル"
        elif signal == -1:
            return "売りシグナル"
        return "様子見"


class SMACrossoverStrategy(Strategy):
    def __init__(
        self, short_window: int = 5, long_window: int = 25, trend_period: int = 200
    ) -> None:
        super().__init__(f"SMA Crossover ({short_window}/{long_window})", trend_period)
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or "Close" not in df.columns:
            return pd.Series(dtype=int)

        signals = pd.Series(0, index=df.index)

        short_sma = df["Close"].rolling(window=self.short_window).mean()
        long_sma = df["Close"].rolling(window=self.long_window).mean()

        # Golden Cross
        signals.loc[
            (short_sma > long_sma) & (short_sma.shift(1) <= long_sma.shift(1))
        ] = 1
        # Dead Cross
        signals.loc[
            (short_sma < long_sma) & (short_sma.shift(1) >= long_sma.shift(1))
        ] = -1

        return self.apply_trend_filter(df, signals)

    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return "短期移動平均線が長期移動平均線を上抜けました（ゴールデンクロス）。上昇トレンドの始まりを示唆しています。"
        elif signal == -1:
            return "短期移動平均線が長期移動平均線を下抜けました（デッドクロス）。下落トレンドの始まりを示唆しています。"
        return "明確なトレンド転換シグナルは出ていません。"


class RSIStrategy(Strategy):
    def __init__(
        self,
        period: int = 14,
        lower: float = 30,
        upper: float = 70,
        trend_period: int = 200,
    ) -> None:
        super().__init__(f"RSI ({period}) Reversal", trend_period)
        self.period = period
        self.lower = lower
        self.upper = upper

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or "Close" not in df.columns:
            return pd.Series(dtype=int)

        rsi_indicator = ta.momentum.RSIIndicator(close=df["Close"], window=self.period)
        rsi = rsi_indicator.rsi()
        signals = pd.Series(0, index=df.index)

        if rsi is None or rsi.isna().all():
            return signals

        prev_rsi = rsi.shift(1)

        # Buy: Cross above lower
        signals.loc[(prev_rsi < self.lower) & (rsi >= self.lower)] = 1
        # Sell: Cross below upper
        signals.loc[(prev_rsi > self.upper) & (rsi <= self.upper)] = -1

        return self.apply_trend_filter(df, signals)

    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return f"RSIが{self.lower}を下回った後、回復しました。売られすぎからの反発を示唆しています。"
        elif signal == -1:
            return f"RSIが{self.upper}を上回った後、下落しました。買われすぎからの反落を示唆しています。"
        return "RSIは中立圏内で推移しています。"


class BollingerBandsStrategy(Strategy):
    def __init__(
        self, length: int = 20, std: float = 2, trend_period: int = 200
    ) -> None:
        super().__init__(f"Bollinger Bands ({length}, {std})", trend_period)
        self.length = length
        self.std = std

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or "Close" not in df.columns:
            return pd.Series(dtype=int)

        bollinger = ta.volatility.BollingerBands(
            close=df["Close"], window=self.length, window_dev=self.std
        )
        lower_band = bollinger.bollinger_lband()
        upper_band = bollinger.bollinger_hband()

        signals = pd.Series(0, index=df.index)

        # Buy: Touch Lower
        signals.loc[df["Close"] < lower_band] = 1
        # Sell: Touch Upper
        signals.loc[df["Close"] > upper_band] = -1

        return self.apply_trend_filter(df, signals)

    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return "株価がボリンジャーバンドの下限にタッチしました。売られすぎからの反発が期待できます。"
        elif signal == -1:
            return "株価がボリンジャーバンドの上限にタッチしました。過熱感があり、反落の可能性があります。"
        return "バンド内での推移が続いています。"


class CombinedStrategy(Strategy):
    def __init__(
        self,
        rsi_period: int = 14,
        bb_length: int = 20,
        bb_std: float = 2,
        trend_period: int = 200,
    ) -> None:
        super().__init__("Combined (RSI + BB)", trend_period)
        self.rsi_period = rsi_period
        self.bb_length = bb_length
        self.bb_std = bb_std

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or "Close" not in df.columns:
            return pd.Series(dtype=int)

        # RSI
        rsi = ta.momentum.RSIIndicator(close=df["Close"], window=self.rsi_period).rsi()

        # BB
        bb = ta.volatility.BollingerBands(
            close=df["Close"], window=self.bb_length, window_dev=self.bb_std
        )
        lower_band = bb.bollinger_lband()
        upper_band = bb.bollinger_hband()

        signals = pd.Series(0, index=df.index)

        # Buy: RSI < 30 AND Close < Lower Band
        signals.loc[(rsi < 30) & (df["Close"] < lower_band)] = 1

        # Sell: RSI > 70 AND Close > Upper Band
        signals.loc[(rsi > 70) & (df["Close"] > upper_band)] = -1

        return self.apply_trend_filter(df, signals)

    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return "RSIとボリンジャーバンドの両方が「売られすぎ」を示しています。強い反発のチャンスです。"
        elif signal == -1:
            return "RSIとボリンジャーバンドの両方が「買われすぎ」を示しています。強い反落の警戒が必要です。"
        return "複数の指標による強いシグナルは出ていません。"


class MLStrategy(Strategy):
    def __init__(self, name: str = "AI Random Forest", trend_period: int = 0) -> None:
        super().__init__(name, trend_period)
        from sklearn.ensemble import RandomForestClassifier

        self.model = RandomForestClassifier(n_estimators=100, random_state=42)

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

        features = ["RSI", "SMA_Ratio", "Volatility", "Ret_1", "Ret_5"]
        X = valid_data[features]
        y = valid_data["Target"]

        # --- Train/Test Split ---
        split_idx = int(len(X) * 0.7)

        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, _y_test = y.iloc[:split_idx], y.iloc[split_idx:]

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


class LightGBMStrategy(Strategy):
    def __init__(self, lookback_days=365, threshold=0.005):
        super().__init__("LightGBM Alpha")
        self.lookback_days = lookback_days
        self.threshold = threshold
        self.model = None
        self.feature_cols = [
            "ATR",
            "BB_Width",
            "RSI",
            "MACD",
            "MACD_Signal",
            "MACD_Diff",
            "Dist_SMA_20",
            "Dist_SMA_50",
            "Dist_SMA_200",
            "OBV",
            "Volume_Change",
            "USDJPY_Ret",
            "USDJPY_Corr",
            "SP500_Ret",
            "SP500_Corr",
            "US10Y_Ret",
            "US10Y_Corr",
        ]

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        import lightgbm as lgb

        # タイムゾーンの不一致を防ぐためにインデックスをtimezone-naiveにする
        if df.index.tz is not None:
            df = df.copy()
            df.index = df.index.tz_localize(None)

        data = add_advanced_features(df)
        macro_data = fetch_macro_data(period="5y")
        data = add_macro_features(data, macro_data)

        min_required = self.lookback_days + 50
        if len(data) < min_required:
            return pd.Series(0, index=df.index)

        signals = pd.Series(0, index=df.index)
        retrain_period = 60
        start_idx = self.lookback_days
        end_idx = len(data)
        current_idx = start_idx

        while current_idx < end_idx:
            train_end = current_idx
            train_start = max(0, train_end - 1000)
            train_df = data.iloc[train_start:train_end].dropna()

            pred_end = min(current_idx + retrain_period, end_idx)
            test_df = data.iloc[current_idx:pred_end].dropna()

            if train_df.empty or test_df.empty:
                current_idx += retrain_period
                continue

            X_train = train_df[self.feature_cols]
            y_train = (train_df["Return_1d"] > 0).astype(int)

            params = {
                "objective": "binary",
                "metric": "binary_logloss",
                "verbosity": -1,
                "seed": 42,
            }
            train_data = lgb.Dataset(X_train, label=y_train)
            self.model = lgb.train(params, train_data, num_boost_round=100)

            X_test = test_df[self.feature_cols]
            if not X_test.empty:
                preds = self.model.predict(X_test)
                chunk_signals = pd.Series(0, index=X_test.index)
                # Tighter thresholds for higher confidence signals
                chunk_signals[preds > 0.60] = 1  # Changed from 0.55
                chunk_signals[preds < 0.40] = -1  # Changed from 0.45
                signals.loc[chunk_signals.index] = chunk_signals

            current_idx += retrain_period

        return signals

    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return "LightGBMモデルがマクロ経済指標やテクニカル指標を分析し、上昇確率が高いと判断しました。"
        elif signal == -1:
            return "LightGBMモデルがマクロ経済指標やテクニカル指標を分析し、下落リスクが高いと判断しました。"
        return "AIによる強い確信度は得られていません。"


class DeepLearningStrategy(Strategy):
    def __init__(
        self,
        lookback=60,
        epochs=5,
        batch_size=32,
        trend_period=200,
        train_window_days=365,
        predict_window_days=20,
    ):
        super().__init__("Deep Learning (LSTM)", trend_period)
        from sklearn.preprocessing import MinMaxScaler

        self.lookback = lookback
        self.epochs = epochs
        self.batch_size = batch_size
        self.train_window_days = train_window_days
        self.predict_window_days = predict_window_days
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def _create_sequences(self, data):
        X, y = [], []
        for i in range(self.lookback, len(data)):
            X.append(data[i - self.lookback: i])
            y.append(data[i, 0])
        return np.array(X), np.array(y)

    def build_model(self, input_shape):
        model = Sequential()
        model.add(LSTM(units=50, return_sequences=False, input_shape=input_shape))
        model.add(Dropout(0.2))
        model.add(Dense(units=1))
        model.compile(optimizer=Adam(learning_rate=0.001), loss="mean_squared_error")
        return model

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or "Close" not in df.columns:
            return pd.Series(dtype=int)

        data = df.copy()
        data["Volume"] = data["Volume"].replace(0, np.nan).ffill()
        data["Volatility"] = data["Close"].rolling(window=20).std() / data["Close"]
        data.dropna(inplace=True)

        if len(data) < self.train_window_days + self.lookback:
            return pd.Series(0, index=df.index)

        feature_cols = ["Close", "Volume", "Volatility"]
        dataset = data[feature_cols].values
        signals = pd.Series(0, index=df.index)

        start_index = self.train_window_days
        end_index = len(dataset)
        step = self.predict_window_days

        print(
            f"Starting Walk-Forward Validation for DL Strategy... (Total steps: {(end_index - start_index) // step})"
        )

        for current_idx in range(start_index, end_index, step):
            train_start = max(0, current_idx - self.train_window_days)
            train_end = current_idx
            predict_end = min(current_idx + step, end_index)

            if train_end >= predict_end:
                break

            train_data = dataset[train_start:train_end]
            local_scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_train = local_scaler.fit_transform(train_data)

            X_train, y_train = self._create_sequences(scaled_train)

            if len(X_train) == 0:
                continue

            model = self.build_model((X_train.shape[1], X_train.shape[2]))
            model.fit(
                X_train,
                y_train,
                batch_size=self.batch_size,
                epochs=self.epochs,
                verbose=0,
            )

            pred_data_start = current_idx - self.lookback
            pred_data_raw = dataset[pred_data_start:predict_end]
            scaled_pred_input = local_scaler.transform(pred_data_raw)
            X_pred, _ = self._create_sequences(scaled_pred_input)

            if len(X_pred) == 0:
                continue

            predictions_scaled = model.predict(X_pred, verbose=0)
            dummy_pred = np.zeros((len(predictions_scaled), len(feature_cols)))
            dummy_pred[:, 0] = predictions_scaled.flatten()
            predictions = local_scaler.inverse_transform(dummy_pred)[:, 0]

            threshold = 0.005

            for i in range(len(predictions)):
                target_df_idx = current_idx + i
                if target_df_idx >= len(data):
                    break
                decision_idx = target_df_idx - 1
                if decision_idx < 0:
                    continue

                current_price = data["Close"].iloc[decision_idx]
                predicted_price = predictions[i]

                if predicted_price > current_price * (1 + threshold):
                    signals.iloc[data.index.get_loc(data.index[decision_idx])] = 1
                elif predicted_price < current_price * (1 - threshold):
                    signals.iloc[data.index.get_loc(data.index[decision_idx])] = -1

        return self.apply_trend_filter(df, signals)

    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return "ディープラーニング（LSTM）が過去の価格・出来高・変動率から、短期的な上昇トレンドを予測しました。"
        elif signal == -1:
            return "ディープラーニング（LSTM）が過去の価格・出来高・変動率から、短期的な下落トレンドを予測しました。"
        return "予測価格は現在の価格と大きな差がありません。"


class DividendStrategy(Strategy):
    def __init__(
        self,
        min_yield: float = 0.035,
        max_payout: float = 0.80,
        trend_period: int = 200,
    ) -> None:
        super().__init__("High Dividend Accumulation", trend_period)
        self.min_yield = min_yield
        self.max_payout = max_payout

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or "Close" not in df.columns:
            return pd.Series(dtype=int)
        signals = pd.Series(1, index=df.index)
        return self.apply_trend_filter(df, signals)

    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return (
                "高配当かつ財務健全性が確認されました。長期保有・積立に適しています。"
            )
        return "条件を満たしていません。"


class EnsembleStrategy(Strategy):
    def __init__(self, enable_regime_detection: bool = True):
        super().__init__("Ensemble Strategy")
        from src.data_loader import fetch_macro_data
        from src.ensemble import EnsembleVoter
        from src.regime import RegimeDetector

        self.strategies = [
            DeepLearningStrategy(),
            LightGBMStrategy(),
            CombinedStrategy(),
        ]

        # デフォルトウェイト
        self.base_weights = {
            "Deep Learning (LSTM)": 1.5,
            "LightGBM Alpha": 1.2,
            "Combined (RSI + BB)": 1.0,
        }

        self.weights = self.base_weights.copy()

        self.voter = EnsembleVoter(self.strategies, self.weights)

        # レジーム検知
        self.enable_regime_detection = enable_regime_detection
        self.regime_detector = None
        self.current_regime = None

        if self.enable_regime_detection:
            try:
                # マクロデータを取得してRegimeDetectorを訓練
                macro_data = fetch_macro_data(period="5y")
                if macro_data:
                    self.regime_detector = RegimeDetector(n_regimes=3)
                    self.regime_detector.fit(macro_data)
                    logger.info("RegimeDetector initialized and fitted.")
                else:
                    logger.warning(
                        "Failed to fetch macro data. Regime detection disabled."
                    )
                    self.enable_regime_detection = False
            except Exception as e:
                logger.error(f"Error initializing RegimeDetector: {e}")
                self.enable_regime_detection = False

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate ensemble signals by combining multiple strategies with weighted voting.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Series of signals: 1 for BUY, -1 for SELL, 0 for HOLD
        """
        # 0. Regime Detection & Weight Adjustment
        if self.enable_regime_detection and self.regime_detector:
            try:
                from src.data_loader import fetch_macro_data

                macro_data = fetch_macro_data(period="1y")
                (
                    regime_id,
                    regime_label,
                    features,
                ) = self.regime_detector.predict_current_regime(macro_data)
                self.current_regime = {
                    "id": regime_id,
                    "label": regime_label,
                    "features": features,
                }

                # レジームに基づいてウェイトを調整
                if regime_id == 2:  # 暴落警戒 (Risk-Off)
                    # 全体的にポジションサイズを縮小
                    self.weights = {k: v * 0.5 for k, v in self.base_weights.items()}
                    logger.info(
                        f"Regime: {regime_label} - Reducing position sizes to 50%"
                    )
                elif regime_id == 1:  # 不安定 (Volatile)
                    # 中程度に縮小
                    self.weights = {k: v * 0.75 for k, v in self.base_weights.items()}
                    logger.info(
                        f"Regime: {regime_label} - Reducing position sizes to 75%"
                    )
                else:  # 安定上昇 (Stable Bull)
                    # 通常通り
                    self.weights = self.base_weights.copy()
                    logger.info(f"Regime: {regime_label} - Using normal position sizes")
            except Exception as e:
                logger.error(f"Error in regime detection: {e}")
                self.weights = self.base_weights.copy()

        # 1. Generate signals from each strategy
        signals_dict = {}
        for strategy in self.strategies:
            try:
                strategy_signals = strategy.generate_signals(df)
                if strategy_signals is not None and not strategy_signals.empty:
                    signals_dict[strategy.name] = strategy_signals
            except Exception as e:
                logger.error(f"Error generating signals from {strategy.name}: {e}")

        if not signals_dict:
            logger.warning("No valid signals from any strategy")
            return pd.Series(0, index=df.index)

        # 2. Align all signals to the same index
        aligned_signals = pd.DataFrame(signals_dict, index=df.index)
        aligned_signals = aligned_signals.fillna(0)

        # 3. Weighted voting for each timestamp
        ensemble_signals = pd.Series(0, index=df.index, dtype=int)

        for idx in df.index:
            weighted_sum = 0.0
            total_weight = 0.0

            for strategy_name, signal_series in signals_dict.items():
                if idx in signal_series.index:
                    signal = signal_series.loc[idx]
                    weight = self.weights.get(strategy_name, 1.0)
                    weighted_sum += signal * weight
                    total_weight += weight

            # Convert weighted sum to final signal
            # Threshold: if weighted average > 0.3, BUY; if < -0.3, SELL; else HOLD
            if total_weight > 0:
                weighted_avg = weighted_sum / total_weight
                if weighted_avg > 0.3:
                    ensemble_signals.loc[idx] = 1
                elif weighted_avg < -0.3:
                    ensemble_signals.loc[idx] = -1
                else:
                    ensemble_signals.loc[idx] = 0

        return ensemble_signals

    def get_signal_explanation(self, signal: int) -> str:
        """Get explanation for the ensemble signal."""
        if signal == 1:
            regime_info = (
                f" (市場環境: {self.current_regime['label']})"
                if self.current_regime
                else ""
            )
            return f"複数のAI戦略が総合的に「買い」を推奨しています{regime_info}。"
        elif signal == -1:
            regime_info = (
                f" (市場環境: {self.current_regime['label']})"
                if self.current_regime
                else ""
            )
            return f"複数のAI戦略が総合的に「売り」を推奨しています{regime_info}。"
        return "アンサンブル戦略では明確なコンセンサスが得られていません。"


def load_custom_strategies() -> list:
    custom_strategies = []
    custom_dir = os.path.join(os.path.dirname(__file__), "custom")

    if not os.path.exists(custom_dir):
        return custom_strategies

    for filename in os.listdir(custom_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            filepath = os.path.join(custom_dir, filename)
            module_name = f"src.strategies.custom.{filename[:-3]}"

            try:
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)

                    for name, obj in inspect.getmembers(module):
                        if (
                            inspect.isclass(obj)
                            and issubclass(obj, Strategy)
                            and obj is not Strategy
                        ):
                            try:
                                strategy_instance = obj()
                                custom_strategies.append(strategy_instance)
                                print(
                                    f"Loaded custom strategy: {strategy_instance.name}"
                                )
                            except Exception as e:
                                print(f"Failed to instantiate {name}: {e}")
            except Exception as e:
                print(f"Failed to load custom strategy from {filename}: {e}")

    return custom_strategies


class TransformerStrategy(Strategy):
    """
    Temporal Fusion Transformer (TFT) を使用した戦略

    時系列予測の最先端Transformerモデルによる売買シグナル生成。
    """

    def __init__(self, name: str = "Transformer", trend_period: int = 200):
        super().__init__(name, trend_period)
        self.model = None
        self.is_trained = False
        self.sequence_length = 60

    def train(self, df: pd.DataFrame):
        try:
            from src.advanced_models import AdvancedModels
            from src.features import add_advanced_features

            df_feat = add_advanced_features(df.copy())
            numeric_cols = df_feat.select_dtypes(include=[np.number]).columns

            # データ準備（簡易版）
            data = df_feat[numeric_cols].values
            X, y = [], []
            for i in range(len(data) - self.sequence_length - 1):
                X.append(data[i: (i + self.sequence_length)])
                y.append(
                    data[i + self.sequence_length + 1, 0]
                )  # Close price as target (simplified)

            X, y = np.array(X), np.array(y)

            if len(X) == 0:
                return

            self.model = AdvancedModels.build_gru_model(
                input_shape=(X.shape[1], X.shape[2])
            )
            self.model.fit(X, y, epochs=10, batch_size=32, verbose=0)
            self.is_trained = True
            logger.info("GRU model trained")

        except Exception as e:
            logger.error(f"Error training GRU: {e}")

    def generate_signal(self, df: pd.DataFrame) -> str:
        if not self.is_trained or self.model is None:
            return "HOLD"

        try:
            from src.features import add_advanced_features

            df_feat = add_advanced_features(df.copy())
            numeric_cols = df_feat.select_dtypes(include=[np.number]).columns

            if len(df_feat) < self.sequence_length:
                return "HOLD"

            recent_data = df_feat[numeric_cols].iloc[-self.sequence_length:].values
            X = np.expand_dims(recent_data, axis=0)

            pred = self.model.predict(X)[0][0]
            current = df["Close"].iloc[-1]

            if pred > current * 1.02:
                return "BUY"
            elif pred < current * 0.98:
                return "SELL"
            return "HOLD"

        except Exception:
            return "HOLD"


class RLStrategy(Strategy):
    """
    強化学習 (DQN) を使用した戦略
    """

    def __init__(self, name: str = "RL_DQN", trend_period: int = 200):
        super().__init__(name, trend_period)
        self.agent = None
        self.is_trained = False
        logger.info(f"RLStrategy initialized: {name}")

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        DQNエージェントを使用してシグナルを生成
        """
        if df is None or len(df) < 100:
            return pd.Series(0, index=df.index)

        signals = pd.Series(0, index=df.index)

        try:
            from src.features import add_advanced_features
            from src.rl_agent import DQNAgent
            from src.rl_environment import TradingEnvironment

            # 特徴量追加
            df_features = add_advanced_features(df.copy())

            # 環境初期化
            env = TradingEnvironment(df_features)
            state_size = env.state_size
            action_size = env.action_space_size

            # エージェント初期化
            if self.agent is None:
                self.agent = DQNAgent(state_size, action_size)

            # 未学習なら学習実行（デモ用簡易学習）
            if not self.is_trained:
                self._train_agent(env, episodes=5)  # 時間短縮のため少なめ
                self.is_trained = True

            # 推論（全期間に対してアクション決定）
            # 注意: 本来はバックテスト環境でstepごとに実行すべきだが、
            # ここでは簡易的に全期間の状態に対してgreedyに行動を選択する

            state = env.reset()
            done = False

            while not done:
                step = env.current_step
                action = self.agent.act(
                    state
                )  # Epsilon-Greedy (学習後はepsilon小さくなる)

                # シグナル変換
                # 0: HOLD -> 0
                # 1: BUY -> 1
                # 2: SELL -> -1
                signal_val = 0
                if action == 1:
                    signal_val = 1
                elif action == 2:
                    signal_val = -1

                signals.iloc[step] = signal_val

                next_state, _, done, _ = env.step(action)
                state = next_state

        except Exception as e:
            logger.error(f"Error in RLStrategy: {e}")

        return signals

    def _train_agent(self, env, episodes: int = 10):
        """エージェントを学習させる"""
        logger.info(f"Training RL agent for {episodes} episodes...")

        for e in range(episodes):
            state = env.reset()
            done = False
            total_reward = 0

            while not done:
                action = self.agent.act(state)
                next_state, reward, done, _ = env.step(action)

                self.agent.remember(state, action, reward, next_state, done)
                state = next_state
                total_reward += reward

                self.agent.replay()

            self.agent.update_target_model()
            logger.info(
                f"Episode {e + 1}/{episodes} - Total Reward: {total_reward:.2f}, Epsilon: {self.agent.epsilon:.2f}"
            )


class GRUStrategy(Strategy):
    """GRUを使用した戦略"""

    def __init__(self, name: str = "GRU", trend_period: int = 200):
        super().__init__(name, trend_period)
        self.model = None
        self.is_trained = False
        self.sequence_length = 30

    def train(self, df: pd.DataFrame):
        try:
            from src.advanced_models import AdvancedModels
            from src.features import add_advanced_features

            df_feat = add_advanced_features(df.copy())
            numeric_cols = df_feat.select_dtypes(include=[np.number]).columns

            # データ準備（簡易版）
            data = df_feat[numeric_cols].values
            X, y = [], []
            for i in range(len(data) - self.sequence_length - 1):
                X.append(data[i: (i + self.sequence_length)])
                y.append(
                    data[i + self.sequence_length + 1, 0]
                )  # Close price as target (simplified)

            X, y = np.array(X), np.array(y)

            if len(X) == 0:
                return

            self.model = AdvancedModels.build_gru_model(
                input_shape=(X.shape[1], X.shape[2])
            )
            self.model.fit(X, y, epochs=10, batch_size=32, verbose=0)
            self.is_trained = True
            logger.info("GRU model trained")

        except Exception as e:
            logger.error(f"Error training GRU: {e}")

    def generate_signal(self, df: pd.DataFrame) -> str:
        if not self.is_trained or self.model is None:
            return "HOLD"

        try:
            from src.features import add_advanced_features

            df_feat = add_advanced_features(df.copy())
            numeric_cols = df_feat.select_dtypes(include=[np.number]).columns

            if len(df_feat) < self.sequence_length:
                return "HOLD"

            recent_data = df_feat[numeric_cols].iloc[-self.sequence_length:].values
            X = np.expand_dims(recent_data, axis=0)

            pred = self.model.predict(X)[0][0]
            current = df["Close"].iloc[-1]

            if pred > current * 1.02:
                return "BUY"
            elif pred < current * 0.98:
                return "SELL"
            return "HOLD"

        except Exception:
            return "HOLD"


class AttentionLSTMStrategy(Strategy):
    """Attention-LSTMを使用した戦略"""

    def __init__(self, name: str = "AttentionLSTM", trend_period: int = 200):
        super().__init__(name, trend_period)
        self.model = None
        self.is_trained = False
        self.sequence_length = 30

    def train(self, df: pd.DataFrame):
        try:
            from src.advanced_models import AdvancedModels
            from src.features import add_advanced_features

            df_feat = add_advanced_features(df.copy())
            numeric_cols = df_feat.select_dtypes(include=[np.number]).columns

            data = df_feat[numeric_cols].values
            X, y = [], []
            for i in range(len(data) - self.sequence_length - 1):
                X.append(data[i: (i + self.sequence_length)])
                y.append(data[i + self.sequence_length + 1, 0])

            X, y = np.array(X), np.array(y)

            if len(X) == 0:
                return

            self.model = AdvancedModels.build_attention_lstm_model(
                input_shape=(X.shape[1], X.shape[2])
            )
            self.model.fit(X, y, epochs=10, batch_size=32, verbose=0)
            self.is_trained = True
            logger.info("Attention-LSTM model trained")

        except Exception as e:
            logger.error(f"Error training Attention-LSTM: {e}")

    def generate_signal(self, df: pd.DataFrame) -> str:
        if not self.is_trained or self.model is None:
            return "HOLD"

        try:
            from src.features import add_advanced_features

            df_feat = add_advanced_features(df.copy())
            numeric_cols = df_feat.select_dtypes(include=[np.number]).columns

            if len(df_feat) < self.sequence_length:
                return "HOLD"

            recent_data = df_feat[numeric_cols].iloc[-self.sequence_length:].values
            X = np.expand_dims(recent_data, axis=0)

            pred = self.model.predict(X)[0][0]
            current = df["Close"].iloc[-1]

            if pred > current * 1.02:
                return "BUY"
            elif pred < current * 0.98:
                return "SELL"
            return "HOLD"

        except Exception:
            return "HOLD"


# -----------------------------------------------------------------------------
# Ensemble Strategy
# -----------------------------------------------------------------------------


class DynamicEnsembleStrategy(Strategy):
    """Dynamic Ensemble Strategy - 動的な戦略アンサンブル"""

    def __init__(
        self, strategies: List[Strategy] = None, trend_period: int = 200
    ) -> None:
        super().__init__("Dynamic Ensemble", trend_period)

        if strategies is None:
            # デフォルトの戦略セット
            self.strategies = [
                LightGBMStrategy(lookback_days=60),
                GRUStrategy(),  # GRUはlookback_daysを受け取らない
                RSIStrategy(period=14),
            ]
        else:
            self.strategies = strategies

        self.ensemble = DynamicEnsemble(self.strategies)

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty:
            return pd.Series(dtype=int)

        # 統合スコアと詳細予測を取得
        ensemble_score, predictions = self.ensemble.predict(df)

        # スコアに基づいてシグナル生成
        # 0.3以上で買い、-0.3以下で売り（閾値は調整可能）
        if ensemble_score >= 0.3:
            signal = 1
        elif ensemble_score <= -0.3:
            signal = -1
        else:
            signal = 0

        # Seriesとして返す（現状は単一時点の評価だが、互換性のためSeriesにする）
        signals = pd.Series(0, index=df.index)
        signals.iloc[-1] = signal

        return signals

    def update_performance(self, ticker: str, date: datetime, actual_return: float):
        """
        パフォーマンスを更新してウェイトを調整する
        （バックテストや実運用後に呼び出す）
        """
        # 直近の予測を再取得する必要があるが、ここでは簡易的に
        # 履歴に保存されている予測を使用するか、別途管理が必要
        # DynamicEnsemble.update は予測値も引数に取るため、
        # 呼び出し元で予測値を保持しておく必要がある

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """詳細分析結果を返す"""
        ensemble_score, predictions = self.ensemble.predict(df)

        if ensemble_score >= 0.3:
            signal = 1
        elif ensemble_score <= -0.3:
            signal = -1
        else:
            signal = 0

        return {
            "signal": signal,
            "confidence": abs(ensemble_score),  # スコアの絶対値を信頼度とする
            "details": {
                "ensemble_score": ensemble_score,
                "model_predictions": predictions,
                "weights": self.ensemble.weights,
            },
        }


# -----------------------------------------------------------------------------
# Multi-Timeframe Strategy
# -----------------------------------------------------------------------------


class MultiTimeframeStrategy(Strategy):
    """
    マルチタイムフレーム戦略

    週足トレンドをフィルターとして使用し、
    日足シグナルが長期トレンドと一致する場合のみエントリーします。
    """

    def __init__(self, base_strategy: Strategy = None, trend_period: int = 200) -> None:
        super().__init__("Multi-Timeframe", trend_period)
        self.base_strategy = base_strategy if base_strategy else CombinedStrategy()
        self.mtf_analyzer = MultiTimeframeAnalyzer()

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty:
            return pd.Series(dtype=int)

        # ベース戦略のシグナル生成
        base_signals = self.base_strategy.generate_signals(df)

        # MTF分析（現状は最新時点のみの判定だが、バックテスト用に全期間計算が必要）
        # ここでは簡易的に、最新のシグナルに対してのみフィルターを適用するロジックにする
        # （全期間のバックテストを厳密に行うには、TimeframeResamplerで全期間の週足を作成し、マージする必要がある）

        # 厳密なバックテスト用の実装:
        #             pass
        # 1. 日足データ全体をリサンプリングして週足データを作成
        # 2. 週足トレンドを計算
        # 3. 日足にマージ（ffill）
        # 4. フィルター適用

        # ここではMTFAnalyzerの機能を使って、データフレーム全体に対して処理を行う
        # ただし、MTFAnalyzer.analyzeは最新状態を返す設計になっているため、
        # ここで独自にリサンプリングとマージを行う

        try:
            # リサンプリング
            weekly_df = self.mtf_analyzer.resample_data(df, "W-FRI")

            # 週足トレンド計算 (SMA20 > SMA50)
            weekly_df["SMA_20"] = weekly_df["Close"].rolling(window=20).mean()
            weekly_df["SMA_50"] = weekly_df["Close"].rolling(window=50).mean()

            weekly_df["Weekly_Trend"] = 0
            weekly_df.loc[
                (weekly_df["Close"] > weekly_df["SMA_20"])
                & (weekly_df["SMA_20"] > weekly_df["SMA_50"]),
                "Weekly_Trend",
            ] = 1  # Uptrend
            weekly_df.loc[
                (weekly_df["Close"] < weekly_df["SMA_20"])
                & (weekly_df["SMA_20"] < weekly_df["SMA_50"]),
                "Weekly_Trend",
            ] = -1  # Downtrend

            # 日足にマージ
            # reindex + ffill で直近の週足トレンドを適用
            weekly_trend_series = (
                weekly_df["Weekly_Trend"].reindex(df.index, method="ffill").fillna(0)
            )

            # フィルター適用
            final_signals = base_signals.copy()

            # 買いシグナル: 週足が上昇トレンド(1)の時のみ許可
            final_signals[(final_signals == 1) & (weekly_trend_series != 1)] = 0

            # 売りシグナル: 週足が下降トレンド(-1)の時のみ許可
            final_signals[(final_signals == -1) & (weekly_trend_series != -1)] = 0

            return final_signals

        except Exception as e:
            # エラー時はベース戦略のシグナルをそのまま返す（安全策）
            print(f"MTF Error: {e}")
            return base_signals

    def get_signal_explanation(self, signal: int) -> str:
        base_expl = self.base_strategy.get_signal_explanation(signal)
        if signal == 1:
            return f"{base_expl} さらに、週足が上昇トレンドを示しており、長期的な上昇が見込まれます。"
        elif signal == -1:
            return f"{base_expl} さらに、週足が下降トレンドを示しており、長期的な下落が見込まれます。"
        return base_expl


# -----------------------------------------------------------------------------
# Sentiment Strategy
# -----------------------------------------------------------------------------
class SentimentStrategy(Strategy):
    """
    ニュース感情分析戦略

    BERTによるニュース感情スコアに基づいてシグナルを生成します。
    """

    def __init__(self, threshold: float = 0.15, period: int = 14) -> None:
        super().__init__("Sentiment Analysis", period)
        self.threshold = threshold

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or "Sentiment_Score" not in df.columns:
            return pd.Series(dtype=int)

        signals = pd.Series(0, index=df.index)

        # 感情スコアに基づくシグナル
        # ポジティブ: 買い
        signals[df["Sentiment_Score"] > self.threshold] = 1

        # ネガティブ: 売り
        signals[df["Sentiment_Score"] < -self.threshold] = -1

        return signals

    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return "ニュース感情がポジティブです。市場心理が好転しており、上昇が期待できます。"
        elif signal == -1:
            return "ニュース感情がネガティブです。市場心理が悪化しており、下落のリスクがあります。"
        return "ニュース感情は中立です。"
