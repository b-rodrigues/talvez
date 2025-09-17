# talvez

A lightweight Python implementation of a Maybe monad (Just / Nothing) inspired by the R package "maybe".

## Features

- Just(value) and Nothing singleton.
- Decorators:
  - `@maybe(...)` turns a function into one returning `Maybe`.
  - `@perhaps(default=..., ...)` returns raw value or a default.
- Functor map: `fmap`
- Monadic bind: `bind`
- Pipeline helpers: `chain`, `compose_maybe`
- Conversions: `from_optional`, `sequence`
- Predicates and combinators: `not_null`, `not_nan`, `not_infinite`, `not_undefined`, `not_empty`, `and_`, `or_`

## Installation

```bash
pip install talvez
# or (development)
pip install -e .
```

## Quick Start

```python
from talvez import maybe, just

@maybe()
def parse_int(s: str) -> int:
    return int(s)

@maybe(ensure=lambda x: x != 0)
def reciprocal(n: int) -> float:
    return 1 / n

result = (
    parse_int("25")
      .bind(reciprocal)
      .fmap(lambda x: x * 100)
)

print(result)             # Just(4.0)
print(result.get_or(-1))  # 4.0

bad = (
    parse_int("not a number")
      .bind(reciprocal)
      .fmap(lambda x: x * 100)
)
print(bad)  # Nothing
```

## Functor and Monad

- `fmap(fn)` applies a pure transformation: `Maybe a` -> `Maybe b`
- `bind(fn)` sequences a computation returning a `Maybe`: `a -> Maybe b`

```python
from talvez import just
res = just(5).fmap(lambda x: x + 2).bind(lambda x: just(x * 10))
print(res)  # Just(70)
```

## Predicates

```python
from talvez import not_null, not_infinite, and_
p = and_(not_null, not_infinite)
print(p(10))         # True
print(p(float('inf')))  # False
```

## Sequencing Pipelines

Use `chain` for immediate execution:

```python
from talvez import chain, just, maybe

@maybe()
def step1(x: int): return x + 1

@maybe()
def step2(x: int): return x * 2

@maybe(ensure=lambda v: v < 50)
def step3(x: int): return x + 10

result = chain(just(5), step1, step2, step3)
print(result)  # Just(22)
```

Use `compose_maybe` to build a reusable pipeline:

```python
from talvez import compose_maybe, just

pipeline = compose_maybe(step1, step2, step3)
print(pipeline(just(5)))  # Just(22)
```

Rule of thumb:
- Use `chain` for ad-hoc immediate sequences.
- Use `compose_maybe` for reusable or shareable pipelines.

## perhaps Decorator

```python
from talvez import perhaps

@perhaps(default=0)
def parse_int_default(s: str) -> int:
    return int(s)

print(parse_int_default("42"))  # 42
print(parse_int_default("x"))   # 0
```

## Interop

```python
from talvez import from_optional
maybe_val = from_optional(None)      # Nothing
maybe_val2 = from_optional("hello")  # Just("hello")
```

## sequence

```python
from talvez import just, nothing, sequence
values = [just(1), just(2), just(3)]
print(sequence(iter(values)))  # Just([1, 2, 3])

mixed = [just(1), nothing(), just(3)]
print(sequence(iter(mixed)))   # Nothing
```

## Warning Handling

Functions wrapped with `@maybe` or `@perhaps` treat Python warnings as failures unless `allow_warning=True`.

```python
import warnings
from talvez import maybe

@maybe(allow_warning=False)
def noisy():
    warnings.warn("careful")
    return 10

print(noisy())  # Nothing
```

## Testing

```bash
pytest
```

## License

GPL-3.0-or-later