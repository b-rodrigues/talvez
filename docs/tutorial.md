# Tutorial

A comprehensive guide to using the `talvez` library for safe, composable handling of optional values and fallible computations in Python.

---

## 1. Introduction

talvez provides small functional primitives centered around a `Maybe` type, inspired by Haskell, other functional programming ecosystems, and the R 'maybe' package. It includes decorators to safely wrap existing functions and compose computations that might fail.

The core problem `talvez` addresses is the inconsistent and often implicit handling of failures in Python. Functions can fail by raising exceptions, returning `None`, or returning special values like `-1` or `False`. This forces developers to write defensive code with scattered `try/except` blocks and `if value is not None:` checks, making the main logic harder to follow.

**Core goals:**

*   **Eliminate scattered `try/except` blocks:** By wrapping fallible operations, `talvez` contains failures within a predictable structure, allowing you to handle them explicitly when you choose.
*   **Make failure explicit:** Instead of relying on exceptions or ambiguous `None` returns, failure is represented by a single, explicit type: `Nothing`. This makes your function signatures more honest about what they can return.
*   **Provide ergonomic wrappers (`@maybe`, `@perhaps`):** These decorators allow you to easily retrofit existing code to use this safer pattern without major refactoring.
*   **Offer simple combinators for building pipelines:** Easily chain together multiple fallible operations in a readable, robust way.

---

## 2. Installation

To install the library, clone the repository and install it in editable mode:

```bash
# git clone <repository_url>
# cd <repository_name>
pip install -e .
```

(A PyPI release can come later.)

---

## 3. The Maybe Type

The `Maybe` type is the heart of the library. It's a generic container that represents a value that may or may not be present. A `Maybe` is one of two things:

1.  `Just(value)`: A container holding a successful result.
2.  `Nothing`: An empty container representing any kind of failure (an exception occurred, a validation check failed, etc.).

This explicitness is its power. A function that returns `Maybe[int]` tells you it will either give you an `int` (wrapped in `Just`) or it will give you `Nothing`.

```python
from talvez import just, nothing, Maybe

# Create a Maybe holding a value
x = just(42)
print(x)  # Output: Just(42)

# Create a Maybe representing failure
y = nothing()
print(y)  # Output: Nothing

# You can check the state of a Maybe
assert x.is_just is True
assert x.is_nothing is False
assert y.is_nothing is True
```

### Key Methods

A `Maybe`'s value is wrapped and cannot be accessed directly. You interact with it through safe methods.

*   `fmap(fn)`: (Functor map) If the `Maybe` is a `Just`, it applies a regular Python function to the *inner value* and wraps the result in a new `Just`. If it's `Nothing`, it does nothing and returns `Nothing`.

    ```python
    just(10).fmap(lambda v: v + 5)          # Returns Just(15)
    nothing().fmap(lambda v: v + 5)         # Returns Nothing
    just("hello").fmap(str.upper)           # Returns Just('HELLO')
    ```

*   `bind(fn)`: (Monadic bind) This is for chaining functions that *already return a `Maybe`*. If the `Maybe` is a `Just`, `bind` applies the function to the inner value. If it's `Nothing`, it returns `Nothing`. This is the primary tool for building pipelines.

    ```python
    # A function that can fail and returns a Maybe
    def safe_inverse(n: float) -> Maybe[float]:
        return just(1/n) if n != 0 else nothing()

    just(4).bind(safe_inverse)    # Returns Just(0.25)
    just(0).bind(safe_inverse)    # Returns Nothing
    nothing().bind(safe_inverse)  # Returns Nothing
    ```

*   `get_or(default)`: Extracts the value from a `Just` or returns the `default` value if it's `Nothing`. This is how you exit the `Maybe` world.

    ```python
    just(100).get_or(0)    # Returns 100
    nothing().get_or(0)    # Returns 0
    ```

*   `to_optional()`: Converts the `Maybe` to a standard Python `Optional`, returning the raw value or `None`.

    ```python
    just("value").to_optional() # Returns "value"
    nothing().to_optional()     # Returns None
    ```

### 3.1. Creating Maybes From Optionals

The `from_optional` helper function provides a clean way to convert standard Python `None`-based logic into the `Maybe` type.

```python
from talvez import from_optional

# A function that might return None
def find_user(user_id: int) -> str | None:
    if user_id == 1:
        return "Alice"
    return None

maybe_user = from_optional(find_user(1))  # Just('Alice')
maybe_nobody = from_optional(find_user(2)) # Nothing
```

### 3.2. Sequencing a Collection of Maybes

The `sequence` function is used to convert an iterator of `Maybe`s into a single `Maybe` of a list. It short-circuits, meaning if *any* element in the collection is `Nothing`, the entire result is `Nothing`. This is useful for validating multiple inputs at once.

```python
from talvez import sequence, just, nothing

# All succeed
maybes1 = iter([just(1), just(2), just(3)])
result1 = sequence(maybes1)
assert result1.get_or([]) == [1, 2, 3]

# One fails
maybes2 = iter([just(1), nothing(), just(3)])
result2 = sequence(maybes2)
assert result2.is_nothing is True
```

---

## 4. Wrapping Existing Functions With Decorators

Decorators are the most ergonomic way to integrate `talvez` into an existing codebase. They automatically wrap a function's execution, handling exceptions and validation for you.

### 4.1. @maybe

`@maybe` converts a function that could raise an exception or return an invalid result into one that safely returns a `Maybe`.

**Behavior:**
*   **Catches any exception:** If the wrapped function raises any `Exception`, `@maybe` catches it and returns `Nothing`.
*   **Enforces a predicate (`ensure`):** You can provide a function to the `ensure` argument. After the original function executes successfully, its result is passed to the `ensure` function. If it doesn't return `True`, the result is discarded and `Nothing` is returned.
*   **Handles warnings:** By default, warnings are ignored. If you set `allow_warning=False`, any warning emitted during the function's execution will be treated as a failure, causing it to return `Nothing`.

**Basic Example (Exception Handling):**

```python
from talvez import maybe

@maybe()
def parse_int(x: str) -> int:
    return int(x)

# Before: parse_int("xyz") would raise a ValueError.
# After: It safely returns Nothing.
assert parse_int("10").get_or(0) == 10
assert parse_int("xyz").is_nothing is True
```

**With a Predicate:**

The `ensure` predicate validates the *successful return value*.

```python
# We want a function that only returns positive numbers
@maybe(ensure=lambda v: v > 0)
def parse_positive_int(x: str) -> int:
    return int(x)

assert parse_positive_int("123").get_or(None) == 123
assert parse_positive_int("-5").is_nothing    # ensure failed
assert parse_positive_int("abc").is_nothing   # int() raised an exception
```

**Handling Warnings:**

```python
import warnings

@maybe(allow_warning=False)
def risky_operation():
    warnings.warn("This is a deprecated function")
    return 1

# The warning is caught and treated as a failure
assert risky_operation().is_nothing is True

@maybe(allow_warning=True) # The default behavior
def less_risky_operation():
    warnings.warn("This can be ignored")
    return 1

assert less_risky_operation().get_or(None) == 1
```

### 4.2. @perhaps

`@perhaps(default=...)` is a convenient alternative to `@maybe`. It behaves identically in terms of catching exceptions and validating results, but instead of returning a `Maybe` wrapper, it returns the raw value on success and a specified `default` value on any failure.

Use `@perhaps` when you want to immediately fall back to a default value rather than carrying the `Maybe` context forward.

```python
from talvez import perhaps

@perhaps(default=0.0)
def safe_div(a, b):
    return a / b

result1 = safe_div(10, 2)  # 5.0
result2 = safe_div(10, 0)  # 0.0 (fallback on ZeroDivisionError)

# Using @maybe would require an extra step:
# @maybe()
# def maybe_div(a,b): return a/b
# result = maybe_div(10,0).get_or(0.0)
```

---

## 5. Predicates and Composition

Predicates are simple functions that take a value and return `True` or `False`. They are used with the `ensure` argument in decorators to perform validation. `talvez` provides several common predicates out of the box.

*   `not_null`: Checks `value is not None`.
*   `not_nan`: Checks that a float is not `NaN`.
*   `not_infinite`: Checks that a number is not `inf` or `-inf`.
*   `not_undefined`: A combination of `not_null`, `not_nan`, and `not_infinite`.
*   `not_empty`: For sized objects (like strings, lists), checks `len(value) > 0`. For non-sized objects, it passes.

You can combine these predicates using `and_` and `or_` to build more complex validation logic.

*   `and_(*preds)`: Creates a new predicate that succeeds only if all child predicates return `True`.
*   `or_(*preds)`: Creates a new predicate that succeeds if at least one child predicate returns `True`.

**Example:**

Let's create a validator for a user profile name, which must exist and not be empty whitespace.

```python
from talvez import maybe, not_null, not_empty, and_

# This predicate ensures the name is not None and not an empty string.
is_valid_name = and_(not_null, not_empty)

@maybe(ensure=is_valid_name)
def build_name(first: str, last: str) -> str:
    # We strip whitespace before validation, but if the string is empty
    # after stripping, not_empty will catch it.
    full_name = f"{first.strip()} {last.strip()}"
    return full_name if full_name.strip() else ""

assert build_name("Ada", "Lovelace").get_or(None) == "Ada Lovelace"
assert build_name("  ", "Lovelace").is_nothing # Fails not_empty after strip
assert build_name("Grace", "").is_nothing     # Fails not_empty after strip
```

---

## 6. Chaining and Pipelines

The true power of `Maybe` emerges when you compose multiple fallible operations. If any step in the chain fails, the entire subsequent chain is skipped, and `Nothing` is propagated to the end.

### 6.1. Manual Chaining With `bind`

You can manually chain operations using the `bind` method. This is explicit and very readable for simple pipelines.

```python
from talvez import just, maybe

@maybe()
def parse(s: str) -> int:
    return int(s.strip())

@maybe(ensure=lambda i: i > 0)
def ensure_positive(i: int) -> int:
    return i

result = (just("  42  ")
          .bind(parse)                 # Becomes Just(42)
          .bind(ensure_positive)       # Still Just(42)
          .fmap(lambda i: i * 2))      # Becomes Just(84)

assert result.get_or(None) == 84

# A failing example
failing_result = (just(" -10 ")
                  .bind(parse)             # Becomes Just(-10)
                  .bind(ensure_positive)   # Becomes Nothing here
                  .fmap(lambda i: i * 2))  # This step is skipped

assert failing_result.is_nothing is True
```

### 6.2. `chain` Utility

The `chain` utility simplifies the process of applying a sequence of functions that each return a `Maybe`. It is syntactic sugar for a series of `bind` calls.

```python
from talvez import maybe, just, chain

@maybe()
def step1(x: int): return x + 10

@maybe()
def step2(x: int): return x * 3

@maybe(ensure=lambda v: v < 50)
def step3_with_validation(x: int): return x + 5

# Success case
res_ok = chain(just(5), step1, step2, step3_with_validation) # ((5+10)*3)+5 = 50. Fails validation.
# Let's adjust step3 to succeed
@maybe(ensure=lambda v: v <= 50)
def step3_fixed(x: int): return x + 5
res_ok_fixed = chain(just(5), step1, step2, step3_fixed) # ((5+10)*3)+5 = 50. Passes validation.
assert res_ok.is_nothing is True
assert res_ok_fixed.get_or(None) == 50

# Failure case
res_fail = chain(just(10), step1, step2, step3_with_validation) # ((10+10)*3)+5 = 65. Fails validation at step3.
assert res_fail.is_nothing is True
```

### 6.3. `compose_maybe` for Reusable Pipelines

If you have a pipeline that you need to reuse, `compose_maybe` lets you define it once as a single function.

```python
from talvez import compose_maybe

# Using the same step functions from the previous example
pipeline = compose_maybe(step1, step2, step3_fixed)

# Now 'pipeline' is a function that takes a Maybe and runs it through the steps.
assert pipeline(just(5)).get_or(None) == 50
assert pipeline(just(10)).is_nothing is True # Fails at step3
assert pipeline(nothing()).is_nothing is True # Starts with Nothing, remains Nothing
```

---

## 7. Error vs. Failure Semantics

`talvez` standardizes how failures are handled, making your code's behavior predictable.

| Scenario                            | `@maybe` outcome | `@perhaps(default=D)` outcome |
| ----------------------------------- | ---------------- | ----------------------------- |
| Function executes successfully      | `Just(value)`    | `value`                       |
| Function raises an exception        | `Nothing`        | `D` (default value)           |
| `ensure` predicate returns `False`  | `Nothing`        | `D` (default value)           |
| Warning emitted & `allow_warning=False` | `Nothing`        | `D` (default value)           |

This uniform table simplifies reasoning about the reliability and output of any function decorated with `talvez`.

---

## 8. Interoperability & Migration

### 8.1. Gradual Adoption

You don't need to rewrite your entire application to use `talvez`. The best approach is to start at the "edges" of your system—places where your code interacts with the messy outside world.

*   **Parsing / Validation:** Wrap functions that parse user input, config files, or API responses.
*   **External I/O:** Wrap functions that read files, make network requests, or query a database. These can all fail for reasons beyond your control.
*   **Optional Configuration:** Instead of `config.get('key')` which returns `None`, wrap it to return a `Maybe`.

Once the inputs to a system are safely wrapped in `Maybe`, you can propagate that safety inward as needed.

### 8.2. Converting Back to Exceptions (If Needed)

Sometimes you need to interact with a library or framework that expects exceptions. It's easy to exit the "Maybe world" and raise an exception.

```python
@maybe()
def parse_int(x: str) -> int:
    return int(x)

raw_input = "x"
parsed_value = parse_int(raw_input)

if parsed_value.is_nothing:
    raise ValueError(f"Invalid integer provided: {raw_input}")

# Now you can safely use the value
use_value(parsed_value.get_or(0)) # Or just parsed_value.value
```

### 8.3. Using With Type Checkers

Type checkers like Mypy understand `Maybe` because it's defined as a `Union`. This allows you to get static analysis benefits. After you check `is_just`, the type checker knows the value is present.

```python
m = parse_int("12")  # Type of m is Maybe[int]

if m.is_just:
    # Inside this block, the type checker knows `m` is Just[int]
    # and that `m.value` exists and is an `int`.
    print(m.value + 10) # No type error
```

---

## 9. Advanced Patterns

### 9.1. Lifting Multi-Arg Functions

Decorators work best on functions that will be the start of a `chain`. If you have a multi-argument function you want to use mid-pipeline, wrap it first and then use `functools.partial` or a `lambda` to supply the other arguments.

```python
from functools import partial
from talvez import maybe, just, chain

@maybe()
def div(a: int, b: int) -> float:
    return a / b

# We want a pipeline that takes a number and divides it by 2.
# We can't pass `div` directly to `chain` because it needs two arguments.

# Option 1: Lambda
pipeline1 = chain(just(20), lambda x: div(x, 2))
assert pipeline1.get_or(None) == 10.0

# Option 2: functools.partial
safe_div_by_2 = partial(div, b=2)
# Whoops, partial doesn't work that way. We need to flip the arguments.
safe_div_by = lambda numerator, denominator: div(numerator, denominator)
pipeline2 = chain(just(20), lambda x: safe_div_by(x, 2))
assert pipeline2.get_or(None) == 10.0
```

### 9.2. Conditional Branching

You can use `bind` with a `lambda` to introduce conditional logic into a pipeline. If a condition isn't met, you can switch the pipeline to the `Nothing` track.

```python
# A pipeline to process even numbers under 20
result = (just(18)
          .fmap(lambda v: v - 4)  # Becomes Just(14)
          .bind(lambda v: just(v) if v % 2 == 0 else nothing()) # Condition passes
          .fmap(lambda v: v * 10)) # Becomes Just(140)

assert result.get_or(None) == 140

# A failing case
result_fail = (just(17)
              .fmap(lambda v: v - 4) # Becomes Just(13)
              .bind(lambda v: just(v) if v % 2 == 0 else nothing()) # Condition fails, becomes Nothing
              .fmap(lambda v: v * 10)) # Skipped

assert result_fail.is_nothing is True
```

### 9.3. Aggregating Independent Maybes

The `sequence` function is the canonical way to handle this. If you have multiple independent `Maybe` values and you need them all to be `Just` to proceed, `sequence` is the tool.

```python
from talvez import sequence

@maybe()
def get_user_id(username: str) -> int:
    return {"alice": 1, "bob": 2}.get(username)

# Get multiple inputs
user_ids = [get_user_id("alice"), get_user_id("bob")] # [Just(1), Just(2)]
all_good = sequence(iter(user_ids))
assert all_good.get_or(None) == [1, 2]

# One input fails
bad_user_ids = [get_user_id("alice"), get_user_id("charlie")] # [Just(1), Nothing]
one_failed = sequence(iter(bad_user_ids))
assert one_failed.is_nothing is True
```

### 9.4. Decorating Methods

The decorators work on instance methods and class methods just as they do on regular functions. The `self` or `cls` argument is handled correctly.

```python
class Calculator:
    def __init__(self, allow_zero=False):
        self.allow_zero = allow_zero

    @maybe()
    def inverse(self, x: float) -> float:
        if x == 0 and not self.allow_zero:
            raise ValueError("Zero is not allowed")
        return 1 / x

calc = Calculator()
assert calc.inverse(4).get_or(None) == 0.25
assert calc.inverse(0).is_nothing is True
```

---

## 10. Testing Strategies

When testing functions that return `Maybe`, you should test both the success and failure paths explicitly.

*   **Assert the structure:** For a successful input, assert the result `is_just`. For a failing input, assert it `is_nothing`. This is more robust than only checking the unwrapped value.
*   **Assert the value:** For a `Just` result, you can then check its contents using `get_or` or by accessing `.value` after an `is_just` check.
*   **Use property tests:** For functional types like `Maybe`, property-based testing is very effective. For example, for any value `x`, `just(x).fmap(lambda y: y)` should always equal `just(x)`.

**Example Test Case:**

```python
from talvez import just

# Assuming parse_positive_int from a previous example
def test_parse_positive_int_success():
    result = parse_positive_int("100")
    assert result.is_just
    assert result.get_or(0) == 100

def test_parse_positive_int_failure_on_negative():
    result = parse_positive_int("-5")
    assert result.is_nothing

def test_parse_positive_int_failure_on_invalid_string():
    result = parse_positive_int("not a number")
    assert result.is_nothing

def test_fmap_identity_law():
    # Property: mapping the identity function over a Just should not change it.
    j = just(5)
    assert j.fmap(lambda x: x) == j
```

---

## 11. Performance Notes

*   **Minimal Overhead:** The overhead of wrapping a value in a `Just` dataclass or creating a `Nothing` singleton is very small. The logic inside the decorators is also lightweight.
*   **Best Use Cases:** The library is ideal for I/O-bound operations, data processing pipelines, and request-level logic where the clarity and safety gains far outweigh the minuscule performance cost.
*   **Hot Loops:** Avoid using `Maybe` wrappers inside tight, performance-critical loops where millions of operations are performed per second. In those scenarios, traditional error handling or raw primitives might be faster.

If profiling ever indicates a bottleneck, you can make targeted optimizations:
*   Inline simple predicate checks instead of using the `ensure` argument.
*   Use `sequence` to validate a list of items in one go rather than in a Python loop.

---

## 12. Comparison With Alternatives

| Approach           | Pros                                           | Cons                                                                                                |
| ------------------ | ---------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| **Exceptions**     | Native to Python, provides a full stack trace. | Can be verbose (`try/except`), encourages non-local control flow, makes function signatures lie.    |
| **Returning `None`** | Simple and common in Python.                 | Ambiguous: Does `None` mean failure or a valid result? Requires constant `if x is not None` checks. |
| **Sentinel Objects** | Explicit about failure.                        | Requires defining custom sentinel objects, adds boilerplate, not easily composable.                 |
| **`talvez` `Maybe`** | Explicit, composable, clean pipelines, safe. | Introduces a new (but simple) concept, requires a small library dependency.                         |

---

## 13. Common Pitfalls

| Pitfall                                     | Explanation                                                                                                                                    | Fix                                                                                                        |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Forgetting `ensure` predicate semantics** | The `ensure` function must return `True` for the pipeline to continue. Returning `None` or `False` will be treated as a failure.                | Ensure your predicate function always returns an explicit boolean: `return value > 0` not just `value > 0`. |
| **Nesting Maybes by mistake**               | Using `.fmap()` with a function that already returns a `Maybe` will result in a nested `Maybe`, like `Just(Just(5))`.                                | Use `.bind()` when your function returns a `Maybe`. `bind` automatically flattens the result.              |
| **Using `.value` without checking**         | Accessing the `.value` property on a `Nothing` instance will raise an `AttributeError`. The property only exists on `Just`.                       | Always use `.get_or(default)` or guard the access with an `if m.is_just:` check.                           |
| **Applying `chain` to a raw value**         | The `chain` function expects its first argument to be a `Maybe`. Passing a raw value like `chain(5, ...)` will fail.                           | Always start your chain with a `Maybe`, e.g., `chain(just(5), ...)`.                                      |

---

## 14. Roadmap Ideas

*   **Async-aware decorators:** Create `@maybe_async` that can wrap and await coroutine functions.
*   **Mypy Plugin:** A plugin could potentially improve type narrowing and inference for more complex pipeline scenarios.
*   **Additional Helpers:** Add more functional combinators like `lift` to adapt multi-argument functions to work on `Maybe` types seamlessly.
*   **Integration with Validation Libraries:** Create adapters for popular libraries like Pydantic to bridge their validation failures into the `Maybe` ecosystem.

---

## 15. Quick Reference

Here is a small, complete example showcasing the core features.

```python
from talvez import just, maybe, chain

# Step 1: Parse a string, but only if it's a digit.
@maybe(ensure=str.isdigit)
def get_digit_str(s: str) -> str:
    return s.strip()

# Step 2: Convert to integer.
@maybe()
def to_int(s: str) -> int:
    return int(s)

# Step 3: Increment the integer, but only if it's positive.
@maybe(ensure=lambda v: v > 0)
def inc_positive(x: int) -> int:
    return x + 1

# Chain the operations together starting with a raw value
result = chain(just(" 41 "), get_digit_str, to_int, inc_positive)

assert result.get_or(None) == 42

# A failing example
failing_result = chain(just(" -5 "), get_digit_str, to_int, inc_positive)
assert failing_result.is_nothing is True
```

---

## 16. Closing Thoughts

`talvez` offers a pragmatic middle ground between Python's traditional error handling and the all-in approach of purely functional languages. It provides functional-style safety without heavy abstractions or a steep learning curve.

The best way to get started is to find a small, risky part of your codebase—like parsing an API response—and wrap it with `@maybe`. See how it cleans up your logic, and grow the pattern organically from there.

Feedback and contributions are welcome
