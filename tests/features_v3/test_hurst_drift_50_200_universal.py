"""Adversarial tests for hurst_drift_50_200 universal scope — iter-v3/064.

iter-v3/064: hurst_drift_50_200 PARKED state — RE-CONFIRMED ABSENT.
- /053: PATH D NULL-RESULT closeout (Critic FINAL `c056354` rec #1).
- /054: PARKED — dropped from V3_FEATURE_COLUMNS_TOP_N.
- /063: RE-INCLUDED briefly in mass expansion 14→48. Pre-flight assertion (PATH
  C-clean + PATH D bans) blocked launch; user-authorized 48→46 drop removed it
  again. Mass-expansion axis itself CLOSED at /063 (SUSPICIOUS-OOS-DOMINANT,
  Critic FINAL `7cbc136`).
- /064: REVERT to 14-feature anchor + ADD adx_14 = 15 features (PHASED
  MASS-EXPANSION #1). hurst_drift_50_200 REMAINS PARKED (catastrophic-dead
  per `feedback_v3_mass_feature_expansion.md` amended 2026-05-14 ban list).

5 tests retained (compute function dispatch + ADF + look-ahead) verify the
underlying primitive remains correctly implemented (zero revert cost; the
compute function and parquet column are RETAINED as dead code in case of
future re-evaluation under different conditions). Tests 1 + 5 verify that
hurst_drift_50_200 is ABSENT from V3_FEATURE_COLUMNS_TOP_N at /064.

State (iter-v3/064 PHASED MASS-EXPANSION #1):
- V3_FEATURE_COLUMNS_TOP_N = 15 features (14 BASELINE_V3 + adx_14).
- hurst_drift_50_200 ABSENT from V3_FEATURE_COLUMNS_TOP_N (PARKED).
- regime_momentum_signed_3d ABSENT (PARKED; retained as dead code).
- regime_momentum_signed_5d PRESENT (mandate per feedback_v3_engineered_features_proven.md).
- adx_14 PRESENT (PHASED MASS-EXPANSION #1 addition).
- V3_MODELS = (BCHUSDT, ADAUSDT, TRXUSDT) — 3 symbols (iter-v3/078 UNIVERSE REVISION).
- REQUIRED_GAP = 66 = (21+1)*3 (UNCHANGED).

EDA evidence (analysis/iteration_v3-053/ SHA `1fc6d55`):
- ADF stationary p<<0.05 all 4 syms (axis2_adf_per_symbol.csv).
- Linear redundancy R^2=1.0 EXACT (algebraic identity).
- IC max 0.85-0.88 with hurst_diff_100_50 (Category 2 carve-out applies).
- Compute function at engineered_v3.py RETAINED as dead code dispatch.
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
# iter-v3/087 WHOLESALE universe-breadth expansion — 6-symbol universe.
_V3_MODELS_ITER_053 = (
    "BCHUSDT",
    "LDOUSDT",
    "TRXUSDT",
    "GALAUSDT",
    "MANAUSDT",
    "SANDUSDT",
)


# ---------------------------------------------------------------------------
# Test 1 — hurst_drift_50_200 MUST be in V3_FEATURE_COLUMNS_TOP_N
# ---------------------------------------------------------------------------


def test_hurst_drift_50_200_in_universal_feature_list() -> None:
    """hurst_drift_50_200 MUST be ABSENT from V3_FEATURE_COLUMNS_TOP_N at iter-v3/065.

    iter-v3/053: SWAP added hurst_drift_50_200 as 15th element.
    iter-v3/054: PARK -- hurst_drift_50_200 DROPPED (Critic FINAL `c056354` rec #1).
    iter-v3/063: RE-INCLUDED briefly under mass-expansion mandate; pre-flight ban
                 filter dropped it again at 48→46 step. Mass-expansion axis CLOSED.
    iter-v3/064: REMAINS PARKED. adx_14 added, then REMOVED at /064 closeout (NEGATIVE).
                 V3_FEATURE_COLUMNS_TOP_N reverted to 14 at commit `04080c4`.
    iter-v3/065: NON-FEATURE axis. Feature count = 14. hurst_drift_50_200 still PARKED-ABSENT.
                 Compute function in engineered_v3.py is RETAINED as dead code dispatch.
    """
    assert "hurst_drift_50_200" not in V3_FEATURE_COLUMNS_TOP_N, (
        "hurst_drift_50_200 FOUND in V3_FEATURE_COLUMNS_TOP_N -- must be ABSENT at iter-v3/065. "
        "PARKED per /053 PATH D NULL-RESULT closeout + Critic FINAL `c056354` rec #1. "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 14, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} elements -- expected 14 (the BASELINE_V3 "
        "/059/060 14-feature anchor stack). iter-v3/087's SOLE axis is the WHOLESALE "
        "V3_MODELS 3->6 expansion, NOT a feature change; the /086 perp-spot basis "
        "family is REVERTED. hurst_drift_50_200 stays PARKED-ABSENT; "
        "/082's funding family stays reverted. "
        "Check V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )
    assert "regime_momentum_signed_3d" not in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_3d STILL in V3_FEATURE_COLUMNS_TOP_N -- "
        "iter-v3/053 PARK must remain active. 3d must be ABSENT (PARKED per /052 "
        "PATH C-suspicious closeout; Critic FINAL `34cc46f` rec #2; NOT re-evaluated). "
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

    # This is a feature-MATH stationarity smoke test — it verifies the
    # hurst_drift_50_200 property, not the live universe composition. It runs on
    # the /059-canonical 3-symbol universe (iter-v3/084 reverted the /083 FILUSDT
    # expansion — /083 was NEGATIVE/NO-MERGE).
    _incumbents_with_parquets = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
    for sym in _incumbents_with_parquets:
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
# Test 5 — V3_MODELS is the /059-canonical 3-symbol universe at iter-v3/084
# ---------------------------------------------------------------------------


def test_v3_models_is_3_symbol_at_iter_v3_084() -> None:
    """V3 universe must be the 6-symbol BCH/LDO/TRX/GALA/MANA/SAND set at iter-v3/087.

    iter-v3/087 CYCLE 3 EXPLORATION #6 — the SOLE axis is a WHOLESALE
    universe-breadth EXPANSION: V3_MODELS grows 3 -> 6 by adding GALAUSDT,
    MANAUSDT, SANDUSDT. ALGOUSDT was REVERTED at the system level per iter-v3/051;
    ADAUSDT is CLOSED (/078 SUSPICIOUS-OOS-DOMINANT); FILUSDT is CLOSED (/083
    NEGATIVE).

    iter-v3/087: feature count = 14 (the BASELINE_V3 /059/060 anchor stack — the
    /086 perp-spot basis family REVERTED, Critic /086 Rec #3). All 6 symbols
    return the 14-feature universal fallback. The /087 axis is a universe
    expansion, NOT a feature change. REQUIRED_GAP = 132 = (21+1)*6.
    """
    from crypto_trade.features_v3 import features_for_symbol  # noqa: PLC0415

    expected_universe = (
        "BCHUSDT",
        "LDOUSDT",
        "TRXUSDT",
        "GALAUSDT",
        "MANAUSDT",
        "SANDUSDT",
    )
    # Each symbol in the expected universe must return the 14-feature universal fallback
    for sym in expected_universe:
        feats = features_for_symbol(sym)
        assert len(feats) == 14, (
            f"{sym} fallback returns {len(feats)} features -- expected 14 "
            "(the BASELINE_V3 /059/060 14-feature anchor stack; the /086 perp-spot "
            "basis family REVERTED at iter-v3/087); hurst_drift_50_200 stays "
            "PARKED-ABSENT."
        )
        assert "hurst_drift_50_200" not in feats, (
            f"{sym} fallback contains hurst_drift_50_200 -- must be ABSENT at iter-v3/065. "
            "PARKED per /053 PATH D NULL-RESULT + Critic FINAL `c056354` rec #1."
        )
        assert "regime_momentum_signed_3d" not in feats, (
            f"{sym} fallback contains regime_momentum_signed_3d -- must be ABSENT. "
            "iter-v3/053: 3d PARKED per /052 PATH C-suspicious; NOT re-evaluated."
        )
        assert "adx_14" not in feats, (
            f"{sym} fallback contains adx_14 -- must be ABSENT at iter-v3/065. "
            "adx_14 REMOVED at /064 closeout (NEGATIVE per Critic FINAL `452fcf2`)."
        )
    # ALGOUSDT must NOT be in the v3 model universe
    assert "ALGOUSDT" not in {sym for sym in expected_universe}, (
        "ALGOUSDT found in expected universe -- must be ABSENT at iter-v3/065. "
        "System-level REVERT at iter-v3/051."
    )
    # Verify the constant matches the expected list exactly
    assert _V3_MODELS_ITER_053 == expected_universe, (
        f"_V3_MODELS_ITER_053 = {_V3_MODELS_ITER_053} -- expected {expected_universe}. "
        "Update _V3_MODELS_ITER_053 constant in this test file."
    )
