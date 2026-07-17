"""tradfi-cup-01 winner paper desk — second TradfiPaperEngine instance for team-10.

Subclasses the proven ``live_tradfi.TradfiPaperEngine`` and overrides ONLY the book source:
``_settled_book`` computes the tournament winner's book through the SAME machinery Stage 2
used — ``holdout.load_holdout_coins`` (frozen-IS canon + return-chained fresh/spliced tail)
→ ``engine.panels_with_volume`` → the frozen ``build_raw_weights`` → ``engine.net_series``
(organizer caps + lag + cost + vol-target). The winner bundle's SHA-256s are re-verified
against ``submission.json`` at construction AND before every book recompute — a post-freeze
edit of the deployed strategy halts the desk instead of silently trading a mutated book.

Everything else (dual PARITY/LIVE tracks, perp+funding marks, quantization, settled-bar
discipline, state store, digest) is inherited unchanged. Separate DB / equity CSV / staggered
refresh keep this desk fully isolated from the incumbent iter-016 desk.

Launch:  PYTHONUNBUFFERED=1 uv run python run_tradfi_tournament_paper.py
Smoke:   uv run python run_tradfi_tournament_paper.py --once   (one settled-book recompute)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

import core_tradfi as ct  # noqa: E402
from live_tradfi import TradfiPaperConfig, TradfiPaperEngine  # noqa: E402
from tournament import constants as tc  # noqa: E402
from tournament import engine as te  # noqa: E402
from tournament import holdout as thold  # noqa: E402
from tournament import protocol as tp  # noqa: E402

WINNER_TEAM = "team-10"


@dataclass(frozen=True)
class TournamentPaperConfig(TradfiPaperConfig):
    db_path: str = str(ct._ROOT / "data" / "tradfi_tournament_paper.db")
    equity_csv: str = str(ct._ROOT / "data" / "tradfi_tournament_equity.csv")
    refresh_interval_seconds: int = 2100  # staggered vs the incumbent desk's 1800
    winner_team: str = WINNER_TEAM


class TournamentPaperEngine(TradfiPaperEngine):
    """Winner desk: identical plumbing, tournament-winner book source."""

    def __init__(self, cfg: TournamentPaperConfig) -> None:
        super().__init__(cfg)
        self._team_dir = tc.team_dir(cfg.winner_team)
        tp.check_submission_shas(self._team_dir)  # frozen-bundle integrity at startup
        print(f"[tournament-desk] winner bundle SHA-verified: {cfg.winner_team}", flush=True)

    def _settled_book(self) -> tuple[pd.Series | None, pd.DataFrame | None, pd.Timestamp | None]:
        """(net, deployed_w, as_of) for the WINNER's book on the settled spliced panel.

        Same construction as Stage 2 (frozen-IS canon; fresh tail return-chained; 2026 tail on
        the perp), truncated to bars whose UTC date < today so no unsettled bar enters. PARITY
        net = funding-off 1x-cost vol-targeted series (funding/quantization live in the
        inherited LIVE track, unchanged).
        """
        tp.check_submission_shas(self._team_dir)
        coins = thold.load_holdout_coins(
            data_dir=self.cfg.data_dir, live_data_dir=self.cfg.live_data_dir
        )
        today_ms = self._today_ms()
        coins = {s: d[d.index < today_ms] for s, d in coins.items() if len(d[d.index < today_ms])}
        if not coins or all(s == tc.VIX_SYM for s in coins):
            return None, None, None
        pn = te.panels_with_volume(coins)
        mod = tp.load_strategy(self._team_dir)
        raw = te.conform_raw(mod.build_raw_weights(te.team_view(pn), te.make_aux(coins)), pn)
        tp.purge_team_modules()
        net, w = te.net_series(raw, pn["ret_fwd"])
        return net, w, w.index[-1]
