"""Market regimes, labelled once from the universe itself.

The tournament exists to find a book that survives bull, bear and chop, and calendar folds do not
measure that: CUP-50's five half-year folds each mixed regimes, so a lane could carry a fold on one
kind of month and be carried by another.  Here every calendar month is labelled from the return of
an equal-weight index of that week's members, and the score prices the worst regime directly.

The rule is public and the labels are derived, not judged: a month is BULL above the declared
threshold, BEAR below its negative, and CHOP between.  Applying it to the sealed window produces
sealed labels, which is why the labels travel inside the snapshot manifest rather than being
recomputed by anything a team can reach.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping

import numpy as np
import pandas as pd

BULL = "bull"
BEAR = "bear"
CHOP = "chop"
REGIMES = (BULL, BEAR, CHOP)


@dataclasses.dataclass(frozen=True, slots=True)
class RegimePolicy:
    bull_threshold: float
    bear_threshold: float
    minimum_days: int
    weights: tuple[float, ...]


def equal_weight_member_index(bars: pd.DataFrame, membership: pd.DataFrame) -> pd.Series:
    """The 8h return of an equal-weight book over the members in force at each boundary."""
    frame = bars.loc[:, ["open_time", "symbol", "close"]].copy()
    frame["open_time"] = pd.DatetimeIndex(pd.to_datetime(frame["open_time"], utc=True))
    panel = frame.pivot_table(
        index="open_time", columns="symbol", values="close", aggfunc="last"
    ).sort_index()
    returns = panel.pct_change()

    roster = membership.loc[:, ["reconstitution_time", "symbol"]].copy()
    roster["reconstitution_time"] = pd.DatetimeIndex(
        pd.to_datetime(roster["reconstitution_time"], utc=True)
    )
    mask = (
        roster.assign(member=True)
        .pivot_table(
            index="reconstitution_time", columns="symbol", values="member", aggfunc="first"
        )
        .reindex(columns=panel.columns)
        .notna()
    )
    aligned = mask.reindex(panel.index, method="ffill").reindex(columns=panel.columns).fillna(False)
    selected = returns.where(aligned.astype(bool))
    index = selected.mean(axis=1, skipna=True)
    return index.replace([np.inf, -np.inf], np.nan).dropna()


def monthly_regime_labels(
    bars: pd.DataFrame, membership: pd.DataFrame, *, policy: RegimePolicy
) -> dict[str, str]:
    """Label every complete calendar month covered by the panel.

    The first month is dropped when the panel starts inside it: a part-month return is not
    comparable with a whole one, and the split deliberately begins mid-March.
    """
    index = equal_weight_member_index(bars, membership)
    if index.empty:
        return {}
    equity = (1.0 + index).cumprod()
    first = pd.Timestamp(index.index[0])
    monthly = equity.resample("MS").last()
    returns = monthly.pct_change().dropna()
    labels: dict[str, str] = {}
    for period, value in returns.items():
        month = pd.Timestamp(period)
        if month <= first.normalize().replace(day=1):
            continue
        if value >= policy.bull_threshold:
            labels[month.strftime("%Y-%m")] = BULL
        elif value <= policy.bear_threshold:
            labels[month.strftime("%Y-%m")] = BEAR
        else:
            labels[month.strftime("%Y-%m")] = CHOP
    return labels


def regime_of_day(labels: Mapping[str, str], day: pd.Timestamp) -> str | None:
    return labels.get(pd.Timestamp(day).strftime("%Y-%m"))
