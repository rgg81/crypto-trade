"""Recompute iter-v3/004 metrics WITHOUT re-running the backtest.

This script:
1. Copies in_sample/ and out_of_sample/ from iter-v3/003 (model unchanged).
2. Loads iter-v3/003's trial_oof_returns.parquet as the consumer input.
3. Calls the now-modified _compute_cpcv_paths (per-cell CSCV) and n_eff
   (per-cell median) from run_baseline_v3 to produce per_cell_pbo.csv,
   dsr.json, comparison.csv, cpcv_paths.csv, pareto_front.csv,
   seed_summary.json, adf_test.csv, ic_matrix.csv.
4. Writes all outputs to reports-v3/iteration_v3-004/.

Wall-clock: 5-30 minutes (CSCV on 173 cells at 45 paths each).

Brief reference: Section 3.5 sub-fixes #1, #2, #4 and Section 3.9 alt path.

Usage:
    uv run python analysis/iteration_v3-004/recompute_metrics.py
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew

# ============================================================
# Paths
# ============================================================
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC003 = REPO_ROOT / "reports-v3" / "iteration_v3-003"
DST004 = REPO_ROOT / "reports-v3" / "iteration_v3-004"
OOF_PARQUET = SRC003 / "trial_oof_returns.parquet"
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC — IMMUTABLE

# ============================================================
# Import runner functions (after PYTHONPATH is configured by uv)
# ============================================================
sys.path.insert(0, str(REPO_ROOT / "src"))

# Deferred import to avoid circular issues
from crypto_trade.strategies.ml.validation_v3 import (  # noqa: E402
    PBOResult,
    deflated_sharpe_ratio_v3,
    n_effective_trials,
    psr,
)


def main() -> None:
    t_start = time.time()
    print(f"[recompute] Starting iter-v3/004 metrics recompute at {time.strftime('%H:%M:%S')}")
    print(f"[recompute] Source: {SRC003}")
    print(f"[recompute] Target: {DST004}")
    print(f"[recompute] OOF parquet: {OOF_PARQUET}")

    # Verify input artifacts
    assert OOF_PARQUET.exists(), f"OOF parquet not found: {OOF_PARQUET}"
    assert (SRC003 / "in_sample" / "trades.csv").exists(), "iter-v3/003 IS trades missing"
    assert (SRC003 / "out_of_sample" / "trades.csv").exists(), "iter-v3/003 OOS trades missing"

    # ============================================================
    # Step 1: copy in_sample/ and out_of_sample/ from iter-v3/003
    # ============================================================
    print("\n[Step 1] Copying in_sample/ and out_of_sample/ from iter-v3/003 ...")
    DST004.mkdir(parents=True, exist_ok=True)
    for split in ["in_sample", "out_of_sample"]:
        src_split = SRC003 / split
        dst_split = DST004 / split
        if dst_split.exists():
            shutil.rmtree(dst_split)
        shutil.copytree(src_split, dst_split)
        print(f"  Copied {src_split} → {dst_split}")

    # ============================================================
    # Step 2: copy static artifacts that are also unchanged
    # ============================================================
    print("\n[Step 2] Copying static artifacts ...")
    for fname in ["adf_test.csv", "ic_matrix.csv"]:
        src_f = SRC003 / fname
        dst_f = DST004 / fname
        if src_f.exists():
            shutil.copy2(src_f, dst_f)
            print(f"  Copied {fname}")

    # ============================================================
    # Step 3: load trades to rebuild metric inputs
    # ============================================================
    print("\n[Step 3] Loading trades from copied CSVs ...")

    def _load_trades_csv(path: Path) -> list[dict]:
        """Load trades.csv into a list of dicts with numeric fields."""
        rows = []
        import csv

        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        return rows

    class TradeLike:
        """Minimal trade object compatible with runner metric functions."""

        def __init__(self, row: dict) -> None:
            self.open_time = int(float(row.get("open_time", 0)))
            self.close_time = int(float(row.get("close_time", 0)))
            self.weighted_pnl = float(row.get("weighted_pnl", 0.0))
            self.symbol = row.get("symbol", "")

    is_rows = _load_trades_csv(DST004 / "in_sample" / "trades.csv")
    oos_rows = _load_trades_csv(DST004 / "out_of_sample" / "trades.csv")
    is_trades = [TradeLike(r) for r in is_rows]
    oos_trades = [TradeLike(r) for r in oos_rows]
    print(f"  IS trades: {len(is_trades)}, OOS trades: {len(oos_trades)}")

    # ============================================================
    # Step 4: per-cell PBO computation (sub-fix #1)
    # Inline implementation mirrors run_baseline_v3._compute_per_cell_pbo
    # ============================================================
    print("\n[Step 4] Per-cell CSCV PBO computation ...")

    from crypto_trade.strategies.ml.validation_v3 import (
        combinatorial_purged_cv,
        pbo_from_cpcv,
    )

    per_cell_n_splits = 10
    per_cell_k = 2
    per_cell_gap = 22

    oof_df = pd.read_parquet(OOF_PARQUET)
    n_raw = len(oof_df)
    oof_df = oof_df.drop_duplicates(
        subset=["symbol", "train_month", "trial_id", "fold_idx", "candle_open_time_ms"]
    )
    n_dedup = len(oof_df)
    oof_df = oof_df[oof_df["candle_open_time_ms"] < OOS_CUTOFF_MS].copy()
    n_is = len(oof_df)
    print(f"  Raw={n_raw}, after dedup={n_dedup}, IS-only={n_is}")

    cells = sorted(oof_df.groupby(["symbol", "train_month"]).groups.keys())
    n_cells = len(cells)
    print(f"  Iterating over {n_cells} (sym, month) cells ...")

    cell_rows: list[dict] = []

    for cell_idx, (sym, month) in enumerate(cells):
        cell_df = oof_df[(oof_df["symbol"] == sym) & (oof_df["train_month"] == month)]
        n_trials_cell = int(cell_df["trial_id"].nunique())
        n_candles_cell = int(cell_df["candle_open_time_ms"].nunique())

        if n_trials_cell < 2 or n_candles_cell < per_cell_n_splits * 3:
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
                n_splits=per_cell_n_splits,
                n_test_splits=per_cell_k,
                gap=per_cell_gap,
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

            pbo_res = pbo_from_cpcv(path_mat, max_splits=5000)
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

        if (cell_idx + 1) % 25 == 0:
            print(f"  {cell_idx + 1}/{n_cells} cells processed ...")

    print(f"  Completed {n_cells} cells")
    per_cell_df = pd.DataFrame(cell_rows)
    per_cell_csv = DST004 / "per_cell_pbo.csv"
    per_cell_df.to_csv(per_cell_csv, index=False)
    print(f"  Wrote {per_cell_csv} ({len(per_cell_df)} rows)")

    informative = per_cell_df[per_cell_df["rank"] > 1]["pbo"].dropna()
    n_informative = len(informative)
    mean_pbo = float(informative.mean()) if n_informative > 0 else float("nan")
    median_pbo = float(informative.median()) if n_informative > 0 else float("nan")
    print(f"  Informative cells: {n_informative}/{n_cells}")
    print(f"  Aggregated mean PBO={mean_pbo:.4f}, median PBO={median_pbo:.4f}")
    print(f"  |delta mean-median|={abs(mean_pbo - median_pbo):.4f}")

    # ============================================================
    # Step 5: n_eff via per-cell median (sub-fix #2)
    # ============================================================
    print("\n[Step 5] Per-cell median n_eff ...")
    informative_neff = per_cell_df[per_cell_df["rank"] > 1]["n_eff"].dropna()
    n_eff = int(np.median(informative_neff)) if len(informative_neff) > 0 else 1
    print(f"  Per-cell median n_eff={n_eff} from {len(informative_neff)} informative cells")

    # ============================================================
    # Step 6: DSR, PSR, n_trials
    # ============================================================
    print("\n[Step 6] DSR, PSR, n_trials ...")
    ensemble_seeds = [42, 123, 456, 789, 1001]
    n_symbols = 4
    n_trials_per_seed = 50
    n_seeds = 1  # primary seed only
    n_trials_total = n_trials_per_seed * len(ensemble_seeds) * n_symbols * n_seeds

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

    print(f"  DSR={dsr_val:.4f}, PSR={psr_val:.4f}, n_trials={n_trials_total}")

    # ============================================================
    # Step 7: Build PBOResult and write dsr.json
    # ============================================================
    print("\n[Step 7] Writing dsr.json ...")
    pbo_result = PBOResult(
        pbo=mean_pbo if not np.isnan(mean_pbo) else None,
        frac_positive_paths=float("nan"),
        path_sharpe_quartiles=(float("nan"), float("nan"), float("nan")),
        n_splits_evaluated=n_informative,
        note=(
            f"Per-cell mean PBO={mean_pbo:.4f} (iter-v3/004 cross-cell mean). "
            f"{n_informative} informative cells (rank>1)."
        ),
    )

    # Monthly Sharpe helpers
    def _monthly_sharpe(trades: list) -> float:
        if not trades:
            return 0.0
        months = pd.to_datetime([t.close_time for t in trades], unit="ms").to_period("M")
        monthly = (
            pd.Series([t.weighted_pnl for t in trades], index=months).groupby(level=0).sum() / 100.0
        )
        if len(monthly) < 2 or monthly.std() == 0:
            return 0.0
        return float(monthly.mean() / monthly.std() * np.sqrt(12))

    is_ms = _monthly_sharpe(is_trades)
    oos_ms = _monthly_sharpe(oos_trades)
    min_trl_months = float(len(is_trades)) / max(1, len(ensemble_seeds) * n_symbols)

    # Write dsr.json — reuse _write_dsr_json logic inline
    pbo_out = pbo_result.pbo
    dsr_dict = {
        "dsr": round(dsr_val, 6),
        "pbo": pbo_out,
        "pbo_note": pbo_result.note,
        "pbo_frac_positive_paths": round(pbo_result.frac_positive_paths, 4)
        if np.isfinite(pbo_result.frac_positive_paths)
        else None,
        "pbo_path_sharpe_q25": None,
        "pbo_path_sharpe_q50": None,
        "pbo_path_sharpe_q75": None,
        "psr": round(psr_val, 6),
        "n_eff": n_eff,
        "n_trials": n_trials_total,
        "min_trl_months": round(min_trl_months, 2),
    }
    dsr_path = DST004 / "dsr.json"
    dsr_path.write_text(json.dumps(dsr_dict, indent=2))
    print(f"  Wrote {dsr_path}")
    print(f"  PBO={pbo_out}, n_eff={n_eff}, DSR={dsr_val:.4f}, PSR={psr_val:.4f}")

    # ============================================================
    # Step 8: Write comparison.csv (copy from iter-v3/003 and patch PBO/n_eff rows)
    # comparison.csv has mixed format: CSV header rows + comment line + per-symbol rows
    # Must patch line-by-line to avoid pandas CSV parsing errors on comment lines.
    # ============================================================
    print("\n[Step 8] Writing comparison.csv ...")
    src_comp = SRC003 / "comparison.csv"
    dst_comp = DST004 / "comparison.csv"

    src_lines = src_comp.read_text().splitlines()
    dst_lines = []
    pbo_str = f"{mean_pbo:.6f}" if not np.isnan(mean_pbo) else "NaN"
    n_eff_str = str(n_eff)

    for line in src_lines:
        # Only patch the 4-column CSV rows (not the comment or per-symbol rows)
        if line.startswith("pbo,"):
            dst_lines.append(f"pbo,{pbo_str},—,—")
        elif line.startswith("n_effective_trials,"):
            dst_lines.append(f"n_effective_trials,{n_eff_str},—,—")
        elif line.startswith("dsr,"):
            parts = line.split(",")
            parts[1] = f"{dsr_val:.6f}"
            dst_lines.append(",".join(parts))
        elif line.startswith("psr,"):
            parts = line.split(",")
            parts[2] = f"{psr_val:.6f}"
            dst_lines.append(",".join(parts))
        else:
            dst_lines.append(line)

    dst_comp.write_text("\n".join(dst_lines) + "\n")
    n_data_rows = sum(
        1 for ln in dst_lines if ln and not ln.startswith("#") and not ln.startswith("metric,")
    )
    print(f"  Wrote {dst_comp} ({n_data_rows} data rows)")

    # ============================================================
    # Step 9: Write cpcv_paths.csv (copy from iter-v3/003 — return proxy unchanged)
    # ============================================================
    print("\n[Step 9] Copying cpcv_paths.csv ...")
    src_cpcv = SRC003 / "cpcv_paths.csv"
    dst_cpcv = DST004 / "cpcv_paths.csv"
    if src_cpcv.exists():
        shutil.copy2(src_cpcv, dst_cpcv)
        print(f"  Copied {src_cpcv} → {dst_cpcv}")
    else:
        import csv as _csv

        with open(dst_cpcv, "w", newline="") as f:
            _csv.writer(f).writerow(["path_id", "sharpe", "max_dd", "n_candles"])
        print("  cpcv_paths.csv not found in iter-v3/003 — wrote empty")

    # ============================================================
    # Step 10: Write pareto_front.csv and seed_summary.json
    # (these are per-seed, but with pbo updated to the computed float)
    # ============================================================
    print("\n[Step 10] Copying and patching pareto_front.csv, seed_summary.json ...")
    src_pareto = SRC003 / "pareto_front.csv"
    dst_pareto = DST004 / "pareto_front.csv"
    if src_pareto.exists():
        pareto_df = pd.read_csv(src_pareto)
        # Patch pbo column to the per-cell mean PBO (sub-fix #5 for pareto_front)
        pareto_df["pbo"] = round(mean_pbo, 6) if not np.isnan(mean_pbo) else None
        pareto_df.to_csv(dst_pareto, index=False)
        print(f"  Wrote {dst_pareto} ({len(pareto_df)} rows)")

    src_seed = SRC003 / "seed_summary.json"
    dst_seed = DST004 / "seed_summary.json"
    if src_seed.exists():
        with open(src_seed) as f:
            seed_data = json.load(f)
        # Patch pbo field (sub-fix #5)
        for entry in seed_data:
            entry["pbo"] = round(mean_pbo, 6) if not np.isnan(mean_pbo) else None
        dst_seed.write_text(json.dumps(seed_data, indent=2))
        print(f"  Wrote {dst_seed}")

    # ============================================================
    # Done
    # ============================================================
    t_end = time.time()
    elapsed = t_end - t_start
    print(f"\n[recompute] DONE in {elapsed:.1f}s ({elapsed / 60:.1f}m)")
    print(f"  per_cell_pbo.csv: {len(per_cell_df)} rows, {n_informative} informative")
    print(f"  Aggregated mean PBO = {mean_pbo:.4f}")
    print(f"  Median n_eff = {n_eff}")
    print(f"  DSR = {dsr_val:.4f}, PSR = {psr_val:.4f}")
    print(f"  IS monthly Sharpe = {is_ms:+.4f}")
    print(f"  OOS monthly Sharpe = {oos_ms:+.4f}")
    print(f"\n  Output: {DST004}")


if __name__ == "__main__":
    main()
