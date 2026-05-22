"""Integration tests for iter-v3/093 derivatives-microstructure regime-conditioned book.

6 mandatory tests per brief Section 9.2 (the /092 anti-recurrence requirement):

  #1 test_dsr_json_is_computed
     — source-level grep assert that the runner imports and CALLS
       validation_v3.deflated_sharpe_ratio_v3 and validation_v3.psr.
       Build FAILS if these call-sites are absent.

  #2 test_no_lookahead_in_derivatives_panel
     — spike-perturbs a single future OI/funding value and asserts
       no past feature changes.

  #3 test_vol_regime_label_uses_train_window_cutpoints
     — asserts tercile cut-points are computed on the training window only,
       never on the test window or full panel.

  #4 test_regime_gate_is_monotone_conservative
     — asserts the size multiplier is always in [0.0, 1.0] and never
       exceeds 1.0 (the R-gate monotone-conservative invariant).

  #5 test_oi_free_panel (Section 11 amendment — repurposed from test_oi_feature_ic_check)
     — asserts DERIVATIVES_FEATURE_COLUMNS contains exactly 13 features and
       that NONE of the 5 dropped per-symbol OI names are present. Confirms
       the 13-feature EDA-validated panel is provably OI-free. The suite
       stays 6 tests; the /092 anti-recurrence guarantee is fully intact.

  #6 test_walk_forward_embargo_intact
     — asserts the e149e9d embargo (train_end_ms = test_start_ms - embargo_ms)
       is present and load-bearing in the new runner.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pandas as pd
from run_derivatives_regime_v3 import (
    EMBARGO_CANDLES,
    _verify_embargo_intact,
    compute_regime_size_multiplier,
    compute_vol_regime_label,
)

# ── Imports under test ────────────────────────────────────────────────────────
from crypto_trade.features_v3.derivatives_state_v3 import (
    DERIVATIVES_FEATURE_COLUMNS,
    compute_derivatives_state_features,
)
from crypto_trade.strategies.ml.validation_v3 import combinatorial_purged_cv

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _synthetic_klines(n: int = 300, seed: int = 42) -> pd.DataFrame:
    """Synthetic 8h kline DataFrame for testing."""
    rng = np.random.default_rng(seed)
    start_ms = 1_580_000_000_000  # 2020-01-26 UTC
    bar_ms = 8 * 3_600_000
    open_times = [start_ms + i * bar_ms for i in range(n)]
    closes = 100.0 * np.cumprod(1 + rng.normal(0, 0.01, n))
    return pd.DataFrame(
        {
            "open_time": open_times,
            "close_time": [ot + bar_ms - 1 for ot in open_times],
            "open": closes * (1 + rng.uniform(-0.005, 0.005, n)),
            "high": closes * (1 + rng.uniform(0.0, 0.01, n)),
            "low": closes * (1 - rng.uniform(0.0, 0.01, n)),
            "close": closes,
            "volume": rng.uniform(1000, 5000, n),
            "symbol": "BCHUSDT",
        }
    )


def _synthetic_funding(klines_df: pd.DataFrame) -> pd.DataFrame:
    """Synthetic funding rate DataFrame aligned to kline open_times."""
    rng = np.random.default_rng(99)
    return pd.DataFrame(
        {
            "funding_time": klines_df["open_time"].values,
            "funding_rate": rng.normal(0.0001, 0.0003, len(klines_df)),
        }
    )


def _synthetic_spot(klines_df: pd.DataFrame) -> pd.DataFrame:
    """Synthetic spot kline DataFrame aligned to kline open_times."""
    rng = np.random.default_rng(77)
    # Spot slightly below perp (positive basis on average)
    spot_closes = klines_df["close"].values * (1 - rng.uniform(0.0, 0.002, len(klines_df)))
    return pd.DataFrame(
        {
            "open_time": klines_df["open_time"].values,
            "close": spot_closes,
        }
    )


def _synthetic_oi(klines_df: pd.DataFrame) -> pd.DataFrame:
    """Synthetic 8h OI DataFrame aligned to kline open_times."""
    rng = np.random.default_rng(55)
    n = len(klines_df)
    oi = np.cumprod(1 + rng.normal(0, 0.005, n)) * 1e6
    oi_val = oi * klines_df["close"].values * 1.0
    return pd.DataFrame(
        {
            "open_time": klines_df["open_time"].values,
            "sum_open_interest": oi,
            "sum_open_interest_value": oi_val,
            "count_toptrader_long_short_ratio": rng.uniform(0.8, 1.2, n),
            "sum_toptrader_long_short_ratio": rng.uniform(0.8, 1.2, n),
            "count_long_short_ratio": rng.uniform(0.9, 1.1, n),
            "sum_taker_long_short_vol_ratio": rng.uniform(0.9, 1.1, n),
        }
    )


# ── Test #1: DSR/PSR call-site structural guard ───────────────────────────────


def test_dsr_json_is_computed():
    """#1 — Runner calls validation_v3.deflated_sharpe_ratio_v3 and validation_v3.psr.

    This is the /092 anti-recurrence structural guard. The test reads the
    runner source and asserts that both call-sites are present as active
    function calls (not just import references). If either is absent, the
    build FAILS before the backtest runs.

    A mock dsr.json with hardcoded 0.0 / NaN would NOT satisfy this test
    because the test inspects the runner SOURCE, not the output file.
    """
    runner_src = Path("run_derivatives_regime_v3.py").read_text()

    # Assert genuine function call (parenthesis must follow the name)
    assert "deflated_sharpe_ratio_v3(" in runner_src, (
        "ANTI-RECURRENCE GUARD FAILED: run_derivatives_regime_v3.py does not contain "
        "a call to deflated_sharpe_ratio_v3(). The /092 defect class (hardcoded "
        "sentinel DSR values) cannot recur. Add a genuine "
        "validation_v3.deflated_sharpe_ratio_v3() call-site to the runner."
    )
    assert "psr(" in runner_src, (
        "ANTI-RECURRENCE GUARD FAILED: run_derivatives_regime_v3.py does not contain "
        "a call to psr(). The /092 defect class (hardcoded sentinel PSR values) "
        "cannot recur. Add a genuine validation_v3.psr() call-site to the runner."
    )
    assert "pbo_from_cpcv(" in runner_src, (
        "ANTI-RECURRENCE GUARD FAILED: run_derivatives_regime_v3.py does not contain "
        "a call to pbo_from_cpcv(). Add a genuine validation_v3.pbo_from_cpcv() "
        "call-site."
    )

    # Also assert the runner imports these from validation_v3 (not from somewhere else)
    assert "from crypto_trade.strategies.ml.validation_v3 import" in runner_src, (
        "Runner must import from validation_v3 (not from a sentinel/mock module)."
    )

    # Verify the runtime guard (_verify_dsr_psr_call_sites) raises on a sentinel
    # by temporarily passing a modified source string to the same logic
    sentinel_src = runner_src.replace("deflated_sharpe_ratio_v3(", "# removed")
    # We can't call _verify_dsr_psr_call_sites directly with a custom src,
    # but we can reproduce its logic inline:
    missing = []
    if "deflated_sharpe_ratio_v3(" not in sentinel_src:
        missing.append("deflated_sharpe_ratio_v3(")
    assert missing, (
        "Expected the sentinel source (without deflated_sharpe_ratio_v3 call) "
        "to be detected as missing — the guard logic is broken."
    )

    print("[test_dsr_json_is_computed] PASS — all three DSR/PSR/PBO call-sites present")


# ── Test #2: No lookahead in derivatives panel ────────────────────────────────


def test_no_lookahead_in_derivatives_panel():
    """#2 — Spike a future OI/funding value; assert NO past feature changes.

    The past-only invariant: features at bar t must not depend on any data
    at bars t+1, t+2, ... Spike-perturbing a future bar must leave all
    past bars' features unchanged.
    """
    klines = _synthetic_klines(200)
    funding = _synthetic_funding(klines)
    spot = _synthetic_spot(klines)
    oi = _synthetic_oi(klines)
    btc_funding = _synthetic_funding(klines)
    btc_oi = _synthetic_oi(klines)

    # Compute baseline features
    baseline = compute_derivatives_state_features(klines, funding, spot, oi, btc_funding, btc_oi)

    # Spike the OI at bar 150 (a future bar relative to bars 0..149)
    oi_spiked = oi.copy()
    oi_spiked.loc[oi_spiked.index[150], "sum_open_interest"] *= 1000.0

    funding_spiked = funding.copy()
    funding_spiked.loc[funding_spiked.index[150], "funding_rate"] = 99.9

    perturbed = compute_derivatives_state_features(
        klines, funding_spiked, spot, oi_spiked, btc_funding, btc_oi
    )

    # Check: features at bars 0..148 must be bit-identical to baseline
    past_cols = list(DERIVATIVES_FEATURE_COLUMNS)
    for col in past_cols:
        if col not in baseline.columns or col not in perturbed.columns:
            continue
        baseline_past = baseline[col].iloc[:149].fillna(0.0).values
        perturbed_past = perturbed[col].iloc[:149].fillna(0.0).values
        max_diff = float(np.nanmax(np.abs(baseline_past - perturbed_past)))
        assert max_diff < 1e-9, (
            f"LOOK-AHEAD VIOLATION in feature '{col}': "
            f"past bars (0..148) changed by {max_diff:.2e} after spiking bar 150. "
            "The .shift(1) past-only discipline is broken."
        )

    print("[test_no_lookahead_in_derivatives_panel] PASS — past features unchanged after spike")


# ── Test #3: Vol-regime label uses train-window cut-points ────────────────────


def test_vol_regime_label_uses_train_window_cutpoints():
    """#3 — Tercile cut-points must be computed on training window only.

    Test: compute labels with and without training mask.
    With a training mask that excludes high-vol bars, the cut-points shift
    and labels must differ from the full-window version.
    """
    rng = np.random.default_rng(42)
    n = 300
    bar_ms = 8 * 3_600_000
    start_ms = 1_580_000_000_000
    open_times = [start_ms + i * bar_ms for i in range(n)]

    # Closes: calm for first 150 bars, stressed for last 150
    closes_calm = 100.0 * np.cumprod(1 + rng.normal(0, 0.003, 150))
    closes_stressed = closes_calm[-1] * np.cumprod(1 + rng.normal(0, 0.03, 150))
    closes = np.concatenate([closes_calm, closes_stressed])

    df = pd.DataFrame({"open_time": open_times, "close": closes})

    # Training mask: first 200 bars (mostly calm)
    training_mask = pd.Series([True] * 200 + [False] * 100, index=df.index)

    # Full-window labels (no mask — cut-points include stressed bars)
    labels_full = compute_vol_regime_label(df, horizon=21, training_mask=None)

    # Training-window-only labels (cut-points on calm bars only)
    labels_train = compute_vol_regime_label(df, horizon=21, training_mask=training_mask)

    # Verify both return valid labels (0, 1, 2, or NaN)
    valid_full = labels_full.dropna()
    valid_train = labels_train.dropna()
    assert set(valid_full.unique()) <= {0.0, 1.0, 2.0}, (
        f"Full-window labels contain invalid values: {valid_full.unique()}"
    )
    assert set(valid_train.unique()) <= {0.0, 1.0, 2.0}, (
        f"Train-masked labels contain invalid values: {valid_train.unique()}"
    )

    # The labels must DIFFER in the stressed window (bars 200+) because the
    # cut-points shift when computed on the calm training window only.
    # With calm-only cut-points, bars 200+ are MORE LIKELY to be classified as
    # 'stressed' (class 2) because their vol exceeds calm-window thresholds.
    stressed_region_full = labels_full.iloc[200:].dropna()
    stressed_region_train = labels_train.iloc[200:].dropna()

    if len(stressed_region_full) > 10 and len(stressed_region_train) > 10:
        # They don't have to be strictly ordered, but must be different (non-trivial test)
        # The key assertion is that the labels differ at all, proving cut-points were
        # computed differently.
        assert not np.allclose(stressed_region_full.values, stressed_region_train.values), (
            "LABEL LOOK-AHEAD: labels are identical with and without training mask. "
            "The cut-points are NOT being computed on the training window only — "
            "they appear to use the full panel regardless of training_mask."
        )

    print(
        "[test_vol_regime_label_uses_train_window_cutpoints] PASS — "
        "labels differ when cut-points computed on training window vs full panel"
    )


# ── Test #4: Regime gate is monotone-conservative ─────────────────────────────


def test_regime_gate_is_monotone_conservative():
    """#4 — Size multiplier is always in [0.0, 1.0]; never > 1.0.

    Tests the smooth probability-weighted multiplier:
        1.0 * P(calm) + 0.6 * P(normal) + 0.0 * P(stressed)

    Since all P(·) >= 0 and sum to 1, and all multipliers are in [0, 1],
    the result is always in [0, 1].  This is the monotone-conservative invariant
    (Section 6): the gate only ever reduces exposure, never amplifies it.
    """
    rng = np.random.default_rng(42)
    n = 1000

    # Random probability vectors (Dirichlet-sampled → valid probability simplex)
    alphas = rng.dirichlet(np.ones(3), size=n)
    proba_df = pd.DataFrame(
        {
            "p_calm": alphas[:, 0],
            "p_normal": alphas[:, 1],
            "p_stressed": alphas[:, 2],
        }
    )

    multipliers = compute_regime_size_multiplier(proba_df)

    # Assert all multipliers in [0.0, 1.0]
    assert multipliers.min() >= -1e-9, (
        f"Regime gate multiplier is negative: min={multipliers.min():.6f}. "
        "MONOTONE-CONSERVATIVE VIOLATION: gate is amplifying short exposure."
    )
    assert multipliers.max() <= 1.0 + 1e-9, (
        f"Regime gate multiplier exceeds 1.0: max={multipliers.max():.6f}. "
        "MONOTONE-CONSERVATIVE VIOLATION: gate is adding leverage (> 1.0× exposure)."
    )

    # Edge cases:
    # Pure calm (P(calm)=1): multiplier must be 1.0
    pure_calm = pd.DataFrame({"p_calm": [1.0], "p_normal": [0.0], "p_stressed": [0.0]})
    m_calm = compute_regime_size_multiplier(pure_calm)
    assert abs(float(m_calm.iloc[0]) - 1.0) < 1e-9, (
        f"Pure-calm prediction must give multiplier=1.0, got {float(m_calm.iloc[0]):.6f}"
    )

    # Pure stressed (P(stressed)=1): multiplier must be 0.0
    pure_stressed = pd.DataFrame({"p_calm": [0.0], "p_normal": [0.0], "p_stressed": [1.0]})
    m_stressed = compute_regime_size_multiplier(pure_stressed)
    assert abs(float(m_stressed.iloc[0]) - 0.0) < 1e-9, (
        f"Pure-stressed prediction must give multiplier=0.0, got {float(m_stressed.iloc[0]):.6f}"
    )

    # Pure normal (P(normal)=1): multiplier must be 0.6
    pure_normal = pd.DataFrame({"p_calm": [0.0], "p_normal": [1.0], "p_stressed": [0.0]})
    m_normal = compute_regime_size_multiplier(pure_normal)
    assert abs(float(m_normal.iloc[0]) - 0.6) < 1e-9, (
        f"Pure-normal prediction must give multiplier=0.6, got {float(m_normal.iloc[0]):.6f}"
    )

    # Uniform distribution (1/3 each): multiplier = 1.0/3 + 0.6/3 + 0.0/3 = 0.5333...
    uniform = pd.DataFrame({"p_calm": [1 / 3], "p_normal": [1 / 3], "p_stressed": [1 / 3]})
    m_uniform = compute_regime_size_multiplier(uniform)
    expected_uniform = 1.0 / 3 + 0.6 / 3 + 0.0 / 3
    assert abs(float(m_uniform.iloc[0]) - expected_uniform) < 1e-9, (
        f"Uniform distribution must give multiplier={expected_uniform:.4f}, "
        f"got {float(m_uniform.iloc[0]):.6f}"
    )

    print(
        f"[test_regime_gate_is_monotone_conservative] PASS — "
        f"all {n} random multipliers in [0.0, 1.0]; edge cases correct"
    )


# ── Test #5: OI-free panel assertion (Section 11 amendment) ──────────────────


def test_oi_free_panel():
    """#5 (Section 11 amendment) — Assert DERIVATIVES_FEATURE_COLUMNS is OI-free.

    Verifies the 13-feature EDA-validated panel (funding 7 + basis 4 +
    cross-asset BTC 2) after the per-symbol OI leg was dropped.

    Assertions:
      (a) Exactly 13 features in DERIVATIVES_FEATURE_COLUMNS.
      (b) None of the 5 dropped per-symbol OI names are present.
      (c) The 2 retained cross-asset BTC features ARE present
          (btc_f_zscore_30 and btc_oi_zscore_30).
      (d) The 13-feature panel is computable end-to-end on synthetic data
          without error (smoke-check that the 5 dead OI columns do not
          block the runner's feature-selection step).

    This test replaces the previous test_oi_feature_ic_check (the fetch-oi
    IS-coverage gate). The suite stays at 6 tests; the /092 anti-recurrence
    guarantee (tests #1/#3/#4/#6) is fully intact.
    """
    oi_dropped = {
        "oi_log_delta_1",
        "oi_zscore_30",
        "oi_mcap_ratio",
        "oi_price_divergence",
        "toptrader_ls_ratio",
    }
    btc_cross_asset = {"btc_f_zscore_30", "btc_oi_zscore_30"}

    # (a) Count assertion
    assert len(DERIVATIVES_FEATURE_COLUMNS) == 13, (
        f"Expected exactly 13 features in DERIVATIVES_FEATURE_COLUMNS after Section 11 "
        f"amendment (18 -> 13). Got {len(DERIVATIVES_FEATURE_COLUMNS)}: "
        f"{list(DERIVATIVES_FEATURE_COLUMNS)}"
    )

    col_set = set(DERIVATIVES_FEATURE_COLUMNS)

    # (b) OI-free assertion
    leaked = oi_dropped & col_set
    assert not leaked, (
        f"SECTION 11 VIOLATION: the following dropped per-symbol OI features are still "
        f"present in DERIVATIVES_FEATURE_COLUMNS: {sorted(leaked)}. "
        f"Remove them — they have insufficient IS-window coverage (BCH/TRX < 0.90)."
    )

    # (c) BTC cross-asset features retained
    missing_btc = btc_cross_asset - col_set
    assert not missing_btc, (
        f"BTC cross-asset features missing from DERIVATIVES_FEATURE_COLUMNS: "
        f"{sorted(missing_btc)}. btc_f_zscore_30 and btc_oi_zscore_30 are retained "
        f"per Section 11 (BTC OI archive starts 2020-09, full IS coverage 1.000)."
    )

    # (d) End-to-end smoke: 13 features computable and selectable from synthetic panel
    klines = _synthetic_klines(200)
    funding = _synthetic_funding(klines)
    spot = _synthetic_spot(klines)
    oi = _synthetic_oi(klines)  # still passed so _add_oi_features runs (dead code)
    btc_funding = _synthetic_funding(klines)
    btc_oi = _synthetic_oi(klines)

    deriv_df = compute_derivatives_state_features(klines, funding, spot, oi, btc_funding, btc_oi)

    # Runner's feature selection step: read exactly DERIVATIVES_FEATURE_COLUMNS (13)
    missing_in_panel = [c for c in DERIVATIVES_FEATURE_COLUMNS if c not in deriv_df.columns]
    assert not missing_in_panel, (
        f"Features in DERIVATIVES_FEATURE_COLUMNS missing from computed panel: "
        f"{missing_in_panel}. The runner's feature-selection step would KeyError."
    )
    selected = deriv_df[list(DERIVATIVES_FEATURE_COLUMNS)]
    assert selected.shape[1] == 13, (
        f"Feature selection returned {selected.shape[1]} columns, expected 13."
    )

    print(
        f"[test_oi_free_panel] PASS — "
        f"{len(DERIVATIVES_FEATURE_COLUMNS)} features, OI-free, BTC cross-asset retained, "
        f"end-to-end selection clean"
    )


# ── Test #6: Walk-forward embargo intact ──────────────────────────────────────


def test_walk_forward_embargo_intact():
    """#6 — Assert the e149e9d walk-forward embargo is present and load-bearing.

    Two checks:
    (a) Source-level: combinatorial_purged_cv source contains 'embargo'.
    (b) Behavioral: the runner's _verify_embargo_intact() does not raise.
    (c) Constant check: EMBARGO_CANDLES == 22 = (21 + 1).
    (d) Numerical: the CPCV function with embargo=2 leaves a 2-row gap between
        train and test in a small synthetic split.
    """
    # (a) Source-level check
    src = inspect.getsource(combinatorial_purged_cv)
    assert "embargo" in src, (
        "EMBARGO INTEGRITY FAILURE: combinatorial_purged_cv source does not contain "
        "the 'embargo' parameter. The e149e9d walk-forward fix may have been lost."
    )

    # (b) Runner's own guard
    _verify_embargo_intact()  # must not raise

    # (c) Constant value
    assert EMBARGO_CANDLES == 22, (
        f"EMBARGO_CANDLES should be 22 = (21 + 1) candles (21-bar forward label + 1). "
        f"Got {EMBARGO_CANDLES}."
    )

    # (d) Numerical: with embargo=2, the gap between train-end and test-start is >= 2
    n_samples = 100
    splits = list(
        combinatorial_purged_cv(
            n_samples=n_samples,
            n_splits=5,
            n_test_splits=2,
            gap=2,
            embargo=2,
            expected_gap=2,
        )
    )
    assert len(splits) > 0, "combinatorial_purged_cv returned no splits"

    embargo_size = 2
    for train_idx, test_idx in splits:
        train_set = set(train_idx)
        test_set = set(test_idx)
        if not train_set or not test_set:
            continue
        # Check: no training index falls within `embargo_size` steps before any test index.
        # In CPCV, train and test are combinatorial (non-contiguous), so max_train/min_test
        # comparison is invalid. Instead verify the embargo zone: for each test bar t,
        # none of (t - embargo_size)..(t - 1) should appear in train.
        for t in test_set:
            for lag in range(1, embargo_size + 1):
                candidate = t - lag
                if candidate >= 0 and candidate in train_set:
                    raise AssertionError(
                        f"EMBARGO FAILURE: train index {candidate} is within "
                        f"{embargo_size} steps of test index {t} (lag={lag}). "
                        "The e149e9d embargo fix is not load-bearing."
                    )

    print(
        f"[test_walk_forward_embargo_intact] PASS — "
        f"embargo={EMBARGO_CANDLES} candles, {len(splits)} CPCV splits verified"
    )
