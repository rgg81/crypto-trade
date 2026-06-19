"""REDUCE the broad-carry drawdown (-32%) — vol-target / drawdown-brake / wider book.

The broad carry's open weakness is a -32% maxDD (short-squeeze price tail). Attack it WITHOUT
killing the carry, via PAST-ONLY exposure overlays + diversification, all IS-calibrated:
  - VOL-TARGET : scale gross exposure by target_vol / trailing_vol(net) -> de-lever in turbulent
                 periods. target = IS median of the rolling net vol.
  - DD-BRAKE   : when running drawdown from the equity peak exceeds a threshold, cut exposure to a
                 floor until a new peak -> caps the tail directly. Uses realized equity <= t-1 only.
  - WIDER BOOK : FRAC 0.25 -> 0.40 (more coins/side -> less squeeze concentration).
  - NO-MAGNETS : exclude the most extreme-funding coins (the squeeze magnets) before ranking.
Overlays compose. Report IS/OOS Sharpe + full/OOS maxDD to find the DD-vs-Sharpe sweet spot.
All overlays are past-only (exposure for candle t uses data <= t-1); leak-safe by construction.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
import broad_carry as bc  # noqa: E402
import pair_engine as pe  # noqa: E402

LO0 = pd.Timestamp("2000-01-01")
HI1 = pd.Timestamp("2100-01-01")


def vol_target(net: pd.Series, win: int = 90, cap: float = 3.0) -> pd.Series:
    """Scale by target/trailing_vol; target = IS-median rolling vol. Past-only (vol <= t-1)."""
    rv = net.rolling(win).std().shift(1)
    target = rv[net.index < pe.OOS_CUTOFF].median()        # IS-only target
    exposure = (target / rv).clip(0.0, cap).fillna(0.0)
    return exposure * net


def dd_brake(net: pd.Series, dd_thresh: float = 0.15, floor: float = 0.3) -> pd.Series:
    """De-lever to `floor` while running drawdown from the peak exceeds dd_thresh. Past-only:
    exposure for candle t is set from realized equity through t-1."""
    vals = net.to_numpy()
    exp = np.ones(len(vals))
    eq = 1.0
    peak = 1.0
    for t in range(len(vals)):
        dd = eq / peak - 1.0 if peak > 0 else 0.0          # drawdown realized THROUGH t-1
        exp[t] = floor if dd < -dd_thresh else 1.0
        eq *= (1.0 + exp[t] * vals[t])                     # apply candle at the chosen exposure
        peak = max(peak, eq)
    return pd.Series(exp * vals, index=net.index)


def stats(net: pd.Series) -> dict:
    eq = (1 + net).cumprod()
    is_eq = (1 + net[net.index < pe.OOS_CUTOFF]).cumprod()
    oos_eq = (1 + net[net.index >= pe.OOS_CUTOFF]).cumprod()
    return {
        "is_sh": pe.monthly_sharpe(net, LO0, pe.OOS_CUTOFF),
        "oos_sh": pe.monthly_sharpe(net, pe.OOS_CUTOFF, HI1),
        "dd": float((eq / eq.cummax() - 1).min()),
        "is_dd": float((is_eq / is_eq.cummax() - 1).min()),
        "oos_dd": float((oos_eq / oos_eq.cummax() - 1).min()),
    }


def line(name: str, net: pd.Series) -> None:
    s = stats(net)
    print(f"  {name:28} IS={s['is_sh']:+.2f} OOS={s['oos_sh']:+.2f} | "
          f"maxDD full={s['dd']*100:5.0f}% IS={s['is_dd']*100:5.0f}% OOS={s['oos_dd']*100:5.0f}%")


def main() -> None:
    coins = bc.load_universe()
    book, _ = bc.build_book(coins, frac=0.25)
    base = book["net"]
    book_wide, _ = bc.build_book(coins, frac=0.40)
    wide = book_wide["net"]

    nomag, _ = bc.build_book(coins, frac=0.25, exclude_top_pctl=0.90)
    nomag = nomag["net"]

    print("DRAWDOWN CONTROLS on the broad carry (IS-calibrated, past-only overlays):")
    line("baseline (FRAC=0.25)", base)
    line("wider book (FRAC=0.40)", wide)
    line("no-magnets (excl top 10%)", nomag)
    line("vol-target", vol_target(base))
    line("dd-brake (15%/floor0.3)", dd_brake(base))
    line("wide + dd-brake", dd_brake(wide))
    line("no-magnets + dd-brake", dd_brake(nomag))
    line("wide + no-magnets + brake", dd_brake(
        bc.build_book(coins, frac=0.40, exclude_top_pctl=0.90)[0]["net"]))


if __name__ == "__main__":
    main()
