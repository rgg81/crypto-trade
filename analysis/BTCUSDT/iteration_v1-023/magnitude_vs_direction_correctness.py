"""IS-ONLY: is the volatility-MAGNITUDE state a TRADE-SELECTION signal, or only a |move|-SIZE signal
that is BLIND to whether the deterministic trend-state direction is right? — iter-v1/023 (BTCUSDT).

The companion script (magnitude_selected_book.py) showed the magnitude-gated book turns NEGATIVE in
the most-recent IS sub-periods (the OOS-proxy) while the incumbent strength gate stays positive. This
script isolates the MECHANISM, the binding-constraint test the task warns about:

  H_size : the magnitude state predicts the |forward move| (a SIZE signal — FE iter-014 confirmed it).
  H_select: the magnitude state predicts whether the deterministic trend-state direction WINS
            (a SELECTION signal — the property a tradeable edge needs).

If H_size holds but H_select FAILS (magnitude predicts size, not direction-correctness), then sizing
the trend-state book by magnitude AMPLIFIES the wrong-direction trades exactly as much as the
right-direction ones in high-vol regimes — and the direction is the binding constraint, so the
magnitude signal cannot rescue OOS robustness. That is the honest-null outcome.

We compute, per IS sub-period (and full-IS):
  - IC(vol_state, |fwd move|)               -> SIZE signal strength (should be +, stable; FE finding)
  - IC(vol_state, dir_ts * fwd_signed_ret)  -> SELECTION signal: does high vol-state predict the
                                               trend-state trade PnL being positive? (the key test)
  - win-rate of the trend-state direction in the HIGH-vol-state half vs the LOW-vol-state half
  - mean trend-state PnL in high vs low vol-state half
  - the SAME for the incumbent strength state (|close-SMA200|/ATR) as the positive control: the
    strength state SHOULD predict direction-correctness (it gates the trend regime).

OOS-VIGILANCE (HARD): strict IS filter + leak-guard assert BEFORE forward quantities; `.shift(1)`
past-only SMA/ATR; vol-state read past-only from parquet; OOS never read. `src/`+runner+OOS UNTOUCHED.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-023/magnitude_vs_direction_correctness.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

OOS_CUTOFF_MS = 1742774400000
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-023"

N_LABEL = 42
SUBPERIOD_DAYS = 182.5
MIN_SUB_N = 60
SMA_WIN = 200
ATR_WIN = 14
MAG_COLS = ("vol_natr_7", "vol_garman_klass_20", "vol_parkinson_20", "vol_bb_bandwidth_30")


def fwd_log_return(close, n):
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        if close[i] > 0 and close[i + n] > 0:
            out[i] = np.log(close[i + n] / close[i])
    return out


def subperiod_bounds(ot_days):
    t0, t1 = ot_days.min(), ot_days.max()
    edges, edge = [], t0
    while edge < t1:
        edges.append((edge, edge + SUBPERIOD_DAYS))
        edge += SUBPERIOD_DAYS
    return edges


def safe_ic(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < MIN_SUB_N or np.nanstd(x[m]) == 0:
        return np.nan
    ic, _ = spearmanr(x[m], y[m])
    return float(ic)


def composite_vol_rank(df):
    n = len(df)
    ranks = np.full((len(MAG_COLS), n), np.nan)
    for j, col in enumerate(MAG_COLS):
        x = df[col].to_numpy(float)
        pr = np.full(n, np.nan)
        finite_idx = np.where(np.isfinite(x))[0]
        for k, t in enumerate(finite_idx):
            if k == 0:
                pr[t] = 0.5
            else:
                pr[t] = float(np.mean(x[finite_idx[:k]] <= x[t]))
        ranks[j] = pr
    return np.nanmean(ranks, axis=0)


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PARQUET)
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"

    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0
    y = fwd_log_return(close, N_LABEL)         # signed forward log-return
    yabs = np.abs(y)                            # |forward move|
    bounds = subperiod_bounds(ot_days)
    sub_labels = [str(pd.to_datetime(lo * 86400_000, unit="ms").date()) for lo, _ in bounds]

    cp = pd.Series(close).shift(1).to_numpy()
    sma = pd.Series(close).rolling(SMA_WIN).mean().shift(1).to_numpy()
    tr = np.maximum(high - low, np.maximum(np.abs(high - cp), np.abs(low - cp)))
    atr = pd.Series(tr).rolling(ATR_WIN).mean().shift(1).to_numpy()
    dist_atr = (cp - sma) / np.where(atr > 0, atr, np.nan)
    strength = np.abs(dist_atr)                 # incumbent conviction state (positive control)
    dir_ts = np.where(cp > sma, 1.0, -1.0)
    ts_pnl_signed = dir_ts * y                  # trend-state directional PnL (pre-cost); >0 = direction won

    vol_rank = composite_vol_rank(df)

    base = np.isfinite(y) & np.isfinite(sma) & np.isfinite(cp) & np.isfinite(vol_rank) & np.isfinite(strength)

    def per_sub_ic(xstate, target):
        out = []
        for lo, hi in bounds:
            m = base & (ot_days >= lo) & (ot_days < hi)
            out.append(safe_ic(xstate[m], target[m]))
        return np.array(out, float)

    # SIZE signal: vol_state vs |fwd move|
    ic_size = per_sub_ic(vol_rank, yabs)
    # SELECTION signal: vol_state vs trend-state directional PnL (does high vol-state -> direction wins?)
    ic_select_vol = per_sub_ic(vol_rank, ts_pnl_signed)
    # POSITIVE CONTROL: strength state vs trend-state directional PnL (should be +, that's why A works)
    ic_select_str = per_sub_ic(strength, ts_pnl_signed)
    # And strength vs |fwd move| (does the conviction state ALSO pick big moves?)
    ic_size_str = per_sub_ic(strength, yabs)

    def frac_sign(arr, ref_sign):
        v = arr[np.isfinite(arr)]
        return float(np.mean(np.sign(v) == ref_sign)) if len(v) else np.nan

    def fullic(xstate, target):
        return safe_ic(xstate[base], target[base])

    full_size = fullic(vol_rank, yabs)
    full_sel_vol = fullic(vol_rank, ts_pnl_signed)
    full_sel_str = fullic(strength, ts_pnl_signed)
    full_size_str = fullic(strength, yabs)

    print(f"IS rows {len(df)}  N={N_LABEL}(14d)  sub-periods={len(bounds)}")
    print("=" * 120)
    print("FULL-IS univariate ICs (the mechanism summary):")
    print(f"  IC(vol_state, |fwd move|)             = {full_size:+.4f}   [SIZE signal — expect +, stable]")
    print(f"  IC(vol_state, trend-state PnL signed) = {full_sel_vol:+.4f}   [SELECTION signal — the KEY test]")
    print(f"  IC(strength , trend-state PnL signed) = {full_sel_str:+.4f}   [POSITIVE CONTROL — why gate A works]")
    print(f"  IC(strength , |fwd move|)             = {full_size_str:+.4f}   [does conviction also size?]")
    print("=" * 120)

    print("PER-SUB-PERIOD IC (last col = most-recent IS sub-period, the OOS-proxy):")
    print("  " + f"{'series':40s} " + " ".join(f"{lab[2:7]:>7s}" for lab in sub_labels) + "  frac_same_sign")
    for name, arr, ref in [
        ("IC(vol_state,|fwd move|)  SIZE", ic_size, +1),
        ("IC(vol_state,TS-PnL)  SELECTION", ic_select_vol, +1),
        ("IC(strength,TS-PnL)  CONTROL", ic_select_str, +1),
        ("IC(strength,|fwd move|)", ic_size_str, +1),
    ]:
        cells = [f"{v:+7.3f}" if np.isfinite(v) else f"{'·':>7s}" for v in arr]
        print(f"  {name:40s} " + " ".join(cells) + f"   {frac_sign(arr, ref):.3f}")

    # win-rate / mean-PnL split: high-vol-state half vs low-vol-state half (full IS, past-only median)
    print("\n" + "=" * 120)
    print("DIRECTION-CORRECTNESS SPLIT — trend-state book in HIGH vs LOW state half (full-IS median split):")
    bm = base & np.isfinite(ts_pnl_signed)
    med_vol = np.nanmedian(vol_rank[bm])
    med_str = np.nanmedian(strength[bm])
    for label, state, med in [("vol_state", vol_rank, med_vol), ("strength", strength, med_str)]:
        hi = bm & (state >= med)
        lo = bm & (state < med)
        wr_hi = float(np.mean(ts_pnl_signed[hi] > 0))
        wr_lo = float(np.mean(ts_pnl_signed[lo] > 0))
        mp_hi = float(np.mean(ts_pnl_signed[hi]) * 100)
        mp_lo = float(np.mean(ts_pnl_signed[lo]) * 100)
        print(f"  {label:10s}: HIGH-half WR={wr_hi:.3f} meanPnL={mp_hi:+.3f}%  |  "
              f"LOW-half WR={wr_lo:.3f} meanPnL={mp_lo:+.3f}%  |  "
              f"HIGH-LOW WR Δ={wr_hi-wr_lo:+.3f}  meanPnL Δ={mp_hi-mp_lo:+.3f}%")

    rows = []
    for name, arr in [("ic_vol_size", ic_size), ("ic_vol_select", ic_select_vol),
                      ("ic_str_select", ic_select_str), ("ic_str_size", ic_size_str)]:
        rec = {"series": name, "full_ic": round(
            {"ic_vol_size": full_size, "ic_vol_select": full_sel_vol,
             "ic_str_select": full_sel_str, "ic_str_size": full_size_str}[name], 4),
            "frac_same_sign_pos": round(frac_sign(arr, +1), 3)}
        for i, lab in enumerate(sub_labels):
            rec[f"ic_{lab}"] = round(float(arr[i]), 4) if np.isfinite(arr[i]) else np.nan
        rows.append(rec)
    pd.DataFrame(rows).to_csv(OUTDIR / "magnitude_vs_direction_correctness.csv", index=False)
    print(f"\nWrote: {OUTDIR / 'magnitude_vs_direction_correctness.csv'}")


if __name__ == "__main__":
    main()
