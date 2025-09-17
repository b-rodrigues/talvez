from __future__ import annotations
from typing import Callable, Any
from .core import Maybe

def chain(m: Maybe[Any], *fns: Callable[[Any], Maybe[Any]]) -> Maybe[Any]:
    current: Maybe[Any] = m
    for fn in fns:
        if current.is_nothing:  # type: ignore[attr-defined]
            break
        current = current.bind(fn)  # type: ignore[arg-type]
    return current

def compose_maybe(*fns: Callable[[Any], Maybe[Any]]):
    def runner(m: Maybe[Any]) -> Maybe[Any]:
        return chain(m, *fns)
    return runner
