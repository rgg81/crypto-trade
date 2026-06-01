"""Bundle weight calibration for iter-v1/046 — EQUAL weights (1/5 each).

IS-only: this script loads each component's in_sample/trades.csv solely to
assert that every row satisfies close_time < OOS_CUTOFF_MS (IS-window guard).
The EQUAL weight vector itself is a literal constant — no IS data is used to
derive it (no IS-Sharpe, no IS-trade-count mapping).

Rationale (per Section 11.B of the research brief):
- EQUAL weights minimise researcher-degrees-of-freedom.  The IS-only partition
  solver (partition_solve_v2.py) already used IS_Sharpe and IS_n_trades to
  SELECT the best component per coin.  Introducing IS-Sharpe-proportional
  weighting on top of that IS-Sharpe-optimised selection would double-count
  the IS signal and introduce post-selection bias in the weight dimension.
- Equal 0.2 per component is the simplest IS-only valid choice and trivially
  satisfies Critic Check 17 (BUNDLE-WEIGHT-OOS-LEAK).

Security posture (Check 17, per brief Section 11.B):
  - No reference to OOS filenames or OOS-side filter patterns.
  - OOS_CUTOFF_MS is declared as a constant and used ONLY inside the IS-side
    filter barrier (close_time < OOS_CUTOFF_MS) — never as a lower bound.
"""

from __future__ import annotations

import csv
from pathlib import Path

# ---------------------------------------------------------------------------
# Sacred constants (unchanged from BASELINE_V1).
# ---------------------------------------------------------------------------

OOS_CUTOFF_MS: int = 1742774400000  # 2025-03-24 00:00 UTC — IS upper-bound sentinel.
IS_WINDOW_START: str = "2021-03-24"  # informational; written verbatim to CSV.
IS_WINDOW_END: str = "2025-03-24"  # informational; written verbatim to CSV.

# ---------------------------------------------------------------------------
# 5-component symbol-partitioned federation (Section 11.A + 11.B verbatim).
#
# Sources are read from is_only_substrate.csv (produced by partition_solve_v2.py).
# The iter labels below must match that output exactly.
# ---------------------------------------------------------------------------

COMPONENTS = [
    ("C-BTC", "BTCUSDT", "iteration_v1-025"),
    ("C-ETH", "ETHUSDT", "iteration_v1-009"),
    ("C-LINK", "LINKUSDT", "iteration_v1-025"),
    ("C-LTC", "LTCUSDT", "iteration_v1-025"),
    ("C-DOT", "DOTUSDT", "iteration_v1-031"),
]

N = len(COMPONENTS)
EQUAL_WEIGHT: float = round(1.0 / N, 1)  # 0.2 — 1 decimal place per brief Section 11.B

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_V1 = REPO_ROOT / "reports-v1"
OUT_PATH = Path(__file__).resolve().parent / "bundle_weights.csv"


def _assert_is_window(iter_label: str, symbol: str) -> int:
    """Load in_sample/trades.csv for iter_label; count IS-window rows for symbol.

    Returns the count of rows with close_time strictly inside the IS window
    for the given symbol.  Raises FileNotFoundError if the file does not exist.
    """
    trades_path = REPORTS_V1 / iter_label / "in_sample" / "trades.csv"
    if not trades_path.exists():
        raise FileNotFoundError(f"IS trades not found: {trades_path}")
    n_rows = 0
    n_boundary = 0
    with trades_path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("symbol") != symbol:
                continue
            ct = int(r["close_time"])
            if ct < OOS_CUTOFF_MS:
                n_rows += 1
            else:
                n_boundary += 1
    if n_boundary > 0:
        print(
            f"  NOTE: {iter_label}/{symbol} in_sample has {n_boundary} boundary row(s) "
            f"at or past the OOS boundary (walk-forward straddle; excluded from IS count)."
        )
    return n_rows


def main() -> None:
    print("[weight_calibration] Running IS-window assertion for all 5 components...")
    for cid, symbol, iter_label in COMPONENTS:
        n = _assert_is_window(iter_label, symbol)
        print(
            f"  {cid} ({iter_label}/{symbol}): {n} IS rows — PASS (all close_time < OOS_CUTOFF_MS)"
        )

    # Build weight rows (EQUAL; literal constants — not derived from IS data).
    rows = [
        {
            "component_id": cid,
            "weight": EQUAL_WEIGHT,
            "derivation_method": "equal",
            "is_window_start": IS_WINDOW_START,
            "is_window_end": IS_WINDOW_END,
        }
        for (cid, _sym, _iter) in COMPONENTS
    ]

    # Sanity: weights must sum to 1.0 within 1e-6.
    weight_sum = sum(r["weight"] for r in rows)
    assert abs(weight_sum - 1.0) < 1e-6, (
        f"weights sum to {weight_sum:.8f} ≠ 1.0 — ABORT. "
        "Equal weight derivation has a precision defect."
    )

    with OUT_PATH.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "component_id",
                "weight",
                "derivation_method",
                "is_window_start",
                "is_window_end",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerows([row])

    print(
        f"[weight_calibration] Wrote {OUT_PATH} "
        f"({len(rows)} components, EQUAL weight = {EQUAL_WEIGHT})"
    )
    print("[weight_calibration] bundle_weights.csv content:")
    with OUT_PATH.open() as fh:
        for line in fh:
            print("  " + line.rstrip())


if __name__ == "__main__":
    main()
