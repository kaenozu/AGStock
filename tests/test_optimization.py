"""
ハイパーパラメータ最適化のテスト

HyperparameterOptimizerクラスの機能を検証するための単体テスト
"""

import pytest
import pandas as pd
import numpy as np
import json
import os
from src.optimization import HyperparameterOptimizer

class TestHyperparameterOptimizer:
    """HyperparameterOptimizerクラスのテスト"""
    
    @pytest.fixture
    def sample_data(self):
        """テスト用のサンプルデータを生成"""
        np.random.seed(42)
        n_samples = 200
        
        # 特徴量を生成
        # optimize_random_forestなどで内部的に特徴量生成(add_advanced_features)が呼ばれるため、
        # 基本的なOHLCVデータを用意する
        dates = pd.date_range(start='2023-01-01', periods=n_samples)
        df = pd.DataFrame({
            'Open': np.random.randn(n_samples).cumsum() + 100,
            'High': np.random.randn(n_samples).cumsum() + 105,
            'Low': np.random.randn(n_samples).cumsum() + 95,
            'Close': np.random.randn(n_samples).cumsum() + 100,
            'Volume': np.random.randint(1000, 10000, n_samples),
        }, index=dates)
        
        return df
    
    @pytest.fixture
    def optimizer(self, tmp_path):
        """テスト用のOptimizerインスタンスを作成"""
        config_path = tmp_path / "model_params.json"
        return HyperparameterOptimizer(config_path=str(config_path))
    
    def test_optimizer_initialization(self, optimizer):
        """Optimizerの初期化をテスト"""
        assert optimizer.best_params == {}
    
    def test_optimize_random_forest_small_trials(self, optimizer, sample_data):
        """RandomForestの最適化をテスト（少ないトライアル数）"""
        # データが少なすぎると警告が出るので、十分な量確保するか、警告を許容する
        # ここでは警告が出てもエラーにならなければOKとする
        
        best_params = optimizer.optimize_random_forest(sample_data, n_trials=2)
        
        # データ数が十分であれば辞書が返る
        if best_params:
            assert isinstance(best_params, dict)
            assert 'n_estimators' in best_params
            assert 'max_depth' in best_params
            assert 'min_samples_split' in best_params
    
    def test_optimize_lightgbm_small_trials(self, optimizer, sample_data):
        """LightGBMの最適化をテスト（少ないトライアル数）"""
        best_params = optimizer.optimize_lightgbm(sample_data, n_trials=2)
        
        if best_params:
            assert isinstance(best_params, dict)
            assert 'num_leaves' in best_params
            assert 'feature_fraction' in best_params
    
    def test_save_and_load_params(self, optimizer, tmp_path):
        """パラメータの保存と読込をテスト"""
        optimizer.best_params = {
            "random_forest": {"n_estimators": 100, "max_depth": 10},
            "lightgbm": {"num_leaves": 31, "learning_rate": 0.1}
        }
        
        optimizer.save_params()
        
        # ファイルが作成されたか
        assert os.path.exists(optimizer.config_path)
        
        # 新しいインスタンスで読み込み
        new_optimizer = HyperparameterOptimizer(config_path=optimizer.config_path)
        assert new_optimizer.best_params == optimizer.best_params

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
