"""
Transformerモデルのテスト（TDD）

テスト駆動開発でTransformerモデルを実装します。
まずテストを書き、その後に実装を進めます。
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class TestTemporalFusionTransformer:
    """TemporalFusionTransformerクラスのテスト"""
    
    @pytest.fixture
    def sample_timeseries_data(self):
        """テスト用の時系列データを生成"""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=200, freq='D')
        
        df = pd.DataFrame({
            'Close': np.random.randn(200).cumsum() + 100,
            'Volume': np.random.randint(1000000, 10000000, 200),
            'RSI': np.random.uniform(30, 70, 200),
            'MACD': np.random.randn(200),
        }, index=dates)
        
        return df
    
    @pytest.fixture
    def tft_model(self):
        """テスト用のTFTモデルインスタンスを作成"""
        from src.transformer_model import TemporalFusionTransformer
        
        model = TemporalFusionTransformer(
            input_size=4,
            hidden_size=32,
            num_attention_heads=4,
            dropout=0.1
        )
        return model
    
    def test_model_initialization(self, tft_model):
        """モデルの初期化をテスト"""
        assert tft_model is not None
        assert tft_model.input_size == 4
        assert tft_model.hidden_size == 32
        assert tft_model.num_attention_heads == 4
        assert tft_model.dropout == 0.1
    
    def test_prepare_sequences(self, tft_model, sample_timeseries_data):
        """時系列データのシーケンス準備をテスト"""
        X, y = tft_model.prepare_sequences(
            sample_timeseries_data,
            sequence_length=30,
            forecast_horizon=5
        )
        
        # シーケンスが正しく作成されているか
        assert X is not None
        assert y is not None
        assert len(X.shape) == 3  # (samples, sequence_length, features)
        assert len(y.shape) == 2  # (samples, forecast_horizon)
        assert X.shape[1] == 30  # sequence_length
        assert y.shape[1] == 5   # forecast_horizon
    
    def test_model_training(self, tft_model, sample_timeseries_data):
        """モデルの学習をテスト"""
        # シーケンス準備
        X, y = tft_model.prepare_sequences(
            sample_timeseries_data,
            sequence_length=30,
            forecast_horizon=5
        )
        
        # 学習（エポック数を少なくして高速化）
        history = tft_model.fit(
            X, y,
            epochs=2,
            batch_size=32,
            validation_split=0.2,
            verbose=0
        )
        
        # 学習履歴が記録されているか
        assert history is not None
        assert 'loss' in history.history
        assert len(history.history['loss']) == 2  # 2エポック
    
    def test_model_prediction(self, tft_model, sample_timeseries_data):
        """モデルの予測をテスト"""
        # シーケンス準備
        X, y = tft_model.prepare_sequences(
            sample_timeseries_data,
            sequence_length=30,
            forecast_horizon=5
        )
        
        # 学習
        tft_model.fit(X, y, epochs=1, batch_size=32, verbose=0)
        
        # 予測
        predictions = tft_model.predict(X[:10])
        
        # 予測結果の形状が正しいか
        assert predictions is not None
        assert len(predictions.shape) == 2
        assert predictions.shape[0] == 10  # 10サンプル
        assert predictions.shape[1] == 5   # 5ステップ先まで予測
    
    def test_attention_weights(self, tft_model, sample_timeseries_data):
        """アテンションウェイトの取得をテスト（説明可能性）"""
        # シーケンス準備
        X, y = tft_model.prepare_sequences(
            sample_timeseries_data,
            sequence_length=30,
            forecast_horizon=5
        )
        
        # 学習
        tft_model.fit(X, y, epochs=1, batch_size=32, verbose=0)
        
        # アテンションウェイトを取得
        attention_weights = tft_model.get_attention_weights(X[:1])
        
        # アテンションウェイトが取得できるか
        assert attention_weights is not None
        assert len(attention_weights.shape) >= 2
        
        # ウェイトの合計が1に近いか（ソフトマックス後）
        assert np.abs(attention_weights.sum() - X.shape[1]) < 1e-5
    
    def test_model_save_and_load(self, tft_model, sample_timeseries_data, tmp_path):
        """モデルの保存と読み込みをテスト"""
        # シーケンス準備と学習
        X, y = tft_model.prepare_sequences(
            sample_timeseries_data,
            sequence_length=30,
            forecast_horizon=5
        )
        tft_model.fit(X, y, epochs=1, batch_size=32, verbose=0)
        
        # 元の予測
        original_predictions = tft_model.predict(X[:5])
        
        # モデル保存
        model_path = tmp_path / "tft_model.h5"
        tft_model.save(str(model_path))
        
        # ファイルが作成されたか
        assert model_path.exists()
        
        # モデル読み込み
        from src.transformer_model import TemporalFusionTransformer
        loaded_model = TemporalFusionTransformer.load(str(model_path))
        
        # 読み込んだモデルで予測
        loaded_predictions = loaded_model.predict(X[:5])
        
        # 予測結果が一致するか
        np.testing.assert_array_almost_equal(
            original_predictions,
            loaded_predictions,
            decimal=5
        )


class TestTransformerStrategy:
    """TransformerStrategyクラスのテスト"""
    
    @pytest.fixture
    def sample_stock_data(self):
        """テスト用の株価データを生成"""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=200, freq='D')
        
        df = pd.DataFrame({
            'Open': np.random.randn(200).cumsum() + 100,
            'High': np.random.randn(200).cumsum() + 102,
            'Low': np.random.randn(200).cumsum() + 98,
            'Close': np.random.randn(200).cumsum() + 100,
            'Volume': np.random.randint(1000000, 10000000, 200)
        }, index=dates)
        
        return df
    
    def test_strategy_initialization(self):
        """TransformerStrategyの初期化をテスト"""
        from src.strategies import TransformerStrategy
        
        strategy = TransformerStrategy(name="TFT_Strategy")
        
        assert strategy is not None
        assert strategy.name == "TFT_Strategy"
        assert hasattr(strategy, 'model')
    
    def test_strategy_generate_signal(self, sample_stock_data):
        """シグナル生成をテスト"""
        from src.strategies import TransformerStrategy
        
        strategy = TransformerStrategy(name="TFT_Strategy")
        
        # シグナル生成（学習済みモデルがない場合はHOLD）
        signal = strategy.generate_signal(sample_stock_data)
        
        assert signal in ['BUY', 'SELL', 'HOLD']
    
    def test_strategy_train_and_predict(self, sample_stock_data):
        """学習と予測のワークフローをテスト"""
        from src.strategies import TransformerStrategy
        
        strategy = TransformerStrategy(name="TFT_Strategy")
        
        # 学習
        strategy.train(sample_stock_data)
        
        # 予測
        signal = strategy.generate_signal(sample_stock_data)
        
        # 学習後はBUYまたはSELLが返る可能性がある
        assert signal in ['BUY', 'SELL', 'HOLD']
    
    def test_strategy_confidence_score(self, sample_stock_data):
        """信頼度スコアの計算をテスト"""
        from src.strategies import TransformerStrategy
        
        strategy = TransformerStrategy(name="TFT_Strategy")
        strategy.train(sample_stock_data)
        
        # 信頼度取得
        signal = strategy.generate_signal(sample_stock_data)
        confidence = strategy.get_confidence()
        
        # 信頼度が0-1の範囲か
        assert 0.0 <= confidence <= 1.0


class TestTransformerIntegration:
    """Transformer統合テスト"""
    
    def test_ensemble_with_transformer(self):
        """アンサンブル戦略へのTransformer統合をテスト"""
        from src.strategies import CombinedStrategy, TransformerStrategy
        
        # Transformerを含むアンサンブル
        ensemble = CombinedStrategy(
            strategies=[
                TransformerStrategy(name="TFT"),
            ],
            voting_method='weighted'
        )
        
        assert ensemble is not None
        assert len(ensemble.strategies) >= 1
    
    def test_transformer_performance_metrics(self, tmp_path):
        """パフォーマンスメトリクスの計算をテスト"""
        # 実装後にテストを追加
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
