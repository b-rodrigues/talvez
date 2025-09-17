import warnings
from talvez import (
    just,
    nothing,
    maybe,
    perhaps,
    not_null,
    not_nan,
    not_infinite,
    not_undefined,
    and_,
    or_,
    Just,
    Nothing,
    chain,
    compose_maybe,
)

def test_just_and_nothing():
    assert isinstance(just(1), Just)
    assert nothing().is_nothing

def test_fmap_and_bind():
    j = just(2).fmap(lambda x: x + 3)
    assert repr(j) == "Just(5)"
    res = just(2).bind(lambda x: just(x * 10))
    assert res.get_or(0) == 20
    assert nothing().fmap(lambda x: x).is_nothing

def test_maybe_success():
    @maybe()
    def f(x): return x + 1
    assert f(1).get_or(0) == 2

def test_maybe_failure():
    @maybe()
    def g(x): return 1 / x
    assert g(0).is_nothing

def test_maybe_warning_handling():
    @maybe(allow_warning=False)
    def h():
        warnings.warn("careful!")
        return 5
    assert h().is_nothing

    @maybe(allow_warning=True)
    def k():
        warnings.warn("careful!")
        return 7
    assert k().get_or(0) == 7

def test_perhaps_default():
    @perhaps(default=0)
    def p(x): return int(x)
    assert p("10") == 10
    assert p("x") == 0

def test_ensure_predicate():
    @maybe(ensure=lambda r: r > 0)
    def f(x): return x
    assert f(5).is_just
    assert f(-1).is_nothing

def test_predicates():
    assert not_null(5)
    assert not_nan(3.0)
    assert not not_nan(float("nan"))
    assert not_infinite(10)
    assert not not_infinite(float("inf"))
    assert not_undefined(42)
    assert not not_undefined(float("inf"))

def test_combinators():
    p = and_(not_null, not_undefined)
    assert p(1)
    assert not p(float("inf"))
    q = or_(not_null, lambda x: False)
    assert q(1)

def test_chain():
    @maybe()
    def step1(x: int): return x + 1
    @maybe()
    def step2(x: int): return x * 2
    @maybe(ensure=lambda v: v < 50)
    def step3(x: int): return x + 10

    res = chain(just(5), step1, step2, step3)
    assert res.get_or(None) == 22

def test_compose_maybe():
    @maybe()
    def step1(x: int): return x + 1
    @maybe()
    def step2(x: int): return x * 2
    pipeline = compose_maybe(step1, step2)
    res = pipeline(just(5))
    assert res.get_or(None) == 12

def test_sequence_breaks_on_nothing():
    from talvez import sequence
    vals = [just(1), nothing(), just(3)]
    out = sequence(iter(vals))
    assert out.is_nothing
