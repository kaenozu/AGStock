"""
高度なアンサンブル学習モジュール

- Stackingアンサンブル
- 動的重み付け
- モデル多様性の導入
- ブレンディング
- メタフィーチャーの利用
"""

import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
import lightgbm as lgb
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error
import logging
from typing import Dict, List, Tuple, Callable, Any, Optional
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class StackingEnsemble:
    """Stackingアンサンブルの実装"""
    
    def __init__(self, base_models: List, meta_model: Any = None):
        self.base_models = base_models
        self.meta_model = meta_model or LinearRegression()
        self.is_fitted = False
    
    def fit(self, X: np.ndarray, y: np.ndarray, cv_folds: int = 5) -> 'StackingEnsemble':
        """モデルの学習"""
        # 時系列交差検証を準備
        tscv = TimeSeriesSplit(n_splits=cv_folds)
        
        # ベースモデルの予測を格納するための配列
        base_predictions = np.zeros((X.shape[0], len(self.base_models)))
        
        # 各フォールドでベースモデルを学習・予測
        for train_idx, val_idx in tscv.split(X):
            X_train_fold, X_val_fold = X[train_idx], X[val_idx]
            y_train_fold = y[train_idx]
            
            for i, model in enumerate(self.base_models):
                # モデルの種類に応じた学習方法
                if hasattr(model, 'fit'):
                    if hasattr(model, 'predict') and not isinstance(model, keras.Model):
                        # sklearn形式のモデル
                        model.fit(X_train_fold.reshape(X_train_fold.shape[0], -1), y_train_fold)
                        fold_pred = model.predict(X_val_fold.reshape(X_val_fold.shape[0], -1))
                    else:
                        # Kerasモデル
                        X_train_reshaped = X_train_fold
                        if len(X_train_reshaped.shape) == 2:
                            X_train_reshaped = X_train_reshaped[:, :, np.newaxis]
                        
                        model.fit(X_train_reshaped, y_train_fold, epochs=10, verbose=0)
                        fold_pred = model.predict(X_val_fold, verbose=0)
                else:
                    # その他のモデル（将来の拡張用）
                    continue
                
                base_predictions[val_idx, i] = fold_pred.flatten()
        
        # メタモデルを学習
        self.meta_model.fit(base_predictions, y)
        self.is_fitted = True
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """予測の実行"""
        if not self.is_fitted:
            raise ValueError("Model has not been fitted yet.")
        
        # ベースモデルの予測
        base_predictions = np.zeros((X.shape[0], len(self.base_models)))
        
        for i, model in enumerate(self.base_models):
            if hasattr(model, 'predict') and not isinstance(model, keras.Model):
                # sklearn形式のモデル
                pred = model.predict(X.reshape(X.shape[0], -1))
            else:
                # Kerasモデル
                X_reshaped = X
                if len(X_reshaped.shape) == 2:
                    X_reshaped = X_reshaped[:, :, np.newaxis]
                pred = model.predict(X_reshaped, verbose=0)
            
            base_predictions[:, i] = pred.flatten()
        
        # メタモデルによる最終予測
        final_pred = self.meta_model.predict(base_predictions)
        return final_pred


class DynamicWeightedEnsemble:
    """動的重み付けアンサンブルの実装"""
    
    def __init__(self, models: List, weight_strategy: str = 'performance'):
        self.models = models
        self.weight_strategy = weight_strategy
        self.weights = np.ones(len(models)) / len(models)
        self.model_performance = [0.0] * len(models)
        self.performance_history = [[] for _ in models]
        self.is_fitted = False
    
    def update_weights_by_performance(self, y_true: np.ndarray, y_preds: List[np.ndarray]):
        """モデルの性能に基づいて重みを更新"""
        performances = []
        
        for i, pred in enumerate(y_preds):
            # 性能指標としてMSEを使用
            perf = 1.0 / (mean_squared_error(y_true, pred) + 1e-8)
            performances.append(perf)
            self.performance_history[i].append(perf)
        
        # 最新N件の平均性能に基づいて重みを更新
        recent_n = min(10, len(self.performance_history[0]))
        for i in range(len(self.models)):
            if len(self.performance_history[i]) >= recent_n:
                avg_perf = np.mean(self.performance_history[i][-recent_n:])
                self.model_performance[i] = avg_perf
        
        # 正規化して重みを計算
        total_perf = sum(self.model_performance)
        if total_perf > 0:
            self.weights = np.array(self.model_performance) / total_perf
        else:
            self.weights = np.ones(len(self.models)) / len(self.models)
    
    def update_weights_by_market_regime(self, volatility: float, correlation: float):
        """市場レジームに基づいて重みを更新"""
        # ボラティリティが高い場合は、より安定したモデルに重みを置く
        if volatility > 0.02:  # 高ボラティリティ
            # 線形回帰などの単純モデルを重視
            simple_model_weight = 0.4
            self.weights = np.array([
                simple_model_weight if i % 2 == 0 else (1 - simple_model_weight) / (len(self.models) - len([j for j in range(len(self.models)) if j % 2 == 0]))
                for i in range(len(self.models))
            ])
        elif correlation > 0.7:  # 高相関
            # モデル間の多様性を重視
            self.weights = np.ones(len(self.models)) / len(self.models)
        else:  # 通常
            # 通常の性能ベースの重み
            pass
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'DynamicWeightedEnsemble':
        """モデルの学習（各ベースモデルを学習）"""
        for i, model in enumerate(self.models):
            if isinstance(model, keras.Model):
                X_reshaped = X
                if len(X_reshaped.shape) == 2:
                    X_reshaped = X_reshaped[:, :, np.newaxis]
                model.fit(X_reshaped, y, epochs=10, verbose=0)
            elif hasattr(model, 'fit'):
                model.fit(X.reshape(X.shape[0], -1), y)
        
        self.is_fitted = True
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """予測の実行（動的重みを使用）"""
        if not self.is_fitted:
            raise ValueError("Model has not been fitted yet.")
        
        predictions = []
        for model in self.models:
            if isinstance(model, keras.Model):
                X_reshaped = X
                if len(X_reshaped.shape) == 2:
                    X_reshaped = X_reshaped[:, :, np.newaxis]
                pred = model.predict(X_reshaped, verbose=0)
            elif hasattr(model, 'predict'):
                pred = model.predict(X.reshape(X.shape[0], -1))
            else:
                continue
            predictions.append(pred)
        
        # 重み付き平均
        weighted_pred = np.zeros_like(predictions[0])
        for i, pred in enumerate(predictions):
            weighted_pred += self.weights[i] * pred
        
        return weighted_pred


class DiversityEnsemble:
    """モデル多様性を導入するアンサンブル"""
    
    def __init__(self, models: List, diversity_metric: str = 'correlation'):
        self.models = models
        self.diversity_metric = diversity_metric
        self.weights = np.ones(len(models)) / len(models)
        self.is_fitted = False
    
    def calculate_diversity_weights(self, predictions: List[np.ndarray]) -> np.ndarray:
        """多様性に基づいた重みを計算"""
        if self.diversity_metric == 'correlation':
            # 予測値の相関行列を計算
            n_models = len(predictions)
            if n_models < 2:
                return self.weights
            
            # 予測値の相関を計算
            pred_matrix = np.column_stack([p.flatten() for p in predictions])
            corr_matrix = np.corrcoef(pred_matrix.T)
            
            # 相関が低い（多様性が高い）モデルに重みを置く
            diversity_scores = []
            for i in range(n_models):
                avg_corr = np.mean([corr_matrix[i, j] for j in range(n_models) if i != j])
                diversity_score = 1.0 - abs(avg_corr)  # 相関の絶対値が低いほど多様性が高い
                diversity_scores.append(diversity_score)
            
            # 正規化
            total_diversity = sum(diversity_scores)
            if total_diversity > 0:
                weights = np.array(diversity_scores) / total_diversity
            else:
                weights = np.ones(n_models) / n_models
        else:
            # その他の多様性指標（将来の拡張用）
            weights = np.ones(len(predictions)) / len(predictions)
        
        return weights
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'DiversityEnsemble':
        """モデルの学習"""
        for model in self.models:
            if isinstance(model, keras.Model):
                X_reshaped = X
                if len(X_reshaped.shape) == 2:
                    X_reshaped = X_reshaped[:, :, np.newaxis]
                model.fit(X_reshaped, y, epochs=10, verbose=0)
            elif hasattr(model, 'fit'):
                model.fit(X.reshape(X.shape[0], -1), y)
        
        self.is_fitted = True
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """予測の実行"""
        if not self.is_fitted:
            raise ValueError("Model has not been fitted yet.")
        
        predictions = []
        for model in self.models:
            if isinstance(model, keras.Model):
                X_reshaped = X
                if len(X_reshaped.shape) == 2:
                    X_reshaped = X_reshaped[:, :, np.newaxis]
                pred = model.predict(X_reshaped, verbose=0)
            elif hasattr(model, 'predict'):
                pred = model.predict(X.reshape(X.shape[0], -1))
            else:
                continue
            predictions.append(pred)
        
        # 多様性に基づく重みを計算
        self.weights = self.calculate_diversity_weights(predictions)
        
        # 重み付き平均
        weighted_pred = np.zeros_like(predictions[0])
        for i, pred in enumerate(predictions):
            weighted_pred += self.weights[i] * pred
        
        return weighted_pred


class ConfidenceWeightedEnsemble:
    """予測確信度に基づく重み付けアンサンブル"""
    
    def __init__(self, models: List, confidence_method: str = 'prediction_interval'):
        self.models = models
        self.confidence_method = confidence_method
        self.weights = np.ones(len(models)) / len(models)
        self.is_fitted = False
    
    def calculate_confidence_weights(self, predictions: List[np.ndarray], X: np.ndarray) -> np.ndarray:
        """予測確信度に基づいて重みを計算"""
        if self.confidence_method == 'prediction_interval':
            # 予測区間の幅が狭いほど確信度が高い
            confidences = []
            for i, model in enumerate(self.models):
                # 予測区間を簡易的に計算（実際にはより複雑な方法が必要）
                # ここでは、モデルの過去の予測精度に基づいて計算
                if hasattr(model, 'history') and model.history is not None:
                    # モデルの履歴から誤差を推定
                    if 'val_loss' in model.history.history:
                        avg_error = np.mean(model.history.history['val_loss'][-5:])  # 最後の5エポックの平均誤差
                        confidence = 1.0 / (avg_error + 1e-8)  # 誤差の逆数を確信度とする
                    else:
                        confidence = 1.0
                else:
                    confidence = 1.0
                
                confidences.append(confidence)
        else:
            # その他の確信度指標（将来の拡張用）
            confidences = [1.0] * len(predictions)
        
        # 正規化
        total_confidence = sum(confidences)
        if total_confidence > 0:
            weights = np.array(confidences) / total_confidence
        else:
            weights = np.ones(len(predictions)) / len(predictions)
        
        return weights
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'ConfidenceWeightedEnsemble':
        """モデルの学習"""
        for model in self.models:
            if isinstance(model, keras.Model):
                X_reshaped = X
                if len(X_reshaped.shape) == 2:
                    X_reshaped = X_reshaped[:, :, np.newaxis]
                history = model.fit(X_reshaped, y, epochs=10, validation_split=0.2, verbose=0)
                model.history = history
            elif hasattr(model, 'fit'):
                model.fit(X.reshape(X.shape[0], -1), y)
        
        self.is_fitted = True
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """予測の実行"""
        if not self.is_fitted:
            raise ValueError("Model has not been fitted yet.")
        
        predictions = []
        for model in self.models:
            if isinstance(model, keras.Model):
                X_reshaped = X
                if len(X_reshaped.shape) == 2:
                    X_reshaped = X_reshaped[:, :, np.newaxis]
                pred = model.predict(X_reshaped, verbose=0)
            elif hasattr(model, 'predict'):
                pred = model.predict(X.reshape(X.shape[0], -1))
            else:
                continue
            predictions.append(pred)
        
        # 確信度に基づく重みを計算
        self.weights = self.calculate_confidence_weights(predictions, X)
        
        # 重み付き平均
        weighted_pred = np.zeros_like(predictions[0])
        for i, pred in enumerate(predictions):
            weighted_pred += self.weights[i] * pred
        
        return weighted_pred


class AdvancedEnsemble:
    """高度なアンサンブル手法を統合したクラス"""
    
    def __init__(self, ensemble_type: str = 'stacking'):
        self.ensemble_type = ensemble_type
        self.ensemble_model = None
    
    def fit(self, X: np.ndarray, y: np.ndarray, base_models: List = None) -> 'AdvancedEnsemble':
        """モデルの学習"""
        if self.ensemble_type == 'stacking':
            self.ensemble_model = StackingEnsemble(base_models)
            self.ensemble_model.fit(X, y)
        elif self.ensemble_type == 'dynamic':
            self.ensemble_model = DynamicWeightedEnsemble(base_models)
            self.ensemble_model.fit(X, y)
        elif self.ensemble_type == 'diversity':
            self.ensemble_model = DiversityEnsemble(base_models)
            self.ensemble_model.fit(X, y)
        elif self.ensemble_type == 'confidence':
            self.ensemble_model = ConfidenceWeightedEnsemble(base_models)
            self.ensemble_model.fit(X, y)
        else:
            raise ValueError(f"Unknown ensemble type: {self.ensemble_type}")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """予測の実行"""
        return self.ensemble_model.predict(X)


def create_model_diversity_ensemble():
    """多様なモデルを統合するアンサンブルを作成"""
    
    # 様々なアーキテクチャのモデルを準備
    models = []
    
    # 1. Simple LSTM
    lstm_model = keras.Sequential([
        keras.layers.LSTM(50, return_sequences=True),
        keras.layers.LSTM(50),
        keras.layers.Dense(25),
        keras.layers.Dense(1)
    ])
    models.append(lstm_model)
    
    # 2. CNN-LSTM
    cnn_lstm_model = keras.Sequential([
        keras.layers.Conv1D(filters=64, kernel_size=3, activation='relu'),
        keras.layers.MaxPooling1D(pool_size=2),
        keras.layers.LSTM(50),
        keras.layers.Dense(25),
        keras.layers.Dense(1)
    ])
    models.append(cnn_lstm_model)
    
    # 3. LightGBM
    lgbm_model = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
    models.append(lgbm_model)
    
    # 4. Random Forest
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    models.append(rf_model)
    
    return models


if __name__ == "__main__":
    # テスト用の実装
    logging.basicConfig(level=logging.INFO)
    
    # ダミーデータの作成
    np.random.seed(42)
    n_samples, sequence_length, n_features = 200, 30, 10
    X = np.random.randn(n_samples, sequence_length, n_features).astype(np.float32)
    y = np.random.randn(n_samples, 1).astype(np.float32).flatten()
    
    # 様々なモデルの準備
    models = create_model_diversity_ensemble()
    
    # Stackingアンサンブルのテスト
    print("Testing Stacking Ensemble...")
    stacking_ensemble = StackingEnsemble(models[:2])  # Kerasモデルのみ使用
    stacking_ensemble.fit(X[:150], y[:150])
    stacking_pred = stacking_ensemble.predict(X[150:])
    print(f"Stacking MSE: {mean_squared_error(y[150:], stacking_pred.flatten()):.4f}")
    
    # 動的重み付けアンサンブルのテスト
    print("\nTesting Dynamic Weighted Ensemble...")
    dyn_ensemble = DynamicWeightedEnsemble(models[:2])
    dyn_ensemble.fit(X[:150], y[:150])
    dyn_pred = dyn_ensemble.predict(X[150:])
    print(f"Dynamic Weighted MSE: {mean_squared_error(y[150:], dyn_pred.flatten()):.4f}")
    
    # 多様性ベースのアンサンブルのテスト
    print("\nTesting Diversity Ensemble...")
    div_ensemble = DiversityEnsemble(models[:2])
    div_ensemble.fit(X[:150], y[:150])
    div_pred = div_ensemble.predict(X[150:])
    print(f"Diversity MSE: {mean_squared_error(y[150:], div_pred.flatten()):.4f}")
    
    # 確信度ベースのアンサンブルのテスト
    print("\nTesting Confidence Weighted Ensemble...")
    conf_ensemble = ConfidenceWeightedEnsemble(models[:2])
    conf_ensemble.fit(X[:150], y[:150])
    conf_pred = conf_ensemble.predict(X[150:])
    print(f"Confidence Weighted MSE: {mean_squared_error(y[150:], conf_pred.flatten()):.4f}")
    
    # 各個別モデルの性能比較
    print("\nIndividual model performances:")
    for i, model in enumerate(models[:2]):  # Kerasモデルのみテスト
        if isinstance(model, keras.Model):
            X_reshaped = X[:150]
            if len(X_reshaped.shape) == 2:
                X_reshaped = X_reshaped[:, :, np.newaxis]
            model.fit(X_reshaped, y[:150], epochs=10, verbose=0)
            X_test_reshaped = X[150:]
            if len(X_test_reshaped.shape) == 2:
                X_test_reshaped = X_test_reshaped[:, :, np.newaxis]
            pred = model.predict(X_test_reshaped, verbose=0)
        else:
            model.fit(X[:150].reshape(X[:150].shape[0], -1), y[:150])
            pred = model.predict(X[150:].reshape(X[150:].shape[0], -1))
        
        mse = mean_squared_error(y[150:], pred.flatten())
        print(f"Model {i} MSE: {mse:.4f}")