"""iter-v3/115 — coherent horizon-exit labeling — GO/NO-GO synthesis (T6).

Reads T1-T5 (produced by horizon_exit_gating_eda.py) and evaluates the PRE-REGISTERED
GO rule. Writes T6_go_nogo_verdict.csv.

PRE-REGISTERED GO RULE (fixed before this script touches any table):

  g1  LABEL VALIDITY      — T1: the horizon-exit label is balanced (long frac in
                            [0.20, 0.80]) on >= 2/3 symbols AND differs materially from
                            the triple-barrier label (tb_hz_label_agreement < 0.95) on
                            >= 2/3 symbols. A degenerate or near-identical label is a
                            no-op axis.

  g2  EXECUTION COHERENCE — T2 + T1: the tb-execution direction-consistency sanity check
                            passes (dir_consistency_tb_exec >= 0.98) on >= 2/3 symbols,
                            AND a real geometry difference exists — the /072 mismatch
                            fraction (T2 mismatch_frac_072) is materially non-zero
                            (>= 0.05) on >= 2/3 symbols. A non-zero /072 mismatch is the
                            evidence that horizon-exit is a genuinely different geometry
                            (not a no-op) AND that the /072-style mismatch the coherent
                            design fixes is a real, sizeable effect.

  g3  TRADE-BOOK GAIN     — T3: the horizon-exit book monthly Sharpe >= the triple-
                            barrier book monthly Sharpe on >= 2/3 symbols (the geometry
                            recovers or at least preserves trade-Sharpe). THE DECISIVE
                            substantive gate — the test /072 skipped.

  VERDICT = GO  iff  g1 AND g2 AND g3.

  T4 (feature->label IC) and T5 (permutation null) are SUPPORTING context — they inform
  the brief's Section 7 mechanism discussion but DO NOT gate, because /105 proved a
  better feature->label IC does not imply a better trade book (the IC is a property of
  the labeling problem, not the trade-construction problem).

Per THE PRIME DIRECTIVE the GO/NO-GO does NOT terminate the iteration — iter-v3/115 runs
a Phase-6 backtest regardless. The verdict sets the brief's modal prediction and the
Section-7/8 pre-registration only.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent


def _load(name: str) -> pd.DataFrame:
    return pd.read_csv(OUT / name)


def main() -> None:
    t1 = _load("T1_label_balance.csv")
    t2 = _load("T2_label_execution_consistency.csv")
    t3 = _load("T3_counterfactual_book.csv")
    t4 = _load("T4_feature_label_ic.csv")
    t5 = _load("T5_permutation_null.csv")

    print("=" * 78)
    print("iter-v3/115 — coherent horizon-exit labeling — GO/NO-GO synthesis (T6)")
    print("=" * 78)

    # ---- g1 — label validity ------------------------------------------------
    g1_balance = int(t1["balance_ok"].sum())
    g1_differs = int(t1["label_differs"].sum())
    g1 = bool(g1_balance >= 2 and g1_differs >= 2)
    print(
        f"\ng1 LABEL VALIDITY: balance_ok {g1_balance}/3, label_differs {g1_differs}/3 "
        f"-> {'PASS' if g1 else 'FAIL'}"
    )

    # ---- g2 — execution coherence ------------------------------------------
    g2_sanity = int(t2["sanity_tb_exec_ok"].sum())
    g2_geomdiff = int((t2["mismatch_frac_072"] >= 0.05).sum())
    g2 = bool(g2_sanity >= 2 and g2_geomdiff >= 2)
    print(
        f"g2 EXECUTION COHERENCE: sanity_tb_exec_ok {g2_sanity}/3, /072-mismatch>=0.05 "
        f"{g2_geomdiff}/3 -> {'PASS' if g2 else 'FAIL'}"
    )

    # ---- g3 — trade-book gain (the decisive gate) --------------------------
    g3_hz_ge_tb = int(t3["hz_ge_tb"].sum())
    g3 = bool(g3_hz_ge_tb >= 2)
    print(
        f"g3 TRADE-BOOK GAIN (decisive): hz monthly Sharpe >= tb on {g3_hz_ge_tb}/3 "
        f"symbols -> {'PASS' if g3 else 'FAIL'}"
    )

    verdict = "GO" if (g1 and g2 and g3) else "NO-GO"

    # ---- supporting context (T4 / T5) --------------------------------------
    t4_within = int(t4["hz_ic_within_25pct"].sum()) if "hz_ic_within_25pct" in t4 else 0
    t5_clears = bool(t5.iloc[0].get("clears_q95", False)) if "clears_q95" in t5 else False
    t5_auc = t5.iloc[0].get("observed_holdout_auc", float("nan")) if len(t5) else float("nan")
    print(
        f"\n[supporting] T4: hz IC within 25% of tb IC on {t4_within}/3 symbols.  "
        f"T5: pooled hz-label held-out AUC {t5_auc}, clears q95 = {t5_clears}."
    )

    print("\n" + "-" * 78)
    print(f"PRE-REGISTERED VERDICT:  {verdict}   (GO iff g1 AND g2 AND g3)")
    print("-" * 78)
    if verdict == "GO":
        print(
            "GO — the coherent horizon-exit geometry recovers or preserves IS trade-Sharpe\n"
            "on >= 2/3 symbols; the brief's modal prediction is a non-negative OOS effect."
        )
    else:
        print(
            "NO-GO — the horizon-exit geometry does NOT recover IS trade-Sharpe on >= 2/3\n"
            "symbols. Per THE PRIME DIRECTIVE the backtest STILL runs; the brief's modal\n"
            "prediction is centered at or below the /060 anchor and Section 7 pre-registers\n"
            "the geometry-does-not-transfer failure mode as the modal outcome."
        )

    t6 = pd.DataFrame(
        [
            {
                "gate": "g1_label_validity",
                "detail": f"balance_ok={g1_balance}/3, label_differs={g1_differs}/3",
                "pass": g1,
            },
            {
                "gate": "g2_execution_coherence",
                "detail": f"sanity_tb_exec_ok={g2_sanity}/3, /072-mismatch>=0.05={g2_geomdiff}/3",
                "pass": g2,
            },
            {
                "gate": "g3_trade_book_gain_DECISIVE",
                "detail": f"hz_monthly_sharpe>=tb on {g3_hz_ge_tb}/3 symbols",
                "pass": g3,
            },
            {
                "gate": "VERDICT",
                "detail": f"GO iff g1 AND g2 AND g3 | T4_support={t4_within}/3 "
                f"T5_clears_q95={t5_clears}",
                "pass": verdict == "GO",
            },
        ]
    )
    t6.to_csv(OUT / "T6_go_nogo_verdict.csv", index=False)
    print(f"\n[T6] verdict table written -> {OUT / 'T6_go_nogo_verdict.csv'}")


if __name__ == "__main__":
    main()
