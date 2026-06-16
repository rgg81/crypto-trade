"""IS-ONLY forensic on the best let-run gates + the N9/3d reserve axis — iter-v1/010.

Follows regime_gate_letrun_sharpe.py. Three questions the gate scan raised:

  A. STABILITY. The top-Sharpe gates (TREND100up, ADX>=25, TREND100up&ADX>=25,
     ADX>=25&fund-z<0) all lift the MODEL's let-run Sharpe vs ungated — but always-LONG
     lifts MORE in those same buckets (beta, not timing alpha). Is the model's lift even
     stable across IS sub-periods, or is it (like iter-008 found) one bull-market third?
     Split IS into 3 chronological thirds; report model let-run annualized Sharpe + WR per
     third for each candidate gate. A real, gateable edge is positive in >=2/3 thirds.

  B. DOES THE MODEL ADD ANYTHING OVER ALWAYS-LONG? Directional information content:
     within each candidate gate, (i) dir_acc of the model's chosen sign vs the realized
     7d sign, (ii) fraction of model trades that are SHORT (if ~0, the model is just a
     long filter and the gate == always-LONG with extra steps), (iii) model let-run mean
     vs always-LONG let-run mean on the SAME bucket candles (paired).

  C. RESERVE AXIS — shorter horizon N9 (3d) to lift the blind hit rate. Re-fit the same
     19-col purged-OOF model on a fixed_horizon N=9 (3d) label; simulate the let-run book
     with a 9-candle timeout (same SL=1.45 ATR, TP non-binding); report UNGATED WR /
     payoff / per-trade + annualized Sharpe vs the N=21 ungated book. Does a shorter
     horizon raise the blind WR enough to clear breakeven robustly without a gate?

OOS-VIGILANCE (HARD): same strict `open_time < OOS_CUTOFF_MS` filter + leak-guard assert;
all forward quantities AFTER the IS filter; regime vars stateless past-only. `src/`, the
runner, and OOS UNTOUCHED.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-010/gate_forensic_and_n9.py
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
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-010"
ATR_SL = 1.45
CANDLES_PER_YEAR = 365.25 * 3.0

ITER009_FEATURES: tuple[str, ...] = (
    "trend_adx_7", "vol_garman_klass_10", "vol_atr_5", "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_5", "vol_mfi_7", "mom_rsi_9", "stat_autocorr_lag1",
    "mr_pct_from_high_5", "vol_cmf_10", "ent_shannon_10", "trend_adx_14",
    "trend_supertrend_14_3", "btc_funding_spread_30_90", "funding_rate_zscore_30",
    "stat_autocorr_lag5", "vol_range_spike_72", "mr_rsi_extreme_14", "stat_kurtosis_20",
)


def fwd_return(close: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        if close[i] != 0:
            out[i] = (close[i + n] - close[i]) / close[i] * 100.0
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


def purged_oof(X, y, valid, folds=5, embargo=3):
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
            reg_alpha=0.5, reg_lambda=0.5, random_state=RANDOM_SEED, n_jobs=4,
            verbose=-1,
        )
        m.fit(Xm[:tr_end], ym[:tr_end])
        preds.append(m.predict(Xm[te_s:te_e]))
        gidx.append(idx[te_s:te_e])
    return np.concatenate(preds), np.concatenate(gidx)


def ann_sharpe(r, freq_frac):
    r = r[np.isfinite(r)]
    if len(r) < 20:
        return np.nan, np.nan, np.nan
    mean, std = float(np.mean(r)), float(np.std(r, ddof=1))
    spt = mean / std if std > 0 else np.nan
    sann = spt * np.sqrt(freq_frac * CANDLES_PER_YEAR) if np.isfinite(spt) else np.nan
    wr = float(np.mean(r > 0))
    return spt, sann, wr


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
    ot = df["open_time"].to_numpy()
    feats = [c for c in ITER009_FEATURES if c in df.columns]
    assert len(feats) == 19
    X = df[feats].to_numpy(float)
    fz = df["funding_rate_zscore_30"].to_numpy(float)

    s = pd.Series(close)

    def slope_sign(w, sw):
        sma = s.rolling(w).mean().shift(1)
        return np.sign(((sma - sma.shift(sw)) / sw).to_numpy())

    t100 = slope_sign(100, 20)
    adx_hi = adx >= 25.0
    fund_neg = fz < 0

    # ===================== N=21 model (the iter-009 book) =========================
    fwd21 = fwd_return(close, 21)
    p21, g21 = purged_oof(X, fwd21, np.isfinite(fwd21))
    d21 = np.zeros(n_is)
    d21[g21] = np.sign(p21)
    model21 = letrun(high, low, close, atr, d21, ATR_SL, 21)
    oof21 = np.zeros(n_is, dtype=bool)
    oof21[g21] = True
    long_dir = np.ones(n_is)
    long21 = letrun(high, low, close, atr, long_dir, ATR_SL, 21)

    # chronological thirds over OOF candles
    ot_oof = ot[oof21 & np.isfinite(model21)]
    edges = np.linspace(ot_oof.min(), ot_oof.max() + 1, 4)
    third = np.digitize(ot, edges[1:-1])  # 0/1/2 per row

    candidates = [
        ("UNGATED", np.ones(n_is, dtype=bool)),
        ("TREND100 up", t100 > 0),
        ("ADX>=25", adx_hi),
        ("TREND100up & ADX>=25", (t100 > 0) & adx_hi),
        ("ADX>=25 & fund z<0", adx_hi & fund_neg),
    ]

    print("=" * 92)
    print("A. SUB-PERIOD STABILITY — model let-run annualized Sharpe per IS third")
    print(f"   thirds: T1[..{pd.to_datetime(edges[1],unit='ms').date()}] "
          f"T2[..{pd.to_datetime(edges[2],unit='ms').date()}] "
          f"T3[..{pd.to_datetime(edges[3],unit='ms').date()}]")
    print("=" * 92)
    rowsA = []
    for name, gmask in candidates:
        cells, wrs, longcells = [], [], []
        for tt in (0, 1, 2):
            m = oof21 & np.isfinite(model21) & gmask & (third == tt)
            _, sann, wr = ann_sharpe(model21[m], m.sum() / n_is)
            _, lsann, _ = ann_sharpe(long21[oof21 & np.isfinite(long21) & gmask
                                             & (third == tt)], m.sum() / n_is)
            cells.append(sann)
            wrs.append(wr)
            longcells.append(lsann)
        n_pos = sum(1 for c in cells if np.isfinite(c) and c > 0)
        rowsA.append(dict(gate=name,
                          T1=round(cells[0], 3), T2=round(cells[1], 3),
                          T3=round(cells[2], 3), thirds_pos=f"{n_pos}/3",
                          T1_wr=round(wrs[0], 3) if np.isfinite(wrs[0]) else np.nan,
                          T2_wr=round(wrs[1], 3) if np.isfinite(wrs[1]) else np.nan,
                          T3_wr=round(wrs[2], 3) if np.isfinite(wrs[2]) else np.nan,
                          LONG_T1=round(longcells[0], 3),
                          LONG_T2=round(longcells[1], 3),
                          LONG_T3=round(longcells[2], 3)))
        print(f"  {name:22s} model[{cells[0]:+.2f} {cells[1]:+.2f} {cells[2]:+.2f}] "
              f"({n_pos}/3 pos)  WR[{wrs[0]:.2f} {wrs[1]:.2f} {wrs[2]:.2f}]  "
              f"LONG[{longcells[0]:+.2f} {longcells[1]:+.2f} {longcells[2]:+.2f}]")

    print("\n" + "=" * 92)
    print("B. DOES THE MODEL ADD DIRECTIONAL INFO OVER ALWAYS-LONG (in candidate gates)?")
    print("=" * 92)
    rowsB = []
    realized21 = fwd21  # realized 7d fwd return for dir_acc
    for name, gmask in candidates:
        m = oof21 & np.isfinite(model21) & gmask & np.isfinite(realized21)
        if m.sum() < 20:
            continue
        sgn_model = d21[m]
        sgn_real = np.sign(realized21[m])
        diracc = float(np.mean(sgn_model == sgn_real))
        frac_short = float(np.mean(sgn_model < 0))
        paired = float(np.mean(model21[m] - long21[m]))  # model minus long, same candles
        rowsB.append(dict(gate=name, n=int(m.sum()), dir_acc=round(diracc, 4),
                          frac_short=round(frac_short, 3),
                          model_minus_long_mean=round(paired, 4)))
        print(f"  {name:22s} n={int(m.sum()):4d} dir_acc={diracc:.4f} "
              f"frac_short={frac_short:.3f} model−long_mean={paired:+.4f}%")

    # ===================== C. RESERVE AXIS — N=9 (3d) =============================
    print("\n" + "=" * 92)
    print("C. RESERVE AXIS — shorter horizon N=9 (3d) let-run book (UNGATED)")
    print("=" * 92)
    fwd9 = fwd_return(close, 9)
    p9, g9 = purged_oof(X, fwd9, np.isfinite(fwd9))
    d9 = np.zeros(n_is)
    d9[g9] = np.sign(p9)
    model9 = letrun(high, low, close, atr, d9, ATR_SL, 9)
    oof9 = np.zeros(n_is, dtype=bool)
    oof9[g9] = True
    long9 = letrun(high, low, close, atr, long_dir, ATR_SL, 9)

    rowsC = []
    for tag, oofm, mdl, lng, n_to in [("N=21 (7d)", oof21, model21, long21, 21),
                                       ("N=9 (3d)", oof9, model9, long9, 9)]:
        mm = oofm & np.isfinite(mdl)
        r = mdl[mm]
        wins, losses = r[r > 0], r[r <= 0]
        wr = len(wins) / len(r)
        payoff = (np.mean(wins) / abs(np.mean(losses))) if len(losses) else np.nan
        be = (1 - wr) / wr
        spt, sann, _ = ann_sharpe(r, mm.sum() / n_is)
        lspt, lsann, lwr = ann_sharpe(lng[oofm & np.isfinite(lng)],
                                      (oofm & np.isfinite(lng)).sum() / n_is)
        rowsC.append(dict(horizon=tag, n=int(mm.sum()),
                          trades_per_mo=round(mm.sum() / n_is * CANDLES_PER_YEAR / 12, 1),
                          wr=round(wr, 4), payoff=round(payoff, 3),
                          be_payoff=round(be, 3), clears_be=payoff > be,
                          sharpe_pt=round(spt, 4), sharpe_ann=round(sann, 4),
                          LONG_sharpe_ann=round(lsann, 4)))
        print(f"  {tag:11s} n={int(mm.sum()):4d} WR={wr:.4f} payoff={payoff:.3f} "
              f"be_payoff={be:.3f} clears={payoff>be}  "
              f"sharpe_ann={sann:+.4f}  LONG_sharpe_ann={lsann:+.4f}")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rowsA).to_csv(OUTDIR / "gate_stability.csv", index=False)
    pd.DataFrame(rowsB).to_csv(OUTDIR / "gate_directional_info.csv", index=False)
    pd.DataFrame(rowsC).to_csv(OUTDIR / "reserve_n9_vs_n21.csv", index=False)
    print(f"\nWrote: {OUTDIR/'gate_stability.csv'}, {OUTDIR/'gate_directional_info.csv'}, "
          f"{OUTDIR/'reserve_n9_vs_n21.csv'}")


if __name__ == "__main__":
    main()
