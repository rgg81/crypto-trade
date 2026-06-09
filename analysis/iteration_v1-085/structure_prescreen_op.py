"""iter-v1/085 STRUCTURE PRE-SCREEN — OPUSDT (the /084 anti-CRV-trap gate).

Implements the refined NEGATIVE-trivial-baseline selector
(feedback_v1_negative_trivial_baseline_selector), IS-ONLY (open_time < OOS_CUTOFF
2025-03-24). The /084 mistake: CRV's near-zero trivial baseline (+0.069) was PURE
NOISE, not edge headroom -> ML cratered (IS -2.47). GATE 2 adds a structure test
so a low GATE-1 baseline is only accepted when actual label-predictive structure
is present.

GATES
  GATE 1  trivial-momentum baseline: min-horizon TS-mom IS Sharpe over
          {5d=15bar, 21d=63bar, 50d=150bar}, fee-adj (0.05%/side, turnover-aware).
          gate1_pass = (min <= +0.15).
  GATE 2 PRIMARY (not run here)  fast single-seed LightGBM probe IS Sharpe >= +0.30.
  GATE 2 SECONDARY (KEY)  max single-feature-vs-LABEL |IC| (Spearman, IS-only)
          over a handful of cheap candidate signals. >= 0.04 is the structure floor.
  GATE 2 TERTIARY  return-autocorr magnitude max(|acf1|,|acf3|,|acf7|) >= 0.03 (info).

LABEL  = sign of the project's ATR triple-barrier outcome, computed forward, IS-only.
         Replicates the v1 specialist labeling EXACTLY:
           ATR(price) = close * vol_natr_21 / 100
           TP = 2.9 * ATR  (atr_tp from Model A ETH cell, /084 vol-class match)
           SL = 1.45 * ATR
           timeout = 21 candles (10080 min / 480)
         Long PnL and short PnL are computed; the label SIGN = +1 if the long
         barrier outcome beats the short, else -1 (i.e. which direction the
         triple barrier rewards). IC is Spearman(feature_t, label_t).

         Barrier scan uses ONLY forward bars that are themselves IS (open_time <
         cutoff) so no OOS bar ever enters the label. Bars whose 21-candle forward
         window would cross the cutoff are dropped (no partial-OOS leak).

verdict: STRONG (max|IC|>=0.06) / MODERATE (0.04-0.06) / WEAK (0.02-0.04) /
         NOISE (<0.02 — the CRV trap).
"""

import datetime as dt

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

OOS_CUTOFF_MS = int(dt.datetime(2025, 3, 24, tzinfo=dt.timezone.utc).timestamp() * 1000)
BARS_PER_DAY = 3
ANN = np.sqrt(BARS_PER_DAY * 365.0)
FEE = 0.0005  # 0.05% per side, turnover-aware (GATE 1)
HORIZONS = {"5d": 15, "21d": 63, "50d": 150}

# v1 specialist labeling (replicated)
ATR_TP = 2.9
ATR_SL = 1.45
TIMEOUT_CANDLES = 21
LABEL_FEE_PCT = 0.1  # round-trip fee% used by label_trades default

SYM = "OPUSDT"
FEAT = f"data/features/{SYM}_8h_features.parquet"
RAW = f"data/{SYM}/8h.csv"


# ---------------------------------------------------------------- GATE 1
def trivial_mom_sharpe(close: pd.Series, n: int) -> float:
    mom = close.pct_change(n)
    pos = np.sign(mom).shift(1)
    bar_ret = close.pct_change()
    gross = pos * bar_ret
    turnover = pos.diff().abs().fillna(0.0)
    net = (gross - FEE * turnover).dropna()
    if net.std(ddof=1) == 0 or len(net) < 30:
        return float("nan")
    return float(net.mean() / net.std(ddof=1) * ANN)


# ---------------------------------------------------------------- LABEL
def triple_barrier_label_sign(df: pd.DataFrame) -> np.ndarray:
    """+1 if long triple-barrier PnL > short PnL, else -1. NaN where unlabelable.

    Strict IS: forward scan only over bars whose open_time < cutoff.
    """
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    close = df["close"].to_numpy(float)
    atr = close * df["vol_natr_21"].to_numpy(float) / 100.0  # price units
    n = len(df)
    lab = np.full(n, np.nan)
    for i in range(n):
        a = atr[i]
        if not np.isfinite(a) or a <= 0:
            continue
        entry = close[i]
        tp_long = entry + ATR_TP * a
        sl_long = entry - ATR_SL * a
        tp_short = entry - ATR_TP * a
        sl_short = entry + ATR_SL * a
        end = min(i + TIMEOUT_CANDLES, n - 1)
        if end <= i:
            continue
        long_pnl = None
        short_pnl = None
        for j in range(i + 1, end + 1):
            hj, lj = high[j], low[j]
            # LONG: SL checked before TP within a bar (conservative)
            if long_pnl is None:
                if lj <= sl_long:
                    long_pnl = (sl_long - entry) / entry
                elif hj >= tp_long:
                    long_pnl = (tp_long - entry) / entry
            # SHORT
            if short_pnl is None:
                if hj >= sl_short:
                    short_pnl = (entry - sl_short) / entry
                elif lj <= tp_short:
                    short_pnl = (entry - tp_short) / entry
            if long_pnl is not None and short_pnl is not None:
                break
        if long_pnl is None:
            long_pnl = (close[end] - entry) / entry
        if short_pnl is None:
            short_pnl = (entry - close[end]) / entry
        rt = LABEL_FEE_PCT / 100.0
        long_pnl -= rt
        short_pnl -= rt
        lab[i] = 1.0 if long_pnl > short_pnl else -1.0
    return lab


def main() -> None:
    feat = pd.read_parquet(FEAT).sort_values("open_time").reset_index(drop=True)
    # IS-only
    feat = feat[feat["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert feat["open_time"].max() < OOS_CUTOFF_MS, "OOS leak!"
    n_is = len(feat)
    is_years = (feat["open_time"].max() - feat["open_time"].min()) / 1000 / 86400 / 365.25

    # GATE 1
    close = feat["close"].astype(float)
    s5 = trivial_mom_sharpe(close, HORIZONS["5d"])
    s21 = trivial_mom_sharpe(close, HORIZONS["21d"])
    s50 = trivial_mom_sharpe(close, HORIZONS["50d"])
    triv_min = float(np.nanmin([s5, s21, s50]))
    gate1_pass = triv_min <= 0.15

    # LABEL (drop tail bars whose forward window can't be fully scanned IS)
    label = triple_barrier_label_sign(feat)
    # The label loop already clamps to n-1 within the IS frame; the last
    # TIMEOUT_CANDLES bars have truncated windows -> drop them to avoid
    # short-window bias.
    label[n_is - TIMEOUT_CANDLES:] = np.nan
    feat["label"] = label

    # GATE 2 SECONDARY — max single-feature-vs-LABEL |IC|
    feat["ret_21d"] = close.pct_change(63)
    candidates = {
        "ret_5d (stat_return_15)": feat["stat_return_15"],
        "ret_21d (pct_change_63)": feat["ret_21d"],
        "rsi_14": feat["mom_rsi_14"],
        "natr_21": feat["vol_natr_21"],
        "bb_bandwidth_30": feat["vol_bb_bandwidth_30"],
        "bb_bandwidth_20": feat["vol_bb_bandwidth_20"],
        "stat_return_30": feat["stat_return_30"],
        "stat_return_5": feat["stat_return_5"],
    }
    valid = feat["label"].notna()
    ic_rows = []
    for name, ser in candidates.items():
        m = valid & ser.notna()
        if m.sum() < 100:
            ic_rows.append((name, float("nan"), int(m.sum())))
            continue
        rho, _ = spearmanr(ser[m], feat["label"][m])
        ic_rows.append((name, float(rho), int(m.sum())))
    ic_df = pd.DataFrame(ic_rows, columns=["feature", "ic", "n"])
    ic_df["abs_ic"] = ic_df["ic"].abs()
    max_ic = float(ic_df["abs_ic"].max())

    # GATE 2 TERTIARY — return autocorr magnitude
    r = close.pct_change().dropna()
    acf = {k: float(r.autocorr(lag=k)) for k in (1, 3, 7)}
    autocorr_mag = float(max(abs(acf[1]), abs(acf[3]), abs(acf[7])))

    # verdict
    if max_ic >= 0.06:
        verdict = "STRONG"
    elif max_ic >= 0.04:
        verdict = "MODERATE"
    elif max_ic >= 0.02:
        verdict = "WEAK"
    else:
        verdict = "NOISE"

    label_bal = pd.Series(label[valid]).value_counts().to_dict()

    print(f"=== OPUSDT STRUCTURE PRE-SCREEN (IS-only, before {dt.date(2025,3,24)}) ===")
    print(f"IS bars: {n_is}   IS years: {is_years:.2f}")
    print(f"label balance (long=+1/short=-1): {label_bal}   labelled n: {int(valid.sum())}")
    print()
    print("GATE 1 — trivial TS-mom Sharpe (fee-adj, turnover-aware):")
    print(f"  s5={s5:.3f}  s21={s21:.3f}  s50={s50:.3f}  MIN={triv_min:.3f}")
    print(f"  gate1_pass (min<=+0.15): {gate1_pass}")
    print()
    print("GATE 2 SECONDARY — single-feature-vs-LABEL |IC| (Spearman):")
    print(ic_df.sort_values("abs_ic", ascending=False).to_string(index=False))
    print(f"  MAX |IC| = {max_ic:.4f}")
    print()
    print("GATE 2 TERTIARY — return autocorr:")
    print(f"  acf1={acf[1]:.4f}  acf3={acf[3]:.4f}  acf7={acf[7]:.4f}  MAG={autocorr_mag:.4f}")
    print()
    print(
        f"STRUCTURE VERDICT: {verdict}   "
        "(STRONG>=0.06 / MOD 0.04-0.06 / WEAK 0.02-0.04 / NOISE<0.02)"
    )

    out = pd.DataFrame([{
        "coin": SYM, "is_years": round(is_years, 2), "is_bars": n_is,
        "triv_s5": round(s5, 3), "triv_s21": round(s21, 3), "triv_s50": round(s50, 3),
        "trivial_baseline_min": round(triv_min, 3), "gate1_pass": gate1_pass,
        "max_feature_label_ic": round(max_ic, 4), "autocorr_mag": round(autocorr_mag, 4),
        "structure_signal": verdict,
    }])
    out.to_csv("analysis/iteration_v1-085/structure_prescreen_op_results.csv", index=False)
    ic_df.sort_values("abs_ic", ascending=False).to_csv(
        "analysis/iteration_v1-085/structure_prescreen_op_ic.csv", index=False
    )


if __name__ == "__main__":
    main()
