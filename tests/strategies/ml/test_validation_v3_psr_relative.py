"""iter-v3/055 — adversarial tests for PSR with non-zero benchmark (DSR_relative).

Reference: Bailey & Lopez de Prado (2014) JPM "Deflated Sharpe Ratio" + AFML Ch. 14.
Gate: DSR_relative = PSR(observed_SR; benchmark = CPCV_path_Sharpe_Q75) > 0.95.
"""

import math

import numpy as np
from scipy.stats import norm

from crypto_trade.strategies.ml.validation_v3 import psr


def test_psr_benchmark_zero_matches_existing_psr():
    """PSR(benchmark=0) must equal existing v3-psr computation byte-for-byte.

    With benchmark_sharpe=0, the formula simplifies to the standard PSR
    as defined in validation_v3.py lines 486-528.
    """
    sr_obs = 1.0
    n_obs = 100
    p0 = psr(
        observed_sharpe=sr_obs,
        n_obs=n_obs,
        skewness=0.0,
        kurtosis=3.0,
        benchmark_sharpe=0.0,
    )
    # Expected: sr_hat=1.0, variance_num=1-(0*1)+(3-1)/4*1^2=1.5, std=sqrt(1.5/99)
    variance_num = 1.0 - 0.0 * 1.0 + (3.0 - 1.0) / 4.0 * 1.0**2
    expected_std = math.sqrt(variance_num / (n_obs - 1))
    expected_z = 1.0 / expected_std
    expected_p = float(norm.cdf(expected_z))
    assert abs(p0 - expected_p) < 1e-9, f"PSR(0)={p0} != expected {expected_p}"


def test_psr_higher_benchmark_lowers_pvalue():
    """Strict monotonicity: higher benchmark must produce strictly lower PSR.

    PSR(SR_obs; benchmark=B) is strictly decreasing in B because sr_hat = SR_obs - B
    decreases monotonically with B (all else equal).
    """
    sr_obs = 1.0
    n_obs = 100
    p_0 = psr(sr_obs, n_obs, 0.0, 3.0, benchmark_sharpe=0.0)
    p_0_5 = psr(sr_obs, n_obs, 0.0, 3.0, benchmark_sharpe=0.5)
    p_1 = psr(sr_obs, n_obs, 0.0, 3.0, benchmark_sharpe=1.0)
    p_1_5 = psr(sr_obs, n_obs, 0.0, 3.0, benchmark_sharpe=1.5)
    assert p_0 > p_0_5 > p_1 > p_1_5, (
        f"Monotonicity violated: p(0)={p_0:.6f} > p(0.5)={p_0_5:.6f} "
        f"> p(1)={p_1:.6f} > p(1.5)={p_1_5:.6f}"
    )


def test_psr_benchmark_at_observed_returns_half():
    """PSR(benchmark = observed_SR) must return exactly 0.5.

    When benchmark equals the observed Sharpe, sr_hat = 0, z = 0, Phi(0) = 0.5.
    This is the boundary case: strategy is indistinguishable from the benchmark.
    """
    sr_obs = 1.0
    n_obs = 100
    p = psr(sr_obs, n_obs, 0.0, 3.0, benchmark_sharpe=1.0)
    assert abs(p - 0.5) < 1e-9, f"PSR(benchmark=observed)={p} != 0.5"


def test_psr_benchmark_negative_increases_pvalue():
    """Negative benchmark must produce higher PSR than benchmark=0.

    A negative benchmark lowers the bar — the strategy more easily exceeds it.
    PSR should be strictly higher than PSR(benchmark=0).
    """
    sr_obs = 1.0
    n_obs = 100
    p_0 = psr(sr_obs, n_obs, 0.0, 3.0, benchmark_sharpe=0.0)
    p_neg = psr(sr_obs, n_obs, 0.0, 3.0, benchmark_sharpe=-0.5)
    assert p_neg > p_0, (
        f"Negative benchmark should raise PSR; got p(-0.5)={p_neg:.6f} <= p(0)={p_0:.6f}"
    )


def test_psr_with_cpcv_q75_integration():
    """End-to-end: feed sample CPCV path Sharpes, verify Q75 extraction and PSR gate.

    Simulates /054-style CPCV path distribution (45 paths). Verifies:
    - Q75 lands in expected band [0.7, 1.0]
    - Strategy SR < Q75 produces PSR < 0.5 (correctly fails gate)
    - Strategy SR > Q75 by +0.66 produces PSR > 0.95 (correctly passes gate)
    """
    # Simulate cycle-4 CPCV path Sharpes (from cpcv_paths.csv: 45 paths).
    # Distribution calibrated so Q75 lands near +0.838 (per /028-/054 cycle-4 constant).
    # 45 paths: Q25=-0.243, Q50=+0.335, Q75=+0.838, max=+1.88.
    # 34 of 45 paths <= Q75 (floor of 75% of 45 = 33.75), so index 34 is Q75.
    cpcv_sharpes = np.concatenate(
        [
            np.array([-0.243] * 12),  # paths 1-12: below Q25
            np.array([0.335] * 11),   # paths 13-23: Q25-Q50 cluster
            np.array([0.838] * 11),   # paths 24-34: Q50-Q75 cluster (Q75 at index 34)
            np.array(  # paths 35-45: top cluster
                [1.20, 1.30, 1.40, 1.50, 1.60, 1.70, 1.75, 1.78, 1.88, 1.88, 1.88]
            ),
        ]
    )
    assert len(cpcv_sharpes) == 45, f"Expected 45 paths, got {len(cpcv_sharpes)}"
    q75 = float(np.percentile(cpcv_sharpes, 75))
    assert 0.7 <= q75 <= 1.1, f"Q75={q75} out of expected band [0.7, 1.1]"

    # Strategy with SR < Q75 → low PSR (fails DSR_relative gate)
    p_low = psr(0.7, 200, 0.0, 3.0, benchmark_sharpe=q75)
    assert p_low < 0.5, f"Low SR vs Q75 should give PSR < 0.5; got {p_low:.4f}"

    # Strategy with SR materially above Q75 → high PSR (passes DSR_relative gate)
    p_high = psr(1.5, 200, 0.0, 3.0, benchmark_sharpe=q75)
    assert p_high > 0.95, f"High SR vs Q75 should give PSR > 0.95; got {p_high:.4f}"
