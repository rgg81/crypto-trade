"""IS-ONLY forensic on the regime-conditional 'positive econ' buckets — iter-v1/008.

The regime scan (regime_conditional_edge.py) found buckets with OOF econ_net > 0
(high-vol, TREND100-up, TREND50-down, ADX>=25). BUT every bucket has OOF dir_acc < 0.5
— the prune model is anti-directional out-of-fold. So a positive econ inside a bucket
canNOT be coming from the model predicting direction correctly. This script settles
WHERE the positive econ comes from, before any gate is recommended. Three tests:

  1. MODEL vs ALWAYS-LONG vs ALWAYS-SHORT econ inside each gate bucket. If always-long
     ≈ the model's econ, the 'edge' is just BTC's directional drift in that regime, not
     a learned signal — gating to it is a beta bet, not alpha, and is fragile.
  2. MODEL-SIGN-FLIPPED econ. If sign-flipping the model BEATS the model (because
     dir_acc<0.5), the model is consistently wrong and the positive bucket econ is an
     accident of return asymmetry, not signal.
  3. SUB-PERIOD STABILITY. Split IS into 3 equal chronological thirds; report the gate
     bucket's model-econ in each third. A real regime edge is positive in >=2/3 thirds;
     a one-bull-run artifact is positive in only the bull third.

OOS-VIGILANCE (HARD): strict `open_time < OOS_CUTOFF_MS` filter + leak-guard assert.
Same past-only regime variables + same purged OOF as regime_conditional_edge.py.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-008/regime_edge_forensic.py
"""

from __future__ import annotations

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000
SYMBOL = "BTCUSDT"
INTERVAL = "8h"
PARQUET = Path("data/features") / f"{SYMBOL}_{INTERVAL}_features.parquet"
ATR_COLUMN = "vol_natr_21"
FEE_PCT = 0.1
RANDOM_SEED = 42
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-008"

V1_BTC_PRUNED_ITER002: tuple[str, ...] = (
    "cal_dow_norm", "mom_macd_hist_12_26_9", "mom_macd_hist_5_13_3", "mr_bb_pctb_10",
    "mr_pct_from_high_10", "mr_pct_from_high_100", "mr_pct_from_low_100",
    "mr_pct_from_low_20", "mr_rsi_extreme_14", "stat_autocorr_lag1",
    "stat_autocorr_lag10", "stat_autocorr_lag5", "stat_kurtosis_10", "stat_kurtosis_30",
    "stat_kurtosis_50", "stat_skew_10", "stat_skew_20", "stat_skew_50", "trend_adx_14",
    "trend_adx_7", "trend_aroon_down_25", "trend_aroon_down_50", "trend_aroon_osc_14",
    "trend_aroon_osc_25", "trend_aroon_osc_50", "trend_plus_di_21", "trend_psar_af",
    "trend_sma_50", "trend_supertrend_10_2", "trend_supertrend_7_3", "vol_ad",
    "vol_cmf_20", "vol_garman_klass_50", "vol_hist_10", "vol_hist_5", "vol_obv",
    "vol_taker_buy_ratio", "vol_taker_buy_ratio_sma_10", "vol_taker_buy_ratio_sma_50",
    "vol_volume_pctchg_15", "vol_volume_pctchg_20",
)


def _tb_long_ret(high, low, close, atr, atr_tp, atr_sl, to_c):
    n = len(close)
    out = np.full(n, np.nan)
    for i in range(n):
        entry = close[i]
        if entry == 0:
            continue
        a = atr[i] if not np.isnan(atr[i]) else entry * 0.02
        tp = entry + a * atr_tp
        sl = entry - a * atr_sl
        end = min(i + to_c, n - 1)
        if end <= i:
            continue
        last = close[end]
        for j in range(i + 1, end + 1):
            last = close[j]
            if low[j] <= sl or high[j] >= tp:
                break
        out[i] = (last - entry) / entry * 100.0
    return out


def _oof(X, y, valid, folds=5, embargo=3):
    idx = np.where(valid)[0]
    n = len(idx)
    Xm, ym = X[idx], y[idx]
    fs = n // folds
    preds, gidx = [], []
    for k in range(1, folds):
        tr_end = k * fs
        te_s = tr_end + embargo
        te_e = min((k + 1) * fs, n)
        if te_s >= te_e:
            continue
        m = lgb.LGBMRegressor(n_estimators=200, max_depth=4, num_leaves=15,
                              learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                              random_state=RANDOM_SEED, n_jobs=2, verbose=-1)
        m.fit(Xm[:tr_end], ym[:tr_end])
        preds.append(m.predict(Xm[te_s:te_e]))
        gidx.append(idx[te_s:te_e])
    return np.concatenate(preds), np.concatenate(gidx)


def _econ(sign_arr, y):
    return float(np.mean(sign_arr * y - FEE_PCT)) if len(y) else np.nan


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
    adx = df["trend_adx_14"].to_numpy(float)
    prune = [c for c in V1_BTC_PRUNED_ITER002 if c in df.columns]
    assert len(prune) == 41
    X = df[prune].to_numpy(float)
    ot = df["open_time"].to_numpy()

    long_ret = _tb_long_ret(high, low, close, atr, 2.9, 1.45, 21)
    valid = ~np.isnan(long_ret)
    pred, gidx = _oof(X, long_ret, valid)
    y = long_ret[gidx]
    msign = np.sign(pred)

    print("=" * 80)
    print(f"IS-ONLY regime-edge FORENSIC — {SYMBOL} {INTERVAL}  | IS rows {n_is}, OOF {len(y)}")
    print("=" * 80)
    print(f"\n[ungated OOF] model_econ={_econ(msign, y):+.4f}  "
          f"alwaysLONG={_econ(np.ones_like(y), y):+.4f}  "
          f"alwaysSHORT={_econ(-np.ones_like(y), y):+.4f}  "
          f"flip_model={_econ(-msign, y):+.4f}")
    print("  (if alwaysLONG≈model or flip>model ⇒ model carries NO directional alpha)")

    # past-only regime vars at OOF rows
    s = pd.Series(close)

    def slope_sign(w, sw):
        sma = s.rolling(w).mean().shift(1)
        return np.sign(((sma - sma.shift(sw)) / sw).to_numpy())

    t100 = slope_sign(100, 20)[gidx]
    t50 = slope_sign(50, 10)[gidx]
    roll = 250
    ns = pd.Series(natr)
    nhi = ns.rolling(roll).quantile(0.67).shift(1).to_numpy()
    volhi = ((natr > nhi) & ~np.isnan(nhi))[gidx]
    adxhi = (adx >= 25)[gidx]
    ot_oof = ot[gidx]

    # chronological thirds (by IS open_time)
    t_lo, t_hi = ot_oof.min(), ot_oof.max()
    edges = np.linspace(t_lo, t_hi + 1, 4)
    third = np.digitize(ot_oof, edges[1:-1])  # 0,1,2

    gates = [
        ("VOL high (natr>p67)", volhi),
        ("TREND100 up", t100 > 0),
        ("TREND50 down", t50 < 0),
        ("ADX>=25", adxhi),
        ("VOL high & TREND100 up", volhi & (t100 > 0)),
    ]

    print("\n[1+2] MODEL vs ALWAYS-LONG vs FLIP inside each gate bucket")
    print("-" * 80)
    rows = []
    for name, mask in gates:
        if mask.sum() == 0:
            continue
        ym, mm = y[mask], msign[mask]
        e_model = _econ(mm, ym)
        e_long = _econ(np.ones_like(ym), ym)
        e_short = _econ(-np.ones_like(ym), ym)
        e_flip = _econ(-mm, ym)
        diracc = float(np.mean(np.sign(mm) == np.sign(ym)))
        verdict = "MODEL-ALPHA" if (e_model > e_long and e_model > e_flip) else (
            "DRIFT(=long)" if abs(e_model - e_long) < 0.05 else
            "ANTI(flip>model)" if e_flip > e_model else "weak")
        rows.append(dict(gate=name, n=int(mask.sum()), dir_acc=diracc,
                         model=e_model, longonly=e_long, shortonly=e_short,
                         flip=e_flip, verdict=verdict))
        print(f"  {name:28s} n={mask.sum():4d} dir_acc={diracc:+.3f} "
              f"model={e_model:+.4f} LONG={e_long:+.4f} SHORT={e_short:+.4f} "
              f"flip={e_flip:+.4f}  => {verdict}")

    print("\n[3] SUB-PERIOD STABILITY (model_econ in each chronological IS third)")
    print("-" * 80)
    for name, mask in gates:
        if mask.sum() == 0:
            continue
        cells = []
        for tt in (0, 1, 2):
            m = mask & (third == tt)
            cells.append(_econ(msign[m], y[m]) if m.sum() > 20 else np.nan)
        n_pos = sum(1 for c in cells if (not np.isnan(c)) and c > 0)
        t0d = pd.to_datetime(edges[0], unit="ms").date()
        t1d = pd.to_datetime(edges[1], unit="ms").date()
        t2d = pd.to_datetime(edges[2], unit="ms").date()
        t3d = pd.to_datetime(edges[3], unit="ms").date()
        print(f"  {name:28s} third1={cells[0]:+.4f} third2={cells[1]:+.4f} "
              f"third3={cells[2]:+.4f}  ({n_pos}/3 positive)")
    print(f"  thirds span: T1[{t0d}..{t1d}] T2[..{t2d}] T3[..{t3d}]")

    # also: long-only econ per third (is the 'edge' just bull-market beta?)
    print("\n[3b] ALWAYS-LONG econ per third (beta reference — is positive econ just drift?)")
    print("-" * 80)
    for name, mask in gates:
        if mask.sum() == 0:
            continue
        cells = []
        for tt in (0, 1, 2):
            m = mask & (third == tt)
            cells.append(_econ(np.ones(int(m.sum())), y[m]) if m.sum() > 20 else np.nan)
        print(f"  {name:28s} third1={cells[0]:+.4f} third2={cells[1]:+.4f} "
              f"third3={cells[2]:+.4f}")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUTDIR / "regime_edge_forensic.csv", index=False)
    print(f"\nWrote: {OUTDIR / 'regime_edge_forensic.csv'}")


if __name__ == "__main__":
    main()
