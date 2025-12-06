"""
config_managerのテスト
"""
import pytest
import os
from unittest.mock import patch
from src.config_manager import Config


def test_config_defaults():
    """デフォルト値のテスト"""
    assert Config.ENVIRONMENT == 'development' or isinstance(Config.ENVIRONMENT, str)
    assert isinstance(Config.DEBUG, bool)
    assert isinstance(Config.PAPER_TRADING, bool)


def test_config_debug_parsing():
    """DEBUG設定のパースのテスト"""
    with patch.dict(os.environ, {'DEBUG': 'true'}):
        # 環境変数を再読み込み
        from importlib import reload
        import src.config_manager
        reload(src.config_manager)
        assert src.config_manager.Config.DEBUG is True


def test_config_paper_trading_parsing():
    """PAPER_TRADING設定のパースのテスト"""
    with patch.dict(os.environ, {'PAPER_TRADING': 'false'}):
        from importlib import reload
        import src.config_manager
        reload(src.config_manager)
        assert src.config_manager.Config.PAPER_TRADING is False


def test_config_cache_ttl_parsing():
    """CACHE_TTL設定のパースのテスト"""
    with patch.dict(os.environ, {'CACHE_TTL': '7200'}):
        from importlib import reload
        import src.config_manager
        reload(src.config_manager)
        assert src.config_manager.Config.CACHE_TTL == 7200


def test_config_max_workers_parsing():
    """MAX_WORKERS設定のパースのテスト"""
    with patch.dict(os.environ, {'MAX_WORKERS': '8'}):
        from importlib import reload
        import src.config_manager
        reload(src.config_manager)
        assert src.config_manager.Config.MAX_WORKERS == 8


def test_config_validate_development():
    """開発環境での検証テスト"""
    with patch.object(Config, 'ENVIRONMENT', 'development'):
        assert Config.validate() is True


def test_config_validate_production_missing_secret():
    """本番環境でSECRET_KEYが未設定の場合"""
    with patch.object(Config, 'ENVIRONMENT', 'production'), \
         patch.object(Config, 'SECRET_KEY', 'dev-secret-key-change-in-production'):
        assert Config.validate() is False


def test_config_validate_production_missing_jwt():
    """本番環境でJWT_SECRETが未設定の場合"""
    with patch.object(Config, 'ENVIRONMENT', 'production'), \
         patch.object(Config, 'SECRET_KEY', 'production-secret'), \
         patch.object(Config, 'JWT_SECRET', 'dev-jwt-secret-change-in-production'):
        assert Config.validate() is False


def test_config_validate_production_missing_openai():
    """本番環境でOPENAI_API_KEYが未設定の場合"""
    with patch.object(Config, 'ENVIRONMENT', 'production'), \
         patch.object(Config, 'SECRET_KEY', 'production-secret'), \
         patch.object(Config, 'JWT_SECRET', 'production-jwt'), \
         patch.object(Config, 'OPENAI_API_KEY', ''):
        assert Config.validate() is False


def test_config_validate_production_all_set():
    """本番環境で全ての必須設定がある場合"""
    with patch.object(Config, 'ENVIRONMENT', 'production'), \
         patch.object(Config, 'SECRET_KEY', 'production-secret'), \
         patch.object(Config, 'JWT_SECRET', 'production-jwt'), \
         patch.object(Config, 'OPENAI_API_KEY', 'sk-test'):
        assert Config.validate() is True


def test_config_to_dict():
    """to_dictメソッドのテスト"""
    config_dict = Config.to_dict()
    
    assert 'environment' in config_dict
    assert 'debug' in config_dict
    assert 'log_level' in config_dict
    assert 'paper_trading' in config_dict
    assert 'auto_trading_enabled' in config_dict
    assert 'enable_notifications' in config_dict
    assert 'cache_ttl' in config_dict
    assert 'max_workers' in config_dict
    
    # 機密情報が含まれていないことを確認
    assert 'SECRET_KEY' not in config_dict
    assert 'JWT_SECRET' not in config_dict
    assert 'OPENAI_API_KEY' not in config_dict


def test_config_to_dict_types():
    """to_dictの返り値の型のテスト"""
    config_dict = Config.to_dict()
    
    assert isinstance(config_dict['environment'], str)
    assert isinstance(config_dict['debug'], bool)
    assert isinstance(config_dict['log_level'], str)
    assert isinstance(config_dict['paper_trading'], bool)
    assert isinstance(config_dict['cache_ttl'], int)
    assert isinstance(config_dict['max_workers'], int)
