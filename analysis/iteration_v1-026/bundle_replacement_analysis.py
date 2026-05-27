"""Bundle replacement analysis — what /027 actually bundles.

After diagnose_roster_overlap.py revealed:
- baseline pool: trades all 5 symbols
- LINK specialist (/018): LINK-only, 154 IS / 48 OOS trades
- ETH+gate specialist (/019): ETH-only, 159 IS / 42 OOS trades

The /027 bundle must REPLACE pool's LINK and ETH arms with the specialists,
NOT additively combine the full pool with both specialists (that would
double-count LINK/ETH).

This script:
1. Builds "pool-minus-LINK-and-ETH" (BTC + LTC + DOT trades only).
2. Builds the BUNDLE = pool-minus-LINK-and-ETH + LINK-specialist + ETH-specialist.
3. Aggregates to monthly PnL and reports bundle Sharpe + DD.
4. Cross-correlation among the THREE bundle components (the replacement model).

Compares to baseline pool's actual Sharpe / DD to estimate /027 lift.
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
    path = report_dir / sample / "trades.csv"
    out: list[dict] = []
    with path.open() as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            out.append(row)
    return out


def month_of(close_time_ms_str: str) -> str:
    return datetime.fromtimestamp(int(close_time_ms_str) / 1000, tz=UTC).strftime("%Y-%m")


def aggregate_monthly(trades: list[dict]) -> dict[str, float]:
    """Sum weighted_pnl per month."""
    by_month: dict[str, float] = {}
    for t in trades:
        m = month_of(t["close_time"])
        by_month[m] = by_month.get(m, 0.0) + float(t["weighted_pnl"])
    return by_month


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


def sharpe(returns: list[float], scale: float = math.sqrt(12)) -> float:
    if len(returns) < 2:
        return float("nan")
    mu = sum(returns) / len(returns)
    var = sum((r - mu) ** 2 for r in returns) / (len(returns) - 1)
    sd = math.sqrt(var)
    if sd == 0:
        return float("nan")
    return mu / sd * scale


def max_dd(returns: list[float]) -> float:
    cum = 0.0
    peak = 0.0
    mdd = 0.0
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
    print("iter-v1/026 — Bundle Replacement Analysis (what /027 actually does)")
    print("=" * 70)

    val_rows: list[dict] = []

    for sample in ("in_sample", "out_of_sample"):
        print(f"\n--- {sample} ---")

        pool_trades = read_trades(POOL, sample)
        link_trades = read_trades(LINK, sample)
        ethg_trades = read_trades(ETHG, sample)

        # Pool minus LINK and ETH
        pool_minus_link_eth = [
            t for t in pool_trades if t["symbol"] not in ("LINKUSDT", "ETHUSDT")
        ]

        n_pool = len(pool_trades)
        n_pml = len(pool_minus_link_eth)
        n_link = len(link_trades)
        n_eth = len(ethg_trades)
        bundle_total = n_pml + n_link + n_eth

        print(f"  pool total trades:                  {n_pool}")
        print(f"  pool minus LINK+ETH (BTC+LTC+DOT):  {n_pml}")
        print(f"  LINK specialist (/018):             {n_link}")
        print(f"  ETH+gate specialist (/019):         {n_eth}")
        print(f"  BUNDLE total trades:                {bundle_total}")

        # Trades by symbol in bundle
        bundle_by_sym: dict[str, int] = {}
        for t in pool_minus_link_eth + link_trades + ethg_trades:
            bundle_by_sym[t["symbol"]] = bundle_by_sym.get(t["symbol"], 0) + 1
        print("  Bundle by symbol: " + ", ".join(
            f"{s}={c}" for s, c in sorted(bundle_by_sym.items())
        ))

        # Monthly aggregations
        pool_m = aggregate_monthly(pool_trades)
        pml_m = aggregate_monthly(pool_minus_link_eth)
        link_m = aggregate_monthly(link_trades)
        eth_m = aggregate_monthly(ethg_trades)
        bundle_m: dict[str, float] = {}
        for d in (pml_m, link_m, eth_m):
            for k, v in d.items():
                bundle_m[k] = bundle_m.get(k, 0.0) + v

        # Months sorted
        all_months = sorted(
            set(pool_m) | set(pml_m) | set(link_m) | set(eth_m) | set(bundle_m)
        )

        # Per-month series (zero-fill for inactive component-months)
        pool_series = [pool_m.get(m, 0.0) for m in all_months]
        pml_series = [pml_m.get(m, 0.0) for m in all_months]
        link_series = [link_m.get(m, 0.0) for m in all_months]
        eth_series = [eth_m.get(m, 0.0) for m in all_months]
        bundle_series = [bundle_m.get(m, 0.0) for m in all_months]

        # Sharpe + DD
        sh_pool = sharpe(pool_series)
        sh_pml = sharpe(pml_series)
        sh_link = sharpe(link_series)
        sh_eth = sharpe(eth_series)
        sh_bundle = sharpe(bundle_series)

        dd_pool = max_dd(pool_series)
        dd_pml = max_dd(pml_series)
        dd_link = max_dd(link_series)
        dd_eth = max_dd(eth_series)
        dd_bundle = max_dd(bundle_series)

        print(f"\n  Monthly Sharpe (sqrt(12)) [info; canonical uses daily sqrt(365)]:")
        print(f"    pool                 = {sh_pool:+.4f}   MaxDD={dd_pool:6.2f}%")
        print(f"    pool minus LINK+ETH  = {sh_pml:+.4f}   MaxDD={dd_pml:6.2f}%")
        print(f"    LINK specialist      = {sh_link:+.4f}   MaxDD={dd_link:6.2f}%")
        print(f"    ETH+gate specialist  = {sh_eth:+.4f}   MaxDD={dd_eth:6.2f}%")
        print(f"    BUNDLE (replacement) = {sh_bundle:+.4f}   MaxDD={dd_bundle:6.2f}%")
        print(f"  Bundle Δ vs pool:      Sharpe Δ={sh_bundle - sh_pool:+.4f}  "
              f"MaxDD Δ={dd_bundle - dd_pool:+.2f}pp")

        # Cross-correlation among the 3 REPLACEMENT components
        print("\n  Cross-correlation among 3 REPLACEMENT components (Pearson):")
        comp_series = {
            "pool-minus-LINK+ETH": pml_series,
            "LINK_specialist": link_series,
            "ETH+gate_specialist": eth_series,
        }
        for a in comp_series:
            for b in comp_series:
                if a >= b:
                    continue
                # active-only overlap
                ax = [v for v in comp_series[a]]
                bx = [v for v in comp_series[b]]
                # filter to months where BOTH have nonzero PnL (or zero if both have zero trades)
                # For replacement bundle, all 3 components should be active in most months
                p = pearson(ax, bx)
                print(f"    {a:25s}× {b:25s}: {p:+.4f}")

        # Re-do cross-correlation on ACTIVE-ONLY months (>0 trades in both components)
        print("\n  Cross-correlation (ACTIVE-ONLY months, both >0 trades):")

        # Build per-month trade-count maps
        def trade_count_by_month(trades: list[dict]) -> dict[str, int]:
            out: dict[str, int] = {}
            for t in trades:
                m = month_of(t["close_time"])
                out[m] = out.get(m, 0) + 1
            return out

        tc_pml = trade_count_by_month(pool_minus_link_eth)
        tc_link = trade_count_by_month(link_trades)
        tc_eth = trade_count_by_month(ethg_trades)

        comp_tc = {
            "pool-minus-LINK+ETH": tc_pml,
            "LINK_specialist": tc_link,
            "ETH+gate_specialist": tc_eth,
        }
        comp_m = {
            "pool-minus-LINK+ETH": pml_m,
            "LINK_specialist": link_m,
            "ETH+gate_specialist": eth_m,
        }
        for a in comp_series:
            for b in comp_series:
                if a >= b:
                    continue
                common = sorted(
                    m for m in comp_tc[a]
                    if m in comp_tc[b] and comp_tc[a][m] > 0 and comp_tc[b][m] > 0
                )
                axs = [comp_m[a][m] for m in common]
                bxs = [comp_m[b][m] for m in common]
                p = pearson(axs, bxs)
                print(f"    {a:25s}× {b:25s}: n={len(common):2d}  Pearson={p:+.4f}")

        val_rows.append({
            "sample": sample,
            "n_trades_pool": n_pool,
            "n_trades_pool_minus_link_eth": n_pml,
            "n_trades_link_spec": n_link,
            "n_trades_eth_spec": n_eth,
            "n_trades_bundle": bundle_total,
            "pool_sharpe_monthly": f"{sh_pool:+.4f}",
            "pool_minus_link_eth_sharpe": f"{sh_pml:+.4f}",
            "link_spec_sharpe": f"{sh_link:+.4f}",
            "eth_spec_sharpe": f"{sh_eth:+.4f}",
            "bundle_sharpe_monthly": f"{sh_bundle:+.4f}",
            "bundle_minus_pool_sharpe_delta": f"{sh_bundle - sh_pool:+.4f}",
            "pool_maxdd_pct": f"{dd_pool:.2f}",
            "bundle_maxdd_pct": f"{dd_bundle:.2f}",
            "bundle_minus_pool_maxdd_delta_pp": f"{dd_bundle - dd_pool:+.2f}",
        })

    with (ANALYSIS_DIR / "bundle_replacement_validation.csv").open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(val_rows[0].keys()))
        wr.writeheader()
        wr.writerows(val_rows)

    print("\n  Output: bundle_replacement_validation.csv")


if __name__ == "__main__":
    main()
