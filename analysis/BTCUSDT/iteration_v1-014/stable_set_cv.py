"""IS-ONLY stationarity gate + redundancy clustering + purged-CV directional proxy — iter-v1/014 (BTCUSDT).

Follows subperiod_ic_stability.py. That screen surfaced the cross-sub-period IC stability of 182 candidate
indicators. This script:

  STAGE A  STATIONARITY GATE. The top-stability candidates include vol_ad / vol_vwap / vol_obv which are
           NON-stationary LEVEL series (ADF p>0.05). Their apparent IC "stability" is a spurious-regression
           artifact (they trend with price -> Spearman IC vs forward return tracks the price trend, not a
           predictive relationship). DROP all ADF-nonstationary candidates before selection. This is the
           econometric guardrail that separates a genuine cross-regime relationship from a level-trend.

  STAGE B  REDUNDANCY CLUSTER. On the surviving stationary stable candidates (frac_same_sign >= 0.727 AND
           ADF-stationary), build the IS Spearman |corr| matrix and hierarchically cluster (correlation
           distance). Keep ONE representative per cluster (the highest stability_score) to avoid the
           redundant-realized-vol-estimator trap (the iter-009 prune found garman/parkinson/natr are
           ~0.92-0.99 collinear).

  STAGE C  PURGED-CV DIRECTIONAL PROXY. The decisive test. Build a STABILITY-SELECTED set from the cluster
           reps and compare it head-to-head against the current 19-col set on the SAME purged walk-forward
           let-run directional proxy used in iter-011 — but the headline metric is CROSS-SUB-PERIOD
           STABILITY of the full (both-side) model book: frac_pos sub-periods, dispersion, worst, and the
           MOST-RECENT sub-period sign (the IS slice nearest OOS — the iter-011 OOS-fragility fingerprint).
           If the stability-selected set raises frac_pos / lowers dispersion / fixes the recent-sub-period
           sign vs the 19-col set, it is the IS-visible signature of better OOS generalization.

  We test the stable set at BOTH N=9 (the campaign direction) and N=21 (longer hold) since the user allows
  pairing short-window features with an expanded label timeout.

OOS-VIGILANCE (HARD): strict `open_time < OOS_CUTOFF_MS` filter + leak-guard assert BEFORE any forward
quantity; purged walk-forward (embargo >= label horizon); forward return + let-run trade on the IS slice
only (tail NaN-mask). Nothing fit/selected against OOS. `src/`, the runner, OOS UNTOUCHED.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-014/stable_set_cv.py
"""

from __future__ import annotations

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from scipy.stats import spearmanr
from statsmodels.tsa.stattools import adfuller

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
ATR_COLUMN = "vol_natr_21"
FEE_PCT = 0.1
ATR_SL = 1.45
CANDLES_PER_DAY = 3.0
CANDLES_PER_YEAR = 365.25 * CANDLES_PER_DAY
SUBPERIOD_DAYS = 182.5
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-014"

ITER009_FEATURES: tuple[str, ...] = (
    "trend_adx_7", "vol_garman_klass_10", "vol_atr_5", "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_5", "vol_mfi_7", "mom_rsi_9", "stat_autocorr_lag1",
    "mr_pct_from_high_5", "vol_cmf_10", "ent_shannon_10", "trend_adx_14",
    "trend_supertrend_14_3", "btc_funding_spread_30_90", "funding_rate_zscore_30",
    "stat_autocorr_lag5", "vol_range_spike_72", "mr_rsi_extreme_14", "stat_kurtosis_20",
)

BASE_PARAMS = dict(
    n_estimators=300, max_depth=4, num_leaves=15, learning_rate=0.03, min_child_samples=80,
    subsample=0.8, colsample_bytree=0.8, reg_alpha=0.5, reg_lambda=0.5, n_jobs=4, verbose=-1,
)


def fwd_log_return(close: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        if close[i] > 0 and close[i + n] > 0:
            out[i] = np.log(close[i + n] / close[i])
    return out


def letrun(high, low, close, atr, direction, atr_sl, timeout_c) -> np.ndarray:
    n = len(close)
    out = np.full(n, np.nan)
    for i in range(n):
        d = direction[i]
        if not np.isfinite(d) or d == 0 or close[i] == 0:
            continue
        entry = close[i]
        a = atr[i] if np.isfinite(atr[i]) else entry * 0.02
        end = min(i + timeout_c, n - 1)
        if end <= i:
            continue
        if d > 0:
            sl = entry - a * atr_sl
            ex = close[end]
            for j in range(i + 1, end + 1):
                if low[j] <= sl:
                    ex = sl
                    break
                ex = close[j]
            raw = (ex - entry) / entry * 100.0
        else:
            sl = entry + a * atr_sl
            ex = close[end]
            for j in range(i + 1, end + 1):
                if high[j] >= sl:
                    ex = sl
                    break
                ex = close[j]
            raw = (entry - ex) / entry * 100.0
        out[i] = raw - FEE_PCT
    return out


def ann_sharpe(r: np.ndarray, n_total: int, min_n: int = 12) -> tuple[float, float, int]:
    r = r[np.isfinite(r)]
    if len(r) < min_n:
        return np.nan, np.nan, len(r)
    mean, std = float(np.mean(r)), float(np.std(r, ddof=1))
    if std <= 0:
        return np.nan, float(np.mean(r > 0)), len(r)
    sann = (mean / std) * np.sqrt(len(r) / n_total * CANDLES_PER_YEAR)
    return sann, float(np.mean(r > 0)), len(r)


def walk_forward_predict(X, y, ot_days, valid, params, seed, n_label,
                         step_days=30.0, min_train_days=365.0):
    embargo_days = (n_label + 3) / CANDLES_PER_DAY
    t0, t_end = ot_days.min(), ot_days.max()
    test_start = t0 + min_train_days + embargo_days
    preds_all, idx_all = [], []
    while test_start < t_end:
        test_end = test_start + step_days
        train_cutoff = test_start - embargo_days
        train_mask = valid & (ot_days < train_cutoff) & (ot_days >= t0)
        test_mask = valid & (ot_days >= test_start) & (ot_days < test_end)
        if int(train_mask.sum()) >= 200 and int(test_mask.sum()) > 0:
            m = lgb.LGBMRegressor(random_state=seed, **params)
            m.fit(X[train_mask], y[train_mask])
            ti = np.where(test_mask)[0]
            preds_all.append(m.predict(X[test_mask]))
            idx_all.append(ti)
        test_start = test_end
    if not idx_all:
        return np.array([]), np.array([], dtype=int)
    return np.concatenate(preds_all), np.concatenate(idx_all)


def subperiod_stats(model_dir, oof, modelbook, ot_days, n_total):
    t0 = ot_days[oof].min()
    t1 = ot_days[oof].max()
    rows, edge, k = [], t0, 0
    while edge < t1:
        hi = edge + SUBPERIOD_DAYS
        win = oof & (ot_days >= edge) & (ot_days < hi)
        full_mask = win & np.isfinite(modelbook)
        full_s, _, full_n = ann_sharpe(modelbook[full_mask], n_total)
        rows.append(dict(period=f"P{k}",
                         start=str(pd.to_datetime(edge * 86400_000, unit="ms").date()),
                         full_n=full_n,
                         full_sharpe=round(full_s, 3) if np.isfinite(full_s) else np.nan))
        edge = hi
        k += 1
    return rows


def stability(rows, key="full_sharpe"):
    vals = np.array([r[key] for r in rows if np.isfinite(r[key])])
    if len(vals) == 0:
        return dict(n=0, frac_pos=np.nan, mean=np.nan, disp=np.nan, worst=np.nan, recent=np.nan)
    recent = next((r[key] for r in reversed(rows) if np.isfinite(r[key])), np.nan)
    return dict(n=len(vals), frac_pos=round(float(np.mean(vals > 0)), 3),
                mean=round(float(np.mean(vals)), 3),
                disp=round(float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0, 3),
                worst=round(float(np.min(vals)), 3),
                recent=round(float(recent), 3) if np.isfinite(recent) else np.nan)


def evaluate_set(name, feats, df, close, high, low, atr, ot_days, n_is, n_label, seed=42):
    X = df[feats].to_numpy(float)
    y = fwd_log_return(close, n_label)
    valid = np.isfinite(y)
    preds, idx = walk_forward_predict(X, y, ot_days, valid, BASE_PARAMS, seed, n_label)
    n = len(close)
    d = np.zeros(n)
    oof = np.zeros(n, dtype=bool)
    if len(idx):
        d[idx] = np.sign(preds)
        oof[idx] = True
    modelbook = letrun(high, low, close, atr, d, ATR_SL, n_label)
    full_mask = oof & np.isfinite(modelbook)
    full_s, full_wr, full_n = ann_sharpe(modelbook[full_mask], n_is)
    sp = subperiod_stats(d, oof, modelbook, ot_days, n_is)
    st = stability(sp)
    return dict(set=name, n_feats=len(feats), n_label=n_label, full_n=full_n,
                full_sharpe=round(full_s, 3), full_wr=round(full_wr, 3),
                sp_n=st["n"], sp_frac_pos=st["frac_pos"], sp_mean=st["mean"],
                sp_dispersion=st["disp"], sp_worst=st["worst"], sp_recent=st["recent"]), sp


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df_full = pd.read_parquet(PARQUET)
    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"
    n_is = len(df)
    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    atr = close * df[ATR_COLUMN].to_numpy(float) / 100.0
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0

    ic_tbl = pd.read_csv(OUTDIR / "subperiod_ic_stability.csv")

    # ---------- STAGE A: stationarity gate on stability candidates ----------
    print("=" * 110)
    print("STAGE A — STATIONARITY GATE (ADF) on frac_same_sign>=0.727 candidates")
    print("=" * 110)
    cand = ic_tbl[ic_tbl["frac_same_sign"] >= 0.727].copy()
    adf_p = {}
    for c in cand["feature"]:
        x = df[c].to_numpy(float)
        x = x[np.isfinite(x)]
        try:
            adf_p[c] = float(adfuller(x, maxlag=20, autolag=None)[1])
        except Exception:
            adf_p[c] = np.nan
    cand["adf_p"] = cand["feature"].map(adf_p)
    cand["stationary"] = cand["adf_p"] < 0.05
    dropped_nonstat = cand[~cand["stationary"]]["feature"].tolist()
    survivors = cand[cand["stationary"]].sort_values("stability_score", ascending=False)
    print(f"  candidates with frac_same_sign>=0.727: {len(cand)}")
    print(f"  DROPPED (ADF-nonstationary, spurious-IC level series): {dropped_nonstat}")
    print(f"  survivors (stationary + stable): {len(survivors)}")
    print(f"  {'feature':28s} {'in19':>5s} {'ic_full':>8s} {'frac_sign':>9s} {'mean|IC|':>9s} "
          f"{'disp':>7s} {'adf_p':>7s} {'stab':>8s}")
    for _, r in survivors.iterrows():
        print(f"  {r['feature']:28s} {str(r['in_19col']):>5s} {r['ic_full']:+8.4f} "
              f"{r['frac_same_sign']:9.3f} {r['mean_abs_ic']:9.4f} {r['ic_dispersion']:7.4f} "
              f"{r['adf_p']:7.4f} {r['stability_score']:8.5f}")
    survivors.to_csv(OUTDIR / "stationary_stable_survivors.csv", index=False)

    # ---------- STAGE B: redundancy cluster on survivors ----------
    print("\n" + "=" * 110)
    print("STAGE B — REDUNDANCY CLUSTER (Spearman |corr|, distance=1-|corr|, avg-link, threshold 0.40)")
    print("=" * 110)
    surv_feats = survivors["feature"].tolist()
    M = df[surv_feats].to_numpy(float)
    k = len(surv_feats)
    corr = np.eye(k)
    for i in range(k):
        for j in range(i + 1, k):
            xi, xj = M[:, i], M[:, j]
            mm = np.isfinite(xi) & np.isfinite(xj)
            if mm.sum() > 50 and np.std(xi[mm]) > 0 and np.std(xj[mm]) > 0:
                c, _ = spearmanr(xi[mm], xj[mm])
                corr[i, j] = corr[j, i] = c
    abscorr = np.abs(corr)
    dist = 1.0 - abscorr
    np.fill_diagonal(dist, 0.0)
    dist = (dist + dist.T) / 2.0
    Z = linkage(squareform(dist, checks=False), method="average")
    clusters = fcluster(Z, t=0.40, criterion="distance")  # |corr|>0.60 within cluster
    score_map = dict(zip(survivors["feature"], survivors["stability_score"]))
    cluster_reps = {}
    cluster_members = {}
    for feat, cl in zip(surv_feats, clusters):
        cluster_members.setdefault(cl, []).append(feat)
        if cl not in cluster_reps or score_map[feat] > score_map[cluster_reps[cl]]:
            cluster_reps[cl] = feat
    print(f"  {len(surv_feats)} survivors -> {len(cluster_members)} clusters (|corr|>0.60 merged):")
    for cl in sorted(cluster_members):
        members = sorted(cluster_members[cl], key=lambda f: -score_map[f])
        rep = cluster_reps[cl]
        print(f"   C{cl:02d} rep={rep:28s} members={members}")
    reps_ranked = sorted(cluster_reps.values(), key=lambda f: -score_map[f])
    pd.DataFrame([dict(cluster=cl, rep=cluster_reps[cl],
                       members="|".join(sorted(cluster_members[cl], key=lambda f: -score_map[f])))
                  for cl in sorted(cluster_members)]).to_csv(
        OUTDIR / "stable_clusters.csv", index=False)

    # ---------- build stability-selected set ----------
    # take cluster reps (one per redundancy cluster), capped at ~16 by stability score
    stable_set = reps_ranked[:16]
    print(f"\n  STABILITY-SELECTED SET ({len(stable_set)} cluster reps, ranked by stability):")
    print(f"   {stable_set}")
    pd.Series(stable_set, name="feature").to_csv(OUTDIR / "stability_selected_set.csv", index=False)

    # ---------- STAGE C: purged-CV directional proxy, stable set vs 19-col ----------
    print("\n" + "=" * 110)
    print("STAGE C — PURGED-CV DIRECTIONAL LET-RUN PROXY (full both-side book; seed 42)")
    print("  headline = CROSS-SUB-PERIOD STABILITY (frac_pos / dispersion / worst / MOST-RECENT sign)")
    print("=" * 110)
    sets = {
        "iter009_19col": list(ITER009_FEATURES),
        "stable_selected": stable_set,
    }
    all_rows = []
    detail_dump = {}
    for n_label in (9, 21):
        print(f"\n  --- N={n_label} ({int(n_label/3)}d forward) ---")
        print(f"  {'set':18s} {'nf':>3s} {'full_S':>8s} {'WR':>6s} {'n':>5s} "
              f"{'sp_n':>4s} {'frac_pos':>8s} {'disp':>6s} {'worst':>7s} {'recent':>7s}")
        for name, feats in sets.items():
            feats = [c for c in feats if c in df.columns]
            row, sp = evaluate_set(name, feats, df, close, high, low, atr, ot_days, n_is, n_label)
            all_rows.append(row)
            detail_dump[f"{name}_N{n_label}"] = sp
            print(f"  {name:18s} {row['n_feats']:>3d} {row['full_sharpe']:+8.3f} "
                  f"{row['full_wr']:6.3f} {row['full_n']:>5d} {row['sp_n']:>4d} "
                  f"{row['sp_frac_pos']:8.3f} {row['sp_dispersion']:6.3f} "
                  f"{row['sp_worst']:+7.3f} {row['sp_recent']:+7.3f}")
    pd.DataFrame(all_rows).to_csv(OUTDIR / "stable_vs_19col_cv.csv", index=False)

    # per-sub-period detail for the two N=9 sets (the campaign direction)
    print("\n  PER-SUB-PERIOD full-book Sharpe (N=9) — the OOS-fragility fingerprint is the LAST row:")
    p19 = {r["start"]: r["full_sharpe"] for r in detail_dump["iter009_19col_N9"]}
    pst = {r["start"]: r["full_sharpe"] for r in detail_dump["stable_selected_N9"]}
    starts = sorted(set(p19) | set(pst))
    print(f"   {'sub-period':12s} {'19col_S':>9s} {'stable_S':>9s}")
    for s in starts:
        a = p19.get(s, np.nan)
        b = pst.get(s, np.nan)
        astr = f"{a:+.3f}" if np.isfinite(a) else "   nan"
        bstr = f"{b:+.3f}" if np.isfinite(b) else "   nan"
        print(f"   {s:12s} {astr:>9s} {bstr:>9s}")

    print(f"\nWrote: {OUTDIR/'stationary_stable_survivors.csv'}, {OUTDIR/'stable_clusters.csv'}, "
          f"{OUTDIR/'stability_selected_set.csv'}, {OUTDIR/'stable_vs_19col_cv.csv'}")


if __name__ == "__main__":
    main()
