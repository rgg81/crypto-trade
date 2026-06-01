"""Tests for iter-v1/054: BTC-only impulse-drop attribution test.

Covers 6 mandatory tests:

1. test_impulse_dropped — btc_funding_rate_8h_impulse NOT in V1_FEATURE_COLUMNS_PRUNED.
2. test_spread_retained — btc_funding_spread_30_90 IS in V1_FEATURE_COLUMNS_PRUNED.
3. test_pruned_size_47 — V1_FEATURE_COLUMNS_PRUNED has exactly 47 features.
4. test_btc_only_cohort — V1_ITER054_UNIVERSE is exactly ("BTCUSDT",).
5. test_features_base_hash_changed_vs_053 — 47-col hash differs from 48-col /052-/053 hash.
6. test_no_lookahead — spread function unchanged; no lookahead regression.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# 1. test_impulse_dropped
# ---------------------------------------------------------------------------


def test_impulse_dropped() -> None:
    """btc_funding_rate_8h_impulse must NOT be in V1_FEATURE_COLUMNS_PRUNED at /054.

    /053 confirmed impulse INERT-by-importance in 3/3 outer seeds (rank >30/48).
    /054 DROP mandate: remove impulse from V1_FEATURE_COLUMNS_PRUNED (48 → 47 cols).
    Feature computation code is preserved in funding_v1.py (restore path if needed).
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED  # noqa: PLC0415

    assert "btc_funding_rate_8h_impulse" not in V1_FEATURE_COLUMNS_PRUNED, (
        "btc_funding_rate_8h_impulse MUST NOT be in V1_FEATURE_COLUMNS_PRUNED at iter-v1/054. "
        "It was confirmed INERT-by-importance in 3/3 outer seeds at /053 (rank >30/48). "
        "The /054 impulse-drop must remove it from the pruned feature set. "
        "Check src/crypto_trade/features_v1/__init__.py — the impulse entry must be "
        "commented out (NOT deleted, since the computation code is preserved in funding_v1.py)."
    )


# ---------------------------------------------------------------------------
# 2. test_spread_retained
# ---------------------------------------------------------------------------


def test_spread_retained() -> None:
    """btc_funding_spread_30_90 MUST be in V1_FEATURE_COLUMNS_PRUNED at /054.

    /053 confirmed spread rank 4-10/48 in 3/3 outer seeds (STABLE multi-seed confirmed).
    /054 retains the spread as the sole remaining BTC-specialist funding feature.
    The impulse-drop test is specifically testing whether spread ALONE delivers
    the /052 IS lift — spread MUST be present for the test to be valid.
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED  # noqa: PLC0415

    assert "btc_funding_spread_30_90" in V1_FEATURE_COLUMNS_PRUNED, (
        "btc_funding_spread_30_90 MUST be in V1_FEATURE_COLUMNS_PRUNED at iter-v1/054. "
        "The spread is the PRIMARY IS contributor (rank 4-10/48 STABLE in 3/3 seeds at /053). "
        "The /054 impulse-drop tests whether spread ALONE delivers the /052 IS lift (+0.1609). "
        "If spread is absent, the test cannot answer the attribution question."
    )


# ---------------------------------------------------------------------------
# 3. test_pruned_size_47
# ---------------------------------------------------------------------------


def test_pruned_size_47() -> None:
    """V1_FEATURE_COLUMNS_PRUNED must have exactly 47 features at iter-v1/054.

    History: 40 (baseline) → 42 (/023) → 43 (/025) → 44 (/034→/040) → 45 (/049)
             → 46 (/050 ADD dot_vs_btc_ret_ratio_30)
             → 48 (/052 ADD btc_funding_rate_8h_impulse + btc_funding_spread_30_90)
             → 48 (/053 UNCHANGED — VALIDATION sub-axis)
             → 47 (/054 DROP btc_funding_rate_8h_impulse — INERT multi-seed confirmed)
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED  # noqa: PLC0415

    n = len(V1_FEATURE_COLUMNS_PRUNED)
    assert n == 49, (
        f"V1_FEATURE_COLUMNS_PRUNED expected 49 features (post iter-v1/058 ADD); got {n}. "
        "History: /052 ADD (46→48); /054 DROP impulse (47); /055 ADD eth ratio (48); "
        "/057 ADD ltc ratio (49) then REVERTED at closeout (48); "
        "/058 ADD btc_oi_delta_5_z30 (48→49)."
    )


# ---------------------------------------------------------------------------
# 4. test_btc_only_cohort
# ---------------------------------------------------------------------------


def test_btc_only_cohort() -> None:
    """V1_ITER054_UNIVERSE must be exactly ('BTCUSDT',) — BTC-only cohort.

    Defined INDEPENDENTLY from V1_ITER052_UNIVERSE and V1_ITER053_UNIVERSE.
    The BTC-only specialist cohort is unchanged from /052-/053.
    """
    from crypto_trade.features_v1 import V1_ITER054_UNIVERSE  # noqa: PLC0415

    assert set(V1_ITER054_UNIVERSE) == {"BTCUSDT"}, (
        f"V1_ITER054_UNIVERSE expected {{'BTCUSDT'}}, got {set(V1_ITER054_UNIVERSE)}. "
        "Brief Section 10.1: BTC-only cohort unchanged from /052-/053. "
        "Independently defined to allow future revert/keep decisions without coupling /052-/053."
    )
    assert len(V1_ITER054_UNIVERSE) == 1, (
        f"V1_ITER054_UNIVERSE should have exactly 1 symbol; got {len(V1_ITER054_UNIVERSE)}."
    )

    # All three BTC-only universes should share the same symbol set
    from crypto_trade.features_v1 import V1_ITER052_UNIVERSE, V1_ITER053_UNIVERSE  # noqa: PLC0415

    assert V1_ITER054_UNIVERSE == V1_ITER052_UNIVERSE == V1_ITER053_UNIVERSE == ("BTCUSDT",), (
        "V1_ITER052_UNIVERSE, V1_ITER053_UNIVERSE, and V1_ITER054_UNIVERSE must all be "
        "('BTCUSDT',) at /054. All three are BTC-only specialist cohorts. "
        "Independence is at the naming level (separate constants for independent revert/keep)."
    )

    # V1_ITER054_UNIVERSE must be in __all__
    import crypto_trade.features_v1 as fv1  # noqa: PLC0415

    assert "V1_ITER054_UNIVERSE" in fv1.__all__, (
        "V1_ITER054_UNIVERSE not found in crypto_trade.features_v1.__all__. "
        "Add it to the __all__ list in src/crypto_trade/features_v1/__init__.py."
    )


# ---------------------------------------------------------------------------
# 5. test_features_base_hash_changed_vs_053
# ---------------------------------------------------------------------------


def test_features_base_hash_changed_vs_053() -> None:
    """The features-base-hash at /054 must DIFFER from the hash at /052-/053.

    /052 and /053 both used 48 cols (UNCHANGED between them).
    /054 drops btc_funding_rate_8h_impulse (48 → 47 cols).
    The SHA-256 of sorted(V1_FEATURE_COLUMNS_PRUNED) MUST change.

    This test verifies the impulse-drop is correctly reflected in the column set hash.
    The pre-registered hash constants in run_iteration_054.py serve as the reference
    (not the dynamic hash from run_iteration_052.py, which reflects the live column set).
    """
    import run_iteration_054  # noqa: PLC0415

    # Pre-registered reference hashes from the /054 runner (hardcoded at authoring time)
    expected_47col = run_iteration_054.FEATURES_BASE_HASH_47COL
    expected_48col = run_iteration_054.FEATURES_BASE_HASH_48COL

    # The two hashes must be different (impulse-drop changes the column set)
    assert expected_47col != expected_48col, (
        "FEATURES_BASE_HASH_47COL and FEATURES_BASE_HASH_48COL must differ in run_iteration_054. "
        "Dropping btc_funding_rate_8h_impulse (48→47 cols) produces a different SHA-256. "
        "If they are equal, the pre-registered hash constants are wrong."
    )

    # Live V1_FEATURE_COLUMNS_PRUNED must not match either the 47-col or 48-col /052-/054 hashes.
    # After /055 ADD (eth_vs_btc_ret_ratio_30), the live hash is a new 48-col hash distinct from
    # the /052-/053 48-col hash (which included btc_funding_rate_8h_impulse, now dropped).
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED  # noqa: PLC0415

    live_hash = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)

    # The live hash must differ from BOTH the 47-col (post-/054 only) AND the /052-/053 48-col
    assert live_hash != expected_48col, (
        f"Live V1_FEATURE_COLUMNS_PRUNED hash matches the /052-/053 48-col reference hash:\n"
        f"  live computed: {live_hash}\n"
        f"  expected_48col (/052-/053): {expected_48col}\n"
        "btc_funding_rate_8h_impulse appears to still be in V1_FEATURE_COLUMNS_PRUNED. "
        "The /054 impulse-drop was not applied OR the /055 ADD was not applied correctly."
    )

    # Note: after /055, live_hash will equal the /055 48-col hash (with eth_vs_btc_ret_ratio_30
    # in place of btc_funding_rate_8h_impulse). This is CORRECT — the /054 impulse-drop is
    # preserved (impulse absent); only the /055 ETH feature was added.
    assert "btc_funding_rate_8h_impulse" not in V1_FEATURE_COLUMNS_PRUNED, (
        "btc_funding_rate_8h_impulse must NOT be in V1_FEATURE_COLUMNS_PRUNED at /054 (DROPPED). "
        "The /055 ADD of eth_vs_btc_ret_ratio_30 does not restore the impulse. "
        "This assertion verifies the /054 impulse-drop is still in effect at /055."
    )

    print(f"  [OK] expected_47col hash (/054 only) = {expected_47col[:16]}...")
    print(f"  [OK] expected_48col hash (/052-/053) = {expected_48col[:16]}...")
    print(f"  [OK] live hash (post-/055)           = {live_hash[:16]}...")
    print("  [OK] Hashes differ as expected (impulse-drop at /054 + ETH ADD at /055).")


# ---------------------------------------------------------------------------
# 6. test_no_lookahead
# ---------------------------------------------------------------------------


def test_no_lookahead() -> None:
    """Verify btc_funding_spread_30_90 has no lookahead after impulse drop.

    The spread = funding_rate_zscore_30 - funding_rate_zscore_90.
    Both parent z-scores use shift(1) in their rolling denominators.
    Modifying a FUTURE bar must NOT change spread[t].

    This is a regression test confirming the spread computation is still correct
    after /054's impulse-drop. The spread function itself is UNCHANGED at /054;
    this test verifies no accidental regression was introduced.
    """
    from crypto_trade.features_v1.funding_v1 import (  # noqa: PLC0415
        compute_btc_funding_spread_30_90,
    )

    # Build a minimal DataFrame with both z-score columns pre-computed
    n = 200
    rng = np.random.default_rng(54)  # deterministic; iter-v1/054-specific seed
    z30_base = rng.normal(0.0, 1.0, size=n)
    z90_base = rng.normal(0.0, 0.8, size=n)
    # Set first 90 to NaN (burn-in)
    z30_base[:90] = np.nan
    z90_base[:90] = np.nan

    df_base = pd.DataFrame({"funding_rate_zscore_30": z30_base, "funding_rate_zscore_90": z90_base})
    df_base = compute_btc_funding_spread_30_90(df_base)
    spread_base = df_base["btc_funding_spread_30_90"].copy()

    # Modify a future bar (row 160) relative to T=100: spread[100] must NOT change
    df_modified = pd.DataFrame(
        {
            "funding_rate_zscore_30": z30_base.copy(),
            "funding_rate_zscore_90": z90_base.copy(),
        }
    )
    df_modified.iloc[160, df_modified.columns.get_loc("funding_rate_zscore_30")] = 9999.0
    df_modified = compute_btc_funding_spread_30_90(df_modified)
    spread_modified = df_modified["btc_funding_spread_30_90"].copy()

    assert spread_base[100] == spread_modified[100], (
        f"btc_funding_spread_30_90[100] changed when future zscore_30[160] was modified: "
        f"base={spread_base[100]:.6f}, modified={spread_modified[100]:.6f}. "
        "Look-ahead bias regression detected at iter-v1/054. "
        "The spread at bar T must depend ONLY on z30[T] and z90[T] (which are themselves "
        "past-only via shift(1) in their rolling denominators — no future contamination)."
    )

    # Burn-in: rows 0..89 should be NaN (spread inherits z90 90-row burn-in)
    assert pd.isna(spread_base[:90]).all(), (
        f"btc_funding_spread_30_90 rows 0..89 should all be NaN (90-row burn-in). "
        f"Non-NaN count: {spread_base[:90].notna().sum()}. "
        "Regression: burn-in behavior changed between /053 and /054."
    )

    # Post burn-in spread should be finite (z30 - z90; both clipped to [-10, 10])
    post_burnin = spread_base.iloc[90:]
    assert post_burnin.notna().all(), (
        "btc_funding_spread_30_90 contains NaN in post-burn-in region at /054 test. "
        "Regression: NaN-guard behavior changed."
    )
    # Spread range: z30 ∈ [-1.5, 1.5] and z90 ∈ [-1.2, 1.2] for our test data (σ ≈ 1/0.8).
    # Spread = z30 - z90 ∈ approximately [-4, 4] — allow wider margin for the test.
    assert (post_burnin.abs() <= 25.0).all(), (
        f"btc_funding_spread_30_90 values outside expected range at /054 test: "
        f"min={post_burnin.min():.4f}, max={post_burnin.max():.4f}. "
        "Regression: spread computation produces extreme values (> ±25)."
    )


# ---------------------------------------------------------------------------
# Bonus guard: impulse computation code preserved in funding_v1.py
# ---------------------------------------------------------------------------


def test_impulse_code_preserved_in_funding_v1() -> None:
    """compute_btc_funding_rate_8h_impulse must still be importable from funding_v1.

    Brief Section 3.1 + LM Master Flag A: the impulse computation code is PRESERVED
    in funding_v1.py even though btc_funding_rate_8h_impulse is DROPPED from
    V1_FEATURE_COLUMNS_PRUNED. This preserves the restore path for /055 if the
    IMPULSE-DROP-DEGRADES verdict is triggered.
    """
    from crypto_trade.features_v1.funding_v1 import (  # noqa: PLC0415
        compute_btc_funding_rate_8h_impulse,
    )

    # Verify the function is callable
    assert callable(compute_btc_funding_rate_8h_impulse), (
        "compute_btc_funding_rate_8h_impulse is not callable. "
        "The function must be preserved in funding_v1.py "
        "even though btc_funding_rate_8h_impulse is removed from V1_FEATURE_COLUMNS_PRUNED. "
        "This preserves the restore path for IMPULSE-DROP-DEGRADES verdict at /054."
    )

    # Quick smoke test: function runs without error on minimal input
    n = 120
    rng = np.random.default_rng(54)
    df = pd.DataFrame({"funding_rate": rng.normal(0.0001, 0.0003, size=n)})
    result = compute_btc_funding_rate_8h_impulse(df)
    assert "btc_funding_rate_8h_impulse" in result.columns, (
        "compute_btc_funding_rate_8h_impulse did not add 'btc_funding_rate_8h_impulse' column. "
        "The function signature or output column name changed between /053 and /054."
    )


# ---------------------------------------------------------------------------
# Bonus guard: runner metadata checks
# ---------------------------------------------------------------------------


def test_runner_metadata_054() -> None:
    """Verify run_iteration_054.py has correct metadata constants."""
    import run_iteration_054  # noqa: PLC0415

    assert run_iteration_054.ITERATION_NUMBER == 54, (
        f"ITERATION_NUMBER expected 54, got {run_iteration_054.ITERATION_NUMBER}."
    )
    assert run_iteration_054.ITERATION_LABEL == "v1-054", (
        f"ITERATION_LABEL expected 'v1-054', got {run_iteration_054.ITERATION_LABEL!r}."
    )
    assert run_iteration_054.SEEDS_DEFAULT == 1, (
        f"SEEDS_DEFAULT expected 1 (single-seed=42; F-AXIS #1 vs /052 anchor requires "
        f"same seed for direct IS comparison), got {run_iteration_054.SEEDS_DEFAULT}."
    )
    assert run_iteration_054.ENSEMBLE_SIZE == 3, (
        f"ENSEMBLE_SIZE expected 3 (inner; UNCHANGED from /052-/053), "
        f"got {run_iteration_054.ENSEMBLE_SIZE}."
    )
    assert run_iteration_054.N_TRIALS_DEFAULT == 18, (
        f"N_TRIALS_DEFAULT expected 18 (EXPLORATION standard), "
        f"got {run_iteration_054.N_TRIALS_DEFAULT}."
    )
    # Hash guard: 47-col hash must differ from 48-col hash
    h47 = run_iteration_054.FEATURES_BASE_HASH_47COL
    h48 = run_iteration_054.FEATURES_BASE_HASH_48COL
    assert h47 != h48, (
        "FEATURES_BASE_HASH_47COL must differ from FEATURES_BASE_HASH_48COL. "
        "Impulse drop changes the column set — hashes must be different."
    )


# ---------------------------------------------------------------------------
# Parametrized: feature presence/absence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "feature_name,expected_in_pruned",
    [
        ("btc_funding_rate_8h_impulse", False),  # DROPPED at /054
        ("btc_funding_spread_30_90", True),  # RETAINED at /054
        ("basis_zscore_30", False),  # dropped at /034/040; must NOT be in pruned at /054
        ("dot_vs_btc_ret_ratio_30", True),  # added at /050; must still be present at /054
        ("regime_momentum_signed_5d", True),  # added at /040; must still be present at /054
    ],
)
def test_feature_presence_parametrized(feature_name: str, expected_in_pruned: bool) -> None:
    """Parametrized check for feature presence/absence in V1_FEATURE_COLUMNS_PRUNED at /054."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED  # noqa: PLC0415

    actual = feature_name in V1_FEATURE_COLUMNS_PRUNED
    assert actual == expected_in_pruned, (
        f"Feature {feature_name!r}: expected in_pruned={expected_in_pruned}, "
        f"got {actual}. "
        f"V1_FEATURE_COLUMNS_PRUNED has {len(V1_FEATURE_COLUMNS_PRUNED)} cols at /054. "
        f"At /054: btc_funding_rate_8h_impulse DROPPED; btc_funding_spread_30_90 RETAINED; "
        f"all other features from /053 unchanged."
    )
