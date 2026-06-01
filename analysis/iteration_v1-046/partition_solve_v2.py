"""IS-only partition solver for iter-v1/046.

Methodology:
-----------
Scans the 220-candidate space (44 source iters × 5 coins) from prior iter
in_sample/trades.csv files.  Applies the IS-only scoring formula:

  score(component, coin) = 0.6 * IS_Sharpe_annualized
                         + 0.4 * (IS_n_trades / 250)

where IS_Sharpe_annualized is the annualised daily Sharpe computed ONLY on
IS trades (close_time < OOS_CUTOFF_MS = 2025-03-24).

HARD GATE: IS_n_trades >= 20 per coin.  Candidates with < 20 IS trades are
excluded before scoring.

SECURITY: This script reads ONLY in_sample/trades.csv paths.  No OOS data is
read.  The IS-side filter applies close_time strictly less than OOS_CUTOFF_MS
(never equal-or-greater).  Full audit: test_no_oos_leak_partition_solve.

Outputs:
--------
  analysis/iteration_v1-046/is_only_substrate.csv
  Columns: component_id, source_iter, source_trades_path, universe,
           is_sharpe, is_n_trades, score, rank

Prints:
  - Top-3 candidates per coin.
  - Selected partition (highest-score per coin).
  - Comparison vs /045 ALT_1 substrate.

Sacred constants (unchanged):
  OOS_CUTOFF_DATE = 2025-03-24  (MS = 1742774400000)
  training_months = 24
"""

from __future__ import annotations

import csv
import math
import os
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Sacred constants — DO NOT CHANGE
# ---------------------------------------------------------------------------

OOS_CUTOFF_MS: int = 1742774400000  # 2025-03-24 00:00 UTC
IS_WINDOW_START: str = "2021-03-24"
IS_WINDOW_END: str = "2025-03-24"
MIN_IS_TRADES: int = 20  # HARD GATE: fewer trades → excluded

# ---------------------------------------------------------------------------
# Universe — 5 coins, each owned by exactly ONE component
# ---------------------------------------------------------------------------

COINS = ["BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"]
COIN_TO_CID = {
    "BTCUSDT": "C-BTC",
    "ETHUSDT": "C-ETH",
    "LINKUSDT": "C-LINK",
    "LTCUSDT": "C-LTC",
    "DOTUSDT": "C-DOT",
}

# ---------------------------------------------------------------------------
# /045 ALT_1 reference substrate (for COINCIDES / DIVERGES comparison)
# ---------------------------------------------------------------------------

ALT_1_SUBSTRATE: dict[str, str] = {
    "C-BTC": "iteration_v1-012",
    "C-ETH": "iteration_v1-042",
    "C-LINK": "iteration_v1-011",
    "C-LTC": "iteration_v1-040",
    "C-DOT": "iteration_v1-031",
}

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_V1 = REPO_ROOT / "reports-v1"
OUT_PATH = Path(__file__).resolve().parent / "is_only_substrate.csv"

# ---------------------------------------------------------------------------
# Excluded entries (not candidates for /046 partition)
# ---------------------------------------------------------------------------

# iter-v1/045 = the current assembly iteration being built (not a prior iter)
# iter-v1/028-frozen-hp = a frozen-HP variant (implementation artifact, not
#   an independent EXPLORATION; same underlying model as iter-v1/028)
# iter-v1/baseline = named "baseline" — synthetic reference, not a real iter

EXCLUDED_ITERS: set[str] = {
    "iteration_v1-045",
    "iteration_v1-028-frozen-hp",
    "iteration_v1-baseline",
}


# ---------------------------------------------------------------------------
# IS Sharpe (annualised daily)
# ---------------------------------------------------------------------------


def _daily_sharpe_annualised(trades: list[dict]) -> float:
    """Annualised daily Sharpe on weighted_pnl bucketed by UTC calendar day.

    IS-only: caller must pre-filter trades to close_time < OOS_CUTOFF_MS.
    """
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


# ---------------------------------------------------------------------------
# Scoring formula
# ---------------------------------------------------------------------------


def _score(is_sharpe: float, is_n_trades: int) -> float:
    """IS-only composite score.

    score = 0.6 * IS_Sharpe_annualized + 0.4 * (IS_n_trades / 250)

    The trade-count term normalises to a benchmark of 250 trades (~1/month
    per coin over the 24-month IS window), penalising sparse models without
    over-weighting high-frequency noise.
    """
    return 0.6 * is_sharpe + 0.4 * (is_n_trades / 250.0)


# ---------------------------------------------------------------------------
# Candidate enumeration
# ---------------------------------------------------------------------------


def _enumerate_candidates() -> list[dict]:
    """Enumerate all (iter, coin) candidates, applying the HARD GATE.

    Returns:
        List of dicts with keys: coin, component_id, iter, is_sharpe,
        is_n_trades, score, source_trades_path.
    """
    candidates: list[dict] = []

    for entry in sorted(os.listdir(REPORTS_V1)):
        if not entry.startswith("iteration_v1-"):
            continue
        if entry in EXCLUDED_ITERS:
            continue

        is_path = REPORTS_V1 / entry / "in_sample" / "trades.csv"
        if not is_path.exists():
            continue

        rows: list[dict] = []
        with is_path.open(newline="") as fh:
            for r in csv.DictReader(fh):
                rows.append(r)

        for coin in COINS:
            # IS-only filter: close_time strictly before the OOS cutoff
            coin_rows = [
                r for r in rows if r.get("symbol") == coin and int(r["close_time"]) < OOS_CUTOFF_MS
            ]
            n = len(coin_rows)

            # HARD GATE
            if n < MIN_IS_TRADES:
                continue

            sharpe = _daily_sharpe_annualised(coin_rows)
            sc = _score(sharpe, n)

            candidates.append(
                {
                    "coin": coin,
                    "component_id": COIN_TO_CID[coin],
                    "iter": entry,
                    "is_sharpe": sharpe,
                    "is_n_trades": n,
                    "score": sc,
                    "source_trades_path": str(is_path),
                }
            )

    return candidates


# ---------------------------------------------------------------------------
# Partition selection
# ---------------------------------------------------------------------------


def _select_partition(candidates: list[dict]) -> dict[str, dict]:
    """Select the highest-scoring candidate per coin (greedy, independent).

    Returns:
        {coin: candidate_dict} for the 5 coins.
    """
    selected: dict[str, dict] = {}
    for coin in COINS:
        coin_cands = [c for c in candidates if c["coin"] == coin]
        if not coin_cands:
            raise RuntimeError(f"No valid IS candidates for {coin} — cannot solve partition.")
        # Sort by score descending; tie-break by is_n_trades descending (more data = tie-winner)
        coin_cands.sort(key=lambda x: (x["score"], x["is_n_trades"]), reverse=True)
        selected[coin] = coin_cands[0]
    return selected


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def _write_substrate_csv(selected: dict[str, dict]) -> None:
    """Write is_only_substrate.csv with rank column per COIN ordering."""
    fieldnames = [
        "component_id",
        "source_iter",
        "source_trades_path",
        "universe",
        "is_sharpe",
        "is_n_trades",
        "score",
        "rank",
    ]
    rows = []
    for rank, coin in enumerate(COINS, start=1):
        sel = selected[coin]
        rows.append(
            {
                "component_id": sel["component_id"],
                "source_iter": sel["iter"],
                "source_trades_path": sel["source_trades_path"],
                "universe": coin,
                "is_sharpe": round(sel["is_sharpe"], 6),
                "is_n_trades": sel["is_n_trades"],
                "score": round(sel["score"], 6),
                "rank": rank,
            }
        )

    with OUT_PATH.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n[partition_solve_v2] Wrote {OUT_PATH} ({len(rows)} rows)")


def _print_top3_per_coin(candidates: list[dict]) -> None:
    """Print top-3 candidates per coin for audit."""
    print("\n" + "=" * 72)
    print("TOP-3 CANDIDATES PER COIN (IS-only scoring)")
    print("=" * 72)
    for coin in COINS:
        cid = COIN_TO_CID[coin]
        coin_cands = [c for c in candidates if c["coin"] == coin]
        coin_cands.sort(key=lambda x: (x["score"], x["is_n_trades"]), reverse=True)
        print(f"\n  {cid} ({coin}):")
        print(f"    {'Rank':<5} {'Source Iter':<30} {'IS_Sharpe':>10} {'IS_n':>7} {'Score':>8}")
        print("    " + "-" * 65)
        for i, cand in enumerate(coin_cands[:3], start=1):
            print(
                f"    {i:<5} {cand['iter']:<30} {cand['is_sharpe']:>+10.4f} "
                f"{cand['is_n_trades']:>7} {cand['score']:>8.4f}"
            )
        selected_iter = coin_cands[0]["iter"] if coin_cands else "N/A"
        print(f"    --> SELECTED: {selected_iter}")


def _compare_vs_alt1(selected: dict[str, dict]) -> bool:
    """Compare IS-only selection vs /045 ALT_1. Print per-coin diff. Return True if coincides."""
    print("\n" + "=" * 72)
    print("COMPARISON vs /045 ALT_1 SUBSTRATE")
    print("=" * 72)
    print(f"  {'Component':<10} {'IS-only Selection':<30} {'ALT_1 Selection':<30} {'Status'}")
    print("  " + "-" * 80)

    coincides = True
    for coin in COINS:
        cid = COIN_TO_CID[coin]
        sel_iter = selected[coin]["iter"]
        alt1_iter = ALT_1_SUBSTRATE[cid]
        if sel_iter == alt1_iter:
            status = "MATCH"
        else:
            status = "DIVERGES"
            coincides = False
        print(f"  {cid:<10} {sel_iter:<30} {alt1_iter:<30} {status}")

    print()
    if coincides:
        print("  OVERALL: COINCIDES — IS-only scoring reproduces /045 ALT_1 substrate exactly.")
    else:
        print(
            "  OVERALL: DIVERGES — IS-only scoring (0.6*IS_Sharpe + 0.4*n/250) selects a "
            "different substrate than /045 ALT_1 (0.5*OOS_Sharpe + 0.3*IS_Sharpe + 0.2*n/100)."
        )
        print(
            "  This is expected: /046 uses IS-ONLY scoring (no OOS data) whereas /045 used "
            "a mixed IS+OOS composite. The /046 substrate is the IS-only-valid selection."
        )

    return coincides


# ---------------------------------------------------------------------------
# Security audit (fail-fast)
# ---------------------------------------------------------------------------


def _self_audit() -> None:
    """Emit security posture declaration.

    Full OOS-leak audit is performed by tests/test_iteration_v1_046.py
    (test_no_oos_leak_partition_solve).  That test runs on CI and before
    every commit.  The in-process audit here is declarative only.
    """
    print("[security] IS-only posture declared:")
    print("  - Only in_sample/trades.csv paths are opened.")
    print("  - IS filter: close_time < OOS_CUTOFF_MS (never >=).")
    print("  - Full audit: tests/test_iteration_v1_046.py::test_no_oos_leak_partition_solve")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 72)
    print("PARTITION-SOLVE v2 — iter-v1/046  (IS-only scoring)")
    print("=" * 72)
    print(f"  IS window:        {IS_WINDOW_START} → {IS_WINDOW_END}")
    print(f"  OOS_CUTOFF_MS:    {OOS_CUTOFF_MS}  (2025-03-24 00:00 UTC)")
    print("  Score formula:    0.6 * IS_Sharpe_ann + 0.4 * (IS_n_trades / 250)")
    print(f"  Hard gate:        IS_n_trades >= {MIN_IS_TRADES}")
    print(f"  Excluded iters:   {sorted(EXCLUDED_ITERS)}")
    print(f"  Reports dir:      {REPORTS_V1}")
    print()

    # Security self-audit first
    _self_audit()

    # Enumerate candidates (IS-only)
    print("\n[enumerate] Scanning candidates...")
    candidates = _enumerate_candidates()
    total_iters = len({c["iter"] for c in candidates})
    print(
        f"  {len(candidates)} candidates after HARD GATE "
        f"(from {total_iters} source iters × 5 coins, "
        f"excluding < {MIN_IS_TRADES} IS trades)"
    )

    # Print top-3 per coin
    _print_top3_per_coin(candidates)

    # Select partition
    selected = _select_partition(candidates)

    # Print selected partition
    print("\n" + "=" * 72)
    print("SELECTED PARTITION (IS-only, highest score per coin)")
    print("=" * 72)
    print(f"  {'Component':<10} {'Source Iter':<30} {'IS_Sharpe':>10} {'IS_n':>6} {'Score':>8}")
    print("  " + "-" * 72)
    for coin in COINS:
        sel = selected[coin]
        print(
            f"  {sel['component_id']:<10} {sel['iter']:<30} "
            f"{sel['is_sharpe']:>+10.4f} {sel['is_n_trades']:>6} {sel['score']:>8.4f}"
        )

    # Compare vs ALT_1
    coincides = _compare_vs_alt1(selected)

    # Write output CSV
    _write_substrate_csv(selected)

    # Print final status
    print()
    print("=" * 72)
    print("[partition_solve_v2] DONE")
    print(f"  Output: {OUT_PATH}")
    print(f"  Coincides with /045 ALT_1: {coincides}")
    print("=" * 72)


if __name__ == "__main__":
    main()
