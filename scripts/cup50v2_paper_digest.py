#!/usr/bin/env python
"""Forward observation across the four CUP-50 v2 desks.

Reports the record, and only the record. There is no ranking in the output and no "leader": the
capital rule is pre-registered, read once after 183 official days, and naming a leader every week
is how a six-month experiment quietly turns into a series of one-week decisions.

Each desk's numbers are computed the same way the tournament computes a cell, so a forward number
and an in-sample number mean the same thing when they are eventually compared.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

DESKS = ("winner", "runner-up-1", "runner-up-2", "ensemble-eq3")


def _utc(value: object) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    return stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")


def desk_record(paper_root: Path, desk_id: str) -> dict[str, object] | None:
    """Forward returns only. The historical series sits beside this one and is not the record.

    ledger/forward_returns.parquet is what the desk has produced since launch. The reconstruction
    also wrote ledger/historical_daily_returns.parquet, which is the pre-launch replay used for
    the tearsheets -- mixing the two would report the tournament's own window as forward
    performance, which is the single most misleading thing this script could do.
    """
    ledger = paper_root / desk_id / "ledger" / "forward_returns.parquet"
    if not ledger.is_file():
        return None
    frame = pd.read_parquet(ledger)
    if frame.empty:
        return None
    if "net_return" not in frame.columns:
        raise ValueError(f"{desk_id}: forward ledger has no net_return column")
    returns = pd.Series(frame["net_return"].to_numpy(dtype=float))
    equity = (1.0 + returns).cumprod()
    peak = equity.cummax()
    drawdown = float((equity / peak - 1.0).min())
    days = len(returns)
    total = float(equity.iloc[-1] - 1.0)
    # Annualised log growth, the tournament's own definition. A day that loses everything makes
    # the log undefined, and an equity path that reaches zero is a failed candidate rather than a
    # number to report, so it is surfaced instead of being quietly dropped.
    if float(equity.iloc[-1]) <= 0.0:
        growth = float("-inf")
    else:
        growth = float((365.0 / max(days, 1)) * float(np.log1p(returns.to_numpy()).sum()))
    volatility = float(returns.std(ddof=0) * (365.0 ** 0.5))
    return {
        "desk": desk_id,
        "days": days,
        "total_return": round(total, 6),
        "annualised_growth": None if growth == float("-inf") else round(growth, 6),
        "annualised_volatility": round(volatility, 6),
        "max_drawdown": round(drawdown, 6),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    root = Path(arguments.root).resolve() if arguments.root else Path(__file__).resolve().parents[1]
    paper_root = root / "paper-cup50v2"

    launch_file = paper_root / "launch.json"
    launch = _utc(json.loads(launch_file.read_text())["launch"]) if launch_file.is_file() else None
    rows = [record for desk in DESKS if (record := desk_record(paper_root, desk)) is not None]

    if arguments.json:
        print(json.dumps({"launch": launch.isoformat() if launch else None, "desks": rows},
                         sort_keys=True))
        return 0
    if launch is None:
        print("desks not launched")
        return 0
    print(f"CUP-50 v2 forward observation since {launch.date()}")
    if not rows:
        print("  no desk has published a forward return yet")
        return 0
    for row in rows:
        growth = row["annualised_growth"]
        rendered = "RUINED" if growth is None else format(growth, "+.4f")
        print(
            f"  {row['desk']:<14} {row['days']:>4}d  "
            f"total {row['total_return']:+.4f}  "
            f"growth {rendered}  "
            f"vol {row['annualised_volatility']:.4f}  "
            f"maxDD {row['max_drawdown']:+.4f}"
        )
    print("  (no ranking by design -- the capital rule is read once, after 183 official days)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
