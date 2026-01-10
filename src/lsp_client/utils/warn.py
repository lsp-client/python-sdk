from __future__ import annotations

import functools
import warnings
from collections.abc import Callable


def deprecated[**P, R](reason: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            name = getattr(func, "__name__", "function")
            warnings.warn(
                f"{name} deprecated: {reason}",
                DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator
