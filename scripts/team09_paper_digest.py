#!/usr/bin/env python3
"""One-screen observational digest for the Team 09 paper desk."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Team 09 paper performance digest")
    parser.add_argument(
        "--paper-dir",
        type=Path,
        default=ROOT / "paper-team09",
    )
    args = parser.parse_args()
    paper = args.paper_dir.resolve()
    integrity = json.loads((paper / "integrity.json").read_text(encoding="utf-8"))
    latest = json.loads((paper / "latest-boundary.json").read_text(encoding="utf-8"))
    gates = pd.read_csv(paper / "gates.csv").iloc[-1]
    positions = pd.read_csv(paper / "current_positions.csv")

    longs = positions.loc[positions["weight"] > 0].nlargest(5, "weight")
    shorts = positions.loc[positions["weight"] < 0].nsmallest(5, "weight")
    print("=== Team 09 exact-replay paper desk — observational digest ===")
    print(
        f"boundary {integrity['boundary']}  integrity={integrity['status']}  "
        f"append={integrity['append_invariance']}"
    )
    print(
        f"forward bars={int(gates['observations'])} "
        f"days={int(gates['daily_observations'])} status={gates['status']}  "
        f"cum={float(gates['cumulative_return']):+.2%}  "
        f"daily-annualized Sharpe={float(gates['net_sharpe']):+.2f}  "
        f"maxDD={float(gates['max_drawdown']):.2%}"
    )
    print(
        f"book {len(positions)} names  gross={positions['weight'].abs().sum():.4f}  "
        f"net={positions['weight'].sum():+.4f}  risk_scale={latest['risk_scale']:.4f}"
    )
    print(
        "longs "
        + ", ".join(
            f"{row.symbol}:{row.weight:+.4f}" for row in longs.itertuples()
        )
    )
    print(
        "shorts "
        + ", ".join(
            f"{row.symbol}:{row.weight:+.4f}" for row in shorts.itertuples()
        )
    )
    print(
        f"modeled equity=${latest['modeled_equity_after_execution']:,.2f} "
        "(canonical $100k replay; PAPER ONLY)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
