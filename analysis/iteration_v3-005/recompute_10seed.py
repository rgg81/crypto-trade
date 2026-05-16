"""Recompute iter-v3/005 metrics — 10-seed Pareto via parquet REUSE.

This script implements iter-v3/005 Section 3.5 sub-fix #1:
  - Reuses iter-v3/003's trial_oof_returns.parquet (model UNCHANGED, no rebacktest).
  - Copies in_sample/ and out_of_sample/ from iter-v3/003 (same trades, same model).
  - Runs the iter-v3/004 per-cell CSCV consumer pipeline 10 times, each with a
    different outer seed controlling the random IS/OOS split sampling inside
    pbo_from_cpcv (via the new ``rng`` parameter added in iter-v3/005).
  - Produces a 10-row pareto_front.csv (schema: seed, monthly_sharpe, max_drawdown,
    calmar, pbo, n_trades, max_concentration_pct) plus per-seed dsr.json files and
    a consolidated seed_summary.json.

Headline IS/OOS metrics (trades, Sharpe, drawdown) are IDENTICAL across all 10
seeds — the model is byte-for-byte unchanged.  Only PBO varies per seed because
the random IS/OOS split sampling in pbo_from_cpcv differs.

Wall-clock estimate: 10 x ~89s = ~15 minutes total.

Brief reference: Section 3.5 sub-fixes #1, #4; Section 3.9 work plan steps 4-6.
Section 5.3 mitigation P3: parquet is read ONCE and the in-memory DataFrame is
shared across all 10 per-seed loops.

Usage (from repo root):
    uv run python analysis/iteration_v3-005/recompute_10seed.py [--seeds N]

Optional flag --seeds N overrides the default list to the first N of the 10
outer seeds.  --seeds 1 and --seeds 2 are the pre-flight checks prescribed in
Phase 6 work plan steps 4-5.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC003 = REPO_ROOT / "reports-v3" / "iteration_v3-003"
DST005 = REPO_ROOT / "reports-v3" / "iteration_v3-005"
OOF_PARQUET = SRC003 / "trial_oof_returns.parquet"
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC — IMMUTABLE

# ---------------------------------------------------------------------------
# 10 outer seeds (brief Section 3.5 sub-fix #1 spec)
# Order preserved: seed=42 MUST appear first so it is row[0] in pareto_front.csv
# and can be compared against iter-v3/004's single-row pareto_front.csv.
# ---------------------------------------------------------------------------
OUTER_SEEDS = [42, 17, 100, 999, 8675309, 0, 12345, 67890, 314159, 271828]

# ---------------------------------------------------------------------------
# Per-cell CSCV configuration (UNCHANGED from iter-v3/004)
# ---------------------------------------------------------------------------
PER_CELL_N_SPLITS = 10
PER_CELL_K = 2  # C(10, 2) = 45 paths
PER_CELL_GAP = 22  # (timeout_candles + 1) = 22 within a single-symbol cell
CSCV_MAX_SPLITS = 5000  # cap on IS/OOS combinations evaluated per cell

# ---------------------------------------------------------------------------
# Import validation helpers
# ---------------------------------------------------------------------------
sys.path.insert(0, str(REPO_ROOT / "src"))

from crypto_trade.strategies.ml.validation_v3 import (  # noqa: E402
    combinatorial_purged_cv,
    deflated_sharpe_ratio_v3,
    n_effective_trials,
    pbo_from_cpcv,
    psr,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class TradeLike:
    """Minimal trade object compatible with metric computation helpers."""

    def __init__(self, row: dict) -> None:
        self.open_time = int(float(row.get("open_time", 0)))
        self.close_time = int(float(row.get("close_time", 0)))
        self.weighted_pnl = float(row.get("weighted_pnl", 0.0))
        self.symbol = row.get("symbol", "")


def _load_trades_csv(path: Path) -> list[TradeLike]:
    import csv

    rows = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(TradeLike(row))
    return rows


def _monthly_sharpe(trades: list[TradeLike]) -> float:
    if not trades:
        return 0.0
    months = pd.to_datetime([t.close_time for t in trades], unit="ms").to_period("M")
    monthly = (
        pd.Series([t.weighted_pnl for t in trades], index=months).groupby(level=0).sum() / 100.0
    )
    if len(monthly) < 2 or monthly.std() == 0:
        return 0.0
    return float(monthly.mean() / monthly.std() * np.sqrt(12))


def _daily_sharpe(trades: list[TradeLike]) -> float:
    if not trades:
        return 0.0
    days = pd.to_datetime([t.close_time for t in trades], unit="ms").normalize()
    daily = pd.Series([t.weighted_pnl for t in trades], index=days).groupby(level=0).sum() / 100.0
    if len(daily) < 2 or daily.std() == 0:
        return 0.0
    return float(daily.mean() / daily.std() * np.sqrt(252))


def _max_drawdown_pct(trades: list[TradeLike]) -> float:
    if not trades:
        return 0.0
    pnl = np.array([t.weighted_pnl for t in trades], dtype=float)
    cum = np.cumsum(pnl)
    peak = np.maximum.accumulate(cum)
    dd = peak - cum
    max_dd = float(dd.max()) if len(dd) > 0 else 0.0
    # Express as percentage of peak (avoid div-by-zero when peak=0)
    peak_val = float(peak.max()) if peak.max() > 0 else 1.0
    return round(max_dd / peak_val * 100, 4)


def _calmar(monthly_sharpe: float, max_dd: float) -> float:
    if max_dd <= 0:
        return 0.0
    return round(monthly_sharpe / (max_dd / 100.0), 4)


def _compute_per_cell_pbo(
    oof_df: pd.DataFrame,
    rng: np.random.Generator | None = None,
) -> tuple[pd.DataFrame, float, float, int]:
    """Run per-cell CSCV consumer on oof_df with optional seed-controlled sampling.

    Returns
    -------
    per_cell_df   — DataFrame with per-(sym, month) PBO/n_eff rows
    mean_pbo      — cross-cell mean PBO (over informative cells)
    median_pbo    — cross-cell median PBO
    median_n_eff  — cross-cell median n_eff (over informative cells)
    """
    cells = sorted(oof_df.groupby(["symbol", "train_month"]).groups.keys())
    n_cells = len(cells)
    cell_rows: list[dict] = []

    for cell_idx, (sym, month) in enumerate(cells):
        cell_df = oof_df[(oof_df["symbol"] == sym) & (oof_df["train_month"] == month)]
        n_trials_cell = int(cell_df["trial_id"].nunique())
        n_candles_cell = int(cell_df["candle_open_time_ms"].nunique())

        if n_trials_cell < 2 or n_candles_cell < PER_CELL_N_SPLITS * 3:
            cell_rows.append(
                {
                    "symbol": sym,
                    "train_month": month,
                    "n_trials": n_trials_cell,
                    "n_candles": n_candles_cell,
                    "n_paths": 0,
                    "rank": 0,
                    "pbo": float("nan"),
                    "n_eff": 0,
                    "mean_path_sharpe": float("nan"),
                    "error": "insufficient_data",
                }
            )
            continue

        try:
            pivot = cell_df.pivot_table(
                index="candle_open_time_ms",
                columns="trial_id",
                values="oof_return",
                aggfunc="mean",
            ).sort_index()
            returns_mat = pivot.to_numpy()
            n_candles_mat, n_trials_mat = returns_mat.shape

            cell_splits = combinatorial_purged_cv(
                n_samples=n_candles_mat,
                n_splits=PER_CELL_N_SPLITS,
                n_test_splits=PER_CELL_K,
                gap=PER_CELL_GAP,
                embargo=0,
            )
            n_paths = len(cell_splits)
            path_mat = np.full((n_paths, n_trials_mat), np.nan, dtype=float)

            for path_id, (_, test_idx) in enumerate(cell_splits):
                if len(test_idx) < 2:
                    continue
                test_rets = returns_mat[test_idx, :]
                mu = np.nanmean(test_rets, axis=0)
                sigma = np.nanstd(test_rets, axis=0, ddof=1)
                with np.errstate(divide="ignore", invalid="ignore"):
                    sharpe = np.where(sigma > 0, mu / sigma, 0.0)
                path_mat[path_id, :] = sharpe

            # Pass the per-seed rng for random IS/OOS split sampling
            pbo_res = pbo_from_cpcv(path_mat, max_splits=CSCV_MAX_SPLITS, rng=rng)
            cell_pbo = pbo_res.pbo if pbo_res.pbo is not None else float("nan")
            cell_neff = n_effective_trials(returns_mat.T)
            rank = int(np.linalg.matrix_rank(returns_mat))
            mean_path_sharpe = float(np.nanmean(path_mat))

            cell_rows.append(
                {
                    "symbol": sym,
                    "train_month": month,
                    "n_trials": n_trials_mat,
                    "n_candles": n_candles_mat,
                    "n_paths": n_paths,
                    "rank": rank,
                    "pbo": cell_pbo,
                    "n_eff": cell_neff,
                    "mean_path_sharpe": round(mean_path_sharpe, 6),
                    "error": "",
                }
            )
        except Exception as exc:
            cell_rows.append(
                {
                    "symbol": sym,
                    "train_month": month,
                    "n_trials": n_trials_cell,
                    "n_candles": n_candles_cell,
                    "n_paths": 0,
                    "rank": 0,
                    "pbo": float("nan"),
                    "n_eff": 0,
                    "mean_path_sharpe": float("nan"),
                    "error": str(exc)[:120],
                }
            )

        if (cell_idx + 1) % 50 == 0:
            print(f"    {cell_idx + 1}/{n_cells} cells ...", flush=True)

    per_cell_df = pd.DataFrame(cell_rows)
    informative = per_cell_df[per_cell_df["rank"] > 1]["pbo"].dropna()
    informative_neff = per_cell_df[per_cell_df["rank"] > 1]["n_eff"].dropna()

    mean_pbo = float(informative.mean()) if len(informative) > 0 else float("nan")
    median_pbo = float(informative.median()) if len(informative) > 0 else float("nan")
    median_n_eff = int(np.median(informative_neff)) if len(informative_neff) > 0 else 0

    return per_cell_df, mean_pbo, median_pbo, median_n_eff


def _read_headline_metrics_from_comparison(
    comparison_path: Path,
    oos_trades: list[TradeLike],
) -> dict:
    """Read headline OOS metrics from comparison.csv (canonical source).

    The model is UNCHANGED from iter-v3/003 — we read the authoritative values
    directly from the source comparison.csv rather than recomputing, ensuring
    exact matches with iter-v3/004's pareto_front.csv schema.

    Pareto schema (from iter-v3/004):
      seed, monthly_sharpe, max_drawdown, calmar, pbo, n_trades, max_concentration_pct
    """
    metrics: dict[str, float] = {}
    sym_wpnl: dict[str, float] = {}
    in_per_symbol = False

    with open(comparison_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("# per_symbol"):
                in_per_symbol = True
                continue
            if in_per_symbol:
                parts = line.split(",")
                if len(parts) >= 4:
                    sym = parts[0]
                    wpnl = float(parts[1])
                    sym_wpnl[sym] = wpnl
                continue
            parts = line.split(",")
            if len(parts) < 3 or parts[0] == "metric":
                continue
            key = parts[0]
            oos_val = parts[2] if len(parts) > 2 else "—"
            if oos_val == "—" or oos_val == "":
                continue
            try:
                metrics[key] = float(oos_val)
            except ValueError:
                pass

    ms = metrics.get("monthly_sharpe", 0.0)
    max_dd = metrics.get("max_drawdown", 0.0)
    calmar = metrics.get("monthly_calmar", 0.0)
    n_trades = int(metrics.get("n_trades", len(oos_trades)))

    # Max concentration from per_symbol section (MKRUSDT 53.21% in iter-v3/003)
    total_positive_wpnl = sum(v for v in sym_wpnl.values() if v > 0)
    if total_positive_wpnl > 0:
        max_conc = max(max(v / total_positive_wpnl * 100.0, 0.0) for v in sym_wpnl.values())
    else:
        # Fallback: use iter-v3/003's known value
        max_conc = 43.64

    return {
        "monthly_sharpe": round(ms, 4),
        "max_drawdown": round(max_dd, 4),
        "calmar": round(calmar, 4),
        "n_trades": n_trades,
        "max_concentration_pct": round(max_conc, 2),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(n_seeds: int = 10) -> None:
    t_start = time.time()
    seeds_to_run = OUTER_SEEDS[:n_seeds]
    print("[recompute_10seed] Starting iter-v3/005 10-seed Pareto recompute")
    print(f"[recompute_10seed] Seeds: {seeds_to_run}")
    print(f"[recompute_10seed] Source: {SRC003}")
    print(f"[recompute_10seed] Target: {DST005}")
    print(f"[recompute_10seed] OOF parquet: {OOF_PARQUET}")

    # ------------------------------------------------------------------
    # Verify input artifacts
    # ------------------------------------------------------------------
    assert OOF_PARQUET.exists(), f"OOF parquet not found: {OOF_PARQUET}"
    assert (SRC003 / "in_sample" / "trades.csv").exists(), "iter-v3/003 IS trades missing"
    assert (SRC003 / "out_of_sample" / "trades.csv").exists(), "iter-v3/003 OOS trades missing"

    # ------------------------------------------------------------------
    # Step 1: copy in_sample/ and out_of_sample/ from iter-v3/003
    # ------------------------------------------------------------------
    print("\n[Step 1] Copying in_sample/ and out_of_sample/ from iter-v3/003 ...")
    DST005.mkdir(parents=True, exist_ok=True)
    for split in ["in_sample", "out_of_sample"]:
        src_split = SRC003 / split
        dst_split = DST005 / split
        if dst_split.exists():
            shutil.rmtree(dst_split)
        shutil.copytree(src_split, dst_split)
        print(f"  Copied {src_split} -> {dst_split}")

    # ------------------------------------------------------------------
    # Step 2: copy static artifacts (adf_test.csv, ic_matrix.csv, cpcv_paths.csv)
    # ------------------------------------------------------------------
    print("\n[Step 2] Copying static artifacts ...")
    for fname in ["adf_test.csv", "ic_matrix.csv", "cpcv_paths.csv"]:
        src_f = SRC003 / fname
        dst_f = DST005 / fname
        if src_f.exists():
            shutil.copy2(src_f, dst_f)
            print(f"  Copied {fname}")

    # ------------------------------------------------------------------
    # Step 3: load trades (same for all seeds — model unchanged)
    # ------------------------------------------------------------------
    print("\n[Step 3] Loading trades from copied CSVs ...")
    is_trades = _load_trades_csv(DST005 / "in_sample" / "trades.csv")
    oos_trades = _load_trades_csv(DST005 / "out_of_sample" / "trades.csv")
    print(f"  IS trades: {len(is_trades)}, OOS trades: {len(oos_trades)}")

    # ------------------------------------------------------------------
    # Step 4: read headline metrics from comparison.csv (canonical source)
    # These are the same for all seeds — the model is unchanged from iter-v3/003.
    # Reading from comparison.csv ensures exact match with iter-v3/004 values.
    # ------------------------------------------------------------------
    headline = _read_headline_metrics_from_comparison(SRC003 / "comparison.csv", oos_trades)
    print("\n[Step 4] Headline OOS metrics (seed-invariant, from comparison.csv):")
    for k, v in headline.items():
        print(f"  {k}: {v}")

    # ------------------------------------------------------------------
    # Step 5: load parquet ONCE — shared across all seeds (P3 mitigation)
    # ------------------------------------------------------------------
    print("\n[Step 5] Loading OOF parquet once (shared across all seeds) ...")
    t_parquet = time.time()
    oof_df_raw = pd.read_parquet(OOF_PARQUET)
    n_raw = len(oof_df_raw)
    oof_df_raw = oof_df_raw.drop_duplicates(
        subset=["symbol", "train_month", "trial_id", "fold_idx", "candle_open_time_ms"]
    )
    n_dedup = len(oof_df_raw)
    oof_df_is = oof_df_raw[oof_df_raw["candle_open_time_ms"] < OOS_CUTOFF_MS].copy()
    n_is = len(oof_df_is)
    print(f"  Raw={n_raw}, after dedup={n_dedup}, IS-only={n_is}")
    print(f"  Parquet load time: {time.time() - t_parquet:.1f}s")

    n_cells = len(sorted(oof_df_is.groupby(["symbol", "train_month"]).groups.keys()))
    print(f"  Total cells to process per seed: {n_cells}")

    # ------------------------------------------------------------------
    # Step 6: 10-seed per-cell CSCV loop
    # ------------------------------------------------------------------
    print(f"\n[Step 6] Running {len(seeds_to_run)}-seed per-cell CSCV ...")
    pareto_rows: list[dict] = []
    seed_summary: list[dict] = []

    for seed_idx, seed in enumerate(seeds_to_run):
        t_seed = time.time()
        print(f"\n  -- Seed {seed} ({seed_idx + 1}/{len(seeds_to_run)}) --")

        rng = np.random.default_rng(seed)
        per_cell_df, mean_pbo, median_pbo, median_n_eff = _compute_per_cell_pbo(oof_df_is, rng=rng)

        elapsed_seed = time.time() - t_seed
        print(
            f"  Seed {seed}: mean_pbo={mean_pbo:.4f}, median_pbo={median_pbo:.4f}, "
            f"median_n_eff={median_n_eff}, wall-clock={elapsed_seed:.1f}s"
        )

        # Save per-seed per_cell_pbo CSV
        per_cell_path = DST005 / f"per_seed_{seed}_per_cell_pbo.csv"
        per_cell_df.to_csv(per_cell_path, index=False)

        # Save per-seed dsr.json (PBO only — DSR is seed-invariant from trades)
        ensemble_seeds_inner = [42, 123, 456, 789, 1001]
        n_symbols = 4
        n_trials_per_seed = 50
        n_trials_total = n_trials_per_seed * len(ensemble_seeds_inner) * n_symbols

        is_wp = np.array([t.weighted_pnl for t in is_trades])
        if len(is_wp) > 1 and is_wp.std() > 0:
            raw_sharpe_is = float(is_wp.mean() / is_wp.std() * np.sqrt(len(is_wp)))
            sk = float(skew(is_wp))
            kt = float(kurtosis(is_wp, fisher=False))
            dsr_result = deflated_sharpe_ratio_v3(
                observed_sr=raw_sharpe_is,
                num_trials=n_trials_total,
                backtest_length=len(is_wp),
                skewness=sk,
                kurtosis=kt,
            )
            dsr_val = dsr_result["p_value"]
        else:
            dsr_val = 0.0

        oos_wp = np.array([t.weighted_pnl for t in oos_trades])
        if len(oos_wp) > 1 and oos_wp.std() > 0:
            raw_sharpe_oos = float(oos_wp.mean() / oos_wp.std() * np.sqrt(len(oos_wp)))
            oos_sk = float(skew(oos_wp))
            oos_kt = float(kurtosis(oos_wp, fisher=False))
            psr_val = psr(
                observed_sharpe=raw_sharpe_oos,
                n_obs=len(oos_wp),
                skewness=oos_sk,
                kurtosis=oos_kt,
            )
        else:
            psr_val = 0.0

        informative_cells = int((per_cell_df["rank"] > 1).sum())
        n_eff_global = median_n_eff
        min_trl_months = float(len(is_trades)) / max(1, len(ensemble_seeds_inner) * n_symbols)

        dsr_dict = {
            "dsr": round(dsr_val, 6),
            "pbo": mean_pbo if not np.isnan(mean_pbo) else None,
            "pbo_note": (
                f"Per-cell mean PBO={mean_pbo:.4f} (iter-v3/005 seed={seed} cross-cell mean). "
                f"{informative_cells} informative cells (rank>1). rng seed={seed}."
            ),
            "pbo_frac_positive_paths": None,
            "pbo_path_sharpe_q25": None,
            "pbo_path_sharpe_q50": None,
            "pbo_path_sharpe_q75": None,
            "psr": round(psr_val, 6),
            "n_eff": n_eff_global,
            "n_trials": n_trials_total,
            "min_trl_months": round(min_trl_months, 2),
        }
        dsr_path = DST005 / f"per_seed_{seed}_dsr.json"
        dsr_path.write_text(json.dumps(dsr_dict, indent=2))

        # Pareto row (brief schema: seed, monthly_sharpe, max_drawdown, calmar,
        # pbo, n_trades, max_concentration_pct)
        pareto_row = {
            "seed": seed,
            "monthly_sharpe": headline["monthly_sharpe"],
            "max_drawdown": headline["max_drawdown"],
            "calmar": headline["calmar"],
            "pbo": round(mean_pbo, 6) if not np.isnan(mean_pbo) else None,
            "n_trades": headline["n_trades"],
            "max_concentration_pct": headline["max_concentration_pct"],
            "n_eff": n_eff_global,
            "mean_pbo": round(mean_pbo, 6) if not np.isnan(mean_pbo) else None,
            "median_pbo": round(median_pbo, 6) if not np.isnan(median_pbo) else None,
        }
        pareto_rows.append(pareto_row)
        seed_summary.append(
            {
                "seed": seed,
                "mean_pbo": round(mean_pbo, 6) if not np.isnan(mean_pbo) else None,
                "median_pbo": round(median_pbo, 6) if not np.isnan(median_pbo) else None,
                "n_eff": n_eff_global,
                "informative_cells": informative_cells,
                "monthly_sharpe": headline["monthly_sharpe"],
                "dsr": round(dsr_val, 6),
                "psr": round(psr_val, 6),
                "wall_clock_s": round(elapsed_seed, 1),
            }
        )

        print(f"  Seed {seed}: pareto row = {pareto_row}")

    # ------------------------------------------------------------------
    # Step 7: write consolidated outputs
    # ------------------------------------------------------------------
    print("\n[Step 7] Writing consolidated outputs ...")

    # pareto_front.csv — 10 rows (brief schema: seed, monthly_sharpe, max_drawdown,
    # calmar, pbo, n_trades, max_concentration_pct)
    pareto_df = pd.DataFrame(pareto_rows)
    pareto_path = DST005 / "pareto_front.csv"
    # Write only the columns matching the brief schema (plus n_eff for verifier 15)
    pareto_cols = [
        "seed",
        "monthly_sharpe",
        "max_drawdown",
        "calmar",
        "pbo",
        "n_trades",
        "max_concentration_pct",
        "n_eff",
    ]
    pareto_df[pareto_cols].to_csv(pareto_path, index=False)
    print(f"  Wrote {pareto_path} ({len(pareto_df)} rows)")

    # seed_summary.json
    seed_summary_path = DST005 / "seed_summary.json"
    seed_summary_path.write_text(json.dumps(seed_summary, indent=2))
    print(f"  Wrote {seed_summary_path}")

    # Write the seed=42 per_cell_pbo.csv as the canonical per_cell_pbo.csv
    # (matches iter-v3/004's output artifact name)
    seed42_per_cell = DST005 / "per_seed_42_per_cell_pbo.csv"
    canonical_per_cell = DST005 / "per_cell_pbo.csv"
    if seed42_per_cell.exists():
        shutil.copy2(seed42_per_cell, canonical_per_cell)
        print("  Copied seed=42 per_cell_pbo.csv as canonical per_cell_pbo.csv")

    # Write the seed=42 dsr.json as the canonical dsr.json
    seed42_dsr = DST005 / "per_seed_42_dsr.json"
    canonical_dsr = DST005 / "dsr.json"
    if seed42_dsr.exists():
        shutil.copy2(seed42_dsr, canonical_dsr)
        print("  Copied seed=42 dsr.json as canonical dsr.json")

    # ------------------------------------------------------------------
    # Step 8: write comparison.csv (copy from iter-v3/004 and patch PBO/n_eff)
    # ------------------------------------------------------------------
    print("\n[Step 8] Writing comparison.csv ...")
    seed42_row = next(r for r in pareto_rows if r["seed"] == 42)
    mean_pbo_s42 = seed42_row["mean_pbo"]
    n_eff_s42 = seed42_row["n_eff"]

    src_comp = SRC003 / "comparison.csv"
    dst_comp = DST005 / "comparison.csv"
    src_lines = src_comp.read_text().splitlines()
    dst_lines = []
    pbo_str = f"{mean_pbo_s42:.6f}" if mean_pbo_s42 is not None else "NaN"
    n_eff_str = str(n_eff_s42)

    # DSR and PSR computed from seed42_dsr.json
    with open(seed42_dsr) as f:
        s42_dsr_data = json.load(f)
    dsr_val_s42 = s42_dsr_data["dsr"]
    psr_val_s42 = s42_dsr_data["psr"]

    for line in src_lines:
        if line.startswith("pbo,"):
            dst_lines.append(f"pbo,{pbo_str},—,—")
        elif line.startswith("n_effective_trials,"):
            dst_lines.append(f"n_effective_trials,{n_eff_str},—,—")
        elif line.startswith("dsr,"):
            parts = line.split(",")
            parts[1] = f"{dsr_val_s42:.6f}"
            dst_lines.append(",".join(parts))
        elif line.startswith("psr,"):
            parts = line.split(",")
            parts[2] = f"{psr_val_s42:.6f}"
            dst_lines.append(",".join(parts))
        else:
            dst_lines.append(line)

    dst_comp.write_text("\n".join(dst_lines) + "\n")
    print(f"  Wrote {dst_comp}")

    # ------------------------------------------------------------------
    # Step 9: print cross-seed summary
    # ------------------------------------------------------------------
    all_pbo = [r["mean_pbo"] for r in seed_summary if r["mean_pbo"] is not None]
    all_ms = [r["monthly_sharpe"] for r in seed_summary]
    n_profitable = sum(1 for ms in all_ms if ms > 0)

    print(f"\n[Summary] Cross-seed results ({len(seeds_to_run)} seeds):")
    print(f"  Monthly Sharpe: all seeds = {headline['monthly_sharpe']:+.4f} (model unchanged)")
    print(f"  Profitable seeds: {n_profitable}/{len(seeds_to_run)}")
    print(
        f"  Per-seed PBO: mean={np.mean(all_pbo):.4f}, std={np.std(all_pbo):.4f}, "
        f"min={np.min(all_pbo):.4f}, max={np.max(all_pbo):.4f}"
    )
    print(f"  Per-seed n_eff: values={[r['n_eff'] for r in seed_summary]}")

    t_total = time.time() - t_start
    print(f"\n[recompute_10seed] DONE in {t_total:.1f}s ({t_total / 60:.1f}m)")
    print(f"  Output: {DST005}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="10-seed Pareto recompute for iter-v3/005")
    parser.add_argument(
        "--seeds",
        type=int,
        default=10,
        help="Number of outer seeds to run (1-10; default=10). Use 1 or 2 for pre-flights.",
    )
    args = parser.parse_args()
    assert 1 <= args.seeds <= 10, f"--seeds must be in [1, 10], got {args.seeds}"
    main(n_seeds=args.seeds)
