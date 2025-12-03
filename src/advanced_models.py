"""
高度な深層学習モデル

GRU (Gated Recurrent Unit) と Attention-LSTM モデルを提供します。
"""

from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, LSTM, GRU, Dropout, Layer, Bidirectional
import tensorflow.keras.backend as K
import logging

logger = logging.getLogger(__name__)


class AttentionLayer(Layer):
    """
    Bahdanau Attention Layer
    """
    def __init__(self, **kwargs):
        super(AttentionLayer, self).__init__(**kwargs)

    def build(self, input_shape):
        self.W = self.add_weight(name='attention_weight',
                                 shape=(input_shape[-1], 1),
                                 initializer='normal',
                                 trainable=True)
        self.b = self.add_weight(name='attention_bias',
                                 shape=(input_shape[1], 1),
                                 initializer='zeros',
                                 trainable=True)
        super(AttentionLayer, self).build(input_shape)

    def call(self, x):
        # e = tanh(dot(x, W) + b)
        e = K.tanh(K.dot(x, self.W) + self.b)
        # a = softmax(e)
        a = K.softmax(e, axis=1)
        # output = x * a
        output = x * a
        # sum over time steps
        return K.sum(output, axis=1)


class AdvancedModels:
    """高度なモデル構築クラス"""
    
    @staticmethod
    def build_gru_model(
        input_shape: tuple,
        hidden_size: int = 64,
        dropout: float = 0.2
    ) -> Model:
        """
        GRUモデルを構築
        """
        inputs = Input(shape=input_shape)
        
        x = GRU(hidden_size, return_sequences=True)(inputs)
        x = Dropout(dropout)(x)
        x = GRU(hidden_size // 2, return_sequences=False)(x)
        x = Dropout(dropout)(x)
        
        outputs = Dense(1)(x)
        
        model = Model(inputs=inputs, outputs=outputs)
        model.compile(optimizer='adam', loss='mse')
        return model
    
    @staticmethod
    def build_attention_lstm_model(
        input_shape: tuple,
        hidden_size: int = 64,
        dropout: float = 0.2
    ) -> Model:
        """
        Attention付きLSTMモデルを構築
        """
        inputs = Input(shape=input_shape)
        
        # Bidirectional LSTM
        x = Bidirectional(LSTM(hidden_size, return_sequences=True))(inputs)
        x = Dropout(dropout)(x)
        
        # Attention Mechanism
        x = AttentionLayer()(x)
        
        x = Dense(32, activation='relu')(x)
        x = Dropout(dropout)(x)
        outputs = Dense(1)(x)
        
        model = Model(inputs=inputs, outputs=outputs)
        model.compile(optimizer='adam', loss='mse')
        return model
