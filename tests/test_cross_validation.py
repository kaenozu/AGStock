"""
クロスバリデーションのテスト
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

from src.cross_validation import TimeSeriesCV, walk_forward_validation


@pytest.fixture
def sample_data():
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    X = pd.DataFrame({"feature": np.arange(100)}, index=dates)
    y = pd.Series(np.arange(100) * 2 + np.random.randn(100), index=dates)
    return X, y


def test_timeseries_cv(sample_data):
    """TimeSeriesCVのテスト"""
    X, y = sample_data
    tscv = TimeSeriesCV(n_splits=3)

    splits = list(tscv.split(X, y))
    assert len(splits) == 3

    # インデックスが増加しているか確認
    for train_idx, test_idx in splits:
        assert train_idx[-1] < test_idx[0]  # 未来のデータを使わない

    # モデル評価テスト
    model = LinearRegression()
    results = tscv.evaluate_model(model, X, y, mean_squared_error)

    assert "mean_score" in results
    assert len(results["scores"]) == 3


def test_walk_forward_validation(sample_data):
    """ウォークフォワードバリデーションのテスト"""
    X, y = sample_data
    model = LinearRegression()

    results = walk_forward_validation(
        model, X, y, train_window=50, test_window=10, step=10, metric_func=mean_squared_error
    )

    assert "mean_score" in results
    assert len(results["scores"]) > 0
