"""Calendar features: hour of day and day of week from open_time."""

from __future__ import annotations

import pandas as pd


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add calendar feature columns (hour_of_day, day_of_week)."""
    cols: dict[str, pd.Series] = {}

    # Convert open_time (epoch ms) to datetime
    dt = pd.to_datetime(df["open_time"], unit="ms", utc=True)

    # Hour of day: 0, 8, 16 for 8h candles (normalized to 0-1)
    cols["cal_hour_norm"] = dt.dt.hour / 24.0

    # Day of week: 0=Monday to 6=Sunday (normalized to 0-1)
    cols["cal_dow_norm"] = dt.dt.dayofweek / 6.0

    return pd.concat([df, pd.DataFrame(cols, index=df.index)], axis=1)
