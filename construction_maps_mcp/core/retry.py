"""Retry decorators with exponential backoff."""

import asyncio
from functools import wraps
from typing import Any, Callable, TypeVar, cast

import backoff

# Type variable for generic functions
F = TypeVar("F", bound=Callable[..., Any])


def async_retry_with_backoff(
    max_tries: int = 3,
    max_time: int = 30,
    exceptions: tuple = (Exception,),
) -> Callable[[F], F]:
    """
    Decorator for async functions with exponential backoff retry.

    Args:
        max_tries: Maximum number of retry attempts
        max_time: Maximum time to spend retrying (seconds)
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @backoff.on_exception(
            backoff.expo,
            exceptions,
            max_tries=max_tries,
            max_time=max_time,
        )
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


def sync_retry_with_backoff(
    max_tries: int = 3,
    max_time: int = 30,
    exceptions: tuple = (Exception,),
) -> Callable[[F], F]:
    """
    Decorator for sync functions with exponential backoff retry.

    Args:
        max_tries: Maximum number of retry attempts
        max_time: Maximum time to spend retrying (seconds)
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @backoff.on_exception(
            backoff.expo,
            exceptions,
            max_tries=max_tries,
            max_time=max_time,
        )
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator
