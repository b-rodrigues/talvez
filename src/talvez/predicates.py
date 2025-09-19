from __future__ import annotations
import math
from typing import Any, Callable

Predicate = Callable[[Any], bool]


def not_true(x: Any) -> bool:
    """
    Return True if the argument is NOT the literal boolean True.

    This helper is intentionally strict: it only treats the single object `True`
    as true-ish for the negation test. Any other truthy value (e.g., 1, "yes",
    non‑empty containers) returns True because it is not the singleton `True`.

    Parameters
    ----------
    x : Any
        Value to test for identity with the boolean `True`.

    Returns
    -------
    bool
        False only when `x is True`; True otherwise.

    Examples
    --------
    ```pycon
    >>> not_true(True)
    False
    >>> not_true(False)
    True
    >>> not_true(1)
    True
    >>> not_true("anything")
    True
    ```

    Notes
    -----
    This function is used internally to implement other predicates without
    conflating general truthiness with strict identity to `True`.
    """
    return not (x is True)


def not_null(a: Any) -> bool:
    """
    Return True if the value is not None.

    Parameters
    ----------
    a : Any
        Value to check.

    Returns
    -------
    bool
        True if `a is not None`, False otherwise.

    Examples
    --------
    ```pycon
    >>> not_null(None)
    False
    >>> not_null(0)
    True
    >>> not_null("")
    True
    ```
    """
    # Intentionally phrased via not_true for internal stylistic consistency.
    return not_true(a is None)


def not_nan(a: Any) -> bool:
    """
    Return True if the value is NOT a floating-point NaN (Not-a-Number).

    Parameters
    ----------
    a : Any
        Value to check. Only floats are considered; other types return True.

    Returns
    -------
    bool
        False only when `a` is a float and `math.isnan(a)` is True.

    Examples
    --------
    ```pycon
    >>> not_nan(float("nan"))
    False
    >>> not_nan(3.14)
    True
    >>> not_nan("nan")
    True
    ```
    """
    return not (isinstance(a, float) and math.isnan(a))


def not_infinite(a: Any) -> bool:
    """
    Return True if the value is not positive or negative infinity.

    Parameters
    ----------
    a : Any
        Value to check. Only ints/floats are considered for +/- infinity.

    Returns
    -------
    bool
        False when `a` is +inf or -inf (as a numeric); True otherwise.

    Examples
    --------
    ```pycon
    >>> not_infinite(float("inf"))
    False
    >>> not_infinite(float("-inf"))
    False
    >>> not_infinite(42)
    True
    >>> not_infinite("inf")
    True
    ```
    """
    return not (isinstance(a, (float, int)) and (a == float("inf") or a == float("-inf")))


def not_undefined(a: Any) -> bool:
    """
    Composite predicate: value is neither None, NaN, nor infinite.

    This is a convenience aggregator combining:
      - not_null
      - not_nan
      - not_infinite

    Parameters
    ----------
    a : Any
        Value to test.

    Returns
    -------
    bool
        True only if all component predicates pass.

    Examples
    --------
    ```pycon
    >>> not_undefined(None)
    False
    >>> not_undefined(float("nan"))
    False
    >>> not_undefined(float("inf"))
    False
    >>> not_undefined(0)
    True
    ```
    """
    return all([
        not_null(a),
        not_nan(a),
        not_infinite(a),
    ])


def not_empty(a: Any) -> bool:
    """
    Return True if the object has a length > 0, or if it has no length concept.

    Semantics:
      - If the object implements __len__, returns len(a) > 0.
      - If it does not (AttributeError / TypeError), treats it as "not empty"
        and returns True (optimistic / permissive behavior).

    Parameters
    ----------
    a : Any
        Value or container to check.

    Returns
    -------
    bool
        False only when a length can be determined AND that length is 0.

    Examples
    --------
    ```pycon
    >>> not_empty([])
    False
    >>> not_empty([1])
    True
    >>> not_empty("")
    False
    >>> not_empty("hi")
    True
    >>> class NoLen: pass
    >>> not_empty(NoLen())
    True  # no length concept -> considered not empty
    ```

    Notes
    -----
    Choosing to treat objects without a length as "not empty" avoids false
    negatives on scalar values; adjust if your domain requires stricter checks.
    """
    try:
        return len(a) > 0  # type: ignore[arg-type]
    except Exception:
        return True


def and_(*preds: Predicate) -> Predicate:
    """
    Logical AND combinator for predicates.

    Returns a new predicate that evaluates each provided predicate in order.
    Short-circuits and returns False on the first predicate that does NOT
    strictly return the boolean True (identity check). Any truthy non-True
    value (e.g. 1) is considered a failure, enforcing discipline in predicate
    implementations.

    Parameters
    ----------
    *preds : Predicate
        Predicates of signature (Any) -> bool.

    Returns
    -------
    Predicate
        Composite predicate representing logical conjunction.

    Examples
    --------
    ```pycon
    >>> p = and_(not_null, not_nan, not_infinite)
    >>> p(10)
    True
    >>> p(float("nan"))
    False
    >>> p(None)
    False
    ```

    Edge Cases
    ----------
    - No predicates: returns a predicate that always returns True.
    """
    if not preds:
        return lambda a: True

    def _combined(a: Any) -> bool:
        for p in preds:
            if not_true(p(a)):
                return False
        return True
    return _combined


def or_(*preds: Predicate) -> Predicate:
    """
    Logical OR combinator for predicates.

    Returns a predicate that evaluates each provided predicate in order and
    short-circuits on the first that returns the literal True. Exceptions inside
    individual predicates are swallowed (treated as a non-match) to keep the OR
    robust.

    Parameters
    ----------
    *preds : Predicate
        Predicates of signature (Any) -> bool.

    Returns
    -------
    Predicate
        Composite predicate representing logical disjunction.

    Examples
    --------
    ```pycon
    >>> p = or_(not_null, not_empty)
    >>> p(None)
    False        # both fail
    >>> p("")
    False        # not_null OK but empty string -> not_empty False
    >>> p("x")
    True
    >>> p([])    # not_null True but empty -> not_empty False -> overall False
    False
    ```

    Edge Cases
    ----------
    - No predicates: returns a predicate that always returns False.
    - Non-boolean truthy values returned by individual predicates are ignored
      unless they are exactly True, encouraging explicit boolean returns.
    """
    if not preds:
        return lambda a: False

    def _combined(a: Any) -> bool:
        for p in preds:
            try:
                if p(a) is True:
                    return True
            except Exception:
                continue
        return False
    return _combined
