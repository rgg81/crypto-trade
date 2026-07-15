from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from crypto_trade.tournament.top40 import ValidationIssue

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/top40_invalid_team_amendment.py"
SPEC = importlib.util.spec_from_file_location("_test_top40_amendment", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
amendment = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = amendment
SPEC.loader.exec_module(amendment)


def _authorized_issues() -> tuple[ValidationIssue, ...]:
    return (
        ValidationIssue(
            "long_and_short_enabled",
            "hard compliance check failed: long_and_short_enabled",
        ),
        ValidationIssue(
            "long_and_short_enabled",
            "public_oos long realized exposure is immaterial: active_fraction=0.038813, "
            "mean=0.007052",
        ),
        ValidationIssue(
            "long_and_short_enabled",
            "public_oos short realized exposure is immaterial: active_fraction=0.038813, "
            "mean=0.007052",
        ),
    )


def test_authorized_issue_set_is_exact_and_narrow() -> None:
    amendment._validate_authorized_issue_set(_authorized_issues())
    with pytest.raises(ValueError, match="unexpected issues"):
        amendment._validate_authorized_issue_set(_authorized_issues()[:2])
    with pytest.raises(ValueError, match="unexpected issues"):
        amendment._validate_authorized_issue_set(
            _authorized_issues() + (ValidationIssue("future_data", "unrelated integrity fault"),)
        )


def test_amendment_excludes_only_team_04() -> None:
    assert amendment.INVALID_TEAM_ID == "team-04"
    assert set(amendment.VALID_TEAM_IDS) == set(amendment.base.TEAM_IDS) - {"team-04"}
    assert len(amendment.VALID_TEAM_IDS) == 9


def test_original_orchestrator_still_matches_phase0_hash() -> None:
    phase0 = json.loads((ROOT / "tournament/top40/phase0_freeze.json").read_text())
    observed = hashlib.sha256((ROOT / "scripts/top40_tournament.py").read_bytes()).hexdigest()
    assert observed == phase0["orchestrator_sha256"]


def test_amendment_changes_only_derived_record_paths() -> None:
    assert set(amendment.AMENDMENT_CHANGED_PATHS) == {
        "tournament/top40/organizer_amendment_01.json",
        "tournament/top40/teams/team-04/submission.json",
        "tournament/top40/run_state.json",
    }
