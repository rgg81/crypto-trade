"""PAPER-mode status — the dry-run engine holds the EXACT strategy book (no venue), so monitoring
shifts from 'query the exchange' to 'confirm the simulated book == the strategy + report paper PnL'.

What it checks (all read-only, no exchange):
  - engine alive (run_portfolio_paper process) + last rebalance / errors parsed from the log
  - the PAPER book = engine-persisted held_w (data/portfolio_paper.db engine_state) — the full
    ~20-name strategy book (incl. venue-untradable coins like ALLO)
  - PARITY: held_w == strategy.next_target_weights (the engine is tracking the strategy) — should be
    bit-close; any name off by > tol is a real tracking bug
  - PAPER PnL: the strategy's net series (baseline-v1 eligexit_net) compounded from the launch candle
    to the latest COMPLETE candle, x equity — i.e. the backtest extended live (idealized: zero
    slippage, fills at the reference). This is the paper equity curve by construction.

Prints `PAPER: OK | ALERT` + a one-line book/PnL digest. Exit 0 always.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time

sys.path.insert(0, "src")
sys.path.insert(0, "analysis/portfolio")

LOG = "logs/portfolio_paper.log"
DB = "data/portfolio_paper.db"
EQUITY = 10_000.0            # paper notional base (matches run_portfolio_paper.py)
PARITY_TOL = 1e-4           # held_w vs strategy target — paper should track bit-close


def _alive() -> bool:
    out = subprocess.run(["ps", "-eo", "cmd"], capture_output=True, text=True).stdout
    return "run_portfolio_paper" in out


def _log_scan() -> tuple[str | None, int, list[str]]:
    if not os.path.exists(LOG):
        return None, 0, ["log missing"]
    txt = open(LOG, errors="replace").read()
    flags = [f"TRACEBACK x{txt.count('Traceback')}"] if "Traceback" in txt else []
    rebals = re.findall(r"rebalance plan as_of=([\d :-]+) ", txt)
    last = rebals[-1].strip() if rebals else None
    return last, len(rebals), flags


def _held_w() -> dict:
    import json
    import sqlite3
    if not os.path.exists(DB):
        return {}
    try:
        con = sqlite3.connect(DB)
        row = con.execute(
            "select value from engine_state where key='portfolio_held_w'").fetchone()
        con.close()
        return json.loads(row[0]) if row else {}
    except Exception:
        return {}


def _launch_candle() -> str | None:
    """First rebalance as_of in the log = the paper launch candle (PnL accrues from here)."""
    if not os.path.exists(LOG):
        return None
    m = re.search(r"rebalance plan as_of=([\d :-]+) ", open(LOG, errors="replace").read())
    return m.group(1).strip() if m else None


def main() -> None:
    import pandas as pd

    flags: list[str] = []
    alive = _alive()
    if not alive:
        flags.append("ENGINE DOWN (run_portfolio_paper not running)")
    last_rebal, n_rebals, log_flags = _log_scan()
    flags += log_flags

    held = _held_w()
    held = {k: float(v) for k, v in held.items()}
    gross = sum(abs(v) for v in held.values())
    net = sum(held.values())

    # PARITY: the paper book must equal the strategy's deployed target (the engine is tracking)
    drift = []
    try:
        from crypto_trade.portfolio import strategy
        uni = strategy.load_universe()
        fwd = strategy.append_forming(uni, strategy.forming_from_close(uni))
        tgt = strategy.next_target_weights(fwd)
        meta = tgt.pop("_meta")
        tgt = {k: float(v) for k, v in tgt.items()}
        for s in sorted(set(tgt) | set(held)):
            if abs(tgt.get(s, 0.0) - held.get(s, 0.0)) > PARITY_TOL:
                drift.append(f"{s}: target {tgt.get(s, 0.0):+.4f} vs held {held.get(s, 0.0):+.4f}")
        as_of = meta["as_of"]
        tgt_n = meta["n_positions"]
    except Exception as exc:
        as_of, tgt_n = "?", 0
        flags.append(f"strategy recompute failed: {repr(exc)[:70]}")
    if drift:
        flags.append(f"PARITY DRIFT ({len(drift)}): " + "; ".join(drift[:4]))

    # PAPER PnL: strategy net (eligexit_net) compounded from the launch candle -> latest candle
    pnl_pct = None
    launch = _launch_candle()
    try:
        import iter_020_hysteresis as hy
        import iter_021_eligexit as ee
        coins = strategy.load_universe()
        book = hy.canonical_book(coins, hy.build_books(coins))
        elig = ee.eligibility_mask(coins, book["target_w"])
        nets = ee.eligexit_net(book, elig, 2, 0.010, "snap")
        nets.index = pd.to_datetime(nets.index)
        if launch:
            seg = nets[nets.index >= pd.Timestamp(launch)]
            if len(seg):
                pnl_pct = float((1 + seg).prod() - 1)
    except Exception as exc:
        flags.append(f"paper PnL calc failed: {repr(exc)[:60]}")

    status = "ALERT" if flags else "OK"
    print(f"PAPER: {status}  (engine={'up' if alive else 'DOWN'}, last_rebal={last_rebal}, "
          f"rebals={n_rebals})")
    pnl_str = (f"${pnl_pct * EQUITY:+,.2f} ({pnl_pct * 100:+.2f}%) since {launch}"
               if pnl_pct is not None else "n/a (need launch candle)")
    print(f"  paper book: {len(held)} names  gross {gross:.3f}  net {net:+.3f}  | "
          f"strategy target {tgt_n} names as_of {as_of}  | PARITY {'OK' if not drift else 'DRIFT'}")
    print(f"  paper PnL (strategy net x ${EQUITY:,.0f}): {pnl_str}")
    for f in flags:
        print(f"  FLAG: {f}")
    print(f"  checked {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")


if __name__ == "__main__":
    main()
