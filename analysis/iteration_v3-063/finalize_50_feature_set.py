"""iter-v3/063 — Finalize the 50-feature selection from EDA T1-T7 outputs.

Per `feedback_v3_mass_feature_expansion.md` Path B (moderate expansion ~50):
- Start from 71-feature catalog
- Apply LDP-style greedy IC pruning (|IC|>0.70 non-carveout) — drop the
  lower-importance member of each redundant pair
- Drop non-stationary features (candle_hour_sin, ADF FAIL in 2 of 3 symbols)
- Verify target count = 50 (or near-50)
- Output T8_final_feature_set.csv with explicit pruning trace

The selection MUST preserve all 14 BASELINE_V3 features (no regression in
edge ingredients). All decisions are traceable via T8_final_feature_set.csv.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

OUT_DIR = Path("analysis/iteration_v3-063")

# BASELINE_V3 mandatory-keep set (14 features)
BASELINE_V3_KEEP = {
    "max_dd_window_50", "ema_spread_atr_20", "ret_kurt_50", "ret_skew_200",
    "range_realized_vol_50", "hurst_diff_100_50", "ret_kurt_200", "hurst_100",
    "btc_ret_14d", "ret_skew_50", "vwap_dev_20", "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d", "regime_momentum_signed_5d",
}


def main():
    catalog = pd.read_csv(OUT_DIR / "T1_feature_catalog.csv")
    adf = pd.read_csv(OUT_DIR / "T3_adf_stationarity_per_sym.csv")
    high_ic = pd.read_csv(OUT_DIR / "T4b_high_ic_pairs.csv")
    importance = pd.read_csv(OUT_DIR / "T5_importance_preview.csv")
    imp_rank: dict[str, int] = dict(zip(importance["feature"], importance["rank_gain"]))

    # Trace each decision per feature
    decisions: list[dict] = []

    candidate = set(catalog["name"])

    # === Pass 1 — drop non-stationary (NOT in baseline-keep set) ===
    non_stat = set(adf.loc[~adf["stationary_majority"], "feature"])
    for f in sorted(non_stat):
        if f in BASELINE_V3_KEEP:
            decisions.append({"feature": f, "action": "KEEP", "reason": "BASELINE_V3 mandatory; ADF FAIL accepted by mandate"})
            continue
        candidate.discard(f)
        decisions.append({"feature": f, "action": "DROP", "reason": "ADF non-stationary in majority of symbols"})

    # === Pass 2 — drop high-IC pairs (no carveout) ===
    # Greedy: process in descending |IC|; for each pair, drop the lower-importance
    # member (unless protected by baseline-keep)
    # Hard duplicates / algebraically identical features get dropped first
    dropped_by_ic: set[str] = set()
    high_ic_sorted = high_ic[~high_ic["carveout_applies"]].sort_values("abs_ic", ascending=False)
    for _, row in high_ic_sorted.iterrows():
        a, b = row["feature_a"], row["feature_b"]
        if a not in candidate or b not in candidate:
            continue
        # Protected?
        a_protected = a in BASELINE_V3_KEEP
        b_protected = b in BASELINE_V3_KEEP
        if a_protected and b_protected:
            decisions.append({
                "feature": f"{a}|{b}", "action": "KEEP_BOTH",
                "reason": f"Both BASELINE_V3 mandatory at |IC|={row['abs_ic']:.3f}",
            })
            continue
        # Drop the lower-importance one
        a_rank = imp_rank.get(a, 999)
        b_rank = imp_rank.get(b, 999)
        if a_protected:
            drop = b
        elif b_protected:
            drop = a
        elif a_rank < b_rank:  # lower rank number = higher importance
            drop = b
        else:
            drop = a
        if drop in candidate:
            candidate.discard(drop)
            dropped_by_ic.add(drop)
            kept = b if drop == a else a
            decisions.append({
                "feature": drop, "action": "DROP",
                "reason": f"|IC|={row['abs_ic']:.3f} with {kept} (kept; ranks {a_rank} vs {b_rank})",
            })

    # === Pass 3 — drop zero-gain features (model couldn't learn from them) ===
    # candle_hour_cos has gain=0 in importance preview — bin shift dominated by
    # cos symmetry under 4-bin 8h cadence; effectively constant per symbol.
    zero_gain_drops: list[str] = []
    for f in list(candidate):
        if f in BASELINE_V3_KEEP:
            continue
        gain = importance.loc[importance["feature"] == f, "gain"].iloc[0] if f in importance["feature"].values else None
        if gain is not None and float(gain) <= 1.0:
            candidate.discard(f)
            zero_gain_drops.append(f)
            decisions.append({
                "feature": f, "action": "DROP",
                "reason": f"Zero/near-zero gain in importance preview (gain={gain:.2f}); model could not learn"
            })

    # === Pass 4 — final count adjustment ===
    print(f"After ADF + IC + zero-gain pruning: {len(candidate)} features.")
    print(f"  Baseline-V3 mandatory: {len(BASELINE_V3_KEEP & candidate)} of 14")

    # If we're well above 50, trim bottom-importance non-baseline features
    if len(candidate) > 55:
        cand_non_base = [(f, imp_rank.get(f, 999)) for f in candidate if f not in BASELINE_V3_KEEP]
        cand_non_base.sort(key=lambda x: x[1], reverse=True)  # highest rank = lowest importance
        n_to_drop = len(candidate) - 50
        for f, rank in cand_non_base[:n_to_drop]:
            candidate.discard(f)
            decisions.append({
                "feature": f, "action": "DROP",
                "reason": f"Bottom-importance prune to reach target 50 (rank {rank})",
            })

    final = sorted(candidate)
    print(f"Final feature count: {len(final)}")
    print(f"Baseline-V3 preserved: {len(BASELINE_V3_KEEP & set(final))} of 14")
    print()
    print("Final feature set:")
    for f in final:
        is_base = "BASE" if f in BASELINE_V3_KEEP else "NEW "
        cat = catalog.loc[catalog["name"] == f, "category"].iloc[0]
        gain = importance.loc[importance["feature"] == f, "gain"].iloc[0] if f in importance["feature"].values else None
        print(f"  [{is_base}] {f:35s} ({cat:15s})  gain={gain:.0f}" if gain else f"  [{is_base}] {f:35s} ({cat:15s})")

    # Save decisions trace
    pd.DataFrame(decisions).to_csv(OUT_DIR / "T8_pruning_decisions.csv", index=False)

    # Save final feature set
    final_df = pd.DataFrame({
        "feature": final,
        "in_baseline_v3": [f in BASELINE_V3_KEEP for f in final],
    })
    final_df = final_df.merge(catalog[["name", "category", "source", "present_in_pq", "compute_status"]],
                              left_on="feature", right_on="name", how="left").drop(columns=["name"])
    final_df = final_df.merge(importance[["feature", "rank_gain", "gain"]], on="feature", how="left")
    final_df = final_df.sort_values("rank_gain")
    final_df.to_csv(OUT_DIR / "T8_final_feature_set.csv", index=False)

    # Summary stats
    cat_counts = final_df["category"].value_counts()
    print()
    print("Final category distribution:")
    print(cat_counts.to_string())

    # Implementation surface for the final set
    new_count = (~final_df["present_in_pq"]).sum()
    print()
    print(f"NEW features (need impl): {new_count}")
    print(f"Already in parquet (zero compute cost): {(final_df['present_in_pq']).sum()}")

    return final


if __name__ == "__main__":
    main()
