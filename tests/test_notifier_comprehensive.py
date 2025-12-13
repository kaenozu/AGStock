"""
Notifierの包括的なテスト
"""

from datetime import datetime
from enum import Enum
from unittest.mock import MagicMock, patch

import pytest

from src.notifier import (DiscordWebhookService, LINENotifyService, Notifier,
                          SlackWebhookService)


class MockPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MockAlertType(Enum):
    PRICE = "price"
    SIGNAL = "signal"
    SYSTEM = "system"


class MockAlert:
    def __init__(self, message, priority=MockPriority.MEDIUM, alert_type=MockAlertType.SYSTEM):
        self.message = message
        self.priority = priority
        self.alert_type = alert_type
        self.timestamp = datetime(2023, 1, 1, 12, 0, 0)


@pytest.fixture
def mock_requests():
    with patch("src.notifier.requests") as mock:
        yield mock


def test_line_notify_service(mock_requests):
    """LINE Notifyサービスのテスト"""
    service = LINENotifyService("test_token")
    alert = MockAlert("Test Message")

    # 成功
    mock_requests.post.return_value.status_code = 200
    assert service.send(alert) is True

    # 失敗
    mock_requests.post.return_value.status_code = 400
    assert service.send(alert) is False

    # 例外
    mock_requests.post.side_effect = Exception("Network Error")
    assert service.send(alert) is False


def test_discord_webhook_service(mock_requests):
    """Discord Webhookサービスのテスト"""
    service = DiscordWebhookService("http://webhook.url")
    alert = MockAlert("Test Message", priority=MockPriority.CRITICAL)

    # 成功 (204 No Content)
    mock_requests.post.return_value.status_code = 204
    assert service.send(alert) is True

    # 失敗
    mock_requests.post.return_value.status_code = 400
    assert service.send(alert) is False

    # 例外
    mock_requests.post.side_effect = Exception("Network Error")
    assert service.send(alert) is False


def test_slack_webhook_service(mock_requests):
    """Slack Webhookサービスのテスト"""
    service = SlackWebhookService("http://webhook.url")
    alert = MockAlert("Test Message", priority=MockPriority.HIGH)

    # 成功
    mock_requests.post.return_value.status_code = 200
    assert service.send(alert) is True

    # 失敗
    mock_requests.post.return_value.status_code = 500
    assert service.send(alert) is False

    # 例外
    mock_requests.post.side_effect = Exception("Network Error")
    assert service.send(alert) is False


def test_legacy_notifier(mock_requests):
    """レガシーNotifierのテスト"""
    with patch.dict("os.environ", {"SLACK_WEBHOOK_URL": "http://slack.url"}):
        notifier = Notifier()

        # Slack通知成功
        mock_requests.post.return_value.status_code = 200
        assert notifier.notify_slack("Message") is True

        # Slack通知失敗
        mock_requests.post.return_value.status_code = 400
        assert notifier.notify_slack("Message") is False

        # 例外
        mock_requests.post.side_effect = Exception("Error")
        assert notifier.notify_slack("Message") is False


def test_legacy_notifier_no_webhook():
    """Webhook URLがない場合のテスト"""
    with patch.dict("os.environ", {}, clear=True):
        notifier = Notifier()
        assert notifier.notify_slack("Message") is False
