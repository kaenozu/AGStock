"""
説明可能なAI (XAI) モジュール

- SHAP値の導入
- 注目度可視化
- LIMEによるローカル説明
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
import shap
import lime
import lime.lime_tabular
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Any, Callable
import logging
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class SHAPExplainer:
    """SHAPによる説明機能"""
    
    def __init__(self, model: Any):
        self.model = model
        self.explainer = None
        self.is_fitted = False
    
    def fit(self, X: np.ndarray) -> 'SHAPExplainer':
        """SHAPエクスプレイナーの学習"""
        try:
            # モデルの種類によって適切なエクスプレイナーを選択
            if hasattr(self.model, 'predict') and not isinstance(self.model, keras.Model):
                # Tree系モデル用
                if hasattr(self.model, 'feature_importances_') or isinstance(self.model, (RandomForestRegressor,)):
                    self.explainer = shap.TreeExplainer(self.model)
                else:
                    # 汎用的なPermutationExplainerを使用
                    self.explainer = shap.Explainer(self.model.predict, X)
            elif isinstance(self.model, keras.Model):
                # DeepSHAP用
                background = X[:100]  # バックグラウンドデータ
                self.explainer = shap.DeepExplainer(self.model, background)
            else:
                # 線形モデルやその他の場合
                self.explainer = shap.LinearExplainer(self.model, X)
            
            self.is_fitted = True
        except Exception as e:
            logger.warning(f"Failed to create SHAP explainer: {e}")
            # フォールバックとして、単純な平均値で初期化
            self.explainer = shap.Explainer(lambda x: np.mean(x, axis=1), X)
            self.is_fitted = True
        
        return self
    
    def explain_instance(self, X_instance: np.ndarray) -> np.ndarray:
        """特定インスタンスのSHAP値を計算"""
        if not self.is_fitted:
            raise ValueError("Explainer not fitted yet. Call fit() method first.")
        
        try:
            shap_values = self.explainer.shap_values(X_instance)
            
            # 2次元の場合は最初のクラスのSHAP値を使用
            if len(shap_values.shape) > 1 and shap_values.shape[-1] > 1:
                if len(shap_values.shape) == 2:
                    shap_values = shap_values[:, 0]  # 最初の出力のSHAP値
                else:
                    shap_values = shap_values[0]  # 最初のサンプルのSHAP値
            
            return shap_values
        except Exception as e:
            logger.error(f"Error computing SHAP values: {e}")
            return np.zeros(X_instance.shape[1] if len(X_instance.shape) > 1 else X_instance.shape[0])
    
    def explain_global(self, X: np.ndarray) -> np.ndarray:
        """グローバルなSHAP値を計算"""
        if not self.is_fitted:
            raise ValueError("Explainer not fitted yet. Call fit() method first.")
        
        try:
            shap_values = self.explainer.shap_values(X)
            
            # 平均絶対SHAP値を返す（特徴量の重要度）
            if len(shap_values.shape) > 1:
                return np.mean(np.abs(shap_values), axis=0)
            else:
                return np.abs(shap_values)
        except Exception as e:
            logger.error(f"Error computing global SHAP values: {e}")
            return np.zeros(X.shape[1] if len(X.shape) > 1 else X.shape[0])
    
    def plot_shap_summary(self, X: np.ndarray, feature_names: Optional[List[str]] = None) -> None:
        """SHAPサマープロットの作成"""
        if not self.is_fitted:
            raise ValueError("Explainer not fitted yet. Call fit() method first.")
        
        shap_values = self.explainer.shap_values(X)
        
        if feature_names is None:
            feature_names = [f"Feature_{i}" for i in range(X.shape[1])]
        
        # SHAPのサマープロットを描画
        plt.figure(figsize=(10, 6))
        shap.summary_plot(shap_values, X, feature_names=feature_names, show=False)
        plt.tight_layout()
        plt.show()


class AttentionVisualizer:
    """Attention重みの可視化"""
    
    def __init__(self, model: keras.Model):
        self.model = model
        self.attention_layer = self._find_attention_layer()
    
    def _find_attention_layer(self) -> Optional[keras.layers.Layer]:
        """モデル内のAttention層を検索"""
        for layer in self.model.layers:
            if 'attention' in layer.name.lower() or hasattr(layer, 'compute_output_shape'):
                # カスタムAttention層などを探す
                if hasattr(layer, 'call') or hasattr(layer, '__call__'):
                    return layer
        return None
    
    def get_attention_weights(self, X: np.ndarray) -> Optional[np.ndarray]:
        """Attention重みの取得"""
        if self.attention_layer is None:
            logger.warning("No attention layer found in the model")
            return None
        
        try:
            # Attention重みを取得するための中間層モデルを作成
            # 入力層からAttention層までの中間モデル
            intermediate_model = keras.Model(
                inputs=self.model.input,
                outputs=self.attention_layer.output
            )
            
            # Attention重みを取得
            attention_output = intermediate_model.predict(X)
            
            # Attention重みが含まれる場合（例: MultiHeadAttentionの場合は重みも取得可能）
            # 実際には、特定のAttention層によって出力形式が異なるため、
            # より具体的な処理が必要になる
            return attention_output
        except Exception as e:
            logger.error(f"Error getting attention weights: {e}")
            return None
    
    def visualize_attention(self, X: np.ndarray, head_idx: int = 0) -> None:
        """Attentionマップの可視化"""
        attention_weights = self.get_attention_weights(X)
        
        if attention_weights is not None:
            # 例として、最初のバッチと指定されたヘッドのAttentionを可視化
            if len(attention_weights.shape) == 4:  # [batch, head, time, time]
                weights = attention_weights[0, head_idx, :, :]  # [time, time]
            elif len(attention_weights.shape) == 3:  # [batch, time, features]
                # 観点を変えて可視化（例: 時間方向のAttention）
                weights = attention_weights[0, :, :]  # [time, features]
            else:
                logger.warning(f"Unexpected attention weights shape: {attention_weights.shape}")
                return
            
            plt.figure(figsize=(10, 8))
            sns.heatmap(weights, annot=True, cmap='viridis')
            plt.title(f'Attention Weights Visualization (Head {head_idx})')
            plt.ylabel('Target Position')
            plt.xlabel('Source Position')
            plt.tight_layout()
            plt.show()
    
    def temporal_attention_analysis(self, X: np.ndarray) -> Dict[str, Any]:
        """時間軸に沿ったAttention分析"""
        attention_weights = self.get_attention_weights(X)
        
        if attention_weights is None:
            return {}
        
        analysis = {}
        
        if len(attention_weights.shape) >= 3:
            # 時間軸ごとのAttention強度
            if len(attention_weights.shape) == 4:  # MultiHeadAttention
                # 各ヘッドの平均を取る
                temporal_attention = np.mean(attention_weights, axis=1)  # [batch, time, time]
            else:
                temporal_attention = attention_weights  # [batch, time, features]
            
            # 最初のサンプルについて分析
            sample_attention = temporal_attention[0]
            
            # 時間軸ごとのAttention強度を計算（行方向の平均）
            time_attention_strength = np.mean(sample_attention, axis=-1)  # [time]
            
            analysis = {
                'temporal_attention_strength': time_attention_strength,
                'highest_attention_at': np.argmax(time_attention_strength),
                'attention_distribution': np.std(time_attention_strength)  # Attentionの集中度
            }
        
        return analysis


class LIMEExplainer:
    """LIMEによる説明機能"""
    
    def __init__(self, model: Any, training_data: np.ndarray, mode: str = 'regression'):
        self.model = model
        self.mode = mode
        
        # LIMEエクスプレイナーの初期化
        feature_names = [f"Feature_{i}" for i in range(training_data.shape[1])]
        if mode == 'regression':
            self.explainer = lime.lime_tabular.LimeTabularExplainer(
                training_data,
                feature_names=feature_names,
                mode=mode,
                random_state=42
            )
        else:
            raise ValueError(f"Mode {mode} not supported. Use 'regression'.")
    
    def explain_instance(self, instance: np.ndarray, num_features: int = 10) -> Dict[str, float]:
        """特定インスタンスのLIME説明を取得"""
        try:
            # 1次元配列を2次元に変換
            if len(instance.shape) == 1:
                instance = instance.reshape(1, -1)
            
            # 予測関数のラッパー
            def predict_fn(x):
                # モデルがkerasモデルの場合、予測には2次元が必要
                if isinstance(self.model, keras.Model):
                    return self.model.predict(x).flatten()
                else:
                    return self.model.predict(x)
            
            # 説明の取得
            exp = self.explainer.explain_instance(
                instance[0],  # LIMEは1つのインスタンスを期待
                predict_fn,
                num_features=num_features
            )
            
            # 説明を辞書形式に変換
            explanation_dict = {}
            for feature, weight in exp.as_list():
                # 特徴量名から重みを抽出
                feature_name = feature.split('=')[0].strip()
                explanation_dict[feature_name] = weight
            
            return explanation_dict
        except Exception as e:
            logger.error(f"Error in LIME explanation: {e}")
            return {}

    def plot_lime_explanation(self, instance: np.ndarray, num_features: int = 10) -> None:
        """LIME説明のプロット"""
        try:
            # 1次元配列を2次元に変換
            if len(instance.shape) == 1:
                instance = instance.reshape(1, -1)
            
            # 予測関数のラッパー
            def predict_fn(x):
                if isinstance(self.model, keras.Model):
                    return self.model.predict(x).flatten()
                else:
                    return self.model.predict(x)
            
            exp = self.explainer.explain_instance(
                instance[0],
                predict_fn,
                num_features=num_features
            )
            
            exp.as_pyplot_figure()
            plt.tight_layout()
            plt.show()
        except Exception as e:
            logger.error(f"Error plotting LIME explanation: {e}")


class XAIFramework:
    """XAIフレームワークの統合クラス"""
    
    def __init__(self, model: Any, training_data: np.ndarray):
        self.model = model
        self.training_data = training_data
        self.shap_explainer = None
        self.lime_explainer = None
        self.attention_visualizer = None
        
        # 使用可能なXAI手法を初期化
        self._initialize_xai_methods()
    
    def _initialize_xai_methods(self):
        """XAI手法の初期化"""
        try:
            # SHAP
            self.shap_explainer = SHAPExplainer(self.model)
            self.shap_explainer.fit(self.training_data)
        except Exception as e:
            logger.warning(f"SHAP not available: {e}")
        
        try:
            # LIME
            self.lime_explainer = LIMEExplainer(self.model, self.training_data)
        except Exception as e:
            logger.warning(f"LIME not available: {e}")
        
        try:
            # Attention可視化（Kerasモデルの場合）
            if isinstance(self.model, keras.Model):
                self.attention_visualizer = AttentionVisualizer(self.model)
        except Exception as e:
            logger.warning(f"Attention visualization not available: {e}")
    
    def explain_prediction(
        self, 
        X_instance: np.ndarray, 
        method: str = 'all',
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """予測の説明を取得"""
        explanations = {}
        
        if method in ['shap', 'all'] and self.shap_explainer:
            try:
                shap_values = self.shap_explainer.explain_instance(X_instance)
                explanations['shap'] = {
                    'values': shap_values,
                    'feature_importance': dict(zip(
                        feature_names or [f"Feature_{i}" for i in range(len(shap_values))],
                        shap_values
                    ))
                }
            except Exception as e:
                logger.warning(f"SHAP explanation failed: {e}")
        
        if method in ['lime', 'all'] and self.lime_explainer:
            try:
                lime_explanation = self.lime_explainer.explain_instance(X_instance)
                explanations['lime'] = lime_explanation
            except Exception as e:
                logger.warning(f"LIME explanation failed: {e}")
        
        if method in ['attention', 'all'] and self.attention_visualizer:
            try:
                attention_analysis = self.attention_visualizer.temporal_attention_analysis(X_instance)
                explanations['attention'] = attention_analysis
            except Exception as e:
                logger.warning(f"Attention analysis failed: {e}")
        
        # 予測値も含める
        try:
            if isinstance(self.model, keras.Model):
                prediction = self.model.predict(X_instance).flatten()[0] if len(X_instance.shape) > 1 else self.model.predict(X_instance.reshape(1, -1)).flatten()[0]
            else:
                prediction = self.model.predict(X_instance)[0] if len(X_instance.shape) > 1 else self.model.predict(X_instance.reshape(1, -1))[0]
            explanations['prediction'] = prediction
        except Exception as e:
            logger.warning(f"Prediction failed: {e}")
        
        return explanations
    
    def generate_explanation_report(
        self, 
        X_instance: np.ndarray, 
        feature_names: Optional[List[str]] = None
    ) -> str:
        """説明レポートの生成"""
        explanations = self.explain_prediction(X_instance, 'all', feature_names)
        
        report = []
        report.append("=== XAI Explanation Report ===\n")
        
        if 'prediction' in explanations:
            report.append(f"Prediction: {explanations['prediction']:.4f}\n")
        
        if 'shap' in explanations:
            report.append("SHAP Feature Importance:")
            shap_importance = explanations['shap']['feature_importance']
            sorted_features = sorted(shap_importance.items(), key=lambda x: abs(x[1]), reverse=True)
            for feature, importance in sorted_features[:5]:  # 上位5件
                report.append(f"  {feature}: {importance:.4f}")
            report.append("")
        
        if 'lime' in explanations:
            report.append("LIME Feature Contribution:")
            lime_explanation = explanations['lime']
            sorted_lime = sorted(lime_explanation.items(), key=lambda x: abs(x[1]), reverse=True)
            for feature, contribution in sorted_lime[:5]:  # 上位5件
                report.append(f"  {feature}: {contribution:.4f}")
            report.append("")
        
        if 'attention' in explanations:
            report.append("Attention Analysis:")
            attention_analysis = explanations['attention']
            for key, value in attention_analysis.items():
                report.append(f"  {key}: {value}")
            report.append("")
        
        return "\n".join(report)


# 便利な関数
def create_xai_report(predictor: Any, X: np.ndarray, feature_names: Optional[List[str]] = None) -> str:
    """XAIレポートの作成（ヘルパー関数）"""
    # トレーニングデータとしてXの一部を使用
    n_train = min(100, len(X) // 2)
    X_train = X[:n_train] if len(X) > n_train else X
    
    # XAIフレームワークの初期化
    xai = XAIFramework(predictor, X_train)
    
    # 最新のデータポイントについて説明を生成
    latest_instance = X[-1:] if len(X.shape) == 2 else X[-1].reshape(1, -1)
    
    return xai.generate_explanation_report(latest_instance, feature_names)


if __name__ == "__main__":
    # テスト用コード
    logging.basicConfig(level=logging.INFO)
    
    # シンプルなモデルでテスト
    model = keras.Sequential([
        keras.layers.Dense(10, activation='relu', input_shape=(10,)),
        keras.layers.Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    
    # ダミーデータ
    X = np.random.random((100, 10)).astype(np.float32)
    y = np.random.random((100, 1)).astype(np.float32)
    model.fit(X, y, epochs=1, verbose=0)
    
    # XAIフレームワークのテスト
    xai = XAIFramework(model, X)
    
    # 特定のインスタンスについて説明を取得
    X_instance = X[:1]
    explanations = xai.explain_prediction(X_instance, feature_names=[f"Feature_{i}" for i in range(10)])
    
    print("XAI Explanations:")
    for method, explanation in explanations.items():
        print(f"{method}: {explanation}")
    
    # 説明レポートの生成
    report = xai.generate_explanation_report(X_instance, [f"Feature_{i}" for i in range(10)])
    print("\n" + report)
    
    print("XAI components test completed.")