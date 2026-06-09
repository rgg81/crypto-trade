"""iter-v1/085 structure pre-screen — XLMUSDT (the /084 anti-CRV-trap gate).

Applies the refined NEGATIVE-trivial-baseline selector (feedback_v1_negative_trivial_baseline_selector):
  GATE 1  — trivial-momentum baseline (IS-only, min-horizon over 5d/21d/50d) <= +0.15
  GATE 2 SECONDARY (KEY) — max single-feature-vs-LABEL |Spearman IC| >= 0.04
  GATE 2 TERTIARY — return-autocorr magnitude max(|acf1|,|acf3|,|acf7|) >= 0.03 (informational)

The /084 mistake: CRV cratered (IS -2.47) because its near-zero trivial baseline was
PURE NOISE, not edge headroom. GATE 2 SECONDARY discriminates structure from noise.

IS-ONLY DISCIPLINE: every computation uses only bars with open_time < OOS_CUTOFF
(2025-03-24). Asserted at runtime. The triple-barrier label scans FORWARD but the
forward scan is contained entirely within IS bars (last labelable bar = last IS bar
minus timeout window); samples whose forward window would cross the cutoff are dropped
so no OOS price information enters the label.

GATE 1 mirrors analysis/iteration_v1-084/eda.py:trivial_mom_sharpe exactly.
GATE 2 label mirrors the single-symbol v1 specialist ATR-scaled triple barrier
(atr_tp=3.5, atr_sl=1.75, timeout=10080min=21 bars; same as Models C/D/E in
run_baseline_v186.py).
"""

import datetime as dt

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

OOS_CUTOFF_MS = int(dt.datetime(2025, 3, 24, tzinfo=dt.timezone.utc).timestamp() * 1000)
BARS_PER_DAY = 3  # 8h cadence
ANN = np.sqrt(BARS_PER_DAY * 365.0)
FEE = 0.0005  # 0.05% per side (GATE 1 trivial baseline, matches /084)
HORIZONS = {"5d": 15, "21d": 63, "50d": 150}  # bars
MIN_IS_YEARS = 4.0

# Single-symbol v1 specialist triple-barrier params (Models C/D/E in run_baseline_v186)
ATR_TP_MULT = 3.5
ATR_SL_MULT = 1.75
TIMEOUT_BARS = 21  # 10080 min / 480 min
ATR_PERIOD = 14
LABEL_FEE_PCT = 0.1  # round-trip fee% in the labeler (matches baseline label_trades)

SYM = "XLMUSDT"
KLINE = f"data/{SYM}/8h.csv"
FEAT = f"data/features/{SYM}_8h_features.parquet"

# GATE 2 candidate signals (cheap, IS-only). oi_delta unavailable for XLM (no OI feature).
CANDIDATES = [
    "stat_return_5",      # ret_5bar (~1.7d)
    "stat_return_15",     # ret_15bar (5d)
    "ret_21d",            # computed inline (63 bar)
    "mom_rsi_14",
    "vol_natr_14",
    "vol_bb_bandwidth_30",
]


def load_is_klines() -> pd.DataFrame:
    df = pd.read_csv(KLINE)
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
    df = df.sort_values("open_time").reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "OOS leak (klines)!"
    for c in ("open", "high", "low", "close"):
        df[c] = df[c].astype(float)
    return df


def trivial_mom_sharpe(close: pd.Series, n: int) -> float:
    """Long if ret_Nd>0 else short, applied to next bar. Turnover-aware fee. /084-identical."""
    mom = close.pct_change(n)
    pos = np.sign(mom).shift(1)
    bar_ret = close.pct_change()
    gross = pos * bar_ret
    turnover = pos.diff().abs().fillna(0.0)
    net = (gross - FEE * turnover).dropna()
    if net.std(ddof=1) == 0 or len(net) < 30:
        return float("nan")
    return float(net.mean() / net.std(ddof=1) * ANN)


def atr_wilder(df: pd.DataFrame, period: int = ATR_PERIOD) -> np.ndarray:
    h, low, c = df["high"].values, df["low"].values, df["close"].values
    pc = np.concatenate([[c[0]], c[:-1]])
    tr = np.maximum.reduce([h - low, np.abs(h - pc), np.abs(low - pc)])
    atr = np.full(len(tr), np.nan)
    if len(tr) >= period:
        atr[period - 1] = tr[:period].mean()
        for i in range(period, len(tr)):
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def triple_barrier_sign(df: pd.DataFrame) -> np.ndarray:
    """Forward TP/SL/timeout label SIGN for each bar, IS-only.

    For each entry bar t: the LONG outcome is computed by scanning forward up to
    TIMEOUT_BARS bars. TP = +ATR_TP_MULT*ATR[t], SL = -ATR_SL_MULT*ATR[t] (% of entry).
    label = +1 if the long PnL (tp/sl/timeout, fee-adjusted) is positive, -1 if negative,
    0 if flat/unlabelable. Samples whose full forward window would cross the IS cutoff
    are NOT dropped here (df is already IS-only); instead the last TIMEOUT_BARS bars get
    label=0 because their forward window is truncated — no OOS data is ever read.
    """
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    atr = atr_wilder(df)
    n = len(df)
    label = np.zeros(n, dtype=np.int64)
    for t in range(n):
        if np.isnan(atr[t]) or close[t] <= 0:
            continue
        # not enough forward bars -> unlabelable (forward window truncated)
        end = min(t + TIMEOUT_BARS, n - 1)
        if end <= t:
            continue
        entry = close[t]
        tp_price = entry * (1 + ATR_TP_MULT * atr[t] / entry)
        sl_price = entry * (1 - ATR_SL_MULT * atr[t] / entry)
        # only count as fully-labelable if a full timeout window exists OR a barrier
        # is hit before data ends
        hit = 0  # 1=tp, -1=sl, -2=timeout
        for j in range(t + 1, end + 1):
            if high[j] >= tp_price:
                hit = 1
                break
            if low[j] <= sl_price:
                hit = -1
                break
        if hit == 0:
            if end < t + TIMEOUT_BARS:
                # forward window truncated by end-of-IS-data and no barrier hit -> drop
                continue
            hit = -2  # genuine timeout
        if hit == 1:
            pnl = ATR_TP_MULT * atr[t] / entry * 100.0 - LABEL_FEE_PCT
        elif hit == -1:
            pnl = -ATR_SL_MULT * atr[t] / entry * 100.0 - LABEL_FEE_PCT
        else:  # timeout -> realized forward return at horizon
            pnl = (close[end] - entry) / entry * 100.0 - LABEL_FEE_PCT
        label[t] = 1 if pnl > 0 else (-1 if pnl < 0 else 0)
    return label


def main() -> None:
    kl = load_is_klines()
    is_years = (kl["open_time"].max() - kl["open_time"].min()) / 1000 / 86400 / 365.25
    print(f"{SYM}: {len(kl)} IS bars, {is_years:.2f}y "
          f"({pd.to_datetime(kl['open_time'].min(), unit='ms').date()} -> "
          f"{pd.to_datetime(kl['open_time'].max(), unit='ms').date()})")

    if is_years < MIN_IS_YEARS:
        print("INSUFFICIENT DATA — gate1_pass=False, structure_signal=NOISE")
        return

    # ---------- GATE 1 ----------
    close = kl["close"]
    s = {lab: trivial_mom_sharpe(close, n) for lab, n in HORIZONS.items()}
    triv_min = float(np.nanmin(list(s.values())))
    gate1_pass = triv_min <= 0.15
    print("\n=== GATE 1 — trivial TS-momentum baseline (IS-only, fee-adj) ===")
    for lab in HORIZONS:
        print(f"  {lab:>4}: {s[lab]:+.4f}")
    print(f"  MIN   : {triv_min:+.4f}   gate1_pass(<=+0.15) = {gate1_pass}")

    # ---------- triple-barrier label ----------
    lab_sign = triple_barrier_sign(kl)
    feat = pd.read_parquet(FEAT)
    feat = feat[feat["open_time"] < OOS_CUTOFF_MS].sort_values("open_time").reset_index(drop=True)
    assert feat["open_time"].max() < OOS_CUTOFF_MS, "OOS leak (features)!"
    # align label index to features by open_time
    kl_idx = kl.set_index("open_time")
    lab_series = pd.Series(lab_sign, index=kl["open_time"].values)
    feat = feat[feat["open_time"].isin(lab_series.index)].copy()
    feat["label"] = feat["open_time"].map(lab_series)
    # build ret_21d inline (63-bar pct change of close)
    feat = feat.sort_values("open_time").reset_index(drop=True)
    feat["ret_21d"] = feat["close"].pct_change(63)
    labeled = feat[feat["label"] != 0].copy()
    n_lab = len(labeled)
    pos_frac = float((labeled["label"] == 1).mean())
    print(f"\n=== Triple-barrier label (ATR tp={ATR_TP_MULT} sl={ATR_SL_MULT} "
          f"timeout={TIMEOUT_BARS}bar) ===")
    print(f"  labelable bars: {n_lab}  (+1 frac = {pos_frac:.3f})")

    # ---------- GATE 2 SECONDARY — max |IC| feature vs label ----------
    print("\n=== GATE 2 SECONDARY — single-feature |Spearman IC| vs label sign ===")
    ics = {}
    for c in CANDIDATES:
        if c not in labeled.columns:
            print(f"  {c:>22}: MISSING — skip")
            continue
        sub = labeled[[c, "label"]].dropna()
        if len(sub) < 50 or sub[c].nunique() < 5:
            print(f"  {c:>22}: insufficient ({len(sub)} obs)")
            continue
        rho, _ = spearmanr(sub[c], sub["label"])
        ics[c] = abs(float(rho))
        print(f"  {c:>22}: |IC| = {abs(rho):.4f}  (rho={rho:+.4f}, n={len(sub)})")
    max_ic = max(ics.values()) if ics else 0.0
    print(f"  MAX |IC| = {max_ic:.4f}")

    # ---------- GATE 2 TERTIARY — return autocorr ----------
    bar_ret = close.pct_change().dropna()
    acf = {}
    for lag in (1, 3, 7):
        acf[lag] = float(bar_ret.autocorr(lag))
    autocorr_mag = max(abs(acf[1]), abs(acf[3]), abs(acf[7]))
    print("\n=== GATE 2 TERTIARY — return autocorr (informational) ===")
    for lag in (1, 3, 7):
        print(f"  acf_{lag}: {acf[lag]:+.4f}")
    print(f"  MAG = {autocorr_mag:.4f}")

    # ---------- verdict ----------
    if max_ic >= 0.06:
        sig = "STRONG"
    elif max_ic >= 0.04:
        sig = "MODERATE"
    elif max_ic >= 0.02:
        sig = "WEAK"
    else:
        sig = "NOISE"
    print("\n=== VERDICT ===")
    print(f"  trivial_baseline_min = {triv_min:+.4f}")
    print(f"  max_feature_label_ic = {max_ic:.4f}")
    print(f"  autocorr_mag         = {autocorr_mag:.4f}")
    print(f"  gate1_pass           = {gate1_pass}")
    print(f"  structure_signal     = {sig}")


if __name__ == "__main__":
    main()
