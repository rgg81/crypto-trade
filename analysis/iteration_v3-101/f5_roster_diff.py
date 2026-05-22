"""iter-v3/101 Phase 7 — Falsifier F5 roster-diff analysis.

F5 (brief Section 4): "Mechanical-only lift — OOS improves but the per-symbol
added-vs-removed-trade mean-duration gap exceeds +1.0 (the /076 trade-selection
sub-channel signature — the lift is a roster-churn artifact, not signal)."

This script diffs the /101 OOS trade roster against the architecturally-matched
baseline roster and computes, per symbol, the mean duration (in 8h candles) of
trades that were ADDED by the weight_mode change vs trades that were REMOVED.

ANCHOR CHOICE — architecturally-matched, per the Phase-7.5 Critic Recommendation 1
and `feedback_v3_dsr_mode_artifact.md`:
  /101 ran 3-seed EXPLORATION mode. The architecturally-matched baseline is /060,
  the cycle-1 3-seed EXPLORATION-mode reference (same ensemble_size=3, same
  n_trials=35). /060's OOS roster IS comparable to /101's. /059 (10-seed
  CONFIRMATION) would be an apples-to-oranges roster comparison and is reported
  only as a secondary caveat cross-check.

A trade is matched between rosters on the key (symbol, direction, open_time).
The weight_mode axis re-weights training samples; it does NOT change features,
labels, or the inference path — so a trade either survives bit-identically or
is replaced. Entry timestamp + symbol + side is the natural identity.

Duration is measured in 8h candles: (close_time - open_time) / 8h_ms.

F5 FIRES if, on any symbol with a non-trivial OOS lift, the (added-trade
mean-duration) - (removed-trade mean-duration) gap exceeds +1.0 candle.

Strictly a Phase-7 post-OOS diagnostic. Reads only committed report CSVs.
"""

from __future__ import annotations

import csv
from pathlib import Path

EIGHT_H_MS = 8 * 60 * 60 * 1000

REPORTS = Path(__file__).resolve().parents[2] / "reports-v3"
ITER_OOS = REPORTS / "iteration_v3-101" / "out_of_sample" / "trades.csv"
ANCHOR_060_OOS = REPORTS / "iteration_v3-060" / "out_of_sample" / "trades.csv"
ANCHOR_059_OOS = REPORTS / "iteration_v3-059" / "out_of_sample" / "trades.csv"

OUT_DIR = Path(__file__).resolve().parent
OUT_CSV = OUT_DIR / "T5_f5_roster_diff.csv"


def load_roster(path: Path) -> dict[tuple[str, str, str], dict]:
    """Return {(symbol, direction, open_time): row} keyed on trade identity."""
    rows: dict[tuple[str, str, str], dict] = {}
    with path.open() as fh:
        for r in csv.DictReader(fh):
            key = (r["symbol"], r["direction"], r["open_time"])
            r["_duration_candles"] = (
                int(r["close_time"]) - int(r["open_time"])
            ) / EIGHT_H_MS
            rows[key] = r
    return rows


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def diff_against(anchor_path: Path, anchor_label: str) -> list[dict]:
    """Per-symbol added/removed/kept duration decomposition vs one anchor."""
    iter_roster = load_roster(ITER_OOS)
    anchor_roster = load_roster(anchor_path)

    symbols = sorted({k[0] for k in iter_roster} | {k[0] for k in anchor_roster})
    out: list[dict] = []

    for sym in symbols:
        iter_keys = {k for k in iter_roster if k[0] == sym}
        anch_keys = {k for k in anchor_roster if k[0] == sym}

        added = iter_keys - anch_keys  # in /101, not in anchor
        removed = anch_keys - iter_keys  # in anchor, not in /101
        kept = iter_keys & anch_keys

        added_dur = [iter_roster[k]["_duration_candles"] for k in added]
        removed_dur = [anchor_roster[k]["_duration_candles"] for k in removed]

        gap = mean(added_dur) - mean(removed_dur)
        # F5 only meaningful where churn exists on both sides.
        f5_evaluable = bool(added) and bool(removed)
        f5_fires = f5_evaluable and gap > 1.0

        out.append(
            {
                "anchor": anchor_label,
                "symbol": sym,
                "n_anchor": len(anch_keys),
                "n_iter": len(iter_keys),
                "n_kept": len(kept),
                "n_added": len(added),
                "n_removed": len(removed),
                "added_mean_dur": round(mean(added_dur), 4) if added else "",
                "removed_mean_dur": round(mean(removed_dur), 4) if removed else "",
                "duration_gap": round(gap, 4) if f5_evaluable else "",
                "f5_evaluable": f5_evaluable,
                "f5_fires_symbol": f5_fires,
            }
        )

    # Portfolio-aggregate row: pool every added/removed trade across symbols.
    all_added_dur, all_removed_dur = [], []
    for sym in symbols:
        iter_keys = {k for k in iter_roster if k[0] == sym}
        anch_keys = {k for k in anchor_roster if k[0] == sym}
        all_added_dur += [
            iter_roster[k]["_duration_candles"] for k in (iter_keys - anch_keys)
        ]
        all_removed_dur += [
            anchor_roster[k]["_duration_candles"] for k in (anch_keys - iter_keys)
        ]
    agg_gap = mean(all_added_dur) - mean(all_removed_dur)
    out.append(
        {
            "anchor": anchor_label,
            "symbol": "PORTFOLIO",
            "n_anchor": len(anchor_roster),
            "n_iter": len(iter_roster),
            "n_kept": len(set(iter_roster) & set(anchor_roster)),
            "n_added": len(all_added_dur),
            "n_removed": len(all_removed_dur),
            "added_mean_dur": round(mean(all_added_dur), 4),
            "removed_mean_dur": round(mean(all_removed_dur), 4),
            "duration_gap": round(agg_gap, 4),
            "f5_evaluable": True,
            "f5_fires_symbol": agg_gap > 1.0,
        }
    )
    return out


def main() -> None:
    rows: list[dict] = []
    rows += diff_against(ANCHOR_060_OOS, "iter-v3/060 (3-seed EXPLORATION — matched)")
    if ANCHOR_059_OOS.exists():
        rows += diff_against(
            ANCHOR_059_OOS, "iter-v3/059 (10-seed CONFIRMATION — caveat only)"
        )

    fields = [
        "anchor",
        "symbol",
        "n_anchor",
        "n_iter",
        "n_kept",
        "n_added",
        "n_removed",
        "added_mean_dur",
        "removed_mean_dur",
        "duration_gap",
        "f5_evaluable",
        "f5_fires_symbol",
    ]
    with OUT_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(f"wrote {OUT_CSV}")
    print()
    print("=== F5 roster-diff — duration in 8h candles ===")
    for r in rows:
        marker = " <== F5 FIRES" if r["f5_fires_symbol"] else ""
        print(
            f"  [{r['anchor'][:34]:34s}] {r['symbol']:10s} "
            f"kept={r['n_kept']:3d} added={r['n_added']:3d} removed={r['n_removed']:3d}  "
            f"added_dur={str(r['added_mean_dur']):>8s} "
            f"removed_dur={str(r['removed_mean_dur']):>8s} "
            f"gap={str(r['duration_gap']):>8s}{marker}"
        )

    matched = [
        r
        for r in rows
        if r["anchor"].startswith("iter-v3/060") and r["symbol"] != "PORTFOLIO"
    ]
    any_fire = any(r["f5_fires_symbol"] for r in matched)
    print()
    print(
        "F5 VERDICT (matched /060 anchor, per-symbol): "
        + ("FIRES" if any_fire else "DOES NOT FIRE")
    )


if __name__ == "__main__":
    main()
