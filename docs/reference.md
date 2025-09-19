# Reference

## Core types

::: talvez.core.Just
::: talvez.core.just
::: talvez.core.Nothing
::: talvez.core.nothing
::: talvez.core.Maybe
::: talvez.core.from_optional
::: talvez.core.sequence

## Decorators

::: talvez.wrappers.maybe
::: talvez.wrappers.perhaps

!!! note "ensure predicate behavior"
    The `ensure` callable MUST return the literal boolean `True` (not just a truthy value) for a result to be accepted. Anything else (False, 1, [], object()) is treated as failure. This is enforced via the `not_true` predicate for defensive programming.

!!! tip "Choosing between maybe() and perhaps()"
    * Use `@maybe()` when you want explicit `Just` / `Nothing` handling.
    * Use `@perhaps(default=...)` when a sentinel fallback is more ergonomic.

## Composition and chaining

::: talvez.ops.chain
::: talvez.ops.runner

## Predicates

::: talvez.predicates.not_true
::: talvez.predicates.not_null
::: talvez.predicates.not_nan
::: talvez.predicates.not_infinite
::: talvez.predicates.not_undefined
::: talvez.predicates.not_empty

## Logical combinators

::: talvez.predicates.not_and_
::: talvez.predicates.not_or_

!!! tip
    These are strict: each predicate must return the literal `True` to be considered a pass. Any other truthy value will fail the conjunction (`and_`) or be ignored in the disjunction (`or_`).

## Common usage patterns

```python
from talvez import maybe, just, nothing, chain, compose_maybe, not_null, and_

@maybe(ensure=lambda x: x > 0)
def positive_delta(x: int) -> int:
    return x - 1

pipeline = compose_maybe(
    lambda x: just(x * 2),
    lambda y: positive_delta(y)  # returns Maybe[int]
)

result = pipeline(just(10))      # Just(19)
failed = pipeline(just(0))       # Nothing
```

## Error & warning handling

- `maybe(..., allow_warning=False)` turns any emitted warning into failure.

- `perhaps(..., allow_warning=True)` will ignore warnings and still return the
  raw value.


## Interoperability

| Purpose | Helper |
|---------|--------|
| Convert Optional[T] to Maybe[T] | `from_optional` |
| Convert Maybe[T] to Optional[T] | `maybe_val.to_optional()` |
| Batch short-circuit across many Maybes | `sequence(iter_of_maybes)` |
