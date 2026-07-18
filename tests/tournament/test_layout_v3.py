from __future__ import annotations

import pytest

from crypto_trade.tournament.layout_v3 import TOP40_V3_LAYOUT


def test_v3_layout_uses_a_fresh_namespace():
    assert TOP40_V3_LAYOUT.name == "quant-portfolio-blind-top40-v3"
    assert TOP40_V3_LAYOUT.branch == "quant-portfolio-blind-top40-v3"
    assert TOP40_V3_LAYOUT.tournament_root == "tournament/top40-v3"
    assert TOP40_V3_LAYOUT.reports_root == "reports-top40-v3"
    assert TOP40_V3_LAYOUT.team_root("team-10") == "tournament/top40-v3/teams/team-10"
    assert TOP40_V3_LAYOUT.state_path == "tournament/top40-v3/run_state.json"
    assert TOP40_V3_LAYOUT.state_lock_path == "tournament/top40-v3/.result-command.lock"
    assert TOP40_V3_LAYOUT.phase0_freeze_path == "tournament/top40-v3/phase0-freeze.json"
    assert (
        TOP40_V3_LAYOUT.organizer_journal_path
        == "tournament/top40-v3/organizer-lab-journal.jsonl"
    )


def test_v3_layout_keeps_exactly_ten_teams():
    assert TOP40_V3_LAYOUT.team_ids == tuple(
        f"team-{number:02d}" for number in range(1, 11)
    )
    with pytest.raises(ValueError, match="unknown tournament team"):
        TOP40_V3_LAYOUT.report_root("team-11")
