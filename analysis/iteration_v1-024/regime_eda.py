"""iter-v1/024 — Phase 1 EDA — regime-conditional sub-models (model-arch family).

Five EDA outputs computed on IS-only data (open_time < OOS_CUTOFF_DATE = 2025-03-24):

  1. regime_sample_size.csv         — extreme/normal bar counts per cohort + IS trade counts.
  2. regime_direction_attribution.csv — direction sign-flip stability in |z30|>1.5 across cohorts.
  3. regime_persistence.csv         — run-length distribution of extreme-regime bars.
  4. regime_cross_cohort_overlap.csv — pairwise extreme-regime co-occurrence rate.
  5. regime_oracle_attribution.csv  — predicted IS PnL Δ from regime-conditional training vs baseline.

ALL computations use only data with timestamp < OOS_CUTOFF_DATE (2025-03-24). The funding
columns are already in `data/features/<SYMBOL>_8h_features.parquet` from /023's QE commit.

Run from repo root:
    uv run python analysis/iteration_v1-024/regime_eda.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# IS / OOS boundary (sacred constant from src/crypto_trade/config.py)
OOS_CUTOFF_MS: int = 1742774400000  # 2025-03-24 00:00:00 UTC

# Regime threshold (LM Master /023 §4 and brief Section 1 mechanism)
REGIME_THRESHOLD: float = 1.5

# v1 baseline universe
V1_SYMBOLS: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
)

# Cohort dispatch (matches run_baseline_v1.py)
COHORT_MAP: dict[str, tuple[str, ...]] = {
    "Pool_A_BTCETH": ("BTCUSDT", "ETHUSDT"),
    "Model_C_LINK": ("LINKUSDT",),
    "Model_D_LTC": ("LTCUSDT",),
    "Model_E_DOT": ("DOTUSDT",),
}

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
OUT_DIR: Path = REPO_ROOT / "analysis" / "iteration_v1-024"
FEATURES_DIR: Path = REPO_ROOT / "data" / "features"
BASELINE_TRADES_IS: Path = (
    REPO_ROOT / "reports-v1" / "iteration_v1-baseline" / "in_sample" / "trades.csv"
)
BASELINE_TRADES_OOS: Path = (
    REPO_ROOT / "reports-v1" / "iteration_v1-baseline" / "out_of_sample" / "trades.csv"
)


def load_kline_features(sym: str) -> pd.DataFrame:
    """Load full feature parquet for symbol, restricted to IS (open_time < OOS_CUTOFF_MS)."""
    df = pd.read_parquet(
        FEATURES_DIR / f"{sym}_8h_features.parquet",
        columns=["open_time", "funding_rate_zscore_30", "funding_rate_zscore_90"],
    )
    return df[df["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)


def load_full_features(sym: str) -> pd.DataFrame:
    """Load full feature parquet WITHOUT IS cutoff (for OOS-side cross-cohort overlap)."""
    return pd.read_parquet(
        FEATURES_DIR / f"{sym}_8h_features.parquet",
        columns=["open_time", "funding_rate_zscore_30", "funding_rate_zscore_90"],
    )


def main() -> None:  # noqa: PLR0915
    """Compute all 5 EDA outputs."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Pre-load all per-symbol IS-only data
    print("[regime_eda] Loading IS features for 5 v1 symbols...")
    sym_to_df: dict[str, pd.DataFrame] = {sym: load_kline_features(sym) for sym in V1_SYMBOLS}
    for sym, sub in sym_to_df.items():
        print(
            f"  {sym}: {len(sub)} IS bars; "
            f"z30 non-null {sub['funding_rate_zscore_30'].notna().mean():.3%}"
        )

    # Pre-load baseline IS trades for trade-count partitioning
    print("[regime_eda] Loading baseline IS trades...")
    base_trades_is = pd.read_csv(BASELINE_TRADES_IS)
    base_trades_oos = pd.read_csv(BASELINE_TRADES_OOS)
    print(
        f"  IS trades: {len(base_trades_is)} ({base_trades_is['symbol'].value_counts().to_dict()})"
    )
    print(
        f"  OOS trades: {len(base_trades_oos)} "
        f"({base_trades_oos['symbol'].value_counts().to_dict()})"
    )

    # ============================================================================
    # 1. regime_sample_size.csv — per-cohort extreme + normal bar counts & trade counts
    # ============================================================================
    print("\n[regime_eda] (1/5) regime_sample_size.csv")
    rows_1: list[dict] = []
    for cohort_name, syms in COHORT_MAP.items():
        # Aggregate bars across cohort's symbols (Pool A pools BTC+ETH)
        cohort_df = pd.concat([sym_to_df[s].assign(symbol=s) for s in syms], ignore_index=True)
        # Drop NaN z30
        cohort_df = cohort_df.dropna(subset=["funding_rate_zscore_30"])
        n_bars = len(cohort_df)
        extreme_mask = cohort_df["funding_rate_zscore_30"].abs() > REGIME_THRESHOLD
        n_extreme = int(extreme_mask.sum())
        n_normal = n_bars - n_extreme
        extreme_pct = n_extreme / n_bars if n_bars > 0 else 0.0

        # Trade counts: partition baseline IS trades by the cohort's symbols + z30 at trade.open_time
        # NOTE: this is ORACLE EDA — descriptively valid but does not predict /024 retrained roster
        sym_set = set(syms)
        cohort_trades_is = base_trades_is[base_trades_is["symbol"].isin(sym_set)].copy()
        # Lookup z30 at each trade's open_time per symbol
        z30_per_trade: list[float] = []
        for _, trow in cohort_trades_is.iterrows():
            sym = trow["symbol"]
            ot = int(trow["open_time"])
            sub = sym_to_df[sym]
            idx = sub["open_time"].searchsorted(ot, side="right") - 1
            if 0 <= idx < len(sub):
                z30_per_trade.append(sub.iloc[idx]["funding_rate_zscore_30"])
            else:
                z30_per_trade.append(np.nan)
        cohort_trades_is["z30_at_open"] = z30_per_trade
        # Trade partition (drop NaN z30)
        valid_trades = cohort_trades_is.dropna(subset=["z30_at_open"])
        extreme_trade_mask = valid_trades["z30_at_open"].abs() > REGIME_THRESHOLD
        n_trades_extreme = int(extreme_trade_mask.sum())
        n_trades_normal = len(valid_trades) - n_trades_extreme

        rows_1.append(
            {
                "cohort": cohort_name,
                "symbols": "+".join(syms),
                "is_bars": n_bars,
                "extreme_bars": n_extreme,
                "normal_bars": n_normal,
                "extreme_pct": round(extreme_pct, 4),
                "is_trades_total": len(valid_trades),
                "is_trades_extreme": n_trades_extreme,
                "is_trades_normal": n_trades_normal,
                "trades_extreme_pct": round(
                    n_trades_extreme / len(valid_trades) if valid_trades.size else 0.0, 4
                ),
            }
        )

    df_1 = pd.DataFrame(rows_1)
    df_1.to_csv(OUT_DIR / "regime_sample_size.csv", index=False)
    print(df_1.to_string(index=False))

    # ============================================================================
    # 2. regime_direction_attribution.csv — direction sign-flip stability in |z30|>1.5
    # ============================================================================
    print("\n[regime_eda] (2/5) regime_direction_attribution.csv")
    rows_2: list[dict] = []
    for cohort_name, syms in COHORT_MAP.items():
        sym_set = set(syms)
        cohort_trades_is = base_trades_is[base_trades_is["symbol"].isin(sym_set)].copy()
        # Lookup z30 at each trade
        z30_per_trade: list[float] = []
        for _, trow in cohort_trades_is.iterrows():
            sym = trow["symbol"]
            ot = int(trow["open_time"])
            sub = sym_to_df[sym]
            idx = sub["open_time"].searchsorted(ot, side="right") - 1
            if 0 <= idx < len(sub):
                z30_per_trade.append(sub.iloc[idx]["funding_rate_zscore_30"])
            else:
                z30_per_trade.append(np.nan)
        cohort_trades_is["z30_at_open"] = z30_per_trade
        valid = cohort_trades_is.dropna(subset=["z30_at_open"])
        extreme = valid[valid["z30_at_open"].abs() > REGIME_THRESHOLD]
        normal = valid[valid["z30_at_open"].abs() <= REGIME_THRESHOLD]

        for regime_name, regime_df in [("EXTREME (|z30|>1.5)", extreme), ("NORMAL", normal)]:
            for direction_label, direction_int in [("longs", 1), ("shorts", -1)]:
                sel = regime_df[regime_df["direction"] == direction_int]
                if sel.empty:
                    continue
                rows_2.append(
                    {
                        "cohort": cohort_name,
                        "regime": regime_name,
                        "direction": direction_label,
                        "n_trades": len(sel),
                        "win_rate": round((sel["net_pnl_pct"] > 0).mean(), 4),
                        "mean_pnl_pct": round(sel["net_pnl_pct"].mean(), 4),
                        "sum_pnl_pct": round(sel["net_pnl_pct"].sum(), 4),
                        "sum_weighted_pnl": round(sel["weighted_pnl"].sum(), 4),
                    }
                )

    df_2 = pd.DataFrame(rows_2)
    df_2.to_csv(OUT_DIR / "regime_direction_attribution.csv", index=False)
    print(df_2.to_string(index=False))

    # ============================================================================
    # 3. regime_persistence.csv — extreme-regime run-length distribution
    # ============================================================================
    print("\n[regime_eda] (3/5) regime_persistence.csv")
    rows_3: list[dict] = []
    for sym, sub in sym_to_df.items():
        s = sub.dropna(subset=["funding_rate_zscore_30"])
        extreme_mask_arr = (s["funding_rate_zscore_30"].abs() > REGIME_THRESHOLD).to_numpy()

        # Compute run lengths of contiguous True/False
        # Boundary-aware run-length encoding
        if len(extreme_mask_arr) == 0:
            continue
        change_points = np.flatnonzero(np.diff(extreme_mask_arr.astype(int)) != 0) + 1
        run_starts = np.concatenate(([0], change_points))
        run_ends = np.concatenate((change_points, [len(extreme_mask_arr)]))
        run_lengths = run_ends - run_starts
        run_values = extreme_mask_arr[run_starts]

        extreme_runs = run_lengths[run_values]
        normal_runs = run_lengths[~run_values]

        # Transition rate: per-bar probability of flipping (cleaner regime ↔ scatter signal)
        n_flips = int(np.sum(np.diff(extreme_mask_arr.astype(int)) != 0))
        flip_rate = n_flips / max(len(extreme_mask_arr) - 1, 1)

        rows_3.append(
            {
                "symbol": sym,
                "n_extreme_runs": int(len(extreme_runs)),
                "extreme_run_mean": float(extreme_runs.mean()) if len(extreme_runs) else 0.0,
                "extreme_run_median": float(np.median(extreme_runs)) if len(extreme_runs) else 0.0,
                "extreme_run_p90": float(np.quantile(extreme_runs, 0.9))
                if len(extreme_runs)
                else 0.0,
                "extreme_run_max": int(extreme_runs.max()) if len(extreme_runs) else 0,
                "normal_run_mean": float(normal_runs.mean()) if len(normal_runs) else 0.0,
                "flip_rate_per_bar": round(flip_rate, 4),
                "regime_like_if_flip_rate_lt_0p10": "REGIME"
                if flip_rate < 0.10
                else ("MIXED" if flip_rate < 0.20 else "NOISE"),
            }
        )

    df_3 = pd.DataFrame(rows_3)
    df_3.to_csv(OUT_DIR / "regime_persistence.csv", index=False)
    print(df_3.to_string(index=False))

    # ============================================================================
    # 4. regime_cross_cohort_overlap.csv — pairwise extreme-regime co-occurrence
    # ============================================================================
    print("\n[regime_eda] (4/5) regime_cross_cohort_overlap.csv")
    # Build per-symbol extreme-regime mask aligned on open_time (intersection of IS)
    sym_masks: dict[str, pd.Series] = {}
    for sym, sub in sym_to_df.items():
        s = sub.dropna(subset=["funding_rate_zscore_30"]).set_index("open_time")
        sym_masks[sym] = (s["funding_rate_zscore_30"].abs() > REGIME_THRESHOLD).astype(int)

    # Align all on common open_time index (intersection)
    common_idx = sym_masks["BTCUSDT"].index
    for sym in V1_SYMBOLS[1:]:
        common_idx = common_idx.intersection(sym_masks[sym].index)
    print(f"  Common IS bars across all 5 symbols: {len(common_idx)}")

    aligned: pd.DataFrame = pd.DataFrame(
        {sym: sym_masks[sym].reindex(common_idx) for sym in V1_SYMBOLS}, index=common_idx
    )
    rows_4: list[dict] = []
    for i, sym_a in enumerate(V1_SYMBOLS):
        for sym_b in V1_SYMBOLS[i + 1 :]:
            both_extreme = ((aligned[sym_a] == 1) & (aligned[sym_b] == 1)).mean()
            a_extreme = (aligned[sym_a] == 1).mean()
            b_extreme = (aligned[sym_b] == 1).mean()
            # Conditional P(B extreme | A extreme)
            if a_extreme > 0:
                cond_b_given_a = both_extreme / a_extreme
            else:
                cond_b_given_a = 0.0
            if b_extreme > 0:
                cond_a_given_b = both_extreme / b_extreme
            else:
                cond_a_given_b = 0.0
            corr = aligned[[sym_a, sym_b]].corr().iloc[0, 1]
            rows_4.append(
                {
                    "sym_a": sym_a,
                    "sym_b": sym_b,
                    "both_extreme_pct": round(both_extreme, 4),
                    "a_extreme_pct": round(a_extreme, 4),
                    "b_extreme_pct": round(b_extreme, 4),
                    "P(B_extreme|A_extreme)": round(cond_b_given_a, 4),
                    "P(A_extreme|B_extreme)": round(cond_a_given_b, 4),
                    "pearson_corr": round(corr, 4),
                }
            )
    df_4 = pd.DataFrame(rows_4)
    df_4.to_csv(OUT_DIR / "regime_cross_cohort_overlap.csv", index=False)
    print(df_4.to_string(index=False))

    # ============================================================================
    # 5. regime_oracle_attribution.csv — predicted IS PnL Δ from regime-conditional
    # ============================================================================
    print("\n[regime_eda] (5/5) regime_oracle_attribution.csv")
    # For each cohort, what would happen if we trained 2 sub-models PERFECTLY (oracle):
    #   - Use extreme-regime sub-model on extreme-regime trades
    #   - Use normal-regime sub-model on normal-regime trades
    # ORACLE assumes per-regime sub-models perfectly capture per-regime PnL distributions.
    # In reality, the model retrains and basin relocates (Jaccard ~10% per /022). The ORACLE
    # bound is a CEILING, NOT a forecast — per `feedback_v3_oracle_eda_validity.md`.

    rows_5: list[dict] = []
    for cohort_name, syms in COHORT_MAP.items():
        sym_set = set(syms)
        cohort_trades_is = base_trades_is[base_trades_is["symbol"].isin(sym_set)].copy()
        # Lookup z30 at each trade
        z30_per_trade: list[float] = []
        for _, trow in cohort_trades_is.iterrows():
            sym = trow["symbol"]
            ot = int(trow["open_time"])
            sub = sym_to_df[sym]
            idx = sub["open_time"].searchsorted(ot, side="right") - 1
            if 0 <= idx < len(sub):
                z30_per_trade.append(sub.iloc[idx]["funding_rate_zscore_30"])
            else:
                z30_per_trade.append(np.nan)
        cohort_trades_is["z30_at_open"] = z30_per_trade
        valid = cohort_trades_is.dropna(subset=["z30_at_open"])

        extreme = valid[valid["z30_at_open"].abs() > REGIME_THRESHOLD]
        normal = valid[valid["z30_at_open"].abs() <= REGIME_THRESHOLD]

        # Baseline cohort total weighted PnL
        baseline_pnl = float(valid["weighted_pnl"].sum())
        extreme_pnl = float(extreme["weighted_pnl"].sum())
        normal_pnl = float(normal["weighted_pnl"].sum())

        # ORACLE upper-bound: keep all longs IF extreme regime LONG PnL > 0, else flip to shorts
        # And same for normal regime. This is the "perfect regime-direction conditioning" ceiling.
        # Compute per (regime, direction):
        def regime_pnl_max(regime_df: pd.DataFrame) -> float:
            long_pnl = float(regime_df[regime_df["direction"] == 1]["weighted_pnl"].sum())
            short_pnl = float(regime_df[regime_df["direction"] == -1]["weighted_pnl"].sum())
            # Oracle picks better direction in this regime — picks each sub-model
            # to take the direction whose IS PnL was already positive
            return max(long_pnl, 0.0) + max(short_pnl, 0.0)

        oracle_extreme = regime_pnl_max(extreme)
        oracle_normal = regime_pnl_max(normal)
        oracle_total = oracle_extreme + oracle_normal
        oracle_delta_vs_baseline = oracle_total - baseline_pnl

        rows_5.append(
            {
                "cohort": cohort_name,
                "n_extreme_trades": len(extreme),
                "n_normal_trades": len(normal),
                "baseline_extreme_pnl_pct": round(extreme_pnl, 4),
                "baseline_normal_pnl_pct": round(normal_pnl, 4),
                "baseline_total_pnl_pct": round(baseline_pnl, 4),
                "oracle_extreme_pnl_pct": round(oracle_extreme, 4),
                "oracle_normal_pnl_pct": round(oracle_normal, 4),
                "oracle_total_pnl_pct": round(oracle_total, 4),
                "oracle_delta_vs_baseline_pp": round(oracle_delta_vs_baseline, 4),
            }
        )

    df_5 = pd.DataFrame(rows_5)
    df_5.to_csv(OUT_DIR / "regime_oracle_attribution.csv", index=False)
    print(df_5.to_string(index=False))

    print("\n[regime_eda] All 5 outputs written to:", OUT_DIR)


if __name__ == "__main__":
    main()
