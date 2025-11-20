import pytest
from unittest.mock import patch, MagicMock
from src.notifier import Notifier

@pytest.fixture
def notifier():
    with patch.dict('os.environ', {
        'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/services/TEST/TEST/TEST',
        'EMAIL_ENABLED': 'true',
        'EMAIL_FROM': 'test@example.com',
        'EMAIL_TO': 'user@example.com'
    }):
        return Notifier()

def test_notify_strong_signal(notifier):
    with patch('src.notifier.requests.post') as mock_post, \
         patch('src.notifier.Notifier.send_email') as mock_email:
        
        mock_post.return_value.status_code = 200
        
        notifier.notify_strong_signal("TEST.T", "BUY", 0.95, 1000.0, "TestStrategy")
        
        # Check Slack call
        assert mock_post.called
        args, kwargs = mock_post.call_args
        assert "STRONG SIGNAL" in kwargs['json']['text']
        
        # Check Email call
        assert mock_email.called
        args, _ = mock_email.call_args
        assert "AGStock Alert: BUY TEST.T" in args[0]

def test_notify_daily_summary(notifier):
    with patch('src.notifier.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        
        signals = [{'ticker': '1234.T', 'action': 'BUY', 'strategy': 'RSI'}]
        notifier.notify_daily_summary(signals, 1000000, 5000)
        
        assert mock_post.called
        args, kwargs = mock_post.call_args
        assert "Daily Summary" in kwargs['json']['text']
