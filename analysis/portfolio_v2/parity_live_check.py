"""LIVE-PARITY gate — the live wrapper reproduces the backtest deployed book BEFORE any order.

Proves `crypto_trade.portfolio_v2.strategy_v2.next_target_weights` (the live target the engine acts
on) equals the v2 backtest's DEPLOYED book last row, per-coin, to machine precision. If this fails,
the live executor is NOT trading the certified BASELINE_PORTFOLIO_V2 book and no live read is
trustworthy.

Both paths read the SAME frozen pf_data/ snapshot and use the IDENTICAL frozen risk layer
(TARGET_VOL=0.006, MAX_LEV=2.0):

  (a) live    : strategy_v2.next_target_weights(coins)    -> {sym: weight} (last deployed row)
  (b) backtest: ensemble signal -> engine_v2.run_book_from_signal(... risk layer ...)
                -> (held_w × scale).iloc[-1]              -> {sym: weight}

PASS iff per-coin max|Δweight| < 1e-9 over the union of held coins. Prints PASS/FAIL + top legs.

Run:  uv run python analysis/portfolio_v2/parity_live_check.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Point the live strategy_v2 module at the frozen pf_data/ snapshot (same data both paths read).
os.environ.setdefault("PORTFOLIO_V2_DATA_DIR", "pf_data")

_ROOT = Path(__file__).resolve().parents[2]
os.chdir(_ROOT)
sys.path.insert(0, str(_ROOT / "analysis"))
sys.path.insert(0, str(_ROOT / "src"))

from crypto_trade.portfolio_v2 import strategy_v2  # noqa: E402
from portfolio_v2 import engine_v2 as e2  # noqa: E402
from portfolio_v2 import universe_v2 as uv  # noqa: E402

THRESH = 1e-9


def _norm(sig: pd.DataFrame) -> pd.DataFrame:
    return sig.div(sig.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def _backtest_deployed_last_row(coins: dict) -> pd.Series:
    """The v2 backtest's DEPLOYED book last row (held_w × scale), risk layer ON — the reference."""
    panel = e2.build_panel(coins)
    elig = (
        uv.eligibility(coins, 20, 40, 168)
        .reindex(index=panel["opens"].index, columns=panel["cols"])
        .fillna(False)
    )

    def _xs(lb: int) -> pd.DataFrame:
        s, _ = e2._xsmom(panel["close"], elig, lb)
        return _norm(s)

    signal = _norm(sum(_xs(lb) for lb in (42, 63, 84, 126, 168)) / 5.0)

    prev_tv, prev_ml = e2.TARGET_VOL, e2.MAX_LEV
    e2.TARGET_VOL, e2.MAX_LEV = 0.006, 2.0
    try:
        res = e2.run_book_from_signal(
            coins,
            signal,
            rank_lo=20,
            rank_hi=40,
            season=168,
            slip_bps_fn=e2.default_slip_bps,
            delta=0.010,
            k_exit=2,
            mode="snap",
        )
    finally:
        e2.TARGET_VOL, e2.MAX_LEV = prev_tv, prev_ml
    deployed = res["held_w"].mul(res["scale"], axis=0)
    return deployed.iloc[-1]


def main() -> int:
    # Sanity: the strategy_v2 module must be pointed at pf_data/ for this comparison.
    if strategy_v2.LIVE_DATA_DIR != "pf_data":
        print(
            f"  WARN strategy_v2.LIVE_DATA_DIR={strategy_v2.LIVE_DATA_DIR!r} (expected 'pf_data'); "
            "set PORTFOLIO_V2_DATA_DIR=pf_data before import."
        )

    print(f"LIVE-PARITY: pf_data/ snapshot via {uv.DATA_GLOB}")
    coins = uv.load_pool_pit()
    print(f"  PIT pool: {len(coins)} candidates")

    # (b) backtest reference — deployed book last row on the snapshot (no forming candle).
    print("  computing backtest deployed-book last row (risk layer ON) ...", flush=True)
    ref = _backtest_deployed_last_row(coins)

    # (a) live wrapper — next_target_weights on the SAME snapshot coins (same last candle => same
    # 'last row'; no forming candle appended so both paths key off the identical panel tail).
    print("  computing strategy_v2.next_target_weights(...) ...", flush=True)
    live = strategy_v2.next_target_weights(coins, delta=0.010)
    meta = live.pop("_meta")

    # Compare per-coin over the union of held names.
    syms = sorted(set(ref[ref.abs() > 1e-12].index) | set(live))
    rows = []
    for s in syms:
        a = float(ref.get(s, 0.0))
        b = float(live.get(s, 0.0))
        rows.append((s, b, a, abs(b - a)))
    max_abs = max((r[3] for r in rows), default=0.0)
    ok = max_abs < THRESH

    ref_gross = float(ref.abs().sum())
    live_gross = float(meta["gross"])
    print()
    print(f"  as_of                 : {meta['as_of']}")
    print(f"  live  n_positions     : {meta['n_positions']}  gross={live_gross:.4f}")
    print(f"  ref   n_positions     : {int((ref.abs() > 1e-9).sum())}  gross={ref_gross:.4f}")
    print(f"  union held coins      : {len(syms)}")
    print(f"  per-coin max|Δweight| : {max_abs:.3e}  (< {THRESH:.0e}: {max_abs < THRESH})")

    top = sorted(rows, key=lambda r: -abs(r[1]))[:10]
    print("\n  top legs (by |live weight|):")
    print(f"    {'symbol':16} {'live_w':>10} {'ref_w':>10} {'|Δ|':>10}")
    for s, b, a, d in top:
        print(f"    {s:16} {b:+10.6f} {a:+10.6f} {d:10.2e}")

    print()
    print(f"  LIVE-PARITY {'PASS' if ok else 'FAIL'}  (max|Δ|={max_abs:.3e} < {THRESH:.0e}: {ok})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
