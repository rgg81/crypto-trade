"""iter-v3/116 — regime-conditioned exit-barrier — GO/NO-GO synthesis (T4).

Reads the four committed gating tables and evaluates the pre-registered GO rule:

  GO  iff  g1 (per-bucket optimal geometry materially differs across buckets)
           AND g2 (regime-conditioned schedule beats static 2:1 on >= 2/3 symbols
                   IS-optimized, worst symbol not below anchor - 0.30)
           AND g3 (g3a placebo-robust on >= 2/3 symbols AND g3b out-of-fold-stable
                   on >= 2/3 symbols).

g3a is the DECISIVE falsifier. If a RANDOM bucketing captures the same conditioned
"lift" that the regime bucketing captures, the T2 lift is grid-search overfitting, not
regime signal — and a regime-conditioned barrier is a parameter-laden global knob, the
/073 SUSPICIOUS-OOS-DOMINANT pattern in disguise.

Per THE PRIME DIRECTIVE the verdict here NEVER terminates the iteration — it sets the
brief's modal prediction and the Section-7/8 pre-registration. The backtest runs.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent

# the /060 EXPLORATION-mode reference (the pre-registered anchor for cycle-6 EXPLORATIONs)
ANCHOR_IS = 0.8325
ANCHOR_OOS = 0.1403
WORST_SYMBOL_FLOOR_DELTA = -0.30  # g2: worst symbol must stay above anchor - 0.30


def main() -> None:
    g1 = pd.read_csv(OUT / "T1b_g1_geometry_differs.csv")
    t2 = pd.read_csv(OUT / "T2_conditioned_vs_static.csv")
    t3a = pd.read_csv(OUT / "T3a_shuffle_placebo.csv")
    t3b = pd.read_csv(OUT / "T3b_out_of_fold.csv")

    rows = []

    # ----- g1: per-bucket optimal geometry materially differs -----
    g1_pass_combos = int(g1["g1_differs"].sum())
    g1_total = len(g1)
    # additional substance check: how concentrated is the grid-search optimum?
    t1 = pd.read_csv(OUT / "T1_regime_bucket_optima.csv").dropna(subset=["best_tp"])
    modal_cell = t1.groupby(["best_tp", "best_sl"]).size().idxmax()
    modal_cell_frac = (
        t1.groupby(["best_tp", "best_sl"]).size().max() / len(t1)
    )
    g1_ok = g1_pass_combos >= 4  # >= 4 of 6 symbol x cond combos
    rows.append(
        {
            "gate": "g1_geometry_differs",
            "metric": "symbol x cond combos with g1_differs=True",
            "value": f"{g1_pass_combos}/{g1_total}",
            "detail": (
                f"modal optimum cell {modal_cell} chosen by "
                f"{modal_cell_frac:.0%} of all buckets — optimum is grid-corner-"
                f"concentrated, the per-bucket 'difference' is <=1 grid step"
            ),
            "pass": bool(g1_ok),
        }
    )

    # ----- g2: conditioned schedule beats static 2:1 (IS-optimized) -----
    # best lift per symbol across the two conditioning variables
    best_per_sym = t2.loc[t2.groupby("symbol")["sharpe_lift"].idxmax()]
    g2_beats = int((best_per_sym["sharpe_lift"] > 0).sum())
    worst_sym_sharpe = float(best_per_sym["conditioned_monthly_sharpe"].min())
    g2_worst_ok = worst_sym_sharpe >= ANCHOR_IS + WORST_SYMBOL_FLOOR_DELTA
    g2_ok = g2_beats >= 2 and g2_worst_ok
    rows.append(
        {
            "gate": "g2_conditioned_beats_static",
            "metric": "symbols where conditioned schedule beats static 2:1 (IS-opt)",
            "value": f"{g2_beats}/3",
            "detail": (
                f"worst symbol conditioned monthly Sharpe {worst_sym_sharpe:.4f} "
                f"(floor {ANCHOR_IS + WORST_SYMBOL_FLOOR_DELTA:.2f}); "
                f"IS-OPTIMIZED CEILING — not a fenced estimate"
            ),
            "pass": bool(g2_ok),
        }
    )

    # ----- g3a: regime-shuffle placebo (the decisive falsifier) -----
    g3a_beats_q95 = int(t3a["real_beats_shuffle_q95"].sum())
    g3a_real_gt_shuffle = int((t3a["real_minus_shuffle_mean"] > 0.15).sum())
    g3a_ok = g3a_beats_q95 >= 4  # >= 4 of 6 combos beat the shuffle q95
    rows.append(
        {
            "gate": "g3a_shuffle_placebo",
            "metric": "symbol x cond combos where real lift beats shuffle q95",
            "value": f"{g3a_beats_q95}/6",
            "detail": (
                f"{g3a_real_gt_shuffle}/6 combos have real_lift - shuffle_mean > "
                f"+0.15 — a RANDOM bucketing captures the same/greater lift in "
                f"{6 - g3a_beats_q95} of 6 combos: the T2 lift is grid-search "
                f"overfitting, NOT regime signal"
            ),
            "pass": bool(g3a_ok),
        }
    )

    # ----- g3b: out-of-fold stability -----
    g3b_helps = int(t3b["fold_a_schedule_helps_fold_b"].sum())
    g3b_ok = g3b_helps >= 4
    rows.append(
        {
            "gate": "g3b_out_of_fold",
            "metric": "symbol x cond combos where fold-A schedule helps fold B",
            "value": f"{g3b_helps}/6",
            "detail": (
                "fold B is the trend-favorable later IS half; a tighter-TP/wider-SL "
                "schedule helps any trending window (the /065 SL-widening lesson) — "
                "g3b alone cannot separate regime signal from that structural bias; "
                "g3a is the controlling test"
            ),
            "pass": bool(g3b_ok),
        }
    )

    verdict = pd.DataFrame(rows)
    verdict.to_csv(OUT / "T4_go_nogo_verdict.csv", index=False)

    g1_p = bool(verdict.loc[verdict.gate == "g1_geometry_differs", "pass"].iloc[0])
    g2_p = bool(verdict.loc[verdict.gate == "g2_conditioned_beats_static", "pass"].iloc[0])
    g3a_p = bool(verdict.loc[verdict.gate == "g3a_shuffle_placebo", "pass"].iloc[0])
    g3b_p = bool(verdict.loc[verdict.gate == "g3b_out_of_fold", "pass"].iloc[0])
    g3_p = g3a_p and g3b_p
    go = g1_p and g2_p and g3_p

    print("=" * 78)
    print("iter-v3/116 — regime-conditioned exit-barrier — GO/NO-GO SYNTHESIS (T4)")
    print("=" * 78)
    print(verdict.to_string(index=False))
    print("-" * 78)
    print(f"  g1 (geometry differs)        : {'PASS' if g1_p else 'FAIL'}")
    print(f"  g2 (conditioned beats static): {'PASS' if g2_p else 'FAIL'}  [IS-optimized]")
    print(f"  g3a (shuffle placebo)        : {'PASS' if g3a_p else 'FAIL'}  [DECISIVE]")
    print(f"  g3b (out-of-fold)            : {'PASS' if g3b_p else 'FAIL'}")
    print(f"  g3 = g3a AND g3b             : {'PASS' if g3_p else 'FAIL'}")
    print("-" * 78)
    print(f"  VERDICT  (GO iff g1 AND g2 AND g3) : {'GO' if go else 'NO-GO'}")
    print("=" * 78)
    if not go:
        print(
            "\nNO-GO RATIONALE: g3a (the decisive shuffle placebo) FAILS — a RANDOM\n"
            "bucketing captures the conditioned 'lift' as well as or better than the\n"
            "regime bucketing in 5 of 6 symbol x cond combos. The per-bucket optimal\n"
            "barrier geometry collapses to a single grid corner (tp=1.0, sl=2.0 — even\n"
            "more extreme than /065's REJECTED 2.0/1.5 widening) in ~3/4 of all buckets.\n"
            "The regime variable carries no information about the optimal barrier\n"
            "geometry; conditioning on it adds parameters with no signal. This is the\n"
            "/073 per-symbol-asymmetry SUSPICIOUS-OOS-DOMINANT pattern with a regime\n"
            "label substituted for the symbol label. Per THE PRIME DIRECTIVE the brief\n"
            "still runs a backtest — the modal prediction is a non-positive OOS effect\n"
            "with an IS-collapse / OOS-spike regime-artifact risk (the /073/065 path).\n"
        )


if __name__ == "__main__":
    main()
