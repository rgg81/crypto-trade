"""iter-v1/002 EXPLORATION — construct the BTC-specific pruned feature set (IS-only).

Consumes analysis/BTCUSDT/iteration_v1-002/ic_importance_cluster_table.csv
(written by ic_pruning_audit.py). Builds the proposed pruned column list by a
transparent, defensible rule and reports its properties so QR can adjust the cutoff.

SELECTION RULE (IS-only, BTC-specific):
  Start from the 52 clusters found at |Spearman rho| >= 0.70 (1 - |rho| distance).
  1. CLUSTER DEDUP: within each multi-member cluster keep ONE representative — the
     member with the best iter-001 BTC importance rank, BUT prefer an ADF-stationary
     member when the rank gap is small (<=3 ranks) so we don't anchor a family on a
     non-stationary price-level proxy.
  2. IMPORTANCE GATE: drop any representative whose iter-001 BTC importance rank is
     worse than 130/193 AND whose |IC_21bar| < 0.03 (joint inert: neither split-share
     nor directional signal). A representative that is BTC-weak on BOTH axes is noise.
  3. cal_dow_norm (calendar seasonality) is force-retained as a cheap orthogonal signal
     even though it falls below the importance gate.

This is a SELECTION/PRUNING iteration: no new engineered features are introduced. The
proposed set is a STRICT SUBSET of the 193-col V1_FEATURE_COLUMNS (purely OHLCV-derived:
cal/interact/mom/mr/stat/trend/vol). The orthogonal non-OHLCV families (funding / OI /
long-short / basis / regime-composed) are NOT in the 193 baseline — adding them is a
NEW-FEATURE axis (recommended iter-003), not pruning; ORTHOGONAL_KEEP is left empty.

Run: uv run python analysis/BTCUSDT/iteration_v1-002/build_pruned_set.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
TABLE = REPO / "analysis" / "BTCUSDT" / "iteration_v1-002" / "ic_importance_cluster_table.csv"

# NOTE on orthogonal non-OHLCV families (funding / OI / long-short / basis / regime):
# These are NOT members of the 193-col V1_FEATURE_COLUMNS that iter-001 trained on (the
# baseline dump is purely OHLCV-derived: cal/interact/mom/mr/stat/trend/vol). They exist
# in the parquet but adding them is a NEW-FEATURE axis, not pruning. To keep iter-002 a
# clean test of the PRUNING hypothesis, the proposed set is a STRICT SUBSET of the 193.
# The orthogonal families are flagged as the recommended iter-003 axis (see feature_report).
ORTHOGONAL_KEEP: list[str] = []


def main() -> None:
    t = pd.read_csv(TABLE).set_index("feature")

    # ---- step 1: cluster representatives ---------------------------------------------
    reps: list[str] = []
    rep_reason: dict[str, str] = {}
    for cl, grp in t.groupby("cluster"):
        grp = grp.sort_values("imp_rank")
        best = grp.index[0]
        best_rank = grp.loc[best, "imp_rank"]
        # prefer an ADF-stationary member if within 3 ranks of the best
        adf_members = grp[grp["adf_raw_pass"] == True]  # noqa: E712
        chosen = best
        reason = f"cluster {int(cl)} rep (best BTC rank {int(best_rank)}; n={len(grp)})"
        if not bool(grp.loc[best, "adf_raw_pass"]) and len(adf_members) > 0:
            adf_best = adf_members.sort_values("imp_rank").index[0]
            if adf_members.loc[adf_best, "imp_rank"] - best_rank <= 3:
                chosen = adf_best
                reason = (
                    f"cluster {int(cl)} rep (ADF-stationary swap: {best}->{adf_best}; "
                    f"best non-stationary; n={len(grp)})"
                )
        reps.append(chosen)
        rep_reason[chosen] = reason

    rep_df = t.loc[reps].copy()

    # ---- step 2: importance gate -----------------------------------------------------
    inert_mask = (rep_df["imp_rank"] > 130) & (rep_df["abs_ic_21bar"] < 0.03)
    dropped_inert = rep_df[inert_mask]
    kept = rep_df[~inert_mask].copy()

    # ---- step 3: orthogonal keeps (add any not already kept) --------------------------
    ortho_present = [c for c in ORTHOGONAL_KEEP if c in t.index]
    for c in ortho_present:
        if c not in kept.index:
            row = t.loc[[c]]
            kept = pd.concat([kept, row])
            rep_reason[c] = "orthogonal non-OHLCV/composed family (diversification)"

    # also retain the calendar pair (cheap, orthogonal seasonality) if present & not inert
    for c in ["cal_dow_norm"]:
        if c in t.index and c not in kept.index:
            kept = pd.concat([kept, t.loc[[c]]])
            rep_reason[c] = "calendar seasonality (orthogonal, cheap)"

    final = sorted(kept.index.tolist())

    print("=" * 100)
    print(f"PROPOSED PRUNED SET: {len(final)} features  (from 193 -> {len(final)})")
    print("=" * 100)
    rep_view = kept.sort_values("imp_rank")[
        ["imp_rank", "abs_ic_21bar", "ic_21bar", "adf_raw_pass", "cluster"]
    ]
    print(rep_view.to_string(float_format=lambda x: f"{x:.4f}"))

    print("\n--- dropped as joint-inert (rank>130 AND |IC21|<0.03) ---")
    print(
        dropped_inert[["imp_rank", "abs_ic_21bar", "cluster"]].to_string(
            float_format=lambda x: f"{x:.4f}"
        )
    )

    # ---- properties ------------------------------------------------------------------
    adf_pass = int(kept["adf_raw_pass"].sum())
    print(
        f"\n[props] ADF raw-alpha pass: {adf_pass}/{len(final)} "
        f"({100 * adf_pass / len(final):.0f}%)"
    )
    print(
        f"[props] median |IC_21bar|: {kept['abs_ic_21bar'].median():.4f}  "
        f"(full-193 median: {t['abs_ic_21bar'].median():.4f})"
    )
    print(
        f"[props] mean iter-001 importance rank of kept: {kept['imp_rank'].mean():.1f} "
        f"(of 193); {int((kept['imp_rank'] <= 50).sum())} are top-50, "
        f"{int((kept['imp_rank'] <= 100).sum())} are top-100"
    )
    n_clusters_kept = kept["cluster"].nunique()
    print(f"[props] clusters represented: {n_clusters_kept} (1 feature per redundant family)")

    # ---- emit copy-pasteable python list ---------------------------------------------
    print("\n" + "=" * 100)
    print("COPY-PASTEABLE feature_columns LIST")
    print("=" * 100)
    print("V1_BTC_PRUNED_ITER002 = [")
    for c in final:
        print(f'    "{c}",')
    print("]")

    out = REPO / "analysis" / "BTCUSDT" / "iteration_v1-002" / "pruned_set_final.csv"
    rep_view.to_csv(out)
    print(f"\n[save] pruned set table -> {out}")
    print(f"[save] count = {len(final)}")


if __name__ == "__main__":
    main()
