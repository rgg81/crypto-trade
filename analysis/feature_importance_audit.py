"""Feature-importance audit script for v1 iteration reports.

Reads per-seed (or per-month) feature_importance CSVs from a target iteration's
reports directory.  Computes mean_rank + std_of_rank per feature across all
available slices, then produces a drop-list for features that are consistently
ranked near the bottom (mean_rank >= 12 AND std_of_rank < 2.0).

Usage:
    uv run python analysis/feature_importance_audit.py \\
        --iter 055 \\
        --output drop_list.txt

    # Explicitly specify which reports root to use:
    uv run python analysis/feature_importance_audit.py \\
        --iter 055 \\
        --reports-root reports-v1 \\
        --output drop_list.txt

    # Override drop criteria:
    uv run python analysis/feature_importance_audit.py \\
        --iter 057 \\
        --min-mean-rank 10 \\
        --max-std-rank 3.0

Outputs:
    drop_list.txt      — one feature name per line (empty if nothing to drop)
    audit_summary.md   — markdown table with mean_rank, std_of_rank, verdict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Default drop-criteria thresholds
# ---------------------------------------------------------------------------

DEFAULT_MIN_MEAN_RANK: float = 12.0  # features with mean_rank >= this are candidates
DEFAULT_MAX_STD_RANK: float = 2.0  # AND std_of_rank < this (consistently bottom)


# ---------------------------------------------------------------------------
# Feature importance CSV discovery
# ---------------------------------------------------------------------------


def find_feature_importance_csvs(reports_dir: Path) -> list[Path]:
    """Discover all feature_importance CSVs in a reports directory.

    Searches recursively for files matching feature_importance*.csv across:
    - reports_dir/ (single-seed layout)
    - reports_dir/seed_*/ (multi-seed layout)
    - reports_dir/in_sample/ + reports_dir/seed_*/in_sample/

    Returns list of paths, empty if none found.
    """
    found: list[Path] = []

    # Patterns to try
    patterns = [
        "feature_importance*.csv",
        "*/feature_importance*.csv",
        "seed_*/in_sample/feature_importance*.csv",
        "in_sample/feature_importance*.csv",
    ]
    for pattern in patterns:
        found.extend(reports_dir.glob(pattern))

    # Deduplicate preserving order
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in found:
        resolved = p.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(p)

    return sorted(unique)


def read_feature_importance_csv(path: Path) -> pd.DataFrame | None:
    """Read a single feature_importance CSV and return a normalised DataFrame.

    Expected columns: feature_name, importance_rank (or mean_gain as fallback).
    Returns None if the file cannot be parsed.
    """
    try:
        df = pd.read_csv(path)
    except Exception:  # noqa: BLE001
        return None

    if "feature_name" not in df.columns:
        return None

    if "importance_rank" in df.columns:
        df = df[["feature_name", "importance_rank"]].copy()
        df["importance_rank"] = pd.to_numeric(df["importance_rank"], errors="coerce")
    elif "mean_gain" in df.columns:
        # Derive rank from mean_gain descending
        df = df[["feature_name", "mean_gain"]].copy()
        df["mean_gain"] = pd.to_numeric(df["mean_gain"], errors="coerce")
        df = df.dropna(subset=["mean_gain"])
        df = df.sort_values("mean_gain", ascending=False).reset_index(drop=True)
        df["importance_rank"] = df.index + 1
        df = df[["feature_name", "importance_rank"]]
    else:
        return None

    df = df.dropna(subset=["importance_rank"])
    if df.empty:
        return None
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Core audit logic
# ---------------------------------------------------------------------------


def compute_rank_stats(slices: list[pd.DataFrame]) -> pd.DataFrame:
    """Compute mean_rank and std_of_rank per feature across all slices.

    Args:
        slices: List of DataFrames, each with columns feature_name, importance_rank.
            Each DataFrame represents one seed / month slice.

    Returns:
        DataFrame with columns: feature_name, mean_rank, std_of_rank, n_slices.
        Sorted by mean_rank ascending.

    Raises:
        ValueError: If slices is empty.
    """
    if not slices:
        raise ValueError("slices must not be empty")

    combined = pd.concat(slices, ignore_index=True)
    stats = (
        combined.groupby("feature_name")["importance_rank"]
        .agg(mean_rank="mean", std_of_rank="std", n_slices="count")
        .reset_index()
    )
    stats["std_of_rank"] = stats["std_of_rank"].fillna(0.0)
    stats = stats.sort_values("mean_rank").reset_index(drop=True)
    return stats


def build_drop_list(
    stats: pd.DataFrame,
    min_mean_rank: float = DEFAULT_MIN_MEAN_RANK,
    max_std_rank: float = DEFAULT_MAX_STD_RANK,
) -> list[str]:
    """Return features that are consistently bottom-ranked and stable.

    Criteria: mean_rank >= min_mean_rank AND std_of_rank < max_std_rank.
    A stable low rank means the feature is not just accidentally bad in one
    walk-forward month; it is persistently unused.

    Args:
        stats: DataFrame from compute_rank_stats.
        min_mean_rank: Mean rank threshold (inclusive).
        max_std_rank: Std-of-rank threshold (exclusive — consistently bad).

    Returns:
        Sorted list of feature names to drop.
    """
    mask = (stats["mean_rank"] >= min_mean_rank) & (stats["std_of_rank"] < max_std_rank)
    candidates = stats.loc[mask, "feature_name"].tolist()
    return sorted(candidates)


def format_audit_summary(
    stats: pd.DataFrame,
    drop_list: list[str],
    min_mean_rank: float,
    max_std_rank: float,
    iter_label: str,
    slice_count: int,
) -> str:
    """Format a markdown audit summary table.

    Args:
        stats: Full rank-stats DataFrame.
        drop_list: Features recommended for dropping.
        min_mean_rank: Threshold used.
        max_std_rank: Threshold used.
        iter_label: Iteration label string (e.g. "055").
        slice_count: Number of slices (seeds/months) analysed.

    Returns:
        Markdown string.
    """
    drop_set = set(drop_list)
    lines: list[str] = [
        f"# Feature Importance Audit — iter-v1/{iter_label}",
        "",
        f"**Slices analysed:** {slice_count}  ",
        f"**Drop criteria:** mean_rank >= {min_mean_rank} AND std_of_rank < {max_std_rank}  ",
        f"**Features to drop:** {len(drop_list)}",
        "",
        "## Rank Table",
        "",
        "| # | feature_name | mean_rank | std_of_rank | n_slices | verdict |",
        "|---|--------------|-----------|-------------|----------|---------|",
    ]
    for i, row in stats.iterrows():
        name = row["feature_name"]
        verdict = "DROP" if name in drop_set else "keep"
        lines.append(
            f"| {int(i) + 1} | {name} | {row['mean_rank']:.2f} | "
            f"{row['std_of_rank']:.2f} | {int(row['n_slices'])} | {verdict} |"
        )

    lines.extend(
        [
            "",
            "## Drop List",
            "",
        ]
    )
    if drop_list:
        for feat in drop_list:
            lines.append(f"- `{feat}`")
    else:
        lines.append("*(nothing to drop)*")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Feature importance audit: rank stability across seeds/months.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--iter",
        required=True,
        metavar="NNN",
        help="Iteration number (e.g. 055).  Used to locate reports-v1/iteration_v1-NNN/.",
    )
    parser.add_argument(
        "--reports-root",
        default="reports-v1",
        type=Path,
        help="Root directory for v1 reports (default: reports-v1).",
    )
    parser.add_argument(
        "--output",
        default="drop_list.txt",
        type=Path,
        help="Output path for the drop list (default: drop_list.txt).",
    )
    parser.add_argument(
        "--min-mean-rank",
        type=float,
        default=DEFAULT_MIN_MEAN_RANK,
        help=f"Mean-rank threshold for drop candidates (default: {DEFAULT_MIN_MEAN_RANK}).",
    )
    parser.add_argument(
        "--max-std-rank",
        type=float,
        default=DEFAULT_MAX_STD_RANK,
        help=f"Std-of-rank threshold for drop candidates (default: {DEFAULT_MAX_STD_RANK}).",
    )
    args = parser.parse_args()

    iter_label = args.iter.zfill(3)
    reports_dir = args.reports_root / f"iteration_v1-{iter_label}"

    if not reports_dir.exists():
        print(
            f"[feature_importance_audit] ERROR: reports directory not found: {reports_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    csvs = find_feature_importance_csvs(reports_dir)
    if not csvs:
        print(
            "[feature_importance_audit] ERROR: no feature_importance*.csv found"
            f" under {reports_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[feature_importance_audit] Found {len(csvs)} feature importance CSV(s).")

    slices: list[pd.DataFrame] = []
    for csv_path in csvs:
        df = read_feature_importance_csv(csv_path)
        if df is not None:
            slices.append(df)
            print(f"  Loaded {csv_path.relative_to(args.reports_root)} ({len(df)} features)")
        else:
            print(
                f"  SKIP {csv_path.relative_to(args.reports_root)} (unrecognised format)",
                file=sys.stderr,
            )

    if not slices:
        print(
            "[feature_importance_audit] ERROR: no valid slices could be parsed.",
            file=sys.stderr,
        )
        sys.exit(1)

    stats = compute_rank_stats(slices)
    drop_list = build_drop_list(stats, args.min_mean_rank, args.max_std_rank)

    # Write drop list
    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(drop_list) + ("\n" if drop_list else ""))
    print(f"\n[feature_importance_audit] drop_list -> {output_path} ({len(drop_list)} features)")

    # Write audit summary markdown
    summary_path = output_path.parent / "audit_summary.md"
    md = format_audit_summary(
        stats,
        drop_list,
        args.min_mean_rank,
        args.max_std_rank,
        iter_label,
        len(slices),
    )
    with open(summary_path, "w") as f:
        f.write(md)
    print(f"[feature_importance_audit] audit_summary -> {summary_path}")

    # Print brief console summary
    print(f"\n{'Feature':<40} {'mean_rank':>10} {'std_rank':>9} {'verdict':>8}")
    print("-" * 72)
    drop_set = set(drop_list)
    for _, row in stats.iterrows():
        verdict = "DROP" if row["feature_name"] in drop_set else "keep"
        print(
            f"{row['feature_name']:<40} {row['mean_rank']:>10.2f} "
            f"{row['std_of_rank']:>9.2f} {verdict:>8}"
        )

    if drop_list:
        print(f"\n[feature_importance_audit] Recommend dropping {len(drop_list)} feature(s):")
        for feat in drop_list:
            print(f"  - {feat}")
    else:
        print("\n[feature_importance_audit] No features recommended for dropping.")


if __name__ == "__main__":
    main()
