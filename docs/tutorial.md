# talvez Tutorial

A comprehensive guide to using the talvez library for safe, composable handling of optional values and fallible computations in Python.

---
## 1. Introduction
Talvez provides small functional primitives centered around a `Maybe` type (inspired by Haskell / other FP ecosystems and the R 'maybe' package) 
plus decorators to safely wrap functions and compose computations that may fail.

Core goals:

- Eliminate scattered try/except blocks
- Make failure explicit (via `Nothing`) rather than implicit (exceptions, `None`, magic values)
- Provide ergonomic wrappers (`@maybe`, `@perhaps`) to retrofit existing code
- Offer simple combinators for building pipelines

---
## 2. Installation
```bash
pip install -e .
```
(From within a clone of the repository. A PyPI release can come later.)

---
## 3. The Maybe Type

`Maybe` is a union: either `Just(value)` or `Nothing`.

```python
from talvez import just, nothing, Maybe

x = just(42)          # Just(42)
y = nothing()         # Nothing

assert x.is_just
assert not x.is_nothing
assert y.is_nothing
```

Key methods:

- `fmap(fn)`: Apply a pure function to the wrapped value if present.
- `bind(fn)`: Apply a function returning another `Maybe` (monadic chaining).
- `get_or(default)`: Extract the value or fall back to a default.
- `to_optional()`: Convert to a Python `Optional` (i.e., unwrap to raw value or `None`).

Example:

```python
just(10).fmap(lambda v: v + 5)          # Just(15)
just(10).bind(lambda v: just(v * 3))    # Just(30)
nothing().fmap(lambda v: v + 5)         # Nothing
```

### 3.1 Creating Maybes From Optionals

```python
from talvez import from_optional
from_optional(5)        # Just(5)
from_optional(None)     # Nothing
```

### 3.2 Sequencing a Collection of Maybes

`sequence` short-circuits to `Nothing` if any element is `Nothing`.

```python
from talvez import sequence, just, nothing
sequence(iter([just(1), just(2), just(3)])).get_or([])  # [1, 2, 3]
sequence(iter([just(1), nothing(), just(3)])).is_nothing  # True
```

---
## 4. Wrapping Existing Functions With Decorators

### 4.1 @maybe

`@maybe` converts a function into one that returns a `Maybe` instead of raising or propagating invalid results.

Behavior:
- Catches any exception => returns `Nothing`
- Optionally enforces a predicate (`ensure`) on the result
- Optionally treats warnings as failures (default: warnings fail only if `allow_warning=False` and one is emitted)

```python
from talvez import maybe

@maybe()
def parse_int(x: str) -> int:
    return int(x)

assert parse_int("10").get_or(0) == 10
assert parse_int("xyz").is_nothing
```

With a predicate:
```python
@maybe(ensure=lambda v: v >= 0)
def half(x: int) -> float:
    return x / 2

assert half(10).get_or(None) == 5
assert half(-4).is_nothing  # ensure failed
```

Handling warnings:
```python
import warnings

@maybe(allow_warning=False)
def risky():
    warnings.warn("deprecated")
    return 1

assert risky().is_nothing  # warning converted to failure
```

### 4.2 @perhaps
`@perhaps(default=...)` is like `@maybe` but returns a raw value with a fallback default instead of a `Maybe`.
```python
from talvez import perhaps

@perhaps(default=0)
def safe_div(a, b):
    return a / b

safe_div(10, 2)  # 5.0
safe_div(10, 0)  # 0  (fallback)
```

---
## 5. Predicates and Composition
Predicates are small boolean helpers used with `ensure` or for custom validation.

Available predicates:
- `not_null` – value is not `None`
- `not_nan` – not a floating NaN
- `not_infinite` – not +/- infinity
- `not_undefined` – passes all of: not_null, not_nan, not_infinite
- `not_empty` – if sized, length > 0; otherwise considered ok

Combinators:
- `and_(*preds)` – all predicates must succeed (truthy)
- `or_(*preds)` – any predicate success is enough

Example:
```python
from talvez import maybe, not_null, not_empty, and_

validate = and_(not_null, not_empty)

@maybe(ensure=validate)
def build_name(first: str, last: str) -> str:
    return f"{first.strip()} {last.strip()}"

assert build_name("Ada", "Lovelace").is_just
assert build_name("", "Lovelace").is_nothing
```

---
## 6. Chaining and Pipelines
Talvez exposes utilities to sequence operations that each return a `Maybe`.

### 6.1 Manual Chaining With bind
```python
from talvez import just

result = (just(" 42 ")
          .fmap(str.strip)
          .bind(lambda s: just(int(s)))
          .fmap(lambda i: i * 2))

assert result.get_or(None) == 84
```

### 6.2 chain Utility
```python
from talvez import maybe, just, chain

@maybe()
def step1(x: int): return x + 1
@maybe()
def step2(x: int): return x * 3
@maybe(ensure=lambda v: v < 50)
def step3(x: int): return x + 10

res = chain(just(5), step1, step2, step3)  # ((5+1)*3)+10 = 28
assert res.get_or(None) == 28
```

### 6.3 compose_maybe for Reusable Pipelines
```python
from talvez import compose_maybe
pipeline = compose_maybe(step1, step2, step3)
assert pipeline(just(5)).get_or(None) == 28
```

---
## 7. Error vs Failure Semantics
| Scenario | @maybe outcome | @perhaps outcome |
|----------|----------------|------------------|
| Function raises exception | Nothing | default value |
| Predicate fails | Nothing | default value |
| Warning emitted & allow_warning=False | Nothing | default value |
| Success | Just(value) | value |

This uniform table simplifies reasoning about function reliability.

---
## 8. Interoperability & Migration
### 8.1 Gradual Adoption

Start by wrapping the “edges” of your system:

- Parsing / validation boundaries
- External I/O normalization
- Optional configuration lookups

Then propagate `Maybe` deeper where error branching is currently ad-hoc.

### 8.2 Converting Back to Exceptions (If Needed)

```python
val = parse_int("x")
if val.is_nothing:
    raise ValueError("Invalid integer")
use(val.get_or(0))
```

### 8.3 Using With Type Checkers

Because `Maybe` is a union, type checkers understand that after pattern checks you can treat the value as present.

```python
m = parse_int("12")
if m.is_just:
    reveal_type(m)          # Just[int]
    print(m.value + 10)
```

---
## 9. Advanced Patterns
### 9.1 Lifting Multi-Arg Functions

Wrap first, then partially apply:
```python
from functools import partial

@maybe()
def div(a: int, b: int): return a / b

half = lambda x: div(x, 2)  # returns Maybe
```

### 9.2 Conditional Branching

```python
candidate = parse_int(" 17 ").fmap(lambda v: v - 5)

next_step = (candidate
             .bind(lambda v: just(v) if v % 2 == 0 else nothing())
             .fmap(lambda v: v * 10))
```

### 9.3 Aggregating Independent Maybes
```python
values = [parse_int(s) for s in ["1", "2", "foo", "4"]]
from talvez import sequence
assert sequence(iter(values)).is_nothing  # one failed
```

### 9.4 Decorating Methods
Decorators work on instance or class methods alike. Just remember they wrap the returned value into a `Maybe`.

### 9.5 Integrating With Async (Future Consideration)

Currently decorators are sync. An async variant could:

- Detect coroutine functions
- Await inside wrapper
You can prototype by manually catching exceptions in async code and returning `Just/ Nothing`.

---
## 10. Testing Strategies

When testing functions that return `Maybe`:

- Assert structural form (is_just / is_nothing)
- Assert value via `get_or` or `value` when is_just
- Use property tests to ensure invariants (e.g., mapping identity leaves value unchanged)

Example:
```python
def test_identity_law():
    from talvez import just
    j = just(5)
    assert j.fmap(lambda x: x).get_or(None) == 5
```

---
## 11. Performance Notes

- Overhead is minimal (dataclass + small wrapper logic)
- Suitable for request-level / batch data processing
- Avoid in ultra-hot loops where raw primitives may be faster

Micro-optimizations (only if profiling demands):
- Inline simple predicates
- Batch unwrap with a single pass using `sequence`

---
## 12. Comparison With Alternatives
| Approach | Pros | Cons |
|----------|------|------|
| Exceptions | Native, stack info | Verbose try/except, control-flow via exceptions |
| Returning None | Simple | Ambiguous None vs legitimate None |
| Sentinel Objects | Explicit | Boilerplate per function |
| talvez Maybe | Composable, declarative | Requires adoption pattern |

---
## 13. Common Pitfalls
| Pitfall | Explanation | Fix |
|---------|-------------|-----|
| Forgetting ensure predicate semantics | `ensure` must return True for success | Return explicit boolean |
| Wrapping function that already returns Maybe | You get nested Maybes if you fmap instead of bind | Use `bind` for functions returning Maybe |
| Using value without checking | Accessing `.value` on Nothing is an error | Use `get_or` or guard with `is_just` |

---
## 14. Roadmap Ideas
- Async-aware decorators
- mypy plugin or refined type narrowing
- Additional functional helpers (e.g., `lift2`, `lift3` for multi-arg lifting)
- Integration with validation libraries

---
## 15. Quick Reference
```python
from talvez import just, nothing, maybe, perhaps, chain, compose_maybe

@maybe(ensure=lambda v: v > 0)
def inc(x): return x + 1

res = chain(just(1), inc, inc)
assert res.get_or(None) == 3
```

---
## 16. Closing Thoughts
talvez offers a pragmatic middle ground: functional-style safety without heavy abstractions. Start small—wrap a couple of risky functions—and grow patterns organically.

Feedback & contributions welcome!
