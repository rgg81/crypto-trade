"""Path layout for the clean Top-40 V3 tournament namespace."""

from __future__ import annotations

from crypto_trade.tournament.layout import TournamentLayout


class TournamentLayoutV3(TournamentLayout):
    """Generation-aware V3 authority paths.

    V3 deliberately uses a hyphenated Phase-0 record, a train-lab journal, and one
    global result-command lock.  Inheriting V2's historical filenames would make
    the otherwise canonical layout advertise authorities that do not exist.
    """

    @property
    def state_lock_path(self) -> str:
        return f"{self.tournament_root}/.result-command.lock"

    @property
    def phase0_freeze_path(self) -> str:
        return f"{self.tournament_root}/phase0-freeze.json"

    @property
    def organizer_journal_path(self) -> str:
        return f"{self.tournament_root}/organizer-lab-journal.jsonl"


TOP40_V3_LAYOUT = TournamentLayoutV3(
    name="quant-portfolio-blind-top40-v3",
    branch="quant-portfolio-blind-top40-v3",
    tournament_root="tournament/top40-v3",
    reports_root="reports-top40-v3",
    orchestrator_script="scripts/top40_v3_tournament.py",
    contract_source="src/crypto_trade/tournament/top40_v3.py",
    team_ids=tuple(f"team-{number:02d}" for number in range(1, 11)),
)
