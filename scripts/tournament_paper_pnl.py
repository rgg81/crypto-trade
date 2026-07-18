"""crypto-cup-01 paper-desk PnL — scored through the tournament evaluator's exact cost model.

The desk holds `strategy_tournament.position_weight_book(...)` rows by construction, so the
honest paper PnL is the evaluator's own net_series over the paper window (taker + liquidity
slippage + native funding + vol-target already folded into the book's scale). Recompute-from-
data architecture: no DB state is trusted for scoring; the DB is only reconciled by the
healthcheck.

  uv run python scripts/tournament_paper_pnl.py [--start 2026-07-18]
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "analysis"))

from portfolio_tournament import constants as tc  # noqa: E402
from portfolio_tournament import engine as te  # noqa: E402
from portfolio_tournament import protocol as tp  # noqa: E402

from crypto_trade.portfolio import strategy_tournament as st  # noqa: E402

DESK_T0 = "2026-07-18"  # paper-desk launch date (quarantine 2026-07-01..T0 stays unscored)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=DESK_T0)
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
    hi = net.index.max() + pd.Timedelta(hours=8)
    m = te.evaluate(net, w, parts, lo=lo, hi=hi)
    s = net[net.index >= lo]
    eq = float((1 + s).cumprod().iloc[-1] - 1) if len(s) else 0.0
    print(f"paper window {lo.date()} -> {net.index.max()} ({len(s)} candles, {m.n_months} months)")
    print(f"  net return {eq * 100:+.2f}%  sharpe {m.sharpe:+.3f}  maxDD {m.maxdd * 100:.1f}%")
    breadth = f"{m.median_names_long:.0f}/{m.median_names_short:.0f}"
    print(f"  ann_turnover {m.ann_turnover:.1f}  breadth {breadth}")
    print(f"  funding_pnl {m.total_funding_pnl:+.4f}  cost {m.total_cost:.4f}")
    gross = float(w.iloc[-1].abs().sum())
    print(f"  last-candle gross {gross:.3f}  net {float(w.iloc[-1].sum()):+.3f}")


if __name__ == "__main__":
    main()
