from __future__ import annotations
import warnings
from functools import wraps
from typing import Callable, TypeVar, Any, Optional

from .core import just, nothing, Maybe
from .predicates import not_true

T = TypeVar("T")

def _with_warning_capture(fn: Callable[..., T], allow_warning: bool):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = fn()
        if w and not allow_warning:
            raise RuntimeError(f"Warning converted to failure: {w[0].message}")
        return result

def maybe(ensure: Optional[Callable[[Any], bool]] = None, allow_warning: bool = False):
    ensure_fn = ensure if ensure is not None else (lambda a: True)

    def deco(f: Callable[..., T]):
        @wraps(f)
        def wrapped(*args, **kwargs) -> Maybe[T]:
            try:
                result = _with_warning_capture(lambda: f(*args, **kwargs), allow_warning)
            except Exception:
                return nothing()
            try:
                if not_true(ensure_fn(result)):
                    return nothing()
            except Exception:
                return nothing()
            return just(result)
        return wrapped
    return deco

def perhaps(default: Any, ensure: Optional[Callable[[Any], bool]] = None, allow_warning: bool = False):
    ensure_fn = ensure if ensure is not None else (lambda a: True)

    def deco(f: Callable[..., T]):
        @wraps(f)
        def wrapped(*args, **kwargs) -> Any:
            try:
                result = _with_warning_capture(lambda: f(*args, **kwargs), allow_warning)
            except Exception:
                return default
            try:
                if not_true(ensure_fn(result)):
                    return default
            except Exception:
                return default
            return result
        return wrapped
    return deco
