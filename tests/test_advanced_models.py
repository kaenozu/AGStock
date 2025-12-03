"""
高度なモデルのテスト
"""

from src.advanced_models import AdvancedModels

def test_build_gru_model():
    """GRUモデル構築テスト"""
    input_shape = (30, 10) # sequence_length=30, features=10
    model = AdvancedModels.build_gru_model(input_shape)
    
    assert model is not None
    assert len(model.layers) > 0
    assert model.input_shape == (None, 30, 10)
    assert model.output_shape == (None, 1)

def test_build_attention_lstm_model():
    """Attention-LSTMモデル構築テスト"""
    input_shape = (30, 10)
    model = AdvancedModels.build_attention_lstm_model(input_shape)
    
    assert model is not None
    # AttentionLayerが含まれているか確認
    layer_names = [layer.__class__.__name__ for layer in model.layers]
    assert 'AttentionLayer' in layer_names
    assert model.output_shape == (None, 1)
