"""tradfi-cup-01 — tournament-owned constants, paths, and the append-only journal.

The tournament defines its OWN splits and never touches ``core_tradfi.OOS_CUTOFF``:
  IS       2010-01-01 .. 2024-06-30 (inclusive)  — visible to teams (frozen snapshot data_is/)
  HOLDOUT  2024-07-01 .. 2026-06-30 (inclusive)  — sealed, orchestrator-only, evaluated once
Holdout evaluation refuses to run unless BOTH the --confirm-holdout flag AND the
``TRADFI_TOURNAMENT_ALLOW_HOLDOUT=1`` env var are present, and every run is journaled.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

import core_tradfi as ct  # noqa: E402

# ---------------------------------------------------------------- splits (tournament-owned) -----
TRN_IS_START = pd.Timestamp("2010-01-01")
TRN_IS_END = pd.Timestamp("2024-06-30")  # inclusive; last IS trading day is 2024-06-28
TRN_HOLD_START = pd.Timestamp("2024-07-01")
TRN_HOLD_END = pd.Timestamp("2026-06-30")  # inclusive
TRN_IS_HI = TRN_IS_END + pd.Timedelta(days=1)  # exclusive-hi for msharpe-style [lo, hi) slices
TRN_HOLD_HI = TRN_HOLD_END + pd.Timedelta(days=1)
IS_END_MS = int(pd.Timestamp("2024-07-01").value // 1_000_000) - 1  # last permitted open_time ms

# ---------------------------------------------------------------- execution / caps --------------
COST_SIDE = ct.COST_SIDE  # 6 bps/side taker+slippage — re-exported, never redefined
PER_NAME_CAP = 0.10  # |w_i| cap after gross-normalisation
NET_CAP = 0.25  # |Σw| cap (market-neutral-ish mandate)
CAP_ITERS = 10  # clip/trim/renormalise iterations before the final hard pass
MIN_MEDIAN_NAMES_PER_SIDE = 5  # breadth validity floor (charter, Critic-checked)
SEED = 20260717

# ---------------------------------------------------------------- paths -------------------------
TOURNAMENT_ROOT = ct._ROOT / "tournament" / "tradfi"
SNAPSHOT_DIR = TOURNAMENT_ROOT / "data_is"
MANIFEST_PATH = TOURNAMENT_ROOT / "MANIFEST.sha256.json"
TEAMS_DIR = TOURNAMENT_ROOT / "teams"
CRITIC_DIR = TOURNAMENT_ROOT / "critic"
RESULTS_DIR = TOURNAMENT_ROOT / "results"
REGISTRY_PATH = TOURNAMENT_ROOT / "registry.jsonl"
JOURNAL_PATH = TOURNAMENT_ROOT / "journal.jsonl"

TEAM_IDS = tuple(f"team-{i:02d}" for i in range(1, 11))

HOLDOUT_ENV_FLAG = "TRADFI_TOURNAMENT_ALLOW_HOLDOUT"

VIX_SYM = "VIX"  # aux series — ships in the snapshot, never a tradable column


def team_dir(team_id: str, teams_dir: Path = TEAMS_DIR) -> Path:
    if team_id not in TEAM_IDS and not team_id.startswith("scratch-"):
        raise ValueError(f"unknown team id {team_id!r} (expected one of {TEAM_IDS})")
    return teams_dir / team_id


def journal(event: str, journal_path: Path = JOURNAL_PATH, **payload) -> dict:
    """Append one JSON line to the tournament journal (append-only by convention + review)."""
    entry = {"ts": datetime.now(UTC).isoformat(timespec="seconds"), "event": event, **payload}
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    with journal_path.open("a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry
