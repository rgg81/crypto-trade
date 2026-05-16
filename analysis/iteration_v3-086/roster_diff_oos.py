"""iter-v3/086 Phase 8 — OOS roster-diff vs the /084 EXPLORATION-MODE-REFERENCE.

The single Phase-8 forensic task: adjudicate the brief Section 7/8 LOCKED F2/F3
duration sub-channel falsifiers, which the Phase 7.5 Critic explicitly delegated
to this Phase-8 roster-diff (review.md Recommendation #1: "I delegate sub-channels
(c)/(d) to the QR's Phase-8 roster-diff").

  F2 — Section 8.3(c) trade-selection sub-channel. On the /084-anchor OOS roster
    diff, the mean trade duration of the trades /086 ADDS minus the trades it
    REMOVES must be <= +1.0 candle. If the added set skews > +1.0 candle
    longer-held than the removed set, the regime factor is loaded via trade
    selection -> SUSPICIOUS.

  F3 — Section 8.3(d) full-roster sub-channel. If the /086 full-OOS-roster mean
    trade duration shifts > +1.0 candle vs /084 -> holding-time extension ->
    SUSPICIOUS.

Disjunctive precedence (brief Section 8): SUSPICIOUS -> NEGATIVE -> PROMISING ->
INERT -> NULL-RESULT. The strict OOS-DOMINANT sub-mode does NOT fire (IS Δ
+0.063 >= 0) and the ratio gate does NOT fire (OOS/IS 1.149 < 3.0); the
classification therefore turns on whether F2/F3 fire. A LOCKED numeric falsifier
that fires cannot be downgraded by a mechanism argument (the /085 discipline,
`feedback_v3_per_symbol_target_axis_falsifier.md`).

Method precedent: `analysis/iteration_v3-085/roster_diff_oos.py` (the /085
closeout's committed roster-diff). This script reads ONLY report CSVs already
written by the /086 and /084 backtests -- it loads no OOS klines and computes
no forward-looking quantity. It is a Phase-7/8 adjudication script, not a
Phase-1-5 EDA script.

Run:  uv run python analysis/iteration_v3-086/roster_diff_oos.py
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

REPORTS = Path(__file__).resolve().parents[2] / "reports-v3"
ITER_086 = REPORTS / "iteration_v3-086"
ITER_084 = REPORTS / "iteration_v3-084"  # the cycle-3 EXPLORATION-MODE-REFERENCE

# 8h candle interval in milliseconds -- the unit the duration gap is measured in.
INTERVAL_MS = 480 * 60 * 1000

# brief Section 8.3(c)/(d) LOCKED falsifier threshold (candles)
SUBCHANNEL_THRESHOLD = 1.0


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open() as f:
        return list(csv.DictReader(f))


def trade_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    """Trade-identity key. A trade is the same trade across two rosters iff symbol,
    direction, entry candle open_time and entry_price all match."""
    return (row["symbol"], row["direction"], row["open_time"], row["entry_price"])


def duration_candles(row: dict[str, str]) -> float:
    return (int(row["close_time"]) - int(row["open_time"])) / INTERVAL_MS


def weighted_pnl(row: dict[str, str]) -> float:
    return float(row["weighted_pnl"])


def mean_dur(rows: list[dict[str, str]]) -> float:
    return sum(duration_candles(r) for r in rows) / len(rows) if rows else 0.0


def f2_roster_diff() -> bool:
    print("=" * 72)
    print("F2 -- OOS roster diff /086 vs /084 (the Section 8.3(c) sub-channel)")
    print("=" * 72)

    o86 = load_csv(ITER_086 / "out_of_sample" / "trades.csv")
    o84 = load_csv(ITER_084 / "out_of_sample" / "trades.csv")

    s86 = {trade_key(r): r for r in o86}
    s84 = {trade_key(r): r for r in o84}

    added = [s86[k] for k in s86 if k not in s84]
    removed = [s84[k] for k in s84 if k not in s86]
    common = [k for k in s86 if k in s84]

    print(f"/086 OOS trades: {len(o86)}    /084 OOS trades: {len(o84)}")
    print(f"common (identical trade-identity key): {len(common)}")
    print(f"/086 ADDS: {len(added)}    /086 REMOVES: {len(removed)}")

    mean_add = mean_dur(added)
    mean_rem = mean_dur(removed)
    gap = mean_add - mean_rem

    print()
    print(f"added   mean duration : {mean_add:.4f} candles")
    print(f"removed mean duration : {mean_rem:.4f} candles")
    print(f">>> added-minus-removed OOS mean-duration gap: {gap:+.4f} candles")
    print(f">>> LOCKED Section 8.3(c) falsifier threshold : +{SUBCHANNEL_THRESHOLD:.1f} candles")
    fires = gap > SUBCHANNEL_THRESHOLD
    print(f">>> F2 SUSPICIOUS sub-channel (c): {'FIRES' if fires else 'does NOT fire'}")

    # robustness -- the gap must not be an artifact of the identity-key choice.
    print()
    print("robustness -- gap under alternative trade-identity keys:")
    for name, kf in [
        ("sym+dir+open+entry", trade_key),
        ("sym+open_time", lambda r: (r["symbol"], r["open_time"])),
        ("sym+dir+open", lambda r: (r["symbol"], r["direction"], r["open_time"])),
    ]:
        a = {kf(r): r for r in o86}
        b = {kf(r): r for r in o84}
        add = [a[k] for k in a if k not in b]
        rem = [b[k] for k in b if k not in a]
        print(
            f"  key={name:20s}: added={len(add):3d} removed={len(rem):3d}  "
            f"gap={mean_dur(add) - mean_dur(rem):+.4f}"
        )

    # per-symbol decomposition -- texture for the diary (does NOT change the LOCKED call).
    print()
    print("per-symbol OOS roster-diff (texture; the LOCKED call is the aggregate gap):")
    for sym in ("BCHUSDT", "LDOUSDT", "TRXUSDT"):
        a = [r for r in added if r["symbol"] == sym]
        r_ = [r for r in removed if r["symbol"] == sym]
        wa = sum(weighted_pnl(x) for x in a)
        wr = sum(weighted_pnl(x) for x in r_)
        print(
            f"  {sym}: added={len(a):2d} (dur {mean_dur(a):.2f}, wpnl {wa:+.2f})  "
            f"removed={len(r_):2d} (dur {mean_dur(r_):.2f}, wpnl {wr:+.2f})  "
            f"dur-gap {mean_dur(a) - mean_dur(r_):+.2f}"
        )

    # exit-reason mix + net wpnl of the swap -- the regime-loading-direction texture.
    print()
    print("exit-reason mix:")
    print(f"  added  : {dict(Counter(r['exit_reason'] for r in added))}")
    print(f"  removed: {dict(Counter(r['exit_reason'] for r in removed))}")
    net = sum(weighted_pnl(r) for r in added) - sum(weighted_pnl(r) for r in removed)
    print(f"net OOS wpnl from the roster swap: {net:+.4f}  (added - removed)")
    return fires


def f3_full_roster() -> bool:
    print()
    print("=" * 72)
    print("F3 -- full-OOS-roster mean-duration shift /086 vs /084 (Section 8.3(d))")
    print("=" * 72)

    o86 = load_csv(ITER_086 / "out_of_sample" / "trades.csv")
    o84 = load_csv(ITER_084 / "out_of_sample" / "trades.csv")

    m86 = mean_dur(o86)
    m84 = mean_dur(o84)
    shift = m86 - m84

    print(f"/086 full-OOS-roster mean duration : {m86:.4f} candles ({len(o86)} trades)")
    print(f"/084 full-OOS-roster mean duration : {m84:.4f} candles ({len(o84)} trades)")
    print(f">>> full-roster mean-duration shift: {shift:+.4f} candles")
    print(f">>> LOCKED Section 8.3(d) falsifier threshold : +{SUBCHANNEL_THRESHOLD:.1f} candles")
    fires = shift > SUBCHANNEL_THRESHOLD
    print(f">>> F3 SUSPICIOUS sub-channel (d): {'FIRES' if fires else 'does NOT fire'}")
    return fires


def main() -> None:
    f2 = f2_roster_diff()
    f3 = f3_full_roster()
    print()
    print("=" * 72)
    print("PHASE 8 ADJUDICATION SUMMARY")
    print("=" * 72)
    print(f"F2 (Section 8.3(c) trade-selection sub-channel): {'FIRES' if f2 else 'does NOT fire'}")
    print(f"F3 (Section 8.3(d) full-roster sub-channel)    : {'FIRES' if f3 else 'does NOT fire'}")
    print(
        "Ratio gate (8.3(a) OOS/IS > 3.0): does NOT fire (1.149).\n"
        "OOS-DOMINANT (8.3(b) IS Δ < 0): does NOT fire (IS Δ +0.063 >= 0)."
    )
    if f2 or f3:
        print(
            ">>> A LOCKED SUSPICIOUS sub-channel FIRES -> FINAL CLASSIFICATION: SUSPICIOUS.\n"
            "    Disjunctive precedence places the firing SUSPICIOUS sub-channel above INERT."
        )
    else:
        print(
            ">>> NO LOCKED SUSPICIOUS sub-channel fires. F1 INERT falsifier is satisfied\n"
            "    (basis features rank 15/16/17 of 17) -> FINAL CLASSIFICATION: INERT.\n"
            "    The +0.696 OOS lift is the documented Optuna-perturbation artifact of 3\n"
            "    INERT columns (feedback_v3_inert_features_at_higher_budget.md), NOT signal."
        )
    print("Decision: NO-MERGE. BASELINE_V3.md UNCHANGED at v0.v3-059.")


if __name__ == "__main__":
    main()
