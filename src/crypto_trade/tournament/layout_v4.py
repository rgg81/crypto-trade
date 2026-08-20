"""Independent, edition-selectable path layouts for Top-40 V4."""

from __future__ import annotations

import dataclasses
import os
import re
from pathlib import PurePosixPath

_TEAM_ID = re.compile(r"team-[0-9]{2}")
_EDITION_ENVIRONMENT = "CRYPTO_TRADE_TOP40_V4_EDITION"


def _safe_relative(value: str, label: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{label} must be a safe repository-relative path")
    return path.as_posix()


@dataclasses.dataclass(frozen=True, slots=True)
class TournamentLayoutV4:
    """Canonical identity and authority paths for one isolated V4 edition."""

    name: str
    branch: str
    tournament_root: str
    reports_root: str
    orchestrator_script: str
    contract_source: str
    team_ids: tuple[str, ...]
    maximum_trials: int = 12
    advance_count: int = 5

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
        if not self.team_ids or len(set(self.team_ids)) != len(self.team_ids):
            raise ValueError("a V4 layout requires unique teams")
        expected = tuple(f"team-{number:02d}" for number in range(1, len(self.team_ids) + 1))
        if self.team_ids != expected or any(
            _TEAM_ID.fullmatch(team_id) is None for team_id in self.team_ids
        ):
            raise ValueError("V4 team ids must be a contiguous team-01..team-N sequence")
        if self.maximum_trials < 1:
            raise ValueError("maximum_trials must be positive")
        if not 1 <= self.advance_count <= len(self.team_ids):
            raise ValueError("advance_count must fit inside the team field")

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
            raise ValueError(
                f"unknown V4 team: {team_id}; expected {self.team_ids[0]} through "
                f"{self.team_ids[-1]}"
            )
        return team_id

    def team_root(self, team_id: str) -> str:
        return f"{self.tournament_root}/teams/{self.require_team(team_id)}"


TOP40_V4_LAYOUT = TournamentLayoutV4(
    name="quant-portfolio-blind-top40-v4-r1",
    branch="quant-portfolio-blind-top40-v4-r1",
    tournament_root="tournament/top40-v4-r1",
    reports_root="reports-top40-v4-r1",
    orchestrator_script="scripts/top40_v4_tournament.py",
    contract_source="src/crypto_trade/tournament/top40_v4.py",
    team_ids=tuple(f"team-{number:02d}" for number in range(1, 13)),
)

TOP40_V4_R2_LAYOUT = TournamentLayoutV4(
    name="quant-portfolio-blind-top40-v4-r2",
    branch="quant-portfolio-blind-top40-v4-r1-v2-restart4",
    tournament_root="tournament/top40-v4-r2",
    reports_root="reports-top40-v4-r2",
    orchestrator_script="scripts/top40_v4_r2_tournament.py",
    contract_source="src/crypto_trade/tournament/top40_v4.py",
    team_ids=tuple(f"team-{number:02d}" for number in range(1, 16)),
    maximum_trials=12,
    advance_count=6,
)

_LAYOUTS = {
    "r1": TOP40_V4_LAYOUT,
    "r2": TOP40_V4_R2_LAYOUT,
}


def select_v4_layout(edition: str) -> TournamentLayoutV4:
    """Select an edition before importing the remaining V4 authority modules.

    Organizer entrypoints are separate processes, so one process owns exactly one edition. The
    environment marker is inherited by activation-test subprocesses and makes accidental mixed
    authority fail visibly instead of silently writing to the wrong namespace.
    """

    try:
        selected = _LAYOUTS[edition]
    except KeyError as exc:
        raise ValueError(f"unknown Top-40 V4 edition: {edition}") from exc
    os.environ[_EDITION_ENVIRONMENT] = edition
    global TOP40_V4_LAYOUT
    TOP40_V4_LAYOUT = selected
    return selected


_requested_edition = os.environ.get(_EDITION_ENVIRONMENT, "r1")
if _requested_edition not in _LAYOUTS:
    raise RuntimeError(f"invalid {_EDITION_ENVIRONMENT}: {_requested_edition}")
TOP40_V4_LAYOUT = _LAYOUTS[_requested_edition]


__all__ = [
    "TOP40_V4_LAYOUT",
    "TOP40_V4_R2_LAYOUT",
    "TournamentLayoutV4",
    "select_v4_layout",
]
