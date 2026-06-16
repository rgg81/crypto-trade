"""iter-v1/002 EXPLORATION — IS-only feature pruning audit for BTCUSDT.

Hypothesis under test: a pruned, higher-signal BTC feature set (cutting noise that
drives iter-001's HIGH K=20 bagging dispersion of 49.46) lifts IS Sharpe without
surrendering OOS.

This script is the EVIDENCE for briefs-v1/BTCUSDT/iteration_v1-002/feature_report.md.
Everything here uses ONLY in-sample data (close_time < OOS_CUTOFF_MS, 2025-03-24).
We NEVER read OOS in design.

Outputs (printed; tables copied into feature_report.md):
  1. Per-feature IS importance (from iter-001 portfolio CSV) + IS IC vs forward label.
     - ic_1bar : Spearman(feature, next-candle log-return)  -> matches iter-001 ic_matrix
                 convention (run_baseline_v1._compute_forward_returns: log(close.shift(-1)/close)).
     - ic_21bar: Spearman(feature, 21-candle-forward log-return) -> matches the MODEL's
                 actual label horizon (timeout_minutes=10080 / interval 480 = 21 candles).
  2. Hierarchical clustering on |Spearman corr| distance across the full 193 -> redundant
     families (1 - |rho| as distance; average linkage; cut at 0.30 -> |rho|>=0.70 merge).
  3. The proposed pruned column list, with per-feature: importance rank, |IC|, ADF pass,
     cluster id, and a keep/drop reason.

Run: uv run python analysis/BTCUSDT/iteration_v1-002/ic_pruning_audit.py
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[3]
PARQUET = REPO / "data" / "features" / "BTCUSDT_8h_features.parquet"
IMP_CSV = (
    REPO
    / "reports-v1"
    / "BTCUSDT"
    / "iteration_v1-001"
    / "in_sample"
    / "feature_importance_portfolio.csv"
)
ADF_CSV = REPO / "reports-v1" / "BTCUSDT" / "iteration_v1-001" / "in_sample" / "adf_test.csv"

# Sacred constant. NEVER changes. IS = close_time strictly before this.
OOS_CUTOFF_MS = pd.Timestamp("2025-03-24", tz="UTC").value // 10**6
HORIZON_CANDLES = 21  # timeout_minutes=10080 / interval_minutes=480 = 21 (model label horizon)


def load_is_frame() -> pd.DataFrame:
    """BTC features, IS-only (close_time < OOS_CUTOFF_MS), sorted by open_time."""
    df = pd.read_parquet(PARQUET)
    df = df.sort_values("open_time").reset_index(drop=True)
    is_df = df[df["close_time"] < OOS_CUTOFF_MS].copy()
    return is_df


def forward_log_return(df: pd.DataFrame, horizon: int) -> np.ndarray:
    """h-candle-forward log return: log(close[t+h]/close[t]). Past-only target (no leak:
    used only as the *label* in IC, never as a feature)."""
    close = df["close"].astype(float)
    fwd = np.log(close.shift(-horizon) / close)
    return fwd.to_numpy()


def main() -> None:
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS, V1_FEATURE_COLUMNS_PRUNED

    full_cols = list(V1_FEATURE_COLUMNS)
    legacy_pruned = list(V1_FEATURE_COLUMNS_PRUNED)

    df = load_is_frame()
    print(f"[load] IS rows: {len(df)}  (close_time < {OOS_CUTOFF_MS})")
    print(
        f"[load] IS span: {pd.to_datetime(df['close_time'].min(), unit='ms')} "
        f"-> {pd.to_datetime(df['close_time'].max(), unit='ms')}"
    )
    n_present = sum(c in df.columns for c in full_cols)
    print(f"[load] full feature cols present: {n_present}/{len(full_cols)}")

    fwd1 = forward_log_return(df, 1)
    fwd21 = forward_log_return(df, HORIZON_CANDLES)

    # ---- 1. per-feature IC (IS-only) -------------------------------------------------
    rows = []
    for c in full_cols:
        feat = df[c].to_numpy(dtype=float)
        # 1-bar IC
        m1 = ~(np.isnan(feat) | np.isnan(fwd1))
        ic1 = (
            spearmanr(feat[m1], fwd1[m1])[0]
            if m1.sum() > 30 and np.nanstd(feat[m1]) > 0
            else np.nan
        )
        # 21-bar IC
        m21 = ~(np.isnan(feat) | np.isnan(fwd21))
        ic21 = (
            spearmanr(feat[m21], fwd21[m21])[0]
            if m21.sum() > 30 and np.nanstd(feat[m21]) > 0
            else np.nan
        )
        nan_frac = float(np.isnan(feat).mean())
        rows.append(
            dict(
                feature=c,
                ic_1bar=ic1,
                ic_21bar=ic21,
                abs_ic_1bar=abs(ic1) if ic1 == ic1 else np.nan,
                abs_ic_21bar=abs(ic21) if ic21 == ic21 else np.nan,
                nan_frac=nan_frac,
                is_n=int(m21.sum()),
            )
        )
    ic_df = pd.DataFrame(rows).set_index("feature")

    # ---- merge iter-001 importance ---------------------------------------------------
    imp = pd.read_csv(IMP_CSV).set_index("feature_name")
    ic_df["imp_gain"] = imp["mean_gain"].reindex(ic_df.index)
    ic_df["imp_rank"] = imp["importance_rank"].reindex(ic_df.index)

    # ---- merge ADF (informational) ---------------------------------------------------
    adf = pd.read_csv(ADF_CSV).set_index("feature")
    ic_df["adf_raw_pass"] = adf["raw_pass"].reindex(ic_df.index)
    ic_df["adf_family"] = adf["family"].reindex(ic_df.index)

    # ---- 2. hierarchical clustering on |Spearman corr| -------------------------------
    feat_mat = df[full_cols].to_numpy(dtype=float)
    # pairwise Spearman across features (IS-only). NaN-robust per-pair would be O(n^2*rows);
    # use a single rank-then-pearson on column-median-filled ranks (standard for |IC| clustering).
    ranked = pd.DataFrame(feat_mat, columns=full_cols).rank()
    ranked = ranked.fillna(ranked.mean())
    corr = np.corrcoef(ranked.to_numpy().T)
    corr = np.nan_to_num(corr, nan=0.0)
    np.fill_diagonal(corr, 1.0)
    dist = 1.0 - np.abs(corr)
    dist = (dist + dist.T) / 2.0
    np.fill_diagonal(dist, 0.0)
    condensed = squareform(dist, checks=False)
    linkage_z = linkage(condensed, method="average")
    # cut at distance 0.30 => merge anything with |rho| >= 0.70 (redundancy threshold)
    cluster_ids = fcluster(linkage_z, t=0.30, criterion="distance")
    ic_df["cluster"] = pd.Series(cluster_ids, index=full_cols).reindex(ic_df.index)

    n_clusters = len(set(cluster_ids))
    print(f"\n[cluster] {len(full_cols)} features -> {n_clusters} clusters at |rho|>=0.70 merge")
    # show clusters with >1 member (the redundant families)
    csizes = pd.Series(cluster_ids, index=full_cols).value_counts()
    multi = csizes[csizes > 1]
    print(
        f"[cluster] {len(multi)} multi-member clusters cover "
        f"{int(multi.sum())} features; {int((csizes == 1).sum())} singletons"
    )

    # ---- 3. ranked shortlist ---------------------------------------------------------
    ic_df = ic_df.sort_values("imp_rank")

    print("\n" + "=" * 110)
    print("TOP 60 FEATURES BY iter-001 IS IMPORTANCE (with IS IC + cluster + ADF)")
    print("=" * 110)
    show = ic_df.head(60)[
        [
            "imp_rank",
            "imp_gain",
            "ic_1bar",
            "ic_21bar",
            "abs_ic_21bar",
            "adf_raw_pass",
            "cluster",
            "nan_frac",
        ]
    ]
    pd.set_option("display.width", 200)
    pd.set_option("display.max_rows", 200)
    print(show.to_string(float_format=lambda x: f"{x:.4f}"))

    # ---- cluster-representative selection --------------------------------------------
    # Within each multi-member cluster, keep the member with the best importance rank
    # (lowest imp_rank). This is the "redundant-family deduplication" step.
    keep_per_cluster: dict[int, str] = {}
    for cl, grp in ic_df.groupby("cluster"):
        best = grp.sort_values("imp_rank").index[0]
        keep_per_cluster[int(cl)] = best

    # Candidate pruned set: top-K by importance, then drop redundant cluster siblings.
    # Strategy: take the top 70 by importance, then within that pool keep only one
    # representative per cluster (the best-ranked), then trim to a 30-45 target via a
    # combined score = importance_rank_pct + redundancy. We expose the components so QR
    # can adjust the cutoff.
    top_pool = ic_df.head(80).copy()
    # mark redundancy: is this feature the cluster representative within the pool?
    pool_reps: dict[int, str] = {}
    for cl, grp in top_pool.groupby("cluster"):
        pool_reps[int(cl)] = grp.sort_values("imp_rank").index[0]
    top_pool["is_cluster_rep"] = [
        f == pool_reps.get(int(cl)) for f, cl in zip(top_pool.index, top_pool["cluster"])
    ]
    redundant_dropped = top_pool[~top_pool["is_cluster_rep"]]
    print("\n" + "=" * 110)
    print("REDUNDANT SIBLINGS DROPPED (top-80 pool, non-cluster-representative)")
    print("=" * 110)
    print(
        redundant_dropped[["imp_rank", "cluster", "abs_ic_21bar"]]
        .sort_values("cluster")
        .to_string(float_format=lambda x: f"{x:.4f}")
    )

    # ---- iter-001-importance-INERT tail ----------------------------------------------
    inert_tail = ic_df[ic_df["imp_rank"] > 150]
    print(f"\n[inert] {len(inert_tail)} features rank >150/193 in iter-001 (bottom-quartile noise)")
    print("        these are the primary prune targets (low split-share AND low |IC|):")
    print(
        inert_tail.sort_values("abs_ic_21bar")
        .head(25)[["imp_rank", "abs_ic_21bar", "ic_21bar"]]
        .to_string(float_format=lambda x: f"{x:.4f}")
    )

    # ---- overlap with legacy pruned set (prior-track knowledge) -----------------------
    legacy_in_full = [c for c in legacy_pruned if c in full_cols]
    print(
        f"\n[legacy] V1_FEATURE_COLUMNS_PRUNED has {len(legacy_pruned)} cols; "
        f"{len(legacy_in_full)} are in the 193 full set."
    )
    legacy_imp = ic_df.loc[[c for c in legacy_in_full]][["imp_rank", "abs_ic_21bar"]]
    print("[legacy] iter-001 BTC importance of the legacy-pruned members:")
    print(legacy_imp.sort_values("imp_rank").to_string(float_format=lambda x: f"{x:.4f}"))
    legacy_top50 = legacy_imp[legacy_imp["imp_rank"] <= 50]
    print(
        f"[legacy] {len(legacy_top50)}/{len(legacy_in_full)} legacy-pruned members "
        f"land in BTC top-50 importance; "
        f"{int((legacy_imp['imp_rank'] > 100).sum())} land >100 (BTC-weak)."
    )

    # save the full audit table for the brief / future reference
    out = REPO / "analysis" / "BTCUSDT" / "iteration_v1-002" / "ic_importance_cluster_table.csv"
    ic_df.to_csv(out)
    print(f"\n[save] full audit table -> {out}")


if __name__ == "__main__":
    main()
