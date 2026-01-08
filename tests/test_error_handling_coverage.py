"""error_handling.pyのテスト"""

from unittest.mock import MagicMock, patch
import pytest
from src.error_handling import (ErrorCategory, RetryableError, api_retry,
                                classify_error, get_user_friendly_message,
                                log_error_with_context, network_retry, retry)

def test_error_category_values():
    """ErrorCategoryの値テスト"""
    # 実装に合わせて大文字であることを確認
    assert ErrorCategory.NETWORK.value == "NETWORK"
    assert ErrorCategory.DATA.value == "DATA"
    assert ErrorCategory.PERMISSION.value == "PERMISSION"
    assert ErrorCategory.VALIDATION.value == "VALIDATION"
    assert ErrorCategory.UNKNOWN.value == "UNKNOWN"

def test_retryable_error():
    """RetryableErrorのテスト"""
    error = RetryableError("Test error")
    assert isinstance(error, Exception)

def test_classify_error_network():
    """ネットワークエラーの分類"""
    error = ConnectionError("Connection refused")
    category = classify_error(error)
    assert category == ErrorCategory.NETWORK

def test_classify_error_timeout():
    """タイムアウトエラーの分類"""
    error = TimeoutError("Connection timed out")
    category = classify_error(error)
    assert category == ErrorCategory.NETWORK

def test_classify_error_unknown():
    """不明なエラーの分類"""
    error = Exception("Some random error")
    category = classify_error(error)
    assert category == ErrorCategory.UNKNOWN

def test_get_user_friendly_message():
    """ユーザーフレンドリーなメッセージの生成"""
    error = ValueError("Invalid input")
    # 実装に合わせて引数を1つにする
    message = get_user_friendly_message(error)
    assert isinstance(message, str)

def test_retry_decorator_success():
    """リトライデコレータ成功テスト"""
    call_count = 0

    # 実装に合わせて引数名を max_retries に修正
    @retry(max_retries=3, backoff_factor=0.01)
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

    @retry(max_retries=3, backoff_factor=0.01)
    def eventually_successful():
        nonlocal call_count
        call_count += 1
        if call_count < 2: # retry logic might differ, max_retries=3 means up to 3 tries
            raise ValueError("Temporary error")
        return "success"

    result = eventually_successful()
    assert result == "success"
    assert call_count >= 2

def test_retry_decorator_all_failures():
    """全てリトライ失敗のテスト"""
    call_count = 0

    @retry(max_retries=3, backoff_factor=0.01)
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

    @network_retry(max_retries=1)
    def network_operation():
        nonlocal call_count
        call_count += 1
        return "network result"

    result = network_operation()
    assert result == "network result"
    assert call_count == 1

def test_log_error_with_context():
    """log_error_with_contextのテスト"""
    error = ValueError("Test error")

    # 実装に合わせて引数を修正
    with patch("src.error_handling.logger") as mock_logger:
        log_error_with_context(error, context={"key": "value"})
        mock_logger.error.assert_called_once()