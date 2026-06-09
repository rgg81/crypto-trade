"""iter-v1/085 STRUCTURE PRE-SCREEN — GRTUSDT (the /084 anti-CRV-trap gate).

Applies the refined negative-trivial-baseline selector
(feedback_v1_negative_trivial_baseline_selector) IS-ONLY (klines strictly
before OOS_CUTOFF 2025-03-24):

  GATE 1 — trivial-momentum baseline: min-horizon (5d/21d/50d) fee-adj IS Sharpe.
           gate1_pass = (min <= +0.15). Avoids the FIL clean-trend trap.
  GATE 2 SECONDARY (KEY) — max single-feature-vs-triple-barrier-LABEL |IC|
           (Spearman, IS-only). The anti-CRV-trap structure test. CRV cratered
           because its near-zero trivial baseline was PURE NOISE (no IC structure),
           not edge headroom.
  GATE 2 TERTIARY — return autocorr magnitude max(|acf_1|,|acf_3|,|acf_7|).

structure_signal verdict on max |IC|:
  STRONG   >= 0.06
  MODERATE 0.04 - 0.06
  WEAK     0.02 - 0.04
  NOISE    < 0.02  (the CRV trap)

LABEL: reuse the production triple-barrier label_trades() with the LightGbmStrategy
defaults (tp=4.0%, sl=2.0%, timeout=4320min=9 bars at 8h). Label sign is the
+1/-1 long/short outcome the model is actually trained on.

IS-ONLY DISCIPLINE: every number uses only bars with open_time < OOS_CUTOFF.
Asserted at runtime. All features past-only (.shift on rolling stats where the
bar's own close would otherwise leak into its own decision).
"""

import datetime as dt

import numpy as np
import pandas as pd
from scipy import stats

from crypto_trade.strategies.ml.labeling import label_trades

OOS_CUTOFF_MS = int(dt.datetime(2025, 3, 24, tzinfo=dt.timezone.utc).timestamp() * 1000)
BARS_PER_DAY = 3  # 8h cadence
ANN = np.sqrt(BARS_PER_DAY * 365.0)
FEE = 0.0005  # 0.05% per side (turnover-aware)
HORIZONS = {"5d": 15, "21d": 63, "50d": 150}  # bars
SYMBOL = "GRTUSDT"
MIN_IS_YEARS = 4.0

# Production LightGbmStrategy label defaults
LABEL_TP_PCT = 4.0
LABEL_SL_PCT = 2.0
LABEL_TIMEOUT_MIN = 4320  # 9 bars at 8h


def load_is(sym: str) -> pd.DataFrame:
    df = pd.read_csv(f"data/{sym}/8h.csv")
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
    df = df.sort_values("open_time").reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, f"{sym} OOS leak!"
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = df[col].astype(float)
    df["symbol"] = sym
    return df


# ---------- GATE 1: trivial TS-momentum baseline ----------
def trivial_mom_sharpe(close: pd.Series, n: int) -> float:
    mom = close.pct_change(n)
    pos = np.sign(mom).shift(1)  # decide at bar t, hold over t->t+1
    bar_ret = close.pct_change()
    gross = pos * bar_ret
    turnover = pos.diff().abs().fillna(0.0)
    net = (gross - FEE * turnover).dropna()
    if net.std(ddof=1) == 0 or len(net) < 30:
        return float("nan")
    return float(net.mean() / net.std(ddof=1) * ANN)


# ---------- GATE 2 SECONDARY: feature-vs-label IC ----------
def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0.0)
    down = -delta.clip(upper=0.0)
    roll_up = up.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    roll_down = down.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = roll_up / roll_down.replace(0.0, np.nan)
    return 100.0 - 100.0 / (1.0 + rs)


def natr(df: pd.DataFrame, period: int = 14, window: int = 30) -> pd.Series:
    h, lo, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - lo), (h - pc).abs(), (lo - pc).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    natr_series = (atr / c) * 100.0
    return natr_series.rolling(window).mean()


def bb_bandwidth(close: pd.Series, window: int = 20, k: float = 2.0) -> pd.Series:
    ma = close.rolling(window).mean()
    sd = close.rolling(window).std(ddof=0)
    upper = ma + k * sd
    lower = ma - k * sd
    return (upper - lower) / ma.replace(0.0, np.nan)


def build_candidate_features(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Cheap candidate signals. All past-only at decision time.

    A feature value at row i must be computable from data with open_time <= i's
    open_time (the bar-close of bar i is known at decision time for bar i->i+1).
    pct_change(n) at i uses closes [i-n .. i] — all <= bar i, no leak.
    """
    close = df["close"]
    feats: dict[str, pd.Series] = {}
    feats["ret_5d"] = close.pct_change(15)  # 5d = 15 bars
    feats["ret_21d"] = close.pct_change(63)  # 21d = 63 bars
    feats["rsi_14"] = rsi(close, 14)
    feats["natr_30"] = natr(df, 14, 30)
    feats["vol_bb_bandwidth"] = bb_bandwidth(close, 20, 2.0)
    # OI not available in 8h klines CSV (no open-interest column) -> skip oi_delta.
    return feats


def compute_label_signs(df: pd.DataFrame) -> np.ndarray:
    """Production triple-barrier label sign (+1 long / -1 short) per row.

    Uses label_trades with LightGbmStrategy defaults. Candidate indices = all
    rows that have enough forward bars for the timeout scan; rows near the IS
    tail with insufficient forward data resolve to timeout/forward-return sign
    (still IS-only since we never read past OOS_CUTOFF).
    """
    master = df[
        ["symbol", "open_time", "close_time", "open", "high", "low", "close"]
    ].reset_index(drop=True)
    candidate_indices = np.arange(len(master), dtype=np.intp)
    labels, _w, _lp, _sp = label_trades(
        master=master,
        candidate_indices=candidate_indices,
        tp_pct=LABEL_TP_PCT,
        sl_pct=LABEL_SL_PCT,
        timeout_minutes=LABEL_TIMEOUT_MIN,
        fee_pct=0.1,
        label_mode="triple_barrier",
    )
    return labels


def spearman_ic(feature: pd.Series, label_sign: np.ndarray) -> tuple[float, int]:
    f = feature.to_numpy(dtype=float)
    mask = np.isfinite(f) & np.isin(label_sign, (-1, 1))
    if mask.sum() < 100:
        return float("nan"), int(mask.sum())
    rho, _p = stats.spearmanr(f[mask], label_sign[mask].astype(float))
    return float(rho), int(mask.sum())


# ---------- GATE 2 TERTIARY: return autocorr ----------
def return_autocorr(close: pd.Series) -> dict[int, float]:
    r = close.pct_change().dropna()
    out = {}
    for lag in (1, 3, 7):
        out[lag] = float(r.autocorr(lag=lag))
    return out


def verdict_structure(max_abs_ic: float) -> str:
    if not np.isfinite(max_abs_ic):
        return "NOISE"
    if max_abs_ic >= 0.06:
        return "STRONG"
    if max_abs_ic >= 0.04:
        return "MODERATE"
    if max_abs_ic >= 0.02:
        return "WEAK"
    return "NOISE"


def main() -> None:
    df = load_is(SYMBOL)
    is_years = (df["open_time"].max() - df["open_time"].min()) / 1000 / 86400 / 365.25
    n_bars = len(df)
    close = df["close"]

    print(f"=== {SYMBOL} STRUCTURE PRE-SCREEN (IS-only, < 2025-03-24) ===")
    print(f"IS years={is_years:.2f}  n_bars={n_bars}")
    print(f"data start={dt.datetime.utcfromtimestamp(df['open_time'].min()/1000):%Y-%m-%d}  "
          f"end={dt.datetime.utcfromtimestamp(df['open_time'].max()/1000):%Y-%m-%d}")

    data_ok = is_years >= MIN_IS_YEARS

    # GATE 1
    s = {k: trivial_mom_sharpe(close, n) for k, n in HORIZONS.items()}
    min_triv = float(np.nanmin(list(s.values())))
    gate1_pass = bool(min_triv <= 0.15)
    print("\n--- GATE 1: trivial TS-mom baseline (fee-adj, ann) ---")
    for k in HORIZONS:
        print(f"  triv_{k}: {s[k]:+.3f}")
    print(f"  MIN-horizon: {min_triv:+.3f}  -> gate1_pass={gate1_pass} (need <= +0.15)")

    # GATE 2 SECONDARY
    print("\n--- GATE 2 SECONDARY: feature-vs-LABEL |IC| (triple-barrier sign) ---")
    label_signs = compute_label_signs(df)
    n_long = int((label_signs == 1).sum())
    n_short = int((label_signs == -1).sum())
    print(f"  label balance: long={n_long}  short={n_short}  "
          f"(long share {n_long/(n_long+n_short):.3f})")
    feats = build_candidate_features(df)
    ic_rows = []
    for name, fs in feats.items():
        rho, n_used = spearman_ic(fs, label_signs)
        ic_rows.append((name, rho, abs(rho) if np.isfinite(rho) else np.nan, n_used))
        print(f"  {name:18s} IC={rho:+.4f}  |IC|={abs(rho):.4f}  n={n_used}")
    valid_abs = [r[2] for r in ic_rows if np.isfinite(r[2])]
    max_abs_ic = float(max(valid_abs)) if valid_abs else float("nan")
    best = max(
        (r for r in ic_rows if np.isfinite(r[2])), key=lambda r: r[2], default=None
    )
    print(f"  MAX |IC| = {max_abs_ic:.4f}"
          + (f" ({best[0]})" if best else ""))

    # GATE 2 TERTIARY
    print("\n--- GATE 2 TERTIARY: return autocorr ---")
    acf = return_autocorr(close)
    autocorr_mag = float(max(abs(acf[1]), abs(acf[3]), abs(acf[7])))
    for lag in (1, 3, 7):
        print(f"  acf_{lag}: {acf[lag]:+.4f}")
    print(f"  autocorr_mag (max|acf|) = {autocorr_mag:.4f}")

    sig = verdict_structure(max_abs_ic) if data_ok else "NOISE"
    print("\n=== VERDICT ===")
    print(f"  data_ok={data_ok}  gate1_pass={gate1_pass}  structure_signal={sig}")
    print(f"  trivial_baseline_min={min_triv:+.4f}")
    print(f"  max_feature_label_ic={max_abs_ic:.4f}")
    print(f"  autocorr_mag={autocorr_mag:.4f}")

    # write CSV
    out = pd.DataFrame(
        [
            dict(
                symbol=SYMBOL,
                is_years=round(is_years, 2),
                n_bars=n_bars,
                triv_5d=round(s["5d"], 4),
                triv_21d=round(s["21d"], 4),
                triv_50d=round(s["50d"], 4),
                trivial_baseline_min=round(min_triv, 4),
                gate1_pass=gate1_pass,
                max_feature_label_ic=round(max_abs_ic, 4),
                best_ic_feature=best[0] if best else "",
                acf_1=round(acf[1], 4),
                acf_3=round(acf[3], 4),
                acf_7=round(acf[7], 4),
                autocorr_mag=round(autocorr_mag, 4),
                structure_signal=sig,
            )
        ]
    )
    out.to_csv("analysis/iteration_v1-085/structure_prescreen_grt.csv", index=False)
    print("\nwrote analysis/iteration_v1-085/structure_prescreen_grt.csv")


if __name__ == "__main__":
    main()
