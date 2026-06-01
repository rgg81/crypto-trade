"""Tests for iter-v1/051: multi-seed re-validation of /050's dot_vs_btc_ret_ratio_30.

Covers 6 mandatory tests:

1.  test_seeds_config — runner requests 4 outer seeds (SEEDS_DEFAULT == 4).
2.  test_no_regime_gate — dispatch block has NO vol-spike regime gate logic.
3.  test_dot_only_cohort — V1_ITER051_UNIVERSE is exactly {"DOTUSDT"}.
4.  test_feature_in_pruned — dot_vs_btc_ret_ratio_30 present in V1_FEATURE_COLUMNS_PRUNED.
5.  test_pruned_size_46 — V1_FEATURE_COLUMNS_PRUNED has exactly 46 features (unchanged from /050).
6.  test_features_base_hash_unchanged_vs_050 — /051 hash equals /050 hash (same feature set).
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """SHA-256 of sorted feature column names — deterministic."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# 1. test_seeds_config
# ---------------------------------------------------------------------------


def test_seeds_config() -> None:
    """Runner SEEDS_DEFAULT must be 4 (4 outer seeds: offsets 0, 5, 10, 15).

    Brief Section 3.2: --seeds 4 is the design choice for multi-seed re-validation
    (outer seeds at ENSEMBLE_SEEDS offsets 0, 5, 10, 15).
    """
    import run_iteration_051 as runner  # noqa: PLC0415

    assert runner.SEEDS_DEFAULT == 4, (
        f"Expected SEEDS_DEFAULT=4 (4 outer seeds for multi-seed re-validation), "
        f"got {runner.SEEDS_DEFAULT}. Brief Section 3.2 mandates 4 outer seeds "
        "(offsets 0, 5, 10, 15 from ENSEMBLE_SEEDS roster)."
    )


# ---------------------------------------------------------------------------
# 2. test_no_regime_gate
# ---------------------------------------------------------------------------


def test_no_regime_gate() -> None:
    """The iter-v1/051 dispatch block in run_baseline_v1.py must NOT contain
    vol-spike regime gate logic (dropped — was 0%% fire rate / INERT at /050).

    Checks that the AST of run_baseline_v1.py's v1-051 dispatch block does NOT
    reference _apply_vol_spike_gate or _btc_vol_q75 or _regime_gate_conf_threshold_050
    identifiers within the v1-051 elif branch.

    Static analysis: we search the source text of run_baseline_v1.py for the
    iter-v1/051 dispatch section and verify it does not contain regime-gate identifiers.
    """
    runner_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    assert runner_path.exists(), f"run_baseline_v1.py not found at {runner_path}"

    src = runner_path.read_text()

    # Find the v1-051 dispatch section bounds
    start_marker = 'iteration_label == "v1-051"'
    # The section ends at the next top-level elif (v1-044 or similar)
    end_marker = 'iteration_label == "v1-044"'

    start_idx = src.find(start_marker)
    assert start_idx != -1, (
        f"iter-v1/051 dispatch block not found in run_baseline_v1.py. "
        f"Expected marker: {start_marker!r}"
    )

    end_idx = src.find(end_marker, start_idx)
    assert end_idx != -1, (
        f"Could not find end marker {end_marker!r} after iter-v1/051 dispatch block."
    )

    dispatch_section = src[start_idx:end_idx]

    # These identifiers must NOT appear in the /051 dispatch block
    forbidden_identifiers = [
        "_apply_vol_spike_gate",
        "_btc_vol_q75",
        "_regime_gate_conf_threshold",
        "vol_spike_regime",
        "_gate_disabled",
        "_btc_vol_050",
        "_is_vols_050",
    ]
    for ident in forbidden_identifiers:
        assert ident not in dispatch_section, (
            f"iter-v1/051 dispatch block contains regime-gate identifier {ident!r}. "
            "The vol-spike regime gate must be DROPPED at /051 (was 0%% fire rate / "
            "INERT at /050; brief Section 3.1 mandates removal)."
        )


# ---------------------------------------------------------------------------
# 3. test_dot_only_cohort
# ---------------------------------------------------------------------------


def test_dot_only_cohort() -> None:
    """V1_ITER051_UNIVERSE must be exactly ('DOTUSDT',) — DOT-only cohort."""
    from crypto_trade.features_v1 import V1_ITER051_UNIVERSE  # noqa: PLC0415

    assert set(V1_ITER051_UNIVERSE) == {"DOTUSDT"}, (
        f"V1_ITER051_UNIVERSE expected {{'DOTUSDT'}}, got {set(V1_ITER051_UNIVERSE)}. "
        "Brief Section 0: DOT-only cohort unchanged from /050."
    )
    assert len(V1_ITER051_UNIVERSE) == 1, (
        f"V1_ITER051_UNIVERSE should have exactly 1 symbol; got {len(V1_ITER051_UNIVERSE)}."
    )


# ---------------------------------------------------------------------------
# 4. test_feature_in_pruned
# ---------------------------------------------------------------------------


def test_feature_in_pruned() -> None:
    """dot_vs_btc_ret_ratio_30 must be present in V1_FEATURE_COLUMNS_PRUNED.

    Feature was added at /050 and is RETAINED at /051 (no feature changes).
    Brief Section 3: V1_FEATURE_COLUMNS_PRUNED (46 cols) unchanged.
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED  # noqa: PLC0415

    assert "dot_vs_btc_ret_ratio_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "dot_vs_btc_ret_ratio_30 not found in V1_FEATURE_COLUMNS_PRUNED. "
        "Feature was added at iter-v1/050 and must be retained at /051 (multi-seed "
        "re-validation). If verdict = LOTTERY-CONFIRMED-NEGATIVE after /051 backtest, "
        "REVERT in the closeout commit — but NOT before the backtest runs."
    )


# ---------------------------------------------------------------------------
# 5. test_pruned_size_46
# ---------------------------------------------------------------------------


def test_pruned_size_46() -> None:
    """V1_FEATURE_COLUMNS_PRUNED must have exactly 46 features (unchanged from /050).

    Brief Section 3: no V1_FEATURE_COLUMNS_PRUNED change at /051.
    History: 40 (baseline) → 42 (/023) → 43 (/025) → 44 (/034→/040) → 45 (/049) → 46 (/050 ADD).
    /051 = multi-seed re-validation only; feature count must remain 46.
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED  # noqa: PLC0415

    n = len(V1_FEATURE_COLUMNS_PRUNED)
    assert n == 46, (
        f"V1_FEATURE_COLUMNS_PRUNED expected 46 features (unchanged from /050); got {n}. "
        "iter-v1/051 must NOT change the feature column count — it is a seed-validation "
        "iteration only. History: ...→ 45 (/049) → 46 (/050 ADD dot_vs_btc_ret_ratio_30)."
    )


# ---------------------------------------------------------------------------
# 6. test_features_base_hash_unchanged_vs_050
# ---------------------------------------------------------------------------


def test_features_base_hash_unchanged_vs_050() -> None:
    """The features-base-hash in run_iteration_051.py must equal the hash in
    run_iteration_050.py (both use the same V1_FEATURE_COLUMNS_PRUNED 46-col set).

    This confirms that no inadvertent feature column change occurred between
    /050 and /051 dispatch wiring.
    """
    # Dynamic import to avoid side-effects from hash computation at module level.
    spec_050 = importlib.util.spec_from_file_location(
        "run_iteration_050",
        Path(__file__).parent.parent / "run_iteration_050.py",
    )
    assert spec_050 is not None, "Cannot locate run_iteration_050.py"
    mod_050 = importlib.util.module_from_spec(spec_050)
    spec_050.loader.exec_module(mod_050)  # type: ignore[union-attr]

    spec_051 = importlib.util.spec_from_file_location(
        "run_iteration_051",
        Path(__file__).parent.parent / "run_iteration_051.py",
    )
    assert spec_051 is not None, "Cannot locate run_iteration_051.py"
    mod_051 = importlib.util.module_from_spec(spec_051)
    spec_051.loader.exec_module(mod_051)  # type: ignore[union-attr]

    hash_050 = mod_050.FEATURES_BASE_HASH_EXPECTED
    hash_051 = mod_051.FEATURES_BASE_HASH_EXPECTED

    assert hash_050 == hash_051, (
        f"Features-base-hash MISMATCH between /050 and /051:\n"
        f"  /050 hash: {hash_050}\n"
        f"  /051 hash: {hash_051}\n"
        "V1_FEATURE_COLUMNS_PRUNED should be identical (46 cols) at both iterations. "
        "iter-v1/051 is a multi-seed re-validation — no feature changes allowed."
    )

    # Also verify both hashes are non-empty and look like SHA-256
    for label, h in (("050", hash_050), ("051", hash_051)):
        assert len(h) == 64, (
            f"/{label} features-base-hash has unexpected length {len(h)} (expected 64 hex chars)."
        )
        assert all(c in "0123456789abcdef" for c in h), (
            f"/{label} features-base-hash contains non-hex characters: {h!r}"
        )
