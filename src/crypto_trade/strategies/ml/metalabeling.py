"""MetaLabelingStrategy: López de Prado AFML Ch. 3 meta-labeling on top of LightGbmStrategy.

Architecture (iter-v3/017):
  M1 = LightGbmStrategy (direction model, unchanged from iter-v3/013).
       Uses 13 V3_FEATURE_COLUMNS + triple-barrier ATR(2.0/1.0) labels.
  M2 = LGBMClassifier binary (confidence/precision model).
       Trained on M1-positive bars only; predicts "did this M1-predicted trade
       reach TP barrier before SL/timeout?"
       Input: 13 V3 features + M1's prediction probability = 14-dim vector.
       Threshold: 0.5 (Bayes-optimal, NOT tuned — single-axis discipline).

Final trading rule:
  trade(t) = 1{t in T^M1+} * 1{M2_confidence(t) >= 0.5}

This module:
  - Wraps LightGbmStrategy as M1 (delegates compute_features, skip, partial
    get_signal to M1).
  - Holds a separate LGBMClassifier (M2) per calendar month (lazy training,
    parallel structure to LightGbmStrategy._train_for_month).
  - Exposes the same public interface as LightGbmStrategy (compute_features /
    get_signal / skip) so RiskV3Wrapper can wrap it transparently.

Look-ahead audit (non-negotiable):
  M2 labels are derived EXCLUSIVELY from the training-window subset.  The
  M2 classifier never sees candles outside the current training window.
  Specifically: M2 is trained on m1_positive_mask rows of feat_train (the
  same feat_train array M1 was trained on) with labels derived from
  long_pnls/short_pnls produced by label_trades on the SAME training window.
  No future candle is observed.

Reference: iter-v3/017 research brief §2.4 pseudocode + §3.5 sub-fix #1.

iter-v1/030 additions:
  - ``bounds_profile`` parameter on ``_train_m2_binary``: "v3" preserves the
    original iter-v3/017 search ranges; "v1_030" applies the tightened LM
    Master §2 bounds (n_estimators [50,200], max_depth [2,4], num_leaves
    [7,31], learning_rate [0.02,0.10], min_child_samples [8,30],
    reg_alpha/reg_lambda [0.01,5], colsample_bytree [0.4,0.8]).
  - ``scale_pos_weight`` explicit per cell under "v1_030" profile (replaces
    is_unbalance=True).
  - Fold-skip when any fold has < ``min_pos_per_fold`` positive labels (3 by
    default, per LM Master §2 stratification fallback).
  - ``n_trials_m2`` parameter on ``MetaLabelingStrategy.__init__``: decouples
    M2 Optuna budget from M1 (default keeps backwards-compat at M1's n_trials;
    /030 passes 18 explicitly).
  - ``include_m1_direction`` parameter: when True the M2 input vector appends
    M1's predicted direction as a second extra feature after m1_confidence
    (45-dim for /030 vs 14-dim for v3/017).
"""

from __future__ import annotations

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from crypto_trade.backtest_models import Signal
from crypto_trade.strategies import NO_SIGNAL
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy, _epoch_ms_to_month

# ---------------------------------------------------------------------------
# M2 training helper
# ---------------------------------------------------------------------------


def _train_m2_binary(
    m2_features: np.ndarray,
    m2_labels: np.ndarray,
    n_trials: int,
    seed: int,
    fast_mode: bool,
    verbose: int,
    bounds_profile: str = "v3",
    min_pos_per_fold: int = 3,
) -> lgb.LGBMClassifier | None:
    """Train M2 LGBMClassifier via Optuna on the M1-positive subset.

    M2 confidence threshold is PINNED at 0.5 (not tuned — single-axis
    discipline).  All other LightGBM hyperparams use the search space
    defined by ``bounds_profile``.

    Parameters
    ----------
    bounds_profile
        "v3" — original iter-v3/017 search ranges (backwards-compatible).
        "v1_030" — LM Master §2 tightened bounds for iter-v1/030:
          n_estimators [50,200], max_depth [2,4], num_leaves [7,31],
          learning_rate [0.02,0.10] log, min_child_samples [8,30],
          reg_alpha/reg_lambda [0.01,5] log, colsample_bytree [0.4,0.8].
          Uses explicit scale_pos_weight = n_neg/n_pos instead of
          is_unbalance=True.
    min_pos_per_fold
        Minimum positive-label count required in a TimeSeriesSplit fold for
        that fold to be included in scoring (LM Master §2 stratification
        fallback, default 3).  Folds with fewer positive labels are skipped.

    Returns None if training fails or training set is too small.
    """
    if len(m2_features) < 10:
        if verbose > 0:
            print(f"  [M2] Insufficient training samples ({len(m2_features)}) — skipping M2")
        return None

    n_pos = int((m2_labels == 1).sum())
    n_neg = int((m2_labels == 0).sum())
    if verbose > 0:
        print(
            f"  [M2] Training binary classifier: {len(m2_features)} samples, "
            f"{n_pos} TP-hits (M2=1), {n_neg} SL/timeout (M2=0) "
            f"[bounds_profile={bounds_profile}]"
        )

    if n_pos == 0 or n_neg == 0:
        if verbose > 0:
            print("  [M2] Degenerate labels (all 0 or all 1) — skipping M2")
        return None

    # Compute explicit scale_pos_weight for v1_030 profile (LM Master §2).
    # More deterministic than is_unbalance=True which uses internal heuristic.
    spw_explicit = float(n_neg) / float(n_pos) if n_pos > 0 else 1.0

    import optuna  # noqa: PLC0415

    # M2 uses a BINARY Optuna objective.  We re-use M1's _objective but with a
    # minimalist wrapper: since M2's PnL economics are not available in the same
    # form as M1 (M2 predicts "was M1 correct?", not direction), we minimise
    # log-loss instead.  We bypass _objective and run a direct Optuna study.
    def _m2_objective(trial: optuna.Trial) -> float:
        from sklearn.model_selection import TimeSeriesSplit  # noqa: PLC0415

        if bounds_profile == "v1_030":
            col_frac = 1.0 if fast_mode else trial.suggest_float("colsample_bytree", 0.4, 0.8)
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 50, 200),
                "max_depth": trial.suggest_int("max_depth", 2, 4),
                "num_leaves": trial.suggest_int("num_leaves", 7, 31),
                "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.10, log=True),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                "colsample_bytree": col_frac,
                "min_child_samples": trial.suggest_int("min_child_samples", 8, 30),
                "reg_alpha": trial.suggest_float("reg_alpha", 0.01, 5.0, log=True),
                "reg_lambda": trial.suggest_float("reg_lambda", 0.01, 5.0, log=True),
                "objective": "binary",
                "scale_pos_weight": spw_explicit,
                "random_state": seed,
                "verbosity": -1,
            }
        else:
            # "v3" — original iter-v3/017 search ranges (backwards-compatible)
            col_frac = 1.0 if fast_mode else trial.suggest_float("colsample_bytree", 0.3, 1.0)
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 50, 500),
                "max_depth": trial.suggest_int("max_depth", 3, 5),
                "num_leaves": trial.suggest_int("num_leaves", 15, 127),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                "colsample_bytree": col_frac,
                "min_child_samples": trial.suggest_int("min_child_samples", 5, 50),
                "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
                "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
                "objective": "binary",
                "is_unbalance": True,
                "random_state": seed,
                "verbosity": -1,
            }

        n_splits = min(3, max(2, len(m2_features) // 10))
        tscv = TimeSeriesSplit(n_splits=n_splits)
        fold_scores: list[float] = []
        feat_df = pd.DataFrame(m2_features)
        for train_idx, val_idx in tscv.split(m2_features):
            if len(train_idx) < 5 or len(val_idx) < 2:
                continue
            # LM Master §2 stratification fallback: skip fold if < min_pos_per_fold
            # positives in val to avoid degenerate F1 from empty positive val fold.
            if int((m2_labels[val_idx] == 1).sum()) < min_pos_per_fold:
                continue
            m = lgb.LGBMClassifier(**params)
            m.fit(feat_df.iloc[train_idx], m2_labels[train_idx])
            y_proba_val = m.predict_proba(feat_df.iloc[val_idx])[:, 1]
            # Score = mean precision-recall F1 at threshold 0.5
            y_pred_val = (y_proba_val >= 0.5).astype(int)
            tp = int(((y_pred_val == 1) & (m2_labels[val_idx] == 1)).sum())
            fp = int(((y_pred_val == 1) & (m2_labels[val_idx] == 0)).sum())
            fn = int(((y_pred_val == 0) & (m2_labels[val_idx] == 1)).sum())
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            fold_scores.append(f1)
        return float(np.mean(fold_scores)) if fold_scores else -10.0

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    sampler = optuna.samplers.TPESampler(seed=seed)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    study.optimize(_m2_objective, n_trials=n_trials)

    best = study.best_params
    if bounds_profile == "v1_030":
        final_params = {
            "n_estimators": best.get("n_estimators", 100),
            "max_depth": best.get("max_depth", 3),
            "num_leaves": best.get("num_leaves", 15),
            "learning_rate": best.get("learning_rate", 0.05),
            "subsample": best.get("subsample", 0.8),
            "colsample_bytree": best.get("colsample_bytree", 0.6),
            "min_child_samples": best.get("min_child_samples", 15),
            "reg_alpha": best.get("reg_alpha", 0.1),
            "reg_lambda": best.get("reg_lambda", 0.1),
            "objective": "binary",
            "scale_pos_weight": spw_explicit,
            "random_state": seed,
            "verbosity": -1,
        }
    else:
        final_params = {
            "n_estimators": best.get("n_estimators", 100),
            "max_depth": best.get("max_depth", 3),
            "num_leaves": best.get("num_leaves", 31),
            "learning_rate": best.get("learning_rate", 0.1),
            "subsample": best.get("subsample", 0.8),
            "colsample_bytree": best.get("colsample_bytree", 1.0),
            "min_child_samples": best.get("min_child_samples", 20),
            "reg_alpha": best.get("reg_alpha", 1e-8),
            "reg_lambda": best.get("reg_lambda", 1e-8),
            "objective": "binary",
            "is_unbalance": True,
            "random_state": seed,
            "verbosity": -1,
        }
    if verbose > 0:
        print(
            f"  [M2] Optuna: {n_trials} trials, best F1={study.best_value:.4f} "
            f"(n_est={final_params['n_estimators']}, depth={final_params['max_depth']}, "
            f"profile={bounds_profile})"
        )

    m2_model = lgb.LGBMClassifier(**final_params)
    feat_df = pd.DataFrame(m2_features)
    m2_model.fit(feat_df, m2_labels)
    return m2_model


# ---------------------------------------------------------------------------
# MetaLabelingStrategy
# ---------------------------------------------------------------------------


class MetaLabelingStrategy:
    """Meta-labeling wrapper: M1 (LightGbmStrategy) + M2 (LGBMClassifier binary).

    Implements the same public interface as LightGbmStrategy:
      - compute_features(master)
      - get_signal(symbol, open_time) -> Signal | NO_SIGNAL
      - skip() -> None

    Delegation model:
      - compute_features: fully delegated to self._m1.
      - get_signal: M1 runs first; if M1 fires, M2 vets the signal.
        If M2 confidence < 0.5, return NO_SIGNAL.
      - _train_for_month: called internally by self._m1 via get_signal;
        MetaLabelingStrategy intercepts the M2 training after M1 trains.

    The interception is achieved via monkey-patching self._m1._train_for_month
    to call _m1_train_for_month_impl + _m2_train_for_month_impl in sequence.
    This avoids code duplication while preserving M1's interface contract.

    M2 state:
      - self._m2_model: the trained M2 LGBMClassifier for the current month.
      - self._m2_active: True when M2 has been trained and can be queried.
      - self._m2_feature_cols: list of 14 feature names (13 V3 + "m1_confidence").
      - self._m2_month_features: dict {(symbol, open_time): np.ndarray[14]} for
        the current test month, populated alongside M1's _month_features.
    """

    def __init__(
        self,
        training_months: int = 24,
        n_trials: int = 10,
        cv_splits: int = 5,
        label_tp_pct: float = 8.0,
        label_sl_pct: float = 4.0,
        label_timeout_minutes: int = 10080,
        fee_pct: float = 0.1,
        features_dir: str = "data/features_v3",
        verbose: int = 0,
        atr_tp_multiplier: float | None = None,
        atr_sl_multiplier: float | None = None,
        atr_column: str = "natr_21_raw",
        ensemble_seeds: list[int] | None = None,
        feature_columns: list[str] | None = None,
        use_atr_labeling: bool = False,
        ood_enabled: bool = False,
        ood_features: list[str] | None = None,
        ood_cutoff_pct: float = 0.70,
        oof_persist_path: Path | None = None,
        fast_mode: bool = False,
        label_mode: str = "triple_barrier",
        trend_scan_grid: tuple[int, ...] = (5, 8, 13, 21),
        n_trials_m2: int | None = None,
        bounds_profile_m2: str = "v3",
        include_m1_direction: bool = False,
        # v1-specific M1 params (passed through to LightGbmStrategy)
        bounds_profile: str = "default",
        sigma_source: str = "natr",
        sigma_k_tp: float | None = None,
        sigma_k_sl: float | None = None,
        sigma_halflife_candles: int = 42,
        sample_weight_mode: str = "abs_pnl",
        # iter-v1/028: separate M2 feature set + configurable veto threshold.
        # m2_feature_columns: distinct positioning/leverage/regime feature set for
        #   the M2 classifier (M1 keeps its own ``feature_columns``). When None the
        #   M2 reuses ``feature_columns`` (iter-v3/017 / iter-v1/030 behaviour —
        #   backwards-compatible).  When provided, the M2 base feature vector is
        #   built from THESE columns (plus m1_confidence [+ m1_direction]); M1 is
        #   unaffected.  This is the brief §4 wiring-flag #3 clean path (a).
        # m2_veto_threshold: M2 P(win) below which the M1 signal is vetoed.
        #   Default 0.5 (Bayes-optimal, iter-v3/017 / iter-v1/030).  iter-v1/028
        #   sets 0.45 — the de-concentrating sweet spot (brief §2.1, wiring-flag #2).
        m2_feature_columns: list[str] | None = None,
        m2_veto_threshold: float = 0.5,
        # iter-v1/028: trend-state direction + conviction (trend-strength) gate
        # threaded into the INNER M1 LightGbmStrategy so M2 filters the SAME
        # deterministic trend-state primary that merged at iter-027 — NOT the
        # LightGbm-learned direction.  Defaults are a strict NO-OP so iter-v1/030
        # (Models A/C/D) stay bit-identical (brief §4 wiring-flag #1, the #1 risk).
        enable_trend_state_dir: bool = False,
        trend_state_sma_window: int = 200,
        trend_state_symbol: str = "BTCUSDT",
        enable_trend_strength_gate: bool = False,
        trend_strength_atr_window: int = 14,
        trend_strength_quantile: float = 0.50,
        # iter-v1/030: AGREE_SCALE conviction modulator, forwarded to M1's LightGbmStrategy
        # for symmetry. Default False = strict NO-OP (iter-030 EXPLORATION keeps M2 OFF, so
        # this M2 path is not exercised; threaded only so the param surface matches run_model).
        enable_agreement_scale: bool = False,
        # iter-v1/032: SHORT-HORIZON MEAN-REVERSION direction override + vol-regime gate,
        # forwarded to M1's LightGbmStrategy for symmetry. Default False = strict NO-OP
        # (iter-032 EXPLORATION keeps M2 OFF, so this M2 path is not exercised; threaded only
        # so the param surface matches run_model).
        enable_reversion_dir: bool = False,
        reversion_z_window: int = 10,
        enable_reversion_trigger_gate: bool = False,
        reversion_z_threshold: float = 1.5,
        reversion_natr_quantile: float = 0.40,
        reversion_natr_col: str = "vol_natr_14",
        # iter-v1/034: PURE-DETERMINISTIC entry, forwarded to M1's LightGbmStrategy for
        # symmetry. Default False = strict NO-OP (iter-034 EXPLORATION keeps M2 OFF, so this
        # M2 path is not exercised; threaded only so the param surface matches run_model).
        deterministic_entry_only: bool = False,
        # iter-v1/028: M1 must run the SAME specialist bagging stack as the merged
        # iter-027 baseline (K independent Optuna studies via specialist_mode).
        # Defaults (specialist_mode=False) keep /030 bit-identical.
        specialist_mode: bool = False,
        specialist_seed_count: int = 0,
        specialist_n_startup_trials: int = 10,
        specialist_n_estimators_max: int = 500,
        # iter-v1/028: model-role + symbol descriptors threaded into M1 (params parquet).
        model_role: str = "",
        symbol: str = "",
    ) -> None:
        """Initialise MetaLabelingStrategy (M1 + M2 binary classifier).

        Parameters
        ----------
        n_trials_m2
            Optuna trial budget for M2 (separate from M1).  Defaults to
            ``n_trials`` (M1 budget) when None, preserving backwards compat
            with iter-v3/017.  iter-v1/030 passes 18 explicitly per LM
            Master §2.3.
        bounds_profile_m2
            Hyperparameter search bounds for M2.  "v3" = original
            iter-v3/017 ranges.  "v1_030" = LM Master §2 tightened bounds
            with explicit scale_pos_weight.
        include_m1_direction
            When True, append M1's predicted direction (±1 encoded as float)
            to the M2 input vector as a second extra feature after
            m1_confidence.  Makes the M2 feature vector 45-dim for /030
            (43 V1 features + m1_confidence + m1_direction) vs 14-dim for
            v3/017 (13 V3 features + m1_confidence).
        """
        if not feature_columns:
            raise ValueError(
                "feature_columns must be explicitly specified — pass the explicit "
                "V3_FEATURE_COLUMNS list. Auto-discovery disabled for reproducibility."
            )
        if not ensemble_seeds:
            raise ValueError("ensemble_seeds must be a non-empty list of integers.")

        self.training_months = training_months
        self.n_trials = n_trials
        self.feature_columns = feature_columns
        self.ensemble_seeds = ensemble_seeds
        self._fast_mode = fast_mode
        self._verbose = verbose
        # iter-v1/030 additions
        self._n_trials_m2: int = n_trials_m2 if n_trials_m2 is not None else n_trials
        self._bounds_profile_m2: str = bounds_profile_m2
        self._include_m1_direction: bool = include_m1_direction

        # Build M1: full LightGbmStrategy (unchanged from iter-v3/013)
        self._m1 = LightGbmStrategy(
            training_months=training_months,
            n_trials=n_trials,
            cv_splits=cv_splits,
            label_tp_pct=label_tp_pct,
            label_sl_pct=label_sl_pct,
            label_timeout_minutes=label_timeout_minutes,
            fee_pct=fee_pct,
            features_dir=features_dir,
            verbose=verbose,
            atr_tp_multiplier=atr_tp_multiplier,
            atr_sl_multiplier=atr_sl_multiplier,
            atr_column=atr_column,
            ensemble_seeds=ensemble_seeds,
            feature_columns=feature_columns,
            use_atr_labeling=use_atr_labeling,
            ood_enabled=ood_enabled,
            ood_features=ood_features,
            ood_cutoff_pct=ood_cutoff_pct,
            oof_persist_path=oof_persist_path,
            fast_mode=fast_mode,
            label_mode=label_mode,
            trend_scan_grid=trend_scan_grid,
            # v1-specific params threaded through to M1 (iter-v1/030)
            bounds_profile=bounds_profile,
            sigma_source=sigma_source,
            sigma_k_tp=sigma_k_tp,
            sigma_k_sl=sigma_k_sl,
            sigma_halflife_candles=sigma_halflife_candles,
            sample_weight_mode=sample_weight_mode,
            # iter-v1/028: trend-state DIRECTION + conviction (trend-strength) gate
            # threaded into M1 so M2 filters the deterministic iter-027 primary.
            enable_trend_state_dir=enable_trend_state_dir,
            trend_state_sma_window=trend_state_sma_window,
            trend_state_symbol=trend_state_symbol,
            enable_trend_strength_gate=enable_trend_strength_gate,
            trend_strength_atr_window=trend_strength_atr_window,
            trend_strength_quantile=trend_strength_quantile,
            # iter-v1/030: AGREE_SCALE conviction modulator (default OFF; symmetry only).
            enable_agreement_scale=enable_agreement_scale,
            # iter-v1/032: SHORT-HORIZON MEAN-REVERSION override + gate (default OFF; symmetry).
            enable_reversion_dir=enable_reversion_dir,
            reversion_z_window=reversion_z_window,
            enable_reversion_trigger_gate=enable_reversion_trigger_gate,
            reversion_z_threshold=reversion_z_threshold,
            reversion_natr_quantile=reversion_natr_quantile,
            reversion_natr_col=reversion_natr_col,
            # iter-v1/034: PURE-DETERMINISTIC entry (default OFF; symmetry only).
            deterministic_entry_only=deterministic_entry_only,
            # iter-v1/028: M1 runs the SAME specialist bagging stack as iter-027.
            specialist_mode=specialist_mode,
            specialist_seed_count=specialist_seed_count,
            specialist_n_startup_trials=specialist_n_startup_trials,
            specialist_n_estimators_max=specialist_n_estimators_max,
            model_role=model_role,
            symbol=symbol,
        )

        # M1 training-window derived params (read after M1 trains)
        self._fee_pct = fee_pct
        self._atr_tp_multiplier = atr_tp_multiplier

        # iter-v1/028: M2 veto threshold + separate M2 feature set.
        self._m2_veto_threshold: float = float(m2_veto_threshold)
        # M2 base feature columns: the distinct positioning/regime set when given,
        # else M1's own columns (iter-v3/017 / iter-v1/030 backwards-compat).
        self._m2_base_cols: list[str] = (
            list(m2_feature_columns) if m2_feature_columns else list(feature_columns)
        )

        # M2 state per calendar month
        self._m2_model: lgb.LGBMClassifier | None = None
        self._m2_active: bool = False
        _m2_extra_cols = ["m1_confidence"]
        if include_m1_direction:
            _m2_extra_cols.append("m1_direction")
        self._m2_feature_cols: list[str] = list(self._m2_base_cols) + _m2_extra_cols
        # Dict {(symbol, open_time): np.ndarray[14]} — populated per training month
        self._m2_month_features: dict[tuple[str, int], np.ndarray] = {}
        # iter-v1/028: M2 base-feature cache for the test month (M2 base cols only),
        # keyed (symbol, open_time).  Populated in _train_m2_for_month Step 7.
        self._m2_test_month_features: dict[tuple[str, int], np.ndarray] = {}
        # Track current month for lazy M2 training
        self._m2_current_month: str | None = None
        # Last M1 confidence used (for M2 input construction at predict time)
        self._last_m1_confidence: float = 0.0
        # TP PnL threshold for M2 label derivation (set when M1 trains)
        self._tp_pnl_threshold: float = 0.0

    # ------------------------------------------------------------------
    # Public interface (mirrors LightGbmStrategy)
    # ------------------------------------------------------------------

    def compute_features(self, master: pd.DataFrame) -> None:
        """Delegate fully to M1."""
        self._m1.compute_features(master)

    def skip(self) -> None:
        """Delegate to M1."""
        self._m1.skip()

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        """M1 predicts direction; if M1 fires, M2 vets confidence.

        Flow:
          1. Get M1 signal (triggers M1 lazy training if month changed).
          2. After M1 trains for a new month, train M2 on the same window.
          3. If M1 returns NO_SIGNAL, return NO_SIGNAL (no M2 query needed).
          4. If M1 fires: build M2 input (M2 base features + M1 confidence
             [+ M1 direction]); if M2 confidence >= ``self._m2_veto_threshold``,
             pass signal through; else veto.
        """
        candle_month = _epoch_ms_to_month(open_time)

        # M1 trains internally within get_signal when month changes
        m1_signal = self._m1.get_signal(symbol, open_time)

        # After M1 has trained for this month, train M2 if we haven't yet
        if candle_month != self._m2_current_month:
            self._train_m2_for_month(candle_month)
            self._m2_current_month = candle_month

        # If M1 returns no signal, M2 is not queried
        if m1_signal is NO_SIGNAL:
            return NO_SIGNAL

        # M2 is inactive (e.g., training failed) → trust M1
        if not self._m2_active or self._m2_model is None:
            if self._verbose > 0:
                print(f"  [M2] inactive for {candle_month} — passing M1 signal")
            return m1_signal

        # Build M2 input: 14-dim vector
        m2_feat = self._get_m2_features(symbol, open_time)
        if m2_feat is None:
            # Missing M2 feature cache entry → trust M1
            return m1_signal

        # M2 prediction
        feat_df = pd.DataFrame(m2_feat.reshape(1, -1), columns=self._m2_feature_cols)
        m2_proba = self._m2_model.predict_proba(feat_df)[0]
        m2_confidence = float(m2_proba[1])  # P(TP-hit)

        thr = self._m2_veto_threshold
        if m2_confidence < thr:
            if self._verbose > 0:
                import datetime as _dt  # noqa: PLC0415

                ts_str = _dt.datetime.fromtimestamp(open_time / 1000, tz=_dt.UTC).strftime(
                    "%Y-%m-%d %H:%M"
                )
                print(
                    f"  [M2] {ts_str} {symbol} → VETOED (M2 conf={m2_confidence:.3f} < {thr:.2f})"
                )
            return NO_SIGNAL

        if self._verbose > 0:
            import datetime as _dt  # noqa: PLC0415

            ts_str = _dt.datetime.fromtimestamp(open_time / 1000, tz=_dt.UTC).strftime(
                "%Y-%m-%d %H:%M"
            )
            print(f"  [M2] {ts_str} {symbol} → PASSED (M2 conf={m2_confidence:.3f} >= {thr:.2f})")
        return m1_signal

    # ------------------------------------------------------------------
    # M2 training (called when month changes)
    # ------------------------------------------------------------------

    def _train_m2_for_month(self, month_str: str) -> None:
        """Train M2 binary classifier on the training window for month_str.

        Steps (per brief §2.4 pseudocode):
          1. Re-use M1's training state (_models, _confidence_thresholds,
             _all_feature_cols, _split_map) from the just-completed M1 training.
          2. Re-run M1 inference on the training window to identify M1-positive bars.
          3. Derive M2 labels: 1 if the M1-predicted direction hit TP first,
             0 if SL or timeout hit first (binary from label_trades output).
          4. Build M2 features: 14-dim = 13 V3 features + M1 confidence.
          5. Train M2 LGBMClassifier on M1-positive subset.
          6. Populate self._m2_month_features with 14-dim test-month feature vectors.

        Look-ahead safety: all operations use ONLY M1._split_map[month_str].train_*
        data, never the test window.
        """
        self._m2_model = None
        self._m2_active = False
        self._m2_month_features = {}
        self._m2_test_month_features = {}

        if not self._m1._models:
            if self._verbose > 0:
                print(f"  [M2] M1 has no models for {month_str} — M2 skipped")
            return

        split = self._m1._split_map.get(month_str)
        if split is None:
            if self._verbose > 0:
                print(f"  [M2] No split for {month_str} — M2 skipped")
            return

        if self._verbose > 0:
            print(f"  [M2] Building M2 labels for {month_str}")

        # Step 1: retrieve M1 training window indices
        open_time_arr = self._m1._open_time_arr
        sym_arr = self._m1._sym_arr
        train_indices = np.where(
            (open_time_arr >= split.train_start_ms) & (open_time_arr < split.train_end_ms)
        )[0]

        if len(train_indices) < 10:
            if self._verbose > 0:
                print(f"  [M2] Insufficient training indices ({len(train_indices)}) — M2 skipped")
            return

        # Step 2: get M1 features for the training window
        from crypto_trade.feature_store import lookup_features  # noqa: PLC0415

        train_lookups = [(str(sym_arr[i]), int(open_time_arr[i])) for i in train_indices]
        train_feat_df = lookup_features(train_lookups, self._m1.features_dir, self._m1._interval)
        if train_feat_df.empty:
            if self._verbose > 0:
                print("  [M2] No features found for training window — M2 skipped")
            return

        # Align with M1's training (same keep_mask logic)
        feat_keys = set(zip(train_feat_df["symbol"], train_feat_df["open_time"]))
        keep_mask = np.array(
            [(str(sym_arr[i]), int(open_time_arr[i])) in feat_keys for i in train_indices]
        )
        train_indices_kept = train_indices[keep_mask]

        if len(train_indices_kept) < 10:
            if self._verbose > 0:
                print(
                    f"  [M2] After feature alignment, only "
                    f"{len(train_indices_kept)} samples — M2 skipped"
                )
            return

        available_feat_cols = self._m1._selected_cols
        if not available_feat_cols:
            available_feat_cols = [
                c for c in self._m1._all_feature_cols if c in train_feat_df.columns
            ]
        feat_train = train_feat_df[available_feat_cols].values

        # iter-v1/028: build the M2 base-feature matrix from the DISTINCT M2 column
        # set (positioning/leverage/regime).  Same train_feat_df rows (identical
        # look-ahead discipline — bounded by split.train_end_ms) but different
        # columns from M1.  When _m2_base_cols == M1 cols this is bit-identical to
        # the iter-v3/017 / iter-v1/030 path.
        _m2_missing = [c for c in self._m2_base_cols if c not in train_feat_df.columns]
        if _m2_missing:
            if self._verbose > 0:
                print(f"  [M2] M2 feature columns missing from parquet {_m2_missing} — M2 skipped")
            return
        m2_feat_train = train_feat_df[self._m2_base_cols].values

        # Step 3: M1 inference on training window to get M1-positive mask
        # Use first M1 ensemble model + mean confidence_threshold
        m1_confidence_threshold = float(np.mean(self._m1._confidence_thresholds))
        feat_train_df = pd.DataFrame(feat_train, columns=available_feat_cols)
        all_proba_train = [m.predict_proba(feat_train_df) for m in self._m1._models]
        m1_proba_train = np.mean(all_proba_train, axis=0)  # [n_train, 2]
        m1_confidence_arr = m1_proba_train.max(axis=1)  # [n_train]
        m1_positive_mask = m1_confidence_arr >= m1_confidence_threshold

        n_m1_pos = int(m1_positive_mask.sum())
        if self._verbose > 0:
            print(
                f"  [M2] M1-positive bars: {n_m1_pos}/{len(train_indices_kept)} "
                f"(threshold={m1_confidence_threshold:.3f})"
            )

        if n_m1_pos < 5:
            if self._verbose > 0:
                print(f"  [M2] Too few M1-positive bars ({n_m1_pos}) — M2 skipped")
            return

        # Step 4: derive M2 binary labels from triple-barrier outcomes
        # Re-run label_trades on the kept training indices (same parameters as M1)
        from crypto_trade.strategies.ml.labeling import label_trades  # noqa: PLC0415

        label_atr = self._m1._label_atr_values if self._m1._label_atr_values is not None else None
        if label_atr is not None:
            label_tp = self._m1.atr_tp_multiplier
            label_sl = self._m1.atr_sl_multiplier or (self._m1.atr_tp_multiplier / 2.0)
        else:
            label_tp = self._m1.label_tp_pct
            label_sl = self._m1.label_sl_pct

        _, _, long_pnls, short_pnls = label_trades(
            self._m1._master,
            train_indices_kept,
            label_tp,
            label_sl,
            self._m1.label_timeout_minutes,
            fee_pct=self._m1.fee_pct,
            atr_values=label_atr,
            verbose=0,
        )

        # M2 label derivation: 1 if M1-predicted direction hit TP first
        # TP threshold: long_pnl > -fee_pct (positive outcome = TP hit)
        # The labeler returns long_pnls in [-sl_pct - fee, tp_pct - fee] range.
        # TP hit iff long_pnl >= (tp_pnl - fee - small_tolerance).
        # We use: long_pnl > 0 (fee already deducted; TP gives positive net return,
        # SL and timeout give negative or near-zero net return).
        m1_pred_classes = np.argmax(m1_proba_train, axis=1)  # 0=short, 1=long
        m2_labels_full = np.zeros(len(train_indices_kept), dtype=np.int32)
        for flat_i in np.where(m1_positive_mask)[0]:
            direction_cls = int(m1_pred_classes[flat_i])
            if direction_cls == 1:  # long prediction
                pnl = float(long_pnls[flat_i])
            else:  # short prediction
                pnl = float(short_pnls[flat_i])
            # TP hit iff net return > 0 (fee already deducted by label_trades)
            m2_labels_full[flat_i] = 1 if pnl > 0.0 else 0

        # Step 5: build M2 features for positive subset
        # Dim = len(_m2_base_cols) + 1 (m1_confidence) [+ 1 (m1_direction) if enabled]
        # iter-v1/028: M2 base features come from the DISTINCT M2 column matrix
        # (m2_feat_train), NOT M1's feature matrix (feat_train).
        m2_pos_idx = np.where(m1_positive_mask)[0]
        feat_train_m1_pos = m2_feat_train[m2_pos_idx]  # [n_m1_pos, n_m2_base_features]
        m1_conf_m1_pos = m1_confidence_arr[m2_pos_idx]  # [n_m1_pos]
        extra_cols = [m1_conf_m1_pos.reshape(-1, 1)]
        if self._include_m1_direction:
            # m1_direction: +1.0 = long predicted, -1.0 = short predicted
            m1_pred_cls_arr = np.argmax(m1_proba_train, axis=1)  # [n_train]
            m1_dir_m1_pos = np.where(m1_pred_cls_arr[m2_pos_idx] == 1, 1.0, -1.0).reshape(-1, 1)
            extra_cols.append(m1_dir_m1_pos)
        m2_features_pos = np.concatenate([feat_train_m1_pos, *extra_cols], axis=1)
        m2_labels_pos = m2_labels_full[m2_pos_idx]

        if self._verbose > 0:
            n_tp = int((m2_labels_pos == 1).sum())
            print(
                f"  [M2] M2 positive-class prior: "
                f"{n_tp}/{n_m1_pos} = {100 * n_tp / n_m1_pos:.1f}% TP-hit rate"
            )

        # Step 6: train M2 with Optuna
        # Use first ensemble seed (same single-seed pattern as EXPLORATION M1)
        m2_seed = self._m1.ensemble_seeds[0]
        m2_model = _train_m2_binary(
            m2_features=m2_features_pos,
            m2_labels=m2_labels_pos,
            n_trials=self._n_trials_m2,
            seed=m2_seed,
            fast_mode=self._fast_mode,
            verbose=self._verbose,
            bounds_profile=self._bounds_profile_m2,
        )

        if m2_model is None:
            # Per LM Master §9 Q8 item 6: log M2_TRAINED status with month_str.
            print(
                f"  [M2] M2_TRAINED=False month={month_str} n_pos={n_m1_pos} "
                f"n_samples={len(m2_features_pos)} (training returned None)"
            )
            return

        self._m2_model = m2_model
        self._m2_active = True

        # Step 7: populate M2 test-month base-feature cache.
        # iter-v1/028: M2 reads a DISTINCT base-feature set (_m2_base_cols) from
        # M1, so we load the M2 base columns for the TEST window from the parquet
        # keyed (symbol, open_time) — the same rows the engine sees at decision
        # time.  Look-ahead-safe: the test window (split.test_start_ms ..
        # split.test_end_ms) is disjoint from the M2 TRAINING window, and the
        # parquet feature columns are past-only by construction.  The extra
        # features (M1 confidence [+ M1 direction]) are appended at predict time
        # in _get_m2_features.
        from crypto_trade.feature_store import load_features_range  # noqa: PLC0415

        test_symbols = list(dict.fromkeys(self._m1._sym_arr))
        self._m2_test_month_features = load_features_range(
            test_symbols,
            self._m1.features_dir,
            self._m1._interval,
            split.test_start_ms,
            split.test_end_ms,
            columns=list(self._m2_base_cols),
        )
        self._m2_month_features = {}  # legacy field retained (unused for /028 path)

        # Per LM Master §9 Q8 item 6: log M2_TRAINED status with month_str.
        print(
            f"  [M2] M2_TRAINED=True month={month_str} n_pos={n_m1_pos} "
            f"n_samples={len(m2_features_pos)} n_trials_m2={self._n_trials_m2} "
            f"bounds={self._bounds_profile_m2}"
        )

    def _get_m2_features(self, symbol: str, open_time: int) -> np.ndarray | None:
        """Build N-dim M2 input for the given candle.

        iter-v1/028: the M2 BASE feature row comes from ``_m2_test_month_features``
        (the DISTINCT M2 positioning/regime column set loaded for the test month),
        NOT M1's feature row.  Appended:
          - M1's prediction probability (m1_confidence) — always present.
          - M1's predicted direction as float (m1_direction) — only when
            ``include_m1_direction=True``.

        M1 confidence/direction are computed from M1's OWN cached feature row
        (M1._month_features + M1._models) — unchanged.  This is look-ahead-safe:
        both rows are the test-month parquet values the engine reads at decision
        time, and the M2 model was trained only on the disjoint training window.

        Returns None if the candle is not in either feature cache.
        """
        key = (symbol, open_time)

        # M1 confidence/direction from M1's cached row (M1 columns).
        m1_feat_row = self._m1._month_features.get(key)
        if m1_feat_row is None:
            return None
        feat_df = pd.DataFrame(m1_feat_row.reshape(1, -1), columns=self._m1._selected_cols)
        all_proba = [m.predict_proba(feat_df)[0] for m in self._m1._models]
        m1_proba = np.mean(all_proba, axis=0)
        m1_confidence = float(m1_proba.max())
        # m1_direction: +1.0 for long prediction (class index 1), -1.0 for short (class index 0)
        m1_pred_cls = int(np.argmax(m1_proba))
        m1_direction = 1.0 if m1_pred_cls == 1 else -1.0

        # M2 base feature row from the DISTINCT M2 column cache.
        m2_base_row = self._m2_test_month_features.get(key)
        if m2_base_row is None:
            return None

        extra = [m1_confidence]
        if self._include_m1_direction:
            extra.append(m1_direction)

        m2_input = np.concatenate([m2_base_row, extra])
        return m2_input

    # ------------------------------------------------------------------
    # M1 delegation (iter-v1/028): the universal single-symbol routing guard
    # and the post-dispatch feature-importance / specialist-dispersion writers
    # read these attributes/methods directly off the strategy object.  When the
    # strategy is a MetaLabelingStrategy they must transparently forward to the
    # inner M1 LightGbmStrategy (which IS the specialist bagging model + the
    # feature-importance source).  M2 importance is tracked separately by the
    # design analysis scripts (m2_feature_importance.csv), not by this writer.
    # ------------------------------------------------------------------

    @property
    def _specialist_models(self) -> list:
        return self._m1._specialist_models

    @property
    def _models(self) -> list:
        return self._m1._models

    @property
    def _selected_cols(self) -> list[str]:
        return self._m1._selected_cols

    @property
    def _per_month_fi_log(self) -> list:
        return getattr(self._m1, "_per_month_fi_log", [])

    @property
    def _nan_skip_log(self) -> list:
        return getattr(self._m1, "_nan_skip_log", [])

    def get_specialist_dispersion_mean(self) -> float | None:
        return self._m1.get_specialist_dispersion_mean()

    def persist_specialist_dispersion_csv(self, path: str) -> None:
        self._m1.persist_specialist_dispersion_csv(path)
