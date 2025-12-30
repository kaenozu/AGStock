"""
エラーハンドリングユーティリティ

リトライメカニズム、エラー分類、ユーザー向けメッセージ生成などの
エラーハンドリング機能を提供します。
"""

import functools
import logging
import time
from enum import Enum
from typing import Any, Callable, Optional, Tuple, Type

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """エラーカテゴリの分類"""

    NETWORK = "network"  # ネットワーク関連エラー
    DATA = "data"  # データ不足・不正
    PERMISSION = "permission"  # 権限・認証エラー
    RESOURCE = "resource"  # リソース不足（メモリ、ディスク等）
    VALIDATION = "validation"  # バリデーションエラー
    EXTERNAL_API = "external_api"  # 外部API エラー
    UNKNOWN = "unknown"  # 不明なエラー


class RetryableError(Exception):
    """リトライ可能なエラーを示す基底クラス"""


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None,
):
    """
        リトライデコレータ

        Args:
            max_attempts: 最大試行回数
            delay: 初回待機時間（秒）
            backoff: 待機時間の乗数（指数バックオフ）
            exceptions: リトライ対象の例外タプル
            on_retry: リトライ時に呼ばれるコールバック関数

        Example:
            ```python
            @retry(max_attempts=3, delay=1.0, backoff=2.0)
            def fetch_data():
    # ネットワークリクエスト
                pass
            ```
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            current_delay = delay

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1

                    if attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )

                    if on_retry:
                        on_retry(attempt, e)

                    time.sleep(current_delay)
                    current_delay *= backoff

            raise RuntimeError(f"Unexpected error in retry logic for {func.__name__}")

        return wrapper

    return decorator


def classify_error(exception: Exception) -> ErrorCategory:
    """
    例外を分類してErrorCategoryを返す

    Args:
        exception: 分類対象の例外

    Returns:
        ErrorCategory: エラーカテゴリ
    """
    error_str = str(exception).lower()
    error_type = type(exception).__name__.lower()

    # ネットワークエラー
    network_keywords = ["connection", "timeout", "network", "unreachable", "http"]
    if any(kw in error_str or kw in error_type for kw in network_keywords):
        return ErrorCategory.NETWORK

    # データ関連エラー
    data_keywords = ["empty", "not found", "missing", "invalid data", "no data"]
    if any(kw in error_str for kw in data_keywords):
        return ErrorCategory.DATA

    # 権限エラー
    permission_keywords = ["permission", "forbidden", "403", "unauthorized", "401"]
    if any(kw in error_str or kw in error_type for kw in permission_keywords):
        return ErrorCategory.PERMISSION

    # リソースエラー
    resource_keywords = ["memory", "disk", "quota", "limit exceeded"]
    if any(kw in error_str for kw in resource_keywords):
        return ErrorCategory.RESOURCE

    # バリデーションエラー
    if "validation" in error_str or "validation" in error_type:
        return ErrorCategory.VALIDATION

    # 外部APIエラー
    if "api" in error_str or "api" in error_type:
        return ErrorCategory.EXTERNAL_API

    return ErrorCategory.UNKNOWN


def get_user_friendly_message(exception: Exception, context: str = "") -> dict:
    """
    ユーザーフレンドリーなエラーメッセージを生成

    Args:
        exception: 例外オブジェクト
        context: エラーが発生したコンテキスト

    Returns:
        dict: {
            'category': ErrorCategory,
            'title': str,
            'message': str,
            'suggestion': str,
            'technical_details': str
        }
    """
    category = classify_error(exception)

    # カテゴリ別メッセージ
    messages = {
        ErrorCategory.NETWORK: {
            "title": "ネットワークエラー",
            "message": "インターネット接続に問題があります。",
            "suggestion": (
                "• インターネット接続を確認してください\n"
                "• VPNやファイアウォール設定を確認してください\n"
                "• しばらく時間をおいて再試行してください"
            ),
        },
        ErrorCategory.DATA: {
            "title": "データエラー",
            "message": "必要なデータが見つからないか、不正なデータです。",
            "suggestion": (
                "• 銘柄コードが正しいか確認してください\n"
                "• データ期間を調整してください\n"
                "• 別の銘柄で試してください"
            ),
        },
        ErrorCategory.PERMISSION: {
            "title": "権限エラー",
            "message": "アクセス権限がありません。",
            "suggestion": (
                "• APIキーが正しく設定されているか確認してください\n"
                "• サービスの利用上限を確認してください\n"
                "• 必要な権限があるか管理者に確認してください"
            ),
        },
        ErrorCategory.RESOURCE: {
            "title": "リソース不足",
            "message": "システムリソースが不足しています。",
            "suggestion": (
                "• PCのメモリ使用状況を確認してください\n"
                "• ディスク容量を確認してください\n"
                "• 処理する銘柄数を減らしてください"
            ),
        },
        ErrorCategory.VALIDATION: {
            "title": "バリデーションエラー",
            "message": "入力値が不正です。",
            "suggestion": (
                "• 入力値を確認してください\n"
                "• 必須項目が入力されているか確認してください"
            ),
        },
        ErrorCategory.EXTERNAL_API: {
            "title": "外部APIエラー",
            "message": "外部サービスとの通信でエラーが発生しました。",
            "suggestion": (
                "• サービスが正常に稼働しているか確認してください\n"
                "• しばらく時間をおいて再試行してください\n"
                "• APIの利用上限を確認してください"
            ),
        },
        ErrorCategory.UNKNOWN: {
            "title": "予期しないエラー",
            "message": "予期しないエラーが発生しました。",
            "suggestion": (
                "• ページを再読み込みしてください\n"
                "• 別の操作で試してください\n"
                "• 問題が続く場合はログを確認してください"
            ),
        },
    }

    msg_data = messages.get(category, messages[ErrorCategory.UNKNOWN])

    return {
        "category": category,
        "title": msg_data["title"],
        "message": msg_data["message"],
        "suggestion": msg_data["suggestion"],
        "technical_details": (
            f"{context}: {type(exception).__name__}: {str(exception)}"
            if context
            else f"{type(exception).__name__}: {str(exception)}"
        ),
        "context": context,
    }


# よく使うリトライ設定のプリセット
def network_retry(func: Callable) -> Callable:
    """ネットワーク処理用のリトライデコレータ（3回、指数バックオフ）"""
    return retry(
        max_attempts=3,
        delay=1.0,
        backoff=2.0,
        exceptions=(ConnectionError, TimeoutError, IOError),
    )(func)


def api_retry(func: Callable) -> Callable:
    """API呼び出し用のリトライデコレータ（5回、長めの待機）"""
    return retry(max_attempts=5, delay=2.0, backoff=2.0, exceptions=(Exception,))(
        func
    )  # 広範囲のエラーをリトライ


# エラーログヘルパー
def log_error_with_context(exception: Exception, context: str, level: str = "error"):
    """
    コンテキスト付きでエラーをログに記録

    Args:
        exception: 例外オブジェクト
        context: エラーが発生したコンテキスト
        level: ログレベル（'error', 'warning', 'critical'）
    """
    error_info = get_user_friendly_message(exception, context)

    log_message = (
        f"\n{'=' * 60}\n"
        f"Error Category: {error_info['category'].value}\n"
        f"Title: {error_info['title']}\n"
        f"Message: {error_info['message']}\n"
        f"Technical Details: {error_info['technical_details']}\n"
        f"{'=' * 60}"
    )

    log_func = getattr(logger, level, logger.error)
    log_func(log_message)


if __name__ == "__main__":
    # テスト例
    @retry(max_attempts=3, delay=0.5)
    def test_function():
        import random

        if random.random() < 0.7:
            raise ConnectionError("Network timeout")
        return "Success!"

    try:
        result = test_function()
        print(f"Result: {result}")
    except Exception as e:
        error_msg = get_user_friendly_message(e, "test_function")
        print("\nUser-friendly error message:")
        print(f"Title: {error_msg['title']}")
        print(f"Message: {error_msg['message']}")
        print(f"Suggestion:\n{error_msg['suggestion']}")
