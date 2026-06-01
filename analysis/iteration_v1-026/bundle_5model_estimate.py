"""5-Model /027 bundle estimate.

Per /025 LOCKED bundle composition (research_brief.md):
- LINK-only specialist Model C' (+0.80 multi-seed Δ target) — LOCKED
- ETH-only + symmetric BTC-trend gate Model G (+0.50) — LOCKED
- BTC, LTC, DOT — all in pool via baseline models

5-Model bundle:
  A':  BTC only (baseline pool trains BTC+ETH pooled; here we extract baseline BTC trades)
  C':  LINK specialist (/018)
  D:   LTC baseline
  E:   DOT baseline
  G:   ETH+gate specialist (/019)

ESTIMATION CAVEAT
-----------------
Baseline Model A is BTC+ETH POOLED. Extracting baseline-BTC trades alone is
an APPROXIMATION — a true BTC-only A' would re-train Optuna on BTC alone and
likely produce a different (smaller-cap) BTC trade roster. The Critic /025
review and Phase 6.0 contract recognize this and the estimate is informational
ONLY — the binding number is /027's actual multi-seed multi-model backtest.

What we report
--------------
1. Per-component monthly returns + Sharpe + DD on existing reports.
2. The 5-model bundle (sum of component weighted PnL) per-month series.
3. Bundle Sharpe + DD.
4. Cross-correlation among the 5 model series (10 pairs).
5. Comparison to /027 target [+1.10, +1.30] OOS.
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
    out: list[dict] = []
    with (report_dir / sample / "trades.csv").open() as f:
        for row in csv.DictReader(f):
            out.append(row)
    return out


def filter_symbol(trades: list[dict], sym: str) -> list[dict]:
    return [t for t in trades if t["symbol"] == sym]


def month_of(ts_ms_str: str) -> str:
    return datetime.fromtimestamp(int(ts_ms_str) / 1000, tz=UTC).strftime("%Y-%m")


def aggregate_monthly(trades: list[dict]) -> dict[str, float]:
    out: dict[str, float] = {}
    for t in trades:
        m = month_of(t["close_time"])
        out[m] = out.get(m, 0.0) + float(t["weighted_pnl"])
    return out


def pearson(xs: list[float], ys: list[float]) -> float:
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


def sharpe(returns: list[float]) -> float:
    if len(returns) < 2:
        return float("nan")
    mu = sum(returns) / len(returns)
    var = sum((r - mu) ** 2 for r in returns) / (len(returns) - 1)
    sd = math.sqrt(var)
    if sd == 0:
        return float("nan")
    return mu / sd * math.sqrt(12)


def max_dd(returns: list[float]) -> float:
    cum, peak, mdd = 0.0, 0.0, 0.0
    for r in returns:
        cum += r
        if cum > peak:
            peak = cum
        dd = peak - cum
        if dd > mdd:
            mdd = dd
    return mdd


def main() -> None:  # noqa: C901
    print("=" * 70)
    print("iter-v1/026 — 5-Model /027 Bundle Estimate")
    print("=" * 70)

    rows_out: list[dict] = []

    for sample in ("in_sample", "out_of_sample"):
        print(f"\n--- {sample} ---")
        base = read_trades(POOL, sample)
        link = read_trades(LINK, sample)
        ethg = read_trades(ETHG, sample)

        # 5 components:
        comp_trades = {
            "A_btc_approx": filter_symbol(base, "BTCUSDT"),
            "C_link_spec":  link,
            "D_ltc":        filter_symbol(base, "LTCUSDT"),
            "E_dot":        filter_symbol(base, "DOTUSDT"),
            "G_eth_spec":   ethg,
        }

        for k, v in comp_trades.items():
            print(f"  {k:15s}: {len(v):>4d} trades")

        comp_monthly = {k: aggregate_monthly(v) for k, v in comp_trades.items()}

        all_months = sorted(set(m for d in comp_monthly.values() for m in d))

        # Per-component series (zero-fill inactive months)
        series = {k: [comp_monthly[k].get(m, 0.0) for m in all_months]
                  for k in comp_monthly}

        # Bundle = sum of all 5 component PnL per month
        bundle_series = [sum(s[i] for s in series.values()) for i in range(len(all_months))]

        for k, s in series.items():
            sh = sharpe(s)
            dd = max_dd(s)
            print(f"  {k:15s}  Sharpe={sh:+.4f}  MaxDD={dd:6.2f}%")

        sh_bundle = sharpe(bundle_series)
        dd_bundle = max_dd(bundle_series)
        sum_trades = sum(len(v) for v in comp_trades.values())
        print(f"\n  BUNDLE (sum)    {sum_trades} trades")
        print(f"  BUNDLE Sharpe (monthly sqrt(12)) = {sh_bundle:+.4f}")
        print(f"  BUNDLE MaxDD                     = {dd_bundle:.2f}%")

        # Cross-correlation matrix (10 pairs)
        print("\n  Cross-correlation matrix (Pearson, all months):")
        keys = list(series.keys())
        for i, a in enumerate(keys):
            for j, b in enumerate(keys):
                if i >= j:
                    continue
                p = pearson(series[a], series[b])
                marker = "  !!! ≥ 0.50" if abs(p) >= 0.50 else ""
                print(f"    {a:15s}× {b:15s} = {p:+.4f}{marker}")

        # Comparison to baseline pool (FULL pool, all 5 syms)
        baseline_monthly = aggregate_monthly(base)
        base_series = [baseline_monthly.get(m, 0.0) for m in all_months]
        sh_base = sharpe(base_series)
        dd_base = max_dd(base_series)
        delta_sh = sh_bundle - sh_base
        delta_dd = dd_bundle - dd_base
        print(f"\n  vs baseline pool  Sharpe={sh_base:+.4f}  MaxDD={dd_base:.2f}%")
        print(f"  Bundle Δ:         Sharpe={delta_sh:+.4f}  MaxDD={delta_dd:+.2f}pp")

        # Target check (OOS only)
        if sample == "out_of_sample":
            target_lo = 1.10
            target_hi = 1.30
            print(f"\n  /027 target band [+{target_lo:.2f}, +{target_hi:.2f}] single-seed reference Sharpe:")
            if sh_bundle >= target_lo:
                print(f"    {sh_bundle:+.4f} ≥ {target_lo} → target ACHIEVABLE (sample-of-1)")
            else:
                print(f"    {sh_bundle:+.4f} < {target_lo} → target NOT ACHIEVABLE at single-seed reference")
                print(f"    gap to target lower bound: {target_lo - sh_bundle:+.4f}")

        # Also a daily-Sharpe estimate using monthly_pnl as proxy (sqrt(252) on monthly basis is incorrect;
        # we don't have daily aggregations here. Report monthly only.)

        # Persist
        for k, s in series.items():
            rows_out.append({
                "sample": sample,
                "component": k,
                "n_trades": len(comp_trades[k]),
                "n_months": sum(1 for v in s if v != 0.0),
                "sharpe_monthly_sqrt12": f"{sharpe(s):+.4f}",
                "maxdd_pct": f"{max_dd(s):.2f}",
            })
        rows_out.append({
            "sample": sample,
            "component": "BUNDLE_sum_5_components",
            "n_trades": sum_trades,
            "n_months": sum(1 for v in bundle_series if v != 0.0),
            "sharpe_monthly_sqrt12": f"{sh_bundle:+.4f}",
            "maxdd_pct": f"{dd_bundle:.2f}",
        })
        rows_out.append({
            "sample": sample,
            "component": "BASELINE_FULL_POOL_5_sym",
            "n_trades": len(base),
            "n_months": sum(1 for v in base_series if v != 0.0),
            "sharpe_monthly_sqrt12": f"{sh_base:+.4f}",
            "maxdd_pct": f"{dd_base:.2f}",
        })

    with (ANALYSIS_DIR / "bundle_5model_estimate.csv").open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        wr.writeheader()
        wr.writerows(rows_out)

    print(f"\n  Output: {ANALYSIS_DIR / 'bundle_5model_estimate.csv'}")


if __name__ == "__main__":
    main()
