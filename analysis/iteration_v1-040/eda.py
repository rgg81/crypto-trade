"""iter-v1/040 EDA — DROP basis_zscore_30 (INERT-3-consec) + ADD regime_momentum_signed_5d.

F-AXIS #1: FEATURE-ENGINEERING family per /038 closeout LM Master Rec 1.

Mechanism:
- DROP basis_zscore_30 (ranks 25-32 across /034/037/038 portfolio + 4 cohorts;
  3-consecutive INERT pattern; feedback_v3_inert_features_at_higher_budget.md).
- ADD regime_momentum_signed_5d = stat_log_return_5 * sign(hurst_100 - 0.5)
  (v3 precedent /025 PROMISING-CLEAN; /028 CONFIRMATION-MERGE; first regime
  composed feature in v3 BASELINE_V3.md).

CRITICAL: v1 features parquet does NOT contain hurst_100 OR ret_5d. We compute
both inline using:
- ret_5d := stat_log_return_5 (present in v1 parquet; 5-bar log return at 8h
  cadence = 40h, which differs from v3's 15-bar/120h). NOTE: same NAME for
  the lookback parameter but the v3 ret_5d is 15 bars (5 calendar days). For
  v1 we instantiate ret_5d AT THE 15-BAR HORIZON via inline shift(15) to match
  the v3 mechanism exactly.
- hurst_100 := computed inline via R/S rolling Hurst (matches v3 regime_v3.py
  _hurst_rs / _rolling_hurst implementation byte-for-byte).

Symbols (v1 universe): BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT.
IS-only: close_time < OOS_CUTOFF_DATE = 2025-03-24.

Output:
- analysis/iteration_v1-040/distribution_per_symbol.csv
- analysis/iteration_v1-040/adf_per_symbol.csv
- analysis/iteration_v1-040/ic_matrix.csv
- analysis/iteration_v1-040/basis_z30_importance_history.csv

QR + Critic interpretive notes per feedback_v3_engineered_feature_pivot.md:
- The composed feature mechanically correlates with its primitives by
  construction. |IC| against ret_5d (the value primitive) is expected ~0.6-0.9.
  This is NOT multicollinearity; it is algebraic structure of x = a * sign(b - 0.5).
  IC carve-out applies; Critic Check 4 uses IMPORTANCE >= 30 threshold not
  |IC| < 0.50 hard gate.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# ------------------------------------------------------------------
# CONSTANTS — match production v1 universe and OOS cutoff
# ------------------------------------------------------------------
SYMBOLS = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT")
OOS_CUTOFF_MS = pd.Timestamp("2025-03-24", tz="UTC").value // 10**6  # ns -> ms
HURST_WINDOW = 100  # matches v3 hurst_100 EXACTLY
RET_HORIZON = 15  # 15 bars * 8h = 120h = 5 days — matches v3 ret_5d EXACTLY


# ------------------------------------------------------------------
# v3-IDENTICAL rolling Hurst implementation (R/S method)
# Copied from src/crypto_trade/features_v3/regime_v3.py:34-75 BYTE-FOR-BYTE.
# ------------------------------------------------------------------
def _hurst_rs(window: np.ndarray) -> float:
    n = len(window)
    if n < 20:
        return np.nan
    lags = [5, 10, 20, 30, 50, 80]
    lags = [lag for lag in lags if lag < n]
    if len(lags) < 3:
        return np.nan
    rs_values: list[float] = []
    log_lags: list[float] = []
    for lag in lags:
        chunks = n // lag
        if chunks < 1:
            continue
        r_list: list[float] = []
        for i in range(chunks):
            chunk = window[i * lag : (i + 1) * lag]
            mean = chunk.mean()
            devs = chunk - mean
            cumdev = np.cumsum(devs)
            r = cumdev.max() - cumdev.min()
            s = chunk.std(ddof=1)
            if s > 0 and np.isfinite(r):
                r_list.append(r / s)
        if r_list:
            rs_values.append(np.mean(r_list))
            log_lags.append(np.log(lag))
    if len(rs_values) < 3:
        return np.nan
    log_rs = np.log(rs_values)
    slope, _ = np.polyfit(log_lags, log_rs, 1)
    return float(slope)


def _rolling_hurst(log_close: pd.Series, window: int) -> pd.Series:
    values = log_close.to_numpy()
    out = np.full(len(values), np.nan, dtype=np.float64)
    for i in range(window, len(values) + 1):
        out[i - 1] = _hurst_rs(values[i - window : i])
    return pd.Series(out, index=log_close.index)


# ------------------------------------------------------------------
# ADF helper (basic implementation; statsmodels is in deps)
# ------------------------------------------------------------------
def adf_pvalue(x: pd.Series) -> float:
    from statsmodels.tsa.stattools import adfuller

    x = x.dropna().to_numpy()
    if len(x) < 100:
        return np.nan
    return float(adfuller(x, autolag="AIC")[1])


# ------------------------------------------------------------------
# Compute composed feature per symbol
# ------------------------------------------------------------------
def compute_for_symbol(parquet_path: Path) -> dict:
    df = pd.read_parquet(parquet_path)
    # IS-only filter — close_time < OOS_CUTOFF
    df = df[df["close_time"] < OOS_CUTOFF_MS].copy()
    n_total = len(df)

    # Compute ret_5d = log(close_t) - log(close_{t-15}) -- v3-identical
    close = df["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    ret_5d = log_close - log_close.shift(RET_HORIZON)

    # Compute hurst_100 inline (v3-identical R/S rolling)
    hurst_100 = _rolling_hurst(log_close, HURST_WINDOW)

    # Compose: regime_momentum_signed_5d = ret_5d * sign(hurst_100 - 0.5)
    sign_h = np.sign(hurst_100 - 0.5)
    sign_h = sign_h.replace(0.0, np.nan)  # treat pure-RW as no-signal
    rms_5d = ret_5d * sign_h
    rms_5d = rms_5d.dropna()

    # Distribution stats
    pct_pos = float((sign_h > 0).sum() / sign_h.notna().sum())
    pct_neg = float((sign_h < 0).sum() / sign_h.notna().sum())
    autocorr_1 = float(rms_5d.autocorr(lag=1))
    adf_p = adf_pvalue(rms_5d)

    dist = {
        "symbol": parquet_path.stem.replace("_8h_features", ""),
        "n_bars_is": n_total,
        "n_valid_rms5d": int(rms_5d.notna().sum()),
        "mean": float(rms_5d.mean()),
        "std": float(rms_5d.std()),
        "min": float(rms_5d.min()),
        "max": float(rms_5d.max()),
        "pct_trending": pct_pos,  # hurst > 0.5
        "pct_meanrev": pct_neg,  # hurst < 0.5
        "autocorr_lag1": autocorr_1,
        "adf_pvalue": adf_p,
        "hurst_mean": float(hurst_100.dropna().mean()),
        "hurst_std": float(hurst_100.dropna().std()),
    }

    # IC matrix vs incumbents (using IS subset; align on rms_5d valid idx)
    incumbents = [
        "stat_return_5",  # closest existing v1 primitive (numerator-like; 5-bar pct return)
        "stat_log_return_5",  # the v3-equivalent ret_5d primitive in v1 (40h horizon)
        "vol_atr_14",
        "trend_aroon_osc_50",
        "stat_autocorr_lag5",
        "mom_rsi_14",
        "trend_adx_14",
    ]
    ic_row = {"symbol": dist["symbol"]}
    valid_idx = rms_5d.index
    for col in incumbents:
        if col not in df.columns:
            ic_row[f"ic_{col}"] = np.nan
            continue
        other = df.loc[valid_idx, col]
        common = pd.concat([rms_5d, other], axis=1).dropna()
        if len(common) < 200:
            ic_row[f"ic_{col}"] = np.nan
        else:
            ic_row[f"ic_{col}"] = float(common.iloc[:, 0].corr(common.iloc[:, 1]))

    # Also IC vs raw ret_5d (the value primitive) — mechanical
    common = pd.concat([rms_5d, ret_5d.loc[valid_idx]], axis=1).dropna()
    ic_row["ic_ret_5d_15bar_value_primitive"] = float(common.iloc[:, 0].corr(common.iloc[:, 1]))
    common = pd.concat([rms_5d, hurst_100.loc[valid_idx]], axis=1).dropna()
    ic_row["ic_hurst_100_regime_primitive"] = float(common.iloc[:, 0].corr(common.iloc[:, 1]))

    return {"dist": dist, "ic": ic_row}


def main() -> None:
    here = Path(__file__).resolve().parent
    repo = here.parent.parent
    features_dir = repo / "data" / "features"

    dist_rows = []
    ic_rows = []
    for sym in SYMBOLS:
        path = features_dir / f"{sym}_8h_features.parquet"
        if not path.exists():
            print(f"MISSING parquet: {path}")
            continue
        print(f"[+] processing {sym} ...")
        result = compute_for_symbol(path)
        dist_rows.append(result["dist"])
        ic_rows.append(result["ic"])

    dist_df = pd.DataFrame(dist_rows)
    ic_df = pd.DataFrame(ic_rows)
    dist_df.to_csv(here / "distribution_per_symbol.csv", index=False)
    ic_df.to_csv(here / "ic_matrix.csv", index=False)

    # ADF aggregate
    adf_df = dist_df[["symbol", "adf_pvalue"]].copy()
    adf_df.to_csv(here / "adf_per_symbol.csv", index=False)

    # basis_zscore_30 importance history (compiled from prior iter reports)
    bhist = [
        # (iter, cohort, rank)
        ("iter-v1/034", "Model_A_pool", 25),
        ("iter-v1/034", "Model_C_LINK", 29),
        ("iter-v1/034", "Model_D_LTC", 32),
        ("iter-v1/034", "Model_E_DOT", 26),
        ("iter-v1/034", "portfolio", 27),
        ("iter-v1/037", "Model_A_pool", 25),
        ("iter-v1/037", "Model_C_LINK", 29),
        ("iter-v1/037", "Model_D_LTC", 31),
        ("iter-v1/037", "Model_E_DOT", 25),
        ("iter-v1/037", "portfolio", 27),
        ("iter-v1/038", "Model_A_pool", 25),
        ("iter-v1/038", "Model_C_LINK", 29),
        ("iter-v1/038", "Model_D_LTC", 32),
        ("iter-v1/038", "Model_E_DOT", 26),
        ("iter-v1/038", "portfolio", 27),
    ]
    bhist_df = pd.DataFrame(bhist, columns=["iter", "cohort", "rank"])
    bhist_df.to_csv(here / "basis_z30_importance_history.csv", index=False)

    print("\n=== Distribution per symbol ===")
    print(dist_df.to_string(index=False))
    print("\n=== IC matrix (composed feature vs incumbents) ===")
    print(ic_df.to_string(index=False))
    print("\n=== basis_zscore_30 importance history ===")
    print(bhist_df.to_string(index=False))
    print(
        "\nMean rank across 5 cohorts x 3 iters:",
        f"{bhist_df['rank'].mean():.2f} (deeply INERT; all 15 obs >= 25)",
    )


if __name__ == "__main__":
    main()
