"""iter-v1/017 — Phase 1 EDA: ETH structural OOS drag analysis (3-axis evidence).

Per Critic /016 Rec #2 NON-NEGOTIABLE: /017 brief Section 2 MUST acknowledge
ETH OOS catastrophic STRUCTURAL across /014 (labeling) / /015 (multi-seed labeling)
/ /016 (sample-weighting) and pre-register either (a) universe-expansion-as-dilution
test OR (b) ETH-specific kill switch.

This script:
1. Loads per-symbol OOS PnL across /014, /015, /016 from existing comparison.csv.
2. Computes ETH share of OOS PnL denominator for each iteration.
3. Predicts denominator-dilution effect of adding SOL (and XRP) to the universe.
4. Tests the regime-bound vs universe-bound hypothesis explicitly.

ETH OOS pattern is computed from already-committed iteration reports.
No model training or labeling occurs.

Writes:
- eth_drag_per_iteration.csv — ETH per-axis IS/OOS trajectory
- denominator_dilution_prediction.csv — predicted ETH share AFTER universe expansion
- regime_vs_universe_hypothesis.csv — falsifier pre-registration
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

REPO_ROOT = Path("/home/roberto/crypto-trade/.worktrees/quant-research")
OUT_DIR = REPO_ROOT / "analysis" / "iteration_v1-017"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def read_per_symbol(iter_label: str, sample: str) -> pd.DataFrame:
    """Load reports-v1/iteration_v1-<label>/<sample>/per_symbol.csv."""
    path = REPO_ROOT / "reports-v1" / f"iteration_v1-{iter_label}" / sample / "per_symbol.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def main() -> None:
    # ---------- Table 1: ETH 3-axis trajectory ----------
    iterations = [
        ("baseline", "baseline"),
        ("014", "labeling-σ_t-LABEL-only"),
        ("015", "labeling-σ_t-symmetric-multi-seed"),
        ("016", "sample-weighting-uniform"),
    ]

    rows = []
    for label, axis in iterations:
        is_df = read_per_symbol(label, "in_sample")
        oos_df = read_per_symbol(label, "out_of_sample")
        if is_df.empty or oos_df.empty:
            continue

        # Identify symbol column (varies slightly across versions)
        sym_col = "symbol" if "symbol" in is_df.columns else is_df.columns[0]
        pnl_col = "net_pnl_pct" if "net_pnl_pct" in is_df.columns else None
        if pnl_col is None:
            # Fallback search
            for c in is_df.columns:
                if "net_pnl" in c.lower():
                    pnl_col = c
                    break
        if pnl_col is None:
            print(f"[WARN] /{label}: no net_pnl_pct column found in {list(is_df.columns)}")
            continue

        eth_is_row = is_df[is_df[sym_col] == "ETHUSDT"]
        eth_oos_row = oos_df[oos_df[sym_col] == "ETHUSDT"]
        if eth_is_row.empty or eth_oos_row.empty:
            continue

        # Total portfolio PnL (sum of all symbol contributions)
        is_total = is_df[pnl_col].sum()
        oos_total = oos_df[pnl_col].sum()
        eth_is = float(eth_is_row[pnl_col].iloc[0])
        eth_oos = float(eth_oos_row[pnl_col].iloc[0])

        eth_is_share = eth_is / is_total * 100 if is_total != 0 else float("nan")
        eth_oos_share = eth_oos / oos_total * 100 if oos_total != 0 else float("nan")

        rows.append(
            {
                "iteration": label,
                "axis": axis,
                "ETH_IS_PnL_pct": round(eth_is, 4),
                "ETH_OOS_PnL_pct": round(eth_oos, 4),
                "portfolio_IS_PnL_pct": round(is_total, 4),
                "portfolio_OOS_PnL_pct": round(oos_total, 4),
                "ETH_IS_share_pct": round(eth_is_share, 2),
                "ETH_OOS_share_pct": round(eth_oos_share, 2),
            }
        )

    if not rows:
        print("[WARN] No per_symbol.csv rows loaded — falling back to engineering-report numbers")
        # Fallback to hard-coded numbers from /016 engineering_report.md §2.1/2.2
        rows = [
            {
                "iteration": "baseline",
                "axis": "baseline",
                "ETH_IS_PnL_pct": -13.70,
                "ETH_OOS_PnL_pct": 2.75,
                "portfolio_IS_PnL_pct": 50.98,
                "portfolio_OOS_PnL_pct": 24.87,
                "ETH_IS_share_pct": round(-13.70 / 50.98 * 100, 2),
                "ETH_OOS_share_pct": round(2.75 / 24.87 * 100, 2),
            },
            {
                "iteration": "014",
                "axis": "labeling-σ_t-LABEL-only",
                "ETH_IS_PnL_pct": -99.73,
                "ETH_OOS_PnL_pct": -41.18,
                "portfolio_IS_PnL_pct": -126.99,
                "portfolio_OOS_PnL_pct": 3.31,
                "ETH_IS_share_pct": round(-99.73 / -126.99 * 100, 2),
                "ETH_OOS_share_pct": round(-41.18 / 3.31 * 100, 2),
            },
            {
                "iteration": "015",
                "axis": "labeling-σ_t-symmetric-multi-seed",
                "ETH_IS_PnL_pct": 17.34,
                "ETH_OOS_PnL_pct": -23.29,
                "portfolio_IS_PnL_pct": 40.74,
                "portfolio_OOS_PnL_pct": 29.66,
                "ETH_IS_share_pct": round(17.34 / 40.74 * 100, 2),
                "ETH_OOS_share_pct": round(-23.29 / 29.66 * 100, 2),
            },
            {
                "iteration": "016",
                "axis": "sample-weighting-uniform",
                "ETH_IS_PnL_pct": -46.47,
                "ETH_OOS_PnL_pct": -51.46,
                "portfolio_IS_PnL_pct": -95.42,
                "portfolio_OOS_PnL_pct": -67.99,
                "ETH_IS_share_pct": round(-46.47 / -95.42 * 100, 2),
                "ETH_OOS_share_pct": round(-51.46 / -67.99 * 100, 2),
            },
        ]

    eth_df = pd.DataFrame(rows)
    eth_df.to_csv(OUT_DIR / "eth_drag_per_iteration.csv", index=False)
    print("=== Table 1: ETH 3-axis OOS Drag Trajectory ===")
    print(eth_df.to_string(index=False))
    print()

    # Diagnostic: 3 different axes, all show ETH catastrophic OOS
    print("DIAGNOSTIC SUMMARY (ETH OOS PnL by axis):")
    print(f"  /014 labeling axis:        ETH OOS = -41.18%")
    print(f"  /015 multi-seed labeling:  ETH OOS = -23.29%")
    print(f"  /016 sample-weighting:     ETH OOS = -51.46%")
    print(f"  mean across 3 axes:        {(-41.18 - 23.29 - 51.46) / 3:.2f}%")
    print(f"  Three disjoint mechanisms all produce ETH OOS ≤ -23 → STRUCTURAL.")
    print()

    # ---------- Table 2: denominator dilution prediction ----------
    # Mechanism: if ETH catastrophic OOS continues at /017, adding SOL (and XRP)
    # to a 6- or 7-symbol universe reduces ETH's denominator share via
    # (a) reducing weight in portfolio Sharpe denominator if SOL contributes
    # positively, OR (b) leaving ETH share unchanged if SOL also catastrophic.
    #
    # Predict using BASELINE distribution (most stable reference) — at baseline:
    #   - ETH OOS PnL = 2.75% (share = 11.08%)
    #   - portfolio total OOS = 24.87%
    # Hypothesis: at /017 6-sym universe, ETH share could DROP if SOL contributes
    # OOS PnL ≥ 0. NO directional prediction on whether ETH itself recovers
    # (regime-bound vs universe-bound is the OPEN QUESTION).

    print("=== Table 2: Denominator-Dilution Prediction (REQUIRED Critic /016 Rec #2) ===")
    # baseline-reference dilution math
    baseline_eth = 2.75
    baseline_portfolio = 24.87
    baseline_eth_share = baseline_eth / baseline_portfolio * 100

    # If SOL contributes ~baseline-like (similar profile), portfolio
    # increases ~5-10% (SOL has ~1.7% IS abs return, 5.94 of all candidates)
    predictions = []
    for sol_oos_pnl in [-10.0, -5.0, 0.0, 5.0, 10.0]:
        new_portfolio = baseline_portfolio + sol_oos_pnl
        new_eth_share = baseline_eth / new_portfolio * 100 if new_portfolio != 0 else float("nan")
        predictions.append(
            {
                "scenario": f"SOL_OOS_PnL={sol_oos_pnl:.1f}",
                "new_portfolio_OOS_PnL_pct": round(new_portfolio, 2),
                "ETH_share_pct_after_dilution": round(new_eth_share, 2),
                "ETH_share_delta_vs_baseline_pct_pts": round(new_eth_share - baseline_eth_share, 2),
            }
        )
    pred_df = pd.DataFrame(predictions)
    pred_df.to_csv(OUT_DIR / "denominator_dilution_prediction.csv", index=False)
    print(pred_df.to_string(index=False))
    print(f"  baseline ETH share: {baseline_eth_share:.2f}%")
    print()

    # ---------- Table 3: regime-bound vs universe-bound hypothesis ----------
    # Per Critic /016 Rec #2: pre-register the falsifier explicitly.
    #
    # Outcome scenarios at /017:
    # A. ETH OOS Δ ≤ -0.30 vs baseline AND ETH OOS share still > 40% → universe-bound
    #    REFUTED, basin is regime-bound. /018 pivots to ETH-specific kill switch.
    # B. ETH OOS Δ ∈ [-0.30, +0.30] AND ETH OOS share drops < 30% via dilution
    #    → BENIGN — universe expansion mechanism worked at denominator level.
    # C. ETH OOS Δ ≥ +0.30 → ETH itself recovered (could mean architecture shift
    #    via pooled-vs-isolated model retrain affected ETH's per-cell Optuna).

    falsifier = [
        {
            "scenario": "A",
            "label": "ETH-still-catastrophic",
            "ETH_OOS_share_threshold": "ETH share remains > 40% of (absolute) portfolio PnL",
            "ETH_OOS_pnl_threshold": "ETH OOS PnL ≤ -20",
            "implication": "regime-bound; /018 pivots to ETH-specific kill switch (Critic /016 Path Forward #3)",
        },
        {
            "scenario": "B",
            "label": "Benign-dilution",
            "ETH_OOS_share_threshold": "ETH share drops to ≤ 30% of (absolute) portfolio PnL",
            "ETH_OOS_pnl_threshold": "ETH OOS PnL ∈ [-15, +5]",
            "implication": "universe expansion works at denominator level; consider further expansion",
        },
        {
            "scenario": "C",
            "label": "ETH-recovery",
            "ETH_OOS_share_threshold": "ETH share neutral OR positive contributor",
            "ETH_OOS_pnl_threshold": "ETH OOS PnL ≥ 0",
            "implication": "model-architecture-driven recovery (single-symbol model dispatch)",
        },
    ]
    fals_df = pd.DataFrame(falsifier)
    fals_df.to_csv(OUT_DIR / "regime_vs_universe_hypothesis.csv", index=False)
    print("=== Table 3: Regime-vs-Universe Hypothesis Pre-Registration ===")
    print(fals_df.to_string(index=False))
    print()

    print(f"Outputs written to {OUT_DIR}/")


if __name__ == "__main__":
    main()
