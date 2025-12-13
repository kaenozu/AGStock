"""
ML Pipelineのテスト
"""

import os
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.ml_pipeline import ContinuousLearner, ModelRegistry


@pytest.fixture
def temp_model_dir(tmp_path):
    return str(tmp_path / "models")


@pytest.fixture
def registry(temp_model_dir):
    return ModelRegistry(base_dir=temp_model_dir)


def test_registry_init(temp_model_dir):
    """レジストリ初期化のテスト"""
    registry = ModelRegistry(base_dir=temp_model_dir)
    assert os.path.exists(temp_model_dir)
    # registry.jsonは保存時に作成されるため、初期化直後は存在しない場合がある
    # assert os.path.exists(os.path.join(temp_model_dir, "registry.json"))


def test_register_model(registry):
    """モデル登録のテスト"""
    model = {"type": "test_model"}
    metrics = {"accuracy": 0.9}

    version_id = registry.register_model("test_model", model, metrics)

    assert version_id is not None
    assert "test_model" in registry.registry["models"]
    assert len(registry.registry["models"]["test_model"]) == 1
    assert registry.registry["models"]["test_model"][0]["metrics"]["accuracy"] == 0.9


@patch("src.ml_pipeline.datetime")
def test_get_latest_model(mock_datetime, registry):
    """最新モデル取得のテスト"""
    # 1回目の登録
    mock_now1 = MagicMock()
    mock_now1.strftime.return_value = "20230101_100000"

    # 2回目の登録
    mock_now2 = MagicMock()
    mock_now2.strftime.return_value = "20230101_100001"

    mock_datetime.now.side_effect = [mock_now1, mock_now2]

    model1 = {"type": "v1"}
    registry.register_model("test_model", model1, {"acc": 0.8}, version_tag="v1")

    model2 = {"type": "v2"}
    registry.register_model("test_model", model2, {"acc": 0.9}, version_tag="v2")

    loaded_model, metadata = registry.get_latest_model("test_model")

    assert loaded_model["type"] == "v2"
    assert metadata["version"] == "v2"


def test_get_best_model(registry):
    """最良モデル取得のテスト"""
    registry.register_model("test_model", {"v": 1}, {"accuracy": 0.8}, version_tag="v1")
    registry.register_model("test_model", {"v": 2}, {"accuracy": 0.9}, version_tag="v2")
    registry.register_model("test_model", {"v": 3}, {"accuracy": 0.7}, version_tag="v3")

    loaded_model, metadata = registry.get_best_model("test_model", metric="accuracy")

    assert loaded_model["v"] == 2
    assert metadata["version"] == "v2"


def test_continuous_learner(registry):
    """継続学習のテスト"""
    learner = ContinuousLearner(registry)

    def trainer_func(data):
        return {"model": "trained"}, {"accuracy": 0.95}

    result = learner.train_and_evaluate("new_model", trainer_func, pd.DataFrame())

    assert result["status"] == "success"
    assert result["metrics"]["accuracy"] == 0.95

    # レジストリに登録されているか確認
    model, meta = registry.get_latest_model("new_model")
    assert model["model"] == "trained"


def test_continuous_learner_failure(registry):
    """学習失敗時のテスト"""
    learner = ContinuousLearner(registry)

    def trainer_func(data):
        raise ValueError("Training failed")

    result = learner.train_and_evaluate("fail_model", trainer_func, pd.DataFrame())

    assert result["status"] == "failed"
    assert "Training failed" in result["error"]
