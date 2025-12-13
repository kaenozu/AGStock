"""ユーティリティ関数とサブモジュールをまとめるパッケージ。"""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


def retry_with_backoff(retries: int = 3, backoff_in_seconds: int = 1):
    """
    エクスポネンシャルバックオフ付きで関数をリトライするデコレーター。

    Args:
        retries: 最大リトライ回数。
        backoff_in_seconds: 初回の待機時間（秒）。
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as exc:  # pragma: no cover - re-raises for visibility
                    if attempt == retries:
                        logger.error(
                            "Function %s failed after %s retries: %s",
                            func.__name__,
                            retries,
                            exc,
                        )
                        raise exc
                    sleep = backoff_in_seconds * 2**attempt
                    logger.warning(
                        "Function %s failed: %s. Retrying in %ss...",
                        func.__name__,
                        exc,
                        sleep,
                    )
                    time.sleep(sleep)
                    attempt += 1

        return wrapper

    return decorator


__all__ = [
    "retry_with_backoff",
]
