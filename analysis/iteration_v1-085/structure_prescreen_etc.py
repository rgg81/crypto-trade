"""iter-v1/085 structure pre-screen for ETCUSDT (the /084 anti-CRV-trap gate).

Applies the refined NEGATIVE-trivial-baseline selector (memory:
feedback_v1_negative_trivial_baseline_selector) to ETCUSDT, IS-only
(klines strictly before OOS_CUTOFF 2025-03-24):

  GATE 1 — trivial TS-momentum baseline (IS-only, min-horizon over
           {5d=15bar, 21d=63bar, 50d=150bar}, fee-adj turnover-aware).
           gate1_pass = (min_sharpe <= +0.15).

  GATE 2 SECONDARY (KEY structure test) — max single-feature-vs-LABEL |IC|.
           Label = sign of EXACT triple-barrier first-hit outcome (ATR-scaled
           barriers tp=2.9*ATR, sl=1.45*ATR, timeout=21 bars; the Model-A-ETH
           vol-class cell used by every fresh-alt specialist ATOM/075, AAVE/076,
           CRV/084). Spearman |IC| of cheap candidate signals vs the label sign.
           STRONG >=0.06 | MODERATE 0.04-0.06 | WEAK 0.02-0.04 | NOISE <0.02.

  GATE 2 TERTIARY (informational) — return autocorr magnitude
           max(|acf_1|, |acf_3|, |acf_7|) on per-bar log returns.

IS-ONLY DISCIPLINE: every quantity below uses only bars with open_time < cutoff.
Asserted at runtime. No OOS bar is ever read.

8h bars -> 3 bars/day. Daily-equivalent Sharpe = per-bar-Sharpe * sqrt(3*365).
Fee model: 0.05% per side on the trivial baseline (turnover-aware), matching
analysis/iteration_v1-084/eda.py for apples-to-apples GATE 1 reuse-comparison.
The triple-barrier label uses fee_pct=0.1 (the v1 backtest fee), but the LABEL
SIGN is fee-insensitive (TP/SL first-hit is a pure price-path question), so the
fee only enters the tie-break at timeout.
"""

import datetime as dt

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

OOS_CUTOFF_MS = int(dt.datetime(2025, 3, 24, tzinfo=dt.timezone.utc).timestamp() * 1000)
BARS_PER_DAY = 3
ANN = np.sqrt(BARS_PER_DAY * 365.0)
FEE = 0.0005  # trivial-baseline per-side fee (matches /084 eda.py)
HORIZONS = {"5d": 15, "21d": 63, "50d": 150}
SYM = "ETCUSDT"

# Triple-barrier params (Model A ETH vol-class cell; fresh-alt specialist convention)
ATR_TP = 2.9
ATR_SL = 1.45
ATR_PERIOD = 14
TIMEOUT_BARS = 21  # 10080 minutes / 480 = 21 bars at 8h


def load_is(sym: str) -> pd.DataFrame:
    df = pd.read_csv(f"data/{sym}/8h.csv")
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
    df = df.sort_values("open_time").reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, f"{sym} OOS leak!"
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype(float)
    return df


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


# ---------------------------------------------------------------- indicators
def atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    h, low, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - low), (h - pc).abs(), (low - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0.0)
    dn = (-delta).clip(lower=0.0)
    rs = up.ewm(alpha=1 / period, adjust=False, min_periods=period).mean() / (
        dn.ewm(alpha=1 / period, adjust=False, min_periods=period).mean() + 1e-12
    )
    return 100.0 - 100.0 / (1.0 + rs)


def bb_bandwidth(close: pd.Series, period: int = 20, k: float = 2.0) -> pd.Series:
    ma = close.rolling(period).mean()
    sd = close.rolling(period).std(ddof=0)
    return (2 * k * sd) / (ma + 1e-12)


# ---------------------------------------------------------------- GATE 2: label
def triple_barrier_sign(df: pd.DataFrame) -> np.ndarray:
    """Exact long-side triple-barrier first-hit sign, IS-only.

    For each bar i, enter at close[i]; scan i+1..i+TIMEOUT for the first bar
    whose HIGH crosses tp = close*(1 + ATR_TP*atr/close) (label +1) or whose LOW
    crosses sl = close*(1 - ATR_SL*atr/close) (label -1). On timeout, label =
    sign(forward return at the timeout bar) (fee-adjusted tie at exactly 0 -> +1).
    Barriers use past-only ATR (atr[i], computed from data up to bar i).
    Returns array aligned to df index; NaN where unscannable (last TIMEOUT bars
    or NaN ATR). This mirrors label_trades' triple_barrier path semantics for the
    label SIGN (the dependent variable for the IC test).
    """
    n = len(df)
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    close = df["close"].to_numpy()
    a = atr(df).to_numpy()
    out = np.full(n, np.nan)
    for i in range(n):
        if i + 1 >= n or np.isnan(a[i]) or close[i] <= 0:
            continue
        entry = close[i]
        tp = entry + ATR_TP * a[i]
        sl = entry - ATR_SL * a[i]
        last = min(i + TIMEOUT_BARS, n - 1)
        label = None
        for j in range(i + 1, last + 1):
            hit_tp = high[j] >= tp
            hit_sl = low[j] <= sl
            if hit_tp and hit_sl:
                # ambiguous bar: conservative -> SL first (worst case for long)
                label = -1
                break
            if hit_tp:
                label = 1
                break
            if hit_sl:
                label = -1
                break
        if label is None:
            # timeout: sign of net forward return at timeout bar
            fwd = (close[last] - entry) / entry - 2 * 0.001  # 0.1% per side
            label = 1 if fwd >= 0 else -1
        out[i] = label
    return out


def main() -> None:
    df = load_is(SYM)
    is_years = (df["open_time"].max() - df["open_time"].min()) / 1000 / 86400 / 365.25
    n_bars = len(df)
    close = df["close"]

    # ---- GATE 1 ----
    sharpes = {lbl: trivial_mom_sharpe(close, n) for lbl, n in HORIZONS.items()}
    min_sharpe = float(np.nanmin(list(sharpes.values())))
    gate1_pass = bool(min_sharpe <= 0.15)

    # ---- GATE 2 SECONDARY: feature-vs-LABEL IC ----
    label = triple_barrier_sign(df)

    candidates = {
        "ret_5d": close.pct_change(HORIZONS["5d"]),
        "ret_21d": close.pct_change(HORIZONS["21d"]),
        "rsi_14": rsi(close, 14),
        "natr_30": (atr(df) / close).rolling(30).mean(),
        "vol_bb_bandwidth_20": bb_bandwidth(close, 20),
        "stat_autocorr_lag5": close.pct_change().rolling(50).apply(
            lambda x: pd.Series(x).autocorr(lag=5), raw=False
        ),
        "mom_roc_10": close.pct_change(10),
        "vol_volume_pctchg_5": df["volume"].pct_change(5),
    }

    lbl_ser = pd.Series(label, index=df.index)
    ic_rows = []
    for name, feat in candidates.items():
        pair = pd.concat([feat, lbl_ser], axis=1).dropna()
        # mask: only bars where label is valid AND feature finite
        pair = pair[np.isfinite(pair.iloc[:, 0]) & np.isfinite(pair.iloc[:, 1])]
        if len(pair) < 100 or pair.iloc[:, 0].std() == 0:
            ic_rows.append((name, float("nan"), len(pair)))
            continue
        rho, _ = spearmanr(pair.iloc[:, 0], pair.iloc[:, 1])
        ic_rows.append((name, float(rho), len(pair)))

    ic_df = pd.DataFrame(ic_rows, columns=["feature", "ic", "n"])
    ic_df["abs_ic"] = ic_df["ic"].abs()
    max_ic = float(ic_df["abs_ic"].max())

    # ---- GATE 2 TERTIARY: return autocorr ----
    log_ret = np.log(close / close.shift(1)).dropna()
    acf1 = float(log_ret.autocorr(lag=1))
    acf3 = float(log_ret.autocorr(lag=3))
    acf7 = float(log_ret.autocorr(lag=7))
    autocorr_mag = float(max(abs(acf1), abs(acf3), abs(acf7)))

    # ---- structure verdict ----
    if max_ic >= 0.06:
        structure = "STRONG"
    elif max_ic >= 0.04:
        structure = "MODERATE"
    elif max_ic >= 0.02:
        structure = "WEAK"
    else:
        structure = "NOISE"

    # ---- label balance (diagnostic — CRV had 30% WR both directions) ----
    valid_lbl = lbl_ser.dropna()
    long_frac = float((valid_lbl == 1).mean())

    print("=" * 64)
    print(f"STRUCTURE PRE-SCREEN — {SYM} (iter-v1/085)")
    print("=" * 64)
    print(f"IS years           : {is_years:.2f}   n_bars={n_bars}")
    print(f"IS label coverage  : {len(valid_lbl)} bars   long_frac={long_frac:.3f}")
    print("-" * 64)
    print("GATE 1 — trivial TS-momentum baseline (IS-only, fee-adj)")
    for lbl, n in HORIZONS.items():
        print(f"   {lbl:>4} ({n:>3} bar): Sharpe {sharpes[lbl]:+.3f}")
    print(f"   min_sharpe       : {min_sharpe:+.3f}")
    print(f"   GATE 1 PASS (<=+0.15)? {gate1_pass}")
    print("-" * 64)
    print("GATE 2 SECONDARY — single-feature-vs-LABEL |IC| (Spearman, IS-only)")
    print(ic_df.sort_values("abs_ic", ascending=False).to_string(index=False))
    print(f"   max |IC|         : {max_ic:.4f}")
    print("-" * 64)
    print("GATE 2 TERTIARY — return autocorr magnitude")
    print(f"   acf1={acf1:+.4f}  acf3={acf3:+.4f}  acf7={acf7:+.4f}")
    print(f"   autocorr_mag     : {autocorr_mag:.4f}  (>=0.03 = persistence)")
    print("=" * 64)
    print(f"STRUCTURE SIGNAL   : {structure}")
    print("=" * 64)

    # persist
    ic_df.to_csv("analysis/iteration_v1-085/etc_feature_label_ic.csv", index=False)
    summary = pd.DataFrame(
        [
            dict(
                coin=SYM,
                is_years=round(is_years, 2),
                n_bars=n_bars,
                s5=round(sharpes["5d"], 3),
                s21=round(sharpes["21d"], 3),
                s50=round(sharpes["50d"], 3),
                trivial_baseline_min=round(min_sharpe, 3),
                gate1_pass=gate1_pass,
                max_feature_label_ic=round(max_ic, 4),
                autocorr_mag=round(autocorr_mag, 4),
                long_frac=round(long_frac, 3),
                structure_signal=structure,
            )
        ]
    )
    summary.to_csv("analysis/iteration_v1-085/structure_prescreen_summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
