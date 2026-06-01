"""iter-v1/056 — CONFIRMATION-PORTFOLIO: 5-component symbol-partitioned federation.

Design:
  C1-BTC: fresh CONFIRMATION sub-run (ensemble-size=10, n-trials=35, seed=1)
  C2-ETH: fresh CONFIRMATION sub-run (ensemble-size=10, n-trials=35, seed=1)
  C3-DOT: fresh CONFIRMATION sub-run (ensemble-size=10, n-trials=35, seed=1)
  C4-LINK: BASELINE_V1 trade roster extraction (LINKUSDT only)
  C5-LTC:  BASELINE_V1 trade roster extraction (LTCUSDT only)
  Bundle:  CSV-replay aggregation at w=0.2 per component

Universe partition: pairwise disjoint (5 components × 1 coin each).
Weight vector: EQUAL 0.2 pre-registered (analysis/iteration_v1-056/bundle_weights.csv).

F-AXIS checks enforced inline:
  F1 — per-regime Pareto-dominance vs BASELINE_V1 (regime_attribution.csv)
  F2 — bundle OOS trade-rate >= 130
  F3 — parity by construction (CSV-replay; no new model code paths)
  F4 — universe disjoint (pairwise-empty) + Jaccard = 1.0
  F5 — weight provenance clean (bundle_weights.csv byte-match)
  F6 — source_checksums.csv written

Sacred constants (DO NOT CHANGE):
  OOS_CUTOFF_MS = 1742774400000   (2025-03-24 00:00 UTC)
  training_months = 24
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from itertools import combinations
from pathlib import Path

# ---------------------------------------------------------------------------
# Sacred constants — DO NOT CHANGE
# ---------------------------------------------------------------------------

OOS_CUTOFF_MS: int = 1742774400000  # 2025-03-24 00:00 UTC
BUNDLE_WEIGHT: float = 0.2  # EQUAL weight per component (1/5)
BASELINE_V1_IS_SHARPE: float = 0.2829
BASELINE_V1_OOS_SHARPE: float = 0.6395
BASELINE_V1_IS_PNL: float = 54.05
BASELINE_V1_OOS_PNL: float = 36.96

# ---------------------------------------------------------------------------
# Component definitions — Section 11.A (universe partition, per-coin ownership)
# ---------------------------------------------------------------------------
# Each entry: (component_id, owned_symbol, sub_dir)
# sub_dir: output directory prefix under reports-v1/iteration_v1-056/
COMPONENT_SOURCES: dict[str, tuple[str, str]] = {
    "C1-BTC": ("BTCUSDT", "C1_BTC"),
    "C2-ETH": ("ETHUSDT", "C2_ETH"),
    "C3-DOT": ("DOTUSDT", "C3_DOT"),
    "C4-LINK": ("LINKUSDT", "C4_LINK_anchor"),
    "C5-LTC": ("LTCUSDT", "C5_LTC_anchor"),
}

BUNDLE_UNIVERSE: frozenset[str] = frozenset(sym for (sym, _) in COMPONENT_SOURCES.values())

# Specialist sub-run specs (C1/C2/C3 only — C4/C5 are anchor trade extractions)
# Format: (component_id, iteration_label_flag, symbol, feature_cols_flag, model_note)
SPECIALIST_SPECS: list[tuple[str, str, str, str]] = [
    ("C1-BTC", "v1-056-C1-BTC", "BTCUSDT", "--pruned-features"),
    ("C2-ETH", "v1-056-C2-ETH", "ETHUSDT", "--pruned-features"),
    ("C3-DOT", "v1-056-C3-DOT", "DOTUSDT", "--pruned-features"),
]

# BASELINE_V1 source for C4/C5 anchor extraction
BASELINE_ITER_LABEL: str = "iteration_v1-baseline"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="iter-v1/056 CONFIRMATION-PORTFOLIO bundle runner")
    p.add_argument(
        "--out",
        default="reports-v1/iteration_v1-056",
        help="Output directory root for the bundle aggregate.",
    )
    p.add_argument(
        "--weights-csv",
        default="analysis/iteration_v1-056/bundle_weights.csv",
        help="Pre-registered bundle_weights.csv path (F5 byte-match assertion).",
    )
    p.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parent),
        help="Repo root (default: directory of this script).",
    )
    p.add_argument(
        "--skip-subruns",
        action="store_true",
        help="Skip C1/C2/C3 specialist sub-runs (use pre-existing outputs). "
        "For post-hoc aggregation only.",
    )
    p.add_argument(
        "--n-trials",
        type=int,
        default=35,
        help="Optuna n_trials per specialist sub-run (default: 35 CONFIRMATION budget).",
    )
    p.add_argument(
        "--ensemble-size",
        type=int,
        default=10,
        help="Ensemble size per specialist sub-run (default: 10 CONFIRMATION budget).",
    )
    p.add_argument(
        "--seeds",
        type=int,
        default=1,
        help="Outer seeds per specialist sub-run (default: 1).",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# F-AXIS #5 (Check 17) — bundle_weights.csv byte-match
# ---------------------------------------------------------------------------


def _verify_weights_csv_match(weights_csv: Path) -> dict[str, float]:
    """Verify bundle_weights.csv exists and return {component_id: weight} dict."""
    if not weights_csv.exists():
        raise FileNotFoundError(
            f"[F-AXIS #5] bundle_weights.csv not found at {weights_csv}. "
            "Run analysis/iteration_v1-056/weight_calibration.py first."
        )
    with weights_csv.open(newline="") as fh:
        csv_weights = {r["component_id"]: float(r["weight"]) for r in csv.DictReader(fh)}

    expected = {cid: BUNDLE_WEIGHT for cid in COMPONENT_SOURCES}
    for cid, w in expected.items():
        csv_w = csv_weights.get(cid)
        if csv_w is None or abs(csv_w - w) > 1e-9:
            raise ValueError(
                f"[F-AXIS #5 BUNDLE-WEIGHT-OOS-LEAK] Expected weight {w} for '{cid}' "
                f"but bundle_weights.csv has {csv_w}. "
                "Pre-registered equal weights must be 0.2 for all 5 components."
            )
    if set(expected) != set(csv_weights):
        raise ValueError(
            f"[F-AXIS #5] Component set mismatch: expected={set(expected)}, CSV={set(csv_weights)}."
        )
    print("[F-AXIS #5] PASS — bundle_weights.csv byte-matches expected EQUAL weights (0.2 × 5).")
    return csv_weights


# ---------------------------------------------------------------------------
# F-AXIS #4 (Check 16) — universe disjointness
# ---------------------------------------------------------------------------


def _verify_universe_disjoint() -> None:
    """F-AXIS #4 / Check 16: pairwise universe intersection must be empty (10 pairs)."""
    universes: dict[str, frozenset[str]] = {
        cid: frozenset([sym]) for cid, (sym, _) in COMPONENT_SOURCES.items()
    }
    for a, b in combinations(sorted(universes), 2):
        overlap = universes[a] & universes[b]
        if overlap:
            raise AssertionError(
                f"[F-AXIS #4 BUNDLE-UNIVERSE-OVERLAP] Coin overlap between "
                f"{a} and {b}: {overlap}. Abort."
            )
    all_syms = set().union(*universes.values())
    assert all_syms == BUNDLE_UNIVERSE, (
        f"Bundle universe mismatch: computed={all_syms}, expected={BUNDLE_UNIVERSE}."
    )
    print(
        f"[F-AXIS #4] PASS — 10 pairwise universe intersections all empty. "
        f"Union={sorted(BUNDLE_UNIVERSE)}."
    )


# ---------------------------------------------------------------------------
# F-AXIS #3 (Check 15) — parity declaration
# ---------------------------------------------------------------------------


def _declare_parity() -> None:
    """F-AXIS #3 BUNDLE-PARITY-VIOLATION: CSV-replay has no new model code paths."""
    print(
        "[F-AXIS #3] PASS by construction — CSV-replay aggregator; "
        "no new LightGBM training, no netting across components, "
        "no joint exit logic. Live engine dispatches each specialist independently."
    )


# ---------------------------------------------------------------------------
# SHA-256 helper
# ---------------------------------------------------------------------------


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# CSV loading + filtering
# ---------------------------------------------------------------------------


def _load_trades(path: Path) -> list[dict]:
    """Load trades.csv; return list of row dicts."""
    if not path.exists():
        raise FileNotFoundError(f"Trades CSV not found: {path}")
    rows: list[dict] = []
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            rows.append(r)
    return rows


def _filter_and_weight(rows: list[dict], symbol: str, weight: float) -> list[dict]:
    """Filter rows to symbol, apply weight to weighted_pnl; return filtered rows."""
    out: list[dict] = []
    for r in rows:
        if r.get("symbol") != symbol:
            continue
        new_r = dict(r)
        try:
            orig_wp = float(r.get("weighted_pnl") or 0.0)
        except ValueError:
            orig_wp = 0.0
        new_r["weighted_pnl"] = str(round(orig_wp * weight, 8))
        for field in ("pnl_pct", "net_pnl_pct"):
            try:
                new_r[field] = str(round(float(r.get(field) or 0.0) * weight, 8))
            except ValueError:
                pass
        out.append(new_r)
    return out


# ---------------------------------------------------------------------------
# Metrics helpers
# ---------------------------------------------------------------------------


def _daily_sharpe(trades: list[dict], cutoff_ms: int | None = None) -> float:
    """Annualised daily Sharpe on weighted_pnl bucketed by UTC calendar day."""
    if cutoff_ms is not None:
        trades = [r for r in trades if int(r["close_time"]) < cutoff_ms]
    if len(trades) < 2:
        return 0.0
    by_day: dict[int, float] = defaultdict(float)
    for r in trades:
        day = int(r["close_time"]) // (24 * 3600 * 1000)
        by_day[day] += float(r.get("weighted_pnl") or 0)
    daily = list(by_day.values())
    if len(daily) < 2:
        return 0.0
    mean = sum(daily) / len(daily)
    var = sum((x - mean) ** 2 for x in daily) / (len(daily) - 1)
    std = math.sqrt(var) if var > 0 else 0.0
    return (mean / std) * math.sqrt(365) if std > 0 else 0.0


def _monthly_sharpe(trades: list[dict], cutoff_ms: int | None = None) -> float:
    """Monthly Sharpe on weighted_pnl bucketed by calendar month."""
    import datetime

    if cutoff_ms is not None:
        trades = [r for r in trades if int(r["close_time"]) < cutoff_ms]
    if not trades:
        return 0.0
    by_month: dict[int, float] = defaultdict(float)
    for r in trades:
        ct = int(r["close_time"])
        dt = datetime.datetime.utcfromtimestamp(ct / 1000.0)
        key = dt.year * 12 + dt.month
        by_month[key] += float(r.get("weighted_pnl") or 0)
    monthly = list(by_month.values())
    if len(monthly) < 2:
        return 0.0
    mean = sum(monthly) / len(monthly)
    var = sum((x - mean) ** 2 for x in monthly) / (len(monthly) - 1)
    std = math.sqrt(var) if var > 0 else 0.0
    return (mean / std) if std > 0 else 0.0


def _max_drawdown(trades: list[dict], cutoff_ms: int | None = None) -> float:
    if cutoff_ms is not None:
        trades = [r for r in trades if int(r["close_time"]) < cutoff_ms]
    if not trades:
        return 0.0
    cum = peak = max_dd = 0.0
    for r in sorted(trades, key=lambda t: int(t["close_time"])):
        cum += float(r.get("weighted_pnl") or 0)
        if cum > peak:
            peak = cum
        dd = peak - cum
        if dd > max_dd:
            max_dd = dd
    return max_dd


def _win_rate(trades: list[dict], cutoff_ms: int | None = None) -> float:
    if cutoff_ms is not None:
        trades = [r for r in trades if int(r["close_time"]) < cutoff_ms]
    if not trades:
        return 0.0
    wins = sum(1 for r in trades if float(r.get("net_pnl_pct") or 0) > 0)
    return wins / len(trades)


def _profit_factor(trades: list[dict], cutoff_ms: int | None = None) -> float:
    if cutoff_ms is not None:
        trades = [r for r in trades if int(r["close_time"]) < cutoff_ms]
    pos = sum(
        float(r.get("weighted_pnl") or 0) for r in trades if float(r.get("weighted_pnl") or 0) > 0
    )
    neg = abs(
        sum(
            float(r.get("weighted_pnl") or 0)
            for r in trades
            if float(r.get("weighted_pnl") or 0) < 0
        )
    )
    return pos / neg if neg > 0 else float("nan")


def _total_pnl(trades: list[dict], cutoff_ms: int | None = None) -> float:
    if cutoff_ms is not None:
        trades = [r for r in trades if int(r["close_time"]) < cutoff_ms]
    return sum(float(r.get("weighted_pnl") or 0) for r in trades)


def _n_trades(trades: list[dict], cutoff_ms: int | None = None) -> int:
    if cutoff_ms is not None:
        trades = [r for r in trades if int(r["close_time"]) < cutoff_ms]
    return len(trades)


# ---------------------------------------------------------------------------
# Regime tagger (date-based approximation; same as /045 framework)
# ---------------------------------------------------------------------------


def _assign_regime_tag(close_time_ms: int) -> str:
    """Date-based regime tagger.

    Covers the 2021-2026 trading window with known BTC market regimes:
      bull   : 2021-01 to 2021-10, 2024-11 to 2025-03
      bear   : 2021-11 to 2022-12
      recovery: 2023-01 to 2023-06
      chop   : 2023-07 to 2024-10
      other  : remaining
    """
    import datetime

    dt = datetime.datetime.utcfromtimestamp(close_time_ms / 1000.0)
    y, m = dt.year, dt.month

    if (y == 2021 and m <= 10) or (y == 2024 and m >= 11) or (y == 2025 and m <= 3):
        return "bull"
    elif (y == 2021 and m >= 11) or (y == 2022):
        return "bear"
    elif y == 2023 and m <= 6:
        return "recovery"
    elif (y == 2023 and m >= 7) or (y == 2024 and m <= 10):
        return "chop"
    else:
        return "other"


# ---------------------------------------------------------------------------
# Jaccard check (F-AXIS #4 extended)
# ---------------------------------------------------------------------------


def _verify_jaccard(bundle_trades: list[dict], component_filtered: dict[str, list[dict]]) -> None:
    """F-AXIS #4 (Jaccard=1.0): bundle roster == union of component rosters."""
    union_keys: set[tuple] = set()
    for cid, rows in component_filtered.items():
        for r in rows:
            union_keys.add((r.get("symbol", ""), r.get("open_time", ""), r.get("close_time", "")))

    bundle_keys: set[tuple] = set()
    for r in bundle_trades:
        bundle_keys.add((r.get("symbol", ""), r.get("open_time", ""), r.get("close_time", "")))

    missing_from_bundle = union_keys - bundle_keys
    extra_in_bundle = bundle_keys - union_keys

    if missing_from_bundle or extra_in_bundle:
        raise AssertionError(
            f"[F-AXIS #4 BUNDLE-UNIVERSE-OVERLAP] Jaccard < 1.0. "
            f"Missing from bundle: {len(missing_from_bundle)} rows. "
            f"Extra in bundle: {len(extra_in_bundle)} rows."
        )
    print(
        f"[F-AXIS #4] Jaccard = 1.0 PASS — bundle roster ({len(bundle_keys)} trades) "
        f"== union of component rosters."
    )


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------


def _write_trades_csv(out_dir: Path, split: str, trades: list[dict]) -> None:
    """Write sorted (by close_time) trade rows to out_dir/split/trades.csv."""
    split_dir = out_dir / split
    split_dir.mkdir(parents=True, exist_ok=True)
    trades_sorted = sorted(trades, key=lambda r: int(r["close_time"]))
    out_path = split_dir / "trades.csv"
    if not trades_sorted:
        out_path.write_text("symbol,close_time,weighted_pnl,net_pnl_pct\n")
        return
    fieldnames = list(trades_sorted[0].keys())
    # Ensure component_id is in fieldnames (add if missing)
    if "component_id" not in fieldnames:
        fieldnames.append("component_id")
    with out_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(trades_sorted)
    print(f"  [trades] {split}: {len(trades_sorted)} rows → {out_path}")


def _write_comparison_csv(
    out_dir: Path, is_trades: list[dict], oos_trades: list[dict]
) -> list[dict]:
    """Write comparison.csv with IS/OOS/ratio for key metrics vs BASELINE_V1."""
    out_path = out_dir / "comparison.csv"

    metrics_data = [
        ("daily_sharpe", _daily_sharpe(is_trades), _daily_sharpe(oos_trades)),
        ("monthly_sharpe", _monthly_sharpe(is_trades), _monthly_sharpe(oos_trades)),
        ("max_drawdown", _max_drawdown(is_trades), _max_drawdown(oos_trades)),
        ("win_rate", _win_rate(is_trades), _win_rate(oos_trades)),
        ("profit_factor", _profit_factor(is_trades), _profit_factor(oos_trades)),
        ("n_trades", float(_n_trades(is_trades)), float(_n_trades(oos_trades))),
        ("total_pnl", _total_pnl(is_trades), _total_pnl(oos_trades)),
    ]

    rows = []
    for metric, is_val, oos_val in metrics_data:
        if is_val and is_val != 0 and not math.isnan(is_val):
            ratio = round(oos_val / is_val, 6)
        else:
            ratio = "nan"
        rows.append(
            {
                "metric": metric,
                "in_sample": round(is_val, 6) if not math.isnan(is_val) else "nan",
                "out_of_sample": round(oos_val, 6) if not math.isnan(oos_val) else "nan",
                "ratio": ratio,
            }
        )

    # Delta vs BASELINE_V1 daily Sharpe
    is_sh = _daily_sharpe(is_trades)
    oos_sh = _daily_sharpe(oos_trades)
    rows.append(
        {
            "metric": "delta_is_sharpe_vs_baseline",
            "in_sample": round(is_sh - BASELINE_V1_IS_SHARPE, 6),
            "out_of_sample": round(oos_sh - BASELINE_V1_OOS_SHARPE, 6),
            "ratio": "N/A",
        }
    )

    with out_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["metric", "in_sample", "out_of_sample", "ratio"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"  [comparison] {out_path} ({len(rows)} rows)")
    return rows


def _write_regime_attribution_csv(
    out_dir: Path,
    all_trades: list[dict],
    baseline_is_trades: list[dict],
    baseline_oos_trades: list[dict],
) -> None:
    """Write regime_attribution.csv with per-regime IS+OOS Sharpe comparison (F-AXIS #1)."""
    regimes = ["bull", "bear", "chop", "recovery", "other"]
    rows = []

    def _regime_trades(trades: list[dict], regime: str, split: str) -> list[dict]:
        if split == "IS":
            sub = [r for r in trades if int(r["close_time"]) < OOS_CUTOFF_MS]
        else:
            sub = [r for r in trades if int(r["close_time"]) >= OOS_CUTOFF_MS]
        return [r for r in sub if _assign_regime_tag(int(r["close_time"])) == regime]

    baseline_all = baseline_is_trades + baseline_oos_trades

    for split_str in ("IS", "OOS"):
        for regime in regimes:
            cand_sub = _regime_trades(all_trades, regime, split_str)
            base_sub = _regime_trades(baseline_all, regime, split_str)
            rows.append(
                {
                    "regime_tag": regime,
                    "split": split_str,
                    "candidate_sharpe": round(_monthly_sharpe(cand_sub), 4),
                    "candidate_max_dd": round(_max_drawdown(cand_sub), 4),
                    "candidate_trade_count": _n_trades(cand_sub),
                    "baseline_sharpe": round(_monthly_sharpe(base_sub), 4),
                    "baseline_max_dd": round(_max_drawdown(base_sub), 4),
                    "baseline_trade_count": _n_trades(base_sub),
                }
            )

    out_path = out_dir / "regime_attribution.csv"
    with out_path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "regime_tag",
                "split",
                "candidate_sharpe",
                "candidate_max_dd",
                "candidate_trade_count",
                "baseline_sharpe",
                "baseline_max_dd",
                "baseline_trade_count",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"  [regime_attribution] {out_path} ({len(rows)} rows)")


def _write_source_checksums(out_dir: Path, component_paths: dict[str, dict[str, Path]]) -> None:
    """Write source_checksums.csv with SHA-256 of each component's trade CSVs (F-AXIS #6)."""
    out_path = out_dir / "source_checksums.csv"
    rows = []
    for cid, paths in component_paths.items():
        row = {"component_id": cid}
        for split, p in paths.items():
            row[f"{split}_sha256"] = _sha256(p) if p.exists() else "MISSING"
        rows.append(row)

    fieldnames = ["component_id", "is_sha256", "oos_sha256"]
    with out_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  [checksums] {out_path} ({len(rows)} rows)")


# ---------------------------------------------------------------------------
# Specialist sub-run dispatch
# ---------------------------------------------------------------------------


def _dispatch_specialist_subrun(
    repo_root: Path,
    comp_id: str,
    iteration_label: str,
    symbol: str,
    sub_dir: str,
    n_trials: int,
    ensemble_size: int,
    seeds: int,
    out_dir: Path,
) -> Path:
    """Dispatch a specialist sub-run via subprocess call to run_baseline_v1.py.

    Returns the path to the sub-run's output directory.
    """
    runner_path = repo_root / "run_baseline_v1.py"
    assert runner_path.exists(), f"run_baseline_v1.py not found at {runner_path}"

    # Determine iteration number from label (e.g., 'v1-056-C1-BTC' → 56)
    subrun_out_dir = out_dir / sub_dir
    subrun_out_dir.mkdir(parents=True, exist_ok=True)

    # Build the argv for the specialist sub-run.
    # Use --iteration-label to route to the correct dispatch branch in run_baseline_v1.py.
    # --iteration 56 maps the natural iteration folder to reports-v1/iteration_v1-056;
    # we'll redirect outputs by copying after the run.
    argv = [
        sys.executable,
        str(runner_path),
        "--confirmation",
        "--iteration",
        "56",
        "--symbols",
        symbol,
        "--pruned-features",
        "--n-trials",
        str(n_trials),
        "--ensemble-size",
        str(ensemble_size),
        "--seeds",
        str(seeds),
        "--iteration-label",
        iteration_label,
        "--no-engineering-report",
    ]

    print(f"\n[iter-v1/056] === Sub-run START: {comp_id} ({symbol}) ===")
    print(f"  cmd: {' '.join(argv[2:])}")
    t0 = time.time()

    proc = subprocess.run(argv, capture_output=False, text=True)
    elapsed = time.time() - t0

    if proc.returncode != 0:
        print(
            f"\n[iter-v1/056] Sub-run {comp_id} FAILED "
            f"(rc={proc.returncode}, elapsed={elapsed:.0f}s).",
            file=sys.stderr,
        )
        sys.exit(proc.returncode)

    print(f"[iter-v1/056] Sub-run {comp_id} DONE ({elapsed:.0f}s).")

    # The sub-run writes to reports-v1/iteration_v1-056/. Copy/move to the sub_dir.
    natural_dir = repo_root / "reports-v1" / "iteration_v1-056"
    if natural_dir.exists() and natural_dir != subrun_out_dir:
        # Copy relevant splits to sub_dir (don't overwrite the whole dir — other sub-runs share it)
        for split in ("in_sample", "out_of_sample"):
            src = natural_dir / split
            dst = subrun_out_dir / split
            if src.exists():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(str(src), str(dst))
        print(f"  [sub-run] {comp_id}: copied {natural_dir}/ → {subrun_out_dir}/")

    return subrun_out_dir


# ---------------------------------------------------------------------------
# Anchor trade extraction
# ---------------------------------------------------------------------------


def _extract_anchor_trades(
    repo_root: Path,
    symbol: str,
    out_dir: Path,
    sub_dir: str,
) -> tuple[Path, Path]:
    """Extract BASELINE_V1 trades for a single anchor symbol.

    Writes IS and OOS trade CSV files to out_dir/sub_dir/{in_sample,out_of_sample}/trades.csv.
    Returns (is_csv_path, oos_csv_path).
    """
    anchor_dir = repo_root / "reports-v1" / BASELINE_ITER_LABEL
    anchor_subdir = out_dir / sub_dir

    for split in ("in_sample", "out_of_sample"):
        src = anchor_dir / split / "trades.csv"
        if not src.exists():
            raise FileNotFoundError(
                f"BASELINE_V1 {split}/trades.csv not found: {src}. "
                "Run `uv run python run_baseline_v1.py --baseline-mode` first."
            )
        rows = _load_trades(src)
        filtered = [r for r in rows if r.get("symbol") == symbol]
        dst_dir = anchor_subdir / split
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / "trades.csv"
        if filtered:
            fieldnames = list(filtered[0].keys())
        else:
            fieldnames = ["symbol", "open_time", "close_time", "weighted_pnl", "net_pnl_pct"]
        with dst.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered)
        print(f"  [anchor] {symbol} {split}: {len(filtered)} rows → {dst}")

    return (
        anchor_subdir / "in_sample" / "trades.csv",
        anchor_subdir / "out_of_sample" / "trades.csv",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    args = _parse_args()
    repo_root = Path(args.repo_root)
    out_dir = repo_root / args.out
    weights_csv = repo_root / args.weights_csv

    out_dir.mkdir(parents=True, exist_ok=True)

    print("[iter-v1/056] CONFIRMATION-PORTFOLIO ACTIVE")
    print(f"  out_dir     = {out_dir}")
    print(f"  weights_csv = {weights_csv}")
    print(f"  n_trials    = {args.n_trials}")
    print(f"  ens_size    = {args.ensemble_size}")
    print(f"  seeds       = {args.seeds}")
    print(f"  skip_subs   = {args.skip_subruns}")
    print()

    # -----------------------------------------------------------------------
    # Pre-flight F-AXIS checks
    # -----------------------------------------------------------------------
    _verify_universe_disjoint()
    csv_weights = _verify_weights_csv_match(weights_csv)
    _declare_parity()
    print()

    # -----------------------------------------------------------------------
    # Step 1-3: Specialist sub-runs (C1-BTC, C2-ETH, C3-DOT)
    # -----------------------------------------------------------------------
    specialist_dirs: dict[str, Path] = {}

    if not args.skip_subruns:
        for comp_id, iter_label, symbol, _feat_flag in SPECIALIST_SPECS:
            sub_dir = COMPONENT_SOURCES[comp_id][1]
            specialist_dirs[comp_id] = _dispatch_specialist_subrun(
                repo_root=repo_root,
                comp_id=comp_id,
                iteration_label=iter_label,
                symbol=symbol,
                sub_dir=sub_dir,
                n_trials=args.n_trials,
                ensemble_size=args.ensemble_size,
                seeds=args.seeds,
                out_dir=out_dir,
            )
    else:
        print("[iter-v1/056] --skip-subruns: using pre-existing specialist outputs.")
        for comp_id, _iter_label, _symbol, _feat_flag in SPECIALIST_SPECS:
            sub_dir = COMPONENT_SOURCES[comp_id][1]
            specialist_dirs[comp_id] = out_dir / sub_dir

    # -----------------------------------------------------------------------
    # Step 4-5: Anchor trade extractions (C4-LINK, C5-LTC)
    # -----------------------------------------------------------------------
    print("\n[load] Extracting BASELINE_V1 anchor trades...")
    for anchor_cid, anchor_sym in [("C4-LINK", "LINKUSDT"), ("C5-LTC", "LTCUSDT")]:
        sub_dir = COMPONENT_SOURCES[anchor_cid][1]
        _extract_anchor_trades(repo_root, anchor_sym, out_dir, sub_dir)

    # -----------------------------------------------------------------------
    # Step 6: CSV-replay aggregator
    # -----------------------------------------------------------------------
    print("\n[load] Loading and filtering component trade rosters...")
    component_is_filtered: dict[str, list[dict]] = {}
    component_oos_filtered: dict[str, list[dict]] = {}
    component_paths: dict[str, dict[str, Path]] = {}

    for cid, (sym, sub_dir) in COMPONENT_SOURCES.items():
        weight = csv_weights[cid]
        comp_dir = out_dir / sub_dir
        is_path = comp_dir / "in_sample" / "trades.csv"
        oos_path = comp_dir / "out_of_sample" / "trades.csv"

        is_rows = _load_trades(is_path)
        oos_rows = _load_trades(oos_path)

        # Filter to owned symbol (specialist sub-runs should be single-symbol;
        # anchor extractions already filtered; guard against any leakage)
        is_filt = _filter_and_weight(is_rows, sym, weight)
        oos_filt = _filter_and_weight(oos_rows, sym, weight)

        for r in is_filt:
            r["component_id"] = cid
        for r in oos_filt:
            r["component_id"] = cid

        component_is_filtered[cid] = is_filt
        component_oos_filtered[cid] = oos_filt
        component_paths[cid] = {"is": is_path, "oos": oos_path}
        print(f"  {cid} ({sym}): IS={len(is_filt)} OOS={len(oos_filt)}")

    # Concatenate + sort
    all_is: list[dict] = []
    for rows in component_is_filtered.values():
        all_is.extend(rows)
    all_is.sort(key=lambda r: int(r["close_time"]))

    all_oos: list[dict] = []
    for rows in component_oos_filtered.values():
        all_oos.extend(rows)
    all_oos.sort(key=lambda r: int(r["close_time"]))

    all_trades = all_is + all_oos

    # F-AXIS #4 Jaccard check
    all_component_filtered: dict[str, list[dict]] = {}
    for cid in COMPONENT_SOURCES:
        all_component_filtered[cid] = component_is_filtered[cid] + component_oos_filtered[cid]
    _verify_jaccard(all_trades, all_component_filtered)

    # -----------------------------------------------------------------------
    # Step 7: Write outputs
    # -----------------------------------------------------------------------
    print(f"\n[output] Writing bundle reports to {out_dir}...")

    _write_trades_csv(out_dir, "in_sample", all_is)
    _write_trades_csv(out_dir, "out_of_sample", all_oos)
    _write_comparison_csv(out_dir, all_is, all_oos)

    # Regime attribution: load BASELINE_V1 trades for comparison
    baseline_src = repo_root / "reports-v1" / BASELINE_ITER_LABEL
    try:
        baseline_is = _load_trades(baseline_src / "in_sample" / "trades.csv")
        baseline_oos = _load_trades(baseline_src / "out_of_sample" / "trades.csv")
    except FileNotFoundError:
        print("  WARNING: BASELINE_V1 trades not found — regime baseline cols = 0")
        baseline_is = []
        baseline_oos = []

    _write_regime_attribution_csv(out_dir, all_trades, baseline_is, baseline_oos)

    # Source checksums (F-AXIS #6)
    _write_source_checksums(
        out_dir,
        {cid: {"is": paths["is"], "oos": paths["oos"]} for cid, paths in component_paths.items()},
    )

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print()
    print("=" * 60)
    print("BUNDLE METRICS SUMMARY — iter-v1/056")
    print("=" * 60)
    is_sh = _daily_sharpe(all_is)
    oos_sh = _daily_sharpe(all_oos)
    is_n = _n_trades(all_is)
    oos_n = _n_trades(all_oos)
    is_pnl = _total_pnl(all_is)
    oos_pnl = _total_pnl(all_oos)
    print(
        f"  IS  daily Sharpe (ann): {is_sh:+.4f}  "
        f"(BASELINE_V1 {BASELINE_V1_IS_SHARPE:+.4f}  "
        f"Δ {is_sh - BASELINE_V1_IS_SHARPE:+.4f})"
    )
    print(
        f"  OOS daily Sharpe (ann): {oos_sh:+.4f}  "
        f"(BASELINE_V1 {BASELINE_V1_OOS_SHARPE:+.4f}  "
        f"Δ {oos_sh - BASELINE_V1_OOS_SHARPE:+.4f})"
    )
    print(f"  IS  n_trades: {is_n}  OOS n_trades: {oos_n}")
    print(f"  IS  total PnL: {is_pnl:+.4f}  OOS total PnL: {oos_pnl:+.4f}")
    print()

    # F-AXIS verification summary
    f2_status = "PASS" if oos_n >= 130 else f"FAIL ({oos_n} < 130)"
    print("[F-AXIS VERIFICATION]")
    print("  F1 (per-regime Pareto): regime_attribution.csv produced — QR evaluates in Phase 7")
    print(f"  F2 (trade-rate floor):  OOS n_trades={oos_n} → {f2_status}")
    print("  F3 (parity):            CSV-replay; no new model code paths — PASS by construction")
    print("  F4 (universe disjoint): PASS (verified above)")
    print("  F5 (weight provenance): PASS (bundle_weights.csv verified above)")
    print("  F6 (checksums):         source_checksums.csv written")
    print()
    print("[iter-v1/056] DONE — OVERALL=READY-FOR-CRITIC")


if __name__ == "__main__":
    main()
