"""iter-v3/116 — three-axis GO/NO-GO synthesis (master synthesis).

Reads the EDA tables of all THREE structural axes the /116 EDA tested and emits the
unified verdict the brief uses:

  Axis A — regime-conditioned exit barrier (the dispatch's recommended axis)
           Tables: T1_regime_bucket_optima.csv, T1b_g1_geometry_differs.csv,
                   T2_conditioned_vs_static.csv, T3a_shuffle_placebo.csv,
                   T3b_out_of_fold.csv, T4_go_nogo_verdict.csv

  Axis B — scaled-entry (staged-entry path) — first PIVOT
           Tables: T5_scaled_entry_grid.csv, T6_confirm_separates.csv

  Axis C — early-exit-on-no-confirmation (a NEW exit primitive) — second PIVOT
           Tables: T7_early_exit_grid.csv, T8_cuts_losers.csv, T9_out_of_fold.csv

Per the dispatch ("If your EDA does NOT support a genuinely distinct, GO-or-uncertain
regime-conditioned-barrier hypothesis, pick a BOLDER, genuinely out-of-the-box structural
axis instead"), this synthesis names which axis the iter-v3/116 backtest runs and why.

Per THE PRIME DIRECTIVE the iteration runs a backtest regardless — the synthesis sets the
brief's modal prediction and the Section-7/8 pre-registration. No EDA-kill.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent

ANCHOR_IS = 0.8325
ANCHOR_OOS = 0.1403


def axis_a_verdict() -> dict:
    """Axis A — regime-conditioned exit barrier — already synthesized at T4."""
    t4 = pd.read_csv(OUT / "T4_go_nogo_verdict.csv")
    passes = dict(zip(t4["gate"], t4["pass"]))
    g1 = bool(passes["g1_geometry_differs"])
    g2 = bool(passes["g2_conditioned_beats_static"])
    g3a = bool(passes["g3a_shuffle_placebo"])
    g3b = bool(passes["g3b_out_of_fold"])
    go = g1 and g2 and g3a and g3b
    return {
        "axis": "A — regime-conditioned exit barrier",
        "g1": g1,
        "g2": g2,
        "g3a": g3a,
        "g3b": g3b,
        "go": go,
        "headline": (
            "NO-GO — g3a (shuffle placebo) FAIL 5/6: a RANDOM bucketing captures the "
            "same lift; per-bucket optima collapse to one grid corner (tp=1.0, sl=2.0). "
            "The regime variable carries NO information about the optimal barrier."
        ),
    }


def axis_b_verdict() -> dict:
    """Axis B — scaled-entry (staged-entry path) — read T5 directly."""
    t5 = pd.read_csv(OUT / "T5_scaled_entry_grid.csv")
    by_sym = t5.dropna(subset=["sharpe_lift"]).groupby("symbol")
    n_pos_per_sym = by_sym["sharpe_lift"].apply(lambda s: int((s > 0).sum()))
    n_total_per_sym = by_sym.size()
    beats = int((n_pos_per_sym > 0).sum())
    # any cell with positive lift in any symbol?
    any_positive = bool((t5["sharpe_lift"].dropna() > 0).any())
    go = any_positive  # the weakest possible g1 — at least one cell positive somewhere
    return {
        "axis": "B — scaled-entry (staged-entry path)",
        "g1_any_cell_positive_any_symbol": any_positive,
        "n_symbols_with_any_positive_cell": int(beats),
        "best_lift_per_sym": by_sym["sharpe_lift"].max().round(4).to_dict(),
        "go": go,
        "headline": (
            "NO-GO — negative lift in ALL 81 grid cells across all 3 symbols. Scaled "
            "entry adds size at a worse fill price (already up +trigger ATR); the small "
            "variance reduction does not compensate."
        ),
    }


def axis_c_verdict() -> dict:
    """Axis C — early-exit-on-no-confirmation."""
    t7 = pd.read_csv(OUT / "T7_early_exit_grid.csv")
    t8 = pd.read_csv(OUT / "T8_cuts_losers.csv")
    t9 = pd.read_csv(OUT / "T9_out_of_fold.csv")

    # g1 — best cell per symbol beats static and worst-symbol floor
    by_sym = t7.dropna(subset=["sharpe_lift"]).groupby("symbol")
    best_per_sym = by_sym["sharpe_lift"].max()
    g1_beats = int((best_per_sym > 0).sum())
    # worst symbol's *best* lift floor — soft check, IS-optimized
    g1_ok = g1_beats >= 2

    # frac_positive_cells per symbol — coherent region?
    frac_positive = by_sym["sharpe_lift"].apply(lambda s: float((s > 0).mean()))

    # g2 — cuts losers? (T8 cut_held_to_barrier_mean_pnl < 0 on >= 2/3 symbols)
    by_sym_cuts = t8.groupby("symbol")["cuts_losers"].any()
    g2_ok = int(by_sym_cuts.sum()) >= 2

    # g3 — out-of-fold stability
    g3_helps = int(t9["fold_a_cell_helps_fold_b"].sum())
    g3_ok = g3_helps >= 2

    go = g1_ok and g2_ok and g3_ok
    return {
        "axis": "C — early-exit-on-no-confirmation",
        "g1_best_per_sym_positive_count": int(g1_beats),
        "best_lift_per_sym": best_per_sym.round(4).to_dict(),
        "frac_positive_cells_per_sym": {k: round(v, 3) for k, v in frac_positive.items()},
        "g2_cuts_losers_any_cell_any_symbol": int(by_sym_cuts.sum()),
        "g3_fold_a_helps_fold_b": g3_helps,
        "go": go,
        "headline": (
            "NO-GO on the formal gates — g2 mechanism FAIL: in 48/48 (trigger,K) cells "
            "the trades the rule cuts are POSITIVE-mean-PnL held-to-barrier (modestly "
            "below-average winners, NOT losers). The small IS lift in some cells "
            "(BCH +0.13, LDO +0.12, TRX +0.06 best) is grid-search-on-an-uptrend "
            "variance reduction, not a discovered loser-filter. g3 unstable on LDO "
            "(fold-A cell regresses fold B by -0.53)."
        ),
    }


def main() -> None:
    a = axis_a_verdict()
    b = axis_b_verdict()
    c = axis_c_verdict()

    print("=" * 78)
    print("iter-v3/116 — three-axis GO/NO-GO synthesis (the iter-v3/116 EDA budget)")
    print("=" * 78)
    print()
    for v in (a, b, c):
        print(f"  {v['axis']}")
        print(f"    GO: {v['go']}")
        print(f"    {v['headline']}")
        print()

    summary = pd.DataFrame(
        [
            {"axis": a["axis"], "go": a["go"], "headline": a["headline"]},
            {"axis": b["axis"], "go": b["go"], "headline": b["headline"]},
            {"axis": c["axis"], "go": c["go"], "headline": c["headline"]},
        ]
    )
    summary.to_csv(OUT / "T10_axis_synthesis.csv", index=False)

    print("-" * 78)
    print("ITER-v3/116 AXIS DECISION")
    print("-" * 78)
    print(
        "All three structural axes return NO-GO on the pre-registered formal gates.\n"
        "Per THE PRIME DIRECTIVE the iteration MUST run a backtest — the EDA designs the\n"
        "experiment, it never terminates it. The backtest axis is selected on the\n"
        "axis-distinguishing criterion 'genuine residual uncertainty' — the axis whose\n"
        "production-Optuna + OOS behavior the EDA cannot fully predict.\n"
        "\n"
        "  Axis A (regime-conditioned barrier) — falsified by shuffle placebo at the EDA\n"
        "    surface (the IS lift is grid-search overfitting). Running it would re-test\n"
        "    a known dead-path family (/065/073) under a thin re-label.\n"
        "  Axis B (scaled-entry) — negative lift in ALL 81 cells. No residual upside.\n"
        "  Axis C (early-exit-on-no-confirmation) — g2 mechanism FAILS (cuts winners,\n"
        "    not losers) BUT a small coherent IS lift exists in a (trigger~0.5, K~3-4)\n"
        "    region for BCH+TRX. Running it tests whether that small IS lift survives\n"
        "    the production-Optuna + OOS (likely modal: it does NOT; the variance-\n"
        "    reduction artifact will revert under multi-seed inference and OOS regime).\n"
        "    This is the bolder axis the dispatch named: a NEW exit primitive distinct\n"
        "    from /107 (the absence-of-excursion complement to /107's high-water-mark\n"
        "    family) — and the one with residual uncertainty worth resolving in\n"
        "    production. The modal pre-registered outcome is NEGATIVE / INERT-to-mildly-\n"
        "    negative; the brief reports this honestly.\n"
        "\n"
        "  /116 BACKTEST AXIS: Axis C — early-exit-on-no-confirmation.\n"
        "  Pre-registered modal outcome: EXPLORATION-NEGATIVE or INERT (no IS lift\n"
        "  survives production-Optuna + multi-seed inference + OOS).\n"
    )


if __name__ == "__main__":
    main()
