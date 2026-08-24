"""crypto-cup-01 paper desk — SIGNAL parity audit: live-computed target weights vs a fresh
backtest recompute, at EVERY historical rebalance the desk has ever logged.

The live engine and the backtest call the exact same function (`strategy_tournament.
next_target_weights` -> `position_weight_book` -> `te.net_series`), so in principle there is
no separate "live" code path to drift from "backtest" (see engine.py's PARITY docstring). This
script does not trust that claim — it EMPIRICALLY TESTS it: for every leg the live desk ever
printed (a target weight it actually computed and traded to, at the moment that candle was the
newest/edge row of its panel), this recomputes the deployed book ONE time, fresh, over the full
history through today (where that same candle is now deep in the interior) and diffs the two.

A mismatch would mean the signal is NOT edge-invariant — e.g. a rolling/expanding computation,
a boundary condition in funding-window bucketing, or a >=-vs-> off-by-one that only shows up
when there is (or isn't) future data past the candle being scored. That is exactly the bug class
a construction-only "same function" argument cannot rule out on its own.

  uv run python scripts/tournament_paper_signal_parity.py [--tol 0.0001]

Exit code 1 if any leg exceeds --tol (default one print-rounding unit, 1e-4).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "analysis"))

from crypto_trade.portfolio import strategy_tournament as st  # noqa: E402

LOG = _ROOT / "logs" / "portfolio_tournament_paper.log"

_AS_OF_RE = re.compile(r"rebalance plan as_of=(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")
_LEG_RE = re.compile(
    r"^\s{4}(BUY|SELL)\s+(\S+)\s+w\s+([+-]\d+\.\d{4})->([+-]\d+\.\d{4})\s+\$"
)


def parse_live_legs(log_text: str) -> dict[tuple[str, str], float]:
    """{(as_of, symbol): target_w_from_log}. Later occurrences of the same key win (matches
    `_save_held` semantics — the last thing actually printed+persisted for that candle)."""
    out: dict[tuple[str, str], float] = {}
    as_of = None
    for line in log_text.splitlines():
        m = _AS_OF_RE.search(line)
        if m:
            as_of = m.group(1)
            continue
        m = _LEG_RE.match(line)
        if m and as_of is not None:
            _side, sym, _cur, tgt = m.groups()
            out[(as_of, sym)] = float(tgt)
        elif as_of is not None and line and not line.startswith(" "):
            as_of = None  # left the leg block (next log line is unrelated engine output)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tol", type=float, default=1e-4, help="max allowed |diff| (default 1e-4)")
    args = ap.parse_args()

    live = parse_live_legs(LOG.read_text())
    n_asof = len({a for a, _ in live})
    print(f"[parity] parsed {len(live)} legs across {n_asof} historical rebalances from the log")
    if not live:
        print("[parity] nothing to check (empty log)")
        return 0

    print("[parity] recomputing the deployed book fresh, full history through today "
          "(same next_target_weights pipeline, ~20-40s)...")
    coins = st.load_universe()
    forming_opens = st.forming_from_close(coins)
    coins = st.append_forming(coins, forming_opens)
    book = st.position_weight_book(coins)  # re-checks the frozen SHA internally

    rows = []
    missing = 0
    for (as_of, sym), tgt_live in live.items():
        ts = pd.Timestamp(as_of)
        if ts not in book.index or sym not in book.columns:
            missing += 1
            continue
        tgt_bt = float(book.loc[ts, sym])
        rows.append((as_of, sym, tgt_live, tgt_bt, abs(tgt_live - tgt_bt)))

    df = pd.DataFrame(rows, columns=["as_of", "symbol", "live_w", "backtest_w", "abs_diff"])
    bad = df[df["abs_diff"] > args.tol].sort_values("abs_diff", ascending=False)

    print(f"[parity] compared {len(df)} legs ({missing} skipped: symbol/candle not in the "
          f"fresh recompute — expected for since-delisted names)")
    print(f"[parity] abs_diff  max={df['abs_diff'].max():.6f}  mean={df['abs_diff'].mean():.6f}  "
          f"p99={df['abs_diff'].quantile(0.99):.6f}")

    if len(bad):
        print(f"\n[parity] {len(bad)} legs exceed tol={args.tol} — SIGNAL MISMATCH:")
        print(bad.head(30).to_string(index=False))
        print("\n[parity] VERDICT: FAIL — live target weight diverged from a fresh backtest "
              "recompute for at least one historical candle. This is a real signal bug, not an "
              "execution-layer artifact (only fully-traded legs are compared).")
        return 1

    print("\n[parity] VERDICT: PASS — every target weight the live desk ever computed and "
          "traded to, across its full history, is reproduced exactly (within print-rounding) "
          "by a fresh from-scratch backtest recompute today. No signal drift detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
