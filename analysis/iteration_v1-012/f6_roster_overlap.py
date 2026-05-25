"""F6 roster-overlap diagnostic — committed artifact per Critic Rec #2 (iter-v1/011 closeout).

Purpose
-------
Produce `f6_roster_overlap.csv` deterministic artifact for any v1 iteration whose
brief Section 4 declares F6-style roster-overlap falsifiers. iter-v1/011 surfaced
the LM Master offline-only computation of F6 baseline-overlap (16.7%) as a
process-integrity gap: load-bearing falsifiers must be reproducible from
committed artifacts equivalent to the comparison.csv + dsr.json contract.

This script joins a TARGET iteration's trades.csv against one or more
REFERENCE iterations' trades.csv on `(symbol, open_time)` and emits per-half
(IS/OOS) per-symbol overlap counts + percentages.

Used by iter-v1/012 substrate-dissolution probe for F7 LTC IS roster
overlap measurement vs /011 (the canonical substrate-lock test).

Inputs (CLI args)
-----------------
--target REPORTS_DIR     directory containing in_sample/trades.csv +
                         out_of_sample/trades.csv (e.g., reports-v1/iteration_v1-012/)
--reference NAME=REPORTS_DIR  repeatable; named reference rosters
                              (e.g., baseline=reports-v1/iteration_v1-baseline/
                                     iter011=reports-v1/iteration_v1-011/)
--output OUT_CSV         output CSV path (e.g., reports-v1/iteration_v1-012/f6_roster_overlap.csv)

Output CSV schema
-----------------
half,symbol,reference_name,n_target,n_reference,n_overlap,pct_target_in_reference,pct_reference_in_target,asymmetric_diff
- half: "IS" or "OOS"
- symbol: per-symbol breakdown PLUS one PORTFOLIO row per (half, reference_name)
- reference_name: from --reference NAME=PATH
- n_target: count of trades in target's half (per-symbol or portfolio)
- n_reference: count of trades in reference's half (same)
- n_overlap: count of (symbol, open_time) keys in BOTH
- pct_target_in_reference: 100 * n_overlap / n_target
- pct_reference_in_target: 100 * n_overlap / n_reference
- asymmetric_diff: pct_target_in_reference - pct_reference_in_target
  (positive = target is a SUBSET-ish of reference; negative = reference is subset-ish of target;
   ~0 = rosters are similar size and ~equally overlapped)

Determinism
-----------
- Sort order: half, symbol (lexicographic), reference_name (order given on CLI)
- Float precision: 6 decimals
- Trade-key tuple: (symbol, open_time) where open_time is the integer ms epoch
  from trades.csv (no string roundtrip)

Usage example
-------------
uv run python analysis/iteration_v1-012/f6_roster_overlap.py \\
    --target reports-v1/iteration_v1-012 \\
    --reference baseline=reports-v1/iteration_v1-baseline \\
    --reference iter011=reports-v1/iteration_v1-011 \\
    --reference iter010=reports-v1/iteration_v1-010 \\
    --output reports-v1/iteration_v1-012/f6_roster_overlap.csv

Author
------
QR phase 1-5 deliverable for iter-v1/012; addresses Critic Rec #2 to /011 closeout
(Critic Phase 7.5 review.md §"Recommendations to QR" Item 2). Codified as
permanent v1 process discipline per `feedback_v1_substrate_basin_lock.md`
and diary-v1/iteration_v1-011.md LESSON #4.

"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def _load_trade_keys(trades_csv: Path) -> dict[str, set[int]]:
    """Read trades.csv and return {symbol: {open_time_ms, ...}}.

    Open time is parsed as int. CSV header includes 'symbol' and 'open_time'.
    Rows with weight_factor == 0 are EXCLUDED (BTC-kill v2-style mask;
    structurally present in v1 only via R5 binary-kill but we still defensively
    drop them — a zero-weight trade is effectively not executed).
    """
    if not trades_csv.exists():
        raise FileNotFoundError(f"missing trades.csv at {trades_csv}")

    keys: dict[str, set[int]] = {}
    with trades_csv.open() as fh:
        reader = csv.DictReader(fh)
        if "symbol" not in reader.fieldnames or "open_time" not in reader.fieldnames:
            raise ValueError(
                f"trades.csv at {trades_csv} missing required columns "
                f"'symbol' or 'open_time' (got {reader.fieldnames})"
            )
        for row in reader:
            sym = row["symbol"]
            ot = int(row["open_time"])
            wf_raw = row.get("weight_factor", "1.0")
            try:
                wf = float(wf_raw)
            except (TypeError, ValueError):
                wf = 1.0
            if wf == 0.0:
                continue
            keys.setdefault(sym, set()).add(ot)
    return keys


def _compute_overlap_row(
    target_keys: set[int],
    reference_keys: set[int],
) -> tuple[int, int, int, float, float, float]:
    """Return (n_target, n_reference, n_overlap, pct_t_in_r, pct_r_in_t, asym_diff)."""
    n_target = len(target_keys)
    n_reference = len(reference_keys)
    n_overlap = len(target_keys & reference_keys)
    pct_t_in_r = (100.0 * n_overlap / n_target) if n_target > 0 else 0.0
    pct_r_in_t = (100.0 * n_overlap / n_reference) if n_reference > 0 else 0.0
    asym_diff = pct_t_in_r - pct_r_in_t
    return (n_target, n_reference, n_overlap, pct_t_in_r, pct_r_in_t, asym_diff)


def _emit_rows_for_half(
    half: str,
    target_dir: Path,
    references: list[tuple[str, Path]],
) -> list[dict[str, object]]:
    """Produce per-symbol AND portfolio rows for one half (IS or OOS)."""
    sub = "in_sample" if half == "IS" else "out_of_sample"
    target_trades = target_dir / sub / "trades.csv"
    target_keys = _load_trade_keys(target_trades)
    rows: list[dict[str, object]] = []

    for ref_name, ref_dir in references:
        ref_trades = ref_dir / sub / "trades.csv"
        ref_keys = _load_trade_keys(ref_trades)
        # Per-symbol union of symbols
        all_symbols = sorted(set(target_keys.keys()) | set(ref_keys.keys()))
        for sym in all_symbols:
            t = target_keys.get(sym, set())
            r = ref_keys.get(sym, set())
            n_t, n_r, n_o, p_tir, p_rit, asym = _compute_overlap_row(t, r)
            rows.append(
                {
                    "half": half,
                    "symbol": sym,
                    "reference_name": ref_name,
                    "n_target": n_t,
                    "n_reference": n_r,
                    "n_overlap": n_o,
                    "pct_target_in_reference": round(p_tir, 6),
                    "pct_reference_in_target": round(p_rit, 6),
                    "asymmetric_diff": round(asym, 6),
                }
            )
        # Portfolio rollup
        t_all: set[tuple[str, int]] = {
            (sym, ot) for sym, ots in target_keys.items() for ot in ots
        }
        r_all: set[tuple[str, int]] = {
            (sym, ot) for sym, ots in ref_keys.items() for ot in ots
        }
        n_t = len(t_all)
        n_r = len(r_all)
        n_o = len(t_all & r_all)
        p_tir = (100.0 * n_o / n_t) if n_t > 0 else 0.0
        p_rit = (100.0 * n_o / n_r) if n_r > 0 else 0.0
        asym = p_tir - p_rit
        rows.append(
            {
                "half": half,
                "symbol": "PORTFOLIO",
                "reference_name": ref_name,
                "n_target": n_t,
                "n_reference": n_r,
                "n_overlap": n_o,
                "pct_target_in_reference": round(p_tir, 6),
                "pct_reference_in_target": round(p_rit, 6),
                "asymmetric_diff": round(asym, 6),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="F6 roster-overlap diagnostic (committed artifact per /011 Critic Rec #2)"
    )
    parser.add_argument(
        "--target",
        required=True,
        type=Path,
        help="Target iteration reports dir (must contain in_sample/trades.csv + out_of_sample/trades.csv)",
    )
    parser.add_argument(
        "--reference",
        required=True,
        action="append",
        default=[],
        help="Reference iteration as NAME=REPORTS_DIR (repeatable)",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output CSV path",
    )
    args = parser.parse_args()

    # Parse --reference NAME=PATH list
    references: list[tuple[str, Path]] = []
    for ref_spec in args.reference:
        if "=" not in ref_spec:
            sys.exit(
                f"ERROR: --reference must be NAME=PATH; got {ref_spec!r}"
            )
        name, _, path_str = ref_spec.partition("=")
        name = name.strip()
        ref_path = Path(path_str.strip())
        if not name or not path_str:
            sys.exit(f"ERROR: empty name or path in --reference {ref_spec!r}")
        references.append((name, ref_path))

    target_dir: Path = args.target

    # Verify target dir has IS + OOS trades.csv
    for sub in ("in_sample", "out_of_sample"):
        p = target_dir / sub / "trades.csv"
        if not p.exists():
            sys.exit(f"ERROR: missing {p}")

    # Compute both halves
    all_rows: list[dict[str, object]] = []
    for half in ("IS", "OOS"):
        all_rows.extend(_emit_rows_for_half(half, target_dir, references))

    # Sort: half (IS before OOS), symbol (PORTFOLIO last by adding suffix), reference_name
    half_order = {"IS": 0, "OOS": 1}

    def _sym_key(s: str) -> tuple[int, str]:
        if s == "PORTFOLIO":
            return (1, s)
        return (0, s)

    all_rows.sort(
        key=lambda r: (
            half_order[r["half"]],
            _sym_key(r["symbol"]),
            r["reference_name"],
        )
    )

    # Emit CSV
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "half",
        "symbol",
        "reference_name",
        "n_target",
        "n_reference",
        "n_overlap",
        "pct_target_in_reference",
        "pct_reference_in_target",
        "asymmetric_diff",
    ]
    with args.output.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)

    # Echo summary to stdout (deterministic ordering)
    print(f"[f6_roster_overlap] wrote {args.output} ({len(all_rows)} rows)")
    print(f"  target: {target_dir}")
    print(f"  references ({len(references)}):")
    for name, path in references:
        print(f"    {name} = {path}")
    print()
    print("Portfolio overlap (target_in_reference %):")
    print(f"  {'half':<5} {'reference':<20} {'n_target':>10} {'n_ref':>10} {'n_overlap':>10} {'pct':>10}")
    for row in all_rows:
        if row["symbol"] == "PORTFOLIO":
            print(
                f"  {row['half']:<5} {row['reference_name']:<20} "
                f"{row['n_target']:>10} {row['n_reference']:>10} "
                f"{row['n_overlap']:>10} {row['pct_target_in_reference']:>9.2f}%"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
