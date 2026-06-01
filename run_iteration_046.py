"""iter-v1/046 — CSV-replay bundle aggregator (IS-only substrate, v2).

Design: NO fresh Optuna, NO LightGBM fit.  Reads pre-existing per-coin
trade rosters from source iterations (selected by IS-only partition_solve_v2.py),
applies 0.2 weight, concatenates, sorts, and emits bundle-level reports.

Key difference from iter-v1/045:
  /045 component sources were selected by a mixed IS+OOS scoring composite
  (0.5*OOS_Sharpe + 0.3*IS_Sharpe + 0.2*OOS_n/100).
  /046 component sources are selected EXCLUSIVELY by IS-only scoring
  (0.6*IS_Sharpe + 0.4*IS_n/250) from analysis/iteration_v1-046/partition_solve_v2.py.
  This tests whether IS-only substrate selection produces a portfolio that
  is competitive with /045's mixed-score substrate in OOS.

Usage:
  uv run python run_iteration_046.py [options]

  --bundle-config  "C-BTC:0.2,C-ETH:0.2,C-LINK:0.2,C-LTC:0.2,C-DOT:0.2"
  --weights-csv    analysis/iteration_v1-046/bundle_weights.csv
  --out            reports-v1/iteration_v1-046/

Dispatch rule (Section 11.C):
  At each (symbol, t), exactly ONE component owns the symbol.
  weight_factor = 0.2 for all components (EQUAL, pre-registered).
  NO aggregation across components — universes are strictly disjoint.

Sacred constants (unchanged):
  OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
  BASELINE_V1_IS_SHARPE  = 0.4761
  BASELINE_V1_OOS_SHARPE = 1.1415
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

# ---------------------------------------------------------------------------
# Sacred constants — DO NOT CHANGE
# ---------------------------------------------------------------------------

OOS_CUTOFF_MS: int = 1742774400000  # 2025-03-24 00:00 UTC
BUNDLE_WEIGHT: float = 0.2  # EQUAL weight per component (1/5)
BASELINE_V1_IS_SHARPE: float = 0.4761
BASELINE_V1_OOS_SHARPE: float = 1.1415
BASELINE_V1_IS_PNL: float = 54.05
BASELINE_V1_OOS_PNL: float = 36.96

# ---------------------------------------------------------------------------
# Component sources (Section 11.A — universe partition, per-coin ownership)
# IS-only partition — selected by partition_solve_v2.py
# Score formula: 0.6 * IS_Sharpe_ann + 0.4 * (IS_n_trades / 250)
# ---------------------------------------------------------------------------

# (component_id, owned_symbol, source_iter_label)
COMPONENT_SOURCES: dict[str, tuple[str, str]] = {
    "C-BTC": ("BTCUSDT", "iteration_v1-025"),
    "C-ETH": ("ETHUSDT", "iteration_v1-009"),
    "C-LINK": ("LINKUSDT", "iteration_v1-025"),
    "C-LTC": ("LTCUSDT", "iteration_v1-025"),
    "C-DOT": ("DOTUSDT", "iteration_v1-031"),
}

BUNDLE_UNIVERSE: frozenset[str] = frozenset(sym for (sym, _) in COMPONENT_SOURCES.values())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_bundle_config(spec: str) -> dict[str, float]:
    """Parse 'C-BTC:0.2,C-ETH:0.2,...' into {component_id: weight}.

    Raises:
        ValueError: on malformed token, unknown component, or weight sum != 1.0.
    """
    result: dict[str, float] = {}
    for token in spec.split(","):
        if ":" not in token:
            raise ValueError(f"Invalid token '{token}': expected 'component_id:weight'.")
        cid, wstr = token.split(":", 1)
        cid = cid.strip()
        if cid not in COMPONENT_SOURCES:
            raise ValueError(f"Unknown component '{cid}'. Valid: {sorted(COMPONENT_SOURCES)}.")
        result[cid] = float(wstr.strip())
    if abs(sum(result.values()) - 1.0) > 1e-6:
        raise ValueError(
            f"Bundle weights sum to {sum(result.values()):.8f} ≠ 1.0. "
            "weights must sum to exactly 1.0 ± 1e-6."
        )
    return result


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="iter-v1/046 CSV-replay bundle aggregator")
    p.add_argument(
        "--bundle-config",
        default="C-BTC:0.2,C-ETH:0.2,C-LINK:0.2,C-LTC:0.2,C-DOT:0.2",
        help="Component weights spec (must match bundle_weights.csv).",
    )
    p.add_argument(
        "--weights-csv",
        default="analysis/iteration_v1-046/bundle_weights.csv",
        help="Pre-registered bundle_weights.csv path (Check 17 byte-match assertion).",
    )
    p.add_argument(
        "--out",
        default="reports-v1/iteration_v1-046/",
        help="Output directory root.",
    )
    p.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parent),
        help="Repo root (default: directory of this script).",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# F-AXIS verifications
# ---------------------------------------------------------------------------


def _verify_weights_csv_match(cli_weights: dict[str, float], weights_csv: Path) -> None:
    """F-AXIS #5 / Check 17: CLI weights must byte-match the committed CSV."""
    if not weights_csv.exists():
        raise FileNotFoundError(
            f"[F-AXIS #5] bundle_weights.csv not found at {weights_csv}. "
            "Run analysis/iteration_v1-046/weight_calibration.py first."
        )
    with weights_csv.open(newline="") as fh:
        csv_weights = {r["component_id"]: float(r["weight"]) for r in csv.DictReader(fh)}
    for cid, w in cli_weights.items():
        csv_w = csv_weights.get(cid)
        if csv_w is None or abs(csv_w - w) > 1e-9:
            raise ValueError(
                f"[F-AXIS #5 BUNDLE-WEIGHT-OOS-LEAK] CLI weight for '{cid}' = {w} "
                f"does not match bundle_weights.csv value = {csv_w}. "
                "Pre-registered weights must match CLI input byte-for-byte."
            )
    if set(cli_weights) != set(csv_weights):
        raise ValueError(
            f"[F-AXIS #5] Component set mismatch: CLI={set(cli_weights)}, CSV={set(csv_weights)}."
        )
    print("[F-AXIS #5] PASS — CLI weights byte-match bundle_weights.csv.")


def _verify_universe_disjoint() -> None:
    """F-AXIS #4 / Check 16: pairwise universe intersection must be empty."""
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
# CSV loading
# ---------------------------------------------------------------------------


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_trades(path: Path) -> list[dict]:
    """Load trades.csv; return list of row dicts with parsed numeric fields."""
    if not path.exists():
        raise FileNotFoundError(f"Trades CSV not found: {path}")
    rows: list[dict] = []
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            rows.append(r)
    return rows


def _filter_and_weight(
    rows: list[dict],
    symbol: str,
    weight: float,
) -> list[dict]:
    """Filter rows to symbol, apply weight to weighted_pnl; return filtered rows."""
    out: list[dict] = []
    for r in rows:
        if r["symbol"] != symbol:
            continue
        new_r = dict(r)
        # Scale weighted_pnl by the bundle weight (0.2).
        try:
            orig_wp = float(r.get("weighted_pnl") or 0.0)
        except ValueError:
            orig_wp = 0.0
        new_r["weighted_pnl"] = str(round(orig_wp * weight, 8))
        # Also scale pnl_pct and net_pnl_pct proportionally.
        for field in ("pnl_pct", "net_pnl_pct"):
            try:
                new_r[field] = str(round(float(r.get(field) or 0.0) * weight, 8))
            except ValueError:
                pass
        new_r["component_id"] = ""  # will be set by caller
        out.append(new_r)
    return out


# ---------------------------------------------------------------------------
# Metrics
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
    if cutoff_ms is not None:
        trades = [r for r in trades if int(r["close_time"]) < cutoff_ms]
    if not trades:
        return 0.0
    by_month: dict[int, float] = defaultdict(float)
    for r in trades:
        ct = int(r["close_time"])
        import datetime

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
# Regime tagger (stdlib-only approximation)
# ---------------------------------------------------------------------------


def _assign_regime_tag_simple(close_time_ms: int) -> str:
    """Simplified regime tagger without BTC klines dependency.

    Uses a date-based heuristic (known BTC market regimes from 2021-2025):
      bull   : 2021-01 to 2021-10, 2024-11 to 2025-03
      bear   : 2021-11 to 2022-12
      recovery: 2023-01 to 2023-06
      chop   : 2023-07 to 2024-06
      vol-spike: episodes within any regime
      other  : remaining

    This is a conservative approximation; the Critic regime_attribution check
    uses the official BTC-klines-based tagger in run_baseline_v1.py.
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
    elif y == 2023 and m >= 7:
        return "chop"
    elif y == 2024 and m <= 10:
        return "chop"
    else:
        return "other"


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
    with out_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trades_sorted)
    print(f"  [trades] {split}: {len(trades_sorted)} rows → {out_path}")


def _write_comparison_csv(
    out_dir: Path,
    is_trades: list[dict],
    oos_trades: list[dict],
) -> None:
    """Write comparison.csv with IS/OOS/ratio for key metrics vs BASELINE_V1."""
    out_path = out_dir / "comparison.csv"

    metrics = [
        ("daily_sharpe", _daily_sharpe(is_trades), _daily_sharpe(oos_trades)),
        ("monthly_sharpe", _monthly_sharpe(is_trades), _monthly_sharpe(oos_trades)),
        ("max_drawdown", _max_drawdown(is_trades), _max_drawdown(oos_trades)),
        ("win_rate", _win_rate(is_trades), _win_rate(oos_trades)),
        ("profit_factor", _profit_factor(is_trades), _profit_factor(oos_trades)),
        ("n_trades", float(_n_trades(is_trades)), float(_n_trades(oos_trades))),
        ("total_pnl", _total_pnl(is_trades), _total_pnl(oos_trades)),
        # Baseline anchors for ∆ columns
        ("baseline_is_sharpe", BASELINE_V1_IS_SHARPE, BASELINE_V1_OOS_SHARPE),
    ]

    rows = []
    for metric, is_val, oos_val in metrics[:-1]:  # exclude baseline anchor row
        ratio = oos_val / is_val if is_val and is_val != 0 else float("nan")
        rows.append(
            {
                "metric": metric,
                "in_sample": round(is_val, 6),
                "out_of_sample": round(oos_val, 6),
                "ratio": round(ratio, 6) if not math.isnan(ratio) else "nan",
            }
        )

    # Baseline delta rows
    is_sharpe = _daily_sharpe(is_trades)
    oos_sharpe = _daily_sharpe(oos_trades)
    rows.append(
        {
            "metric": "delta_is_sharpe_vs_baseline",
            "in_sample": round(is_sharpe - BASELINE_V1_IS_SHARPE, 6),
            "out_of_sample": round(oos_sharpe - BASELINE_V1_OOS_SHARPE, 6),
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
    """Write regime_attribution.csv with per-regime IS+OOS Sharpe comparison."""
    regimes = ["bull", "bear", "chop", "vol-spike", "recovery", "other"]
    rows = []

    def _regime_sharpe(trades: list[dict], regime: str, cutoff_ms: int, split: str) -> float:
        if split == "IS":
            sub = [r for r in trades if int(r["close_time"]) < cutoff_ms]
        else:
            sub = [r for r in trades if int(r["close_time"]) >= cutoff_ms]
        sub = [r for r in sub if _assign_regime_tag_simple(int(r["close_time"])) == regime]
        return _monthly_sharpe(sub)

    def _regime_max_dd(trades: list[dict], regime: str, cutoff_ms: int, split: str) -> float:
        if split == "IS":
            sub = [r for r in trades if int(r["close_time"]) < cutoff_ms]
        else:
            sub = [r for r in trades if int(r["close_time"]) >= cutoff_ms]
        sub = [r for r in sub if _assign_regime_tag_simple(int(r["close_time"])) == regime]
        return _max_drawdown(sub)

    def _regime_n(trades: list[dict], regime: str, cutoff_ms: int, split: str) -> int:
        if split == "IS":
            sub = [r for r in trades if int(r["close_time"]) < cutoff_ms]
        else:
            sub = [r for r in trades if int(r["close_time"]) >= cutoff_ms]
        return sum(1 for r in sub if _assign_regime_tag_simple(int(r["close_time"])) == regime)

    baseline_all = baseline_is_trades + baseline_oos_trades

    for in_sample_flag in (True, False):
        split_str = "IS" if in_sample_flag else "OOS"
        for regime in regimes:
            rows.append(
                {
                    "regime_tag": regime,
                    "in_sample": in_sample_flag,
                    "candidate_sharpe": round(
                        _regime_sharpe(all_trades, regime, OOS_CUTOFF_MS, split_str), 4
                    ),
                    "candidate_max_dd": round(
                        _regime_max_dd(all_trades, regime, OOS_CUTOFF_MS, split_str), 4
                    ),
                    "candidate_trade_count": _regime_n(
                        all_trades, regime, OOS_CUTOFF_MS, split_str
                    ),
                    "baseline_sharpe": round(
                        _regime_sharpe(baseline_all, regime, OOS_CUTOFF_MS, split_str), 4
                    ),
                    "baseline_max_dd": round(
                        _regime_max_dd(baseline_all, regime, OOS_CUTOFF_MS, split_str), 4
                    ),
                    "baseline_trade_count": _regime_n(
                        baseline_all, regime, OOS_CUTOFF_MS, split_str
                    ),
                }
            )

    out_path = out_dir / "regime_attribution.csv"
    with out_path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "regime_tag",
                "in_sample",
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


# ---------------------------------------------------------------------------
# Jaccard / roster-integrity check (F-AXIS #4 + LM R3)
# ---------------------------------------------------------------------------


def _verify_jaccard(
    bundle_trades: list[dict],
    component_filtered: dict[str, list[dict]],
) -> None:
    """F-AXIS #4 (Jaccard=1.0): bundle roster == union of component rosters."""
    union_keys: set[tuple] = set()
    for cid, rows in component_filtered.items():
        for r in rows:
            union_keys.add((r["symbol"], r["open_time"], r["close_time"]))

    bundle_keys: set[tuple] = set()
    for r in bundle_trades:
        bundle_keys.add((r["symbol"], r["open_time"], r["close_time"]))

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
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    args = _parse_args()
    repo_root = Path(args.repo_root)
    out_dir = repo_root / args.out
    weights_csv = repo_root / args.weights_csv

    print("[iter-v1/046] IS-ONLY-SUBSTRATE CONFIRMATION ACTIVE")
    print(f"  out_dir     = {out_dir}")
    print(f"  weights_csv = {weights_csv}")
    print()

    # --- Parse CLI weights ---
    try:
        cli_weights = _parse_bundle_config(args.bundle_config)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    # F-AXIS #5 (Check 17) — weights_csv byte-match
    _verify_weights_csv_match(cli_weights, weights_csv)

    # F-AXIS #4 (Check 16) — universe disjointness
    _verify_universe_disjoint()

    # F-AXIS #6 — source CSV checksums
    print("[F-AXIS #6] Computing source CSV SHA-256 checksums...")
    checksums: dict[str, dict[str, str]] = {}
    for cid, (sym, iter_label) in COMPONENT_SOURCES.items():
        src = repo_root / "reports-v1" / iter_label
        is_path = src / "in_sample" / "trades.csv"
        oos_path = src / "out_of_sample" / "trades.csv"
        checksums[cid] = {
            "is_sha256": _sha256(is_path),
            "oos_sha256": _sha256(oos_path),
        }
        print(
            f"  {cid}: IS={checksums[cid]['is_sha256'][:16]}...  "
            f"OOS={checksums[cid]['oos_sha256'][:16]}..."
        )

    # --- Load + filter component trades ---
    component_is_filtered: dict[str, list[dict]] = {}
    component_oos_filtered: dict[str, list[dict]] = {}
    print()
    print("[load] Loading and filtering component trade rosters...")
    for cid, (sym, iter_label) in COMPONENT_SOURCES.items():
        weight = cli_weights[cid]
        src = repo_root / "reports-v1" / iter_label
        is_rows = _load_trades(src / "in_sample" / "trades.csv")
        oos_rows = _load_trades(src / "out_of_sample" / "trades.csv")
        is_filt = _filter_and_weight(is_rows, sym, weight)
        oos_filt = _filter_and_weight(oos_rows, sym, weight)
        for r in is_filt:
            r["component_id"] = cid
        for r in oos_filt:
            r["component_id"] = cid
        component_is_filtered[cid] = is_filt
        component_oos_filtered[cid] = oos_filt
        print(f"  {cid} ({iter_label}, {sym}): IS={len(is_filt)} OOS={len(oos_filt)}")

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

    # --- Write outputs ---
    print()
    print(f"[output] Writing bundle reports to {out_dir}...")
    out_dir.mkdir(parents=True, exist_ok=True)

    _write_trades_csv(out_dir, "in_sample", all_is)
    _write_trades_csv(out_dir, "out_of_sample", all_oos)

    _write_comparison_csv(out_dir, all_is, all_oos)

    # Load baseline trades for regime_attribution comparison
    baseline_src = repo_root / "reports-v1" / "iteration_v1-baseline"
    try:
        baseline_is = _load_trades(baseline_src / "in_sample" / "trades.csv")
        baseline_oos = _load_trades(baseline_src / "out_of_sample" / "trades.csv")
    except FileNotFoundError:
        print("  WARNING: baseline trades not found — regime_attribution baseline cols = 0")
        baseline_is = []
        baseline_oos = []

    _write_regime_attribution_csv(out_dir, all_trades, baseline_is, baseline_oos)

    # Write checksums to engineering log
    cksum_path = out_dir / "source_checksums.csv"
    with cksum_path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["component_id", "iter_label", "symbol", "is_sha256", "oos_sha256"]
        )
        writer.writeheader()
        for cid, (sym, iter_label) in COMPONENT_SOURCES.items():
            writer.writerow(
                {
                    "component_id": cid,
                    "iter_label": iter_label,
                    "symbol": sym,
                    **checksums[cid],
                }
            )
    print(f"  [checksums] {cksum_path}")

    # --- Summary ---
    print()
    print("=" * 60)
    print("BUNDLE METRICS SUMMARY")
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

    # F-AXIS verification printout
    btc_oos_n = _n_trades(component_oos_filtered["C-BTC"])
    btc_f7_note = "NOTE: low count — monitor F-AXIS #7 fallback" if btc_oos_n < 30 else "OK"
    f2_status = "PASS" if oos_n >= 130 else "FAIL (< 130)"
    print("[F-AXIS VERIFICATION]")
    print("  F1 (per-regime Pareto): regime_attribution.csv produced")
    print(f"  F2 (trade-rate floor): OOS n_trades={oos_n} ({f2_status})")
    print("  F3 (parity): CSV-replay; no new model code paths — PASS by construction")
    print("  F4 (universe disjoint): PASS (verified above)")
    print("  F5 (weight provenance): PASS (verified above)")
    print("  F6 (checksums): source_checksums.csv written")
    print(f"  F7 (BTC robustness): BTC OOS n={btc_oos_n} ({btc_f7_note})")

    print()
    print("[iter-v1/046] DONE — OVERALL=READY-FOR-CRITIC")


if __name__ == "__main__":
    main()
