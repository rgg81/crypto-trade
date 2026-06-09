"""iter-v1/084 REFORMED symbol-selection EDA — trivial TS-momentum baseline.

Batch: ALGOUSDT, ETCUSDT, FTMUSDT, EGLDUSDT.

REFORMED SELECTION RULE (2026-06-09 user directive "option 3"):
The empirical predictor of ML edge headroom is the TRIVIAL-MOMENTUM BASELINE,
computed IS-ONLY (klines strictly before OOS_CUTOFF 2025-03-24). A symbol whose
trivial TS-momentum already prints a strongly POSITIVE Sharpe leaves the ML model
no headroom (the FIL/083 trap: trivial +1.45 -> ML -0.82). A symbol with a
NEGATIVE trivial baseline has room for ML to add edge (DOT/063, AAVE/078 both
had weak/negative trivial baselines and WORKED).

Pick the symbol with the MOST NEGATIVE min-across-horizon trivial Sharpe that
also has >=4y data and HIGH/MEDIUM headroom.

IS-ONLY DISCIPLINE: every Sharpe below uses only bars with open_time < OOS_CUTOFF.
Asserted at runtime (max open_time used < cutoff).

8h bars -> 3 bars/day. Daily-equivalent Sharpe = per-bar-Sharpe * sqrt(3*365).
Fee model: 0.05% per side, charged only on position CHANGES (turnover-aware),
so a buy-and-hold-direction streak is not over-penalized.
"""

import datetime as dt
import sys

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = int(
    dt.datetime(2025, 3, 24, tzinfo=dt.timezone.utc).timestamp() * 1000
)
BARS_PER_DAY = 3  # 8h cadence
ANN = np.sqrt(BARS_PER_DAY * 365.0)
FEE = 0.0005  # 0.05% per side
HORIZONS = {"5d": 15, "21d": 63, "50d": 150}  # bars
SYMBOLS = ["ALGOUSDT", "ETCUSDT", "FTMUSDT", "EGLDUSDT"]
MIN_IS_YEARS = 4.0
OUT_CSV = "analysis/iteration_v1-084/eda_results_algo_etc_ftm_egld.csv"


def load_is(sym: str) -> pd.DataFrame:
    df = pd.read_csv(f"data/{sym}/8h.csv")
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
    df = df.sort_values("open_time").reset_index(drop=True)
    # IS-only leakage assertion
    assert df["open_time"].max() < OOS_CUTOFF_MS, f"{sym} OOS leak!"
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    return df


def trivial_mom_sharpe(close: pd.Series, n: int) -> tuple[float, int]:
    """Long if ret_Nd>0 else short. Position applied to NEXT bar return.

    Turnover-aware fee: FEE*|pos_change| each bar (entry+exit each cost FEE).
    Returns (annualized daily-equiv Sharpe, n_position_changes).
    """
    mom = close.pct_change(n)
    pos = np.sign(mom).shift(1)  # decide at bar t, hold over t->t+1
    bar_ret = close.pct_change()  # return realized over current bar
    gross = pos * bar_ret
    turnover = pos.diff().abs().fillna(0.0)
    net = gross - FEE * turnover
    net = net.dropna()
    if net.std(ddof=1) == 0 or len(net) < 30:
        return float("nan"), 0
    sharpe = net.mean() / net.std(ddof=1) * ANN
    n_changes = int(turnover.fillna(0).gt(0).sum())
    return float(sharpe), n_changes


def natr30_p50(df: pd.DataFrame) -> float:
    """NATR = ATR(14) / close * 100, then 30-bar rolling, report median pct."""
    h, low, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - low), (h - pc).abs(), (low - pc).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    natr = (atr / c) * 100.0
    natr30 = natr.rolling(30).mean()
    return float(natr30.median())


def regime_tag(close: pd.Series) -> pd.Series:
    """Coarse 50-bar (~17d) trailing regime: bull/bear/chop via slope+vol."""
    ret50 = close.pct_change(50)
    vol50 = close.pct_change().rolling(50).std()
    # bull if ret50 > +1 vol-unit move, bear if < -1, else chop
    thr = vol50 * np.sqrt(50)
    tag = pd.Series("chop", index=close.index)
    tag[ret50 > thr] = "bull"
    tag[ret50 < -thr] = "bear"
    return tag


def per_regime_trivial(close: pd.Series, n: int) -> dict:
    mom = close.pct_change(n)
    pos = np.sign(mom).shift(1)
    bar_ret = close.pct_change()
    turnover = pos.diff().abs().fillna(0.0)
    net = (pos * bar_ret - FEE * turnover)
    tag = regime_tag(close).shift(1)  # regime known at decision time
    out = {}
    for r in ["bull", "bear", "chop"]:
        seg = net[(tag == r)].dropna()
        if len(seg) >= 30 and seg.std(ddof=1) > 0:
            out[r] = float(seg.mean() / seg.std(ddof=1) * ANN)
        else:
            out[r] = float("nan")
    return out


def verdict(min_sharpe: float, is_years: float) -> str:
    if is_years < MIN_IS_YEARS:
        return "NONE"
    if min_sharpe < -0.30:
        return "HIGH"
    if min_sharpe <= 0.20:
        return "MEDIUM"
    if min_sharpe <= 0.80:
        return "LOW"
    return "NONE"


def main() -> None:
    symbols = sys.argv[1:] if len(sys.argv) > 1 else SYMBOLS
    rows = []
    for sym in symbols:
        df = load_is(sym)
        is_years = (df["open_time"].max() - df["open_time"].min()) / 1000 / 86400 / 365.25
        close = df["close"]
        sharpes = {}
        changes = {}
        for label, n in HORIZONS.items():
            s, nc = trivial_mom_sharpe(close, n)
            sharpes[label] = s
            changes[label] = nc
        min_s = np.nanmin(list(sharpes.values()))
        natr = natr30_p50(df)
        regimes = per_regime_trivial(close, HORIZONS["21d"])
        v = verdict(min_s, is_years)
        rows.append(
            dict(
                symbol=sym,
                data_years=round(is_years, 2),
                n_bars=len(df),
                s5=round(sharpes["5d"], 3),
                s21=round(sharpes["21d"], 3),
                s50=round(sharpes["50d"], 3),
                min_sharpe=round(float(min_s), 3),
                natr30_p50=round(natr, 3),
                reg_bull=round(regimes["bull"], 2),
                reg_bear=round(regimes["bear"], 2),
                reg_chop=round(regimes["chop"], 2),
                chg21=changes["21d"],
                verdict=v,
            )
        )
    res = pd.DataFrame(rows)
    print(res.to_string(index=False))
    res.to_csv(OUT_CSV, index=False)

    # Pick: most-negative min_sharpe among >=4y + HIGH/MEDIUM
    elig = res[(res["data_years"] >= MIN_IS_YEARS) & (res["verdict"].isin(["HIGH", "MEDIUM"]))]
    if len(elig):
        best = elig.sort_values("min_sharpe").iloc[0]
        print(f"\nBEST = {best['symbol']}  min_sharpe={best['min_sharpe']}  verdict={best['verdict']}")
    else:
        print("\nNo eligible symbol in this batch (all <4y or no headroom).")


if __name__ == "__main__":
    main()
