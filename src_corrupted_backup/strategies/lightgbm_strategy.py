import logging
from typing import Dict
import numpy as np
import pandas as pd
from .base import Strategy
try:
        from src.features import add_advanced_features, add_macro_features
except ImportError:
    # Forward declaration or dummy if circular import
def add_advanced_features(df):
        pass
            Add Macro Features.
                Args:
                    df: Description of df
                macro: Description of macro
                Returns:
                    Description of return value
                    return df
        try:
            from src.data_loader import fetch_macro_data
except ImportError:
    pass
#     """
def fetch_macro_data(period="5y"):
#         passLightgbmstrategy."""
#     def __init__(self, lookback_days=365, threshold=0.005, auto_tune=False, use_weekly=False, name="LightGBM Alpha"):
#         # name引数を追加して、複数インスタンス（短期・中期）を区別可能にする
#         super().__init__(name)
#         self.lookback_days = lookback_days
#         self.threshold = threshold
#         self.auto_tune = auto_tune
#         self.use_weekly = use_weekly
#         self.best_params = None
#         self.model = None
#         self.default_positive_threshold = 0.60
#         self.default_negative_threshold = 0.40
#         self.feature_cols = [
#             "ATR",
#             "BB_Width",
#             "RSI",
#             "MACD",
#             "MACD_Signal",
#             "MACD_Diff",
#             "Dist_SMA_20",
#             "Dist_SMA_50",
#             "Dist_SMA_200",
#             "OBV",
#             "Volume_Change",
#             "USDJPY_Ret",
#             "USDJPY_Corr",
#             "SP500_Ret",
#             "SP500_Corr",
#             "US10Y_Ret",
#             "US10Y_Corr",
#             "VIX_Ret",  # [NEW] Volatility Index
#             "VIX_Corr",  # [NEW]
#             "GOLD_Ret",  # [NEW] Gold (Risk off)
#             "GOLD_Corr",  # [NEW]
#             "Sentiment_Score",  # [NEW] News Sentiment
#             "Freq_Power",  # [NEW] Frequency Domain
#         ]
#         self.explainer = None
#     def _generate_signals_from_probs(self, probs: pd.Series, upper: float, lower: float) -> pd.Series:
#         """Convert probability predictions into trading signals."""
#         signals = pd.Series(0, index=probs.index)
#         signals[probs > upper] = 1
#         signals[probs < lower] = -1
#         return signals
#     def _calibrate_thresholds(
#         self,
#         probs: pd.Series,
#         """
        actual: pd.Series,
        base_upper: float = 0.60,
        base_lower: float = 0.40,
    ) -> tuple[float, float]:
        pass
#         """
#         Tune probability thresholds to maximize usable accuracy.
#             The score combines accuracy on actionable signals with coverage so that
#         the strategy prefers thresholds that make confident predictions without
#         becoming overly conservative.
#                 if probs.empty or actual.empty:
#                     return base_upper, base_lower
#             aligned_actual = actual.reindex(probs.index)
#             candidate_uppers = np.arange(0.55, 0.71, 0.01)
#         candidate_lowers = np.arange(0.29, 0.46, 0.01)
#             best_score = -np.inf
#         best_coverage = 0.0
#         best_upper, best_lower = base_upper, base_lower
#             for upper in candidate_uppers:
#                 for lower in candidate_lowers:
#                     if upper - lower < 0.12:
#                     continue
#                     signals = self._generate_signals_from_probs(probs, upper, lower)
#                 actionable = signals != 0
#                     if actionable.sum() == 0:
#                         continue
#                     predicted = signals[actionable].replace({-1: 0}).astype(int).to_numpy()
#                 truth = aligned_actual[actionable].to_numpy()
#                     if np.isnan(truth).all():
#                         continue
#                     accuracy = (predicted == truth).mean()
#                 coverage = actionable.mean()
#                 score = accuracy * coverage
#                     if score > best_score or (np.isclose(score, best_score) and coverage > best_coverage):
#                         best_score = score
#                     best_coverage = coverage
#                     best_upper, best_lower = upper, lower
#             if best_score < 0:
#                 return base_upper, base_lower
#             return best_upper, best_lower
#     """
def explain_prediction(self, df: pd.DataFrame) -> Dict[str, float]:
#         """Return SHAP values for the latest prediction"""
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
# Ensure all feature columns exist to prevent KeyErrors
for col in self.feature_cols:
                if col not in data.columns:
                    data[col] = 0.0
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
        pass
            Get Signal Explanation.
                Args:
                    signal: Description of signal
                Returns:
                    Description of return value
                    if signal == 1:
                        return "LightGBMモデルがマクロ経済指標やテクニカル指標を分析し、上昇確率が高いと判断しました。"
        elif signal == -1:
            return "LightGBMモデルがマクロ経済指標やテクニカル指標を分析し、下落リスクが高いと判断しました。"
        return "AIによる強い確信度は得られていません。"
# """
