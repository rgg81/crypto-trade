"""PRISTINE one-shot bear validation — the FROZEN iter-008 champion on the 2008 GFC metals crash.

The iter-008 champion's all-weather win was selected with the 2011-2015 bear visible across the
exploration, so that bear is CORROBORATING, not a clean OOS (Critic: PROMOTE-BOOTSTRAP). This script
runs the FROZEN champion (zero param changes) on a genuinely-PRISTINE bear never touched during
selection: the **2008 GFC commodity crash** (silver ~$21→$9 = −57%, gold ~$1000→$700; silver crashed
~2× gold → the dispersion long-gold/short-silver bear-edge should fire hard). Dukascopy gold/silver
reach ~2003, so 2008 is available; pt/pd do not (2-metal, like 2011-2015).

DISCIPLINE: champion params are FROZEN literals (win=450, thresh=0.6, a_w=0.5, dW 0.25→1.5; brake
D_trip/D_rearm from the bear-blind iter_007_calibrate; floor=0.25). ONE shot, NO tuning. If the bear
PAYS here too, the 2011-2015 result generalizes → converts BOOTSTRAP toward a clean confirmation.

Run:  uv run python analysis/portfolio/metals/bear_test_2008_pristine.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import ingest_dukascopy as ing  # noqa: E402
import iter_007_allweather as aw  # noqa: E402
import iter_012_cot_ensemble as i12  # noqa: E402
import universe_metals as um  # noqa: E402

DIR_2008 = _HERE.parents[2] / "data_bear2008"
INSTR = {"XAUUSDT": "xauusd", "XAGUSDT": "xagusd"}
START, END = "2006-06-01", "2009-07-01"  # warmup from 2006 (SMA450≈150d) through the recovery

# Evaluation windows over the PRISTINE 2008 crash (never seen during iter-008 selection)
WINDOWS = [
    (
        "2008 crash+recovery 2008-03 → 2009-06",
        pd.Timestamp("2008-03-01"),
        pd.Timestamp("2009-06-01"),
    ),
    (
        "2008 PURE crash      2008-07 → 2008-12",
        pd.Timestamp("2008-07-01"),
        pd.Timestamp("2008-12-01"),
    ),
]


def _ingest() -> None:
    for ticker, inst in INSTR.items():
        out = ing.csv_path(DIR_2008, ticker, "8h")
        if out.exists():
            print(f"  {ticker}: cached")
            continue
        print(f"  {ticker} ← dukascopy {inst} {START}..{END} ...", flush=True)
        with tempfile.TemporaryDirectory(prefix="b2008_") as tmp:
            ing.write_klines(
                out, ing.to_klines(ing.resample_8h(ing.fetch_h1(inst, START, END, tmp)))
            )


def _stats(net: pd.Series, lo: pd.Timestamp, hi: pd.Timestamp) -> tuple[float, float, float]:
    s = net[(net.index >= lo) & (net.index < hi)]
    if len(s) < 2:
        return float("nan"), float("nan"), float("nan")
    eq = (1 + s).cumprod()
    return um.msharpe(s, lo, hi), float((eq / eq.cummax() - 1).min()), float(eq.iloc[-1] - 1)


def main() -> None:
    print("=" * 90)
    print("PRISTINE 2008 BEAR — FROZEN iter-008 champion (never selected on this window)")
    print("=" * 90)
    _ingest()
    coins = um.load_metals(DIR_2008)
    print(
        f"\n  universe {tuple(coins)}  span {next(iter(coins.values())).shape}  (gold/silver only)"
    )

    # FROZEN books: baseline L2+brake vs the CURRENT champion (iter-012, position-level honest net).
    # The iter-008 BINARY regime_book is SUPERSEDED + look-ahead-inflated (do NOT cite +1.25/+3.15);
    # the live champion is iter_012.desk_net (breadth-accel + deadband + gold/silver COT ensemble).
    net0_l2 = aw.book_l2(coins)
    net_base = aw.apply_brake(net0_l2, aw.dd_brake_scalar(net0_l2))  # iter-007 baseline
    net_champ = i12.desk_net(coins)  # iter-012 (what live deploys)

    print(f"\n  {'window':42} {'book':16} {'Sharpe':>7} {'maxDD':>8} {'net%':>7}")
    print("  " + "-" * 84)
    for label, lo, hi in WINDOWS:
        for name, net in (("baseline L2+brake", net_base), ("CHAMPION regime", net_champ)):
            sr, dd, tot = _stats(net, lo, hi)
            print(
                f"  {label if name.startswith('baseline') else '':42} {name:16} "
                f"{sr:>+7.2f} {dd * 100:>7.1f}% {tot * 100:>+6.0f}%"
            )
        print()
    print(
        "  READ (one-shot, no tuning): does the champion bound/pay the PRISTINE 2008 bear like it"
    )
    print("  did the selection-contaminated 2011-2015 bear? If yes → architecture generalizes.")


if __name__ == "__main__":
    main()
