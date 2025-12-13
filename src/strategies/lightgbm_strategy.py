import logging
from typing import Dict

import lightgbm as lgb
import numpy as np
import pandas as pd

from .base import Strategy

try:
    from src.features import add_advanced_features, add_macro_features
except ImportError:
    # Forward declaration or dummy if circular import
    def add_advanced_features(df):
        return df

    def add_macro_features(df, macro):
        return df


try:
    from src.data_loader import fetch_macro_data
except ImportError:

    def fetch_macro_data(period="5y"):
        return {}


try:
    from src.optimization.optuna_tuner import OptunaTuner
except ImportError:
    OptunaTuner = None

logger = logging.getLogger(__name__)


class LightGBMStrategy(Strategy):
    def __init__(self, lookback_days=365, threshold=0.005, auto_tune=False):
        super().__init__("LightGBM Alpha")
        self.lookback_days = lookback_days
        self.threshold = threshold
        self.auto_tune = auto_tune
        self.best_params = None
        self.model = None
        self.default_positive_threshold = 0.60
        self.default_negative_threshold = 0.40
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
        self.explainer = None

    def _generate_signals_from_probs(self, probs: pd.Series, upper: float, lower: float) -> pd.Series:
        """Convert probability predictions into trading signals."""
        signals = pd.Series(0, index=probs.index)
        signals[probs > upper] = 1
        signals[probs < lower] = -1
        return signals

    def _calibrate_thresholds(
        self,
        probs: pd.Series,
        actual: pd.Series,
        base_upper: float = 0.60,
        base_lower: float = 0.40,
    ) -> tuple[float, float]:
        """
        Tune probability thresholds to maximize usable accuracy.

        The score combines accuracy on actionable signals with coverage so that
        the strategy prefers thresholds that make confident predictions without
        becoming overly conservative.
        """
        if probs.empty or actual.empty:
            return base_upper, base_lower

        aligned_actual = actual.reindex(probs.index)

        candidate_uppers = np.arange(0.55, 0.71, 0.01)
        candidate_lowers = np.arange(0.29, 0.46, 0.01)

        best_score = -np.inf
        best_coverage = 0.0
        best_upper, best_lower = base_upper, base_lower

        for upper in candidate_uppers:
            for lower in candidate_lowers:
                if upper - lower < 0.12:
                    continue

                signals = self._generate_signals_from_probs(probs, upper, lower)
                actionable = signals != 0

                if actionable.sum() == 0:
                    continue

                predicted = signals[actionable].replace({-1: 0}).astype(int).to_numpy()
                truth = aligned_actual[actionable].to_numpy()

                if np.isnan(truth).all():
                    continue

                accuracy = (predicted == truth).mean()
                coverage = actionable.mean()
                score = accuracy * coverage

                if score > best_score or (np.isclose(score, best_score) and coverage > best_coverage):
                    best_score = score
                    best_coverage = coverage
                    best_upper, best_lower = upper, lower

        if best_score < 0:
            return base_upper, base_lower

        return best_upper, best_lower

    def explain_prediction(self, df: pd.DataFrame) -> Dict[str, float]:
        """Return SHAP values for the latest prediction"""
        if self.model is None:
            return {}

        try:
            import shap

            # Prepare latest data point
            data = add_advanced_features(df)
            macro_data = fetch_macro_data(period="5y")
            data = add_macro_features(data, macro_data)

            if data.empty:
                return {}

            latest_data = data[self.feature_cols].iloc[[-1]]

            # Create explainer if not cached (TreeExplainer is efficient)
            if self.explainer is None:
                self.explainer = shap.TreeExplainer(self.model)

            shap_values = self.explainer.shap_values(latest_data)

            # Handle list output for binary classification
            if isinstance(shap_values, list):
                vals = shap_values[1][0]  # Positive class
            else:
                vals = shap_values[0]

            explanation = dict(zip(self.feature_cols, vals))
            # Sort by absolute impact
            sorted_expl = dict(sorted(explanation.items(), key=lambda item: abs(item[1]), reverse=True))
            return sorted_expl

        except ImportError:
            logger.warning("SHAP not installed")
            return {}
        except Exception as e:
            logger.error(f"Error in SHAP explanation: {e}")
            return {}

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        try:
            # Verify lightgbm is available
            import lightgbm as lgb
        except ImportError:
            logger.warning("LightGBM not installed. Returning empty signals.")
            return pd.Series(0, index=df.index)

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

            # Default params
            params = {"objective": "binary", "metric": "binary_logloss", "verbosity": -1, "seed": 42}

            # Auto-Tune if enabled (and enough data)
            if self.auto_tune and len(train_df) > 200:
                try:
                    # Only tune occasionally to save time (e.g. at start or every year)
                    # For simplicity here: Tune if model is None (first run) or every 5 loops
                    if self.model is None or (current_idx - start_idx) % (retrain_period * 5) == 0:
                        logger.info(f"Running Optuna tuning at index {current_idx}...")
                        tuner = OptunaTuner(n_trials=10)  # 10 trials for speed
                        best_params = tuner.optimize_lightgbm(X_train, y_train)
                        params.update(best_params)
                        self.best_params = best_params  # Cache for display
                except Exception as e:
                    logger.error(f"Optuna tuning failed: {e}")

            train_data = lgb.Dataset(X_train, label=y_train)
            self.model = lgb.train(params, train_data, num_boost_round=100)

            # Calibrate thresholds using recent training performance
            calibrated_upper = self.default_positive_threshold
            calibrated_lower = self.default_negative_threshold

            calibration_size = max(50, int(len(train_df) * 0.2))
            if calibration_size < len(train_df):
                calibration_df = train_df.tail(calibration_size)
                calibration_probs = pd.Series(
                    self.model.predict(calibration_df[self.feature_cols]),
                    index=calibration_df.index,
                )
                calibration_y = (calibration_df["Return_1d"] > 0).astype(int)
                calibrated_upper, calibrated_lower = self._calibrate_thresholds(
                    calibration_probs,
                    calibration_y,
                    base_upper=self.default_positive_threshold,
                    base_lower=self.default_negative_threshold,
                )

                # Persist the latest calibrated thresholds for subsequent windows
                self.default_positive_threshold = calibrated_upper
                self.default_negative_threshold = calibrated_lower

            X_test = test_df[self.feature_cols]
            if not X_test.empty:
                preds = pd.Series(self.model.predict(X_test), index=X_test.index)
                chunk_signals = self._generate_signals_from_probs(preds, calibrated_upper, calibrated_lower)
                signals.loc[chunk_signals.index] = chunk_signals

            current_idx += retrain_period

        return signals

    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return "LightGBMモデルがマクロ経済指標やテクニカル指標を分析し、上昇確率が高いと判断しました。"
        elif signal == -1:
            return "LightGBMモデルがマクロ経済指標やテクニカル指標を分析し、下落リスクが高いと判断しました。"
        return "AIによる強い確信度は得られていません。"
