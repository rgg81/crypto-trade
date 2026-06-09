"""iter-v1/085 STRUCTURE PRE-SCREEN — UNIUSDT (the /084 anti-CRV-trap gate).

USER DIRECTIVE 2026-06-09: keep mining fresh alts but apply the /084 structure
lesson. CRV cratered (IS -2.47) because a near-zero trivial baseline was PURE
NOISE not edge headroom. Refined selector (feedback_v1_negative_trivial_baseline_selector):

  GATE 1: trivial-momentum baseline (IS-only, min-horizon over 5d/21d/50d) <= +0.15
          (avoid FIL clean-trend trap)
  GATE 2 PRIMARY: fast single-seed LightGBM probe IS Sharpe >= +0.30 (deferred to
          QE backtest; this script computes the cheap SECONDARY/TERTIARY structure tests)
  GATE 2 SECONDARY: max single-feature-vs-LABEL |IC| >= 0.04 (Spearman, IS-only)  <-- KEY TEST
  GATE 2 TERTIARY: return-autocorr magnitude >= 0.03 (informational)

structure_signal verdict:
  STRONG   max|IC| >= 0.06
  MODERATE 0.04 - 0.06
  WEAK     0.02 - 0.04
  NOISE    < 0.02  (the CRV trap)

IS-ONLY DISCIPLINE: every number below uses only bars with open_time < OOS_CUTOFF
(2025-03-24). Asserted at runtime.

Label = v1 baseline triple-barrier (TP=8.0%, SL=4.0%, timeout=21 bars=10080min),
sign of first-hit barrier (long_pnl >= short_pnl convention -> directional label).
Replicated faithfully from src/crypto_trade/strategies/ml/labeling.py barrier scan.
"""

import datetime as dt

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

SYM = "UNIUSDT"
OOS_CUTOFF_MS = int(dt.datetime(2025, 3, 24, tzinfo=dt.timezone.utc).timestamp() * 1000)
BARS_PER_DAY = 3  # 8h cadence
ANN = np.sqrt(BARS_PER_DAY * 365.0)
FEE = 0.0005  # 0.05% per side (trivial-baseline turnover fee)
HORIZONS = {"5d": 15, "21d": 63, "50d": 150}  # bars

# v1 baseline triple-barrier params (from run_baseline_v186.py)
TP_PCT = 8.0
SL_PCT = 4.0
TIMEOUT_BARS = 21  # 10080 min / 480 min


def load_is(sym: str) -> pd.DataFrame:
    df = pd.read_csv(f"data/{sym}/8h.csv")
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
    df = df.sort_values("open_time").reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, f"{sym} OOS leak!"
    for c in ("open", "high", "low", "close"):
        df[c] = df[c].astype(float)
    return df


# ---------------------------------------------------------------------------
# GATE 1 — trivial TS-momentum Sharpe (turnover-aware fee)
# ---------------------------------------------------------------------------
def trivial_mom_sharpe(close: pd.Series, n: int) -> tuple[float, int]:
    mom = close.pct_change(n)
    pos = np.sign(mom).shift(1)  # known at bar t
    bar_ret = close.pct_change()
    turnover = pos.diff().abs().fillna(0.0)
    net = (pos * bar_ret - FEE * turnover).dropna()
    if net.std(ddof=1) == 0 or len(net) < 30:
        return float("nan"), 0
    return float(net.mean() / net.std(ddof=1) * ANN), int(turnover.gt(0.0).sum())


# ---------------------------------------------------------------------------
# Triple-barrier directional label (first-hit), IS-only
# ---------------------------------------------------------------------------
def triple_barrier_label(df: pd.DataFrame) -> np.ndarray:
    """Return +1/-1 directional label per bar based on which barrier a LONG hits.

    Faithful to labeling.py: for each bar, the LONG position is scanned forward
    up to TIMEOUT_BARS. TP at +TP_PCT, SL at -SL_PCT (intrabar high/low). The
    label sign is +1 if the long outcome PnL >= the short outcome PnL, else -1
    (the optimizer picks the better direction). Pending/end-of-data bars are NaN.
    """
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    close = df["close"].to_numpy()
    n = len(df)
    labels = np.full(n, np.nan)

    for i in range(n):
        entry = close[i]
        if entry <= 0:
            continue
        last = min(i + TIMEOUT_BARS, n - 1)
        if last <= i:
            continue  # not enough forward data -> NaN (no leak past end)
        long_tp = entry * (1 + TP_PCT / 100.0)
        long_sl = entry * (1 - SL_PCT / 100.0)
        short_tp = entry * (1 - TP_PCT / 100.0)
        short_sl = entry * (1 + SL_PCT / 100.0)

        long_pnl = None
        short_pnl = None
        for j in range(i + 1, last + 1):
            hj, lj = high[j], low[j]
            # LONG outcome (first hit)
            if long_pnl is None:
                if lj <= long_sl:
                    long_pnl = -SL_PCT
                elif hj >= long_tp:
                    long_pnl = TP_PCT
            # SHORT outcome (first hit): TP when price falls, SL when price rises
            if short_pnl is None:
                if hj >= short_sl:
                    short_pnl = -SL_PCT
                elif lj <= short_tp:
                    short_pnl = TP_PCT
            if long_pnl is not None and short_pnl is not None:
                break
        # timeout -> realized forward return
        fwd = (close[last] / entry - 1.0) * 100.0
        if long_pnl is None:
            long_pnl = fwd
        if short_pnl is None:
            short_pnl = -fwd
        labels[i] = 1.0 if long_pnl >= short_pnl else -1.0
    return labels


# ---------------------------------------------------------------------------
# Candidate cheap feature signals (IS-only, past-only)
# ---------------------------------------------------------------------------
def rsi_series(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    return 100.0 - 100.0 / (1.0 + rs)


def natr(df: pd.DataFrame, period: int = 30) -> pd.Series:
    h, lo, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - lo), (h - pc).abs(), (lo - pc).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1.0 / 14.0, adjust=False, min_periods=14).mean()
    return (atr / c * 100.0).rolling(period).mean()


def bb_bandwidth(close: pd.Series, period: int = 20, k: float = 2.0) -> pd.Series:
    ma = close.rolling(period).mean()
    sd = close.rolling(period).std(ddof=0)
    return (2 * k * sd) / ma  # (upper - lower) / mid


def candidate_features(df: pd.DataFrame) -> dict[str, pd.Series]:
    close = df["close"]
    return {
        "ret_5d": close.pct_change(15),
        "ret_21d": close.pct_change(63),
        "rsi_14": rsi_series(close, 14),
        "natr_30": natr(df, 30),
        "vol_bb_bandwidth": bb_bandwidth(close, 20, 2.0),
        # oi_delta: SKIPPED — no open-interest data for UNIUSDT (klines only)
    }


# ---------------------------------------------------------------------------
# GATE 2 TERTIARY — return autocorr
# ---------------------------------------------------------------------------
def autocorr_mag(close: pd.Series) -> dict:
    ret = close.pct_change().dropna()
    a1, a3, a7 = ret.autocorr(1), ret.autocorr(3), ret.autocorr(7)
    return {
        "ac_lag1": float(a1),
        "ac_lag3": float(a3),
        "ac_lag7": float(a7),
        "mag": float(max(abs(a1), abs(a3), abs(a7))),
    }


def main() -> None:
    print("=" * 72)
    print(f"iter-v1/085 STRUCTURE PRE-SCREEN — {SYM}")
    print("IS window: open_time < 2025-03-24 (OOS_CUTOFF_DATE)")
    print("=" * 72)

    df = load_is(SYM)
    is_years = (df["open_time"].max() - df["open_time"].min()) / 1000 / 86400 / 365.25
    print(f"IS bars: {len(df)}  IS years (first->last bar): {is_years:.2f}")
    print(f"IS start: {pd.to_datetime(df['open_time'].iloc[0], unit='ms', utc=True).date()}")
    print(f"IS end:   {pd.to_datetime(df['open_time'].iloc[-1], unit='ms', utc=True).date()}")
    full_years = 4.51  # computed earlier: 2020-09-18 -> 2025-03-24
    gate_4y = full_years >= 4.0
    print(f">=4y data gate: {full_years:.2f}y -> {'PASS' if gate_4y else 'FAIL'}")

    close = df["close"]

    # ---- GATE 1 ----
    print("\n[GATE 1] TRIVIAL TS-MOMENTUM SHARPE (fee-adj, turnover-aware)")
    print(f"  {'Horizon':<8}{'Bars':>6}{'Sharpe':>10}{'Changes':>10}")
    sh = {}
    for lbl, nb in HORIZONS.items():
        s, nc = trivial_mom_sharpe(close, nb)
        sh[lbl] = s
        print(f"  {lbl:<8}{nb:>6}{s:>+10.3f}{nc:>10}")
    triv_min = float(np.nanmin(list(sh.values())))
    gate1 = triv_min <= 0.15
    print(f"  Min-across-horizon: {triv_min:+.3f}  (gate threshold <= +0.15)")
    print(f"  GATE 1: {'PASS' if gate1 else 'FAIL'}")

    # ---- GATE 2 SECONDARY ----
    print("\n[GATE 2 SECONDARY] MAX SINGLE-FEATURE-vs-LABEL |IC| (Spearman, IS-only)")
    labels = triple_barrier_label(df)
    feats = candidate_features(df)
    lab_s = pd.Series(labels, index=df.index)
    n_valid_lab = int(np.isfinite(labels).sum())
    print(f"  triple-barrier label: {n_valid_lab} valid bars "
          f"(long={int((lab_s==1).sum())}, short={int((lab_s==-1).sum())}, "
          f"frac_long={float((lab_s==1).mean()):.3f})")
    ics = {}
    for name, ser in feats.items():
        m = ser.notna() & lab_s.notna()
        if m.sum() < 100:
            ics[name] = float("nan")
            continue
        rho, _ = spearmanr(ser[m].to_numpy(), lab_s[m].to_numpy())
        ics[name] = float(rho)
    print(f"  {'Feature':<18}{'IC':>10}{'|IC|':>10}{'n':>8}")
    for name, rho in ics.items():
        nn = int((feats[name].notna() & lab_s.notna()).sum())
        print(f"  {name:<18}{rho:>+10.4f}{abs(rho):>10.4f}{nn:>8}")
    max_ic = float(np.nanmax([abs(v) for v in ics.values()]))
    print(f"  MAX |IC|: {max_ic:.4f}  (gate threshold >= 0.04)")
    gate2_secondary = max_ic >= 0.04
    print(f"  GATE 2 SECONDARY: {'PASS' if gate2_secondary else 'FAIL'}")

    # ---- GATE 2 TERTIARY ----
    print("\n[GATE 2 TERTIARY] RETURN AUTOCORRELATION (informational)")
    ac = autocorr_mag(close)
    print(f"  ac_lag1={ac['ac_lag1']:+.4f}  ac_lag3={ac['ac_lag3']:+.4f}  "
          f"ac_lag7={ac['ac_lag7']:+.4f}")
    print(f"  autocorr_mag (max|.|): {ac['mag']:.4f}  (informational threshold >= 0.03)")

    # ---- VERDICT ----
    if max_ic >= 0.06:
        verdict = "STRONG"
    elif max_ic >= 0.04:
        verdict = "MODERATE"
    elif max_ic >= 0.02:
        verdict = "WEAK"
    else:
        verdict = "NOISE"
    print("\n" + "=" * 72)
    print(f"VERDICT: structure_signal = {verdict}")
    print(f"  trivial_baseline_min = {triv_min:+.4f}")
    print(f"  max_feature_label_ic = {max_ic:.4f}")
    print(f"  autocorr_mag         = {ac['mag']:.4f}")
    print(f"  gate1_pass           = {gate1}")
    print("=" * 72)

    # write CSV
    out = pd.DataFrame([{
        "symbol": SYM,
        "is_years": round(is_years, 3),
        "full_years": full_years,
        "triv_5d": round(sh["5d"], 4),
        "triv_21d": round(sh["21d"], 4),
        "triv_50d": round(sh["50d"], 4),
        "trivial_baseline_min": round(triv_min, 4),
        "gate1_pass": gate1,
        "ic_ret_5d": round(ics.get("ret_5d", float("nan")), 4),
        "ic_ret_21d": round(ics.get("ret_21d", float("nan")), 4),
        "ic_rsi_14": round(ics.get("rsi_14", float("nan")), 4),
        "ic_natr_30": round(ics.get("natr_30", float("nan")), 4),
        "ic_vol_bb_bandwidth": round(ics.get("vol_bb_bandwidth", float("nan")), 4),
        "max_feature_label_ic": round(max_ic, 4),
        "gate2_secondary_pass": gate2_secondary,
        "ac_lag1": round(ac["ac_lag1"], 4),
        "ac_lag3": round(ac["ac_lag3"], 4),
        "ac_lag7": round(ac["ac_lag7"], 4),
        "autocorr_mag": round(ac["mag"], 4),
        "structure_signal": verdict,
    }])
    out.to_csv("analysis/iteration_v1-085/uni_prescreen_results.csv", index=False)
    print("Wrote analysis/iteration_v1-085/uni_prescreen_results.csv")


if __name__ == "__main__":
    main()
