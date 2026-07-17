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


def settled_scaled_book(
    team_dir: Path,
    *,
    today_ms: int,
    data_dir: str | None = None,
    live_data_dir: str | None = None,
) -> tuple[pd.Series | None, pd.DataFrame | None]:
    """(vol-targeted net, VOL-SCALED lagged weight book) for a frozen team bundle on the
    settled spliced panel — the SINGLE code path shared by the desk engine and the monitor.

    Construction matches Stage 2 (frozen-IS canon; fresh tail return-chained; 2026 tail on the
    perp), truncated to bars < ``today_ms``. The returned book carries the portfolio vol-target
    scalar IN THE WEIGHTS (``w_scaled[t] = w[t]·scale[t]``, scale past-only), mirroring the
    incumbent desk convention where held/LIVE weights are the real vol-scaled magnitudes; the
    net series is identical to ``engine.net_series`` output bit-for-bit
    (``net = net_raw·scale``).
    """
    tp.check_submission_shas(team_dir)
    coins = thold.load_holdout_coins(data_dir=data_dir, live_data_dir=live_data_dir)
    coins = {s: d[d.index < today_ms] for s, d in coins.items() if len(d[d.index < today_ms])}
    if not coins or all(s == tc.VIX_SYM for s in coins):
        return None, None
    pn = te.panels_with_volume(coins)
    mod = tp.load_strategy(team_dir)
    raw = te.conform_raw(mod.build_raw_weights(te.team_view(pn), te.make_aux(coins)), pn)
    tp.purge_team_modules()
    w = te.normalize_and_cap(raw).shift(1)
    pnl = (w * pn["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
    cost = tc.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    net_raw = (pnl - cost).dropna()
    scale = ct.vol_target_scale(net_raw)
    net = net_raw * scale  # == ct.vol_target(net_raw) == engine.net_series() net
    w_scaled = w.mul(scale.reindex(w.index).fillna(0.0), axis=0)
    return net, w_scaled


class TournamentPaperEngine(TradfiPaperEngine):
    """Winner desk: identical plumbing, tournament-winner book source (vol-scaled)."""

    def __init__(self, cfg: TournamentPaperConfig) -> None:
        super().__init__(cfg)
        self._team_dir = tc.team_dir(cfg.winner_team)
        tp.check_submission_shas(self._team_dir)  # frozen-bundle integrity at startup
        print(f"[tournament-desk] winner bundle SHA-verified: {cfg.winner_team}", flush=True)

    def _settled_book(self) -> tuple[pd.Series | None, pd.DataFrame | None, pd.Timestamp | None]:
        """(net, VOL-SCALED deployed_w, as_of) for the WINNER's settled book — held, PARITY
        and LIVE tracks all derive from this one source (funding/quantization inherited)."""
        net, w_scaled = settled_scaled_book(
            self._team_dir,
            today_ms=self._today_ms(),
            data_dir=self.cfg.data_dir,
            live_data_dir=self.cfg.live_data_dir,
        )
        if w_scaled is None:
            return None, None, None
        return net, w_scaled, w_scaled.index[-1]

    def _target_weights(self, as_of: pd.Timestamp, deployed_w: pd.DataFrame) -> dict:
        """Held book = the winner's vol-scaled row held DURING ``as_of`` (same source as the
        LIVE track — no independent recompute needed; parity is checked by the monitor)."""
        row = deployed_w.loc[as_of]
        out = {t: float(v) for t, v in row.items() if abs(float(v)) > 1e-12}
        out["_meta"] = {
            "as_of": as_of,
            "gross": float(row.abs().sum()),
            "net_dollar": float(row.sum()),
            "n_names": len(out),
            "scaled": True,
        }
        return out
