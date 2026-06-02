"""iter-v1/061 — BTC-only zero-randomness diagnostic.

This is a thin dispatch wrapper around ``run_baseline_v1.main()``.  It hardwires
the EXPLORATION-mode arguments for iter-v1/061 and monkey-patches
``optimize_and_train`` to inject hardcoded HPs via Optuna's ``study.enqueue_trial()``
before the single Optuna trial executes.

Axis:
    EXPLORATION (methodology; cycle-7 EXPLORATION 4/N).
    Cohort: BTCUSDT only (BTC-only specialist head).
    CHANGE vs /058: NO new feature; NO parquet regen required.
    ALL sources of randomness eliminated per LM Master Phase 4.5:
        - n_trials=1    (single Optuna trial; no search)
        - seeds=1       (single inner seed; no ensemble averaging)
        - subsample=1.0 (no row subsampling; via v1_pruned_axis016 + enqueue_trial)
        - colsample_bytree=1.0 (no column subsampling; via v1_pruned_axis016 + enqueue_trial)
        - bagging_freq=0 (alias of subsample_freq; hardcoded in HP dict)
        - deterministic=True (LightGBM non-deterministic micro-optimizations disabled)
        - num_threads=1  (eliminates float-summation order non-determinism)
        - is_unbalance=False (eliminates month-varying implicit scale_pos_weight)
        - force_col_wise=True (avoids row/col mode auto-choice)

Monkey-patch mechanism:
    run_iteration_061.main() replaces ``optimize_and_train`` in
    ``crypto_trade.strategies.ml.optimization`` with a wrapper that:
    1. Creates an Optuna study (identical to the original)
    2. Calls ``study.enqueue_trial(HARDCODED_LGBM_PARAMS_OPTUNA_KEYS)`` to force
       the single trial to use the hardcoded HP values from HARDCODED_LGBM_PARAMS_061
    3. Calls ``study.optimize(objective, n_trials=1)`` — the enqueued trial fires first
    4. Returns the trained model + selected columns + confidence_threshold
    The original ``optimize_and_train`` is restored after ``run_baseline_v1.main()``
    returns, to prevent side effects on subsequent callers.

Dispatch branch in run_baseline_v1.py:
    ``elif iteration_label == "v1-061" and set(symbols) == set(V1_ITER061_UNIVERSE)``
    Architecture: Model A_BTC_specialist (BTC only).
        R1=OFF (same as /052-/054 BTC specialist convention)
        R2=OFF (same as /052-/054 BTC specialist convention)
        R3=OFF (OOD gate DISABLED — eliminates covariance-inversion non-determinism)
        atr_tp=3.5, atr_sl=1.75 (UNCHANGED from BTC specialist convention)

LM Master Phase 4.5 hardcoded HPs (ADOPTED VERBATIM from lgbm_advisor.md):
    n_estimators=300, max_depth=4, num_leaves=31, learning_rate=0.05,
    min_child_samples=50, reg_alpha=0.1, reg_lambda=0.1,
    confidence_threshold=0.7, training_days=360.
    Plus: subsample=1.0, colsample_bytree=1.0, bagging_freq=0,
          deterministic=True, num_threads=1, is_unbalance=False, force_col_wise=True.

Verdict framework (brief Section 4):
    F1 (PRIMARY): IS Sharpe bit-exact reproducible across 2 consecutive runs → REPRODUCIBLE
    F2 (DIAGNOSTIC): IS Sharpe vs LM Master prediction +0.08 (band [−0.10, +0.20]):
        ≥ +0.20 → OPTUNA-LOTTERY-SOURCE
        [−0.10, +0.20] → NOISE-FLOOR-CONFIRMED (60% modal prediction)
        << −0.10 → ARCHITECTURE-DATA-ISSUE

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    ENSEMBLE_SEEDS[0] = 42  (single seed; offset=0)

No parquet regeneration required:
    V1_FEATURE_COLUMNS_PRUNED is 48 cols (UNCHANGED from /058 closeout).
    BTCUSDT parquet was regenerated at /058; same stack applies at /061.

Features-base-hash:
    48-col hash (current; UNCHANGED from /057 closeout / /058 REVERT):
        b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3

Invocation:
    # Default (zero-randomness diagnostic, n_trials=1, seeds=1):
    uv run python run_iteration_061.py

    # Override n_trials (for debugging only; defeats zero-randomness purpose):
    uv run python run_iteration_061.py --n-trials 1

    # Verify features-base-hash only (dry-run, no backtest):
    uv run python run_iteration_061.py --check-hash

Output paths:
    reports-v1/iteration_v1-061/in_sample/
    reports-v1/iteration_v1-061/out_of_sample/
    reports-v1/iteration_v1-061/comparison.csv
    reports-v1/iteration_v1-061/run.log
"""

from __future__ import annotations

import argparse
import hashlib
import sys

# ---------------------------------------------------------------------------
# features-base-hash guard
# ---------------------------------------------------------------------------
# Import V1_FEATURE_COLUMNS_PRUNED at startup — confirms 48 cols UNCHANGED.
# /061 does NOT add or remove any feature; parquet from /058 is reused.
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

# Pre-registered 48-col hash (UNCHANGED from /057 closeout / /058 REVERT).
# Computed from: hashlib.sha256('\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest()
# This hash is IDENTICAL to the /057 closeout ref and /058 REVERT state.
# /061 does NOT change the feature column set — the hash MUST remain 48-col.
#
# To regenerate:
#   uv run python -c "
#   import hashlib
#   from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
#   print(hashlib.sha256('\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest())
#   "
FEATURES_BASE_HASH_48COL: str = "b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3"


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# Hardcoded HP dict — LM Master Phase 4.5 (ADOPTED VERBATIM)
# ---------------------------------------------------------------------------
# These values are injected via study.enqueue_trial() in the monkey-patch below.
# The "runner-level" keys (confidence_threshold, training_days, training_months,
# n_trials, cv_splits, cv_gap) are passed both via enqueue_trial (for the Optuna
# trial object) and enforced at the dispatch level in run_baseline_v1.py.
HARDCODED_LGBM_PARAMS_061: dict = {
    # Tree complexity — depth-shallow, leaves moderate (LM Master Rec 1)
    "n_estimators": 300,
    "max_depth": 4,
    "num_leaves": 31,
    "min_child_samples": 50,
    "min_split_gain": 0,
    # Learning rate + boosting (LM Master Rec 1 + DART/GOSS excluded)
    "learning_rate": 0.05,
    "boosting_type": "gbdt",
    # Subsampling DISABLED (user spec + LM Master Rec 2 + "Other Randomness Sources" #1)
    "subsample": 1,
    "subsample_freq": 0,
    "bagging_freq": 0,
    "bagging_fraction": 1,
    "colsample_bytree": 1,
    "feature_fraction": 1,
    # Regularization (LM Master Rec 1 — central tendency)
    "reg_alpha": 0.1,
    "reg_lambda": 0.1,
    # Determinism flags (LM Master Rec 3 + "Other Randomness Sources" #2, #3)
    "random_state": 42,
    "deterministic": True,
    "force_col_wise": True,
    "num_threads": 1,
    # Objective + class handling (LM Master Rec 4 + "Other Randomness Sources" #1)
    "objective": "binary",
    "is_unbalance": False,
    "class_weight": None,
    "scale_pos_weight": 1,
    # Misc
    "verbosity": -1,
    "metric": "binary_logloss",
    # Training schedule — runner-level (NOT passed to LightGBM; used in Optuna suggest_* calls)
    "confidence_threshold": 0.7,
    "training_days": 360,
    "training_months": 24,
    "n_trials": 1,
    "cv_splits": 5,
    "cv_gap": 42,
}

# Optuna enqueue_trial keys — only the subset that _objective() calls trial.suggest_*() for.
# With bounds_profile="v1_pruned_axis016", subsample and colsample_bytree are pinned to 1.0
# and NOT suggested by Optuna (the _pin_subsampling flag in _objective bypasses suggest_*).
# Providing them in enqueue_trial is safe (extra keys are ignored by Optuna's study.enqueue_trial).
_ENQUEUE_PARAMS: dict = {
    "confidence_threshold": HARDCODED_LGBM_PARAMS_061["confidence_threshold"],
    "training_days": HARDCODED_LGBM_PARAMS_061["training_days"],
    "n_estimators": HARDCODED_LGBM_PARAMS_061["n_estimators"],
    "max_depth": HARDCODED_LGBM_PARAMS_061["max_depth"],
    "num_leaves": HARDCODED_LGBM_PARAMS_061["num_leaves"],
    "learning_rate": HARDCODED_LGBM_PARAMS_061["learning_rate"],
    "subsample": HARDCODED_LGBM_PARAMS_061["subsample"],
    "colsample_bytree": HARDCODED_LGBM_PARAMS_061["colsample_bytree"],
    "min_child_samples": HARDCODED_LGBM_PARAMS_061["min_child_samples"],
    "reg_alpha": HARDCODED_LGBM_PARAMS_061["reg_alpha"],
    "reg_lambda": HARDCODED_LGBM_PARAMS_061["reg_lambda"],
}

# ---------------------------------------------------------------------------
# Runner constants
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-061"
ITERATION_NUMBER: int = 61
N_TRIALS_DEFAULT: int = 1  # zero-randomness spec — single deterministic trial
SEEDS_DEFAULT: int = 1  # single seed; no ensemble averaging
ENSEMBLE_SIZE: int = 1  # single inner model

# Compute the live hash at import time (confirms 48-col UNCHANGED).
_LIVE_HASH = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
FEATURES_BASE_HASH_EXPECTED: str = _LIVE_HASH


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/061 EXPLORATION runner: "
            "BTC-only zero-randomness diagnostic "
            "(n_trials=1, seeds=1, subsample=1.0, colsample_bytree=1.0, bagging_freq=0; "
            "cycle-7 EXPLORATION 4/N)"
        )
    )
    p.add_argument(
        "--n-trials",
        type=int,
        default=N_TRIALS_DEFAULT,
        help=(
            f"Optuna trial budget per cell (default {N_TRIALS_DEFAULT}; MUST be 1 for diagnostic)."
        ),
    )
    p.add_argument(
        "--seeds",
        type=int,
        default=SEEDS_DEFAULT,
        help=(
            f"Number of outer seeds (default {SEEDS_DEFAULT}). "
            "MUST be 1 for zero-randomness diagnostic. "
            "Multi-seed would defeat the reproducibility purpose."
        ),
    )
    p.add_argument(
        "--check-hash",
        action="store_true",
        default=False,
        help="Print the features-base-hash and exit (dry-run; no backtest launched).",
    )
    return p.parse_args()


def _verify_features_hash(expected: str) -> None:
    """Assert V1_FEATURE_COLUMNS_PRUNED matches the pre-registered 48-col hash.

    /061 does NOT change the feature column set — hash must be IDENTICAL to /057 closeout.
    Exits with a non-zero status if the hash does not match.
    """
    actual = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    if actual != expected:
        print(
            f"[iter-v1/061] FEATURES-BASE-HASH MISMATCH\n"
            f"  expected : {expected} (48-col; UNCHANGED from /057 closeout)\n"
            f"  actual   : {actual}\n"
            f"  V1_FEATURE_COLUMNS_PRUNED (len={len(V1_FEATURE_COLUMNS_PRUNED)}):\n"
            + "\n".join(f"    {i:03d}: {c}" for i, c in enumerate(V1_FEATURE_COLUMNS_PRUNED)),
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/061] ABORT: feature column set does not match pre-registered 48-col hash. "
            "V1_FEATURE_COLUMNS_PRUNED was modified — /061 must use the UNCHANGED 48-col stack. "
            "If a feature was added (e.g. btc_oi_delta_5_z30 from /058 not reverted), "
            "revert it before running /061."
        )
    print(
        f"[iter-v1/061] features-base-hash PASS: {actual[:16]}... "
        f"(48 columns; UNCHANGED from /057 closeout)"
    )


def _make_fixed_optimize_and_train() -> object:
    """Return a monkey-patch wrapper for optimize_and_train that injects hardcoded HPs.

    The wrapper:
    1. Creates an Optuna study (identical sampler + user_attrs as the original)
    2. Calls study.enqueue_trial(_ENQUEUE_PARAMS) BEFORE study.optimize() — this forces
       the first (and only, at n_trials=1) trial to use the hardcoded HP values.
    3. Calls study.optimize(objective, n_trials=1) — the enqueued trial fires and is
       the only trial evaluated.
    4. Trains the final LightGBM model with the hardcoded HP dict (adding determinism
       flags: deterministic=True, num_threads=1, is_unbalance=False, force_col_wise=True).
    5. Returns (model, selected_cols, confidence_threshold) matching the original signature.

    Why study.enqueue_trial() works here:
        Optuna's enqueue_trial() adds a trial to the "to-be-evaluated" queue.
        When study.optimize(n_trials=1) is called, the FIRST trial popped from the queue
        is the enqueued trial — it uses the provided params WITHOUT calling the sampler.
        This overrides ALL trial.suggest_* calls in _objective() with the pre-registered
        values, producing a fully deterministic single-trial evaluation.

    Why NOT use FixedTrial sampler:
        optuna.samplers.FixedTrial does NOT exist in Optuna's public API. The correct
        approach for "fix all hyperparameters" is enqueue_trial(), which works with the
        existing TPESampler and does not require a custom sampler class.

    LightGBM determinism flags (added to the params dict AFTER Optuna trial execution):
        The trial.suggest_* calls in _objective() build the params dict but do NOT
        include deterministic=True, num_threads=1, force_col_wise=True, is_unbalance=False.
        These are injected by the wrapper AFTER _objective() runs the CV (which uses
        train_test params for CV only, not the final model). The final model is then
        trained by lgbm.py's optimize_and_train return path with the enqueued trial's
        best_params. The wrapper overrides the final params before calling LGBMClassifier.
    """
    import optuna

    import crypto_trade.strategies.ml.optimization as _opt_mod

    # Capture the original function for restoration and for calling _objective.
    _orig = _opt_mod.optimize_and_train

    def _fixed_optimize_and_train(
        train_features,
        train_labels,
        all_columns,
        long_pnls,
        short_pnls,
        n_trials,
        cv_splits,
        seed,
        verbose=0,
        **kwargs,
    ):
        """Monkey-patched optimize_and_train: injects hardcoded HPs via enqueue_trial."""
        # Validate that the caller is using n_trials=1 (zero-randomness spec).
        if n_trials != 1:
            print(
                f"[iter-v1/061] WARNING: n_trials={n_trials} passed to _fixed_optimize_and_train; "
                f"expected 1 for zero-randomness diagnostic. Proceeding — enqueue_trial "
                f"fills trial 0 with hardcoded HPs; remaining trials use TPESampler.",
                file=sys.stderr,
            )

        # Extract open_times from kwargs (needed to determine if training_days is suggested).
        open_times = kwargs.get("open_times")
        oof_persist_path = kwargs.get("oof_persist_path")
        train_month = kwargs.get("train_month", "")
        symbols_arr = kwargs.get("symbols_arr")
        ternary = kwargs.get("ternary", False)
        cv_gap = kwargs.get("cv_gap", 0)
        bounds_profile = kwargs.get("bounds_profile", "default")
        min_child_samples_lower_bound = kwargs.get("min_child_samples_lower_bound")

        if verbose <= 0:
            optuna.logging.set_verbosity(optuna.logging.WARNING)

        sampler = optuna.samplers.TPESampler(seed=seed)
        study = optuna.create_study(direction="maximize", sampler=sampler)
        study.set_user_attr("fast_mode", False)
        study.set_user_attr("optuna_objective", "sharpe")

        # Build the enqueue params dict.
        # Include training_days ONLY if open_times is provided (matches _objective logic).
        enqueue = dict(_ENQUEUE_PARAMS)
        if open_times is None:
            enqueue.pop("training_days", None)

        # Inject hardcoded HPs — the enqueued trial fires as trial 0.
        study.enqueue_trial(enqueue)
        print(
            f"[iter-v1/061] study.enqueue_trial() called with hardcoded HPs: "
            f"n_estimators={enqueue['n_estimators']}, max_depth={enqueue['max_depth']}, "
            f"num_leaves={enqueue['num_leaves']}, lr={enqueue['learning_rate']}, "
            f"colsample={enqueue.get('colsample_bytree', 'pinned@1.0')}, "
            f"subsample={enqueue.get('subsample', 'pinned@1.0')}, "
            f"confidence_threshold={enqueue['confidence_threshold']}, "
            f"training_days={enqueue.get('training_days', 'N/A')} "
            f"(open_times={'set' if open_times is not None else 'None'})"
        )

        # Use the original _objective from optimization.py via the module reference.
        from crypto_trade.strategies.ml.optimization import _objective

        oof_buffer: list | None = [] if oof_persist_path is not None else None
        study.optimize(
            lambda trial: _objective(
                trial,
                train_features,
                train_labels,
                None,  # sample_weights — let _objective default to ones
                long_pnls,
                short_pnls,
                all_columns,
                cv_splits,
                seed,
                verbose,
                open_times=open_times,
                ternary=ternary,
                cv_gap=cv_gap,
                train_month=train_month,
                symbols_arr=symbols_arr,
                oof_buffer=oof_buffer,
                bounds_profile=bounds_profile,
                min_child_samples_lower_bound=min_child_samples_lower_bound,
            ),
            n_trials=n_trials,
        )

        # Flush OOF buffer if needed (mirrors original implementation).
        if oof_persist_path is not None and oof_buffer:
            import os
            import tempfile

            import pandas as pd

            oof_persist_path.parent.mkdir(parents=True, exist_ok=True)
            new_df = pd.DataFrame(
                oof_buffer,
                columns=[
                    "trial_id",
                    "symbol",
                    "train_month",
                    "fold_idx",
                    "candle_open_time_ms",
                    "oof_return",
                ],
            )
            if oof_persist_path.exists():
                existing = pd.read_parquet(oof_persist_path)
                combined = pd.concat([existing, new_df], ignore_index=True)
            else:
                combined = new_df
            tmp_fd, tmp_name = tempfile.mkstemp(dir=oof_persist_path.parent, suffix=".parquet.tmp")
            try:
                os.close(tmp_fd)
                combined.to_parquet(tmp_name, index=False)
                os.replace(tmp_name, oof_persist_path)
            except Exception:
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass
                raise

        # Extract best trial results.
        best = study.best_trial
        best_params = best.params
        confidence_threshold = float(best_params["confidence_threshold"])
        training_days = (
            int(best_params["training_days"]) if "training_days" in best_params else None
        )

        # Build the final LightGBM params dict (mirrors _objective's params construction).
        import lightgbm as lgb
        import numpy as np

        from crypto_trade.strategies.ml.optimization import labels_to_classes

        _pruned = bounds_profile in ("v1_pruned", "v1_pruned_axis016")
        _pin_subsampling = bounds_profile == "v1_pruned_axis016"

        lgbm_params = {
            "n_estimators": int(best_params["n_estimators"]),
            "max_depth": int(best_params["max_depth"]),
            "num_leaves": int(best_params["num_leaves"]),
            "learning_rate": float(best_params["learning_rate"]),
            "subsample": (1.0 if _pin_subsampling else float(best_params.get("subsample", 1.0))),
            "colsample_bytree": (
                1.0 if _pin_subsampling else float(best_params.get("colsample_bytree", 1.0))
            ),
            "min_child_samples": int(best_params["min_child_samples"]),
            "reg_alpha": float(best_params["reg_alpha"]),
            "reg_lambda": float(best_params["reg_lambda"]),
            "random_state": seed,
            "verbosity": -1,
            # Determinism flags injected by /061 monkey-patch (NOT in standard _objective).
            "deterministic": HARDCODED_LGBM_PARAMS_061["deterministic"],
            "force_col_wise": HARDCODED_LGBM_PARAMS_061["force_col_wise"],
            "num_threads": HARDCODED_LGBM_PARAMS_061["num_threads"],
        }
        if ternary:
            lgbm_params["objective"] = "multiclass"
            lgbm_params["num_class"] = 3
        else:
            lgbm_params["objective"] = "binary"
            # Explicitly set is_unbalance=False (LM Master Rec 4 — eliminates month-varying
            # implicit scale_pos_weight randomness source).
            lgbm_params["is_unbalance"] = False
            lgbm_params["scale_pos_weight"] = 1

        # Resolve training window (mirrors lgbm.py's _training_days_filter_mask logic).
        if training_days is not None and open_times is not None:
            # Apply training window filter: keep only rows within training_days of train_end_ms.
            train_end_ms = kwargs.get("train_end_ms")
            if train_end_ms is not None:
                training_ms = training_days * 24 * 3600 * 1000
                cutoff_ms = train_end_ms - training_ms
                mask = open_times >= cutoff_ms
                feat_train = train_features[mask]
                labels = (
                    labels_to_classes(train_labels[mask]) if not ternary else train_labels[mask]
                )
                weights = np.ones(len(labels), dtype=np.float64)
            else:
                feat_train = train_features
                labels = labels_to_classes(train_labels) if not ternary else train_labels
                weights = np.ones(len(labels), dtype=np.float64)
        else:
            feat_train = train_features
            labels = labels_to_classes(train_labels) if not ternary else train_labels
            weights = np.ones(len(labels), dtype=np.float64)

        # Handle sample_weights from kwargs.
        sample_weights = kwargs.get("sample_weights")
        if sample_weights is not None:
            if training_days is not None and open_times is not None and kwargs.get("train_end_ms"):
                training_ms = training_days * 24 * 3600 * 1000
                cutoff_ms = kwargs["train_end_ms"] - training_ms
                mask = open_times >= cutoff_ms
                weights = sample_weights[mask]
            else:
                weights = sample_weights

        print(
            f"[iter-v1/061] Training final model with deterministic HPs: "
            f"n_est={lgbm_params['n_estimators']}, depth={lgbm_params['max_depth']}, "
            f"leaves={lgbm_params['num_leaves']}, lr={lgbm_params['learning_rate']:.4f}, "
            f"subsample={lgbm_params['subsample']:.1f}, "
            f"colsample={lgbm_params['colsample_bytree']:.1f}, "
            f"deterministic={lgbm_params['deterministic']}, "
            f"num_threads={lgbm_params['num_threads']}, "
            f"is_unbalance={lgbm_params.get('is_unbalance', 'N/A')}"
        )

        clf = lgb.LGBMClassifier(**lgbm_params)
        clf.fit(feat_train, labels, sample_weight=weights)

        # Validate subsample/colsample_bytree/bagging_freq from fitted model.
        fitted_params = clf.get_params()
        assert fitted_params.get("subsample", 1.0) == 1.0, (
            f"[iter-v1/061] ASSERTION FAIL: subsample={fitted_params.get('subsample')} != 1.0. "
            "Hardware-mandatory: subsample MUST be 1.0 for zero-randomness experiment."
        )
        assert fitted_params.get("colsample_bytree", 1.0) == 1.0, (
            f"[iter-v1/061] ASSERTION FAIL: "
            f"colsample_bytree={fitted_params.get('colsample_bytree')} != 1.0. "
            "Hardware-mandatory: colsample_bytree MUST be 1.0 for zero-randomness experiment."
        )
        assert fitted_params.get("bagging_freq", 0) == 0, (
            f"[iter-v1/061] ASSERTION FAIL: bagging_freq={fitted_params.get('bagging_freq')} != 0. "
            "Hardware-mandatory: bagging_freq MUST be 0 for zero-randomness experiment."
        )
        print(
            "[iter-v1/061] HP validation PASS: "
            f"subsample={fitted_params.get('subsample', 1.0):.1f} (expect 1.0), "
            f"colsample_bytree={fitted_params.get('colsample_bytree', 1.0):.1f} (expect 1.0), "
            f"bagging_freq={fitted_params.get('bagging_freq', 0)} (expect 0)"
        )

        return clf, all_columns, confidence_threshold

    return _fixed_optimize_and_train, _orig


def main() -> None:
    args = _parse_args()

    # --- Hash check (always runs; dry-run exits here if --check-hash) ---
    _verify_features_hash(FEATURES_BASE_HASH_48COL)

    if args.check_hash:
        print(
            f"[iter-v1/061] --check-hash mode. "
            f"Hash = {FEATURES_BASE_HASH_EXPECTED}. "
            f"V1_FEATURE_COLUMNS_PRUNED len = {len(V1_FEATURE_COLUMNS_PRUNED)}. "
            "No backtest launched."
        )
        print(f"  n_trials               : {N_TRIALS_DEFAULT} (FIXED — zero-randomness spec)")
        print(f"  seeds                  : {SEEDS_DEFAULT} (FIXED — single deterministic seed)")
        print(f"  ensemble_size          : {ENSEMBLE_SIZE} (FIXED — single model)")
        print("  48-col hash:", FEATURES_BASE_HASH_48COL)
        print("  Hardcoded HPs (enqueue_trial keys):")
        for k, v in _ENQUEUE_PARAMS.items():
            print(f"    {k}: {v}")
        print("  Column list:")
        for i, col in enumerate(V1_FEATURE_COLUMNS_PRUNED):
            print(f"    {i:02d}: {col}")
        return

    # --- Pre-flight assertions ---
    if args.n_trials != 1:
        print(
            f"[iter-v1/061] WARNING: --n-trials={args.n_trials} overrides default 1. "
            "Zero-randomness diagnostic requires n_trials=1. "
            "Only use a different value for debugging purposes.",
            file=sys.stderr,
        )
    if args.seeds != 1:
        print(
            f"[iter-v1/061] WARNING: --seeds={args.seeds} overrides default 1. "
            "Zero-randomness diagnostic requires seeds=1 (single deterministic seed). "
            "Only use a different value for multi-seed validation purposes.",
            file=sys.stderr,
        )

    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"[iter-v1/061] PRE-FLIGHT FAIL: expected 48 features (UNCHANGED), "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "V1_FEATURE_COLUMNS_PRUNED must be 48 at iter-v1/061."
    )

    print("=" * 70)
    print("iter-v1/061 — BTC-only zero-randomness diagnostic")
    print(f"  ITERATION_LABEL        : {ITERATION_LABEL}")
    print(f"  n_trials               : {args.n_trials} (MUST be 1 for zero-randomness)")
    print(f"  seeds                  : {args.seeds} (MUST be 1 for single deterministic seed)")
    print(f"  ensemble_size          : {ENSEMBLE_SIZE} (single inner model)")
    n_cols = len(V1_FEATURE_COLUMNS_PRUNED)
    print(f"  feature_columns        : {n_cols} cols (V1_FEATURE_COLUMNS_PRUNED; UNCHANGED)")
    print("  cohort                 : BTCUSDT only (V1_ITER061_UNIVERSE)")
    print("  model                  : A_BTC_specialist (R1=OFF, R2=OFF, R3=OFF)")
    print("  subsample              : 1.0 (HARDCODED — hardware-mandatory)")
    print("  colsample_bytree       : 1.0 (HARDCODED — hardware-mandatory)")
    print("  bagging_freq           : 0   (HARDCODED — hardware-mandatory)")
    print("  deterministic          : True (LightGBM flag)")
    print("  num_threads            : 1   (eliminates float-summation order non-determinism)")
    print("  is_unbalance           : False (eliminates month-varying scale_pos_weight)")
    print("  verdict framework      :")
    print("    F1 (PRIMARY): IS Sharpe bit-exact reproducible → REPRODUCIBLE")
    print("                  / HIDDEN-RANDOMNESS-BUG")
    print("    F2 (DIAGNOSTIC): IS Sharpe vs LM +0.08 [−0.10, +0.20] band:")
    print("      ≥ +0.20 → OPTUNA-LOTTERY-SOURCE")
    print("      [−0.10, +0.20] → NOISE-FLOOR-CONFIRMED (60% modal)")
    print("      << −0.10 → ARCHITECTURE-DATA-ISSUE")
    print("  48-col hash            :", FEATURES_BASE_HASH_48COL[:32] + "...")
    print("=" * 70)

    # --- Apply monkey-patch to optimize_and_train ---
    # The monkey-patch replaces optimize_and_train in the optimization module
    # with a wrapper that injects hardcoded HPs via study.enqueue_trial().
    # The original is restored after run_baseline_v1.main() returns.
    import crypto_trade.strategies.ml.optimization as _opt_mod

    _fixed_fn, _orig_fn = _make_fixed_optimize_and_train()
    _opt_mod.optimize_and_train = _fixed_fn  # type: ignore[assignment]

    print("[iter-v1/061] Monkey-patch APPLIED: optimize_and_train → _fixed_optimize_and_train")
    print(f"  enqueue_trial keys: {list(_ENQUEUE_PARAMS.keys())}")

    # --- Inject argv for run_baseline_v1.main() ---
    # run_baseline_v1.main() reads sys.argv. We replace it with the hardwired
    # EXPLORATION arguments for iter-v1/061.
    # NOTE: import run_baseline_v1 as a module at repo root (NOT 'crypto_trade.run_baseline_v1').
    # The --pruned-features flag selects V1_FEATURE_COLUMNS_PRUNED (48 cols).
    # The --ensemble-size 1 flag sets ENSEMBLE_SIZE=1 (single inner model).
    # The --n-trials 1 flag enforces the single-trial zero-randomness constraint.
    # The --symbols BTCUSDT flag selects the BTC-only cohort.
    sys.argv = [
        "run_baseline_v1.py",
        "--exploration",
        "--iteration",
        str(ITERATION_NUMBER),
        "--n-trials",
        str(args.n_trials),
        "--ensemble-size",
        str(ENSEMBLE_SIZE),
        "--symbols",
        "BTCUSDT",
        "--pruned-features",
        "--seeds",
        str(args.seeds),
    ]

    print(f"[iter-v1/061] sys.argv set: {sys.argv}")

    try:
        import run_baseline_v1 as _rbv1  # module at repo root (NOT crypto_trade.run_baseline_v1)

        _rbv1.main()
    finally:
        # Restore original optimize_and_train to prevent side effects.
        _opt_mod.optimize_and_train = _orig_fn  # type: ignore[assignment]
        print("[iter-v1/061] Monkey-patch RESTORED: optimize_and_train → original")


if __name__ == "__main__":
    main()
