from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, TypeVar, Callable, Union, Optional, Any, Iterator

T = TypeVar("T")
U = TypeVar("U")


class _Nothing:
    __slots__ = ()

    def __repr__(self) -> str:
        return "Nothing"

    def __bool__(self) -> bool:
        return False

    def fmap(self, fn: Callable[[Any], U]) -> "Nothing":
        return self

    def bind(self, fn: Callable[[Any], "Maybe[U]"]) -> "Nothing":
        return self

    def get_or(self, default: U) -> U:
        return default

    def to_optional(self) -> Optional[Any]:
        return None

    @property
    def is_nothing(self) -> bool:
        return True

    @property
    def is_just(self) -> bool:
        return False


Nothing = _Nothing()


@dataclass(frozen=True)
class Just(Generic[T]):
    value: T

    def __repr__(self) -> str:
        return f"Just({self.value!r})"

    def __bool__(self) -> bool:
        return True

    def fmap(self, fn: Callable[[T], U]) -> "Maybe[U]":
        try:
            return just(fn(self.value))
        except Exception:
            return Nothing

    def bind(self, fn: Callable[[T], "Maybe[U]"]) -> "Maybe[U]":
        try:
            result = fn(self.value)
            if not isinstance(result, (Just, _Nothing)):
                raise TypeError("bind function must return a Maybe")
            return result
        except Exception:
            return Nothing

    def get_or(self, default: U) -> Union[T, U]:
        return self.value

    def to_optional(self) -> Optional[T]:
        return self.value

    @property
    def is_nothing(self) -> bool:
        return False

    @property
    def is_just(self) -> bool:
        return True


Maybe = Union[Just[T], _Nothing]


def just(a: T) -> Just[T]:
    return Just(a)


def nothing() -> _Nothing:
    return Nothing


def from_optional(opt: Optional[T]) -> Maybe[T]:
    return nothing() if opt is None else just(opt)


def sequence(maybes: Iterator[Maybe[T]]) -> Maybe[list[T]]:
    out: list[T] = []
    for m in maybes:
        if isinstance(m, _Nothing):
            return Nothing
        out.append(m.value)  # type: ignore[attr-defined]
    return just(out)
