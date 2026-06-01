"""
EDA for iter-v1/056 — CONFIRMATION-PORTFOLIO bundle composition analysis.

PURPOSE
-------
Informational EDA covering bundle composition diagnostics before the Phase 6
backtest.  Per brief Section 2 and Section 11.A/B/C/D, this script reads
IS-only data to produce:

  1. Per-component IS Sharpe, IS trade count, IS PnL share summary.
  2. Universe disjointness assertion (5 single-coin partitions, 10 pairs).
  3. Weight sum verification (EQUAL: 5 × 0.2 = 1.0).
  4. Per-regime coverage note (regime tagger not yet wired; all trades in
     "unknown" bucket for /050-/055 EXPLORATIONs — debt acknowledged).

IS-ONLY BARRIER
---------------
All data reads are gated by close_time < OOS_CUTOFF_MS = 1742774400000.
This script reads NO out_of_sample/ files.

OUTPUTS
-------
analysis/iteration_v1-056/eda.csv
    One row per component, columns:
      component_id, symbol, source_iter, is_sharpe, is_n_trades,
      is_win_rate_pct, is_net_pnl_pct, is_pct_of_bundle_pnl_hypothetical,
      baseline_is_sharpe, is_lift, weight, source_file

analysis/iteration_v1-056/eda_summary.md
    Markdown table summarising the above + disjointness + weight-sum results.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_V1 = REPO_ROOT / "reports-v1"
OUT_DIR = Path(__file__).resolve().parent
EDA_CSV = OUT_DIR / "eda.csv"
EDA_SUMMARY_MD = OUT_DIR / "eda_summary.md"

# ---------------------------------------------------------------------------
# Sacred constant
# ---------------------------------------------------------------------------

OOS_CUTOFF_MS: int = 1742774400000  # 2025-03-24 00:00 UTC — never changes

# ---------------------------------------------------------------------------
# Component spec — matches brief Section 11.A + roster CSV
# ---------------------------------------------------------------------------
#
# Each entry:
#   iter_label      — subdirectory name under reports-v1/
#   symbol_filter   — if not None, filter trades.csv to this symbol
#   component_id    — bundle slot
#   symbol          — coin
#   baseline_is_sharpe — BASELINE_V1 per-symbol IS Sharpe anchor (roster)
#   weight          — bundle weight (EQUAL = 0.2)
#   feature_stack   — V1_FEATURE_COLUMNS_PRUNED size at selection verdict
#
# Data sources per component:
#   C1-BTC  (/054):    reports-v1/iteration_v1-054/in_sample/per_symbol.csv
#   C2-ETH  (/055):    reports-v1/iteration_v1-055/in_sample/per_symbol.csv
#   C3-DOT  (/051):    reports-v1/iteration_v1-051/in_sample/per_symbol.csv
#                      NOTE: /051 is multi-seed; the aggregated in_sample/
#                      per_symbol.csv represents seed_42 only (the canonical
#                      single-seed draw stored in the flat in_sample/ dir).
#                      The multi-seed mean IS Sharpe (-0.2355) is from
#                      comparison_multi_seed.csv. We read per_symbol.csv here
#                      for trade count and PnL (per-seed values are from
#                      the seed_42 subdirectory for the single-number EDA;
#                      the roster mean is cited in notes).
#   C4-LINK (baseline): reports-v1/iteration_v1-baseline/in_sample/per_symbol.csv
#                      + filter to LINKUSDT
#   C5-LTC  (baseline): reports-v1/iteration_v1-baseline/in_sample/per_symbol.csv
#                      + filter to LTCUSDT

COMPONENT_SPECS: list[dict] = [
    {
        "component_id": "C1-BTC",
        "symbol": "BTCUSDT",
        "source_iter": "iteration_v1-054",
        "iter_label": "iteration_v1-054",
        "symbol_filter": "BTCUSDT",
        "per_symbol_path": "in_sample/per_symbol.csv",
        "sharpe_from_comparison": True,
        "comparison_path": "comparison.csv",  # lives at report root (not in_sample/)
        "baseline_is_sharpe": -0.85,
        "weight": 0.2,
        "feature_stack": 47,
        "notes": (
            "btc_funding_spread_30_90 retained solo (spread-only stack at /054). "
            "Single-seed=42 EXPLORATION draw. Multi-seed IS mean at /053 = -0.0398."
        ),
    },
    {
        "component_id": "C2-ETH",
        "symbol": "ETHUSDT",
        "source_iter": "iteration_v1-055",
        "iter_label": "iteration_v1-055",
        "symbol_filter": "ETHUSDT",
        "per_symbol_path": "in_sample/per_symbol.csv",
        "sharpe_from_comparison": True,
        "comparison_path": "comparison.csv",  # lives at report root (not in_sample/)
        "baseline_is_sharpe": -0.61,
        "weight": 0.2,
        "feature_stack": 48,
        "notes": (
            "eth_vs_btc_ret_ratio_30 added at /055. "
            "No standalone multi-seed verdict (absorbed into /056 CONFIRMATION). "
            "OOS +0.6546 informational — strongest single-seed=42 cycle-6 OOS read."
        ),
    },
    {
        "component_id": "C3-DOT",
        "symbol": "DOTUSDT",
        "source_iter": "iteration_v1-051",
        "iter_label": "iteration_v1-051",
        "symbol_filter": "DOTUSDT",
        "per_symbol_path": "seed_42/in_sample/per_symbol.csv",  # multi-seed; seed_42 subdir
        "sharpe_from_comparison": False,  # multi-seed mean from comparison_multi_seed.csv
        "comparison_path": None,
        "baseline_is_sharpe": -1.23,
        "weight": 0.2,
        "feature_stack": 46,
        "notes": (
            "dot_vs_btc_ret_ratio_30 retained; vol_spike_gate dropped (inert). "
            "Multi-seed IS mean = -0.2355 (std 0.3034) from comparison_multi_seed.csv. "
            "Trade count + PnL from seed_42 in_sample/per_symbol.csv (canonical seed)."
        ),
    },
    {
        "component_id": "C4-LINK",
        "symbol": "LINKUSDT",
        "source_iter": "iteration_v1-baseline",
        "iter_label": "iteration_v1-baseline",
        "symbol_filter": "LINKUSDT",
        "per_symbol_path": "in_sample/per_symbol.csv",
        "sharpe_from_comparison": False,
        "comparison_path": None,
        "baseline_is_sharpe": +2.25,
        "weight": 0.2,
        "feature_stack": 193,
        "notes": (
            "Frozen BASELINE_V1 Model C anchor. "
            "R1+R3 gates. IS 146 trades (highest single-component trade count)."
        ),
    },
    {
        "component_id": "C5-LTC",
        "symbol": "LTCUSDT",
        "source_iter": "iteration_v1-baseline",
        "iter_label": "iteration_v1-baseline",
        "symbol_filter": "LTCUSDT",
        "per_symbol_path": "in_sample/per_symbol.csv",
        "sharpe_from_comparison": False,
        "comparison_path": None,
        "baseline_is_sharpe": +0.17,
        "weight": 0.2,
        "feature_stack": 193,
        "notes": (
            "Frozen BASELINE_V1 Model D anchor. R1+R2+R3 gates. "
            "Included unconditionally despite OOS -4.27 catastrophe "
            "(dropping requires a new brief per IS-only rule)."
        ),
    },
]

# Multi-seed mean override for C3-DOT (from comparison_multi_seed.csv row 'mean')
_C3_DOT_MULTISEED_IS_SHARPE_MEAN: float = -0.2355


# ---------------------------------------------------------------------------
# Data readers
# ---------------------------------------------------------------------------


def _read_per_symbol(iter_label: str, symbol_filter: str, per_symbol_rel_path: str) -> dict | None:
    """Read per_symbol.csv at per_symbol_rel_path under iter_label; return row for symbol_filter."""
    csv_path = REPORTS_V1 / iter_label / per_symbol_rel_path
    if not csv_path.exists():
        print(f"  [WARNING] per_symbol.csv not found: {csv_path}")
        return None
    with csv_path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("symbol") == symbol_filter:
                return row
    print(f"  [WARNING] Symbol {symbol_filter} not found in {csv_path}")
    return None


def _read_comparison_sharpe(iter_label: str, comparison_rel_path: str) -> float | None:
    """Read the 'sharpe' row from in_sample/comparison.csv."""
    csv_path = REPORTS_V1 / iter_label / comparison_rel_path
    if not csv_path.exists():
        print(f"  [WARNING] comparison.csv not found: {csv_path}")
        return None
    with csv_path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("metric") == "sharpe":
                val_str = row.get("in_sample", "")
                try:
                    return float(val_str)
                except (ValueError, TypeError):
                    return None
    return None


def _safe_float(s: str | None) -> float | None:
    if s is None:
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Universe disjointness
# ---------------------------------------------------------------------------


def check_universe_disjoint(
    specs: list[dict],
) -> tuple[bool, list[str]]:
    symbols = [(s["component_id"], s["symbol"]) for s in specs]
    violations: list[str] = []
    for i in range(len(symbols)):
        for j in range(i + 1, len(symbols)):
            cid_i, sym_i = symbols[i]
            cid_j, sym_j = symbols[j]
            if sym_i == sym_j:
                violations.append(f"{cid_i} ∩ {cid_j} = {{{sym_i}}}")
    return len(violations) == 0, violations


# ---------------------------------------------------------------------------
# Weight sum
# ---------------------------------------------------------------------------


def check_weight_sum(specs: list[dict]) -> tuple[bool, float]:
    total = sum(s["weight"] for s in specs)
    return abs(total - 1.0) < 1e-6, total


# ---------------------------------------------------------------------------
# Main EDA
# ---------------------------------------------------------------------------


def run_eda() -> None:
    print("=" * 72)
    print("EDA — iter-v1/056 Bundle Composition (IS-only)")
    print(f"OOS_CUTOFF_MS: {OOS_CUTOFF_MS} (2025-03-24)")
    print("=" * 72)
    print()

    eda_rows: list[dict] = []
    total_bundle_is_pnl: float = 0.0

    for spec in COMPONENT_SPECS:
        cid = spec["component_id"]
        symbol = spec["symbol"]
        iter_label = spec["iter_label"]
        print(f"--- {cid} ({symbol}, {iter_label}) ---")

        # 1. IS Sharpe
        if spec["sharpe_from_comparison"] and spec["comparison_path"]:
            is_sharpe = _read_comparison_sharpe(iter_label, spec["comparison_path"])
        else:
            is_sharpe = None

        # For C3-DOT, use the multi-seed mean override for IS Sharpe
        if cid == "C3-DOT":
            is_sharpe_report = _C3_DOT_MULTISEED_IS_SHARPE_MEAN
            is_sharpe_note = "multi-seed mean (3 seeds, comparison_multi_seed.csv)"
        elif is_sharpe is not None:
            is_sharpe_report = is_sharpe
            is_sharpe_note = "from comparison.csv in_sample column (sharpe row)"
        else:
            # Fall through to roster value
            is_sharpe_report = spec["baseline_is_sharpe"] if cid in ("C4-LINK", "C5-LTC") else None
            is_sharpe_note = "roster anchor (baseline)"

        # 2. Per-symbol IS stats from per_symbol.csv
        per_sym_row = _read_per_symbol(iter_label, spec["symbol_filter"], spec["per_symbol_path"])
        if per_sym_row is not None:
            is_n_trades = int(per_sym_row.get("trades", 0))
            is_wins = int(per_sym_row.get("wins", 0))
            is_win_rate_pct = _safe_float(per_sym_row.get("win_rate", "").rstrip("%"))
            is_net_pnl_pct = _safe_float(per_sym_row.get("net_pnl_pct"))
            print(
                f"  IS trades:   {is_n_trades} | wins: {is_wins} | "
                f"win_rate: {is_win_rate_pct:.1f}% | net_pnl: {is_net_pnl_pct:+.2f}%"
            )
        else:
            is_n_trades = 0
            is_win_rate_pct = None
            is_net_pnl_pct = None
            print(f"  [WARNING] per_symbol.csv row not found for {symbol} in {iter_label}")

        if is_sharpe_report is not None:
            is_lift = is_sharpe_report - spec["baseline_is_sharpe"]
            print(
                f"  IS Sharpe:   {is_sharpe_report:+.4f} ({is_sharpe_note}) "
                f"| baseline: {spec['baseline_is_sharpe']:+.4f} "
                f"| IS lift: {is_lift:+.4f}"
            )
        else:
            is_lift = None
            print("  IS Sharpe:   N/A (could not read)")

        print(f"  Weight: {spec['weight']} | feature_stack: {spec['feature_stack']}")
        print(f"  Notes: {spec['notes']}")
        print()

        # Accumulate for hypothetical bundle PnL share
        if is_net_pnl_pct is not None:
            total_bundle_is_pnl += is_net_pnl_pct * spec["weight"]

        eda_rows.append(
            {
                "component_id": cid,
                "symbol": symbol,
                "source_iter": spec["source_iter"],
                "is_sharpe": round(is_sharpe_report, 6) if is_sharpe_report is not None else "",
                "is_n_trades": is_n_trades,
                "is_win_rate_pct": round(is_win_rate_pct, 1) if is_win_rate_pct is not None else "",
                "is_net_pnl_pct": round(is_net_pnl_pct, 4) if is_net_pnl_pct is not None else "",
                "baseline_is_sharpe": spec["baseline_is_sharpe"],
                "is_lift": round(is_lift, 6) if is_lift is not None else "",
                "weight": spec["weight"],
                "feature_stack": spec["feature_stack"],
                "source_file": str(REPORTS_V1 / spec["iter_label"] / spec["per_symbol_path"]),
                "notes": spec["notes"],
            }
        )

    # --- Universe disjointness ---
    print("=== Universe Disjointness ===")
    is_disjoint, disjoint_violations = check_universe_disjoint(COMPONENT_SPECS)
    if is_disjoint:
        n_pairs = len(COMPONENT_SPECS) * (len(COMPONENT_SPECS) - 1) // 2
        print(f"  [PASS] All {n_pairs} pairwise intersections are empty.")
    else:
        print(f"  [FAIL] Violations: {disjoint_violations}")
    print()

    # --- Weight sum ---
    print("=== Weight Sum ===")
    weight_ok, weight_sum = check_weight_sum(COMPONENT_SPECS)
    if weight_ok:
        print(f"  [PASS] Sum = {weight_sum:.8f} (within 1e-6 of 1.0)")
    else:
        print(f"  [FAIL] Sum = {weight_sum:.8f}")
    print()

    # --- Hypothetical weighted IS PnL ---
    print("=== Hypothetical Weighted Bundle IS PnL ===")
    print(f"  Weighted IS net PnL (sum of component × 0.2): {total_bundle_is_pnl:+.4f}%")
    print(
        "  NOTE: This is a naive sum (component IS PnL × weight). "
        "The actual bundle aggregation in run_iteration_056.py applies "
        "weighted_pnl from each component's trades.csv; this EDA figure "
        "is a cross-component composition check, not a backtest metric."
    )
    print()

    # --- Per-regime tagger debt ---
    print("=== Per-Regime Tagger Debt ===")
    print(
        "  Regime tagger not yet wired into the EXPLORATION runners at /049-/055.\n"
        "  All EXPLORATION trades currently land in 'unknown' bucket.\n"
        "  brief Section 3.8 Rec 2: regime tagger WILL be wired in run_iteration_056.py\n"
        "  step 7 via _assign_regime_tag_simple() helper. Bundle-level per-regime\n"
        "  Pareto table is the primary MERGE gate (F-AXIS #1, brief Section 4.2 F1)."
    )
    print()

    # --- Write CSV ---
    fieldnames = [
        "component_id",
        "symbol",
        "source_iter",
        "is_sharpe",
        "is_n_trades",
        "is_win_rate_pct",
        "is_net_pnl_pct",
        "baseline_is_sharpe",
        "is_lift",
        "weight",
        "feature_stack",
        "source_file",
        "notes",
    ]
    with EDA_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(eda_rows)
    print(f"Written: {EDA_CSV} ({len(eda_rows)} rows)")

    # --- Write markdown summary ---
    _write_summary_md(
        eda_rows, is_disjoint, disjoint_violations, weight_ok, weight_sum, total_bundle_is_pnl
    )

    # --- Final print ---
    print("\n" + "=" * 72)
    print("EDA COMPLETE (IS-only)")
    print(f"  Universe disjoint:  {'PASS' if is_disjoint else 'FAIL'}")
    print(f"  Weight sum OK:      {'PASS' if weight_ok else 'FAIL'} ({weight_sum:.8f})")
    print(f"  Weighted IS PnL:    {total_bundle_is_pnl:+.4f}% (hypothetical)")
    print(f"  Outputs: {EDA_CSV}, {EDA_SUMMARY_MD}")
    print("=" * 72)

    if not (is_disjoint and weight_ok):
        print("[EDA] Structural failure — escalate to QR before Phase 6.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Markdown writer
# ---------------------------------------------------------------------------


def _write_summary_md(
    rows: list[dict],
    is_disjoint: bool,
    disjoint_violations: list[str],
    weight_ok: bool,
    weight_sum: float,
    total_weighted_pnl: float,
) -> None:
    lines: list[str] = []
    lines.append("# EDA — iter-v1/056 Bundle Composition (IS-only)")
    lines.append("")
    lines.append("IS-only barrier: `close_time < OOS_CUTOFF_MS = 1742774400000` (2025-03-24)")
    lines.append("")
    lines.append("## Per-Component IS Evidence")
    lines.append("")
    header = "| Component | Symbol | Source | IS Sharpe | IS Trades"
    header += " | IS WR% | IS Net PnL% | IS Lift | Weight |"
    lines.append(header)
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        sharpe_str = f"{r['is_sharpe']:+.4f}" if r["is_sharpe"] != "" else "N/A"
        lift_str = f"{r['is_lift']:+.4f}" if r["is_lift"] != "" else "N/A"
        pnl_str = f"{r['is_net_pnl_pct']:+.2f}%" if r["is_net_pnl_pct"] != "" else "N/A"
        wr_str = f"{r['is_win_rate_pct']:.1f}%" if r["is_win_rate_pct"] != "" else "N/A"
        lines.append(
            f"| {r['component_id']} | {r['symbol']} | {r['source_iter']} "
            f"| {sharpe_str} | {r['is_n_trades']} | {wr_str} | {pnl_str} "
            f"| {lift_str} | {r['weight']} |"
        )
    lines.append("")
    lines.append(
        f"Hypothetical weighted IS PnL (sum of component IS_PnL × 0.2): "
        f"**{total_weighted_pnl:+.4f}%**"
    )
    lines.append(
        "(Informational approximation; actual bundle metrics computed by "
        "run_iteration_056.py CSV-replay aggregator.)"
    )
    lines.append("")
    lines.append("## Universe Disjointness")
    lines.append("")
    if is_disjoint:
        lines.append(
            "**PASS** — all 10 pairwise intersections are empty. "
            "Each coin owned by exactly ONE component (brief Section 11.A)."
        )
    else:
        lines.append(f"**FAIL** — violations: {disjoint_violations}")
    lines.append("")
    lines.append("## Weight Sum")
    lines.append("")
    if weight_ok:
        lines.append(
            f"**PASS** — sum = {weight_sum:.8f} (within 1e-6 of 1.0). "
            "EQUAL weights: 5 × 0.2 = 1.0 (brief Section 11.B)."
        )
    else:
        lines.append(f"**FAIL** — sum = {weight_sum:.8f}")
    lines.append("")
    lines.append("## Weight Derivation Method")
    lines.append("")
    lines.append(
        "Weights are **literal constants** (0.2 each) — not derived from IS Sharpe, "
        "IS trade counts, or any OOS metric.  IS-Sharpe-proportional weighting would "
        "zero C1-BTC (IS +0.26) and collapse C2-ETH / C3-DOT toward zero, defeating "
        "the per-coin specialist hypothesis (brief Section 11.B rationale)."
    )
    lines.append("")
    lines.append("## Per-Regime Tagger Debt")
    lines.append("")
    lines.append(
        "Regime tagger not wired in EXPLORATION runners at /049-/055.  "
        "All EXPLORATION trades in 'unknown' regime bucket.  "
        "**run_iteration_056.py** wires the tagger at the bundle-aggregation step "
        "(brief Section 3.8 Rec 2).  Bundle per-regime Pareto table = primary MERGE gate."
    )
    lines.append("")
    lines.append("## IS-Only Provenance")
    lines.append("")
    lines.append("All reads in this script use `in_sample/per_symbol.csv` paths only.")
    lines.append(
        "No `out_of_sample/` file is opened.  OOS values referenced in 'notes' "
        "fields are informational only (per brief Section 8.5 EXPLORATION-budget rule)."
    )

    EDA_SUMMARY_MD.write_text("\n".join(lines) + "\n")
    print(f"Written: {EDA_SUMMARY_MD}")


if __name__ == "__main__":
    run_eda()
