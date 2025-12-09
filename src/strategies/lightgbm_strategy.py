import pandas as pd
import logging
from typing import Dict, Any
from .base import Strategy


try:
    from src.features import add_advanced_features, add_macro_features
except ImportError:
    # Forward declaration or dummy if circular import
    def add_advanced_features(df): return df
    def add_macro_features(df, macro): return df

try:
    from src.data_loader import fetch_macro_data
except ImportError:
    def fetch_macro_data(period="5y"): return {}

logger = logging.getLogger(__name__)

class LightGBMStrategy(Strategy):
    def __init__(self, lookback_days=365, threshold=0.005):
        super().__init__("LightGBM Alpha")
        self.lookback_days = lookback_days
        self.threshold = threshold
        self.model = None
        self.feature_cols = ['ATR', 'BB_Width', 'RSI', 'MACD', 'MACD_Signal', 'MACD_Diff', 
                             'Dist_SMA_20', 'Dist_SMA_50', 'Dist_SMA_200', 'OBV', 'Volume_Change',
                             'USDJPY_Ret', 'USDJPY_Corr', 'SP500_Ret', 'SP500_Corr', 'US10Y_Ret', 'US10Y_Corr']
        self.explainer = None

    def explain_prediction(self, df: pd.DataFrame) -> Dict[str, float]:
        """Return SHAP values for the latest prediction"""
        if self.model is None:
            return {}
            
        try:
            import shap
            import lightgbm as lgb
            
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
                vals = shap_values[1][0] # Positive class
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
            y_train = (train_df['Return_1d'] > 0).astype(int)
            
            params = {'objective': 'binary', 'metric': 'binary_logloss', 'verbosity': -1, 'seed': 42}
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
