#!/usr/bin/env python
"""Quantstats tearsheets for every CUP-50 v2 desk, over in-sample, sealed, and the full window.

Three windows per desk, twelve reports. The split matters more than the numbers: the in-sample
window is what the team could see while it worked, the sealed window is what it could not, and the
full window is the two stitched together. Reading them side by side is the only way to see whether
a lane's edge survived the boundary or merely spanned it.

These are analysis artifacts, not tournament evidence. The scored result is the leaderboard; a
tearsheet is a lens on the same returns, computed by a third-party library with its own
conventions. Where quantstats and the tournament's own cell disagree on a number, the tournament's
definition is the one that ranked the field.
"""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import pandas as pd

from crypto_trade.cup50v2.config import OOS_START
from crypto_trade.cup50v2_desk.authority import repository_root

DESKS = ("winner", "runner-up-1", "runner-up-2", "ensemble-eq3")
WINDOWS = ("in_sample", "sealed", "full")


def _returns(paper: Path) -> pd.Series:
    frame = pd.read_parquet(paper / "ledger" / "historical_daily_returns.parquet")
    series = pd.Series(
        frame["net_return"].to_numpy(dtype=float),
        index=pd.DatetimeIndex(frame["date"]),
        name="return",
    )
    if series.index.tz is None:
        series.index = series.index.tz_localize("UTC")
    return series.sort_index()


def _slice(series: pd.Series, window: str) -> pd.Series:
    if window == "in_sample":
        return series[series.index < OOS_START]
    if window == "sealed":
        return series[series.index >= OOS_START]
    return series


def _summary(series: pd.Series) -> dict[str, float | int]:
    if series.empty:
        return {"days": 0}
    equity = (1.0 + series).cumprod()
    peak = equity.cummax()
    years = len(series) / 365.0
    volatility = float(series.std(ddof=1) * (365.0 ** 0.5))
    return {
        "days": int(len(series)),
        "total_return": round(float(equity.iloc[-1] - 1.0), 6),
        "cagr": round(float(equity.iloc[-1] ** (1.0 / years) - 1.0), 6) if years > 0 else 0.0,
        "annualised_volatility": round(volatility, 6),
        "sharpe": round(float(series.mean() / series.std(ddof=1) * (365.0 ** 0.5)), 4)
        if series.std(ddof=1) > 0
        else 0.0,
        "max_drawdown": round(float((equity / peak - 1.0).min()), 6),
        "hit_rate": round(float((series > 0).mean()), 4),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--output", default="reports-cup50v2/quantstats")
    arguments = parser.parse_args()
    root = Path(arguments.root).resolve() if arguments.root else repository_root()
    destination = root / arguments.output
    destination.mkdir(parents=True, exist_ok=True)

    import quantstats as qs

    index = {}
    for desk_id in DESKS:
        paper = root / "paper-cup50v2" / desk_id
        ledger = paper / "ledger" / "historical_daily_returns.parquet"
        if not ledger.is_file():
            print(f"{desk_id}: no return series yet; run cup50v2_reconstruct_desks.py first")
            continue
        team = json.loads((paper / "desk.json").read_text())["team_id"]
        series = _returns(paper)
        index[desk_id] = {"team_id": team, "windows": {}}
        for window in WINDOWS:
            piece = _slice(series, window)
            summary = _summary(piece)
            index[desk_id]["windows"][window] = summary
            if piece.empty:
                continue
            report = destination / f"{desk_id}_{window}.html"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                qs.reports.html(
                    piece,
                    output=str(report),
                    title=f"CUP-50 v2 {desk_id} ({team}) — {window.replace('_', ' ')}",
                    download_filename=str(report),
                )
            print(
                f"{desk_id:<14} {window:<10} {summary['days']:>5}d  "
                f"sharpe {summary['sharpe']:+.2f}  "
                f"cagr {summary['cagr']:+.4f}  maxDD {summary['max_drawdown']:+.4f}",
                flush=True,
            )
    (destination / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    print(f"\nwrote {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
