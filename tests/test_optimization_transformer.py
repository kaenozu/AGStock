import os

import numpy as np
import pandas as pd
import pytest

from src.optimization import HyperparameterOptimizer


@pytest.fixture
def sample_data():
    dates = pd.date_range(start="2023-01-01", periods=300)
    df = pd.DataFrame(
        {
            "Open": np.random.rand(300) * 100 + 100,
            "High": np.random.rand(300) * 100 + 110,
            "Low": np.random.rand(300) * 100 + 90,
            "Close": np.random.rand(300) * 100 + 100,
            "Volume": np.random.randint(100, 1000, 300),
        },
        index=dates,
    )
    return df


def test_optimize_transformer(sample_data):
    # Use a temporary config file
    config_path = "test_config/model_params.json"

    # Create directory
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    if os.path.exists(config_path):
        os.remove(config_path)

    optimizer = HyperparameterOptimizer(config_path=config_path)

    # Run optimization with minimal trials
    best_params = optimizer.optimize_transformer(sample_data, n_trials=2)

    assert best_params is not None
    assert "hidden_size" in best_params
    assert "learning_rate" in best_params

    # Check if params are saved
    assert os.path.exists(config_path)

    # Cleanup
    if os.path.exists(config_path):
        os.remove(config_path)
    if os.path.exists("test_config"):
        os.rmdir("test_config")
