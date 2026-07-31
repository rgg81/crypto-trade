"""Causal contract-maturation baseline for Team 10."""

from __future__ import annotations

import math
from typing import Mapping

import pandas as pd


class ContractMaturationSeasoningStrategy:
    """Long the oldest contract-age cohort and short the youngest."""

    _BAR_DURATION = pd.Timedelta(hours=8)
    _MINIMUM_HISTORY = pd.Timedelta(days=180)
    _COHORT_SIZE = 4
    _WEIGHT_PER_SYMBOL = 0.08

    def __init__(self) -> None:
        self._last_rebalance_week: tuple[int, int] | None = None

    def target_weights(
        self, context, *, seed: int
    ) -> Mapping[str, float] | None:
        """Return one causal Monday target per UTC week."""
        del seed

        decision_time = pd.Timestamp(context.decision_time)
        if decision_time.tzinfo is None:
            decision_time = decision_time.tz_localize("UTC")
        else:
            decision_time = decision_time.tz_convert("UTC")

        if decision_time.weekday() != 0:
            return None

        iso_calendar = decision_time.isocalendar()
        week_key = (int(iso_calendar.year), int(iso_calendar.week))
        if week_key == self._last_rebalance_week:
            return None
        self._last_rebalance_week = week_key

        contract_ages: list[tuple[float, str]] = []
        for symbol in sorted(set(context.eligible_symbols)):
            frame = context.bars.get(symbol)
            if frame is None or len(frame) == 0 or "open_time" not in frame:
                continue

            open_times = pd.to_datetime(
                frame["open_time"], utc=True, errors="coerce"
            )
            completed_open_times = open_times[
                open_times + self._BAR_DURATION <= decision_time
            ].dropna()
            if completed_open_times.empty:
                continue

            first_past_open = completed_open_times.min()
            observed_age = decision_time - first_past_open
            if observed_age < self._MINIMUM_HISTORY:
                continue

            age_days = observed_age.total_seconds() / 86_400.0
            if math.isfinite(age_days):
                contract_ages.append((age_days, symbol))

        contract_ages.sort(key=lambda item: (item[0], item[1]))
        side_count = min(self._COHORT_SIZE, len(contract_ages) // 2)
        if side_count == 0:
            return {}

        youngest = contract_ages[:side_count]
        oldest = contract_ages[-side_count:]

        targets: dict[str, float] = {}
        for _, symbol in youngest:
            targets[symbol] = -self._WEIGHT_PER_SYMBOL
        for _, symbol in oldest:
            targets[symbol] = self._WEIGHT_PER_SYMBOL
        return targets


def build_strategy() -> ContractMaturationSeasoningStrategy:
    """Construct a clean strategy instance."""
    return ContractMaturationSeasoningStrategy()
