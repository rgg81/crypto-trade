"""iter-v3/110 EDA — T6 recompute (composite-score sign fix).

universe_construction.py's first T6 had an inconsistent rank convention: it
mixed ascending and descending ``DataFrame.rank`` calls, so the summed
``composite_score`` was not monotone in goodness (it ranked ATOM — the WORST
signal — at #1). This script recomputes T6 with ALL three component ranks on
the SAME convention: rank N = best. It reads the already-committed T1/T4/T5
CSVs — no re-fitting, no model involvement, fully reproducible.

Convention (all "rank N = best", i.e. larger rank number = better symbol):
  mean_fold_auc       — higher is better -> rank ascending=True  (largest AUC -> rank N)
  gated_hit_rate      — higher is better -> rank ascending=True
  perm_p_value        — LOWER is better  -> rank ascending=False (smallest p -> rank N)
composite_score = sum of the three; sort DESCENDING (largest sum = best).
"""

from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import INCUMBENTS  # noqa: E402

OUT = Path(__file__).resolve().parent

t1 = pd.read_csv(OUT / "T1_per_symbol_signal.csv")
t4 = pd.read_csv(OUT / "T4_gated_tail_edge.csv")
t5 = pd.read_csv(OUT / "T5_pnl_correlation.csv")

merged = t1.merge(
    t4[["symbol", "n_gated", "gated_hit_rate", "binom_p_vs_random", "mean_gated_bet_pnl"]],
    on="symbol",
    how="left",
)

# all three on the "rank N = best" convention
merged["rk_auc"] = merged["mean_fold_auc"].rank(ascending=True)        # high AUC -> high rank
merged["rk_hit"] = merged["gated_hit_rate"].rank(ascending=True)        # high hit -> high rank
merged["rk_perm_p"] = merged["perm_p_value"].rank(ascending=False)     # low p   -> high rank
merged["composite_score"] = merged["rk_auc"] + merged["rk_hit"] + merged["rk_perm_p"]
merged = merged.sort_values("composite_score", ascending=False).reset_index(drop=True)
merged["final_rank"] = np.arange(1, len(merged) + 1)

cols = [
    "final_rank", "symbol", "is_incumbent", "mean_fold_auc", "perm_p_value",
    "SIGNAL_GO", "gated_hit_rate", "binom_p_vs_random", "mean_gated_bet_pnl",
    "composite_score",
]
merged[cols].to_csv(OUT / "T6_universe_recommendation.csv", index=False)

# diversification: mean pairwise PnL-proxy corr of the top-N
def mean_corr(syms: list[str]) -> float:
    pairs = [
        t5[(t5["sym_a"].isin([a, b])) & (t5["sym_b"].isin([a, b]))]["pnl_proxy_corr"].iloc[0]
        for a, b in combinations(syms, 2)
    ]
    return float(np.mean(pairs))


print("=== T6 final composite ranking (sign-corrected) ===")
print(merged[cols].to_string(index=False))

top5 = list(merged.head(5)["symbol"])
top6 = list(merged.head(6)["symbol"])
print(f"\nTop-5 universe = {top5}")
print(f"  mean pairwise PnL-proxy corr (top-5) = {mean_corr(top5):.4f}")
print(f"Top-6 universe = {top6}")
print(f"  mean pairwise PnL-proxy corr (top-6) = {mean_corr(top6):.4f}")
print(
    f"Incumbent BCH/LDO/TRX mean pairwise PnL-proxy corr = "
    f"{mean_corr(list(INCUMBENTS)):.4f}"
)

# the three highest-AUC signal symbols (the alternate "pure signal" cut)
sig3 = list(t1.sort_values("mean_fold_auc", ascending=False).head(3)["symbol"])
print(f"\nPure-signal top-3 (by mean_fold_auc) = {sig3}")
print(f"  mean pairwise PnL-proxy corr = {mean_corr(sig3):.4f}")
sig5 = list(t1.sort_values("mean_fold_auc", ascending=False).head(5)["symbol"])
print(f"Pure-signal top-5 (by mean_fold_auc) = {sig5}")
print(f"  mean pairwise PnL-proxy corr = {mean_corr(sig5):.4f}")
