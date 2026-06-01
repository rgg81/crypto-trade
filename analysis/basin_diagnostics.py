"""Basin-lottery detection CLI for v1 iteration reports.

Reads per-seed comparison.csv + trades.csv files from a target iteration's
reports directory, computes four new basin-lottery metrics, and writes
basin_diagnostics.json (extended schema with new fields).

New gates added on top of the src-level module:
  - compute_per_seed_spread: max-min of OOS Sharpe across outer seeds
  - compute_pairwise_jaccard: median pairwise Jaccard of trade-time-symbol sets
  - compute_cross_seed_param_spearman: Spearman rho on importance/HP ranks
  - compute_basin_lottery_verdict: "PASS" | "BASIN-LOTTERY-WEAK" | "BASIN-LOTTERY-CONFIRMED"

Usage:
    uv run python analysis/basin_diagnostics.py --reports reports-v1/iteration_v1-NNN/
    uv run python analysis/basin_diagnostics.py --reports reports-v1/iteration_v1-NNN/ \\
        --output-dir reports-v1/iteration_v1-NNN/basin_diagnostics/

Outputs:
    basin_diagnostics.json — extended schema with new fields
    per_seed_spread.txt   — diagnostic line printed to stdout

Schema additions to basin_diagnostics.json:
    v1_per_seed_spread    float   max_oos_sharpe - min_oos_sharpe across seeds
    v1_jaccard_median     float   median pairwise Jaccard of trade-time-symbol sets
    v1_spearman_rho       float   Spearman rho of feature importance ranks across seeds
    lottery_verdict       str     "PASS" | "BASIN-LOTTERY-WEAK" | "BASIN-LOTTERY-CONFIRMED"
    lottery_action_taken  str     human-readable action recommendation
"""

from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr  # type: ignore[import-untyped]

# ---------------------------------------------------------------------------
# Thresholds for basin-lottery verdict
# ---------------------------------------------------------------------------

# spread = max(oos_sharpe) - min(oos_sharpe) across outer seeds
SPREAD_WARN_THRESHOLD: float = 0.80  # >= this → WEAK signal
SPREAD_FAIL_THRESHOLD: float = 1.50  # >= this → CONFIRMED

# Jaccard median: low overlap = seeds found different trade sets
JACCARD_WEAK_THRESHOLD: float = 0.35  # <= this → WEAK (low overlap)
JACCARD_FAIL_THRESHOLD: float = 0.15  # <= this → CONFIRMED (lottery relocation)

# Spearman rho of feature importance ranks across seeds
SPEARMAN_WEAK_THRESHOLD: float = 0.60  # <= this → WEAK (unstable rankings)
SPEARMAN_FAIL_THRESHOLD: float = 0.30  # <= this → CONFIRMED (chaotic landscape)


# ---------------------------------------------------------------------------
# Core metric functions (public API)
# ---------------------------------------------------------------------------


def compute_per_seed_spread(per_seed_sharpe_array: list[float] | np.ndarray) -> float:
    """Compute max - min of OOS Sharpe across outer seeds.

    A large spread (>= 1.50) indicates that different seeds found qualitatively
    different optima — a canonical basin-lottery signature.

    Args:
        per_seed_sharpe_array: List or array of per-seed OOS Sharpe ratios.
            NaN values are ignored; must have at least 2 finite values.

    Returns:
        max(sharpes) - min(sharpes), or NaN if fewer than 2 finite values.

    Raises:
        ValueError: If the input is empty.
    """
    arr = np.asarray(per_seed_sharpe_array, dtype=float)
    if arr.size == 0:
        raise ValueError("per_seed_sharpe_array must not be empty")
    finite = arr[np.isfinite(arr)]
    if len(finite) < 2:
        return float("nan")
    return float(np.max(finite) - np.min(finite))


def compute_pairwise_jaccard(trades_per_seed_dict: dict[str, set[tuple]]) -> float:
    """Compute median pairwise Jaccard of trade-time-symbol sets across outer seeds.

    Each value in trades_per_seed_dict is a set of (symbol, open_time) tuples
    representing the trades found in that seed's OOS window.  The median of
    all C(n, 2) pairwise Jaccard coefficients is returned.

    Args:
        trades_per_seed_dict: Mapping of seed_label -> set of (symbol, open_time_int)
            tuples.  At least 2 seeds required.

    Returns:
        Median pairwise Jaccard coefficient in [0, 1], or NaN if fewer than 2 seeds.

    Raises:
        ValueError: If the input is empty.
    """
    if not trades_per_seed_dict:
        raise ValueError("trades_per_seed_dict must not be empty")
    seeds = list(trades_per_seed_dict.keys())
    if len(seeds) < 2:
        return float("nan")

    jaccards: list[float] = []
    for s1, s2 in combinations(seeds, 2):
        set1 = trades_per_seed_dict[s1]
        set2 = trades_per_seed_dict[s2]
        union = len(set1 | set2)
        if union == 0:
            jaccards.append(float("nan"))
        else:
            jaccards.append(len(set1 & set2) / union)

    valid = [j for j in jaccards if not np.isnan(j)]
    if not valid:
        return float("nan")
    return float(np.median(valid))


def compute_cross_seed_param_spearman(
    best_params_per_seed: dict[str, dict[str, float]],
) -> float:
    """Compute mean Spearman rho of HP/importance ranks across outer seeds.

    For each pair of seeds, compute the Spearman correlation of their rank
    vectors (over shared features/parameters).  Returns the mean of all
    pairwise rho values.

    A high rho (>= 0.60) means seeds agree on which parameters/features
    are most important — stable loss landscape.  A low rho (<= 0.30) means
    different seeds favour completely different regions — basin lottery.

    Args:
        best_params_per_seed: Mapping of seed_label -> dict of feature_name ->
            importance_rank (lower = more important).  All seeds should share
            the same feature keys.

    Returns:
        Mean pairwise Spearman rho, or NaN if fewer than 2 seeds or no common
        features.

    Raises:
        ValueError: If the input is empty.
    """
    if not best_params_per_seed:
        raise ValueError("best_params_per_seed must not be empty")
    seeds = list(best_params_per_seed.keys())
    if len(seeds) < 2:
        return float("nan")

    rho_values: list[float] = []
    for s1, s2 in combinations(seeds, 2):
        d1 = best_params_per_seed[s1]
        d2 = best_params_per_seed[s2]
        common_keys = sorted(set(d1.keys()) & set(d2.keys()))
        if len(common_keys) < 3:
            continue
        v1 = [d1[k] for k in common_keys]
        v2 = [d2[k] for k in common_keys]
        rho, _ = spearmanr(v1, v2)
        if np.isfinite(rho):
            rho_values.append(float(rho))

    if not rho_values:
        return float("nan")
    return float(np.mean(rho_values))


def compute_basin_lottery_verdict(
    spread: float,
    jaccard_median: float,
    spearman_rho: float,
) -> str:
    """Classify basin-lottery risk from three diagnostic metrics.

    Verdict logic (ordered by severity):
    - BASIN-LOTTERY-CONFIRMED: spread >= 1.50 OR jaccard_median <= 0.15
      OR spearman_rho <= 0.30 (at least one metric in FAIL zone)
    - BASIN-LOTTERY-WEAK: spread >= 0.80 OR jaccard_median <= 0.35
      OR spearman_rho <= 0.60 (at least one metric in WARN zone)
    - PASS: all metrics in safe zone

    NaN values are treated as unknown and do not contribute to a FAIL verdict
    (conservative: missing evidence does not trigger alarm).

    Args:
        spread: Per-seed OOS Sharpe max-min spread.
        jaccard_median: Median pairwise Jaccard across seeds.
        spearman_rho: Mean pairwise Spearman rho of importance ranks.

    Returns:
        "PASS", "BASIN-LOTTERY-WEAK", or "BASIN-LOTTERY-CONFIRMED".
    """
    # CONFIRMED: any metric in fail zone
    spread_confirmed = np.isfinite(spread) and spread >= SPREAD_FAIL_THRESHOLD
    jaccard_confirmed = np.isfinite(jaccard_median) and jaccard_median <= JACCARD_FAIL_THRESHOLD
    spearman_confirmed = np.isfinite(spearman_rho) and spearman_rho <= SPEARMAN_FAIL_THRESHOLD

    if spread_confirmed or jaccard_confirmed or spearman_confirmed:
        return "BASIN-LOTTERY-CONFIRMED"

    # WEAK: any metric in warn zone
    spread_weak = np.isfinite(spread) and spread >= SPREAD_WARN_THRESHOLD
    jaccard_weak = np.isfinite(jaccard_median) and jaccard_median <= JACCARD_WEAK_THRESHOLD
    spearman_weak = np.isfinite(spearman_rho) and spearman_rho <= SPEARMAN_WEAK_THRESHOLD

    if spread_weak or jaccard_weak or spearman_weak:
        return "BASIN-LOTTERY-WEAK"

    return "PASS"


def _verdict_to_action(verdict: str) -> str:
    """Convert lottery verdict to a human-readable action recommendation."""
    if verdict == "PASS":
        return "No action required — seed ensemble is stable."
    if verdict == "BASIN-LOTTERY-WEAK":
        return (
            "Warning: weak lottery signal detected. Consider adding a 3rd outer seed "
            "before merge evaluation. Do NOT increase n_trials without brief update."
        )
    # CONFIRMED
    return (
        "BLOCK merge: basin-lottery confirmed. Escalate to QR. Options: "
        "(1) add >=5 outer seeds and verify mean OOS Sharpe > 0, "
        "(2) freeze HP from IS-best seed and re-run OOS, "
        "(3) declare EXPLORATION-NEGATIVE and abandon axis."
    )


# ---------------------------------------------------------------------------
# Report-directory reader helpers
# ---------------------------------------------------------------------------


def _find_seed_dirs(reports_dir: Path) -> list[Path]:
    """Find per-seed subdirectories inside a reports directory.

    Supports two layouts:
      Layout A (multi-seed): reports_dir/{seed_42,seed_offset3,...}/comparison.csv
      Layout B (single-seed): reports_dir/comparison.csv (treated as seed_42)

    Returns a list of directories that contain comparison.csv.
    """
    # Layout A: subdirs named seed_*
    seed_subdirs = sorted(reports_dir.glob("seed_*"))
    valid_a = [d for d in seed_subdirs if d.is_dir() and (d / "comparison.csv").exists()]
    if valid_a:
        return valid_a

    # Layout B: comparison.csv directly in reports_dir
    if (reports_dir / "comparison.csv").exists():
        return [reports_dir]

    return []


def _read_oos_sharpe_from_seed_dir(seed_dir: Path) -> float:
    """Read OOS Sharpe from comparison.csv in a seed directory."""
    csv_path = seed_dir / "comparison.csv"
    df = pd.read_csv(csv_path)
    # comparison.csv has columns: metric, in_sample, out_of_sample, ratio
    if "metric" in df.columns and "out_of_sample" in df.columns:
        row = df[df["metric"] == "sharpe"]
        if not row.empty:
            val = row.iloc[0]["out_of_sample"]
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
    return float("nan")


def _read_trade_set_from_seed_dir(seed_dir: Path) -> set[tuple]:
    """Read (symbol, open_time_int) trade set from OOS trades.csv in a seed directory."""
    trades_path = seed_dir / "out_of_sample" / "trades.csv"
    if not trades_path.exists():
        return set()
    df = pd.read_csv(trades_path)
    if "symbol" not in df.columns or "open_time" not in df.columns:
        return set()
    pairs = set(zip(df["symbol"], df["open_time"].astype(int)))
    return pairs


def _read_importance_ranks_from_seed_dir(seed_dir: Path) -> dict[str, float]:
    """Read feature importance ranks from the portfolio CSV in a seed directory.

    Returns mapping of feature_name -> importance_rank (lower = more important).
    """
    # Try portfolio first, then any feature_importance*.csv
    candidates = list((seed_dir / "in_sample").glob("feature_importance_portfolio.csv"))
    if not candidates:
        candidates = list((seed_dir / "in_sample").glob("feature_importance*.csv"))
    if not candidates:
        # Also check directly in seed_dir
        candidates = list(seed_dir.glob("feature_importance_portfolio.csv"))
        if not candidates:
            candidates = list(seed_dir.glob("feature_importance*.csv"))
    if not candidates:
        return {}

    df = pd.read_csv(candidates[0])
    if "feature_name" not in df.columns or "importance_rank" not in df.columns:
        # Try mean_gain as proxy for rank
        if "feature_name" in df.columns and "mean_gain" in df.columns:
            df = df.sort_values("mean_gain", ascending=False).reset_index(drop=True)
            df["importance_rank"] = df.index + 1
        else:
            return {}

    return dict(zip(df["feature_name"], df["importance_rank"].astype(float)))


# ---------------------------------------------------------------------------
# Main CLI logic
# ---------------------------------------------------------------------------


def run_basin_diagnostics(reports_dir: Path, output_dir: Path | None = None) -> dict[str, Any]:
    """Run all four new basin-lottery gates on a reports directory.

    Args:
        reports_dir: Path to iteration reports directory.
        output_dir: Where to write basin_diagnostics.json.  Defaults to
            reports_dir/basin_diagnostics/.

    Returns:
        Extended summary dict written to basin_diagnostics.json.
    """
    if output_dir is None:
        output_dir = reports_dir / "basin_diagnostics"
    output_dir.mkdir(parents=True, exist_ok=True)

    seed_dirs = _find_seed_dirs(reports_dir)
    if not seed_dirs:
        print(
            "[basin_diagnostics] ERROR: no seed directories with"
            f" comparison.csv found in {reports_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[basin_diagnostics] Found {len(seed_dirs)} seed dir(s): {[d.name for d in seed_dirs]}")

    # --- Collect per-seed data ---
    per_seed_sharpes: list[float] = []
    trades_per_seed: dict[str, set[tuple]] = {}
    importance_per_seed: dict[str, dict[str, float]] = {}

    for seed_dir in seed_dirs:
        label = seed_dir.name
        sharpe = _read_oos_sharpe_from_seed_dir(seed_dir)
        per_seed_sharpes.append(sharpe)
        if np.isfinite(sharpe):
            print(f"  [{label}] OOS Sharpe = {sharpe:.4f}")
        else:
            print(f"  [{label}] OOS Sharpe = NaN")

        trades = _read_trade_set_from_seed_dir(seed_dir)
        trades_per_seed[label] = trades
        print(f"  [{label}] OOS trades = {len(trades)}")

        ranks = _read_importance_ranks_from_seed_dir(seed_dir)
        importance_per_seed[label] = ranks
        print(f"  [{label}] importance features = {len(ranks)}")

    # --- Compute metrics ---
    spread = compute_per_seed_spread(per_seed_sharpes)
    jaccard_median = compute_pairwise_jaccard(trades_per_seed)
    spearman_rho = compute_cross_seed_param_spearman(importance_per_seed)
    verdict = compute_basin_lottery_verdict(spread, jaccard_median, spearman_rho)
    action = _verdict_to_action(verdict)

    # --- Print diagnostics ---
    spread_str = f"{spread:.4f}" if np.isfinite(spread) else "NaN"
    jaccard_str = f"{jaccard_median:.4f}" if np.isfinite(jaccard_median) else "NaN"
    spearman_str = f"{spearman_rho:.4f}" if np.isfinite(spearman_rho) else "NaN"

    print(
        f"\n[basin_diagnostics] spread={spread_str} "
        f"jaccard_median={jaccard_str} "
        f"spearman_rho={spearman_str} "
        f"-> LOTTERY_VERDICT={verdict}"
    )
    print(f"[basin_diagnostics] ACTION: {action}")

    # --- Load existing basin_diagnostics.json if present (to merge V1/V2/V3 fields) ---
    existing_json_path = output_dir / "basin_diagnostics.json"
    existing: dict[str, Any] = {}
    if existing_json_path.exists():
        try:
            with open(existing_json_path) as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            existing = {}

    # --- Build extended summary ---
    summary: dict[str, Any] = existing.copy()
    summary["v1_per_seed_spread"] = spread if np.isfinite(spread) else None
    summary["v1_jaccard_median"] = jaccard_median if np.isfinite(jaccard_median) else None
    summary["v1_spearman_rho"] = spearman_rho if np.isfinite(spearman_rho) else None
    summary["lottery_verdict"] = verdict
    summary["lottery_action_taken"] = action

    # Write extended JSON
    with open(existing_json_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"[basin_diagnostics] Written: {existing_json_path}")
    return summary


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Basin-lottery detection for v1 iteration reports.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--reports",
        required=True,
        type=Path,
        help="Path to iteration reports directory (e.g. reports-v1/iteration_v1-034/).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for basin_diagnostics.json (default: --reports/basin_diagnostics/).",
    )
    args = parser.parse_args()

    reports_dir = args.reports
    if not reports_dir.exists():
        print(
            f"[basin_diagnostics] ERROR: reports directory not found: {reports_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    run_basin_diagnostics(reports_dir, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
