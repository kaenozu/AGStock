"""
Configのテスト - Pydanticベースの新しいConfig用
"""

import pytest


def test_config_pydantic_structure():
    """新しいPydantic Configの構造テスト"""
    from src.config import Config, settings

    # settingsはConfigインスタンス
    assert isinstance(settings, Config)

    # 各セクションが存在
    assert hasattr(settings, "trading")
    assert hasattr(settings, "ai")
    assert hasattr(settings, "system")
    assert hasattr(settings, "risk_management")


def test_config_trading_defaults():
    """トレード設定のデフォルト値テスト"""
    from src.config import settings

    assert settings.trading.max_daily_trades == 5
    assert settings.trading.daily_loss_limit_pct == -5.0
    assert settings.trading.max_position_size == 0.2
    assert settings.trading.min_cash_reserve == 200000.0


def test_config_ai_defaults():
    """AI設定のデフォルト値テスト"""
    from src.config import settings

    assert settings.ai.enabled is True
    assert settings.ai.model_name == "gemini-2.0-flash-exp"
    assert settings.ai.confidence_threshold == 0.7
    assert settings.ai.debate_rounds == 3


def test_config_system_defaults():
    """システム設定のデフォルト値テスト"""
    from src.config import settings

    assert settings.system.initial_capital == 10000000
    assert settings.system.realtime_ttl_seconds == 30


def test_config_get_method():
    """後方互換性のあるgetメソッドテスト"""
    from src.config import config

    # ネストされた値へのアクセス
    assert config.get("system.initial_capital") == 10000000
    assert config.get("trading.max_daily_trades") == 5
    assert config.get("risk_management.max_position_size") == 0.2


def test_config_get_nonexistent_key():
    """存在しないキーの取得テスト"""
    from src.config import config

    # 存在しないキーはNoneを返す
    assert config.get("nonexistent.key") is None
    # デフォルト値を指定
    assert config.get("nonexistent.key", default="fallback") == "fallback"


def test_config_get_with_default():
    """デフォルト値付きの取得テスト"""
    from src.config import config

    assert config.get("unknown.path", default=999) == 999


def test_global_config_instance():
    """グローバルインスタンスのテスト"""
    from src.config import config, settings

    assert config is not None
    assert settings is not None
    # configはConfigSingletonのインスタンス
    assert config.get("system.initial_capital") == 10000000


def test_config_tickers():
    """ティッカーリストのテスト"""
    from src.config import settings

    assert len(settings.tickers_jp) > 0
    assert len(settings.tickers_us) > 0
    assert "7203.T" in settings.tickers_jp
    assert "AAPL" in settings.tickers_us


def test_config_ensure_dirs():
    """ディレクトリ作成のテスト"""
    from src.config import settings
    from pathlib import Path

    settings.ensure_dirs()
    assert Path(settings.system.data_dir).exists()
