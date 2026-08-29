"""Performance for all four desks, reported apart by phase. Never ranked.

Two distinctions in the ledger are load-bearing:

**Bars are not days.** One row per 8h decision, three per day. Everything here compounds to UTC days
first, so the numbers mean what the tournament's cells mean.

**Bridge is not official.** The ledger begins where the historical window ended, not where the desks
launched, so its early rows are real out-of-sample data that existed before any desk went live. Only
the ``official`` phase is the forward record. They are reported apart, always: adding them would
credit a desk with performance it never traded.

**This is reporting, not ranking.** The desks are printed in a fixed order, never sorted by
performance, and no leader is named. The capital rule is read once, after 365 official days, and the
four-desk design exists precisely because in-sample rank did not predict forward rank. Turning a
routine report into a weekly verdict is that same error arriving by a different route.

Imports ``desk_parity()`` so the performance line and the integrity line cannot disagree about
whether a desk still matches its backtest.

Usage::

    uv run python scripts/top40v5_paper_digest.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.tournament.v5.desk.ledger import read_ledger
from crypto_trade.tournament.v5.desk.parity import desk_parity

REPO = Path(__file__).resolve().parents[1]
PAPER = REPO / "paper-top40v5"
ANNUAL = 365.0


def _daily(rows: pd.DataFrame) -> pd.Series:
    series = pd.Series(
        rows["net_return"].to_numpy(dtype=float), index=pd.to_datetime(rows["boundary"], utc=True)
    )
    return (1.0 + series).resample("1D").prod() - 1.0


def _stats(daily: pd.Series) -> dict[str, float]:
    if len(daily) < 2:
        return {
            "days": len(daily),
            "total": 0.0,
            "cagr": 0.0,
            "vol": 0.0,
            "maxdd": 0.0,
            "sharpe": 0.0,
        }
    equity = (1.0 + daily).cumprod()
    years = max(len(daily) / ANNUAL, 1e-9)
    deviation = float(daily.std(ddof=1))
    return {
        "days": int(len(daily)),
        "total": float(equity.iloc[-1] - 1.0),
        "cagr": float(equity.iloc[-1] ** (1.0 / years) - 1.0),
        "vol": deviation * float(np.sqrt(ANNUAL)),
        "maxdd": float((1.0 - equity / equity.cummax()).max()),
        "sharpe": float(daily.mean() / deviation * np.sqrt(ANNUAL)) if deviation > 0 else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()

    manifest_path = PAPER / "deployment-manifest.json"
    if not manifest_path.is_file():
        print("no deployment manifest; the desks are not deployed")
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    report: dict[str, object] = {}
    for desk in sorted(manifest):
        ledger = read_ledger(PAPER / desk / "ledger" / "forward_returns.parquet")
        parity = desk_parity(PAPER / desk)
        entry: dict[str, object] = {
            "parity": parity.state,
            "verified_through": parity.verified_through,
        }
        if ledger.empty:
            entry["note"] = "no forward returns yet"
        else:
            for phase, subset in (
                ("bridge", ledger[~ledger["official"]]),
                ("official", ledger[ledger["official"]]),
            ):
                entry[phase] = (
                    _stats(_daily(subset)) if not subset.empty else _stats(pd.Series(dtype=float))
                )
        report[desk] = entry

    if arguments.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=float))
        return 0

    for desk in sorted(report):
        entry = report[desk]
        print(f"{desk}")
        print(f"  parity {entry['parity']} through {entry['verified_through'] or '—'}")
        if "note" in entry:
            print(f"  {entry['note']}")
            continue
        for phase in ("official", "bridge"):
            s = entry[phase]
            if not s["days"]:
                print(f"  {phase:9s} no days yet")
                continue
            print(
                f"  {phase:9s} {s['days']:4d}d  total {s['total']:+7.2%}  cagr {s['cagr']:+7.2%}"
                f"  vol {s['vol']:6.2%}  maxdd {s['maxdd']:6.2%}  sharpe {s['sharpe']:+.3f}"
            )
    print("\nreported, not ranked; the capital rule is read once after 365 official days")
    return 0


if __name__ == "__main__":
    sys.exit(main())
