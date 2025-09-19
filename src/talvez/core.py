"""
Core Maybe type implementation for the `talvez` library.

This module defines a lightweight, Pythonic representation of the classic
"Maybe" (a.k.a. "Option") type common in functional programming. A `Maybe`
value is either a `Just(value)` representing a successful / present result,
or `Nothing` representing absence or failure.

Key Design Goals
----------------
- Minimal runtime overhead (simple dataclass + singleton sentinel).
- Ergonomic chaining via `fmap` (map a pure function) and `bind`
  (chain a function returning another Maybe).
- Explicit, opt-in handling for failure states instead of relying on
  exceptions or `None` ambiguities.
- Interoperability helpers (`from_optional`, `to_optional`, `sequence`).

Typical Usage
-------------
>>> from talvez import just, nothing
>>> j = just(10)
>>> j.fmap(lambda x: x + 5)        # Just(15)
>>> j.bind(lambda x: just(x / 2))  # Just(5.0)
>>> nothing().fmap(lambda x: x+1)  # Nothing

Conversion from standard Python optional values:
>>> from_optional(42)     # Just(42)
>>> from_optional(None)   # Nothing

Batch short-circuiting:
>>> sequence(iter([just(1), just(2)])).get_or([])  # [1, 2]
>>> sequence(iter([just(1), nothing(), just(3)])).is_nothing  # True
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, TypeVar, Callable, Union, Optional, Any, Iterator

T = TypeVar("T")
U = TypeVar("U")


class _Nothing:
    """
    Sentinel singleton representing the absence of a value.

    Behaves as the "empty" variant of the Maybe type. All transformation
    methods (`fmap`, `bind`) return itself, and inspection helpers allow
    safe branching based on presence (`is_nothing`, `is_just`).

    Instances
    ---------
    Only a single shared instance (`Nothing`) is ever created; users
    should obtain it via the `nothing()` factory for clarity.

    Truthiness
    ----------
    Evaluates to False in boolean context:
    >>> bool(nothing())
    False

    Methods
    -------
    fmap(fn): returns Nothing (ignores fn)
    bind(fn): returns Nothing (ignores fn)
    get_or(default): returns the provided default
    to_optional(): returns None
    """

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return "Nothing"

    def __bool__(self) -> bool:
        return False

    # Transformations -------------------------------------------------

    def fmap(self, fn: Callable[[Any], U]) -> "Nothing":
        """
        Functor map: ignore the function and return self.

        Provided for interface parity with `Just`.
        """
        return self

    def bind(self, fn: Callable[[Any], "Maybe[U]"]) -> "Nothing":
        """
        Monadic bind: ignore the function and return self.

        Provided for interface parity with `Just`.
        """
        return self

    # Extraction ------------------------------------------------------

    def get_or(self, default: U) -> U:
        """
        Return the supplied default because no value is present.

        Parameters
        ----------
        default : U
            Fallback to return.

        Returns
        -------
        U
            The provided default.
        """
        return default

    def to_optional(self) -> Optional[Any]:
        """
        Convert to a standard Optional (always None here).

        Returns
        -------
        None
        """
        return None

    # Introspection ---------------------------------------------------

    @property
    def is_nothing(self) -> bool:
        """Return True (this is the Nothing variant)."""
        return True

    @property
    def is_just(self) -> bool:
        """Return False (this is not a Just)."""
        return False


# Public singleton instance
Nothing = _Nothing()


@dataclass(frozen=True)
class Just(Generic[T]):
    """
    Holds a successfully computed / present value.

    Methods mirror those on `_Nothing`, but actually apply the provided
    transformations. Failures during mapping or binding gracefully degrade
    to `Nothing`.

    Parameters
    ----------
    value : T
        The wrapped payload.

    Truthiness
    ----------
    Evaluates to True in boolean context:
    >>> bool(just(0))
    True

    Transformations
    ---------------
    fmap(fn): Apply a pure function, catching exceptions -> Maybe
    bind(fn): Chain a Maybe-returning function, validating return type
    """

    value: T

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"Just({self.value!r})"

    def __bool__(self) -> bool:
        return True

    # Transformations -------------------------------------------------

    def fmap(self, fn: Callable[[T], U]) -> "Maybe[U]":
        """
        Apply a pure function to the contained value.

        Exceptions raised by `fn` cause the result to become `Nothing`.

        Parameters
        ----------
        fn : Callable[[T], U]
            Pure transformation function.

        Returns
        -------
        Maybe[U]
            Just of transformed value, or Nothing on exception.
        """
        try:
            return just(fn(self.value))
        except Exception:
            return Nothing

    def bind(self, fn: Callable[[T], "Maybe[U]"]) -> "Maybe[U]":
        """
        Chain a function returning another Maybe (monadic bind).

        Enforces that `fn` returns either a `Just` or `Nothing`; any
        other return type results in `Nothing`.

        Parameters
        ----------
        fn : Callable[[T], Maybe[U]]
            Function returning a Maybe.

        Returns
        -------
        Maybe[U]
            Result of `fn(self.value)` or Nothing on error / type mismatch.

        Raises
        ------
        (internally caught)
            Any exception from `fn` results in Nothing.
        """
        try:
            result = fn(self.value)
            if not isinstance(result, (Just, _Nothing)):
                raise TypeError("bind function must return a Maybe")
            return result
        except Exception:
            return Nothing

    # Extraction ------------------------------------------------------

    def get_or(self, default: U) -> Union[T, U]:
        """
        Return the wrapped value (ignoring the default).

        Provided for API symmetry with `_Nothing.get_or`.

        Parameters
        ----------
        default : U
            (Unused) placeholder for symmetry.

        Returns
        -------
        T
            The contained value.
        """
        return self.value

    def to_optional(self) -> Optional[T]:
        """
        Convert to a standard Optional (always the underlying value here).

        Returns
        -------
        Optional[T]
            The contained value (never None unless it was explicitly None).
        """
        return self.value

    # Introspection ---------------------------------------------------

    @property
    def is_nothing(self) -> bool:
        """Return False (this is a Just)."""
        return False

    @property
    def is_just(self) -> bool:
        """Return True (this is a Just)."""
        return True


# Public type alias
Maybe = Union[Just[T], _Nothing]


# Factory functions ------------------------------------------------------

def just(a: T) -> Just[T]:
    """
    Wrap a raw value into a `Just`.

    Parameters
    ----------
    a : T
        Value to wrap.

    Returns
    -------
    Just[T]
        A Maybe representing presence.
    """
    return Just(a)


def nothing() -> _Nothing:
    """
    Obtain the `Nothing` sentinel.

    Returns
    -------
    _Nothing
        The shared singleton representing absence.
    """
    return Nothing


def from_optional(opt: Optional[T]) -> Maybe[T]:
    """
    Convert a standard Optional into a Maybe.

    Parameters
    ----------
    opt : Optional[T]
        An optional value (None indicates absence).

    Returns
    -------
    Maybe[T]
        `Just(opt)` if not None, else `Nothing`.
    """
    return nothing() if opt is None else just(opt)


def sequence(maybes: Iterator[Maybe[T]]) -> Maybe[list[T]]:
    """
    Turn an iterator of Maybe values into a Maybe of a list.

    Short-circuits to `Nothing` if any element is `Nothing`; otherwise
    collects unwrapped values into a list.

    Parameters
    ----------
    maybes : Iterator[Maybe[T]]
        Iterator yielding Maybe values.

    Returns
    -------
    Maybe[list[T]]
        Just of collected values if all succeed, else Nothing.

    Examples
    --------
    >>> sequence(iter([just(1), just(2)])).get_or([])
    [1, 2]
    >>> sequence(iter([just(1), nothing(), just(3)])).is_nothing
    True
    """
    out: list[T] = []
    for m in maybes:
        if isinstance(m, _Nothing):
            return Nothing
        out.append(m.value)  # type: ignore[attr-defined]
    return just(out)
