"""portfolio-iteration-v2 iter-v2-004 — RESIDUAL (BTC-beta-neutralized) cross-sectional momentum.

Literature lead (diary-portfolio-v2/RESEARCH_notes.md): raw XS-mom is weak on crypto, but RESIDUAL
momentum (momentum of the BTC-beta-stripped return) survives OOS with higher Sharpe / fewer crashes.
Directly targets the iter-v2-001 anchor failure: mid-cap directional trend died because it is
BTC-beta-coupled and that beta went dead in 2024-26. Residualizing isolates idiosyncratic relative
strength → dollar-neutral L/S on rank 21-40, via engine_v2.run_book_from_signal.

Judged (OOS HIDDEN) on: IS + EARLY[2021-23]/LATE[2024→cutoff] split, vs the anchor (LATE +1.16) AND
vs RAW XS-mom (the non-residual sibling — does residualization actually add?). Pre-registered gates:
  G2 (load-bearing): resmom LATE > anchor LATE (+1.16) by >= +0.20.
  Gbeat: resmom LATE > raw XS-mom LATE (the residualization must earn its keep).
  G3 (cost): the LATE lift survives 2x-taker AND slip_pessimistic (rank-churn is the binding risk).

Run from worktree root:  uv run python analysis/portfolio_v2/iter_v2_004_resmom.py [--reveal]
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
os.chdir(_ROOT)
sys.path.insert(0, str(_ROOT / "analysis"))

import pandas as pd  # noqa: E402

from portfolio_v2 import engine_v2 as e2  # noqa: E402
from portfolio_v2 import resmom_v2 as rm  # noqa: E402
from portfolio_v2 import universe_v2 as uv  # noqa: E402
from portfolio_v2.diag_v2_001 import per_year_sharpe, slip_pessimistic  # noqa: E402

REVEAL = "--reveal" in sys.argv
EARLY_LO, EARLY_HI = pd.Timestamp("2021-01-01"), pd.Timestamp("2024-01-01")
LATE_LO, LATE_HI = pd.Timestamp("2024-01-01"), e2.OOS_CUTOFF


def era(net: pd.Series) -> tuple[float, float]:
    return e2.msharpe(net, EARLY_LO, EARLY_HI), e2.msharpe(net, LATE_LO, LATE_HI)


def line(label: str, res: dict, *, show_oos: bool = False) -> None:
    net = res["net"]
    e_, l_ = era(net)
    is_ = e2.msharpe(net, e2.LO0, e2.OOS_CUTOFF)
    oos = f"  OOS={e2.msharpe(net, e2.OOS_CUTOFF, e2.HI1):+.2f}" if (show_oos and REVEAL) else ""
    print(
        f"  {label:30} IS={is_:+.2f}  EARLY={e_:+.2f}  LATE={l_:+.2f}  "
        f"turn={res['turnover']:.3f}  aPos={res['avg_positions']:.1f}{oos}"
    )
    print(f"     per-year={per_year_sharpe(net)}")


def main() -> None:
    print("=" * 100)
    print("iter-v2-004 — RESIDUAL (BTC-beta) cross-sectional momentum, rank 21-40 (OOS hidden)")
    print("=" * 100)
    pool = uv.load_pool_pit()
    print(f"[pool] {len(pool)} coins (BTC present: {'BTCUSDT' in pool})")

    # anchor reference
    anc = e2.run_book(pool, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=e2.default_slip_bps)
    line("anchor (trend+carry λ)", anc)
    anc_e, anc_l = era(anc["net"])

    def run_signal(sig, **kw):
        return e2.run_book_from_signal(
            pool, sig, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=e2.default_slip_bps, **kw
        )

    # RAW XS-mom (non-residual sibling) as the does-residualization-add baseline (L=84)
    from portfolio_v2.engine_v2 import _xsmom  # noqa: E402

    panel = e2.build_panel(pool)
    elig = (
        uv.eligibility(pool, 20, 40, 168)
        .reindex(index=panel["opens"].index, columns=panel["cols"])
        .fillna(False)
    )
    raw_xs, _ = _xsmom(panel["close"], elig, 84)
    line("RAW xs-mom L=84 (baseline)", run_signal(raw_xs))

    # RESIDUAL momentum sweep over lookback + beta window
    print("\n[residual-momentum sweep]")
    best = None
    for lb in (42, 84, 126):
        for bw in (45, 90):
            sig = rm.resmom_signal(
                pool, rank_lo=20, rank_hi=40, season=168, lookback=lb, beta_win=bw
            )
            res = run_signal(sig)
            _, late_s = era(res["net"])
            line(f"resmom L={lb} betaWin={bw}", res)
            if best is None or late_s > best[0]:
                best = (late_s, lb, bw, sig, res)

    # cost stress on the best LATE candidate
    late_s, lb, bw, sig, res = best
    print(
        f"\n[best LATE] resmom L={lb} betaWin={bw}: LATE={late_s:+.2f} (anchor LATE {anc_l:+.2f})"
    )
    line("  default slip", res, show_oos=True)
    line("  2x taker", run_signal(sig, cost_mult=2.0), show_oos=True)
    line("  2x slip", run_signal(sig, slip_mult=2.0))
    line(
        "  pessimistic slip",
        e2.run_book_from_signal(
            pool, sig, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=slip_pessimistic
        ),
        show_oos=True,
    )

    # gate read (IS + LATE only)
    print("\n[gate read — IS + LATE only, OOS not consulted]")
    print(f"  anchor LATE={anc_l:+.2f}  |  best resmom LATE={late_s:+.2f}  ΔLATE={late_s - anc_l:+.2f}")
    print(f"  G2 (ΔLATE >= +0.20): {'PASS' if (late_s - anc_l) >= 0.20 else 'FAIL'}")


if __name__ == "__main__":
    main()
