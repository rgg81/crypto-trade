"""Narrow strategy interface for independently developed tournament teams."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from typing import Protocol

import pandas as pd

# Reserved organizer-owned target-artifact metadata; it can never be a tradable symbol.
REBALANCE_INSTRUCTION_COLUMN = "__crypto_trade_rebalance__"


@dataclasses.dataclass(frozen=True)
class DecisionContext:
    """Past-only market view supplied by the central tournament runner.

    ``bars`` contains rows whose close time is no later than ``decision_time``. Funding rows are
    strictly earlier than ``decision_time``. ``eligible_symbols`` is weekly membership
    intersected with symbols that have an executable open at the decision; that open price is not
    exposed. Teams cannot submit fills or PnL through this API.
    """

    decision_time: pd.Timestamp
    bars: Mapping[str, pd.DataFrame]
    funding: pd.DataFrame
    auxiliary: Mapping[str, pd.DataFrame]
    eligible_symbols: Sequence[str]


class TargetStrategy(Protocol):
    """Return signed unlevered targets, or ``None`` to keep current quantities.

    A mapping is an explicit strategy rebalance, including an empty mapping which requests a flat
    book. ``None`` skips only the strategy rebalance at that decision. The central evaluator still
    enforces membership exits, delisting exits, participation limits, and exposure reductions.
    Canonical workers stage no fitted models or data artifacts: any learned state must be fitted or
    updated from the past-only rows streamed through ``DecisionContext`` during the run.
    """

    def target_weights(
        self, context: DecisionContext, *, seed: int
    ) -> Mapping[str, float] | None: ...


# Canonical team entrypoints define ``build_strategy() -> TargetStrategy``. The factory lets the
# common runner create one clean stateful instance without importing team code into this package.
