"""Validation 3 — trade-roster overlap baseline ↔ /031 OOS by symbol.

Reads:
  reports-v1/iteration_v1-baseline/out_of_sample/trades.csv
  reports-v1/iteration_v1-031/out_of_sample/trades.csv

For each of 5 symbols (BTC, ETH, LINK, LTC, DOT):
  intersect = trades in BOTH files with same (symbol, open_time)
  overlap_pct = intersect / baseline_count

Bands per Critic spec:
  PASS:        overlap ∈ [35%, 75%]
  ACCEPTABLE:  25% ≤ overlap < 35%
  CATASTROPHIC FAIL: overlap < 25%
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_TRADES = REPO_ROOT / "reports-v1" / "iteration_v1-baseline" / "out_of_sample" / "trades.csv"
ITER_TRADES = REPO_ROOT / "reports-v1" / "iteration_v1-031" / "out_of_sample" / "trades.csv"
OUT_CSV = REPO_ROOT / "analysis" / "iteration_v1-031" / "v3_precise_overlap.csv"

V1_SYMBOLS = ["BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"]


def main() -> None:
    print(f"[v3] Reading {BASELINE_TRADES}")
    base = pd.read_csv(BASELINE_TRADES)
    print(f"[v3] Reading {ITER_TRADES}")
    iter_df = pd.read_csv(ITER_TRADES)
    print(f"[v3] Baseline trades: {len(base):,}")
    print(f"[v3] /031 trades:    {len(iter_df):,}")

    # Inspect columns
    print(f"\n[v3] Baseline columns: {list(base.columns)}")

    # Per-symbol overlap on (symbol, open_time)
    rows = []
    for sym in V1_SYMBOLS:
        b = base[base["symbol"] == sym]
        i = iter_df[iter_df["symbol"] == sym]
        b_keys = set(b["open_time"].astype(str))
        i_keys = set(i["open_time"].astype(str))
        intersect = b_keys & i_keys
        b_count = len(b_keys)
        i_count = len(i_keys)
        i_int = len(intersect)
        if b_count == 0:
            overlap_pct = float("nan")
            verdict = "N/A (no baseline trades)"
        else:
            overlap_pct = 100 * i_int / b_count
            if overlap_pct >= 35 and overlap_pct <= 75:
                verdict = "PASS"
            elif overlap_pct >= 25:
                verdict = "ACCEPTABLE"
            elif overlap_pct > 75:
                verdict = "TOO-HIGH (no edge)"
            else:
                verdict = "CATASTROPHIC FAIL"
        rows.append(
            {
                "symbol": sym,
                "baseline_trades": b_count,
                "iter_trades": i_count,
                "intersect_trades": i_int,
                "overlap_pct": overlap_pct,
                "verdict": verdict,
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print("\n[v3] Per-symbol overlap:")
    print(df.to_string(index=False))

    n_fail = (df["verdict"] == "CATASTROPHIC FAIL").sum()
    n_pass = (df["verdict"] == "PASS").sum()
    n_acc = (df["verdict"] == "ACCEPTABLE").sum()
    print(f"\n[v3] Summary: {n_pass} PASS, {n_acc} ACCEPTABLE, {n_fail} CATASTROPHIC FAIL of {len(df)}")
    if n_fail > 0:
        print("[v3] V3 OVERALL VERDICT: FAIL (at least one symbol catastrophic)")
    elif n_pass == len(df):
        print("[v3] V3 OVERALL VERDICT: PASS (all symbols in [35%, 75%])")
    else:
        print("[v3] V3 OVERALL VERDICT: BORDERLINE (some acceptable, none catastrophic)")
    print(f"\n[v3] Wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
