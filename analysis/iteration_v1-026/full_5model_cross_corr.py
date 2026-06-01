"""Full 5-Model cross-correlation matrix (Pearson + Spearman) for /026 brief.

10 pairs × 2 samples × 2 metrics = 40 cells. Identifies all pairs ≥ 0.50.
"""

from __future__ import annotations

import csv
import math
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path("/home/roberto/crypto-trade/.worktrees/quant-research")
ANALYSIS_DIR = REPO_ROOT / "analysis" / "iteration_v1-026"
POOL = REPO_ROOT / "reports-v1" / "iteration_v1-baseline"
LINK = REPO_ROOT / "reports-v1" / "iteration_v1-018"
ETHG = REPO_ROOT / "reports-v1" / "iteration_v1-019"


def read_trades(report_dir: Path, sample: str) -> list[dict]:
    out = []
    with (report_dir / sample / "trades.csv").open() as f:
        for row in csv.DictReader(f):
            out.append(row)
    return out


def filter_symbol(trades, sym):
    return [t for t in trades if t["symbol"] == sym]


def month_of(ms_str):
    return datetime.fromtimestamp(int(ms_str) / 1000, tz=UTC).strftime("%Y-%m")


def aggregate_monthly(trades):
    out = {}
    for t in trades:
        m = month_of(t["close_time"])
        out[m] = out.get(m, 0.0) + float(t["weighted_pnl"])
    return out


def pearson(xs, ys):
    if len(xs) < 2:
        return float("nan")
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return float("nan")
    return num / (dx * dy)


def spearman(xs, ys):
    if len(xs) < 2:
        return float("nan")

    def ranks(vs):
        indexed = sorted(enumerate(vs), key=lambda t: t[1])
        out = [0.0] * len(vs)
        i = 0
        while i < len(indexed):
            j = i
            while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                out[indexed[k][0]] = avg
            i = j + 1
        return out

    return pearson(ranks(xs), ranks(ys))


def main() -> None:
    rows_out: list[dict] = []
    for sample in ("in_sample", "out_of_sample"):
        base = read_trades(POOL, sample)
        link = read_trades(LINK, sample)
        ethg = read_trades(ETHG, sample)
        comp_trades = {
            "A_btc_approx": filter_symbol(base, "BTCUSDT"),
            "C_link_spec":  link,
            "D_ltc":        filter_symbol(base, "LTCUSDT"),
            "E_dot":        filter_symbol(base, "DOTUSDT"),
            "G_eth_spec":   ethg,
        }
        comp_monthly = {k: aggregate_monthly(v) for k, v in comp_trades.items()}
        all_months = sorted(set(m for d in comp_monthly.values() for m in d))
        series = {k: [comp_monthly[k].get(m, 0.0) for m in all_months]
                  for k in comp_monthly}

        keys = list(series.keys())
        print(f"\n=== {sample} ===")
        print(f"  Months: {len(all_months)}")
        for i, a in enumerate(keys):
            for j, b in enumerate(keys):
                if i >= j:
                    continue
                p = pearson(series[a], series[b])
                s = spearman(series[a], series[b])
                breach = abs(p) >= 0.50 or abs(s) >= 0.50
                marker = " !!!" if breach else ""
                print(
                    f"  {a:15s}× {b:15s}  Pearson={p:+.4f}  Spearman={s:+.4f}{marker}"
                )
                rows_out.append({
                    "sample": sample,
                    "pair_a": a,
                    "pair_b": b,
                    "pearson": f"{p:+.4f}",
                    "spearman": f"{s:+.4f}",
                    "abs_pearson_ge_0p50": "YES" if abs(p) >= 0.50 else "NO",
                    "abs_spearman_ge_0p50": "YES" if abs(s) >= 0.50 else "NO",
                })

    with (ANALYSIS_DIR / "full_5model_cross_corr.csv").open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        wr.writeheader()
        wr.writerows(rows_out)
    print(f"\n  Output: {ANALYSIS_DIR / 'full_5model_cross_corr.csv'}")


if __name__ == "__main__":
    main()
