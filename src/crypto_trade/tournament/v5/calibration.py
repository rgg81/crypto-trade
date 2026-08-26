"""Pre-activation calibration of the V5 qualification bar.

A gate nobody measured is a gate nobody can trust. V4-R2 shipped a field-adjusted confidence floor
that no candidate could reach -- the best of ninety-four measured trials scored 0.01 against a 0.90
requirement -- and the consequence was not a strict tournament but a bypassed one: the bracket was
filled from a fallback path that ranked on worst-fold Sharpe and therefore preferred a book that
barely traded.

This module measures what the bar actually does before it can be activated. It drives the
*production* gate code over two populations:

* a **null** population that must mostly fail, built to look structurally identical to a real
  submission so that only edge is missing;
* a **plausible-good** population that must mostly pass, built at a grid of known true Sharpes.

Both run on development-derived synthetic paths only. Nothing here reads a sealed or holdout row,
so the numbers can be committed before either is opened.

The output is an operating characteristic -- a measured false-positive rate and a measured power
at a stated true Sharpe -- which is the claim the charter has to publish. A bar that no plausible
strategy clears cannot be activated, and neither can one a null population walks through.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Sequence

import numpy as np

from crypto_trade.tournament.v5 import statistics as stats
from crypto_trade.tournament.v5.gates import (
    SEALED_STAGE,
    GateThresholds,
    SelectionEvidence,
    assess,
)

NULL = "null"
GOOD = "plausible_good"

# Structural profile of a book that is a genuine portfolio. The calibration is about the
# *performance* bar, so every null and good candidate is given healthy structure and differs only
# in edge; degenerate books are calibrated separately because they must fail on structure alone.
_HEALTHY = {
    "mean_gross_exposure": 0.55,
    "median_effective_breadth": 11.0,
    "breadth_pass_fraction": 0.95,
    "active_bar_fraction": 0.97,
    "long_exposure_share": 0.50,
    "short_exposure_share": 0.50,
    "realized_annual_volatility": 0.10,
    "risk_unit_capped_fraction": 0.05,
    "annualised_turnover": 25.0,
    "gross_edge_bps_per_turnover": 60.0,
    "cost_share_of_positive_gross": 0.20,
    "accepted_trials": 12,
    "source_review_passed": True,
    "invariance_suite_passed": True,
}


class CalibrationError(ValueError):
    """Raised when a calibration request cannot produce a meaningful measurement."""


def _fold_fraction(returns: np.ndarray, folds: int = 5) -> float:
    chunks = np.array_split(returns, folds)
    return float(np.mean([chunk.sum() > 0.0 for chunk in chunks]))


def deletion_profile_p05(returns: np.ndarray, *, block: int = 30) -> float:
    """Fifth percentile of the Sharpe surviving every contiguous deletion of ``block`` days.

    A percentile rather than the minimum: over ~900 overlapping deletions the minimum is an
    extreme-value statistic and ranks noise. This subsumes "remove the best month" -- measured on
    the V4-R9 holdout, the winner's best-month-removed Sharpe was 0.674 while its worst 30-day
    contiguous deletion gave 0.600, so the calendar-restricted version flatters.
    """

    if returns.size <= block + 2:
        raise CalibrationError("series too short for a deletion profile")
    survivors = [
        stats.sharpe_ratio(np.delete(returns, slice(start, start + block)), annualised=True)
        for start in range(returns.size - block)
    ]
    return float(np.percentile(survivors, 5))


def evidence_from_returns(
    returns: np.ndarray,
    *,
    trial_count: int,
    trial_sharpe_dispersion: float,
    top_symbol_share: float = 0.18,
    overrides: dict[str, object] | None = None,
) -> SelectionEvidence:
    """Build gate evidence from a return path, computing every statistical field for real.

    The statistical fields are never hand-set: a null path has to fail the deflated-Sharpe gate
    because its numbers say so, not because the fixture declared it.
    """

    variance = stats.annualised_to_period_variance(trial_sharpe_dispersion)
    deflated = stats.deflated_sharpe_ratio(
        returns, trial_count=trial_count, trial_sharpe_variance=variance
    )
    equity = np.cumprod(1.0 + returns)
    drawdown = float(np.max(1.0 - equity / np.maximum.accumulate(equity)))
    annualised = float(np.mean(returns) * stats.TRADING_DAYS_PER_YEAR)
    fields: dict[str, object] = {
        **_HEALTHY,
        "ruined": False,
        "triple_cost_annualised_return": annualised - 0.02,
        "net_sharpe": stats.sharpe_ratio(returns, annualised=True),
        "double_cost_sharpe": stats.sharpe_ratio(returns, annualised=True) * 0.8,
        "max_drawdown": drawdown,
        "positive_fold_fraction": _fold_fraction(returns),
        "deflated_sharpe_probability": deflated.probability,
        "top_symbol_gross_pnl_share": top_symbol_share,
        "deletion_profile_p05_sharpe": deletion_profile_p05(returns),
    }
    fields.update(overrides or {})
    return SelectionEvidence(**fields)  # type: ignore[arg-type]


def _path(true_annual_sharpe: float, *, periods: int, seed: int) -> np.ndarray:
    daily_volatility = 0.10 / math.sqrt(stats.TRADING_DAYS_PER_YEAR)
    drift = true_annual_sharpe / stats.TRADING_DAYS_PER_YEAR * 0.10
    return np.random.default_rng(seed).normal(drift, daily_volatility, size=periods)


def build_null_population(
    *, count: int, periods: int, seed: int, trial_count: int, dispersion: float
) -> list[SelectionEvidence]:
    """Books with a real book's structure and no edge.

    Includes a *lottery search*: for each candidate, draw ``trial_count`` zero-edge paths and keep
    the best. That is the population the correction exists to catch -- a team that searched until
    something looked good -- and it is far harder to reject than a single null draw.
    """

    population: list[SelectionEvidence] = []
    generator = np.random.default_rng(seed)
    for index in range(count):
        if index % 2 == 0:
            returns = _path(0.0, periods=periods, seed=int(generator.integers(1 << 31)))
        else:
            attempts = [
                _path(0.0, periods=periods, seed=int(generator.integers(1 << 31)))
                for _ in range(trial_count)
            ]
            returns = max(attempts, key=lambda path: stats.sharpe_ratio(path))
        population.append(
            evidence_from_returns(
                returns, trial_count=trial_count, trial_sharpe_dispersion=dispersion
            )
        )
    return population


def build_good_population(
    *,
    sharpe_grid: Sequence[float],
    per_level: int,
    periods: int,
    seed: int,
    trial_count: int,
    dispersion: float,
) -> dict[float, list[SelectionEvidence]]:
    """Books with a known true Sharpe and a real book's structure."""

    generator = np.random.default_rng(seed)
    population: dict[float, list[SelectionEvidence]] = {}
    for level in sharpe_grid:
        population[level] = [
            evidence_from_returns(
                _path(level, periods=periods, seed=int(generator.integers(1 << 31))),
                trial_count=trial_count,
                trial_sharpe_dispersion=dispersion,
            )
            for _ in range(per_level)
        ]
    return population


def build_degenerate_population() -> list[tuple[str, SelectionEvidence]]:
    """Books that are not portfolios. These must fail on structure alone, at every stage.

    Each is drawn from something a prior edition actually produced rather than invented: the
    two-name book, the barely-trading book at 0.037 mean gross, the one-sided leg, the
    cost-annihilated book at 268x turnover, and the ruined trial.
    """

    def make(**overrides: object) -> SelectionEvidence:
        return evidence_from_returns(
            _path(1.5, periods=600, seed=17),
            trial_count=12,
            trial_sharpe_dispersion=0.5,
            overrides=overrides,
        )

    return [
        ("two_name_book", make(median_effective_breadth=2.17, breadth_pass_fraction=0.10)),
        ("barely_trading", make(mean_gross_exposure=0.037, active_bar_fraction=0.47)),
        ("one_sided", make(short_exposure_share=0.01)),
        ("cost_annihilated", make(annualised_turnover=268.0, gross_edge_bps_per_turnover=-358.0)),
        ("ruined", make(ruined=True)),
    ]


@dataclasses.dataclass(frozen=True, slots=True)
class CalibrationReport:
    """The measured operating characteristic of a frozen bar."""

    stage: str
    null_count: int
    null_pass_rate: float
    degenerate_pass_rate: float
    power_by_sharpe: dict[float, float]
    thresholds: dict[str, object]

    def power_at(self, level: float) -> float:
        if level not in self.power_by_sharpe:
            raise CalibrationError(f"no measured power at true Sharpe {level}")
        return self.power_by_sharpe[level]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "top40-v5-calibration-v1",
            "stage": self.stage,
            "null_count": self.null_count,
            "null_pass_rate": self.null_pass_rate,
            "degenerate_pass_rate": self.degenerate_pass_rate,
            "power_by_sharpe": {str(k): v for k, v in sorted(self.power_by_sharpe.items())},
            "thresholds": self.thresholds,
        }


def _pass_rate(population: Sequence[SelectionEvidence], thresholds, stage) -> float:  # type: ignore[no-untyped-def]
    if not population:
        raise CalibrationError("cannot measure a pass rate on an empty population")
    outcomes = [assess(item, thresholds, stage=stage).eligible for item in population]
    return float(np.mean(outcomes))


def calibrate(
    thresholds: GateThresholds,
    *,
    stage: str = SEALED_STAGE,
    null_count: int = 120,
    per_level: int = 30,
    periods: int = 360,
    sharpe_grid: Sequence[float] = (0.5, 1.0, 1.5, 2.0),
    seed: int = 20260826,
    trial_count: int = 1,
    dispersion: float = 0.768,
) -> CalibrationReport:
    """Measure what this bar does, on development-derived synthetic paths only.

    ``periods`` defaults to the sealed budget of 360 days rather than a comfortable length: the
    bar has to be characterised on the evidence it will actually see.

    ``trial_count`` defaults to one because that is the sealed stage's true multiplicity. The
    search ran on visible data the sealed blocks never saw, so holding them out has already
    removed the selection bias; deflating again charges the same search twice and cost power at a
    true Sharpe of 1.0 0.70 -> 0.24 while leaving the false-positive rate essentially unchanged.
    Pass the team's journalled trial count when characterising the *development* report instead.
    """

    nulls = build_null_population(
        count=null_count,
        periods=periods,
        seed=seed,
        trial_count=trial_count,
        dispersion=dispersion,
    )
    goods = build_good_population(
        sharpe_grid=sharpe_grid,
        per_level=per_level,
        periods=periods,
        seed=seed + 1,
        trial_count=trial_count,
        dispersion=dispersion,
    )
    degenerate = [item for _, item in build_degenerate_population()]
    return CalibrationReport(
        stage=stage,
        null_count=len(nulls),
        null_pass_rate=_pass_rate(nulls, thresholds, stage),
        degenerate_pass_rate=_pass_rate(degenerate, thresholds, stage),
        power_by_sharpe={
            level: _pass_rate(items, thresholds, stage) for level, items in goods.items()
        },
        thresholds=dataclasses.asdict(thresholds),
    )


def assert_bar_is_usable(
    report: CalibrationReport,
    *,
    maximum_null_pass_rate: float,
    minimum_power_at: dict[float, float],
) -> None:
    """Activation gate. A bar no plausible strategy clears cannot be activated.

    Neither can one a null population walks through: the failure V4-R2 shipped was unpassable in
    one direction, and the opposite failure is just as disqualifying.
    """

    if report.degenerate_pass_rate > 0.0:
        raise CalibrationError(
            f"degenerate books cleared the bar at rate {report.degenerate_pass_rate:.3f}; "
            "structural gates must reject a book that is not a portfolio"
        )
    if report.null_pass_rate > maximum_null_pass_rate:
        raise CalibrationError(
            f"null pass rate {report.null_pass_rate:.3f} exceeds {maximum_null_pass_rate:.3f}"
        )
    for level, required in sorted(minimum_power_at.items()):
        measured = report.power_at(level)
        if measured < required:
            raise CalibrationError(
                f"power {measured:.3f} at true Sharpe {level} is below the required "
                f"{required:.3f}; this bar cannot be passed by a plausible strategy"
            )


__all__ = [
    "GOOD",
    "NULL",
    "CalibrationError",
    "CalibrationReport",
    "assert_bar_is_usable",
    "build_degenerate_population",
    "build_good_population",
    "build_null_population",
    "calibrate",
    "deletion_profile_p05",
    "evidence_from_returns",
]
