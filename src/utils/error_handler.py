"""
Unified Error Handler for AGStock
Provides consistent error handling, logging, and user-friendly notifications.
"""

import logging
import traceback
from functools import wraps
from typing import Any, Callable, Optional

import streamlit as st

logger = logging.getLogger(__name__)


class AGStockError(Exception):
    """Base exception for AGStock applications."""
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ):
        super().__init__(message)
        self.user_message = user_message or message
        self.recovery_hint = recovery_hint


class DataFetchError(AGStockError):
    """Errors related to fetching market or external data."""
    pass


class AnalysisError(AGStockError):
    """Errors occurring during strategy analysis or model inference."""
    pass


class ExecutionError(AGStockError):
    """Errors occurring during trade execution or order processing."""
    pass


class ConfigurationError(AGStockError):
    """Errors related to system settings or missing API keys."""
    pass


def handle_error(error: Exception, context: str = "", show_to_user: bool = True) -> None:
    """
    Centralized error handling. Logs the full traceback and optionally notifies user via UI.
    """
    error_msg = f"{context}: {str(error)}" if context else str(error)
    logger.error(error_msg)
    logger.debug(traceback.format_exc())

    if show_to_user:
        if isinstance(error, AGStockError):
            st.error(f"❌ {error.user_message}")
            if error.recovery_hint:
                st.info(f"💡 {error.recovery_hint}")
        else:
            st.error(f"❌ エラーが発生しました: {error_msg}")
            st.info("💡 問題が解決しない場合は、ページを再読み込みするかログを確認してください。")


def safe_execute(
    func: Callable, *args, default_return: Any = None, context: str = "", **kwargs
) -> Any:
    """Safely execute a function, catching and handling any exceptions."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_error(e, context=context or f"Execution of {func.__name__}")
        return default_return


def error_boundary(default_return: Any = None, show_error: bool = True):
    """Decorator to catch exceptions in a function and return a default value."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if show_error:
                    handle_error(e, context=f"Error in {func.__name__}")
                return default_return
        return wrapper
    return decorator


def validate_ticker(ticker: str) -> bool:
    """Validates the format of a ticker symbol."""
    if not ticker or not isinstance(ticker, str):
        raise ConfigurationError(
            f"Invalid ticker: {ticker}",
            user_message="銘柄コードが正しくありません。",
            recovery_hint="正しい形式（例: 7203.T）で入力してください。"
        )
    return True


def validate_api_key(name: str, value: Optional[str]) -> bool:
    """Validates if a required API key is present."""
    if not value or value.startswith("YOUR_"):
        raise ConfigurationError(
            f"Missing API Key: {name}",
            user_message=f"{name} が設定されていません。",
            recovery_hint="設定画面から正しいAPIキーを入力してください。"
        )
    return True


class ErrorRecovery:
    """Utility for automatic error recovery strategies."""

    @staticmethod
    def retry_with_backoff(func: Callable, max_retries: int = 3, initial_delay: float = 1.0) -> Any:
        """Retries a function call with exponential backoff on failure."""
        import time
        delay = initial_delay
        last_exception = None
        
        for i in range(max_retries):
            try:
                return func()
            except Exception as e:
                last_exception = e
                logger.warning(f"Retry {i+1}/{max_retries} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
                
        raise last_exception
