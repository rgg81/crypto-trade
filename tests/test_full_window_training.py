"""Tests for the FULL-WINDOW-TRAINING design flag.

Design (v1 BUNDLE-002 specialists):
  When ``full_window_training=True``:
    (a) ``training_days`` is NOT added to the Optuna search space — trials get no
        ``training_days`` key.
    (b) The CV objective uses the FULL training window (no per-fold slice) — because
        ``training_days`` stays ``None``, the slice in ``_objective`` is a no-op.
    (c) The per-seed final retrain uses the FULL window (no slice).

  Default ``full_window_training=False`` is BYTE-IDENTICAL to the current
  C2/H1-fixed behavior: ``training_days`` is searched + sliced in CV and at the
  final fit.

These tests drive the shared ``_objective`` (used by both the standard ensemble
``optimize_and_train`` path and the SPECIALIST per-seed studies in ``lgbm.py``)
through a tiny Optuna study, then inspect ``study.best_params`` to confirm the
search-space gating. A separate test patches ``LGBMClassifier.fit`` to confirm the
per-fold CV training slice spans the full window when the flag is ON.
"""

from __future__ import annotations

import numpy as np
import optuna

from crypto_trade.strategies.ml.optimization import _objective


def _make_synth(n: int = 240, n_features: int = 4, seed: int = 0):
    """Synthetic multi-bar training set at 8h cadence with monotone open_times."""
    rng = np.random.default_rng(seed)
    interval_ms = 8 * 3_600_000
    open_times = np.arange(n, dtype=np.int64) * interval_ms
    feats = rng.random((n, n_features)).astype(np.float64)
    labels = rng.choice([-1, 1], size=n).astype(np.float64)
    weights = np.ones(n, dtype=np.float64)
    long_pnls = rng.normal(0.0, 0.01, size=n)
    short_pnls = rng.normal(0.0, 0.01, size=n)
    cols = [f"f{i}" for i in range(n_features)]
    return open_times, feats, labels, weights, long_pnls, short_pnls, cols


def _run_study(full_window_training: bool, n_trials: int = 5) -> optuna.Study:
    open_times, feats, labels, weights, long_pnls, short_pnls, cols = _make_synth()
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
    study.set_user_attr("optuna_objective", "sharpe")
    study.set_user_attr("full_window_training", full_window_training)
    study.optimize(
        lambda trial: _objective(
            trial,
            feats,
            labels,
            weights,
            long_pnls,
            short_pnls,
            cols,
            cv_splits=3,
            seed=42,
            verbose=0,
            open_times=open_times,
            ternary=False,
            cv_gap=0,
            bounds_profile="v1_specialist",
        ),
        n_trials=n_trials,
    )
    return study


def test_flag_off_searches_training_days() -> None:
    """Default (flag OFF): training_days IS suggested in every trial."""
    study = _run_study(full_window_training=False)
    for trial in study.trials:
        assert "training_days" in trial.params, (
            "With full_window_training=False, training_days must be in the search space"
        )


def test_flag_on_omits_training_days() -> None:
    """Flag ON: training_days is NOT suggested in any trial."""
    study = _run_study(full_window_training=True)
    for trial in study.trials:
        assert "training_days" not in trial.params, (
            "With full_window_training=True, training_days must NOT be in trial params"
        )


def test_flag_on_cv_uses_full_window() -> None:
    """Flag ON: the per-fold CV fit receives the full (untrimmed) training window.

    Without the flag, _objective trims each fold's training rows to the last
    `training_days` days. With the flag, training_days stays None so the trim is
    skipped — the fit X for the LAST fold equals the full TimeSeriesSplit train_idx
    span (no row removed beyond TimeSeriesSplit's own fold boundaries).
    """
    from sklearn.model_selection import TimeSeriesSplit

    open_times, feats, labels, weights, long_pnls, short_pnls, cols = _make_synth()

    captured: list[int] = []

    import crypto_trade.strategies.ml.optimization as opt_mod

    orig_fit = opt_mod.lgb.LGBMClassifier.fit

    def _spy_fit(self, x, y, *args, **kwargs):  # noqa: ANN001
        captured.append(len(x))
        return orig_fit(self, x, y, *args, **kwargs)

    cv_splits = 3
    # Expected full-window per-fold train sizes from TimeSeriesSplit (no trimming).
    tscv = TimeSeriesSplit(n_splits=cv_splits, gap=0)
    expected_train_sizes = [len(tr) for tr, _ in tscv.split(feats)]

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=7))
    study.set_user_attr("optuna_objective", "sharpe")
    study.set_user_attr("full_window_training", True)

    opt_mod.lgb.LGBMClassifier.fit = _spy_fit
    try:
        study.optimize(
            lambda trial: _objective(
                trial,
                feats,
                labels,
                weights,
                long_pnls,
                short_pnls,
                cols,
                cv_splits=cv_splits,
                seed=7,
                verbose=0,
                open_times=open_times,
                ternary=False,
                cv_gap=0,
                bounds_profile="v1_specialist",
            ),
            n_trials=1,
        )
    finally:
        opt_mod.lgb.LGBMClassifier.fit = orig_fit

    # One fit per CV fold for the single trial; sizes equal the untrimmed splits.
    assert captured == expected_train_sizes, (
        f"Flag ON must use full-window CV folds {expected_train_sizes}; got {captured}"
    )


def test_flag_threads_through_constructor() -> None:
    """LightGbmStrategy exposes _full_window_training; default False, settable True."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    default = LightGbmStrategy(
        feature_columns=list(V1_FEATURE_COLUMNS_PRUNED),
        ensemble_seeds=[42],
    )
    assert default._full_window_training is False, "default must be False (byte-unchanged)"

    flagged = LightGbmStrategy(
        feature_columns=list(V1_FEATURE_COLUMNS_PRUNED),
        ensemble_seeds=[42],
        full_window_training=True,
    )
    assert flagged._full_window_training is True


def test_bundle_002_models_have_flag_on() -> None:
    """All 4 BUNDLE_002 specialists declare full_window_training=True."""
    from crypto_trade.live import models as live_models

    bundle = live_models.BUNDLE_002_MODELS
    assert len(bundle) == 4, "BUNDLE_002 is DOT/ETH/BTC/AAVE (4 specialists)"
    for mc in bundle:
        assert mc.full_window_training is True, (
            f"{mc.name}: BUNDLE_002 specialists must use full_window_training=True"
        )
