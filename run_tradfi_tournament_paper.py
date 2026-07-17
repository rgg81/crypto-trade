"""Launcher — tradfi-cup-01 WINNER paper desk (team-10, per-name 12m sign trend).

Second desk instance; fully isolated from the incumbent iter-016 desk (own DB
data/tradfi_tournament_paper.db, own equity CSV, staggered refresh cadence).

Run:    PYTHONUNBUFFERED=1 uv run python run_tradfi_tournament_paper.py \
            > logs/tradfi_tournament_paper.log 2>&1 &
Smoke:  uv run python run_tradfi_tournament_paper.py --once
"""

from __future__ import annotations

import sys
from pathlib import Path

_TRADFI = Path(__file__).resolve().parent / "analysis" / "portfolio" / "tradfi"
if str(_TRADFI) not in sys.path:
    sys.path.insert(0, str(_TRADFI))

from tournament.paper import TournamentPaperConfig, TournamentPaperEngine  # noqa: E402


def main() -> None:
    engine = TournamentPaperEngine(TournamentPaperConfig())
    if "--once" in sys.argv:  # smoke: one settled-book recompute, no loop, no state writes
        net, w, as_of = engine._settled_book()
        if w is None:
            print("[once] no settled data")
            return
        row = w.loc[as_of]
        active = row[row.abs() > 1e-9]
        print(
            f"[once] as_of={as_of.date()}  active_names={len(active)}  "
            f"gross={row.abs().sum():.3f}  net={row.sum():+.3f}"
        )
        print(f"[once] top longs : {active.nlargest(3).round(4).to_dict()}")
        print(f"[once] top shorts: {active.nsmallest(3).round(4).to_dict()}")
        print(f"[once] parity net tail Sharpe-ready rows: {len(net)}")
        return
    engine.run()


if __name__ == "__main__":
    main()
