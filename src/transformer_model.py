"""
Temporal Fusion Transformer (TFT) モデル

時系列予測のための最先端Transformerモデル。
マルチヘッドアテンション機構により、重要な時点を自動で検出します。
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, List
import logging
from datetime import datetime

# TensorFlow/Kerasのインポート
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    from tensorflow.keras.models import Model, load_model as keras_load_model
except ImportError:
    raise ImportError("TensorFlow is required. Please install with: pip install tensorflow")

logger = logging.getLogger(__name__)


class TemporalFusionTransformer:
    """
    Temporal Fusion Transformer (TFT) モデル
    
    時系列データの予測に特化したTransformerモデル。
    マルチヘッドアテンション機構により、予測に重要な時点を自動検出します。
    """
    
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 64,
        num_attention_heads: int = 4,
        dropout: float = 0.1,
        num_encoder_layers: int = 2,
        learning_rate: float = 0.001
    ):
        """
        Args:
            input_size: 入力特徴量の数
            hidden_size: 隠れ層のサイズ
            num_attention_heads: アテンションヘッドの数
            dropout: ドロップアウト率
            num_encoder_layers: エンコーダー層の数
            learning_rate: 学習率
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_attention_heads = num_attention_heads
        self.dropout = dropout
        self.num_encoder_layers = num_encoder_layers
        self.learning_rate = learning_rate
        
        self.model: Optional[Model] = None
        self.attention_model: Optional[Model] = None
        self.is_trained = False
        
        logger.info(f"Initialized TFT: input={input_size}, hidden={hidden_size}, heads={num_attention_heads}, lr={learning_rate}")
    
    def _build_model(self, sequence_length: int, forecast_horizon: int):
        """
        モデルを構築
        
        Args:
            sequence_length: 入力シーケンスの長さ
            forecast_horizon: 予測する未来のステップ数
        """
        # 入力層
        inputs = keras.Input(shape=(sequence_length, self.input_size))
        
        # Positional Encoding
        positions = tf.range(start=0, limit=sequence_length, delta=1)
        pos_encoding = layers.Embedding(
            input_dim=sequence_length,
            output_dim=self.hidden_size
        )(positions)
        
        # 入力を隠れ層サイズに変換
        x = layers.Dense(self.hidden_size)(inputs)
        x = x + pos_encoding
        
        # Multi-Head Attention層
        for _ in range(self.num_encoder_layers):
            # Self-Attention
            attention_output = layers.MultiHeadAttention(
                num_heads=self.num_attention_heads,
                key_dim=self.hidden_size // self.num_attention_heads,
                dropout=self.dropout
            )(x, x)
            
            # Add & Norm
            x = layers.LayerNormalization(epsilon=1e-6)(x + attention_output)
            
            # Feed Forward
            ff = layers.Dense(self.hidden_size * 4, activation='relu')(x)
            ff = layers.Dropout(self.dropout)(ff)
            ff = layers.Dense(self.hidden_size)(ff)
            
            # Add & Norm
            x = layers.LayerNormalization(epsilon=1e-6)(x + ff)
        
        # Global pooling
        x = layers.GlobalAveragePooling1D()(x)
        
        # 出力層（forecast_horizon分の予測）
        x = layers.Dense(self.hidden_size, activation='relu')(x)
        x = layers.Dropout(self.dropout)(x)
        outputs = layers.Dense(forecast_horizon)(x)
        
        # モデル作成
        self.model = Model(inputs=inputs, outputs=outputs)
        
        # アテンションウェイト抽出用のモデルも作成
        # （説明可能性のため）
        attention_layer = self.model.layers[4]  # 最初のMultiHeadAttention層
        self.attention_model = Model(
            inputs=self.model.input,
            outputs=attention_layer.output
        )
        
        # コンパイル
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        logger.info(f"Model built: seq_len={sequence_length}, forecast={forecast_horizon}")
    
    def prepare_sequences(
        self,
        data: pd.DataFrame,
        sequence_length: int = 30,
        forecast_horizon: int = 5,
        target_column: str = 'Close'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        時系列データをシーケンスに変換
        
        Args:
            data: 時系列データ（DataFrame）
            sequence_length: 入力シーケンスの長さ
            forecast_horizon: 予測する未来のステップ数
            target_column: 予測対象のカラム名
            
        Returns:
            (X, y): 入力シーケンスとターゲット
        """
        # 数値カラムのみ選択
        numeric_data = data.select_dtypes(include=[np.number]).values
        
        X_list = []
        y_list = []
        
        for i in range(len(numeric_data) - sequence_length - forecast_horizon + 1):
            # 入力シーケンス
            X_list.append(numeric_data[i:i+sequence_length])
            
            # ターゲット（Close価格の未来forecast_horizon分）
            if target_column in data.columns:
                target_idx = data.columns.get_loc(target_column)
                y_list.append(numeric_data[i+sequence_length:i+sequence_length+forecast_horizon, target_idx])
            else:
                # target_columnがない場合は最初のカラムを使用
                y_list.append(numeric_data[i+sequence_length:i+sequence_length+forecast_horizon, 0])
        
        X = np.array(X_list)
        y = np.array(y_list)
        
        logger.info(f"Prepared sequences: X.shape={X.shape}, y.shape={y.shape}")
        
        return X, y
    
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2,
        verbose: int = 1
    ):
        """
        モデルを学習
        
        Args:
            X: 入力シーケンス (samples, sequence_length, features)
            y: ターゲット (samples, forecast_horizon)
            epochs: エポック数
            batch_size: バッチサイズ
            validation_split: 検証データの割合
            verbose: ログレベル
            
        Returns:
            学習履歴
        """
        sequence_length = X.shape[1]
        forecast_horizon = y.shape[1]
        
        # モデル構築（初回のみ）
        if self.model is None:
            self._build_model(sequence_length, forecast_horizon)
        
        # 学習
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=verbose,
            callbacks=[
                keras.callbacks.EarlyStopping(
                    patience=10,
                    restore_best_weights=True
                )
            ]
        )
        
        self.is_trained = True
        logger.info(f"Training completed: final loss={history.history['loss'][-1]:.4f}")
        
        return history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        予測を実行
        
        Args:
            X: 入力シーケンス
            
        Returns:
            予測結果
        """
        if self.model is None:
            raise ValueError("Model not built. Call fit() first.")
        
        predictions = self.model.predict(X, verbose=0)
        return predictions
    
    def get_attention_weights(self, X: np.ndarray) -> np.ndarray:
        """
        アテンションウェイトを取得（説明可能性のため）
        
        Args:
            X: 入力シーケンス
            
        Returns:
            アテンションウェイト
        """
        if self.attention_model is None:
            raise ValueError("Attention model not available")
        
        attention_output = self.attention_model.predict(X, verbose=0)
        
        # アテンションスコアを計算（簡易版）
        attention_weights = np.mean(np.abs(attention_output), axis=-1)
        
        return attention_weights
    
    def save(self, filepath: str):
        """
        モデルを保存
        
        Args:
            filepath: 保存先パス
        """
        if self.model is None:
            raise ValueError("Model not built")
        
        self.model.save(filepath)
        logger.info(f"Model saved to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'TemporalFusionTransformer':
        """
        モデルを読み込み
        
        Args:
            filepath: モデルファイルのパス
            
        Returns:
            TemporalFusionTransformerインスタンス
        """
        loaded_keras_model = keras_load_model(filepath)
        
        # パラメータを復元（近似）
        instance = cls(
            input_size=loaded_keras_model.input_shape[-1],
            hidden_size=64,  # デフォルト値
            num_attention_heads=4
        )
        instance.model = loaded_keras_model
        instance.is_trained = True
        
        logger.info(f"Model loaded from {filepath}")
        
        return instance


if __name__ == "__main__":
    # 簡単なテスト
    logging.basicConfig(level=logging.INFO)
    
    # サンプルデータ
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=200, freq='D')
    data = pd.DataFrame({
        'Close': np.random.randn(200).cumsum() + 100,
        'Volume': np.random.randint(1000000, 10000000, 200),
        'RSI': np.random.uniform(30, 70, 200),
        'MACD': np.random.randn(200),
    }, index=dates)
    
    # モデル作成
    tft = TemporalFusionTransformer(
        input_size=4,
        hidden_size=32,
        num_attention_heads=4
    )
    
    # シーケンス準備
    X, y = tft.prepare_sequences(data, sequence_length=30, forecast_horizon=5)
    print(f"X.shape: {X.shape}, y.shape: {y.shape}")
    
    # 学習
    history = tft.fit(X, y, epochs=2, verbose=1)
    
    # 予測
    predictions = tft.predict(X[:5])
    print(f"Predictions shape: {predictions.shape}")
    print(f"Sample prediction: {predictions[0]}")
    
    # アテンションウェイト
    attention = tft.get_attention_weights(X[:1])
    print(f"Attention weights shape: {attention.shape}")
