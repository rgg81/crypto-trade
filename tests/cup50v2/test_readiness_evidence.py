"""What the recorded twelve-seed readiness run proves.

CUP-50 activated on a flat strategy and three organizer defects survived into a live field. This
asserts against the evidence file the real run produced, so a later change that quietly breaks
execution, the risk unit or the cost model fails here rather than in an observation nobody can redo.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

EVIDENCE = Path("tournament/cup50v2/preflight/seed-field-readiness.json")


@pytest.fixture(scope="module")
def readiness() -> dict:
    if not EVIDENCE.is_file() or not EVIDENCE.read_text().strip():
        pytest.skip("readiness has not been run in this checkout")
    return json.loads(EVIDENCE.read_text())


def test_the_whole_field_deployed(readiness: dict) -> None:
    assert readiness["status"] == "ready"
    assert readiness["deployed_lanes"] == 12
    assert len(readiness["lanes"]) == 12


def test_every_lane_traded_and_stayed_solvent(readiness: dict) -> None:
    for team_id, lane in readiness["lanes"].items():
        for multiplier in ("1", "2", "3"):
            cell = lane[multiplier]
            assert cell["turnover"] > 0.0, team_id
            assert cell["final_equity"] > 0.0, (team_id, multiplier)


def test_the_common_risk_unit_delivered_the_target_volatility(readiness: dict) -> None:
    """The point of the ex-ante unit, measured on real data.

    CUP-50 scaled by realised past volatility and its winner ran at 23% annualised against a 10%
    target, which made cross-lane drawdown comparison meaningless. Every lane here lands inside a
    narrow band around the target, so a drawdown difference between two lanes is a difference in
    behaviour rather than in size.
    """
    volatilities = {
        team_id: lane["1"]["annualized_volatility"] for team_id, lane in readiness["lanes"].items()
    }
    for team_id, value in volatilities.items():
        assert 0.06 <= value <= 0.14, (team_id, value)
    spread = max(volatilities.values()) - min(volatilities.values())
    assert spread < 0.05, volatilities


def test_no_lane_was_annihilated_by_its_own_turnover(readiness: dict) -> None:
    """Four CUP-50 lanes ran 231x-937x a year and lost 68-91% at 3x cost."""
    for team_id, lane in readiness["lanes"].items():
        assert lane["1"]["turnover"] < 500.0, (team_id, lane["1"]["turnover"])
        survived = lane["3"]["final_equity"] / lane["1"]["final_equity"]
        assert survived > 0.25, (team_id, survived)
