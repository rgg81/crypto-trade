"""Agreement check: fastsim vs the organiser's own evaluate_targets on identical target frames.

No trial is spent: this calls the organiser evaluator directly on a fixed target matrix rather
than through scripts/cup20_evaluate.py, and produces no number of record.
"""
from __future__ import annotations

import sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-12/research")
from panel import Panel
import fastsim as FS
import metricsfast as MF

from crypto_trade.cup20.runner import (
    apply_exposure_caps, apply_risk_scalars, evaluator_config, normalise_unit_gross,
)
from crypto_trade.cup20.risk_unit import common_risk_scalars
from crypto_trade.cup20.metrics import window_metrics
from crypto_trade.tournament.engine_v2 import evaluate_targets
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN
from crypto_trade.cup20.config import load_config

p = Panel()
n, ns = len(p.times), len(p.symbols)
elig = p.eligible[p.t0 : p.t0 + n]

# Test book A: equal-weight long every eligible name, rebalanced every 3rd boundary (daily).
W = np.zeros((n, ns))
rebal = np.zeros(n, dtype=bool)
for i in range(n):
    if i % 3 != 0:
        continue
    rebal[i] = True
    m = elig[i]
    if m.sum():
        W[i, m] = 1.0 / m.sum()

# Test book B: cross-sectional 5/5 long-short on 30-bar momentum, rebalanced every 3rd boundary.
op = p.open[p.t0 - 30 : p.t0 + n]
mom = np.full((n, ns), np.nan)
for i in range(n):
    a, b = op[i], op[i + 30 - 30]  # placeholder
W2 = np.zeros((n, ns))
rebal2 = np.zeros(n, dtype=bool)
closes = p.close
for i in range(n):
    if i % 3 != 0:
        continue
    gi = p.t0 + i
    r = closes[gi - 1] / closes[gi - 91] - 1.0
    m = elig[i] & np.isfinite(r)
    if m.sum() < 10:
        continue
    rebal2[i] = True
    idx = np.where(m)[0]
    order = idx[np.argsort(r[idx])]
    k = 5
    W2[i, order[-k:]] = 1.0 / (2 * k)
    W2[i, order[:k]] = -1.0 / (2 * k)

cfg = evaluator_config(load_config("tournament/cup20/config.toml").raw["execution"])

for label, Wx, rb in (("longonly-EW", W, rebal), ("xs-momentum-5/5", W2, rebal2)):
    t = time.time()
    run = FS.run_book(Wx, rb, p)
    fast_ms = time.time() - t
    fs = MF.scored_vector(run, p, trial_count=2)

    # organiser path on the same requested book
    cols = list(p.symbols)
    df = pd.DataFrame(Wx, index=p.times, columns=cols)
    df[REBALANCE_INSTRUCTION_COLUMN] = rb
    t = time.time()
    req = normalise_unit_gross(df)
    tgt = apply_exposure_caps(req, cfg)
    ref = evaluate_targets(p.snapshot.bars, p.snapshot.funding, p.snapshot.membership, tgt,
                           mark_prices=p.snapshot.mark_prices, config=cfg, cost_multiplier=1.0)
    gr = ref.returns["price_pnl"] + ref.returns["funding_pnl"]
    sc = common_risk_scalars(gr, list(tgt.index), target_annualized_volatility=0.10,
                             lookback_days=90, interval_hours=8, minimum_scale=0.20,
                             maximum_scale=3.0)
    scaled = apply_exposure_caps(apply_risk_scalars(tgt, sc), cfg)
    org = {c: evaluate_targets(p.snapshot.bars, p.snapshot.funding, p.snapshot.membership, scaled,
                               mark_prices=p.snapshot.mark_prices, config=cfg,
                               cost_multiplier=float(c)) for c in (1, 2)}
    org_ms = time.time() - t
    w1 = window_metrics(org[1]); w2 = window_metrics(org[2])
    print(f"\n### {label}  fast={fast_ms:.1f}s organiser={org_ms:.1f}s")
    print(f"  scalars  max|d| = {np.max(np.abs(sc.to_numpy() - run['scalars'])):.3e}")
    for k, o, f in (
        ("sharpe_1x", w1.net_sharpe, fs["net_sharpe"]),
        ("sharpe_2x", w2.net_sharpe, fs["double_cost_sharpe"]),
        ("ann_ret_1x", w1.annualized_return, fs["annualized_return"]),
        ("maxDD_1x", w1.max_drawdown, fs["max_drawdown"]),
        ("maxDD_2x", w2.max_drawdown, fs["double_cost_max_drawdown"]),
        ("vol_1x", w1.annualized_volatility, fs["annualized_volatility"]),
        ("turnover_1x", w1.annualized_turnover, fs["annualized_turnover"]),
        ("edge_bps", w1.gross_edge_bps_per_turnover, fs["gross_edge_bps_per_turnover"]),
        ("trades", w1.trade_count, fs["trade_count"]),
        ("longPnL", w1.long_gross_pnl, fs["long_gross_pnl"]),
        ("shortPnL", w1.short_gross_pnl, fs["short_gross_pnl"]),
    ):
        print(f"  {k:12s} organiser={o:12.5f}  fast={f:12.5f}  diff={f-o:+.5f}")
