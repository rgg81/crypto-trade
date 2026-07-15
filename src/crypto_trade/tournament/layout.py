"""Path layout for side-by-side immutable tournament generations."""

from __future__ import annotations

import dataclasses
import re
from pathlib import PurePosixPath

_TEAM_ID = re.compile(r"team-(?:0[1-9]|10)")


def _safe_relative(value: str, label: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{label} must be a safe repository-relative path")
    return path.as_posix()


@dataclasses.dataclass(frozen=True)
class TournamentLayout:
    """Canonical paths and identity for one tournament generation."""

    name: str
    branch: str
    tournament_root: str
    reports_root: str
    orchestrator_script: str
    contract_source: str
    team_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", self.name):
            raise ValueError("tournament name must be lowercase kebab-case")
        if not self.branch or any(character.isspace() for character in self.branch):
            raise ValueError("tournament branch is invalid")
        for field in (
            "tournament_root",
            "reports_root",
            "orchestrator_script",
            "contract_source",
        ):
            object.__setattr__(self, field, _safe_relative(getattr(self, field), field))
        if len(self.team_ids) != 10 or len(set(self.team_ids)) != 10:
            raise ValueError("a Top-40 layout requires ten unique teams")
        if any(_TEAM_ID.fullmatch(team_id) is None for team_id in self.team_ids):
            raise ValueError("team ids must be team-01 through team-10")

    @property
    def config_path(self) -> str:
        return f"{self.tournament_root}/config.toml"

    @property
    def state_path(self) -> str:
        return f"{self.tournament_root}/run_state.json"

    @property
    def state_lock_path(self) -> str:
        return f"{self.tournament_root}/run_state.lock"

    @property
    def phase0_freeze_path(self) -> str:
        return f"{self.tournament_root}/phase0_freeze.json"

    @property
    def organizer_journal_path(self) -> str:
        return f"{self.tournament_root}/organizer_research_journal.jsonl"

    @property
    def finalist_cohort_lock_path(self) -> str:
        return f"{self.tournament_root}/finalist_cohort_lock.json"

    def require_team(self, team_id: str) -> str:
        if team_id not in self.team_ids:
            raise ValueError(f"unknown tournament team: {team_id}")
        return team_id

    def team_root(self, team_id: str) -> str:
        return f"{self.tournament_root}/teams/{self.require_team(team_id)}"

    def report_root(self, team_id: str) -> str:
        return f"{self.reports_root}/{self.require_team(team_id)}"


TOP40_V2_LAYOUT = TournamentLayout(
    name="quant-portfolio-blind-top40-v2",
    branch="quant-portfolio-blind-top40-v2",
    tournament_root="tournament/top40-v2",
    reports_root="reports-top40-v2",
    orchestrator_script="scripts/top40_v2_tournament.py",
    contract_source="src/crypto_trade/tournament/top40_v2.py",
    team_ids=tuple(f"team-{number:02d}" for number in range(1, 11)),
)
