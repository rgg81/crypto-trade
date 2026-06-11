"""LightGbmStrategy: ML-based strategy with lazy monthly walk-forward retraining."""

from __future__ import annotations

import datetime
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from crypto_trade.backtest_models import Signal
from crypto_trade.feature_store import load_features_range, lookup_features
from crypto_trade.strategies import NO_SIGNAL
from crypto_trade.strategies.ml.labeling import compute_sample_uniqueness, label_trades
from crypto_trade.strategies.ml.optimization import (
    classes_to_labels,
    labels_to_classes,
    labels_to_classes_ternary,
    optimize_and_train,
)
from crypto_trade.strategies.ml.sample_weighting import (
    compute_composite_inv_concurrency_weights,
)
from crypto_trade.strategies.ml.walk_forward import (
    MonthSplit,
    compute_embargo_candles,
    generate_monthly_splits,
)

# Columns that are metadata, not features
_META_COLUMNS = frozenset(
    {
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "close_time",
        "volume",
        "quote_volume",
        "trades",
        "taker_buy_volume",
        "taker_buy_quote_volume",
        "symbol",
    }
)


def _discover_feature_columns(
    features_dir: str,
    interval: str,
    symbols: list[str] | None = None,
) -> list[str]:
    """Discover feature columns present in ALL Parquet files (intersection).

    If *symbols* is provided, only scan those symbols' files instead of all
    files in the directory.
    """
    from pathlib import Path

    d = Path(features_dir)
    if symbols:
        parquet_files = [
            d / f"{sym}_{interval}_features.parquet"
            for sym in symbols
            if (d / f"{sym}_{interval}_features.parquet").exists()
        ]
    else:
        parquet_files = list(d.glob(f"*_{interval}_features.parquet"))
    if not parquet_files:
        raise FileNotFoundError(
            f"No Parquet feature files found in {features_dir} for interval {interval}"
        )

    first_schema = pq.read_schema(parquet_files[0])
    common: set[str] = {n for n in first_schema.names if n not in _META_COLUMNS}
    for pf in parquet_files[1:]:
        schema = pq.read_schema(pf)
        common &= set(schema.names)

    return [n for n in first_schema.names if n in common]


def _epoch_ms_to_month(open_time: int) -> str:
    """Convert epoch milliseconds to 'YYYY-MM' string."""
    return datetime.datetime.fromtimestamp(open_time / 1000, tz=datetime.UTC).strftime("%Y-%m")


def _ms_to_date(ms: int) -> str:
    """Convert epoch milliseconds to 'YYYY-MM-DD' string."""
    return datetime.datetime.fromtimestamp(ms / 1000, tz=datetime.UTC).strftime("%Y-%m-%d")


def _ms_to_datetime(ms: int) -> str:
    """Convert epoch milliseconds to 'YYYY-MM-DD HH:MM' string."""
    return datetime.datetime.fromtimestamp(ms / 1000, tz=datetime.UTC).strftime("%Y-%m-%d %H:%M")


# ---------------------------------------------------------------------------
# iter-v1/063 SPECIALIST + BUNDLE methodology constants
# ---------------------------------------------------------------------------

#: Number of independent Optuna studies in SPECIALIST mode (one per seed).
V1_SPECIALIST_SEED_COUNT: int = 50

#: Optuna n_trials per seed/study in SPECIALIST mode.
V1_SPECIALIST_OPTUNA_TRIALS: int = 30

#: Deterministic 50-seed roster for SPECIALIST mode (42..91 inclusive).
V1_SPECIALIST_SEEDS: tuple[int, ...] = tuple(range(42, 42 + V1_SPECIALIST_SEED_COUNT))

#: H2 fix — maximum number of per-seed failures tolerated before raising.
#: If more than this many seeds fail in a single _train_for_month call,
#: SpecialistSeedFailureError is raised rather than silently continuing.
#: Rationale: 5 of 50 seeds failing is plausible (10%); 6+ is a systematic
#: data or environment issue that must not produce a quietly-degraded model.
V1_SPECIALIST_SEED_TOLERANCE: int = 5


class SpecialistSeedFailureError(RuntimeError):
    """Raised when more than V1_SPECIALIST_SEED_TOLERANCE seeds fail in one month.

    H2 fix: converts the previously-silent degradation into a fail-loud signal
    so callers (runners, tests) can distinguish a healthy partial-failure
    (≤ tolerance) from a systematic environment or data corruption issue.
    """

    def __init__(self, failed: int, tolerance: int, month_str: str, seeds: list[str]) -> None:
        self.failed = failed
        self.tolerance = tolerance
        self.month_str = month_str
        self.seeds = seeds
        super().__init__(
            f"[SPECIALIST] {failed} seed(s) failed for {month_str} "
            f"(tolerance={tolerance}). Failed seeds: {seeds}. "
            "Investigate data / environment before re-running."
        )


_INTERVAL_MINUTES = {
    "1m": 1,
    "3m": 3,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "4h": 240,
    "8h": 480,
    "12h": 720,
    "1d": 1440,
    "24h": 1440,  # iter-v3/117: alias for "1d" — 24h bar interval for candle-frequency axis
}


def _interval_to_minutes(interval: str) -> int:
    """Convert interval string to minutes."""
    return _INTERVAL_MINUTES.get(interval, 480)


def conviction_derate(
    confidence: float,
    c_floor: float = 0.50,
    c_ref: float = 0.65,
    w_min_frac: float = 0.50,
) -> int:
    """Conviction-DERATE map (iter-v3/079 primitive 13).

    Maps the M1 ensemble's directional confidence scalar to a per-trade weight
    in [50, 100].  The map is monotone non-decreasing in confidence and is a
    pure de-rate: it never levers above the flat weight=100 baseline.

    Parameters (a-priori, data-free constants):
        c_floor    = 0.50  — coin-flip line → weight floor.
        c_ref      = 0.65  — clear-conviction reference → full weight (100).
        w_min_frac = 0.50  — weight floor as a fraction of 100.

    Formula:
        weight = round( 100 * clip( (confidence - c_floor) / (c_ref - c_floor),
                                    w_min_frac, 1.0 ) )

    Returns int in [50, 100] (compatible with Signal.weight int contract).
    """
    return round(100 * float(np.clip((confidence - c_floor) / (c_ref - c_floor), w_min_frac, 1.0)))


class LightGbmStrategy:
    """LightGBM strategy with lazy monthly walk-forward retraining."""

    def __init__(
        self,
        training_months: int = 12,
        n_trials: int = 50,
        cv_splits: int = 5,
        label_tp_pct: float = 4.0,
        label_sl_pct: float = 2.0,
        label_timeout_minutes: int = 4320,
        fee_pct: float = 0.1,
        features_dir: str = "data/features",
        verbose: int = 0,
        atr_tp_multiplier: float | None = None,
        atr_sl_multiplier: float | None = None,
        atr_column: str = "vol_natr_21",
        ensemble_seeds: list[int] | None = None,
        neutral_threshold_pct: float | None = None,
        cv_label_gap: bool = True,
        feature_columns: list[str] | None = None,
        sample_uniqueness: bool = False,
        time_decay_half_life: float | None = None,
        use_atr_labeling: bool = False,
        min_natr_threshold: float | None = None,
        ood_enabled: bool = False,
        ood_features: list[str] | None = None,
        ood_cutoff_pct: float = 0.70,
        oof_persist_path: Path | None = None,
        fast_mode: bool = False,
        inference_threshold_floor: float = 0.0,
        label_mode: str = "triple_barrier",
        trend_scan_grid: tuple[int, ...] = (5, 8, 13, 21),
        bounds_profile: str = "default",
        sigma_source: str = "natr",
        sigma_k_tp: float | None = None,
        sigma_k_sl: float | None = None,
        sigma_halflife_candles: int = 42,
        sample_weight_mode: str = "abs_pnl",
        params_persist_path: Path | None = None,
        model_role: str = "",
        symbol: str = "",
        data_filter_callback: Callable[[pd.DataFrame], np.ndarray] | None = None,
        data_filter_columns: list[str] | None = None,
        nan_skip_columns: list[str] | None = None,
        nan_skip_threshold: float = 0.5,
        frozen_hp_parquet: Path | None = None,
        optuna_objective: str = "sharpe",
        min_child_samples_lower_bound: int | None = None,
        specialist_mode: bool = False,
        specialist_n_startup_trials: int = 10,
        specialist_n_estimators_max: int = 500,
        # iter-v1/074: AXIS-R — Mid-Bull SHORT VETO post-aggregator rule layer.
        # When True, direction==-1 signals are vetoed when ret_270b ∈ [lo, hi].
        # ret_270b = (close[t] / close[t - lookback]) - 1.0 on 8h candles (90-day trailing return).
        # Pre-registered band edges [0.20, 0.50] frozen at brief authoring.
        # Default False = BIT-IDENTICAL to all prior runs.
        enable_mid_bull_short_veto: bool = False,
        mid_bull_short_veto_lo: float = 0.20,
        mid_bull_short_veto_hi: float = 0.50,
        mid_bull_short_veto_lookback: int = 270,
        # iter-v1/084: R-FADE — OI-divergence-conditional confidence gate.
        # When True, entry is VETOED when sign(signal) OPPOSES sign(oi_price_divergence_30[t])
        # AND |oi_price_divergence_30[t]| > fade_z (IS-calibrated, pre-registered).
        # Reuses the AXIS-R /074 gate pattern: post-aggregator, stateless, identical in
        # backtest and live (parity-clean). Default False = BIT-IDENTICAL to all prior runs.
        # ONLY enabled in the CRV specialist cell (iter-v1/084 dispatch).
        enable_oi_divergence_fade_gate: bool = False,
        oi_divergence_fade_z: float = 2.0,  # pre-registered IS-calibrated threshold
        oi_divergence_fade_column: str = "oi_price_divergence_30",
        # iter-v1/091: R-CONV — ensemble-conviction trade gate.
        # When True, candles whose net seed-agreement fraction _sp_confidence < r_conv_tau
        # are SKIPPED (return NO_SIGNAL) in the SPECIALIST path. Stateless post-aggregator
        # RULE layer (same band as /074 AXIS-R + /084 R-FADE). Does NOT change the model,
        # seeds, trials, or Optuna objective. Default False = BIT-IDENTICAL to all prior runs.
        # Pre-registered tau=0.06 (IS-only basis; 67 IS trades in [0,0.06) = net-losing bucket).
        # ONLY enabled in the ETH specialist cell (iter-v1/091 dispatch).
        enable_r_conv_gate: bool = False,
        r_conv_tau: float = 0.06,  # pre-registered IS-calibrated threshold
    ) -> None:
        if not feature_columns:
            raise ValueError(
                "feature_columns must be explicitly specified — auto-discovery "
                "is disabled to guarantee reproducibility across parquet "
                "schema changes. Pass an explicit list of column names."
            )
        if not ensemble_seeds:
            raise ValueError(
                "ensemble_seeds must be a non-empty list of integers. Pass the "
                "production list (e.g. [42, 123, 456, 789, 1001]) to ensemble "
                "across seeds, or [42] for a single-seed run."
            )
        self.training_months = training_months
        self.n_trials = n_trials
        self.cv_splits = cv_splits
        self.label_tp_pct = label_tp_pct
        self.label_sl_pct = label_sl_pct
        self.label_timeout_minutes = label_timeout_minutes
        self.fee_pct = fee_pct
        self.features_dir = features_dir
        self.verbose = verbose
        self.atr_tp_multiplier = atr_tp_multiplier
        self.atr_sl_multiplier = atr_sl_multiplier
        self.atr_column = atr_column
        self.ensemble_seeds = ensemble_seeds
        self.neutral_threshold_pct = neutral_threshold_pct
        self.cv_label_gap = cv_label_gap
        self.feature_columns = feature_columns
        self.sample_uniqueness = sample_uniqueness
        self.time_decay_half_life = time_decay_half_life
        self.use_atr_labeling = use_atr_labeling
        self.min_natr_threshold = min_natr_threshold
        self.ood_enabled = ood_enabled
        self.ood_features = list(ood_features) if ood_features else None
        self.ood_cutoff_pct = ood_cutoff_pct
        # iter-v3/003: path for per-trial OOF return persistence (sub-fix 1c)
        self._oof_persist_path: Path | None = oof_persist_path
        # iter-v1/021: path for Optuna best_params persistence (pool-anchor H1 diagnostic)
        self._params_persist_path: Path | None = params_persist_path
        # iter-v1/021: model role string embedded in params parquet rows
        # (e.g. "Model_A_pool", "Model_H_BTC"). Runner sets this when constructing strategy.
        self._model_role: str = model_role
        # iter-v1/021: symbol descriptor embedded in params parquet rows
        # For pooled models (A), caller passes e.g. "BTC+ETH"; for single-cohort
        # models (H), caller passes the single symbol (e.g. "BTCUSDT").
        self._symbol: str = symbol
        # iter-v1/024: optional training-data partition callback.
        # Callable[[pd.DataFrame], np.ndarray] — receives a DataFrame whose
        # columns include at minimum the kline columns from master PLUS any
        # columns listed in data_filter_columns (loaded from parquet and merged
        # before calling the callback).  Applied BEFORE labeling in
        # _train_for_month().  Default None = no filter (backward-compatible;
        # bit-identical to all pre-/024 runs).
        self._data_filter_callback: Callable[[pd.DataFrame], np.ndarray] | None = (
            data_filter_callback
        )
        # iter-v1/024: list of feature-parquet columns that must be present in
        # the DataFrame passed to data_filter_callback.  When non-empty, these
        # columns are loaded from parquet (via lookup_features) and left-joined
        # onto the master slice before calling the callback.  Required because
        # self._master is built from kline CSVs only and does NOT contain
        # feature columns such as funding_rate_zscore_30.
        self._data_filter_columns: list[str] | None = (
            list(data_filter_columns) if data_filter_columns else None
        )
        # iter-v1/025: per-(symbol, month) NaN-fraction skip guard.
        # When set, any symbol whose training-fold slice has > nan_skip_threshold
        # fraction of NaN values in ANY of the listed columns is excluded from
        # that month's training fold.  Default None = no guard (backward-compat).
        # Implements LM Master §5(a) ADOPTED recommendation for oi_delta_30_z90.
        self._nan_skip_columns: list[str] | None = (
            list(nan_skip_columns) if nan_skip_columns else None
        )
        self._nan_skip_threshold: float = float(nan_skip_threshold)
        # Accumulates per-(symbol, month) NaN-fraction rows for oi_coverage_check.csv.
        # Keys: symbol, month, column, nan_fraction, skipped.
        self._nan_skip_log: list[dict] = []
        # iter-v1/032: frozen HP parquet path for basin-lottery ablation.
        # When set, Optuna search is SKIPPED entirely. Per (model, month, inner_seed)
        # the pre-extracted best hyperparameters from the baseline run are used to
        # train LightGBM directly. Only sample_weight_mode varies vs the baseline.
        # None = normal Optuna search (default, backward-compatible).
        self._frozen_hp_parquet: Path | None = frozen_hp_parquet
        # Cached DataFrame (loaded once on first _train_for_month call).
        self._frozen_hp_df: pd.DataFrame | None = None
        # iter-v3/007: fast exploration mode (colsample fixed at 1.0 in optimization.py)
        self._fast_mode: bool = fast_mode
        # iter-v1/002: Optuna hyperparameter bounds profile.
        # "default" = original 193-feature bounds (all tracks except v1_pruned).
        # "v1_pruned" = tighter bounds for 40-feature pruned set per LM Master
        # Phase 4.5 Recs #1–3. Forwarded to optimization.optimize_and_train.
        self._bounds_profile: str = bounds_profile
        # iter-v1/037: Optuna study objective metric.
        # "sharpe" (default) = mean/std — BIT-IDENTICAL to all pre-/037 callers.
        # "sortino" = mean/downside_std — loss-function axis (NEW 12th family).
        if optuna_objective not in ("sharpe", "sortino"):
            raise ValueError(
                f"optuna_objective must be 'sharpe' or 'sortino'; got {optuna_objective!r}"
            )
        self._optuna_objective: str = optuna_objective
        # iter-v1/041: Optuna min_child_samples lower bound override.
        # None = BIT-IDENTICAL to prior behaviour (20 for v1_pruned, 5 for default).
        # Set to 50 for iter-v1/041 triple-barrier tighten (denser-label noise mitigation:
        # larger leaf populations average out per-leaf noise from shorter-horizon labels).
        self._min_child_samples_lower_bound: int | None = min_child_samples_lower_bound
        # iter-v1/063: SPECIALIST + BUNDLE methodology flag.
        # When True, _train_for_month runs V1_SPECIALIST_SEED_COUNT independent Optuna
        # studies (one per seed in V1_SPECIALIST_SEEDS) each with
        # n_trials=V1_SPECIALIST_OPTUNA_TRIALS.
        # max_depth=5 FIXED, num_leaves=31 FIXED, min_child_samples NOT in search space.
        # get_signal aggregates via mean-of-signed-weights across 50 seeds.
        # Default False = old behavior (backward-compatible for v2/v3 and prior v1).
        self._specialist_mode: bool = bool(specialist_mode)
        # Wall-clock mitigation: n_startup_trials for TPESampler in specialist mode.
        self._specialist_n_startup_trials: int = int(specialist_n_startup_trials)
        # Wall-clock mitigation: upper bound on n_estimators in specialist mode.
        self._specialist_n_estimators_max: int = int(specialist_n_estimators_max)
        # Per-seed specialist state: list of (model, selected_cols, threshold) tuples.
        # Reset every _train_for_month call when specialist_mode=True.
        self._specialist_models: list[tuple[object, list[str], float]] = []
        # H2 fix: track per-seed failures across the walk-forward timeline.
        # Each entry is (seed: int, exc_repr: str) — accumulated globally (not reset
        # per month) so runners can inspect cumulative failure history.
        self._failed_seeds_log: list[tuple[int, str]] = []
        # H2 fix: number of successfully-trained seeds per walk-forward month.
        # Appended once per _train_for_month call in specialist mode.
        # Used by get_n_seeds_used_mean() to produce the N_seeds_used comparison.csv row.
        self._seeds_used_per_month: list[int] = []
        # iter-v1/063: per-candle ensemble dispersion diagnostic.
        # Accumulates population std of signed_weights for every candle that fires a
        # specialist signal (i.e. abs(final_signed) >= 1e-9) AND passes the AXIS-R veto.
        # Informational only — NOT a gate.  For /064+ briefs, F-AXIS #2 σ_pop SHOULD
        # cite get_specialist_dispersion_mean() as the σ_pop proxy rather than
        # cross-seed Sharpe spread (which is structurally undefined under the
        # 50-seed aggregator producing a single backtest).
        # H8/H9 fix: each entry is a dict with keys:
        #   open_time_ms: int   — candle open time (epoch ms)
        #   signed_weight_std: float — population std of signed_weights
        #   period: str         — "IS" or "OOS" (set by set_period() at IS/OOS boundary)
        # Append happens AFTER AXIS-R veto so vetoed candles are excluded.
        self._specialist_dispersion_stats: list[dict] = []
        # H8/H9 fix: tracks the current evaluation period ("IS" or "OOS").
        # Callers must call set_period("OOS") at the OOS_CUTOFF_DATE boundary.
        # Defaults to "IS" so pre-boundary candles are always tagged correctly.
        self._current_period: str = "IS"
        # iter-v1/074: AXIS-R — Mid-Bull SHORT VETO post-aggregator rule layer.
        # Enabled via enable_mid_bull_short_veto=True (SPECIALIST + /074 dispatch only).
        # Band edges pre-registered [0.20, 0.50]; lookback 270 8h candles = 90 calendar days.
        # Deterministic post-aggregator filter: does NOT change Optuna training-objective domain.
        self._enable_mid_bull_short_veto: bool = bool(enable_mid_bull_short_veto)
        self._mid_bull_short_veto_lo: float = float(mid_bull_short_veto_lo)
        self._mid_bull_short_veto_hi: float = float(mid_bull_short_veto_hi)
        self._mid_bull_short_veto_lookback: int = int(mid_bull_short_veto_lookback)
        # Per-symbol sorted (open_time_ms, close) arrays for O(log n) lookback queries.
        # Populated in compute_features(); keyed by symbol string.
        self._close_by_sym: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        # Veto event log: list of (symbol, open_time_ms, ret_270b) for F-AXIS-COUNTERFACTUAL audit.
        self._axis_r_veto_log: list[dict] = []
        # iter-v1/084: R-FADE — OI-divergence-conditional confidence gate.
        # Enabled via enable_oi_divergence_fade_gate=True (CRV specialist cell only).
        # fade_z: |oi_price_divergence_30| threshold (default 2.0; IS-calibrated pre-registered).
        # fade_column: name of the divergence feature column (default "oi_price_divergence_30").
        # Stateless post-aggregator gate; does NOT change Optuna training-objective domain.
        self._enable_oi_divergence_fade_gate: bool = bool(enable_oi_divergence_fade_gate)
        self._oi_divergence_fade_z: float = float(oi_divergence_fade_z)
        self._oi_divergence_fade_column: str = str(oi_divergence_fade_column)
        # R-FADE event log: list of dicts for IS calibration audit.
        self._oi_divergence_fade_log: list[dict] = []
        # iter-v1/091: R-CONV — ensemble-conviction trade gate.
        # Enabled via enable_r_conv_gate=True (ETH specialist cell only; iter-v1/091 dispatch).
        # r_conv_tau: _sp_confidence threshold (default 0.06; IS-calibrated, pre-registered).
        # Stateless post-aggregator gate; does NOT change Optuna training-objective domain.
        # Applied AFTER _sp_confidence is computed and BEFORE the Signal is built (same
        # post-aggregator RULE-layer band as /074 AXIS-R + /084 R-FADE).
        # r_conv_skip decision_log entries carry ensemble_std so the dropped set can be
        # split by abstention vs disagreement in Phase 7.4 (LM §1 REQUIRED deliverable).
        self._enable_r_conv_gate: bool = bool(enable_r_conv_gate)
        self._r_conv_tau: float = float(r_conv_tau)
        # iter-v3/072: labeling mode — "triple_barrier" (default, backward-compat)
        # or "fixed_horizon" (sign of N-candle-forward return; no barriers).
        # iter-v3/105: "trend_scanning" (OLS trend, max-|t| horizon selection
        # from *trend_scan_grid*). When label_mode != "trend_scanning", the
        # grid is inert (backward-compatible for v1/v2 and all existing callers).
        self.label_mode: str = label_mode
        self.trend_scan_grid: tuple[int, ...] = tuple(trend_scan_grid)
        # iter-v1/014: σ_t-scaled barrier labeling source.
        # sigma_source = "natr" (default) → existing NATR_21×atr_mult path (BIT-IDENTICAL).
        # sigma_source = "ewma14d" → past-only EWMA σ_t barriers at sigma_halflife_candles.
        # When "ewma14d", sigma_k_tp and sigma_k_sl MUST be provided.
        # BARRIER-SOURCE CONSISTENCY: when "ewma14d", BOTH label-time barriers (in
        # label_trades via sigma_values) AND execution-time barriers (atr_tp_multiplier /
        # atr_sl_multiplier plumbed through BacktestConfig) SHOULD use σ_t-scaled values.
        # The runner achieves execution-side consistency by passing the same effective
        # k values via the BacktestConfig stop_loss_pct / take_profit_pct path (runner
        # responsibility per Section 10.1 RESOLUTION in iter-v1/014 brief).
        if sigma_source not in ("natr", "ewma14d"):
            raise ValueError(f"sigma_source must be 'natr' or 'ewma14d'; got {sigma_source!r}")
        if sigma_source == "ewma14d" and (sigma_k_tp is None or sigma_k_sl is None):
            raise ValueError(
                "sigma_k_tp and sigma_k_sl must be provided when sigma_source='ewma14d'"
            )
        self.sigma_source: str = sigma_source
        self.sigma_k_tp: float | None = sigma_k_tp
        self.sigma_k_sl: float | None = sigma_k_sl
        self.sigma_halflife_candles: int = int(sigma_halflife_candles)
        # iter-v1/016: sample-weighting axis — controls per-row weight assignment.
        # "abs_pnl"           (default) — BIT-IDENTICAL to baseline; keeps label_trades output.
        # "uniform"           — replaces train_weights with np.ones(n); Kish n_eff = 1.000.
        # "uniqueness_only"   — replaces train_weights with raw compute_sample_uniqueness output
        #                       (NOT multiplied by abs_pnl — the prior multiply was a near-no-op
        #                       per EDA Section 2.5: Spearman 0.997 after multiply).
        # "abs_pnl_timedecay" — iter-v1/090: abs_pnl weights MULTIPLIED by exp(-ln2/12·age_months)
        #                       (López de Prado AFML Ch.4 exponential time-decay).  half_life=12mo
        #                       is the pre-registered value (4:1 recent:old emphasis across 24mo
        #                       window).  OPT-IN / DEFAULT-OFF: abs_pnl path is BYTE-IDENTICAL
        #                       when this mode is NOT selected.  The decay fires via the existing
        #                       (b3) block below; the (b1.5) branch just sets _apply_timedecay=True.
        _valid_modes = {
            "abs_pnl",
            "uniform",
            "uniqueness_only",
            "composite_inv_concurrency",
            "abs_pnl_timedecay",  # iter-v1/090
        }
        if sample_weight_mode not in _valid_modes:
            raise ValueError(
                f"sample_weight_mode must be one of {_valid_modes}; got {sample_weight_mode!r}"
            )
        self.sample_weight_mode: str = sample_weight_mode
        # iter-v3/067 Path D: universal inference-time confidence-threshold floor.
        # Default 0.0 = no floor (backward-compatible). Pass 0.60 to raise the bar
        # for marginal-confidence trades (brief Section 3 Sub-fix 2).
        self._inference_threshold_floor: float = float(inference_threshold_floor)
        if self.ood_enabled and not self.ood_features:
            raise ValueError("ood_features must be specified when ood_enabled=True")
        self._ood_mean: np.ndarray | None = None
        self._ood_inv_cov: np.ndarray | None = None
        self._ood_cutoff: float | None = None
        self._ood_feature_cols: list[str] = []
        self._month_ood_features: dict[tuple[str, int], np.ndarray] = {}

        # iter-v1/016: F-AXIS-MECHANISM logging buffer.
        # Each _train_for_month call appends one dict per (model_tag, month) cell with
        # Kish n_eff ratio, per-symbol weight share (Model A only), and timeout_fallback_share.
        # The runner reads strategy._faxm_log after backtest completion and writes the CSV.
        # Empty list when sample_weight_mode="abs_pnl" (default) to avoid noise in baseline.
        self._faxm_log: list[dict] = []

        # iter-v1/021 BLOCK-PENDING-FIX H2: per-month feature importance log.
        # _train_for_month resets self._models = [] at each month start, so
        # post-dispatch reads of _models capture stale/empty state for models
        # that finish their last walk-forward month before the others.  This log
        # accumulates {train_month: str, mean_gain: dict[feat -> float]} across
        # ALL walk-forward months, making _write_feature_importance stale-safe.
        # Initialized to empty; populated unconditionally in _train_for_month
        # whenever self._models is non-empty after the ensemble loop.
        self._per_month_fi_log: list[dict] = []

        # Set during compute_features
        self._master: pd.DataFrame | None = None
        self._sym_arr: np.ndarray = np.array([])
        self._open_time_arr: np.ndarray = np.array([])
        self._interval: str = "8h"
        self._all_feature_cols: list[str] = []
        self._splits: list[MonthSplit] = []
        self._split_map: dict[str, MonthSplit] = {}
        # Per-month lazy training state
        self._current_month: str | None = None
        self._model: object | None = None
        self._models: list = []
        self._selected_cols: list[str] = []
        self._confidence_threshold: float = 0.50
        self._confidence_thresholds: list[float] = []
        self._month_features: dict[tuple[str, int], np.ndarray] = {}
        # ATR cache for dynamic barriers
        self._month_natr: dict[tuple[str, int], float] = {}
        # iter-v1/015 C1 FIX: σ_t cache for execution-time barriers (ewma14d path).
        # Populated in _train_for_month() when sigma_source="ewma14d", mirroring
        # _month_natr.  Key = (symbol, open_time_ms) of test-month-first-candle.
        self._month_sigma: dict[tuple[str, int], float] = {}
        # Per-row ATR values for dynamic labeling (price units)
        self._label_atr_values: np.ndarray | None = None
        # iter-v1/014: per-row past-only EWMA σ_t values for σ_t-scaled labeling.
        # Populated in compute_features() when sigma_source="ewma14d".
        self._label_sigma_values: np.ndarray | None = None

    def compute_features(self, master: pd.DataFrame) -> None:
        """Lightweight setup: store master and generate splits. No training."""
        self._master = master
        self._sym_arr = master["symbol"].to_numpy(dtype=str)
        self._open_time_arr = master["open_time"].values

        # Detect interval
        self._interval = self._detect_interval(master)

        # feature_columns is required (validated in __init__) — no auto-discovery
        self._all_feature_cols = list(self.feature_columns)

        # Generate monthly splits with a labeler-aware embargo at the train/test
        # boundary. ``compute_embargo_candles`` is the single source of truth
        # also used for the CV gap below — see _train_for_month.
        interval_minutes = _interval_to_minutes(self._interval)
        self._splits = generate_monthly_splits(
            self._open_time_arr,
            self.training_months,
            label_timeout_minutes=self.label_timeout_minutes,
            interval_minutes=interval_minutes,
        )
        self._split_map = {s.test_month: s for s in self._splits}

        if self.verbose > 0:
            print(
                f"[lgbm] {len(self._all_feature_cols)} feature columns, "
                f"{len(self._splits)} walk-forward splits"
            )

        self._current_month = None
        self._model = None

        # iter-v1/074: AXIS-R close-price index — O(log n) lookback queries.
        # Build a per-symbol (open_time_ms, close) index for ret_270b computation.
        if self._enable_mid_bull_short_veto:
            self._close_by_sym = {}
            for _sym in np.unique(self._sym_arr):
                _sym_mask = self._sym_arr == _sym
                _ot_sym = self._open_time_arr[_sym_mask]
                _cl_sym = master["close"].values[_sym_mask].astype(np.float64)
                _sort_idx = np.argsort(_ot_sym)
                self._close_by_sym[str(_sym)] = (
                    _ot_sym[_sort_idx].astype(np.int64),
                    _cl_sym[_sort_idx],
                )

        # Load per-row ATR values for dynamic labeling
        if self.use_atr_labeling and self.atr_tp_multiplier is not None:
            self._label_atr_values = self._load_atr_for_master()
            if self.verbose > 0:
                valid = ~np.isnan(self._label_atr_values)
                print(
                    f"[lgbm] ATR labeling: {valid.sum()}/{len(self._label_atr_values)} "
                    f"rows with ATR values"
                )
        else:
            self._label_atr_values = None

        # iter-v1/014: σ_t-scaled barriers — load past-only EWMA σ_t per row.
        # _load_sigma_for_master applies .shift(1) INSIDE the method to guarantee
        # strict past-only (no future return leaks into labeling). See A2 guard.
        if self.sigma_source == "ewma14d":
            self._label_sigma_values = self._load_sigma_for_master()
            if self.verbose > 0:
                valid = ~np.isnan(self._label_sigma_values)
                p10 = float(np.nanpercentile(self._label_sigma_values, 10))
                p50 = float(np.nanpercentile(self._label_sigma_values, 50))
                p90 = float(np.nanpercentile(self._label_sigma_values, 90))
                print(
                    f"[lgbm] σ_t labeling (ewma14d halflife={self.sigma_halflife_candles}c): "
                    f"{valid.sum()}/{len(self._label_sigma_values)} rows valid | "
                    f"p10={p10:.5f} p50={p50:.5f} p90={p90:.5f}"
                )
        else:
            self._label_sigma_values = None

    def _load_atr_for_master(self) -> np.ndarray:
        """Load per-candle ATR values (price units) aligned with master rows."""
        from pathlib import Path

        n = len(self._master)
        atr_values = np.full(n, np.nan, dtype=np.float64)
        close_arr = self._master["close"].values.astype(np.float64)

        for sym in np.unique(self._sym_arr):
            path = Path(self.features_dir) / f"{sym}_{self._interval}_features.parquet"
            if not path.exists():
                continue
            table = pq.read_table(path, columns=["open_time", self.atr_column])
            feat_ot = table.column("open_time").to_numpy().astype(np.int64)
            feat_natr = table.column(self.atr_column).to_numpy().astype(np.float64)

            # Vectorized lookup via searchsorted
            sort_order = np.argsort(feat_ot)
            sorted_ot = feat_ot[sort_order]
            sorted_natr = feat_natr[sort_order]

            sym_mask = self._sym_arr == sym
            sym_indices = np.where(sym_mask)[0]
            sym_times = self._open_time_arr[sym_indices].astype(np.int64)

            positions = np.searchsorted(sorted_ot, sym_times)
            in_bounds = positions < len(sorted_ot)
            clamped = np.minimum(positions, len(sorted_ot) - 1)
            matched = in_bounds & (sorted_ot[clamped] == sym_times)

            natr_vals = np.where(matched, sorted_natr[clamped], np.nan)
            atr_values[sym_indices] = close_arr[sym_indices] * natr_vals / 100.0

        return atr_values

    def _load_sigma_for_master(self) -> np.ndarray:
        """Load per-candle past-only EWMA σ_t values aligned with master rows.

        iter-v1/014 — A2 anti-pattern guard (forward-window σ_t):

        The EWMA standard deviation is computed from close-to-close log-returns
        using ``pd.Series.ewm(halflife=N, adjust=False).std()``. CRITICALLY, the
        result is then **shifted forward by 1 candle** via ``.shift(1)`` so that
        sigma_t[i] contains only information from returns[0..i-1] — i.e. strictly
        past data. Without this shift, sigma_t[i] would incorporate return[i] (the
        current candle's return) into the barrier distance used to label candle i,
        creating look-ahead bias in the training labels.

        This shift is the MANDATORY past-only safety guard. Any reader modifying
        this method MUST preserve the ``.shift(1)`` call. The test suite in
        ``tests/test_iteration_v1_014_sigma_t.py::test_sigma_t_is_past_only``
        verifies this property numerically.
        """
        assert self._master is not None, "_load_sigma_for_master called before compute_features"
        n = len(self._master)
        sigma_values = np.full(n, np.nan, dtype=np.float64)

        for sym in np.unique(self._sym_arr):
            sym_mask = self._sym_arr == sym
            sym_indices = np.where(sym_mask)[0]

            # Extract close prices for this symbol in master row order
            close_sym = self._master["close"].values[sym_indices].astype(np.float64)

            if len(close_sym) < 2:
                continue

            # Log-returns: ret[i] = log(close[i] / close[i-1])
            # ret[0] is NaN (no prior close for the first row)
            log_ret = pd.Series(np.log(close_sym / np.roll(close_sym, 1)))
            log_ret.iloc[0] = np.nan

            # Past-only EWMA std: halflife in candles.
            # MANDATORY .shift(1): sigma at position i = std of returns[0..i-1].
            # DO NOT REMOVE .shift(1) — it is the A2 lookahead-safety guard.
            ewma_std = log_ret.ewm(halflife=self.sigma_halflife_candles, adjust=False).std()
            ewma_std_shifted = ewma_std.shift(1)  # A2 GUARD — past-only

            sigma_values[sym_indices] = ewma_std_shifted.to_numpy(dtype=np.float64)

        return sigma_values

    def _train_for_month(self, month_str: str) -> None:
        """Train a model for the given month. Called lazily from get_signal."""
        self._model = None
        self._selected_cols = []
        self._confidence_threshold = 0.50
        self._month_features = {}

        split = self._split_map.get(month_str)
        if split is None:
            if self.verbose > 0:
                print(f"[lgbm] No split for {month_str} (insufficient training data)")
            return

        if not self._all_feature_cols:
            if self.verbose > 0:
                print(f"[lgbm] No feature columns available, skipping {month_str}")
            return

        if self.verbose > 0:
            print(f"[lgbm] === Training for {month_str} ===")
            print(
                f"  Train window: {_ms_to_date(split.train_start_ms)} "
                f"\u2192 {_ms_to_date(split.train_end_ms)}"
            )

        # (a) Get all indices in the training window
        train_indices = np.where(
            (self._open_time_arr >= split.train_start_ms)
            & (self._open_time_arr < split.train_end_ms)
        )[0]

        # iter-v1/024: apply regime-partition filter (data_filter_callback).
        # The callback receives a DataFrame slice that includes all kline columns
        # from master PLUS any columns listed in _data_filter_columns (loaded
        # from parquet and merged by open_time+symbol key before calling the
        # callback).  Applied BEFORE labeling so the sub-model sees only its
        # regime's training rows.
        # Default None → no filter; backward-compatible (bit-identical to pre-/024).
        if self._data_filter_callback is not None and len(train_indices) > 0:
            _master_slice = self._master.iloc[train_indices].copy()

            # Enrich the slice with parquet columns needed by the filter.
            # _data_filter_columns is set when the filter reads columns NOT in
            # the kline-only master (e.g. funding_rate_zscore_30).
            if self._data_filter_columns:
                _filter_lookups = [
                    (str(self._sym_arr[i]), int(self._open_time_arr[i])) for i in train_indices
                ]
                _filter_feat_df = lookup_features(
                    _filter_lookups,
                    self.features_dir,
                    self._interval,
                    columns=self._data_filter_columns,
                )
                if not _filter_feat_df.empty:
                    # left-join on open_time + symbol so kline rows without a
                    # parquet match get NaN (the filter's NaN → normal fallback
                    # handles them correctly).
                    _filter_feat_df = _filter_feat_df.rename(columns={"open_time": "__ot__"})
                    _master_slice = _master_slice.assign(__ot__=_master_slice["open_time"])
                    # Add symbol column to filter feat df for the merge key
                    if "symbol" not in _filter_feat_df.columns:
                        pass  # lookup_features already adds symbol
                    _master_slice = _master_slice.merge(
                        _filter_feat_df,
                        on=["__ot__", "symbol"],
                        how="left",
                    ).drop(columns=["__ot__"])

            _filter_mask = self._data_filter_callback(_master_slice)
            train_indices = train_indices[_filter_mask]
            if self.verbose > 0:
                print(
                    f"  [data_filter] Partition: {len(train_indices)} rows after filter "
                    f"(from full window)"
                )

        if len(train_indices) < 10:
            if self.verbose > 0:
                print(f"  Skipping {month_str}: only {len(train_indices)} train samples")
            return

        if self.verbose > 0:
            from collections import Counter

            n_unique_syms = len(set(self._sym_arr[train_indices]))
            print(f"  {len(train_indices)} training samples from {n_unique_syms} symbols")
            sample_months = Counter(
                _epoch_ms_to_month(int(t)) for t in self._open_time_arr[train_indices]
            )
            dist_parts = [f"{m}: {c}" for m, c in sorted(sample_months.items())]
            print(f"  Samples per month: {', '.join(dist_parts)}")

        # (b) Label all training samples (with fee-aware returns)
        # iter-v1/014: σ_t-scaled barriers TAKE PRIORITY when sigma_source="ewma14d".
        # Otherwise fall through to existing ATR or fixed-percentage paths.
        # Both label-time AND execution-time barriers use σ_t when ewma14d (runner
        # responsibility per Section 10.1 RESOLUTION in iter-v1/014 brief).
        if self._label_sigma_values is not None:
            # σ_t-scaled path (iter-v1/014): atr_values is NOT passed.
            # tp_pct / sl_pct are ignored; barrier distances computed inside
            # label_trades via sigma_values × sigma_k_tp/sl × entry.
            label_tp = self.label_tp_pct  # used as dummy; not evaluated in sigma path
            label_sl = self.label_sl_pct
            label_atr = None
            label_sigma = self._label_sigma_values
        elif self._label_atr_values is not None:
            # Existing ATR path: tp_pct / sl_pct are ATR multipliers.
            label_tp = self.atr_tp_multiplier
            label_sl = self.atr_sl_multiplier or self.atr_tp_multiplier / 2.0
            label_atr = self._label_atr_values
            label_sigma = None
        else:
            label_tp = self.label_tp_pct
            label_sl = self.label_sl_pct
            label_atr = None
            label_sigma = None
        train_labels, train_weights, long_pnls, short_pnls = label_trades(
            self._master,
            train_indices,
            label_tp,
            label_sl,
            self.label_timeout_minutes,
            fee_pct=self.fee_pct,
            atr_values=label_atr,
            sigma_values=label_sigma,
            sigma_k_tp=self.sigma_k_tp if label_sigma is not None else None,
            sigma_k_sl=self.sigma_k_sl if label_sigma is not None else None,
            verbose=self.verbose,
            neutral_threshold_pct=self.neutral_threshold_pct,
            label_mode=self.label_mode,
            trend_scan_grid=self.trend_scan_grid,
            interval_minutes=_interval_to_minutes(self._interval),  # iter-v1/015 C1 FIX
        )

        ternary = self.neutral_threshold_pct is not None

        # (b1.5) iter-v1/016: sample_weight_mode axis — REPLACES abs_pnl weights when mode
        # is "uniform" or "uniqueness_only".  Must execute BEFORE the legacy sample_uniqueness
        # multiplier block (b2) below so that modes are independent, not composed.
        # "abs_pnl" (default) keeps train_weights exactly as returned by label_trades.
        # "abs_pnl_timedecay" (iter-v1/090): keeps abs_pnl base weights here, sets an
        # internal flag so (b3) applies the exponential time-decay multiply below.
        # The decay COMPOSES with Optuna's training_days trim (trim-after-decay is intended:
        # optimization.py:392 trims train_idx to last training_days, then :417 w_train=w[train_idx]
        # — decayed weights survive the trim; this is the AFML Ch.4 decay-within-window design).
        _apply_timedecay: bool = False  # set True only for abs_pnl_timedecay mode
        if self.sample_weight_mode == "uniform":
            train_weights = np.ones(len(train_weights), dtype=np.float64)
            if self.verbose > 0:
                print("  [sample_weight_mode=uniform] weights replaced with np.ones(n)")
        elif self.sample_weight_mode == "uniqueness_only":
            uniq_replace = compute_sample_uniqueness(
                train_indices,
                self.label_timeout_minutes,
                self._open_time_arr,
                self._sym_arr,
            )
            train_weights = uniq_replace.astype(np.float64)
            if self.verbose > 0:
                print(
                    f"  [sample_weight_mode=uniqueness_only] weights replaced with raw "
                    f"uniqueness: min={uniq_replace.min():.4f}, "
                    f"mean={uniq_replace.mean():.4f}, max={uniq_replace.max():.4f}"
                )
        elif self.sample_weight_mode == "composite_inv_concurrency":
            # iter-v1/031: inv_concurrency_only sample-weighting axis.
            # weight_t = (1 / c_at_entry(t)) / mean(1/c_at_entry) per (symbol, training_window).
            # c_at_entry(t) = count of label windows ACTIVE at bar t (past-only; no future
            # contamination). Mean-renormalized so each symbol's weights sum to N_sym.
            # F-AXIS #1 wiring print: emitted ONCE per (model, month) cell at this site —
            # BEFORE the ensemble seed loop so the print fires once per cell (not 5× per seed).
            _interval_minutes = _interval_to_minutes(self._interval)
            _interval_ms = _interval_minutes * 60_000
            _label_timeout_bars = self.label_timeout_minutes // _interval_minutes
            # Build boolean train_mask aligned with master frame
            _n_master = len(self._open_time_arr)
            _train_mask = np.zeros(_n_master, dtype=bool)
            _train_mask[train_indices] = True
            _inv_conc_weights = compute_composite_inv_concurrency_weights(
                self._open_time_arr,
                self._sym_arr,
                _train_mask,
                _label_timeout_bars,
                _interval_ms,
            )
            _w_mean = float(_inv_conc_weights.mean())
            _w_std = float(_inv_conc_weights.std())
            _n_w = len(_inv_conc_weights)
            _kish_n_eff_conc = float((_inv_conc_weights.sum()) ** 2 / (_inv_conc_weights**2).sum())
            _kish_conc = _kish_n_eff_conc / _n_w if _n_w > 0 else 0.0
            print(
                f"  [sample_weight_mode=composite_inv_concurrency] "
                f"cell=({self._model_role or 'model'}, {month_str}) "
                f"weight_mean={_w_mean:.4f} weight_std={_w_std:.4f} "
                f"kish={_kish_conc:.4f}"
            )
            train_weights = _inv_conc_weights
        elif self.sample_weight_mode == "abs_pnl_timedecay":
            # iter-v1/090: W-DECAY — keep abs_pnl base weights; signal (b3) to apply
            # exponential time-decay multiply.  No replacement here — decay is multiplicative.
            _apply_timedecay = True
        # "abs_pnl" — no change; label_trades output already in train_weights

        # (b2) Apply sample uniqueness weighting (AFML Ch. 4)
        if self.sample_uniqueness:
            uniq = compute_sample_uniqueness(
                train_indices,
                self.label_timeout_minutes,
                self._open_time_arr,
                self._sym_arr,
            )
            train_weights = train_weights * uniq
            if self.verbose > 0:
                print(
                    f"  Uniqueness: min={uniq.min():.3f}, "
                    f"mean={uniq.mean():.3f}, max={uniq.max():.3f}"
                )

        # (b3) Apply time decay weighting.
        # Fires when:
        #   (a) time_decay_half_life is set directly (legacy path), OR
        #   (b) _apply_timedecay=True (abs_pnl_timedecay mode, iter-v1/090).
        # The pre-registered default for abs_pnl_timedecay is half_life=12mo (365d).
        # Age is measured relative to the latest training bar (train_times.max()),
        # which is always <= train_end_ms (past-only — no look-ahead contamination).
        # The decay SURVIVES the optimization.py:392 training_days trim because
        # train_idx is trimmed first, then w_train=w[train_idx] reads the already-decayed
        # weights (trim-after-decay ordering confirmed; AFML Ch.4 decay-within-window).
        _default_wdecay_half_life_months: float = 12.0  # pre-registered; iter-v1/090
        if self.time_decay_half_life is not None or _apply_timedecay:
            _half_life = (
                self.time_decay_half_life
                if self.time_decay_half_life is not None
                else _default_wdecay_half_life_months
            )
            train_times = self._open_time_arr[train_indices]
            max_time = train_times.max()
            age_ms = max_time - train_times
            age_months = age_ms / (30.44 * 24 * 3600 * 1000)  # approx months
            lam = np.log(2) / _half_life
            decay = np.exp(-lam * age_months)
            # iter-v1/090 §1c REQUIRED attribution log:
            # Prints decay.mean(), weight_sum BEFORE and AFTER the decay multiply so
            # Phase 7.4 can split recency-channel vs regularization-loosening side-effect
            # (un-renormalized decay halves total weight mass → loosens min_child_weight;
            # the log is the minimum attribution artifact per LM Master §1c advisory).
            _w_sum_before = float(train_weights.sum())
            train_weights = train_weights * decay
            _w_sum_after = float(train_weights.sum())
            _kish_n_eff_decay = (
                float((train_weights.sum()) ** 2 / (train_weights**2).sum())
                if train_weights.sum() > 0
                else 0.0
            )
            _kish_ratio_decay = (
                _kish_n_eff_decay / len(train_weights) if len(train_weights) > 0 else 0.0
            )
            print(
                f"  [W-DECAY §1c] half_life={_half_life}mo "
                f"decay.mean={decay.mean():.4f} decay.min={decay.min():.3f} "
                f"weight_sum_before={_w_sum_before:.4f} "
                f"weight_sum_after={_w_sum_after:.4f} "
                f"(ratio={_w_sum_after / _w_sum_before:.4f} ≈ decay.mean) "
                f"kish_ratio_after={_kish_ratio_decay:.4f}"
            )

        # (b4) iter-v1/016: F-AXIS-MECHANISM cell logging.
        # Log Kish n_eff ratio, per-symbol weight share (pooled models), and
        # timeout_fallback_share for the F-AXIS-MECHANISM compound falsifier.
        # Only appends when sample_weight_mode != "abs_pnl" (active axis run).
        if self.sample_weight_mode != "abs_pnl":
            _w = train_weights
            _kish_n_eff = float((_w.sum()) ** 2 / (_w**2).sum()) if _w.sum() > 0 else 0.0
            _n_actual = len(_w)
            _kish_ratio = _kish_n_eff / _n_actual if _n_actual > 0 else 0.0
            # Per-symbol weight share (for pooled model-A BTC+ETH attribution).
            _syms_in_cell = self._sym_arr[train_indices]
            _unique_syms = sorted(set(_syms_in_cell))
            _per_sym_share: dict[str, float] = {}
            _total_w = float(_w.sum())
            for _s in _unique_syms:
                _mask = _syms_in_cell == _s
                _per_sym_share[_s] = float(_w[_mask].sum()) / _total_w if _total_w > 0 else 0.0
            # Timeout fallback share (labels == 0 in triple-barrier = timeout class).
            # Neutral labels from neutral_threshold_pct are also 0 — safe approximation
            # since /016 uses binary labels (neutral_threshold_pct=None).
            _timeout_share = float((train_labels == 0).mean())
            _cell: dict = {
                "month": month_str,
                "n_actual": _n_actual,
                "kish_n_eff": round(_kish_n_eff, 2),
                "kish_ratio": round(_kish_ratio, 4),
                "timeout_fallback_share": round(_timeout_share, 4),
                "weight_mode": self.sample_weight_mode,
            }
            for _s, _share in _per_sym_share.items():
                _cell[f"weight_share_{_s}"] = round(_share, 4)
            self._faxm_log.append(_cell)

        if self.verbose > 0:
            n_long = int((train_labels == 1).sum())
            n_short = int((train_labels == -1).sum())
            n_neutral = int((train_labels == 0).sum())
            total = len(train_labels)
            neutral_str = ""
            if n_neutral > 0:
                neutral_str = f", {n_neutral} neutral ({100 * n_neutral / total:.1f}%)"
            print(
                f"  Labels: {n_long} long ({100 * n_long / total:.1f}%), "
                f"{n_short} short ({100 * n_short / total:.1f}%){neutral_str} | "
                f"weights: min={train_weights.min():.2f}, "
                f"mean={train_weights.mean():.2f}, "
                f"max={train_weights.max():.2f}"
            )

        # (c) Load training features
        train_lookups = [
            (str(self._sym_arr[i]), int(self._open_time_arr[i])) for i in train_indices
        ]
        train_feat_df = lookup_features(train_lookups, self.features_dir, self._interval)
        if train_feat_df.empty:
            if self.verbose > 0:
                print(f"  Skipping {month_str}: no features found for training")
            return

        # Align features with labels, weights, and returns
        feat_keys = set(zip(train_feat_df["symbol"], train_feat_df["open_time"]))
        keep_mask = np.array(
            [
                (str(self._sym_arr[i]), int(self._open_time_arr[i])) in feat_keys
                for i in train_indices
            ]
        )
        train_labels = train_labels[keep_mask]
        train_weights = train_weights[keep_mask]
        long_pnls = long_pnls[keep_mask]
        short_pnls = short_pnls[keep_mask]
        train_open_times = self._open_time_arr[train_indices][keep_mask]

        # iter-v1/025: per-(symbol, month) NaN-fraction skip guard (LM Master §5(a) ADOPTED).
        # For each symbol in train_feat_df, if ANY nan_skip_columns column has >nan_skip_threshold
        # fraction of NaN values, that symbol's rows are excluded from this month's fold.
        # Backward-compat: _nan_skip_columns=None skips this block entirely.
        if self._nan_skip_columns:
            _skip_syms: set[str] = set()
            _check_cols = [c for c in self._nan_skip_columns if c in train_feat_df.columns]
            if _check_cols and "symbol" in train_feat_df.columns:
                for _sym_name, _sym_group in train_feat_df.groupby("symbol"):
                    for _col in _check_cols:
                        _nan_frac = float(_sym_group[_col].isna().mean())
                        _skipped = _nan_frac > self._nan_skip_threshold
                        self._nan_skip_log.append(
                            {
                                "symbol": str(_sym_name),
                                "month": month_str,
                                "column": _col,
                                "nan_fraction": round(_nan_frac, 4),
                                "skipped": _skipped,
                            }
                        )
                        if _skipped:
                            _skip_syms.add(str(_sym_name))
            if _skip_syms:
                if self.verbose > 0:
                    print(
                        f"  [nan_skip] Excluding symbols with >{self._nan_skip_threshold:.0%} "
                        f"NaN in {self._nan_skip_columns}: {sorted(_skip_syms)}"
                    )
                # Build mask: keep only rows whose symbol is NOT in _skip_syms.
                # train_feat_df is aligned to train_indices after keep_mask.
                _has_sym = "symbol" in train_feat_df.columns
                _sym_col = train_feat_df["symbol"].values if _has_sym else None
                if _sym_col is not None:
                    _sym_keep = np.array([str(s) not in _skip_syms for s in _sym_col])
                    train_feat_df = train_feat_df[_sym_keep].reset_index(drop=True)
                    train_labels = train_labels[_sym_keep]
                    train_weights = train_weights[_sym_keep]
                    long_pnls = long_pnls[_sym_keep]
                    short_pnls = short_pnls[_sym_keep]
                    train_open_times = train_open_times[_sym_keep]
                    if self.verbose > 0:
                        print(
                            f"  [nan_skip] {len(train_feat_df)} rows remain after "
                            f"excluding {len(_skip_syms)} symbol(s)"
                        )
                    if len(train_feat_df) < 10:
                        if self.verbose > 0:
                            print(
                                f"  Skipping {month_str}: only {len(train_feat_df)} rows "
                                "after nan_skip exclusion"
                            )
                        return

        available_feat_cols = [c for c in self._all_feature_cols if c in train_feat_df.columns]
        feat_train = train_feat_df[available_feat_cols].values

        if self.verbose > 0:
            print(
                f"  Features: {len(train_feat_df)}/{len(train_indices)} "
                f"matched, {len(available_feat_cols)} columns"
            )

        # (d) Optuna optimization (all features, with threshold)
        # CV gap prevents label leakage between train and val folds inside
        # TimeSeriesSplit. Uses the SAME ``compute_embargo_candles`` helper
        # that walk_forward.py uses for the train/test boundary — single
        # source of truth, no duplicated formula. Multiplies by n_symbols
        # because TimeSeriesSplit counts ROWS (which are interleaved
        # symbol-by-symbol), so one candle of time = n_symbols rows.
        if self.cv_label_gap:
            interval_minutes = _interval_to_minutes(self._interval)
            embargo_candles = compute_embargo_candles(self.label_timeout_minutes, interval_minutes)
            n_symbols = len(set(self._sym_arr[train_indices]))
            cv_gap = embargo_candles * n_symbols
        else:
            cv_gap = 0
        if self.verbose > 0:
            print(f"  CV gap: {cv_gap} rows")

        seeds = self.ensemble_seeds
        self._models = []
        self._confidence_thresholds = []

        # sub-fix 1c (iter-v3/003): per-ensemble-seed OOF persistence context
        # symbols_arr aligns with feat_train rows (after keep_mask filtering)
        train_symbols_arr = self._sym_arr[train_indices][keep_mask]

        # iter-v1/063: SPECIALIST mode — 50 independent Optuna studies, one per seed.
        # When active, bypass the standard ensemble loop entirely.
        # Each seed runs its own TPESampler study at n_trials=V1_SPECIALIST_OPTUNA_TRIALS.
        # HP search space: max_depth=5 FIXED, num_leaves=31 FIXED, min_child_samples REMOVED.
        # Aggregation in get_signal: mean-of-signed-weights across 50 seeds.
        if self._specialist_mode:
            self._specialist_models = []
            # H2 fix: per-month failure accumulator (reset each call).
            _sp_failed_this_month: list[tuple[int, str]] = []
            # H5/H10 fix: global OOF accumulator across all seeds for this month.
            # Always a list; we only flush when _oof_persist_path is set.
            _sp_oof_global_buf: list[dict] = []
            specialist_seeds = V1_SPECIALIST_SEEDS
            if self.verbose > 0:
                print(
                    f"  [SPECIALIST] mode active: "
                    f"{len(specialist_seeds)} seeds × "
                    f"{V1_SPECIALIST_OPTUNA_TRIALS} trials each | "
                    f"max_depth=5 FIXED | num_leaves=31 FIXED | "
                    f"min_child_samples=REMOVED | "
                    f"n_startup_trials={self._specialist_n_startup_trials} | "
                    f"n_estimators_max={self._specialist_n_estimators_max}"
                )
            for _sp_idx, _sp_seed in enumerate(specialist_seeds):
                if self.verbose > 0 and (_sp_idx % 10 == 0 or _sp_idx == len(specialist_seeds) - 1):
                    print(
                        f"  [SPECIALIST seed {_sp_idx + 1}/{len(specialist_seeds)}] seed={_sp_seed}"
                    )
                try:
                    import optuna as _optuna

                    _sp_sampler = _optuna.samplers.TPESampler(
                        seed=_sp_seed,
                        n_startup_trials=self._specialist_n_startup_trials,
                    )
                    _sp_study = _optuna.create_study(direction="maximize", sampler=_sp_sampler)
                    _sp_study.set_user_attr("fast_mode", False)
                    _sp_study.set_user_attr("optuna_objective", self._optuna_objective)
                    _sp_study.set_user_attr("specialist_mode", True)
                    _sp_study.set_user_attr(
                        "specialist_n_estimators_max", self._specialist_n_estimators_max
                    )

                    from crypto_trade.strategies.ml.optimization import (
                        _objective as _opt_objective,
                    )

                    # H5/H10 fix: per-seed buffer — non-None iff _oof_persist_path is set,
                    # which causes _objective to populate it (oof_buffer is not None check).
                    _sp_oof_buf: list[dict] | None = (
                        [] if self._oof_persist_path is not None else None
                    )

                    # Capture loop variables for closure (avoid late-binding issues).
                    _sp_feat = feat_train
                    _sp_lbl = train_labels
                    _sp_sw = train_weights
                    _sp_lp = long_pnls
                    _sp_sp_pnls = short_pnls
                    _sp_cols = available_feat_cols
                    _sp_cv = self.cv_splits
                    _sp_vb = self.verbose
                    _sp_ot = train_open_times
                    _sp_ternary = ternary
                    _sp_cvgap = cv_gap
                    _sp_month = month_str
                    _sp_sym = train_symbols_arr
                    _sp_buf = _sp_oof_buf
                    _sp_s = _sp_seed

                    def _make_sp_objective(
                        feat, lbl, sw, lp, sp, cols, cv, seed, vb, ot, trn, cvg, mon, sym, buf
                    ):
                        def _sp_obj(_trial):
                            return _opt_objective(
                                _trial,
                                feat,
                                lbl,
                                sw,
                                lp,
                                sp,
                                cols,
                                cv,
                                seed,
                                vb,
                                open_times=ot,
                                ternary=trn,
                                cv_gap=cvg,
                                train_month=mon,
                                symbols_arr=sym,
                                oof_buffer=buf,
                                bounds_profile="v1_specialist",
                                min_child_samples_lower_bound=None,
                            )

                        return _sp_obj

                    _sp_study.optimize(
                        _make_sp_objective(
                            _sp_feat,
                            _sp_lbl,
                            _sp_sw,
                            _sp_lp,
                            _sp_sp_pnls,
                            _sp_cols,
                            _sp_cv,
                            _sp_s,
                            _sp_vb,
                            _sp_ot,
                            _sp_ternary,
                            _sp_cvgap,
                            _sp_month,
                            _sp_sym,
                            _sp_buf,
                        ),
                        n_trials=V1_SPECIALIST_OPTUNA_TRIALS,
                    )

                    _sp_best = _sp_study.best_trial
                    _sp_params = _sp_best.params
                    _sp_ct = float(_sp_params["confidence_threshold"])

                    import lightgbm as _lgb_sp

                    _sp_lgbm_params = {
                        "n_estimators": int(_sp_params["n_estimators"]),
                        "max_depth": 5,
                        "num_leaves": 31,
                        "learning_rate": float(_sp_params["learning_rate"]),
                        "subsample": float(_sp_params.get("subsample", 1.0)),
                        "colsample_bytree": float(_sp_params.get("colsample_bytree", 1.0)),
                        "reg_alpha": float(_sp_params["reg_alpha"]),
                        "reg_lambda": float(_sp_params["reg_lambda"]),
                        "random_state": _sp_seed,
                        "verbosity": -1,
                        "objective": "multiclass" if ternary else "binary",
                        "is_unbalance": True,
                    }
                    if ternary:
                        _sp_lgbm_params["num_class"] = 3

                    _sp_y = (
                        labels_to_classes_ternary(train_labels)
                        if ternary
                        else labels_to_classes(train_labels)
                    )

                    # C2/H1 FIX: apply Optuna-chosen training_days window at the
                    # per-seed final retrain — mirroring optimization.py:738-744.
                    # Without this slice, every seed trains on the FULL 24-month
                    # window regardless of what Optuna selected, silently
                    # discarding the HP that the objective was optimized for.
                    _sp_feat_fit = feat_train
                    _sp_y_fit = _sp_y
                    _sp_sw_fit = train_weights
                    if _sp_ot is not None and "training_days" in _sp_params:
                        _sp_td = int(_sp_params["training_days"])
                        _sp_anchor_ms = int(split.test_start_ms)
                        _sp_cutoff_ms = _sp_anchor_ms - _sp_td * 86_400_000
                        _sp_td_mask = _sp_ot >= _sp_cutoff_ms
                        _sp_feat_fit = feat_train[_sp_td_mask]
                        _sp_y_fit = _sp_y[_sp_td_mask]
                        _sp_sw_fit = train_weights[_sp_td_mask]

                    _sp_clf = _lgb_sp.LGBMClassifier(**_sp_lgbm_params)
                    _sp_clf.fit(_sp_feat_fit, _sp_y_fit, sample_weight=_sp_sw_fit)
                    self._specialist_models.append((_sp_clf, available_feat_cols, _sp_ct))
                    # H5/H10 fix: tag per-seed OOF rows with seed_id and merge into
                    # the global accumulator.  _sp_buf is only non-None when
                    # _oof_persist_path is set; _sp_buf references the same list as
                    # _sp_oof_buf so it already holds rows the objective appended.
                    if _sp_buf is not None:
                        for _row in _sp_buf:
                            _sp_oof_global_buf.append({**_row, "seed_id": _sp_seed})
                except Exception as _sp_exc:
                    # H2 fix: track per-seed failures; raise after tolerance exceeded.
                    _exc_repr = repr(_sp_exc)
                    _sp_failed_this_month.append((_sp_seed, _exc_repr))
                    self._failed_seeds_log.append((_sp_seed, _exc_repr))
                    if self.verbose > 0:
                        print(
                            f"  [SPECIALIST seed {_sp_seed}] failed "
                            f"({len(_sp_failed_this_month)}/{V1_SPECIALIST_SEED_TOLERANCE} "
                            f"tolerance): {_exc_repr}"
                        )
                    if len(_sp_failed_this_month) > V1_SPECIALIST_SEED_TOLERANCE:
                        # Emit decision_log before raising so the failure is traceable.
                        try:
                            from crypto_trade import decision_log as _dl

                            _dl.log(
                                {
                                    "kind": "specialist_seed_failures",
                                    "month": month_str,
                                    "failed_count": len(_sp_failed_this_month),
                                    "tolerance": V1_SPECIALIST_SEED_TOLERANCE,
                                    "failed_seeds": [s for s, _ in _sp_failed_this_month],
                                    "decision": "raise:tolerance_exceeded",
                                }
                            )
                        except Exception:
                            pass
                        raise SpecialistSeedFailureError(
                            failed=len(_sp_failed_this_month),
                            tolerance=V1_SPECIALIST_SEED_TOLERANCE,
                            month_str=month_str,
                            seeds=[str(s) for s, _ in _sp_failed_this_month],
                        )

            # H2 fix: emit decision_log summary of per-seed failures (even when 0).
            try:
                from crypto_trade import decision_log as _dl_post

                _dl_post.log(
                    {
                        "kind": "specialist_seed_failures",
                        "month": month_str,
                        "failed_count": len(_sp_failed_this_month),
                        "tolerance": V1_SPECIALIST_SEED_TOLERANCE,
                        "failed_seeds": [s for s, _ in _sp_failed_this_month],
                        "succeeded_count": len(self._specialist_models),
                        "decision": (
                            "pass" if len(_sp_failed_this_month) == 0 else "pass:within_tolerance"
                        ),
                    }
                )
            except Exception:
                pass

            # H5/H10 fix: flush global OOF accumulator to parquet after all seeds complete.
            # Uses the same atomic write-to-temp + os.replace pattern as optimization.py
            # Sub-fix 1b.  Schema adds seed_id and specialist_seed_count to the standard
            # oof_buffer columns so DSR/PBO basin-lottery diagnostics can operate on
            # SPECIALIST-mode OOF paths identically to ensemble-mode.
            if self._oof_persist_path is not None and _sp_oof_global_buf:
                import os
                import tempfile

                import pandas as pd

                _sp_n_seeds_written = len(self._specialist_models)
                # Stamp specialist_seed_count into each row before writing.
                for _r in _sp_oof_global_buf:
                    _r["specialist_seed_count"] = _sp_n_seeds_written
                _sp_oof_new_df = pd.DataFrame(
                    _sp_oof_global_buf,
                    columns=[
                        "trial_id",
                        "symbol",
                        "train_month",
                        "fold_idx",
                        "candle_open_time_ms",
                        "oof_return",
                        "seed_id",
                        "specialist_seed_count",
                    ],
                )
                self._oof_persist_path.parent.mkdir(parents=True, exist_ok=True)
                if self._oof_persist_path.exists():
                    _sp_existing = pd.read_parquet(self._oof_persist_path)
                    _sp_combined = pd.concat([_sp_existing, _sp_oof_new_df], ignore_index=True)
                else:
                    _sp_combined = _sp_oof_new_df
                _sp_tmp_fd, _sp_tmp_name = tempfile.mkstemp(
                    dir=self._oof_persist_path.parent, suffix=".parquet.tmp"
                )
                try:
                    os.close(_sp_tmp_fd)
                    _sp_combined.to_parquet(_sp_tmp_name, index=False)
                    os.replace(_sp_tmp_name, self._oof_persist_path)
                except Exception:
                    try:
                        os.unlink(_sp_tmp_name)
                    except OSError:
                        pass
                    raise

            # H2 fix: record seeds used for this month.
            self._seeds_used_per_month.append(len(self._specialist_models))

            if not self._specialist_models:
                if self.verbose > 0:
                    print(f"  [SPECIALIST] all seeds failed for {month_str}")
                return

            # Populate _models/_confidence_thresholds for backward-compat paths
            # (feature-importance logging, _model, etc. still use first specialist).
            self._models = [m for m, _, _ in self._specialist_models]
            self._confidence_thresholds = [ct for _, _, ct in self._specialist_models]
            self._model = self._specialist_models[0][0]
            self._selected_cols = self._specialist_models[0][1]
            self._confidence_threshold = self._specialist_models[0][2]

            # Accumulate per-month feature importance (uses all specialist models).
            _fi_cols = list(self.feature_columns)
            if _fi_cols and self._models:
                _month_gains: dict[str, list[float]] = {c: [] for c in _fi_cols}
                for _m in self._models:
                    _fi_arr: np.ndarray | None = None
                    if hasattr(_m, "booster_"):
                        _fi_arr = _m.booster_.feature_importance(importance_type="gain")
                    elif hasattr(_m, "feature_importances_"):
                        _fi_arr = _m.feature_importances_
                    if _fi_arr is not None:
                        for _i, _c in enumerate(_fi_cols):
                            if _i < len(_fi_arr):
                                _month_gains[_c].append(float(_fi_arr[_i]))
                _mean_gain: dict[str, float] = {
                    c: float(np.mean(v)) if v else 0.0 for c, v in _month_gains.items()
                }
                self._per_month_fi_log.append({"train_month": month_str, "mean_gain": _mean_gain})

            # Load test-month features (uses selected_cols from first specialist).
            _sp_selected_cols = self._specialist_models[0][1]
            symbols = list(dict.fromkeys(self._sym_arr))
            self._month_features = load_features_range(
                symbols,
                self.features_dir,
                self._interval,
                split.test_start_ms,
                split.test_end_ms,
                columns=_sp_selected_cols,
            )
            # OOD detector (shared per-coin per-month — one set of stats for all seeds).
            self._ood_mean = None
            self._ood_inv_cov = None
            self._ood_cutoff = None
            self._month_ood_features = {}
            if self.ood_enabled and self.ood_features:
                ood_cols_in_train = [c for c in self.ood_features if c in train_feat_df.columns]
                if len(ood_cols_in_train) == len(self.ood_features) and len(train_feat_df) >= 100:
                    self._ood_feature_cols = ood_cols_in_train
                    train_ood_raw = train_feat_df[ood_cols_in_train].to_numpy(dtype=np.float64)
                    finite_mask = np.isfinite(train_ood_raw).all(axis=1)
                    train_ood = train_ood_raw[finite_mask]
                    if len(train_ood) >= 100:
                        self._ood_mean = train_ood.mean(axis=0)
                        cov = np.cov(train_ood.T)
                        if cov.ndim == 0:
                            cov = np.array([[float(cov)]])
                        reg = 1e-6 * np.trace(cov) / cov.shape[0] * np.eye(cov.shape[0])
                        try:
                            self._ood_inv_cov = np.linalg.pinv(cov + reg)
                            centered = train_ood - self._ood_mean
                            distances = np.einsum(
                                "ij,jk,ik->i", centered, self._ood_inv_cov, centered
                            )
                            self._ood_cutoff = float(np.quantile(distances, self.ood_cutoff_pct))
                            self._month_ood_features = load_features_range(
                                symbols,
                                self.features_dir,
                                self._interval,
                                split.test_start_ms,
                                split.test_end_ms,
                                columns=ood_cols_in_train,
                            )
                        except np.linalg.LinAlgError:
                            self._ood_mean = None
                            self._ood_inv_cov = None
                            self._ood_cutoff = None
            # Load NATR / σ_t cache.
            self._month_natr = {}
            if self.atr_tp_multiplier is not None:
                natr_data = load_features_range(
                    symbols,
                    self.features_dir,
                    self._interval,
                    split.test_start_ms,
                    split.test_end_ms,
                    columns=[self.atr_column],
                )
                for _k, _arr in natr_data.items():
                    self._month_natr[_k] = float(_arr[0])
            self._month_sigma = {}
            if self.sigma_source == "ewma14d" and self._label_sigma_values is not None:
                test_mask = (self._open_time_arr >= split.test_start_ms) & (
                    self._open_time_arr < split.test_end_ms
                )
                test_indices = np.where(test_mask)[0]
                for _idx in test_indices:
                    _sym = str(self._sym_arr[_idx])
                    _ot = int(self._open_time_arr[_idx])
                    self._month_sigma[(_sym, _ot)] = float(self._label_sigma_values[_idx])

            if self.verbose > 0:
                print(
                    f"  [SPECIALIST] {len(self._specialist_models)} seeds trained for "
                    f"{month_str}: "
                    f"{len(self._month_features)} test candles with features"
                )
            # Early return — skip the standard ensemble loop below.
            return

        # iter-v1/032: lazy-load frozen HP DataFrame on first call.
        if self._frozen_hp_parquet is not None and self._frozen_hp_df is None:
            self._frozen_hp_df = pd.read_parquet(self._frozen_hp_parquet)
            if self.verbose > 0:
                print(
                    f"  [frozen_hp] Loaded {len(self._frozen_hp_df)} rows from "
                    f"{self._frozen_hp_parquet}"
                )

        for i, seed in enumerate(seeds):
            if self.verbose > 0 and len(seeds) > 1:
                print(f"  [ensemble {i + 1}/{len(seeds)}] seed={seed}")
            try:
                # iter-v1/032: when frozen HP is enabled, skip Optuna and train
                # directly with the baseline's best hyperparameters for this cell.
                if self._frozen_hp_df is not None:
                    _model_key = self._model_role  # e.g. "A", "C", "D", "E"
                    _row_mask = (
                        (self._frozen_hp_df["model"] == _model_key)
                        & (self._frozen_hp_df["month"] == month_str)
                        & (self._frozen_hp_df["inner_seed"] == seed)
                    )
                    _hp_rows = self._frozen_hp_df[_row_mask]
                    if _hp_rows.empty:
                        if self.verbose > 0:
                            print(
                                f"  [frozen_hp] WARNING: no baseline HP for model="
                                f"{_model_key!r} month={month_str!r} seed={seed}; "
                                f"skipping this seed"
                            )
                        continue
                    _hp = _hp_rows.iloc[0]
                    import lightgbm as lgb_direct

                    _lgbm_params = {
                        "n_estimators": int(_hp["n_estimators"]),
                        "max_depth": int(_hp["max_depth"]),
                        "num_leaves": int(_hp["num_leaves"]),
                        "learning_rate": float(_hp["learning_rate"]),
                        "subsample": float(_hp["subsample"]),
                        "colsample_bytree": float(_hp["colsample_bytree"]),
                        "min_child_samples": int(_hp["min_child_samples"]),
                        "reg_alpha": float(_hp["reg_alpha"]),
                        "reg_lambda": float(_hp["reg_lambda"]),
                        "random_state": seed,
                        "n_jobs": -1,
                        "verbose": -1,
                    }
                    confidence_threshold = float(_hp["confidence_threshold"])
                    _clf = lgb_direct.LGBMClassifier(**_lgbm_params)
                    _clf.fit(feat_train, train_labels, sample_weight=train_weights)
                    model = _clf
                    selected_cols = available_feat_cols
                    if self.verbose > 0:
                        print(
                            f"  [frozen_hp] Trained with baseline HP: "
                            f"n_est={_lgbm_params['n_estimators']} "
                            f"depth={_lgbm_params['max_depth']} "
                            f"ct={confidence_threshold:.3f}"
                        )
                else:
                    model, selected_cols, confidence_threshold = optimize_and_train(
                        feat_train,
                        train_labels,
                        available_feat_cols,
                        long_pnls,
                        short_pnls,
                        self.n_trials,
                        self.cv_splits,
                        seed,
                        self.verbose,
                        sample_weights=train_weights,
                        open_times=train_open_times,
                        train_end_ms=split.train_end_ms,
                        ternary=ternary,
                        cv_gap=cv_gap,
                        oof_persist_path=self._oof_persist_path,
                        train_month=month_str,
                        symbols_arr=train_symbols_arr,
                        fast_mode=self._fast_mode,
                        bounds_profile=self._bounds_profile,
                        params_persist_path=self._params_persist_path,
                        model_role=self._model_role,
                        symbol=self._symbol,
                        optuna_objective=self._optuna_objective,
                        min_child_samples_lower_bound=self._min_child_samples_lower_bound,
                    )
                self._models.append(model)
                self._confidence_thresholds.append(confidence_threshold)
            except Exception as exc:
                if self.verbose > 0:
                    print(f"  Optimization failed for {month_str} seed={seed}: {exc}")

        if not self._models:
            return

        # Use first model as primary (backward compat)
        self._model = self._models[0]
        self._selected_cols = selected_cols
        # iter-v3/067 Path D: apply universal inference-time confidence-threshold floor.
        # Floor=0.60 raises the bar for marginal-confidence trades whose Optuna-inherited
        # per-seed mean falls below 0.60 (brief Section 3 Sub-fix 1 + Sub-fix 2).
        # Default floor=0.0 is a no-op, preserving backward compatibility for v1/v2/earlier v3.
        # Ref: Critic /066 Rec #2 — Path D is a GATE modifier, not a WEIGHT modifier.
        self._confidence_threshold = float(
            max(np.mean(self._confidence_thresholds), self._inference_threshold_floor)
        )

        # iter-v1/021 BLOCK-PENDING-FIX H2: accumulate per-month mean gain per feature.
        # Done here (after ensemble loop, before _models is reset next month) so
        # _write_feature_importance can aggregate across months instead of reading
        # stale post-dispatch _models.  Uses booster_.feature_importance('gain')
        # matching the importance_type='gain' mandate in LM Master Phase 4.5 §4.
        _fi_cols = list(self.feature_columns)
        if _fi_cols and self._models:
            _month_gains: dict[str, list[float]] = {c: [] for c in _fi_cols}
            for _m in self._models:
                _fi_arr: np.ndarray | None = None
                if hasattr(_m, "booster_"):
                    _fi_arr = _m.booster_.feature_importance(importance_type="gain")
                elif hasattr(_m, "feature_importances_"):
                    _fi_arr = _m.feature_importances_
                if _fi_arr is not None:
                    for _i, _c in enumerate(_fi_cols):
                        if _i < len(_fi_arr):
                            _month_gains[_c].append(float(_fi_arr[_i]))
            _mean_gain: dict[str, float] = {
                c: float(np.mean(v)) if v else 0.0 for c, v in _month_gains.items()
            }
            self._per_month_fi_log.append({"train_month": month_str, "mean_gain": _mean_gain})

        # (e) Batch-load test month features
        symbols = list(dict.fromkeys(self._sym_arr))
        self._month_features = load_features_range(
            symbols,
            self.features_dir,
            self._interval,
            split.test_start_ms,
            split.test_end_ms,
            columns=selected_cols,
        )

        # (e2) R3 OOD detector — training-window Mahalanobis stats
        self._ood_mean = None
        self._ood_inv_cov = None
        self._ood_cutoff = None
        self._month_ood_features = {}
        if self.ood_enabled and self.ood_features:
            ood_cols_in_train = [c for c in self.ood_features if c in train_feat_df.columns]
            if len(ood_cols_in_train) < len(self.ood_features):
                missing = set(self.ood_features) - set(ood_cols_in_train)
                if self.verbose > 0:
                    print(f"  OOD: missing features {missing} — disabling for this month")
            elif len(train_feat_df) < 100:
                if self.verbose > 0:
                    print("  OOD: insufficient training samples — disabling for this month")
            else:
                self._ood_feature_cols = ood_cols_in_train
                train_ood_raw = train_feat_df[ood_cols_in_train].to_numpy(dtype=np.float64)
                # Drop rows with NaN/inf before computing mean/cov
                finite_mask = np.isfinite(train_ood_raw).all(axis=1)
                train_ood = train_ood_raw[finite_mask]
                if len(train_ood) < 100:
                    if self.verbose > 0:
                        print(
                            "  OOD: insufficient finite training rows "
                            f"({len(train_ood)}) — disabling for this month"
                        )
                else:
                    self._ood_mean = train_ood.mean(axis=0)
                    cov = np.cov(train_ood.T)
                    # Ridge regularization — stabilizes pinv when features
                    # are near-collinear (returns at lag 1/2/5/10 are correlated).
                    reg = 1e-6 * np.trace(cov) / cov.shape[0] * np.eye(cov.shape[0])
                    try:
                        self._ood_inv_cov = np.linalg.pinv(cov + reg)
                        centered = train_ood - self._ood_mean
                        distances = np.einsum("ij,jk,ik->i", centered, self._ood_inv_cov, centered)
                        self._ood_cutoff = float(np.quantile(distances, self.ood_cutoff_pct))
                        if self.verbose > 0:
                            print(
                                f"  OOD: {len(ood_cols_in_train)} features, "
                                f"cutoff (q={self.ood_cutoff_pct}) = "
                                f"{self._ood_cutoff:.2f}"
                            )
                        self._month_ood_features = load_features_range(
                            symbols,
                            self.features_dir,
                            self._interval,
                            split.test_start_ms,
                            split.test_end_ms,
                            columns=ood_cols_in_train,
                        )
                    except np.linalg.LinAlgError:
                        self._ood_mean = None
                        self._ood_inv_cov = None
                        self._ood_cutoff = None
                        if self.verbose > 0:
                            print("  OOD: cov inversion failed — disabled for this month")

        # (f) Load NATR for dynamic barriers (if ATR mode enabled)
        self._month_natr = {}
        if self.atr_tp_multiplier is not None:
            natr_data = load_features_range(
                symbols,
                self.features_dir,
                self._interval,
                split.test_start_ms,
                split.test_end_ms,
                columns=[self.atr_column],
            )
            for key, arr in natr_data.items():
                self._month_natr[key] = float(arr[0])

        # (g) iter-v1/015 C1 FIX: populate σ_t cache for execution-time barriers.
        # When sigma_source="ewma14d", read _label_sigma_values for every candle
        # in the test window and cache by (symbol, open_time_ms) — same key space
        # as _month_natr so get_signal can look up per-candle sigma identically.
        # This ensures execution-time barriers match label-time barriers (C1 FIX).
        self._month_sigma = {}
        if self.sigma_source == "ewma14d" and self._label_sigma_values is not None:
            test_mask = (self._open_time_arr >= split.test_start_ms) & (
                self._open_time_arr < split.test_end_ms
            )
            test_indices = np.where(test_mask)[0]
            for idx in test_indices:
                sym = str(self._sym_arr[idx])
                ot = int(self._open_time_arr[idx])
                self._month_sigma[(sym, ot)] = float(self._label_sigma_values[idx])

        if self.verbose > 0:
            print(
                f"  Model trained for {month_str}: "
                f"{len(self._month_features)} test candles with features, "
                f"confidence_threshold={self._confidence_threshold:.3f}"
            )

    def skip(self) -> None:
        pass

    def set_period(self, period: str) -> None:
        """Set the current evaluation period for dispersion tagging (H8/H9 fix).

        Must be called by the runner at the IS/OOS boundary (i.e. when candle
        open_time crosses OOS_CUTOFF_MS).  All subsequent dispersion entries will
        carry ``period`` in their dict.

        Args:
            period: ``"IS"`` or ``"OOS"``.  Any other value raises ValueError.
        """
        if period not in ("IS", "OOS"):
            raise ValueError(f"period must be 'IS' or 'OOS'; got {period!r}")
        self._current_period = period

    def get_specialist_dispersion_mean(self, period: str | None = None) -> float | None:
        """Return mean population std of signed_weights across firing specialist candles.

        This is the σ_pop proxy for /064+ brief F-AXIS #2.  Under the 50-seed
        specialist aggregator, σ_SR (cross-seed Sharpe spread) is structurally
        undefined because all seeds produce a single aggregated backtest rather
        than 50 separate backtests.  This per-candle ensemble_std metric fills
        that role: it measures how spread the 50 seeds' signed_weights are for
        each candle that generated a signal AND passed the AXIS-R veto.

        H8/H9 fix: each entry in _specialist_dispersion_stats is a dict; the
        optional ``period`` arg filters to "IS" or "OOS" rows.

        Args:
            period: If None (default), compute mean across all periods.
                    If ``"IS"`` or ``"OOS"``, restrict to that period's rows.

        Returns None when no matching signals have fired yet.
        Acceptance threshold should be calibrated empirically in /064+ iterations;
        this diagnostic is informational, NOT a load-bearing gate.
        """
        if not self._specialist_dispersion_stats:
            return None
        if period is None:
            vals = [e["signed_weight_std"] for e in self._specialist_dispersion_stats]
        else:
            vals = [
                e["signed_weight_std"]
                for e in self._specialist_dispersion_stats
                if e["period"] == period
            ]
        if not vals:
            return None
        return float(np.mean(vals))

    def get_n_seeds_used_mean(self) -> float | None:
        """Return mean number of successfully-trained seeds across walk-forward months.

        H2 fix — provides the N_seeds_used scalar for comparison.csv so downstream
        readers can audit whether systematic seed failures degraded the specialist
        ensemble.  Returns None when no months have been trained yet (non-specialist
        mode, or called before the first _train_for_month).

        Expected value under healthy conditions: close to V1_SPECIALIST_SEED_COUNT (50).
        A value materially below 45 (= tolerance of 5) should trigger investigation.
        """
        if not self._seeds_used_per_month:
            return None
        return float(np.mean(self._seeds_used_per_month))

    def persist_specialist_dispersion_csv(self, path: str, period: str | None = None) -> None:
        """Persist the in-memory specialist dispersion stats to a CSV file.

        H8/H9 fix: each entry in ``_specialist_dispersion_stats`` is now a dict
        with fields ``open_time_ms``, ``signed_weight_std``, and ``period``.
        The ``period`` argument filters which rows are written:
        - ``None`` (default) — writes all rows (backward-compatible legacy callers
          that pass a single combined path).
        - ``"IS"`` — writes only IS-period rows (for in_sample/ subdirectory).
        - ``"OOS"`` — writes only OOS-period rows (for out_of_sample/ subdirectory).

        Writes three columns:
        - ``observation_idx`` — 0-based index within the filtered row set.
        - ``open_time_ms`` — candle open time in epoch milliseconds.
        - ``signed_weight_std`` — per-candle population std of signed_weights.

        This method is the load-bearing hygiene patch mandated by LM Master
        Risk 1 (iter-v1/065 lgbm_advisor.md) and brief Section 6.5.  /065+
        runners MUST call this method after the per-symbol backtest completes.
        Post-H8/H9: runners should call once with period="IS" for IS reports
        and once with period="OOS" for OOS reports.

        If the filtered accumulator is empty (no signals fired in that period),
        writes a zero-row CSV with the header intact so downstream readers do
        not crash.

        Args:
            path: Absolute or relative filesystem path for the output CSV.
                  Parent directory is created if it does not exist.
            period: Optional filter — ``"IS"``, ``"OOS"``, or ``None`` (all).
        """
        import csv as _csv  # noqa: PLC0415

        if period is None:
            rows_to_write = self._specialist_dispersion_stats
        else:
            rows_to_write = [e for e in self._specialist_dispersion_stats if e["period"] == period]

        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", newline="") as _fh:
            writer = _csv.DictWriter(
                _fh, fieldnames=["observation_idx", "open_time_ms", "signed_weight_std"]
            )
            writer.writeheader()
            for idx, entry in enumerate(rows_to_write):
                writer.writerow(
                    {
                        "observation_idx": idx,
                        "open_time_ms": entry["open_time_ms"],
                        "signed_weight_std": entry["signed_weight_std"],
                    }
                )
        n_obs = len(rows_to_write)
        mean_val = self.get_specialist_dispersion_mean(period=period)
        period_label = f"period={period}" if period is not None else "all periods"
        print(
            f"[lgbm] specialist_dispersion.csv persisted: "
            f"{n_obs} observations ({period_label}) → {out_path} "
            f"(mean σ_pop={mean_val:.4f})"
            if mean_val is not None
            else f"[lgbm] specialist_dispersion.csv persisted: "
            f"{n_obs} observations ({period_label}, empty — no signals fired) → {out_path}"
        )

    def _compute_ret_270b(self, symbol: str, open_time: int) -> float | None:
        """Compute trailing-270-bar return for AXIS-R veto (iter-v1/074).

        Returns (close[t] / close[t - lookback]) - 1.0 where lookback =
        self._mid_bull_short_veto_lookback (270 by default = 90 calendar days
        on 8h candles).  Returns None when insufficient history is available.

        Uses the per-symbol sorted (open_time_ms, close) index built in
        compute_features(); O(log n) binary search per call.
        """
        sym_data = self._close_by_sym.get(symbol)
        if sym_data is None:
            return None
        ot_arr, cl_arr = sym_data
        # Find the position of the current candle.
        idx_curr = int(np.searchsorted(ot_arr, open_time, side="left"))
        if idx_curr >= len(ot_arr):
            return None
        # Need lookback bars before this candle (not including it).
        idx_past = idx_curr - self._mid_bull_short_veto_lookback
        if idx_past < 0:
            return None
        close_curr = cl_arr[idx_curr]
        close_past = cl_arr[idx_past]
        if close_past <= 0.0 or not np.isfinite(close_curr) or not np.isfinite(close_past):
            return None
        return float(close_curr / close_past) - 1.0

    def _apply_mid_bull_short_veto(self, signal: Signal, symbol: str, open_time: int) -> Signal:
        """Apply AXIS-R Mid-Bull SHORT VETO to an aggregated signal (iter-v1/074).

        Veto fires when:
          signal.direction == -1
          AND ret_270b = (close[t] / close[t-270]) - 1.0 ∈ [lo, hi]

        Long signals, flat signals, and candles outside the band are untouched.
        Logs forensic event kind=axis_r_veto for Phase 7 counterfactual audit.

        Args:
            signal: Aggregated signal from the 50-seed mean-of-signed-weights.
            symbol: Trading symbol (e.g. "ETHUSDT").
            open_time: Candle open_time in epoch milliseconds.

        Returns:
            Original signal (if veto does not fire) or Signal(direction=0, weight=0).
        """
        if not self._enable_mid_bull_short_veto:
            return signal
        if signal.direction != -1:
            return signal
        ret_270b = self._compute_ret_270b(symbol, open_time)
        if ret_270b is None:
            return signal
        if self._mid_bull_short_veto_lo <= ret_270b <= self._mid_bull_short_veto_hi:
            from crypto_trade import decision_log

            decision_log.log(
                {
                    "kind": "axis_r_veto",
                    "symbol": symbol,
                    "ot": open_time,
                    "ret_270b": ret_270b,
                    "veto_lo": self._mid_bull_short_veto_lo,
                    "veto_hi": self._mid_bull_short_veto_hi,
                    "signal_direction_pre_veto": signal.direction,
                    "signal_weight_pre_veto": signal.weight,
                }
            )
            self._axis_r_veto_log.append(
                {
                    "symbol": symbol,
                    "open_time": open_time,
                    "ret_270b": ret_270b,
                    "direction_pre_veto": signal.direction,
                    "weight_pre_veto": signal.weight,
                }
            )
            return Signal(direction=0, weight=0)
        return signal

    def _apply_oi_divergence_fade_gate(
        self,
        signal: Signal,
        feat_row: np.ndarray,
        symbol: str,
        open_time: int,
    ) -> Signal:
        """Apply R-FADE OI-divergence-conditional confidence gate (iter-v1/084).

        Gate fires when:
          |oi_price_divergence_30[t]| > fade_z
          AND sign(signal.direction) OPPOSES sign(oi_price_divergence_30[t])

        When OI divergence contradicts the trade direction with sufficient strength,
        the entry is VETOED (returns NO_SIGNAL). State-free, post-aggregator.

        Logic:
          oi_div > 0 means sign(OI_delta) > sign(price_ret) — OI building against price.
          oi_div < 0 means sign(OI_delta) < sign(price_ret) — OI retreating with price.
          FADE fires when trade direction AGREES with price direction but OPPOSES OI.
          Concretely:
            - signal.direction == +1 (long) AND oi_div < -fade_z (OI retreating, bearish)
            - signal.direction == -1 (short) AND oi_div > +fade_z (OI building, bullish)

        Args:
            signal: Aggregated signal from the specialist mean-of-signed-weights.
            feat_row: Feature vector numpy array (aligned with _selected_cols).
            symbol: Trading symbol.
            open_time: Candle open_time in epoch milliseconds.

        Returns:
            Original signal if gate does not fire, or Signal(direction=0, weight=0).
        """
        if not self._enable_oi_divergence_fade_gate:
            return signal
        if signal.direction == 0:
            return signal

        # Look up the OI divergence value from the feature row.
        col_name = self._oi_divergence_fade_column
        try:
            col_idx = self._selected_cols.index(col_name)
        except ValueError:
            # Column not in feature set — gate cannot fire (graceful degradation).
            return signal

        oi_div_val = float(feat_row[col_idx])
        if not np.isfinite(oi_div_val):
            # NaN/inf — cannot evaluate gate; pass through (conservative).
            return signal

        fade_z = self._oi_divergence_fade_z
        # Gate fires when signal direction OPPOSES OI divergence direction strongly.
        # oi_div > 0 means OI building vs price (bullish OI signal).
        # oi_div < 0 means OI retreating vs price (bearish OI signal).
        # FADE: veto LONG when oi_div < -fade_z (bearish OI signal contradicts long).
        #       veto SHORT when oi_div > +fade_z (bullish OI signal contradicts short).
        gate_fires = (signal.direction == 1 and oi_div_val < -fade_z) or (
            signal.direction == -1 and oi_div_val > fade_z
        )
        if gate_fires:
            from crypto_trade import decision_log

            event = {
                "kind": "oi_divergence_fade_gate",
                "symbol": symbol,
                "ot": open_time,
                "oi_div_val": oi_div_val,
                "fade_z": fade_z,
                "signal_direction_pre_fade": signal.direction,
                "signal_weight_pre_fade": signal.weight,
            }
            decision_log.log(event)
            self._oi_divergence_fade_log.append(
                {
                    "symbol": symbol,
                    "open_time": open_time,
                    "oi_div_val": oi_div_val,
                    "direction_pre_fade": signal.direction,
                    "weight_pre_fade": signal.weight,
                }
            )
            return Signal(direction=0, weight=0)
        return signal

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        """Return signal for one candle. Always predicts 1 or -1."""
        # Detect month change → lazy training
        candle_month = _epoch_ms_to_month(open_time)
        if candle_month != self._current_month:
            self._current_month = candle_month
            self._train_for_month(candle_month)

        self._last_predict_log: str | None = None

        if not self._models:
            return NO_SIGNAL

        # Look up features from month cache
        key = (symbol, open_time)
        feat_row = self._month_features.get(key)

        # iter-v1/063: SPECIALIST aggregator — mean of signed weights.
        # Each seed evaluates probability against ITS OWN threshold independently.
        # Aggregation: final_signed = mean(direction_i × weight_i) across 50 seeds.
        # R3 OOD is SHARED (applied once below, same as non-specialist path).
        if self._specialist_mode and self._specialist_models:
            if feat_row is None:
                from crypto_trade import decision_log

                decision_log.log(
                    {
                        "kind": "lgbm_signal",
                        "symbol": symbol,
                        "ot": open_time,
                        "month": candle_month,
                        "decision": "skipped:no_features",
                    }
                )
                return NO_SIGNAL

            feat_df_sp = pd.DataFrame(feat_row.reshape(1, -1), columns=self._selected_cols)

            # R3 OOD check (SHARED — evaluated once before aggregating seeds).
            if (
                self.ood_enabled
                and self._ood_mean is not None
                and self._ood_inv_cov is not None
                and self._ood_cutoff is not None
            ):
                ood_row = self._month_ood_features.get(key)
                if ood_row is not None and np.isfinite(ood_row).all():
                    diff = ood_row.astype(np.float64) - self._ood_mean
                    dist = float(diff @ self._ood_inv_cov @ diff)
                    if dist > self._ood_cutoff:
                        from crypto_trade import decision_log

                        decision_log.log(
                            {
                                "kind": "lgbm_signal",
                                "symbol": symbol,
                                "ot": open_time,
                                "month": candle_month,
                                "ood_dist": dist,
                                "ood_cutoff": float(self._ood_cutoff),
                                "decision": "skipped:ood",
                            }
                        )
                        return NO_SIGNAL

            ternary_sp = self.neutral_threshold_pct is not None
            _signed_weights: list[float] = []
            for _sp_model, _sp_cols, _sp_ct in self._specialist_models:
                # Re-build feat_df with this seed's selected columns (may differ).
                if _sp_cols != self._selected_cols:
                    _feat_df_i = pd.DataFrame(
                        feat_row.reshape(1, -1)[:, : len(_sp_cols)],
                        columns=_sp_cols,
                    )
                else:
                    _feat_df_i = feat_df_sp
                _proba_i = _sp_model.predict_proba(_feat_df_i)[0]
                if ternary_sp:
                    _conf_i = max(float(_proba_i[0]), float(_proba_i[2]))
                    _dir_i = 1 if float(_proba_i[2]) >= float(_proba_i[0]) else -1
                else:
                    _conf_i = float(max(_proba_i))
                    _dir_i = int(classes_to_labels(np.array([int(np.argmax(_proba_i))]))[0])
                _weight_i = 100 if _conf_i > _sp_ct else 0
                _signed_weights.append(float(_dir_i) * float(_weight_i))

            _final_signed = float(np.mean(_signed_weights)) if _signed_weights else 0.0
            # iter-v1/063: per-candle ensemble dispersion (population std of signed_weights).
            # Computed regardless of whether the signal fires — useful for diagnosing
            # no-consensus candles too.  Appended to dispersion stats only when signal
            # fires (below) to avoid polluting the diagnostic with skipped candles.
            _ensemble_std = float(np.std(_signed_weights)) if len(_signed_weights) > 1 else 0.0

            if abs(_final_signed) < 1e-9:
                # All seeds voted 0 (below threshold) or perfectly cancelled.
                from crypto_trade import decision_log

                decision_log.log(
                    {
                        "kind": "lgbm_signal",
                        "symbol": symbol,
                        "ot": open_time,
                        "month": candle_month,
                        "specialist_seeds": len(self._specialist_models),
                        "final_signed": _final_signed,
                        "ensemble_std": _ensemble_std,
                        "decision": "skipped:specialist_no_consensus",
                    }
                )
                return NO_SIGNAL

            _sp_direction = 1 if _final_signed > 0 else -1
            _sp_weight = int(round(abs(_final_signed)))
            _sp_confidence = abs(_final_signed) / 100.0

            # iter-v1/091: R-CONV — ensemble-conviction trade gate.
            # Post-aggregator RULE layer (same band as /074 AXIS-R + /084 R-FADE).
            # Skip candles whose net seed-agreement fraction _sp_confidence < r_conv_tau.
            # Stateless; does NOT change the model, seeds, trials, or Optuna objective.
            # Default False = BIT-IDENTICAL to all prior iterations when gate is OFF.
            # The r_conv_skip decision_log entry carries ensemble_std so Phase 7.4 can
            # split the dropped set by abstention (low std) vs disagreement (high std)
            # — LM §1 REQUIRED deliverable.
            # NOTE: _specialist_dispersion_stats.append() is NOT reached for skipped
            # candles (gate fires here, before the dispersion append below). Correct:
            # skipped candles must not pollute the dispersion diagnostic.
            if self._enable_r_conv_gate and _sp_confidence < self._r_conv_tau:
                from crypto_trade import decision_log

                decision_log.log(
                    {
                        "kind": "r_conv_skip",
                        "symbol": symbol,
                        "ot": open_time,
                        "month": candle_month,
                        "specialist_seeds": len(self._specialist_models),
                        "final_signed": _final_signed,
                        "ensemble_std": _ensemble_std,
                        "confidence": _sp_confidence,
                        "r_conv_tau": self._r_conv_tau,
                        "decision": "skipped:r_conv_low_conviction",
                    }
                )
                return NO_SIGNAL

            # NATR-based dynamic TP/SL (same as non-specialist path).
            _sp_tp_pct = None
            _sp_sl_pct = None
            if self.atr_tp_multiplier is not None:
                _natr_sp = self._month_natr.get(key)
                if _natr_sp is not None and _natr_sp > 0:
                    _sp_tp_pct = _natr_sp * self.atr_tp_multiplier
                    _sp_sl_pct = _natr_sp * (
                        self.atr_sl_multiplier
                        if self.atr_sl_multiplier is not None
                        else self.atr_tp_multiplier / 2.0
                    )

            from crypto_trade import decision_log

            # iter-v1/074: AXIS-R Mid-Bull SHORT VETO — post-aggregator rule layer.
            # Applied AFTER mean-of-signed-weights aggregator emits Signal(direction, weight)
            # and BEFORE R3 OOD / R5 vol-target call-sites (pre-registered; anti-tuning).
            _sp_signal_pre_veto = Signal(
                direction=_sp_direction,
                weight=_sp_weight,
                tp_pct=_sp_tp_pct,
                sl_pct=_sp_sl_pct,
                confidence=_sp_confidence,
            )
            _sp_signal = self._apply_mid_bull_short_veto(_sp_signal_pre_veto, symbol, open_time)
            if _sp_signal.direction == 0:
                # Veto fired — log and return NO_SIGNAL (not the vetoed direction).
                decision_log.log(
                    {
                        "kind": "lgbm_signal",
                        "symbol": symbol,
                        "ot": open_time,
                        "month": candle_month,
                        "specialist_seeds": len(self._specialist_models),
                        "final_signed": _final_signed,
                        "ensemble_std": _ensemble_std,
                        "direction_pre_veto": _sp_direction,
                        "decision": "vetoed:axis_r_mid_bull_short",
                    }
                )
                return NO_SIGNAL

            # iter-v1/084: R-FADE — OI-divergence-conditional confidence gate.
            # Applied AFTER AXIS-R veto and BEFORE R3 OOD / R5 vol-target call-sites.
            # Stateless post-aggregator gate: VETO entry when OI-price divergence
            # strongly contradicts the trade direction.
            _sp_signal = self._apply_oi_divergence_fade_gate(
                _sp_signal, feat_row, symbol, open_time
            )
            if _sp_signal.direction == 0:
                # R-FADE gate fired — log and return NO_SIGNAL.
                decision_log.log(
                    {
                        "kind": "lgbm_signal",
                        "symbol": symbol,
                        "ot": open_time,
                        "month": candle_month,
                        "specialist_seeds": len(self._specialist_models),
                        "final_signed": _final_signed,
                        "ensemble_std": _ensemble_std,
                        "direction_pre_fade": _sp_direction,
                        "decision": "vetoed:oi_divergence_fade_gate",
                    }
                )
                return NO_SIGNAL

            # H8/H9 fix: accumulate dispersion diagnostic AFTER AXIS-R veto so
            # vetoed candles are excluded from the dispersion stats.  Tag each
            # entry with open_time_ms and the current period ("IS"/"OOS") so
            # persist_specialist_dispersion_csv() can produce separate files.
            self._specialist_dispersion_stats.append(
                {
                    "open_time_ms": int(open_time),
                    "signed_weight_std": _ensemble_std,
                    "period": self._current_period,
                }
            )

            decision_log.log(
                {
                    "kind": "lgbm_signal",
                    "symbol": symbol,
                    "ot": open_time,
                    "month": candle_month,
                    "specialist_seeds": len(self._specialist_models),
                    "final_signed": _final_signed,
                    "ensemble_std": _ensemble_std,
                    "direction": _sp_direction,
                    "tp_pct": _sp_tp_pct,
                    "sl_pct": _sp_sl_pct,
                    "confidence": _sp_confidence,
                    "decision": "signal",
                }
            )
            return _sp_signal
        if feat_row is None:
            from crypto_trade import decision_log

            decision_log.log(
                {
                    "kind": "lgbm_signal",
                    "symbol": symbol,
                    "ot": open_time,
                    "month": candle_month,
                    "decision": "skipped:no_features",
                }
            )
            return NO_SIGNAL

        # Predict with all ensemble models and average probabilities
        feat_df = pd.DataFrame(feat_row.reshape(1, -1), columns=self._selected_cols)
        all_proba = [m.predict_proba(feat_df)[0] for m in self._models]
        proba = np.mean(all_proba, axis=0)

        ternary = self.neutral_threshold_pct is not None

        if ternary:
            # 3-class: [P(short), P(neutral), P(long)]
            # Confidence = max(P(short), P(long)), ignoring neutral
            directional_conf = max(float(proba[0]), float(proba[2]))
            confidence = directional_conf
        else:
            # Binary: [P(short), P(long)]
            confidence = float(max(proba))

        from crypto_trade import decision_log

        if confidence < self._confidence_threshold:
            if self.verbose > 0:
                ts_str = _ms_to_datetime(open_time)
                self._last_predict_log = (
                    f"[predict] {ts_str} {symbol} → SKIP "
                    f"(conf={confidence:.2f} < "
                    f"{self._confidence_threshold:.2f})"
                )
            decision_log.log(
                {
                    "kind": "lgbm_signal",
                    "symbol": symbol,
                    "ot": open_time,
                    "month": candle_month,
                    "threshold": float(self._confidence_threshold),
                    "ensemble_proba": proba,
                    "per_seed_probas": [p for p in all_proba],
                    "feat_hash": decision_log.hash_features(feat_row),
                    "feat_values": {
                        c: float(feat_row[i]) for i, c in enumerate(self._selected_cols)
                    },
                    "decision": "skipped:below_threshold",
                }
            )
            return NO_SIGNAL

        # R3 OOD detector: skip candles where features are too far from training
        if (
            self.ood_enabled
            and self._ood_mean is not None
            and self._ood_inv_cov is not None
            and self._ood_cutoff is not None
        ):
            ood_row = self._month_ood_features.get(key)
            if ood_row is not None and np.isfinite(ood_row).all():
                diff = ood_row.astype(np.float64) - self._ood_mean
                dist = float(diff @ self._ood_inv_cov @ diff)
                if dist > self._ood_cutoff:
                    if self.verbose > 0:
                        ts_str = _ms_to_datetime(open_time)
                        self._last_predict_log = (
                            f"[predict] {ts_str} {symbol} → SKIP "
                            f"(OOD dist={dist:.2f} > {self._ood_cutoff:.2f})"
                        )
                    decision_log.log(
                        {
                            "kind": "lgbm_signal",
                            "symbol": symbol,
                            "ot": open_time,
                            "month": candle_month,
                            "threshold": float(self._confidence_threshold),
                            "ensemble_proba": proba,
                            "ood_dist": dist,
                            "ood_cutoff": float(self._ood_cutoff),
                            "feat_hash": decision_log.hash_features(feat_row),
                            "decision": "skipped:ood",
                        }
                    )
                    return NO_SIGNAL

        # Regime filter: skip low-volatility candles
        if self.min_natr_threshold is not None:
            natr = self._month_natr.get((symbol, open_time))
            if natr is not None and natr < self.min_natr_threshold:
                if self.verbose > 0:
                    ts_str = _ms_to_datetime(open_time)
                    self._last_predict_log = (
                        f"[predict] {ts_str} {symbol} → SKIP "
                        f"(NATR={natr:.2f}% < "
                        f"{self.min_natr_threshold:.1f}%)"
                    )
                decision_log.log(
                    {
                        "kind": "lgbm_signal",
                        "symbol": symbol,
                        "ot": open_time,
                        "month": candle_month,
                        "natr": float(natr),
                        "min_natr": float(self.min_natr_threshold),
                        "decision": "skipped:low_natr",
                    }
                )
                return NO_SIGNAL

        if ternary:
            # Direction from long vs short probability only
            direction = 1 if proba[2] >= proba[0] else -1
        else:
            pred_class = int(np.argmax(proba))
            direction = int(classes_to_labels(np.array([pred_class]))[0])

        # Compute dynamic TP/SL: dispatch on sigma_source.
        # - "natr" (default): BIT-IDENTICAL to pre-/015 behavior.
        # - "ewma14d" (iter-v1/015 C1 FIX): σ_t × k × √timeout × 100 at execution-time,
        #   matching the label-time formula.  Raises RuntimeError on NaN/missing σ_t
        #   (per LM Master Phase 4.5 Rec #3 mandate — refuse silent NATR fallback).
        tp_pct = None
        sl_pct = None
        if self.sigma_source == "ewma14d":
            sigma = self._month_sigma.get(key)
            if sigma is None or np.isnan(sigma):
                raise RuntimeError(
                    f"σ_t unavailable for {key}; refusing silent NATR fallback. "
                    "Ensure _label_sigma_values is populated and the candle is in "
                    "the test window.  (iter-v1/015 C1 FIX — LM Master Rec #3)"
                )
            interval_minutes = _interval_to_minutes(self._interval)
            timeout_candles = self.label_timeout_minutes / interval_minutes
            sqrt_timeout = float(np.sqrt(timeout_candles))
            tp_pct = float(sigma * self.sigma_k_tp * sqrt_timeout * 100.0)
            sl_pct = float(sigma * self.sigma_k_sl * sqrt_timeout * 100.0)
        elif self.atr_tp_multiplier is not None:
            natr = self._month_natr.get(key)
            if natr is not None and natr > 0:
                tp_pct = natr * self.atr_tp_multiplier
                sl_pct = natr * (
                    self.atr_sl_multiplier
                    if self.atr_sl_multiplier is not None
                    else self.atr_tp_multiplier / 2.0
                )

        if self.verbose > 0:
            dir_label = "LONG" if direction == 1 else "SHORT"
            ts_str = _ms_to_datetime(open_time)
            atr_str = ""
            if tp_pct is not None and self.sigma_source == "ewma14d":
                atr_str = f" σ_t-TP={tp_pct:.1f}%/σ_t-SL={sl_pct:.1f}%"
            elif tp_pct is not None:
                atr_str = f" TP={tp_pct:.1f}%/SL={sl_pct:.1f}%"
            self._last_predict_log = (
                f"[predict] {ts_str} {symbol} → {dir_label} (proba={confidence:.2f}{atr_str})"
            )

        decision_log.log(
            {
                "kind": "lgbm_signal",
                "symbol": symbol,
                "ot": open_time,
                "month": candle_month,
                "threshold": float(self._confidence_threshold),
                "ensemble_proba": proba,
                "per_seed_probas": [p for p in all_proba],
                "feat_hash": decision_log.hash_features(feat_row),
                "feat_values": {c: float(feat_row[i]) for i, c in enumerate(self._selected_cols)},
                "direction": direction,
                "tp_pct": tp_pct,
                "sl_pct": sl_pct,
                "confidence": confidence,
                "decision": "signal",
            }
        )
        return Signal(
            direction=direction,
            weight=100,
            tp_pct=tp_pct,
            sl_pct=sl_pct,
            confidence=confidence,
        )

    @staticmethod
    def _detect_interval(master: pd.DataFrame) -> str:
        """Detect interval from typical close_time - open_time gap."""
        if len(master) < 2:
            return "8h"
        diff = master["close_time"].iloc[0] - master["open_time"].iloc[0]
        interval_map = {
            59_999: "1m",
            179_999: "3m",
            299_999: "5m",
            899_999: "15m",
            1_799_999: "30m",
            3_599_999: "1h",
            14_399_999: "4h",
            28_799_999: "8h",
            43_199_999: "12h",
            86_399_999: "24h",  # iter-v3/117: 24h bars named "24h" to match parquet suffix
        }
        best = "8h"
        best_dist = abs(diff - 28_799_999)
        for ms, name in interval_map.items():
            dist = abs(diff - ms)
            if dist < best_dist:
                best_dist = dist
                best = name
        return best
