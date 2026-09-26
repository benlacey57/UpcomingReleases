import functools
import logging
import time
from typing import Callable, Any
from src.config import settings

logger = logging.getLogger(__name__)

def log_execution(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to log function entry, exit, execution time, and exceptions."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        logger.info(f"Executing '{func.__name__}' with args: {args}, kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"Successfully executed '{func.__name__}' in {elapsed:.4f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed executing '{func.__name__}' after {elapsed:.4f}s: {str(e)}")
            raise
    return wrapper

def feature_flag(flag_name: str, fallback_return: Any = None) -> Callable[..., Any]:
    """Decorator to conditionally execute functions based on Pydantic settings feature flags."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            is_enabled = getattr(settings, flag_name, False)
            if not is_enabled:
                logger.warning(f"Feature flag '{flag_name}' is disabled. Bypassing execution of '{func.__name__}'.")
                return fallback_return
            return func(*args, **kwargs)
        return wrapper
    return decorator

def retry_on_failure(retries: int = 3, delay: float = 1.0) -> Callable[..., Any]:
    """Decorator to retry a function execution upon encountering exceptions."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            while attempt < retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= retries:
                        logger.error(f"Function '{func.__name__}' failed after {retries} attempts.")
                        raise e
                    logger.warning(f"Attempt {attempt} for '{func.__name__}' failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator
