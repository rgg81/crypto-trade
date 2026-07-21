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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=DESK_T0)
    ap.add_argument("--equity", type=float, default=DESK_EQUITY)
    args = ap.parse_args()

    tp.check_submission_shas(st.TEAM_DIR)
    coins = st.load_universe()
    pn, scoring, elig = st._panels(coins)
    mod = tp.load_strategy(st.TEAM_DIR)
    view = {k: pn[k].copy() for k in ("open", "close", "quote_volume")}
    aux = {"eligibility": elig.copy(), "seed": tc.SEED}
    raw = te.conform_raw(mod.build_raw_weights(view, aux), pn)
    tp.purge_team_modules()
    net, w, parts = te.net_series(raw, pn, scoring)

    lo = pd.Timestamp(args.start)
    last = net.index.max()
    hi = last + pd.Timedelta(hours=8)
    m = te.evaluate(net, w, parts, lo=lo, hi=hi)
    s = net[net.index >= lo]

    cum = _window_return(net, lo)
    eq_now = args.equity * (1 + cum)
    d1 = _window_return(net, last - pd.Timedelta(hours=24)) if len(s) else 0.0
    days = (last - lo).total_seconds() / 86400 if len(s) else 0.0
    fund_dollars = m.total_funding_pnl * args.equity if np.isfinite(m.total_funding_pnl) else 0.0
    cost_dollars = m.total_cost * args.equity if np.isfinite(m.total_cost) else 0.0
    sharpe = f"{m.sharpe:+.2f}" if np.isfinite(m.sharpe) else "n/a (<2mo)"

    print("=== crypto-cup-01 paper desk (team-02 breakout) — PnL digest ===")
    print(f"window {lo.date()} → {last}  ({days:.1f}d, {len(s)} candles)")
    print(f"  ACCUM P&L   {cum * 100:+.2f}%   ${args.equity * cum:+,.0f}   equity ${eq_now:,.0f}")
    print(f"  last 24h    {d1 * 100:+.2f}%")
    print(f"  maxDD       {m.maxdd * 100:.1f}%    sharpe {sharpe}")
    turn = f"turnover {m.ann_turnover:.0f}x/yr"
    print(f"  funding     ${fund_dollars:+,.0f}   cost ${cost_dollars:-,.0f}   {turn}")
    # DEPLOYED book = w × vol-target scale (matches the desk log's target_gross), not the
    # pre-scale normalized w (which is gross≈1).
    deployed = w.mul(parts["scale"], axis=0).iloc[-1]
    n_long = int((deployed > 1e-9).sum())
    n_short = int((deployed < -1e-9).sum())
    print(
        f"  book        gross {deployed.abs().sum():.3f}  net {deployed.sum():+.3f}  "
        f"{n_long}L/{n_short}S"
    )


if __name__ == "__main__":
    main()
