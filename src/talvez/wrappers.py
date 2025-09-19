from __future__ import annotations
import warnings
from functools import wraps
from typing import Callable, TypeVar, Any, Optional

from .core import just, nothing, Maybe
from .predicates import not_true

T = TypeVar("T")


def _with_warning_capture(fn: Callable[..., T], allow_warning: bool):
    """
    Execute a callable while optionally converting emitted warnings into failures.

    This helper centralizes warning capture logic so both `maybe` and `perhaps`
    decorators behave consistently.

    Parameters
    ----------
    fn : Callable[..., T]
        Zero-argument callable (a closure wrapping the original target function
        with its bound *args/**kwargs) to be executed.
    allow_warning : bool
        If False, the presence of at least one warning causes a RuntimeError
        (which upstream decorators interpret as failure). If True, warnings are
        ignored and the result is treated as successful.

    Returns
    -------
    T
        The result of calling `fn()` if no (blocking) warning occurred.

    Raises
    ------
    RuntimeError
        If a warning is emitted and `allow_warning` is False.
    """
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = fn()
        if w and not allow_warning:
            raise RuntimeError(f"Warning converted to failure: {w[0].message}")
        return result


def maybe(
    ensure: Optional[Callable[[Any], bool]] = None,
    allow_warning: bool = False
):
    """
    Decorator factory: wrap a function so it returns a Maybe (Just / Nothing).

    The wrapped function is executed inside a protective layer that:
      1. Captures exceptions -> returns `Nothing`
      2. Optionally treats warnings as failures (`allow_warning=False`)
      3. Applies an `ensure` predicate to the result; non-True -> `Nothing`
      4. Returns `Just(result)` on success

    IMPORTANT: The `ensure` predicate must return the literal boolean `True`
    for acceptance. Returning any other truthy object (e.g., 1, non-empty list)
    will be considered failure because `talvez.predicates.not_true` checks for
    identity with `True`. This enforces discipline and avoids accidental
    truthiness bugs.

    Parameters
    ----------
    ensure : Optional[Callable[[Any], bool]], default=None
        Predicate applied to the successful raw result. If omitted, all results
        are accepted. If the predicate raises an exception or returns anything
        other than the literal `True`, the outcome becomes `Nothing`.
    allow_warning : bool, default=False
        If False, any warning raised during execution causes the decorator to
        return `Nothing`. If True, warnings are ignored.

    Returns
    -------
    Callable[[Callable[..., T]], Callable[..., Maybe[T]]]
        A decorator that transforms a function returning T into one returning
        `Maybe[T]`.

    Examples
    --------
    >>> from talvez import just, nothing
    >>> @maybe()
    ... def parse_int(s: str) -> int:
    ...     return int(s)
    ...
    >>> parse_int("10").get_or(None)
    10
    >>> parse_int("x").is_nothing
    True

    With an ensure predicate:

    >>> @maybe(ensure=lambda v: v > 0)
    ... def delta(x): return x - 1
    ...
    >>> delta(5).is_just
    True
    >>> delta(0).is_nothing   # ensure failed (returns -1)
    True

    Handling warnings:

    >>> import warnings
    >>> @maybe(allow_warning=False)
    ... def risky():
    ...     warnings.warn("deprecated")
    ...     return 42
    ...
    >>> risky().is_nothing
    True
    >>> @maybe(allow_warning=True)
    ... def tolerant():
    ...     warnings.warn("deprecated")
    ...     return 42
    ...
    >>> tolerant().get_or(None)
    42

    Edge Cases
    ----------
    - Exception in function: returns `Nothing`
    - Exception in ensure predicate: returns `Nothing`
    - Warning + allow_warning=False: returns `Nothing`
    - Function returns None and ensure not provided: wraps as Just(None)
      (use ensure to reject None if undesired).
    """
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


def perhaps(
    default: Any,
    ensure: Optional[Callable[[Any], bool]] = None,
    allow_warning: bool = False
):
    """
    Decorator factory: wrap a function so it returns a raw value with fallback.

    Unlike `maybe`, this returns the successful result directly, or a
    user-specified `default` on failure. Failure conditions mirror `maybe`:
      - Exception raised
      - Warning emitted (if `allow_warning=False`)
      - Ensure predicate not returning literal True
      - Ensure predicate raising an exception

    Parameters
    ----------
    default : Any
        The value returned when the wrapped function "fails". Should be a
        sensible sentinel consistent with your domain.
    ensure : Optional[Callable[[Any], bool]], default=None
        Predicate validating the raw result. Must return the literal True to
        accept; any other outcome triggers the fallback.
    allow_warning : bool, default=False
        If False, any warning turns the result into `default`. If True, warnings
        are ignored.

    Returns
    -------
    Callable[[Callable[..., T]], Callable[..., Any]]
        A decorator that converts a function returning T into one returning
        T-or-default.

    Examples
    --------
    >>> @perhaps(default=0)
    ... def safe_div(a, b): return a / b
    ...
    >>> safe_div(10, 2)
    5.0
    >>> safe_div(10, 0)
    0

    With ensure:

    >>> @perhaps(default=None, ensure=lambda v: v > 10)
    ... def compute(x): return x * 3
    ...
    >>> compute(5)
    15
    >>> compute(3)  # 3*3 = 9 -> ensure fails
    None

    Warning handling:

    >>> import warnings
    >>> @perhaps(default=-1, allow_warning=False)
    ... def noisy():
    ...     warnings.warn("careful")
    ...     return 99
    ...
    >>> noisy()
    -1

    Design Rationale
    ----------------
    Use `perhaps` when you want ergonomic fallback semantics without having to
    manipulate a Maybe object explicitly, for contexts where sentinel defaults
    are acceptable and clearly documented.

    Edge Cases
    ----------
    - If the function legitimately returns a value equal to `default`, you
      cannot distinguish fallback vs success—choose a unique sentinel if needed.
    - As with `maybe`, ensure must return literal True (not just truthy).
    """
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
