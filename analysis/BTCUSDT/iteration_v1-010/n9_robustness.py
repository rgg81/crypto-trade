"""IS-ONLY robustness check on the N=9 (3d) reserve axis — iter-v1/010.

gate_forensic_and_n9.py [C] showed the shorter-horizon N=9 let-run book lifts the BLIND
(ungated) annualized Sharpe +0.66 -> +1.07 and — uniquely — the model BEATS always-LONG
ungated (+1.07 vs +0.81), via a higher WR (34.3% -> 44.5%) that smooths the equity curve.
Before recommending N=9 as the iter-010 axis, confirm the lift is NOT a T3-inversion
artifact (the failure mode that sank every N=21 gate) and is SEED-ROBUST (the campaign's
basin-lottery vigilance). Two tests, IS-only:

  1. SUB-PERIOD STABILITY: N=9 model let-run annualized Sharpe + WR + model-vs-LONG per IS
     third. Pass if model Sharpe is positive in >=2/3 thirds AND (critically) does NOT
     invert in T3 the way every N=21 gate did, AND model >= LONG in the thirds.
  2. SEED ROBUSTNESS: re-fit the N=9 purged-OOF model at 6 seeds; report ungated
     annualized Sharpe + WR per seed (mean, min, frac positive, frac beating always-LONG).
     Sign-robust if frac_pos == 1.0 and the mean clearly beats the N=21 ungated +0.66.

OOS-VIGILANCE (HARD): strict IS filter + leak-guard assert; forward quantities after the
filter. `src/`, runner, OOS UNTOUCHED.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-010/n9_robustness.py
"""

from __future__ import annotations

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
ATR_COLUMN = "vol_natr_21"
FEE_PCT = 0.1
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-010"
ATR_SL = 1.45
CANDLES_PER_YEAR = 365.25 * 3.0
SEEDS = (42, 123, 456, 789, 1001, 2024)

ITER009_FEATURES: tuple[str, ...] = (
    "trend_adx_7", "vol_garman_klass_10", "vol_atr_5", "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_5", "vol_mfi_7", "mom_rsi_9", "stat_autocorr_lag1",
    "mr_pct_from_high_5", "vol_cmf_10", "ent_shannon_10", "trend_adx_14",
    "trend_supertrend_14_3", "btc_funding_spread_30_90", "funding_rate_zscore_30",
    "stat_autocorr_lag5", "vol_range_spike_72", "mr_rsi_extreme_14", "stat_kurtosis_20",
)


def fwd_return(close, n):
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        if close[i] != 0:
            out[i] = (close[i + n] - close[i]) / close[i] * 100.0
    return out


def letrun(high, low, close, atr, direction, atr_sl, timeout_c):
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


def purged_oof(X, y, valid, seed, folds=5, embargo=3):
    idx = np.where(valid)[0]
    Xm, ym = X[idx], y[idx]
    fs = len(idx) // folds
    preds, gidx = [], []
    for k in range(1, folds):
        tr_end = k * fs
        te_s = tr_end + embargo
        te_e = min((k + 1) * fs, len(idx))
        if te_s >= te_e:
            continue
        m = lgb.LGBMRegressor(
            n_estimators=300, max_depth=4, num_leaves=15, learning_rate=0.03,
            min_child_samples=80, subsample=0.8, colsample_bytree=0.8,
            reg_alpha=0.5, reg_lambda=0.5, random_state=seed, n_jobs=4, verbose=-1,
        )
        m.fit(Xm[:tr_end], ym[:tr_end])
        preds.append(m.predict(Xm[te_s:te_e]))
        gidx.append(idx[te_s:te_e])
    return np.concatenate(preds), np.concatenate(gidx)


def ann_sharpe(r, freq_frac):
    r = r[np.isfinite(r)]
    if len(r) < 20:
        return np.nan, np.nan
    mean, std = float(np.mean(r)), float(np.std(r, ddof=1))
    spt = mean / std if std > 0 else np.nan
    sann = spt * np.sqrt(freq_frac * CANDLES_PER_YEAR) if np.isfinite(spt) else np.nan
    return sann, float(np.mean(r > 0))


def main() -> None:
    df_full = pd.read_parquet(PARQUET)
    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"
    n_is = len(df)
    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    natr = df[ATR_COLUMN].to_numpy(float)
    atr = close * natr / 100.0
    ot = df["open_time"].to_numpy()
    feats = [c for c in ITER009_FEATURES if c in df.columns]
    assert len(feats) == 19
    X = df[feats].to_numpy(float)
    long_dir = np.ones(n_is)

    fwd9 = fwd_return(close, 9)
    realized9 = fwd9

    # ---- 1. sub-period stability (seed 42) ----
    p9, g9 = purged_oof(X, fwd9, np.isfinite(fwd9), 42)
    d9 = np.zeros(n_is)
    d9[g9] = np.sign(p9)
    model9 = letrun(high, low, close, atr, d9, ATR_SL, 9)
    long9 = letrun(high, low, close, atr, long_dir, ATR_SL, 9)
    oof9 = np.zeros(n_is, dtype=bool)
    oof9[g9] = True

    ot_oof = ot[oof9 & np.isfinite(model9)]
    edges = np.linspace(ot_oof.min(), ot_oof.max() + 1, 4)
    third = np.digitize(ot, edges[1:-1])

    print("=" * 90)
    print("1. N=9 SUB-PERIOD STABILITY (seed 42)  — does it AVOID the N=21 T3 inversion?")
    print(f"   thirds: T1[..{pd.to_datetime(edges[1],unit='ms').date()}] "
          f"T2[..{pd.to_datetime(edges[2],unit='ms').date()}] "
          f"T3[..{pd.to_datetime(edges[3],unit='ms').date()}]")
    print("=" * 90)
    rows1 = []
    for tt in (0, 1, 2):
        m = oof9 & np.isfinite(model9) & (third == tt)
        sann, wr = ann_sharpe(model9[m], m.sum() / n_is)
        lm = oof9 & np.isfinite(long9) & (third == tt)
        lsann, _ = ann_sharpe(long9[lm], lm.sum() / n_is)
        diracc = float(np.mean(d9[m] == np.sign(realized9[m]))) if m.sum() else np.nan
        rows1.append(dict(third=f"T{tt+1}", n=int(m.sum()), model_sharpe_ann=round(sann, 3),
                          wr=round(wr, 3), dir_acc=round(diracc, 4),
                          LONG_sharpe_ann=round(lsann, 3),
                          model_beats_long=sann > lsann))
        print(f"  T{tt+1}: model_sharpe_ann={sann:+.3f}  WR={wr:.3f}  dir_acc={diracc:.4f}"
              f"  LONG_sharpe_ann={lsann:+.3f}  model>LONG={sann>lsann}")
    n_pos = sum(1 for r in rows1 if r["model_sharpe_ann"] > 0)
    n_beat = sum(1 for r in rows1 if r["model_beats_long"])
    print(f"  => {n_pos}/3 thirds positive ; model beats LONG in {n_beat}/3 thirds")

    # ---- 2. seed robustness ----
    print("\n" + "=" * 90)
    print("2. N=9 SEED ROBUSTNESS (ungated annualized Sharpe + WR across 6 seeds)")
    print("=" * 90)
    rows2 = []
    for seed in SEEDS:
        ps, gs = purged_oof(X, fwd9, np.isfinite(fwd9), seed)
        ds = np.zeros(n_is)
        ds[gs] = np.sign(ps)
        ms = letrun(high, low, close, atr, ds, ATR_SL, 9)
        oofs = np.zeros(n_is, dtype=bool)
        oofs[gs] = True
        mm = oofs & np.isfinite(ms)
        sann, wr = ann_sharpe(ms[mm], mm.sum() / n_is)
        lsann, _ = ann_sharpe(long9[oofs & np.isfinite(long9)],
                              (oofs & np.isfinite(long9)).sum() / n_is)
        rows2.append(dict(seed=seed, sharpe_ann=round(sann, 4), wr=round(wr, 4),
                          LONG_sharpe_ann=round(lsann, 4), beats_long=sann > lsann))
        print(f"  seed {seed:5d}: sharpe_ann={sann:+.4f}  WR={wr:.4f}  "
              f"LONG={lsann:+.4f}  model>LONG={sann>lsann}")
    svals = np.array([r["sharpe_ann"] for r in rows2])
    print(f"  => mean={svals.mean():+.4f}  min={svals.min():+.4f}  "
          f"max={svals.max():+.4f}  spread={svals.max()-svals.min():.4f}  "
          f"frac_pos={np.mean(svals>0):.2f}  "
          f"frac_beat_long={np.mean([r['beats_long'] for r in rows2]):.2f}")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows1).to_csv(OUTDIR / "n9_stability.csv", index=False)
    pd.DataFrame(rows2).to_csv(OUTDIR / "n9_seed_robustness.csv", index=False)
    print(f"\nWrote: {OUTDIR/'n9_stability.csv'}, {OUTDIR/'n9_seed_robustness.csv'}")


if __name__ == "__main__":
    main()
