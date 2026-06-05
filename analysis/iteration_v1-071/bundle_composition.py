"""
iter-v1/071 — BUNDLE-001 ASSEMBLY composition analysis.

Computes union-of-specialist bundle metrics from the 3 finalized specialists'
trades.csv files (committed at quant-research HEAD ee37f07e — recovered from
stash@{0} per /070 artifact-recovery).

Specialists (pairwise-disjoint coin universes per feedback_v1_bundle_no_coin_overlap.md):
- /063 DOT — R-config (R1+R2+R3), atr 3.5/1.75
- /064 ETH — Model A (R3 only), atr 2.9/1.45
- /065 BTC — Model A (R3 only), atr 2.9/1.45

LINK + LTC DROPPED (2-strike rule).

Bundle = simple UNION of trades (no weights, no overlap possible).
PnL = sum across the 3 coins (each coin owned by exactly ONE specialist).

Inputs (read-only):
- reports-v1/iteration_v1-063/{in_sample,out_of_sample}/trades.csv
- reports-v1/iteration_v1-064/{in_sample,out_of_sample}/trades.csv
- reports-v1/iteration_v1-065/{in_sample,out_of_sample}/trades.csv

Outputs:
- stdout-only (numerical evidence inlined in the brief)
"""

import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "reports-v1"

specs = [
    ("063", "DOTUSDT", "R-config (R1+R2+R3)", "atr 3.5/1.75"),
    ("064", "ETHUSDT", "Model A (R3 only)", "atr 2.9/1.45"),
    ("065", "BTCUSDT", "Model A (R3 only)", "atr 2.9/1.45"),
]


def stats(path: Path) -> dict:
    trades = []
    with open(path) as fh:
        for row in csv.DictReader(fh):
            trades.append(row)
    n = len(trades)
    pnl = [float(t["net_pnl_pct"]) for t in trades]
    wins = sum(1 for p in pnl if p > 0)
    gross_w = sum(p for p in pnl if p > 0)
    gross_l = sum(-p for p in pnl if p < 0)
    total = sum(pnl)
    wr = wins / n * 100 if n else 0
    pf = gross_w / gross_l if gross_l > 0 else float("inf")
    avg = total / n if n else 0
    sd = math.sqrt(sum((p - avg) ** 2 for p in pnl) / n) if n > 1 else 0
    pt_sharpe = (avg / sd) if sd > 0 else 0
    return {
        "n": n, "total_pnl_pct": total, "win_rate": wr,
        "profit_factor": pf, "avg_pnl_pct": avg, "stdev_pnl_pct": sd,
        "per_trade_sharpe": pt_sharpe,
    }


def main() -> None:
    print(f"{'spec':<5}{'sym':<10}{'window':<14}{'n':>5}{'PnL%':>10}{'WR%':>7}{'PF':>7}{'avgPnL%':>10}{'σPnL%':>9}{'ptSR':>8}")
    for spec, sym, _, _ in specs:
        for w in ("in_sample", "out_of_sample"):
            s = stats(ROOT / f"iteration_v1-{spec}" / w / "trades.csv")
            print(f"{spec:<5}{sym:<10}{w:<14}{s['n']:>5}{s['total_pnl_pct']:>10.2f}{s['win_rate']:>7.2f}{s['profit_factor']:>7.2f}{s['avg_pnl_pct']:>10.3f}{s['stdev_pnl_pct']:>9.3f}{s['per_trade_sharpe']:>8.3f}")

    print("\n--- Bundle = UNION of 3 specialists (pairwise-disjoint coins) ---")
    for w_name, w_key in [("IS", "in_sample"), ("OOS", "out_of_sample")]:
        all_pnls: list[tuple[str, float, str]] = []
        for spec, _sym, _, _ in specs:
            with open(ROOT / f"iteration_v1-{spec}" / w_key / "trades.csv") as fh:
                for row in csv.DictReader(fh):
                    all_pnls.append((row["symbol"], float(row["net_pnl_pct"]), row["close_time"]))
        n = len(all_pnls)
        pnls = [p for _, p, _ in all_pnls]
        total = sum(pnls)
        wins = sum(1 for p in pnls if p > 0)
        gross_w = sum(p for p in pnls if p > 0)
        gross_l = sum(-p for p in pnls if p < 0)
        avg = total / n if n else 0
        sd = math.sqrt(sum((p - avg) ** 2 for p in pnls) / n) if n > 1 else 0
        pt_sharpe = avg / sd if sd > 0 else 0
        pf = gross_w / gross_l if gross_l > 0 else float("inf")
        print(f"{w_name}: n={n}  totalPnL={total:.2f}%  WR={wins/n*100:.2f}%  PF={pf:.2f}  "
              f"avgPnL={avg:.3f}%  σ={sd:.3f}%  ptSR={pt_sharpe:.3f}")
        by_sym: dict[str, list[float]] = {}
        for sym, p, _ in all_pnls:
            by_sym.setdefault(sym, []).append(p)
        print(f"  Per-symbol PnL contribution:")
        for sym, ps in sorted(by_sym.items()):
            share = sum(ps) / total * 100 if total != 0 else 0
            print(f"    {sym:<10}  n={len(ps):>3}  PnL={sum(ps):>8.2f}%  share={share:>6.2f}%")


if __name__ == "__main__":
    main()
