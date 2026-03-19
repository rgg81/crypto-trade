"""RangeSpikeLightGbmStrategy: ML-based strategy with lazy monthly walk-forward retraining."""

from __future__ import annotations

import datetime

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from crypto_trade.backtest_models import Signal
from crypto_trade.feature_store import load_features_range, lookup_features
from crypto_trade.strategies import NO_SIGNAL
from crypto_trade.strategies.ml.labeling import label_trades
from crypto_trade.strategies.ml.optimization import (
    build_feature_column_map,
    classes_to_labels,
    optimize_and_train,
)
from crypto_trade.strategies.ml.walk_forward import (
    MonthSplit,
    generate_monthly_splits,
    select_training_samples,
)

# Columns that are metadata, not features
_META_COLUMNS = frozenset({"open_time", "open", "high", "low", "close", "close_time", "volume",
                           "quote_volume", "trades", "taker_buy_volume", "taker_buy_quote_volume",
                           "symbol"})


def _discover_feature_columns(features_dir: str, interval: str) -> list[str]:
    """Read one Parquet file's schema to discover all feature column names."""
    from pathlib import Path

    d = Path(features_dir)
    parquet_files = list(d.glob(f"*_{interval}_features.parquet"))
    if not parquet_files:
        raise FileNotFoundError(
            f"No Parquet feature files found in {features_dir} for interval {interval}"
        )
    schema = pq.read_schema(parquet_files[0])
    return [name for name in schema.names if name not in _META_COLUMNS]


def _epoch_ms_to_month(open_time: int) -> str:
    """Convert epoch milliseconds to 'YYYY-MM' string."""
    return datetime.datetime.fromtimestamp(
        open_time / 1000, tz=datetime.UTC
    ).strftime("%Y-%m")


def _ms_to_date(ms: int) -> str:
    """Convert epoch milliseconds to 'YYYY-MM-DD' string."""
    return datetime.datetime.fromtimestamp(ms / 1000, tz=datetime.UTC).strftime("%Y-%m-%d")


class RangeSpikeLightGbmStrategy:
    """LightGBM strategy with lazy monthly walk-forward retraining."""

    def __init__(
        self,
        training_months: int = 12,
        n_samples: int = 10_000,
        spike_window: int = 16,
        n_trials: int = 50,
        cv_splits: int = 3,
        label_tp_pct: float = 3.0,
        label_sl_pct: float = 2.0,
        label_timeout_minutes: int = 120,
        features_dir: str = "data/features",
        seed: int = 42,
        verbose: int = 0,
    ) -> None:
        self.training_months = training_months
        self.n_samples = n_samples
        self.spike_window = spike_window
        self.n_trials = n_trials
        self.cv_splits = cv_splits
        self.label_tp_pct = label_tp_pct
        self.label_sl_pct = label_sl_pct
        self.label_timeout_minutes = label_timeout_minutes
        self.features_dir = features_dir
        self.seed = seed
        self.verbose = verbose

        # Set during compute_features
        self._master: pd.DataFrame | None = None
        self._sym_arr: np.ndarray = np.array([])
        self._open_time_arr: np.ndarray = np.array([])
        self._range_spike: np.ndarray = np.array([])
        self._interval: str = "15m"
        self._all_feature_cols: list[str] = []
        self._splits: list[MonthSplit] = []
        self._split_map: dict[str, MonthSplit] = {}
        self._pos: int = 0

        # Per-month lazy training state
        self._current_month: str | None = None
        self._model: object | None = None
        self._selected_cols: list[str] = []
        self._month_features: dict[tuple[str, int], np.ndarray] = {}

    def compute_features(self, master: pd.DataFrame) -> None:
        """Lightweight setup: compute range_spike and generate splits. No training."""
        self._master = master
        self._sym_arr = master["symbol"].to_numpy(dtype=str)
        self._open_time_arr = master["open_time"].values

        # Compute range_spike (still needed for training sample selection)
        range_ratio = (master["high"] - master["low"]) / master["open"]
        rolling_mean = range_ratio.groupby(master["symbol"]).transform(
            lambda x: x.rolling(self.spike_window, min_periods=self.spike_window).mean()
        )
        range_spike_series = range_ratio / rolling_mean.replace(0.0, float("nan"))
        self._range_spike = range_spike_series.values

        # Detect interval
        self._interval = self._detect_interval(master)

        # Discover feature columns
        try:
            self._all_feature_cols = _discover_feature_columns(
                self.features_dir, self._interval
            )
        except FileNotFoundError:
            self._all_feature_cols = []

        # Generate monthly splits
        self._splits = generate_monthly_splits(
            self._open_time_arr, self.training_months
        )
        self._split_map = {s.test_month: s for s in self._splits}

        if self.verbose > 0:
            print(f"[range_spike_lgbm] {len(self._all_feature_cols)} feature columns, "
                  f"{len(self._splits)} walk-forward splits")

        self._pos = 0
        self._current_month = None
        self._model = None

    def _train_for_month(self, month_str: str) -> None:
        """Train a model for the given month. Called lazily from get_signal."""
        self._model = None
        self._selected_cols = []
        self._month_features = {}

        split = self._split_map.get(month_str)
        if split is None:
            if self.verbose > 0:
                print(f"[range_spike_lgbm] No split for {month_str} (insufficient training data)")
            return

        if not self._all_feature_cols:
            if self.verbose > 0:
                print(f"[range_spike_lgbm] No feature columns available, skipping {month_str}")
            return

        if self.verbose > 0:
            print(f"[range_spike_lgbm] === Training for {month_str} ===")
            print(f"  Train window: {_ms_to_date(split.train_start_ms)} "
                  f"\u2192 {_ms_to_date(split.train_end_ms)}")

        # (a) Select training samples
        train_indices = select_training_samples(
            self._open_time_arr, self._range_spike,
            split.train_start_ms, split.train_end_ms,
            self.n_samples,
        )
        if len(train_indices) < 10:
            if self.verbose > 0:
                print(f"  Skipping {month_str}: only {len(train_indices)} train samples")
            return

        if self.verbose > 0:
            from collections import Counter

            n_unique_syms = len(set(self._sym_arr[train_indices]))
            window_mask = (
                (self._open_time_arr >= split.train_start_ms)
                & (self._open_time_arr < split.train_end_ms)
            )
            n_candidates = int(window_mask.sum())
            print(f"  Selected {len(train_indices)} training samples "
                  f"(from {n_candidates} candidates)")
            print(f"  Symbols: {n_unique_syms} unique")
            sample_months = Counter(
                _epoch_ms_to_month(int(t)) for t in self._open_time_arr[train_indices]
            )
            dist_parts = [f"{m}: {c}" for m, c in sorted(sample_months.items())]
            print(f"  Samples per month: {', '.join(dist_parts)}")

        # (b) Label training samples
        train_labels = label_trades(
            self._master, train_indices,
            self.label_tp_pct, self.label_sl_pct, self.label_timeout_minutes,
        )

        if self.verbose > 0:
            n_long = int((train_labels == 1).sum())
            n_short = int((train_labels == -1).sum())
            n_skip = int((train_labels == 0).sum())
            total = len(train_labels)
            print(f"  Labels: {n_long} long ({100 * n_long / total:.1f}%), "
                  f"{n_short} short ({100 * n_short / total:.1f}%), "
                  f"{n_skip} skip ({100 * n_skip / total:.1f}%)")

        # (c) Load training features (exact-match lookup for sparse training samples)
        train_lookups = [
            (str(self._sym_arr[i]), int(self._open_time_arr[i]))
            for i in train_indices
        ]
        train_feat_df = lookup_features(
            train_lookups, self.features_dir, self._interval
        )
        if train_feat_df.empty:
            if self.verbose > 0:
                print(f"  Skipping {month_str}: no features found for training")
            return

        # Align features with labels
        feat_keys = set(zip(train_feat_df["symbol"], train_feat_df["open_time"]))
        keep_mask = np.array([
            (str(self._sym_arr[i]), int(self._open_time_arr[i])) in feat_keys
            for i in train_indices
        ])
        train_labels = train_labels[keep_mask]

        available_feat_cols = [c for c in self._all_feature_cols if c in train_feat_df.columns]
        feat_train = train_feat_df[available_feat_cols].values

        if self.verbose > 0:
            print(f"  Features: {len(train_feat_df)}/{len(train_indices)} matched, "
                  f"{len(available_feat_cols)} columns")

        # (d) Drop NaN rows
        nan_mask = ~np.isnan(feat_train).any(axis=1)
        feat_train = feat_train[nan_mask]
        train_labels = train_labels[nan_mask]

        if self.verbose > 0:
            print(f"  After NaN cleanup: {len(train_labels)} samples")

        if len(train_labels) < 10:
            if self.verbose > 0:
                print(f"  Skipping {month_str}: only {len(train_labels)} "
                      f"valid samples after NaN removal")
            return

        avail_col_map = build_feature_column_map(available_feat_cols)

        # (e) Optuna optimization
        try:
            model, selected_cols = optimize_and_train(
                feat_train, train_labels,
                available_feat_cols, avail_col_map,
                self.n_trials, self.cv_splits,
                self.label_tp_pct, self.label_sl_pct, 0.1,
                self.seed, self.verbose,
            )
        except Exception as exc:
            if self.verbose > 0:
                print(f"  Optimization failed for {month_str}: {exc}")
            return

        self._model = model
        self._selected_cols = selected_cols

        # (f) Batch-load test month features
        symbols = list(dict.fromkeys(self._sym_arr))  # unique, preserving order
        self._month_features = load_features_range(
            symbols, self.features_dir, self._interval,
            split.test_start_ms, split.test_end_ms,
            columns=selected_cols,
        )

        if self.verbose > 0:
            print(f"  Model trained for {month_str}: "
                  f"{len(self._month_features)} test candles with features")

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        """Return signal for one candle."""
        self._pos += 1

        # Detect month change → lazy training
        candle_month = _epoch_ms_to_month(open_time)
        if candle_month != self._current_month:
            self._current_month = candle_month
            self._train_for_month(candle_month)

        if self._model is None:
            return NO_SIGNAL

        # Look up features from month cache
        key = (symbol, open_time)
        feat_row = self._month_features.get(key)
        if feat_row is None:
            return NO_SIGNAL

        # Predict
        feat_2d = feat_row.reshape(1, -1)
        feat_2d = np.nan_to_num(feat_2d, nan=0.0)
        pred_class = self._model.predict(feat_2d)
        direction = int(classes_to_labels(np.asarray(pred_class))[0])

        if direction == 0:
            return NO_SIGNAL
        return Signal(direction=direction, weight=100)

    @staticmethod
    def _detect_interval(master: pd.DataFrame) -> str:
        """Detect interval from typical close_time - open_time gap."""
        if len(master) < 2:
            return "15m"
        diff = master["close_time"].iloc[0] - master["open_time"].iloc[0]
        interval_map = {
            59_999: "1m", 179_999: "3m", 299_999: "5m", 899_999: "15m",
            1_799_999: "30m", 3_599_999: "1h", 14_399_999: "4h",
            86_399_999: "1d",
        }
        best = "15m"
        best_dist = abs(diff - 899_999)
        for ms, name in interval_map.items():
            dist = abs(diff - ms)
            if dist < best_dist:
                best_dist = dist
                best = name
        return best
