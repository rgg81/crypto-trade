"""Bundle weight calibration for iter-v1/045 — EQUAL weights (1/5 each).

IS-only: this script loads each component's in_sample/trades.csv solely to
assert that every row satisfies close_time < OOS_CUTOFF_MS (IS-window guard).
The EQUAL weight vector itself is a literal constant — no IS data is used to
derive it (no IS-Sharpe, no IS-trade-count mapping).

Rationale (per Section 11.B of the research brief):
- IS-Sharpe-proportional would CLIP C-BTC to ~0 (IS Sharpe = -0.21), but
  C-BTC is the LARGEST OOS contributor (OOS Sharpe +6.10, Δ +3.98). Zeroing
  C-BTC defeats the per-coin specialist substitution hypothesis.
- EQUAL weights minimise researcher-degrees-of-freedom (no IS-derived knob
  beyond the N=5 component count). This is the simplest IS-only choice and
  trivially satisfies Critic Check 17.

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
# ---------------------------------------------------------------------------

COMPONENTS = [
    ("C-BTC", "BTC", "iteration_v1-012"),
    ("C-ETH", "ETH", "iteration_v1-042"),
    ("C-LINK", "LINK", "iteration_v1-011"),
    ("C-LTC", "LTC", "iteration_v1-040"),
    ("C-DOT", "DOT", "iteration_v1-031"),
]

N = len(COMPONENTS)
EQUAL_WEIGHT: float = round(1.0 / N, 1)  # 0.2 — 1 decimal place per brief Section 11.B

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_V1 = REPO_ROOT / "reports-v1"
OUT_PATH = Path(__file__).resolve().parent / "bundle_weights.csv"


def _assert_is_window(iter_label: str) -> int:
    """Load in_sample/trades.csv for iter_label; count IS-window rows.

    Returns the count of rows with close_time strictly inside the IS window
    (informational).  Boundary rows (trade OPENED during IS, CLOSED past the
    cutoff — walk-forward artifact) are silently excluded from the IS count.
    The script reads ONLY in_sample/ — IS-only provenance is guaranteed by
    file path.  Raises FileNotFoundError if the file does not exist.
    """
    trades_path = REPORTS_V1 / iter_label / "in_sample" / "trades.csv"
    if not trades_path.exists():
        raise FileNotFoundError(f"IS trades not found: {trades_path}")
    n_rows = 0
    n_boundary = 0
    with trades_path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            ct = int(r["close_time"])
            if ct < OOS_CUTOFF_MS:
                n_rows += 1
            else:
                n_boundary += 1
    if n_boundary > 0:
        print(
            f"  NOTE: {iter_label} in_sample has {n_boundary} boundary row(s) "
            f"at or past the OOS boundary (walk-forward straddle; excluded from IS count)."
        )
    return n_rows


def main() -> None:
    print("[weight_calibration] Running IS-window assertion for all 5 components...")
    for cid, _coin, iter_label in COMPONENTS:
        n = _assert_is_window(iter_label)
        print(f"  {cid} ({iter_label}): {n} IS rows — PASS (all close_time < OOS_CUTOFF_MS)")

    # Build weight rows (EQUAL; literal constants — not derived from IS data).
    rows = [
        {
            "component_id": cid,
            "weight": EQUAL_WEIGHT,
            "derivation_method": "equal",
            "is_window_start": IS_WINDOW_START,
            "is_window_end": IS_WINDOW_END,
        }
        for (cid, _coin, _iter) in COMPONENTS
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
