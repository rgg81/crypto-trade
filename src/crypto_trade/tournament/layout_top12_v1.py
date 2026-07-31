"""Independent twelve-team path layout for Top-12 V1."""

from __future__ import annotations

import dataclasses
import re
from pathlib import PurePosixPath

_TEAM_ID = re.compile(r"team-(?:0[1-9]|1[0-2])")


def _safe_relative(value: str, label: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{label} must be a safe repository-relative path")
    return path.as_posix()


@dataclasses.dataclass(frozen=True, slots=True)
class TournamentLayoutTop12V1:
    """Canonical Top-12 V1 identity and authority paths."""

    name: str
    branch: str
    tournament_root: str
    reports_root: str
    orchestrator_script: str
    contract_source: str
    team_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name or re.fullmatch(r"[a-z0-9][a-z0-9-]*", self.name) is None:
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
        if len(self.team_ids) != 12 or len(set(self.team_ids)) != 12:
            raise ValueError("a Top-12 V1 layout requires twelve unique teams")
        if any(_TEAM_ID.fullmatch(team_id) is None for team_id in self.team_ids):
            raise ValueError("Top-12 V1 team ids must be team-01 through team-12")

    @property
    def config_path(self) -> str:
        return f"{self.tournament_root}/config.toml"

    @property
    def activation_freeze_path(self) -> str:
        return f"{self.tournament_root}/activation-freeze.json"

    @property
    def journal_path(self) -> str:
        return f"{self.tournament_root}/research-journal.jsonl"

    @property
    def result_lock_path(self) -> str:
        return f"{self.tournament_root}/.result-command.lock"

    @property
    def nomination_registry_path(self) -> str:
        return f"{self.tournament_root}/nomination-registry.json"

    @property
    def selection_freeze_path(self) -> str:
        return f"{self.tournament_root}/selection-freeze.json"

    def require_team(self, team_id: str) -> str:
        if team_id not in self.team_ids:
            raise ValueError(f"unknown Top-12 V1 team: {team_id}")
        return team_id

    def team_root(self, team_id: str) -> str:
        return f"{self.tournament_root}/teams/{self.require_team(team_id)}"


TOP12_V1_LAYOUT = TournamentLayoutTop12V1(
    name="quant-portfolio-blind-top12-v1",
    branch="quant-portfolio-blind-top12",
    tournament_root="tournament/top12-v1",
    reports_root="reports-top12-v1",
    orchestrator_script="scripts/top12_v1_tournament.py",
    contract_source="src/crypto_trade/tournament/top12_v1.py",
    team_ids=tuple(f"team-{number:02d}" for number in range(1, 13)),
)


__all__ = ["TOP12_V1_LAYOUT", "TournamentLayoutTop12V1"]
