"""
Configのテスト
"""
import pytest
import os
from pathlib import Path
from unittest.mock import patch, mock_open
import yaml


@pytest.fixture
def clean_config():
    """各テスト前にConfigをリセット"""
    from src.config import Config
    Config._instance = None
    Config._config = {}
    yield
    Config._instance = None
    Config._config = {}


def test_config_singleton(clean_config):
    """シングルトンパターンのテスト"""
    from src.config import Config
    
    config1 = Config()
    config2 = Config()
    
    assert config1 is config2


def test_config_load_from_yaml(clean_config):
    """YAMLファイルからの設定読み込みテスト"""
    yaml_content = """
system:
  initial_capital: 5000000
risk_management:
  max_position_size: 0.15
"""
    
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=yaml_content)):
        from src.config import Config
        config = Config()
        
        assert config.get('system.initial_capital') == 5000000
        assert config.get('risk_management.max_position_size') == 0.15


def test_config_fallback_defaults(clean_config):
    """設定ファイルがない場合のデフォルト値テスト"""
    with patch('pathlib.Path.exists', return_value=False):
        from src.config import Config
        config = Config()
        
        assert config.get('system.initial_capital') == 10000000
        assert config.get('risk_management.max_position_size') == 0.2


def test_config_get_nested_value(clean_config):
    """ネストされた値の取得テスト"""
    with patch('pathlib.Path.exists', return_value=False):
        from src.config import Config
        config = Config()
        
        value = config.get('system.initial_capital')
        assert value == 10000000


def test_config_get_nonexistent_key(clean_config):
    """存在しないキーの取得テスト"""
    with patch('pathlib.Path.exists', return_value=False):
        from src.config import Config
        config = Config()
        
        value = config.get('nonexistent.key', default='default_value')
        assert value == 'default_value'


def test_config_get_with_default(clean_config):
    """デフォルト値付きの取得テスト"""
    with patch('pathlib.Path.exists', return_value=False):
        from src.config import Config
        config = Config()
        
        value = config.get('unknown.path', default=999)
        assert value == 999


def test_config_env_override_slack(clean_config):
    """環境変数によるSlack設定の上書きテスト"""
    with patch('pathlib.Path.exists', return_value=False), \
         patch.dict(os.environ, {'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/test'}):
        from src.config import Config
        config = Config()
        
        assert config.get('notifications.slack.webhook_url') == 'https://hooks.slack.com/test'


def test_config_env_override_discord(clean_config):
    """環境変数によるDiscord設定の上書きテスト"""
    with patch('pathlib.Path.exists', return_value=False), \
         patch.dict(os.environ, {'DISCORD_WEBHOOK_URL': 'https://discord.com/api/webhooks/test'}):
        from src.config import Config
        config = Config()
        
        assert config.get('notifications.discord.webhook_url') == 'https://discord.com/api/webhooks/test'


def test_config_env_override_pushover(clean_config):
    """環境変数によるPushover設定の上書きテスト"""
    with patch('pathlib.Path.exists', return_value=False), \
         patch.dict(os.environ, {
             'PUSHOVER_USER_KEY': 'test_user_key',
             'PUSHOVER_API_TOKEN': 'test_api_token'
         }):
        from src.config import Config
        config = Config()
        
        assert config.get('notifications.pushover.user_key') == 'test_user_key'
        assert config.get('notifications.pushover.api_token') == 'test_api_token'


def test_config_env_override_email(clean_config):
    """環境変数によるEmail設定の上書きテスト"""
    with patch('pathlib.Path.exists', return_value=False), \
         patch.dict(os.environ, {
             'EMAIL_ENABLED': 'true',
             'EMAIL_FROM': 'from@example.com',
             'EMAIL_TO': 'to@example.com',
             'EMAIL_PASSWORD': 'secret'
         }):
        from src.config import Config
        config = Config()
        
        assert config.get('notifications.email.enabled') is True
        assert config.get('notifications.email.from_address') == 'from@example.com'
        assert config.get('notifications.email.to_address') == 'to@example.com'
        assert config.get('notifications.email.password') == 'secret'


def test_config_env_email_enabled_false(clean_config):
    """EMAIL_ENABLEDがfalseの場合のテスト"""
    with patch('pathlib.Path.exists', return_value=False), \
         patch.dict(os.environ, {'EMAIL_ENABLED': 'false'}):
        from src.config import Config
        config = Config()
        
        assert config.get('notifications.email.enabled') is False


def test_global_config_instance(clean_config):
    """グローバルインスタンスのテスト"""
    with patch('pathlib.Path.exists', return_value=False):
        from src.config import config
        
        assert config is not None
        assert config.get('system.initial_capital') == 10000000
