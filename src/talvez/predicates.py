from __future__ import annotations
import math
from typing import Any, Callable

def not_true(x: Any) -> bool:
    return not (x is True)

def not_null(a: Any) -> bool:
    return not_true(a is None)

def not_nan(a: Any) -> bool:
    return not (isinstance(a, float) and math.isnan(a))

def not_infinite(a: Any) -> bool:
    return not (isinstance(a, (float, int)) and (a == float("inf") or a == float("-inf")))

def not_undefined(a: Any) -> bool:
    return all([
        not_null(a),
        not_nan(a),
        not_infinite(a),
    ])


def not_empty(a: Any) -> bool:
    try:
        return len(a) > 0  # type: ignore[arg-type]
    except Exception:
        return True

Predicate = Callable[[Any], bool]

def and_(*preds: Predicate) -> Predicate:
    def _combined(a: Any) -> bool:
        for p in preds:
            if not_true(p(a)):
                return False
        return True
    return _combined


def or_(*preds: Predicate) -> Predicate:
    def _combined(a: Any) -> bool:
        for p in preds:
            try:
                if p(a) is True:
                    return True
            except Exception:
                continue
        return False
    return _combined
