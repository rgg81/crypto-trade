"""iter-v3/101 — ANGLE 1 — LTC DEEP-DIVE.

CONTEXT
-------
The /101 first IC screen (`excluded_majors_ic_screen.py`, commit 8ffed8d)
found LTCUSDT the SINGLE excluded liquid major clearing both the GENUINE band
(within-symbol purged-5-fold-CV rank-IC +0.0613) AND sign-stability across 3
IS thirds (3/3 thirds positive, worst third +0.00147). Every other major was
either THIN (8 of 10) or SIGN-FLIPPING (SOL +0.063 but flipped). BTC -0.069 /
ETH -0.003 are the two deepest markets and are NEGATIVE.

THE QUESTION FOR THIS ANGLE
---------------------------
+0.0613 / sign-stable is one number from one config. Is it a genuinely
TRADEABLE edge, or a scrape-band artifact? Three sub-questions:

  (a) HOW DOES LTC COMPARE TO LDO (v3's best altcoin, +0.178)? LDO is 2.9x
      LTC's IC. If LTC is structurally LDO-like-but-weaker, that is one
      reading; if LTC's edge is texturally different (e.g. far more
      regime-dependent, or one feature carrying everything), that is another.

  (b) IS THE +0.0613 STABLE TO RESEED / FOLD-COUNT / EMBARGO PERTURBATION?
      A genuine within-symbol edge survives a 10-seed LightGBM reseed and a
      3-fold-vs-5-fold-vs-10-fold change. A scrape-band artifact does not.

  (c) WHERE DOES LTC'S SIGNAL CONCENTRATE? Decompose the IC by IS calendar
      year, by realized-vol bucket, by trend/range regime (Hurst). If +0.0613
      is the average of a strong-regime +0.15 and a dead-regime -0.02, the
      edge is real but regime-gated. If it is a flat +0.06 everywhere, it is
      a weak-but-broad edge.

This is EDA. No backtest, no brief, no src/ changes. IS-only.

NO-CHEATING
-----------
  - OOS_CUTOFF_MS = 1742774400000 (2025-03-24). Every row open_time < cutoff.
  - 24-month per-symbol listing burn-in (TRAINING_MONTHS=24) — the runner's
    walk-forward evaluation span.
  - /059 production triple-barrier label (ATR TP=2.0 / SL=1.0, timeout 21
    candles, fee 0.1%) — byte-identical to the /101 IC-screen labeler.
  - 14-feature V3_FEATURE_COLUMNS stack — the /059 anchor.
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
FEE_PCT = 0.1
EMBARGO_CANDLES = 22
DATA_DIR = Path("data/features_v3")
OUT = Path("analysis/iteration_v3-101")

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
    verbose=-1,
    n_jobs=2,
)


def triple_barrier_label(df: pd.DataFrame) -> pd.DataFrame:
    """Byte-identical to the /101 IC-screen labeler (the /059 production rule)."""
    out = df.reset_index(drop=True).copy()
    n = len(out)
    high = out["high"].to_numpy(dtype=np.float64)
    low = out["low"].to_numpy(dtype=np.float64)
    close = out["close"].to_numpy(dtype=np.float64)
    close_time = out["close_time"].to_numpy(dtype=np.int64)
    natr = out["natr_21_raw"].to_numpy(dtype=np.float64)
    timeout_ms = TIMEOUT_MIN * 60 * 1000

    labels = np.zeros(n, dtype=np.int64)
    pnls = np.full(n, np.nan, dtype=np.float64)

    for i in range(n):
        entry = close[i]
        if entry <= 0:
            continue
        atr = (natr[i] / 100.0) * entry if np.isfinite(natr[i]) else entry * 0.02
        tp_dist = atr * TP_MULT
        sl_dist = atr * SL_MULT
        long_tp = entry + tp_dist
        long_sl = entry - sl_dist
        short_tp = entry - tp_dist
        short_sl = entry + sl_dist
        deadline = close_time[i] + timeout_ms

        long_result = 0
        short_result = 0
        long_step = -1
        short_step = -1
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
                long_result, long_step = -2, n
            if short_result == 0:
                short_result, short_step = -2, n

        fwd_ret = (last_close - entry) / entry * 100.0 if entry != 0 else 0.0

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
        pnls[i] = fwd_ret

    out["tb_label"] = labels
    out["fwd_ret"] = pnls
    return out


def load_symbol_is(symbol: str) -> pd.DataFrame | None:
    path = DATA_DIR / f"{symbol}_8h_features.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path).sort_values("open_time").reset_index(drop=True)
    first_ms = int(df["open_time"].min())
    burnin_end = first_ms + TRAINING_MONTHS * 30 * 24 * 60 * 60 * 1000
    df = triple_barrier_label(df)
    is_mask = (df["open_time"] >= burnin_end) & (df["open_time"] < OOS_CUTOFF_MS)
    isd = df[is_mask].copy()
    isd["symbol"] = symbol
    isd["y"] = (isd["tb_label"] == 1).astype(int)
    return isd.dropna(subset=list(V3_FEATURE_COLUMNS)).reset_index(drop=True)


def rank_ic(pred: np.ndarray, target: np.ndarray) -> float:
    if len(pred) < 30:
        return float("nan")
    c = pd.Series(pred).rank().corr(pd.Series(target).rank())
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


def cv_ic(d: pd.DataFrame, k: int, embargo: int, seed: int) -> float:
    X = d[list(V3_FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
    y = d["y"].to_numpy(dtype=int)
    tgt = d["tb_label"].to_numpy(dtype=np.float64)
    ics: list[float] = []
    for tr, te in purged_kfold_indices(len(d), k, embargo):
        if len(np.unique(y[tr])) < 2 or len(te) < 30:
            continue
        m = lgb.LGBMClassifier(**LGB_PARAMS, random_state=seed)
        m.fit(X[tr], y[tr])
        p = m.predict_proba(X[te])[:, 1]
        ic = rank_ic(p, tgt[te])
        if pd.notna(ic):
            ics.append(ic)
    return float(np.nanmean(ics)) if ics else float("nan")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/101 ANGLE 1 — LTC DEEP-DIVE (IS-only)")
    print("=" * 78)

    ltc = load_symbol_is("LTCUSDT")
    ldo = load_symbol_is("LDOUSDT")
    bch = load_symbol_is("BCHUSDT")
    trx = load_symbol_is("TRXUSDT")
    if ltc is None or ldo is None:
        print("LTC or LDO parquet missing — abort")
        return

    # ---- A1: structural comparison LTC vs LDO vs BCH vs TRX ----
    print("\nA1 — LTC vs altcoin reference (panel size, label balance, 5-fold CV IC):")
    a1_rows = []
    for name, d in [("LTCUSDT", ltc), ("LDOUSDT", ldo), ("BCHUSDT", bch), ("TRXUSDT", trx)]:
        if d is None:
            continue
        ic5 = cv_ic(d, 5, EMBARGO_CANDLES, 42)
        a1_rows.append(
            {
                "symbol": name,
                "is_rows": len(d),
                "long_label_frac": round(float(d["y"].mean()), 4),
                "mean_fwd_ret_pct": round(float(d["fwd_ret"].mean()), 4),
                "fwd_ret_std_pct": round(float(d["fwd_ret"].std()), 4),
                "cv5_rank_ic": round(ic5, 5),
            }
        )
        print(
            f"  {name:10s}: rows={len(d):5d}  long_frac={d['y'].mean():.4f}  "
            f"CV5-IC={ic5:+.5f}"
        )
    a1 = pd.DataFrame(a1_rows)
    a1.to_csv(OUT / "A1_ltc_vs_altcoin_structural.csv", index=False)

    # ---- A2: reseed + fold-count + embargo robustness on LTC ----
    print("\nA2 — LTC CV-IC robustness (10 reseeds x {3,5,10}-fold; embargo sweep):")
    a2_rows = []
    for k in (3, 5, 10):
        seed_ics = [cv_ic(ltc, k, EMBARGO_CANDLES, s) for s in range(10)]
        seed_ics = [v for v in seed_ics if pd.notna(v)]
        a2_rows.append(
            {
                "config": f"{k}fold_emb22",
                "k": k,
                "embargo": EMBARGO_CANDLES,
                "n_seeds": len(seed_ics),
                "mean_ic": round(float(np.mean(seed_ics)), 5),
                "std_ic": round(float(np.std(seed_ics)), 5),
                "min_ic": round(float(np.min(seed_ics)), 5),
                "max_ic": round(float(np.max(seed_ics)), 5),
                "frac_positive": round(float(np.mean([v > 0 for v in seed_ics])), 3),
            }
        )
        print(
            f"  {k:2d}-fold emb22: mean {np.mean(seed_ics):+.5f}  "
            f"std {np.std(seed_ics):.5f}  range [{np.min(seed_ics):+.4f}, "
            f"{np.max(seed_ics):+.4f}]  {np.mean([v > 0 for v in seed_ics]) * 100:.0f}% pos"
        )
    for emb in (0, 11, 44):
        seed_ics = [cv_ic(ltc, 5, emb, s) for s in range(10)]
        seed_ics = [v for v in seed_ics if pd.notna(v)]
        a2_rows.append(
            {
                "config": f"5fold_emb{emb}",
                "k": 5,
                "embargo": emb,
                "n_seeds": len(seed_ics),
                "mean_ic": round(float(np.mean(seed_ics)), 5),
                "std_ic": round(float(np.std(seed_ics)), 5),
                "min_ic": round(float(np.min(seed_ics)), 5),
                "max_ic": round(float(np.max(seed_ics)), 5),
                "frac_positive": round(float(np.mean([v > 0 for v in seed_ics])), 3),
            }
        )
        print(
            f"  5-fold emb{emb:2d}: mean {np.mean(seed_ics):+.5f}  "
            f"std {np.std(seed_ics):.5f}  {np.mean([v > 0 for v in seed_ics]) * 100:.0f}% pos"
        )
    a2 = pd.DataFrame(a2_rows)
    a2.to_csv(OUT / "A2_ltc_cv_robustness.csv", index=False)

    # ---- A3: LTC IC by calendar year ----
    print("\nA3 — LTC CV-IC decomposed by IS calendar year:")
    ltc2 = ltc.copy()
    ltc2["year"] = pd.to_datetime(ltc2["open_time"], unit="ms").dt.year
    a3_rows = []
    for yr, g in ltc2.groupby("year"):
        g = g.reset_index(drop=True)
        if len(g) < 120:
            a3_rows.append({"year": int(yr), "n": len(g), "cv3_ic": np.nan})
            print(f"  {yr}: n={len(g)} — too few rows")
            continue
        ic = cv_ic(g, 3, EMBARGO_CANDLES, 42)
        a3_rows.append({"year": int(yr), "n": len(g), "cv3_ic": round(ic, 5)})
        print(f"  {yr}: n={len(g):4d}  CV3-IC={ic:+.5f}")
    a3 = pd.DataFrame(a3_rows)
    a3.to_csv(OUT / "A3_ltc_ic_by_year.csv", index=False)

    # ---- A4: LTC IC by regime (vol bucket, Hurst trend/range) ----
    print("\nA4 — LTC univariate-feature-blend IC by regime "
          "(within-symbol, regime-conditioned):")
    # Build a single purged-5-fold OOF prediction, then slice by regime.
    X = ltc[list(V3_FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
    y = ltc["y"].to_numpy(dtype=int)
    oof = np.full(len(ltc), np.nan)
    for tr, te in purged_kfold_indices(len(ltc), 5, EMBARGO_CANDLES):
        if len(np.unique(y[tr])) < 2:
            continue
        m = lgb.LGBMClassifier(**LGB_PARAMS, random_state=42)
        m.fit(X[tr], y[tr])
        oof[te] = m.predict_proba(X[te])[:, 1]
    ltc3 = ltc.copy()
    ltc3["oof"] = oof
    ltc3 = ltc3.dropna(subset=["oof"]).reset_index(drop=True)
    a4_rows = []
    # vol regime
    vol_med = ltc3["range_realized_vol_50"].median()
    for label, mask in [
        ("vol_low", ltc3["range_realized_vol_50"] <= vol_med),
        ("vol_high", ltc3["range_realized_vol_50"] > vol_med),
        ("hurst_trend", ltc3["hurst_100"] > 0.5),
        ("hurst_range", ltc3["hurst_100"] <= 0.5),
        ("btcup", ltc3["btc_ret_14d"] > 0),
        ("btcdown", ltc3["btc_ret_14d"] <= 0),
    ]:
        seg = ltc3[mask]
        ic = rank_ic(
            seg["oof"].to_numpy(dtype=np.float64),
            seg["tb_label"].to_numpy(dtype=np.float64),
        )
        a4_rows.append({"regime": label, "n": len(seg), "oof_rank_ic": round(ic, 5)})
        print(f"  {label:14s}: n={len(seg):4d}  OOF-IC={ic:+.5f}")
    a4 = pd.DataFrame(a4_rows)
    a4.to_csv(OUT / "A4_ltc_ic_by_regime.csv", index=False)

    print("\n" + "=" * 78)
    print("ANGLE 1 SUMMARY")
    print("=" * 78)
    ltc_mean5 = next(r["mean_ic"] for r in a2_rows if r["config"] == "5fold_emb22")
    ltc_std5 = next(r["std_ic"] for r in a2_rows if r["config"] == "5fold_emb22")
    print(f"  LTC 5-fold CV-IC (10-seed mean): {ltc_mean5:+.5f} +- {ltc_std5:.5f}")
    print(f"  LDO 5-fold CV-IC (seed 42): "
          f"{next(r['cv5_rank_ic'] for r in a1_rows if r['symbol'] == 'LDOUSDT'):+.5f}")
    print("  Read the A2/A3/A4 tables: is LTC's edge seed-stable, and where")
    print("  does it concentrate (year / vol / Hurst)?")
    print("  Files: A1_ltc_vs_altcoin_structural.csv, A2_ltc_cv_robustness.csv,")
    print("         A3_ltc_ic_by_year.csv, A4_ltc_ic_by_regime.csv")


if __name__ == "__main__":
    main()
