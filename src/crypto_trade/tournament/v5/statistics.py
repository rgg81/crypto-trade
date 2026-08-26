"""Selection statistics for Top-40 V5.

V4-R2 gated on ``max(0, 1 - N*(1-p))`` -- a Bonferroni factor applied to a bootstrap *positivity
probability*. Two defects compounded. The quantity is not a p-value, so multiplying it by N has no
frequentist meaning at all; and the bootstrap ran at 2,000 resamples, quantising the estimate to
5e-4, so at N=180 field trials the 0.90 floor demanded at most one negative resample in two
thousand. Measured across the 94 accepted trials, the best observed probability was 0.9945 and
none cleared it. The gate could not be passed, so the bracket was filled by a fallback path that
ranked on worst-fold Sharpe and therefore rewarded inactivity.

The replacement is the Deflated Sharpe Ratio of Bailey and Lopez de Prado, which is built for
exactly this and which the improvements report already cites. Three things matter in how it is
applied here:

* it is computed against the observed dispersion of a team's *own* trial Sharpes, which the
  hash-chained research journal makes estimable for the first time;
* it corrects for skew and kurtosis, which is not optional on this data -- measured trial moments
  ranged from (0.91, 17.8) to (-36.9, 1396), and a Gaussian Sharpe test on that is meaningless;
* it is reported on development and *gated* only on the sealed blocks, where the team took one
  look and never optimised against the outcome, so the multiplicity there is one rather than N.

Implemented without scipy: promoting it from the notebook group to a runtime dependency would
change ``uv.lock``, which is inside the frozen hash scope that binds a tournament's identity.
"""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pandas as pd

EULER_MASCHERONI = 0.5772156649015329
TRADING_DAYS_PER_YEAR = 365.0


class StatisticsError(ValueError):
    """Raised when a statistic is asked for on evidence that cannot support it."""


def normal_cdf(value: float) -> float:
    """Standard normal CDF via ``math.erf``."""

    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


# Acklam's rational approximation. Relative error below 1.15e-9 across the open unit interval --
# absolute error therefore grows in the tails, reaching ~5e-9 near 1e-6, which is still orders of
# magnitude finer than any threshold this module compares against.
_ACKLAM_A = (
    -3.969683028665376e01,
    2.209460984245205e02,
    -2.759285104469687e02,
    1.383577518672690e02,
    -3.066479806614716e01,
    2.506628277459239e00,
)
_ACKLAM_B = (
    -5.447609879822406e01,
    1.615858368580409e02,
    -1.556989798598866e02,
    6.680131188771972e01,
    -1.328068155288572e01,
)
_ACKLAM_C = (
    -7.784894002430293e-03,
    -3.223964580411365e-01,
    -2.400758277161838e00,
    -2.549732539343734e00,
    4.374664141464968e00,
    2.938163982698783e00,
)
_ACKLAM_D = (
    7.784695709041462e-03,
    3.224671290700398e-01,
    2.445134137142996e00,
    3.754408661907416e00,
)
_ACKLAM_LOW = 0.02425


def normal_quantile(probability: float) -> float:
    """Inverse standard normal CDF."""

    if not 0.0 < probability < 1.0:
        raise StatisticsError("normal_quantile requires a probability strictly inside (0, 1)")
    if probability < _ACKLAM_LOW:
        q = math.sqrt(-2.0 * math.log(probability))
        return (
            (
                (((_ACKLAM_C[0] * q + _ACKLAM_C[1]) * q + _ACKLAM_C[2]) * q + _ACKLAM_C[3]) * q
                + _ACKLAM_C[4]
            )
            * q
            + _ACKLAM_C[5]
        ) / ((((_ACKLAM_D[0] * q + _ACKLAM_D[1]) * q + _ACKLAM_D[2]) * q + _ACKLAM_D[3]) * q + 1.0)
    if probability > 1.0 - _ACKLAM_LOW:
        return -normal_quantile(1.0 - probability)
    q = probability - 0.5
    r = q * q
    return (
        (
            (
                (((_ACKLAM_A[0] * r + _ACKLAM_A[1]) * r + _ACKLAM_A[2]) * r + _ACKLAM_A[3]) * r
                + _ACKLAM_A[4]
            )
            * r
            + _ACKLAM_A[5]
        )
        * q
        / (
            (
                (((_ACKLAM_B[0] * r + _ACKLAM_B[1]) * r + _ACKLAM_B[2]) * r + _ACKLAM_B[3]) * r
                + _ACKLAM_B[4]
            )
            * r
            + 1.0
        )
    )


def _clean(returns: pd.Series | np.ndarray) -> np.ndarray:
    values = np.asarray(pd.Series(returns).astype(float).to_numpy())
    values = values[np.isfinite(values)]
    if values.size < 2:
        raise StatisticsError("at least two finite observations are required")
    return values


def sharpe_ratio(returns: pd.Series | np.ndarray, *, annualised: bool = False) -> float:
    """Per-period Sharpe, or annualised at 365 periods per year."""

    values = _clean(returns)
    deviation = float(values.std(ddof=1))
    if deviation <= 1e-15:
        return 0.0
    ratio = float(values.mean()) / deviation
    return ratio * math.sqrt(TRADING_DAYS_PER_YEAR) if annualised else ratio


def _moments(values: np.ndarray) -> tuple[float, float]:
    """Sample skewness and non-excess kurtosis."""

    deviation = float(values.std(ddof=1))
    if deviation <= 1e-15:
        return 0.0, 3.0
    centred = (values - values.mean()) / deviation
    return float((centred**3).mean()), float((centred**4).mean())


def probabilistic_sharpe_ratio(returns: pd.Series | np.ndarray, *, benchmark: float = 0.0) -> float:
    """Probability the true per-period Sharpe exceeds ``benchmark``.

    Corrects for skew and kurtosis. On this data that is load-bearing rather than a refinement:
    a fat left tail makes a Gaussian test far too confident about a positive mean.
    """

    values = _clean(returns)
    observed = sharpe_ratio(values)
    skew, kurtosis = _moments(values)
    count = values.size
    variance = 1.0 - skew * observed + 0.25 * (kurtosis - 1.0) * observed * observed
    if variance <= 0.0:
        raise StatisticsError("degenerate Sharpe variance; the return series is pathological")
    statistic = (observed - benchmark) * math.sqrt(count - 1) / math.sqrt(variance)
    return normal_cdf(statistic)


def annualised_to_period_variance(annualised_deviation: float) -> float:
    """Convert a dispersion of annualised Sharpes into per-period variance.

    The statistic is linear in the dispersion, so feeding it annualised units silently returns an
    annualised benchmark and every later annualisation compounds the error. Journalled trial
    Sharpes are annualised; this is the conversion that keeps the comparison honest.
    """

    return (annualised_deviation / math.sqrt(TRADING_DAYS_PER_YEAR)) ** 2


def expected_maximum_sharpe(trial_count: int, trial_sharpe_variance: float) -> float:
    """Expected maximum **per-period** Sharpe from ``trial_count`` independent null searches.

    ``trial_sharpe_variance`` must be in per-period units, matching the Sharpe it will be compared
    against; use :func:`annualised_to_period_variance` on a journalled dispersion.

    This is the benchmark a candidate has to beat to be distinguishable from the best of its own
    search. It scales with the dispersion of the team's *own* trials, so a team whose twelve
    attempts cluster tightly faces a lower bar than one that sprayed.
    """

    if trial_count < 1:
        raise StatisticsError("trial_count must be at least 1")
    if trial_sharpe_variance < 0.0:
        raise StatisticsError("trial_sharpe_variance cannot be negative")
    if trial_count == 1 or trial_sharpe_variance == 0.0:
        return 0.0
    deviation = math.sqrt(trial_sharpe_variance)
    upper = normal_quantile(1.0 - 1.0 / trial_count)
    lower = normal_quantile(1.0 - 1.0 / (trial_count * math.e))
    return deviation * ((1.0 - EULER_MASCHERONI) * upper + EULER_MASCHERONI * lower)


@dataclasses.dataclass(frozen=True, slots=True)
class DeflatedSharpe:
    """A Sharpe claim priced against the search that produced it."""

    observed_sharpe: float
    observed_sharpe_annualised: float
    benchmark_sharpe: float
    benchmark_sharpe_annualised: float
    probability: float
    trial_count: int
    trial_sharpe_variance: float
    observations: int
    skewness: float
    kurtosis: float

    def as_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)


def deflated_sharpe_ratio(
    returns: pd.Series | np.ndarray,
    *,
    trial_count: int,
    trial_sharpe_variance: float,
) -> DeflatedSharpe:
    """Probability the true Sharpe beats the best a null search of this size would produce."""

    values = _clean(returns)
    benchmark = expected_maximum_sharpe(trial_count, trial_sharpe_variance)
    skew, kurtosis = _moments(values)
    annualisation = math.sqrt(TRADING_DAYS_PER_YEAR)
    return DeflatedSharpe(
        observed_sharpe=sharpe_ratio(values),
        observed_sharpe_annualised=sharpe_ratio(values, annualised=True),
        benchmark_sharpe=benchmark,
        benchmark_sharpe_annualised=benchmark * annualisation,
        probability=probabilistic_sharpe_ratio(values, benchmark=benchmark),
        trial_count=trial_count,
        trial_sharpe_variance=trial_sharpe_variance,
        observations=int(values.size),
        skewness=skew,
        kurtosis=kurtosis,
    )


def stationary_bootstrap_indices(
    length: int, *, samples: int, expected_block: float, seed: int
) -> np.ndarray:
    """Politis-Romano stationary bootstrap index matrix.

    Block lengths are geometric rather than fixed, so a result does not depend on where an
    arbitrary block grid happens to fall -- the circular fixed-block scheme V4 used made the
    answer a function of that alignment.
    """

    if length < 2:
        raise StatisticsError("bootstrap requires at least two observations")
    if samples < 100:
        raise StatisticsError("bootstrap requires at least 100 resamples")
    if expected_block <= 0.0:
        raise StatisticsError("expected_block must be positive")
    generator = np.random.default_rng(seed)
    restart = generator.random((samples, length)) < (1.0 / expected_block)
    restart[:, 0] = True
    starts = generator.integers(0, length, size=(samples, length))
    indices = np.empty((samples, length), dtype=np.int64)
    current = starts[:, 0].copy()
    for position in range(length):
        current = np.where(restart[:, position], starts[:, position], (current + 1) % length)
        indices[:, position] = current
    return indices


def bootstrap_probability_positive_mean(
    returns: pd.Series | np.ndarray,
    *,
    samples: int = 20_000,
    expected_block: float = 10.0,
    seed: int = 20260826,
) -> float:
    """Fraction of stationary-bootstrap resamples whose arithmetic mean is positive.

    20,000 resamples rather than 2,000: the coarser grid quantised the estimate to 5e-4, which is
    what made the old adjusted threshold unrepresentable rather than merely strict.
    """

    values = _clean(returns)
    indices = stationary_bootstrap_indices(
        values.size, samples=samples, expected_block=expected_block, seed=seed
    )
    return float((values[indices].mean(axis=1) > 0.0).mean())


def benjamini_hochberg(p_values: dict[str, float], *, q: float) -> dict[str, bool]:
    """Benjamini-Hochberg FDR control across independent research lanes.

    Family-wise correction is the wrong instrument here. Fifteen teams pursuing fifteen different
    mechanisms are fifteen research programmes, not 180 draws at one target, and one team's false
    positive does not make another's evidence weaker. Controlling the false-discovery rate keeps
    the bar a bar; controlling the family-wise rate turns it into a competition.
    """

    if not 0.0 < q < 1.0:
        raise StatisticsError("q must lie strictly inside (0, 1)")
    if not p_values:
        return {}
    ordered = sorted(p_values.items(), key=lambda item: (item[1], item[0]))
    total = len(ordered)
    largest_passing = 0
    for rank, (_, value) in enumerate(ordered, start=1):
        if value <= q * rank / total:
            largest_passing = rank
    passing = {name for name, _ in ordered[:largest_passing]}
    return {name: name in passing for name in p_values}


__all__ = [
    "DeflatedSharpe",
    "annualised_to_period_variance",
    "EULER_MASCHERONI",
    "StatisticsError",
    "benjamini_hochberg",
    "bootstrap_probability_positive_mean",
    "deflated_sharpe_ratio",
    "expected_maximum_sharpe",
    "normal_cdf",
    "normal_quantile",
    "probabilistic_sharpe_ratio",
    "sharpe_ratio",
    "stationary_bootstrap_indices",
]
