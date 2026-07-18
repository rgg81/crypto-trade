"""crypto-cup-01 — tournament-owned constants, paths, and the append-only journal.

The tournament defines its OWN splits (never reuses any track's OOS_CUTOFF):
  IS       2020-01-01 .. 2024-06-30 (inclusive)  — visible to teams (frozen snapshot data_is/)
  HOLDOUT  2024-07-01 .. 2026-06-30 (inclusive)  — sealed, orchestrator-only, evaluated once
Holdout evaluation refuses to run unless BOTH the --confirm-holdout flag AND the
``CRYPTO_TOURNAMENT_ALLOW_HOLDOUT=1`` env var are present, and every run is journaled.

Grid: Binance USDT-perp 8h candles (00/08/16 UTC opens). Universe: weekly PIT top-40 by
trailing 7-day dollar volume (see ``universe.py``), pure crypto coins only.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

_ROOT = _HERE.parents[1]  # the quant-portfolio-tournament worktree root

# ---------------------------------------------------------------- splits (tournament-owned) -----
TRN_IS_START = pd.Timestamp("2020-01-01")
TRN_IS_END = pd.Timestamp("2024-06-30")  # inclusive; last IS candle opens 2024-06-30 16:00 UTC
TRN_HOLD_START = pd.Timestamp("2024-07-01")
TRN_HOLD_END = pd.Timestamp("2026-06-30")  # inclusive — exactly 24 monthly Sharpe points
TRN_IS_HI = TRN_HOLD_START  # exclusive-hi for msharpe-style [lo, hi) slices
TRN_HOLD_HI = TRN_HOLD_END + pd.Timedelta(days=1)
IS_END_MS = int(pd.Timestamp("2024-07-01").value // 1_000_000) - 1  # last permitted open_time ms

# ---------------------------------------------------------------- grid --------------------------
STEP_MS = 8 * 60 * 60 * 1000  # 8h candles
CANDLES_PER_YEAR = 1095  # 3 candles/day × 365 — crypto trades every day

# ---------------------------------------------------------------- universe ----------------------
TOP_N = 40  # weekly top-40 by trailing dollar volume
DVOL_WIN = 21  # 7 days of 8h candles — the trailing quote-volume ranking window
DVOL_MIN_PERIODS = 18  # tolerate a 1-candle exchange outage mid-life without a week's ejection
REFRESH_WEEKDAY = 0  # Monday 00:00 UTC candles are the weekly universe refresh points

# Stablecoin/fiat-pegged exclusion (symbol substring) — identical to the production universe_v2.
STABLE = re.compile(r"(USDC|BUSD|FDUSD|TUSD|USD1|DAI|USDP|EUR|USTC|FRAX|PAXG|XUSD|USDE)")

# Non-COIN perps to EXCLUDE (Binance ``underlyingType != COIN``: tokenized stocks/EQUITY,
# COMMODITY/metals, INDEX baskets, PREMARKET/pre-IPO names). Copied VERBATIM from the audited
# production list in analysis/portfolio_v2/universe_v2.py so the frozen evaluator has no import
# edge into team-prohibited paths. The tournament trades PURE CRYPTO only.
NON_COIN_PERPS = frozenset(
    {
        "0GUSDT",
        "ALLUSDT",
        "AMZNUSDT",
        "AZTECUSDT",
        "BLUEBIRDUSDT",
        "BMNRUSDT",
        "BREVUSDT",
        "BTCDOMUSDT",
        "CCUSDT",
        "COINUSDT",
        "COPPERUSDT",
        "CRCLUSDT",
        "DEFIUSDT",
        "EDGEUSDT",
        "EPICUSDT",
        "ESPUSDT",
        "EWJUSDT",
        "FAKEKR000660USDT",
        "FOGOUSDT",
        "GOOGLUSDT",
        "HOODUSDT",
        "INTCUSDT",
        "KATUSDT",
        "KITEUSDT",
        "MEGAUSDT",
        "METAUSDT",
        "METUSDT",
        "MONUSDT",
        "MSTRUSDT",
        "NVDAUSDT",
        "OPENAIUSDT",
        "PAYPUSDT",
        "PLTRUSDT",
        "QNTXUSDT",
        "QQQUSDT",
        "SENTUSDT",
        "SPACEFUSDT",
        "SPCXUSDT",
        "SPYUSDT",
        "STABLEUSDT",
        "TSLAUSDT",
        "XAGUSDT",
        "XAUUSDT",
        "XPDUSDT",
        "XPTUSDT",
        "YBUSDT",
        "ZAMAUSDT",
    }
)

# ---------------------------------------------------------------- execution / caps --------------
COST_SIDE = 0.0005  # 5 bps/side taker fee on |Δweight| turnover
# Liquidity-scaled per-side slippage (bps), from the audited engine_v2 model:
#   slip_bps = clip(SLIP_A + SLIP_B / dvol_$M, SLIP_FLOOR, SLIP_CAP)
SLIP_A = 1.0
SLIP_B = 20.0
SLIP_FLOOR = 1.0
SLIP_CAP = 10.0
LIQ_WIN = 90  # trailing candles for the slippage dollar-volume estimate (past-only)

PER_NAME_CAP = 0.10  # |w_i| cap after gross-normalisation
NET_CAP = 0.25  # |Σw| cap (market-neutral-ish mandate)
CAP_ITERS = 10  # clip/trim/renormalise iterations before the final hard pass
MIN_MEDIAN_NAMES_PER_SIDE = 5  # breadth validity floor (charter, Critic-checked)

TARGET_VOL = 0.01  # per-candle portfolio vol target (~33%/yr at 1095 candles)
PORT_VOL_WIN = 84  # trailing candles for the portfolio vol estimate
MAX_LEV = 3.0  # vol-target scale cap

SEED = 20260718

# ---------------------------------------------------------------- IS regime tags ----------------
# Fixed crypto-native regime windows for the all-weather scorecard. Every boundary is anchored
# to a DOCUMENTED macro event (pre-registered, never tuned to any strategy's P&L):
#   2020-02-14→03-13 COVID crash (capitulation low Mar 13); 2021-04-14 Coinbase-IPO cycle top;
#   2021-07-20 China-mining-ban capitulation low; 2021-11-10 69k ATH; 2022-11-21 FTX trough;
#   2023-10-16 ETF run-up start (BlackRock ticker listing); 2024-03-14 73k ATH post-ETF.
_REGIMES = [
    ("bull", "2020-01-01", "2020-02-14"),  # pre-COVID grind-up
    ("bear", "2020-02-14", "2020-03-13"),  # COVID crash
    ("bull", "2020-03-13", "2021-04-14"),  # 2020-21 bull to the Coinbase-IPO top
    ("bear", "2021-04-14", "2021-07-20"),  # May-2021 China-mining-ban crash
    ("bull", "2021-07-20", "2021-11-10"),  # run to the 69k ATH
    ("bear", "2021-11-10", "2022-11-21"),  # 2022 macro bear: Fed / LUNA / 3AC / FTX
    ("chop", "2022-11-21", "2023-10-16"),  # FTX-aftermath base + 2023 ranges
    ("bull", "2023-10-16", "2024-03-14"),  # ETF run-up + approval to the Mar-2024 ATH
    ("chop", "2024-03-14", "2024-07-01"),  # post-halving range into IS end
]

# ---------------------------------------------------------------- paths -------------------------
TOURNAMENT_ROOT = _ROOT / "tournament" / "crypto"
SNAPSHOT_DIR = TOURNAMENT_ROOT / "data_is"
MANIFEST_PATH = TOURNAMENT_ROOT / "MANIFEST.sha256.json"
TEAMS_DIR = TOURNAMENT_ROOT / "teams"
CRITIC_DIR = TOURNAMENT_ROOT / "critic"
RESULTS_DIR = TOURNAMENT_ROOT / "results"
REGISTRY_PATH = TOURNAMENT_ROOT / "registry.jsonl"
JOURNAL_PATH = TOURNAMENT_ROOT / "journal.jsonl"
BUILD_DIR = TOURNAMENT_ROOT / "_build"  # organizer scratch: union lists, coverage reports

# The shared live data store (klines / funding_rates / open_interest) lives in the MAIN repo
# checkout; worktrees gitignore their own data/. Overridable via CLI --src flags.
MAIN_DATA_DIR = _ROOT.parent.parent / "data"

TEAM_IDS = tuple(f"team-{i:02d}" for i in range(1, 11))

HOLDOUT_ENV_FLAG = "CRYPTO_TOURNAMENT_ALLOW_HOLDOUT"


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


def crypto_pool_symbol(sym: str) -> bool:
    """True iff a symbol belongs to the tournament's full crypto pool (pre-ranking filter)."""
    return (
        sym.endswith("USDT")
        and sym.isascii()
        and not STABLE.search(sym)
        and sym not in NON_COIN_PERPS
    )
