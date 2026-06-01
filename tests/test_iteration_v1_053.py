"""Tests for iter-v1/053: BTC-only multi-seed re-validation of /052 funding specialist.

Covers 7 mandatory tests:

1.  test_seeds_config — SEEDS_DEFAULT is 3.
2.  test_outer_seed_offsets_patched — runner patches _OUTER_SEED_OFFSETS to (0, 3, 6).
3.  test_btc_only_cohort — V1_ITER053_UNIVERSE is exactly {"BTCUSDT"}.
4.  test_features_in_pruned — both /052 features present in V1_FEATURE_COLUMNS_PRUNED.
5.  test_pruned_size_48 — V1_FEATURE_COLUMNS_PRUNED has exactly 48 features (unchanged from /052).
6.  test_features_base_hash_unchanged_vs_052 — hash at /053 equals hash at /052 (no feature change).
7.  test_no_lookahead — re-verify btc_funding_rate_8h_impulse has no lookahead (same features).
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
# 1. test_seeds_config
# ---------------------------------------------------------------------------


def test_seeds_config() -> None:
    """SEEDS_DEFAULT in run_iteration_053 must be 3 (3 outer seeds for multi-seed validation).

    Brief Section 3.2 mandates --seeds 3 with offsets (0, 3, 6).
    """
    import run_iteration_053  # noqa: PLC0415

    assert run_iteration_053.SEEDS_DEFAULT == 3, (
        f"run_iteration_053.SEEDS_DEFAULT expected 3 (multi-seed mandate from LM Master Rec 3 "
        f"at /052 Phase 4.5), got {run_iteration_053.SEEDS_DEFAULT}. "
        "Brief Section 3.2: --seeds 3 with offsets 0, 3, 6 (disjoint inner-ensemble pools)."
    )
    assert run_iteration_053.ENSEMBLE_SIZE == 3, (
        f"run_iteration_053.ENSEMBLE_SIZE expected 3 (inner ensemble size UNCHANGED from /052), "
        f"got {run_iteration_053.ENSEMBLE_SIZE}. "
        "Offset arithmetic: max(offset)+ENSEMBLE_SIZE = 6+3 = 9 ≤ 10 ✓"
    )
    assert run_iteration_053.N_TRIALS_DEFAULT == 18, (
        f"run_iteration_053.N_TRIALS_DEFAULT expected 18 (EXPLORATION standard), "
        f"got {run_iteration_053.N_TRIALS_DEFAULT}."
    )
    assert run_iteration_053.ITERATION_NUMBER == 53, (
        f"run_iteration_053.ITERATION_NUMBER expected 53, got {run_iteration_053.ITERATION_NUMBER}."
    )
    assert run_iteration_053.ITERATION_LABEL == "v1-053", (
        f"run_iteration_053.ITERATION_LABEL expected 'v1-053', "
        f"got {run_iteration_053.ITERATION_LABEL!r}."
    )


# ---------------------------------------------------------------------------
# 2. test_outer_seed_offsets_patched
# ---------------------------------------------------------------------------


def test_outer_seed_offsets_patched() -> None:
    """Runner must patch run_baseline_v1._OUTER_SEED_OFFSETS to (0, 3, 6).

    The monkey-patch is scope-limited to run_iteration_053.py (per /051 precedent).
    Verifies:
      (a) (0, 3, 6) gives 3 disjoint inner-pool windows with ENSEMBLE_SIZE=3.
      (b) max(offset) + ENSEMBLE_SIZE ≤ 10 (framework constraint at run_baseline_v1.py:7382).
      (c) All pools are disjoint (no seed reuse across outer seeds).
    """
    # The patch value is hardcoded in main() just before run_baseline_v1.main().
    # We verify the contract by reading the source file and checking the assignment.
    import inspect

    import run_iteration_053  # noqa: PLC0415

    source = inspect.getsource(run_iteration_053.main)
    assert "_OUTER_SEED_OFFSETS = (0, 3, 6)" in source, (
        "run_iteration_053.main() must contain "
        "`run_baseline_v1._OUTER_SEED_OFFSETS = (0, 3, 6)` (scope-limited monkey-patch). "
        "This is the key diff vs /052 (single-seed) — /053 runs 3 disjoint outer seeds."
    )

    # (a-c) Verify the arithmetic independently
    offsets = (0, 3, 6)
    ensemble_size = run_iteration_053.ENSEMBLE_SIZE  # must be 3
    all_seeds = [42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006]

    # (b) Constraint: offset + ensemble_size ≤ len(all_seeds)
    for offset in offsets:
        assert offset + ensemble_size <= len(all_seeds), (
            f"Offset {offset} + ENSEMBLE_SIZE {ensemble_size} = {offset + ensemble_size} "
            f"exceeds ENSEMBLE_SEEDS length {len(all_seeds)}. "
            "Framework constraint at run_baseline_v1.py:7382 would cap the outer seeds."
        )

    # (c) Pools are disjoint
    pools = [frozenset(all_seeds[offset : offset + ensemble_size]) for offset in offsets]
    seen: set[int] = set()
    for pool_idx, pool in enumerate(pools):
        overlap = pool & seen
        assert not overlap, (
            f"Outer seed pool {pool_idx} (offset={offsets[pool_idx]}) "
            f"overlaps with earlier pools: {overlap}. "
            "Inner-ensemble pools must be fully disjoint across outer seeds. "
            f"Pools: {[list(p) for p in pools]}"
        )
        seen.update(pool)

    # (a) Verify expected pool members
    assert pools[0] == frozenset([42, 123, 456]), (
        f"offset=0 pool expected {{42, 123, 456}}, got {pools[0]}. "
        "offset=0 must reproduce /052 single-seed=42 result bit-exactly (seed=42 sanity gate)."
    )
    assert pools[1] == frozenset([789, 1001, 2002]), (
        f"offset=3 pool expected {{789, 1001, 2002}}, got {pools[1]}."
    )
    assert pools[2] == frozenset([3003, 4004, 5005]), (
        f"offset=6 pool expected {{3003, 4004, 5005}}, got {pools[2]}."
    )


# ---------------------------------------------------------------------------
# 3. test_btc_only_cohort
# ---------------------------------------------------------------------------


def test_btc_only_cohort() -> None:
    """V1_ITER053_UNIVERSE must be exactly ('BTCUSDT',) — BTC-only cohort.

    Defined INDEPENDENTLY from V1_ITER052_UNIVERSE per LM Master Flag C at /053 Phase 4.5
    (allows independent revert/keep decisions without coupling /052 and /053 constants).
    """
    from crypto_trade.features_v1 import V1_ITER053_UNIVERSE  # noqa: PLC0415

    assert set(V1_ITER053_UNIVERSE) == {"BTCUSDT"}, (
        f"V1_ITER053_UNIVERSE expected {{'BTCUSDT'}}, got {set(V1_ITER053_UNIVERSE)}. "
        "Brief Section 10.1: BTC-only cohort, independently defined from V1_ITER052_UNIVERSE."
    )
    assert len(V1_ITER053_UNIVERSE) == 1, (
        f"V1_ITER053_UNIVERSE should have exactly 1 symbol; got {len(V1_ITER053_UNIVERSE)}."
    )

    # Verify both constants exist and have the same value (separate named constants is the
    # independence requirement per LM Master Flag C — Python may intern identical tuples).
    from crypto_trade.features_v1 import V1_ITER052_UNIVERSE  # noqa: PLC0415

    assert V1_ITER052_UNIVERSE == V1_ITER053_UNIVERSE, (
        "V1_ITER052_UNIVERSE and V1_ITER053_UNIVERSE must both be ('BTCUSDT',) at /053. "
        "Both are BTC-only specialist cohorts. Independence is at the naming level "
        "(LM Master Flag C: separate constants allow future independent revert/keep decisions)."
    )
    # Both must be in __all__ independently
    import crypto_trade.features_v1 as fv1  # noqa: PLC0415

    assert "V1_ITER052_UNIVERSE" in fv1.__all__, "V1_ITER052_UNIVERSE not in __all__."
    assert "V1_ITER053_UNIVERSE" in fv1.__all__, "V1_ITER053_UNIVERSE not in __all__."


# ---------------------------------------------------------------------------
# 4. test_features_in_pruned
# ---------------------------------------------------------------------------


def test_features_in_pruned() -> None:
    """btc_funding_spread_30_90 must be present in V1_FEATURE_COLUMNS_PRUNED.

    iter-v1/052 ADDed both btc_funding_rate_8h_impulse and btc_funding_spread_30_90.
    iter-v1/053 VALIDATION left them both in place.
    iter-v1/054 DROPPED btc_funding_rate_8h_impulse (INERT in 3/3 seeds at /053).
    At current state (post-/054): only btc_funding_spread_30_90 remains from /052.
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED  # noqa: PLC0415

    assert "btc_funding_spread_30_90" in V1_FEATURE_COLUMNS_PRUNED, (
        "btc_funding_spread_30_90 not found in V1_FEATURE_COLUMNS_PRUNED. "
        "This feature was added at /052, retained through /053 and /054."
    )
    # Impulse was present at /052-/053 but DROPPED at /054.
    assert "btc_funding_rate_8h_impulse" not in V1_FEATURE_COLUMNS_PRUNED, (
        "btc_funding_rate_8h_impulse should NOT be in V1_FEATURE_COLUMNS_PRUNED. "
        "It was dropped at iter-v1/054 (INERT confirmed in 3/3 seeds at /053)."
    )


# ---------------------------------------------------------------------------
# 5. test_pruned_size_48
# ---------------------------------------------------------------------------


def test_pruned_size_48() -> None:
    """V1_FEATURE_COLUMNS_PRUNED must have exactly 48 features at iter-v1/053.

    /053 is VALIDATION (no feature changes). The 48-col count is UNCHANGED from /052.

    History: 40 (baseline) → 42 (/023) → 43 (/025) → 44 (/034→/040) → 45 (/049)
             → 46 (/050 ADD dot_vs_btc_ret_ratio_30)
             → 48 (/052 ADD btc_funding_rate_8h_impulse + btc_funding_spread_30_90)
             → 48 (/053 UNCHANGED — VALIDATION sub-axis)
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED  # noqa: PLC0415

    n = len(V1_FEATURE_COLUMNS_PRUNED)
    assert n == 49, (
        f"V1_FEATURE_COLUMNS_PRUNED expected 49 features (post iter-v1/058 ADD); got {n}. "
        "iter-v1/053 was VALIDATION (UNCHANGED at 48 from /052). "
        "/055 added eth (48); /057 added then REVERTED ltc (48); /058 added btc_oi_delta_5_z30 (49). "
        "If n != 49: check /058 ADD was applied."
    )


# ---------------------------------------------------------------------------
# 6. test_features_base_hash_unchanged_vs_052
# ---------------------------------------------------------------------------


def test_features_base_hash_unchanged_vs_052() -> None:
    """The features-base-hash at /053 must equal the hash at /052 (no feature change).

    Both runners compute SHA-256 of sorted(V1_FEATURE_COLUMNS_PRUNED). Since /053 makes
    no feature changes, the hashes must be identical. This test imports both runners and
    compares FEATURES_BASE_HASH_EXPECTED from each.
    """
    import run_iteration_052  # noqa: PLC0415
    import run_iteration_053  # noqa: PLC0415

    hash_052 = run_iteration_052.FEATURES_BASE_HASH_EXPECTED
    hash_053 = run_iteration_053.FEATURES_BASE_HASH_EXPECTED
    assert hash_053 == hash_052, (
        f"Features-base-hash CHANGED between /052 and /053:\n"
        f"  /052 hash: {hash_052}\n"
        f"  /053 hash: {hash_053}\n"
        "iter-v1/053 is VALIDATION — no feature changes allowed. "
        "V1_FEATURE_COLUMNS_PRUNED must be 48 cols in both runners (UNCHANGED). "
        "If hashes differ, check that no feature was added/removed between /052 and /053."
    )

    # Also verify the hash matches the live V1_FEATURE_COLUMNS_PRUNED
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED  # noqa: PLC0415

    live_hash = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    assert live_hash == run_iteration_053.FEATURES_BASE_HASH_EXPECTED, (
        f"Live V1_FEATURE_COLUMNS_PRUNED hash does not match /053 pre-registered hash.\n"
        f"  pre-registered: {run_iteration_053.FEATURES_BASE_HASH_EXPECTED}\n"
        f"  live computed : {live_hash}\n"
        "This means V1_FEATURE_COLUMNS_PRUNED was modified after /053 runner was written. "
        "DO NOT modify V1_FEATURE_COLUMNS_PRUNED between /052 and /053 closeout."
    )


# ---------------------------------------------------------------------------
# 7. test_no_lookahead
# ---------------------------------------------------------------------------


def test_no_lookahead() -> None:
    """Re-verify btc_funding_rate_8h_impulse has no lookahead at /053.

    Same features as /052 — this is a regression test confirming the feature
    computation is still correct after any potential code changes between iterations.

    The impulse is: diff(funding_rate)[t] / rolling(90).std(diff(funding_rate))[t]
    Both diff()[t] and the rolling std ending at bar t use only past-known data at bar t.
    Modifying a FUTURE bar must NOT change impulse[t].
    """
    from crypto_trade.features_v1.funding_v1 import (
        compute_btc_funding_rate_8h_impulse,  # noqa: PLC0415
    )

    n = 200
    rng = np.random.default_rng(53)  # deterministic; iter-v1/053-specific seed
    funding_rate = rng.normal(0.0001, 0.0003, size=n)

    df_base = pd.DataFrame({"funding_rate": funding_rate})
    df_base = compute_btc_funding_rate_8h_impulse(df_base)
    impulse_base = df_base["btc_funding_rate_8h_impulse"].copy()

    # Modify a future bar (row 160) relative to T=100; impulse[100] must NOT change
    df_modified = pd.DataFrame({"funding_rate": funding_rate.copy()})
    df_modified.loc[160, "funding_rate"] = 9999.0  # extreme modification of future bar
    df_modified = compute_btc_funding_rate_8h_impulse(df_modified)
    impulse_modified = df_modified["btc_funding_rate_8h_impulse"].copy()

    assert impulse_base[100] == impulse_modified[100], (
        f"btc_funding_rate_8h_impulse[100] changed when future rate[160] was modified: "
        f"base={impulse_base[100]:.6f}, modified={impulse_modified[100]:.6f}. "
        "Look-ahead bias regression detected at iter-v1/053. "
        "The impulse at bar T must depend ONLY on funding_rate[T] and earlier — "
        "never on future bars."
    )

    # Burn-in: rows 0..89 should be NaN (90-row rolling window)
    assert pd.isna(impulse_base[:90]).all(), (
        f"btc_funding_rate_8h_impulse rows 0..89 should all be NaN (90-row burn-in). "
        f"Non-NaN count: {impulse_base[:90].notna().sum()}. "
        "Regression: burn-in behavior changed between /052 and /053."
    )

    # Clipping: all post-burn-in values must be within [-10, +10]
    post_burnin = impulse_base.iloc[90:]
    assert post_burnin.notna().all(), (
        "btc_funding_rate_8h_impulse contains NaN in post-burn-in region at /053 test. "
        "Regression: NaN-guard behavior changed."
    )
    assert (post_burnin.abs() <= 10.0 + 1e-9).all(), (
        f"btc_funding_rate_8h_impulse values outside clip range [-10, +10] at /053 test: "
        f"min={post_burnin.min():.4f}, max={post_burnin.max():.4f}. "
        "Regression: clip behavior changed."
    )


# ---------------------------------------------------------------------------
# Bonus guard: V1_ITER053_UNIVERSE in __all__
# ---------------------------------------------------------------------------


def test_v1_iter053_universe_exported() -> None:
    """V1_ITER053_UNIVERSE must appear in crypto_trade.features_v1.__all__."""
    import crypto_trade.features_v1 as fv1  # noqa: PLC0415

    assert "V1_ITER053_UNIVERSE" in fv1.__all__, (
        "V1_ITER053_UNIVERSE not found in crypto_trade.features_v1.__all__. "
        "Add it to the __all__ list in src/crypto_trade/features_v1/__init__.py "
        "(per LM Master Flag C: separate constant from V1_ITER052_UNIVERSE)."
    )
    assert hasattr(fv1, "V1_ITER053_UNIVERSE"), (
        "V1_ITER053_UNIVERSE is in __all__ but not accessible as an attribute. "
        "Check src/crypto_trade/features_v1/__init__.py for typo in constant definition."
    )


# ---------------------------------------------------------------------------
# Bonus guard: dispatch block exists in run_baseline_v1
# ---------------------------------------------------------------------------


def test_dispatch_block_exists_in_runner() -> None:
    """run_baseline_v1.py must contain a 'v1-053' dispatch block.

    The runner's per-iteration dispatch uses `iteration_label == 'v1-053'` to
    route to the BTC multi-seed re-validation block. Without it, run_iteration_053.py
    would fall through to the wrong dispatch or raise an error.
    """
    import pathlib

    runner_path = pathlib.Path(__file__).parent.parent / "run_baseline_v1.py"
    assert runner_path.exists(), (
        f"run_baseline_v1.py not found at {runner_path}. "
        "Expected at repo root alongside run_iteration_053.py."
    )
    source = runner_path.read_text(encoding="utf-8")
    assert '"v1-053"' in source or "'v1-053'" in source, (
        "run_baseline_v1.py does not contain a 'v1-053' dispatch block. "
        "Add the dispatch block per brief Section 10.3 and the /051/052 template pattern."
    )
    assert "V1_ITER053_UNIVERSE" in source, (
        "run_baseline_v1.py does not reference V1_ITER053_UNIVERSE. "
        "The dispatch block must import and use V1_ITER053_UNIVERSE for cohort assertion."
    )

    # Verify the offset patch comment is in the runner
    assert "_OUTER_SEED_OFFSETS = (0, 3, 6)" in (
        pathlib.Path(__file__).parent.parent / "run_iteration_053.py"
    ).read_text(encoding="utf-8"), (
        "run_iteration_053.py does not contain "
        "`run_baseline_v1._OUTER_SEED_OFFSETS = (0, 3, 6)`. "
        "The offset patch is mandatory for /053 multi-seed run."
    )


# ---------------------------------------------------------------------------
# Parametrized: verify pytest does not need real data for structural tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "feature_name,expected_in_pruned",
    [
        # Impulse was in pruned at /053 but DROPPED at /054 (INERT in 3/3 seeds)
        ("btc_funding_rate_8h_impulse", False),
        ("btc_funding_spread_30_90", True),  # retained through /054
        ("basis_zscore_30", False),  # dropped at /034/040; must NOT be in pruned
    ],
)
def test_feature_presence_parametrized(feature_name: str, expected_in_pruned: bool) -> None:
    """Parametrized check for feature presence/absence in V1_FEATURE_COLUMNS_PRUNED at /053."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED  # noqa: PLC0415

    actual = feature_name in V1_FEATURE_COLUMNS_PRUNED
    assert actual == expected_in_pruned, (
        f"Feature {feature_name!r}: expected in_pruned={expected_in_pruned}, "
        f"got {actual}. "
        f"V1_FEATURE_COLUMNS_PRUNED has {len(V1_FEATURE_COLUMNS_PRUNED)} cols at /053."
    )
