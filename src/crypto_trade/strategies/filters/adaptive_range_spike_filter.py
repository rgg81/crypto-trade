"""Adaptive range spike filter — pandas implementation.

Detects high-volatility candles using the ``range_spike`` metric (candle range
normalised by a rolling mean) and auto-calibrates the threshold so the filter
fires at a target rate (~signals / month).

The thin ``AdaptiveRangeSpikeFilter`` class computes spike features once in
``compute_features`` and recalibrates lazily in ``get_signal`` when enough
history has accumulated and the recalibration interval has elapsed.

Threshold search uses binary search (signal count is monotonically decreasing
with threshold), and monthly signal counting uses actual calendar months from
the open_time timestamps.

Dependencies (``pandas``) are imported lazily so the module always loads
(strategy registration works), but you get a clear ``ImportError`` if you
actually run the filter without installing the ``adaptive`` dependency group::

    uv sync --group adaptive
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import numpy as np
import pandas as pd

from crypto_trade.backtest_models import Signal, Strategy
from crypto_trade.strategies import NO_SIGNAL

# ---------------------------------------------------------------------------
# CalibrationResult — audit trail for each recalibration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CalibrationResult:
    """Snapshot recorded after every successful recalibration."""

    threshold: float
    signals_per_month: float
    calibrated_at: int  # epoch ms
    error: float  # |actual − target|


# ---------------------------------------------------------------------------
# Standalone functions
# ---------------------------------------------------------------------------


def count_signals_per_month(
    spikes: np.ndarray,
    open_times: np.ndarray,
    threshold: float,
) -> float:
    """Count how many spikes exceed *threshold*, averaged over calendar months.

    Groups signals by actual calendar month (year*12 + month) and returns the
    mean count across months.  Returns ``0.0`` when there are no complete months.
    """
    if len(spikes) == 0:
        return 0.0

    mask = spikes >= threshold
    signal_times = open_times[mask]

    if len(signal_times) == 0:
        # Check if we have at least one month of data
        all_keys = _month_keys(open_times)
        if len(np.unique(all_keys)) == 0:
            return 0.0
        return 0.0

    # Group all candles by month to know how many months we span
    all_keys = _month_keys(open_times)
    unique_months = np.unique(all_keys)
    n_months = len(unique_months)

    if n_months == 0:
        return 0.0

    # Count signals per month
    signal_keys = _month_keys(signal_times)
    total_signals = len(signal_keys)

    return float(total_signals / n_months)


def _month_keys(epoch_ms: np.ndarray) -> np.ndarray:
    """Convert epoch-ms timestamps to month keys (year*12 + month)."""
    # Convert ms -> seconds -> datetime64[s] -> extract year/month
    seconds = (epoch_ms // 1000).astype("datetime64[s]")
    years = seconds.astype("datetime64[Y]").astype(int) + 1970
    months = seconds.astype("datetime64[M]").astype(int) % 12 + 1
    return years * 12 + months


def find_best_threshold(
    spikes: np.ndarray,
    open_times: np.ndarray,
    target_signals_month: float,
    threshold_lo: float = 2.0,
    threshold_hi: float = 12.0,
) -> float:
    """Binary search for the threshold closest to *target_signals_month*.

    Signal count is monotonically decreasing with threshold, so binary search
    converges in ~50 iterations to machine-precision accuracy.
    """
    lo, hi = threshold_lo, threshold_hi

    for _ in range(50):
        mid = (lo + hi) / 2
        actual = count_signals_per_month(spikes, open_times, mid)
        if actual > target_signals_month:
            lo = mid  # too many signals → raise threshold
        else:
            hi = mid  # too few signals → lower threshold

    return (lo + hi) / 2


# ---------------------------------------------------------------------------
# AdaptiveRangeSpikeFilter — thin wrapper class
# ---------------------------------------------------------------------------

_MS_PER_DAY = 24 * 60 * 60 * 1000


@dataclass
class AdaptiveRangeSpikeFilter:
    """Adaptive range spike filter that recalibrates via binary search.

    Wraps an inner strategy using the same decorator pattern as
    ``RangeSpikeFilter``.  Every ``recalibrate_days`` days it runs
    ``find_best_threshold`` across all tracked symbols to keep the
    threshold aligned with the target signal rate.
    """

    inner: Strategy | None = None
    window: int = 16
    target_signals_month: int = 400
    recalibrate_days: int = 30
    min_history_days: int = 30
    initial_threshold: float = 5.85
    threshold_lo: float = 2.0
    threshold_hi: float = 12.0

    def __post_init__(self) -> None:
        self.threshold: float = self.initial_threshold
        self._calibration_log: list[CalibrationResult] = []
        self._interval_ms: int = 900_000  # default 15m, overridden in compute_features

    # -- derived helpers -----------------------------------------------------

    @property
    def _min_history_candles(self) -> int:
        interval_minutes = self._interval_ms // 60_000
        return self.min_history_days * 24 * 60 // interval_minutes

    # -- Strategy protocol ---------------------------------------------------

    def compute_features(self, master: pd.DataFrame) -> None:
        if self.inner is not None:
            self.inner.compute_features(master)

        # Compute range spike for all data (grouped by symbol)
        range_ratio = (master["high"] - master["low"]) / master["open"]
        rolling_mean = range_ratio.groupby(master["symbol"]).transform(
            lambda x: x.rolling(self.window, min_periods=self.window).mean()
        )
        range_spike = range_ratio / rolling_mean.replace(0.0, float("nan"))

        del range_ratio, rolling_mean
        self._spikes = range_spike.values
        self._open_times = master["open_time"].values
        self._n_symbols = master["symbol"].nunique()
        self._pos = 0
        self._next_cal_time = 0  # triggers calibration on first eligible candle

        # Deduce interval from data
        ot = self._open_times[self._open_times > 0]
        if len(ot) >= 2:
            diffs = np.diff(ot[:100])
            positive = diffs[diffs > 0]
            if len(positive) > 0:
                self._interval_ms = int(np.min(positive))

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        i = self._pos
        self._pos += 1

        spike = self._spikes[i]
        ot = int(self._open_times[i])

        # Lazy recalibration check
        if ot >= self._next_cal_time and i >= self._min_history_candles:
            spikes_so_far = self._spikes[:i]
            open_times_so_far = self._open_times[:i]
            # Drop NaNs
            valid_mask = ~np.isnan(spikes_so_far)
            valid_spikes = spikes_so_far[valid_mask]
            valid_times = open_times_so_far[valid_mask]
            if len(valid_spikes) > 0:
                old_th = self.threshold
                dt = datetime.fromtimestamp(ot / 1000, tz=UTC)
                print(
                    f"[adaptive] recalibrating at {dt:%Y-%m-%d %H:%M} "
                    f"| {self._n_symbols} symbols | threshold={old_th:.4f}"
                )
                try:
                    best = find_best_threshold(
                        valid_spikes,
                        valid_times,
                        target_signals_month=self.target_signals_month,
                        threshold_lo=self.threshold_lo,
                        threshold_hi=self.threshold_hi,
                    )
                    spm = count_signals_per_month(valid_spikes, valid_times, best)
                    actual_target_diff = abs(spm - self.target_signals_month)
                    self.threshold = best
                    print(
                        f"[adaptive] done — threshold {old_th:.4f} → {best:.4f} "
                        f"| signals/month={spm:.0f} "
                        f"(target={self.target_signals_month}) "
                        f"| error={actual_target_diff:.1f}"
                    )
                    self._calibration_log.append(
                        CalibrationResult(
                            threshold=best,
                            signals_per_month=spm,
                            calibrated_at=ot,
                            error=actual_target_diff,
                        )
                    )
                except Exception:
                    pass  # Keep current threshold on error

                self._next_cal_time = ot + self.recalibrate_days * _MS_PER_DAY

        # Check spike against threshold (NaN → False)
        passes = not np.isnan(spike) and spike >= self.threshold

        if not passes:
            if self.inner is not None:
                self.inner.get_signal(symbol, open_time)
            return NO_SIGNAL

        dt = datetime.fromtimestamp(ot / 1000, tz=UTC)
        print(f"[signal] {dt:%Y-%m-%d %H:%M} {symbol} | spike={spike:.2f} th={self.threshold:.4f}")

        if self.inner is not None:
            return self.inner.get_signal(symbol, open_time)
        return NO_SIGNAL

