"""
SmartNotifierの包括的なテスト
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
import json
from src.smart_notifier import SmartNotifier


@pytest.fixture
def mock_config():
    return {
        "notifications": {
            "line": {"enabled": True, "token": "line_token"},
            "discord": {"enabled": True, "webhook_url": "http://discord.url"}
        }
    }


@pytest.fixture
def smart_notifier(mock_config):
    with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
        return SmartNotifier("config.json")


@pytest.fixture
def mock_requests():
    with patch('src.smart_notifier.requests') as mock:
        yield mock


def test_init(mock_config):
    """初期化のテスト"""
    with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
        sn = SmartNotifier("config.json")
        assert sn.line_token == "line_token"
        assert sn.discord_webhook == "http://discord.url"


def test_init_no_config():
    """設定ファイルがない場合の初期化テスト"""
    with patch('builtins.open', side_effect=FileNotFoundError):
        sn = SmartNotifier("config.json")
        assert sn.line_token is None
        assert sn.discord_webhook is None


def test_send_line_notify(smart_notifier, mock_requests):
    """LINE通知送信テスト"""
    mock_requests.post.return_value.status_code = 200
    assert smart_notifier.send_line_notify("Test") is True
    
    mock_requests.post.return_value.status_code = 400
    assert smart_notifier.send_line_notify("Test") is False


def test_send_line_notify_no_token(smart_notifier):
    """トークンなしでのLINE通知テスト"""
    smart_notifier.line_token = None
    assert smart_notifier.send_line_notify("Test") is False


def test_send_line_notify_with_image(smart_notifier, mock_requests):
    """画像付きLINE通知テスト"""
    mock_requests.post.return_value.status_code = 200
    
    with patch('builtins.open', mock_open(read_data=b'image_data')):
        assert smart_notifier.send_line_notify("Test", image_path="test.png") is True
        
    # ファイルオープン引数の確認は複雑なので省略


def test_send_discord_webhook(smart_notifier, mock_requests):
    """Discord通知送信テスト"""
    mock_requests.post.return_value.status_code = 204
    assert smart_notifier.send_discord_webhook("Test") is True
    
    mock_requests.post.return_value.status_code = 400
    assert smart_notifier.send_discord_webhook("Test") is False


def test_send_discord_webhook_with_image(smart_notifier, mock_requests):
    """画像付きDiscord通知テスト"""
    mock_requests.post.return_value.status_code = 200
    
    # mock_openがconfig読み込みと画像読み込みで競合しないように注意
    # SmartNotifierは初期化済みなのでconfig読み込みは終わっている
    with patch('builtins.open', mock_open(read_data=b'image_data')):
        assert smart_notifier.send_discord_webhook("Test", image_path="test.png") is True


def test_send_daily_summary_rich(smart_notifier, mock_requests):
    """日次サマリー送信テスト"""
    summary = {
        'date': '2023-01-01',
        'total_value': 1000000,
        'daily_pnl': 5000,
        'win_rate': 0.6,
        'advice': 'Hold',
        'signals': [{'action': 'BUY', 'ticker': 'AAPL', 'name': 'Apple'}]
    }
    
    mock_requests.post.return_value.status_code = 200
    
    smart_notifier.send_daily_summary_rich(summary)
    
    assert mock_requests.post.call_count >= 2 # LINEとDiscord両方に送信
