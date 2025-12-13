"""
高度な予測モデル

- Attention付きLSTM
- CNN-LSTMハイブリッド
- 多段階予測モデル
- N-BEATSスタイルモデル
"""

import logging
import warnings
from typing import Dict, Optional, Tuple

import lightgbm as lgb
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from tensorflow import keras
from tensorflow.keras import layers

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


class AttentionLayer(layers.Layer):
    """Attentionメカニズムを実装するカスタムレイヤー"""

    def __init__(self, **kwargs):
        super(AttentionLayer, self).__init__(**kwargs)

    def build(self, input_shape):
        self.W = self.add_weight(
            name="attention_weight",
            shape=(input_shape[-1], input_shape[-1]),
            initializer="random_normal",
            trainable=True,
        )
        self.b = self.add_weight(name="attention_bias", shape=(input_shape[-1],), initializer="zeros", trainable=True)
        super(AttentionLayer, self).build(input_shape)

    def call(self, x):
        # Attentionスコアの計算
        e = tf.nn.tanh(tf.tensordot(x, self.W, axes=1) + self.b)
        a = tf.nn.softmax(tf.reduce_sum(e, axis=-1, keepdims=True), axis=1)
        # 元の入力とAttention重みの乗算
        output = x * a
        return output


class AttentionLSTM(keras.Model):
    """Attention付きLSTMモデル"""

    def __init__(
        self, input_dim: int, hidden_dim: int = 50, num_layers: int = 2, dropout: float = 0.2, forecast_horizon: int = 5
    ):
        super(AttentionLSTM, self).__init__()

        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.forecast_horizon = forecast_horizon

        # LSTMレイヤー
        self.lstm_layers = []
        for i in range(num_layers):
            return_sequences = True if i < num_layers - 1 else False
            self.lstm_layers.append(
                layers.LSTM(hidden_dim, return_sequences=return_sequences, dropout=dropout, recurrent_dropout=dropout)
            )

        # Attentionレイヤー
        self.attention = AttentionLayer()

        # フォワード部分
        self.dropout = layers.Dropout(dropout)
        self.dense1 = layers.Dense(50, activation="relu")
        self.dense2 = layers.Dense(forecast_horizon)

    def call(self, x, training=None):
        # LSTM
        for lstm_layer in self.lstm_layers:
            x = lstm_layer(x)

        # Attention
        x = self.attention(x)

        # 平坦化
        x = layers.GlobalMaxPooling1D()(x)

        # ドロップアウトと全結合
        x = self.dropout(x, training=training)
        x = self.dense1(x)
        x = self.dropout(x, training=training)
        x = self.dense2(x)

        return x


class CNNLSTMHybrid(keras.Model):
    """CNN-LSTMハイブリッドモデル"""

    def __init__(
        self,
        input_dim: int,
        cnn_filters: int = 64,
        cnn_kernel_size: int = 3,
        lstm_units: int = 50,
        dropout: float = 0.2,
        forecast_horizon: int = 5,
    ):
        super(CNNLSTMHybrid, self).__init__()

        self.forecast_horizon = forecast_horizon

        # CNN部分
        self.cnn1 = layers.Conv1D(filters=cnn_filters, kernel_size=cnn_kernel_size, activation="relu", padding="same")
        self.cnn2 = layers.Conv1D(filters=cnn_filters, kernel_size=cnn_kernel_size, activation="relu", padding="same")
        self.pool = layers.MaxPooling1D(pool_size=2)
        self.dropout_cnn = layers.Dropout(dropout)

        # LSTM部分
        self.lstm = layers.LSTM(lstm_units, return_sequences=True, dropout=dropout)
        self.lstm2 = layers.LSTM(lstm_units, dropout=dropout)

        # 出力部分
        self.dropout = layers.Dropout(dropout)
        self.dense1 = layers.Dense(50, activation="relu")
        self.dense2 = layers.Dense(forecast_horizon)

    def call(self, x, training=None):
        # CNNで短期パターンを抽出
        x = self.cnn1(x)
        x = self.cnn2(x)
        x = self.pool(x)
        x = self.dropout_cnn(x, training=training)

        # LSTMで長期依存性を学習
        x = self.lstm(x)
        x = self.lstm2(x)

        # 出力層
        x = self.dropout(x, training=training)
        x = self.dense1(x)
        x = self.dropout(x, training=training)
        x = self.dense2(x)

        return x


class MultiStepPredictor(keras.Model):
    """多段階予測モデル"""

    def __init__(
        self, input_dim: int, hidden_dim: int = 50, num_layers: int = 2, dropout: float = 0.2, forecast_horizon: int = 5
    ):
        super(MultiStepPredictor, self).__init__()

        self.forecast_horizon = forecast_horizon
        self.hidden_dim = hidden_dim

        # 共通エンコーダー
        self.lstm_encoder = layers.LSTM(hidden_dim, return_state=True, dropout=dropout)

        # 各ステップのデコーダー
        self.decoders = []
        for _ in range(forecast_horizon):
            decoder_lstm = layers.LSTM(hidden_dim, return_sequences=False, dropout=dropout)
            decoder_dense = layers.Dense(1)
            self.decoders.append((decoder_lstm, decoder_dense))

        self.dropout = layers.Dropout(dropout)

    def call(self, x, training=None):
        # エンコーディング
        encoder_out, state_h, state_c = self.lstm_encoder(x)

        # 各ステップを順次予測
        outputs = []
        current_input = encoder_out  # 最初の入力

        for decoder_lstm, decoder_dense in self.decoders:
            # LSTMデコーディング
            decoder_out = decoder_lstm(current_input[:, tf.newaxis, :])
            # 出力計算
            output = decoder_dense(decoder_out)
            outputs.append(output)

            # 次のステップの入力として使用
            current_input = decoder_out

        # すべてのステップの出力を結合
        return tf.concat(outputs, axis=1)


class NBEATSBlock(layers.Layer):
    """N-BEATSの基本ブロック"""

    def __init__(self, units: int, thetas_dim: int, num_layers: int, **kwargs):
        super().__init__(**kwargs)
        self.units = units
        self.thetas_dim = thetas_dim
        self.num_layers = num_layers

        # FC layers
        self.fc_layers = []
        for _ in range(num_layers):
            self.fc_layers.append(layers.Dense(units, activation="relu"))

        # Thetas出力
        self.theta_fc = layers.Dense(thetas_dim, activation="linear")

        # トレンド/季節性コンポーネント用のベース
        self.backcast_fc = layers.Dense(units, activation="relu")
        self.forecast_fc = layers.Dense(units, activation="relu")

    def call(self, x):
        # Feed forward
        for fc in self.fc_layers:
            x = fc(x)

        # Thetasを計算
        thetas = self.theta_fc(x)

        # BackcastとForecastを計算（簡略化版）
        backcast = self.backcast_fc(thetas)
        forecast = self.forecast_fc(thetas)

        return backcast, forecast


class NBEATS(keras.Model):
    """N-BEATS風の時系列予測モデル"""

    def __init__(
        self,
        input_size: int,
        forecast_size: int = 5,
        stack_types: list = ["trend", "seasonal"],
        num_blocks: int = 2,
        num_layers: int = 4,
        units: int = 32,
    ):
        super(NBEATS, self).__init__()

        self.input_size = input_size
        self.forecast_size = forecast_size
        self.stack_types = stack_types
        self.num_blocks = num_blocks

        # 前処理用Dense layer
        self.preprocess = layers.Dense(units, activation="relu")

        # 各スタック
        self.blocks = []
        for stack_type in stack_types:
            stack_blocks = []
            for _ in range(num_blocks):
                thetas_dim = forecast_size if stack_type == "seasonal" else forecast_size
                block = NBEATSBlock(units=units, thetas_dim=thetas_dim, num_layers=num_layers)
                stack_blocks.append(block)
            self.blocks.append(stack_blocks)

        # 最終出力
        self.output_layer = layers.Dense(forecast_size)

    def call(self, x):
        # 前処理
        x = self.preprocess(x)

        # 各スタックを処理
        forecast = tf.zeros_like(x[:, -self.forecast_size :], dtype=tf.float32)

        for stack_blocks in self.blocks:
            backcast = x
            for block in stack_blocks:
                b, f = block(backcast)
                backcast = backcast - b
                forecast = forecast + f

        # 最終出力
        forecast = self.output_layer(forecast)

        return forecast


class EnhancedLSTM(keras.Model):
    """高度なLSTMアーキテクチャ"""

    def __init__(
        self, input_dim: int, hidden_dim: int = 64, num_layers: int = 3, dropout: float = 0.2, forecast_horizon: int = 5
    ):
        super(EnhancedLSTM, self).__init__()

        self.forecast_horizon = forecast_horizon
        self.num_layers = num_layers

        # LSTM layers with batch normalization
        self.lstm_layers = []
        for i in range(num_layers):
            return_sequences = True if i < num_layers - 1 else False
            lstm_layer = layers.LSTM(
                hidden_dim,
                return_sequences=return_sequences,
                dropout=dropout,
                recurrent_dropout=dropout,
                recurrent_activation="sigmoid",  # Forget gate
                implementation=2,  # CuDNN implementation if available
            )
            self.lstm_layers.append(lstm_layer)

            # Batch normalization after each LSTM (except the last one)
            if return_sequences:
                self.lstm_layers.append(layers.BatchNormalization())

        # Attention layer
        self.attention = AttentionLayer()

        # Output layers
        self.global_avg_pool = layers.GlobalAveragePooling1D()
        self.dropout = layers.Dropout(dropout)
        self.dense1 = layers.Dense(128, activation="relu")
        self.batch_norm = layers.BatchNormalization()
        self.dense2 = layers.Dense(64, activation="relu")
        self.dropout2 = layers.Dropout(dropout)
        self.dense3 = layers.Dense(forecast_horizon)

    def call(self, x, training=None):
        # Pass through LSTM layers
        for i, layer in enumerate(self.lstm_layers):
            if isinstance(layer, layers.BatchNormalization):
                x = layer(x, training=training)
            else:
                x = layer(x)

        # Apply attention
        x = self.attention(x)

        # Global average pooling
        x = self.global_avg_pool(x)

        # Dense layers with dropout and batch norm
        x = self.dropout(x, training=training)
        x = self.dense1(x)
        x = self.batch_norm(x, training=training)
        x = self.dense2(x)
        x = self.dropout2(x, training=training)
        x = self.dense3(x)

        return x


class AdvancedModels:
    """高度な予測モデルのクラス"""

    @staticmethod
    def build_attention_lstm(input_shape: Tuple[int, int], forecast_horizon: int = 5) -> keras.Model:
        """Attention付きLSTMモデルを構築"""
        model = AttentionLSTM(
            input_dim=input_shape[-1], hidden_dim=64, num_layers=2, dropout=0.2, forecast_horizon=forecast_horizon
        )

        model.build(input_shape)

        model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001), loss="mse", metrics=["mae"])

        return model

    @staticmethod
    def build_cnn_lstm(input_shape: Tuple[int, int], forecast_horizon: int = 5) -> keras.Model:
        """CNN-LSTMハイブリッドモデルを構築"""
        model = CNNLSTMHybrid(
            input_dim=input_shape[-1],
            cnn_filters=64,
            cnn_kernel_size=3,
            lstm_units=50,
            dropout=0.2,
            forecast_horizon=forecast_horizon,
        )

        model.build(input_shape)

        model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001), loss="mse", metrics=["mae"])

        return model

    @staticmethod
    def build_multistep_predictor(input_shape: Tuple[int, int], forecast_horizon: int = 5) -> keras.Model:
        """多段階予測モデルを構築"""
        model = MultiStepPredictor(
            input_dim=input_shape[-1], hidden_dim=64, num_layers=2, dropout=0.2, forecast_horizon=forecast_horizon
        )

        model.build(input_shape)

        model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001), loss="mse", metrics=["mae"])

        return model

    @staticmethod
    def build_nbeats(input_shape: Tuple[int, int], forecast_horizon: int = 5) -> keras.Model:
        """N-BEATS風モデルを構築"""
        model = NBEATS(
            input_size=input_shape[-1],
            forecast_size=forecast_horizon,
            stack_types=["trend", "seasonal"],
            num_blocks=2,
            num_layers=4,
            units=32,
        )

        model.build(input_shape)

        model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001), loss="mse", metrics=["mae"])

        return model

    @staticmethod
    def build_enhanced_lstm(input_shape: Tuple[int, int], forecast_horizon: int = 5) -> keras.Model:
        """高度なLSTMモデルを構築"""
        model = EnhancedLSTM(
            input_dim=input_shape[-1], hidden_dim=64, num_layers=3, dropout=0.2, forecast_horizon=forecast_horizon
        )

        model.build(input_shape)

        model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001), loss="mse", metrics=["mae"])

        return model


if __name__ == "__main__":
    # テスト用の実装
    logging.basicConfig(level=logging.INFO)

    # ダミーデータの作成
    batch_size, sequence_length, features = 32, 60, 10
    X = np.random.randn(batch_size, sequence_length, features).astype(np.float32)
    y = np.random.randn(batch_size, 5).astype(np.float32)  # 5ステップ先予測

    # モデルのテスト
    input_shape = (None, sequence_length, features)

    # Attention LSTM
    model1 = AdvancedModels.build_attention_lstm(input_shape, forecast_horizon=5)
    print(f"Attention LSTM params: {model1.count_params():,}")

    # CNN-LSTM
    model2 = AdvancedModels.build_cnn_lstm(input_shape, forecast_horizon=5)
    print(f"CNN-LSTM params: {model2.count_params():,}")

    # Multi-step predictor
    model3 = AdvancedModels.build_multistep_predictor(input_shape, forecast_horizon=5)
    print(f"Multi-step predictor params: {model3.count_params():,}")

    # N-BEATS
    model4 = AdvancedModels.build_nbeats(input_shape, forecast_horizon=5)
    print(f"N-BEATS params: {model4.count_params():,}")

    # Enhanced LSTM
    model5 = AdvancedModels.build_enhanced_lstm(input_shape, forecast_horizon=5)
    print(f"Enhanced LSTM params: {model5.count_params():,}")

    # 学習テスト
    print("Training test...")
    history = model1.fit(X, y, epochs=1, batch_size=16, verbose=1)
    print("Training completed successfully!")
