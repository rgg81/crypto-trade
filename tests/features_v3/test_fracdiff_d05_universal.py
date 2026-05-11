"""Adversarial tests for fracdiff_d05_close universal scope — iter-v3/051.

5 mandatory tests per brief Section 3 Sub-fix 7:

1. test_fracdiff_d05_close_in_universal_feature_list — fracdiff_d05_close MUST be in
   V3_FEATURE_COLUMNS_TOP_N; verify it is present and total count == 15.
2. test_fracdiff_d05_close_present_in_all_4_symbol_parquets — all 4 symbol parquets
   (BCH/LDO/TRX/ALGO; ALGO reserved-for-future even though not in /051 V3_MODELS) must
   have fracdiff_d05_close column.
3. test_fracdiff_d05_close_stationary_per_symbol — ADF p<0.05 for fracdiff_d05_close
   in IS subset of each symbol's parquet (smoke test).
4. test_fracdiff_d05_close_no_lookahead — verify compute_fracdiff_d05_close uses past-
   only data (Fixed-Width Window FFD; value at bar t depends only on bars [0, t]).
5. test_v3_models_is_3_symbol_at_iter_v3_051 — V3_MODELS must be exactly
   (BCH, LDO, TRX) at iter-v3/051; regression test against accidental ALGO re-add.

System-level REVERT state (iter-v3/051):
- V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols (ALGO REVERTED).
- V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty — REVERT).
- block_long_for = () (empty — REVERT).
- REQUIRED_GAP = 66 = (21+1)*3 (REVERT).
- V3_FEATURE_COLUMNS_TOP_N = 15 features (fracdiff_d05_close ADDED).

Single axis under test: fracdiff_d05_close at universal scope (14 → 15).
EDA evidence (analysis/iteration_v3-051/ SHA `290f37b`):
- ADF stationary at p<0.05 across all 4 symbols.
- IC carve-out PASS (max |IC|=0.7381 with vwap_dev_20 source primitive).
- Univariate Spearman significant negative (mean ρ=-0.044) across all 4 symbols.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N
from crypto_trade.features_v3.engineered_v3 import compute_fracdiff_d05_close

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_8H_MS = 8 * 3600 * 1000
_IS_START_MS = 1_679_616_000_000  # 2023-03-24 00:00 UTC
_OOS_CUTOFF_MS = 1_742_774_400_000  # 2025-03-24 00:00 UTC (IMMUTABLE)

_PARQUET_DIR = "data/features_v3"
_V3_ALL_SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT", "ALGOUSDT")
_V3_MODELS_ITER_051 = ("BCHUSDT", "LDOUSDT", "TRXUSDT")


# ---------------------------------------------------------------------------
# Test 1 — fracdiff_d05_close MUST be in V3_FEATURE_COLUMNS_TOP_N (universal list)
# ---------------------------------------------------------------------------


def test_fracdiff_d05_close_in_universal_feature_list() -> None:
    """fracdiff_d05_close MUST be in V3_FEATURE_COLUMNS_TOP_N and count MUST be 15.

    iter-v3/051: cycle 4 #1 EXPLORATION axis. fracdiff_d05_close ADDED (14 → 15).
    """
    assert "fracdiff_d05_close" in V3_FEATURE_COLUMNS_TOP_N, (
        "fracdiff_d05_close NOT found in V3_FEATURE_COLUMNS_TOP_N — "
        "iter-v3/051 ADD axis failed. Add it as 15th element."
    )
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 15, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} elements — expected 15. "
        "iter-v3/051: fracdiff_d05_close ADDED (14 → 15). "
        "Check V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


# ---------------------------------------------------------------------------
# Test 2 — fracdiff_d05_close present in all 4 symbol parquets (no regen needed)
# ---------------------------------------------------------------------------


def test_fracdiff_d05_close_present_in_all_4_symbol_parquets() -> None:
    """All 4 symbol parquets MUST contain fracdiff_d05_close column.

    iter-v3/051 brief Sub-fix 9: no feature regeneration required. QR claims the
    column is already present in all 4 parquets. This test verifies the claim.
    ALGOUSDT is included even though not in /051 V3_MODELS (reserved-for-future).
    """
    for sym in _V3_ALL_SYMBOLS:
        path = f"{_PARQUET_DIR}/{sym}_8h_features.parquet"
        try:
            schema = pq.read_schema(path)
            cols = schema.names
        except Exception as exc:
            pytest.fail(f"{sym} parquet not readable at {path}: {exc}")
        assert "fracdiff_d05_close" in cols, (
            f"{sym} parquet at {path} missing fracdiff_d05_close column. "
            "Run `uv run crypto-trade features --track v3` to regenerate parquets."
        )


# ---------------------------------------------------------------------------
# Test 3 — fracdiff_d05_close ADF stationarity smoke test (IS subset)
# ---------------------------------------------------------------------------


def test_fracdiff_d05_close_stationary_per_symbol() -> None:
    """fracdiff_d05_close ADF p-value must be < 0.05 in IS subset for each /051 symbol.

    iter-v3/051 EDA evidence: ADF p≈0 for BCH/LDO/TRX. This smoke test reads the
    actual parquet IS subset and re-runs ADF to confirm the column is stationary.

    Uses statsmodels adfuller with autolag='AIC'.
    """
    import pyarrow.parquet as pq  # noqa: PLC0415
    from statsmodels.tsa.stattools import adfuller  # noqa: PLC0415

    for sym in _V3_MODELS_ITER_051:
        path = f"{_PARQUET_DIR}/{sym}_8h_features.parquet"
        try:
            df = pq.read_table(
                path,
                columns=["open_time", "fracdiff_d05_close"],
            ).to_pandas()
        except Exception as exc:
            pytest.fail(f"{sym} parquet read failed: {exc}")

        # IS subset only (open_time < OOS_CUTOFF_MS)
        df_is = df[df["open_time"] < _OOS_CUTOFF_MS].copy()
        series = df_is["fracdiff_d05_close"].dropna()

        assert len(series) >= 100, f"{sym}: IS subset too small ({len(series)} rows) for ADF test."

        adf_stat, p_value, *_ = adfuller(series, autolag="AIC")
        assert p_value < 0.05, (
            f"{sym}: fracdiff_d05_close ADF p-value={p_value:.4f} — expected < 0.05. "
            f"ADF stat={adf_stat:.4f}. Feature is NOT stationary in IS. "
            "Check compute_fracdiff_d05_close in fracdiff_v3.py."
        )


# ---------------------------------------------------------------------------
# Test 4 — fracdiff_d05_close no lookahead (past-only convention)
# ---------------------------------------------------------------------------


def test_fracdiff_d05_close_no_lookahead() -> None:
    """compute_fracdiff_d05_close must use only past data at each bar.

    Fixed-Width Window FFD computes the weighted sum of past values at each bar t:
    ffd(t) = sum_{k=0}^{K} w_k * close[t-k]
    All weights look BACKWARD (k >= 0). No future close is used.

    We verify this by checking that adding future data after a point t does NOT
    change the feature value at t — if it changed, the function would be looking ahead.

    This is a regression guard against naive pd.rolling().apply() implementations
    that might compute over a centered window.
    """
    # Build a minimal close series
    n = 100
    rng = np.random.default_rng(42)
    open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
    close = rng.uniform(100.0, 1000.0, n)
    df_short = pd.DataFrame({"open_time": open_times, "close": close})

    # Extend with different future data
    future_close = rng.uniform(100.0, 1000.0, 50)
    future_times = [_IS_START_MS + (n + i) * _8H_MS for i in range(50)]
    future_df = pd.DataFrame({"open_time": future_times, "close": future_close})
    df_long = pd.concat([df_short, future_df], ignore_index=True)

    # Compute feature on both
    result_short = compute_fracdiff_d05_close(df_short.copy())["fracdiff_d05_close"]
    result_long = compute_fracdiff_d05_close(df_long.copy())["fracdiff_d05_close"]

    # Values at the last bar of df_short must be identical in both
    # (past-only: future data cannot affect past bars)
    last_common_val_short = result_short.iloc[-1]
    last_common_val_long = result_long.iloc[n - 1]

    # Allow tiny floating-point tolerance
    if not (np.isnan(last_common_val_short) and np.isnan(last_common_val_long)):
        assert abs(last_common_val_short - last_common_val_long) < 1e-10, (
            f"compute_fracdiff_d05_close lookahead detected: "
            f"value at bar {n - 1} changed when future data was appended. "
            f"short={last_common_val_short:.6f}, long={last_common_val_long:.6f}. "
            "Check Fixed-Width Window FFD implementation in fracdiff_v3.py — "
            "ensure only backward-looking weights (k >= 0) are used."
        )


# ---------------------------------------------------------------------------
# Test 5 — V3_MODELS is exactly (BCH, LDO, TRX) at iter-v3/051 (regression guard)
# ---------------------------------------------------------------------------


def test_v3_models_is_3_symbol_at_iter_v3_051() -> None:
    """V3_MODELS must be exactly (BCHUSDT, LDOUSDT, TRXUSDT) at iter-v3/051.

    Regression guard against accidental ALGO re-add. ALGOUSDT was REVERTED per
    system-level rule `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED
    2026-05-10 (second-cycle confirmation of per-symbol-customization anti-pattern).

    iter-v3/051: SYSTEM-LEVEL REVERT to iter-v3/028 architecture. V3_MODELS = 3-sym.
    """
    # Import locally to catch import-time state
    import importlib  # noqa: PLC0415
    import sys  # noqa: PLC0415

    # Force reimport to ensure we see the current module state
    if "run_baseline_v3" in sys.modules:
        run_mod = sys.modules["run_baseline_v3"]
    else:
        run_mod = importlib.import_module("run_baseline_v3")

    v3_models = run_mod.V3_MODELS
    symbols = [sym for _, sym in v3_models]

    assert len(symbols) == 3, (
        f"V3_MODELS has {len(symbols)} symbols — expected exactly 3 (BCH/LDO/TRX). "
        "iter-v3/051 SYSTEM-LEVEL REVERT: ALGOUSDT must be absent from V3_MODELS. "
        f"Current symbols: {symbols}"
    )
    assert "ALGOUSDT" not in symbols, (
        f"ALGOUSDT FOUND in V3_MODELS — must be absent at iter-v3/051. "
        "SYSTEM-LEVEL REVERT to iter-v3/028 architecture; ALGO must not be in V3_MODELS. "
        f"Current symbols: {symbols}"
    )
    expected = {"BCHUSDT", "LDOUSDT", "TRXUSDT"}
    actual = set(symbols)
    assert actual == expected, (
        f"V3_MODELS symbols mismatch: expected {expected}, got {actual}. "
        "iter-v3/051 V3_MODELS must be exactly (BCHUSDT, LDOUSDT, TRXUSDT)."
    )
