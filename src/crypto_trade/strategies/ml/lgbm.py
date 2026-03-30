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
    return datetime.datetime.fromtimestamp(
        open_time / 1000, tz=datetime.UTC
    ).strftime("%Y-%m")


def _ms_to_date(ms: int) -> str:
    """Convert epoch milliseconds to 'YYYY-MM-DD' string."""
    return datetime.datetime.fromtimestamp(
        ms / 1000, tz=datetime.UTC
    ).strftime("%Y-%m-%d")


def _ms_to_datetime(ms: int) -> str:
    """Convert epoch milliseconds to 'YYYY-MM-DD HH:MM' string."""
    return datetime.datetime.fromtimestamp(
        ms / 1000, tz=datetime.UTC
    ).strftime("%Y-%m-%d %H:%M")


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
        seed: int = 42,
        verbose: int = 0,
        atr_tp_multiplier: float | None = None,
        atr_sl_multiplier: float | None = None,
        atr_column: str = "vol_natr_21",
        ensemble_seeds: list[int] | None = None,
        neutral_threshold_pct: float | None = None,
    ) -> None:
        self.training_months = training_months
        self.n_trials = n_trials
        self.cv_splits = cv_splits
        self.label_tp_pct = label_tp_pct
        self.label_sl_pct = label_sl_pct
        self.label_timeout_minutes = label_timeout_minutes
        self.fee_pct = fee_pct
        self.features_dir = features_dir
        self.seed = seed
        self.verbose = verbose
        self.atr_tp_multiplier = atr_tp_multiplier
        self.atr_sl_multiplier = atr_sl_multiplier
        self.atr_column = atr_column
        self.ensemble_seeds = ensemble_seeds
        self.neutral_threshold_pct = neutral_threshold_pct

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

    def compute_features(self, master: pd.DataFrame) -> None:
        """Lightweight setup: store master and generate splits. No training."""
        self._master = master
        self._sym_arr = master["symbol"].to_numpy(dtype=str)
        self._open_time_arr = master["open_time"].values

        # Detect interval
        self._interval = self._detect_interval(master)

        # Discover feature columns (use ALL of them)
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
                print(
                    f"[lgbm] No split for {month_str} "
                    "(insufficient training data)"
                )
            return

        if not self._all_feature_cols:
            if self.verbose > 0:
                print(
                    f"[lgbm] No feature columns available, "
                    f"skipping {month_str}"
                )
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
                print(
                    f"  Skipping {month_str}: only "
                    f"{len(train_indices)} train samples"
                )
            return

        if self.verbose > 0:
            from collections import Counter

            n_unique_syms = len(set(self._sym_arr[train_indices]))
            print(
                f"  {len(train_indices)} training samples "
                f"from {n_unique_syms} symbols"
            )
            sample_months = Counter(
                _epoch_ms_to_month(int(t))
                for t in self._open_time_arr[train_indices]
            )
            dist_parts = [f"{m}: {c}" for m, c in sorted(sample_months.items())]
            print(f"  Samples per month: {', '.join(dist_parts)}")

        # (b) Label all training samples (with fee-aware returns)
        train_labels, train_weights, long_pnls, short_pnls = label_trades(
            self._master,
            train_indices,
            self.label_tp_pct,
            self.label_sl_pct,
            self.label_timeout_minutes,
            fee_pct=self.fee_pct,
            verbose=self.verbose,
            neutral_threshold_pct=self.neutral_threshold_pct,
        )

        ternary = self.neutral_threshold_pct is not None

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
            (str(self._sym_arr[i]), int(self._open_time_arr[i]))
            for i in train_indices
        ]
        train_feat_df = lookup_features(
            train_lookups, self.features_dir, self._interval
        )
        if train_feat_df.empty:
            if self.verbose > 0:
                print(
                    f"  Skipping {month_str}: no features found for training"
                )
            return

        # Align features with labels, weights, and returns
        feat_keys = set(
            zip(train_feat_df["symbol"], train_feat_df["open_time"])
        )
        keep_mask = np.array(
            [
                (str(self._sym_arr[i]), int(self._open_time_arr[i]))
                in feat_keys
                for i in train_indices
            ]
        )
        train_labels = train_labels[keep_mask]
        train_weights = train_weights[keep_mask]
        long_pnls = long_pnls[keep_mask]
        short_pnls = short_pnls[keep_mask]
        train_open_times = self._open_time_arr[train_indices][keep_mask]

        available_feat_cols = [
            c for c in self._all_feature_cols if c in train_feat_df.columns
        ]
        feat_train = train_feat_df[available_feat_cols].values

        if self.verbose > 0:
            print(
                f"  Features: {len(train_feat_df)}/{len(train_indices)} "
                f"matched, {len(available_feat_cols)} columns"
            )

        # (d) Optuna optimization (all features, with threshold)
        seeds = self.ensemble_seeds or [self.seed]
        self._models = []
        self._confidence_thresholds = []

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
        self._confidence_threshold = float(np.mean(self._confidence_thresholds))

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
            return NO_SIGNAL

        # Predict with all ensemble models and average probabilities
        feat_df = pd.DataFrame(
            feat_row.reshape(1, -1), columns=self._selected_cols
        )
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

        if confidence < self._confidence_threshold:
            if self.verbose > 0:
                ts_str = _ms_to_datetime(open_time)
                self._last_predict_log = (
                    f"[predict] {ts_str} {symbol} → SKIP "
                    f"(conf={confidence:.2f} < "
                    f"{self._confidence_threshold:.2f})"
                )
            return NO_SIGNAL

        if ternary:
            # Direction from long vs short probability only
            direction = 1 if proba[2] >= proba[0] else -1
        else:
            pred_class = int(np.argmax(proba))
            direction = int(classes_to_labels(np.array([pred_class]))[0])

        # Compute dynamic TP/SL from ATR if configured
        tp_pct = None
        sl_pct = None
        if self.atr_tp_multiplier is not None:
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
            if tp_pct is not None:
                atr_str = f" TP={tp_pct:.1f}%/SL={sl_pct:.1f}%"
            self._last_predict_log = (
                f"[predict] {ts_str} {symbol} → {dir_label} "
                f"(proba={confidence:.2f}{atr_str})"
            )

        return Signal(direction=direction, weight=100, tp_pct=tp_pct, sl_pct=sl_pct)

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
            86_399_999: "1d",
        }
        best = "8h"
        best_dist = abs(diff - 28_799_999)
        for ms, name in interval_map.items():
            dist = abs(diff - ms)
            if dist < best_dist:
                best_dist = dist
                best = name
        return best
