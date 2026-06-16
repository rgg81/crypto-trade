"""IS-ONLY orthogonal (non-OHLCV) feature scan for BTCUSDT iter-v1/006.

Feature Engineer Phase 4 (4a/4b/4c) analysis. Screens the candidate NON-OHLCV
feature families against the frozen 41-col OHLCV prune (V1_BTC_PRUNED_ITER002),
on the IS window ONLY (open_time strictly before OOS_CUTOFF_MS = 2025-03-24).

Three diagnostics per candidate:
  1. IS Information Coefficient (Spearman + Pearson) vs forward log-returns at the
     1-bar horizon (matches run_baseline_v1._compute_forward_returns) AND a 3-bar
     horizon. Plus quintile-bucket forward-return monotonicity.
  2. Redundancy vs the 41-col prune: max |Pearson corr| against every prune column.
  3. Marginal cluster (gain) importance: a small IS-only LightGBM fit on
     [41-col prune + candidate] predicting the 1-bar forward return; the candidate's
     gain-importance RANK among 42 is reported (bottom third => INERT).

The script is re-runnable and asserts the IS-only cutoff. It reads ONLY the BTC
8h parquet. It NEVER touches OOS rows. No production code is modified.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-006/feature_ortho_scan.py
"""

from __future__ import annotations

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

# --------------------------------------------------------------------------- #
# Sacred constants — IS-only, single-symbol, no look-ahead.
# --------------------------------------------------------------------------- #
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC (config.OOS_CUTOFF_MS)
SYMBOL = "BTCUSDT"
INTERVAL = "8h"
PARQUET = Path("data/features") / f"{SYMBOL}_{INTERVAL}_features.parquet"

# Frozen 41-col OHLCV prune (run_baseline_v1.V1_BTC_PRUNED_ITER002 ~line 285).
V1_BTC_PRUNED_ITER002: tuple[str, ...] = (
    "cal_dow_norm",
    "mom_macd_hist_12_26_9",
    "mom_macd_hist_5_13_3",
    "mr_bb_pctb_10",
    "mr_pct_from_high_10",
    "mr_pct_from_high_100",
    "mr_pct_from_low_100",
    "mr_pct_from_low_20",
    "mr_rsi_extreme_14",
    "stat_autocorr_lag1",
    "stat_autocorr_lag10",
    "stat_autocorr_lag5",
    "stat_kurtosis_10",
    "stat_kurtosis_30",
    "stat_kurtosis_50",
    "stat_skew_10",
    "stat_skew_20",
    "stat_skew_50",
    "trend_adx_14",
    "trend_adx_7",
    "trend_aroon_down_25",
    "trend_aroon_down_50",
    "trend_aroon_osc_14",
    "trend_aroon_osc_25",
    "trend_aroon_osc_50",
    "trend_plus_di_21",
    "trend_psar_af",
    "trend_sma_50",
    "trend_supertrend_10_2",
    "trend_supertrend_7_3",
    "vol_ad",
    "vol_cmf_20",
    "vol_garman_klass_50",
    "vol_hist_10",
    "vol_hist_5",
    "vol_obv",
    "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_10",
    "vol_taker_buy_ratio_sma_50",
    "vol_volume_pctchg_15",
    "vol_volume_pctchg_20",
)

# Candidate NON-OHLCV families (task spec). btc_funding_spread_30_90 is the
# iter-005 NEGATIVE — kept as a redundancy reference, excluded from recommendation.
CANDIDATES: tuple[str, ...] = (
    "funding_rate_zscore_30",
    "funding_rate_zscore_90",
    "btc_funding_rate_8h_impulse",
    "btc_funding_spread_30_90",  # iter-005 NEGATIVE (reference)
    "oi_delta_30_z90",
    "btc_oi_delta_5_z30",
    "oi_price_divergence_30",
    "basis_zscore_30",  # retired iter-040 in pooled pipeline (3x INERT) — re-eval
    "long_short_zscore_30",
    "dot_vs_btc_ret_ratio_30",  # cross-asset
    "eth_vs_btc_ret_ratio_30",  # cross-asset
    "ltc_vs_btc_ret_ratio_30",  # cross-asset
)

ALREADY_TESTED_NEGATIVE = {"btc_funding_spread_30_90"}

RANDOM_SEED = 42


def _forward_log_return(close: pd.Series, horizon: int) -> np.ndarray:
    """Past-only-safe forward log-return: log(close[t+h]/close[t]). NaN at tail."""
    return np.log(close.shift(-horizon) / close).to_numpy()


def main() -> None:
    assert PARQUET.exists(), f"parquet not found: {PARQUET}"
    df_full = pd.read_parquet(PARQUET)

    # IS-only filter — strict less-than the cutoff. This is the ONLY data used.
    assert "open_time" in df_full.columns, "open_time column missing"
    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"
    n_is = len(df)

    # Forward returns (IS rows aligned). 1-bar matches the runner; 3-bar = ~1 day.
    fwd1 = _forward_log_return(df["close"], 1)
    fwd3 = _forward_log_return(df["close"], 3)

    print("=" * 78)
    print(f"IS-ONLY orthogonal feature scan — {SYMBOL} {INTERVAL}")
    print(f"IS rows (open_time < {OOS_CUTOFF_MS} = 2025-03-24): {n_is}")
    print(f"IS window: {pd.to_datetime(df['open_time'].min(), unit='ms')} .. "
          f"{pd.to_datetime(df['open_time'].max(), unit='ms')}")
    print("=" * 78)

    # ------------------------------------------------------------------- #
    # 1. IS IC (Spearman + Pearson) vs fwd1 and fwd3 + quintile monotonicity
    # ------------------------------------------------------------------- #
    ic_rows = []
    for c in CANDIDATES:
        if c not in df.columns:
            ic_rows.append({"feature": c, "status": "ABSENT"})
            continue
        s = df[c]
        nn = int(s.notna().sum())
        cov = 100.0 * nn / n_is
        if nn < 200:  # not enough IS coverage to evaluate
            ic_rows.append({
                "feature": c, "status": f"NO-IS-COVERAGE ({nn} non-null, {cov:.1f}%)",
                "is_nonnull": nn, "cov_pct": cov,
            })
            continue

        # Align feature with each forward-return horizon on jointly-valid rows.
        def _ic(feat: pd.Series, fwd: np.ndarray):
            mask = feat.notna().to_numpy() & np.isfinite(fwd)
            x = feat.to_numpy()[mask]
            y = fwd[mask]
            if len(x) < 100 or np.std(x) == 0:
                return np.nan, np.nan, len(x)
            sp = spearmanr(x, y).correlation
            pe = pearsonr(x, y)[0]
            return sp, pe, len(x)

        sp1, pe1, n1 = _ic(s, fwd1)
        sp3, pe3, n3 = _ic(s, fwd3)

        # Quintile-bucket forward (1-bar) return monotonicity.
        mask = s.notna().to_numpy() & np.isfinite(fwd1)
        x = s.to_numpy()[mask]
        y = fwd1[mask]
        try:
            q = pd.qcut(pd.Series(x), 5, labels=False, duplicates="drop")
            bucket_means = pd.Series(y).groupby(q.to_numpy()).mean()
            mono_spread = float(bucket_means.iloc[-1] - bucket_means.iloc[0])
            # +1 strictly increasing, -1 strictly decreasing, 0 otherwise
            diffs = np.diff(bucket_means.to_numpy())
            if np.all(diffs > 0):
                mono = "incr"
            elif np.all(diffs < 0):
                mono = "decr"
            else:
                mono = "mixed"
        except Exception:
            mono_spread, mono = np.nan, "NA"

        ic_rows.append({
            "feature": c,
            "status": "TESTED-NEG-REF" if c in ALREADY_TESTED_NEGATIVE else "ok",
            "is_nonnull": nn, "cov_pct": cov,
            "sp_ic_1bar": sp1, "pe_ic_1bar": pe1,
            "sp_ic_3bar": sp3, "pe_ic_3bar": pe3,
            "q_mono": mono, "q_top_minus_bot_fwd1": mono_spread,
        })

    ic_df = pd.DataFrame(ic_rows)

    print("\n[1] IS INFORMATION COEFFICIENT (Spearman / Pearson) + quintile monotonicity")
    print("-" * 78)
    show = ic_df[ic_df["status"].isin(["ok", "TESTED-NEG-REF"])].copy()
    for _, r in show.iterrows():
        print(f"{r['feature']:30s} cov={r['cov_pct']:5.1f}%  "
              f"sp1={r['sp_ic_1bar']:+.4f} pe1={r['pe_ic_1bar']:+.4f}  "
              f"sp3={r['sp_ic_3bar']:+.4f} pe3={r['pe_ic_3bar']:+.4f}  "
              f"qmono={r['q_mono']:5s} qspread={r['q_top_minus_bot_fwd1']:+.5f}"
              + ("  [iter-005 NEG ref]" if r['status'] == "TESTED-NEG-REF" else ""))
    dead = ic_df[~ic_df["status"].isin(["ok", "TESTED-NEG-REF"])]
    for _, r in dead.iterrows():
        print(f"{r['feature']:30s} ** {r['status']} **")

    # ------------------------------------------------------------------- #
    # 1b. CONTEXT: univariate IS-IC of the 41 prune cols the model ALREADY
    #     uses. If the candidate ICs sit at/above this band, the orthogonal
    #     family is at least as strong as the price base (decisive for A vs C).
    # ------------------------------------------------------------------- #
    prune_present = [c for c in V1_BTC_PRUNED_ITER002 if c in df.columns]
    assert len(prune_present) == 41, f"expected 41 prune cols, got {len(prune_present)}"
    prune_ics = []
    for pc in prune_present:
        s = df[pc]
        mask = s.notna().to_numpy() & np.isfinite(fwd1)
        if mask.sum() < 200 or np.std(s.to_numpy()[mask]) == 0:
            continue
        prune_ics.append(abs(spearmanr(s.to_numpy()[mask], fwd1[mask]).correlation))
    prune_ics = np.array(prune_ics)
    print("\n[1b] CONTEXT — 41-col PRUNE univariate |IS-IC| (the price signal in use)")
    print("-" * 78)
    print(f"     max={prune_ics.max():.4f}  mean={prune_ics.mean():.4f}  "
          f"median={np.median(prune_ics):.4f}  "
          f"(#cols |IC|>0.04: {int((prune_ics > 0.04).sum())}/{len(prune_ics)})")
    print("     => the best candidate ICs above this band are STRONGER than any price col.")

    # ------------------------------------------------------------------- #
    # 2. Redundancy vs the 41-col prune (max |Pearson| across prune cols)
    # ------------------------------------------------------------------- #
    prune_mat = df[prune_present]

    print("\n[2] REDUNDANCY vs 41-col prune (max |Pearson corr|; want LOW = orthogonal)")
    print("-" * 78)
    redund_rows = []
    for c in CANDIDATES:
        if c not in df.columns or df[c].notna().sum() < 200:
            redund_rows.append({"feature": c, "max_abs_corr": np.nan, "argmax_col": "NA"})
            continue
        feat = df[c]
        corrs = {}
        for pc in prune_present:
            both = feat.notna() & prune_mat[pc].notna()
            if both.sum() < 100:
                continue
            x = feat[both].to_numpy()
            yy = prune_mat[pc][both].to_numpy()
            if np.std(x) == 0 or np.std(yy) == 0:
                continue
            corrs[pc] = abs(pearsonr(x, yy)[0])
        if corrs:
            argmax_col = max(corrs, key=corrs.get)
            mac = corrs[argmax_col]
        else:
            argmax_col, mac = "NA", np.nan
        redund_rows.append({"feature": c, "max_abs_corr": mac, "argmax_col": argmax_col})
        print(f"{c:30s} max|corr|={mac:.4f}  (vs {argmax_col})"
              + ("  [iter-005 NEG ref]" if c in ALREADY_TESTED_NEGATIVE else ""))
    redund_df = pd.DataFrame(redund_rows)

    # Mutual correlation among the *evaluable* candidates (for cluster decision).
    eval_cands = [c for c in CANDIDATES
                  if c in df.columns and df[c].notna().sum() >= 200
                  and c not in ALREADY_TESTED_NEGATIVE]
    print("\n[2b] MUTUAL |Pearson| among evaluable candidates (cluster orthogonality)")
    print("-" * 78)
    mut = pd.DataFrame(index=eval_cands, columns=eval_cands, dtype=float)
    for a in eval_cands:
        for b in eval_cands:
            both = df[a].notna() & df[b].notna()
            if both.sum() < 100:
                mut.loc[a, b] = np.nan
                continue
            mut.loc[a, b] = abs(pearsonr(df[a][both], df[b][both])[0])
    with pd.option_context("display.width", 160, "display.max_columns", 20):
        print(mut.round(3).to_string())

    # ------------------------------------------------------------------- #
    # 3. Marginal cluster (gain) importance: LightGBM on [41 prune + candidate]
    # ------------------------------------------------------------------- #
    print("\n[3] MARGINAL CLUSTER IMPORTANCE — gain rank of candidate among 42")
    print("-" * 78)
    print("    (small IS-only LGBM, depth 4, n_estimators=200, seed=42, 1-bar fwd label)")
    imp_rows = []
    for c in CANDIDATES:
        if c not in df.columns or df[c].notna().sum() < 200:
            imp_rows.append({"feature": c, "gain_rank": np.nan, "gain_pct": np.nan,
                             "n_features": np.nan, "bottom_third": "NA"})
            continue
        feat_cols = prune_present + [c]
        # Rows with a finite 1-bar forward label. LightGBM tolerates NaN features.
        lbl_mask = np.isfinite(fwd1)
        X = df.loc[lbl_mask, feat_cols].to_numpy()
        y = fwd1[lbl_mask]
        model = lgb.LGBMRegressor(
            n_estimators=200,
            max_depth=4,
            num_leaves=15,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=RANDOM_SEED,
            n_jobs=2,
            verbose=-1,
        )
        model.fit(X, y)
        gains = model.booster_.feature_importance(importance_type="gain")
        gain_series = pd.Series(gains, index=feat_cols)
        total = gain_series.sum()
        gain_pct = 100.0 * gain_series[c] / total if total > 0 else 0.0
        # Rank 1 = highest gain.
        rank = int(gain_series.rank(ascending=False).loc[c])
        n_feat = len(feat_cols)
        bottom_third = "BOTTOM-THIRD (INERT)" if rank > (2 * n_feat / 3) else "ok"
        imp_rows.append({"feature": c, "gain_rank": rank, "gain_pct": gain_pct,
                         "n_features": n_feat, "bottom_third": bottom_third})
        print(f"{c:30s} rank={rank:2d}/{n_feat}  gain%={gain_pct:6.2f}  {bottom_third}"
              + ("  [iter-005 NEG ref]" if c in ALREADY_TESTED_NEGATIVE else ""))
    imp_df = pd.DataFrame(imp_rows)

    # ------------------------------------------------------------------- #
    # Combined ranked shortlist + verdicts
    # ------------------------------------------------------------------- #
    summary = ic_df.merge(redund_df, on="feature", how="left").merge(
        imp_df, on="feature", how="left")

    def _verdict(r):
        if r["feature"] in ALREADY_TESTED_NEGATIVE:
            return "EXCLUDED (iter-005 NEGATIVE)"
        if str(r.get("status", "")).startswith("ABSENT") \
                or str(r.get("status", "")).startswith("NO-IS-COVERAGE"):
            return "UNAVAILABLE (no IS coverage)"
        ic_abs = max(abs(r.get("sp_ic_1bar", np.nan)), abs(r.get("sp_ic_3bar", np.nan)))
        rank = r.get("gain_rank", np.nan)
        nfeat = r.get("n_features", np.nan)
        if pd.isna(rank):
            return "UNAVAILABLE"
        top_half = rank <= (nfeat / 2)
        ic_ok = ic_abs > 0.04
        if ic_ok and top_half:
            return "PASS (|IC|>0.04 AND top-half importance)"
        if ic_ok and not top_half:
            return "WEAK (IC ok, importance bottom-half)"
        if not ic_ok and top_half:
            return "WEAK (importance ok, IC<0.04)"
        return "FAIL (IC<0.04 AND importance bottom-half)"

    summary["verdict"] = summary.apply(_verdict, axis=1)

    out_cols = ["feature", "cov_pct", "sp_ic_1bar", "sp_ic_3bar",
                "q_mono", "max_abs_corr", "argmax_col",
                "gain_rank", "n_features", "gain_pct", "verdict"]
    out_cols = [c for c in out_cols if c in summary.columns]
    summary_out = summary[out_cols].copy()

    print("\n" + "=" * 78)
    print("COMBINED SHORTLIST (sorted: PASS first, then by |1-bar Spearman IC|)")
    print("=" * 78)
    summary_out["_absic"] = summary_out["sp_ic_1bar"].abs().fillna(-1)
    summary_out["_passorder"] = summary_out["verdict"].str.startswith("PASS").map(
        {True: 0, False: 1})
    summary_out = summary_out.sort_values(
        ["_passorder", "_absic"], ascending=[True, False]).drop(
        columns=["_absic", "_passorder"])
    with pd.option_context("display.width", 200, "display.max_columns", 30):
        print(summary_out.to_string(index=False))

    # ------------------------------------------------------------------- #
    # 4. ADF stationarity (informational, not blocking)
    # ------------------------------------------------------------------- #
    print("\n[4] ADF STATIONARITY (informational)")
    print("-" * 78)
    try:
        from statsmodels.tsa.stattools import adfuller  # noqa: PLC0415

        for c in eval_cands:
            s = df[c].dropna()
            stat, p = adfuller(s, autolag="AIC")[:2]
            tag = "STATIONARY" if p < 0.05 else "non-stationary"
            print(f"{c:30s} ADF={stat:8.3f} p={p:.4f} {tag}")
    except ImportError:
        print("  statsmodels not available — skipping ADF (informational only)")

    # ------------------------------------------------------------------- #
    # 5. Purged forward-chaining CV — MARGINAL out-of-fold model improvement.
    #    This is the decisive metric: univariate IC can mislead (iter-005
    #    funding-spread had IC but degraded IS inside the bagged specialist).
    #    Here we measure whether the candidate helps the MODEL out-of-fold.
    #    5 forward-chaining folds, embargo 3 bars, 1-bar fwd label, IS-only.
    # ------------------------------------------------------------------- #
    print("\n[5] PURGED FORWARD-CHAINING CV — marginal OOF lift (decisive metric)")
    print("-" * 78)
    print("    (prune-only baseline vs prune+candidate; dir_acc = signed-return")
    print("     directional accuracy out-of-fold; the metric that drives Sharpe)")
    idx = np.where(np.isfinite(fwd1))[0]
    n_cv = len(idx)
    folds = 5
    fold_size = n_cv // folds

    def _cv(extra: list[str]) -> tuple[float, float]:
        cols = prune_present + extra
        Xm = df.loc[idx, cols].to_numpy()
        ym = fwd1[idx]
        accs, r2s = [], []
        for k in range(1, folds):
            tr_end = k * fold_size
            te_start = tr_end + 3  # embargo 3 bars
            te_end = min((k + 1) * fold_size, n_cv)
            if te_start >= te_end:
                continue
            mdl = lgb.LGBMRegressor(
                n_estimators=200, max_depth=4, num_leaves=15, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8, random_state=RANDOM_SEED,
                n_jobs=2, verbose=-1)
            mdl.fit(Xm[:tr_end], ym[:tr_end])
            p = mdl.predict(Xm[te_start:te_end])
            yt = ym[te_start:te_end]
            accs.append(float(np.mean(np.sign(p) == np.sign(yt))))
            ss_res = float(np.sum((yt - p) ** 2))
            ss_tot = float(np.sum((yt - yt.mean()) ** 2))
            r2s.append(1 - ss_res / ss_tot if ss_tot > 0 else np.nan)
        return float(np.mean(accs)), float(np.nanmean(r2s))

    base_acc, base_r2 = _cv([])
    print(f"{'PRUNE-ONLY (41 cols)':30s} dir_acc={base_acc:.4f}  oof_R2={base_r2:+.5f}")
    cv_results = []
    singles = [c for c in eval_cands]
    for c in singles:
        a, r = _cv([c])
        cv_results.append({"combo": c, "dir_acc": a, "d_acc": a - base_acc,
                           "oof_r2": r, "d_r2": r - base_r2})
        print(f"+ {c:28s} dir_acc={a:.4f} (Δ{a - base_acc:+.4f})  "
              f"oof_R2={r:+.5f} (Δ{r - base_r2:+.5f})")
    # A couple of orthogonal cluster probes (low mutual-corr pairs).
    for combo in (["funding_rate_zscore_90", "oi_price_divergence_30"],
                  ["funding_rate_zscore_30", "funding_rate_zscore_90"]):
        if all(c in df.columns for c in combo):
            a, r = _cv(combo)
            label = "+".join(combo)
            cv_results.append({"combo": label, "dir_acc": a, "d_acc": a - base_acc,
                               "oof_r2": r, "d_r2": r - base_r2})
            print(f"+ {label:28s} dir_acc={a:.4f} (Δ{a - base_acc:+.4f})  "
                  f"oof_R2={r:+.5f} (Δ{r - base_r2:+.5f})")
    pd.DataFrame(cv_results).to_csv(
        Path("analysis") / SYMBOL / "iteration_v1-006" / "purged_cv_marginal.csv",
        index=False)

    out_csv = Path("analysis") / SYMBOL / "iteration_v1-006" / "feature_ortho_scan.csv"
    summary_out.to_csv(out_csv, index=False)
    mut.to_csv(Path("analysis") / SYMBOL / "iteration_v1-006" / "candidate_mutual_corr.csv")
    print(f"\nWrote: {out_csv}")
    print("Wrote: analysis/BTCUSDT/iteration_v1-006/candidate_mutual_corr.csv")
    print("Wrote: analysis/BTCUSDT/iteration_v1-006/purged_cv_marginal.csv")


if __name__ == "__main__":
    main()
