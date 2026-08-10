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


# CONTRACT CHANGE, disclosed explicitly rather than quietly changed. This test previously read
# `test_undeclared_role_is_not_checked` and asserted `gate.passed` for exactly this input -- it
# pinned the defect as the contract. A long/short book whose short sleeve LOST money could declare
# ("long",) and the short-PnL floor would never be evaluated: opting out of a hard floor by
# describing itself differently. Roles are now derived from which sides actually traded, so an
# undeclared-but-traded side is gated AND the mis-declaration is its own failure.
def test_undeclared_but_traded_role_is_still_gated():
    gate = _evaluate(declared_roles=("long",), short_gross_pnl=-5.0)
    assert not gate.passed
    assert gate.checks["role_short_gross_pnl"] is False
    assert gate.checks["declared_roles_match_traded_sides"] is False


def test_declaring_a_role_the_book_never_traded_also_fails():
    # The other direction: a research certificate claiming a short sleeve that does not exist is
    # as much a false statement as one hiding a sleeve that does.
    gate = _evaluate(declared_roles=("long", "short"), short_gross_pnl=0.0)
    assert not gate.passed
    assert gate.checks["declared_roles_match_traded_sides"] is False


def test_short_only_book_passes_on_its_own_terms():
    # The short-only case deferred at Task 9: every single-role test there declared ("long",).
    # A book that only ever shorts declares ("short",), is gated on the short floor alone, and the
    # long floor is neither applied nor silently skipped -- it is absent because no long was traded.
    gate = _evaluate(declared_roles=("short",), long_gross_pnl=0.0)
    assert gate.passed
    assert gate.checks["role_short_gross_pnl"] is True
    assert "role_long_gross_pnl" not in gate.checks
    assert gate.checks["declared_roles_match_traded_sides"] is True


def test_short_only_book_with_a_losing_short_sleeve_fails():
    gate = _evaluate(declared_roles=("short",), long_gross_pnl=0.0, short_gross_pnl=-5.0)
    assert not gate.passed
    assert gate.failures == ("role_short_gross_pnl",)


# --- a side counts only when it is MATERIAL ------------------------------------------------
#
# Nothing upstream filters dust: normalise_unit_gross only divides by gross, and the evaluator
# treats any target above 1e-12 as real. So a long-only book that emitted a single -1e-9 weight at
# one boundary in four years genuinely carries a nanoscale short with a sign-random PnL. Under a
# `!= 0.0` rule that book collected TWO hard-floor failures -- a coin flip on the short floor, and a
# roles mismatch that fired even when the dust sleeve happened to be PROFITABLE, since the check
# compares sets rather than signs. The charter publishes this as a hard floor, so that would be a
# disqualification on a rounding artifact.


def test_a_genuinely_two_sided_book_still_gates_both_roles():
    # A real but small short sleeve: 0.1% of gross activity, a thousand times the threshold. The
    # dust guard must not become a hole a real sleeve fits through.
    gate = _evaluate(declared_roles=("long", "short"), long_gross_pnl=1.0, short_gross_pnl=0.001)
    assert gate.passed
    assert gate.checks["role_short_gross_pnl"] is True
    assert gate.checks["declared_roles_match_traded_sides"] is True

    losing = _evaluate(declared_roles=("long",), long_gross_pnl=1.0, short_gross_pnl=-0.001)
    assert not losing.passed
    assert losing.checks["role_short_gross_pnl"] is False
    assert losing.checks["declared_roles_match_traded_sides"] is False


def test_a_long_only_book_with_a_dust_short_is_not_disqualified():
    # One -1e-9 weight held for one bar through an ordinary move, against a book earning 0.22:
    # ~1e-11 of PnL, five orders of magnitude below the 1e-6 relative threshold.
    gate = _evaluate(declared_roles=("long",), long_gross_pnl=0.22, short_gross_pnl=-1e-11)
    assert gate.passed
    assert gate.checks["declared_roles_match_traded_sides"] is True
    assert "role_short_gross_pnl" not in gate.checks

    # Sign-independent: dust must be ignored whichever way it happened to land. Under the old rule
    # this direction PASSED the coin flip and still failed the set comparison.
    profitable_dust = _evaluate(
        declared_roles=("long",), long_gross_pnl=0.22, short_gross_pnl=+1e-11
    )
    assert profitable_dust.passed


# Declares ("long",) ONLY, so the short gate can appear for exactly one reason: materiality pulled
# it into the union. Declaring both would put it there regardless and prove nothing about the
# threshold. Each row makes |long| + |short| == 1.0, so short_pnl IS the relative magnitude.
@pytest.mark.parametrize(
    ("short_pnl", "is_material"),
    [
        (1e-6, False),  # exactly AT the threshold: strictly greater is required
        (1e-5, True),  # an order of magnitude above it
        (1e-7, False),  # an order of magnitude below it
    ],
)
def test_the_materiality_threshold_is_relative_to_total_gross_activity(short_pnl, is_material):
    gate = _evaluate(
        declared_roles=("long",), long_gross_pnl=1.0 - short_pnl, short_gross_pnl=short_pnl
    )
    assert ("role_short_gross_pnl" in gate.checks) is is_material
    # Same absolute PnL against a book a million times larger is dust, and against one a million
    # times smaller is the whole book -- the threshold has to scale, not sit at a fixed number.
    tiny_book = _evaluate(
        declared_roles=("long",), long_gross_pnl=short_pnl * 10.0, short_gross_pnl=short_pnl
    )
    assert "role_short_gross_pnl" in tiny_book.checks
    huge_book = _evaluate(
        declared_roles=("long",), long_gross_pnl=short_pnl * 1e9, short_gross_pnl=short_pnl
    )
    assert "role_short_gross_pnl" not in huge_book.checks


def test_a_non_finite_side_is_always_material_and_can_never_be_dismissed_as_dust():
    # It cannot be shown small, so it must be gated -- where _positive then fails it. A book with a
    # huge long could otherwise make a NaN short look immaterial by comparison.
    gate = _evaluate(declared_roles=("long",), long_gross_pnl=1e9, short_gross_pnl=float("nan"))
    assert gate.checks["role_short_gross_pnl"] is False
    assert not gate.passed


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
        "declared_roles_match_traded_sides",
    }
)


def test_gate_vector_has_exactly_the_expected_gate_names():
    gate = _evaluate()  # declared_roles=("long", "short")
    expected = EXPECTED_TOP_LEVEL_GATE_NAMES | {"role_long_gross_pnl", "role_short_gross_pnl"}
    assert set(gate.checks) == expected


# CONTRACT CHANGE, disclosed. Previously `test_gate_vector_only_includes_declared_role_names`,
# asserting that a traded-but-undeclared side produced NO gate. That was the defect. The gate set
# is now the union of declared and traded sides.
def test_gate_vector_covers_every_side_the_book_actually_traded():
    gate = _evaluate(declared_roles=("long",), short_gross_pnl=-5.0)
    expected = EXPECTED_TOP_LEVEL_GATE_NAMES | {"role_long_gross_pnl", "role_short_gross_pnl"}
    assert set(gate.checks) == expected


def test_gate_vector_omits_a_side_that_was_neither_declared_nor_traded():
    gate = _evaluate(declared_roles=("short",), long_gross_pnl=0.0)
    expected = EXPECTED_TOP_LEVEL_GATE_NAMES | {"role_short_gross_pnl"}
    assert set(gate.checks) == expected


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


# --- amendment A5: the graded credits must never disagree with the boolean floors ---------------


def test_a_full_credit_agrees_with_the_boolean_floor_for_every_unpriced_gate():
    """The anti-drift guard. Two copies of a threshold that disagree is this build's recurring bug.

    ``UNPRICED_FLOOR_SPECS`` restates thresholds ``evaluate_floors`` also reads. This walks every
    one of them across its boundary and asserts the two agree at each step: credit 1.0 exactly when
    the boolean gate is True, credit < 1.0 exactly when it is False. A typo'd comparison or a
    mis-keyed threshold fails here rather than mis-scoring a team in silence.
    """
    from crypto_trade.cup20.qualification import UNPRICED_FLOOR_SPECS, floor_credits

    floors = CONFIG["floors"]
    for gate, (metric, comparison, floor_key) in UNPRICED_FLOOR_SPECS.items():
        threshold = 0.0 if floor_key is None else float(floors[floor_key])
        step = abs(threshold) * 0.10 if threshold else 0.5
        for value in (threshold - step, threshold, threshold + step):
            gates = _evaluate(**{metric: value})
            scored = dict(PASSING, **{metric: value})
            credit = floor_credits(scored, floors=floors)[gate]
            assert (credit == 1.0) == gates.checks[gate], (
                f"{gate}: value={value} credit={credit} boolean={gates.checks[gate]}"
            )


def test_the_unpriced_specs_never_overlap_what_the_score_already_prices():
    """A floor charged twice -- once in G, once in the factor -- is a floor weighted arbitrarily."""
    from crypto_trade.cup20.qualification import (
        ADMISSION_GATES,
        UNPRICED_FLOOR_SPECS,
    )

    priced_by_g = {
        "worst_fold_sharpe",
        "median_fold_sharpe",
        "max_drawdown",
        "calmar",
        "positive_quarter_fraction",
        "trial_adjusted_confidence",
        "neighbourhood_positive_fraction",
    }
    assert not set(UNPRICED_FLOOR_SPECS) & priced_by_g
    assert not set(UNPRICED_FLOOR_SPECS) & ADMISSION_GATES


def test_a_fully_compliant_book_is_left_alone_by_the_factor():
    """The factor must not silently re-rank books that met every floor it prices."""
    from crypto_trade.cup20.qualification import compliance_factor

    assert compliance_factor(PASSING, floors=CONFIG["floors"]) == 1.0


def test_missing_an_unpriced_floor_costs_something_rather_than_nothing():
    from crypto_trade.cup20.qualification import compliance_factor

    churny = dict(PASSING, annualized_turnover=45.8)
    assert compliance_factor(churny, floors=CONFIG["floors"]) < 1.0
