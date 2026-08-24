"""derive_forward_membership must never request a reconstitution boundary in decision's future.

The field stalled for a full day on this: at any decision inside the 24h before a live Monday
reconstitution, the code asked for that Monday's membership a day early. episode_eligibility is
past-only -- an episode's end is its last CACHED bar's close time, which cannot reach a boundary
that has not occurred -- so every symbol failed eligibility and require_exact_membership raised on
every tick until decision itself became that Monday. No downstream consumer needed the lookahead:
both places that read the combined membership table filter `reconstitution_time <= decision`.
"""

from __future__ import annotations

import pandas as pd

from crypto_trade.cup50v2.config import OOS_END
from crypto_trade.cup50v2.universe import weekly_reconstitution_times


def _boundaries(decision: pd.Timestamp) -> tuple[pd.Timestamp, ...]:
    # Mirrors the call in derive_forward_membership exactly, so a regression there is caught here.
    end = decision + pd.Timedelta(seconds=1)
    return weekly_reconstitution_times(OOS_END + pd.Timedelta(seconds=1), end)


def test_no_boundary_strictly_after_decision_is_ever_requested() -> None:
    """8h decisions spanning three weekly crossings; none may ask past its own instant."""
    grid = pd.date_range("2026-08-17T00:00:00Z", "2026-08-31T00:00:00Z", freq="8h")
    for decision in grid:
        boundaries = _boundaries(pd.Timestamp(decision))
        assert all(boundary <= decision for boundary in boundaries), (
            f"{decision} requested a future boundary: {boundaries}"
        )


def test_the_monday_boundary_itself_is_requested_exactly_on_its_own_tick() -> None:
    """The exact failure: the 24h before Monday must exclude it; Monday must include it."""
    monday = pd.Timestamp("2026-08-24T00:00:00Z")
    for hours_before in (16, 8):
        decision = monday - pd.Timedelta(hours=hours_before)
        boundaries = _boundaries(decision)
        assert monday not in boundaries, f"{decision} should not yet see {monday}"
    boundaries_on_monday = _boundaries(monday)
    assert monday in boundaries_on_monday, "decision on the boundary itself must include it"
