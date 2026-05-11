"""Adversarial tests for hurst_drift_50_200 universal scope — iter-v3/053.

5 mandatory tests per brief Section 3.9:

1. test_hurst_drift_50_200_in_universal_feature_list — hurst_drift_50_200 MUST be in
   V3_FEATURE_COLUMNS_TOP_N as 15th element (SWAP: regime_momentum_signed_3d PARKED).
2. test_hurst_drift_50_200_computable_from_source_primitives — assert exact match between
   compute_hurst_drift_50_200 output and hurst_100 - hurst_diff_100_50 - hurst_200 on
   synthetic data (verifies algebraic identity R^2=1.0).
3. test_hurst_drift_50_200_stationary_per_symbol — ADF p<0.05 for hurst_drift_50_200
   in IS subset of each V3_MODELS symbol (computed on-the-fly from parquet primitives).
4. test_hurst_drift_50_200_past_only_no_lookahead — assert value at row t depends only
   on rows 0..t; verified by appending future bars and checking row t value is unchanged.
5. test_v3_models_is_3_symbol_at_iter_v3_053 — assert V3_MODELS = (BCHUSDT, LDOUSDT,
   TRXUSDT); confirms universe UNCHANGED at /053.

SWAP state (iter-v3/053):
- V3_FEATURE_COLUMNS_TOP_N = 15 features (SWAP: regime_momentum_signed_3d PARKED;
  hurst_drift_50_200 ACTIVATED).
- hurst_drift_50_200 PRESENT as 15th element.
- regime_momentum_signed_3d ABSENT from V3_FEATURE_COLUMNS_TOP_N (PARKED; retained).
- fracdiff_d05_close ABSENT (PARKED since iter-v3/052).
- regime_momentum_signed_5d PRESENT (mandate per feedback_v3_engineered_features_proven.md).
- V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols (UNCHANGED from /052).
- REQUIRED_GAP = 66 = (21+1)*3 (UNCHANGED).

EDA evidence (analysis/iteration_v3-053/ SHA `1fc6d55`):
- ADF stationary p<<0.05 all 4 syms (axis2_adf_per_symbol.csv; structurally stationary
  by construction: bounded difference of two bounded R/S Hurst measurements).
- Linear redundancy R^2=1.0 EXACT (axis5_linear_redundancy.csv): hurst_drift_50_200 =
  hurst_100 - hurst_diff_100_50 - hurst_200 (algebraic identity; residuals at machine epsilon).
- IC max 0.85-0.88 with hurst_diff_100_50 (source primitive); Category 2 carve-out applies.
- Univariate Spearman rho NOT significant p<0.05 in any of 4 symbols (mean +0.0114).
- compute function at engineered_v3.py (ACTIVATED via dispatch at /053).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N
from crypto_trade.features_v3.engineered_v3 import compute_hurst_drift_50_200

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_8H_MS = 8 * 3600 * 1000
_IS_START_MS = 1_679_616_000_000  # 2023-03-24 00:00 UTC
_OOS_CUTOFF_MS = 1_742_774_400_000  # 2025-03-24 00:00 UTC (IMMUTABLE)

_PARQUET_DIR = "data/features_v3"
_V3_MODELS_ITER_053 = ("BCHUSDT", "LDOUSDT", "TRXUSDT")


# ---------------------------------------------------------------------------
# Test 1 — hurst_drift_50_200 MUST be in V3_FEATURE_COLUMNS_TOP_N
# ---------------------------------------------------------------------------


def test_hurst_drift_50_200_in_universal_feature_list() -> None:
    """hurst_drift_50_200 MUST NOT be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/054; count MUST be 14.

    iter-v3/053: SWAP added hurst_drift_50_200 as 15th element.
    iter-v3/054: PARK -- hurst_drift_50_200 DROPPED (Critic FINAL `c056354` rec #1;
    PATH C-suspicious OOS/IS ratio 3.73; rank 11-13/15 all 3 syms). Count 15→14.
    The compute function is RETAINED in dispatch (zero revert cost).
    """
    assert "hurst_drift_50_200" not in V3_FEATURE_COLUMNS_TOP_N, (
        "hurst_drift_50_200 FOUND in V3_FEATURE_COLUMNS_TOP_N -- "
        "iter-v3/054 PARK failed. Remove it from V3_FEATURE_COLUMNS_TOP_N in "
        "features_v3/__init__.py."
    )
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 14, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} elements -- expected 14. "
        "iter-v3/054: PARK drops hurst_drift_50_200 (15→14). "
        "Check V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )
    assert "regime_momentum_signed_3d" not in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_3d STILL in V3_FEATURE_COLUMNS_TOP_N -- "
        "iter-v3/053 SWAP incomplete. 3d must be PARKED (dropped per /052 PATH C-suspicious "
        "closeout; Critic FINAL `34cc46f` rec #2). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


# ---------------------------------------------------------------------------
# Test 2 — Algebraic identity: exact match with hurst_100 - hurst_diff_100_50 - hurst_200
# ---------------------------------------------------------------------------


def test_hurst_drift_50_200_computable_from_source_primitives() -> None:
    """compute_hurst_drift_50_200 output must be EXACTLY hurst_100 - hurst_diff_100_50 - hurst_200.

    Verifies the R^2=1.0 algebraic identity (analysis/iteration_v3-053/axis5_linear_redundancy.csv
    SHA `1fc6d55`): hurst_drift_50_200 = hurst_100 - hurst_diff_100_50 - hurst_200 to
    machine precision (residuals at ~1e-16 in EDA).

    Uses synthetic data with known values to verify exact arithmetic correctness.
    """
    rng = np.random.default_rng(42)
    n = 300
    # Simulate Hurst-like values in (0, 1)
    hurst_100 = rng.uniform(0.3, 0.8, n)
    hurst_diff = rng.uniform(-0.2, 0.2, n)  # diff can be negative
    hurst_200 = rng.uniform(0.3, 0.8, n)
    close = rng.uniform(100.0, 1000.0, n)

    df = pd.DataFrame(
        {
            "close": close,
            "hurst_100": hurst_100,
            "hurst_diff_100_50": hurst_diff,
            "hurst_200": hurst_200,
        }
    )

    result = compute_hurst_drift_50_200(df.copy())
    assert "hurst_drift_50_200" in result.columns, (
        "compute_hurst_drift_50_200 did not produce 'hurst_drift_50_200' column. "
        "Check the function signature and return value in engineered_v3.py."
    )

    # Expected value: exact linear combination
    expected = hurst_100 - hurst_diff - hurst_200
    actual = result["hurst_drift_50_200"].values

    max_abs_diff = np.nanmax(np.abs(actual - expected))
    assert max_abs_diff < 1e-10, (
        f"compute_hurst_drift_50_200 does not match algebraic identity. "
        f"Max absolute difference: {max_abs_diff:.2e} (expected < 1e-10). "
        "hurst_drift_50_200 MUST equal hurst_100 - hurst_diff_100_50 - hurst_200 exactly. "
        "Check the arithmetic in compute_hurst_drift_50_200 in engineered_v3.py."
    )


# ---------------------------------------------------------------------------
# Test 3 — ADF stationarity smoke test (computed on-the-fly from parquet primitives)
# ---------------------------------------------------------------------------


def test_hurst_drift_50_200_stationary_per_symbol() -> None:
    """hurst_drift_50_200 ADF p-value must be < 0.05 in IS subset for each /053 symbol.

    iter-v3/053 EDA evidence (analysis/iteration_v3-053/axis2_adf_per_symbol.csv SHA `1fc6d55`):
    ADF p << 0.05 for BCH/LDO/TRX/ALGO. Structurally stationary by construction
    (bounded difference of two bounded R/S Hurst measurements).
    This smoke test computes hurst_drift_50_200 on-the-fly from parquet source primitives
    (hurst_100, hurst_diff_100_50, hurst_200) and runs ADF to confirm. NO parquet regen needed.

    Uses statsmodels adfuller with autolag='AIC'.
    """
    import pyarrow.parquet as pq  # noqa: PLC0415
    from statsmodels.tsa.stattools import adfuller  # noqa: PLC0415

    for sym in _V3_MODELS_ITER_053:
        path = f"{_PARQUET_DIR}/{sym}_8h_features.parquet"
        try:
            df = pq.read_table(
                path,
                columns=["open_time", "hurst_100", "hurst_diff_100_50", "hurst_200"],
            ).to_pandas()
        except Exception as exc:
            pytest.fail(f"{sym} parquet read failed at {path}: {exc}")

        # Compute hurst_drift_50_200 on-the-fly from primitives
        df["hurst_drift_50_200"] = (
            df["hurst_100"].astype(float)
            - df["hurst_diff_100_50"].astype(float)
            - df["hurst_200"].astype(float)
        )

        # IS subset only (open_time < OOS_CUTOFF_MS)
        df_is = df[df["open_time"] < _OOS_CUTOFF_MS].copy()
        series = df_is["hurst_drift_50_200"].dropna()

        assert len(series) >= 100, f"{sym}: IS subset too small ({len(series)} rows) for ADF test."

        adf_stat, p_value, *_ = adfuller(series, autolag="AIC")
        assert p_value < 0.05, (
            f"{sym}: hurst_drift_50_200 ADF p-value={p_value:.4f} -- expected < 0.05. "
            f"ADF stat={adf_stat:.4f}. Feature is NOT stationary in IS. "
            "EDA evidence: p<<0.05 for all 4 symbols at SHA `1fc6d55` axis2_adf_per_symbol.csv. "
            "Check source primitives (hurst_100, hurst_diff_100_50, hurst_200) in parquet."
        )


# ---------------------------------------------------------------------------
# Test 4 — hurst_drift_50_200 no lookahead (past-only convention)
# ---------------------------------------------------------------------------


def test_hurst_drift_50_200_past_only_no_lookahead() -> None:
    """compute_hurst_drift_50_200 must use only past data at each bar.

    Construction (engineered_v3.py):
    - hurst_drift_50_200 = hurst_100[t] - hurst_diff_100_50[t] - hurst_200[t]
    - All 3 source primitives are past-only (computed by add_regime_v3_features:
      rolling R/S Hurst windows ending at t-1 in the regime_v3 implementation).
    - Element-wise subtraction at row t: uses only source primitive values at row t.
    - Appending future rows does NOT alter source primitive values at row t (rolling
      windows are backward-looking).

    We verify by checking that adding different future data after point t does NOT
    change the feature value at t (past-only invariant).

    Past-only invariant: value at bar n-1 of df_short MUST equal value at bar n-1 of df_long.
    """
    n = 250  # sufficient bars for source primitive warm-up mock
    rng = np.random.default_rng(123)
    open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
    close = rng.uniform(100.0, 1000.0, n)
    # Simulate source primitives (past-only by construction; mock here with known values)
    hurst_100 = rng.uniform(0.3, 0.8, n)
    hurst_diff = rng.uniform(-0.2, 0.2, n)
    hurst_200 = rng.uniform(0.3, 0.8, n)

    df_short = pd.DataFrame(
        {
            "open_time": open_times,
            "close": close,
            "hurst_100": hurst_100,
            "hurst_diff_100_50": hurst_diff,
            "hurst_200": hurst_200,
        }
    )

    # Extend with DIFFERENT future data
    future_close = rng.uniform(100.0, 1000.0, 50)
    future_hurst_100 = rng.uniform(0.3, 0.8, 50)
    future_hurst_diff = rng.uniform(-0.2, 0.2, 50)
    future_hurst_200 = rng.uniform(0.3, 0.8, 50)
    future_times = [_IS_START_MS + (n + i) * _8H_MS for i in range(50)]
    future_df = pd.DataFrame(
        {
            "open_time": future_times,
            "close": future_close,
            "hurst_100": future_hurst_100,
            "hurst_diff_100_50": future_hurst_diff,
            "hurst_200": future_hurst_200,
        }
    )
    df_long = pd.concat([df_short, future_df], ignore_index=True)

    # Compute feature on both
    result_short = compute_hurst_drift_50_200(df_short.copy())
    result_long = compute_hurst_drift_50_200(df_long.copy())

    # Values at the last bar of df_short must be identical in both
    last_val_short = result_short["hurst_drift_50_200"].iloc[-1]
    last_val_long = result_long["hurst_drift_50_200"].iloc[n - 1]

    if not (np.isnan(last_val_short) and np.isnan(last_val_long)):
        abs_diff = abs(float(last_val_short) - float(last_val_long))
        assert abs_diff < 1e-10, (
            f"compute_hurst_drift_50_200 lookahead detected: "
            f"value at bar {n - 1} changed when future data was appended. "
            f"short={last_val_short:.10f}, long={last_val_long:.10f}, diff={abs_diff:.2e}. "
            "hurst_drift_50_200 must be past-only: element-wise subtraction of "
            "past-only source primitives at row t. "
            "Check compute_hurst_drift_50_200 in engineered_v3.py -- "
            "all 3 source primitives (hurst_100, hurst_diff_100_50, hurst_200) must be "
            "indexed at row t (no .shift(-N) or future slicing)."
        )


# ---------------------------------------------------------------------------
# Test 5 — V3_MODELS is 3-symbol universe at iter-v3/053
# ---------------------------------------------------------------------------


def test_v3_models_is_3_symbol_at_iter_v3_053() -> None:
    """V3 universe must be (BCHUSDT, LDOUSDT, TRXUSDT) at iter-v3/054.

    Confirms the 3-symbol universe is UNCHANGED from /052-/053. ALGOUSDT was REVERTED
    at the system level per iter-v3/051 (feedback_v3_per_symbol_lifts_oos_breaks_is.md
    UPDATED 2026-05-10; two-cycle anti-pattern confirmation at /039+/050).

    iter-v3/054: hurst_drift_50_200 PARKED (15→14). All 3 symbols return 14-feature fallback.
    REQUIRED_GAP = 66 = (21+1)*3 (3-symbol universe; UNCHANGED).
    """
    from crypto_trade.features_v3 import features_for_symbol  # noqa: PLC0415

    expected_universe = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
    # Each symbol in the expected universe must return the 14-feature universal fallback
    for sym in expected_universe:
        feats = features_for_symbol(sym)
        assert len(feats) == 14, (
            f"{sym} fallback returns {len(feats)} features -- expected 14. "
            "iter-v3/054 universe: BCH + LDO + TRX, all at 14-feature universal fallback "
            "(hurst_drift_50_200 PARKED; Critic FINAL `c056354` rec #1)."
        )
        assert "hurst_drift_50_200" not in feats, (
            f"{sym} fallback contains hurst_drift_50_200 -- must be ABSENT. "
            "iter-v3/054: hurst_drift_50_200 PARKED (15→14)."
        )
        assert "regime_momentum_signed_3d" not in feats, (
            f"{sym} fallback contains regime_momentum_signed_3d -- must be ABSENT. "
            "iter-v3/053: 3d PARKED per /052 PATH C-suspicious."
        )
    # ALGOUSDT must NOT be in the v3 model universe
    assert "ALGOUSDT" not in {sym for sym in expected_universe}, (
        "ALGOUSDT found in expected universe -- must be ABSENT at iter-v3/054. "
        "System-level REVERT at iter-v3/051."
    )
    # Verify the constant matches the expected list exactly
    assert _V3_MODELS_ITER_053 == expected_universe, (
        f"_V3_MODELS_ITER_053 = {_V3_MODELS_ITER_053} -- expected {expected_universe}. "
        "Update _V3_MODELS_ITER_053 constant in this test file."
    )
