"""Adversarial tests for regime_momentum_signed_3d universal scope — iter-v3/052.

5 mandatory tests per brief Section 3.2:

1. test_regime_momentum_signed_3d_in_universal_feature_list — regime_momentum_signed_3d
   MUST be in V3_FEATURE_COLUMNS_TOP_N; verify it is present and total count == 15.
   (SWAP: fracdiff_d05_close PARKED; regime_momentum_signed_3d ACTIVATED as 15th element.)
2. test_regime_momentum_signed_3d_present_in_all_4_symbol_parquets — all 4 symbol parquets
   (BCH/LDO/TRX/ALGO; ALGO reserved-for-future) must have regime_momentum_signed_3d column
   after feature regen.
3. test_regime_momentum_signed_3d_stationary_per_symbol — ADF p<0.05 for
   regime_momentum_signed_3d in IS subset of each /052 symbol's parquet (smoke test).
4. test_regime_momentum_signed_3d_no_lookahead — verify compute_regime_momentum_signed_3d
   uses past-only data (ret_3d = close.shift(1)/close.shift(4)-1.0 + hurst.shift(1)).
5. test_v3_feature_columns_top_n_swap_fracdiff_to_3d_at_iter_v3_052 — comprehensive SWAP
   state: regime_momentum_signed_3d PRESENT; fracdiff_d05_close ABSENT; count == 15;
   regime_momentum_signed_5d PRESENT (mandate).

SWAP state (iter-v3/052):
- V3_FEATURE_COLUMNS_TOP_N = 15 features (SWAP: fracdiff PARKED; 3d ACTIVATED).
- regime_momentum_signed_3d PRESENT as 15th element.
- fracdiff_d05_close ABSENT from V3_FEATURE_COLUMNS_TOP_N (PARKED; column still in parquets).
- regime_momentum_signed_5d PRESENT (mandate per feedback_v3_engineered_features_proven.md).
- V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols (UNCHANGED from /051).
- REQUIRED_GAP = 66 = (21+1)*3 (UNCHANGED).

EDA evidence (analysis/iteration_v3-051/axis_c_regime_3d_*.csv SHA `290f37b`):
- ADF stationary p=0 all 4 syms (structurally stationary by construction).
- IC strict-gate PASS: max |IC| = 0.6192 < 0.70 (NO carve-out needed).
- Univariate Spearman ρ -0.044 to -0.068 significant all 4 syms (mean -0.057).
- IC with sister 5d feature 0.43-0.47 (below 0.50 stacking-risk threshold).
- compute function at engineered_v3.py:330-376 (ACTIVATED via dispatch at /052).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N
from crypto_trade.features_v3.engineered_v3 import compute_regime_momentum_signed_3d

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_8H_MS = 8 * 3600 * 1000
_IS_START_MS = 1_679_616_000_000  # 2023-03-24 00:00 UTC
_OOS_CUTOFF_MS = 1_742_774_400_000  # 2025-03-24 00:00 UTC (IMMUTABLE)

_PARQUET_DIR = "data/features_v3"
_V3_ALL_SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT", "ALGOUSDT")
_V3_MODELS_ITER_052 = ("BCHUSDT", "LDOUSDT", "TRXUSDT")


# ---------------------------------------------------------------------------
# Test 1 — regime_momentum_signed_3d MUST be in V3_FEATURE_COLUMNS_TOP_N
# ---------------------------------------------------------------------------


def test_regime_momentum_signed_3d_in_universal_feature_list() -> None:
    """regime_momentum_signed_3d MUST be in V3_FEATURE_COLUMNS_TOP_N; count MUST be 15.

    iter-v3/052: SWAP — regime_momentum_signed_3d REPLACES fracdiff_d05_close as
    15th element. QR-EDA-backed per /051 RANKED #2 (SHA `290f37b`).
    Net count stays at 15 (SWAP; fracdiff PARKED).
    """
    assert "regime_momentum_signed_3d" in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_3d NOT found in V3_FEATURE_COLUMNS_TOP_N — "
        "iter-v3/052 SWAP failed. Add it as 15th element in features_v3/__init__.py."
    )
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 15, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} elements — expected 15. "
        "iter-v3/052: SWAP keeps count at 15 (fracdiff OUT; regime_momentum_signed_3d IN). "
        "Check V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )
    assert "fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N, (
        "fracdiff_d05_close STILL in V3_FEATURE_COLUMNS_TOP_N — "
        "iter-v3/052 SWAP incomplete. fracdiff must be PARKED (dropped from model input). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


# ---------------------------------------------------------------------------
# Test 2 — regime_momentum_signed_3d present in all 4 symbol parquets
# ---------------------------------------------------------------------------


def test_regime_momentum_signed_3d_present_in_all_4_symbol_parquets() -> None:
    """All 4 symbol parquets MUST contain regime_momentum_signed_3d column.

    iter-v3/052 requires feature parquet regen (compute_regime_momentum_signed_3d was
    dead code before /052 dispatch activation; column was NOT in /051 parquets).
    ALGOUSDT included even though not in /052 V3_MODELS (reserved-for-future).
    Run: `uv run crypto-trade features --track v3 --interval 8h
         --symbols BCHUSDT,LDOUSDT,TRXUSDT,ALGOUSDT --format parquet --workers 4`
    """
    for sym in _V3_ALL_SYMBOLS:
        path = f"{_PARQUET_DIR}/{sym}_8h_features.parquet"
        try:
            schema = pq.read_schema(path)
            cols = schema.names
        except Exception as exc:
            pytest.fail(f"{sym} parquet not readable at {path}: {exc}")
        assert "regime_momentum_signed_3d" in cols, (
            f"{sym} parquet at {path} missing regime_momentum_signed_3d column. "
            "Run `uv run crypto-trade features --track v3 --interval 8h "
            "--symbols BCHUSDT,LDOUSDT,TRXUSDT,ALGOUSDT --format parquet --workers 4` "
            "to regenerate parquets with the activated dispatch."
        )


# ---------------------------------------------------------------------------
# Test 3 — regime_momentum_signed_3d ADF stationarity smoke test (IS subset)
# ---------------------------------------------------------------------------


def test_regime_momentum_signed_3d_stationary_per_symbol() -> None:
    """regime_momentum_signed_3d ADF p-value must be < 0.05 in IS subset for each /052 symbol.

    iter-v3/052 EDA evidence (analysis/iteration_v3-051/axis_c_regime_3d_adf.csv SHA `290f37b`):
    ADF p=0 for BCH/LDO/TRX/ALGO. Structurally stationary by construction
    (ret_3d is a log-return, stationary; sign(hurst-0.5) is bounded {-1,0,+1}).
    This smoke test reads the actual parquet IS subset and re-runs ADF to confirm.

    Uses statsmodels adfuller with autolag='AIC'.
    """
    from statsmodels.tsa.stattools import adfuller  # noqa: PLC0415

    for sym in _V3_MODELS_ITER_052:
        path = f"{_PARQUET_DIR}/{sym}_8h_features.parquet"
        try:
            df = pq.read_table(
                path,
                columns=["open_time", "regime_momentum_signed_3d"],
            ).to_pandas()
        except Exception as exc:
            pytest.fail(f"{sym} parquet read failed: {exc}")

        # IS subset only (open_time < OOS_CUTOFF_MS)
        df_is = df[df["open_time"] < _OOS_CUTOFF_MS].copy()
        series = df_is["regime_momentum_signed_3d"].dropna()

        assert len(series) >= 100, f"{sym}: IS subset too small ({len(series)} rows) for ADF test."

        adf_stat, p_value, *_ = adfuller(series, autolag="AIC")
        assert p_value < 0.05, (
            f"{sym}: regime_momentum_signed_3d ADF p-value={p_value:.4f} — expected < 0.05. "
            f"ADF stat={adf_stat:.4f}. Feature is NOT stationary in IS. "
            "Check compute_regime_momentum_signed_3d in engineered_v3.py. "
            "EDA evidence: p=0 for all 4 symbols at SHA `290f37b`."
        )


# ---------------------------------------------------------------------------
# Test 4 — regime_momentum_signed_3d no lookahead (past-only convention)
# ---------------------------------------------------------------------------


def test_regime_momentum_signed_3d_no_lookahead() -> None:
    """compute_regime_momentum_signed_3d must use only past data at each bar.

    Construction (engineered_v3.py:330-376):
    - ret_3d = close.shift(1) / close.shift(4) - 1.0
      Bar t uses close[t-1] / close[t-4] — strictly past-only.
    - hurst_100: rolling 100-bar R/S Hurst (past-only by construction in add_regime_v3_features).
    - regime_sign = sign(hurst_100.shift(1) - 0.5): bar t uses hurst[t-1] — past-only.

    We verify by checking that adding future data after point t does NOT change
    the feature value at t (appending future rows cannot alter past results).

    Past-only invariant: value at bar n-1 of df_short MUST equal value at bar n-1 of df_long.
    """
    # Build a minimal DataFrame with hurst_100 (required upstream dependency)
    n = 200  # needs >= 100 bars for hurst_100 warm-up
    rng = np.random.default_rng(42)
    open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
    close = rng.uniform(100.0, 1000.0, n)
    # Simulate hurst_100: values in (0, 1) bounded, no warm-up needed for mock
    hurst_100 = rng.uniform(0.3, 0.7, n)
    df_short = pd.DataFrame({"open_time": open_times, "close": close, "hurst_100": hurst_100})

    # Extend with different future data
    future_close = rng.uniform(100.0, 1000.0, 50)
    future_hurst = rng.uniform(0.3, 0.7, 50)
    future_times = [_IS_START_MS + (n + i) * _8H_MS for i in range(50)]
    future_df = pd.DataFrame(
        {"open_time": future_times, "close": future_close, "hurst_100": future_hurst}
    )
    df_long = pd.concat([df_short, future_df], ignore_index=True)

    # Compute feature on both
    result_short = compute_regime_momentum_signed_3d(df_short.copy())
    result_long = compute_regime_momentum_signed_3d(df_long.copy())

    # Values at the last bar of df_short must be identical in both
    last_common_val_short = result_short.iloc[-1]
    last_common_val_long = result_long.iloc[n - 1]

    # Allow tiny floating-point tolerance
    if not (np.isnan(last_common_val_short) and np.isnan(last_common_val_long)):
        assert abs(float(last_common_val_short) - float(last_common_val_long)) < 1e-10, (
            f"compute_regime_momentum_signed_3d lookahead detected: "
            f"value at bar {n - 1} changed when future data was appended. "
            f"short={last_common_val_short:.6f}, long={last_common_val_long:.6f}. "
            "Check past-only construction in engineered_v3.py:330-376 — "
            "close.shift(1), close.shift(4), hurst_100.shift(1) must all be strictly past."
        )


# ---------------------------------------------------------------------------
# Test 5 — Comprehensive SWAP state at iter-v3/052
# ---------------------------------------------------------------------------


def test_v3_feature_columns_top_n_swap_fracdiff_to_3d_at_iter_v3_052() -> None:
    """Comprehensive SWAP state verification at iter-v3/052.

    Checks:
    - regime_momentum_signed_3d PRESENT as 15th element (ACTIVATED via SWAP).
    - fracdiff_d05_close ABSENT from V3_FEATURE_COLUMNS_TOP_N (PARKED).
    - count == 15 (SWAP; net count unchanged).
    - regime_momentum_signed_5d PRESENT (mandate per feedback_v3_engineered_features_proven.md).
    - regime_momentum_signed_3d is the LAST element (15th position; SWAP at 15th slot).
    """
    assert "regime_momentum_signed_3d" in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_3d NOT found in V3_FEATURE_COLUMNS_TOP_N. "
        "iter-v3/052 SWAP: Add it as 15th element in features_v3/__init__.py."
    )
    assert "fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N, (
        "fracdiff_d05_close STILL in V3_FEATURE_COLUMNS_TOP_N. "
        "iter-v3/052 SWAP: Remove it (PARKED per /051 EXPLORATION-NULL-RESULT + "
        "Critic FINAL `32cc46f` rec #2)."
    )
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 15, (
        f"V3_FEATURE_COLUMNS_TOP_N count={n} — expected 15. "
        "SWAP must keep count at 15 (fracdiff OUT; regime_momentum_signed_3d IN)."
    )
    assert "regime_momentum_signed_5d" in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_5d NOT found in V3_FEATURE_COLUMNS_TOP_N. "
        "Mandate per feedback_v3_engineered_features_proven.md is ACTIVE at iter-v3/052 "
        "(iter-v3/028 baseline edge ingredient; multi-seed CONFIRMATION-MERGE)."
    )
    # Verify regime_momentum_signed_3d is the last element (15th position == index 14)
    last_element = V3_FEATURE_COLUMNS_TOP_N[-1]
    assert last_element == "regime_momentum_signed_3d", (
        f"Last element of V3_FEATURE_COLUMNS_TOP_N is '{last_element}' — "
        "expected 'regime_momentum_signed_3d'. "
        "iter-v3/052 SWAP: regime_momentum_signed_3d must be at position 15 (index 14). "
        "Check V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )
