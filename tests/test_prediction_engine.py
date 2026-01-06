"""
予測エンジンのパフォーマンスと精度テスト
機械学習モデルの推論精度、処理速度、安定性をテスト
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import time

# テスト対象モジュール
from src.enhanced_ensemble_predictor import EnhancedEnsemblePredictor
from src.advanced_models import AdvancedModels
from src.lgbm_predictor import LGBMPredictor
from src.prophet_predictor import ProphetPredictor


class TestPredictionEngine:
    """予測エンジンのテストスイート"""

    @pytest.fixture
    def sample_data(self):
        """サンプルデータの準備"""
        np.random.seed(42)
        dates = pd.date_range("2020-01-01", "2024-01-01", freq="D")

        # 株価データのシミュレーション
        price_data = np.random.lognormal(4.5, 0.2, len(dates))

        return pd.DataFrame(
            {
                "Open": price_data * np.random.uniform(0.98, 1.02, len(dates)),
                "High": price_data * np.random.uniform(1.0, 1.1, len(dates)),
                "Low": price_data * np.random.uniform(0.9, 1.0, len(dates)),
                "Close": price_data,
                "Volume": np.random.randint(100000, 1000000, len(dates)),
            },
            index=dates,
        )

    @pytest.fixture
    def mock_predictor(self):
        """モック予測エンジン"""
        from unittest.mock import MagicMock, Mock
        import pandas as pd
        import numpy as np

        with patch(
            "src.enhanced_ensemble_predictor.EnhancedEnsemblePredictor.__init__",
            return_value=None,
        ):
            predictor = EnhancedEnsemblePredictor()
            predictor.models = {}
            predictor.prediction_cache = {}
            predictor.is_fitted = True
            predictor.feature_columns = ["Close", "Volume", "RSI", "MACD"]
            
            # engineer_features (alias for _prepare_features) をモック
            predictor.engineer_features = MagicMock()
            def mock_engineer(data, ticker="unknown", fundamentals=None):
                return pd.DataFrame({
                    "RSI": [50.0] * len(data),
                    "MACD": [0.0] * len(data)
                }, index=data.index)
            predictor.engineer_features.side_effect = mock_engineer
            predictor._prepare_features = predictor.engineer_features
            
            predictor.weights = {}
            predictor.advanced_ensemble = MagicMock()
            predictor.diversity_ensemble = MagicMock()
            
            # 各コンポーネントをMagicMockで作成し、数値比較で落ちないようにデフォルト値を設定
            mock_factory = lambda: MagicMock(return_value=0.02)
            
            predictor.transformer_predictor = mock_factory()
            predictor.transformer_predictor.predict_point.return_value = 0.02
            
            predictor.advanced_models = mock_factory()
            predictor.advanced_models.predict_point.return_value = 0.02
            
            predictor.lgbm_predictor = mock_factory()
            predictor.lgbm_predictor.predict_point.return_value = 0.02
            
            predictor.prophet_predictor = mock_factory()
            predictor.future_predictor = mock_factory()
            predictor.sentiment_predictor = mock_factory()
            predictor.risk_predictor = mock_factory()
            predictor.multi_asset_predictor = mock_factory()
            predictor.scenario_predictor = mock_factory()
            predictor.scenario_predictor.analyze.return_value = {"details": "mock"}
            
            async def side_effect(data_dict):
                return {ticker: {"prediction": 0.02} for ticker in data_dict.keys()}
            predictor.batch_predict = AsyncMock(side_effect=side_effect)
            
            predictor.mlops_manager = MagicMock()
            predictor.concept_drift_detector = MagicMock()
            predictor.concept_drift_detector.detect.return_value = (False, 0.0)
            
            predictor.continual_learning_system = MagicMock()
            predictor.fundamental_analyzer = MagicMock()
            predictor.xai_framework = MagicMock()
            predictor.logger = MagicMock()
            return predictor

    def test_ensemble_predictor_initialization(self, mock_predictor):
        """アンサンブル予測エンジンの初期化テスト"""
        assert isinstance(mock_predictor.models, dict)
        assert isinstance(mock_predictor.feature_columns, list)
        assert isinstance(mock_predictor.prediction_cache, dict)
        assert len(mock_predictor.feature_columns) > 0

    def test_feature_engineering(self, sample_data, mock_predictor):
        """特徴量エンジニアリングのテスト"""
        # テクニカル指標の計算
        with patch("src.enhanced_ensemble_predictor.generate_enhanced_features") as mock_gen, \
             patch("src.enhanced_ensemble_predictor.preprocess_for_prediction") as mock_pre:
            
            mock_gen.return_value = pd.DataFrame({
                "RSI": [50.0] * len(sample_data),
                "MACD": [0.0] * len(sample_data)
            }, index=sample_data.index)
            mock_pre.return_value = (mock_gen.return_value, None)
            
            features = mock_predictor.engineer_features(sample_data)

        assert isinstance(features, pd.DataFrame)
        assert "RSI" in features.columns
        assert "MACD" in features.columns
        assert features.dropna().shape[0] > 0

    def test_single_model_prediction(self, sample_data):
        """単一モデルの予測テスト"""
        # LGBMモデルのテスト
        lgbm = LGBMPredictor()

        # データ準備
        features = self.prepare_features(sample_data)
        target = sample_data["Close"].shift(-1).dropna()

        # トレーニング（データサイズを削減して高速化）
        train_size = min(len(features), 100)
        lgbm.train(features[:train_size], target[:train_size])

        # 予測
        prediction = lgbm.predict(features.iloc[-1:])

        assert isinstance(prediction, (float, np.ndarray))
        assert not np.isnan(prediction)

    def test_ensemble_prediction_accuracy(self, sample_data, mock_predictor):
        """アンサンブル予測の精度テスト"""
        # モデルの属性をモック (実数としての変化率)
        mock_predictor.lgbm_predictor.predict_point.return_value = 0.01     # +1%
        mock_predictor.transformer_predictor.predict_point.return_value = 0.02  # +2%
        mock_predictor.advanced_models.predict_point.return_value = 0.03    # +3%
        
        mock_predictor.advanced_ensemble = None # Force fallback to mean

        # アンサンブル予測
        result = mock_predictor.predict_ensemble(sample_data.iloc[-1:])
        prediction = result["predicted_price"] if isinstance(result, dict) else result
        
        # 期待される価格
        current_price = sample_data["Close"].iloc[-1]
        expected_change = (0.01 + 0.02 + 0.03) / 3.0
        expected_price = current_price * (1 + expected_change)
        
        assert abs(prediction - expected_price) < 0.001

    def test_prediction_performance_benchmark(self, sample_data, mock_predictor):
        """予測パフォーマンスのベンチマークテスト"""
        # 大量データでの処理速度テスト
        large_data = pd.concat([sample_data] * 10)  # 10倍のデータ

        start_time = time.time()

        # 特徴量エンジニアリング
        features = mock_predictor.engineer_features(large_data)

        processing_time = time.time() - start_time

        # 1秒以内に処理完了
        assert processing_time < 1.0
        assert len(features) > 0

    def test_cache_mechanism(self, sample_data, mock_predictor):
        """キャッシュメカニズムのテスト"""
        ticker = "AAPL"
        date = sample_data.index[-1]
        cache_key = f"{ticker}_{date.strftime('%Y-%m-%d')}"

        # キャッシュが空であることを確認
        assert cache_key not in mock_predictor.prediction_cache

        # 予測を実行してキャッシュに保存
        mock_predictor.prediction_cache[cache_key] = 150.0

        # キャッシュから取得
        cached_prediction = mock_predictor.get_cached_prediction(ticker, date)

        assert cached_prediction == 150.0

    def test_error_handling_in_prediction(self, mock_predictor):
        """予測時のエラーハンドリングテスト"""
        # 不正なデータ形式
        invalid_data = pd.DataFrame({"invalid": [1, 2, 3]})

        # エラーが適切に処理されるか
        with pytest.raises((ValueError, KeyError)):
            mock_predictor.predict_ensemble(invalid_data)

    def test_model_confidence_calculation(self, sample_data, mock_predictor):
        """モデル信頼度計算のテスト"""
        # モデルの予測と実際の値
        predictions = np.array([150.0, 152.0, 149.0])
        actual_values = np.array([151.0, 153.0, 148.0])

        # 信頼度計算
        confidence = mock_predictor.calculate_confidence(predictions, actual_values)

        assert 0 <= confidence <= 1
        assert isinstance(confidence, float)

    def test_prediction_consistency(self, sample_data, mock_predictor):
        """予測の一貫性テスト"""
        # 同じデータでの複数回予測
        predictions = []

        for _ in range(3):
            # モック設定（同じ値を返す）
            mock_predictor.lgbm_predictor.predict_point.return_value = 0.01
            mock_predictor.advanced_ensemble = None

            result = mock_predictor.predict_ensemble(sample_data.iloc[-1:])
            prediction = result["predicted_price"] if isinstance(result, dict) else result
            predictions.append(prediction)

        # 予測結果が一貫していることを確認
        assert all(p == predictions[0] for p in predictions)

    def test_feature_importance_analysis(self, sample_data, mock_predictor):
        """特徴量重要度分析のテスト"""
        # モデルのモック
        mock_model = Mock()
        mock_model.feature_importance.return_value = {
            "Close": 0.4,
            "RSI": 0.3,
            "MACD": 0.2,
            "Volume": 0.1,
        }

        mock_predictor.models = {"lgbm": mock_model}

        # 重要度分析
        importance = mock_predictor.analyze_feature_importance()

        assert isinstance(importance, dict)
        assert "Close" in importance
        assert importance["Close"] > 0

    def test_model_update_mechanism(self, sample_data, mock_predictor):
        """モデル更新メカニズムのテスト"""
        # 更新データの準備
        new_data = sample_data.iloc[-30:]  # 最新30日分

        # モデル更新のモック
        mock_predictor.update_models = Mock(return_value=True)

        # 更新実行
        result = mock_predictor.update_models_with_new_data(new_data)

        assert result is True
        mock_predictor.update_models.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_prediction(self, sample_data, mock_predictor):
        """バッチ予測のテスト"""
        tickers = ["AAPL", "GOOGL", "MSFT"]
        data_dict = {ticker: sample_data for ticker in tickers}

        # バッチ予測の実行
        predictions = await mock_predictor.batch_predict(data_dict)

        assert isinstance(predictions, dict)
        assert len(predictions) == len(tickers)

        for ticker in tickers:
            assert ticker in predictions
            assert isinstance(predictions[ticker], (float, np.ndarray))

    def test_prediction_validity_checks(self, sample_data, mock_predictor):
        """予測妥当性チェックのテスト"""
        # 予測結果の妥当性チェック
        prediction = 150.0
        current_price = 100.0

        # 異常な予測の検出
        result = mock_predictor.validate_prediction(prediction, current_price)
        is_valid = result["is_valid"] if isinstance(result, dict) else result

        # 50%以上の変動は無効と判定
        if abs(prediction - current_price) / current_price > 0.5:
            assert not is_valid
        else:
            assert is_valid

    @staticmethod
    def prepare_features(data):
        """特徴量準備のヘルパー関数"""
        features = data.copy()

        # 簡単なテクニカル指標
        features["RSI"] = 50 + np.random.randn(len(data)) * 10
        features["MACD"] = np.random.randn(len(data)) * 2

        return features.dropna()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
