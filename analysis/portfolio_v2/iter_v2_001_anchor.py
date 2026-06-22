"""portfolio-iteration-v2 iter-v2-001 — ANCHOR.

Port the v1 trend+carry+band+eligexit stack to rank 21-40 on the survivorship-safe PIT universe
with liquidity-scaled slippage. Three reference points (NO new factor — this is the foundation
iteration):

  1. v1 INFLATED   — engine_v2 v1-compat (survivor pool, top-20, season=None, slip=0). Published
                     v1 number; reproduces iter_021 K=2 (parity-gated). Shown as the upper bound.
  2. v1 HONEST     — top-20 on the corrected PIT pool (season=168) + slippage. The de-inflated v1
                     benchmark v2 must actually be compared against.
  3. v2 ANCHOR     — rank 21-40 on the same corrected PIT pool + slippage. The v2 starting baseline.

Plus: the survivorship diagnostic (candidate count per year — must GROW toward 2026 under PIT) and
slippage/cost sensitivity on the v2 anchor.

Run from the worktree root:  uv run python analysis/portfolio_v2/iter_v2_001_anchor.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
os.chdir(_ROOT)  # so pf_data/... resolves from the worktree root
sys.path.insert(0, str(_ROOT / "analysis"))

from portfolio_v2 import engine_v2 as e2  # noqa: E402
from portfolio_v2 import universe_v2 as uv  # noqa: E402


def summary(net: pd.Series) -> dict:
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    oos = net[net.index >= e2.OOS_CUTOFF]
    oeq = (1 + oos).cumprod()
    odd = float((oeq / oeq.cummax() - 1).min()) if len(oos) else float("nan")
    yr = {int(k): round(v * 100) for k, v in net.groupby(net.index.year).sum().items()}
    return {
        "IS": e2.msharpe(net, e2.LO0, e2.OOS_CUTOFF),
        "OOS": e2.msharpe(net, e2.OOS_CUTOFF, e2.HI1),
        "maxDD": dd * 100,
        "oosDD": odd * 100,
        "netTot": (eq.iloc[-1] - 1) * 100,
        "yr": yr,
    }


def line(label: str, res: dict) -> None:
    s = summary(res["net"])
    print(
        f"  {label:24} IS={s['IS']:+.2f} OOS={s['OOS']:+.2f} "
        f"maxDD={s['maxDD']:4.0f}% oosDD={s['oosDD']:4.0f}% "
        f"netTot={s['netTot']:+5.0f}%  avgPos={res['avg_positions']:4.1f} "
        f"turn={res['turnover']:.3f} tick={res['tickets']:4.1f}"
    )
    print(f"     net%/yr={s['yr']}")


def main() -> None:
    print("=" * 100)
    print("iter-v2-001 ANCHOR — rank 21-40 L/S, survivorship-safe PIT universe + slippage")
    print("=" * 100)

    # ---- 1. v1 INFLATED (upper bound; survivor pool, top-20, no slippage) ----
    pool_v1 = uv.load_pool_v1compat()
    print(f"\n[pools] v1-compat survivor pool: {len(pool_v1)} coins")
    r_infl = e2.run_book(pool_v1, rank_lo=0, rank_hi=20, season=None, slip_bps_fn=None)

    # ---- 2 & 3 on the corrected PIT pool ----
    pool_pit = uv.load_pool_pit()
    print(f"[pools] PIT survivorship-safe pool: {len(pool_pit)} coins (no lifetime filter)")

    # survivorship diagnostic — eligible-rank count per year must GROW toward 2026 under PIT
    cc = uv.candidate_count_per_year(pool_pit, season=168)
    print(
        "\n[survivorship diagnostic] mean #seasoned-ranked candidates per year (PIT, season=168):"
    )
    print("   " + "  ".join(f"{int(y)}:{v:.0f}" for y, v in cc.items()))
    cc_v1 = uv.candidate_count_per_year(pool_v1, season=None)
    print("   (v1 survivor-snapshot for contrast):")
    print("   " + "  ".join(f"{int(y)}:{v:.0f}" for y, v in cc_v1.items()))

    r_hon = e2.run_book(
        pool_pit, rank_lo=0, rank_hi=20, season=168, slip_bps_fn=e2.default_slip_bps
    )
    r_anc = e2.run_book(
        pool_pit, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=e2.default_slip_bps
    )

    print("\n[results]")
    line("v1 INFLATED (top20,no-slip)", r_infl)
    line("v1 HONEST  (top20,PIT,slip)", r_hon)
    line("v2 ANCHOR  (21-40,PIT,slip)", r_anc)

    # ---- slippage / cost sensitivity on the v2 anchor ----
    print("\n[v2-anchor sensitivity]")
    r_noslip = e2.run_book(pool_pit, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=None)
    r_slip2 = e2.run_book(
        pool_pit, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=e2.default_slip_bps, slip_mult=2.0
    )
    r_cost2 = e2.run_book(
        pool_pit, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=e2.default_slip_bps, cost_mult=2.0
    )
    line("anchor no-slip (taker only)", r_noslip)
    line("anchor 2x-slip", r_slip2)
    line("anchor 2x-taker", r_cost2)

    print(
        "\n[verdict scaffold] v2 anchor vs de-inflated v1 (both PIT+slip) is the honest comparison;"
    )
    print("  the INFLATED row is the survivorship upper bound (parity-gated to iter_021 K=2).")


if __name__ == "__main__":
    main()
