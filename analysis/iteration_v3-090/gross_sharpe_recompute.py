"""iter-v3/090 closeout — TASK 1: recompute gross monthly Sharpe correctly.

Critic Phase-7.5 review (briefs-v3/iteration_v3-090/review.md) BLOCKED /090: the
engineering report's central diagnostic — "/090 OOS gross monthly Sharpe FELL from
/089's +0.5947 to +0.5398" — rests on hand-computed gross-Sharpe figures on a
non-per-month basis. /089's documented OOS gross monthly Sharpe is +0.1717 (three
independent /089 artifacts + the /090 brief). The Critic proved +0.5947 is
mathematically impossible for /089's OOS book.

This script is pure analysis on the COMMITTED trades CSVs. No runner/src change,
no backtest re-run.

Method (identical for /089 and /090, IS and OOS):
  1. Bucket each trade into its calendar month by `open_time` (epoch-ms) — the
     same field the runner's monthly_pnl.csv uses (the trades CSV carries no
     other timestamp).
  2. VALIDATION FIRST: sum `net_pnl` per calendar month -> monthly series ->
     Sharpe = mean/std, sample std (ddof=1), NO annualization. This MUST
     reproduce (a) the per-month series in monthly_pnl.csv and (b) the net
     monthly Sharpe in comparison.csv. If it does not, the aggregation is wrong.
  3. THEN: sum `gross_pnl` per calendar month the identical way -> gross monthly
     series -> gross monthly Sharpe.

Run:  uv run python analysis/iteration_v3-090/gross_sharpe_recompute.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPORTS = Path("reports-v3")
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24, src/crypto_trade/config.py — IMMUTABLE

# Documented anchors (from committed artifacts) — for the validation cross-check.
COMPARISON_NET_SHARPE = {
    ("089", "IS"): -0.195952503376504,
    ("089", "OOS"): -0.09845342937883349,
    ("090", "IS"): -0.23045809700848496,
    ("090", "OOS"): -0.07704315881213512,
}
# /089's documented OOS gross monthly Sharpe — stated in the /089 engineering
# report, the /089 Critic review, the /089 diary, and the /090 brief.
DOC_089_OOS_GROSS = 0.1717


def monthly_sharpe(series: pd.Series) -> float:
    """Sharpe of a monthly PnL series: mean/std, sample std (ddof=1), no annualization."""
    return float(series.mean() / series.std(ddof=1))


def bucket_monthly(trades: pd.DataFrame, col: str) -> pd.Series:
    """Sum `col` per calendar month, keyed by `open_time` (epoch-ms)."""
    month = pd.to_datetime(trades["open_time"], unit="ms", utc=True).dt.strftime("%Y-%m")
    return trades.groupby(month)[col].sum().sort_index()


def load_split(iteration: str, split: str) -> pd.DataFrame:
    folder = "in_sample" if split == "IS" else "out_of_sample"
    path = REPORTS / f"iteration_v3-{iteration}" / folder / "trades.csv"
    df = pd.read_csv(path)
    # Defensive: confirm the split label matches the OOS cutoff.
    is_oos = df["open_time"] >= OOS_CUTOFF_MS
    expect_oos = split == "OOS"
    assert (is_oos == expect_oos).all(), (
        f"{iteration}/{split}: trades CSV straddles the OOS cutoff "
        f"({int((is_oos != expect_oos).sum())} mis-labeled rows)"
    )
    return df


def reference_monthly_pnl(iteration: str, split: str) -> pd.Series | None:
    folder = "in_sample" if split == "IS" else "out_of_sample"
    path = REPORTS / f"iteration_v3-{iteration}" / folder / "monthly_pnl.csv"
    if not path.exists():
        return None
    ref = pd.read_csv(path)
    return ref.set_index("month")["net_pnl"].sort_index()


def main() -> None:
    rows = []
    print("=" * 78)
    print("iter-v3/090 — gross monthly Sharpe recompute (TASK 1)")
    print("Method: per-calendar-month sum, Sharpe = mean/std (ddof=1), no annualization")
    print("=" * 78)

    for iteration in ("089", "090"):
        for split in ("IS", "OOS"):
            trades = load_split(iteration, split)
            net_m = bucket_monthly(trades, "net_pnl")
            gross_m = bucket_monthly(trades, "gross_pnl")

            net_sharpe = monthly_sharpe(net_m)
            gross_sharpe = monthly_sharpe(gross_m)
            comp_net = COMPARISON_NET_SHARPE[(iteration, split)]

            # --- VALIDATION 1: per-month net series vs monthly_pnl.csv ---
            ref = reference_monthly_pnl(iteration, split)
            series_ok = "no-ref"
            if ref is not None:
                aligned = net_m.reindex(ref.index)
                max_abs = float((aligned - ref).abs().max())
                series_ok = f"max|Δ|={max_abs:.2e}" + (
                    "  MATCH" if max_abs < 1e-9 else "  MISMATCH"
                )
                assert max_abs < 1e-9, (
                    f"{iteration}/{split}: recomputed monthly net series does NOT "
                    f"match monthly_pnl.csv (max|Δ|={max_abs:.3e}) — aggregation wrong"
                )

            # --- VALIDATION 2: net monthly Sharpe vs comparison.csv ---
            sharpe_dev = abs(net_sharpe - comp_net)
            sharpe_ok = sharpe_dev < 1e-9
            assert sharpe_ok, (
                f"{iteration}/{split}: recomputed net monthly Sharpe {net_sharpe:.10f} "
                f"!= comparison.csv {comp_net:.10f} (Δ={sharpe_dev:.3e}) — aggregation wrong"
            )

            print(
                f"\n[{iteration}/{split}]  n_months={len(net_m)}  "
                f"n_trades={len(trades)}  gross_total={gross_m.sum():+.6f}  "
                f"net_total={net_m.sum():+.6f}"
            )
            print(f"  monthly_pnl.csv series check : {series_ok}")
            print(
                f"  net monthly Sharpe           : recomputed {net_sharpe:+.6f}  "
                f"| comparison.csv {comp_net:+.6f}  | Δ={sharpe_dev:.2e}  "
                f"{'MATCH' if sharpe_ok else 'MISMATCH'}"
            )
            print(f"  gross monthly Sharpe         : recomputed {gross_sharpe:+.6f}")

            rows.append(
                {
                    "iter": iteration,
                    "split": split,
                    "net_sharpe_comparison_csv": round(comp_net, 6),
                    "net_sharpe_recomputed": round(net_sharpe, 6),
                    "net_sharpe_match": sharpe_ok,
                    "gross_sharpe_recomputed": round(gross_sharpe, 6),
                }
            )

    table = pd.DataFrame(rows)
    print("\n" + "=" * 78)
    print("AUTHORITATIVE TABLE — gross monthly Sharpe recompute")
    print("=" * 78)
    print(table.to_string(index=False))

    # --- F3 inputs ---
    gross = {(r["iter"], r["split"]): r["gross_sharpe_recomputed"] for r in rows}
    g089_oos = gross[("089", "OOS")]
    g090_oos = gross[("090", "OOS")]
    print("\n" + "=" * 78)
    print("TASK 2 — falsifier F3 inputs")
    print("=" * 78)
    print(f"  /089 OOS gross monthly Sharpe — documented anchor : +{DOC_089_OOS_GROSS:.4f}")
    print(f"  /089 OOS gross monthly Sharpe — recomputed         : {g089_oos:+.6f}")
    print(f"  /090 OOS gross monthly Sharpe — recomputed         : {g090_oos:+.6f}")
    matches_doc = abs(g089_oos - DOC_089_OOS_GROSS) < 5e-3
    doc_verdict = (
        "REPRODUCES (within 5e-3)" if matches_doc else "DISCREPANCY — recompute is authoritative"
    )
    print(f"  recompute vs documented +0.1717                    : {doc_verdict}")
    # F3 (brief Section 4): fires iff /090 OOS gross monthly Sharpe <= /089's anchor.
    f3_vs_doc = g090_oos <= DOC_089_OOS_GROSS
    f3_vs_recompute = g090_oos <= g089_oos
    print(
        f"\n  F3 ('/090 OOS gross monthly Sharpe <= /089 +0.1717'):"
        f"\n    vs documented /089 anchor (+0.1717) : "
        f"{'FIRES' if f3_vs_doc else 'does NOT fire'}"
    )
    print(
        f"    vs recomputed /089 anchor ({g089_oos:+.4f}) : "
        f"{'FIRES' if f3_vs_recompute else 'does NOT fire'}"
    )

    out = Path("analysis/iteration_v3-090/gross_sharpe_recompute_output.txt")
    with out.open("w") as fh:
        fh.write("iter-v3/090 — gross monthly Sharpe recompute (TASK 1 output)\n")
        fh.write(
            "Method: per-calendar-month sum on open_time; "
            "Sharpe=mean/std (ddof=1); no annualization\n\n"
        )
        fh.write(table.to_string(index=False))
        fh.write("\n\nF3 inputs:\n")
        fh.write(f"  /089 OOS gross monthly Sharpe — documented : +{DOC_089_OOS_GROSS:.4f}\n")
        fh.write(f"  /089 OOS gross monthly Sharpe — recomputed : {g089_oos:+.6f}\n")
        fh.write(f"  /090 OOS gross monthly Sharpe — recomputed : {g090_oos:+.6f}\n")
        fh.write(
            f"  F3 vs documented (+0.1717) : {'FIRES' if f3_vs_doc else 'does NOT fire'}\n"
        )
        f3_recompute_str = "FIRES" if f3_vs_recompute else "does NOT fire"
        fh.write(f"  F3 vs recomputed ({g089_oos:+.4f}) : {f3_recompute_str}\n")
    print(f"\nOutput saved -> {out}")


if __name__ == "__main__":
    main()
