"""Tests for the CUP-20 generalisation-shaped ranking score.

Fifty-eight of one hundred points reward consistency across chronological folds, thirty-five
reward drawdown control, and seven reward multiplicity honesty. The score ranks; it never vetoes
(the hard floors in qualification.py do the disqualifying). `_clamp`'s non-finite handling is
this module's one documented historical bug: an earlier version mapped every non-finite value to
0.0, so a book with the best possible drawdown profile (zero drawdown, positive return -> calmar
= +inf) scored 0 of 15 Calmar points instead of the full 15 -- the ranking inverted at the
extreme. Every test group below states what mutation it is designed to catch.
"""

import dataclasses

import pytest

from crypto_trade.cup20.scoring import RankedEntry, rank_entries, robustness_score, select_advancing

BASE = {
    "worst_fold_sharpe": 0.75,
    "median_fold_sharpe": 1.00,
    "max_drawdown": 0.05,
    "calmar": 1.50,
    "positive_quarter_fraction": 0.875,
    "trial_adjusted_confidence": 1.00,
}


def test_perfect_candidate_scores_one_hundred():
    assert robustness_score(BASE, drawdown_floor=0.20) == pytest.approx(100.0)


def test_floor_candidate_scores_zero():
    worst = {
        "worst_fold_sharpe": -0.25,
        "median_fold_sharpe": 0.25,
        "max_drawdown": 0.20,
        "calmar": 0.0,
        "positive_quarter_fraction": 0.50,
        "trial_adjusted_confidence": 0.90,
    }
    assert robustness_score(worst, drawdown_floor=0.20) == pytest.approx(0.0)


def test_components_are_clamped_and_cannot_exceed_their_weight():
    generous = dict(BASE)
    generous.update({"worst_fold_sharpe": 99.0, "calmar": 99.0, "max_drawdown": 0.0})
    assert robustness_score(generous, drawdown_floor=0.20) == pytest.approx(100.0)


def test_generalisation_outweighs_drawdown():
    consistent = dict(BASE, worst_fold_sharpe=0.75, max_drawdown=0.19, calmar=0.1)
    shallow = dict(BASE, worst_fold_sharpe=-0.25, median_fold_sharpe=0.25, max_drawdown=0.0)
    assert robustness_score(consistent, drawdown_floor=0.20) > robustness_score(
        shallow, drawdown_floor=0.20
    )


def test_holdout_drawdown_floor_rebases_the_component():
    scored = dict(BASE, max_drawdown=0.20)
    assert robustness_score(scored, drawdown_floor=0.25) > robustness_score(
        scored, drawdown_floor=0.20
    )


def test_ranking_is_by_descending_score_then_tie_breaks():
    entries = [
        RankedEntry(
            "team-03",
            "c3",
            50.0,
            dict(BASE, max_drawdown=0.10, worst_fold_sharpe=0.5, annualized_turnover=10.0),
        ),
        RankedEntry(
            "team-01",
            "c1",
            50.0,
            dict(BASE, max_drawdown=0.08, worst_fold_sharpe=0.5, annualized_turnover=10.0),
        ),
        RankedEntry(
            "team-02",
            "c2",
            70.0,
            dict(BASE, max_drawdown=0.15, worst_fold_sharpe=0.5, annualized_turnover=10.0),
        ),
    ]
    ordered = [entry.team_id for entry in rank_entries(entries)]
    assert ordered == ["team-02", "team-01", "team-03"]


def test_tie_break_falls_through_to_team_id():
    scored = dict(BASE, annualized_turnover=10.0)
    entries = [
        RankedEntry("team-05", "c5", 50.0, dict(scored)),
        RankedEntry("team-02", "c2", 50.0, dict(scored)),
    ]
    assert [entry.team_id for entry in rank_entries(entries)] == ["team-02", "team-05"]


def test_select_advancing_never_backfills_beyond_the_qualifier_pool():
    scored = dict(BASE, annualized_turnover=10.0)
    entries = [RankedEntry("team-01", "c1", 60.0, dict(scored))]
    assert len(select_advancing(entries, slots=3)) == 1


def test_select_advancing_truncates_to_the_declared_slots():
    scored = dict(BASE, annualized_turnover=10.0)
    entries = [
        RankedEntry(f"team-{index:02d}", f"c{index}", float(90 - index), dict(scored))
        for index in range(1, 8)
    ]
    advancing = select_advancing(entries, slots=3)
    assert [entry.team_id for entry in advancing] == ["team-01", "team-02", "team-03"]


# =============================================================================================
# Additional coverage, organized by the "pre-empt the defect pattern" checklist. Each section
# states, up front, what mutation it exists to catch.
# =============================================================================================


# --- shared fixtures for isolated-component analysis (item c) ------------------------------
#
# ZERO_CREDIT mirrors the brief's own `worst` fixture from test_floor_candidate_scores_zero
# (identical values, promoted to module scope for reuse): every one of the six components
# clamps to 0 at drawdown_floor=0.20 (test_zero_credit_baseline_actually_scores_zero below
# re-confirms this before anything else relies on it). Overriding exactly one key at a time and
# reading the resulting TOTAL score isolates that component's own contribution: with every other
# component held at zero, the total score IS the isolated component's contribution, with no
# interference from BASE's simultaneous-max-everything construction.

ZERO_CREDIT = {
    "worst_fold_sharpe": -0.25,
    "median_fold_sharpe": 0.25,
    "max_drawdown": 0.20,
    "calmar": 0.0,
    "positive_quarter_fraction": 0.50,
    "trial_adjusted_confidence": 0.90,
}

# (component, value that drives it to full credit, expected isolated contribution == its weight)
FULL_CREDIT_ISOLATION = [
    ("worst_fold_sharpe", 0.75, 30.0),
    ("median_fold_sharpe", 1.00, 20.0),
    ("max_drawdown", 0.05, 20.0),
    ("calmar", 1.50, 15.0),
    ("positive_quarter_fraction", 0.875, 8.0),
    ("trial_adjusted_confidence", 1.00, 7.0),
]


def test_zero_credit_baseline_actually_scores_zero():
    assert robustness_score(ZERO_CREDIT, drawdown_floor=0.20) == pytest.approx(0.0)


@pytest.mark.parametrize(("component", "value", "expected_weight"), FULL_CREDIT_ISOLATION)
def test_each_component_in_isolation_contributes_exactly_its_own_weight(
    component, value, expected_weight
):
    scored = dict(ZERO_CREDIT, **{component: value})
    assert robustness_score(scored, drawdown_floor=0.20) == pytest.approx(expected_weight)


def test_component_weights_sum_to_exactly_one_hundred():
    # States the "these six weights are a 100-point objective" invariant directly and by itself,
    # rather than leaving it implied by six separate per-component assertions elsewhere. Verified
    # empirically (not just reasoned about) what this catches versus what it doesn't, by mutation
    # -- see task-10-report.md for the full transcript:
    #   * A NON-compensating weight edit (e.g. 30.0 -> 35.0 with nothing offsetting it) fails
    #     this test (105 != 100) -- but it also fails test_perfect_candidate_scores_one_hundred
    #     AND the affected row of test_each_component_in_isolation_contributes_exactly_its_own_
    #     weight, so this test is not what uniquely catches that case.
    #   * A COMPENSATING two-weight rebalance (e.g. worst_fold_sharpe 30 -> 25 *and* calmar
    #     15 -> 20, sum still 100) is the case this test cannot catch either -- confirmed by
    #     direct mutation, both this test and test_perfect_candidate_scores_one_hundred keep
    #     passing. What DOES catch it is test_each_component_in_isolation_contributes_exactly_
    #     its_own_weight, whose six rows each pin an independent, hand-derived literal (30.0,
    #     20.0, 20.0, 15.0, 8.0, 7.0): any single weight drifting away from its own literal
    #     fails that row regardless of what any other weight does to compensate.
    # This test's honest job is documentation-as-code for the 100-point objective, and a
    # backstop against a future refactor of robustness_score (e.g. to loop over a weight table)
    # under which the isolated-contribution technique might stop being a lossless per-component
    # probe -- not a claim of unique detection power over the per-component test above.
    total = sum(
        robustness_score(dict(ZERO_CREDIT, **{component: value}), drawdown_floor=0.20)
        for component, value, _ in FULL_CREDIT_ISOLATION
    )
    assert total == pytest.approx(100.0)


# --- non-finite orientation, per component, isolated (items a + c) -------------------------
#
# `_clamp` itself only ever sees the POST-TRANSFORM "larger is better" clamp argument, and is
# direction-agnostic: nan -> 0.0, +inf -> 1.0, -inf -> 0.0. Five of the six components pass
# their raw metric into that argument through a POSITIVE affine transform (or none), so for
# those five the naive pattern "raw nan -> nothing, raw +inf -> full credit, raw -inf ->
# nothing" holds directly. max_drawdown's argument is `(drawdown_floor - raw) / span` -- a
# NEGATIVE affine transform, because a SMALLER raw drawdown is what's better -- so that one
# component's raw-metric orientation is inverted: raw +inf drawdown is the worst possible book
# (zero credit, not full), raw -inf drawdown is algebraically the best possible book (full
# credit, not zero). Each row is verified against the correct orientation for THAT component's
# own raw metric, not copy-pasted from the other five.

NON_FINITE_ORIENTATION = [
    # component, raw override value, expected TOTAL score (others held at ZERO_CREDIT)
    #
    # Amendment A5: the worst end of each component now earns MINUS its weight rather than zero.
    # Under the old clamp, "infinitely bad" and "merely at the threshold" both scored zero on the
    # term, so the score could not tell them apart. Orientation is what these rows exist to pin, and
    # it is unchanged -- only the magnitude of the worst case moved, from 0 to -weight.
    ("worst_fold_sharpe", float("nan"), 0.0),
    ("worst_fold_sharpe", float("inf"), 30.0),
    ("worst_fold_sharpe", float("-inf"), -30.0),
    ("median_fold_sharpe", float("nan"), 0.0),
    ("median_fold_sharpe", float("inf"), 20.0),
    ("median_fold_sharpe", float("-inf"), -20.0),
    ("max_drawdown", float("nan"), 0.0),
    ("max_drawdown", float("inf"), -20.0),  # inverted: infinite drawdown is the worst book
    ("max_drawdown", float("-inf"), 20.0),  # inverted: -inf drawdown is algebraically the best
    ("calmar", float("nan"), 0.0),
    ("calmar", float("inf"), 15.0),  # the historical bug's exact scenario
    ("calmar", float("-inf"), -15.0),
    ("positive_quarter_fraction", float("nan"), 0.0),
    ("positive_quarter_fraction", float("inf"), 8.0),
    ("positive_quarter_fraction", float("-inf"), -8.0),
    ("trial_adjusted_confidence", float("nan"), 0.0),
    ("trial_adjusted_confidence", float("inf"), 7.0),
    ("trial_adjusted_confidence", float("-inf"), -7.0),
]

# 6 components x {nan, +inf, -inf}; pins the battery's own breadth so a future edit can't
# silently shrink it without a visible assertion failure.
assert len(NON_FINITE_ORIENTATION) == 18


@pytest.mark.parametrize(("component", "value", "expected_score"), NON_FINITE_ORIENTATION)
def test_non_finite_raw_metric_earns_the_correctly_oriented_credit(
    component, value, expected_score
):
    scored = dict(ZERO_CREDIT, **{component: value})
    assert robustness_score(scored, drawdown_floor=0.20) == pytest.approx(expected_score)


def test_calmar_positive_infinity_scores_the_same_full_credit_as_an_ordinary_1_5_calmar_book():
    # The task's own worked example, made concrete and comparative: a book with zero drawdown
    # and positive return (calmar = +inf) must not rank BELOW an ordinary book whose calmar is
    # merely 1.50. Both must earn the full 15/15 -- the ranking must not invert at the extreme.
    infinite_calmar = dict(ZERO_CREDIT, calmar=float("inf"))
    ordinary_calmar = dict(ZERO_CREDIT, calmar=1.50)
    infinite_score = robustness_score(infinite_calmar, drawdown_floor=0.20)
    ordinary_score = robustness_score(ordinary_calmar, drawdown_floor=0.20)
    assert infinite_score == pytest.approx(15.0)
    assert ordinary_score == pytest.approx(15.0)
    assert infinite_score == pytest.approx(ordinary_score)


# --- finite saturation, both directions, general clamp branch (item b) ---------------------
#
# Distinct from the dedicated +inf/-inf equality checks in _clamp: these values are finite but
# land outside [0, 1] once the affine transform is applied, so they exercise `min(1.0, max(0.0,
# value))` specifically -- a different code path than the equality checks even where the output
# happens to coincide. The brief's own test_components_are_clamped_and_cannot_exceed_their_
# weight already covers UPPER saturation (worst_fold_sharpe/calmar = 99.0) and, via
# max_drawdown=0.0, max_drawdown's upper-argument saturation too. Not covered anywhere else:
# LOWER saturation (finite, not -inf) for any component, or an exact mid-range (non-boundary,
# non-saturated) arithmetic value for either orientation.

FINITE_GENERAL_BRANCH = [
    # component, value, expected total (rest of the dict left at BASE's own full-credit values)
    #
    # Amendment A5 replaced the lower clamp with a decaying tail, so the two out-of-range rows no
    # longer SATURATE -- that was the defect: a book at 21% drawdown and one at 95% scored
    # identically, and the ranking could not order them. Mid-range rows are untouched by A5, which
    # is the property that matters: the tail changes nothing above a threshold.
    ("worst_fold_sharpe", -5.0, 100.0 - 30.0 - 24.782608695652176),  # arg -4.75 -> -0.826087
    ("max_drawdown", 0.50, 100.0 - 20.0 - 13.333333333333334),  # arg -2.0 -> -0.666667
    ("worst_fold_sharpe", 0.25, 85.0),  # exact mid-range: arg=0.5 -> half of 30=15; 100-30+15
    ("max_drawdown", 0.125, 90.0),  # exact mid-range, inverted: arg=0.5 -> half of 20=10; 100-20+10
]


def test_the_decaying_tail_orders_books_that_the_old_clamp_could_not():
    """The defect A5 fixes, pinned so it cannot come back.

    Under the clamp, 21% and 95% drawdown both scored 41.789 and worst folds of -0.26 and -40.0
    both scored 38.173. A score that returns the same number for a survivable book and a ruinous
    one is not ranking them; it is deferring to whichever tie-break runs next, and only when every
    other term happens to agree exactly.
    """
    base = {
        "worst_fold_sharpe": 0.195,
        "median_fold_sharpe": 0.870,
        "max_drawdown": 0.127,
        "calmar": 0.877,
        "positive_quarter_fraction": 0.647,
        "trial_adjusted_confidence": 0.839,
    }
    drawdowns = [robustness_score(dict(base, max_drawdown=d), drawdown_floor=0.20)
                 for d in (0.21, 0.50, 0.95)]
    assert drawdowns == sorted(drawdowns, reverse=True)
    assert len(set(drawdowns)) == 3

    folds = [robustness_score(dict(base, worst_fold_sharpe=w), drawdown_floor=0.20)
             for w in (-0.26, -5.0, -40.0)]
    assert folds == sorted(folds, reverse=True)
    assert len(set(folds)) == 3


def test_the_tail_never_lets_one_term_swamp_the_other_five():
    """Hyperbolic, not linear: the tail approaches -1 and never passes it.

    A linear continuation would let a single catastrophic term dominate without limit, so one bad
    fold could outrank every other property of the book combined. Each term stays inside its own
    weight.
    """
    from crypto_trade.cup20.scoring import _decaying

    assert _decaying(-1e12) > -1.0
    assert _decaying(float("-inf")) == -1.0
    assert _decaying(-1e12) < _decaying(-1e6) < _decaying(-1.0) < 0.0


@pytest.mark.parametrize(("component", "value", "expected_score"), FINITE_GENERAL_BRANCH)
def test_finite_out_of_range_and_mid_range_values_use_the_general_clamp_branch(
    component, value, expected_score
):
    scored = dict(BASE, **{component: value})
    assert robustness_score(scored, drawdown_floor=0.20) == pytest.approx(expected_score)


# --- drawdown_floor validation branches (item b) --------------------------------------------
#
# Both raises exist in the given implementation but neither is exercised by the brief's own
# nine tests. 0.20 (in-sample) and 0.25 (holdout) are the two production floors (tournament/
# cup20/config.toml's [floors].max_drawdown and [holdout].max_drawdown respectively) -- both
# comfortably clear the 0.05 full-credit level exercised here.


@pytest.mark.parametrize("floor", [0.0, -0.10])
def test_non_positive_drawdown_floor_is_rejected(floor):
    with pytest.raises(ValueError, match="drawdown_floor must be positive"):
        robustness_score(BASE, drawdown_floor=floor)


@pytest.mark.parametrize("floor", [0.05, 0.03])
def test_drawdown_floor_at_or_below_the_full_credit_level_is_rejected(floor):
    with pytest.raises(ValueError, match="must exceed the 0.05 full-credit level"):
        robustness_score(BASE, drawdown_floor=floor)


# --- tie-break levels, each proven reachable on its own (items b + c) ----------------------
#
# "Add a test that each tie-break level actually fires, by constructing entries equal on every
# prior level. If a tie-break is unreachable because an earlier key already separates the
# entries, the test proves nothing." Each test below constructs two entries equal on every PRIOR
# level, differing only at the level under test, with team_id assigned ADVERSARIALLY: the
# intended winner always gets the alphabetically LATER id ("team-99"), the loser the earlier one
# ("team-01"). If the level under test were silently dropped from the sort key, the entries
# would fall straight through to team_id and rank in the OPPOSITE order -- so each test only
# passes if that specific level is doing the work, not team_id accidentally agreeing with it.


def test_tie_break_level_1_max_drawdown_lower_wins():
    winner = RankedEntry(
        "team-99",
        "cw",
        50.0,
        dict(BASE, max_drawdown=0.05, worst_fold_sharpe=0.5, annualized_turnover=10.0),
    )
    loser = RankedEntry(
        "team-01",
        "cl",
        50.0,
        dict(BASE, max_drawdown=0.15, worst_fold_sharpe=0.5, annualized_turnover=10.0),
    )
    ordered = [entry.team_id for entry in rank_entries([loser, winner])]
    assert ordered == ["team-99", "team-01"]


def test_tie_break_level_2_worst_fold_sharpe_higher_wins():
    winner = RankedEntry(
        "team-99",
        "cw",
        50.0,
        dict(BASE, max_drawdown=0.10, worst_fold_sharpe=0.9, annualized_turnover=10.0),
    )
    loser = RankedEntry(
        "team-01",
        "cl",
        50.0,
        dict(BASE, max_drawdown=0.10, worst_fold_sharpe=0.2, annualized_turnover=10.0),
    )
    ordered = [entry.team_id for entry in rank_entries([loser, winner])]
    assert ordered == ["team-99", "team-01"]


def test_tie_break_level_3_annualized_turnover_lower_wins():
    winner = RankedEntry(
        "team-99",
        "cw",
        50.0,
        dict(BASE, max_drawdown=0.10, worst_fold_sharpe=0.5, annualized_turnover=5.0),
    )
    loser = RankedEntry(
        "team-01",
        "cl",
        50.0,
        dict(BASE, max_drawdown=0.10, worst_fold_sharpe=0.5, annualized_turnover=20.0),
    )
    ordered = [entry.team_id for entry in rank_entries([loser, winner])]
    assert ordered == ["team-99", "team-01"]


def test_tie_break_level_4_team_id_full_chain():
    # The brief's own test_tie_break_falls_through_to_team_id already proves this for two
    # teams; this reinforces it across a three-team chain fed in shuffled input order.
    scored = dict(BASE, max_drawdown=0.10, worst_fold_sharpe=0.5, annualized_turnover=10.0)
    entries = [
        RankedEntry("team-12", "c12", 50.0, dict(scored)),
        RankedEntry("team-01", "c01", 50.0, dict(scored)),
        RankedEntry("team-05", "c05", 50.0, dict(scored)),
    ]
    ordered = [entry.team_id for entry in rank_entries(entries)]
    assert ordered == ["team-01", "team-05", "team-12"]


# --- non-finite tie-break metrics now fail loudly, not silently (fix round 1, finding 1) ---
#
# Coordinator finding: rank_entries had no floor upstream to actually rely on -- the reviewer
# grepped the package and found rank_entries/robustness_score/select_advancing have zero
# callers outside this test file, so "Task 6/9 already guarantee finite input" was not a
# designed safeguard, just the absence of any real caller at all. The brief's own global
# constraint ("ranking must be a total order -- no dependence on input sequence") carries no
# upstream-filtering carve-out. Fixed by failing closed instead of inventing a NaN/+inf/-inf
# ordering policy across three differently-oriented fields: `_finite_tie_break` raises
# `ValueError` naming the offending team and field, mirroring qualification.py's own convention
# ("a missing key raises; a non-finite value fails"). This SUPERSEDES three tests this fix round
# removed: a 6-case battery asserting +inf/-inf resolved a winner directionally (they now raise,
# same as NaN, instead of resolving anything); a test asserting NaN "does not crash the sort"
# (it now DOES raise, intentionally -- that is the fix); and a test that documented the
# permutation-invariance gap as a known, unfixed limitation (the gap is closed: a non-finite
# tie-break value can no longer silently reach any comparison, input-order-dependent or not).

NON_FINITE_TIE_BREAK_FIELDS = ["max_drawdown", "worst_fold_sharpe", "annualized_turnover"]
NON_FINITE_TIE_BREAK_VALUES = [float("nan"), float("inf"), float("-inf")]


@pytest.mark.parametrize("field", NON_FINITE_TIE_BREAK_FIELDS)
@pytest.mark.parametrize("value", NON_FINITE_TIE_BREAK_VALUES)
def test_non_finite_tie_break_metric_raises_naming_the_team_and_field(value, field):
    # A single entry is enough: the finiteness check runs unconditionally while building each
    # entry's sort key -- the same "eager, not lazy" evaluation already proven by
    # test_missing_tie_break_metric_raises_even_when_scores_differ below -- so it does not
    # require an actual tie, or even a second entry, to fire.
    scored = dict(BASE, max_drawdown=0.10, worst_fold_sharpe=0.5, annualized_turnover=10.0)
    scored[field] = value
    entries = [RankedEntry("team-07", "c7", 50.0, scored)]
    with pytest.raises(ValueError) as excinfo:
        rank_entries(entries)
    message = str(excinfo.value)
    assert "team-07" in message
    assert field in message


def test_select_advancing_also_raises_on_a_non_finite_tie_break_metric():
    # Not explicitly requested, but cheap and directly on point: select_advancing delegates
    # straight to rank_entries, and it is the function that actually picks who advances -- the
    # guard must be visible through that entry point too, not just the one this fix round tests
    # most heavily.
    scored = dict(BASE, max_drawdown=float("nan"), worst_fold_sharpe=0.5, annualized_turnover=10.0)
    entries = [RankedEntry("team-07", "c7", 50.0, scored)]
    with pytest.raises(ValueError, match="max_drawdown"):
        select_advancing(entries, slots=3)


def test_all_finite_tie_break_metrics_rank_normally_after_the_finiteness_guard():
    # The guard must not false-positive on legitimate data. Reuses the same multi-level tie
    # structure as test_ranking_is_invariant_to_input_order_across_all_tie_break_levels below
    # (unique top score; a tie broken first by drawdown, then by worst_fold_sharpe; unique
    # bottom score) to prove the fix leaves ordinary, all-finite ranking untouched.
    top = RankedEntry(
        "team-04",
        "c4",
        80.0,
        dict(BASE, max_drawdown=0.10, worst_fold_sharpe=0.5, annualized_turnover=10.0),
    )
    tied_best = RankedEntry(
        "team-01",
        "c1",
        60.0,
        dict(BASE, max_drawdown=0.05, worst_fold_sharpe=0.9, annualized_turnover=10.0),
    )
    tied_worst = RankedEntry(
        "team-07",
        "c7",
        60.0,
        dict(BASE, max_drawdown=0.05, worst_fold_sharpe=0.5, annualized_turnover=10.0),
    )
    bottom = RankedEntry(
        "team-11",
        "c11",
        40.0,
        dict(BASE, max_drawdown=0.20, worst_fold_sharpe=0.1, annualized_turnover=10.0),
    )
    ordered = [entry.team_id for entry in rank_entries([bottom, tied_worst, top, tied_best])]
    assert ordered == ["team-04", "team-01", "team-07", "team-11"]


def test_missing_tie_break_metric_raises_even_when_scores_differ():
    # sorted(key=...) computes the FULL key tuple for every element up front (decorate-sort-
    # undecorate), regardless of whether a tie-break would ever be consulted. A `scored` dict
    # missing a tie-break key must therefore fail loudly even when scores alone would have
    # fully ordered the entries -- proving the key function isn't lazily short-circuited.
    complete = dict(BASE, max_drawdown=0.10, worst_fold_sharpe=0.5, annualized_turnover=10.0)
    incomplete = dict(BASE, max_drawdown=0.10, worst_fold_sharpe=0.5)  # no annualized_turnover
    entries = [
        RankedEntry("team-01", "c1", 90.0, complete),
        RankedEntry("team-02", "c2", 10.0, incomplete),
    ]
    with pytest.raises(KeyError, match="annualized_turnover"):
        rank_entries(entries)


# --- permutation invariance for the realistic (finite) domain (global constraint) -----------
#
# "Determinism: identical inputs always produce identical ordering. Ranking must be a total
# order -- no dependence on input sequence." Five entries: a unique top score, a three-way tie
# at score=60 broken across two different tie-break levels (drawdown, then worst_fold_sharpe),
# and a unique bottom score. Three different input orderings of the SAME five entries must all
# produce the identical output sequence.


def test_ranking_is_invariant_to_input_order_across_all_tie_break_levels():
    top = RankedEntry(
        "team-04",
        "c4",
        80.0,
        dict(BASE, max_drawdown=0.10, worst_fold_sharpe=0.5, annualized_turnover=10.0),
    )
    tied_best = RankedEntry(
        "team-01",
        "c1",
        60.0,
        dict(BASE, max_drawdown=0.05, worst_fold_sharpe=0.9, annualized_turnover=10.0),
    )
    tied_middle = RankedEntry(
        "team-07",
        "c7",
        60.0,
        dict(BASE, max_drawdown=0.05, worst_fold_sharpe=0.5, annualized_turnover=10.0),
    )
    tied_worst = RankedEntry(
        "team-02",
        "c2",
        60.0,
        dict(BASE, max_drawdown=0.10, worst_fold_sharpe=0.5, annualized_turnover=10.0),
    )
    bottom = RankedEntry(
        "team-11",
        "c11",
        40.0,
        dict(BASE, max_drawdown=0.20, worst_fold_sharpe=0.1, annualized_turnover=10.0),
    )
    expected = ["team-04", "team-01", "team-07", "team-02", "team-11"]

    original = [top, tied_best, tied_middle, tied_worst, bottom]
    reversed_order = list(reversed(original))
    shuffled = [bottom, tied_middle, top, tied_worst, tied_best]

    for ordering in (original, reversed_order, shuffled):
        assert [entry.team_id for entry in rank_entries(ordering)] == expected


# --- select_advancing: fewer / exactly / more than slots, plus edges (item b) ---------------


def test_select_advancing_with_exactly_the_slot_count():
    scored = dict(BASE, annualized_turnover=10.0)
    entries = [
        RankedEntry("team-01", "c1", 90.0, dict(scored)),
        RankedEntry("team-02", "c2", 80.0, dict(scored)),
        RankedEntry("team-03", "c3", 70.0, dict(scored)),
    ]
    advancing = select_advancing(entries, slots=3)
    assert isinstance(advancing, tuple)
    assert [entry.team_id for entry in advancing] == ["team-01", "team-02", "team-03"]


def test_select_advancing_with_zero_qualifiers_returns_empty_not_an_error():
    assert select_advancing((), slots=3) == ()


@pytest.mark.parametrize("slots", [0, -1])
def test_select_advancing_rejects_non_positive_slots(slots):
    scored = dict(BASE, annualized_turnover=10.0)
    entries = [RankedEntry("team-01", "c1", 60.0, dict(scored))]
    with pytest.raises(ValueError, match="slots must be positive"):
        select_advancing(entries, slots=slots)


def test_select_advancing_sorts_before_truncating_not_just_input_order():
    # Deliberately NOT pre-sorted (ascending scores) -- unlike the brief's own truncation test,
    # whose f"team-{index:02d}"/(90 - index) construction happens to already be in descending-
    # score order, so a mutation that replaced `rank_entries(entries)[:slots]` with plain
    # `tuple(entries)[:slots]` (no sorting at all) would still pass that test. This one only
    # passes if select_advancing genuinely ranks before truncating.
    scored = dict(BASE, annualized_turnover=10.0)
    entries = [
        RankedEntry("team-c", "cc", 10.0, dict(scored)),
        RankedEntry("team-b", "cb", 50.0, dict(scored)),
        RankedEntry("team-a", "ca", 90.0, dict(scored)),
    ]
    advancing = select_advancing(entries, slots=2)
    assert [entry.team_id for entry in advancing] == ["team-a", "team-b"]


# --- RankedEntry hygiene (global constraint: frozen dataclasses for value objects) ----------


def test_ranked_entry_is_frozen():
    entry = RankedEntry("team-01", "c1", 50.0, dict(BASE, annualized_turnover=10.0))
    with pytest.raises(dataclasses.FrozenInstanceError):
        entry.score = 99.0  # type: ignore[misc]
