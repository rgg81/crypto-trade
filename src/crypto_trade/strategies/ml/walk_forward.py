"""Monthly walk-forward splits and training sample selection."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MonthSplit:
    train_start_ms: int
    train_end_ms: int  # exclusive
    test_start_ms: int
    test_end_ms: int  # exclusive
    test_month: str  # "YYYY-MM" for logging


def _month_boundaries(year: int, month: int) -> tuple[int, int]:
    """Return (start_ms, end_ms) for a given year/month.

    end_ms is exclusive (start of next month).
    """
    import datetime

    start = datetime.datetime(year, month, 1, tzinfo=datetime.UTC)
    start_ms = int(start.timestamp() * 1000)

    if month == 12:
        end = datetime.datetime(year + 1, 1, 1, tzinfo=datetime.UTC)
    else:
        end = datetime.datetime(year, month + 1, 1, tzinfo=datetime.UTC)
    end_ms = int(end.timestamp() * 1000)

    return start_ms, end_ms


def generate_monthly_splits(
    open_times: np.ndarray,
    training_months: int,
) -> list[MonthSplit]:
    """Generate walk-forward monthly train/test splits.

    For each month M starting from index ``training_months``:
    - train window = months [M - training_months, M)
    - test window  = month [M, M+1)
    """
    import datetime

    # Extract unique (year, month) pairs in order
    ts_seconds = open_times / 1000.0
    dates = [datetime.datetime.fromtimestamp(t, tz=datetime.UTC) for t in ts_seconds]
    seen: set[tuple[int, int]] = set()
    months_ordered: list[tuple[int, int]] = []
    for d in dates:
        ym = (d.year, d.month)
        if ym not in seen:
            seen.add(ym)
            months_ordered.append(ym)

    splits: list[MonthSplit] = []

    for i in range(training_months, len(months_ordered)):
        test_year, test_month = months_ordered[i]
        train_start_year, train_start_month = months_ordered[i - training_months]

        train_start_ms, _ = _month_boundaries(train_start_year, train_start_month)
        test_start_ms, test_end_ms = _month_boundaries(test_year, test_month)
        train_end_ms = test_start_ms  # train ends where test begins

        splits.append(
            MonthSplit(
                train_start_ms=train_start_ms,
                train_end_ms=train_end_ms,
                test_start_ms=test_start_ms,
                test_end_ms=test_end_ms,
                test_month=f"{test_year:04d}-{test_month:02d}",
            )
        )

    return splits


def select_training_samples(
    open_times: np.ndarray,
    range_spike: np.ndarray,
    train_start_ms: int,
    train_end_ms: int,
    n_samples: int,
) -> np.ndarray:
    """Select top range_spike candles from the training window, distributed across months.

    Returns integer indices into the original arrays.
    """
    import datetime

    # Filter to training window
    mask = (open_times >= train_start_ms) & (open_times < train_end_ms)
    window_indices = np.where(mask)[0]

    if len(window_indices) == 0:
        return np.array([], dtype=np.intp)

    if len(window_indices) <= n_samples:
        return window_indices

    # Group by calendar month
    ts_seconds = open_times[window_indices] / 1000.0
    month_keys = np.array(
        [datetime.datetime.fromtimestamp(t, tz=datetime.UTC).strftime("%Y-%m") for t in ts_seconds]
    )
    unique_months = list(dict.fromkeys(month_keys))  # preserves order
    n_months = len(unique_months)
    per_month = n_samples // n_months

    selected: list[np.ndarray] = []
    for m in unique_months:
        month_mask = month_keys == m
        month_indices = window_indices[month_mask]
        month_spikes = range_spike[month_indices]

        # Top per_month by range_spike
        if len(month_indices) <= per_month:
            selected.append(month_indices)
        else:
            top_k = np.argpartition(month_spikes, -per_month)[-per_month:]
            selected.append(month_indices[top_k])

    result = np.concatenate(selected)

    # If total exceeds n_samples, trim by global range_spike ranking
    if len(result) > n_samples:
        global_spikes = range_spike[result]
        top_k = np.argpartition(global_spikes, -n_samples)[-n_samples:]
        result = result[top_k]

    return np.sort(result)
