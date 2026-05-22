"""
iter-v3/015 — Taker-buy ratio z-score (TBR_z30) EDA (NEW microstructure feature family).

Per `feedback_structural_over_knob_exploration.md` (NEW rule 2026-05-07): after
iter-v3/014 ADX axis closed (asymmetric NEGATIVE -1.83 OOS Δ; original ADX=18
mandate DOWNGRADED), iter-v3/015 must pivot to a NEW feature family — NOT a
gate-threshold knob. Axis priority order (highest first):
    1. NEW feature families (funding rate, OI, basis, microstructure, on-chain)
    2. NEW model architecture (XGBoost, CatBoost, NN)
    3. NEW labeling architecture (meta-labeling, regime-conditional triple-barrier)
    4. NEW risk primitive (orthogonal to existing 7 gates)
    5. NEW universe (cross-track basket, regime-conditional symbol set)
    6. Gate-threshold knob (LOWEST priority)

This script implements the EDA for the chosen axis: Category 1 NEW feature
family (microstructure), specifically a single new feature
``tbr_zscore_30`` = z-score of (taker_buy_quote_volume / quote_volume) over
a rolling 30-bar (~10-day) window, on existing 8h Binance kline data.

Why TBR (taker buy ratio):
    - Crypto-native: taker-buy imbalance is the canonical aggressive-buyer-flow
      proxy in perpetual-futures markets where queue position is unobservable.
    - Already in 8h kline data layer (taker_buy_quote_volume + quote_volume in
      every Binance 8h candle); ZERO new fetcher infrastructure needed —
      immediately backtestable in the 2h EXPLORATION wall-clock budget.
    - Never used in v3 (V3_FEATURE_COLUMNS contains zero taker_buy-derived
      features); v1 has `vol_taker_buy_ratio` and SMA variants in
      BASELINE_FEATURE_COLUMNS but those are RAW ratios, not z-scored — the
      raw ratio is non-stationary across symbols and regimes (BCH average TBR
      differs structurally from TRX average TBR). The z-score normalization
      makes the feature scale-invariant, mandatory per the
      "scale-invariant features" project rule.
    - 30-bar window (~10 days) is the funding-cycle-aligned timescale on 8h
      candles (1 funding period = 1 candle; 30 candles = ~9 funding cycles
      = enough to see flow regime persistence without overlapping training
      window's stationarity boundary).

Inputs read (IS-only — training window pre-OOS_CUTOFF_DATE 2025-03-24):
    - data/features_v3/{BCH,LDO,TRX}USDT_8h_features.parquet — already-generated
      feature parquets (existing 13 V3_FEATURE_COLUMNS + raw kline columns
      including taker_buy_quote_volume and quote_volume).

Outputs (committed BEFORE the brief — Phase 5.5 reproducibility requirement):
    - analysis/iteration_v3-015/tbr_eda_coverage.csv — NaN counts, percent valid
    - analysis/iteration_v3-015/tbr_eda_distribution.csv — per-symbol mean,
      median, std, percentiles of raw TBR and z-scored TBR_z30
    - analysis/iteration_v3-015/tbr_eda_correlation.csv — IC matrix between
      tbr_zscore_30 and the 13 V3_FEATURE_COLUMNS, per-symbol
    - analysis/iteration_v3-015/tbr_eda_rankic.csv — rank-IC of tbr_zscore_30
      and forward-return horizons (1-bar, 3-bar, 7-bar) on IS data
    - analysis/iteration_v3-015/synthesis.md — narrative summary

Methodology — single-feature axis:
    1. Compute ``tbr_raw`` = taker_buy_quote_volume / quote_volume per candle.
       Note: kline guarantees quote_volume > taker_buy_quote_volume >= 0;
       ratio is in [0, 1]. NaN only when quote_volume = 0 (rare).
    2. Compute ``tbr_zscore_30`` = (tbr_raw - mean(tbr_raw, 30)) / std(tbr_raw, 30)
       using past-only rolling stats. Implementation uses pandas ``.shift(1)``
       at the rolling level to ensure the bar's own value is excluded.
    3. Coverage: count NaN values per symbol; expected ~30 NaN at series start
       (rolling-window initialization) + occasional NaN from quote_volume=0.
    4. Distribution: expected mean ~0 by construction, std ~1 ± noise.
    5. Correlation: Spearman |IC| vs each of the 13 V3_FEATURE_COLUMNS.
       MANDATORY: max |IC| < 0.70 (v3 IC_threshold from BASELINE_V3.md). If
       any pair exceeds 0.70, the candidate feature is redundant and the
       axis should be replaced.
    6. Rank-IC vs forward returns: Spearman ρ between tbr_zscore_30 at
       candle close and the cumulative return over the next k bars
       (k ∈ {1, 3, 7}). A meaningful predictive signal requires |IC| > 0.02
       on at least one horizon (the v3 implicit threshold inferred from
       existing feature behavior).

Invariants the script asserts (and exits non-zero on failure):
    - All 3 symbol parquets exist + non-empty
    - taker_buy_quote_volume + quote_volume columns present
    - At least 80% of candles have valid tbr_zscore_30 (coverage floor)
    - max |IC| vs V3_FEATURE_COLUMNS < 0.70 on ALL 3 symbols (TIGHT v3 gate)
    - Decision summary saved to synthesis.md

Track isolation: this script runs on the v3 worktree only. It reads
data/features_v3/*.parquet (track-isolated). It writes only to
analysis/iteration_v3-015/. Zero edits to src/.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

# v3 sacred constants
OOS_CUTOFF_DATE = pd.Timestamp("2025-03-24", tz="UTC")
OOS_CUTOFF_MS = int(OOS_CUTOFF_DATE.value // 1_000_000)

# IS training window — 24 months before OOS cutoff
TRAINING_MONTHS = 24
IS_START_TS = OOS_CUTOFF_DATE - pd.DateOffset(months=TRAINING_MONTHS)
IS_START_MS = int(IS_START_TS.value // 1_000_000)

# v3 universe (3 symbols, BCH+LDO+TRX, MKR-dropped per iter-v3/013)
V3_SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")

# 13 V3_FEATURE_COLUMNS — inherited from iter-v3/008+ (post-vwap_dev_50 drop)
V3_FEATURE_COLUMNS_TOP_N = (
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
)

# Forward-return horizons for rank-IC check
FWD_HORIZONS = (1, 3, 7)

# IC redundancy gate — v3 BASELINE_V3.md threshold
IC_THRESHOLD = 0.70

# TBR z-score window — 30 bars = 10 days at 8h cadence
TBR_ZSCORE_WINDOW = 30

# Coverage floor for the candidate feature
COVERAGE_FLOOR_PCT = 80.0


def compute_tbr_zscore(df: pd.DataFrame, window: int = TBR_ZSCORE_WINDOW) -> pd.DataFrame:
    """Compute raw TBR + z-scored TBR over a rolling window.

    All ops past-only. ``rolling`` excludes current row by default (closed='right'),
    so the z-score at bar t uses bars t-(window-1)...t. We additionally shift
    by 1 to STRICTLY exclude the bar's own taker volume from the bar's
    z-score — this matches the v3 brief's look-ahead discipline.

    Returns
    -------
    pd.DataFrame
        Columns added: ``tbr_raw``, ``tbr_zscore_30``.
    """
    df = df.copy()
    qv = df["quote_volume"].astype(float)
    tbqv = df["taker_buy_quote_volume"].astype(float)

    # Raw ratio in [0, 1]; NaN where quote_volume == 0
    tbr_raw = np.where(qv > 0, tbqv / qv, np.nan)
    df["tbr_raw"] = tbr_raw

    # Rolling stats lag by 1 — bar t z-score uses bars t-30...t-1 only
    s = pd.Series(tbr_raw, index=df.index)
    rmean = s.shift(1).rolling(window=window, min_periods=window).mean()
    rstd = s.shift(1).rolling(window=window, min_periods=window).std(ddof=1)
    df["tbr_zscore_30"] = (s.shift(1) - rmean) / rstd.replace(0, np.nan)

    return df


def slice_is_window(df: pd.DataFrame) -> pd.DataFrame:
    """Filter rows to the IS training window only [IS_START_MS, OOS_CUTOFF_MS)."""
    mask = (df["open_time"] >= IS_START_MS) & (df["open_time"] < OOS_CUTOFF_MS)
    return df[mask].reset_index(drop=True)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    data_dir = repo_root / "data" / "features_v3"
    out_dir = Path(__file__).resolve().parent

    # Coverage / distribution / correlation / rank-IC tables
    coverage_rows: list[dict] = []
    distribution_rows: list[dict] = []
    correlation_rows: list[dict] = []
    rankic_rows: list[dict] = []

    # Aggregated max-IC for invariant check
    max_abs_ic_per_symbol: dict[str, float] = {}

    for symbol in V3_SYMBOLS:
        path = data_dir / f"{symbol}_8h_features.parquet"
        if not path.exists():
            print(f"FAIL parquet missing for {symbol}: {path}")
            return 2

        df_full = pd.read_parquet(path)
        if "taker_buy_quote_volume" not in df_full.columns:
            print(f"FAIL taker_buy_quote_volume missing for {symbol}")
            return 2
        if "quote_volume" not in df_full.columns:
            print(f"FAIL quote_volume missing for {symbol}")
            return 2

        # Compute candidate feature on FULL series (lookback window crosses
        # IS boundary edge cleanly using pre-IS data).
        df_full = compute_tbr_zscore(df_full, window=TBR_ZSCORE_WINDOW)

        # Slice IS window AFTER feature computation (so the rolling window
        # at the IS boundary uses pre-IS data, no look-ahead within IS).
        df_is = slice_is_window(df_full)

        n_total = len(df_is)
        n_valid_zsc = df_is["tbr_zscore_30"].notna().sum()
        n_valid_raw = df_is["tbr_raw"].notna().sum()
        coverage_pct = 100.0 * n_valid_zsc / n_total if n_total > 0 else 0.0

        coverage_rows.append(
            dict(
                symbol=symbol,
                n_is_total=n_total,
                n_valid_tbr_raw=int(n_valid_raw),
                n_valid_tbr_zscore_30=int(n_valid_zsc),
                coverage_zscore_pct=round(coverage_pct, 2),
                date_start=str(pd.to_datetime(int(df_is["open_time"].min()), unit="ms")),
                date_end=str(pd.to_datetime(int(df_is["open_time"].max()), unit="ms")),
            )
        )

        # Distribution stats on the IS-only valid rows
        valid = df_is[df_is["tbr_zscore_30"].notna()]
        for col in ("tbr_raw", "tbr_zscore_30"):
            s = valid[col]
            distribution_rows.append(
                dict(
                    symbol=symbol,
                    feature=col,
                    n=int(len(s)),
                    mean=round(float(s.mean()), 6),
                    median=round(float(s.median()), 6),
                    std=round(float(s.std(ddof=1)), 6),
                    p01=round(float(s.quantile(0.01)), 6),
                    p05=round(float(s.quantile(0.05)), 6),
                    p25=round(float(s.quantile(0.25)), 6),
                    p75=round(float(s.quantile(0.75)), 6),
                    p95=round(float(s.quantile(0.95)), 6),
                    p99=round(float(s.quantile(0.99)), 6),
                )
            )

        # Correlation against the 13 V3_FEATURE_COLUMNS (Spearman)
        max_abs_ic_sym = 0.0
        max_abs_ic_against = ""
        for v3col in V3_FEATURE_COLUMNS_TOP_N:
            if v3col not in valid.columns:
                # cross-asset btc features only on btc_ret_14d / sym_vs_btc_ret_7d
                # are computed in the regime/cross_btc modules and present in parquet.
                # Missing column => log NaN
                ic = float("nan")
            else:
                pair = valid[["tbr_zscore_30", v3col]].dropna()
                if len(pair) < 30:
                    ic = float("nan")
                else:
                    ic = float(pair["tbr_zscore_30"].corr(pair[v3col], method="spearman"))
            correlation_rows.append(
                dict(
                    symbol=symbol,
                    candidate="tbr_zscore_30",
                    against=v3col,
                    ic_spearman=round(ic, 4) if not np.isnan(ic) else float("nan"),
                    n_pairs=int(len(pair) if v3col in valid.columns else 0),
                )
            )
            if not np.isnan(ic) and abs(ic) > max_abs_ic_sym:
                max_abs_ic_sym = abs(ic)
                max_abs_ic_against = v3col
        max_abs_ic_per_symbol[symbol] = max_abs_ic_sym
        print(
            f"{symbol}: coverage_zscore_30 = {coverage_pct:.1f}%, "
            f"max |IC| = {max_abs_ic_sym:.4f} vs {max_abs_ic_against}"
        )

        # Rank-IC vs forward returns
        # log_return cumulative over k bars: r_k = log(close_{t+k}/close_t)
        close = valid["close"].astype(float).reset_index(drop=True)
        z = valid["tbr_zscore_30"].astype(float).reset_index(drop=True)
        for k in FWD_HORIZONS:
            log_ret_fwd = np.log(close.shift(-k) / close)
            pair = pd.DataFrame({"z": z, "fwd": log_ret_fwd}).dropna()
            if len(pair) < 30:
                ic_fwd = float("nan")
            else:
                ic_fwd = float(pair["z"].corr(pair["fwd"], method="spearman"))
            rankic_rows.append(
                dict(
                    symbol=symbol,
                    feature="tbr_zscore_30",
                    horizon_bars=k,
                    horizon_days=round(k * 8.0 / 24.0, 2),
                    n_pairs=int(len(pair)),
                    rank_ic_spearman=round(ic_fwd, 5) if not np.isnan(ic_fwd) else float("nan"),
                )
            )

    # Persist outputs
    pd.DataFrame(coverage_rows).to_csv(out_dir / "tbr_eda_coverage.csv", index=False)
    pd.DataFrame(distribution_rows).to_csv(out_dir / "tbr_eda_distribution.csv", index=False)
    pd.DataFrame(correlation_rows).to_csv(out_dir / "tbr_eda_correlation.csv", index=False)
    pd.DataFrame(rankic_rows).to_csv(out_dir / "tbr_eda_rankic.csv", index=False)

    # Compute aggregate max-|IC| across all (symbol × v3col) pairs for headline
    corr_df = pd.DataFrame(correlation_rows)
    corr_df["abs_ic"] = corr_df["ic_spearman"].abs()
    overall_max = float(corr_df["abs_ic"].max())
    overall_max_row = corr_df.loc[corr_df["abs_ic"].idxmax()]

    # Synthesis narrative
    rankic_df = pd.DataFrame(rankic_rows)
    coverage_df = pd.DataFrame(coverage_rows)
    min_coverage = float(coverage_df["coverage_zscore_pct"].min())

    synthesis = []
    synthesis.append("# iter-v3/015 — TBR z-score 30 EDA Synthesis\n")
    synthesis.append("## Decision\n")
    synthesis.append(
        f"Candidate feature: **tbr_zscore_30** = z-score of "
        f"(taker_buy_quote_volume / quote_volume) over rolling "
        f"{TBR_ZSCORE_WINDOW}-bar window (~10 days at 8h cadence).\n"
    )
    synthesis.append("\n## Coverage check (IS window only)\n")
    synthesis.append(coverage_df.to_markdown(index=False))
    synthesis.append(
        f"\n\nMin coverage: {min_coverage:.2f}% "
        f"({'PASS' if min_coverage >= COVERAGE_FLOOR_PCT else 'FAIL'} "
        f"— floor {COVERAGE_FLOOR_PCT}%)\n"
    )
    synthesis.append("\n## Distribution check\n")
    synthesis.append(pd.DataFrame(distribution_rows).to_markdown(index=False))
    synthesis.append("\n\n## Correlation gate (vs 13 V3_FEATURE_COLUMNS)\n")
    synthesis.append(
        f"Max |IC| across all (symbol × V3col) pairs: **{overall_max:.4f}**, "
        f"reached at ({overall_max_row['symbol']}, {overall_max_row['against']}).\n\n"
    )
    synthesis.append(
        f"Per-symbol max |IC|: "
        + ", ".join(f"{s} = {v:.4f}" for s, v in max_abs_ic_per_symbol.items())
        + "\n"
    )
    synthesis.append(
        f"\nIC gate (< {IC_THRESHOLD}): "
        f"**{'PASS' if overall_max < IC_THRESHOLD else 'FAIL'}**\n"
    )
    synthesis.append("\n## Rank-IC vs forward returns (predictive signal)\n")
    synthesis.append(rankic_df.to_markdown(index=False))
    synthesis.append("\n")

    # Verdict
    coverage_ok = min_coverage >= COVERAGE_FLOOR_PCT
    ic_ok = overall_max < IC_THRESHOLD
    nontrivial_rankic = rankic_df["rank_ic_spearman"].abs().max() >= 0.02
    overall = coverage_ok and ic_ok
    synthesis.append("\n## Overall verdict\n")
    synthesis.append(f"- Coverage gate: **{'PASS' if coverage_ok else 'FAIL'}**\n")
    synthesis.append(f"- IC redundancy gate (< {IC_THRESHOLD}): **{'PASS' if ic_ok else 'FAIL'}**\n")
    synthesis.append(
        f"- Non-trivial rank-IC (max |IC| >= 0.02): "
        f"**{'PASS' if nontrivial_rankic else 'INFORMATIONAL'}**\n"
    )
    synthesis.append(
        f"\n**Final**: candidate is {'tractable' if overall else 'BLOCKED'} for "
        "iter-v3/015 EXPLORATION as a single new feature added to "
        "V3_FEATURE_COLUMNS (13 → 14).\n"
    )

    (out_dir / "synthesis.md").write_text("\n".join(synthesis))

    # Print key headline for capture
    print("\n=== EDA HEADLINE ===")
    print(f"min coverage IS = {min_coverage:.2f}% (floor {COVERAGE_FLOOR_PCT}%)")
    print(f"overall max |IC| = {overall_max:.4f} (threshold {IC_THRESHOLD})")
    print(
        "max |rank-IC| vs forward returns = "
        f"{rankic_df['rank_ic_spearman'].abs().max():.4f}"
    )
    print(f"verdict: {'TRACTABLE' if overall else 'BLOCKED'}")

    if not overall:
        # Coverage or IC failure is a script-level FAIL signal but we still
        # write outputs so the brief can document the failure honestly.
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
