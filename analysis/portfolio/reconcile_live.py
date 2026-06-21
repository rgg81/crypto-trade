"""RECONCILIATION — prove the live engine reproduces the backtest BIT-BY-BIT from a MID-MONTH start.

Two parity hazards of a mid-month live launch:
  (1) lambda is walk-forward-picked at the MONTH BOUNDARY (trailing 24mo); a mid-month join must use
      the lambda already decided for this month.
  (2) the hysteresis band is PATH-DEPENDENT (held[t] chains from history); the live book must equal
      the backtest's CURRENT held book at the join candle, not start flat.

Both are handled IF the live target (next_target_weights), from data through the HOLD candle, equals
the backtest deployed book row for that candle — at EVERY join point. We truncate the universe
to candle H inclusive ("we joined at H's open") and assert that equality to machine precision for a
MID-MONTH candle, a MONTH-BOUNDARY candle, and near-end — and that it is invariant to future data
(no look-ahead). A full mid-month REPLAY through the engine's tracking checks the live held series
tracks the backtest within the min-notional dust tolerance.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
sys.path.insert(0, "analysis/portfolio")

from crypto_trade.portfolio import strategy  # noqa: E402


def _truncate(coins: dict, as_of_ms: int) -> dict:
    """Coins with all candles through as_of_ms ('we joined at this candle's open')."""
    return {s: d[d.index <= as_of_ms] for s, d in coins.items()}


def main() -> None:
    coins = strategy.load_universe()
    full = strategy.position_weight_book(coins)            # ground-truth deployed book
    dt_index = full.index
    # Timestamp.value = ns since epoch (naive=UTC); // 1e6 = the exact open_time ms of each candle.
    open_ms = np.array([int(ts.value // 1_000_000) for ts in dt_index], dtype="int64")

    n = len(dt_index)
    month = pd.DatetimeIndex(dt_index).to_period("M")
    boundary_hold = None   # a candle that is the FIRST of its month (join at a month edge)
    midmonth_hold = None   # a mid-month candle
    for h in range(n - 60, n):
        if h > 0 and month[h] != month[h - 1] and boundary_hold is None:
            boundary_hold = h
        if 5 < dt_index[h].day < 25 and midmonth_hold is None:
            midmonth_hold = h
    tests = {"mid-month": midmonth_hold, "month-boundary": boundary_hold, "near-end": n - 1}

    print("RECONCILIATION — next_target_weights(through HOLD candle) vs backtest deployed book:")
    print("  (truncate to candle H inclusive; must reproduce deployed[H] bit-exact AND be")
    print("   invariant to truncating data after H = no look-ahead + mid-month/boundary repro)")
    worst = 0.0
    for label, h in tests.items():
        if h is None:
            print(f"  {label:16} (no such candle in window — skipped)")
            continue
        trunc = _truncate(coins, int(open_ms[h]))
        nt = strategy.next_target_weights(trunc)
        nt.pop("_meta")
        bt_row = full.iloc[h]                              # backtest deployed weight @ candle H
        syms = set(nt) | set(bt_row[bt_row.abs() > 1e-9].index)
        diff = max((abs(nt.get(s, 0.0) - float(bt_row.get(s, 0.0))) for s in syms), default=0.0)
        worst = max(worst, diff)
        status = "PASS" if diff < 1e-9 else "FAIL"
        kind = "mid-month" if 5 < dt_index[h].day < 25 else "month-edge"
        print(f"  {label:16} hold={dt_index[h].date()} ({kind}) "
              f"n={len(nt)} maxdiff={diff:.2e} [{status}]")
    verdict = "PARITY HOLDS — bit-exact" if worst < 1e-9 else "DIVERGENCE — BUG"
    print(f"\n  WORST maxdiff across join points = {worst:.2e}  ({verdict})")

    # --- LIVE close-proxy forming path: the engine injects forming via close[last] (non-ragged).
    #     Assert it reproduces deployed[H] with relative weights bit-exact + gross within the proxy
    #     tolerance. This guards the XLM-0.40 ragged-panel bug class. ---
    print("\nLIVE close-proxy forming path (the engine's actual path) vs backtest deployed book:")
    worst_rel = worst_gross = 0.0
    for label, h in tests.items():
        if h is None:
            continue
        trunc = _truncate(coins, int(open_ms[h - 1]))        # data through H-1 (last closed)
        forming = strategy.forming_from_close(trunc)         # close-proxy forming for candle H
        nt = strategy.next_target_weights(strategy.append_forming(trunc, forming))
        gp = nt.pop("_meta")["gross"]
        bt = full.iloc[h]
        gr = float(bt.abs().sum())
        syms = set(nt) | set(bt[bt.abs() > 1e-9].index)
        rel = max(abs(nt.get(s, 0.0) / gp - float(bt.get(s, 0.0)) / gr) for s in syms)
        worst_rel = max(worst_rel, rel)
        worst_gross = max(worst_gross, abs(gr - gp) / gr)
    print(f"  worst RELATIVE weight diff = {worst_rel:.2e} (bit-exact? {worst_rel < 1e-9}) | "
          f"worst gross diff = {worst_gross * 100:.3f}%")

    if midmonth_hold is None:
        return
    print("\nMID-MONTH ENGINE REPLAY (track backtest book; dust = min_notional/equity):")
    from crypto_trade.portfolio.engine import PortfolioConfig
    cfg = PortfolioConfig(equity_usd=10_000.0)
    dust_w = cfg.min_notional_usd / (cfg.equity_usd * cfg.leverage)
    held: dict[str, float] = {}                            # live paper book, start flat at join
    max_track = 0.0
    for h in range(midmonth_hold, min(midmonth_hold + 12, n)):
        trunc = _truncate(coins, int(open_ms[h]))
        tgt = strategy.next_target_weights(trunc)
        tgt.pop("_meta")
        new_held = {}
        for s in set(tgt) | set(held):
            t, c = float(tgt.get(s, 0.0)), float(held.get(s, 0.0))
            new_held[s] = t if abs(t - c) >= dust_w else c  # track exactly unless trade < dust
        held = {s: w for s, w in new_held.items() if abs(w) > 1e-12}
        bt_row = full.iloc[h]
        syms = set(held) | set(bt_row[bt_row.abs() > 1e-9].index)
        track = max((abs(held.get(s, 0.0) - float(bt_row.get(s, 0.0))) for s in syms), default=0.0)
        max_track = max(max_track, track)
    ok = "YES" if max_track <= dust_w + 1e-9 else "NO"
    print(f"  max live-vs-backtest weight gap over replay = {max_track:.2e} "
          f"(<= dust {dust_w:.2e}? {ok})")


if __name__ == "__main__":
    main()
