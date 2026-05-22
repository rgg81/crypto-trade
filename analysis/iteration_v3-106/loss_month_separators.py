"""iter-v3/106 EDA script 2 — characterize the IS loss months.

Tests the user's hypothesis: the IS loss months are "unseen-regime" months —
the market state is novel / far from the model's training distribution.

For each IS calendar month, computes (strictly IS-only, strictly causal — every
value is a function only of data with open_time < the month's start) a battery
of candidate REGIME SEPARATORS, then measures which one cleanly separates the
15 loss months from the 21 profit months identified in EDA 1.

The headline candidate — and the genuinely-NEW mechanism vs the incumbent
RiskV2 gates — is a TRAILING-WINDOW MAHALANOBIS OOD DISTANCE:

  At month M, take the model's per-symbol TRAINING window (the trailing
  `training_months = 24` of feature rows that the LightGBM for the first cell of
  month M is fit on). Fit a mean vector mu and covariance Sigma on that window.
  Then take the feature rows of month M itself and compute the mean Mahalanobis
  distance  D(M) = mean_t sqrt( (x_t - mu)^T Sigma^-1 (x_t - mu) ).

  D(M) large  <=>  month M's joint feature distribution sits far from what the
  model was trained on  <=>  the user's "regime the model hasn't seen".

Why this is NOT a re-tread of the incumbent gates:
  - R3 z-score OOD (risk_v2._zscore_ood) is UNIVARIATE: it fires if ANY single
    feature's |z| exceeds a threshold, against the FULL static IS window. It is
    blind to (a) joint/correlation structure — a month can be OOD in the
    *combination* of features while every marginal sits at |z|<2; and (b) it
    uses the whole IS as the reference, not the rolling 24-month TRAINING
    window, so it cannot detect drift relative to what the current model
    actually saw.
  - The Mahalanobis composite is MULTIVARIATE (uses Sigma^-1, i.e. the full
    covariance) and TRAILING (re-fits the reference to each month's own
    24-month training window). It is a different statistic on a different
    reference set.
  - Primitive 9 (regime kill switch) keyed on BTC drawdown_30d / BTC vol-z is
    CLOSED (/022, /074). Mahalanobis on the symbol's own 14-feature vector is a
    different signal — it is the model's own input-space novelty, not a
    hand-picked BTC scalar.

Secondary separators computed for completeness / to confirm Mahalanobis wins:
  - btc_dd_30d        : BTC 30-day (90-bar) drawdown at month start  [primitive 9 — closed]
  - btc_vol_z_30d     : BTC realized-vol z-score at month start      [primitive 9 — closed]
  - atr_pct_rank_200  : symbol ATR percentile (vol regime)
  - hurst_100         : symbol Hurst (trend vs mean-revert regime)
  - range_realized_vol_50 : symbol realized vol level

NO CHEATING — strictly IS-only and strictly causal. The Mahalanobis reference
window for month M ends at month M's start (training_months back); month M's own
rows are scored against a reference that does NOT include them. No post-cutoff
data is read.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.features_v3 import V3_FEATURE_COLUMNS

OUT_DIR = "analysis/iteration_v3-106"
SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
TRAINING_MONTHS = 24  # IMMUTABLE — matches src/crypto_trade/config.py
BAR_MS = 8 * 60 * 60 * 1000


def load_features(symbol: str) -> pd.DataFrame:
    cols = [
        "open_time",
        "high",
        "low",
        "close",
        "atr_pct_rank_200",
        "hurst_100",
        "range_realized_vol_50",
        *V3_FEATURE_COLUMNS,
    ]
    cols = list(dict.fromkeys(cols))
    df = pq.read_table(f"data/features_v3/{symbol}_8h_features.parquet", columns=cols).to_pandas()
    return df.sort_values("open_time").reset_index(drop=True)


def mahalanobis_for_window(ref: np.ndarray, test: np.ndarray) -> float:
    """Mean Mahalanobis distance of `test` rows against the `ref` distribution.

    ref, test : (n, d) arrays of the 14 V3 features. Rows with any NaN dropped.
    Sigma is regularized (ridge on the diagonal) for numerical stability — the
    same shrinkage idea v1's R3 OOD gate uses; the regularization is a fixed
    a-priori 1e-6 * mean-variance, not tuned.
    """
    ref = ref[~np.isnan(ref).any(axis=1)]
    test = test[~np.isnan(test).any(axis=1)]
    if len(ref) < 50 or len(test) == 0:
        return np.nan
    mu = ref.mean(axis=0)
    cov = np.cov(ref, rowvar=False)
    ridge = 1e-6 * np.mean(np.diag(cov))
    cov = cov + ridge * np.eye(cov.shape[0])
    try:
        inv = np.linalg.inv(cov)
    except np.linalg.LinAlgError:
        return np.nan
    diff = test - mu
    d2 = np.einsum("ij,jk,ik->i", diff, inv, diff)
    d2 = d2[d2 >= 0]
    return float(np.sqrt(d2).mean()) if len(d2) else np.nan


def btc_regime_series() -> pd.DataFrame:
    """BTC 30-day drawdown + realized-vol z-score, indexed by open_time. Past-only."""
    btc = pq.read_table(
        "data/features_v3/BTCUSDT_8h_features.parquet", columns=["open_time", "close"]
    ).to_pandas()
    btc = btc.sort_values("open_time").reset_index(drop=True)
    c = btc["close"].astype(float)
    # 90-bar (30-day) rolling max drawdown, past-only via shift(1)
    cs = c.shift(1)
    roll_max = cs.rolling(90, min_periods=20).max()
    btc["btc_dd_30d"] = ((roll_max - cs) / roll_max * 100.0).clip(lower=0.0)
    # realized-vol z-score: 90-bar std of log returns, z vs trailing 360-bar
    logret = np.log(c / c.shift(1))
    vol90 = logret.rolling(90, min_periods=20).std().shift(1)
    btc["btc_vol_z_30d"] = (vol90 - vol90.rolling(360, min_periods=90).mean()) / vol90.rolling(
        360, min_periods=90
    ).std()
    return btc[["open_time", "btc_dd_30d", "btc_vol_z_30d"]]


def main() -> None:
    months = pd.read_csv(f"{OUT_DIR}/T1_per_month_is_pnl.csv")
    months["is_loss"] = months["weighted_pnl"] < 0

    feats = {s: load_features(s) for s in SYMBOLS}
    btc = btc_regime_series()

    rows = []
    for _, m in months.iterrows():
        month = m["month"]
        month_start = pd.Period(month, freq="M").start_time
        month_end = pd.Period(month, freq="M").end_time
        ms_start = int(month_start.value // 1_000_000)
        ms_end = int(month_end.value // 1_000_000)
        # Trailing training window: [ms_start - 24 months, ms_start)
        train_start = int(
            (month_start - pd.DateOffset(months=TRAINING_MONTHS)).value // 1_000_000
        )

        # --- Mahalanobis OOD: per symbol, pool the per-symbol distances ---
        maha_per_sym = []
        for s in SYMBOLS:
            df = feats[s]
            ref = df[(df["open_time"] >= train_start) & (df["open_time"] < ms_start)]
            test = df[(df["open_time"] >= ms_start) & (df["open_time"] <= ms_end)]
            if len(ref) < 50 or len(test) == 0:
                continue
            d = mahalanobis_for_window(
                ref[list(V3_FEATURE_COLUMNS)].to_numpy(),
                test[list(V3_FEATURE_COLUMNS)].to_numpy(),
            )
            if not np.isnan(d):
                maha_per_sym.append(d)
        maha = float(np.mean(maha_per_sym)) if maha_per_sym else np.nan

        # --- secondary separators: symbol vol/trend regime at month START (causal) ---
        # Use the last feature bar STRICTLY before the month start, per symbol, averaged.
        atr_vals, hurst_vals, rvol_vals = [], [], []
        for s in SYMBOLS:
            df = feats[s]
            prior = df[df["open_time"] < ms_start]
            if len(prior) == 0:
                continue
            last = prior.iloc[-1]
            if np.isfinite(last["atr_pct_rank_200"]):
                atr_vals.append(float(last["atr_pct_rank_200"]))
            if np.isfinite(last["hurst_100"]):
                hurst_vals.append(float(last["hurst_100"]))
            if np.isfinite(last["range_realized_vol_50"]):
                rvol_vals.append(float(last["range_realized_vol_50"]))

        # --- BTC regime at month START (causal) — primitive-9 reference signals ---
        btc_prior = btc[btc["open_time"] < ms_start]
        btc_dd = float(btc_prior["btc_dd_30d"].iloc[-1]) if len(btc_prior) else np.nan
        btc_vz = float(btc_prior["btc_vol_z_30d"].iloc[-1]) if len(btc_prior) else np.nan

        rows.append(
            {
                "month": month,
                "is_loss": bool(m["is_loss"]),
                "weighted_pnl": float(m["weighted_pnl"]),
                "win_rate": float(m["win_rate"]),
                "n_trades": int(m["n_trades"]),
                "maha_ood": maha,
                "atr_pct_rank_200": float(np.mean(atr_vals)) if atr_vals else np.nan,
                "hurst_100": float(np.mean(hurst_vals)) if hurst_vals else np.nan,
                "range_realized_vol_50": float(np.mean(rvol_vals)) if rvol_vals else np.nan,
                "btc_dd_30d": btc_dd,
                "btc_vol_z_30d": btc_vz,
            }
        )

    sep = pd.DataFrame(rows)
    sep.to_csv(f"{OUT_DIR}/T2_loss_month_separators.csv", index=False)

    # ------------------------------------------------------------------
    # Separation power: for each candidate, mean(loss) vs mean(profit),
    # rank-biserial / AUC (does the candidate rank loss months high?),
    # and Mann-Whitney-style separation.
    # ------------------------------------------------------------------
    candidates = [
        "maha_ood",
        "atr_pct_rank_200",
        "hurst_100",
        "range_realized_vol_50",
        "btc_dd_30d",
        "btc_vol_z_30d",
    ]
    loss_mask = sep["is_loss"].to_numpy()
    print("=" * 86)
    print("iter-v3/106 EDA 2 — DOES A REGIME SEPARATOR CLEANLY SPLIT THE IS LOSS MONTHS?")
    print("=" * 86)
    print(f"loss months = {loss_mask.sum()}   profit months = {(~loss_mask).sum()}")
    print()
    print(f"{'candidate':<24} {'mean(loss)':>12} {'mean(profit)':>13} {'AUC':>8} {'sep':>8}")
    print("-" * 70)
    sep_rows = []
    for c in candidates:
        v = sep[c].to_numpy(dtype=float)
        ok = np.isfinite(v)
        vl = v[ok & loss_mask]
        vp = v[ok & ~loss_mask]
        if len(vl) == 0 or len(vp) == 0:
            continue
        # AUC = P(loss month ranks higher than profit month) via pairwise wins.
        wins = sum((a > b) + 0.5 * (a == b) for a in vl for b in vp)
        auc = wins / (len(vl) * len(vp))
        # Standardized separation: (mean_loss - mean_profit) / pooled std.
        pooled = np.sqrt((vl.var(ddof=1) + vp.var(ddof=1)) / 2) if len(vl) > 1 and len(vp) > 1 else np.nan
        sepd = (vl.mean() - vp.mean()) / pooled if pooled and pooled > 0 else np.nan
        print(f"{c:<24} {vl.mean():>12.4f} {vp.mean():>13.4f} {auc:>8.3f} {sepd:>8.3f}")
        sep_rows.append(
            {
                "candidate": c,
                "mean_loss": vl.mean(),
                "mean_profit": vp.mean(),
                "auc_loss_ranks_high": auc,
                "cohens_d_separation": sepd,
                "n_loss": len(vl),
                "n_profit": len(vp),
            }
        )
    pd.DataFrame(sep_rows).to_csv(f"{OUT_DIR}/T3_separation_power.csv", index=False)
    print()
    print("AUC reading: 0.50 = no separation; >0.70 = the candidate ranks loss months")
    print("high (a usable 'unseen-regime' detector); <0.30 = ranks them low (inverse).")
    print()

    # Print the per-month maha + win_rate so the loss/profit structure is visible.
    print("--- per-month: maha_ood vs outcome (sorted by maha_ood desc) ---")
    show = sep.sort_values("maha_ood", ascending=False)[
        ["month", "is_loss", "weighted_pnl", "win_rate", "maha_ood", "atr_pct_rank_200", "hurst_100"]
    ]
    print(show.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print()
    print(f"Wrote {OUT_DIR}/T2_loss_month_separators.csv  ({len(sep)} rows)")
    print(f"Wrote {OUT_DIR}/T3_separation_power.csv  ({len(sep_rows)} rows)")


if __name__ == "__main__":
    main()
