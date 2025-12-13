import numpy as np
import pandas as pd
import pytest

from src.advanced_features import (add_trend_features,
                                   generate_all_advanced_features)


@pytest.fixture
def sample_data():
    dates = pd.date_range(start="2023-01-01", periods=100)
    df = pd.DataFrame(
        {
            "Open": np.random.rand(100) * 100 + 100,
            "High": np.random.rand(100) * 100 + 110,
            "Low": np.random.rand(100) * 100 + 90,
            "Close": np.random.rand(100) * 100 + 100,
            "Volume": np.random.randint(100, 1000, 100),
        },
        index=dates,
    )
    return df


def test_add_trend_features(sample_data):
    df_out = add_trend_features(sample_data)

    assert "ADX" in df_out.columns
    assert "CCI" in df_out.columns
    assert "RSI" in df_out.columns
    assert "MACD" in df_out.columns

    # Check for NaNs (should be handled by generate_all, but here we check raw output)
    # ta library might produce NaNs at the beginning
    assert not df_out["ADX"].isnull().all()


def test_generate_all_advanced_features(sample_data):
    df_out = generate_all_advanced_features(sample_data)

    # Check shape
    assert df_out.shape[1] > sample_data.shape[1]

    # Check specific features
    assert "Close_lag_1" in df_out.columns
    assert "Close_std_5" in df_out.columns
    assert "ATR_14" in df_out.columns
    assert "ADX" in df_out.columns

    # Check NaN handling
    assert not df_out.isnull().any().any()
