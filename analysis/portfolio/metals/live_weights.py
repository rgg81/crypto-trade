"""Live parity bridge — the deployed per-metal position book of the CURRENT metals champion.

Thin adapter over the champion module (iter-010: breadth-acceleration gate + POSITION-LEVEL honest
accounting). The live paper engine and the reconcile harness call ONLY these three functions, so
swapping the champion is a one-line re-point here.

PARITY IS NOW TRIVIAL. The champion's net is computed FROM the deployed position book
(`net[t] = Σ desk[t,i]·ret_fwd[t,i] − COST·Σ|Δdesk[t,i]|`), so the positions the live engine holds
(`deployed_weight_book` / `next_target_weights_metals`) and the PnL it books (`regime_net`) come
from the same `desk` matrix — no two-stream reconstruction to drift. `reconcile_metals.py` proves
the live recompute reproduces the backtest book bit-for-bit.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import iter_011_deadband as champ  # noqa: E402  — the current metals champion

CHAMP = champ.CHAMP11


def deployed_weight_book(coins: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.Series]:
    """Full per-candle DESK position book (per-metal weights) + bear flag — the backtest target."""
    return champ.desk_book(coins)


def regime_net(coins: dict[str, pd.DataFrame]) -> pd.Series:
    """The desk NET return series (paper-PnL source of truth) — POSITION-LEVEL, computed from the
    deployed book, so it is bit-consistent with the positions the live engine holds."""
    return champ.desk_net(coins)


def next_target_weights_metals(coins: dict[str, pd.DataFrame], tol: float = 1e-9) -> dict:
    """Per-metal deployed position to hold during the just-opened forming candle — live target."""
    return champ.next_target_weights(coins, tol)
