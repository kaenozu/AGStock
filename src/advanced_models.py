"""
高度な予測モデル

- Attention付きLSTM
- CNN-LSTMハイブリッド
- 多段階予測モデル
- N-BEATSスタイルモデル

遅延読み込み対応版
"""

import logging
import warnings
from typing import Tuple, Optional, Any

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

# TensorFlowの遅延読み込み
_tf = None
_keras = None
_layers = None
TF_AVAILABLE = None


def _ensure_tf():
    """TensorFlowを必要な時に読み込む"""
    global _tf, _keras, _layers, TF_AVAILABLE
    if TF_AVAILABLE is None:
        try:
            from src.utils.lazy_imports import get_tensorflow, get_keras
            _tf = get_tensorflow()
            _keras = get_keras()
            _layers = _keras.layers
            TF_AVAILABLE = True
            logger.debug("TensorFlow loaded successfully")
        except ImportError:
            logger.warning("TensorFlow not available. Advanced models will not be usable.")
            TF_AVAILABLE = False
    return TF_AVAILABLE


def get_tf():
    _ensure_tf()
    return _tf


def get_keras_module():
    _ensure_tf()
    return _keras


def get_layers():
    _ensure_tf()
    return _layers


class AttentionLayer:
    """Attention層（遅延読み込み対応）"""
    
    def __new__(cls, *args, **kwargs):
        if not _ensure_tf():
            raise ImportError("TensorFlow is required for AttentionLayer")
        
        layers = get_layers()
        
        class _AttentionLayer(layers.Layer):
            def __init__(self, units: int, **layer_kwargs):
                super().__init__(**layer_kwargs)
                self.units = units
                self.W = None
                self.b = None
                self.u = None

            def build(self, input_shape):
                tf = get_tf()
                self.W = self.add_weight(
                    name="attention_weight",
                    shape=(input_shape[-1], self.units),
                    initializer="glorot_uniform",
                    trainable=True,
                )
                self.b = self.add_weight(
                    name="attention_bias",
                    shape=(self.units,),
                    initializer="zeros",
                    trainable=True,
                )
                self.u = self.add_weight(
                    name="context_vector",
                    shape=(self.units,),
                    initializer="glorot_uniform",
                    trainable=True,
                )
                super().build(input_shape)

            def call(self, inputs):
                tf = get_tf()
                score = tf.tanh(tf.tensordot(inputs, self.W, axes=1) + self.b)
                attention_weights = tf.nn.softmax(tf.tensordot(score, self.u, axes=1), axis=1)
                context_vector = inputs * tf.expand_dims(attention_weights, -1)
                return tf.reduce_sum(context_vector, axis=1)

            def get_config(self):
                config = super().get_config()
                config.update({"units": self.units})
                return config
        
        return _AttentionLayer(*args, **kwargs)


class AdvancedModels:
    """高度な予測モデル群"""

    def __init__(self):
        self.models = {}

    def build_attention_lstm(
        self, input_shape: Tuple[int, int], lstm_units: int = 64, attention_units: int = 32
    ):
        """Attention付きLSTMモデルを構築"""
        if not _ensure_tf():
            raise ImportError("TensorFlow is required")
        
        keras = get_keras_module()
        layers = get_layers()
        
        inputs = keras.Input(shape=input_shape)
        lstm_out = layers.LSTM(lstm_units, return_sequences=True)(inputs)
        attention_out = AttentionLayer(attention_units)(lstm_out)
        outputs = layers.Dense(1)(attention_out)

        model = keras.Model(inputs, outputs)
        model.compile(optimizer="adam", loss="mse", metrics=["mae"])
        return model

    def build_cnn_lstm(self, input_shape: Tuple[int, int], filters: int = 64, lstm_units: int = 50):
        """CNN-LSTMハイブリッドモデル"""
        if not _ensure_tf():
            raise ImportError("TensorFlow is required")
        
        keras = get_keras_module()
        layers = get_layers()
        
        model = keras.Sequential([
            layers.Conv1D(filters, 3, activation="relu", input_shape=input_shape),
            layers.MaxPooling1D(2),
            layers.LSTM(lstm_units),
            layers.Dense(32, activation="relu"),
            layers.Dense(1),
        ])
        model.compile(optimizer="adam", loss="mse")
        return model

    def build_multi_step_model(self, input_shape: Tuple[int, int], output_steps: int = 5):
        """複数ステップ予測モデル"""
        if not _ensure_tf():
            raise ImportError("TensorFlow is required")
        
        keras = get_keras_module()
        layers = get_layers()
        
        model = keras.Sequential([
            layers.LSTM(64, return_sequences=True, input_shape=input_shape),
            layers.LSTM(32),
            layers.Dense(output_steps),
        ])
        model.compile(optimizer="adam", loss="mse")
        return model

    def build_nbeats_style(self, input_shape: Tuple[int, int], num_blocks: int = 3):
        """N-BEATSスタイルモデル"""
        if not _ensure_tf():
            raise ImportError("TensorFlow is required")
        
        keras = get_keras_module()
        layers = get_layers()
        tf = get_tf()
        
        inputs = keras.Input(shape=input_shape)
        x = layers.Flatten()(inputs)

        for _ in range(num_blocks):
            x = layers.Dense(64, activation="relu")(x)
            x = layers.Dense(64, activation="relu")(x)

        outputs = layers.Dense(1)(x)
        model = keras.Model(inputs, outputs)
        model.compile(optimizer="adam", loss="mse")
        return model


# 後方互換性のためのエクスポート
def create_attention_layer(units: int):
    """Attention層を作成（後方互換性）"""
    return AttentionLayer(units)
