"""iter-v3/101 — ANGLE 4 — POOLED vs CROSS-SECTIONAL ON THE MAJOR UNIVERSE.

THE QUESTION
------------
The /101 first IC screen and angles 1-3 are all WITHIN-symbol. But the liquid
majors are a tight, deeply-correlated, deeply-liquid universe — the natural
home for two architectures the per-symbol model cannot exploit:

  (a) POOLED — one model trained on all 10 majors' bars stacked. More data
      (~32k IS rows vs ~3k per symbol), correlated symbols sharing structure.
      The /093 pooled-vs-single test was on thin altcoins; a pooled model on
      the deep, homogeneous major universe is a different proposition.

  (b) CROSS-SECTIONAL / RELATIVE-VALUE RANKING — at each 8h bar, rank the 10
      majors by a feature (or a model score) and trade the cross-section
      (long the top, short the bottom). This is the equity-quant playbook;
      it is structurally suited to a liquid correlated universe. The /088-092
      cross-sectional re-architecture was near-breakeven on thin altcoins —
      but a 10-name liquid major panel is the universe cross-sectional models
      were designed for.

WHAT THIS ANGLE MEASURES
------------------------
  D1  POOLED purged-5-fold-CV rank-IC. Stack all 10 majors' IS bars, train
      ONE 14-feature LightGBM on 4/5 purged folds (purge respects the global
      time order), measure rank-IC vs the /059 triple-barrier label on the
      held-out fold. Compare to the per-symbol numbers and to a pooled model
      on the 3 altcoins.

  D2  POOLED-MODEL per-symbol IC TRANSFER. Take the pooled OOF predictions and
      measure the rank-IC SEPARATELY for each major's rows. A pooled model is
      only useful if its signal transfers to the individual symbols — not just
      in aggregate. Per-symbol sign-consistency of the pooled signal.

  D3  CROSS-SECTIONAL FEATURE rank-IC. For each feature, at every 8h bar
      cross-sectionally rank the 10 majors, and measure the rank correlation
      of that cross-sectional feature rank vs the cross-sectional forward
      3-candle return rank. Averaged over bars = the cross-sectional IC of
      that feature. This is the "does relative value work on the majors"
      headline. A feature with a cross-sectional IC clearly above the
      within-symbol thin floor is a real relative-value signal.

  D4  CROSS-SECTIONAL MODEL rank-IC. Build the pooled-model OOF score, then at
      each bar cross-sectionally rank the 10 majors by that score and measure
      the rank-IC vs the cross-sectional forward-return rank. This is the
      direct EDA proxy for a cross-sectional long-short major book's signal
      strength — no backtest, just the per-bar cross-sectional IC.

This is EDA. No backtest, no brief, no src/ changes. IS-only.

NO-CHEATING
-----------
  - OOS_CUTOFF_MS = 1742774400000. Every row open_time < cutoff.
  - 24-month per-symbol burn-in applied BEFORE pooling.
  - Pooled purged-CV: rows sorted by global open_time; the embargo purges
    rows within 22 candles of a test-fold boundary so no label window leaks.
  - Cross-sectional forward return is the target ONLY — never a feature.
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
ALTCOINS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")

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
    return isd.dropna(subset=list(V3_FEATURE_COLUMNS)).reset_index(drop=True)


def rank_ic(pred: np.ndarray, target: np.ndarray) -> float:
    mask = np.isfinite(pred) & np.isfinite(target)
    if mask.sum() < 30:
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


def pooled_oof(pool: pd.DataFrame) -> np.ndarray:
    """Purged-5-fold OOF prediction for a time-ordered pooled panel.
    The embargo is enlarged by n_symbols since each calendar timestamp now has
    one row per symbol — 22 candles * n_symbols rows fall in the label window.
    """
    n_sym = pool["symbol"].nunique()
    pool = pool.sort_values(["open_time", "symbol"]).reset_index(drop=True)
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
    return pool


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/101 ANGLE 4 — POOLED vs CROSS-SECTIONAL ON THE MAJORS (IS-only)")
    print("=" * 78)

    panels: dict[str, pd.DataFrame] = {}
    for sym in EXCLUDED_MAJORS + ALTCOINS:
        d = load_symbol_is(sym)
        if d is None:
            print(f"  {sym}: parquet missing — skipped")
            continue
        panels[sym] = d
        print(f"  {sym:10s}: {len(d):5d} IS rows")

    majors = {s: panels[s] for s in EXCLUDED_MAJORS if s in panels}
    alts = {s: panels[s] for s in ALTCOINS if s in panels}

    # ---- D1: pooled CV-IC (majors) and (altcoins) ----
    print("\nD1 — POOLED purged-5-fold CV rank-IC:")
    d1_rows = []
    for label, group in [("majors_10", majors), ("altcoins_3", alts)]:
        pool = pd.concat(group.values(), ignore_index=True)
        pool = pooled_oof(pool)
        valid = pool.dropna(subset=["oof"])
        ic = rank_ic(
            valid["oof"].to_numpy(dtype=np.float64),
            valid["tb_label"].to_numpy(dtype=np.float64),
        )
        d1_rows.append(
            {"pool": label, "n_symbols": len(group), "n_rows": len(pool),
             "pooled_cv_rank_ic": round(ic, 5)}
        )
        print(f"  {label:12s}: {len(group)} symbols, {len(pool):6d} rows, "
              f"pooled CV-IC = {ic:+.5f}")
    d1 = pd.DataFrame(d1_rows)
    d1.to_csv(OUT / "D1_pooled_cv_ic.csv", index=False)

    # ---- D2: pooled-model per-symbol IC transfer (majors) ----
    print("\nD2 — POOLED-major-model per-symbol IC transfer "
          "(does the pooled signal transfer to each major?):")
    pool_m = pd.concat(majors.values(), ignore_index=True)
    pool_m = pooled_oof(pool_m)
    d2_rows = []
    for sym in majors:
        sub = pool_m[(pool_m["symbol"] == sym) & pool_m["oof"].notna()].copy()
        sub = sub.sort_values("open_time").reset_index(drop=True)
        ic_full = rank_ic(
            sub["oof"].to_numpy(dtype=np.float64),
            sub["tb_label"].to_numpy(dtype=np.float64),
        )
        n = len(sub)
        thirds = []
        for lo, hi in [(0, n // 3), (n // 3, 2 * n // 3), (2 * n // 3, n)]:
            seg = sub.iloc[lo:hi]
            thirds.append(
                rank_ic(
                    seg["oof"].to_numpy(dtype=np.float64),
                    seg["tb_label"].to_numpy(dtype=np.float64),
                )
            )
        signs = {np.sign(v) for v in thirds if pd.notna(v) and abs(v) > 0.02}
        d2_rows.append(
            {
                "symbol": sym,
                "pooled_model_ic_on_symbol": round(ic_full, 5) if pd.notna(ic_full) else np.nan,
                "third_1": round(thirds[0], 5) if pd.notna(thirds[0]) else np.nan,
                "third_2": round(thirds[1], 5) if pd.notna(thirds[1]) else np.nan,
                "third_3": round(thirds[2], 5) if pd.notna(thirds[2]) else np.nan,
                "sign_stable": len(signs) <= 1,
            }
        )
        print(
            f"  {sym:10s}: pooled-model IC {ic_full:+.5f}  "
            f"thirds [{thirds[0]:+.4f}, {thirds[1]:+.4f}, {thirds[2]:+.4f}]  "
            f"{'stable' if len(signs) <= 1 else 'FLIP'}"
        )
    d2 = pd.DataFrame(d2_rows)
    d2.to_csv(OUT / "D2_pooled_per_symbol_transfer.csv", index=False)

    # ---- D3: cross-sectional feature rank-IC ----
    print("\nD3 — CROSS-SECTIONAL feature rank-IC across the 10 majors")
    print("     (per-bar rank of feature vs per-bar rank of fwd_ret_3, "
          "averaged over bars):")
    # build a long panel of majors only, keep bars where >= 6 majors present
    longm = pd.concat(
        [d.assign(symbol=s) for s, d in majors.items()], ignore_index=True
    )
    d3_rows = []
    for feat in V3_FEATURE_COLUMNS:
        per_bar = []
        for _, g in longm.dropna(subset=[feat, "fwd_ret_3"]).groupby("open_time"):
            if len(g) < 6:
                continue
            ic = rank_ic(
                g[feat].to_numpy(dtype=np.float64),
                g["fwd_ret_3"].to_numpy(dtype=np.float64),
            )
            if pd.notna(ic):
                per_bar.append(ic)
        mean_xs_ic = float(np.mean(per_bar)) if per_bar else float("nan")
        frac_pos = float(np.mean([v > 0 for v in per_bar])) if per_bar else float("nan")
        d3_rows.append(
            {
                "feature": feat,
                "n_bars": len(per_bar),
                "mean_cross_sectional_ic": round(mean_xs_ic, 5),
                "frac_bars_positive": round(frac_pos, 3),
            }
        )
        print(
            f"  {feat:28s}: XS-IC {mean_xs_ic:+.5f}  "
            f"({len(per_bar)} bars, {frac_pos * 100:.0f}% pos)"
        )
    d3 = pd.DataFrame(d3_rows).sort_values(
        "mean_cross_sectional_ic", key=lambda s: s.abs(), ascending=False
    )
    d3.to_csv(OUT / "D3_cross_sectional_feature_ic.csv", index=False)

    # ---- D4: cross-sectional MODEL rank-IC ----
    print("\nD4 — CROSS-SECTIONAL pooled-model-score rank-IC across the majors:")
    longm2 = pool_m[pool_m["oof"].notna()].copy()
    per_bar = []
    for _, g in longm2.dropna(subset=["fwd_ret_3"]).groupby("open_time"):
        if len(g) < 6:
            continue
        ic = rank_ic(
            g["oof"].to_numpy(dtype=np.float64),
            g["fwd_ret_3"].to_numpy(dtype=np.float64),
        )
        if pd.notna(ic):
            per_bar.append(ic)
    mean_xs = float(np.mean(per_bar)) if per_bar else float("nan")
    frac_pos = float(np.mean([v > 0 for v in per_bar])) if per_bar else float("nan")
    print(
        f"  pooled-model cross-sectional IC: {mean_xs:+.5f}  "
        f"({len(per_bar)} bars, {frac_pos * 100:.0f}% bars positive)"
    )
    # also: tb_label cross-sectional version
    per_bar_tb = []
    for _, g in longm2.groupby("open_time"):
        if len(g) < 6:
            continue
        ic = rank_ic(
            g["oof"].to_numpy(dtype=np.float64),
            g["tb_label"].to_numpy(dtype=np.float64),
        )
        if pd.notna(ic):
            per_bar_tb.append(ic)
    mean_xs_tb = float(np.mean(per_bar_tb)) if per_bar_tb else float("nan")
    print(f"  pooled-model cross-sectional IC vs tb_label: {mean_xs_tb:+.5f}")
    d4 = pd.DataFrame(
        [
            {"metric": "xs_model_ic_vs_fwd_ret_3", "value": round(mean_xs, 5),
             "n_bars": len(per_bar), "frac_bars_positive": round(frac_pos, 3)},
            {"metric": "xs_model_ic_vs_tb_label", "value": round(mean_xs_tb, 5),
             "n_bars": len(per_bar_tb), "frac_bars_positive": np.nan},
        ]
    )
    d4.to_csv(OUT / "D4_cross_sectional_model_ic.csv", index=False)

    print("\n" + "=" * 78)
    print("ANGLE 4 SUMMARY")
    print("=" * 78)
    best_xs = d3.iloc[0]
    print(f"  pooled-majors CV-IC: "
          f"{d1[d1['pool'] == 'majors_10']['pooled_cv_rank_ic'].iloc[0]:+.5f}")
    print(f"  best cross-sectional feature: {best_xs['feature']} "
          f"XS-IC {best_xs['mean_cross_sectional_ic']:+.5f}")
    print(f"  pooled-model cross-sectional IC: {mean_xs:+.5f}")
    print("  Files: D1_pooled_cv_ic.csv, D2_pooled_per_symbol_transfer.csv,")
    print("         D3_cross_sectional_feature_ic.csv,")
    print("         D4_cross_sectional_model_ic.csv")


if __name__ == "__main__":
    main()
