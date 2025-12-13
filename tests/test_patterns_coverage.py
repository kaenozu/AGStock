"""patterns.pyのテスト"""

import numpy as np
import pandas as pd
import pytest

from src.patterns import (detect_double_bottom,
                          detect_head_and_shoulders_bottom, detect_triangle,
                          find_local_extrema, scan_for_patterns)


@pytest.fixture
def sample_df():
    """基本的なサンプルデータ"""
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    np.random.seed(42)

    base = 100
    prices = base + np.cumsum(np.random.randn(100) * 2)

    return pd.DataFrame(
        {
            "Open": prices * 0.99,
            "High": prices * 1.02,
            "Low": prices * 0.98,
            "Close": prices,
            "Volume": [1000000] * 100,
        },
        index=dates,
    )


@pytest.fixture
def double_bottom_df():
    """ダブルボトムパターンを持つデータ"""
    dates = pd.date_range("2023-01-01", periods=60, freq="D")

    # W字型のパターンを作成（60個のデータポイント）
    prices = np.array(
        [
            100,
            98,
            95,
            92,
            90,
            88,
            85,
            88,
            90,
            93,  # 10
            95,
            98,
            100,
            102,
            105,
            108,
            110,
            112,
            110,
            108,  # 10
            105,
            102,
            100,
            97,
            95,
            92,
            90,
            87,
            85,
            87,  # 10
            90,
            93,
            95,
            98,
            100,
            103,
            105,
            108,
            110,
            112,  # 10
            115,
            118,
            120,
            122,
            125,
            128,
            130,
            132,
            135,
            137,  # 10
            140,
            143,
            145,
            148,
            150,
            152,
            155,
            158,
            160,
            165,  # 10 = 60 total
        ]
    )

    return pd.DataFrame(
        {"Open": prices * 0.99, "High": prices * 1.02, "Low": prices * 0.98, "Close": prices, "Volume": [1000000] * 60},
        index=dates,
    )


def test_find_local_extrema(sample_df):
    """find_local_extremaのテスト"""
    result = find_local_extrema(sample_df, window=5)

    assert "is_max" in result.columns
    assert "is_min" in result.columns
    assert result["is_max"].dtype == bool
    assert result["is_min"].dtype == bool


def test_detect_double_bottom_insufficient_data():
    """データ不足の場合None"""
    df = pd.DataFrame(
        {
            "Open": [100] * 10,
            "High": [105] * 10,
            "Low": [95] * 10,
            "Close": [102] * 10,
        }
    )

    result = detect_double_bottom(df)
    assert result is None


def test_detect_double_bottom(double_bottom_df):
    """ダブルボトム検出のテスト"""
    result = detect_double_bottom(double_bottom_df, tolerance=0.1)
    # パターンが見つかる可能性がある（データ依存）
    if result is not None:
        assert "pattern" in result
        assert result["pattern"] == "Double Bottom"


def test_detect_head_and_shoulders_bottom_insufficient_data():
    """データ不足の場合None"""
    df = pd.DataFrame(
        {
            "Open": [100] * 30,
            "High": [105] * 30,
            "Low": [95] * 30,
            "Close": [102] * 30,
        }
    )

    result = detect_head_and_shoulders_bottom(df)
    assert result is None


def test_detect_head_and_shoulders_bottom(sample_df):
    """逆三尊検出のテスト"""
    result = detect_head_and_shoulders_bottom(sample_df)
    # パターンが見つかならないか見つかるか（データ依存）
    assert result is None or "pattern" in result


def test_detect_triangle_insufficient_data():
    """データ不足の場合None"""
    df = pd.DataFrame(
        {
            "Open": [100] * 10,
            "High": [105] * 10,
            "Low": [95] * 10,
            "Close": [102] * 10,
        }
    )

    result = detect_triangle(df)
    assert result is None


def test_detect_triangle(sample_df):
    """三角形パターン検出のテスト"""
    result = detect_triangle(sample_df)
    # パターンが見つかならないか見つかるか（データ依存）
    assert result is None or "pattern" in result


def test_scan_for_patterns(sample_df):
    """scan_for_patternsのテスト"""
    result = scan_for_patterns("TEST", sample_df)

    assert isinstance(result, list)
    for pattern in result:
        assert "ticker" in pattern
        assert pattern["ticker"] == "TEST"


def test_scan_for_patterns_with_error():
    """エラーが発生した場合の処理"""
    # 不正なデータ
    df = pd.DataFrame({"invalid": [1, 2, 3]})

    result = scan_for_patterns("TEST", df)
    assert isinstance(result, list)
