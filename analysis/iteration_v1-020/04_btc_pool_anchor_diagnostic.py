"""iter-v1/020 EDA — script 04.

BTC pool-anchor diagnostic.

The pool-anchor hypothesis claims that Model A (BTC+ETH pooled) trains BTC's
predictions to compensate for ETH's drag — BTC gets a "supportive" prediction
profile that helps ETH in pool but causes BTC's own labels to look bad in IS.
If true, BTC-only specialization at /020 should SOLVE the IS catastrophic
(intrinsic edge restored) and may PRESERVE the OOS positive rotation.

The intrinsic IS-OOS hypothesis claims BTC IS = 2022-2024 bear chop is
structurally different from BTC OOS = 2025-2026 mixed regime; pooled
or not, BTC's intrinsic edge profile is regime-dependent. If true,
BTC-only specialization should NOT fix the IS catastrophic (the IS data
just happens to be a bad regime for any BTC model).

Diagnostic: correlate BTC trade outcomes within Model A months against
ETH trade outcomes within the same Model A training months.
HIGH correlation → BTC and ETH labels co-move within pool training →
pool DOES learn cross-symbol patterns → pool-anchor hypothesis MORE likely.
LOW correlation → BTC and ETH labels independent within pool → pool training
just sums independent symbol contributions → INTRINSIC hypothesis MORE likely.

Reads:
  reports-v1/iteration_v1-baseline/in_sample/trades.csv (BTC + ETH rows)

Writes:
  analysis/iteration_v1-020/btc_eth_monthly_correlation.csv
  analysis/iteration_v1-020/btc_pool_anchor_summary.csv
"""

from __future__ import annotations

import csv
import statistics
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
IS_TRADES = REPO / "reports-v1" / "iteration_v1-baseline" / "in_sample" / "trades.csv"

OUT_CORR = REPO / "analysis" / "iteration_v1-020" / "btc_eth_monthly_correlation.csv"
OUT_SUMMARY = REPO / "analysis" / "iteration_v1-020" / "btc_pool_anchor_summary.csv"


def _ms_to_month(ms_str: str) -> str:
    ms = int(ms_str)
    dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
    return f"{dt.year:04d}-{dt.month:02d}"


def _load_symbol_monthly(path: Path, symbol: str) -> dict[str, float]:
    """Return {month: net_pnl_pct sum} for one symbol."""
    buckets: dict[str, float] = {}
    with path.open() as fh:
        for row in csv.DictReader(fh):
            if row["symbol"] != symbol:
                continue
            month = _ms_to_month(row["open_time"])
            pnl = float(row["net_pnl_pct"])
            buckets[month] = buckets.get(month, 0.0) + pnl
    return buckets


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return float("nan")
    mx = statistics.mean(xs)
    my = statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx2 = sum((x - mx) ** 2 for x in xs)
    dy2 = sum((y - my) ** 2 for y in ys)
    denom = (dx2 * dy2) ** 0.5
    return num / denom if denom > 0 else float("nan")


def _spearman(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return float("nan")

    def _rank(vals: list[float]) -> list[float]:
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        ranks = [0.0] * len(vals)
        i = 0
        while i < len(vals):
            j = i
            while j + 1 < len(vals) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                ranks[order[k]] = avg_rank
            i = j + 1
        return ranks

    return _pearson(_rank(xs), _rank(ys))


def main() -> None:
    btc_monthly = _load_symbol_monthly(IS_TRADES, "BTCUSDT")
    eth_monthly = _load_symbol_monthly(IS_TRADES, "ETHUSDT")

    months_common = sorted(set(btc_monthly.keys()) & set(eth_monthly.keys()))
    btc_vals = [btc_monthly[m] for m in months_common]
    eth_vals = [eth_monthly[m] for m in months_common]

    OUT_CORR.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CORR.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["month", "btc_monthly_net_pnl_pct", "eth_monthly_net_pnl_pct"])
        for m, bv, ev in zip(months_common, btc_vals, eth_vals):
            writer.writerow([m, f"{bv:.4f}", f"{ev:.4f}"])
    print(f"wrote {OUT_CORR}")

    pearson = _pearson(btc_vals, eth_vals)
    spearman = _spearman(btc_vals, eth_vals)

    # Sign-agreement: how often do BTC and ETH have same-sign monthly PnL?
    same_sign = sum(1 for b, e in zip(btc_vals, eth_vals) if (b * e) > 0)
    opp_sign = sum(1 for b, e in zip(btc_vals, eth_vals) if (b * e) < 0)
    zero_either = len(btc_vals) - same_sign - opp_sign

    # BTC-only months: months with BTC trades but no ETH trades (rare in pool)
    btc_only_months = sorted(set(btc_monthly.keys()) - set(eth_monthly.keys()))
    eth_only_months = sorted(set(eth_monthly.keys()) - set(btc_monthly.keys()))

    rows = [
        {
            "metric": "n_months_common (BTC and ETH both traded)",
            "value": f"{len(months_common)}",
        },
        {"metric": "n_months_btc_only", "value": f"{len(btc_only_months)}"},
        {"metric": "n_months_eth_only", "value": f"{len(eth_only_months)}"},
        {
            "metric": "pearson(BTC, ETH) monthly net_pnl",
            "value": f"{pearson:+.4f}",
        },
        {
            "metric": "spearman(BTC, ETH) monthly net_pnl",
            "value": f"{spearman:+.4f}",
        },
        {
            "metric": "same_sign_months (both positive OR both negative)",
            "value": f"{same_sign} / {len(months_common)}",
        },
        {
            "metric": "opposite_sign_months (one positive, one negative)",
            "value": f"{opp_sign} / {len(months_common)}",
        },
        {
            "metric": "btc_total_is_net_pnl_pct (across common months)",
            "value": f"{sum(btc_vals):+.4f}",
        },
        {
            "metric": "eth_total_is_net_pnl_pct (across common months)",
            "value": f"{sum(eth_vals):+.4f}",
        },
        {
            "metric": "btc_mean_monthly_pnl",
            "value": f"{statistics.mean(btc_vals):+.4f}",
        },
        {
            "metric": "eth_mean_monthly_pnl",
            "value": f"{statistics.mean(eth_vals):+.4f}",
        },
    ]

    with OUT_SUMMARY.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {OUT_SUMMARY}")

    print()
    print("BTC-ETH pool-anchor diagnostic:")
    print(f"  Pearson(BTC, ETH) monthly = {pearson:+.4f}")
    print(f"  Spearman(BTC, ETH) monthly = {spearman:+.4f}")
    print(f"  Same-sign months: {same_sign}/{len(months_common)} = "
          f"{100 * same_sign / max(1, len(months_common)):.1f}%")
    print()
    print("Interpretation:")
    print("  - |ρ| > 0.50 → BTC/ETH labels strongly co-vary in pool → "
          "POOL-ANCHOR hypothesis MORE plausible.")
    print("  - |ρ| < 0.30 → BTC/ETH labels mostly independent → "
          "INTRINSIC IS-OOS regime hypothesis MORE plausible.")
    print("  - Same-sign > 75% → BTC and ETH move together monthly → "
          "pool training likely shares regime priors across the cohort.")


if __name__ == "__main__":
    main()
