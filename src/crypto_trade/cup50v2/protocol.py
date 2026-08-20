"""Versioned, strategy-visible CUP-50 v2 interface."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from typing import Protocol

import pandas as pd


@dataclasses.dataclass(frozen=True, slots=True)
class DecisionContextV2:
    """The complete and deliberately narrow view available to a strategy.

    Bars for the current eligible symbols are drawn from the trailing 180 complete UTC days and
    have actual ``close_time < decision_time``; funding uses the same trailing window and has
    ``funding_time < decision_time``. Opens, execution marks, fills, positions, costs, equity, and
    PnL have no field in this interface.
    """

    decision_time: pd.Timestamp
    bars: Mapping[str, pd.DataFrame]
    funding: pd.DataFrame
    auxiliary: Mapping[str, pd.DataFrame]
    eligible_symbols: Sequence[str]


class TargetStrategyV2(Protocol):
    """Return signed target weights, ``{}`` to flatten, or ``None`` to hold.

    A strategy may set boolean ``uses_bars`` or ``uses_funding`` to false when that entire input
    is mechanism-inapplicable. The evaluator then supplies an empty input of the same interface.
    Omitted declarations default to true.
    """

    def target_weights(
        self, context: DecisionContextV2, *, seed: int
    ) -> Mapping[str, float] | None: ...


def build_strategy() -> TargetStrategyV2:  # pragma: no cover - interface documentation only
    """Canonical team entrypoint (implemented by each frozen source bundle)."""
    raise NotImplementedError
