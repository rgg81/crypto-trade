"""iter-v1/021 EDA — Three-cohort outcome table.

Reads baseline + /018 LINK-only + /019 ETH+gate + /020 BTC-only per-symbol
attribution and produces a single table establishing the three-cohort
comparison that motivates the methodology-pivot diagnostic.

OUTPUT: analysis/iteration_v1-021/three_cohort_outcome_table.csv

The table establishes the principle: per-cohort isolation succeeds only when
either (a) the cohort has an independent positive prior at pool level OR
(b) an orthogonal mechanism is added on top of isolation.

IS-only by construction — reads pre-existing comparison.csv and per-symbol
CSV files from /018, /019, /020 reports + baseline. NO model retraining,
NO OOS peek beyond what /018/019/020 already saw at Phase 7.

This produces the evidence base for brief Section 2.
"""

from __future__ import annotations

import csv
from pathlib import Path

REPORTS_V1 = Path(__file__).resolve().parents[2] / "reports-v1"
OUT_DIR = Path(__file__).resolve().parent
OUT_DIR.mkdir(parents=True, exist_ok=True)


def read_per_symbol(report_dir: Path, split: str) -> dict[str, dict[str, str]]:
    """Read per_symbol.csv from a report dir's in_sample/ or out_of_sample/."""
    path = report_dir / split / "per_symbol.csv"
    if not path.exists():
        return {}
    rows: dict[str, dict[str, str]] = {}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sym = row.get("symbol", "")
            rows[sym] = row
    return rows


def read_comparison(report_dir: Path) -> dict[str, dict[str, str]]:
    """Read comparison.csv and key by metric."""
    path = report_dir / "comparison.csv"
    if not path.exists():
        return {}
    rows: dict[str, dict[str, str]] = {}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            metric = row.get("metric", "")
            rows[metric] = row
    return rows


def to_float(s: str | None) -> float:
    """Convert a comparison-csv string ('+33.17%' or '-0.5566') to float."""
    if s is None:
        return float("nan")
    s = s.strip().rstrip("%")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def main() -> None:
    # Cohort axis registry — (cohort, source iteration, label, isolation type, prior class).
    # Each row records: how the cohort was isolated, what mechanism (if any) was added,
    # what its baseline pool-level OOS contribution was, what the isolation produced.
    cohort_specs = [
        # (label, cohort_symbol, report_iter, isolation_mode, knob_added, prior_class)
        ("BTC_in_pool_baseline", "BTCUSDT", "iteration_v1-baseline", "pool", "none", "ASYMMETRIC_ROTATION"),
        ("LINK_in_pool_baseline", "LINKUSDT", "iteration_v1-baseline", "pool", "none", "POSITIVE_EVERYWHERE"),
        ("ETH_in_pool_baseline", "ETHUSDT", "iteration_v1-baseline", "pool", "none", "NEGATIVE_EVERYWHERE"),
        ("LINK_only_018", "LINKUSDT", "iteration_v1-018", "single_cohort", "none", "POSITIVE_EVERYWHERE"),
        ("ETH_only_plus_gate_019", "ETHUSDT", "iteration_v1-019", "single_cohort", "BTC_trend_gate", "NEGATIVE_EVERYWHERE"),
        ("BTC_only_020", "BTCUSDT", "iteration_v1-020", "single_cohort", "none", "ASYMMETRIC_ROTATION"),
    ]

    out_rows: list[dict[str, str]] = []
    for label, sym, iter_id, isolation, knob, prior_class in cohort_specs:
        report_dir = REPORTS_V1 / iter_id
        is_per = read_per_symbol(report_dir, "in_sample")
        oos_per = read_per_symbol(report_dir, "out_of_sample")
        cmp_rows = read_comparison(report_dir)

        is_sym = is_per.get(sym, {})
        oos_sym = oos_per.get(sym, {})

        # Portfolio Sharpe from comparison.csv
        sharpe_row = cmp_rows.get("sharpe", {})
        is_portfolio_sharpe = sharpe_row.get("in_sample", "")
        oos_portfolio_sharpe = sharpe_row.get("out_of_sample", "")

        out_rows.append(
            {
                "label": label,
                "cohort_symbol": sym,
                "iteration": iter_id,
                "isolation_mode": isolation,
                "knob_added": knob,
                "prior_class": prior_class,
                "is_trades": is_sym.get("trades", ""),
                "is_win_rate": is_sym.get("win_rate", ""),
                "is_net_pnl_pct": is_sym.get("net_pnl_pct", ""),
                "oos_trades": oos_sym.get("trades", ""),
                "oos_win_rate": oos_sym.get("win_rate", ""),
                "oos_net_pnl_pct": oos_sym.get("net_pnl_pct", ""),
                "portfolio_is_sharpe": is_portfolio_sharpe,
                "portfolio_oos_sharpe": oos_portfolio_sharpe,
            }
        )

    out_path = OUT_DIR / "three_cohort_outcome_table.csv"
    fieldnames = list(out_rows[0].keys())
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {out_path}")
    print()
    print("THREE-COHORT OUTCOME TABLE — establishes per-cohort isolation principle:")
    print()
    for row in out_rows:
        sym = row["cohort_symbol"]
        label = row["label"]
        prior = row["prior_class"]
        knob = row["knob_added"]
        is_p = row["is_net_pnl_pct"]
        oos_p = row["oos_net_pnl_pct"]
        print(
            f"  {label:36s} sym={sym:8s} prior={prior:22s} "
            f"knob={knob:18s} IS_net_pnl={is_p:>9s} OOS_net_pnl={oos_p:>9s}"
        )


if __name__ == "__main__":
    main()
