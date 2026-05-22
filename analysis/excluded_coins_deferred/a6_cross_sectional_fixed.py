"""iter-v3/101 — ANGLE 4 (re-run) — CROSS-SECTIONAL RANK-IC ON THE MAJORS, FIXED.

WHY THIS SCRIPT EXISTS
----------------------
a4_pooled_and_cross_sectional.py computed D1 (pooled CV-IC) and D2 (pooled
per-symbol transfer) correctly, but its D3/D4 cross-sectional blocks returned
0 bars — a code defect: the long panel was assembled via repeated
`.assign(symbol=s)` on already-symbol-tagged frames inside a comprehension,
and the per-bar `groupby("open_time")` then saw no bar with >= 6 symbols.

A standalone overlap check confirmed the data is fine: 3431 IS bars carry
>= 6 of the 10 majors and 2702 bars carry all 10 (timestamps align
byte-identically across symbols — BTC/ETH `open_time` overlap is 6989/6989).
So the cross-sectional angle IS testable; this script re-runs D3/D4 cleanly.

WHAT THIS MEASURES (the equity-quant relative-value playbook on the majors)
---------------------------------------------------------------------------
  F1  CROSS-SECTIONAL FEATURE rank-IC. At each 8h bar, across the majors
      present, rank-correlate each feature's cross-sectional rank with the
      cross-sectional forward-3-candle-return rank. Average over bars. A
      feature with mean XS-IC clearly above the thin floor + a high fraction
      of positive bars is a real relative-value signal.

  F2  CROSS-SECTIONAL MODEL rank-IC. Build a pooled-major LightGBM OOF score
      (purged 5-fold, frozen 14-feature stack, /059 label), then at each bar
      rank-correlate the cross-sectional model-score rank with the
      cross-sectional fwd-return rank. This is the direct EDA proxy for a
      cross-sectional long-short major book's per-bar signal — no backtest.

  F3  TOP-MINUS-BOTTOM forward return. At each bar, long the top-3 majors by
      the pooled-model score and short the bottom-3; record the equal-weight
      forward-3-candle return of that long-short basket. Mean, std, monthly
      Sharpe proxy. This is the closest IS-only read on whether a
      cross-sectional major book would have an edge.

This is EDA. No backtest, no brief, no src/ changes. IS-only.

NO-CHEATING
-----------
  - OOS_CUTOFF_MS = 1742774400000. Every row open_time < cutoff.
  - 24-month per-symbol burn-in.
  - The pooled-model OOF uses a purged 5-fold with the embargo scaled by
    n_symbols so no label window leaks across the test boundary.
  - Forward return is the TARGET only — never a feature.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import lightgbm as lgb
except ImportError:  # pragma: no cover
    print("lightgbm not importable", file=sys.stderr)
    raise

OOS_CUTOFF_MS = 1742774400000
TRAINING_MONTHS = 24
TIMEOUT_MIN = 10080
TP_MULT = 2.0
SL_MULT = 1.0
EMBARGO_CANDLES = 22
DATA_DIR = Path("data/features_v3")
OUT = Path("analysis/iteration_v3-101")

EXCLUDED_MAJORS = (
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "NEARUSDT",
)

V3_FEATURE_COLUMNS = (
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
    "regime_momentum_signed_5d",
)

LGB_PARAMS = dict(
    objective="binary",
    n_estimators=200,
    num_leaves=31,
    max_depth=5,
    learning_rate=0.05,
    min_child_samples=40,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    random_state=42,
    verbose=-1,
    n_jobs=2,
)


def triple_barrier_label(df: pd.DataFrame) -> np.ndarray:
    out = df.reset_index(drop=True)
    n = len(out)
    high = out["high"].to_numpy(dtype=np.float64)
    low = out["low"].to_numpy(dtype=np.float64)
    close = out["close"].to_numpy(dtype=np.float64)
    close_time = out["close_time"].to_numpy(dtype=np.int64)
    natr = out["natr_21_raw"].to_numpy(dtype=np.float64)
    timeout_ms = TIMEOUT_MIN * 60 * 1000
    labels = np.zeros(n, dtype=np.int64)
    for i in range(n):
        entry = close[i]
        if entry <= 0:
            continue
        atr = (natr[i] / 100.0) * entry if np.isfinite(natr[i]) else entry * 0.02
        long_tp = entry + atr * TP_MULT
        long_sl = entry - atr * SL_MULT
        short_tp = entry - atr * TP_MULT
        short_sl = entry + atr * SL_MULT
        deadline = close_time[i] + timeout_ms
        long_result = short_result = 0
        long_step = short_step = -1
        last_close = entry
        j = i + 1
        while j < n:
            if close_time[j] > deadline:
                if long_result == 0:
                    long_result, long_step = -2, j
                if short_result == 0:
                    short_result, short_step = -2, j
                break
            h, lo = high[j], low[j]
            last_close = close[j]
            if long_result == 0:
                if lo <= long_sl:
                    long_result, long_step = -1, j
                elif h >= long_tp:
                    long_result, long_step = 1, j
            if short_result == 0:
                if h >= short_sl:
                    short_result, short_step = -1, j
                elif lo <= short_tp:
                    short_result, short_step = 1, j
            if long_result != 0 and short_result != 0:
                break
            j += 1
        else:
            if long_result == 0:
                long_result = -2
            if short_result == 0:
                short_result = -2
        fwd_ret = (last_close - entry) / entry if entry != 0 else 0.0
        long_tp_hit = long_result == 1
        short_tp_hit = short_result == 1
        if long_tp_hit and not short_tp_hit:
            lab = 1
        elif short_tp_hit and not long_tp_hit:
            lab = -1
        elif long_tp_hit and short_tp_hit:
            lab = 1 if long_step <= short_step else -1
        else:
            lab = 1 if fwd_ret >= 0 else -1
        labels[i] = lab
    return labels


def load_symbol_is(symbol: str) -> pd.DataFrame | None:
    path = DATA_DIR / f"{symbol}_8h_features.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path).sort_values("open_time").reset_index(drop=True)
    first_ms = int(df["open_time"].min())
    burnin_end = first_ms + TRAINING_MONTHS * 30 * 24 * 60 * 60 * 1000
    df["tb_label"] = triple_barrier_label(df)
    close = df["close"].to_numpy(dtype=np.float64)
    fwd3 = np.full(len(df), np.nan)
    for i in range(len(df) - 3):
        if close[i] > 0:
            fwd3[i] = (close[i + 3] - close[i]) / close[i] * 100.0
    df["fwd_ret_3"] = fwd3
    is_mask = (df["open_time"] >= burnin_end) & (df["open_time"] < OOS_CUTOFF_MS)
    isd = df[is_mask].copy()
    isd["symbol"] = symbol
    isd["y"] = (isd["tb_label"] == 1).astype(int)
    keep = ["open_time", "symbol", "y", "tb_label", "fwd_ret_3", *V3_FEATURE_COLUMNS]
    return isd[keep].dropna(subset=list(V3_FEATURE_COLUMNS)).reset_index(drop=True)


def rank_ic(pred: np.ndarray, target: np.ndarray) -> float:
    mask = np.isfinite(pred) & np.isfinite(target)
    if mask.sum() < 4:
        return float("nan")
    c = pd.Series(pred[mask]).rank().corr(pd.Series(target[mask]).rank())
    return float(c) if pd.notna(c) else float("nan")


def purged_kfold_indices(n: int, k: int, embargo: int):
    fold_sizes = np.full(k, n // k, dtype=int)
    fold_sizes[: n % k] += 1
    current = 0
    bounds = []
    for fs in fold_sizes:
        bounds.append((current, current + fs))
        current += fs
    for lo, hi in bounds:
        test_idx = np.arange(lo, hi)
        train_mask = np.ones(n, dtype=bool)
        train_mask[max(0, lo - embargo) : min(n, hi + embargo)] = False
        yield np.where(train_mask)[0], test_idx


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/101 ANGLE 4 (re-run) — CROSS-SECTIONAL ON THE MAJORS — FIXED")
    print("=" * 78)

    frames = []
    for sym in EXCLUDED_MAJORS:
        d = load_symbol_is(sym)
        if d is None:
            print(f"  {sym}: parquet missing — skipped")
            continue
        frames.append(d)
        print(f"  {sym:10s}: {len(d):5d} IS rows")
    longm = pd.concat(frames, ignore_index=True)
    # only bars where >= 6 majors are present (so a cross-section exists)
    bar_counts = longm.groupby("open_time")["symbol"].nunique()
    valid_bars = bar_counts[bar_counts >= 6].index
    longx = longm[longm["open_time"].isin(valid_bars)].copy()
    print(f"\n  cross-sectional panel: {len(valid_bars)} bars with >= 6 majors, "
          f"{len(longx)} symbol-bar rows")

    # ---- F1: cross-sectional feature rank-IC ----
    print("\nF1 — CROSS-SECTIONAL feature rank-IC (per-bar feature rank vs "
          "per-bar fwd_ret_3 rank, averaged over bars):")
    f1_rows = []
    for feat in V3_FEATURE_COLUMNS:
        per_bar = []
        for _, g in longx.dropna(subset=[feat, "fwd_ret_3"]).groupby("open_time"):
            if len(g) < 6:
                continue
            ic = rank_ic(
                g[feat].to_numpy(dtype=np.float64),
                g["fwd_ret_3"].to_numpy(dtype=np.float64),
            )
            if pd.notna(ic):
                per_bar.append(ic)
        mean_ic = float(np.mean(per_bar)) if per_bar else float("nan")
        std_ic = float(np.std(per_bar)) if per_bar else float("nan")
        frac_pos = float(np.mean([v > 0 for v in per_bar])) if per_bar else float("nan")
        # IC t-stat (mean / (std/sqrt(n))) — significance of the XS-IC
        tstat = (
            mean_ic / (std_ic / np.sqrt(len(per_bar)))
            if per_bar and std_ic > 0
            else float("nan")
        )
        f1_rows.append(
            {
                "feature": feat,
                "n_bars": len(per_bar),
                "mean_xs_ic": round(mean_ic, 5),
                "std_xs_ic": round(std_ic, 5),
                "ic_tstat": round(tstat, 3) if pd.notna(tstat) else np.nan,
                "frac_bars_positive": round(frac_pos, 3),
            }
        )
        print(
            f"  {feat:28s}: XS-IC {mean_ic:+.5f}  t={tstat:+.2f}  "
            f"({frac_pos * 100:.0f}% pos, {len(per_bar)} bars)"
        )
    f1 = pd.DataFrame(f1_rows).sort_values(
        "mean_xs_ic", key=lambda s: s.abs(), ascending=False
    )
    f1.to_csv(OUT / "F1_cross_sectional_feature_ic.csv", index=False)

    # ---- pooled-major OOF model score ----
    pool = longx.sort_values(["open_time", "symbol"]).reset_index(drop=True)
    n_sym = pool["symbol"].nunique()
    X = pool[list(V3_FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
    y = pool["y"].to_numpy(dtype=int)
    oof = np.full(len(pool), np.nan)
    emb = EMBARGO_CANDLES * n_sym
    for tr, te in purged_kfold_indices(len(pool), 5, emb):
        if len(np.unique(y[tr])) < 2:
            continue
        m = lgb.LGBMClassifier(**LGB_PARAMS)
        m.fit(X[tr], y[tr])
        oof[te] = m.predict_proba(X[te])[:, 1]
    pool["oof"] = oof
    pool = pool.dropna(subset=["oof"]).reset_index(drop=True)

    # ---- F2: cross-sectional model rank-IC ----
    print("\nF2 — CROSS-SECTIONAL pooled-model-score rank-IC:")
    per_bar = []
    for _, g in pool.dropna(subset=["fwd_ret_3"]).groupby("open_time"):
        if len(g) < 6:
            continue
        ic = rank_ic(
            g["oof"].to_numpy(dtype=np.float64),
            g["fwd_ret_3"].to_numpy(dtype=np.float64),
        )
        if pd.notna(ic):
            per_bar.append(ic)
    mean_ic = float(np.mean(per_bar)) if per_bar else float("nan")
    std_ic = float(np.std(per_bar)) if per_bar else float("nan")
    frac_pos = float(np.mean([v > 0 for v in per_bar])) if per_bar else float("nan")
    tstat = (
        mean_ic / (std_ic / np.sqrt(len(per_bar)))
        if per_bar and std_ic > 0
        else float("nan")
    )
    print(
        f"  pooled-model XS-IC = {mean_ic:+.5f}  t={tstat:+.2f}  "
        f"({frac_pos * 100:.0f}% bars positive, {len(per_bar)} bars)"
    )

    # ---- F3: top-minus-bottom long-short basket forward return ----
    print("\nF3 — TOP-3-minus-BOTTOM-3 long-short basket forward-3-candle return:")
    ls_rets = []
    for _, g in pool.dropna(subset=["fwd_ret_3"]).groupby("open_time"):
        if len(g) < 6:
            continue
        gs = g.sort_values("oof")
        bottom = gs.head(3)["fwd_ret_3"].mean()
        top = gs.tail(3)["fwd_ret_3"].mean()
        ls_rets.append(top - bottom)
    ls = np.array(ls_rets, dtype=np.float64)
    ls = ls[np.isfinite(ls)]
    mean_ls = float(np.mean(ls)) if len(ls) else float("nan")
    std_ls = float(np.std(ls)) if len(ls) else float("nan")
    # 8h bars -> ~3 per day; the basket holds 3 candles so bars overlap, but
    # as a rough per-bar Sharpe proxy: mean/std * sqrt(bars-per-year/overlap).
    # report the raw per-bar mean/std and a simple annualization (3 bars/day,
    # 365 days, /3 overlap) for orientation only.
    ann = (
        mean_ls / std_ls * np.sqrt(365.0 * 3 / 3)
        if len(ls) and std_ls > 0
        else float("nan")
    )
    print(
        f"  long-short per-bar fwd3 return: mean {mean_ls:+.4f}%  "
        f"std {std_ls:.4f}%  ({len(ls)} bars)"
    )
    print(f"  rough annualized Sharpe proxy (orientation only): {ann:+.3f}")
    print(f"  fraction of bars with positive long-short return: "
          f"{np.mean(ls > 0) * 100:.1f}%")

    f2f3 = pd.DataFrame(
        [
            {"metric": "xs_model_ic", "value": round(mean_ic, 5),
             "tstat": round(tstat, 3) if pd.notna(tstat) else np.nan,
             "n_bars": len(per_bar), "frac_positive": round(frac_pos, 3)},
            {"metric": "long_short_mean_fwd3_pct", "value": round(mean_ls, 5),
             "tstat": np.nan, "n_bars": len(ls),
             "frac_positive": round(float(np.mean(ls > 0)), 3)},
            {"metric": "long_short_std_fwd3_pct", "value": round(std_ls, 5),
             "tstat": np.nan, "n_bars": len(ls), "frac_positive": np.nan},
            {"metric": "long_short_ann_sharpe_proxy", "value": round(ann, 4),
             "tstat": np.nan, "n_bars": len(ls), "frac_positive": np.nan},
        ]
    )
    f2f3.to_csv(OUT / "F2F3_cross_sectional_model.csv", index=False)

    print("\n" + "=" * 78)
    print("ANGLE 4 (re-run) SUMMARY")
    print("=" * 78)
    best = f1.iloc[0]
    print(f"  best cross-sectional FEATURE: {best['feature']} "
          f"XS-IC {best['mean_xs_ic']:+.5f} (t={best['ic_tstat']})")
    print(f"  cross-sectional MODEL XS-IC: {mean_ic:+.5f} (t={tstat:+.2f})")
    print(f"  long-short basket: mean fwd3 {mean_ls:+.4f}%, "
          f"ann-Sharpe-proxy {ann:+.3f}")
    print("  Files: F1_cross_sectional_feature_ic.csv,")
    print("         F2F3_cross_sectional_model.csv")


if __name__ == "__main__":
    main()
