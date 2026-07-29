"""crypto-cup-01 paper-desk PnL digest — scored through the tournament evaluator's cost model.

The desk holds `strategy_tournament.position_weight_book(...)` rows by construction, so the
honest paper PnL is the evaluator's own net_series over the paper window (taker + liquidity
slippage + native funding + vol-target already folded into the book's scale). Recompute-from-
data architecture: no DB state is trusted for scoring; the DB is only reconciled by the
healthcheck.

Prints an accumulated-PnL DIGEST (equity, cum $/%, drawdown, exposure) as the headline plus a
trailing-24h delta, so the monitor tick can surface running P&L at a glance every cycle.

  uv run python scripts/tournament_paper_pnl.py [--start 2026-07-18] [--equity 10000]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "analysis"))

from portfolio_tournament import constants as tc  # noqa: E402
from portfolio_tournament import engine as te  # noqa: E402
from portfolio_tournament import protocol as tp  # noqa: E402

from crypto_trade.portfolio import strategy_tournament as st  # noqa: E402

DESK_T0 = "2026-07-18"  # paper-desk launch date (quarantine 2026-07-01..T0 stays unscored)
DESK_EQUITY = 10_000.0  # matches run_portfolio_tournament_paper.py


def _window_return(net: pd.Series, lo: pd.Timestamp) -> float:
    s = net[net.index >= lo]
    return float((1 + s).cumprod().iloc[-1] - 1) if len(s) else 0.0


def compute_stats(start: str = DESK_T0, equity: float = DESK_EQUITY) -> dict:
    """Recompute the paper book from data and return the digest stats as a dict.

    Single source of truth for both the full digest (this script) and the compact one-liner
    the watchdog prints. SHA-checks the frozen submission first (raises on mutation — an
    integrity failure the caller surfaces). ~20-40s (loads the full-history universe).
    """
    tp.check_submission_shas(st.TEAM_DIR)
    coins = st.load_universe()
    pn, scoring, elig = st._panels(coins)
    mod = tp.load_strategy(st.TEAM_DIR)
    view = {k: pn[k].copy() for k in ("open", "close", "quote_volume")}
    aux = {"eligibility": elig.copy(), "seed": tc.SEED}
    raw = te.conform_raw(mod.build_raw_weights(view, aux), pn)
    tp.purge_team_modules()
    net, w, parts = te.net_series(raw, pn, scoring)

    lo = pd.Timestamp(start)
    last = net.index.max()
    hi = last + pd.Timedelta(hours=8)
    m = te.evaluate(net, w, parts, lo=lo, hi=hi)
    s = net[net.index >= lo]
    cum = _window_return(net, lo)
    d1 = _window_return(net, last - pd.Timedelta(hours=24)) if len(s) else 0.0

    # Decompose net on the DEPLOYED (vol-target-scaled) basis so price + funding − cost ties to
    # ACCUM P&L. parts["pnl"/"fpnl"/"cost"] are PRE-scale (gross≈1); the deployed book is
    # gross≈0.64, so each must be × scale before summing — otherwise funding/cost read on a
    # different basis than the headline and look ~1.6× too large.
    win = (net.index >= lo) & (net.index < hi)
    sc = parts["scale"].reindex(net.index)
    deployed = w.mul(parts["scale"], axis=0).iloc[-1]
    return {
        "start": lo.date(),
        "last": last,
        "days": (last - lo).total_seconds() / 86400 if len(s) else 0.0,
        "n_candles": len(s),
        "accum_pct": cum * 100,
        "accum_usd": equity * cum,
        "equity": equity * (1 + cum),
        "d1_pct": d1 * 100,
        "maxdd_pct": m.maxdd * 100,
        "sharpe": f"{m.sharpe:+.2f}" if np.isfinite(m.sharpe) else "n/a (<2mo)",
        "price_usd": float((parts["pnl"].reindex(net.index) * sc)[win].sum()) * equity,
        "funding_usd": float((parts["fpnl"].reindex(net.index) * sc)[win].sum()) * equity,
        "cost_usd": float((parts["cost"].reindex(net.index) * sc)[win].sum()) * equity,
        "turnover": m.ann_turnover,
        "gross": float(deployed.abs().sum()),
        "net": float(deployed.sum()),
        "n_long": int((deployed > 1e-9).sum()),
        "n_short": int((deployed < -1e-9).sum()),
    }


def oneline(d: dict) -> str:
    """Compact single-line P&L pulse (used by the watchdog)."""
    return (
        f"P&L {d['accum_pct']:+.2f}% (${d['accum_usd']:+,.0f}, eq ${d['equity']:,.0f}) "
        f"24h {d['d1_pct']:+.2f}% maxDD {d['maxdd_pct']:.1f}% | "
        f"price {d['price_usd']:+,.0f} fund {d['funding_usd']:+,.0f} cost {d['cost_usd']:-,.0f} | "
        f"book g{d['gross']:.2f} n{d['net']:+.2f} {d['n_long']}L/{d['n_short']}S"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=DESK_T0)
    ap.add_argument("--equity", type=float, default=DESK_EQUITY)
    args = ap.parse_args()
    d = compute_stats(args.start, args.equity)

    p, f, c = d["price_usd"], d["funding_usd"], d["cost_usd"]
    accum = f"{d['accum_pct']:+.2f}%   ${d['accum_usd']:+,.0f}   equity ${d['equity']:,.0f}"
    decomp = f"price {p:+,.0f}  funding {f:+,.0f}  cost {c:-,.0f}"
    book = f"gross {d['gross']:.3f}  net {d['net']:+.3f}  {d['n_long']}L/{d['n_short']}S"
    print("=== crypto-cup-01 paper desk (team-02 breakout) — PnL digest ===")
    print(f"window {d['start']} → {d['last']}  ({d['days']:.1f}d, {d['n_candles']} candles)")
    print(f"  ACCUM P&L   {accum}")
    print(f"  last 24h    {d['d1_pct']:+.2f}%")
    print(f"  maxDD       {d['maxdd_pct']:.1f}%    sharpe {d['sharpe']}")
    print(f"  decomp $    {decomp}")
    print(f"  turnover    {d['turnover']:.0f}x/yr")
    print(f"  book        {book}")


if __name__ == "__main__":
    main()
