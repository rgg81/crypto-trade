#!/usr/bin/env python
"""Forward observation across the four CUP-50 v2 desks.

Reports the record and only the record. There is no ranking and no "leader": the capital rule is
pre-registered, read once after 183 official days, and naming a leader every week is how a
six-month experiment quietly becomes a series of one-week decisions.

Two things this script is careful about, because getting either wrong misreports performance in a
direction nobody would question:

*Bars are not days.* The ledger holds one row per 8h decision, three per day. Counting rows as days
reported "64 days" for desks that had been live for hours, and then annualised by 365 on top of it.
Everything here compounds to UTC days first, so a number means what it means in the tournament's
own cells.

*Bridge is not official.* forward_returns.parquet begins when the sealed window ends, not when the
desk launched, so its early rows are real out-of-sample data that existed before the desk went
live. Only the official phase is the forward record, and only official days count toward the
capital rule. Adding the two together would credit a desk with performance it never traded.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

DESKS = ("winner", "runner-up-1", "runner-up-2", "ensemble-eq3")

# Below this many official days an annualised figure is extrapolation, not measurement: one day of
# +1.2% annualises to +442%. Total return and drawdown are honest from the first day; growth,
# volatility and anything derived from them are withheld until there is enough sample to mean
# something. A number that looks like a result is worse than no number.
MINIMUM_DAYS_FOR_ANNUALISED = 20


def _utc(value: object) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    return stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")


def _daily(frame: pd.DataFrame) -> pd.Series:
    series = pd.Series(
        frame["net_return"].to_numpy(dtype=float),
        index=pd.DatetimeIndex(frame["decision_time"]),
    )
    return (1.0 + series).groupby(series.index.normalize()).prod() - 1.0


def _statistics(series: pd.Series) -> dict[str, object]:
    if series.empty:
        return {"days": 0}
    equity = (1.0 + series).cumprod()
    peak = equity.cummax()
    ruined = float(equity.iloc[-1]) <= 0.0
    return {
        "days": int(len(series)),
        "total_return": round(float(equity.iloc[-1] - 1.0), 6),
        "annualised_growth": None
        if ruined
        else round(float((365.0 / len(series)) * np.log1p(series.to_numpy()).sum()), 6),
        "annualised_volatility": round(float(series.std(ddof=0) * (365.0**0.5)), 6),
        "max_drawdown": round(float((equity / peak - 1.0).min()), 6),
    }


def desk_record(paper_root: Path, desk_id: str) -> dict[str, object] | None:
    ledger = paper_root / desk_id / "ledger" / "forward_returns.parquet"
    if not ledger.is_file():
        return None
    frame = pd.read_parquet(ledger)
    if frame.empty or "net_return" not in frame.columns:
        return None
    phases: dict[str, dict[str, object]] = {}
    for name in ("official", "bridge"):
        piece = frame[frame["phase"] == name] if "phase" in frame.columns else frame
        phases[name] = _statistics(_daily(piece)) if len(piece) else {"days": 0}
    return {"desk": desk_id, "official": phases["official"], "bridge": phases["bridge"]}


def capital_rule(paper_root: Path, now: pd.Timestamp, minimum_days: int) -> dict[str, object]:
    launch_file = paper_root / "launch.json"
    if not launch_file.is_file():
        return {"status": "NOT-LAUNCHED"}
    launch = _utc(json.loads(launch_file.read_text())["launch"])
    days = (now - launch).total_seconds() / 86400.0
    return {
        "status": "ACCRUING" if days < minimum_days else "DECIDABLE",
        "official_days": round(days, 1),
        "minimum_days": minimum_days,
    }


def _line(desk: str, stats: dict[str, object]) -> str:
    head = (
        f"{stats['days']:>4}d  total {float(stats['total_return']):+.4f}  "
        f"maxDD {float(stats['max_drawdown']):+.4f}"
    )
    if int(stats["days"]) < MINIMUM_DAYS_FOR_ANNUALISED:
        return f"{head}  (annualised figures withheld until {MINIMUM_DAYS_FOR_ANNUALISED}d)"
    growth = stats["annualised_growth"]
    rendered = "RUINED" if growth is None else format(float(growth), "+.4f")
    return f"{head}  growth {rendered}  vol {float(stats['annualised_volatility']):.4f}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--minimum-days", type=int, default=183)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    root = Path(arguments.root).resolve() if arguments.root else Path(__file__).resolve().parents[1]
    paper_root = root / "paper-cup50v2"
    now = pd.Timestamp.now(tz="UTC")

    rows = [record for desk in DESKS if (record := desk_record(paper_root, desk)) is not None]
    capital = capital_rule(paper_root, now, arguments.minimum_days)
    if arguments.json:
        print(json.dumps({"capital": capital, "desks": rows}, sort_keys=True))
        return 0
    if capital["status"] == "NOT-LAUNCHED":
        print("desks not launched")
        return 0
    print(f"CUP-50 v2 forward observation ({capital['official_days']:.1f} days since launch)")
    if not rows:
        print("  no desk has published a forward return yet")
        return 0
    for row in rows:
        official, bridge = row["official"], row["bridge"]
        if official["days"]:
            print(f"  {row['desk']:<14} official {_line(row['desk'], official)}")
        else:
            extra = (
                f"  (bridge {bridge['days']}d total {float(bridge['total_return']):+.4f})"
                if bridge["days"]
                else ""
            )
            print(f"  {row['desk']:<14} official    0d  no settled boundary yet{extra}")
    print("  bridge = between the sealed window ending and launch; NOT the forward record and")
    print("  not counted by the capital rule, which reads official days only")
    print("  (no ranking by design -- the capital rule is read once, after 183 official days)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
