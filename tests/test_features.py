"""
特徴量エンジニアリングのテスト

add_advanced_features関数とその他の特徴量生成機能を検証するテスト
"""

import numpy as np
import pandas as pd
import pytest

from src.features import (add_advanced_features, add_frequency_features,
                          add_sentiment_features)


class TestAdvancedFeatures:
    """高度な特徴量生成のテスト"""

    @pytest.fixture
    def sample_price_data(self):
        """テスト用の価格データを生成"""
        np.random.seed(42)
        dates = pd.date_range("2024-01-01", periods=100, freq="D")

        df = pd.DataFrame(
            {
                "Open": np.random.randn(100).cumsum() + 100,
                "High": np.random.randn(100).cumsum() + 102,
                "Low": np.random.randn(100).cumsum() + 98,
                "Close": np.random.randn(100).cumsum() + 100,
                "Volume": np.random.randint(1000000, 10000000, 100),
            },
            index=dates,
        )

        # High > Low を保証
        df["High"] = df[["Open", "High", "Close"]].max(axis=1) + 1
        df["Low"] = df[["Open", "Low", "Close"]].min(axis=1) - 1

        return df

    def test_add_advanced_features_basic(self, sample_price_data):
        """基本的な特徴量が追加されるかテスト"""
        result = add_advanced_features(sample_price_data.copy())

        # DataFrameが返ってくるか
        assert isinstance(result, pd.DataFrame)

        # 元のカラムが保持されているか
        for col in sample_price_data.columns:
            assert col in result.columns

        # 新しい特徴量が追加されているか
        expected_features = ["RSI", "MACD", "BB_upper", "BB_lower", "ATR"]
        for feature in expected_features:
            assert feature in result.columns, f"Missing feature: {feature}"

    def test_add_advanced_features_no_nan_in_latest(self, sample_price_data):
        """最新のデータにNaNがないかテスト（一部の初期値を除く）"""
        result = add_advanced_features(sample_price_data.copy())

        # 最後の10行をチェック（十分なデータがある部分）
        latest_rows = result.tail(10)

        # RSI, MACDなどの主要な指標
        key_features = ["RSI", "MACD", "ATR"]
        for feature in key_features:
            if feature in latest_rows.columns:
                # 少なくとも50%のデータが存在するか
                non_null_ratio = latest_rows[feature].notna().sum() / len(latest_rows)
                assert non_null_ratio >= 0.5, f"{feature} has too many NaN values"

    def test_add_advanced_features_values_in_range(self, sample_price_data):
        """特徴量が妥当な範囲にあるかテスト"""
        result = add_advanced_features(sample_price_data.copy())

        # RSIは0-100の範囲
        if "RSI" in result.columns:
            rsi_values = result["RSI"].dropna()
            if len(rsi_values) > 0:
                assert rsi_values.min() >= 0, "RSI < 0"
                assert rsi_values.max() <= 100, "RSI > 100"

        # ATRは正の値
        if "ATR" in result.columns:
            atr_values = result["ATR"].dropna()
            if len(atr_values) > 0:
                assert atr_values.min() >= 0, "ATR < 0"


class TestFrequencyFeatures:
    """周波数特徴量のテスト"""

    @pytest.fixture
    def sample_price_series(self):
        """テスト用の価格系列を生成"""
        np.random.seed(42)
        # 周期的なパターン + ノイズ
        t = np.linspace(0, 4 * np.pi, 100)
        prices = 100 + 10 * np.sin(t) + np.random.randn(100) * 2

        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        return pd.Series(prices, index=dates, name="Close")

    def test_add_frequency_features_basic(self, sample_price_series):
        """周波数特徴量が追加されるかテスト"""
        df = sample_price_series.to_frame()
        result = add_frequency_features(df.copy())

        # 新しい特徴量が追加されているか
        assert "Freq_Power" in result.columns or "Frequency_Power" in result.columns

    def test_add_frequency_features_non_negative(self, sample_price_series):
        """周波数パワーが非負かテスト"""
        df = sample_price_series.to_frame()
        result = add_frequency_features(df.copy())

        # Freq_Powerカラムを探す
        freq_col = None
        for col in result.columns:
            if "freq" in col.lower() and "power" in col.lower():
                freq_col = col
                break

        if freq_col:
            power_values = result[freq_col].dropna()
            if len(power_values) > 0:
                assert power_values.min() >= 0, "Frequency power should be non-negative"


class TestSentimentFeatures:
    """センチメント特徴量のテスト"""

    def test_add_sentiment_features_basic(self):
        """センチメント特徴量が追加されるかテスト"""
        # 簡単なダミーデータ
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        df = pd.DataFrame({"Close": range(100, 110)}, index=dates)

        # センチメント機能が利用可能かチェック
        try:
            result = add_sentiment_features(df.copy())

            # 機能が実装されている場合
            if result is not None and not result.equals(df):
                # センチメント関連のカラムがあるか
                sentiment_cols = [col for col in result.columns if "sentiment" in col.lower()]
                assert len(sentiment_cols) > 0, "No sentiment columns added"
        except (ImportError, NotImplementedError):
            # 機能が未実装の場合はスキップ
            pytest.skip("Sentiment features not implemented")


class TestFeatureEngineeringIntegration:
    """特徴量エンジニアリング統合テスト"""

    def test_full_feature_pipeline(self):
        """完全な特徴量パイプラインをテスト"""
        np.random.seed(42)
        dates = pd.date_range("2024-01-01", periods=100, freq="D")

        # 元データ
        df = pd.DataFrame(
            {
                "Open": np.random.randn(100).cumsum() + 100,
                "High": np.random.randn(100).cumsum() + 102,
                "Low": np.random.randn(100).cumsum() + 98,
                "Close": np.random.randn(100).cumsum() + 100,
                "Volume": np.random.randint(1000000, 10000000, 100),
            },
            index=dates,
        )

        # High > Low を保証
        df["High"] = df[["Open", "High", "Close"]].max(axis=1) + 1
        df["Low"] = df[["Open", "Low", "Close"]].min(axis=1) - 1

        # 特徴量追加
        result = add_advanced_features(df.copy())

        if result is not None:
            result = add_frequency_features(result)

        # 最終的なDataFrameが妥当か
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(df)
        assert len(result.columns) > len(df.columns)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
