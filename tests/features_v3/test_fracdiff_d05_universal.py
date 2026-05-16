"""Adversarial tests for fracdiff_d05_close — PARKED-ABSENT at iter-v3/064.

iter-v3/052: SWAP added fracdiff_d05_close as 15th element; subsequently PARKED.
iter-v3/063: RE-INCLUDED briefly under mass-expansion mandate (14→48 → 14→46 after
             pre-flight ban filter). Mass-expansion axis itself CLOSED at /063
             (SUSPICIOUS-OOS-DOMINANT, Critic FINAL `7cbc136`).
iter-v3/064: PHASED MASS-EXPANSION #1: REVERT to 14-feature anchor + ADD adx_14 = 15.
             fracdiff_d05_close PARKED-ABSENT (along with all other /063 NEW features
             except adx_14). Compute function retained in engineered_v3.py dispatch
             (parquet column generated; zero revert cost).

5 tests retained as dead-code coverage:
1. test_fracdiff_d05_close_present_in_universal_feature_list — verifies fracdiff_d05_close
   is ABSENT from V3_FEATURE_COLUMNS_TOP_N at /064. Total count must be 15.
2-5. Compute function correctness + parquet column presence + ADF + look-ahead.

State (iter-v3/064 PHASED MASS-EXPANSION #1):
- V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols (iter-v3/079 baseline-restore;
  /078's ADAUSDT universe revision was SUSPICIOUS-OOS-DOMINANT and is CLOSED).
- V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty — REVERT carry-forward).
- block_long_for = () (empty — REVERT carry-forward).
- REQUIRED_GAP = 66 = (21+1)*3 (UNCHANGED).
- V3_FEATURE_COLUMNS_TOP_N = 15 features (14 BASELINE_V3 + adx_14).
  fracdiff_d05_close ABSENT. Compute function in engineered_v3.py RETAINED as dead code.

EDA evidence (analysis/iteration_v3-051/ SHA `290f37b`):
- ADF stationary at p<0.05 across all 4 symbols (column still valid; just parked).
- IC carve-out PASS (max |IC|=0.7381 with vwap_dev_20 source primitive).
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
_V3_ALL_SYMBOLS = ("BCHUSDT", "ADAUSDT", "TRXUSDT", "LDOUSDT", "ALGOUSDT")
_V3_MODELS_ITER_052 = ("BCHUSDT", "LDOUSDT", "TRXUSDT")  # iter-v3/079 baseline-restore


# ---------------------------------------------------------------------------
# Test 1 — fracdiff_d05_close MUST NOT be in V3_FEATURE_COLUMNS_TOP_N (PARKED at /064)
# ---------------------------------------------------------------------------


def test_fracdiff_d05_close_present_in_universal_feature_list() -> None:
    """fracdiff_d05_close MUST be ABSENT from V3_FEATURE_COLUMNS_TOP_N at iter-v3/065.

    iter-v3/052: SWAP added fracdiff; PARKED at /053.
    iter-v3/063: RE-INCLUDED briefly in mass expansion 14→48. Mass-expansion axis CLOSED.
    iter-v3/064: PHASED MASS-EXPANSION #1: REVERT to 14-feature anchor + ADD adx_14 = 15.
                 fracdiff_d05_close REMAINS PARKED-ABSENT.
                 adx_14 REMOVED at /064 closeout (NEGATIVE per Critic `452fcf2`).
    iter-v3/065: NON-FEATURE axis. Feature count = 14. fracdiff_d05_close still PARKED-ABSENT.
                 Compute function in engineered_v3.py RETAINED as dead code.
    """
    assert "fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N, (
        "fracdiff_d05_close FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT at iter-v3/065. "
        "PARKED at /053 PATH C-suspicious + carry-forward at /065. "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 14, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} elements — expected 14 (the BASELINE_V3 "
        "/059/060 14-feature anchor stack). iter-v3/087's SOLE axis is the WHOLESALE "
        "V3_MODELS 3->6 expansion, NOT a feature change; the /086 perp-spot basis "
        "family is REVERTED (Critic /086 Rec #3 — /086 INERT). fracdiff_d05_close "
        "stays PARKED-ABSENT; /082's 4-member funding family stays reverted. "
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

    for sym in _V3_MODELS_ITER_052:
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
# Test 5 — V3_MODELS is the 6-symbol WHOLESALE-expanded universe at iter-v3/087
# ---------------------------------------------------------------------------


def test_v3_models_at_iter_v3_084() -> None:
    """V3_MODELS must be the 6-symbol BCH/LDO/TRX/GALA/MANA/SAND set at iter-v3/087.

    iter-v3/087 CYCLE 3 EXPLORATION #6 — the SOLE axis is a WHOLESALE
    universe-breadth EXPANSION: V3_MODELS grows 3 -> 6 by adding GALAUSDT,
    MANAUSDT, SANDUSDT (the Grinold-Kahn breadth lever). Regression guard
    against accidental ALGO re-add (REVERT at /051), ADA re-add (/078
    SUSPICIOUS-OOS-DOMINANT, CLOSED), HBAR/AVAX (CLOSED at /021), and FILUSDT
    re-add (/083 NEGATIVE, CLOSED universe-expansion candidate).

    HISTORY:
    - iter-v3/051: SYSTEM-LEVEL REVERT (4 -> 3 syms; drop ALGOUSDT)
    - iter-v3/069: 3 -> 4 (+ADAUSDT) UNIVERSE EXPANSION (INERT-AT-EXPLORATION)
    - iter-v3/070: 4 -> 3 (REVERT ADAUSDT) CYCLE 1 CONFIRMATION
    - iter-v3/078: LDOUSDT -> ADAUSDT UNIVERSE REVISION (SUSPICIOUS-OOS-DOMINANT)
    - iter-v3/079: ADAUSDT -> LDOUSDT REVERT (baseline-restore; /078 axis CLOSED)
    - iter-v3/083: 3 -> 4 (+FILUSDT) UNIVERSE EXPANSION (NEGATIVE/NO-MERGE)
    - iter-v3/084: 4 -> 3 (REVERT FILUSDT) — clean /059-config anchor re-run
    - iter-v3/087: 3 -> 6 (+GALA +MANA +SAND) WHOLESALE breadth EXPANSION
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

    assert len(symbols) == 6, (
        f"V3_MODELS has {len(symbols)} symbols — expected exactly 6 "
        f"(BCH/LDO/TRX/GALA/MANA/SAND) at iter-v3/087. Current symbols: {symbols}"
    )
    assert "ALGOUSDT" not in symbols, (
        f"ALGOUSDT FOUND in V3_MODELS — must be absent (system-level REVERT at /051). "
        f"Current symbols: {symbols}"
    )
    assert "LDOUSDT" in symbols, (
        f"LDOUSDT NOT FOUND in V3_MODELS — must be present (an incumbent, RETAINED "
        f"through the /087 WHOLESALE expansion). Current symbols: {symbols}"
    )
    assert "FILUSDT" not in symbols, (
        f"FILUSDT FOUND in V3_MODELS — must be absent (/083's FILUSDT universe "
        f"expansion was NEGATIVE/NO-MERGE; FILUSDT is a CLOSED universe-expansion "
        f"candidate). Current symbols: {symbols}"
    )
    assert "ADAUSDT" not in symbols, (
        f"ADAUSDT FOUND in V3_MODELS — must be absent (/078's LDOUSDT->ADAUSDT "
        f"universe revision was SUSPICIOUS-OOS-DOMINANT and is CLOSED). "
        f"Current symbols: {symbols}"
    )
    # iter-v3/021 closed HBAR + AVAX at catalog level (NEGATIVE-clean)
    assert "HBARUSDT" not in symbols, (
        f"HBARUSDT FOUND in V3_MODELS — must be absent (CLOSED at catalog level "
        f"per iter-v3/021 diary lesson (c) — universe expansion HBAR+AVAX NEGATIVE-clean). "
        f"Current symbols: {symbols}"
    )
    assert "AVAXUSDT" not in symbols, (
        f"AVAXUSDT FOUND in V3_MODELS — must be absent (CLOSED at catalog level "
        f"per iter-v3/021 diary lesson (c) — universe expansion HBAR+AVAX NEGATIVE-clean). "
        f"Current symbols: {symbols}"
    )
    expected = {"BCHUSDT", "LDOUSDT", "TRXUSDT", "GALAUSDT", "MANAUSDT", "SANDUSDT"}
    actual = set(symbols)
    assert actual == expected, (
        f"V3_MODELS symbols mismatch: expected {expected}, got {actual}. "
        "iter-v3/087 V3_MODELS must be the 6-symbol WHOLESALE-expanded universe "
        "(BCH/LDO/TRX incumbents + GALA/MANA/SAND added)."
    )
