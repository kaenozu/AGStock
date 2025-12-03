"""
メタラーニングのテスト
"""

import pytest
import pandas as pd
import numpy as np
import os
from src.meta_learner import MetaLearner

@pytest.fixture
def sample_data():
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    
    # ベースモデルの予測（少しノイズあり）
    y_true = np.sin(np.arange(100) * 0.1)
    
    pred_a = y_true + np.random.normal(0, 0.1, 100)
    pred_b = y_true + np.random.normal(0, 0.2, 100)
    
    base_preds = pd.DataFrame({
        'ModelA': pred_a,
        'ModelB': pred_b
    }, index=dates)
    
    y = pd.Series(y_true, index=dates)
    
    features = pd.DataFrame({
        'Volatility': np.random.rand(100),
        'RSI': np.random.rand(100) * 100
    }, index=dates)
    
    return base_preds, y, features

def test_meta_learner_flow(sample_data):
    """メタラーニングの学習・予測フローテスト"""
    base_preds, y, features = sample_data
    
    # 学習用とテスト用に分割
    train_size = 80
    
    train_preds = base_preds.iloc[:train_size]
    train_y = y.iloc[:train_size]
    train_feat = features.iloc[:train_size]
    
    test_preds = base_preds.iloc[train_size:]
    test_feat = features.iloc[train_size:]
    
    # モデル初期化
    learner = MetaLearner(model_path="models/test_meta.txt")
    
    # 学習
    learner.train(train_preds, train_y, train_feat)
    assert learner.is_trained
    assert learner.model is not None
    
    # 予測
    final_preds = learner.predict(test_preds, test_feat)
    assert len(final_preds) == len(test_preds)
    assert isinstance(final_preds, pd.Series)
    
    # 保存・ロード確認
    learner.save_model()
    assert os.path.exists("models/test_meta.txt")
    
    new_learner = MetaLearner(model_path="models/test_meta.txt")
    new_learner.load_model()
    assert new_learner.is_trained
    
    # クリーンアップ
    if os.path.exists("models/test_meta.txt"):
        os.remove("models/test_meta.txt")
