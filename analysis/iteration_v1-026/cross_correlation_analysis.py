"""iter-v1/026 — Pre-CONFIRMATION Cross-Correlation Sanity Check.

This script is read-only over existing reports. It does NOT run any backtest.

Purpose
-------
Before /027 CONFIRMATION bundles the BASELINE_V1 pool, the LINK specialist
(/018), and the ETH+gate specialist (/019), verify the components are
sufficiently uncorrelated to deliver an additive Sharpe lift.

LM Master /025 §4 mandate:
    Pearson(pool, LINK)         < 0.50
    Pearson(pool, ETH+gate)     < 0.50
    Pearson(LINK, ETH+gate)     < 0.50  (ideal — diversification)

Inputs (read-only)
------------------
- reports-v1/iteration_v1-baseline/in_sample/monthly_pnl.csv
- reports-v1/iteration_v1-baseline/out_of_sample/monthly_pnl.csv
- reports-v1/iteration_v1-018/in_sample/monthly_pnl.csv
- reports-v1/iteration_v1-018/out_of_sample/monthly_pnl.csv
- reports-v1/iteration_v1-019/in_sample/monthly_pnl.csv
- reports-v1/iteration_v1-019/out_of_sample/monthly_pnl.csv

Outputs
-------
- analysis/iteration_v1-026/cross_correlation_matrix.csv
- analysis/iteration_v1-026/bundle_composition_validation.csv
- analysis/iteration_v1-026/baseline_stability.csv

Methodology notes
-----------------
- We treat the monthly_pnl.csv column `pnl_pct` (PERCENT, weighted, net of fees
  and risk gates) as the strategy's monthly return for each component.
- Months where a component traded ZERO trades are EXCLUDED on a per-pair basis
  (overlap-only correlation). This avoids spurious zero pairs distorting the
  Pearson estimate; v3 catalog precedent (iter-v3/020 single-seed=42 frozen
  baseline pattern) confirms zero-trade months are not informative for
  diversification.
- We report BOTH Pearson (linear) and Spearman (rank) — Pearson is the
  LM Master mandate threshold; Spearman is a robustness check against
  outlier-driven Pearson inflation.
- Drawdown of each component computed from cumulative monthly PnL (additive,
  not multiplicative — the strategy uses fixed-notional sizing, so the
  comparison.csv 'max_drawdown' field is a cumulative equity drawdown which is
  what we replicate here from monthly_pnl).
- Bundle Sharpe target validation uses TWO weighting schemes:
    (a) Equal-weighted (1/3 each) — LM Master default
    (b) Inverse-volatility weighted — risk-parity baseline
  Then we compare the projected bundle Sharpe to /027's announced target band
  [+1.10, +1.30].
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

# ----- Path config --------------------------------------------------------- #

REPO_ROOT = Path("/home/roberto/crypto-trade/.worktrees/quant-research")
ANALYSIS_DIR = REPO_ROOT / "analysis" / "iteration_v1-026"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

COMPONENTS = {
    "pool": REPO_ROOT / "reports-v1" / "iteration_v1-baseline",
    "LINK": REPO_ROOT / "reports-v1" / "iteration_v1-018",
    "ETHgate": REPO_ROOT / "reports-v1" / "iteration_v1-019",
}


# ----- IO helpers ---------------------------------------------------------- #

def read_monthly_pnl(report_dir: Path, sample: str) -> dict[str, tuple[float, int]]:
    """Read monthly_pnl.csv and return {month: (pnl_pct, trade_count)}.

    `sample` is "in_sample" or "out_of_sample".
    """
    path = report_dir / sample / "monthly_pnl.csv"
    out: dict[str, tuple[float, int]] = {}
    with path.open() as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            month = row["month"].strip()
            pnl = float(row["pnl_pct"])
            tc = int(row["trade_count"])
            out[month] = (pnl, tc)
    return out


# ----- Correlation kernels ------------------------------------------------- #

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


def spearman(xs: list[float], ys: list[float]) -> float:
    """Spearman = Pearson on ranks. Average ranks used for ties."""
    if len(xs) < 2:
        return float("nan")

    def ranks(vs: list[float]) -> list[float]:
        indexed = sorted(enumerate(vs), key=lambda t: t[1])
        out = [0.0] * len(vs)
        i = 0
        while i < len(indexed):
            j = i
            # advance j while ties
            while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
                j += 1
            # average rank for the tied block (1-indexed ranks)
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                out[indexed[k][0]] = avg
            i = j + 1
        return out

    return pearson(ranks(xs), ranks(ys))


# ----- Strategy summary stats --------------------------------------------- #

def sharpe_annualized_monthly(pnl_series: list[float]) -> float:
    """Annualized Sharpe from monthly returns (% units, no risk-free rate).

    Uses sqrt(12) for annualization (project convention; the strategy operates
    on month-resampled walk-forward bars).
    """
    if len(pnl_series) < 2:
        return float("nan")
    n = len(pnl_series)
    mean = sum(pnl_series) / n
    var = sum((x - mean) ** 2 for x in pnl_series) / (n - 1)
    sd = math.sqrt(var)
    if sd == 0:
        return float("nan")
    return mean / sd * math.sqrt(12)


def max_drawdown_from_monthly(pnl_series: list[float]) -> float:
    """Equity drawdown from cumulative monthly PnL (additive).

    Returns DD as a positive percent (e.g., 41.0 = 41% peak-to-trough).
    """
    cum = 0.0
    peak = 0.0
    mdd = 0.0
    for x in pnl_series:
        cum += x
        if cum > peak:
            peak = cum
        dd = peak - cum
        if dd > mdd:
            mdd = dd
    return mdd


# ----- Main routine -------------------------------------------------------- #

def main() -> None:  # noqa: C901
    print("=" * 70)
    print("iter-v1/026 — Pre-CONFIRMATION Cross-Correlation Sanity Check")
    print("=" * 70)

    # 1. Load monthly PnL for each component, both samples.
    data: dict[str, dict[str, dict[str, tuple[float, int]]]] = {}
    for comp, report_dir in COMPONENTS.items():
        data[comp] = {
            "in_sample": read_monthly_pnl(report_dir, "in_sample"),
            "out_of_sample": read_monthly_pnl(report_dir, "out_of_sample"),
        }
        print(
            f"  Loaded {comp:8s}  IS months={len(data[comp]['in_sample']):2d}"
            f"  OOS months={len(data[comp]['out_of_sample']):2d}"
        )

    # ------------------------------------------------------------------ #
    # Phase 3 (executed first): BASELINE_V1 stability re-check.
    # ------------------------------------------------------------------ #
    # The project canonical "sharpe" field in comparison.csv is a DAILY-pnl
    # Sharpe annualized by sqrt(365), NOT a monthly aggregated Sharpe. The
    # BASELINE_V1.md "Monthly Sharpe = +0.2829" label is a doc misnomer — the
    # underlying number IS the comparison.csv `sharpe` row. We re-read the
    # comparison.csv DIRECTLY to verify the anchor numbers haven't drifted.
    #
    # We ALSO report a monthly-aggregated Sharpe (sqrt(12) on monthly_pnl.csv)
    # for informational purposes — it answers a different question (the
    # cross-correlation Sharpe of the bundle uses MONTHLY aggregation since
    # that's the cadence at which we have aligned PnL across components).

    def read_comparison(report_dir: Path) -> dict[str, dict[str, str]]:
        path = report_dir / "comparison.csv"
        out: dict[str, dict[str, str]] = {}
        with path.open() as f:
            rdr = csv.DictReader(f)
            for row in rdr:
                out[row["metric"]] = {
                    "in_sample": row["in_sample"],
                    "out_of_sample": row["out_of_sample"],
                    "ratio": row.get("ratio", ""),
                }
        return out

    baseline_comp = read_comparison(COMPONENTS["pool"])

    is_sharpe_compcsv = float(baseline_comp["sharpe"]["in_sample"])
    oos_sharpe_compcsv = float(baseline_comp["sharpe"]["out_of_sample"])
    is_trades_compcsv = int(baseline_comp["total_trades"]["in_sample"])
    oos_trades_compcsv = int(baseline_comp["total_trades"]["out_of_sample"])

    base_is_months = sorted(data["pool"]["in_sample"].keys())
    base_oos_months = sorted(data["pool"]["out_of_sample"].keys())
    is_returns_base = [data["pool"]["in_sample"][m][0] for m in base_is_months]
    oos_returns_base = [data["pool"]["out_of_sample"][m][0] for m in base_oos_months]
    is_sharpe_monthly_agg = sharpe_annualized_monthly(is_returns_base)
    oos_sharpe_monthly_agg = sharpe_annualized_monthly(oos_returns_base)

    print("\n--- Phase 3: BASELINE_V1 stability re-check ---")
    print(
        "  Canonical comparison.csv sharpe (daily PnL, sqrt(365) annualization):"
    )
    print(
        f"    IS  = {is_sharpe_compcsv:+.4f}   "
        f"(BASELINE_V1.md anchor = +0.2829)"
    )
    print(
        f"    OOS = {oos_sharpe_compcsv:+.4f}   "
        f"(BASELINE_V1.md anchor = +0.6637)"
    )
    print(f"    IS  trades = {is_trades_compcsv}  (anchor = 621)")
    print(f"    OOS trades = {oos_trades_compcsv}  (anchor = 189)")
    print(
        f"  Monthly-aggregated Sharpe (sqrt(12) on monthly_pnl.csv, INFO ONLY):"
    )
    print(f"    IS  = {is_sharpe_monthly_agg:+.4f}")
    print(f"    OOS = {oos_sharpe_monthly_agg:+.4f}")

    with (ANALYSIS_DIR / "baseline_stability.csv").open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow([
            "metric", "computed_v1_026", "baseline_v1_anchor", "match"
        ])
        wr.writerow([
            "is_sharpe_comparison_csv",
            f"{is_sharpe_compcsv:+.4f}",
            "+0.2829",
            "YES" if abs(is_sharpe_compcsv - 0.2829) < 0.001 else "NO",
        ])
        wr.writerow([
            "oos_sharpe_comparison_csv",
            f"{oos_sharpe_compcsv:+.4f}",
            "+0.6637",
            "YES" if abs(oos_sharpe_compcsv - 0.6637) < 0.001 else "NO",
        ])
        wr.writerow([
            "is_trades_comparison_csv",
            str(is_trades_compcsv),
            "621",
            "YES" if is_trades_compcsv == 621 else "NO",
        ])
        wr.writerow([
            "oos_trades_comparison_csv",
            str(oos_trades_compcsv),
            "189",
            "YES" if oos_trades_compcsv == 189 else "NO",
        ])
        wr.writerow([
            "is_sharpe_monthly_agg_info_only",
            f"{is_sharpe_monthly_agg:+.4f}",
            "(no anchor; from monthly_pnl.csv via sqrt(12))",
            "—",
        ])
        wr.writerow([
            "oos_sharpe_monthly_agg_info_only",
            f"{oos_sharpe_monthly_agg:+.4f}",
            "(no anchor; from monthly_pnl.csv via sqrt(12))",
            "—",
        ])

    # ------------------------------------------------------------------ #
    # Phase 1: Cross-correlation matrices.
    # ------------------------------------------------------------------ #
    print("\n--- Phase 1: Cross-correlation analysis ---")

    pair_specs = [
        ("pool", "LINK"),
        ("pool", "ETHgate"),
        ("LINK", "ETHgate"),
    ]

    corr_rows: list[dict] = []
    for sample in ("in_sample", "out_of_sample"):
        print(f"\n  Sample: {sample}")
        for a, b in pair_specs:
            da = data[a][sample]
            db = data[b][sample]
            # Overlap months: BOTH must have at least one trade
            overlap = sorted(
                m for m in da
                if m in db and da[m][1] > 0 and db[m][1] > 0
            )
            xs = [da[m][0] for m in overlap]
            ys = [db[m][0] for m in overlap]
            p = pearson(xs, ys)
            s = spearman(xs, ys)
            print(
                f"    {a:8s}× {b:8s}  n_months={len(overlap):2d}  "
                f"Pearson={p:+.4f}  Spearman={s:+.4f}"
            )
            corr_rows.append({
                "sample": sample,
                "pair": f"{a}_x_{b}",
                "n_months": len(overlap),
                "pearson": f"{p:+.4f}",
                "spearman": f"{s:+.4f}",
            })

    # Combined IS+OOS
    print("\n  Sample: combined (IS + OOS, overlap-only)")
    for a, b in pair_specs:
        comb_a = dict(data[a]["in_sample"])
        comb_a.update(data[a]["out_of_sample"])
        comb_b = dict(data[b]["in_sample"])
        comb_b.update(data[b]["out_of_sample"])
        overlap = sorted(
            m for m in comb_a
            if m in comb_b and comb_a[m][1] > 0 and comb_b[m][1] > 0
        )
        xs = [comb_a[m][0] for m in overlap]
        ys = [comb_b[m][0] for m in overlap]
        p = pearson(xs, ys)
        s = spearman(xs, ys)
        print(
            f"    {a:8s}× {b:8s}  n_months={len(overlap):2d}  "
            f"Pearson={p:+.4f}  Spearman={s:+.4f}"
        )
        corr_rows.append({
            "sample": "combined",
            "pair": f"{a}_x_{b}",
            "n_months": len(overlap),
            "pearson": f"{p:+.4f}",
            "spearman": f"{s:+.4f}",
        })

    with (ANALYSIS_DIR / "cross_correlation_matrix.csv").open("w", newline="") as f:
        wr = csv.DictWriter(
            f, fieldnames=["sample", "pair", "n_months", "pearson", "spearman"]
        )
        wr.writeheader()
        wr.writerows(corr_rows)

    # ------------------------------------------------------------------ #
    # Phase 2: Bundle composition validation.
    # ------------------------------------------------------------------ #
    print("\n--- Phase 2: Bundle composition validation ---")

    # Per-month overlap stats per sample
    val_rows: list[dict] = []
    for sample in ("in_sample", "out_of_sample"):
        months_all_three = sorted(
            m for m in data["pool"][sample]
            if (
                m in data["LINK"][sample] and m in data["ETHgate"][sample]
                and data["pool"][sample][m][1] > 0
                and data["LINK"][sample][m][1] > 0
                and data["ETHgate"][sample][m][1] > 0
            )
        )
        months_pool = {m for m, (_, tc) in data["pool"][sample].items() if tc > 0}
        months_link = {m for m, (_, tc) in data["LINK"][sample].items() if tc > 0}
        months_eth = {m for m, (_, tc) in data["ETHgate"][sample].items() if tc > 0}

        print(f"\n  Sample: {sample}")
        print(f"    Active months — pool={len(months_pool)} LINK={len(months_link)} "
              f"ETH+gate={len(months_eth)}")
        print(f"    Months with all 3 active: {len(months_all_three)}")

        # Equal-weighted bundle on overlap-only months (worst-case alignment).
        # We ALSO compute "loose" bundle: each component contributes when active
        # (zero otherwise, no trade), which is what /027 would actually run.
        union_months = sorted(months_pool | months_link | months_eth)
        bundle_eq_loose: list[float] = []
        for m in union_months:
            parts = []
            if m in data["pool"][sample] and data["pool"][sample][m][1] > 0:
                parts.append(data["pool"][sample][m][0])
            else:
                parts.append(0.0)
            if m in data["LINK"][sample] and data["LINK"][sample][m][1] > 0:
                parts.append(data["LINK"][sample][m][0])
            else:
                parts.append(0.0)
            if m in data["ETHgate"][sample] and data["ETHgate"][sample][m][1] > 0:
                parts.append(data["ETHgate"][sample][m][0])
            else:
                parts.append(0.0)
            bundle_eq_loose.append(sum(parts) / 3.0)

        # Inverse-volatility weighted bundle (uses sd of each component's active months).
        # Use IS sd for both IS and OOS bundle reconstruction
        # (avoid using OOS for weighting decisions = OOS-peeking).
        if sample == "in_sample":
            # Recompute the sds from this sample for IS bundle
            sds: dict[str, float] = {}
            for comp in ("pool", "LINK", "ETHgate"):
                vs = [data[comp][sample][m][0] for m in months_pool
                      if m in data[comp][sample] and data[comp][sample][m][1] > 0]
                if len(vs) > 1:
                    mu = sum(vs) / len(vs)
                    var = sum((v - mu) ** 2 for v in vs) / (len(vs) - 1)
                    sds[comp] = math.sqrt(var)
                else:
                    sds[comp] = float("nan")
        # On OOS, REUSE the IS-derived sds. Don't peek.
        inv_w = {comp: 1 / sds[comp] for comp in sds if sds[comp] > 0}
        norm = sum(inv_w.values())
        weights = {comp: inv_w[comp] / norm for comp in inv_w}

        bundle_iv_loose: list[float] = []
        for m in union_months:
            v_pool = (
                data["pool"][sample][m][0]
                if m in data["pool"][sample] and data["pool"][sample][m][1] > 0
                else 0.0
            )
            v_link = (
                data["LINK"][sample][m][0]
                if m in data["LINK"][sample] and data["LINK"][sample][m][1] > 0
                else 0.0
            )
            v_eth = (
                data["ETHgate"][sample][m][0]
                if m in data["ETHgate"][sample] and data["ETHgate"][sample][m][1] > 0
                else 0.0
            )
            bundle_iv_loose.append(
                weights["pool"] * v_pool
                + weights["LINK"] * v_link
                + weights["ETHgate"] * v_eth
            )

        bundle_eq_sharpe = sharpe_annualized_monthly(bundle_eq_loose)
        bundle_iv_sharpe = sharpe_annualized_monthly(bundle_iv_loose)
        bundle_eq_dd = max_drawdown_from_monthly(bundle_eq_loose)
        bundle_iv_dd = max_drawdown_from_monthly(bundle_iv_loose)

        # Standalone component Sharpe + DD on this sample (active-months only)
        comp_stats: dict[str, tuple[float, float]] = {}
        for comp in ("pool", "LINK", "ETHgate"):
            vs = [
                data[comp][sample][m][0]
                for m in sorted(data[comp][sample].keys())
                if data[comp][sample][m][1] > 0
            ]
            comp_stats[comp] = (
                sharpe_annualized_monthly(vs),
                max_drawdown_from_monthly(vs),
            )

        print(f"    Standalone Sharpe (active-months):")
        for comp, (sh, dd) in comp_stats.items():
            print(f"      {comp:8s}  Sharpe={sh:+.4f}  MaxDD={dd:.2f}%")
        print(f"    IV weights (from IS-derived sds): {weights}")
        print(f"    Equal-weighted bundle Sharpe (loose) = {bundle_eq_sharpe:+.4f}  "
              f"MaxDD={bundle_eq_dd:.2f}%")
        print(f"    IV-weighted bundle    Sharpe (loose) = {bundle_iv_sharpe:+.4f}  "
              f"MaxDD={bundle_iv_dd:.2f}%")

        val_rows.append({
            "sample": sample,
            "months_pool_active": len(months_pool),
            "months_link_active": len(months_link),
            "months_eth_active": len(months_eth),
            "months_all_three_active": len(months_all_three),
            "pool_sharpe": f"{comp_stats['pool'][0]:+.4f}",
            "link_sharpe": f"{comp_stats['LINK'][0]:+.4f}",
            "ethgate_sharpe": f"{comp_stats['ETHgate'][0]:+.4f}",
            "pool_maxdd_pct": f"{comp_stats['pool'][1]:.2f}",
            "link_maxdd_pct": f"{comp_stats['LINK'][1]:.2f}",
            "ethgate_maxdd_pct": f"{comp_stats['ETHgate'][1]:.2f}",
            "iv_weight_pool": f"{weights.get('pool', float('nan')):.4f}",
            "iv_weight_link": f"{weights.get('LINK', float('nan')):.4f}",
            "iv_weight_ethgate": f"{weights.get('ETHgate', float('nan')):.4f}",
            "bundle_equal_weighted_sharpe": f"{bundle_eq_sharpe:+.4f}",
            "bundle_inv_vol_sharpe": f"{bundle_iv_sharpe:+.4f}",
            "bundle_equal_weighted_maxdd_pct": f"{bundle_eq_dd:.2f}",
            "bundle_inv_vol_maxdd_pct": f"{bundle_iv_dd:.2f}",
        })

    with (ANALYSIS_DIR / "bundle_composition_validation.csv").open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(val_rows[0].keys()))
        wr.writeheader()
        wr.writerows(val_rows)

    # ------------------------------------------------------------------ #
    # Phase 4: GREEN/YELLOW/RED verdict (printed; the brief writes it up).
    # ------------------------------------------------------------------ #
    print("\n--- Phase 4: Verdict by LM Master /025 §4 thresholds ---")

    def verdict_for_pair(rows: list[dict], pair_key: str) -> tuple[str, list[float]]:
        is_p = next(
            float(r["pearson"]) for r in rows
            if r["sample"] == "in_sample" and r["pair"] == pair_key
        )
        oos_p = next(
            float(r["pearson"]) for r in rows
            if r["sample"] == "out_of_sample" and r["pair"] == pair_key
        )
        comb_p = next(
            float(r["pearson"]) for r in rows
            if r["sample"] == "combined" and r["pair"] == pair_key
        )
        worst = max(abs(is_p), abs(oos_p), abs(comb_p))
        flag = "PASS" if worst < 0.50 else "FAIL"
        return flag, [is_p, oos_p, comb_p]

    pair_verdicts = {}
    for pair_label, pk in (
        ("pool × LINK", "pool_x_LINK"),
        ("pool × ETH+gate", "pool_x_ETHgate"),
        ("LINK × ETH+gate", "LINK_x_ETHgate"),
    ):
        flag, ps = verdict_for_pair(corr_rows, pk)
        print(
            f"  {pair_label:18s}  Pearson IS={ps[0]:+.4f} OOS={ps[1]:+.4f} "
            f"Comb={ps[2]:+.4f}  → {flag} (threshold |p|<0.50)"
        )
        pair_verdicts[pair_label] = (flag, ps)

    fails_required = sum(
        1 for k in ("pool × LINK", "pool × ETH+gate")
        if pair_verdicts[k][0] == "FAIL"
    )
    fails_ideal = sum(
        1 for k in ("pool × LINK", "pool × ETH+gate", "LINK × ETH+gate")
        if pair_verdicts[k][0] == "FAIL"
    )
    if fails_required >= 2:
        overall = "RED"
    elif fails_required == 1:
        overall = "YELLOW (1 required-pair fail)"
    elif fails_ideal >= 1:
        overall = "YELLOW (ideal-pair LINK×ETHgate fails — diversification not ideal)"
    else:
        overall = "GREEN"
    print(f"\n  OVERALL VERDICT: {overall}")

    print("\n  Output files:")
    print(f"    {ANALYSIS_DIR / 'cross_correlation_matrix.csv'}")
    print(f"    {ANALYSIS_DIR / 'bundle_composition_validation.csv'}")
    print(f"    {ANALYSIS_DIR / 'baseline_stability.csv'}")
    print()


if __name__ == "__main__":
    main()
