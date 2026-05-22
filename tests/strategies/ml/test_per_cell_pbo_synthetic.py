"""Adversarial unit tests for the per-cell PBO consumer pipeline (iter-v3/004).

Tests verify that per-cell CSCV aggregation via cross-cell mean preserves
strategy-distinguishing signal — i.e., the aggregated PBO correctly separates
overfit cells from clean cells.

Brief Section 3.5 sub-fix #3 specification:
  (a) 10 synthetic overfit cells: trial 0 IS-favorable / OOS-unfavorable.
      Assert: per-cell PBOs near 1.0, aggregated mean PBO near 1.0.
  (b) 10 synthetic clean cells: all 50 trials IID-Gaussian.
      Assert: per-cell PBOs cluster near 0.5 or lower (small-N CSCV effect),
      aggregated mean PBO < 0.5.
  (c) Mix of 5 overfit + 5 clean.
      Assert: aggregated mean PBO is between overfit-only and clean-only means.

Per brief Section 2.4 empirical finding: clean cells cluster near PBO=0.0 (not
0.5) because the IS-best strategy tends to also be the OOS-best in small-N
CSCV when no overfit structure is present. The falsifier therefore targets
strict pairwise separation (min(overfit) > max(clean)) rather than absolute
thresholds.
"""

from __future__ import annotations

import numpy as np

from crypto_trade.strategies.ml.validation_v3 import (
    combinatorial_purged_cv,
    pbo_from_cpcv,
)

# ---------------------------------------------------------------------------
# CSCV configuration — per brief Section 0, within-cell gap = 22
# ---------------------------------------------------------------------------

PER_CELL_N_SPLITS = 10
PER_CELL_K = 2  # C(10, 2) = 45 paths
PER_CELL_GAP = 22  # (timeout_candles + 1) = (21 + 1) = 22 within a single-symbol cell
N_CANDLES_PER_CELL = 400  # enough for 10 splits of ~40 candles each
N_TRIALS = 50


# ---------------------------------------------------------------------------
# Synthetic cell builder helpers
# ---------------------------------------------------------------------------


def _make_overfit_cell_returns(seed: int) -> np.ndarray:
    """Construct a (n_candles, n_trials) returns matrix for one overfit cell.

    Trial 0 is explicitly IS-favorable / OOS-unfavorable:
    - First half of candles: strong positive returns for trial 0
    - Second half of candles: strong negative returns for trial 0
    All other 49 trials are IID Gaussian noise (no edge).

    When CSCV splits the candle timeline into 10 groups and selects 2 as
    test (OOS), trial 0 tends to be IS-best (selected from the first-half
    candles) but OOS-worst (evaluated on the second-half candles). This
    produces PBO ≈ 1.0 for this cell.
    """
    rng = np.random.default_rng(seed)
    n_candles = N_CANDLES_PER_CELL

    # All trials start as noise
    returns_mat = rng.standard_normal((n_candles, N_TRIALS)) * 0.05

    # Trial 0: +1.0 on first half, -1.0 on second half (strong overfit signal)
    half = n_candles // 2
    returns_mat[:half, 0] = 1.0 + 0.05 * rng.standard_normal(half)
    returns_mat[half:, 0] = -1.0 + 0.05 * rng.standard_normal(n_candles - half)

    return returns_mat


def _make_clean_cell_returns(seed: int) -> np.ndarray:
    """Construct a (n_candles, n_trials) returns matrix for one clean cell.

    All 50 trials are IID Gaussian with no structured edge.
    No trial has a consistent IS-vs-OOS pattern. CSCV PBO should be low
    (near 0.0) because the IS-best trial also tends to be OOS-best (no
    overfit structure to reverse the ordering).
    """
    rng = np.random.default_rng(seed)
    return rng.standard_normal((N_CANDLES_PER_CELL, N_TRIALS)) * 0.05


def _compute_cell_pbo(returns_mat: np.ndarray) -> float:
    """Compute per-cell PBO from a (n_candles, n_trials) returns matrix.

    Replicates the analysis/iteration_v3-004/per_cell_pbo_demo.py logic:
    1. Run CSCV with per-cell gap=22 to get 45 paths.
    2. For each path, compute per-trial Sharpe on the test candles.
    3. Build (n_paths, n_trials) path-Sharpe matrix.
    4. Call pbo_from_cpcv on the path matrix.

    Returns per-cell PBO (float in [0, 1]) or NaN if CSCV fails.
    """
    n_candles, n_trials = returns_mat.shape

    splits = combinatorial_purged_cv(
        n_samples=n_candles,
        n_splits=PER_CELL_N_SPLITS,
        n_test_splits=PER_CELL_K,
        gap=PER_CELL_GAP,
        embargo=0,
    )
    n_paths = len(splits)

    path_mat = np.full((n_paths, n_trials), np.nan, dtype=float)
    for path_id, (_, test_idx) in enumerate(splits):
        if len(test_idx) < 2:
            continue
        test_returns = returns_mat[test_idx, :]  # (n_test_candles, n_trials)
        mu = np.nanmean(test_returns, axis=0)
        sigma = np.nanstd(test_returns, axis=0, ddof=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            sharpe = np.where(sigma > 0, mu / sigma, 0.0)
        path_mat[path_id, :] = sharpe

    result = pbo_from_cpcv(path_mat, max_splits=5000)
    return result.pbo if result.pbo is not None else float("nan")


# ---------------------------------------------------------------------------
# (a) Overfit cells: min(per-cell PBO) should be high; mean ≈ 1.0
# ---------------------------------------------------------------------------


def test_overfit_cells_high_pbo() -> None:
    """Per-cell PBOs for 10 overfit cells should all be near 1.0.

    Overfit cells have trial 0 IS-favorable / OOS-unfavorable by construction.
    The CSCV estimator must detect this: IS-best (trial 0) should fall in the
    lower OOS half for most IS/OOS splits, yielding PBO ≈ 1.0 per cell.

    Assertion (brief Section 3.5 sub-fix #3):
    - All 10 overfit cell PBOs > 0.7 (strong overfit signal)
    - Mean PBO across 10 overfit cells > 0.7
    """
    overfit_pbos = []
    for i in range(10):
        returns_mat = _make_overfit_cell_returns(seed=100 + i)
        pbo = _compute_cell_pbo(returns_mat)
        overfit_pbos.append(pbo)

    mean_overfit_pbo = float(np.nanmean(overfit_pbos))

    assert all(p > 0.7 for p in overfit_pbos), (
        f"Expected all overfit cell PBOs > 0.7. Got: {[f'{p:.3f}' for p in overfit_pbos]}"
    )
    assert mean_overfit_pbo > 0.7, f"Expected mean overfit PBO > 0.7. Got: {mean_overfit_pbo:.4f}"


# ---------------------------------------------------------------------------
# (b) Clean cells: all per-cell PBOs should be < 0.5; mean < 0.5
# ---------------------------------------------------------------------------


def test_clean_cells_low_pbo() -> None:
    """Per-cell PBOs for 10 IID-Gaussian clean cells: mean < 0.5 and majority < 0.5.

    Clean cells have no structured IS-vs-OOS reversal. The IS-best trial
    should not consistently fall in the lower OOS half, so PBOs tend to be
    low (near 0.0).

    Per brief Section 2.4 empirical note: clean cell PBOs cluster near 0.0
    (not 0.5) because CSCV at N=45 paths with small-noise returns tends to
    preserve rank ordering (IS-best stays OOS-best in clean data). However,
    some cells may produce PBO > 0.5 by pure random chance (CSCV variance
    on small N). The correct assertion is therefore:
    - Mean PBO < 0.5 (aggregate signal is low)
    - At least 7/10 cells have PBO < 0.5 (majority signal is low)

    The primary consumer-preserves-signal assertion is in test
    test_pairwise_separation_overfit_vs_clean (strict pairwise separation).
    """
    clean_pbos = []
    for i in range(10):
        returns_mat = _make_clean_cell_returns(seed=200 + i)
        pbo = _compute_cell_pbo(returns_mat)
        clean_pbos.append(pbo)

    mean_clean_pbo = float(np.nanmean(clean_pbos))
    n_below_half = sum(1 for p in clean_pbos if p < 0.5)

    assert mean_clean_pbo < 0.5, (
        f"Expected mean clean PBO < 0.5. Got: {mean_clean_pbo:.4f}. "
        f"Per-cell PBOs: {[f'{p:.3f}' for p in clean_pbos]}"
    )
    assert n_below_half >= 7, (
        f"Expected ≥7/10 clean cells to have PBO < 0.5. Got {n_below_half}/10. "
        f"Per-cell PBOs: {[f'{p:.3f}' for p in clean_pbos]}"
    )


# ---------------------------------------------------------------------------
# (c) Pairwise separation: min(overfit) > max(clean)
# ---------------------------------------------------------------------------


def test_pairwise_separation_overfit_vs_clean() -> None:
    """Per-cell PBO consumer pipeline must strictly separate overfit from clean.

    Brief Section 3.5 sub-fix #3 pre-registered criteria (from Section 2.4):
    - min(overfit_pbos) > max(clean_pbos) [strict pairwise separation]
    - Median delta (median_overfit - median_clean) > 0.5
    - Overfit median > 0.7

    This is the consumer-preserves-signal test that iter-v3/003 lacked.
    """
    overfit_pbos = []
    clean_pbos = []

    for i in range(10):
        r_ov = _make_overfit_cell_returns(seed=300 + i)
        overfit_pbos.append(_compute_cell_pbo(r_ov))

        r_cl = _make_clean_cell_returns(seed=400 + i)
        clean_pbos.append(_compute_cell_pbo(r_cl))

    min_overfit = float(np.nanmin(overfit_pbos))
    max_clean = float(np.nanmax(clean_pbos))
    median_overfit = float(np.nanmedian(overfit_pbos))
    median_clean = float(np.nanmedian(clean_pbos))
    median_delta = median_overfit - median_clean

    assert min_overfit > max_clean, (
        f"Pairwise separation failed: min(overfit)={min_overfit:.4f} "
        f"should be > max(clean)={max_clean:.4f}. "
        f"Overfit PBOs: {[f'{p:.3f}' for p in overfit_pbos]}. "
        f"Clean PBOs: {[f'{p:.3f}' for p in clean_pbos]}."
    )
    assert median_delta > 0.5, (
        f"Median delta (overfit - clean) = {median_delta:.4f} should be > 0.5. "
        f"Median overfit={median_overfit:.4f}, median clean={median_clean:.4f}."
    )
    assert median_overfit > 0.7, f"Overfit median PBO = {median_overfit:.4f} should be > 0.7."


# ---------------------------------------------------------------------------
# (d) Mixed cells: aggregated mean between overfit-only and clean-only
# ---------------------------------------------------------------------------


def test_mixed_cells_mean_pbo_between_extremes() -> None:
    """5 overfit + 5 clean cells: cross-cell mean PBO between the two extremes.

    If mean_overfit ≈ 1.0 and mean_clean ≈ 0.0, then mean_mixed ≈ 0.5.
    The test does not hardcode 0.5 but instead asserts the mixed mean is
    strictly between the individual means — confirming the aggregator is
    linear and not saturating.

    Note: this test uses different seeds than tests (a), (b), (c) to
    avoid correlation.
    """
    overfit_pbos = []
    clean_pbos = []

    for i in range(5):
        r_ov = _make_overfit_cell_returns(seed=500 + i)
        overfit_pbos.append(_compute_cell_pbo(r_ov))

        r_cl = _make_clean_cell_returns(seed=600 + i)
        clean_pbos.append(_compute_cell_pbo(r_cl))

    mixed_pbos = overfit_pbos + clean_pbos
    mean_overfit = float(np.nanmean(overfit_pbos))
    mean_clean = float(np.nanmean(clean_pbos))
    mean_mixed = float(np.nanmean(mixed_pbos))

    assert mean_clean < mean_mixed < mean_overfit, (
        f"Mixed mean should be between clean and overfit means. "
        f"mean_clean={mean_clean:.4f}, mean_mixed={mean_mixed:.4f}, "
        f"mean_overfit={mean_overfit:.4f}."
    )
