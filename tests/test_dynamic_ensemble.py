from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from src.dynamic_ensemble import DynamicEnsemble


# ダミー戦略クラス
class MockStrategy:
    def __init__(self, name, fixed_signal):
        self.name = name
        self.fixed_signal = fixed_signal

    def generate_signals(self, df):
        return pd.Series([self.fixed_signal] * len(df), index=df.index)

    def analyze(self, df):
        return {"signal": self.fixed_signal, "confidence": 1.0}


@pytest.fixture
def sample_data():
    dates = pd.date_range(start="2023-01-01", periods=10)
    df = pd.DataFrame(
        {
            "Open": np.random.rand(10) * 100,
            "High": np.random.rand(10) * 100,
            "Low": np.random.rand(10) * 100,
            "Close": np.random.rand(10) * 100,
            "Volume": np.random.randint(100, 1000, 10),
        },
        index=dates,
    )
    return df


import os


def test_dynamic_ensemble_initialization():
    state_file = "test_state_init.json"
    if os.path.exists(state_file):
        os.remove(state_file)

    s1 = MockStrategy("S1", 1)
    s2 = MockStrategy("S2", -1)
    ensemble = DynamicEnsemble([s1, s2], state_file=state_file)

    assert len(ensemble.weights) == 2
    assert ensemble.weights["S1"] == 0.5
    assert ensemble.weights["S2"] == 0.5

    if os.path.exists(state_file):
        os.remove(state_file)


def test_prediction_integration(sample_data):
    state_file = "test_state_pred.json"
    if os.path.exists(state_file):
        os.remove(state_file)

    s1 = MockStrategy("S1", 1)  # Always Buy
    s2 = MockStrategy("S2", -1)  # Always Sell
    ensemble = DynamicEnsemble([s1, s2], state_file=state_file)

    # Initial weights are 0.5, 0.5
    # Score = 1 * 0.5 + (-1) * 0.5 = 0
    score, preds = ensemble.predict(sample_data)

    assert score == 0.0
    assert preds["S1"] == 1.0
    assert preds["S2"] == -1.0

    if os.path.exists(state_file):
        os.remove(state_file)


def test_weight_update():
    state_file = "test_state_up.json"
    if os.path.exists(state_file):
        os.remove(state_file)

    s1 = MockStrategy("S1", 1)  # Always Buy
    s2 = MockStrategy("S2", -1)  # Always Sell
    ensemble = DynamicEnsemble([s1, s2], learning_rate=0.5, state_file=state_file)

    # Case 1: Market goes UP (Return > 0)
    # S1 (Buy) is correct, S2 (Sell) is wrong
    ticker = "TEST"
    date = datetime(2023, 1, 1)
    actual_return = 0.05  # +5%
    predictions = {"S1": 1, "S2": -1}

    ensemble.update(ticker, date, actual_return, predictions)

    # S1 should have higher weight
    assert ensemble.weights["S1"] > ensemble.weights["S2"]
    print(f"Weights after update: {ensemble.weights}")

    if os.path.exists(state_file):
        os.remove(state_file)


def test_weight_update_down_market():
    state_file = "test_state_down.json"
    if os.path.exists(state_file):
        os.remove(state_file)

    s1 = MockStrategy("S1", 1)  # Always Buy
    s2 = MockStrategy("S2", -1)  # Always Sell
    ensemble = DynamicEnsemble([s1, s2], learning_rate=0.5, state_file=state_file)

    # Case 2: Market goes DOWN (Return < 0)
    # S1 (Buy) is wrong, S2 (Sell) is correct
    ticker = "TEST"
    date = datetime(2023, 1, 1)
    actual_return = -0.05  # -5%
    predictions = {"S1": 1, "S2": -1}

    ensemble.update(ticker, date, actual_return, predictions)

    # S2 should have higher weight
    assert ensemble.weights["S2"] > ensemble.weights["S1"]
    print(f"Weights after update: {ensemble.weights}")

    if os.path.exists(state_file):
        os.remove(state_file)
