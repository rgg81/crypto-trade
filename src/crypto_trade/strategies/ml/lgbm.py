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
    optimize_and_train,
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
        # iter-v3/007: fast exploration mode (colsample fixed at 1.0 in optimization.py)
        self._fast_mode: bool = fast_mode
        # iter-v1/002: Optuna hyperparameter bounds profile.
        # "default" = original 193-feature bounds (all tracks except v1_pruned).
        # "v1_pruned" = tighter bounds for 40-feature pruned set per LM Master
        # Phase 4.5 Recs #1–3. Forwarded to optimization.optimize_and_train.
        self._bounds_profile: str = bounds_profile
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
        # "abs_pnl"        (default) — BIT-IDENTICAL to baseline; keeps label_trades output.
        # "uniform"        — replaces train_weights with np.ones(n); Kish n_eff = 1.000.
        # "uniqueness_only" — replaces train_weights with raw compute_sample_uniqueness output
        #                     (NOT multiplied by abs_pnl — the prior multiply was a near-no-op
        #                     per EDA Section 2.5: Spearman 0.997 after multiply).
        _valid_modes = {"abs_pnl", "uniform", "uniqueness_only"}
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

        # (b3) Apply time decay weighting
        if self.time_decay_half_life is not None:
            train_times = self._open_time_arr[train_indices]
            max_time = train_times.max()
            age_ms = max_time - train_times
            age_months = age_ms / (30.44 * 24 * 3600 * 1000)  # approx months
            lam = np.log(2) / self.time_decay_half_life
            decay = np.exp(-lam * age_months)
            train_weights = train_weights * decay
            if self.verbose > 0:
                print(
                    f"  Time decay (half_life={self.time_decay_half_life}mo): "
                    f"min={decay.min():.3f}, mean={decay.mean():.3f}, "
                    f"max={decay.max():.3f}"
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

        for i, seed in enumerate(seeds):
            if self.verbose > 0 and len(seeds) > 1:
                print(f"  [ensemble {i + 1}/{len(seeds)}] seed={seed}")
            try:
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
