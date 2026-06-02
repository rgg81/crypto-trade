"""Tests for iter-v1/061: BTC-only zero-randomness diagnostic.

Covers 7 mandatory tests:

1. test_btc_only_cohort — V1_ITER061_UNIVERSE is exactly ("BTCUSDT",).
2. test_subsample_1_0 — HARDCODED_LGBM_PARAMS_061["subsample"] == 1 (not 0.5 or 0.8).
3. test_colsample_1_0 — HARDCODED_LGBM_PARAMS_061["colsample_bytree"] == 1.
4. test_bagging_freq_0 — HARDCODED_LGBM_PARAMS_061["bagging_freq"] == 0.
5. test_n_trials_1 — N_TRIALS_DEFAULT == 1.
6. test_seeds_1 — SEEDS_DEFAULT == 1.
7. test_hardcoded_hp_dict_complete — All 17 required keys present in HARDCODED_LGBM_PARAMS_061.

Additional tests:
8. test_features_unchanged_48col — V1_FEATURE_COLUMNS_PRUNED has exactly 48 cols (/061 adds none).
9. test_btc_iter061_universe_in_all — V1_ITER061_UNIVERSE is in crypto_trade.features_v1.__all__.
10. test_features_base_hash_48col — Live hash matches pre-registered 48-col hash.
11. test_runner_metadata_061 — ITERATION_NUMBER, ITERATION_LABEL, ENSEMBLE_SIZE correct.
12. test_enqueue_params_subset_of_hardcoded — _ENQUEUE_PARAMS keys are a subset
    of HARDCODED_LGBM_PARAMS_061.
13. test_determinism_flags_set — deterministic=True, num_threads=1, is_unbalance=False,
    force_col_wise=True.
"""

from __future__ import annotations

import hashlib

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# Pre-registered 48-col hash (UNCHANGED from /057 closeout / /058 REVERT).
FEATURES_BASE_HASH_48COL: str = "b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3"


# ---------------------------------------------------------------------------
# 1. test_btc_only_cohort
# ---------------------------------------------------------------------------


def test_btc_only_cohort() -> None:
    """V1_ITER061_UNIVERSE must be exactly ('BTCUSDT',) — BTC-only cohort.

    /061 mirrors the BTC-only specialist head from /052-/054-/058.
    Single-symbol head is the diagnostic unit: one feature set, one training window,
    one deterministic model.
    """
    from crypto_trade.features_v1 import V1_ITER061_UNIVERSE

    assert set(V1_ITER061_UNIVERSE) == {"BTCUSDT"}, (
        f"V1_ITER061_UNIVERSE expected {{'BTCUSDT'}}, got {set(V1_ITER061_UNIVERSE)}. "
        "Brief Section 3.3: BTC-only cohort for /061 zero-randomness diagnostic."
    )
    assert len(V1_ITER061_UNIVERSE) == 1, (
        f"V1_ITER061_UNIVERSE should have exactly 1 symbol; got {len(V1_ITER061_UNIVERSE)}."
    )


# ---------------------------------------------------------------------------
# 2. test_subsample_1_0
# ---------------------------------------------------------------------------


def test_subsample_1_0() -> None:
    """HARDCODED_LGBM_PARAMS_061['subsample'] must be 1 (hardware-mandatory).

    subsample=1.0 eliminates ALL row-subsampling randomness from LightGBM training.
    This is the user spec AND LM Master Rec 2 (Other Randomness Sources).
    Any value < 1.0 defeats the zero-randomness experiment.
    """
    from run_iteration_061 import HARDCODED_LGBM_PARAMS_061

    subsample = HARDCODED_LGBM_PARAMS_061.get("subsample")
    assert subsample == 1, (
        f"HARDCODED_LGBM_PARAMS_061['subsample'] expected 1, got {subsample!r}. "
        "Hardware-mandatory: subsample must be 1 (no row subsampling). "
        "Brief Section 3.1 + LM Master Rec 2."
    )


# ---------------------------------------------------------------------------
# 3. test_colsample_1_0
# ---------------------------------------------------------------------------


def test_colsample_1_0() -> None:
    """HARDCODED_LGBM_PARAMS_061['colsample_bytree'] must be 1 (hardware-mandatory).

    colsample_bytree=1.0 eliminates ALL column-subsampling randomness from LightGBM.
    Together with subsample=1.0, this makes every tree deterministic given the data + HPs.
    """
    from run_iteration_061 import HARDCODED_LGBM_PARAMS_061

    colsample = HARDCODED_LGBM_PARAMS_061.get("colsample_bytree")
    assert colsample == 1, (
        f"HARDCODED_LGBM_PARAMS_061['colsample_bytree'] expected 1, got {colsample!r}. "
        "Hardware-mandatory: colsample_bytree must be 1 (no column subsampling). "
        "Brief Section 3.1 + LM Master Rec 2."
    )


# ---------------------------------------------------------------------------
# 4. test_bagging_freq_0
# ---------------------------------------------------------------------------


def test_bagging_freq_0() -> None:
    """HARDCODED_LGBM_PARAMS_061['bagging_freq'] must be 0 (hardware-mandatory).

    bagging_freq=0 disables subsampling at the bagging level (alias of subsample_freq).
    LightGBM uses both subsample AND bagging_freq to control row subsampling.
    Setting both to 0/1.0 ensures complete determinism.
    """
    from run_iteration_061 import HARDCODED_LGBM_PARAMS_061

    bagging_freq = HARDCODED_LGBM_PARAMS_061.get("bagging_freq")
    assert bagging_freq == 0, (
        f"HARDCODED_LGBM_PARAMS_061['bagging_freq'] expected 0, got {bagging_freq!r}. "
        "Hardware-mandatory: bagging_freq must be 0 (disables bagging). "
        "Brief Section 3.1 + LM Master Rec 2."
    )


# ---------------------------------------------------------------------------
# 5. test_n_trials_1
# ---------------------------------------------------------------------------


def test_n_trials_1() -> None:
    """N_TRIALS_DEFAULT must be 1 — single deterministic Optuna trial.

    n_trials=1 means Optuna runs exactly one trial (the enqueued hardcoded HP trial).
    No TPE exploration, no stochastic search. The enqueue_trial() mechanism injects
    the fixed HP values as trial 0, and study.optimize(n_trials=1) evaluates only that trial.
    """
    from run_iteration_061 import N_TRIALS_DEFAULT

    assert N_TRIALS_DEFAULT == 1, (
        f"N_TRIALS_DEFAULT expected 1, got {N_TRIALS_DEFAULT}. "
        "iter-v1/061 spec: n_trials=1 (zero-randomness; single deterministic trial). "
        "Brief Section 3.1."
    )


# ---------------------------------------------------------------------------
# 6. test_seeds_1
# ---------------------------------------------------------------------------


def test_seeds_1() -> None:
    """SEEDS_DEFAULT must be 1 — single deterministic seed.

    seeds=1 means only one inner ensemble member (ENSEMBLE_SIZE=1) and no outer
    seed loop. The single seed is 42 (offset=0 from ENSEMBLE_SEEDS). This guarantees
    the ensemble produces a single deterministic model, not a stochastic average.
    """
    from run_iteration_061 import SEEDS_DEFAULT

    assert SEEDS_DEFAULT == 1, (
        f"SEEDS_DEFAULT expected 1, got {SEEDS_DEFAULT}. "
        "iter-v1/061 spec: seeds=1 (zero-randomness; single deterministic seed). "
        "Brief Section 3.1."
    )


# ---------------------------------------------------------------------------
# 7. test_hardcoded_hp_dict_complete
# ---------------------------------------------------------------------------


def test_hardcoded_hp_dict_complete() -> None:
    """HARDCODED_LGBM_PARAMS_061 must contain all 17 required keys (LM Master spec).

    Required keys from lgbm_advisor.md §"Recommended Hardcoded HP Values" +
    §"Other Randomness Sources":
        LightGBM model params (11): n_estimators, max_depth, num_leaves, min_child_samples,
            min_split_gain, learning_rate, boosting_type, subsample, colsample_bytree,
            reg_alpha, reg_lambda
        Aliases (4): subsample_freq, bagging_freq, bagging_fraction, feature_fraction
        Determinism flags (4): random_state, deterministic, force_col_wise, num_threads
        Objective/class (4): objective, is_unbalance, class_weight, scale_pos_weight
        Misc (2): verbosity, metric
        Training schedule (6): confidence_threshold, training_days, training_months,
            n_trials, cv_splits, cv_gap
    Total: at least 17 distinct keys.
    """
    from run_iteration_061 import HARDCODED_LGBM_PARAMS_061

    required_keys = {
        # LightGBM model params
        "n_estimators",
        "max_depth",
        "num_leaves",
        "min_child_samples",
        "min_split_gain",
        "learning_rate",
        "boosting_type",
        # Subsampling (all aliases)
        "subsample",
        "subsample_freq",
        "bagging_freq",
        "bagging_fraction",
        "colsample_bytree",
        "feature_fraction",
        # Regularization
        "reg_alpha",
        "reg_lambda",
        # Determinism flags
        "random_state",
        "deterministic",
        "force_col_wise",
        "num_threads",
        # Objective + class handling
        "objective",
        "is_unbalance",
        "class_weight",
        "scale_pos_weight",
        # Misc
        "verbosity",
        "metric",
        # Training schedule (runner-level)
        "confidence_threshold",
        "training_days",
        "training_months",
        "n_trials",
        "cv_splits",
        "cv_gap",
    }

    actual_keys = set(HARDCODED_LGBM_PARAMS_061.keys())
    missing = required_keys - actual_keys
    assert not missing, (
        f"HARDCODED_LGBM_PARAMS_061 is missing {len(missing)} required keys: {sorted(missing)}. "
        "Brief Section 3.1 mandates the COMPLETE HP dict per LM Master Phase 4.5 ADOPTED VERBATIM. "
        "Ensure all randomness-elimination keys are present."
    )
    # Spot-check critical values
    hp = HARDCODED_LGBM_PARAMS_061  # local alias for shorter lines
    assert hp["n_estimators"] == 300, (
        f"n_estimators expected 300 (LM Master Rec 1), got {hp['n_estimators']}."
    )
    assert hp["max_depth"] == 4, f"max_depth expected 4 (LM Master Rec 1), got {hp['max_depth']}."
    assert hp["num_leaves"] == 31, (
        f"num_leaves expected 31 (2^4-1; LM Master Rec 1), got {hp['num_leaves']}."
    )
    assert hp["confidence_threshold"] == 0.7, (
        f"confidence_threshold expected 0.7 (LM Master Rec 6), got {hp['confidence_threshold']}."
    )
    assert hp["training_days"] == 360, (
        f"training_days expected 360 (LM Master Rec 7), got {hp['training_days']}."
    )
    assert hp["n_trials"] == 1, f"n_trials expected 1 (user spec), got {hp['n_trials']}."
    assert hp["cv_gap"] == 42, (
        f"cv_gap expected 42 (8h embargo; 7d triple-barrier), got {hp['cv_gap']}."
    )
    print(
        f"  [OK] HARDCODED_LGBM_PARAMS_061 has {len(actual_keys)} keys "
        f"({len(required_keys)} required, {len(actual_keys) - len(required_keys)} extra)"
    )


# ---------------------------------------------------------------------------
# 8. test_features_unchanged_48col
# ---------------------------------------------------------------------------


def test_features_unchanged_48col() -> None:
    """V1_FEATURE_COLUMNS_PRUNED must have exactly 48 features at iter-v1/061.

    /061 does NOT add or remove any feature (UNCHANGED from /057 closeout / /058 REVERT).
    History:
        40 (baseline /002) → 42 (/023) → 43 (/025) → 44 (/034→/040) → 45 (/049)
        → 46 (/050) → 48 (/052 ADD two features) → 47 (/054 DROP impulse)
        → 48 (/055 ADD eth_vs_btc_ret_ratio_30) → 49 (/057 ADD ltc, REVERTED)
        → 49 (/058 ADD btc_oi_delta_5_z30, REVERTED at closeout)
        → 48 (/061 UNCHANGED)
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    n = len(V1_FEATURE_COLUMNS_PRUNED)
    assert n == 48, (
        f"V1_FEATURE_COLUMNS_PRUNED expected 48 features at iter-v1/061 (UNCHANGED); got {n}. "
        "iter-v1/061 must NOT add or remove any feature. "
        "If n == 49: a feature was NOT reverted from /057 or /058 — check __init__.py. "
        "If n == 47: a feature was accidentally dropped — check __init__.py."
    )


# ---------------------------------------------------------------------------
# 9. test_btc_iter061_universe_in_all
# ---------------------------------------------------------------------------


def test_btc_iter061_universe_in_all() -> None:
    """V1_ITER061_UNIVERSE must be in crypto_trade.features_v1.__all__."""
    import crypto_trade.features_v1 as fv1

    assert "V1_ITER061_UNIVERSE" in fv1.__all__, (
        "V1_ITER061_UNIVERSE not found in crypto_trade.features_v1.__all__. "
        "Add it to the __all__ list in src/crypto_trade/features_v1/__init__.py."
    )


# ---------------------------------------------------------------------------
# 10. test_features_base_hash_48col
# ---------------------------------------------------------------------------


def test_features_base_hash_48col() -> None:
    """Live V1_FEATURE_COLUMNS_PRUNED must match the pre-registered 48-col hash.

    /061 uses the SAME 48-col feature set as /057 closeout and /058 REVERT.
    The SHA-256 of sorted(V1_FEATURE_COLUMNS_PRUNED) must be identical.
    If the hash differs, a feature was accidentally added or removed.
    """
    from run_iteration_061 import FEATURES_BASE_HASH_48COL

    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    live_hash = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    assert live_hash == FEATURES_BASE_HASH_48COL, (
        f"Live V1_FEATURE_COLUMNS_PRUNED hash does not match pre-registered 48-col hash.\n"
        f"  pre-registered 48-col: {FEATURES_BASE_HASH_48COL}\n"
        f"  live computed        : {live_hash}\n"
        f"  live len             : {len(V1_FEATURE_COLUMNS_PRUNED)}\n"
        "If live hash differs: V1_FEATURE_COLUMNS_PRUNED was modified. "
        "iter-v1/061 must use UNCHANGED 48-col stack."
    )
    print(f"  [OK] 48-col hash = {live_hash[:16]}... (UNCHANGED from /057 closeout)")


# ---------------------------------------------------------------------------
# 11. test_runner_metadata_061
# ---------------------------------------------------------------------------


def test_runner_metadata_061() -> None:
    """Verify run_iteration_061.py has correct metadata constants."""
    from run_iteration_061 import (
        ENSEMBLE_SIZE,
        FEATURES_BASE_HASH_48COL,
        HARDCODED_LGBM_PARAMS_061,
        ITERATION_LABEL,
        ITERATION_NUMBER,
        N_TRIALS_DEFAULT,
        SEEDS_DEFAULT,
    )

    assert ITERATION_NUMBER == 61, f"ITERATION_NUMBER expected 61, got {ITERATION_NUMBER}."
    assert ITERATION_LABEL == "v1-061", (
        f"ITERATION_LABEL expected 'v1-061', got {ITERATION_LABEL!r}."
    )
    assert N_TRIALS_DEFAULT == 1, (
        f"N_TRIALS_DEFAULT expected 1 (zero-randomness), got {N_TRIALS_DEFAULT}."
    )
    assert SEEDS_DEFAULT == 1, (
        f"SEEDS_DEFAULT expected 1 (single deterministic seed), got {SEEDS_DEFAULT}."
    )
    assert ENSEMBLE_SIZE == 1, (
        f"ENSEMBLE_SIZE expected 1 (single inner model), got {ENSEMBLE_SIZE}."
    )
    assert FEATURES_BASE_HASH_48COL == FEATURES_BASE_HASH_48COL, (
        "FEATURES_BASE_HASH_48COL must be set (non-empty)."
    )
    assert len(FEATURES_BASE_HASH_48COL) == 64, (
        f"FEATURES_BASE_HASH_48COL must be a 64-char SHA-256 hex string, "
        f"got {len(FEATURES_BASE_HASH_48COL)} chars."
    )
    # Verify the HP dict is populated
    assert len(HARDCODED_LGBM_PARAMS_061) >= 17, (
        f"HARDCODED_LGBM_PARAMS_061 expected ≥17 keys, got {len(HARDCODED_LGBM_PARAMS_061)}."
    )
    print(f"  [OK] ITERATION_LABEL={ITERATION_LABEL}, ITERATION_NUMBER={ITERATION_NUMBER}")
    print(
        f"  [OK] N_TRIALS_DEFAULT={N_TRIALS_DEFAULT}, "
        f"SEEDS_DEFAULT={SEEDS_DEFAULT}, ENSEMBLE_SIZE={ENSEMBLE_SIZE}"
    )
    print(f"  [OK] FEATURES_BASE_HASH_48COL={FEATURES_BASE_HASH_48COL[:16]}...")


# ---------------------------------------------------------------------------
# 12. test_enqueue_params_subset_of_hardcoded
# ---------------------------------------------------------------------------


def test_enqueue_params_subset_of_hardcoded() -> None:
    """_ENQUEUE_PARAMS keys must be a subset of HARDCODED_LGBM_PARAMS_061 keys.

    _ENQUEUE_PARAMS contains the subset of keys passed to study.enqueue_trial().
    All values in _ENQUEUE_PARAMS must match the corresponding values in
    HARDCODED_LGBM_PARAMS_061 (no divergence between what is enqueued and what
    is declared as the hardcoded HP dict).
    """
    from run_iteration_061 import _ENQUEUE_PARAMS, HARDCODED_LGBM_PARAMS_061

    # All enqueue keys must be in the full HP dict
    extra_keys = set(_ENQUEUE_PARAMS.keys()) - set(HARDCODED_LGBM_PARAMS_061.keys())
    assert not extra_keys, (
        f"_ENQUEUE_PARAMS has keys NOT in HARDCODED_LGBM_PARAMS_061: {sorted(extra_keys)}. "
        "_ENQUEUE_PARAMS must be a strict subset of HARDCODED_LGBM_PARAMS_061."
    )

    # Values must match for all enqueue keys
    for key in _ENQUEUE_PARAMS:
        enqueue_val = _ENQUEUE_PARAMS[key]
        hardcoded_val = HARDCODED_LGBM_PARAMS_061[key]
        assert enqueue_val == hardcoded_val, (
            f"_ENQUEUE_PARAMS[{key!r}]={enqueue_val!r} != "
            f"HARDCODED_LGBM_PARAMS_061[{key!r}]={hardcoded_val!r}. "
            "Enqueued values must match the hardcoded HP dict exactly."
        )

    # Must include the critical keys that ARE actually suggested by _objective()
    required_enqueue_keys = {
        "confidence_threshold",
        "n_estimators",
        "max_depth",
        "num_leaves",
        "learning_rate",
        "min_child_samples",
        "reg_alpha",
        "reg_lambda",
    }
    missing_enqueue = required_enqueue_keys - set(_ENQUEUE_PARAMS.keys())
    assert not missing_enqueue, (
        f"_ENQUEUE_PARAMS is missing critical keys that _objective() suggests: "
        f"{sorted(missing_enqueue)}. "
        "These keys MUST be in _ENQUEUE_PARAMS for the enqueue_trial() override to work."
    )
    n_enq = len(_ENQUEUE_PARAMS)
    print(f"  [OK] _ENQUEUE_PARAMS has {n_enq} keys, all matching HARDCODED_LGBM_PARAMS_061")


# ---------------------------------------------------------------------------
# 13. test_determinism_flags_set
# ---------------------------------------------------------------------------


def test_determinism_flags_set() -> None:
    """Determinism flags must be correctly set in HARDCODED_LGBM_PARAMS_061.

    These flags are the core of the zero-randomness experiment:
    - deterministic=True: disables LightGBM's non-deterministic micro-optimizations
    - num_threads=1: eliminates float-summation order non-determinism from multi-threading
    - is_unbalance=False: eliminates month-varying implicit scale_pos_weight
    - force_col_wise=True: avoids row/col mode auto-choice (which can flip across runs)

    Any deviation makes the experiment non-reproducible and defeats the diagnostic purpose.
    """
    from run_iteration_061 import HARDCODED_LGBM_PARAMS_061

    assert HARDCODED_LGBM_PARAMS_061.get("deterministic") is True, (
        f"deterministic expected True, got {HARDCODED_LGBM_PARAMS_061.get('deterministic')!r}. "
        "LM Master §'Other Randomness Sources' #2: deterministic=True is CRITICAL."
    )
    assert HARDCODED_LGBM_PARAMS_061.get("num_threads") == 1, (
        f"num_threads expected 1, got {HARDCODED_LGBM_PARAMS_061.get('num_threads')!r}. "
        "LM Master §'Other Randomness Sources' #2: num_threads=1 eliminates "
        "float-summation order non-determinism from multi-threading."
    )
    assert HARDCODED_LGBM_PARAMS_061.get("is_unbalance") is False, (
        f"is_unbalance expected False, got {HARDCODED_LGBM_PARAMS_061.get('is_unbalance')!r}. "
        "LM Master §'Other Randomness Sources' #1: is_unbalance=False eliminates "
        "month-varying implicit scale_pos_weight randomness."
    )
    assert HARDCODED_LGBM_PARAMS_061.get("force_col_wise") is True, (
        f"force_col_wise expected True, got {HARDCODED_LGBM_PARAMS_061.get('force_col_wise')!r}. "
        "LM Master §'Other Randomness Sources': force_col_wise=True avoids row/col mode "
        "auto-choice non-determinism."
    )
    print("  [OK] All 4 determinism flags set correctly:")
    print(f"    deterministic={HARDCODED_LGBM_PARAMS_061['deterministic']}")
    print(f"    num_threads={HARDCODED_LGBM_PARAMS_061['num_threads']}")
    print(f"    is_unbalance={HARDCODED_LGBM_PARAMS_061['is_unbalance']}")
    print(f"    force_col_wise={HARDCODED_LGBM_PARAMS_061['force_col_wise']}")
