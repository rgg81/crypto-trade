"""Measure, on development data only, the quantities the derived config numbers rest on.

Every number in the config carries exactly one of ``structural``, ``inherited``, ``calibrated`` or
``derived``, with the hash of the artifact that justifies it. This script produces that artifact for
the ``derived`` half: quantities that follow from a measurement anybody can repeat, rather than from
a judgement I would be making with six prior editions' results in my head.

Development data only, and the sealed blocks are excluded from every measurement here. Measuring a
purge width on the days the purge is meant to protect would be circular.

What is measured and what it justifies:

* **Return autocorrelation** at lags 1..30, on the equal-weight member index. Justifies the purge
  width -- how far a sealed block's information reaches into its neighbours -- and is also where the
  charter's disclosed limit comes from: absolute-return autocorrelation persists far enough that a
  team can always infer a sealed block's *volatility regime* from its neighbours, though never its
  sign. Stated rather than implied away.
* **Membership shape** over the scored window. Justifies the universe rule's parameters: a rule that
  leaves too thin a cross-section produces a book that cannot be a portfolio, whatever the strategy.
* **Bootstrap resolution.** Justifies the sample count. V4-R9 ran 2000 samples, which quantises a
  probability to 5e-4, and then required a threshold that needed at most one negative resample in
  2000 -- a threshold beyond the estimator's representable range.
* **Window arithmetic** for the sealed schedule.

Usage::

    uv run python scripts/top40_v5_measure.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SNAPSHOT = Path("data/top40/snapshot-v3")
SCORED_START = pd.Timestamp("2020-08-02", tz="UTC")
SCORED_END = pd.Timestamp("2024-02-01", tz="UTC")


def _member_index(bars: pd.DataFrame, membership: pd.DataFrame) -> pd.Series:
    """Equal-weight daily return of the point-in-time membership.

    The natural reference series: it is what the cross-section actually did, and it exists without
    naming any particular symbol.
    """

    frame = bars.copy()
    frame["open_time"] = pd.to_datetime(frame["open_time"], utc=True)
    window = frame[(frame["open_time"] >= SCORED_START) & (frame["open_time"] < SCORED_END)]
    members = set(membership["symbol"].astype(str).unique())
    window = window[window["symbol"].astype(str).isin(members)]
    wide = window.pivot_table(
        index="open_time", columns="symbol", values="close", aggfunc="last"
    ).sort_index()
    returns = wide.pct_change().replace([np.inf, -np.inf], np.nan)
    daily = (1.0 + returns.mean(axis=1)).resample("1D").prod() - 1.0
    return daily.dropna()


def _autocorrelation(series: pd.Series, lags: int = 30) -> dict[str, list[float]]:
    values = series.to_numpy(dtype=float)
    signed = [float(pd.Series(values).autocorr(lag)) for lag in range(1, lags + 1)]
    absolute = [float(pd.Series(np.abs(values)).autocorr(lag)) for lag in range(1, lags + 1)]
    return {"signed": signed, "absolute": absolute}


def _first_lag_below(values: list[float], threshold: float) -> int:
    """The first lag at which the magnitude stays below the threshold for the rest of the series.

    'Stays below' rather than 'first drops below': a single dip is noise, and a purge width chosen
    on one is a purge width that does not hold.
    """

    for index in range(len(values)):
        if all(abs(item) < threshold for item in values[index:]):
            return index + 1
    return len(values) + 1


def _membership_shape(membership: pd.DataFrame) -> dict[str, float]:
    frame = membership.copy()
    column = "reconstitution_time"
    frame[column] = pd.to_datetime(frame[column], utc=True)
    window = frame[(frame[column] >= SCORED_START) & (frame[column] < SCORED_END)]
    per_week = window.groupby(column)["symbol"].nunique()
    return {
        "reconstitutions": int(len(per_week)),
        "minimum_members": int(per_week.min()),
        "p10_members": float(per_week.quantile(0.10)),
        "median_members": float(per_week.median()),
        "full_slot_weeks": int((per_week >= 40).sum()),
        "distinct_symbols": int(window["symbol"].nunique()),
    }


def _bootstrap_resolution(samples: list[int]) -> dict[str, float]:
    """The finest probability each sample count can represent.

    A threshold below its own estimator's resolution is unpassable by construction, which is
    precisely how V4-R9's gate admitted zero of ninety-four trials.
    """

    return {str(count): 1.0 / count for count in samples}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="tournament/top40-v5/measurements.json")
    arguments = parser.parse_args()

    if not (SNAPSHOT / "bars.parquet").is_file():
        print(f"no snapshot at {SNAPSHOT}")
        return 1

    print("loading snapshot...", flush=True)
    bars = pd.read_parquet(SNAPSHOT / "bars.parquet")
    membership = pd.read_parquet(SNAPSHOT / "membership.parquet")

    print("measuring the member index...", flush=True)
    index_returns = _member_index(bars, membership)
    autocorrelation = _autocorrelation(index_returns)
    purge_lag = _first_lag_below(autocorrelation["signed"], 0.10)
    absolute_lag = _first_lag_below(autocorrelation["absolute"], 0.10)

    shape = _membership_shape(membership)
    resolution = _bootstrap_resolution([2000, 5000, 10000, 20000, 50000])

    window_days = int((SCORED_END - SCORED_START).days)
    payload = {
        "schema_version": "top40-v5-measurements-v1",
        "window": {
            "start": SCORED_START.isoformat(),
            "end_exclusive": SCORED_END.isoformat(),
            "days": window_days,
            "blocks_of_45": window_days // 45,
        },
        "index_returns": {
            "days": int(len(index_returns)),
            "annualised_volatility": float(index_returns.std(ddof=1) * np.sqrt(365.0)),
        },
        "autocorrelation": autocorrelation,
        "signed_autocorrelation_settles_at_lag": purge_lag,
        "absolute_autocorrelation_settles_at_lag": absolute_lag,
        "membership_shape": shape,
        "bootstrap_resolution": resolution,
    }

    print(f"\nscored window            {window_days} days ({window_days // 45} blocks of 45)")
    print(f"index daily returns      {len(index_returns)} days")
    print(f"signed autocorr settles  lag {purge_lag}  -> purge width")
    print(f"absolute autocorr        lag {absolute_lag}  -> the disclosed volatility-regime limit")
    print(f"membership               min {shape['minimum_members']}, median "
          f"{shape['median_members']:.0f}, {shape['reconstitutions']} reconstitutions")
    print(f"bootstrap resolution     2000 -> {resolution['2000']:.1e}, "
          f"20000 -> {resolution['20000']:.1e}")

    destination = Path(arguments.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\nwrote {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
