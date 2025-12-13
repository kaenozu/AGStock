"""error_handling.pyのテスト"""

from unittest.mock import MagicMock, patch

import pytest

from src.error_handling import (ErrorCategory, RetryableError, api_retry,
                                classify_error, get_user_friendly_message,
                                log_error_with_context, network_retry, retry)


def test_error_category_values():
    """ErrorCategoryの値テスト"""
    assert ErrorCategory.NETWORK.value == "network"
    assert ErrorCategory.DATA.value == "data"
    assert ErrorCategory.PERMISSION.value == "permission"
    assert ErrorCategory.RESOURCE.value == "resource"
    assert ErrorCategory.VALIDATION.value == "validation"
    assert ErrorCategory.EXTERNAL_API.value == "external_api"
    assert ErrorCategory.UNKNOWN.value == "unknown"


def test_retryable_error():
    """RetryableErrorのテスト"""
    error = RetryableError("Test error")
    assert isinstance(error, Exception)


def test_classify_error_network():
    """ネットワークエラーの分類"""
    # ConnectionErrorはネットワークカテゴリ
    error = ConnectionError("Connection refused")
    category = classify_error(error)
    assert category == ErrorCategory.NETWORK


def test_classify_error_timeout():
    """タイムアウトエラーの分類"""
    error = TimeoutError("Connection timed out")
    category = classify_error(error)
    assert category == ErrorCategory.NETWORK


def test_classify_error_file_not_found():
    """ファイルエラーの分類"""
    error = FileNotFoundError("File not found")
    category = classify_error(error)
    # "not found" はデータカテゴリ
    assert category == ErrorCategory.DATA


def test_classify_error_permission():
    """パーミッションエラーの分類"""
    error = PermissionError("Permission denied")
    category = classify_error(error)
    assert category == ErrorCategory.PERMISSION


def test_classify_error_value():
    """バリデーションエラーの分類"""
    # "validation" を含むエラー
    error = ValueError("validation error")
    category = classify_error(error)
    assert category == ErrorCategory.VALIDATION


def test_classify_error_unknown():
    """不明なエラーの分類"""
    error = Exception("Some random error")
    category = classify_error(error)
    assert category == ErrorCategory.UNKNOWN


def test_get_user_friendly_message():
    """ユーザーフレンドリーなメッセージの生成"""
    error = ValueError("Invalid input")
    message = get_user_friendly_message(error, "テスト処理")

    assert "title" in message
    assert "message" in message
    assert "suggestion" in message
    assert "technical_details" in message


def test_get_user_friendly_message_network():
    """ネットワークエラーのメッセージ"""
    import socket

    error = socket.timeout("Connection timed out")
    message = get_user_friendly_message(error, "データ取得")

    assert "title" in message


def test_retry_decorator_success():
    """リトライデコレータ成功テスト"""
    call_count = 0

    @retry(max_attempts=3, delay=0.01)
    def successful_function():
        nonlocal call_count
        call_count += 1
        return "success"

    result = successful_function()
    assert result == "success"
    assert call_count == 1


def test_retry_decorator_failure_then_success():
    """リトライ後成功のテスト"""
    call_count = 0

    @retry(max_attempts=3, delay=0.01)
    def eventually_successful():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary error")
        return "success"

    result = eventually_successful()
    assert result == "success"
    assert call_count == 3


def test_retry_decorator_all_failures():
    """全てリトライ失敗のテスト"""
    call_count = 0

    @retry(max_attempts=3, delay=0.01)
    def always_fails():
        nonlocal call_count
        call_count += 1
        raise ValueError("Permanent error")

    with pytest.raises(ValueError):
        always_fails()

    assert call_count == 3


def test_network_retry_decorator():
    """network_retryデコレータのテスト"""
    call_count = 0

    @network_retry
    def network_operation():
        nonlocal call_count
        call_count += 1
        return "network result"

    result = network_operation()
    assert result == "network result"
    assert call_count == 1


def test_api_retry_decorator():
    """api_retryデコレータのテスト"""
    call_count = 0

    @api_retry
    def api_operation():
        nonlocal call_count
        call_count += 1
        return "api result"

    result = api_operation()
    assert result == "api result"
    assert call_count == 1


def test_log_error_with_context():
    """log_error_with_contextのテスト"""
    error = ValueError("Test error")

    # ログが記録されることを確認
    with patch("src.error_handling.logger") as mock_logger:
        log_error_with_context(error, "test context", level="error")
        mock_logger.error.assert_called_once()


def test_log_error_with_context_warning():
    """warningレベルのログテスト"""
    error = ValueError("Test warning")

    with patch("src.error_handling.logger") as mock_logger:
        log_error_with_context(error, "test context", level="warning")
        mock_logger.warning.assert_called_once()


def test_log_error_with_context_critical():
    """criticalレベルのログテスト"""
    error = ValueError("Critical error")

    with patch("src.error_handling.logger") as mock_logger:
        log_error_with_context(error, "test context", level="critical")
        mock_logger.critical.assert_called_once()
