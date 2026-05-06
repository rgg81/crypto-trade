"""v3 validation helpers — CPCV, PBO (CSCV), PSR, DSR, and n_eff.

iter-v3/002 replaces the buggy iter-v3/001 implementations with correct
algorithms from AFML Ch. 11-12 and Bailey & López de Prado (2014).

Changes from iter-v3/001:
  1. ``pbo_from_cpcv`` — complete rewrite.  Now accepts a 2-D matrix of
     shape (N_paths, S_strategies) and implements the CSCV estimator.
     The 1-D "one Sharpe per path" form (S=1) correctly returns NaN.
  2. ``combinatorial_purged_cv`` — adds a runtime assertion that the
     supplied gap equals the required formula value (embargo fix).
  3. ``deflated_sharpe_ratio_v3`` — new; removes the negative-SR clamp
     that masked unprofitable strategies in iter-v3/001.
  4. ``n_effective_trials`` — unchanged; valid for a true n_trials×T matrix.

Library stack (from brief Section 9):
  No new dependencies.  Pure-Python + numpy + scipy.
  mlfinpy / pypbo unavailable on Python 3.13.

References:
  - Bailey, D. & López de Prado, M. (2014),
    "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest
    Overfitting, and Non-Normality", Journal of Portfolio Management.
  - López de Prado, M. (2018), *Advances in Financial Machine Learning*,
    Chapters 11 and 12.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from itertools import combinations
from typing import NamedTuple

import numpy as np
from scipy.stats import norm

# ---------------------------------------------------------------------------
# Constants re-exported for runner pre-flight assertions
# ---------------------------------------------------------------------------

#: Documented gap formula for v3: (timeout_candles + 1) * n_symbols
#: With timeout=21 candles (10080 min / 480 min) and 3 symbols → 66.
#: Updated from 88 (4 symbols) to 66 (3 symbols) at iter-v3/013 when MKR was dropped.
REQUIRED_GAP: int = (21 + 1) * 3  # 66

# ---------------------------------------------------------------------------
# CPCV — Combinatorial Purged Cross-Validation (AFML Ch. 12)
# ---------------------------------------------------------------------------


def combinatorial_purged_cv(
    n_samples: int,
    n_splits: int = 10,
    n_test_splits: int = 2,
    gap: int = 0,
    embargo: int = 0,
    expected_gap: int | None = None,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Generate C(N, k) train/test index splits via CPCV.

    Parameters
    ----------
    n_samples
        Total number of samples (e.g., number of IS-window candles).
    n_splits
        N — number of groups to split data into. Default 10.
    n_test_splits
        k — number of groups held out for testing in each combination.
        C(N, k) total paths. Default 2 → C(10,2)=45 paths.
    gap
        Number of samples to exclude on both sides of each test boundary
        (purge gap). Implements López de Prado's purge for label overlap.
        For v3: gap = (timeout_candles+1)*n_symbols = (21+1)*3 = 66
        (3-symbol BCH+LDO+TRX universe since iter-v3/013).
    embargo
        Additional samples to embargo after each test block (prevent leakage
        from autocorrelated features). Default 0; recommend ~1% of T.
    expected_gap
        If supplied, asserts that ``gap == expected_gap``.  If the caller
        passes a degraded gap (e.g. min(88, n_trades//20)), this assertion
        fires and the run fails loudly instead of silently degrading the
        purge guarantee.  iter-v3/001 bug: gap was silently rescaled 88→11.

    Returns
    -------
    list of (train_indices, test_indices) tuples
        len = C(n_splits, n_test_splits). Indices are numpy int arrays
        into [0, n_samples).

    Raises
    ------
    AssertionError
        If ``expected_gap`` is supplied and ``gap != expected_gap``.
    ValueError
        If n_splits or n_test_splits are out of bounds.
    """
    if expected_gap is not None and gap != expected_gap:
        raise AssertionError(
            f"combinatorial_purged_cv: gap={gap} does not match expected_gap={expected_gap}. "
            f"The documented formula for v3 is (timeout_candles+1)*n_symbols = {REQUIRED_GAP}. "
            "Silent gap rescaling is forbidden. Fix the caller to pass the correct gap "
            "or update expected_gap if the formula changed."
        )

    if n_splits < 2:
        raise ValueError(f"n_splits must be >= 2, got {n_splits}")
    if n_test_splits < 1 or n_test_splits >= n_splits:
        raise ValueError(f"n_test_splits must be in [1, n_splits-1], got {n_test_splits}")

    indices = np.arange(n_samples, dtype=np.intp)

    # Split data into N groups
    group_sizes = np.full(n_splits, n_samples // n_splits, dtype=int)
    group_sizes[: n_samples % n_splits] += 1  # distribute remainder

    group_starts = np.concatenate([[0], np.cumsum(group_sizes[:-1])])
    group_ends = np.cumsum(group_sizes)  # exclusive end indices

    splits: list[tuple[np.ndarray, np.ndarray]] = []

    for test_groups in combinations(range(n_splits), n_test_splits):
        # Test indices: union of selected groups
        test_idx_list: list[np.ndarray] = []
        for g in test_groups:
            test_idx_list.append(indices[group_starts[g] : group_ends[g]])
        test_idx = np.concatenate(test_idx_list)

        # Purge: exclude gap samples on BOTH SIDES of each test boundary
        purged: set[int] = set()
        for g in test_groups:
            lo = max(0, group_starts[g] - gap)
            hi = min(n_samples, group_ends[g] + gap + embargo)
            for idx in range(lo, hi):
                purged.add(idx)

        # Train indices: all indices not in test and not purged
        test_set = set(test_idx.tolist())
        train_idx = np.array(
            [i for i in range(n_samples) if i not in test_set and i not in purged],
            dtype=np.intp,
        )

        splits.append((train_idx, test_idx))

    return splits


def cpcv_paths_from_splits(
    splits: list[tuple[np.ndarray, np.ndarray]],
    all_returns: np.ndarray,
) -> list[np.ndarray]:
    """Extract test-fold return sequences from CPCV splits.

    Parameters
    ----------
    splits
        Output of ``combinatorial_purged_cv``.
    all_returns
        Full return array of length n_samples. Test returns are extracted
        per path.

    Returns
    -------
    list of numpy arrays, one per path, containing the test-fold returns.
    """
    return [all_returns[test_idx] for _, test_idx in splits]


# ---------------------------------------------------------------------------
# PBO — Probability of Backtest Overfitting
#        CSCV estimator, AFML Ch. 12 / Bailey & LdP 2014
# ---------------------------------------------------------------------------


class PBOResult(NamedTuple):
    """Result of the CSCV PBO estimator."""

    pbo: float | None
    """PBO in [0, 1], or None when S=1 (undefined)."""

    frac_positive_paths: float
    """Fraction of CPCV paths with positive metric.  Always available."""

    path_sharpe_quartiles: tuple[float, float, float]
    """25th, 50th, 75th percentile of path metrics."""

    n_splits_evaluated: int
    """Number of IS/OOS splits used in the CSCV estimate."""

    note: str
    """Human-readable explanation (used in engineering report)."""


def pbo_from_cpcv(
    path_metric_matrix: np.ndarray | list,
    max_splits: int = 5000,
    rng: np.random.Generator | None = None,
) -> PBOResult:
    """Probability of Backtest Overfitting — CSCV on a strategy × path matrix.

    Implements Bailey & López de Prado's CSCV estimator (2014):

        For each symmetric IS/OOS split of the N CPCV paths:
          1. Compute each strategy's *mean IS metric* (mean over IS-half paths).
          2. Identify the IS-best strategy n* = argmax(mean IS metric).
          3. Compute n*'s *mean OOS metric* (mean over OOS-half paths).
          4. Compute n*'s OOS rank omega = rank(n*) / S_strategies.
          5. Record omega.
        PBO = P(omega < 0.5) = fraction of IS/OOS splits where the IS-best
              strategy falls in the lower half of OOS performance.

    Parameters
    ----------
    path_metric_matrix
        Either:
        - 2-D array of shape (N_paths, S_strategies). Element [i, s] is the
          OOS metric for strategy s on CPCV path i.  Higher is better.
        - 1-D array of length N_paths (S=1 case, vacuous — returns NaN).
    max_splits
        Maximum number of IS/OOS symmetric splits evaluated (C(N, N//2)
        can be exponential for large N; cap for tractability).
    rng
        Optional numpy random Generator for random sampling of IS/OOS splits
        when C(N, N//2) > max_splits.  When provided, ``max_splits``
        combinations are drawn uniformly at random (without replacement)
        from all C(N, N//2) possible splits.  When None (default), the first
        ``max_splits`` combinations from ``itertools.combinations`` are used
        (fully deterministic — original behaviour).  Supplying different
        Generator objects (via ``np.random.default_rng(seed)``) produces
        different random samples, enabling cross-seed PBO variance estimation.
        Has no effect when C(N, N//2) ≤ max_splits (all splits evaluated
        regardless).

    Returns
    -------
    PBOResult
        .pbo     — float in [0,1], or None if S=1 (undefined).
        .frac_positive_paths — always computed (descriptive fallback).
        .path_sharpe_quartiles — (p25, p50, p75).
        .n_splits_evaluated — splits used.
        .note — explanation string.

    Notes
    -----
    PBO interpretation (from brief Section 8, criterion 8):
    - PBO < 0.4  → strategy appears to generalise (v3 MERGE threshold)
    - PBO ≈ 0.5  → chance baseline (IS-best strategy regresses to median OOS)
    - PBO > 0.6  → overfit (IS-best consistently in lower OOS half)

    For S=1 there is no strategy axis — omega is trivially 1.0 regardless
    of performance, so PBO is undefined.  Return None and use
    frac_positive_paths as the descriptive statistic instead.
    """
    mat = np.asarray(path_metric_matrix, dtype=float)

    # ---- Normalise to 2-D
    if mat.ndim == 1:
        mat = mat.reshape(-1, 1)
    if mat.ndim != 2:
        raise ValueError(f"path_metric_matrix must be 1-D or 2-D, got shape {mat.shape}")

    n_paths, n_strategies = mat.shape

    # ---- Descriptive stats (always computed)
    flat = mat.ravel()
    flat_finite = flat[np.isfinite(flat)]
    frac_pos = float(np.mean(flat_finite > 0)) if len(flat_finite) > 0 else float("nan")
    q25, q50, q75 = (
        (
            float(np.percentile(flat_finite, 25)),
            float(np.percentile(flat_finite, 50)),
            float(np.percentile(flat_finite, 75)),
        )
        if len(flat_finite) >= 4
        else (float("nan"), float("nan"), float("nan"))
    )

    # ---- S=1: undefined
    if n_strategies == 1:
        note = (
            f"PBO undefined: path_metric_matrix has S=1 strategy axis. "
            f"CSCV requires S>1. Descriptive: frac_positive_paths={frac_pos:.3f}, "
            f"path_sharpe_quartiles=({q25:.3f}, {q50:.3f}, {q75:.3f}) from {n_paths} paths."
        )
        return PBOResult(
            pbo=None,
            frac_positive_paths=frac_pos,
            path_sharpe_quartiles=(q25, q50, q75),
            n_splits_evaluated=0,
            note=note,
        )

    if n_paths < 2:
        note = "PBO undefined: fewer than 2 paths."
        return PBOResult(
            pbo=None,
            frac_positive_paths=frac_pos,
            path_sharpe_quartiles=(q25, q50, q75),
            n_splits_evaluated=0,
            note=note,
        )

    # ---- CSCV: enumerate (or sample) symmetric IS/OOS splits of the N paths
    half = n_paths // 2
    n_omega_below_half = 0
    n_splits = 0

    all_path_indices = list(range(n_paths))

    # Total number of possible symmetric IS/OOS splits
    n_total_splits = math.comb(n_paths, half)
    use_random_sampling = rng is not None and n_total_splits > max_splits

    if use_random_sampling:
        # Random sampling: draw max_splits indices into the combinations enumeration
        # without replacement, then materialise only those combinations.
        # Strategy: enumerate ALL combinations into a list only when
        # n_total_splits is tractable (≤ 2 × max_splits); otherwise sample
        # by index using the bijective combinadic algorithm.
        # For the per-cell use-case (n_paths=45, half=22), n_total_splits ≈ 6.5e12
        # which is too large to enumerate.  We instead use rejection sampling on
        # the combinations generator to approximate random sampling with low
        # collision probability: draw max_splits sorted subsets of {0..n_paths-1}
        # of size ``half`` via rng.choice on individual positions.
        #
        # Simpler and correct implementation: pre-draw max_splits random IS masks
        # using rng.choice on [n_paths], each of size half, deduplicated.
        seen: set[tuple[int, ...]] = set()
        split_list: list[tuple[int, ...]] = []
        # Safety cap: avoid infinite loop if collisions are frequent
        max_attempts = max_splits * 20
        attempts = 0
        while len(split_list) < max_splits and attempts < max_attempts:
            chosen = tuple(sorted(rng.choice(n_paths, size=half, replace=False).tolist()))
            if chosen not in seen:
                seen.add(chosen)
                split_list.append(chosen)
            attempts += 1
        iter_splits: list[tuple[int, ...]] = split_list
    else:
        # Deterministic: first max_splits from itertools.combinations (original behaviour)
        iter_splits = []
        for combo in combinations(all_path_indices, half):
            iter_splits.append(combo)
            if len(iter_splits) >= max_splits:
                break

    for is_path_indices in iter_splits:
        oos_path_indices = [i for i in all_path_indices if i not in set(is_path_indices)]

        is_mat = mat[list(is_path_indices), :]  # (half, S)
        oos_mat = mat[list(oos_path_indices), :]  # (n_paths - half, S)

        # Mean IS metric per strategy
        is_means = np.nanmean(is_mat, axis=0)  # shape (S,)
        # IS-best strategy index
        n_star = int(np.argmax(is_means))

        # n*'s mean OOS metric
        n_star_oos_mean = float(np.nanmean(oos_mat[:, n_star]))

        # OOS means for all strategies
        oos_means = np.nanmean(oos_mat, axis=0)  # shape (S,)

        # Rank of n* in OOS (0-based, ascending)
        # omega = (rank + 1) / S; omega < 0.5 means n* is in lower OOS half
        rank = int(np.sum(oos_means < n_star_oos_mean))  # number of strategies worse than n*
        omega = float(rank + 1) / float(n_strategies)  # rank / S in (0,1]

        if omega < 0.5:
            n_omega_below_half += 1

        n_splits += 1

    pbo_val = float(n_omega_below_half) / float(n_splits) if n_splits > 0 else float("nan")

    note = (
        f"CSCV PBO on ({n_paths} paths, {n_strategies} strategies): "
        f"PBO={pbo_val:.4f} from {n_splits} IS/OOS splits. "
        f"frac_positive_paths={frac_pos:.3f}."
    )
    return PBOResult(
        pbo=pbo_val,
        frac_positive_paths=frac_pos,
        path_sharpe_quartiles=(q25, q50, q75),
        n_splits_evaluated=n_splits,
        note=note,
    )


# ---------------------------------------------------------------------------
# DSR — Deflated Sharpe Ratio (clamp-free, v3 version)
# ---------------------------------------------------------------------------


def deflated_sharpe_ratio_v3(
    observed_sr: float,
    num_trials: int,
    backtest_length: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
) -> dict[str, float]:
    """Deflated Sharpe Ratio after multiple-testing correction.

    Identical to ``validation_v2.deflated_sharpe_ratio`` EXCEPT:
    - No clamping of the p_value to 0 for negative observed_sr.
      The LdP-correct formula is ``Phi((SR_obs - E[max_SR]) / sigma_SR)``
      which is well-defined for any sign of SR_obs.  A negative SR_obs
      returns a tiny but positive probability (not zero).

    Parameters
    ----------
    observed_sr
        Observed Sharpe ratio (may be negative — not clamped).
    num_trials
        Total number of strategy configurations evaluated.
    backtest_length
        Number of return observations used to compute observed_sr.
    skewness
        Skewness of the return series.
    kurtosis
        Raw kurtosis (3 = Gaussian).

    Returns
    -------
    dict with keys: ``dsr`` (z-score), ``p_value``, ``expected_max_sr``,
    ``sr_std_err``.

    Notes
    -----
    The v2 implementation ``validation_v2.deflated_sharpe_ratio`` returns
    p_value = norm.cdf(dsr_z) which does NOT clamp.  The actual clamp was
    in the iter-v3/001 runner (run_baseline_v3.py:935) which set
    ``dsr_val = 0.0`` in the else-branch when observed_sr could not be
    computed from insufficient samples.  This function does not clamp and
    the runner must not override its return value with 0.0.
    """
    euler_mascheroni = 0.5772156649

    if num_trials <= 0:
        raise ValueError("num_trials must be positive")
    if backtest_length <= 1:
        raise ValueError("backtest_length must be > 1")

    variance_num = 1.0 - skewness * observed_sr + (kurtosis - 1.0) / 4.0 * observed_sr**2
    variance_num = max(variance_num, 1e-12)
    sr_std = math.sqrt(variance_num / (backtest_length - 1))

    ln_n = math.log(num_trials)
    if num_trials == 1 or ln_n <= 0:
        expected_max_sr = 0.0
    else:
        from scipy.stats import norm as _norm

        expected_max_sr = (1.0 - euler_mascheroni) * _norm.ppf(
            1.0 - 1.0 / num_trials
        ) + euler_mascheroni * _norm.ppf(1.0 - 1.0 / (num_trials * math.e))

    dsr_z = (observed_sr - expected_max_sr) / sr_std if sr_std > 0 else 0.0
    p_value = float(norm.cdf(dsr_z))
    # NOTE: p_value is in (0, 1) for all inputs — no clamp applied.

    return {
        "dsr": float(dsr_z),
        "p_value": p_value,  # NOT clamped to 0 even when observed_sr < 0
        "expected_max_sr": float(expected_max_sr),
        "sr_std_err": float(sr_std),
    }


# ---------------------------------------------------------------------------
# PSR — Probabilistic Sharpe Ratio (Bailey & LdP 2014)
# ---------------------------------------------------------------------------


def psr(
    observed_sharpe: float,
    n_obs: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
    benchmark_sharpe: float = 0.0,
) -> float:
    """Probabilistic Sharpe Ratio — P(true SR > benchmark | observed SR).

    Formula from Bailey & López de Prado (2014):

        PSR(SR*) = Phi{ (SR_hat - SR*) * sqrt(n-1)
                        / sqrt(1 - gamma_1 * SR_hat + (gamma_2-1)/4 * SR_hat^2) }

    Parameters
    ----------
    observed_sharpe
        Observed Sharpe ratio of the strategy.
    n_obs
        Number of return observations.
    skewness
        Skewness of the return series.
    kurtosis
        Raw kurtosis (3 = Gaussian; pass observed value).
    benchmark_sharpe
        The null hypothesis Sharpe. Default 0.

    Returns
    -------
    float in [0, 1].
    """
    if n_obs <= 1:
        return 0.0

    sr_hat = observed_sharpe - benchmark_sharpe
    variance_num = 1.0 - skewness * sr_hat + (kurtosis - 1.0) / 4.0 * sr_hat**2
    variance_num = max(variance_num, 1e-12)
    std_sr = math.sqrt(variance_num / (n_obs - 1))
    if std_sr <= 0:
        return 1.0 if sr_hat > 0 else 0.0

    z = sr_hat / std_sr
    return float(norm.cdf(z))


# ---------------------------------------------------------------------------
# N_effective trials (PCA-95% rank on trial return matrix)
# ---------------------------------------------------------------------------


def n_effective_trials(trial_returns: np.ndarray) -> int:
    """Estimate effective number of independent trials via PCA.

    Parameters
    ----------
    trial_returns
        2-D array of shape (n_trials, n_periods). Each row = one trial's
        return sequence.  MUST be a true n_trials × T matrix (not a
        row-repeated tile — iter-v3/001's bug returned rank=1 trivially).

    Returns
    -------
    int — number of principal components needed for ≥95% cumulative variance.
    """
    m = np.asarray(trial_returns, dtype=float)
    if m.ndim != 2 or m.shape[0] < 2 or m.shape[1] < 2:
        return max(1, m.shape[0] if m.ndim == 2 else 1)

    m_centered = m - m.mean(axis=1, keepdims=True)
    cov = np.cov(m_centered)
    eigenvalues = np.linalg.eigvalsh(cov)
    eigenvalues = np.sort(eigenvalues)[::-1]
    eigenvalues = np.clip(eigenvalues, 0, None)

    total_var = float(eigenvalues.sum())
    if total_var == 0:
        return 1

    cumvar = np.cumsum(eigenvalues) / total_var
    n_eff = int(np.searchsorted(cumvar, 0.95)) + 1
    return min(n_eff, len(eigenvalues))


# ---------------------------------------------------------------------------
# Convenience iterator for walk-forward CPCV (called by runner)
# ---------------------------------------------------------------------------


def cpcv_walk_forward_splits(
    n_samples: int,
    n_splits: int = 10,
    n_test_splits: int = 2,
    gap: int = REQUIRED_GAP,
    embargo: int = 27,
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Yield (train_idx, test_idx) tuples for CPCV walk-forward.

    Default gap = REQUIRED_GAP = (timeout_candles+1)*n_symbols = 66
    (3-symbol BCH+LDO+TRX universe since iter-v3/013).
    Default embargo = ~1% of 24-month T ≈ 27 candles.
    Asserts gap == REQUIRED_GAP to catch silent rescaling.
    """
    splits = combinatorial_purged_cv(
        n_samples=n_samples,
        n_splits=n_splits,
        n_test_splits=n_test_splits,
        gap=gap,
        embargo=embargo,
        expected_gap=REQUIRED_GAP,
    )
    yield from iter(splits)


__all__ = [
    "REQUIRED_GAP",
    "PBOResult",
    "combinatorial_purged_cv",
    "cpcv_paths_from_splits",
    "cpcv_walk_forward_splits",
    "deflated_sharpe_ratio_v3",
    "n_effective_trials",
    "pbo_from_cpcv",
    "psr",
]
