"""Canonical identity and authority paths for the single Top-40 V5 edition."""

from __future__ import annotations

import dataclasses
import re
from pathlib import PurePosixPath

_TEAM_ID = re.compile(r"team-[0-9]{2}")


def _safe_relative(value: str, label: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{label} must be a safe repository-relative path")
    return path.as_posix()


@dataclasses.dataclass(frozen=True, slots=True)
class TournamentLayoutV5:
    """Identity and authority paths for one Top-40 V5 tournament.

    Every path is derived from ``tournament_root`` or ``reports_root``. V4 hard-coded its team-kit
    root as a module constant, which meant a new edition inherited the previous edition's kit
    directory without failing; deriving it here makes that class of mistake unrepresentable.
    """

    name: str
    branch: str
    tournament_root: str
    reports_root: str
    orchestrator_script: str
    broker_script: str
    contract_source: str
    team_ids: tuple[str, ...]
    maximum_trials: int = 12
    minimum_trials_before_decision: int = 8
    desk_individual_count: int = 3

    def __post_init__(self) -> None:
        if not self.name or re.fullmatch(r"[a-z0-9][a-z0-9-]*", self.name) is None:
            raise ValueError("tournament name must be lowercase kebab-case")
        if not self.branch or any(character.isspace() for character in self.branch):
            raise ValueError("tournament branch is invalid")
        for field in (
            "tournament_root",
            "reports_root",
            "orchestrator_script",
            "broker_script",
            "contract_source",
        ):
            object.__setattr__(self, field, _safe_relative(getattr(self, field), field))
        if not self.team_ids or len(set(self.team_ids)) != len(self.team_ids):
            raise ValueError("a V5 layout requires unique teams")
        expected = tuple(f"team-{number:02d}" for number in range(1, len(self.team_ids) + 1))
        if self.team_ids != expected or any(
            _TEAM_ID.fullmatch(team_id) is None for team_id in self.team_ids
        ):
            raise ValueError("V5 team ids must be a contiguous team-01..team-N sequence")
        if self.maximum_trials < 1:
            raise ValueError("maximum_trials must be positive")
        if not 1 <= self.minimum_trials_before_decision <= self.maximum_trials:
            raise ValueError("minimum_trials_before_decision must fit inside the trial budget")
        if not 1 <= self.desk_individual_count <= len(self.team_ids):
            raise ValueError("desk_individual_count must fit inside the team field")

    # -- authority files -------------------------------------------------------------------

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

    @property
    def calibration_report_path(self) -> str:
        return f"{self.tournament_root}/calibration-report.json"

    @property
    def snapshot_preflight_path(self) -> str:
        return f"{self.tournament_root}/snapshot-preflight.json"

    @property
    def mutation_ledger_path(self) -> str:
        return "tests/tournament/MUTATIONS-V5.md"

    # -- roots -----------------------------------------------------------------------------

    @property
    def team_kit_root(self) -> str:
        return f"{self.tournament_root}/team-kit"

    @property
    def private_root(self) -> str:
        return f"{self.tournament_root}/private"

    @property
    def is_reports_root(self) -> str:
        """Visible development artifacts. Never contains a sealed-block statistic."""

        return f"{self.reports_root}/is"

    @property
    def sealed_private_root(self) -> str:
        """Sealed-block artifacts, organizer-only.

        Physically separate from ``is_reports_root`` so that the function building a team's
        feedback packet cannot compute a sealed statistic even by mistake. A filter can be
        forgotten once; a directory the code never opens cannot.
        """

        return f"{self.private_root}/sealed"

    @property
    def scouting_private_root(self) -> str:
        return f"{self.private_root}/scouting"

    @property
    def historical_private_root(self) -> str:
        return f"{self.private_root}/historical"

    @property
    def historical_release_root(self) -> str:
        return f"{self.reports_root}/historical"

    @property
    def source_archive_root(self) -> str:
        return f"{self.reports_root}/source-archives/sha256"

    # -- per-team paths --------------------------------------------------------------------

    def require_team(self, team_id: str) -> str:
        if team_id not in self.team_ids:
            raise ValueError(
                f"unknown V5 team: {team_id}; expected {self.team_ids[0]} through "
                f"{self.team_ids[-1]}"
            )
        return team_id

    def team_root(self, team_id: str) -> str:
        return f"{self.tournament_root}/teams/{self.require_team(team_id)}"

    def team_scouting_root(self, team_id: str) -> str:
        """Phase S workspace.

        Deliberately a sibling of ``candidates``/``outbox``/``feedback`` rather than a child of
        them: the networked scouting profile mounts only this subtree, so it can never read the
        lane's evaluation feedback.
        """

        return f"{self.team_root(team_id)}/scouting"


TOP40_V5_LAYOUT = TournamentLayoutV5(
    name="quant-portfolio-blind-top40-v5",
    branch="quant-portfolio-blind-top40-v5",
    tournament_root="tournament/top40-v5",
    reports_root="reports-top40-v5",
    orchestrator_script="scripts/top40_v5_tournament.py",
    broker_script="scripts/top40_v5_team_broker.py",
    contract_source="src/crypto_trade/tournament/v5/contract.py",
    team_ids=tuple(f"team-{number:02d}" for number in range(1, 16)),
    maximum_trials=12,
    minimum_trials_before_decision=8,
    desk_individual_count=3,
)


__all__ = ["TOP40_V5_LAYOUT", "TournamentLayoutV5"]
