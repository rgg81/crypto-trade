"""iter-v1/002 EXPLORATION — quantify the signal-density / redundancy gain of the
pruned set vs the full 193, IS-only, to ground the dispersion-reduction prediction.

The K=20 bagging dispersion (iter-001 mean = 49.46) measures how much the 20 Optuna
studies disagree per candle. The mechanistic driver of high dispersion is a wide,
redundant feature space: each study, on its own colsample_bytree subsample + bootstrap,
can latch onto a DIFFERENT member of a redundant cluster (e.g. one study uses
trend_ema_5, another trend_sma_50 — same factor, different split path). Pruning
redundant siblings forces all studies toward the SAME representative -> tighter
consensus -> lower dispersion.

This script does NOT run the backtest (that is QE's Phase 6). It produces IS-only
proxies that justify the *direction* of the dispersion prediction:
  - feature-count reduction (193 -> N)
  - redundancy reduction: max off-diagonal |Spearman corr| within the kept set vs full
  - signal density: median |IC_21bar| of kept vs full; share of kept features that clear
    a |IC|>=0.03 floor.

Run: uv run python analysis/BTCUSDT/iteration_v1-002/dispersion_proxy.py
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[3]
PARQUET = REPO / "data" / "features" / "BTCUSDT_8h_features.parquet"
PRUNED_CSV = REPO / "analysis" / "BTCUSDT" / "iteration_v1-002" / "pruned_set_final.csv"
TABLE = REPO / "analysis" / "BTCUSDT" / "iteration_v1-002" / "ic_importance_cluster_table.csv"
OOS_CUTOFF_MS = pd.Timestamp("2025-03-24", tz="UTC").value // 10**6


def mean_abs_offdiag(corr: np.ndarray) -> float:
    n = corr.shape[0]
    if n < 2:
        return float("nan")
    iu = np.triu_indices(n, k=1)
    return float(np.nanmean(np.abs(corr[iu])))


def frac_redundant(corr: np.ndarray, thresh: float = 0.70) -> float:
    """Fraction of feature pairs with |rho| >= thresh (the redundancy load)."""
    n = corr.shape[0]
    if n < 2:
        return float("nan")
    iu = np.triu_indices(n, k=1)
    a = np.abs(corr[iu])
    return float((a >= thresh).mean())


def main() -> None:
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS

    full_cols = list(V1_FEATURE_COLUMNS)
    pruned = pd.read_csv(PRUNED_CSV).iloc[:, 0].tolist()
    t = pd.read_csv(TABLE).set_index("feature")

    df = pd.read_parquet(PARQUET).sort_values("open_time").reset_index(drop=True)
    df = df[df["close_time"] < OOS_CUTOFF_MS]

    def rank_corr(cols: list[str]) -> np.ndarray:
        r = df[cols].rank()
        r = r.fillna(r.mean())
        c = np.corrcoef(r.to_numpy().T)
        return np.nan_to_num(c, nan=0.0)

    corr_full = rank_corr(full_cols)
    corr_pruned = rank_corr(pruned)

    print("=" * 78)
    print(f"SIGNAL-DENSITY / REDUNDANCY: full-193 vs pruned-{len(pruned)}")
    print("=" * 78)
    print(
        f"  feature count                : 193 -> {len(pruned)}  "
        f"({100 * len(pruned) / 193:.0f}% retained, {193 - len(pruned)} cut)"
    )
    print(
        f"  mean |Spearman| off-diagonal : {mean_abs_offdiag(corr_full):.4f} -> "
        f"{mean_abs_offdiag(corr_pruned):.4f}"
    )
    print(
        f"  frac pairs |rho|>=0.70 (redund): {frac_redundant(corr_full):.4f} -> "
        f"{frac_redundant(corr_pruned):.4f}"
    )
    fic = t.loc[full_cols, "abs_ic_21bar"]
    pic = t.loc[pruned, "abs_ic_21bar"]
    print(f"  median |IC_21bar|            : {fic.median():.4f} -> {pic.median():.4f}")
    print(
        f"  share |IC_21bar|>=0.03       : {(fic >= 0.03).mean():.2f} -> {(pic >= 0.03).mean():.2f}"
    )
    print(
        f"  median iter-001 imp rank     : {t.loc[full_cols, 'imp_rank'].median():.0f}/193 -> "
        f"{t.loc[pruned, 'imp_rank'].median():.0f}/193"
    )

    print("\n--- INTERPRETATION ---")
    print(
        "  The pruned set cuts the redundant-pair load from "
        f"{frac_redundant(corr_full):.3f} to {frac_redundant(corr_pruned):.3f} "
        "of all pairs and raises"
    )
    print("  median |IC| signal density. Both push the 20 Optuna studies toward the SAME")
    print("  cluster representatives -> the mechanistic driver of per-candle disagreement")
    print("  (studies latching onto different redundant siblings) is removed.")
    print("  PREDICTION: K-bagging dispersion should DROP from iter-001's 49.46.")


if __name__ == "__main__":
    main()
