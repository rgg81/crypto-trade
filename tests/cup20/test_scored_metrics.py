"""Tests for the cost-level assembly that bridges ``run_candidate`` to the floors and the ranking.

The mutation this whole file exists to catch is a SWAPPED COST LEVEL: an assembly that reads
``net_sharpe`` at 2x, or hands the ranking the 1x drawdown, is not detectably wrong at runtime --
every value is finite, every key is present, and the only symptom is that a tournament is decided
on a different question than the charter asked. It is also invisible to any test whose fixture
reuses one ``EvaluationResult`` across cost levels, because then every level agrees by
construction and a swap is a no-op. That exact mistake was made once in this build.

So the fixture below builds THREE genuinely different books, one per cost multiplier, and
``test_fixture_cost_levels_are_pairwise_distinct`` asserts they differ on every metric before any
other test relies on them. Each cost-level assertion then pins a key to a value only the correct
level produces, and ``test_swapping_base_and_double_results_moves_every_cost_dependent_key`` runs
the swap directly.
"""

import ast
import inspect
import math
import statistics
import textwrap

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.adjudication import adjudicate_candidate
from crypto_trade.cup20.config import load_config
from crypto_trade.cup20.metrics import (
    fold_positive_pnl_shares,
    fold_sharpes,
    holdout_folds,
    is_folds,
    window_metrics,
)
from crypto_trade.cup20.neighbourhood import median_metrics, positive_point_fraction
from crypto_trade.cup20.qualification import evaluate_floors
from crypto_trade.cup20.runner import CandidateRun
from crypto_trade.cup20.scored_metrics import (
    ASSEMBLED_METRIC_KEYS,
    BASE_COST,
    DOUBLE_COST,
    FLOOR_METRIC_KEYS,
    RANKING_METRIC_KEYS,
    TRIPLE_COST,
    assemble_scored_metrics,
    neighbourhood_median,
    ranking_metrics,
)
from crypto_trade.cup20.scoring import RankedEntry, rank_entries, robustness_score
from crypto_trade.tournament.engine_v2 import EvaluationResult

CONFIG = load_config("tournament/cup20/config.toml").raw

IS_START = pd.Timestamp("2020-08-01T00:00:00Z")
IS_END = pd.Timestamp("2024-08-01T00:00:00Z")
INDEX = pd.date_range(IS_START, IS_END, freq="8h", inclusive="left", name="timestamp")
FOLDS = is_folds(IS_START, IS_END)
FOLD_EDGES = (
    IS_START,
    pd.Timestamp("2021-08-01T00:00:00Z"),
    pd.Timestamp("2022-08-01T00:00:00Z"),
    pd.Timestamp("2023-08-01T00:00:00Z"),
    IS_END,
)


def _piecewise_drift(per_fold: tuple[float, float, float, float]) -> np.ndarray:
    """Per-bar drift that changes at every fold boundary, so fold Sharpes differ by design."""
    values = np.zeros(len(INDEX), dtype=float)
    for drift, start, end in zip(per_fold, FOLD_EDGES[:-1], FOLD_EDGES[1:], strict=True):
        values[(INDEX >= start) & (INDEX < end)] = drift
    return values


def _level_result(
    *,
    per_fold_drift: tuple[float, float, float, float],
    volatility: float,
    turnover: float,
    fee: float,
    slippage: float,
    short_share: float,
    trades: int,
    seed: int,
) -> EvaluationResult:
    """One book. Every argument moves at least one reported metric."""
    rng = np.random.default_rng(seed)
    net = _piecewise_drift(per_fold_drift) + rng.normal(0.0, volatility, size=len(INDEX))
    costs = fee + slippage
    price = net + costs  # gross = net + costs, so cost share and gross edge are self-consistent
    returns = pd.DataFrame(
        {
            "net_return": net,
            "price_pnl": price,
            "long_price_pnl": price * (1.0 - short_share),
            "short_price_pnl": price * short_share,
            "funding_pnl": np.zeros(len(INDEX)),
            "long_funding_pnl": np.zeros(len(INDEX)),
            "short_funding_pnl": np.zeros(len(INDEX)),
            "fees": np.full(len(INDEX), fee),
            "slippage": np.full(len(INDEX), slippage),
            "turnover": np.full(len(INDEX), turnover),
        },
        index=INDEX,
    )
    events = pd.DataFrame(
        {
            "event_type": ["trade"] * trades + ["mark_to_market"] * 7,
            "notional": [100.0] * trades + [250.0] * 7,
        }
    )
    return EvaluationResult(returns=returns, positions=pd.DataFrame(), events=events)


# Base cost: a book that works in all four folds.
BASE_RESULT = _level_result(
    per_fold_drift=(0.0025, 0.0021, 0.0018, 0.0027),
    volatility=0.010,
    turnover=0.004,
    fee=0.00004,
    slippage=0.00002,
    short_share=0.35,
    trades=900,
    seed=101,
)
# Double cost: the same mechanism, but two folds have flipped sign. Chosen so that
# `positive_fold_count`, `worst_fold_sharpe` and `median_fold_sharpe` all land somewhere the base
# book never would -- a swap is then visible in the value, not merely in a float's last bits.
DOUBLE_RESULT = _level_result(
    per_fold_drift=(0.0019, 0.0014, -0.0016, -0.0011),
    volatility=0.013,
    turnover=0.006,
    fee=0.00009,
    slippage=0.00005,
    short_share=0.20,
    trades=700,
    seed=202,
)
# Triple cost: barely alive.
TRIPLE_RESULT = _level_result(
    per_fold_drift=(0.0004, 0.0002, -0.0003, 0.0001),
    volatility=0.016,
    turnover=0.009,
    fee=0.00013,
    slippage=0.00008,
    short_share=0.45,
    trades=500,
    seed=303,
)

BASE_METRICS = window_metrics(BASE_RESULT)
DOUBLE_METRICS = window_metrics(DOUBLE_RESULT)
TRIPLE_METRICS = window_metrics(TRIPLE_RESULT)
BASE_FOLD_SHARPES = tuple(fold_sharpes(BASE_RESULT, FOLDS).values())
DOUBLE_FOLD_SHARPES = tuple(fold_sharpes(DOUBLE_RESULT, FOLDS).values())
BASE_FOLD_SHARES = tuple(fold_positive_pnl_shares(BASE_RESULT, FOLDS).values())
DOUBLE_FOLD_SHARES = tuple(fold_positive_pnl_shares(DOUBLE_RESULT, FOLDS).values())


def _run(**results: EvaluationResult) -> CandidateRun:
    return CandidateRun(
        targets=pd.DataFrame(),
        scaled_targets=pd.DataFrame(),
        risk_scalars=pd.Series(dtype=float),
        unscaled=BASE_RESULT,
        results={int(level): result for level, result in results.items()},
    )


RUN = _run(**{"1": BASE_RESULT, "2": DOUBLE_RESULT, "3": TRIPLE_RESULT})
SWAPPED_RUN = _run(**{"1": DOUBLE_RESULT, "2": BASE_RESULT, "3": TRIPLE_RESULT})
ASSEMBLED = assemble_scored_metrics(RUN, is_start=IS_START, is_end=IS_END)


# --- the fixture itself, without which every assertion below is vacuous ---------------------


def test_fixture_cost_levels_are_pairwise_distinct():
    # A fixture that reuses one EvaluationResult across cost levels cannot detect a swap. Assert
    # the premise explicitly rather than trusting it: every WindowMetrics field must differ
    # between the base and double books, and the fold statistics with them.
    for field, base_value in BASE_METRICS.as_dict().items():
        assert base_value != DOUBLE_METRICS.as_dict()[field], field
        assert base_value != TRIPLE_METRICS.as_dict()[field], field
    assert BASE_FOLD_SHARPES != DOUBLE_FOLD_SHARPES
    assert BASE_FOLD_SHARES != DOUBLE_FOLD_SHARES


def test_a_fold_whose_sharpe_is_exactly_zero_is_not_counted_as_positive():
    # Section 7.3: "A regime or fold is positive only when its Sharpe is strictly greater than
    # zero. Zero is not positive." A zero-Sharpe fold is not hypothetical -- `sharpe()` returns
    # exactly 0.0 for a slice with no dispersion, which a flat or halted fold produces -- and
    # `> 0` versus `>= 0` is a one-character mutation that no other test in this file can see,
    # because every fold in the main fixture is strictly signed.
    flat = _level_result(
        per_fold_drift=(0.0020, 0.0015, 0.0, 0.0018),
        volatility=0.012,
        turnover=0.005,
        fee=0.00007,
        slippage=0.00004,
        short_share=0.25,
        trades=800,
        seed=404,
    )
    # F3 is dispersion-free, so its Sharpe is exactly 0.0 rather than merely small.
    flat.returns.loc[
        (flat.returns.index >= FOLD_EDGES[2]) & (flat.returns.index < FOLD_EDGES[3]),
        "net_return",
    ] = 0.0
    sharpes = fold_sharpes(flat, FOLDS)
    assert sharpes["F3"] == 0.0
    assert sum(1 for value in sharpes.values() if value > 0.0) == 3

    run = _run(**{"1": BASE_RESULT, "2": flat, "3": TRIPLE_RESULT})
    scored = assemble_scored_metrics(run, is_start=IS_START, is_end=IS_END)
    assert scored["positive_fold_count"] == 3.0  # not 4: the zero fold is excluded


def test_fixture_fold_signs_differ_between_the_base_and_double_books():
    # The strongest discriminator available: the base book has four positive folds, the double
    # book two. A `positive_fold_count` of 4 is then proof the wrong level was read.
    assert sum(1 for value in BASE_FOLD_SHARPES if value > 0.0) == 4
    assert sum(1 for value in DOUBLE_FOLD_SHARPES if value > 0.0) == 2
    assert min(BASE_FOLD_SHARPES) > 0.0
    assert min(DOUBLE_FOLD_SHARPES) < 0.0


# --- every key reads the level policy names for it -------------------------------------------


# (key, the value only the CORRECT cost level produces, the value a swapped level would give).
# Hoisted to a module constant so the exhaustiveness test below can read it: the table is only a
# contract if every assembled key appears in it.
_COST_LEVEL_CASES = [
    # section 7.3, cost level named in the charter's own row
    ("net_sharpe", BASE_METRICS.net_sharpe, DOUBLE_METRICS.net_sharpe),
    ("double_cost_sharpe", DOUBLE_METRICS.net_sharpe, BASE_METRICS.net_sharpe),
    ("triple_cost_sharpe", TRIPLE_METRICS.net_sharpe, BASE_METRICS.net_sharpe),
    (
        "annualized_return",
        BASE_METRICS.annualized_return,
        DOUBLE_METRICS.annualized_return,
    ),
    (
        "double_cost_annualized_return",
        DOUBLE_METRICS.annualized_return,
        BASE_METRICS.annualized_return,
    ),
    (
        "positive_fold_count",
        float(sum(1 for value in DOUBLE_FOLD_SHARPES if value > 0.0)),
        float(sum(1 for value in BASE_FOLD_SHARPES if value > 0.0)),
    ),
    ("worst_fold_sharpe", min(DOUBLE_FOLD_SHARPES), min(BASE_FOLD_SHARPES)),
    (
        "cost_share_of_positive_gross",
        BASE_METRICS.cost_share_of_positive_gross,
        DOUBLE_METRICS.cost_share_of_positive_gross,
    ),
    # section 7.3 rows that name no level: base cost, per the ruling
    ("max_drawdown", BASE_METRICS.max_drawdown, DOUBLE_METRICS.max_drawdown),
    (
        "annualized_volatility",
        BASE_METRICS.annualized_volatility,
        DOUBLE_METRICS.annualized_volatility,
    ),
    (
        "positive_quarter_fraction",
        BASE_METRICS.positive_quarter_fraction,
        DOUBLE_METRICS.positive_quarter_fraction,
    ),
    (
        "annualized_turnover",
        BASE_METRICS.annualized_turnover,
        DOUBLE_METRICS.annualized_turnover,
    ),
    (
        "gross_edge_bps_per_turnover",
        BASE_METRICS.gross_edge_bps_per_turnover,
        DOUBLE_METRICS.gross_edge_bps_per_turnover,
    ),
    ("top5_day_share", BASE_METRICS.top5_day_share, DOUBLE_METRICS.top5_day_share),
    ("max_fold_positive_pnl_share", max(BASE_FOLD_SHARES), max(DOUBLE_FOLD_SHARES)),
    ("trade_count", float(BASE_METRICS.trade_count), float(DOUBLE_METRICS.trade_count)),
    ("long_gross_pnl", BASE_METRICS.long_gross_pnl, DOUBLE_METRICS.long_gross_pnl),
    ("short_gross_pnl", BASE_METRICS.short_gross_pnl, DOUBLE_METRICS.short_gross_pnl),
    # section 7.4 ranking inputs: 2x
    (
        "median_fold_sharpe",
        statistics.median(DOUBLE_FOLD_SHARPES),
        statistics.median(BASE_FOLD_SHARPES),
    ),
    ("calmar", DOUBLE_METRICS.calmar, BASE_METRICS.calmar),
    ("double_cost_max_drawdown", DOUBLE_METRICS.max_drawdown, BASE_METRICS.max_drawdown),
    (
        "double_cost_positive_quarter_fraction",
        DOUBLE_METRICS.positive_quarter_fraction,
        BASE_METRICS.positive_quarter_fraction,
    ),
    (
        "double_cost_annualized_turnover",
        DOUBLE_METRICS.annualized_turnover,
        BASE_METRICS.annualized_turnover,
    ),
]


@pytest.mark.parametrize(("key", "expected", "wrong_level_value"), _COST_LEVEL_CASES)
def test_every_assembled_key_reads_its_declared_cost_level(key, expected, wrong_level_value):
    assert ASSEMBLED[key] == pytest.approx(expected)
    # And is not merely equal to the value a swapped level would have produced.
    assert ASSEMBLED[key] != pytest.approx(wrong_level_value)


def test_every_cost_level_parametrisation_covers_the_whole_assembled_vector():
    # The table above is only a contract if it is exhaustive: a new key added to the assembly
    # without a cost-level assertion is the defect this file exists to prevent.
    assert {key for key, _, _ in _COST_LEVEL_CASES} == ASSEMBLED_METRIC_KEYS
    assert len(_COST_LEVEL_CASES) == len(ASSEMBLED_METRIC_KEYS)


def test_swapping_base_and_double_results_moves_every_cost_dependent_key():
    swapped = assemble_scored_metrics(SWAPPED_RUN, is_start=IS_START, is_end=IS_END)
    for key in ASSEMBLED_METRIC_KEYS - {"triple_cost_sharpe"}:
        assert ASSEMBLED[key] != pytest.approx(swapped[key]), key
    # The one key that reads neither swapped level must be untouched, which proves the swap
    # itself is what moved the others rather than some incidental non-determinism.
    assert ASSEMBLED["triple_cost_sharpe"] == swapped["triple_cost_sharpe"]


# --- the key set is a contract with the consumers, not a convention --------------------------


def _scored_subscripts(function) -> set[str]:
    """Every ``scored["literal"]`` a consumer performs, read out of its source."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    return {
        node.slice.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == "scored"
        and isinstance(node.slice, ast.Constant)
        and isinstance(node.slice.value, str)
    }


def _tie_break_fields(function) -> set[str]:
    """Every field name ``rank_entries`` passes to ``_finite_tie_break``."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    return {
        node.args[1].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_finite_tie_break"
        and len(node.args) == 2
        and isinstance(node.args[1], ast.Constant)
        and isinstance(node.args[1].value, str)
    }


def test_floor_key_set_is_exactly_what_evaluate_floors_subscripts():
    # Catches a floor that starts consuming a nineteenth metric without the assembly producing
    # it -- which would otherwise surface as a KeyError only once real team numbers exist.
    assert _scored_subscripts(evaluate_floors) == FLOOR_METRIC_KEYS


def test_ranking_key_set_is_exactly_what_the_ranking_reads():
    assert _scored_subscripts(robustness_score) | _tie_break_fields(rank_entries) == (
        RANKING_METRIC_KEYS
    )


def test_assembled_key_set_is_exactly_the_declared_contract():
    assert set(ASSEMBLED) == ASSEMBLED_METRIC_KEYS


def test_assembled_vector_satisfies_evaluate_floors_with_no_missing_key():
    gate = evaluate_floors(
        ASSEMBLED,
        floors=CONFIG["floors"],
        statistics_config=CONFIG["statistics"],
        research_config=CONFIG["research"],
        declared_roles=("long", "short"),
        sign_inversion_passes_core=False,
        neighbourhood_positive_fraction=0.9,
        trial_adjusted_confidence=0.95,
    )
    assert FLOOR_METRIC_KEYS - {"long_gross_pnl", "short_gross_pnl"} <= set(gate.checks)


def test_ranking_view_key_set_is_exactly_the_ranking_contract():
    view = ranking_metrics(ASSEMBLED, trial_adjusted_confidence=0.93)
    assert set(view) == RANKING_METRIC_KEYS


def test_ranking_view_supports_the_score_and_every_tie_break():
    view = ranking_metrics(ASSEMBLED, trial_adjusted_confidence=0.93)
    entry = RankedEntry("team-01", "c1", robustness_score(view, drawdown_floor=0.20), view)
    assert rank_entries([entry]) == (entry,)


# --- the ranking reads the 2x twins, never the 1x floor values --------------------------------


def test_ranking_view_takes_the_double_cost_twins_not_the_floor_values():
    view = ranking_metrics(ASSEMBLED, trial_adjusted_confidence=0.93)
    for ranking_key, floor_key in (
        ("max_drawdown", "max_drawdown"),
        ("positive_quarter_fraction", "positive_quarter_fraction"),
        ("annualized_turnover", "annualized_turnover"),
    ):
        assert view[ranking_key] == pytest.approx(ASSEMBLED[f"double_cost_{floor_key}"])
        # The two levels genuinely differ (asserted above), so this is a real discrimination.
        assert view[ranking_key] != pytest.approx(ASSEMBLED[floor_key])


def test_ranking_view_passes_through_the_metrics_already_at_two_x():
    view = ranking_metrics(ASSEMBLED, trial_adjusted_confidence=0.93)
    for key in ("worst_fold_sharpe", "median_fold_sharpe", "calmar"):
        assert view[key] == pytest.approx(ASSEMBLED[key])


def test_trial_adjusted_confidence_is_cost_free_and_comes_from_the_caller():
    assert "trial_adjusted_confidence" not in ASSEMBLED
    view = ranking_metrics(ASSEMBLED, trial_adjusted_confidence=0.93)
    assert view["trial_adjusted_confidence"] == pytest.approx(0.93)


def test_ranking_metrics_raises_when_a_double_cost_twin_is_missing():
    truncated = {k: v for k, v in ASSEMBLED.items() if k != "double_cost_max_drawdown"}
    with pytest.raises(KeyError, match="double_cost_max_drawdown"):
        ranking_metrics(truncated, trial_adjusted_confidence=0.93)


# --- raise paths, one test each ---------------------------------------------------------------


@pytest.mark.parametrize("absent", [BASE_COST, DOUBLE_COST, TRIPLE_COST])
def test_assembly_raises_when_a_cost_level_is_absent(absent):
    partial = _run(
        **{
            str(level): result
            for level, result in ((1, BASE_RESULT), (2, DOUBLE_RESULT), (3, TRIPLE_RESULT))
            if level != absent
        }
    )
    with pytest.raises(ValueError, match=f"missing \\[{absent}\\]"):
        assemble_scored_metrics(partial, is_start=IS_START, is_end=IS_END)


def test_assembly_raises_on_a_naive_is_start():
    with pytest.raises(ValueError, match="is_start must be timezone-aware"):
        assemble_scored_metrics(RUN, is_start=pd.Timestamp("2020-08-01"), is_end=IS_END)


def test_assembly_raises_on_a_naive_is_end():
    with pytest.raises(ValueError, match="is_end must be timezone-aware"):
        assemble_scored_metrics(RUN, is_start=IS_START, is_end=pd.Timestamp("2024-08-01"))


def test_assembly_raises_on_an_empty_fold_sequence():
    with pytest.raises(ValueError, match="at least one fold"):
        assemble_scored_metrics(RUN, is_start=IS_START, is_end=IS_END, folds=())


def test_assembly_raises_when_the_folds_do_not_start_at_the_window_start():
    late = ((FOLDS[0][0], FOLDS[0][1] + pd.Timedelta(days=1), FOLDS[0][2]), *FOLDS[1:])
    with pytest.raises(ValueError, match="folds must tile"):
        assemble_scored_metrics(RUN, is_start=IS_START, is_end=IS_END, folds=late)


def test_assembly_raises_when_the_folds_do_not_end_at_the_window_end():
    short = (*FOLDS[:-1], (FOLDS[-1][0], FOLDS[-1][1], FOLDS[-1][2] - pd.Timedelta(days=1)))
    with pytest.raises(ValueError, match="folds must tile"):
        assemble_scored_metrics(RUN, is_start=IS_START, is_end=IS_END, folds=short)


def test_assembly_raises_when_two_folds_leave_a_gap():
    gapped = (
        (FOLDS[0][0], FOLDS[0][1], FOLDS[0][2] - pd.Timedelta(days=7)),
        *FOLDS[1:],
    )
    with pytest.raises(ValueError, match="do not abut"):
        assemble_scored_metrics(RUN, is_start=IS_START, is_end=IS_END, folds=gapped)


def test_assembly_raises_on_a_zero_width_fold():
    degenerate = (
        ("F1", IS_START, IS_START),
        ("F2", IS_START, IS_END),
    )
    with pytest.raises(ValueError, match="fold F1 has non-positive width"):
        assemble_scored_metrics(RUN, is_start=IS_START, is_end=IS_END, folds=degenerate)


def test_assembly_raises_on_a_naive_fold_boundary():
    naive = (("F1", pd.Timestamp("2020-08-01"), IS_END),)
    with pytest.raises(ValueError, match="fold F1 start must be timezone-aware"):
        assemble_scored_metrics(RUN, is_start=IS_START, is_end=IS_END, folds=naive)


def test_the_folds_override_is_what_lets_the_holdout_reuse_this_assembly():
    # The sealed window is two years and scored on four 6-month blocks (section 8), so the
    # override has to be usable -- and the tiling check has to accept it.
    sealed_start = pd.Timestamp("2024-08-01T00:00:00Z")
    sealed_end = pd.Timestamp("2026-08-01T00:00:00Z")
    holdout = holdout_folds(sealed_start, sealed_end)
    scored = assemble_scored_metrics(RUN, is_start=sealed_start, is_end=sealed_end, folds=holdout)
    assert set(scored) == ASSEMBLED_METRIC_KEYS


def test_holdout_folds_against_the_in_sample_window_are_rejected():
    # The cross-window mistake the tiling check exists for: sealed-window fold boundaries applied
    # to an in-sample run would leave every fold empty, and `sharpe()` of an empty slice is 0.0,
    # so nothing downstream would raise.
    holdout = holdout_folds(
        pd.Timestamp("2024-08-01T00:00:00Z"), pd.Timestamp("2026-08-01T00:00:00Z")
    )
    with pytest.raises(ValueError, match="folds must tile"):
        assemble_scored_metrics(RUN, is_start=IS_START, is_end=IS_END, folds=holdout)


# --- neighbourhood median -----------------------------------------------------------------


def test_neighbourhood_median_is_the_per_metric_median():
    points = [dict(ASSEMBLED, net_sharpe=value) for value in (0.4, 0.9, 1.7)]
    assert neighbourhood_median(points)["net_sharpe"] == pytest.approx(0.9)


def test_neighbourhood_median_fails_closed_on_a_non_finite_point():
    # This exact ORDER is the fail-open being closed, and it is why the guard is not redundant:
    # statistics.median SORTS, NaN has no ordering, and (0.4, 1.7, nan) sorts to leave 1.7 in the
    # middle -- so the unguarded median comes back finite and entirely plausible with a NaN
    # sample behind it. Other orderings of the same three values happen to return NaN by luck,
    # which is exactly why luck cannot be what a hard floor depends on.
    points = [dict(ASSEMBLED, net_sharpe=value) for value in (0.4, 1.7, math.nan)]
    assert median_metrics(points)["net_sharpe"] == pytest.approx(1.7)
    assert math.isnan(neighbourhood_median(points)["net_sharpe"])


def test_neighbourhood_median_fails_closed_whatever_the_point_order():
    for order in ((math.nan, 0.4, 1.7), (0.4, math.nan, 1.7), (0.4, 1.7, math.nan)):
        points = [dict(ASSEMBLED, net_sharpe=value) for value in order]
        assert math.isnan(neighbourhood_median(points)["net_sharpe"]), order


def test_neighbourhood_median_fails_closed_on_an_infinite_point():
    points = [dict(ASSEMBLED, max_drawdown=value) for value in (0.1, math.inf, 0.3)]
    assert math.isnan(neighbourhood_median(points)["max_drawdown"])


def test_neighbourhood_median_leaves_the_other_metrics_finite():
    # Per-metric, not per-record: one poisoned metric must not erase the diagnostics beside it.
    points = [dict(ASSEMBLED, net_sharpe=value) for value in (0.4, 1.7, math.nan)]
    medians = neighbourhood_median(points)
    assert math.isnan(medians["net_sharpe"])
    assert math.isfinite(medians["max_drawdown"])


def test_neighbourhood_median_rejects_points_with_different_key_sets():
    points = [dict(ASSEMBLED), {k: v for k, v in ASSEMBLED.items() if k != "calmar"}]
    with pytest.raises(ValueError, match="same metric keys"):
        neighbourhood_median(points)


# --- the whole chain, which is the thing that did not exist ---------------------------------


def test_the_full_chain_composes_from_candidate_runs_to_a_verdict():
    # run_candidate -> assemble per point -> per-metric median -> positive-point fraction ->
    # floors -> G. Every earlier test pins one link; this one asserts the links join, which is
    # the defect this task exists to fix: nothing composed the floors with the ranking, and the
    # per-point vector had to satisfy `positive_point_fraction`'s key requirements as well.
    points = []
    for shift in range(7):
        run = _run(
            **{
                "1": _level_result(
                    per_fold_drift=(0.0022 + shift * 1e-4, 0.0019, 0.0017, 0.0025),
                    volatility=0.010,
                    turnover=0.004,
                    fee=0.00004,
                    slippage=0.00002,
                    short_share=0.35,
                    trades=900,
                    seed=1000 + shift,
                ),
                "2": DOUBLE_RESULT,
                "3": TRIPLE_RESULT,
            }
        )
        points.append(assemble_scored_metrics(run, is_start=IS_START, is_end=IS_END))

    scored = neighbourhood_median(points)
    assert set(scored) == ASSEMBLED_METRIC_KEYS
    # positive_point_fraction reads `annualized_return` (1x) and `double_cost_sharpe` (2x) off
    # the very same per-point vectors, so the assembled key set has to satisfy it too.
    fraction = positive_point_fraction(points)
    assert 0.0 <= fraction <= 1.0

    verdict = adjudicate_candidate(
        scored,
        team_id="team-01",
        candidate_id="c1",
        floors=CONFIG["floors"],
        statistics_config=CONFIG["statistics"],
        research_config=CONFIG["research"],
        declared_roles=("long", "short"),
        sign_inversion_passes_core=False,
        neighbourhood_positive_fraction=fraction,
        trial_adjusted_confidence=0.95,
        drawdown_floor=float(CONFIG["floors"]["max_drawdown"]),
    )
    # The synthetic book is not a qualifier, and it is not supposed to be: what is asserted is
    # that the chain produced a NAMED verdict rather than a KeyError, and that the gate vector
    # explains it.
    assert set(verdict.scored) == ASSEMBLED_METRIC_KEYS
    assert verdict.gates.checks
    assert verdict.qualified is (verdict.score is not None)
    if not verdict.qualified:
        assert verdict.failures
