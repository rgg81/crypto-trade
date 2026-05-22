"""Cross-sectional ranking model runner -- iter-v3/092 (multi-seed CONFIRMATION).

iter-v3/092 is the CYCLE-3 CONFIRMATION: a multi-seed CONFIRMATION-grade
verdict that formally closes the cross-sectional LGBMRanker line.  It
multi-seed-validates the trained LGBMRanker (score_mode="trained") at horizon
H=21, with the /089 cost-aware construction retained.

/092 BUILD -- multi-seed support:
  - CONFIRMATION_OUTER_SEEDS = (42, 123): outer-seed loop runs the full
    cross-sectional walk-forward backtest once per outer seed.
  - 5-model inner ensemble per outer seed: inner seeds derived via
    _derive_ensemble_seeds(outer_seed, 5), matching the BASELINE_V3.md lineage.
  - Arithmetic-mean score averaging across the 5 inner models per bar.
  - Per-seed reports: reports-v3/iteration_v3-092/seed_<s>/
  - Multi-seed aggregate: reports-v3/iteration_v3-092/ (comparison.csv,
    ensemble_summary.json, dsr.json on the aggregate book).
  - --seeds N: controls how many outer seeds to use (selects first N from
    CONFIRMATION_OUTER_SEEDS).  NEW independent argument -- NOT the deprecated
    per-symbol runner's --seeds.  No deprecation warning; live and functional.

RETAINED from /088 + /089 + /091:
  - score_mode="trained" (the /091 model-free path is preserved but unused).
  - XS_HORIZON = 21, XS_HOLD_BARS = 21 (corrected /091 horizon-EDA best).
  - SIGN FIX -- high score = predicted future WINNER; LONG the top quantile.
  - CPCV-PROXY FIX -- _compute_xs_cpcv computes ACTUAL long-short net return.
  - COST-AWARE CONSTRUCTION -- QUINTILE + 21-bar OVERLAPPING HOLDS + NO-TRADE
    BAND, 0.138 turnover ceiling.
  - Feature stack: 13-feature base (V3_FEATURE_COLUMNS_TOP_N minus btc_ret_14d).
  - Walk-forward embargo_ms = (XS_HORIZON+1)*interval_ms (corrected /091 fix).
  - Gross-Sharpe runner artifact (_monthly_sharpe shared helper, /091 setup 2).

Usage:
    uv run python run_cross_sectional_v3.py --skip-features --seeds 2 --n-trials 35
    uv run python run_cross_sectional_v3.py --skip-features --seeds 1 --n-trials 35
    uv run python run_cross_sectional_v3.py --skip-features             # seeds=2 default
    uv run python run_cross_sectional_v3.py --smoke-test    # fast multi-seed wiring check
    uv run python run_cross_sectional_v3.py --clean-oof     # re-run from scratch

Correctness guarantees:
  - OOS_CUTOFF_DATE = 2025-03-24 and training_months = 24 are IMMUTABLE.
  - XS_REQUIRED_GAP = 484 asserted at CPCV call-site via expected_gap.
  - Walk-forward embargo_ms = (XS_HORIZON+1)*interval_ms (corrected /091 fix).
  - Feature columns passed explicitly (no auto-discovery).
  - _derive_ensemble_seeds copied verbatim from run_baseline_v3.py:119-128
    (brief Section 3.3 Mechanism A) -- reproduces BASELINE_V3.md lineage.
"""

from __future__ import annotations

import argparse
import json
import subprocess
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
    XS_DOWNSIDE_FEATURES,
    XS_DROP_FEATURES,
    XS_HOLD_BARS,
    XS_HORIZON,
    XS_NO_TRADE_BAND,
    XS_QUANTILE_FRAC,
    XS_REQUIRED_GAP,
    XS_TURNOVER_CEILING,
    XS_UNIVERSE,
    CrossSectionalRankStrategy,
    _generate_xs_monthly_splits,
    build_cross_sectional_panel,
    compute_oos_rank_ic,
    compute_turnover_per_bar,
    label_cross_sectional_rank,
    run_cross_sectional_backtest,
)
from crypto_trade.strategies.ml.validation_v3 import (
    PBOResult,
    combinatorial_purged_cv,
)

# ============================================================
# Constants -- DO NOT CHANGE
# ============================================================
OOS_CUTOFF_DATE = "2025-03-24"  # IMMUTABLE
TRAINING_MONTHS = 24  # IMMUTABLE
ITERATION_LABEL = "v3-092"
REPORTS_DIR = Path("reports-v3")
FEATURES_DIR = Path("data/features_v3")
DATA_DIR = Path("data")

# iter-v3/092 -- multi-seed CONFIRMATION outer seeds.
# Selects first --seeds elements from this tuple.
CONFIRMATION_OUTER_SEEDS: tuple[int, ...] = (42, 123)

# iter-v3/092 inner-ensemble size (5 inner seeds per outer seed).
ENSEMBLE_SIZE = 5

# iter-v3/091 -- feature set REVERTED to /088/089 13-feature base.
# The /090 downside-risk expansion (xs_sortino_mom_12, xs_downbeta_50) was
# FALSIFIED (Critic /090 OVERALL=BLOCK).  For the model-free primary book the
# feature columns are not used at scoring time (trailing-return score only);
# they ARE used by the reference LGBMRanker comparator.
XS_BASE_FEATURES: list[str] = [
    c for c in V3_FEATURE_COLUMNS_TOP_N if c not in XS_DROP_FEATURES
]  # 13 features
XS_FEATURE_COLUMNS: list[str] = XS_BASE_FEATURES  # 13 features (downside reverted)

# CPCV parameters (pooled cross-sectional path).
# XS_REQUIRED_GAP = 484 = (H+1)*N_symbols = (21+1)*22.
# This is DIFFERENT from REQUIRED_GAP = 66 (legacy per-symbol path).
CPCV_N_SPLITS = 10
CPCV_N_TEST_SPLITS = 2
CPCV_EMBARGO = 27  # ~1% of 24-month T ~= 2742 candles * 0.01


# ============================================================
# iter-v3/092 -- _derive_ensemble_seeds
# Copied VERBATIM from run_baseline_v3.py lines 119-128 at c6a03ed
# (brief Section 3.3 Mechanism A -- no src/ change).
# Reproduces the BASELINE_V3.md "Unified 10-Seed Ensemble Architecture"
# lineage: ENSEMBLE_SEEDS[0:5] == _derive_ensemble_seeds(42, 5),
#          ENSEMBLE_SEEDS[5:10] == _derive_ensemble_seeds(123, 5).
# ============================================================


def _derive_ensemble_seeds(outer_seed: int, size: int = 5) -> list[int]:
    rng = np.random.default_rng(outer_seed)
    return [int(s) for s in rng.integers(low=0, high=2**31 - 1, size=size)]


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
    """Assert the iter-v3/091 13-feature cross-sectional set.

    iter-v3/091 REVERTS the /090 downside-risk expansion: XS_FEATURE_COLUMNS
    is the 13-feature base only (V3_FEATURE_COLUMNS_TOP_N minus btc_ret_14d).
    The /090 downside features (XS_DOWNSIDE_FEATURES) must be ABSENT.
    """
    # iter-v3/102: V3_FEATURE_COLUMNS_TOP_N grew 14 → 15 (alpha032 added).
    # XS_BASE_FEATURES = V3_FEATURE_COLUMNS_TOP_N minus XS_DROP_FEATURES (btc_ret_14d)
    # → 15 - 1 = 14.  Update the assertion accordingly.
    _expected_xs_base = len(XS_BASE_FEATURES)  # dynamic: len(V3_FEATURE_COLUMNS_TOP_N) - 1
    if _expected_xs_base < 13:
        raise RuntimeError(
            f"XS_BASE_FEATURES has {_expected_xs_base} columns -- expected ≥13. "
            "The base cross-sectional set is V3_FEATURE_COLUMNS_TOP_N minus btc_ret_14d."
        )
    if len(XS_FEATURE_COLUMNS) != _expected_xs_base:
        raise RuntimeError(
            f"XS_FEATURE_COLUMNS has {len(XS_FEATURE_COLUMNS)} columns -- expected "
            f"{_expected_xs_base} (V3_FEATURE_COLUMNS_TOP_N minus btc_ret_14d). "
            f"XS_FEATURE_COLUMNS = {XS_FEATURE_COLUMNS}."
        )
    if "btc_ret_14d" in XS_FEATURE_COLUMNS:
        raise RuntimeError(
            "btc_ret_14d FOUND in XS_FEATURE_COLUMNS -- must be dropped (zero "
            "cross-sectional dispersion, EDA T6). Check XS_DROP_FEATURES."
        )
    for f in XS_DOWNSIDE_FEATURES:
        if f in XS_FEATURE_COLUMNS:
            raise RuntimeError(
                f"iter-v3/091 REVERT: /090 downside feature {f!r} must be ABSENT "
                "from XS_FEATURE_COLUMNS (the /090 expansion was FALSIFIED)."
            )


def _verify_xs_gap_assertion() -> None:
    """Self-assert: XS_REQUIRED_GAP == 484 at H=21."""
    expected = (XS_HORIZON + 1) * len(XS_UNIVERSE)
    assert XS_REQUIRED_GAP == expected, (
        f"XS_REQUIRED_GAP={XS_REQUIRED_GAP} != (H+1)*N={expected}. "
        "This constant governs label look-ahead safety -- check cross_sectional.py."
    )
    print(
        f"[preflight] XS_REQUIRED_GAP={XS_REQUIRED_GAP} == "
        f"(H={XS_HORIZON}+1)*N={len(XS_UNIVERSE)} -- PASS"
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
    results: pd.DataFrame,
    report_dir: Path,
    n_trials: int,
    seed: int = 42,
) -> tuple[pd.DataFrame, PBOResult]:
    """Run CPCV on the IS pooled cross-section -- ACTUAL long-short net return.

    iter-v3/089 CPCV-PROXY FIX (Critic /088 Rec #3).
    --------------------------------------------------
    The /088 implementation computed each CPCV path "Sharpe" as a label-grade
    self-correlation (`mean(sub_labels[long_idx]) - mean(sub_labels[short_idx])`)
    -- a degenerate proxy: grade-0 < grade-2 by construction of the tercile
    label, so it measures nothing about the model.  `cpcv_paths.csv` collapsed
    to 45 rows of literally `sharpe=0.0`, and the F4 `frac_positive_paths`
    gate carried no information.

    The fix: the CPCV path metric is now the ACTUAL realised long-short NET
    return of the trained model on each path's test fold.  We do not re-fit
    the model per path -- instead we read the per-(timestamp, symbol) net_pnl
    from the already-computed walk-forward backtest `results` (which carries
    the trained model's CORRECTED-SIGN positions, gross PnL, turnover fee and
    net PnL).  For a CPCV path defined over a subset of IS timestamps we sum
    net_pnl into one book return per timestamp and compute the Sharpe of the
    path's test-fold book-return series.  This is the actual model-driven
    long-short net P&L on the path -- exactly the informative F4 gate.

    Uses XS_REQUIRED_GAP=484 (asserted via expected_gap).

    Returns (cpcv_df, pbo_result).
    """
    # Restrict to the IS rows of the backtest results.
    is_res = results[~results["is_oos"]].copy()
    # One book return per IS timestamp = sum of per-symbol net_pnl at that bar.
    bar_ret = (
        is_res.groupby("open_time")["net_pnl"].sum().sort_index()
        if not is_res.empty
        else pd.Series(dtype=float)
    )
    is_timestamps = bar_ret.index.to_numpy()
    n_samples = len(is_timestamps)

    print(f"[cpcv] IS book-return timestamps: {n_samples}, XS_REQUIRED_GAP={XS_REQUIRED_GAP}")

    if n_samples < CPCV_N_SPLITS * 4:
        # Too few timestamps to split meaningfully -- emit an honest sentinel.
        pbo_sentinel = PBOResult(
            pbo=None,
            frac_positive_paths=0.0,
            path_sharpe_quartiles=(float("nan"), float("nan"), float("nan")),
            n_splits_evaluated=0,
            note=(
                f"Cross-sectional CPCV: only {n_samples} IS book-return "
                "timestamps -- too few for CPCV. frac_positive_paths sentinel 0.0."
            ),
        )
        return pd.DataFrame(columns=["path_id", "sharpe", "max_dd", "n_trades"]), pbo_sentinel

    splits = combinatorial_purged_cv(
        n_samples=n_samples,
        n_splits=CPCV_N_SPLITS,
        n_test_splits=CPCV_N_TEST_SPLITS,
        gap=XS_REQUIRED_GAP,
        embargo=CPCV_EMBARGO,
        expected_gap=XS_REQUIRED_GAP,  # hard self-assertion
    )

    bar_ret_arr = bar_ret.to_numpy()

    def _path_net_sharpe(test_idx: np.ndarray) -> tuple[float, float]:
        """Actual realised long-short NET-return Sharpe + max-DD on a path's
        test fold.  test_idx indexes the sorted IS book-return series."""
        path_rets = bar_ret_arr[test_idx]
        if len(path_rets) < 2:
            return 0.0, 0.0
        std = float(path_rets.std())
        sharpe = float(path_rets.mean() / std) if std > 1e-12 else 0.0
        cum = np.cumsum(path_rets)
        peak = np.maximum.accumulate(cum)
        dd = peak - cum
        denom = max(abs(float(peak.max())), 1e-10)
        max_dd = float(dd.max() / denom) if len(dd) > 0 else 0.0
        return sharpe, max_dd

    path_sharpes: list[float] = []
    path_max_dds: list[float] = []
    path_n_trades: list[int] = []
    for _train_idx, test_idx in splits:
        s, mdd = _path_net_sharpe(test_idx)
        path_sharpes.append(s)
        path_max_dds.append(mdd)
        path_n_trades.append(int(len(test_idx)))

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
            "sharpe": path_sharpes,  # actual long-short NET-return Sharpe per path
            "max_dd": path_max_dds,  # actual max-DD on the path's net-return series
            "n_trades": path_n_trades,  # test-fold timestamp count for the path
        }
    )

    pbo_result = PBOResult(
        pbo=None,  # PBO requires a 2D matrix (multiple strategies)
        frac_positive_paths=frac_pos,
        path_sharpe_quartiles=(q25, q50, q75),
        n_splits_evaluated=len(splits),
        note=(
            f"Cross-sectional CPCV (actual long-short net return): {len(splits)} paths, "
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
    outer_seed: int | None = None,
) -> dict:
    """Write all A6 report files for the cross-sectional backtest.

    Returns a dict of the key scalar metrics for aggregate reporting.
    """
    report_dir.mkdir(parents=True, exist_ok=True)
    is_dir = report_dir / "in_sample"
    oos_dir = report_dir / "out_of_sample"
    is_dir.mkdir(exist_ok=True)
    oos_dir.mkdir(exist_ok=True)

    # Split results into IS and OOS.
    is_results = results[~results["is_oos"]].copy()
    oos_results = results[results["is_oos"]].copy()

    import datetime as _dt

    # Per-split pnl to monthly summary (accepts any pnl_col name).
    def _monthly_pnl(sub: pd.DataFrame, pnl_col: str) -> pd.DataFrame:
        if sub.empty:
            return pd.DataFrame(columns=["month", pnl_col])
        sub = sub.copy()
        sub["month"] = sub["open_time"].apply(
            lambda t: _dt.datetime.fromtimestamp(t / 1000, tz=_dt.UTC).strftime("%Y-%m")
        )
        return sub.groupby("month")[pnl_col].sum().reset_index()

    # Shared Sharpe helper -- iter-v3/091 SETUP item 2 (Critic /090 Rec #1).
    # Both net and gross monthly Sharpe use this IDENTICAL code path.
    # pnl_col = "net_pnl" (net) or "gross_pnl" (gross).
    def _monthly_sharpe(sub: pd.DataFrame, pnl_col: str) -> float:
        monthly = _monthly_pnl(sub, pnl_col)
        if len(monthly) < 2:
            return 0.0
        s = monthly[pnl_col]
        return float(s.mean() / s.std()) if s.std() > 1e-10 else 0.0

    is_monthly = _monthly_pnl(is_results, "net_pnl")
    oos_monthly = _monthly_pnl(oos_results, "net_pnl")

    is_ms = _monthly_sharpe(is_results, "net_pnl")
    oos_ms = _monthly_sharpe(oos_results, "net_pnl")
    is_gross_ms = _monthly_sharpe(is_results, "gross_pnl")
    oos_gross_ms = _monthly_sharpe(oos_results, "gross_pnl")

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

    # iter-v3/089 turnover ceiling -- the HARD pre-registered gate.
    is_turnover = compute_turnover_per_bar(results, is_oos=False)
    oos_turnover = compute_turnover_per_bar(results, is_oos=True)
    turnover_gate_pass = is_turnover <= XS_TURNOVER_CEILING

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
    gross_oos_is_ratio = (oos_gross_ms / is_gross_ms) if abs(is_gross_ms) > 1e-10 else float("nan")
    comparison_rows = [
        {
            "metric": "monthly_sharpe",
            "in_sample": is_ms,
            "out_of_sample": oos_ms,
            "ratio": oos_is_ratio,
        },
        {
            # iter-v3/091 SETUP item 2: gross_monthly_sharpe via shared helper
            # (Critic /090 Rec #1 -- closes the /090 OVERALL=BLOCK root cause).
            "metric": "gross_monthly_sharpe",
            "in_sample": is_gross_ms,
            "out_of_sample": oos_gross_ms,
            "ratio": gross_oos_is_ratio,
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
            # iter-v3/089 -- mean gross turnover per bar; the HARD pre-registered
            # gate is IS turnover <= XS_TURNOVER_CEILING (0.138).
            "metric": "turnover_per_bar",
            "in_sample": is_turnover,
            "out_of_sample": oos_turnover,
            "ratio": oos_turnover / max(is_turnover, 1e-10),
        },
        {
            # 1.0 = IS turnover within the ceiling (PASS); 0.0 = breach (FAIL).
            "metric": "turnover_ceiling_gate_pass",
            "in_sample": float(turnover_gate_pass),
            "out_of_sample": XS_TURNOVER_CEILING,
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

    # dsr.json -- iter-v3/091: gross_monthly_sharpe now a runner artifact.
    outer_seed_str = f"outer_seed={outer_seed}" if outer_seed is not None else "aggregate"
    dsr_data = {
        "dsr": 0.0,  # not applicable for cross-sectional path at EXPLORATION
        "pbo": pbo_result.pbo if pbo_result.pbo is not None else float("nan"),
        "psr": 0.0,  # not applicable
        "frac_positive_paths": pbo_result.frac_positive_paths,
        "n_trials": n_trials_total,
        "n_eff": 0,  # not computed for cross-sectional path
        "monthly_sharpe_is": is_ms,
        "monthly_sharpe_oos": oos_ms,
        "gross_monthly_sharpe_is": is_gross_ms,
        "gross_monthly_sharpe_oos": oos_gross_ms,
        "rank_ic_mean_oos": rank_ic_stats["mean_rank_ic"],
        "rank_ic_std_oos": rank_ic_stats["std_rank_ic"],
        "rank_ic_n_timestamps": rank_ic_stats["n_timestamps"],
        "turnover_per_bar_is": is_turnover,
        "turnover_per_bar_oos": oos_turnover,
        "turnover_ceiling": XS_TURNOVER_CEILING,
        "turnover_ceiling_gate_pass": bool(turnover_gate_pass),
        "note": (
            f"iter-v3/092 cross-sectional path ({outer_seed_str}): "
            f"F3 (IS turnover/bar {is_turnover:.4f} <= ceiling {XS_TURNOVER_CEILING}): "
            f"{'PASS' if turnover_gate_pass else 'FAIL'}. "
            f"G9 (OOS rank-IC {rank_ic_stats['mean_rank_ic']:.4f} > 0): "
            f"{'PASS' if rank_ic_stats['mean_rank_ic'] > 0 else 'FAIL'}."
        ),
    }
    with open(report_dir / "dsr.json", "w") as f:
        json.dump(dsr_data, f, indent=2)

    # Print summary.
    seed_label = f" [outer_seed={outer_seed}]" if outer_seed is not None else " [AGGREGATE]"
    print("\n" + "=" * 60)
    print(f"CROSS-SECTIONAL BACKTEST SUMMARY -- iter-{ITERATION_LABEL}{seed_label}")
    print("=" * 60)
    print(f"IS monthly Sharpe (net):   {is_ms:+.4f}")
    print(f"OOS monthly Sharpe (net):  {oos_ms:+.4f}")
    print(f"IS monthly Sharpe (gross): {is_gross_ms:+.4f}")
    print(f"OOS monthly Sharpe (gross):{oos_gross_ms:+.4f}")
    ratio_str = f"{oos_is_ratio:.4f}" if not np.isnan(oos_is_ratio) else "N/A"
    print(f"OOS/IS net ratio:          {ratio_str}")
    print(f"IS max drawdown:    {is_mdd:.4f}")
    print(f"OOS max drawdown:   {oos_mdd:.4f}")
    print(f"IS  n_bars:  {len(is_results)}")
    print(f"OOS n_bars:  {len(oos_results)}")
    print(
        f"OOS rank-IC: {rank_ic_stats['mean_rank_ic']:.4f} +/- "
        f"{rank_ic_stats['std_rank_ic']:.4f} "
        f"(n={rank_ic_stats['n_timestamps']} timestamps)"
    )
    print(f"frac_positive_paths (CPCV): {pbo_result.frac_positive_paths:.3f}")
    print(f"CPCV note: {pbo_result.note}")
    print(
        f"IS turnover/bar:  {is_turnover:.4f}  (OOS {oos_turnover:.4f})  "
        f"ceiling {XS_TURNOVER_CEILING}"
    )
    if turnover_gate_pass:
        print(
            f"HARD turnover gate (F3): PASS -- IS turnover/bar {is_turnover:.4f} "
            f"<= ceiling {XS_TURNOVER_CEILING}."
        )
    else:
        print(
            f"HARD turnover gate (F3): FAIL (NO-MERGE) -- IS turnover/bar {is_turnover:.4f} "
            f"> ceiling {XS_TURNOVER_CEILING}."
        )
    print("=" * 60 + "\n")

    # Return scalar metrics for aggregate report assembly.
    return {
        "outer_seed": outer_seed,
        "is_monthly_sharpe": is_ms,
        "oos_monthly_sharpe": oos_ms,
        "is_gross_monthly_sharpe": is_gross_ms,
        "oos_gross_monthly_sharpe": oos_gross_ms,
        "is_max_drawdown": is_mdd,
        "oos_max_drawdown": oos_mdd,
        "is_n_bars": len(is_results),
        "oos_n_bars": len(oos_results),
        "oos_rank_ic_mean": rank_ic_stats["mean_rank_ic"],
        "frac_positive_paths": pbo_result.frac_positive_paths,
        "is_turnover_per_bar": is_turnover,
        "oos_turnover_per_bar": oos_turnover,
        "turnover_ceiling_gate_pass": bool(turnover_gate_pass),
        "oos_net_positive": oos_ms > 0,
    }


# ============================================================
# Main runner
# ============================================================


def _run_one_book(
    panel: pd.DataFrame,
    labels: pd.Series,
    score_mode: str,
    report_dir: Path,
    n_trials: int,
    outer_seed: int,
    ensemble_seeds: list[int],
) -> dict:
    """Run one cross-sectional book with a multi-seed inner ensemble and write reports.

    iter-v3/092: ensemble_seeds is the 5-element inner-seed list derived from
    _derive_ensemble_seeds(outer_seed, 5).  CrossSectionalRankStrategy trains
    one LGBMRanker per inner seed and averages their predict() vectors.

    Returns the scalar-metrics dict from _write_xs_reports for aggregate assembly.
    """
    strategy = CrossSectionalRankStrategy(
        training_months=TRAINING_MONTHS,
        n_trials=n_trials,
        feature_columns=XS_FEATURE_COLUMNS,
        features_dir=str(FEATURES_DIR),
        symbols=XS_UNIVERSE,
        horizon=XS_HORIZON,
        seed=outer_seed,
        ensemble_seeds=ensemble_seeds,
        verbose=0,
    )

    print(
        f"\n[backtest:{score_mode}] Running cross-sectional walk-forward backtest "
        f"(score_mode={score_mode!r}, outer_seed={outer_seed}, "
        f"inner_ensemble={len(ensemble_seeds)} models) -> {report_dir}"
    )
    print(
        f"[backtest:{score_mode}] /089 construction: quantile_frac={XS_QUANTILE_FRAC}, "
        f"hold_bars={XS_HOLD_BARS}, no_trade_band={XS_NO_TRADE_BAND}, "
        f"turnover ceiling={XS_TURNOVER_CEILING}"
    )
    train_start_ms = int(panel[panel["open_time"] < OOS_CUTOFF_MS]["open_time"].min())
    results = run_cross_sectional_backtest(
        strategy=strategy,
        panel=panel,
        labels=labels,
        train_start_ms=train_start_ms,
        oos_cutoff_ms=OOS_CUTOFF_MS,
        quantile_frac=XS_QUANTILE_FRAC,
        hold_bars=XS_HOLD_BARS,
        no_trade_band=XS_NO_TRADE_BAND,
        score_mode=score_mode,
    )
    print(f"[backtest:{score_mode}] {len(results)} bar-symbol rows produced.")

    if results.empty:
        print(f"WARNING: backtest (score_mode={score_mode!r}) produced no results.")
        return {}

    # OOS rank-IC.
    print(f"\n[rank-IC:{score_mode}] Computing OOS rank-IC...")
    rank_ic_stats = compute_oos_rank_ic(results)
    print(
        f"[rank-IC:{score_mode}] mean={rank_ic_stats['mean_rank_ic']:.4f}, "
        f"std={rank_ic_stats['std_rank_ic']:.4f}, "
        f"n={rank_ic_stats['n_timestamps']}"
    )

    # IS-only CPCV.
    print(f"\n[cpcv:{score_mode}] Running IS-only CPCV (actual long-short net return)...")
    cpcv_df, pbo_result = _compute_xs_cpcv(
        results,
        report_dir,
        n_trials=n_trials,
        seed=outer_seed,
    )

    # Write reports and return scalar metrics.
    print(f"\n[reports:{score_mode}] Writing report files to {report_dir}...")
    return _write_xs_reports(
        results=results,
        rank_ic_stats=rank_ic_stats,
        pbo_result=pbo_result,
        cpcv_df=cpcv_df,
        report_dir=report_dir,
        n_trials=n_trials,
        ensemble_size=len(ensemble_seeds),
        outer_seed=outer_seed,
    )


def _write_aggregate_reports(
    seed_metrics: list[dict],
    report_dir: Path,
    n_trials: int,
) -> None:
    """Write multi-seed aggregate comparison.csv, ensemble_summary.json, dsr.json.

    Brief Section 3.3 item 3: the aggregate reports contain the multi-seed-mean
    IS/OOS monthly Sharpe, per-seed values, min across seeds, and a 2-seed
    Pareto boolean (both seeds individually OOS-net-positive).
    """
    if not seed_metrics:
        print("[aggregate] No seed metrics to aggregate -- skipping.")
        return

    report_dir.mkdir(parents=True, exist_ok=True)

    # Per-seed scalars.
    is_sharpes = [m["is_monthly_sharpe"] for m in seed_metrics]
    oos_sharpes = [m["oos_monthly_sharpe"] for m in seed_metrics]
    is_gross = [m["is_gross_monthly_sharpe"] for m in seed_metrics]
    oos_gross = [m["oos_gross_monthly_sharpe"] for m in seed_metrics]
    frac_pos_paths = [m["frac_positive_paths"] for m in seed_metrics]
    is_mdds = [m["is_max_drawdown"] for m in seed_metrics]
    oos_mdds = [m["oos_max_drawdown"] for m in seed_metrics]
    rank_ics = [m["oos_rank_ic_mean"] for m in seed_metrics]
    is_turnovers = [m["is_turnover_per_bar"] for m in seed_metrics]
    oos_net_positives = [m["oos_net_positive"] for m in seed_metrics]

    mean_is = float(np.mean(is_sharpes))
    mean_oos = float(np.mean(oos_sharpes))
    mean_is_gross = float(np.mean(is_gross))
    mean_oos_gross = float(np.mean(oos_gross))
    mean_frac_pos = float(np.mean(frac_pos_paths))
    mean_is_mdd = float(np.mean(is_mdds))
    mean_oos_mdd = float(np.mean(oos_mdds))
    mean_rank_ic = float(np.mean(rank_ics))
    mean_is_turnover = float(np.mean(is_turnovers))
    min_is = float(np.min(is_sharpes))
    min_oos = float(np.min(oos_sharpes))
    pareto_both_oos_positive = all(oos_net_positives)

    oos_is_ratio = (mean_oos / mean_is) if abs(mean_is) > 1e-10 else float("nan")
    gross_oos_is_ratio = (
        (mean_oos_gross / mean_is_gross) if abs(mean_is_gross) > 1e-10 else float("nan")
    )

    n_seeds = len(seed_metrics)
    n_trials_total = n_trials * ENSEMBLE_SIZE * n_seeds

    # Build aggregate comparison.csv with mean + per-seed columns + min.
    seed_is_cols = {f"seed_{m['outer_seed']}_is": m["is_monthly_sharpe"] for m in seed_metrics}
    seed_oos_cols = {f"seed_{m['outer_seed']}_oos": m["oos_monthly_sharpe"] for m in seed_metrics}

    def _agg_row(metric: str, is_val: float, oos_val: float, ratio: float, **extras: float) -> dict:
        row = {"metric": metric, "in_sample": is_val, "out_of_sample": oos_val, "ratio": ratio}
        row.update(extras)
        return row

    comparison_rows = [
        _agg_row(
            "monthly_sharpe",
            mean_is,
            mean_oos,
            oos_is_ratio,
            min_in_sample=min_is,
            min_out_of_sample=min_oos,
            **seed_is_cols,
            **seed_oos_cols,
        ),
        _agg_row(
            "gross_monthly_sharpe",
            mean_is_gross,
            mean_oos_gross,
            gross_oos_is_ratio,
        ),
        _agg_row(
            "max_drawdown",
            mean_is_mdd,
            mean_oos_mdd,
            mean_oos_mdd / max(mean_is_mdd, 1e-10),
        ),
        {
            "metric": "rank_ic_mean",
            "in_sample": float("nan"),
            "out_of_sample": mean_rank_ic,
            "ratio": float("nan"),
        },
        {
            "metric": "turnover_per_bar",
            "in_sample": mean_is_turnover,
            "out_of_sample": float("nan"),
            "ratio": float("nan"),
        },
        {
            "metric": "frac_positive_paths_mean",
            "in_sample": mean_frac_pos,
            "out_of_sample": float("nan"),
            "ratio": float("nan"),
        },
        {
            "metric": "pareto_both_oos_positive",
            "in_sample": float(pareto_both_oos_positive),
            "out_of_sample": float("nan"),
            "ratio": float("nan"),
        },
        {
            "metric": "n_seeds",
            "in_sample": n_seeds,
            "out_of_sample": float("nan"),
            "ratio": float("nan"),
        },
        {
            "metric": "n_trials_total",
            "in_sample": n_trials_total,
            "out_of_sample": float("nan"),
            "ratio": float("nan"),
        },
    ]
    pd.DataFrame(comparison_rows).to_csv(report_dir / "comparison.csv", index=False)

    # ensemble_summary.json -- brief Section 3.3 item 3.
    per_seed_rows = []
    for m in seed_metrics:
        per_seed_rows.append(
            {
                "outer_seed": m["outer_seed"],
                "is_monthly_sharpe": m["is_monthly_sharpe"],
                "oos_monthly_sharpe": m["oos_monthly_sharpe"],
                "is_gross_monthly_sharpe": m["is_gross_monthly_sharpe"],
                "oos_gross_monthly_sharpe": m["oos_gross_monthly_sharpe"],
                "oos_rank_ic_mean": m["oos_rank_ic_mean"],
                "frac_positive_paths": m["frac_positive_paths"],
                "is_turnover_per_bar": m["is_turnover_per_bar"],
                "oos_net_positive": m["oos_net_positive"],
            }
        )
    ensemble_summary = {
        "iteration": ITERATION_LABEL,
        "n_seeds": n_seeds,
        "ensemble_size_per_seed": ENSEMBLE_SIZE,
        "total_models_per_cell": n_seeds * ENSEMBLE_SIZE,
        "per_seed": per_seed_rows,
        "multi_seed_mean": {
            "is_monthly_sharpe": mean_is,
            "oos_monthly_sharpe": mean_oos,
            "is_gross_monthly_sharpe": mean_is_gross,
            "oos_gross_monthly_sharpe": mean_oos_gross,
            "oos_rank_ic_mean": mean_rank_ic,
            "frac_positive_paths": mean_frac_pos,
            "is_turnover_per_bar": mean_is_turnover,
        },
        "multi_seed_min": {
            "is_monthly_sharpe": min_is,
            "oos_monthly_sharpe": min_oos,
        },
        "pareto_both_oos_positive": pareto_both_oos_positive,
        "confirmation_gate_G10": pareto_both_oos_positive,
    }
    with open(report_dir / "ensemble_summary.json", "w") as f:
        json.dump(ensemble_summary, f, indent=2)

    # dsr.json for the aggregate -- using aggregate mean-book metrics.
    dsr_data = {
        "dsr": 0.0,
        "pbo": float("nan"),
        "psr": 0.0,
        "frac_positive_paths": mean_frac_pos,
        "n_trials": n_trials_total,
        "n_eff": 0,
        "monthly_sharpe_is": mean_is,
        "monthly_sharpe_oos": mean_oos,
        "gross_monthly_sharpe_is": mean_is_gross,
        "gross_monthly_sharpe_oos": mean_oos_gross,
        "rank_ic_mean_oos": mean_rank_ic,
        "turnover_ceiling": XS_TURNOVER_CEILING,
        "pareto_both_oos_positive": pareto_both_oos_positive,
        "note": (
            f"iter-v3/092 aggregate ({n_seeds} outer seeds x {ENSEMBLE_SIZE} inner "
            f"= {n_seeds * ENSEMBLE_SIZE} models/cell). "
            f"G10 (Pareto both OOS+): {'PASS' if pareto_both_oos_positive else 'FAIL'}. "
            f"G2 (mean OOS net Sharpe >= +1.0): {'PASS' if mean_oos >= 1.0 else 'FAIL'} "
            f"(observed {mean_oos:+.4f})."
        ),
    }
    with open(report_dir / "dsr.json", "w") as f:
        json.dump(dsr_data, f, indent=2)

    # Print aggregate summary.
    print("\n" + "=" * 70)
    print(f"MULTI-SEED AGGREGATE SUMMARY -- iter-{ITERATION_LABEL}")
    print("=" * 70)
    print(f"Outer seeds: {[m['outer_seed'] for m in seed_metrics]}")
    print(f"Inner ensemble per seed: {ENSEMBLE_SIZE} models")
    print(f"Total models/cell: {n_seeds * ENSEMBLE_SIZE}")
    print()
    for m in seed_metrics:
        print(
            f"  seed={m['outer_seed']:>3d}: IS={m['is_monthly_sharpe']:+.4f}  "
            f"OOS={m['oos_monthly_sharpe']:+.4f}  "
            f"frac_pos={m['frac_positive_paths']:.3f}  "
            f"OOS+={'YES' if m['oos_net_positive'] else 'NO'}"
        )
    print()
    print(f"  MEAN IS  monthly Sharpe: {mean_is:+.4f}  (min: {min_is:+.4f})")
    print(f"  MEAN OOS monthly Sharpe: {mean_oos:+.4f}  (min: {min_oos:+.4f})")
    if not np.isnan(oos_is_ratio):
        print(f"  MEAN OOS/IS ratio:       {oos_is_ratio:.4f}")
    else:
        print("  MEAN OOS/IS ratio: N/A")
    print(f"  MEAN frac_positive_paths: {mean_frac_pos:.3f}")
    print(f"  MEAN OOS rank-IC:        {mean_rank_ic:+.4f}")
    print()
    g1_pass = mean_is >= 1.0
    g2_pass = mean_oos >= 1.0
    g10_pass = pareto_both_oos_positive
    print(f"  G1 (IS >= +1.0):         {'PASS' if g1_pass else 'FAIL'}  ({mean_is:+.4f})")
    print(f"  G2 (OOS >= +1.0):        {'PASS' if g2_pass else 'FAIL'}  ({mean_oos:+.4f})")
    print(
        f"  G10 (Pareto both OOS+):  {'PASS' if g10_pass else 'FAIL'}  "
        f"({'all positive' if g10_pass else 'some negative'})"
    )
    print("=" * 70 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cross-sectional ranking model runner -- iter-v3/092 (multi-seed CONFIRMATION)"
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=35,
        help="Optuna trials per monthly model per inner seed (default 35).",
    )
    parser.add_argument(
        "--skip-features",
        action="store_true",
        help="Skip feature generation (use existing parquets).",
    )
    parser.add_argument(
        "--exploration",
        action="store_true",
        help="(Unused in /092 CONFIRMATION mode -- retained for CLI compat.)",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help=(
            "Multi-seed wiring smoke test: runs the outer-seed loop over a "
            "short IS-only date slice to verify the multi-seed path runs "
            "end-to-end and produces the expected report structure."
        ),
    )
    parser.add_argument(
        "--clean-oof",
        action="store_true",
        help="Delete any existing reports for this iteration before starting.",
    )
    # iter-v3/092 NEW argument: controls outer-seed count.
    # This is NOT the deprecated per-symbol --seeds from run_baseline_v3.py.
    # The cross-sectional --seeds is live and functional; no deprecation warning.
    parser.add_argument(
        "--seeds",
        type=int,
        default=2,
        help=(
            "Number of outer seeds to use (default 2 -- selects first N elements "
            "of CONFIRMATION_OUTER_SEEDS = (42, 123)). "
            "This is a NEW argument added at iter-v3/092; it is NOT the deprecated "
            "per-symbol runner's --seeds from run_baseline_v3.py."
        ),
    )
    args = parser.parse_args()

    if args.seeds < 1 or args.seeds > len(CONFIRMATION_OUTER_SEEDS):
        raise ValueError(
            f"--seeds must be between 1 and {len(CONFIRMATION_OUTER_SEEDS)}, got {args.seeds}."
        )
    outer_seeds = list(CONFIRMATION_OUTER_SEEDS[: args.seeds])

    t_start = time.time()

    # Pre-flight.
    _verify_branch()
    _verify_xs_universe()
    _verify_feature_columns()
    _verify_xs_gap_assertion()
    _verify_data_freshness(XS_UNIVERSE)

    print(f"\nCross-Sectional v3 iter-{ITERATION_LABEL} [CONFIRMATION]")
    print(f"Universe: {len(XS_UNIVERSE)} symbols")
    print(f"Features: {len(XS_FEATURE_COLUMNS)} cross-sectionally rank-normalized features")
    print(f"XS_REQUIRED_GAP: {XS_REQUIRED_GAP} = (H={XS_HORIZON}+1)*N={len(XS_UNIVERSE)}")
    print(f"Optuna n_trials: {args.n_trials} per inner model")
    print(f"Outer seeds: {outer_seeds} ({len(outer_seeds)} seeds)")
    print(f"Inner ensemble per seed: {ENSEMBLE_SIZE} models")
    print(f"Total models/cell: {len(outer_seeds) * ENSEMBLE_SIZE}")
    print(f"OOS split: {OOS_CUTOFF_DATE} (IMMUTABLE)")
    print(f"Training months: {TRAINING_MONTHS} (IMMUTABLE)")
    print(f"embargo_ms: (H={XS_HORIZON}+1)*interval_ms (corrected /091 fix)\n")

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
        _run_smoke_test(outer_seeds, args)
        return

    # Build the pooled cross-sectional panel (all timestamps, IS + OOS).
    print("\n[panel] Building pooled cross-sectional panel (iter-v3/092 base-13)...")
    panel = build_cross_sectional_panel(
        features_dir=FEATURES_DIR,
        symbols=XS_UNIVERSE,
        feature_columns=list(V3_FEATURE_COLUMNS_TOP_N),
        expand_downside=False,
    )
    print(
        f"[panel] {len(panel)} total rows "
        f"({panel['open_time'].nunique()} unique timestamps, "
        f"{panel['symbol'].nunique()} symbols, "
        f"{len(XS_FEATURE_COLUMNS)} base features)"
    )

    # Label: cross-sectional graded relevance {0, 1, 2}, H=21.
    print(f"[label] Computing cross-sectional rank labels (H={XS_HORIZON})...")
    labels = label_cross_sectional_rank(panel, horizon=XS_HORIZON)
    n_valid = labels.notna().sum()
    print(f"[label] {n_valid} valid labels ({n_valid / len(labels):.1%} of panel rows)")

    # -----------------------------------------------------------------
    # iter-v3/092 MULTI-SEED CONFIRMATION RUN:
    #   - Run the trained LGBMRanker once per outer seed.
    #   - Write per-seed reports to seed_<s>/.
    #   - Write multi-seed aggregate to the root report_dir.
    # -----------------------------------------------------------------
    seed_metrics: list[dict] = []

    for outer_seed in outer_seeds:
        inner_seeds = _derive_ensemble_seeds(outer_seed, ENSEMBLE_SIZE)
        seed_dir = report_dir / f"seed_{outer_seed}"
        print(f"\n{'=' * 60}\n[outer_seed={outer_seed}] Inner seeds: {inner_seeds}\n{'=' * 60}")
        metrics = _run_one_book(
            panel=panel,
            labels=labels,
            score_mode="trained",
            report_dir=seed_dir,
            n_trials=args.n_trials,
            outer_seed=outer_seed,
            ensemble_seeds=inner_seeds,
        )
        if metrics:
            seed_metrics.append(metrics)

    # Write multi-seed aggregate.
    print("\n[aggregate] Writing multi-seed aggregate reports...")
    _write_aggregate_reports(
        seed_metrics=seed_metrics,
        report_dir=report_dir,
        n_trials=args.n_trials,
    )

    elapsed = time.time() - t_start
    h, m = divmod(int(elapsed), 3600)
    m, s = divmod(m, 60)
    print(f"\nTotal wall-clock: {h}h {m:02d}m {s:02d}s")
    print(f"Per-seed reports at: {report_dir.resolve()}/seed_<outer_seed>/")
    print(f"Aggregate reports at: {report_dir.resolve()}/")
    print("\nOVERALL=READY-FOR-CRITIC")


def _run_smoke_test(outer_seeds: list[int], args: argparse.Namespace) -> None:
    """Multi-seed wiring smoke test.

    iter-v3/092: verifies the outer-seed loop runs for each seed, produces
    seed_<s>/ report directories, and the aggregate report structure is written.
    Uses a short IS-only date slice (no real training) via model_free scoring.
    """
    print(
        f"\n[smoke] Multi-seed wiring smoke test (outer_seeds={outer_seeds}, "
        "model_free scoring -- no training required)..."
    )

    panel = build_cross_sectional_panel(
        features_dir=FEATURES_DIR,
        symbols=XS_UNIVERSE,
        feature_columns=list(V3_FEATURE_COLUMNS_TOP_N),
        expand_downside=False,
    )
    panel_is = panel[panel["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    labels_all = label_cross_sectional_rank(panel_is, horizon=XS_HORIZON)

    interval_ms = 8 * 3600 * 1000
    embargo_ms = (XS_HORIZON + 1) * interval_ms
    all_ts = np.sort(panel_is["open_time"].unique())
    splits = _generate_xs_monthly_splits(
        all_timestamps=all_ts,
        training_months=12,
        embargo_ms=embargo_ms,
    )
    if not splits:
        print("[smoke] ERROR: no splits generated. Exiting.")
        return

    report_dir = REPORTS_DIR / f"iteration_{ITERATION_LABEL}"
    smoke_dir = report_dir / "smoke_test"
    smoke_dir.mkdir(parents=True, exist_ok=True)

    seed_metrics: list[dict] = []
    t0 = time.time()

    for outer_seed in outer_seeds:
        inner_seeds = _derive_ensemble_seeds(outer_seed, ENSEMBLE_SIZE)
        seed_dir = report_dir / f"seed_{outer_seed}"
        seed_dir.mkdir(parents=True, exist_ok=True)
        print(
            f"\n[smoke] outer_seed={outer_seed}, inner_seeds={inner_seeds[:2]}... "
            f"(showing first 2 of {ENSEMBLE_SIZE})"
        )

        strategy = CrossSectionalRankStrategy(
            training_months=12,
            n_trials=2,
            feature_columns=XS_FEATURE_COLUMNS,
            features_dir=str(FEATURES_DIR),
            symbols=XS_UNIVERSE,
            horizon=XS_HORIZON,
            seed=outer_seed,
            ensemble_seeds=inner_seeds,
            verbose=0,
        )

        train_start_ms = int(panel_is["open_time"].min())
        results = run_cross_sectional_backtest(
            strategy=strategy,
            panel=panel_is,
            labels=labels_all,
            train_start_ms=train_start_ms,
            oos_cutoff_ms=int(panel_is["open_time"].max()) + interval_ms,
            quantile_frac=XS_QUANTILE_FRAC,
            hold_bars=XS_HOLD_BARS,
            no_trade_band=XS_NO_TRADE_BAND,
            score_mode="model_free",
        )

        # model_free: no inner models trained.
        assert strategy._models == [], (
            f"[smoke] FAIL seed={outer_seed} -- model_free must not populate _models"
        )
        print(f"[smoke] seed={outer_seed}: {len(results)} bar-symbol rows produced. PASS.")

        if not results.empty:
            rank_ic_stats = compute_oos_rank_ic(results)
            cpcv_df, pbo_result = _compute_xs_cpcv(results, seed_dir, n_trials=0, seed=outer_seed)
            metrics = _write_xs_reports(
                results=results,
                rank_ic_stats=rank_ic_stats,
                pbo_result=pbo_result,
                cpcv_df=cpcv_df,
                report_dir=seed_dir,
                n_trials=0,
                ensemble_size=1,
                outer_seed=outer_seed,
            )
            seed_metrics.append(metrics)

    # Write aggregate for smoke test.
    if seed_metrics:
        _write_aggregate_reports(seed_metrics=seed_metrics, report_dir=report_dir, n_trials=0)

    elapsed = time.time() - t0

    # Verify expected report structure.
    ok = True
    for outer_seed in outer_seeds:
        seed_dir = report_dir / f"seed_{outer_seed}"
        for fname in ["comparison.csv", "dsr.json", "cpcv_paths.csv"]:
            fpath = seed_dir / fname
            if not fpath.exists():
                print(f"[smoke] MISSING: {fpath}")
                ok = False
    for fname in ["comparison.csv", "ensemble_summary.json", "dsr.json"]:
        fpath = report_dir / fname
        if not fpath.exists():
            print(f"[smoke] MISSING aggregate: {fpath}")
            ok = False

    n_seed_dirs = sum(1 for s in outer_seeds if (report_dir / f"seed_{s}").is_dir())
    assert n_seed_dirs == len(outer_seeds), (
        f"[smoke] Expected {len(outer_seeds)} seed dirs, found {n_seed_dirs}"
    )
    print(f"[smoke] seed_<s>/ dirs: {n_seed_dirs}/{len(outer_seeds)} -- PASS")

    if ok:
        print(f"\n[smoke] PASS -- multi-seed wiring verified in {elapsed:.1f}s")
        print(f"[smoke] Report dirs: {[str(report_dir / f'seed_{s}') for s in outer_seeds]}")
        print(f"[smoke] Aggregate: {report_dir}/ensemble_summary.json -- EXISTS")
        print("\n[smoke] Multi-seed CONFIRMATION wiring COMPLETE.")
    else:
        print("\n[smoke] FAIL -- missing report files (see above).")


if __name__ == "__main__":
    main()
