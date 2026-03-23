"""LightGbmStrategy: ML-based strategy with lazy monthly walk-forward retraining."""

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


def _discover_feature_columns(features_dir: str, interval: str) -> list[str]:
    """Discover feature columns present in ALL Parquet files (intersection).

    Uses the intersection so Optuna never selects a column missing from any symbol.
    """
    from pathlib import Path

    d = Path(features_dir)
    parquet_files = list(d.glob(f"*_{interval}_features.parquet"))
    if not parquet_files:
        raise FileNotFoundError(
            f"No Parquet feature files found in {features_dir} for interval {interval}"
        )

    # Read first file for column order, then intersect with all others
    first_schema = pq.read_schema(parquet_files[0])
    common: set[str] = {n for n in first_schema.names if n not in _META_COLUMNS}
    for pf in parquet_files[1:]:
        schema = pq.read_schema(pf)
        common &= set(schema.names)

    # Preserve column order from first file
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


class LightGbmStrategy:
    """LightGBM strategy with lazy monthly walk-forward retraining."""

    def __init__(
        self,
        training_months: int = 1,
        n_trials: int = 50,
        cv_splits: int = 5,
        label_tp_pct: float = 3.0,
        label_sl_pct: float = 2.0,
        label_timeout_minutes: int = 120,
        features_dir: str = "data/features",
        seed: int = 42,
        verbose: int = 0,
    ) -> None:
        self.training_months = training_months
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
        self._interval: str = "15m"
        self._all_feature_cols: list[str] = []
        self._splits: list[MonthSplit] = []
        self._split_map: dict[str, MonthSplit] = {}
        # Per-month lazy training state
        self._current_month: str | None = None
        self._model: object | None = None
        self._selected_cols: list[str] = []
        self._confidence_threshold: float = 0.50
        self._month_features: dict[tuple[str, int], np.ndarray] = {}

    def compute_features(self, master: pd.DataFrame) -> None:
        """Lightweight setup: store master and generate splits. No training."""
        self._master = master
        self._sym_arr = master["symbol"].to_numpy(dtype=str)
        self._open_time_arr = master["open_time"].values

        # Detect interval
        self._interval = self._detect_interval(master)

        # Discover feature columns
        try:
            self._all_feature_cols = _discover_feature_columns(self.features_dir, self._interval)
        except FileNotFoundError:
            self._all_feature_cols = []

        # Generate monthly splits
        self._splits = generate_monthly_splits(self._open_time_arr, self.training_months)
        self._split_map = {s.test_month: s for s in self._splits}

        if self.verbose > 0:
            print(
                f"[lgbm] {len(self._all_feature_cols)} feature columns, "
                f"{len(self._splits)} walk-forward splits"
            )

        self._current_month = None
        self._model = None

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

        # (b) Label all training samples
        train_labels, train_weights = label_trades(
            self._master,
            train_indices,
            self.label_tp_pct,
            self.label_sl_pct,
            self.label_timeout_minutes,
            verbose=self.verbose,
        )

        if self.verbose > 0:
            n_long = int((train_labels == 1).sum())
            n_short = int((train_labels == -1).sum())
            total = len(train_labels)
            ratio = n_short / n_long if n_long > 0 else 0.0
            print(
                f"  Labels: {n_long} long ({100 * n_long / total:.1f}%), "
                f"{n_short} short ({100 * n_short / total:.1f}%) | "
                f"weights: min={train_weights.min():.2f}, "
                f"mean={train_weights.mean():.2f}, max={train_weights.max():.2f}"
            )
            print(f"  Class balance: scale_pos_weight\u2248{ratio:.3f} (is_unbalance=True)")

        # (c) Load training features
        train_lookups = [
            (str(self._sym_arr[i]), int(self._open_time_arr[i])) for i in train_indices
        ]
        train_feat_df = lookup_features(train_lookups, self.features_dir, self._interval)
        if train_feat_df.empty:
            if self.verbose > 0:
                print(f"  Skipping {month_str}: no features found for training")
            return

        # Align features with labels and weights
        feat_keys = set(zip(train_feat_df["symbol"], train_feat_df["open_time"]))
        keep_mask = np.array(
            [
                (str(self._sym_arr[i]), int(self._open_time_arr[i])) in feat_keys
                for i in train_indices
            ]
        )
        train_labels = train_labels[keep_mask]
        train_weights = train_weights[keep_mask]
        train_open_times = self._open_time_arr[train_indices][keep_mask]

        available_feat_cols = [c for c in self._all_feature_cols if c in train_feat_df.columns]
        feat_train = train_feat_df[available_feat_cols].values

        if self.verbose > 0:
            print(
                f"  Features: {len(train_feat_df)}/{len(train_indices)} matched, "
                f"{len(available_feat_cols)} columns"
            )

        avail_col_map = build_feature_column_map(available_feat_cols)

        # (d) Optuna optimization (with training_days for time-based trimming)
        try:
            model, selected_cols, confidence_threshold = optimize_and_train(
                feat_train,
                train_labels,
                available_feat_cols,
                avail_col_map,
                self.n_trials,
                self.cv_splits,
                self.label_tp_pct,
                self.label_sl_pct,
                0.1,
                self.seed,
                self.verbose,
                sample_weights=train_weights,
                open_times=train_open_times,
                train_end_ms=split.train_end_ms,
            )
        except Exception as exc:
            if self.verbose > 0:
                print(f"  Optimization failed for {month_str}: {exc}")
            return

        self._model = model
        self._selected_cols = selected_cols
        self._confidence_threshold = confidence_threshold

        # (e) Batch-load test month features
        symbols = list(dict.fromkeys(self._sym_arr))  # unique, preserving order
        self._month_features = load_features_range(
            symbols,
            self.features_dir,
            self._interval,
            split.test_start_ms,
            split.test_end_ms,
            columns=selected_cols,
        )

        if self.verbose > 0:
            print(
                f"  Model trained for {month_str}: "
                f"{len(self._month_features)} test candles with features, "
                f"confidence_threshold={self._confidence_threshold:.3f}"
            )

    def skip(self) -> None:
        pass

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        """Return signal for one candle."""
        # Detect month change → lazy training
        candle_month = _epoch_ms_to_month(open_time)
        if candle_month != self._current_month:
            self._current_month = candle_month
            self._train_for_month(candle_month)

        self._last_predict_log: str | None = None

        if self._model is None:
            return NO_SIGNAL

        # Look up features from month cache
        key = (symbol, open_time)
        feat_row = self._month_features.get(key)
        if feat_row is None:
            return NO_SIGNAL

        # Predict with confidence threshold gate
        feat_df = pd.DataFrame(feat_row.reshape(1, -1), columns=self._selected_cols)
        proba = self._model.predict_proba(feat_df)[0]  # [P(short), P(long)]
        confidence = float(max(proba))

        if confidence < self._confidence_threshold:
            if self.verbose > 0:
                ts_str = _ms_to_datetime(open_time)
                self._last_predict_log = (
                    f"[predict] {ts_str} {symbol} → SKIP "
                    f"(confidence={confidence:.2f} < {self._confidence_threshold:.2f})"
                )
            return NO_SIGNAL

        pred_class = int(np.argmax(proba))
        direction = int(classes_to_labels(np.array([pred_class]))[0])

        if self.verbose > 0:
            dir_label = "LONG" if direction == 1 else "SHORT"
            ts_str = _ms_to_datetime(open_time)
            self._last_predict_log = (
                f"[predict] {ts_str} {symbol} → {dir_label} (proba={confidence:.2f})"
            )

        return Signal(direction=direction, weight=100)

    @staticmethod
    def _detect_interval(master: pd.DataFrame) -> str:
        """Detect interval from typical close_time - open_time gap."""
        if len(master) < 2:
            return "15m"
        diff = master["close_time"].iloc[0] - master["open_time"].iloc[0]
        interval_map = {
            59_999: "1m",
            179_999: "3m",
            299_999: "5m",
            899_999: "15m",
            1_799_999: "30m",
            3_599_999: "1h",
            14_399_999: "4h",
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
