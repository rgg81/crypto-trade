"""Diagnostic: do pool and LINK-specialist share trade rosters?

If pool already trades LINK trades that the LINK specialist is ALSO trading,
the bundle math overcounts. The pool of /018 should NOT have any LINK trades
in its roster (LINK is owned by Model C in the baseline; iter-v1/018's brief
should have replaced Model C with the LINK specialist — but the comparison.csv
total trade count of 154 IS / 48 OOS suggests /018 trains a STANDALONE LINK
specialist, NOT a bundle).

What we want to verify:
1. Does iter-v1/018's trades.csv contain ONLY LINKUSDT trades, or does it
   replicate Model A (BTC+ETH) too?
2. Does iter-v1/019's trades.csv contain ONLY ETHUSDT trades?
3. If both specialists are stand-alone (single-symbol), then bundling them
   with the BASELINE pool means: pool already trades the same symbols as
   each specialist. Bundle weights need careful accounting.

This is informational only — the analysis_v1-026 brief flags it; /027's
QE/Critic apply the actual roster-replacement logic.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

REPO_ROOT = Path("/home/roberto/crypto-trade/.worktrees/quant-research")


def trade_symbol_distribution(report_dir: Path, sample: str) -> tuple[Counter[str], int]:
    path = report_dir / sample / "trades.csv"
    syms: Counter[str] = Counter()
    n = 0
    with path.open() as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            syms[row["symbol"]] += 1
            n += 1
    return syms, n


def main() -> None:
    for label, report_dir in (
        ("baseline pool", REPO_ROOT / "reports-v1" / "iteration_v1-baseline"),
        ("LINK specialist (/018)", REPO_ROOT / "reports-v1" / "iteration_v1-018"),
        ("ETH+gate specialist (/019)", REPO_ROOT / "reports-v1" / "iteration_v1-019"),
    ):
        print(f"\n{label}:")
        for sample in ("in_sample", "out_of_sample"):
            syms, n = trade_symbol_distribution(report_dir, sample)
            print(
                f"  {sample:<15} n={n:>4d}  by symbol: "
                + ", ".join(f"{s}={c}" for s, c in syms.most_common())
            )


if __name__ == "__main__":
    main()
