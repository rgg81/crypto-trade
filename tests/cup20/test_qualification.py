"""Tests for the CUP-20 conjunctive hard floors.

Every floor is conjunctive: aggregate performance never compensates for one
failed floor, and every comparison must fail closed on a non-finite input.
"""

import pytest

from crypto_trade.cup20.config import load_config
from crypto_trade.cup20.qualification import evaluate_floors

CONFIG = load_config("tournament/cup20/config.toml").raw

PASSING = {
    "net_sharpe": 1.20,
    "double_cost_sharpe": 0.95,
    "triple_cost_sharpe": 0.60,
    "annualized_return": 0.18,
    "double_cost_annualized_return": 0.14,
    "max_drawdown": 0.12,
    "annualized_volatility": 0.10,
    "positive_quarter_fraction": 0.69,
    "positive_fold_count": 4,
    "worst_fold_sharpe": 0.35,
    "annualized_turnover": 14.0,
    "gross_edge_bps_per_turnover": 95.0,
    "cost_share_of_positive_gross": 0.11,
    "top5_day_share": 0.22,
    "max_fold_positive_pnl_share": 0.38,
    "trade_count": 3100,
    "long_gross_pnl": 0.22,
    "short_gross_pnl": 0.15,
}


def _evaluate(**overrides):
    scored = dict(PASSING)
    kwargs = {
        "declared_roles": ("long", "short"),
        "sign_inversion_passes_core": False,
        "neighbourhood_positive_fraction": 0.86,
        "trial_adjusted_confidence": 0.97,
    }
    for key, value in overrides.items():
        if key in kwargs:
            kwargs[key] = value
        else:
            scored[key] = value
    return evaluate_floors(
        scored,
        floors=CONFIG["floors"],
        statistics_config=CONFIG["statistics"],
        research_config=CONFIG["research"],
        **kwargs,
    )


# --- brief Step 1, verbatim -------------------------------------------------


def test_passing_candidate_passes_every_gate():
    gate = _evaluate()
    assert gate.passed
    assert gate.failures == ()


@pytest.mark.parametrize(
    ("override", "expected_failure"),
    [
        ({"net_sharpe": 0.79}, "net_sharpe"),
        ({"double_cost_sharpe": 0.49}, "double_cost_sharpe"),
        ({"triple_cost_sharpe": 0.0}, "triple_cost_sharpe"),
        ({"annualized_return": 0.0}, "annualized_return"),
        ({"max_drawdown": 0.2001}, "max_drawdown"),
        ({"annualized_volatility": 0.0599}, "annualized_volatility"),
        ({"positive_quarter_fraction": 0.49}, "positive_quarter_fraction"),
        ({"positive_fold_count": 2}, "positive_fold_count"),
        ({"worst_fold_sharpe": -0.26}, "worst_fold_sharpe"),
        ({"annualized_turnover": 25.1}, "annualized_turnover"),
        ({"gross_edge_bps_per_turnover": 39.9}, "gross_edge_bps_per_turnover"),
        ({"cost_share_of_positive_gross": 0.31}, "cost_share_of_positive_gross"),
        ({"top5_day_share": 0.36}, "top5_day_share"),
        ({"max_fold_positive_pnl_share": 0.61}, "max_fold_positive_pnl_share"),
        ({"trade_count": 499}, "trade_count"),
        ({"short_gross_pnl": -0.01}, "role_short_gross_pnl"),
        ({"neighbourhood_positive_fraction": 0.69}, "neighbourhood_positive_fraction"),
        ({"trial_adjusted_confidence": 0.89}, "trial_adjusted_confidence"),
        ({"sign_inversion_passes_core": True}, "sign_inversion_not_profitable"),
    ],
)
def test_each_floor_is_individually_binding(override, expected_failure):
    gate = _evaluate(**override)
    assert not gate.passed
    assert expected_failure in gate.failures


def test_undeclared_role_is_not_checked():
    gate = _evaluate(declared_roles=("long",), short_gross_pnl=-5.0)
    assert gate.passed


def test_zero_is_not_positive():
    assert not _evaluate(short_gross_pnl=0.0).passed


def test_missing_metric_fails_closed():
    scored = dict(PASSING)
    del scored["worst_fold_sharpe"]
    with pytest.raises(KeyError):
        evaluate_floors(
            scored,
            floors=CONFIG["floors"],
            statistics_config=CONFIG["statistics"],
            research_config=CONFIG["research"],
            declared_roles=("long", "short"),
            sign_inversion_passes_core=False,
            neighbourhood_positive_fraction=0.86,
            trial_adjusted_confidence=0.97,
        )


def test_non_finite_metric_fails_closed():
    assert not _evaluate(net_sharpe=float("nan")).passed


# --- additional coverage: gate-vector completeness (item c) ----------------
#
# The task instructions call this out explicitly: assert the gate vector
# contains EXACTLY the expected set of gate names, so a future change that
# silently drops a floor from the `checks` dict is caught. None of the
# brief's own tests would notice a dropped gate as long as the remaining
# gates still passed/failed as expected -- `gate.passed`/`gate.failures`
# only look at gates that ARE present.

EXPECTED_TOP_LEVEL_GATE_NAMES = frozenset(
    {
        "net_sharpe",
        "double_cost_sharpe",
        "triple_cost_sharpe",
        "annualized_return",
        "double_cost_annualized_return",
        "max_drawdown",
        "annualized_volatility",
        "positive_quarter_fraction",
        "positive_fold_count",
        "worst_fold_sharpe",
        "annualized_turnover",
        "gross_edge_bps_per_turnover",
        "cost_share_of_positive_gross",
        "top5_day_share",
        "max_fold_positive_pnl_share",
        "trade_count",
        "neighbourhood_positive_fraction",
        "trial_adjusted_confidence",
        "sign_inversion_not_profitable",
    }
)


def test_gate_vector_has_exactly_the_expected_gate_names():
    gate = _evaluate()  # declared_roles=("long", "short")
    expected = EXPECTED_TOP_LEVEL_GATE_NAMES | {"role_long_gross_pnl", "role_short_gross_pnl"}
    assert set(gate.checks) == expected


def test_gate_vector_only_includes_declared_role_names():
    gate = _evaluate(declared_roles=("long",), short_gross_pnl=-5.0)
    expected = EXPECTED_TOP_LEVEL_GATE_NAMES | {"role_long_gross_pnl"}
    assert set(gate.checks) == expected
    assert "role_short_gross_pnl" not in gate.checks


# --- additional coverage: exact inclusive boundary values -------------------
#
# GLOBAL CONSTRAINTS: "Floors are inclusive where the brief says >= or <=;
# test the exact boundary value, not just clearly-passing and
# clearly-failing values." The brief's own parametrized failures use values
# just PAST the boundary (0.79 vs a 0.80 floor, 0.2001 vs a 0.20 ceiling) --
# none of them lands exactly ON it. These values are deliberately literal
# (copied from tournament/cup20/config.toml's [floors]/[statistics]/
# [research] tables) rather than read back out of CONFIG, so a failure here
# also flags unnoticed config drift, not only a `>`-vs-`>=` regression.

INCLUSIVE_BOUNDARY_PASSES = [
    ({"net_sharpe": 0.80}, "net_sharpe"),
    ({"double_cost_sharpe": 0.50}, "double_cost_sharpe"),
    ({"max_drawdown": 0.20}, "max_drawdown"),
    ({"annualized_volatility": 0.06}, "annualized_volatility"),
    ({"positive_quarter_fraction": 0.50}, "positive_quarter_fraction"),
    ({"positive_fold_count": 3}, "positive_fold_count"),
    ({"worst_fold_sharpe": -0.25}, "worst_fold_sharpe"),
    ({"annualized_turnover": 25.0}, "annualized_turnover"),
    ({"gross_edge_bps_per_turnover": 40.0}, "gross_edge_bps_per_turnover"),
    ({"cost_share_of_positive_gross": 0.30}, "cost_share_of_positive_gross"),
    ({"top5_day_share": 0.35}, "top5_day_share"),
    ({"max_fold_positive_pnl_share": 0.60}, "max_fold_positive_pnl_share"),
    ({"trade_count": 500}, "trade_count"),
    ({"neighbourhood_positive_fraction": 0.70}, "neighbourhood_positive_fraction"),
    ({"trial_adjusted_confidence": 0.90}, "trial_adjusted_confidence"),
]


@pytest.mark.parametrize(("override", "gate_name"), INCLUSIVE_BOUNDARY_PASSES)
def test_inclusive_boundary_value_passes(override, gate_name):
    gate = _evaluate(**override)
    assert gate.checks[gate_name] is True
    assert gate.passed


# The brief's own tests already pin the zero boundary for triple_cost_sharpe,
# annualized_return (both in test_each_floor_is_individually_binding) and
# short_gross_pnl (test_zero_is_not_positive). double_cost_annualized_return
# and long_gross_pnl are the two `_positive` gates it never touches.
@pytest.mark.parametrize(
    ("override", "gate_name"),
    [
        ({"double_cost_annualized_return": 0.0}, "double_cost_annualized_return"),
        ({"long_gross_pnl": 0.0}, "role_long_gross_pnl"),
    ],
)
def test_remaining_positive_gates_reject_zero_at_boundary(override, gate_name):
    gate = _evaluate(**override)
    assert gate.checks[gate_name] is False
    assert not gate.passed


# --- additional coverage: exhaustive NaN fail-closed battery (item a) ------
#
# "Add a test that puts NaN into EVERY gated metric in turn and asserts the
# gate fails. Not one representative metric -- every one." All 18 keys
# `scored` must contain, plus neighbourhood_positive_fraction and
# trial_adjusted_confidence (named separately since they arrive as kwargs,
# not through `scored`) = 20 individually-gated numeric inputs. Each
# assertion checks the SPECIFIC gate, not just overall gate.passed, so a bug
# that fails the wrong gate (rather than no gate) would still be caught.

NAN_TARGETS = [
    ("net_sharpe", "net_sharpe"),
    ("double_cost_sharpe", "double_cost_sharpe"),
    ("triple_cost_sharpe", "triple_cost_sharpe"),
    ("annualized_return", "annualized_return"),
    ("double_cost_annualized_return", "double_cost_annualized_return"),
    ("max_drawdown", "max_drawdown"),
    ("annualized_volatility", "annualized_volatility"),
    ("positive_quarter_fraction", "positive_quarter_fraction"),
    ("positive_fold_count", "positive_fold_count"),
    ("worst_fold_sharpe", "worst_fold_sharpe"),
    ("annualized_turnover", "annualized_turnover"),
    ("gross_edge_bps_per_turnover", "gross_edge_bps_per_turnover"),
    ("cost_share_of_positive_gross", "cost_share_of_positive_gross"),
    ("top5_day_share", "top5_day_share"),
    ("max_fold_positive_pnl_share", "max_fold_positive_pnl_share"),
    ("trade_count", "trade_count"),
    ("long_gross_pnl", "role_long_gross_pnl"),
    ("short_gross_pnl", "role_short_gross_pnl"),
    ("neighbourhood_positive_fraction", "neighbourhood_positive_fraction"),
    ("trial_adjusted_confidence", "trial_adjusted_confidence"),
]

# 18 `scored` keys + neighbourhood_positive_fraction + trial_adjusted_confidence.
assert len(NAN_TARGETS) == 20


@pytest.mark.parametrize(("field", "gate_name"), NAN_TARGETS)
def test_every_gated_metric_fails_closed_on_nan(field, gate_name):
    gate = _evaluate(**{field: float("nan")})
    assert gate.checks[gate_name] is False
    assert not gate.passed


# --- additional coverage: +/-inf, sensible in the direction each floor cares
# about (item a) ---------------------------------------------------------
#
# qualification._finite maps ANY non-finite input (nan, +inf, -inf) to NaN,
# so both directions of infinity fail every gate type -- including the
# direction a naive, unguarded comparison would have let through: `inf >=
# floor` is True, `-inf <= ceiling` is True, `inf > 0` is True. The comment
# on each pair below names which direction is the trap (must fail despite
# naively "trivially clearing" the bound) versus the ordinary direction
# (fails for the unremarkable reason too, checked here for completeness).

INFINITY_TARGETS = [
    # _at_least floor: +inf is the trap (naively inf >= floor is True).
    ("net_sharpe", "net_sharpe", float("inf")),
    ("net_sharpe", "net_sharpe", float("-inf")),
    # _at_most ceiling: -inf is the trap (naively -inf <= ceiling is True).
    ("max_drawdown", "max_drawdown", float("inf")),
    ("max_drawdown", "max_drawdown", float("-inf")),
    # _positive: +inf is the trap (naively inf > 0 is True).
    ("triple_cost_sharpe", "triple_cost_sharpe", float("inf")),
    ("triple_cost_sharpe", "triple_cost_sharpe", float("-inf")),
    # role positive check: separate role_values dict indirection, same rule.
    ("short_gross_pnl", "role_short_gross_pnl", float("inf")),
    ("short_gross_pnl", "role_short_gross_pnl", float("-inf")),
    # the two non-`scored` kwargs are also _at_least floors.
    ("neighbourhood_positive_fraction", "neighbourhood_positive_fraction", float("inf")),
    ("trial_adjusted_confidence", "trial_adjusted_confidence", float("inf")),
]


@pytest.mark.parametrize(("field", "gate_name", "value"), INFINITY_TARGETS)
def test_infinite_metric_fails_closed_regardless_of_direction(field, gate_name, value):
    gate = _evaluate(**{field: value})
    assert gate.checks[gate_name] is False
    assert not gate.passed


# --- additional coverage: missing key for an UNDECLARED role (item b) ------
#
# The subtle case the brief documents deliberately: role_values reads BOTH
# long_gross_pnl and short_gross_pnl into a local dict UNCONDITIONALLY,
# before declared_roles is consulted at all -- so a metric that was never
# computed is loud even for a role nobody declared. This is the one raise
# path test_undeclared_role_is_not_checked (brief, above) cannot exercise,
# since that test leaves short_gross_pnl present (just negative).


def test_missing_undeclared_role_metric_still_raises():
    scored = dict(PASSING)
    del scored["short_gross_pnl"]
    with pytest.raises(KeyError, match="short_gross_pnl"):
        evaluate_floors(
            scored,
            floors=CONFIG["floors"],
            statistics_config=CONFIG["statistics"],
            research_config=CONFIG["research"],
            declared_roles=("long",),
            sign_inversion_passes_core=False,
            neighbourhood_positive_fraction=0.86,
            trial_adjusted_confidence=0.97,
        )


def test_unrecognized_declared_role_raises_key_error():
    # role_values only has "long" and "short" entries. A typo'd role name
    # must fail loudly rather than silently never gating that role's floor.
    with pytest.raises(KeyError):
        _evaluate(declared_roles=("longg",))


# --- additional coverage: conjunctivity, proven directly --------------------
#
# "Add a test proving conjunctivity directly: a candidate that fails exactly
# one floor while excelling at everything else must not pass." EXCELLING
# clears every floor by a wide margin; each parametrized case then breaks
# exactly one of them. Asserting `gate.failures == (expected_failure,)`
# (an exact one-element tuple, not just membership) proves both that the
# candidate is rejected AND that no other gate is spuriously tripped by the
# excelling values -- aggregate excellence does not leak into, mask, or
# compensate for the one failure.

EXCELLING = {
    "net_sharpe": 5.0,
    "double_cost_sharpe": 4.5,
    "triple_cost_sharpe": 4.0,
    "annualized_return": 2.0,
    "double_cost_annualized_return": 1.8,
    "max_drawdown": 0.01,
    "annualized_volatility": 0.50,
    "positive_quarter_fraction": 1.0,
    "positive_fold_count": 4,
    "worst_fold_sharpe": 3.0,
    "annualized_turnover": 1.0,
    "gross_edge_bps_per_turnover": 500.0,
    "cost_share_of_positive_gross": 0.01,
    "top5_day_share": 0.05,
    "max_fold_positive_pnl_share": 0.10,
    "trade_count": 100_000,
    "long_gross_pnl": 10.0,
    "short_gross_pnl": 10.0,
}


def _evaluate_excelling(**overrides):
    scored = dict(EXCELLING)
    kwargs = {
        "declared_roles": ("long", "short"),
        "sign_inversion_passes_core": False,
        "neighbourhood_positive_fraction": 0.99,
        "trial_adjusted_confidence": 1.0,
    }
    for key, value in overrides.items():
        if key in kwargs:
            kwargs[key] = value
        else:
            scored[key] = value
    return evaluate_floors(
        scored,
        floors=CONFIG["floors"],
        statistics_config=CONFIG["statistics"],
        research_config=CONFIG["research"],
        **kwargs,
    )


def test_excelling_candidate_passes_every_gate():
    # Validates the EXCELLING fixture itself before the single-floor-failure
    # tests below rely on it as a clean baseline -- mirrors the brief's own
    # test_passing_candidate_passes_every_gate for the PASSING fixture.
    gate = _evaluate_excelling()
    assert gate.passed
    assert gate.failures == ()


@pytest.mark.parametrize(
    ("override", "expected_failure"),
    [
        ({"max_drawdown": 0.99}, "max_drawdown"),
        ({"trade_count": 1}, "trade_count"),
        ({"triple_cost_sharpe": -1.0}, "triple_cost_sharpe"),
    ],
)
def test_conjunctive_gate_rejects_a_candidate_failing_only_one_floor(override, expected_failure):
    gate = _evaluate_excelling(**override)
    assert not gate.passed
    assert gate.failures == (expected_failure,)
