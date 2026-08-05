"""Assemble the scored metric vector, reading each metric at the cost level policy names for it.

``run_candidate`` produces one ``EvaluationResult`` per cost multiplier; ``evaluate_floors`` and
``robustness_score`` consume a flat ``Mapping[str, float]``. This module is the bridge, and the
only thing it decides is WHICH cost level each metric is read at. That decision is policy, not
plumbing -- charter sections 7.3 and 7.4 -- so every assignment below names its level in the
expression itself (``at_base_cost.``, ``at_double_cost.``, ``at_triple_cost.``) rather than
reading it from a shared local that a later edit could quietly repoint.

Two rules, and they deliberately disagree with each other:

* a FLOOR metric (section 7.3) is read at the cost level that section names for it, and at BASE
  (1x) cost where it names none. 1x is the actual cost model; ``maxDD <= 0.20`` asks whether the
  real book would have been survivable, which is a question about the real book. The charter
  already carries dedicated 2x and 3x Sharpe floors, and those are where cost resilience is
  stressed -- it does not need every other floor stressed a second time.
* a RANKING input (section 7.4) is read at 2x cost, as that section states for all of its inputs,
  so the ranking rewards robustness under a cost shock.
* a HOLDOUT eligibility floor (section 8) follows the floor rule, not the ranking rule: it is a
  floor, so an unqualified one is base cost. Section 8's two unqualified rows -- ``maxDD <= 0.25``
  and "at least 5 of 8 quarters positive" -- are therefore both 1x, and its 2x return and 2x
  Sharpe rows say 2x on their face.

Three metrics -- ``max_drawdown``, ``positive_quarter_fraction`` and ``annualized_turnover`` --
are consumed by BOTH, so they are computed TWICE, at two different levels, and both values are
carried. That is intended, not a bug. The floor value keeps the plain name, because that is what
``evaluate_floors`` subscripts; the ranking value is carried under a ``double_cost_`` name and
:func:`ranking_metrics` maps it back onto the name ``robustness_score`` subscripts. Making the
ranking go through an explicit remap is the point: a single shared dict would have silently served
one level to both consumers, and nothing in either consumer could have noticed.
"""

from __future__ import annotations

import dataclasses
import math
import statistics
from collections.abc import Iterator, Mapping, Sequence

import pandas as pd

from crypto_trade.cup20.config import IS_END, SEALED_END, SEALED_START
from crypto_trade.cup20.metrics import (
    Fold,
    fold_positive_pnl_shares,
    fold_sharpes,
    holdout_folds,
    is_folds,
    window_metrics,
)
from crypto_trade.cup20.neighbourhood import median_metrics
from crypto_trade.cup20.runner import CandidateRun

BASE_COST = 1
DOUBLE_COST = 2
TRIPLE_COST = 3

# Every cost multiplier the assembly reads. Kept as a tuple rather than derived from
# ``run.results`` so a run that is missing a level fails loudly instead of assembling a partial
# vector: a metric silently absent from the scored dict raises in ``evaluate_floors``, but a
# metric silently read at the WRONG level would not raise anywhere.
REQUIRED_COST_LEVELS: tuple[int, ...] = (BASE_COST, DOUBLE_COST, TRIPLE_COST)

# Exactly what ``qualification.evaluate_floors`` subscripts out of its ``scored`` mapping. A test
# parses that function's source and asserts this set equals its subscripts, so a floor that starts
# consuming a new key cannot ship without the assembly producing it.
FLOOR_METRIC_KEYS: frozenset[str] = frozenset(
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
        "long_gross_pnl",
        "short_gross_pnl",
    }
)

# Exactly what ``scoring.robustness_score`` subscripts, plus the three tie-break fields
# ``scoring.rank_entries`` reads off ``RankedEntry.scored``. Both are asserted against the parsed
# source in the same way.
RANKING_METRIC_KEYS: frozenset[str] = frozenset(
    {
        "worst_fold_sharpe",
        "median_fold_sharpe",
        "max_drawdown",
        "calmar",
        "positive_quarter_fraction",
        "annualized_turnover",
        "trial_adjusted_confidence",
    }
)

# The ranking-only metrics, which have no floor and therefore keep their plain names at 2x.
RANKING_ONLY_KEYS: frozenset[str] = frozenset({"median_fold_sharpe", "calmar"})

# The three metrics both consumers read, at two different levels. The floor value holds the plain
# name; these carry the 2x value the ranking needs. ``trial_adjusted_confidence`` is deliberately
# NOT here: it is cost-free, computed once per section 7.3 and never recomputed per cost level, so
# it enters through :func:`ranking_metrics`' keyword rather than out of a run.
DOUBLE_COST_RANKING_KEYS: frozenset[str] = frozenset(
    {
        "double_cost_max_drawdown",
        "double_cost_positive_quarter_fraction",
        "double_cost_annualized_turnover",
    }
)

# Exactly what ``qualification.evaluate_holdout_eligibility`` subscripts and no floor or ranking
# input already carries. Section 8 states its quarter floor as a COUNT ("at least 5 of 8 quarters
# positive"), which no section 7.3 floor needs -- that one reads the fraction. Asserted against the
# parsed source the same way the other two key sets are.
HOLDOUT_ONLY_KEYS: frozenset[str] = frozenset({"positive_quarter_count"})

# Exactly what :func:`assemble_scored_metrics` returns.
ASSEMBLED_METRIC_KEYS: frozenset[str] = (
    FLOOR_METRIC_KEYS | RANKING_ONLY_KEYS | DOUBLE_COST_RANKING_KEYS | HOLDOUT_ONLY_KEYS
)


STAGE_IN_SAMPLE = "in_sample"
STAGE_HOLDOUT = "holdout"
STAGES: tuple[str, ...] = (STAGE_IN_SAMPLE, STAGE_HOLDOUT)


@dataclasses.dataclass(frozen=True, slots=True)
class MetricProvenance:
    """Which stage, window and folds produced a scored vector.

    A flat ``dict[str, float]`` cannot answer "where did these numbers come from", and the two
    adjudicators ask exactly that question in opposite directions. Without provenance riding along
    with the numbers, a caller that assembled in-sample metrics and handed them to
    :func:`~crypto_trade.cup20.adjudication.adjudicate_holdout_candidate` would have the wrong
    window scored against section 8's conditions, with every value finite, every key present and
    nothing anywhere in a position to notice.
    """

    stage: str
    window_start: pd.Timestamp
    window_end: pd.Timestamp
    folds: tuple[Fold, ...]

    def describe(self) -> str:
        names = ",".join(name for name, _, _ in self.folds)
        return f"{self.stage} over [{self.window_start}, {self.window_end}) on folds {names}"


class ScoredVector(Mapping[str, float]):
    """An assembled metric vector that remembers the stage it was assembled for.

    A ``Mapping`` rather than a wrapper object on purpose: ``evaluate_floors``,
    ``evaluate_holdout_eligibility``, ``ranking_metrics`` and ``neighbourhood_median`` all consume
    ``Mapping[str, float]`` and none of them needs to change. What changes is that the two
    adjudicators can now REFUSE a bare mapping, because a bare mapping carries no claim about where
    it came from and an unverifiable claim must fail closed rather than be assumed correct.
    """

    __slots__ = ("_metrics", "provenance")

    def __init__(self, metrics: Mapping[str, float], provenance: MetricProvenance) -> None:
        self._metrics: dict[str, float] = dict(metrics)
        self.provenance: MetricProvenance = provenance

    def __getitem__(self, key: str) -> float:
        return self._metrics[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._metrics)

    def __len__(self) -> int:
        return len(self._metrics)

    def __repr__(self) -> str:
        return f"ScoredVector({self.provenance.describe()}, {len(self._metrics)} metrics)"


def _utc(value: object, label: str) -> pd.Timestamp:
    """Normalise a boundary to UTC, refusing a naive timestamp rather than guessing its zone.

    ``pd.Timestamp.tz_convert`` raises ``TypeError`` on a naive value, which would surface here as
    an unattributed pandas error several frames deep. Every window boundary in CUP-20 is an
    instant, never a wall-clock reading, so a naive one is a caller mistake worth naming.
    """
    stamp = pd.Timestamp(value)  # type: ignore[arg-type]
    if stamp.tz is None:
        raise ValueError(f"{label} must be timezone-aware, got the naive timestamp {stamp}")
    return stamp.tz_convert("UTC")


def _validate_folds(
    folds: Sequence[Fold], window_start: pd.Timestamp, window_end: pd.Timestamp
) -> tuple[Fold, ...]:
    """Require the folds to tile ``[window_start, window_end)`` exactly, with no gap or overlap.

    ``folds`` exists so the holdout can pass ``holdout_folds`` instead of ``is_folds``, and that
    override is precisely where a cross-window mistake becomes possible -- scoring the sealed
    window against in-sample fold boundaries would leave every fold empty, and ``sharpe()`` of an
    empty slice is 0.0, so ``positive_fold_count`` would read 0 and ``worst_fold_sharpe`` 0.0
    without anything raising. Tiling is checked against the same window the caller declared, so
    the two cannot silently disagree.
    """
    if not folds:
        raise ValueError("assemble_scored_metrics requires at least one fold")
    normalised: list[Fold] = []
    for name, start, end in folds:
        fold_start = _utc(start, f"fold {name} start")
        fold_end = _utc(end, f"fold {name} end")
        if fold_start >= fold_end:
            raise ValueError(f"fold {name} has non-positive width: [{fold_start}, {fold_end})")
        normalised.append((name, fold_start, fold_end))
    if normalised[0][1] != window_start or normalised[-1][2] != window_end:
        raise ValueError(
            f"folds must tile [{window_start}, {window_end}); the declared folds cover "
            f"[{normalised[0][1]}, {normalised[-1][2]})"
        )
    for previous, current in zip(normalised, normalised[1:], strict=False):
        if previous[2] != current[1]:
            raise ValueError(
                f"folds {previous[0]} and {current[0]} do not abut: {previous[0]} ends at "
                f"{previous[2]} and {current[0]} starts at {current[1]}"
            )
    return tuple(normalised)


def _canonical_folds(stage: str, start: pd.Timestamp, end: pd.Timestamp) -> tuple[Fold, ...]:
    """The one fold construction the charter states for this stage over this window."""
    return is_folds(start, end) if stage == STAGE_IN_SAMPLE else holdout_folds(start, end)


def _validate_stage_window(stage: str, start: pd.Timestamp, end: pd.Timestamp) -> None:
    """Reject a window that is not the one this stage is defined over.

    The two stages are pinned to different degrees, and the asymmetry is real rather than an
    oversight. The sealed window is frozen at BOTH ends by ``[splits]`` -- ``sealed_start`` and
    ``sealed_end`` are entries in ``config._FROZEN_SCALARS`` -- so a holdout assembly can be
    required to be exactly it, and that single equality is what makes "these metrics came from the
    sealed window" a fact rather than a caller's assertion. The in-sample window's START is
    computed at snapshot build (``resolve_is_start`` finds the first boundary with twenty eligible
    names) and so cannot be pinned to a constant; its END is the frozen cutoff, and an in-sample
    window that reaches past the cutoff is the leak this whole apparatus exists to prevent, so that
    end is checked.
    """
    if stage == STAGE_HOLDOUT:
        if (start, end) != (SEALED_START, SEALED_END):
            raise ValueError(
                f"a holdout assembly must cover exactly the sealed window "
                f"[{SEALED_START}, {SEALED_END}); it was handed [{start}, {end})"
            )
        return
    if end > IS_END:
        raise ValueError(
            f"an in-sample assembly must end at or before the cutoff {IS_END}; its window "
            f"[{start}, {end}) reaches into the sealed side"
        )


def assemble_scored_metrics(
    run: CandidateRun,
    *,
    stage: str,
    is_start: pd.Timestamp,
    is_end: pd.Timestamp,
    folds: Sequence[Fold] | None = None,
) -> ScoredVector:
    """Every metric the floors and the ranking consume, each read at its declared cost level.

    One point's vector, not a neighbourhood's: section 7.2 scores the per-metric median across the
    declared neighbourhood, so callers assemble one of these per point and then take
    :func:`neighbourhood_median`.

    ``stage`` is required and is the vector's provenance: it selects the fold construction, pins
    the window (see :func:`_validate_stage_window`), and travels with the returned
    :class:`ScoredVector` so the adjudicator for the OTHER stage can refuse it. Passing an explicit
    ``folds`` sequence is still allowed -- it is how a caller proves the folds are the ones it
    meant -- but it must equal the canonical construction for the stage and window, so the override
    can no longer be the route by which the wrong window gets scored.
    """
    missing_levels = [level for level in REQUIRED_COST_LEVELS if level not in run.results]
    if missing_levels:
        raise ValueError(
            f"assemble_scored_metrics needs an EvaluationResult at every cost multiplier "
            f"{list(REQUIRED_COST_LEVELS)}; run.results is missing {missing_levels}"
        )

    window_start = _utc(is_start, "is_start")
    window_end = _utc(is_end, "is_end")
    if stage not in STAGES:
        raise ValueError(f"stage must be one of {list(STAGES)}, got {stage!r}")
    _validate_stage_window(stage, window_start, window_end)
    resolved_folds = _validate_folds(
        _canonical_folds(stage, window_start, window_end) if folds is None else folds,
        window_start,
        window_end,
    )
    canonical = _canonical_folds(stage, window_start, window_end)
    if resolved_folds != canonical:
        raise ValueError(
            f"a {stage} assembly must use the folds the charter states for its window "
            f"({[name for name, _, _ in canonical]} over [{window_start}, {window_end})); it was "
            f"handed {[name for name, _, _ in resolved_folds]} with different bounds"
        )

    at_base_cost = window_metrics(run.results[BASE_COST])
    at_double_cost = window_metrics(run.results[DOUBLE_COST])
    at_triple_cost = window_metrics(run.results[TRIPLE_COST])

    # Fold statistics: section 7.3 floors "folds positive" and "worst-fold Sharpe" at 2x, and
    # section 7.4 ranks worst and median fold Sharpe at 2x, so all four come off ONE 2x series.
    double_cost_fold_sharpes = tuple(
        fold_sharpes(run.results[DOUBLE_COST], resolved_folds).values()
    )
    # ... but the fold PnL-concentration floor is unqualified in section 7.3, so it is base cost:
    # it asks whether the real book's positive PnL came from one lucky year.
    base_cost_fold_shares = tuple(
        fold_positive_pnl_shares(run.results[BASE_COST], resolved_folds).values()
    )
    # Strictly greater than zero, per section 7.3's "zero is not positive". NaN fails it too,
    # which is the direction a hard-floor input must fail in.
    double_cost_positive_folds = sum(1 for value in double_cost_fold_sharpes if value > 0.0)

    metrics = {
        # --- section 7.3 floors, at the level section 7.3 names --------------------------------
        "net_sharpe": float(at_base_cost.net_sharpe),  # 1x: "Net Sharpe (1x cost)"
        "double_cost_sharpe": float(at_double_cost.net_sharpe),  # 2x: "Net Sharpe (2x cost)"
        "triple_cost_sharpe": float(at_triple_cost.net_sharpe),  # 3x: "Net Sharpe (3x cost)"
        "annualized_return": float(at_base_cost.annualized_return),  # 1x: "(1x and 2x)"
        "double_cost_annualized_return": float(at_double_cost.annualized_return),  # 2x: same row
        "positive_fold_count": float(double_cost_positive_folds),  # 2x: "Folds positive at 2x"
        "worst_fold_sharpe": float(min(double_cost_fold_sharpes)),  # 2x: "Worst-fold ... at 2x"
        "cost_share_of_positive_gross": float(  # 1x: "BASE cost share of positive gross PnL"
            at_base_cost.cost_share_of_positive_gross
        ),
        # --- section 7.3 floors that name no level, so base cost (see the module docstring) -----
        "max_drawdown": float(at_base_cost.max_drawdown),  # 1x floor; the 2x twin is below
        "annualized_volatility": float(at_base_cost.annualized_volatility),  # 1x
        "positive_quarter_fraction": float(at_base_cost.positive_quarter_fraction),  # 1x floor
        "annualized_turnover": float(at_base_cost.annualized_turnover),  # 1x floor
        "gross_edge_bps_per_turnover": float(at_base_cost.gross_edge_bps_per_turnover),  # 1x
        "top5_day_share": float(at_base_cost.top5_day_share),  # 1x
        "max_fold_positive_pnl_share": float(max(base_cost_fold_shares)),  # 1x
        "trade_count": float(at_base_cost.trade_count),  # 1x
        "long_gross_pnl": float(at_base_cost.long_gross_pnl),  # 1x
        "short_gross_pnl": float(at_base_cost.short_gross_pnl),  # 1x
        # --- section 8 holdout eligibility, which names no level either, so base cost -----------
        # Same ruling, same reason: "maximum drawdown <= 0.25" and "at least 5 of 8 quarters
        # positive" ask whether the REAL book survived the sealed window, and section 8 already
        # gates cost resilience separately through its 2x return and 2x Sharpe rows.
        "positive_quarter_count": float(at_base_cost.positive_quarter_count),  # 1x
        # --- section 7.4 ranking inputs, all at 2x ---------------------------------------------
        "median_fold_sharpe": float(statistics.median(double_cost_fold_sharpes)),  # 2x
        "calmar": float(at_double_cost.calmar),  # 2x: "calmar_2x", 2x return over 2x drawdown
        # The three metrics the floors already read at 1x, computed a SECOND time at 2x because
        # section 7.4 ranks at 2x. Both values are carried; ``ranking_metrics`` picks these.
        "double_cost_max_drawdown": float(at_double_cost.max_drawdown),  # 2x
        "double_cost_positive_quarter_fraction": float(  # 2x
            at_double_cost.positive_quarter_fraction
        ),
        "double_cost_annualized_turnover": float(at_double_cost.annualized_turnover),  # 2x
    }
    return ScoredVector(
        metrics,
        MetricProvenance(
            stage=stage,
            window_start=window_start,
            window_end=window_end,
            folds=resolved_folds,
        ),
    )


def neighbourhood_median(
    per_point: Sequence[Mapping[str, float]],
) -> dict[str, float] | ScoredVector:
    """Per-metric median across the neighbourhood, failing closed on a non-finite point.

    ``median_metrics`` delegates to ``statistics.median``, which SORTS its input -- and NaN has no
    ordering, so ``nan < x`` and ``x < nan`` are both False and a single NaN point can land
    anywhere in the sorted run. The median then comes back finite and plausible while one of the
    samples behind it was not a number at all: a fail-open on precisely the value every hard floor
    is written to reject. Any metric that is non-finite at ANY point therefore medians to NaN
    here, which every floor comparison then fails, and the gate vector names which one.

    Provenance survives the median when every point has it and they agree, which is what lets the
    adjudicators check a NEIGHBOURHOOD-median vector rather than only a single point's. Points that
    disagree about their stage, window or folds are rejected outright: a median taken across two
    different windows is not a statistic about either of them. A neighbourhood of plain mappings
    still medians to a plain mapping -- the adjudicators reject those on arrival, so nothing is
    silently blessed -- but a MIXTURE of the two is refused here, because a median that quietly
    dropped the one provenance it had would be exactly the fail-open this is preventing.
    """
    medians = median_metrics(per_point)
    for key in medians:
        if not all(math.isfinite(float(point[key])) for point in per_point):
            medians[key] = math.nan
    provenances = [point.provenance for point in per_point if isinstance(point, ScoredVector)]
    if not provenances:
        return medians
    if len(provenances) != len(per_point):
        raise ValueError(
            f"{len(provenances)} of {len(per_point)} neighbourhood points carry provenance; a "
            "neighbourhood is assembled all at once or not at all"
        )
    distinct = {provenance.describe() for provenance in provenances}
    if len(distinct) != 1:
        raise ValueError(
            f"neighbourhood points disagree about their provenance: {sorted(distinct)}"
        )
    return ScoredVector(medians, provenances[0])


def ranking_metrics(
    scored: Mapping[str, float], *, trial_adjusted_confidence: float
) -> dict[str, float]:
    """The section 7.4 view of an assembled vector: every metric at 2x cost.

    Three of these read a DIFFERENT cost level than the identically named floor input, which is
    the whole reason this remap exists rather than the ranking simply reusing ``scored``.
    ``trial_adjusted_confidence`` is not a cost-level quantity at all -- it is the single value
    section 7.3 defines, computed once and never recomputed per cost level -- so it arrives as an
    argument rather than out of the run.
    """
    return {
        "worst_fold_sharpe": float(scored["worst_fold_sharpe"]),  # 2x already, per section 7.3
        "median_fold_sharpe": float(scored["median_fold_sharpe"]),  # 2x
        "calmar": float(scored["calmar"]),  # 2x
        "max_drawdown": float(scored["double_cost_max_drawdown"]),  # 2x, NOT the 1x floor value
        "positive_quarter_fraction": float(  # 2x, NOT the 1x floor value
            scored["double_cost_positive_quarter_fraction"]
        ),
        "annualized_turnover": float(  # 2x, NOT the 1x floor value; section 7.4 tie-break
            scored["double_cost_annualized_turnover"]
        ),
        "trial_adjusted_confidence": float(trial_adjusted_confidence),  # cost-free
    }
