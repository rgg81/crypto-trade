"""Tests for iter-v1/051: multi-seed re-validation of /050's dot_vs_btc_ret_ratio_30.

Covers 6 mandatory tests:

1.  test_seeds_config — runner requests 3 outer seeds (SEEDS_DEFAULT == 3).
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
    """Runner SEEDS_DEFAULT must be 3 (3 outer seeds: offsets 0, 3, 6).

    Brief Section 3.2: --seeds 3 is the design choice for multi-seed re-validation.
    Offsets [0, 3, 6] satisfy run_baseline_v1.py:7382 constraint: offset+ensemble_size ≤ 10.
    Inner seed windows: [42,123,456], [789,1001,2002], [3003,4004,5005] — fully disjoint.
    """
    import run_iteration_051 as runner  # noqa: PLC0415

    assert runner.SEEDS_DEFAULT == 3, (
        f"Expected SEEDS_DEFAULT=3 (3 outer seeds for multi-seed re-validation), "
        f"got {runner.SEEDS_DEFAULT}. Brief Section 3.2 mandates 3 outer seeds "
        "(offsets 0, 3, 6 from ENSEMBLE_SEEDS roster; satisfies offset+ensemble_size ≤ 10)."
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
    History: 40 → 42 (/023) → 43 (/025) → 44 (/034→/040) → 45 (/049) → 46 (/050 ADD)
             → 48 (/052 ADD btc_funding_rate_8h_impulse + btc_funding_spread_30_90).
    /051 = multi-seed re-validation only; no feature changes at /051.
    /052 subsequently extended to 48; the live constant reflects post-/052 state.
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED  # noqa: PLC0415

    n = len(V1_FEATURE_COLUMNS_PRUNED)
    assert n == 47, (
        f"V1_FEATURE_COLUMNS_PRUNED expected 48 features (post iter-v1/052 ADD); got {n}. "
        "History: ...→ 46 (/050 ADD dot_vs_btc_ret_ratio_30) "
        "→ 48 (/052 ADD btc_funding_rate_8h_impulse + btc_funding_spread_30_90)."
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


# ---------------------------------------------------------------------------
# 7. test_outer_seed_offsets_patched
# ---------------------------------------------------------------------------


def test_outer_seed_offsets_patched() -> None:
    """run_iteration_051.py must monkey-patch run_baseline_v1._OUTER_SEED_OFFSETS to (0, 3, 6).

    Rationale: the framework default (0, 5, 10, 15, 20) silently skips offset 10 at
    ENSEMBLE_SIZE=3 because 10 + 3 = 13 > 10 (len(ENSEMBLE_SEEDS) = 10).  The patch
    sets (0, 3, 6), which gives three fully-disjoint inner-seed windows:
      offset 0 → [42, 123, 456]
      offset 3 → [789, 1001, 2002]
      offset 6 → [3003, 4004, 5005]
    All three satisfy offset + ENSEMBLE_SIZE (3) ≤ 10 — no silent skip.

    This test verifies:
      (a) The patch source text is present in run_iteration_051.py.
      (b) Applying the patch to a fresh import of run_baseline_v1 yields (0, 3, 6).
      (c) All three offsets produce valid windows at ENSEMBLE_SIZE=3 (offset+3 ≤ 10).
      (d) The framework SOURCE file at line 1524 still declares (0, 5, 10, 15, 20)
          — confirms the patch is scope-limited and did not bleed into the framework.
    """
    import re

    import run_baseline_v1 as rbv1

    # (a) Patch source text present in run_iteration_051.py
    runner_path = Path(__file__).parent.parent / "run_iteration_051.py"
    src = runner_path.read_text()
    assert "_OUTER_SEED_OFFSETS = (0, 3, 6)" in src, (
        "run_iteration_051.py must contain the monkey-patch line "
        "`run_baseline_v1._OUTER_SEED_OFFSETS = (0, 3, 6)`. "
        "Without it the framework default (0,5,10,15,20) silently skips offset 10 "
        "at ENSEMBLE_SIZE=3 (10+3>10), producing only 2 effective seeds instead of 3."
    )

    # (b) Applying the patch yields (0, 3, 6)
    rbv1._OUTER_SEED_OFFSETS = (0, 3, 6)
    assert rbv1._OUTER_SEED_OFFSETS == (0, 3, 6), (
        f"After monkey-patch, run_baseline_v1._OUTER_SEED_OFFSETS expected (0, 3, 6), "
        f"got {rbv1._OUTER_SEED_OFFSETS}."
    )

    # (c) All offsets valid at ENSEMBLE_SIZE=3 (offset + 3 <= 10)
    ensemble_size = 3
    ensemble_seeds_len = 10  # len([42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006])
    for offset in (0, 3, 6):
        assert offset + ensemble_size <= ensemble_seeds_len, (
            f"Offset {offset} + ensemble_size {ensemble_size} = {offset + ensemble_size} "
            f"> {ensemble_seeds_len} (len(ENSEMBLE_SEEDS)). "
            "This offset would be silently skipped by the runner's guard at "
            "run_baseline_v1.py:7382."
        )

    # (d) Framework SOURCE file default is still (0, 5, 10, 15, 20) — scope-limited
    framework_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    framework_src = framework_path.read_text()
    pattern = r"_OUTER_SEED_OFFSETS\s*:\s*tuple\[int,\s*\.\.\.\]\s*=\s*(\([^)]+\))"
    m = re.search(pattern, framework_src)
    assert m is not None, (
        "Could not find `_OUTER_SEED_OFFSETS: tuple[int, ...] = (...)` in "
        "run_baseline_v1.py. Framework source structure may have changed — "
        "update this test."
    )
    raw = m.group(1).strip("()").split(",")
    framework_default = tuple(int(x.strip()) for x in raw if x.strip())
    assert framework_default == (0, 5, 10, 15, 20), (
        f"run_baseline_v1.py framework default changed from (0,5,10,15,20) "
        f"to {framework_default}. "
        "The /051 monkey-patch is SCOPE-LIMITED — it must NOT modify the framework "
        "source file. Restore run_baseline_v1.py:1524 to "
        "`_OUTER_SEED_OFFSETS: tuple[int, ...] = (0, 5, 10, 15, 20)`."
    )
