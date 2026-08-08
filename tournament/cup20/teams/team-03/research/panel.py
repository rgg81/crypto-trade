"""Shared IS panel construction for team-03 signal diagnostics.

Reads only ``data/cup20/is/`` and only builds *descriptive* statistics of the signal itself --
conditional forward returns, information coefficients, gate coverage, and the mechanical
properties of a weight stream (turnover, name count). It never computes a costed equity curve,
a Sharpe or a drawdown: the tournament's only scorer is ``scripts/cup20_evaluate.py``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA_ROOT = Path("data/cup20/is")
INTERVAL_HOURS = 8


def load_close_panel() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Wide close/open panels indexed by bar close time (== the decision boundary)."""
    bars = pd.read_parquet(DATA_ROOT / "bars.parquet")
    bars["decision_time"] = bars["open_time"] + pd.Timedelta(hours=INTERVAL_HOURS)
    close = bars.pivot(index="decision_time", columns="symbol", values="close").sort_index()
    open_ = bars.pivot(index="decision_time", columns="symbol", values="open").sort_index()
    return close, open_


def load_membership_mask(index: pd.DatetimeIndex, columns: pd.Index) -> pd.DataFrame:
    """Point-in-time membership as a boolean frame on the decision grid."""
    membership = pd.read_parquet(DATA_ROOT / "membership.parquet")
    membership["reconstitution_time"] = pd.to_datetime(
        membership["reconstitution_time"], utc=True
    )
    flags = (
        membership.assign(member=True)
        .pivot_table(
            index="reconstitution_time", columns="symbol", values="member", aggfunc="first"
        )
        .reindex(columns=columns)
        .fillna(False)
        .astype(bool)
    )
    return flags.reindex(index, method="ffill").fillna(False).astype(bool)


def rolling_stats(close: pd.DataFrame, formation: int) -> dict[str, pd.DataFrame]:
    """Momentum, efficiency ratio, sign persistence and jump share over ``formation`` bars."""
    logp = np.log(close)
    step = logp.diff()
    displacement = logp.diff(formation)
    path = step.abs().rolling(formation).sum()
    efficiency = displacement.abs() / path.replace(0.0, np.nan)
    up_share = (step > 0).astype(float).rolling(formation).mean()
    up_share = up_share.where(step.rolling(formation).count() == formation)
    persistence = np.where(
        displacement.to_numpy() >= 0, up_share.to_numpy(), 1.0 - up_share.to_numpy()
    )
    persistence = pd.DataFrame(persistence, index=close.index, columns=close.columns)
    largest = step.abs().rolling(formation).max()
    jump_share = largest / path.replace(0.0, np.nan)
    volatility = step.rolling(formation).std()
    return {
        "momentum": displacement,
        "efficiency": efficiency,
        "persistence": persistence,
        "jump_share": jump_share,
        "volatility": volatility,
        "path": path,
    }


def forward_log_return(close: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Forward ``horizon``-bar log return, aligned to the decision boundary that precedes it."""
    logp = np.log(close)
    return logp.shift(-horizon) - logp


def stacked(frames: dict[str, pd.DataFrame], mask: pd.DataFrame) -> pd.DataFrame:
    """Long-format panel restricted to point-in-time members with complete features."""
    pieces = {name: frame.where(mask).stack() for name, frame in frames.items()}
    return pd.DataFrame(pieces).dropna()
