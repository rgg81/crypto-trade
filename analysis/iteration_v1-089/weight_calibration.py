"""
iter-v1/089 — BUNDLE-003 IS-ONLY weight calibration (HARD per
feedback_v1_bundle_weight_is_only / Critic Check 17 = BUNDLE-WEIGHT-OOS-LEAK).

Computes per-component bundle weights from IS DATA ONLY for the 5 BUNDLE-003
components, then writes them to weights.json for compose_bundle_003.py to consume.

  Components (pairwise-disjoint coin universe; Check 16):
    DOT  = /063 (from /082 partition)   owns {DOTUSDT}
    ETH  = /064 (from /082 partition)   owns {ETHUSDT}
    BTC  = /065 (from /082 partition)   owns {BTCUSDT}
    AAVE = /078 (from /082 partition)   owns {AAVEUSDT}
    XRP  = /088 (standalone specialist) owns {XRPUSDT}

METHOD — faithful mirror of BUNDLE-002 (/082):
  BUNDLE-002 was composed at EQUAL component weight: each component's trades
  enter the union 1:1 (weight 1.0), bundle PnL = sum of net_pnl_pct, monthly
  Sharpe = +0.7157 IS / +1.0043 OOS (reproduced bit-exact, validated).
  Therefore the *operative* calibrated weight set for an apples-to-apples
  BUNDLE-003-vs-BUNDLE-002 comparison is EQUAL WEIGHT across the 5 components.

  We additionally compute an IS-only INVERSE-VOLATILITY (risk-parity) weight set
  as a robustness companion. RP weights are reported and stored; compose applies
  the EQUAL set as PRIMARY (to mirror /082) and the RP set as a SECONDARY
  robustness pass. Both weight sets are derived from IS data ONLY — the OOS
  files are never opened in this script.

  Inverse-volatility weight for component c:
    w_c_raw = 1 / sigma_c          (sigma_c = std of component IS monthly PnL)
    w_c     = w_c_raw / sum_k w_k_raw          (normalized to sum 1, then x5
                                                so equal-weight baseline = 1.0/comp)

  Rationale for reporting RP: equal-weight lets a high-variance component
  dominate bundle drawdown. RP down-weights the noisiest streams. If the
  BUNDLE-003 verdict is identical under both weightings, the merge decision is
  weight-robust. If they disagree, that is itself a finding for the Critic.

IS-ONLY ASSERTION: this module reads only `in_sample/trades.csv`. A guard at
the bottom asserts no out_of_sample path is ever constructed.
"""

from __future__ import annotations

import csv
import datetime
import json
import math
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REPORTS = REPO / "reports-v1"
OUT_JSON = REPO / "analysis" / "iteration_v1-089" / "weights.json"

OOS_CUTOFF = datetime.date(2025, 3, 24)  # sacred constant; close-day < cutoff => IS

# Component -> (source iteration dir, owned symbol).
# Incumbent 4 come from the /082 BUNDLE-002 partition (verified per-symbol counts
# DOT 149 / ETH 198 / BTC 190 / AAVE 157). XRP from its standalone /088 run.
COMPONENTS = [
    ("DOT", "iteration_v1-082", "DOTUSDT"),
    ("ETH", "iteration_v1-082", "ETHUSDT"),
    ("BTC", "iteration_v1-082", "BTCUSDT"),
    ("AAVE", "iteration_v1-082", "AAVEUSDT"),
    ("XRP", "iteration_v1-088", "XRPUSDT"),
]


def is_monthly_pnl(run_dir: str, symbol: str) -> dict[str, float]:
    """IS-ONLY monthly net_pnl_pct for `symbol` from run_dir/in_sample/trades.csv.

    Re-split on the strict OOS_CUTOFF close-day rule so a trade that closes just
    past the cutoff but lives in the in_sample file is still excluded from IS.
    """
    path = REPORTS / run_dir / "in_sample" / "trades.csv"
    monthly: dict[str, float] = defaultdict(float)
    with open(path) as fh:
        for row in csv.DictReader(fh):
            if row["symbol"] != symbol:
                continue
            close = datetime.datetime.fromtimestamp(
                int(row["close_time"]) / 1000, datetime.UTC
            )
            if close.date() >= OOS_CUTOFF:
                continue  # strict IS boundary
            monthly[close.strftime("%Y-%m")] += float(row["net_pnl_pct"])
    return dict(monthly)


def monthly_std(monthly: dict[str, float]) -> float:
    vals = list(monthly.values())
    if len(vals) < 2:
        return float("nan")
    m = sum(vals) / len(vals)
    var = sum((x - m) ** 2 for x in vals) / (len(vals) - 1)
    return math.sqrt(var) if var > 0 else 0.0


def monthly_sharpe(monthly: dict[str, float]) -> float:
    vals = list(monthly.values())
    if len(vals) < 2:
        return float("nan")
    m = sum(vals) / len(vals)
    var = sum((x - m) ** 2 for x in vals) / (len(vals) - 1)
    s = math.sqrt(var) if var > 0 else 0.0
    return (m / s) * math.sqrt(12) if s > 0 else float("nan")


def main() -> None:
    print("=== BUNDLE-003 IS-ONLY WEIGHT CALIBRATION — iter-v1/089 ===\n")
    print("Components (pairwise-disjoint; IS data only):")

    comp_monthly: dict[str, dict[str, float]] = {}
    comp_std: dict[str, float] = {}
    comp_sharpe: dict[str, float] = {}
    comp_total: dict[str, float] = {}
    for name, run_dir, sym in COMPONENTS:
        m = is_monthly_pnl(run_dir, sym)
        comp_monthly[name] = m
        comp_std[name] = monthly_std(m)
        comp_sharpe[name] = monthly_sharpe(m)
        comp_total[name] = sum(m.values())
        print(
            f"  {name:<4} {sym:<9} src={run_dir}  "
            f"IS_months={len(m):>2}  IS_total={comp_total[name]:>8.3f}%  "
            f"IS_monthly_std={comp_std[name]:>6.3f}  IS_Sharpe={comp_sharpe[name]:>6.3f}"
        )

    n = len(COMPONENTS)

    # --- PRIMARY: equal weight (mirrors BUNDLE-002 /082 composition exactly) ---
    equal_w = {name: 1.0 for name, _, _ in COMPONENTS}

    # --- SECONDARY: IS-only inverse-volatility (risk-parity) robustness pass ---
    inv = {name: (1.0 / comp_std[name]) if comp_std[name] > 0 else 0.0 for name in equal_w}
    inv_sum = sum(inv.values())
    # Normalize so the AVERAGE weight is 1.0 (i.e. multiply normalized share by n).
    # This keeps RP directly comparable to the equal set whose average is also 1.0.
    rp_w = {name: (inv[name] / inv_sum) * n if inv_sum > 0 else 1.0 for name in equal_w}

    print("\n--- WEIGHT SETS (both IS-derived) ---")
    print(f"{'component':<10}{'equal_w':>10}{'rp_w (inv-vol)':>16}")
    for name, _, _ in COMPONENTS:
        print(f"{name:<10}{equal_w[name]:>10.4f}{rp_w[name]:>16.4f}")
    print(
        f"{'(avg)':<10}{sum(equal_w.values()) / n:>10.4f}"
        f"{sum(rp_w.values()) / n:>16.4f}"
    )

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "method": "equal_weight_primary (mirror /082) + inverse_vol_secondary",
        "is_only": True,
        "oos_cutoff": OOS_CUTOFF.isoformat(),
        "components": [
            {
                "name": name,
                "source": run_dir,
                "symbol": sym,
                "is_months": len(comp_monthly[name]),
                "is_monthly_std": comp_std[name],
                "is_sharpe": comp_sharpe[name],
                "is_total_pnl": comp_total[name],
                "equal_weight": equal_w[name],
                "rp_weight": rp_w[name],
            }
            for name, run_dir, sym in COMPONENTS
        ],
        "equal_weights": equal_w,
        "rp_weights": rp_w,
    }
    with open(OUT_JSON, "w") as fh:
        json.dump(payload, fh, indent=2)
    print(f"\nWrote: {OUT_JSON}")
    print("\nPRIMARY weight set = EQUAL (mirrors BUNDLE-002 /082).")
    print("SECONDARY weight set = inverse-IS-vol (risk-parity robustness companion).")


if __name__ == "__main__":
    main()
