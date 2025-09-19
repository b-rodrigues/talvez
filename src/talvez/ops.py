from __future__ import annotations
from typing import Callable, Any
from .core import Maybe

def chain(m: Maybe[Any], *fns: Callable[[Any], Maybe[Any]]) -> Maybe[Any]:
    """
    Sequentially apply a series of Maybe-producing functions, short-circuiting on the first failure.

    This function implements a left-to-right monadic bind chain. It starts with an
    initial Maybe `m` and applies each function in `fns` to the unwrapped value
    of the current `Just` (via `bind`). If at any point the current value is
    `Nothing`, evaluation stops early and `Nothing` is returned.

    Parameters
    ----------
    m : Maybe[Any]
        The initial Maybe value (typically `just(x)` or `nothing()`).
    *fns : Callable[[Any], Maybe[Any]]
        A variadic sequence of functions. Each function must accept the unwrapped
        value from the previous `Just` and return a new `Maybe`.

    Returns
    -------
    Maybe[Any]
        The resulting Maybe after applying all functions, or the first `Nothing`
        encountered.

    Notes
    -----
    - This is analogous to a fold/ reduce over monadic bind operations.
    - Functions are only invoked if the current accumulator is a `Just`.
    - Any function returning `Nothing` halts further processing.

    Examples
    --------
    >>> from talvez import just, nothing
    >>> def parse_int(s: str):
    ...     try:
    ...         return just(int(s))
    ...     except ValueError:
    ...         return nothing()
    ...
    >>> def reciprocal(x: int):
    ...     return nothing() if x == 0 else just(1 / x)
    ...
    >>> chain(just("10"), parse_int, reciprocal).get_or(None)
    0.1
    >>> chain(just("foo"), parse_int, reciprocal).is_nothing
    True

    Edge Cases
    ----------
    - Passing no functions: returns the original `m`.
    - If `m` is already `Nothing`, no functions are executed.
    """
    current: Maybe[Any] = m
    for fn in fns:
        if current.is_nothing:  # type: ignore[attr-defined]
            break
        current = current.bind(fn)  # type: ignore[arg-type]
    return current


def compose_maybe(*fns: Callable[[Any], Maybe[Any]]):
    """
    Compose multiple Maybe-producing functions into a reusable pipeline.

    Returns a new function that expects an initial `Maybe` and applies the
    provided functions in order using `chain`. This is useful when you want to
    define a processing pipeline once and reuse it across different starting
    values.

    Parameters
    ----------
    *fns : Callable[[Any], Maybe[Any]]
        A sequence of functions, each taking a plain (unwrapped) value and
        returning a `Maybe`.

    Returns
    -------
    Callable[[Maybe[Any]], Maybe[Any]]
        A function that, given an initial `Maybe`, applies the pipeline.

    Examples
    --------
    >>> from talvez import just, nothing
    >>> def non_empty(s: str):
    ...     return just(s) if s else nothing()
    ...
    >>> def to_int(s: str):
    ...     try:
    ...         return just(int(s))
    ...     except ValueError:
    ...         return nothing()
    ...
    >>> def positive(x: int):
    ...         return just(x) if x > 0 else nothing()
    ...
    >>> pipeline = compose_maybe(non_empty, to_int, positive)
    >>> pipeline(just("42")).get_or(None)
    42
    >>> pipeline(just("")).is_nothing
    True
    >>> pipeline(just("-5")).is_nothing
    True

    Comparison
    ----------
    This:
        pipeline = compose_maybe(f1, f2, f3)
        result = pipeline(just(x))
    Is equivalent to:
        result = chain(just(x), f1, f2, f3)

    Edge Cases
    ----------
    - If no functions are provided, the returned runner is the identity on `Maybe`.
    - Fail-fast semantics are inherited from `chain`.
    """
    def runner(m: Maybe[Any]) -> Maybe[Any]:
        return chain(m, *fns)
    return runner
