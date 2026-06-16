"""IS-ONLY: does a BULL-regime restriction REDUCE sub-period dispersion at N=9? — iter-v1/011.

The decisive question for the iter-011 recommendation. regime_structural_test.py showed the LONG
edge is regime-bound (BULL +2.47 / BEAR +0.11). But the iter-010 brief rejected a regime GATE at
N=21 because every gate INVERTED in the most-recent IS third (locking in fragile beta). That
analysis was at N=21. This script checks the unifying stability metric (sub-period frac_pos +
dispersion + WORST sub-period + the most-recent-sub-period sign) AT N=9 for:

  - the ungated full model book (iter-010 N9 setup) — the incumbent recommendation
  - the BULL-regime-restricted model book (drop trades when 200-SMA falling)
  - a LONG-only-in-BULL book

The honest test: a regime restriction is only worth recommending if it (a) improves sub-period
frac_pos OR (b) materially raises the WORST sub-period Sharpe AND (c) does NOT invert in the most
recent IS sub-period (2025 Q1, the slice nearest OOS — the iter-010 T3-inversion failure mode). If
the most-recent sub-period stays negative even under the BULL restriction, the restriction does not
fix the IS-visible OOS-fragility fingerprint and the finding is STRUCTURAL with no IS-selectable fix.

OOS-VIGILANCE (HARD): strict IS filter + leak assert; expanding WF trains only before each test
window minus embargo >= label horizon; 200-SMA regime is stateless past-only (`.shift(1)`). `src/`,
runner, OOS UNTOUCHED. No OOS fit/selection.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-011/regime_gate_subperiod_n9.py
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
ATR_SL = 1.45
N_LABEL = 9
CANDLES_PER_DAY = 3.0
CANDLES_PER_YEAR = 365.25 * CANDLES_PER_DAY
EMBARGO_C = N_LABEL + 3
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-011"

ITER009_FEATURES: tuple[str, ...] = (
    "trend_adx_7",
    "vol_garman_klass_10",
    "vol_atr_5",
    "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_5",
    "vol_mfi_7",
    "mom_rsi_9",
    "stat_autocorr_lag1",
    "mr_pct_from_high_5",
    "vol_cmf_10",
    "ent_shannon_10",
    "trend_adx_14",
    "trend_supertrend_14_3",
    "btc_funding_spread_30_90",
    "funding_rate_zscore_30",
    "stat_autocorr_lag5",
    "vol_range_spike_72",
    "mr_rsi_extreme_14",
    "stat_kurtosis_20",
)
BASE_PARAMS = dict(
    n_estimators=300,
    max_depth=4,
    num_leaves=15,
    learning_rate=0.03,
    min_child_samples=80,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.5,
    reg_lambda=0.5,
    n_jobs=4,
    verbose=-1,
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


def expanding_wf(X, y, ot_days, valid, params, seed, min_train_days=365.0, step_days=30.0):
    n = len(X)
    embargo_days = EMBARGO_C / CANDLES_PER_DAY
    t0 = ot_days.min()
    ts = t0 + min_train_days + embargo_days
    preds, idx = [], []
    while ts < ot_days.max():
        te = ts + step_days
        tc = ts - embargo_days
        tr = valid & (ot_days < tc) & (ot_days >= t0)
        tem = valid & (ot_days >= ts) & (ot_days < te)
        if tr.sum() >= 200 and tem.sum() > 0:
            m = lgb.LGBMRegressor(random_state=seed, **params)
            m.fit(X[tr], y[tr])
            preds.append(m.predict(X[tem]))
            idx.append(np.where(tem)[0])
        ts = te
    p = np.concatenate(preds)
    g = np.concatenate(idx)
    d = np.zeros(n)
    d[g] = np.sign(p)
    oof = np.zeros(n, dtype=bool)
    oof[g] = True
    return d, oof


def ann_sharpe(r, n_total, min_n=10):
    r = r[np.isfinite(r)]
    if len(r) < min_n:
        return np.nan, np.nan, len(r)
    mean, std = float(np.mean(r)), float(np.std(r, ddof=1))
    if std <= 0:
        return np.nan, float(np.mean(r > 0)), len(r)
    return (
        (mean / std) * np.sqrt(len(r) / n_total * CANDLES_PER_YEAR),
        float(np.mean(r > 0)),
        len(r),
    )


def sp_stability(book_mask, book, ot_days, oof, n_is, period_days=182.5):
    t0 = ot_days[oof].min()
    t1 = ot_days[oof].max()
    cells, starts = [], []
    edge = t0
    while edge < t1:
        m = book_mask & (ot_days >= edge) & (ot_days < edge + period_days)
        sann, _, _ = ann_sharpe(book[m], n_is)
        cells.append(sann)
        starts.append(str(pd.to_datetime(edge * 86400_000, unit="ms").date()))
        edge += period_days
    fin = [c for c in cells if np.isfinite(c)]
    frac_pos = float(np.mean(np.array(fin) > 0)) if fin else np.nan
    disp = float(np.std(fin, ddof=1)) if len(fin) > 1 else np.nan
    worst = float(np.min(fin)) if fin else np.nan
    last = cells[-1] if cells else np.nan
    return cells, starts, frac_pos, disp, worst, last


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
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0
    feats = [c for c in ITER009_FEATURES if c in df.columns]
    X = df[feats].to_numpy(float)
    y = fwd_return(close, N_LABEL)
    valid = np.isfinite(y)

    s = pd.Series(close)
    sma200 = s.rolling(200).mean().shift(1)
    trend_bull = ((sma200 - sma200.shift(20)) > 0).to_numpy()

    d, oof = expanding_wf(X, y, ot_days, valid, BASE_PARAMS, 42)
    mb = letrun(high, low, close, atr, d, ATR_SL, N_LABEL)

    books = [
        ("ungated full (iter-010 N9)", oof & np.isfinite(mb)),
        ("BULL-restricted full", oof & np.isfinite(mb) & trend_bull),
        ("LONG-only in BULL", oof & (d > 0) & np.isfinite(mb) & trend_bull),
        ("ungated LONG-only", oof & (d > 0) & np.isfinite(mb)),
    ]
    print("=" * 104)
    print("SUB-PERIOD STABILITY AT N=9 — does BULL restriction fix dispersion / most-recent sign?")
    print("  KEY: most-recent sub-period (2025-01-03) sign = IS-visible OOS-fragility fingerprint")
    print("=" * 104)
    rows = []
    detail_starts = None
    for name, bmask in books:
        cells, starts, frac_pos, disp, worst, last = sp_stability(bmask, mb, ot_days, oof, n_is)
        detail_starts = starts
        overall, wr, nn = ann_sharpe(mb[bmask], n_is)
        cellstr = " ".join(f"{c:+.2f}" if np.isfinite(c) else " nan " for c in cells)
        print(f"  {name:28s} overall_S={overall:+.3f} n={nn:4d}")
        print(f"      per-sub-period: {cellstr}")
        print(
            f"      frac_pos={frac_pos:.3f}  dispersion={disp:.3f}  worst={worst:+.3f}  "
            f"MOST-RECENT(2025Q1)={last:+.3f}"
        )
        rows.append(
            dict(
                book=name,
                overall_sharpe=round(overall, 3),
                n=nn,
                frac_pos=round(frac_pos, 3),
                dispersion=round(disp, 3),
                worst_subperiod=round(worst, 3),
                most_recent_subperiod=round(last, 3),
            )
        )
    OUTDIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUTDIR / "regime_gate_subperiod_n9.csv", index=False)
    print(f"\n  sub-period starts: {detail_starts}")
    print(f"\nWrote: {OUTDIR / 'regime_gate_subperiod_n9.csv'}")


if __name__ == "__main__":
    main()
