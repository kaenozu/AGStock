import json

import yaml

from src.utils.config_loader import DEFAULT_CONFIG, load_config_from_yaml


def test_loads_valid_yaml(tmp_path):
    config = {"alpha": 1, "beta": {"gamma": True}}
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    assert load_config_from_yaml(str(config_path)) == config


def test_empty_yaml_returns_default(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("", encoding="utf-8")

    assert load_config_from_yaml(str(config_path)) == DEFAULT_CONFIG


def test_invalid_yaml_falls_back_to_default(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("paper_trading: [1000000", encoding="utf-8")

    assert load_config_from_yaml(str(config_path)) == DEFAULT_CONFIG


def test_json_fallback_when_yaml_missing(tmp_path):
    json_config = {"paper_trading": {"initial_capital": 500000}}
    json_path = tmp_path / "config.json"
    json_path.write_text(json.dumps(json_config), encoding="utf-8")

    # YAMLが存在しない場合は同名のJSONを読み取る
    yaml_path = tmp_path / "config.yaml"
    assert load_config_from_yaml(str(yaml_path)) == json_config
