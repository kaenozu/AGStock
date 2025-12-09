import time
import logging
import functools
from typing import Callable, Any

logger = logging.getLogger(__name__)

def retry_with_backoff(retries: int = 3, backoff_in_seconds: int = 1):
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        retries: Number of retries before giving up.
        backoff_in_seconds: Initial backoff time in seconds.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        logger.error(f"Function {func.__name__} failed after {retries} retries: {e}")
                        raise e
                    else:
                        sleep = (backoff_in_seconds * 2 ** x)
                        logger.warning(f"Function {func.__name__} failed: {e}. Retrying in {sleep}s...")
                        time.sleep(sleep)
                        x += 1
        return wrapper
    return decorator
