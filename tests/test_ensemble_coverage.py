"""ensemble.pyのテスト"""

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from src.ensemble import EnsembleVoter


@pytest.fixture
def sample_df():
    """サンプルデータ"""
    dates = pd.date_range("2023-01-01", periods=50, freq="D")
    np.random.seed(42)

    prices = 100 + np.cumsum(np.random.randn(50) * 2)

    return pd.DataFrame(
        {"Open": prices * 0.99, "High": prices * 1.02, "Low": prices * 0.98, "Close": prices, "Volume": [1000000] * 50},
        index=dates,
    )


def create_mock_strategy(name: str, signal: int):
    """モック戦略を作成"""
    strategy = MagicMock()
    strategy.name = name
    strategy.analyze.return_value = {"signal": signal}
    return strategy


def test_ensemble_voter_init():
    """初期化テスト"""
    strategy1 = create_mock_strategy("strategy1", 1)
    strategy2 = create_mock_strategy("strategy2", -1)

    voter = EnsembleVoter([strategy1, strategy2])

    assert len(voter.strategies) == 2
    assert "strategy1" in voter.weights
    assert "strategy2" in voter.weights


def test_ensemble_voter_init_with_weights():
    """重み付き初期化テスト"""
    strategy1 = create_mock_strategy("strategy1", 1)
    strategy2 = create_mock_strategy("strategy2", -1)

    weights = {"strategy1": 0.7, "strategy2": 0.3}
    voter = EnsembleVoter([strategy1, strategy2], weights=weights)

    assert voter.weights["strategy1"] == 0.7
    assert voter.weights["strategy2"] == 0.3


def test_ensemble_voter_vote_buy_signal(sample_df):
    """買いシグナルのテスト"""
    strategy1 = create_mock_strategy("strategy1", 1)
    strategy2 = create_mock_strategy("strategy2", 1)
    strategy3 = create_mock_strategy("strategy3", 1)

    voter = EnsembleVoter([strategy1, strategy2, strategy3])
    result = voter.vote(sample_df)

    assert result["signal"] == 1
    assert result["confidence"] > 0
    assert "details" in result


def test_ensemble_voter_vote_sell_signal(sample_df):
    """売りシグナルのテスト"""
    strategy1 = create_mock_strategy("strategy1", -1)
    strategy2 = create_mock_strategy("strategy2", -1)
    strategy3 = create_mock_strategy("strategy3", -1)

    voter = EnsembleVoter([strategy1, strategy2, strategy3])
    result = voter.vote(sample_df)

    assert result["signal"] == -1
    assert result["confidence"] > 0


def test_ensemble_voter_vote_hold_signal(sample_df):
    """ホールドシグナルのテスト"""
    strategy1 = create_mock_strategy("strategy1", 1)
    strategy2 = create_mock_strategy("strategy2", -1)
    strategy3 = create_mock_strategy("strategy3", 0)

    voter = EnsembleVoter([strategy1, strategy2, strategy3])
    result = voter.vote(sample_df)

    # 投票がほぼ均衡しているのでHOLD
    assert result["signal"] == 0


def test_ensemble_voter_vote_weighted(sample_df):
    """重み付き投票のテスト"""
    strategy1 = create_mock_strategy("strategy1", 1)
    strategy2 = create_mock_strategy("strategy2", -1)

    # strategy1を高く評価
    weights = {"strategy1": 0.9, "strategy2": 0.1}
    voter = EnsembleVoter([strategy1, strategy2], weights=weights)
    result = voter.vote(sample_df)

    # strategy1の重みが大きいので買い
    assert result["signal"] == 1


def test_ensemble_voter_vote_details(sample_df):
    """詳細情報のテスト"""
    strategy1 = create_mock_strategy("strategy1", 1)
    strategy2 = create_mock_strategy("strategy2", -1)

    voter = EnsembleVoter([strategy1, strategy2])
    result = voter.vote(sample_df)

    assert "strategy1" in result["details"]
    assert "strategy2" in result["details"]
    assert result["details"]["strategy1"]["signal"] == 1
    assert result["details"]["strategy2"]["signal"] == -1
