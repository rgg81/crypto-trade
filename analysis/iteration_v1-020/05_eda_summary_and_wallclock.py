"""iter-v1/020 EDA — script 05.

EDA summary + wall-clock estimate.

Consolidates findings from scripts 01-04 into a single summary CSV plus
emits the wall-clock estimate for brief Section 3.6.

Writes:
  analysis/iteration_v1-020/eda_summary.csv
  analysis/iteration_v1-020/wallclock_estimate.csv
"""

from __future__ import annotations

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT_SUMMARY = REPO / "analysis" / "iteration_v1-020" / "eda_summary.csv"
OUT_WALLCLOCK = REPO / "analysis" / "iteration_v1-020" / "wallclock_estimate.csv"


def main() -> None:
    summary_rows = [
        {
            "finding": "BTC IS-OOS asymmetric rotation",
            "evidence": (
                "BTC IS net_pnl 0/5 positive across baseline+/014/015/016/017; "
                "mean -38.12%, range [-93.81, -0.65]. BTC OOS net_pnl 4/5 positive; "
                "mean +7.70%, range [-8.31, +33.17]. Strongest IS-OOS asymmetric "
                "rotation in v1 catalog."
            ),
            "implication": (
                "BTC behaves like a per-symbol regime-mismatch case: IS=catastrophic, "
                "OOS=preserved. The asymmetry is the structural prior for /020 verdict."
            ),
        },
        {
            "finding": "BTC IS catastrophic regime-concentrated in IS_H1",
            "evidence": (
                "IS_H1 (first half, ~2022-Q4 to mid-2024): BTC net_pnl -36.01% across "
                "15 months, mean -2.40%/month, 5/15 positive. IS_H2 (mid-2024+): "
                "BTC net_pnl -1.27% across 16 months, mean -0.08%/month, 8/16 positive. "
                "H1 catastrophic >> H2 flat."
            ),
            "implication": (
                "BTC IS catastrophic is regime-bound (early-IS specific). Cohort "
                "isolation alone (BTC-only single-seed) is UNLIKELY to fix H1 "
                "catastrophic — the regime mismatch is real, not pool-induced."
            ),
        },
        {
            "finding": "BTC OOS strongly positive",
            "evidence": (
                "BTC OOS net_pnl +33.17% across 11 months, mean +3.02%/month, "
                "6/11 positive months, range [-12.63, +21.59]. WR jumps from "
                "33.6% IS to 45.7% OOS."
            ),
            "implication": (
                "BTC OOS edge is observable in baseline pool. Question is whether "
                "BTC-only isolation preserves or destroys it."
            ),
        },
        {
            "finding": "BTC-ETH pool-anchor diagnostic: NEAR ZERO correlation",
            "evidence": (
                "Pearson(BTC, ETH) monthly net_pnl = -0.0220 across 29 common pool-training "
                "months. Spearman = +0.0227. Same-sign months 51.7% (15/29, ~coin-flip). "
                "BTC and ETH monthly PnL within pool training are statistically independent."
            ),
            "implication": (
                "INTRINSIC IS-OOS hypothesis SUPPORTED over POOL-ANCHOR hypothesis. "
                "Model A's pooled training does NOT couple BTC and ETH labels "
                "(Pearson |ρ| < 0.30 threshold). BTC's IS catastrophic is NOT explained "
                "by ETH's drag-via-pool. BTC-only isolation will likely PRESERVE IS "
                "catastrophic (regime is the constraint, not pooling). Verdict prior "
                "shifts toward INERT/NEGATIVE."
            ),
        },
        {
            "finding": "BTC OOS contribution stable under universe expansion (/017)",
            "evidence": (
                "Baseline BTC OOS net_pnl +33.17%. /017 with +SOL universe: "
                "BTC OOS +15.11% (still positive, lower magnitude). BTC IS at /017: "
                "-93.81% (CATASTROPHIC, worst in baseline+/017 IS) vs baseline "
                "-37.28%. Universe expansion sharpened BTC IS catastrophic and "
                "compressed OOS positive."
            ),
            "implication": (
                "Adding symbols to the pool DOES NOT fix BTC IS catastrophic — it "
                "WORSENS it. Subtracting symbols (BTC-only at /020) is the "
                "opposite axis. Outcome is uncertain: if pool-coupling were the "
                "lever, /017 would have helped BTC IS (it didn't). But pool-anchor "
                "diagnostic ρ ≈ 0 rules out coupling. INERT modal."
            ),
        },
        {
            "finding": "BTC structural prior summary",
            "evidence": (
                "Across 5 architectures (baseline + /014/015/016/017), BTC IS net_pnl "
                "is 5/5 negative with mean -38.12%, but BTC OOS net_pnl is 4/5 positive "
                "with mean +7.70%. This is the OPPOSITE of LINK (9/9 OOS positive with "
                "+9 IS positive too) and the OPPOSITE of ETH (5/5 OOS NEGATIVE through "
                "cycle-3 architectures until /019 cohort+gate dissolved it)."
            ),
            "implication": (
                "BTC's per-symbol structural prior is unique — IS-NEG/OOS-POS rotation. "
                "Hypothesis under test: this rotation is INTRINSIC (regime mismatch) or "
                "POOL-INDUCED (pool training compensation pattern). Pool-anchor diagnostic "
                "ρ ≈ 0 supports INTRINSIC."
            ),
        },
    ]

    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    with OUT_SUMMARY.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["finding", "evidence", "implication"])
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"wrote {OUT_SUMMARY}")

    # Wall-clock estimate
    wc_rows = [
        {"step": "Anchor: /019 ETH-only at ENSEMBLE_SIZE=3 + n_trials=18 + V1_FEATURE_COLUMNS_PRUNED",
         "duration_min": "25",
         "source": "/019 diary 'wall-clock ~25 min' + 548s = 9.1 min Model G compute"},
        {"step": "BTC-only at identical scale (1 sym, R3-only, no R1/R2)",
         "duration_min": "20-25",
         "source": "BTC has comparable training-row count to ETH; expect parity"},
        {"step": "No post-hoc gate (no BTC-trend filter; pure cohort isolation)",
         "duration_min": "0",
         "source": "vs /019 which had ~1 min gate overhead"},
        {"step": "Methodology + reporting overhead (CPCV, PSR, DSR on 1-model trade roster)",
         "duration_min": "3",
         "source": "Same as /019"},
        {"step": "TOTAL PROJECTED",
         "duration_min": "23-28 (mid-point 25 min)",
         "source": "78%+ margin vs 2h cap; well below 1.6h Phase 5.5 BLOCK threshold"},
        {"step": "Kill-switch threshold",
         "duration_min": "45",
         "source": "1.8x projected mid-point; well below 2h cap"},
    ]

    with OUT_WALLCLOCK.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(wc_rows[0].keys()))
        writer.writeheader()
        writer.writerows(wc_rows)
    print(f"wrote {OUT_WALLCLOCK}")

    print()
    print("EDA summary (6 findings) + wall-clock estimate (mid-point 25 min) ready for brief.")


if __name__ == "__main__":
    main()
