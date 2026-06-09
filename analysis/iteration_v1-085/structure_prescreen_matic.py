"""iter-v1/085 STRUCTURE PRE-SCREEN — MATICUSDT (the /084 anti-CRV-trap gate).

Refined selector (feedback_v1_negative_trivial_baseline_selector), IS-ONLY:
  GATE 1  trivial-momentum baseline (min-horizon over 5d/21d/50d, fee-adj) <= +0.15
  GATE 2 PRIMARY    fast single-seed LightGBM probe IS Sharpe >= +0.30
  GATE 2 SECONDARY  max single-feature-vs-LABEL |IC| (Spearman) >= 0.04  [KEY structure test]
  GATE 2 TERTIARY   return-autocorr magnitude >= 0.03  (informational)

structure_signal: STRONG >=0.06 | MODERATE 0.04-0.06 | WEAK 0.02-0.04 | NOISE <0.02 (CRV trap)

IS-ONLY DISCIPLINE: every stat uses only bars with open_time < OOS_CUTOFF (2025-03-24).
Asserted at runtime. Triple-barrier label uses PAST-ONLY EWMA sigma_t (no labeling-window std).

NOTE ON MATIC: data is frozen at 2024-09-11 (delisted; MATIC -> POL migration). This is
~194 days BEFORE the OOS cutoff, so the symbol has ZERO OOS coverage and <4y data.
This script runs the full structure diagnostic on the IS data anyway to DOCUMENT the
finding, but the data-coverage failure is dispositive regardless of the structure verdict.
"""

import datetime as dt

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

OOS_CUTOFF_MS = int(dt.datetime(2025, 3, 24, tzinfo=dt.timezone.utc).timestamp() * 1000)
BARS_PER_DAY = 3
ANN = np.sqrt(BARS_PER_DAY * 365.0)
FEE = 0.0005
HORIZONS = {"5d": 15, "21d": 63, "50d": 150}
MIN_IS_YEARS = 4.0
SYM = "MATICUSDT"

# Triple-barrier params (v1 convention): horizon, TP/SL in units of past-only EWMA sigma
TB_HORIZON = 15  # 5d at 8h
TB_TP = 2.0
TB_SL = 2.0
SIGMA_SPAN = 50  # EWMA span for past-only volatility


def load_is(sym: str) -> pd.DataFrame:
    df = pd.read_csv(f"data/{sym}/8h.csv")
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
    df = df.sort_values("open_time").reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, f"{sym} OOS leak!"
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype(float)
    return df


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


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def natr(df: pd.DataFrame, n: int = 14, roll: int = 30) -> pd.Series:
    h, low, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - low), (h - pc).abs(), (low - pc).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    return ((atr / c) * 100.0).rolling(roll).mean()


def bb_bandwidth(close: pd.Series, n: int = 20) -> pd.Series:
    ma = close.rolling(n).mean()
    sd = close.rolling(n).std(ddof=0)
    return (2 * 2 * sd) / ma  # (upper-lower)/mid = 4*sd/ma


def triple_barrier_sign(df: pd.DataFrame) -> pd.Series:
    """Forward triple-barrier label sign with PAST-ONLY EWMA sigma_t.

    For each bar t: sigma_t = EWMA std of past bar returns (shifted, no look-ahead).
    Look forward up to TB_HORIZON bars; +1 if upper barrier (TP*sigma) hit first,
    -1 if lower (SL*sigma) hit first, sign(terminal return) on timeout.
    Returns label aligned at decision bar t (IS-only input already).
    """
    c = df["close"].to_numpy()
    ret = df["close"].pct_change()
    sigma = ret.ewm(span=SIGMA_SPAN, adjust=False).std().shift(1).to_numpy()  # past-only
    n = len(c)
    lab = np.full(n, np.nan)
    for t in range(n):
        s = sigma[t]
        if not np.isfinite(s) or s <= 0:
            continue
        if t + 1 >= n:
            continue
        up = c[t] * (1 + TB_TP * s)
        dn = c[t] * (1 - TB_SL * s)
        end = min(t + TB_HORIZON, n - 1)
        hit = 0
        for k in range(t + 1, end + 1):
            if c[k] >= up:
                hit = 1
                break
            if c[k] <= dn:
                hit = -1
                break
        if hit == 0:
            hit = int(np.sign(c[end] - c[t]))
        lab[t] = hit
    return pd.Series(lab, index=df.index)


def main() -> None:
    df = load_is(SYM)
    is_years = (df["open_time"].max() - df["open_time"].min()) / 1000 / 86400 / 365.25
    n_bars = len(df)
    last_date = dt.datetime.fromtimestamp(
        df["open_time"].max() / 1000, tz=dt.timezone.utc
    ).date()
    oos_date = dt.datetime.fromtimestamp(
        OOS_CUTOFF_MS / 1000, tz=dt.timezone.utc
    ).date()
    has_oos_coverage = df["open_time"].max() >= OOS_CUTOFF_MS  # always False if delisted pre-OOS
    print(f"=== {SYM} structure pre-screen (IS-only) ===")
    print(f"data_years={is_years:.3f}  n_bars={n_bars}  last_bar={last_date}  oos_cutoff={oos_date}")
    print(f">=4y? {is_years >= MIN_IS_YEARS}   has any OOS bars? {has_oos_coverage}")

    close = df["close"]

    # ---- GATE 1: trivial momentum baseline ----
    s = {k: trivial_mom_sharpe(close, n) for k, n in HORIZONS.items()}
    trivial_min = float(np.nanmin(list(s.values())))
    gate1_pass = trivial_min <= 0.15
    print("\n--- GATE 1 trivial momentum ---")
    for k in HORIZONS:
        print(f"  {k:>4}: Sharpe {s[k]:+.3f}")
    print(f"  MIN = {trivial_min:+.3f}   gate1_pass(<=+0.15) = {gate1_pass}")

    # ---- GATE 2 SECONDARY: max single-feature-vs-LABEL |IC| (KEY) ----
    label = triple_barrier_sign(df)
    feats = {
        "ret_5d": close.pct_change(15),
        "ret_21d": close.pct_change(63),
        "rsi_14": rsi(close, 14),
        "natr_30": natr(df, 14, 30),
        "vol_bb_bandwidth": bb_bandwidth(close, 20),
        "ret_50d": close.pct_change(150),
        "taker_buy_ratio": (
            df["taker_buy_volume"].astype(float)
            / df["volume"].replace(0, np.nan)
        ),
    }
    # NOTE: oi_delta unavailable for MATIC (no OI history archived); omitted.
    print("\n--- GATE 2 SECONDARY  feature-vs-LABEL |IC| (Spearman, IS-only) ---")
    ics = {}
    valid_label = label.dropna()
    for name, fseries in feats.items():
        merged = pd.concat([fseries, label], axis=1).dropna()
        if len(merged) < 100:
            ics[name] = float("nan")
            print(f"  {name:>17}: n<100  skip")
            continue
        rho, _ = spearmanr(merged.iloc[:, 0], merged.iloc[:, 1])
        ics[name] = abs(float(rho))
        print(f"  {name:>17}: |IC| {abs(rho):.4f}  (n={len(merged)})")
    max_ic = float(np.nanmax(list(ics.values())))
    argmax_ic = max(ics, key=lambda k: (ics[k] if np.isfinite(ics[k]) else -1))
    print(f"  label coverage: {len(valid_label)}/{n_bars} bars labeled")
    print(f"  MAX |IC| = {max_ic:.4f}  (from {argmax_ic})")

    # ---- GATE 2 TERTIARY: return autocorr magnitude ----
    r = close.pct_change().dropna()
    acf = {lag: float(r.autocorr(lag)) for lag in (1, 3, 7)}
    autocorr_mag = max(abs(v) for v in acf.values())
    print("\n--- GATE 2 TERTIARY return autocorr ---")
    for lag, v in acf.items():
        print(f"  acf_{lag}: {v:+.4f}")
    print(f"  autocorr_mag = {autocorr_mag:.4f}  (>=0.03 informational)")

    # ---- structure_signal verdict ----
    if max_ic >= 0.06:
        sig = "STRONG"
    elif max_ic >= 0.04:
        sig = "MODERATE"
    elif max_ic >= 0.02:
        sig = "WEAK"
    else:
        sig = "NOISE"

    # Data-coverage override: <4y OR no OOS bars => structurally unusable as specialist.
    coverage_ok = (is_years >= MIN_IS_YEARS) and has_oos_coverage

    print("\n=== VERDICT ===")
    print(f"trivial_baseline_min = {trivial_min:+.3f}")
    print(f"max_feature_label_ic = {max_ic:.4f}")
    print(f"autocorr_mag         = {autocorr_mag:.4f}")
    print(f"gate1_pass           = {gate1_pass}")
    print(f"structure_signal(IC) = {sig}")
    print(f"coverage_ok(>=4y & has OOS) = {coverage_ok}")

    pd.DataFrame(
        [
            dict(
                symbol=SYM,
                data_years=round(is_years, 3),
                n_bars=n_bars,
                last_bar=str(last_date),
                has_oos_coverage=has_oos_coverage,
                s5=round(s["5d"], 3),
                s21=round(s["21d"], 3),
                s50=round(s["50d"], 3),
                trivial_min=round(trivial_min, 3),
                gate1_pass=gate1_pass,
                max_feature_label_ic=round(max_ic, 4),
                max_ic_feature=argmax_ic,
                autocorr_mag=round(autocorr_mag, 4),
                structure_signal=sig,
                coverage_ok=coverage_ok,
            )
        ]
    ).to_csv("analysis/iteration_v1-085/structure_prescreen_matic.csv", index=False)
    print("\nwrote analysis/iteration_v1-085/structure_prescreen_matic.csv")


if __name__ == "__main__":
    main()
