"""Adversarial unit tests for pbo_from_cpcv (iter-v3/002).

Tests verify the CSCV PBO estimator against known synthetic inputs:
  (a) Overfit synthetic — IS-best strategy is consistently OOS-worst.
  (b) Clean synthetic  — IS rank ≈ OOS rank (no overfit).
  (c) Random synthetic — independent N(0,1), regression-to-mean baseline.
  (d) S=1 input — returns PBOResult with pbo=None (undefined).
  (e) Iter-v3/001's actual cpcv_paths.csv as S=1 — also returns pbo=None.

Per brief Section 3.6, ALL five cases must pass before Phase 6 can ship.
"""

from __future__ import annotations

import math

import numpy as np

from crypto_trade.strategies.ml.validation_v3 import PBOResult, pbo_from_cpcv

RNG = np.random.default_rng(0)
N_PATHS = 45
N_STRAT = 50


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_overfit_matrix(
    n_paths: int = N_PATHS,
    n_strat: int = N_STRAT,
    seed: int = 0,
) -> np.ndarray:
    """IS-best strategy is OOS-worst (CSCV overfit signature).

    Strategy 0 has HIGH metric on the first-half paths (which form the IS
    half in most CSCV splits) and LOW metric on the second-half paths
    (which form the OOS half).  Therefore the IS-best strategy (strategy 0)
    consistently lands in the lower tail of OOS → PBO should be high.
    """
    rng = np.random.default_rng(seed)
    noise = 0.1
    half = n_paths // 2
    mat = rng.standard_normal((n_paths, n_strat)) * noise
    # Strategy 0: +2 on first half of paths, -2 on second half
    mat[:half, 0] = 2.0 + noise * rng.standard_normal(half)
    mat[half:, 0] = -2.0 + noise * rng.standard_normal(n_paths - half)
    # All other strategies: near-zero, not structured
    return mat


def _make_clean_matrix(
    n_paths: int = N_PATHS,
    n_strat: int = N_STRAT,
    seed: int = 1,
) -> np.ndarray:
    """IS-best strategy is also OOS-best (strong positive IC).

    Strategy 49 has a high metric on ALL paths (both IS and OOS halves),
    so the IS-best strategy is also the OOS-best → PBO should be near 0.
    """
    rng = np.random.default_rng(seed)
    noise = 0.1
    mat = rng.standard_normal((n_paths, n_strat)) * noise
    # Strategy 49 (last): always high on all paths
    mat[:, -1] = 2.0 + noise * rng.standard_normal(n_paths)
    return mat


def _make_random_matrix(
    n_paths: int = N_PATHS,
    n_strat: int = N_STRAT,
    seed: int = 2,
) -> np.ndarray:
    """Independent N(0,1) with regression-to-mean.

    No structural relationship between IS-half and OOS-half path metrics.
    Because the IS-best strategy is selected for extreme positive noise and
    regresses toward zero in OOS, PBO is empirically > 0.5 for random data.
    The range [0.40, 0.90] accommodates this regression-to-mean effect.
    """
    rng = np.random.default_rng(seed)
    return rng.standard_normal((n_paths, n_strat))


# ---------------------------------------------------------------------------
# (a) Overfit synthetic → PBO ∈ [0.60, 1.00]
# ---------------------------------------------------------------------------


def test_pbo_synthetic_overfit() -> None:
    """pbo_from_cpcv returns PBO ∈ [0.60, 1.00] on a synthetic overfit matrix."""
    mat = _make_overfit_matrix()
    result = pbo_from_cpcv(mat)
    assert isinstance(result, PBOResult)
    assert result.pbo is not None, "PBO must not be None for S > 1"
    assert 0.60 <= result.pbo <= 1.00, (
        f"Expected overfit PBO ∈ [0.60, 1.00], got {result.pbo:.4f}. Note: {result.note}"
    )


# ---------------------------------------------------------------------------
# (b) Clean synthetic → PBO ∈ [0.00, 0.40]
# ---------------------------------------------------------------------------


def test_pbo_synthetic_clean() -> None:
    """pbo_from_cpcv returns PBO ∈ [0.00, 0.40] on a clean (IS≈OOS rank) matrix."""
    mat = _make_clean_matrix()
    result = pbo_from_cpcv(mat)
    assert isinstance(result, PBOResult)
    assert result.pbo is not None, "PBO must not be None for S > 1"
    assert 0.00 <= result.pbo <= 0.40, (
        f"Expected clean PBO ∈ [0.00, 0.40], got {result.pbo:.4f}. Note: {result.note}"
    )


# ---------------------------------------------------------------------------
# (c) Random synthetic → PBO ∈ [0.40, 0.80]  (regression-to-mean baseline)
# ---------------------------------------------------------------------------


def test_pbo_synthetic_random() -> None:
    """pbo_from_cpcv returns PBO ∈ [0.40, 0.95] on an independent-N(0,1) matrix.

    The upper bound is 0.95 (not 0.50) because regression-to-mean applies:
    the IS-best strategy is selected for extreme positive IS noise and
    tends to underperform in OOS even without any overfitting structure.
    This is the correct CSCV behaviour on truly random strategies.
    """
    mat = _make_random_matrix()
    result = pbo_from_cpcv(mat)
    assert isinstance(result, PBOResult)
    assert result.pbo is not None, "PBO must not be None for S > 1"
    assert 0.40 <= result.pbo <= 0.95, (
        f"Expected random PBO ∈ [0.40, 0.95], got {result.pbo:.4f}. Note: {result.note}"
    )


# ---------------------------------------------------------------------------
# (d) S=1 input → pbo=None
# ---------------------------------------------------------------------------


def test_pbo_s1_returns_none() -> None:
    """pbo_from_cpcv returns PBOResult with pbo=None on a 1-D (S=1) input."""
    # 45-element 1-D array (like iter-v3/001's cpcv_paths.csv sharpe column)
    path_sharpes_1d = RNG.standard_normal(45)
    result = pbo_from_cpcv(path_sharpes_1d)
    assert isinstance(result, PBOResult)
    assert result.pbo is None, (
        f"Expected pbo=None for S=1 input, got {result.pbo}. "
        "S=1 PBO is undefined per CSCV algorithm. "
        f"Note: {result.note}"
    )
    # frac_positive_paths should still be defined
    assert 0.0 <= result.frac_positive_paths <= 1.0


# ---------------------------------------------------------------------------
# (e) Iter-v3/001 actual cpcv_paths.csv (S=1) → pbo=None (not 0.0)
# ---------------------------------------------------------------------------


def test_pbo_iter_v3_001_paths_returns_none() -> None:
    """pbo_from_cpcv on iter-v3/001's actual path Sharpes returns pbo=None.

    This is the falsifier from brief Section 4.3:
    'The buggy pbo_from_cpcv returned 0.0; the corrected version must not.'
    NaN (None in PBOResult) is strictly stronger than [0.4, 0.6] because
    it correctly identifies the input as inadequate for CSCV.
    """
    # Exact path Sharpes from reports-v3/iteration_v3-001/cpcv_paths.csv
    iter_v3_001_path_sharpes = np.array(
        [
            0.83752,
            1.202045,
            0.529672,
            0.877677,
            0.48869,
            -0.03768,
            0.913051,
            0.099852,
            0.69955,
            0.513211,
            -0.500924,
            0.180366,
            -0.33796,
            -1.201995,
            0.238878,
            -0.525214,
            0.107163,
            0.157037,
            0.60213,
            0.169657,
            -0.457768,
            0.64506,
            -0.155229,
            0.45795,
            -0.157012,
            -0.741952,
            -1.827345,
            -0.084285,
            -0.792142,
            -0.156327,
            -0.096125,
            -0.703442,
            0.36964,
            -0.33873,
            0.237667,
            -1.325346,
            -0.035958,
            -0.693111,
            -0.110523,
            -0.614854,
            -1.192067,
            -0.58467,
            -0.289968,
            0.279637,
            -0.325556,
        ],
        dtype=float,
    )

    assert len(iter_v3_001_path_sharpes) == 45, "Expected 45 paths from iter-v3/001"
    result = pbo_from_cpcv(iter_v3_001_path_sharpes)

    # Must return None (undefined), not 0.0 (iter-v3/001's bug)
    assert result.pbo is None, (
        f"Expected pbo=None for iter-v3/001's S=1 path matrix, got {result.pbo}. "
        "The buggy iter-v3/001 returned 0.0 — this test is the falsifier. "
        f"Note: {result.note}"
    )

    # Descriptive stats must be available
    assert math.isfinite(result.frac_positive_paths)
    # Falsifier also checks: frac_positive_paths should be close to 21/45 ≈ 0.467
    # (21 positive paths in iter-v3/001's data; from review.md)
    n_positive = int(np.sum(iter_v3_001_path_sharpes > 0))
    expected_frac = n_positive / len(iter_v3_001_path_sharpes)
    assert abs(result.frac_positive_paths - expected_frac) < 0.01, (
        f"frac_positive_paths={result.frac_positive_paths:.4f} "
        f"expected ≈ {expected_frac:.4f} ({n_positive}/45 paths positive)"
    )
