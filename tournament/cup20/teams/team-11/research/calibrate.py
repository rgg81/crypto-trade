"""Calibrate the offline replica against the organiser's OWN modules.

Runs one transparent book through ``crypto_trade.cup20.runner.run_candidate`` (the same function
``scripts/cup20_evaluate.py`` calls) and through ``fastsim``, and prints the residual on every
metric that gates a floor. Costs no trial: it never touches the journal and never asks the
evaluator for a score -- it is the team's own bench, and its only job is to establish how far the
bench can be trusted before thousands of offline sweeps are run on it.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Mapping

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-11/research")
import fastsim  # noqa: E402
import panel as panel_mod  # noqa: E402

from crypto_trade.cup20.metrics import fold_sharpes, is_folds, window_metrics  # noqa: E402
from crypto_trade.cup20.runner import decision_grid, evaluator_config, run_candidate  # noqa: E402
from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start  # noqa: E402

IS_END = pd.Timestamp("2024-08-01T00:00:00Z")
RAW_EXECUTION = {
    "interval_hours": 8,
    "initial_equity": 100_000.0,
    "taker_fee_bps_per_side": 5.0,
    "slippage_bps_per_side": 2.5,
    "max_gross_exposure": 1.0,
    "max_abs_net_exposure": 1.0,
    "max_symbol_exposure": 0.20,
    "max_bar_participation": 0.001,
}
RISK_UNIT = {
    "target_annualized_volatility": 0.10,
    "lookback_days": 90,
    "minimum_scale": 0.20,
    "maximum_scale": 3.0,
}


class WeightTable:
    """Replays a precomputed (boundary x symbol) weight matrix through the organiser's runner."""

    def __init__(self, times, symbols, weights, rebalance):
        self.index = {pd.Timestamp(t): i for i, t in enumerate(times)}
        self.symbols = symbols
        self.weights = weights
        self.rebalance = rebalance

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        i = self.index.get(pd.Timestamp(context.decision_time))
        if i is None or not self.rebalance[i]:
            return None
        row = self.weights[i]
        out = {}
        for s in context.eligible_symbols:
            j = self.symbols.index(s)
            v = float(row[j])
            if v != 0.0:
                out[s] = v
        return out


def build_test_book(p, start_idx, kind="dispersion"):
    """A transparent, non-trivial book: cross-sectional rank on 21-bar close momentum,
    rebalanced every 3 bars at phase 0. Deliberately not the candidate mechanism."""
    import measures as M

    n = len(p.times)
    clr = M.close_log_return(p.close)
    mom = M.causal_rolling_sum(clr, 21)
    r = M.cross_section_rank(mom, p.eligible)
    w = np.nan_to_num(-r)
    reb = np.zeros(n, dtype=bool)
    reb[start_idx::3] = True
    w = np.where(p.eligible, w, 0.0)
    return w, reb


def main() -> None:
    t0 = time.time()
    p = panel_mod.load()
    snapshot = load_snapshot("data/cup20/is")
    is_start = resolve_is_start(snapshot.membership, target_size=20)
    grid = decision_grid(is_start, IS_END, interval_hours=8)
    start_idx = int(np.where(p.times == is_start)[0][0])
    assert len(grid) == len(p.times) - start_idx, (len(grid), len(p.times) - start_idx)

    w, reb = build_test_book(p, start_idx)
    print(f"panel built in {time.time() - t0:.1f}s; boundaries={len(grid)}")

    t1 = time.time()
    fast = fastsim.full_evaluate(p, start_idx, w[start_idx:], reb[start_idx:])
    print(f"fastsim  full evaluation: {time.time() - t1:.1f}s")

    t2 = time.time()
    strategy = WeightTable(p.times[start_idx:], p.symbols, w[start_idx:], reb[start_idx:])
    run = run_candidate(
        strategy,
        snapshot,
        decision_times=grid,
        seed=11,
        config=evaluator_config(RAW_EXECUTION),
        risk_unit=RISK_UNIT,
        cost_multipliers=(1, 2, 3),
        risk_policy=None,
    )
    print(f"organiser full evaluation: {time.time() - t2:.1f}s")

    folds = is_folds(is_start, IS_END)
    print("\nmetric                 organiser        fastsim         residual")
    for lv in (1, 2, 3):
        wm = window_metrics(run.results[lv])
        f = fast[lv]
        pairs = [
            ("net_sharpe", wm.net_sharpe, f["sharpe"]),
            ("annualized_return", wm.annualized_return, f["ann_return"]),
            ("annualized_volatility", wm.annualized_volatility, f["ann_vol"]),
            ("max_drawdown", wm.max_drawdown, f["max_dd"]),
            ("annualized_turnover", wm.annualized_turnover, f["ann_turnover"]),
            ("gross_edge_bps", wm.gross_edge_bps_per_turnover, f["gross_edge_bps"]),
            ("cost_share", wm.cost_share_of_positive_gross, f["cost_share"]),
            ("long_gross_pnl", wm.long_gross_pnl, f["long_gross"]),
            ("short_gross_pnl", wm.short_gross_pnl, f["short_gross"]),
            ("trade_count", float(wm.trade_count), float(f["trades"])),
        ]
        print(f"--- cost {lv}x ---")
        for name, a, b in pairs:
            print(f"{name:<22} {a:>14.6f} {b:>14.6f} {b - a:>+14.6f}")
        if lv == 2:
            fs = fold_sharpes(run.results[lv], folds)
            d = pd.Series(f["daily"], index=pd.DatetimeIndex(f["daily_index"], tz="UTC"))
            mine = {
                name: (
                    float(np.mean(x)) / float(np.std(x, ddof=1)) * np.sqrt(365.0)
                    if len(x) > 1 and np.std(x, ddof=1) > 0 else 0.0
                )
                for name, x in (
                    (nm, d[(d.index >= s) & (d.index < e)].to_numpy()) for nm, s, e in folds
                )
            }
            print("fold sharpes 2x:")
            for nm in fs:
                print(f"  {nm}  organiser {fs[nm]:>+8.4f}   fastsim {mine[nm]:>+8.4f}"
                      f"   residual {mine[nm] - fs[nm]:>+8.4f}")
    print(f"\nexposure_caps requested min scale: organiser "
          f"{run.requested_trim.summary()['minimum_scale']:.6f}  "
          f"fastsim {fast['requested_min_scale']:.6f}")
    print(f"total wall clock {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
