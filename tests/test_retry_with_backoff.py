import pytest

from src import helpers, utils


def test_helpers_reexports_utils_retry_function():
    """helpersがutilsのバックオフデコレータをそのまま再利用することを確認。"""
    assert helpers.retry_with_backoff is utils.retry_with_backoff


def test_retry_with_backoff_retries_with_exponential_backoff(monkeypatch):
    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr("src.utils.time.sleep", fake_sleep)

    call_count = {
        "count": 0,
    }

    @helpers.retry_with_backoff(retries=2, backoff_in_seconds=1)
    def flaky_function():
        call_count["count"] += 1
        if call_count["count"] < 3:
            raise ValueError("temporary failure")
        return "success"

    assert flaky_function() == "success"
    assert sleep_calls == [1, 2]
    assert call_count["count"] == 3
