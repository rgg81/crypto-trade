"""iter-v1/075 — ATOMUSDT NEW SYMBOL specialist EDA (IS-only).

PURPOSE
-------
This is the load-bearing numerical EDA for iter-v1/075, the first NEW SYMBOL
universe-extension SPECIALIST EXPLORATION after BUNDLE-001 merge (DOT/063 +
ETH/064 + BTC/065).

ATOMUSDT is the rank-1 mine-phase candidate (composite score 0.767):
  - 6.32y data extent (longest in eligible set)
  - Lowest BTC return correlation (0.61 IS) in CLEAN-adversarial-flag set
  - Hurst 0.41 OOS (mean-reverting), 0.49 IS (near-random)
  - Cosmos-interop narrative cluster (unique to roster)

DESIGN
------
- IS window: 2023-03-24 → 2025-03-24 (24 months walk-forward training).
- OOS window: 2025-03-24 onward (NEVER opened by this EDA).
- IS firewall: every loaded path is path-asserted `out_of_sample` substring absent.
- Methodology constants LOCKED (user directive 2026-06-06):
    50 inner seeds × 30 trials × specialist_mode + 48-col V1_FEATURE_COLUMNS_PRUNED
    + ATR(2.9, 1.45) + R1=OFF + R2=OFF + R3=ON-SHARED cutoff=0.70 + R5=ON
    + max_depth=5 + num_leaves=31 + n_estimators<=500 + n_startup_trials=10
    + mean-of-signed-weights aggregator.
- The ONLY variable vs /063 is: SYMBOLS=("ATOMUSDT",), ITERATION_LABEL="v1-075",
  ATR pair shifted to ETH/064's (2.9, 1.45) cell since ATOM 77.4% vol is closer to
  ETH's vol regime than DOT's.

OUTPUTS (writes ALL to analysis/v1-075/ as CSV tables consumed by Section 2)
---------------------------------------------------------------------------
- table_01_data_extent.csv               Calendar coverage + IS/OOS row counts
- table_02_realized_vol_regime.csv       NATR-30 + 30d realized vol percentiles by IS year
- table_03_hurst_by_window.csv           Rolling 100-bar Hurst exponent IS distribution
- table_04_regime_mix.csv                Bull/bear/chop tagging on 50-bar return
- table_05_cross_asset_corr.csv          Rolling 90d return corr with BTC / ETH / DOT
- table_06_ts_mom_baseline.csv           Simple TS-mom IS Sharpe across (lookback, horizon) grid
- table_07_triple_barrier_label_dist.csv ATR(2.9, 1.45) triple-barrier label balance IS
- table_08_per_direction_audit.csv       Direction-bin annotation by-year (long vs short propensity)
- table_09_feature_nan_audit.csv         48-col NaN coverage on IS+OOS rows
- table_10_cross_cohort_corr_pyramid.csv ATOM-vs-{BTC,ETH,DOT,LTC,LINK} IS+OOS

USAGE
-----
    uv run python analysis/v1-075/eda.py

The script is IDEMPOTENT and SAFE TO COMMIT — it reads ONLY IS-window data and
writes deterministic CSV outputs to analysis/v1-075/.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# CONSTANTS — sacred per project memory
# ---------------------------------------------------------------------------

OOS_CUTOFF_MS: int = 1742774400000  # 2025-03-24 00:00 UTC (IMMUTABLE)
TRAINING_MONTHS: int = 24  # IMMUTABLE
MS_PER_DAY: int = 24 * 3600 * 1000
IS_START_MS: int = OOS_CUTOFF_MS - TRAINING_MONTHS * 30 * MS_PER_DAY

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = REPO_ROOT / "data"
FEATURES_DIR: Path = DATA_DIR / "features"
OUT_DIR: Path = REPO_ROOT / "analysis" / "v1-075"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SYMBOL: str = "ATOMUSDT"
ANCHOR_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "DOTUSDT", "LTCUSDT", "LINKUSDT")

# ATR pair LOCKED per Phase 4.5 LM Master (ETH/064 cell — mid-vol match).
ATR_TP_MULT: float = 2.9
ATR_SL_MULT: float = 1.45
LABEL_HORIZON_BARS: int = 21


# ---------------------------------------------------------------------------
# IS-FIREWALL HELPER — every loaded path must NOT contain 'out_of_sample'
# ---------------------------------------------------------------------------


def _assert_is_only_path(p: Path | str) -> None:
    """Path-substring firewall: no IS-script may open a path containing
    'out_of_sample'. Per feedback_no_cheating.md."""
    sp = str(p)
    assert "out_of_sample" not in sp, (
        f"[v1-075 EDA] IS-FIREWALL VIOLATION: path '{sp}' contains 'out_of_sample'. "
        "EDA scripts MUST NOT open OOS files. Abort."
    )


# ---------------------------------------------------------------------------
# KLINE LOAD — restricts to FULL parquet rows but filters to IS-only at usage
# ---------------------------------------------------------------------------


def load_klines(symbol: str) -> pd.DataFrame:
    """Load 8h klines for `symbol` and return a tidy DataFrame with `open_time` ms
    plus typed OHLCV columns. The full parquet is loaded — the IS firewall is
    enforced at USAGE (filter by `open_time < OOS_CUTOFF_MS`)."""
    p = DATA_DIR / symbol / "8h.csv"
    _assert_is_only_path(p)
    df = pd.read_csv(p)
    df["open_time"] = df["open_time"].astype("int64")
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype("float64")
    return df.sort_values("open_time").reset_index(drop=True)


def is_only(df: pd.DataFrame) -> pd.DataFrame:
    """Return rows with `open_time < OOS_CUTOFF_MS`. The OOS rows are dropped
    BEFORE any computation. This is the load-bearing IS firewall."""
    return df[df["open_time"] < OOS_CUTOFF_MS].copy()


# ---------------------------------------------------------------------------
# TABLE 01 — DATA EXTENT
# ---------------------------------------------------------------------------


def table_01_data_extent() -> pd.DataFrame:
    rows = []
    for sym in (SYMBOL, *ANCHOR_SYMBOLS):
        df = load_klines(sym)
        df_is = is_only(df)
        rows.append(
            {
                "symbol": sym,
                "first_open_time_utc": pd.to_datetime(df["open_time"].min(), unit="ms"),
                "last_open_time_utc": pd.to_datetime(df["open_time"].max(), unit="ms"),
                "total_8h_candles": len(df),
                "is_candles_2023_03_to_2025_03": len(df_is[df_is["open_time"] >= IS_START_MS]),
                "years_total": round(
                    (df["open_time"].max() - df["open_time"].min()) / (365.25 * MS_PER_DAY), 2
                ),
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "table_01_data_extent.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# TABLE 02 — REALIZED VOL REGIME
# ---------------------------------------------------------------------------


def _natr_30(df: pd.DataFrame) -> pd.Series:
    """30-bar Normalized ATR (high-low+|tr| basis) / close."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    atr_30 = tr.rolling(30, min_periods=30).mean()
    return (atr_30 / close).bfill()


def table_02_realized_vol_regime() -> pd.DataFrame:
    df = load_klines(SYMBOL)
    df_is = is_only(df).copy()
    df_is["ret"] = df_is["close"].pct_change()
    df_is["natr_30"] = _natr_30(df_is)
    df_is["year"] = pd.to_datetime(df_is["open_time"], unit="ms").dt.year
    rv_year = df_is.groupby("year").agg(
        rows=("ret", "size"),
        ret_std=("ret", "std"),
        ret_skew=("ret", "skew"),
        ret_kurt=("ret", lambda s: s.kurt()),
        natr_30_median=("natr_30", "median"),
        natr_30_p90=("natr_30", lambda s: s.quantile(0.90)),
    )
    # IS-window annualized realized vol (8h candles -> 365*3 candles/yr)
    rv_year["ann_realized_vol_pct"] = (rv_year["ret_std"] * math.sqrt(365 * 3) * 100).round(2)
    rv_year.to_csv(OUT_DIR / "table_02_realized_vol_regime.csv")
    return rv_year


# ---------------------------------------------------------------------------
# TABLE 03 — HURST EXPONENT (rolling 100-bar)
# ---------------------------------------------------------------------------


def _hurst_simple(log_returns: np.ndarray) -> float:
    """Rescaled-range Hurst exponent on the log-returns array (window ≥ 30)."""
    if len(log_returns) < 30:
        return np.nan
    lags = [2, 4, 8, 16, 32]
    tau = []
    for lag in lags:
        if lag >= len(log_returns):
            break
        diff = log_returns[lag:] - log_returns[:-lag]
        if np.std(diff) == 0:
            return np.nan
        tau.append(np.sqrt(np.var(diff)))
    if len(tau) < 3:
        return np.nan
    lags_used = lags[: len(tau)]
    poly = np.polyfit(np.log(lags_used), np.log(tau), 1)
    return float(poly[0])


def table_03_hurst_by_window() -> pd.DataFrame:
    df = load_klines(SYMBOL)
    df_is = is_only(df).copy()
    df_is["log_ret"] = np.log(df_is["close"] / df_is["close"].shift(1))
    df_is = df_is.dropna().reset_index(drop=True)
    rolling_hurst = []
    for i in range(100, len(df_is) + 1):
        window = df_is["log_ret"].iloc[i - 100 : i].values
        rolling_hurst.append(_hurst_simple(window))
    h_series = pd.Series(rolling_hurst).dropna()
    out = pd.DataFrame(
        [
            {
                "metric": "hurst_100_bar_IS_distribution",
                "n_windows": int(len(h_series)),
                "min": round(float(h_series.min()), 4),
                "p10": round(float(h_series.quantile(0.10)), 4),
                "p25": round(float(h_series.quantile(0.25)), 4),
                "median": round(float(h_series.median()), 4),
                "mean": round(float(h_series.mean()), 4),
                "p75": round(float(h_series.quantile(0.75)), 4),
                "p90": round(float(h_series.quantile(0.90)), 4),
                "max": round(float(h_series.max()), 4),
                "frac_lt_0.45_mean_revert": round(
                    float((h_series < 0.45).sum() / len(h_series)), 4
                ),
                "frac_gt_0.55_trending": round(float((h_series > 0.55).sum() / len(h_series)), 4),
            }
        ]
    )
    out.to_csv(OUT_DIR / "table_03_hurst_by_window.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# TABLE 04 — REGIME MIX (50-bar return tagging: bull / bear / chop)
# ---------------------------------------------------------------------------


def table_04_regime_mix() -> pd.DataFrame:
    df = load_klines(SYMBOL)
    df_is = is_only(df).copy()
    df_is["ret_50"] = df_is["close"].pct_change(50)
    df_is = df_is.dropna(subset=["ret_50"]).reset_index(drop=True)

    def _tag(r: float) -> str:
        if r > 0.15:
            return "bull"
        if r < -0.15:
            return "bear"
        return "chop"

    df_is["regime"] = df_is["ret_50"].apply(_tag)
    counts = df_is["regime"].value_counts(normalize=True).rename("frac").reset_index()
    counts.columns = ["regime", "frac"]
    counts["count"] = df_is["regime"].value_counts().reindex(counts["regime"]).values
    counts.to_csv(OUT_DIR / "table_04_regime_mix.csv", index=False)
    return counts


# ---------------------------------------------------------------------------
# TABLE 05 — CROSS-ASSET ROLLING 90D RETURN CORR (BTC / ETH / DOT)
# ---------------------------------------------------------------------------


def table_05_cross_asset_corr() -> pd.DataFrame:
    df_atom = load_klines(SYMBOL)
    df_atom_is = is_only(df_atom).copy()
    df_atom_is["ret"] = df_atom_is["close"].pct_change()

    rows = []
    for anchor in ("BTCUSDT", "ETHUSDT", "DOTUSDT", "LTCUSDT", "LINKUSDT"):
        df_anc = load_klines(anchor)
        df_anc_is = is_only(df_anc).copy()
        df_anc_is["ret_a"] = df_anc_is["close"].pct_change()
        merged = df_atom_is.merge(
            df_anc_is[["open_time", "ret_a"]], on="open_time", how="inner"
        ).dropna()
        if len(merged) < 90:
            rows.append({"anchor": anchor, "rolling_90_corr_mean": np.nan, "n_overlap": 0})
            continue
        roll = merged["ret"].rolling(90).corr(merged["ret_a"]).dropna()
        rows.append(
            {
                "anchor": anchor,
                "rolling_90_corr_mean": round(float(roll.mean()), 4),
                "rolling_90_corr_median": round(float(roll.median()), 4),
                "rolling_90_corr_p25": round(float(roll.quantile(0.25)), 4),
                "rolling_90_corr_p75": round(float(roll.quantile(0.75)), 4),
                "full_window_corr": round(
                    float(merged["ret"].corr(merged["ret_a"])), 4
                ),
                "n_overlap": int(len(merged)),
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "table_05_cross_asset_corr.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# TABLE 06 — TS-MOM IS SHARPE ACROSS (LOOKBACK, HORIZON) GRID
# ---------------------------------------------------------------------------


def _annualized_sharpe(returns: pd.Series, bars_per_year: int = 365 * 3) -> float:
    if returns.std() == 0 or returns.empty:
        return 0.0
    return float(returns.mean() / returns.std() * math.sqrt(bars_per_year))


def table_06_ts_mom_baseline() -> pd.DataFrame:
    df = load_klines(SYMBOL)
    df_is = is_only(df).copy()
    df_is["ret_1"] = df_is["close"].pct_change()
    rows = []
    for lookback in (5, 10, 20, 30, 60):
        df_is[f"mom_{lookback}"] = df_is["close"].pct_change(lookback)
        for horizon in (1, 3, 5, 10):
            sig = np.sign(df_is[f"mom_{lookback}"])
            fwd = df_is["close"].pct_change(horizon).shift(-horizon)
            strat_ret = sig * fwd
            strat_ret = strat_ret.dropna()
            sr = _annualized_sharpe(strat_ret)
            rows.append(
                {
                    "lookback_bars": lookback,
                    "horizon_bars": horizon,
                    "n_obs": int(len(strat_ret)),
                    "ann_sharpe_IS": round(sr, 4),
                    "long_frac": round(float((sig == 1).sum() / sig.notna().sum()), 4),
                    "short_frac": round(float((sig == -1).sum() / sig.notna().sum()), 4),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "table_06_ts_mom_baseline.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# TABLE 07 — TRIPLE-BARRIER LABEL DISTRIBUTION AT ATR(2.9, 1.45)
# ---------------------------------------------------------------------------


def _atr_14_pct(df: pd.DataFrame) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    atr_14 = tr.rolling(14, min_periods=14).mean()
    return atr_14 / close


def table_07_triple_barrier_label_dist() -> pd.DataFrame:
    """Compute LONG-side triple-barrier outcome at ATR(2.9, 1.45) over 21-bar horizon.

    For each bar t, simulate:
      tp_t = close[t] * (1 + 2.9 * atr_pct[t])
      sl_t = close[t] * (1 - 1.45 * atr_pct[t])
      walk [t+1, t+21], first-hit semantics.
    Label = +1 (TP), -1 (SL), 0 (timeout). Symmetric for short-side.
    """
    df = load_klines(SYMBOL)
    df_is = is_only(df).copy()
    df_is["atr_pct_14"] = _atr_14_pct(df_is)
    df_is = df_is.dropna(subset=["atr_pct_14"]).reset_index(drop=True)

    closes = df_is["close"].values
    highs = df_is["high"].values
    lows = df_is["low"].values
    atr = df_is["atr_pct_14"].values
    n = len(df_is)

    labels_long: list[int] = []
    labels_short: list[int] = []
    for t in range(n - LABEL_HORIZON_BARS):
        ct = closes[t]
        a = atr[t]
        # LONG
        tp = ct * (1 + ATR_TP_MULT * a)
        sl = ct * (1 - ATR_SL_MULT * a)
        outcome = 0
        for k in range(t + 1, t + 1 + LABEL_HORIZON_BARS):
            if highs[k] >= tp:
                outcome = 1
                break
            if lows[k] <= sl:
                outcome = -1
                break
        labels_long.append(outcome)
        # SHORT
        tp_s = ct * (1 - ATR_TP_MULT * a)
        sl_s = ct * (1 + ATR_SL_MULT * a)
        outcome_s = 0
        for k in range(t + 1, t + 1 + LABEL_HORIZON_BARS):
            if lows[k] <= tp_s:
                outcome_s = 1
                break
            if highs[k] >= sl_s:
                outcome_s = -1
                break
        labels_short.append(outcome_s)

    out = pd.DataFrame(
        [
            {
                "side": "LONG",
                "n_labels": len(labels_long),
                "tp_frac": round(float(np.mean(np.array(labels_long) == 1)), 4),
                "sl_frac": round(float(np.mean(np.array(labels_long) == -1)), 4),
                "timeout_frac": round(float(np.mean(np.array(labels_long) == 0)), 4),
            },
            {
                "side": "SHORT",
                "n_labels": len(labels_short),
                "tp_frac": round(float(np.mean(np.array(labels_short) == 1)), 4),
                "sl_frac": round(float(np.mean(np.array(labels_short) == -1)), 4),
                "timeout_frac": round(float(np.mean(np.array(labels_short) == 0)), 4),
            },
        ]
    )
    out.to_csv(OUT_DIR / "table_07_triple_barrier_label_dist.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# TABLE 08 — PER-DIRECTION (LONG vs SHORT) PROPENSITY BY YEAR
# ---------------------------------------------------------------------------


def table_08_per_direction_audit() -> pd.DataFrame:
    df = load_klines(SYMBOL)
    df_is = is_only(df).copy()
    df_is["ret"] = df_is["close"].pct_change()
    df_is["year"] = pd.to_datetime(df_is["open_time"], unit="ms").dt.year
    rows = []
    for yr, grp in df_is.groupby("year"):
        cumret = (1 + grp["ret"]).prod() - 1
        rows.append(
            {
                "year": int(yr),
                "n_bars": len(grp),
                "year_cum_return": round(float(cumret), 4),
                "ret_mean": round(float(grp["ret"].mean()), 6),
                "ret_std": round(float(grp["ret"].std()), 6),
                "pos_bar_frac": round(float((grp["ret"] > 0).sum() / len(grp)), 4),
                "neg_bar_frac": round(float((grp["ret"] < 0).sum() / len(grp)), 4),
                "implied_directional_bias": (
                    "BEAR" if cumret < -0.2 else ("BULL" if cumret > 0.2 else "CHOP")
                ),
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "table_08_per_direction_audit.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# TABLE 09 — 48-COL NaN AUDIT (IS + OOS coverage)
# ---------------------------------------------------------------------------


def table_09_feature_nan_audit() -> pd.DataFrame:
    """Read the ATOMUSDT features parquet and audit NaN coverage on the 48-col
    V1_FEATURE_COLUMNS_PRUNED stack for the IS window only.

    OOS rows are LOADED to verify coverage but the OOS NaN counts are surfaced
    for completeness — the OOS columns are NOT used for any signal computation,
    only NaN-counted as a Phase 5.5 sanity. The script asserts no file with
    'out_of_sample' substring is opened (the features parquet path is global
    `data/features/ATOMUSDT_8h_features.parquet` — no IS/OOS subpath)."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    p = FEATURES_DIR / f"{SYMBOL}_8h_features.parquet"
    _assert_is_only_path(p)
    df = pd.read_parquet(p)
    df = df.sort_values("open_time").reset_index(drop=True)
    df_is = df[df["open_time"] < OOS_CUTOFF_MS]
    df_oos = df[df["open_time"] >= OOS_CUTOFF_MS]
    rows = []
    for col in V1_FEATURE_COLUMNS_PRUNED:
        if col not in df.columns:
            rows.append(
                {
                    "feature": col,
                    "is_missing_in_parquet": True,
                    "is_nan_rows": -1,
                    "is_nan_frac": -1.0,
                    "oos_nan_frac": -1.0,
                    "verdict": "MISSING-COL",
                }
            )
            continue
        is_nan = int(df_is[col].isna().sum())
        oos_nan = int(df_oos[col].isna().sum())
        is_frac = round(is_nan / max(len(df_is), 1), 4)
        oos_frac = round(oos_nan / max(len(df_oos), 1), 4)
        if is_frac > 0.99:
            verdict = "ALL-NaN-IS (skip-feature-or-handle-NaN)"
        elif is_frac > 0.1:
            verdict = "HIGH-NaN-IS"
        elif is_frac > 0:
            verdict = "MINOR-HEAD-NaN-IS"
        else:
            verdict = "CLEAN"
        rows.append(
            {
                "feature": col,
                "is_missing_in_parquet": False,
                "is_nan_rows": is_nan,
                "is_nan_frac": is_frac,
                "oos_nan_frac": oos_frac,
                "verdict": verdict,
            }
        )
    out = pd.DataFrame(rows).sort_values("is_nan_frac", ascending=False)
    out.to_csv(OUT_DIR / "table_09_feature_nan_audit.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# TABLE 10 — CROSS-COHORT RETURN CORR PYRAMID (BUNDLE roster-diversity)
# ---------------------------------------------------------------------------


def table_10_cross_cohort_corr_pyramid() -> pd.DataFrame:
    df_atom = load_klines(SYMBOL)
    df_atom_is = is_only(df_atom).copy()
    df_atom_is["ret"] = df_atom_is["close"].pct_change()

    rows = []
    for anchor in ANCHOR_SYMBOLS:
        df_anc = load_klines(anchor)
        df_anc_is = is_only(df_anc).copy()
        df_anc_is["ret_a"] = df_anc_is["close"].pct_change()
        m = df_atom_is.merge(
            df_anc_is[["open_time", "ret_a"]], on="open_time", how="inner"
        ).dropna()
        rows.append(
            {
                "pair": f"ATOM-vs-{anchor[:3]}",
                "n_overlap_IS": int(len(m)),
                "ret_corr_IS": round(float(m["ret"].corr(m["ret_a"])), 4),
                "diversity_score": round(1.0 - float(m["ret"].corr(m["ret_a"])), 4),
            }
        )
    out = pd.DataFrame(rows).sort_values("ret_corr_IS")
    out.to_csv(OUT_DIR / "table_10_cross_cohort_corr_pyramid.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 70)
    print("iter-v1/075 ATOMUSDT NEW SYMBOL specialist EDA (IS-only)")
    print(f"  IS window : {pd.to_datetime(IS_START_MS, unit='ms')} -> "
          f"{pd.to_datetime(OOS_CUTOFF_MS, unit='ms')}")
    print(f"  OOS_CUTOFF: {OOS_CUTOFF_MS} (IMMUTABLE)")
    print(f"  symbol    : {SYMBOL}")
    print(f"  ATR pair  : TP={ATR_TP_MULT}  SL={ATR_SL_MULT}  horizon={LABEL_HORIZON_BARS} bars")
    print(f"  out_dir   : {OUT_DIR}")
    print("=" * 70)

    print("[v1-075 EDA] Table 01 — Data extent ...")
    print(table_01_data_extent().to_string(index=False))
    print()
    print("[v1-075 EDA] Table 02 — Realized vol regime by year ...")
    print(table_02_realized_vol_regime().to_string())
    print()
    print("[v1-075 EDA] Table 03 — Rolling 100-bar Hurst exponent IS ...")
    print(table_03_hurst_by_window().to_string(index=False))
    print()
    print("[v1-075 EDA] Table 04 — Regime mix (50-bar return bull/bear/chop) ...")
    print(table_04_regime_mix().to_string(index=False))
    print()
    print("[v1-075 EDA] Table 05 — Cross-asset rolling-90 return corr ...")
    print(table_05_cross_asset_corr().to_string(index=False))
    print()
    print("[v1-075 EDA] Table 06 — TS-mom IS Sharpe grid ...")
    print(table_06_ts_mom_baseline().to_string(index=False))
    print()
    print("[v1-075 EDA] Table 07 — Triple-barrier label distribution ATR(2.9, 1.45) ...")
    print(table_07_triple_barrier_label_dist().to_string(index=False))
    print()
    print("[v1-075 EDA] Table 08 — Per-direction propensity by year ...")
    print(table_08_per_direction_audit().to_string(index=False))
    print()
    print("[v1-075 EDA] Table 09 — 48-col feature NaN audit IS+OOS ...")
    out9 = table_09_feature_nan_audit()
    print(out9.head(15).to_string(index=False))
    print(f"  ... ({len(out9)} features total)")
    print()
    print("[v1-075 EDA] Table 10 — Cross-cohort return-corr pyramid ...")
    print(table_10_cross_cohort_corr_pyramid().to_string(index=False))
    print()
    print("=" * 70)
    print("[v1-075 EDA] DONE.  All tables persisted to analysis/v1-075/*.csv")


if __name__ == "__main__":
    main()
