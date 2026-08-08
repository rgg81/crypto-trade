"""Calibrated screen, anchored on the organiser's own packet for journal sequence #21.

Sequence #21 evaluated the nominee and returned annualised turnover 28.76 and net Sharpe 1.018 at
1x, against offline figures of 20.5 and IR 1.31 for the identical configuration. Two constants
follow and are used here to convert an offline reading into an expected packet reading:

    turnover_packet  ~ 1.403 * turnover_offline      (the risk scalar's realised median was 0.293,
                                                      not the 0.20 clamp the offline screen assumed,
                                                      and the requested book is trimmed by the
                                                      per-symbol cap at 694 of 1445 boundaries)
    sharpe_packet    ~ 0.92 * IR_offline - 0.00912 * turnover_offline

Both are fitted to ONE organiser observation and are a screen, not a score. They exist so that the
turnover repair is not attempted blind. The failure they are repairing -- turnover 28.76 against a
25.0 floor -- came from the organiser's harness, and so will its verdict.

Two turnover repairs are tested here:
  R1 damp each tranche's own net exposure before averaging, rather than damping the averaged book,
     so the damping term is itself smoothed over SMOOTH_BARS instead of moving every rebalance;
  R2 longer smoothing and a longer cadence.
"""

from __future__ import annotations

import itertools
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eda_surface import funding_per_bar  # noqa: E402
from eda_variants import simulate  # noqa: E402
from panel import load_close_panel, load_membership_mask, rolling_stats  # noqa: E402

TURNOVER_FACTOR = 1.403
SHARPE_GAIN = 0.92
SHARPE_COST = 0.00912

CLOSE: pd.DataFrame
MASK: pd.DataFrame


@lru_cache(maxsize=None)
def tranches(formation: int, z: float) -> pd.DataFrame:
    stats = rolling_stats(CLOSE, formation)
    mom = stats["momentum"].where(MASK)
    pers = stats["persistence"].where(MASK)
    vol = stats["volatility"].where(MASK)
    valid = mom.notna() & pers.notna() & vol.notna() & (vol > 0) & (mom != 0)
    sign = np.sign(mom).where(valid)
    score = ((2.0 * pers - 1.0) * np.sqrt(formation)).where(valid)
    part = (sign.where(score >= z) / vol).fillna(0.0)
    gross = part.abs().sum(axis=1)
    return part.div(gross.where(gross > 0, 1.0), axis=0)


def _damp(frame: pd.DataFrame, damping: float) -> pd.DataFrame:
    if damping <= 0.0:
        return frame
    live = (frame != 0.0).sum(axis=1).replace(0, np.nan)
    return frame.sub(damping * frame.sum(axis=1) / live, axis=0).where(frame != 0.0, 0.0)


def build(formation, z, smooth, damping, *, per_tranche: bool) -> pd.DataFrame:
    part = tranches(formation, z)
    if per_tranche:
        part = _damp(part, damping)
    position = part.rolling(smooth, min_periods=1).mean().where(MASK, 0.0)
    if not per_tranche:
        position = _damp(position, damping)
    gross = position.abs().sum(axis=1)
    return position.div(gross.where(gross > 0, 1.0), axis=0)


def main() -> None:
    global CLOSE, MASK
    close, _ = load_close_panel()
    CLOSE = close
    MASK = load_membership_mask(close.index, close.columns)
    funding = funding_per_bar(close.index, close.columns)

    print(f"{'mode':>6} {'f':>3} {'z':>5} {'sm':>3} {'dp':>5} {'cad':>4} | {'IR':>5} {'turnOFF':>7} "
          f"| {'->turn':>7} {'->sharpe':>8} | {'e/t':>5} {'S':>5} | folds")
    rows = []
    for per_tranche, formation, z, smooth, damping, cadence in itertools.product(
        (True, False), (15, 18), (1.10,), (33, 45, 57), (0.45, 0.55, 0.65), (3, 6)
    ):
        book = build(formation, z, smooth, damping, per_tranche=per_tranche)
        r = simulate(book, close, funding, every=cadence, phase=1)
        turn = r["turnover_exec"] * TURNOVER_FACTOR
        sharpe = SHARPE_GAIN * r["ir"] - SHARPE_COST * r["turnover_exec"]
        rows.append((sharpe, turn, per_tranche, formation, z, smooth, damping, cadence, r))
    rows.sort(key=lambda item: -item[0])
    for sharpe, turn, per_tranche, formation, z, smooth, damping, cadence, r in rows:
        flag = "OK" if turn <= 25.0 and r["short"] > 0.02 and r["edge_per_turn"] >= 45 else ""
        print(
            f"{'tranche' if per_tranche else 'book':>6} {formation:>3} {z:>5.2f} {smooth:>3} "
            f"{damping:>5.2f} {cadence:>4} | {r['ir']:5.2f} {r['turnover_exec']:7.1f} | "
            f"{turn:7.1f} {sharpe:8.3f} | {r['edge_per_turn']:5.1f} {r['short']:+5.2f} | "
            + " ".join(f"{v:+5.2f}" for v in r["fold_ir"]) + f"  {flag}"
        )


if __name__ == "__main__":
    main()
