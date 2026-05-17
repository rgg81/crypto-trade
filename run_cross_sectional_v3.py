"""Cross-sectional ranking model runner — iter-v3/088.

Implements the Phase-6 A5/A6 build stages:
  A5 — cross-sectional backtest path
  A6 — report emission (comparison.csv, rank-IC report, dsr.json, etc.)

This is a SEPARATE runner from run_baseline_v3.py so the legacy per-symbol
path stays intact.  The cross-sectional path trades XS_UNIVERSE (22 symbols)
rather than the 3-symbol V3_MODELS.

Usage:
    uv run python run_cross_sectional_v3.py
    uv run python run_cross_sectional_v3.py --n-trials 35 --exploration
    uv run python run_cross_sectional_v3.py --skip-features     # reuse parquets
    uv run python run_cross_sectional_v3.py --smoke-test        # fast IS-only smoke
    uv run python run_cross_sectional_v3.py --clean-oof         # re-run from scratch

Correctness guarantees:
  - OOS_CUTOFF_DATE = 2025-03-24 and training_months = 24 are IMMUTABLE.
  - XS_REQUIRED_GAP = 88 asserted at CPCV call-site via expected_gap.
  - Walk-forward train_end_ms = test_start_ms - embargo_ms (e149e9d fix).
  - The cross-sectional label's H=3 forward window never overlaps a test row.
  - Feature columns passed explicitly (no auto-discovery).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.features_v3 import (
    V3_EXCLUDED_SYMBOLS,
    V3_FEATURE_COLUMNS_TOP_N,
)
from crypto_trade.strategies.ml.cross_sectional import (
    XS_DROP_FEATURES,
    XS_HORIZON,
    XS_MIN_SYMBOLS_PER_BAR,
    XS_REQUIRED_GAP,
    XS_UNIVERSE,
    CrossSectionalRankStrategy,
    _generate_xs_monthly_splits,
    build_cross_sectional_panel,
    compute_oos_rank_ic,
    label_cross_sectional_rank,
    run_cross_sectional_backtest,
)
from crypto_trade.strategies.ml.validation_v3 import (
    PBOResult,
    combinatorial_purged_cv,
)

# ============================================================
# Constants — DO NOT CHANGE
# ============================================================
OOS_CUTOFF_DATE = "2025-03-24"  # IMMUTABLE
TRAINING_MONTHS = 24  # IMMUTABLE
ITERATION_LABEL = "v3-088"
REPORTS_DIR = Path("reports-v3")
FEATURES_DIR = Path("data/features_v3")
DATA_DIR = Path("data")

# Cross-sectional features: 14-feature /059 anchor minus btc_ret_14d.
XS_FEATURE_COLUMNS: list[str] = [
    c for c in V3_FEATURE_COLUMNS_TOP_N if c not in XS_DROP_FEATURES
]  # 13 features

# CPCV parameters (pooled cross-sectional path).
# XS_REQUIRED_GAP = 88 = (H+1)*N_symbols = (3+1)*22.
# This is DIFFERENT from REQUIRED_GAP = 66 (legacy per-symbol path).
CPCV_N_SPLITS = 10
CPCV_N_TEST_SPLITS = 2
CPCV_EMBARGO = 27  # ~1% of 24-month T ≈ 2742 candles * 0.01


# ============================================================
# Pre-flight checks
# ============================================================


def _verify_branch() -> None:
    branch = subprocess.check_output(
        ["git", "--no-optional-locks", "branch", "--show-current"],
        text=True,
    ).strip()
    allowed = branch.startswith("iteration-v3/") or branch in ("quant-research", "main")
    if not allowed:
        raise RuntimeError(
            f"Cross-sectional v3 runner must run from iteration-v3/*, "
            f"quant-research, or main; got: {branch}"
        )


def _verify_xs_universe() -> None:
    """Hard assert: no v1/v2 symbols in XS_UNIVERSE."""
    overlap = set(XS_UNIVERSE) & set(V3_EXCLUDED_SYMBOLS)
    if overlap:
        raise RuntimeError(
            f"XS_UNIVERSE contains v1/v2 symbols: {sorted(overlap)}\n"
            f"V3_EXCLUDED_SYMBOLS = {V3_EXCLUDED_SYMBOLS}"
        )
    # Verify XS_REQUIRED_GAP formula.
    expected_gap = (XS_HORIZON + 1) * len(XS_UNIVERSE)
    if XS_REQUIRED_GAP != expected_gap:
        raise RuntimeError(
            f"XS_REQUIRED_GAP={XS_REQUIRED_GAP} != (H+1)*N={expected_gap}. "
            "Fix the XS_REQUIRED_GAP constant in cross_sectional.py."
        )


def _verify_data_freshness(symbols: tuple[str, ...], max_lag_hours: float = 16.0) -> None:
    """Verify kline CSVs are fresh enough.

    A symbol passes if:
      (a) its last bar is within max_lag_hours of now (actively trading), OR
      (b) its last bar is past OOS_CUTOFF_MS (it was active through the full IS+OOS
          evaluation window, even if subsequently delisted).

    This handles delisted symbols that were valid IS+OOS candidates (e.g., EOSUSDT
    delisted after the OOS evaluation window closed).
    """
    now_ms = int(time.time() * 1000)
    stale: list[tuple[str, float]] = []
    for sym in symbols:
        p = DATA_DIR / sym / "8h.csv"
        if not p.exists():
            raise RuntimeError(f"Cross-sectional runner: missing CSV for {sym} at {p}")
        df = pd.read_csv(p, usecols=["close_time"])
        last_close = int(df["close_time"].max())
        lag_h = (now_ms - last_close) / 3_600_000
        # Accept if fresh (within lag window) OR if data extends past OOS cutoff
        # (symbol may be delisted but its IS+OOS data is complete).
        if lag_h > max_lag_hours and last_close < OOS_CUTOFF_MS:
            stale.append((sym, round(lag_h, 1)))
    if stale:
        raise RuntimeError(
            f"Cross-sectional runner: STALE DATA (>{max_lag_hours}h lag AND "
            f"last bar before OOS_CUTOFF_MS): {stale}. "
            f"Run `uv run crypto-trade fetch --symbols <syms> --intervals 8h`"
        )


def _verify_feature_columns() -> None:
    """Assert 13 cross-sectional features (14 minus btc_ret_14d)."""
    if len(XS_FEATURE_COLUMNS) != 13:
        raise RuntimeError(
            f"XS_FEATURE_COLUMNS has {len(XS_FEATURE_COLUMNS)} columns — expected 13. "
            "The cross-sectional feature set is V3_FEATURE_COLUMNS_TOP_N minus btc_ret_14d."
        )
    if "btc_ret_14d" in XS_FEATURE_COLUMNS:
        raise RuntimeError(
            "btc_ret_14d FOUND in XS_FEATURE_COLUMNS — must be dropped (zero "
            "cross-sectional dispersion, EDA T6). Check XS_DROP_FEATURES."
        )


def _verify_xs_gap_assertion() -> None:
    """Self-assert: XS_REQUIRED_GAP == 88."""
    expected = (XS_HORIZON + 1) * len(XS_UNIVERSE)
    assert XS_REQUIRED_GAP == expected, (
        f"XS_REQUIRED_GAP={XS_REQUIRED_GAP} != (H+1)*N={expected}. "
        "This constant governs label look-ahead safety — check cross_sectional.py."
    )
    print(
        f"[preflight] XS_REQUIRED_GAP={XS_REQUIRED_GAP} == "
        f"(H={XS_HORIZON}+1)*N={len(XS_UNIVERSE)} — PASS"
    )


# ============================================================
# Feature generation
# ============================================================


def _generate_xs_features(symbols: list[str]) -> None:
    """Generate v3 feature parquets for all XS_UNIVERSE symbols."""
    cmd = [
        "uv",
        "run",
        "crypto-trade",
        "features",
        "--symbols",
        ",".join(symbols),
        "--interval",
        "8h",
        "--track",
        "v3",
        "--format",
        "parquet",
        "--workers",
        "4",
    ]
    print(f"[features] Generating v3 features for {len(symbols)} XS symbols...")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        raise RuntimeError(f"Feature generation failed with exit code {result.returncode}")
    print("[features] Feature generation complete.")


# ============================================================
# CPCV on IS candle sequence
# ============================================================


def _compute_xs_cpcv(
    panel_is: pd.DataFrame,
    labels_is: pd.Series,
    report_dir: Path,
    n_trials: int,
    seed: int = 42,
) -> tuple[pd.DataFrame, PBOResult]:
    """Run CPCV on the IS pooled panel.

    Uses XS_REQUIRED_GAP=88 (asserted via expected_gap).

    Returns (cpcv_df, pbo_result).
    """
    # The IS panel is sorted by (open_time, symbol).  CPCV operates on
    # the n_IS_timestamps sequence (one "sample" per unique timestamp).
    is_timestamps = np.sort(panel_is["open_time"].unique())
    n_samples = len(is_timestamps)

    print(f"[cpcv] IS timestamps: {n_samples}, XS_REQUIRED_GAP={XS_REQUIRED_GAP}")

    splits = combinatorial_purged_cv(
        n_samples=n_samples,
        n_splits=CPCV_N_SPLITS,
        n_test_splits=CPCV_N_TEST_SPLITS,
        gap=XS_REQUIRED_GAP,
        embargo=CPCV_EMBARGO,
        expected_gap=XS_REQUIRED_GAP,  # hard self-assertion
    )

    # For each path, compute a "Sharpe proxy" from the label grades.
    # In a full backtest CPCV, we would run the model on each path's test fold.
    # For the IS-only CPCV diagnostic we use the label-based equal-weight book
    # return as the proxy: long grade-0 symbols, short grade-2 symbols at each
    # IS timestamp in the test fold.
    def _path_proxy_sharpe(test_idx: np.ndarray) -> float:
        """Equal-weight label-based long-short return proxy."""
        test_ts = is_timestamps[test_idx]
        path_rets: list[float] = []
        for ts in test_ts:
            ts_mask = panel_is["open_time"] == ts
            sub = panel_is[ts_mask].copy()
            sub_labels = labels_is[ts_mask].values
            if len(sub) < XS_MIN_SYMBOLS_PER_BAR:
                continue
            # Long grade-0, short grade-2.
            long_idx = np.where(sub_labels == 0)[0]
            short_idx = np.where(sub_labels == 2)[0]
            if len(long_idx) == 0 or len(short_idx) == 0:
                continue
            # Equal-weight 1-bar return proxy: close-to-close.
            close_vals = sub["close"].values
            if len(close_vals) < 2:
                continue
            # Use label grades as proxy for realized return direction.
            long_ret = float(np.mean(sub_labels[long_idx]))  # higher label = more positive ret
            short_ret = float(np.mean(sub_labels[short_idx]))  # short the winners
            path_rets.append(long_ret - short_ret)
        if len(path_rets) < 2:
            return 0.0
        arr = np.array(path_rets)
        return float(arr.mean() / arr.std()) if arr.std() > 1e-10 else 0.0

    path_sharpes: list[float] = []
    for train_idx, test_idx in splits:
        path_sharpes.append(_path_proxy_sharpe(test_idx))

    path_sharpes_arr = np.array(path_sharpes)
    frac_pos = float(np.mean(path_sharpes_arr > 0))
    q25, q50, q75 = (
        (
            float(np.percentile(path_sharpes_arr, 25)),
            float(np.percentile(path_sharpes_arr, 50)),
            float(np.percentile(path_sharpes_arr, 75)),
        )
        if len(path_sharpes_arr) >= 4
        else (float("nan"), float("nan"), float("nan"))
    )

    cpcv_df = pd.DataFrame(
        {
            "path_id": list(range(len(path_sharpes))),
            "sharpe": path_sharpes,
            "max_dd": [0.0] * len(path_sharpes),  # not computed in proxy mode
            "n_trades": [0] * len(path_sharpes),  # not applicable
        }
    )

    pbo_result = PBOResult(
        pbo=None,  # PBO requires a 2D matrix (multiple strategies)
        frac_positive_paths=frac_pos,
        path_sharpe_quartiles=(q25, q50, q75),
        n_splits_evaluated=len(splits),
        note=(
            f"Cross-sectional CPCV label-proxy: {len(splits)} paths, "
            f"frac_positive={frac_pos:.3f}, Q50={q50:.4f}. "
            f"XS_REQUIRED_GAP={XS_REQUIRED_GAP} asserted."
        ),
    )
    print(f"[cpcv] {pbo_result.note}")
    return cpcv_df, pbo_result


# ============================================================
# Report emission (A6)
# ============================================================


def _write_xs_reports(
    results: pd.DataFrame,
    rank_ic_stats: dict,
    pbo_result: PBOResult,
    cpcv_df: pd.DataFrame,
    report_dir: Path,
    n_trials: int,
    ensemble_size: int,
) -> None:
    """Write all A6 report files for the cross-sectional backtest."""
    report_dir.mkdir(parents=True, exist_ok=True)
    is_dir = report_dir / "in_sample"
    oos_dir = report_dir / "out_of_sample"
    is_dir.mkdir(exist_ok=True)
    oos_dir.mkdir(exist_ok=True)

    # Split results into IS and OOS.
    is_results = results[~results["is_oos"]].copy()
    oos_results = results[results["is_oos"]].copy()

    # Per-split net_pnl to monthly summary.
    def _monthly_pnl(sub: pd.DataFrame) -> pd.DataFrame:
        if sub.empty:
            return pd.DataFrame(columns=["month", "net_pnl"])
        sub = sub.copy()
        sub["month"] = sub["open_time"].apply(
            lambda t: (
                __import__("datetime")
                .datetime.fromtimestamp(t / 1000, tz=__import__("datetime").timezone.utc)
                .strftime("%Y-%m")
            )
        )
        return sub.groupby("month")["net_pnl"].sum().reset_index()

    is_monthly = _monthly_pnl(is_results)
    oos_monthly = _monthly_pnl(oos_results)

    # Sharpe.
    def _monthly_sharpe(monthly_df: pd.DataFrame) -> float:
        if len(monthly_df) < 2:
            return 0.0
        s = monthly_df["net_pnl"]
        return float(s.mean() / s.std()) if s.std() > 1e-10 else 0.0

    is_ms = _monthly_sharpe(is_monthly)
    oos_ms = _monthly_sharpe(oos_monthly)

    # Max drawdown on cumulative net_pnl.
    def _max_dd(sub: pd.DataFrame) -> float:
        if sub.empty:
            return 0.0
        cum = sub.sort_values("open_time")["net_pnl"].cumsum().values
        peak = np.maximum.accumulate(cum)
        dd = peak - cum
        # peak.max() can be 0 or negative when all cumulative PnL is <= 0;
        # clamp to abs to avoid division by a tiny positive that inflates the ratio.
        peak_max = float(peak.max())
        denom = max(abs(peak_max), 1e-10)
        return float(dd.max() / denom) if len(dd) > 0 else 0.0

    is_mdd = _max_dd(is_results)
    oos_mdd = _max_dd(oos_results)

    # Per-symbol attribution.
    def _per_sym(sub: pd.DataFrame) -> pd.DataFrame:
        if sub.empty:
            return pd.DataFrame()
        grp = (
            sub.groupby("symbol")
            .agg(
                weighted_pnl=("net_pnl", "sum"),
                n_trades=("net_pnl", "count"),
            )
            .reset_index()
        )
        total_pnl = grp["weighted_pnl"].abs().sum()
        grp["concentration_pct"] = grp["weighted_pnl"].abs() / max(total_pnl, 1e-10) * 100
        return grp

    is_per_sym = _per_sym(is_results)
    oos_per_sym = _per_sym(oos_results)

    # Write per-split CSVs.
    is_results.to_csv(is_dir / "trades.csv", index=False)
    oos_results.to_csv(oos_dir / "trades.csv", index=False)
    is_monthly.to_csv(is_dir / "monthly_pnl.csv", index=False)
    oos_monthly.to_csv(oos_dir / "monthly_pnl.csv", index=False)
    is_per_sym.to_csv(is_dir / "per_symbol.csv", index=False)
    oos_per_sym.to_csv(oos_dir / "per_symbol.csv", index=False)

    # Rank-IC CSV.
    rank_ic_df = pd.DataFrame([rank_ic_stats])
    rank_ic_df.to_csv(report_dir / "rank_ic.csv", index=False)

    # CPCV paths CSV.
    cpcv_df.to_csv(report_dir / "cpcv_paths.csv", index=False)

    # comparison.csv.
    n_trials_total = n_trials * ensemble_size
    oos_is_ratio = (oos_ms / is_ms) if abs(is_ms) > 1e-10 else float("nan")
    comparison_rows = [
        {
            "metric": "monthly_sharpe",
            "in_sample": is_ms,
            "out_of_sample": oos_ms,
            "ratio": oos_is_ratio,
        },
        {
            "metric": "max_drawdown",
            "in_sample": is_mdd,
            "out_of_sample": oos_mdd,
            "ratio": oos_mdd / max(is_mdd, 1e-10),
        },
        {
            "metric": "n_trades",
            "in_sample": len(is_results),
            "out_of_sample": len(oos_results),
            "ratio": len(oos_results) / max(len(is_results), 1),
        },
        {
            "metric": "total_pnl",
            "in_sample": float(is_results["net_pnl"].sum()),
            "out_of_sample": float(oos_results["net_pnl"].sum()),
            "ratio": float("nan"),
        },
        {
            "metric": "rank_ic_mean",
            "in_sample": float("nan"),
            "out_of_sample": rank_ic_stats["mean_rank_ic"],
            "ratio": float("nan"),
        },
        {
            "metric": "frac_positive_paths",
            "in_sample": pbo_result.frac_positive_paths,
            "out_of_sample": float("nan"),
            "ratio": float("nan"),
        },
        {
            "metric": "n_trials",
            "in_sample": n_trials_total,
            "out_of_sample": float("nan"),
            "ratio": float("nan"),
        },
    ]
    pd.DataFrame(comparison_rows).to_csv(report_dir / "comparison.csv", index=False)

    # dsr.json.
    dsr_data = {
        "dsr": 0.0,  # not applicable for cross-sectional path at EXPLORATION
        "pbo": pbo_result.pbo if pbo_result.pbo is not None else float("nan"),
        "psr": 0.0,  # not applicable
        "frac_positive_paths": pbo_result.frac_positive_paths,
        "n_trials": n_trials_total,
        "n_eff": 0,  # not computed for cross-sectional path
        "rank_ic_mean_oos": rank_ic_stats["mean_rank_ic"],
        "rank_ic_std_oos": rank_ic_stats["std_rank_ic"],
        "rank_ic_n_timestamps": rank_ic_stats["n_timestamps"],
        "note": (
            "iter-v3/088 cross-sectional path: DSR/PSR not applicable at EXPLORATION. "
            f"Primary falsifier F1: OOS rank-IC={rank_ic_stats['mean_rank_ic']:.4f}. "
            f"F1 PASS if > 0, FAIL if <= 0."
        ),
    }
    with open(report_dir / "dsr.json", "w") as f:
        json.dump(dsr_data, f, indent=2)

    # Print summary.
    print("\n" + "=" * 60)
    print(f"CROSS-SECTIONAL BACKTEST SUMMARY — iter-{ITERATION_LABEL}")
    print("=" * 60)
    print(f"IS monthly Sharpe:  {is_ms:+.4f}")
    print(f"OOS monthly Sharpe: {oos_ms:+.4f}")
    ratio_str = f"{oos_is_ratio:.4f}" if not np.isnan(oos_is_ratio) else "N/A"
    print(f"OOS/IS ratio:       {ratio_str}")
    print(f"IS max drawdown:    {is_mdd:.4f}")
    print(f"OOS max drawdown:   {oos_mdd:.4f}")
    print(f"IS  n_bars:  {len(is_results)}")
    print(f"OOS n_bars:  {len(oos_results)}")
    print(
        f"OOS rank-IC: {rank_ic_stats['mean_rank_ic']:.4f} ± {rank_ic_stats['std_rank_ic']:.4f} "
        f"(n={rank_ic_stats['n_timestamps']} timestamps)"
    )
    print(f"frac_positive_paths (CPCV): {pbo_result.frac_positive_paths:.3f}")
    print(f"CPCV note: {pbo_result.note}")
    if rank_ic_stats["mean_rank_ic"] > 0:
        print("F1 (OOS rank-IC > 0): PASS — cross-sectional signal transferred OOS.")
    else:
        print("F1 (OOS rank-IC > 0): FAIL — cross-sectional signal did NOT transfer OOS.")
    print("=" * 60 + "\n")


# ============================================================
# Main runner
# ============================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cross-sectional ranking model runner — iter-v3/088"
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=35,
        help="Optuna trials per monthly model (default 35, EXPLORATION mode).",
    )
    parser.add_argument(
        "--skip-features",
        action="store_true",
        help="Skip feature generation (use existing parquets).",
    )
    parser.add_argument(
        "--exploration",
        action="store_true",
        help="EXPLORATION mode (default; single-seed Optuna).",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help=(
            "IS-only smoke test: train on first 12 months of IS, predict the "
            "next month, print rank-IC.  Fast sanity check (< 5 min)."
        ),
    )
    parser.add_argument(
        "--clean-oof",
        action="store_true",
        help="Delete any existing reports for this iteration before starting.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for Optuna TPE sampler (default 42).",
    )
    args = parser.parse_args()

    t_start = time.time()

    # Pre-flight.
    _verify_branch()
    _verify_xs_universe()
    _verify_feature_columns()
    _verify_xs_gap_assertion()
    _verify_data_freshness(XS_UNIVERSE)

    print(f"\nCross-Sectional v3 iter-{ITERATION_LABEL}")
    print(f"Universe: {len(XS_UNIVERSE)} symbols — XS_UNIVERSE")
    print(f"Features: {len(XS_FEATURE_COLUMNS)} cross-sectionally rank-normalized features")
    print(f"XS_REQUIRED_GAP: {XS_REQUIRED_GAP} = (H={XS_HORIZON}+1)*N={len(XS_UNIVERSE)}")
    print(f"Optuna n_trials: {args.n_trials}")
    print(f"OOS split: {OOS_CUTOFF_DATE} (IMMUTABLE)")
    print(f"Training months: {TRAINING_MONTHS} (IMMUTABLE)\n")

    # Clean existing reports if requested.
    report_dir = REPORTS_DIR / f"iteration_{ITERATION_LABEL}"
    if args.clean_oof and report_dir.exists():
        import shutil

        shutil.rmtree(report_dir)
        print(f"[CLEAN] Removed existing report dir: {report_dir}")

    # Feature generation.
    if not args.skip_features:
        _generate_xs_features(list(XS_UNIVERSE))
    else:
        print("[features] Skipping feature generation (--skip-features)")

    # Smoke-test shortcut.
    if args.smoke_test:
        _run_smoke_test(args)
        return

    # Build the pooled cross-sectional panel (all timestamps, IS + OOS).
    print("\n[panel] Building pooled cross-sectional panel...")
    panel = build_cross_sectional_panel(
        features_dir=FEATURES_DIR,
        symbols=XS_UNIVERSE,
        feature_columns=list(V3_FEATURE_COLUMNS_TOP_N),
    )
    print(
        f"[panel] {len(panel)} total rows "
        f"({panel['open_time'].nunique()} unique timestamps, "
        f"{panel['symbol'].nunique()} symbols)"
    )

    # Label: cross-sectional graded relevance {0, 1, 2}.
    print("[label] Computing cross-sectional rank labels (H=3)...")
    labels = label_cross_sectional_rank(panel, horizon=XS_HORIZON)
    n_valid = labels.notna().sum()
    print(f"[label] {n_valid} valid labels ({n_valid / len(labels):.1%} of panel rows)")

    # Create the strategy instance.
    strategy = CrossSectionalRankStrategy(
        training_months=TRAINING_MONTHS,
        n_trials=args.n_trials,
        feature_columns=XS_FEATURE_COLUMNS,
        features_dir=str(FEATURES_DIR),
        symbols=XS_UNIVERSE,
        horizon=XS_HORIZON,
        seed=args.seed,
        verbose=0,
    )

    # Run the full walk-forward backtest.
    print("\n[backtest] Running cross-sectional walk-forward backtest...")
    train_start_ms = int(panel[panel["open_time"] < OOS_CUTOFF_MS]["open_time"].min())
    results = run_cross_sectional_backtest(
        strategy=strategy,
        panel=panel,
        labels=labels,
        train_start_ms=train_start_ms,
        oos_cutoff_ms=OOS_CUTOFF_MS,
    )
    print(f"[backtest] {len(results)} bar-symbol rows produced.")

    if results.empty:
        print("ERROR: backtest produced no results. Exiting.")
        sys.exit(1)

    # OOS rank-IC (primary falsifier F1).
    print("\n[rank-IC] Computing OOS rank-IC...")
    rank_ic_stats = compute_oos_rank_ic(results)
    print(
        f"[rank-IC] mean={rank_ic_stats['mean_rank_ic']:.4f}, "
        f"std={rank_ic_stats['std_rank_ic']:.4f}, "
        f"n={rank_ic_stats['n_timestamps']}"
    )

    # IS-only CPCV.
    panel_is = panel[panel["open_time"] < OOS_CUTOFF_MS].copy()
    labels_is = labels[panel["open_time"] < OOS_CUTOFF_MS].copy()
    print("\n[cpcv] Running IS-only CPCV (label proxy)...")
    cpcv_df, pbo_result = _compute_xs_cpcv(
        panel_is,
        labels_is,
        report_dir,
        n_trials=args.n_trials,
        seed=args.seed,
    )

    # Write all reports.
    print("\n[reports] Writing report files...")
    _write_xs_reports(
        results=results,
        rank_ic_stats=rank_ic_stats,
        pbo_result=pbo_result,
        cpcv_df=cpcv_df,
        report_dir=report_dir,
        n_trials=args.n_trials,
        ensemble_size=1,  # single-seed EXPLORATION
    )

    elapsed = time.time() - t_start
    h, m = divmod(int(elapsed), 3600)
    m, s = divmod(m, 60)
    print(f"\nTotal wall-clock: {h}h {m:02d}m {s:02d}s")
    print(f"Reports at: {report_dir.resolve()}")
    print("\nOVERALL=READY-FOR-CRITIC")


def _run_smoke_test(args: argparse.Namespace) -> None:
    """IS-only smoke test: build panel, label, train one month, print rank-IC."""
    print("\n[smoke] IS-only smoke test (fast — single training month)...")

    panel = build_cross_sectional_panel(
        features_dir=FEATURES_DIR,
        symbols=XS_UNIVERSE,
        feature_columns=list(V3_FEATURE_COLUMNS_TOP_N),
    )
    panel_is = panel[panel["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    labels_all = label_cross_sectional_rank(panel_is, horizon=XS_HORIZON)

    # Use the first 12 IS months as training, predict the 13th.
    interval_ms = 8 * 3600 * 1000
    embargo_ms = XS_REQUIRED_GAP * interval_ms
    all_ts = np.sort(panel_is["open_time"].unique())
    splits = _generate_xs_monthly_splits(
        all_timestamps=all_ts,
        training_months=12,  # shorter for smoke test
        embargo_ms=embargo_ms,
    )
    if not splits:
        print("[smoke] ERROR: no splits generated. Exiting.")
        return

    split = splits[0]
    train_mask = (panel_is["open_time"] >= split["train_start_ms"]) & (
        panel_is["open_time"] < split["train_end_ms"]
    )
    train_panel = panel_is[train_mask].copy().reset_index(drop=True)
    train_labels = labels_all[train_mask].reset_index(drop=True)
    valid = train_labels.notna()
    train_panel_v = train_panel[valid].reset_index(drop=True)
    train_labels_v = train_labels[valid].reset_index(drop=True)

    strategy = CrossSectionalRankStrategy(
        training_months=12,
        n_trials=5,  # fast: 5 Optuna trials
        feature_columns=XS_FEATURE_COLUMNS,
        features_dir=str(FEATURES_DIR),
        symbols=XS_UNIVERSE,
        horizon=XS_HORIZON,
        seed=args.seed,
        verbose=0,
    )

    print(f"[smoke] Training on {len(train_panel_v)} rows for month {split['test_month']}...")
    t0 = time.time()
    is_ic = strategy._train_for_month(
        train_panel_v.sort_values(["open_time", "symbol"]).reset_index(drop=True),
        train_labels_v,
    )
    elapsed = time.time() - t0
    print(f"[smoke] IS rank-IC = {is_ic:.4f}  (trained in {elapsed:.1f}s)")

    # Score the test month.
    test_mask = (panel_is["open_time"] >= split["test_start_ms"]) & (
        panel_is["open_time"] < split["test_end_ms"]
    )
    test_panel = panel_is[test_mask].copy().reset_index(drop=True)
    test_labels = labels_all[test_mask].reset_index(drop=True)

    if not test_panel.empty and strategy._model is not None:
        scores = strategy.predict_ranking(test_panel)
        oos_ic = CrossSectionalRankStrategy._spearman_ic_by_timestamp(
            test_panel["open_time"].values, scores, test_labels.fillna(1).values.astype(int)
        )
        print(f"[smoke] OOS (1-month hold-out) rank-IC = {oos_ic:.4f}")
        n_ts = test_panel["open_time"].nunique()
        print(f"[smoke] Test rows: {len(test_panel)}, timestamps: {n_ts}")

    print("\n[smoke] Smoke test COMPLETE — architecture runs end-to-end.")
    print(
        f"[smoke] IS rank-IC={is_ic:.4f} (positive expected for reversal with sign-aligned labels)"
    )
    if is_ic > 0:
        print("[smoke] PASS — IS rank-IC > 0: model is learning the cross-sectional signal.")
    else:
        print("[smoke] NOTE — IS rank-IC <= 0: investigate label sign alignment.")


if __name__ == "__main__":
    main()
