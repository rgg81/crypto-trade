"""iter-v3/087 Phase 8 — OOS roster-diff vs the /084 EXPLORATION-MODE-REFERENCE.

The single Phase-8 forensic task: formally adjudicate the brief Section 4.3 /
Section 8.3 LOCKED F4 trade-selection sub-channels, which the Phase 7.5 Critic
flagged for this Phase-8 roster-diff (review.md "The Classification" section:
"(c)/(d) the trade-selection sub-channels require the Phase-8 OOS roster-diff
... the QR must run the roster-diff to formally close (c)/(d)").

  F4 / Section 8.3(c) — trade-selection sub-channel. On the /084-anchor OOS
    roster diff, the mean trade duration of the trades /087 ADDS minus the
    trades it REMOVES must be <= +1.0 candle. If the added set skews > +1.0
    candle longer-held than the removed set, the regime factor is loaded via
    trade selection -> SUSPICIOUS.

  Section 8.3(d) — added-symbol target-axis sub-channel. The GALA+MANA+SAND
    OOS-roster mean trade duration must be <= +1.0 candle longer than the
    incumbent (BCH/LDO/TRX) OOS pooled-roster mean duration. The brief
    Section 4.4 pre-registered target-axis falsifier.

Disjunctive precedence (brief Section 8): SUSPICIOUS -> NEGATIVE -> PROMISING ->
INERT -> NULL-RESULT. SUSPICIOUS is IMPROBABLE here on headline metrics — OOS
went DOWN (Δ -0.8349), not UP: the ratio gate (a) is NEGATIVE (-0.5460, not
> 3.0) and the OOS-DOMINANT sub-mode (b) is foreclosed (IS Δ +0.0883 >= 0).
The headline NEGATIVE clause (Section 8.2, OOS Δ < -0.20) fires decisively.
This script formally CLOSES the (c)/(d) sub-channels so the Section 8
classification is complete. A LOCKED numeric falsifier that fires cannot be
downgraded by a mechanism argument (the /085 discipline,
`feedback_v3_per_symbol_target_axis_falsifier.md`).

Method precedent: `analysis/iteration_v3-086/roster_diff_oos.py` and
`analysis/iteration_v3-085/roster_diff_oos.py`. This script reads ONLY report
CSVs already written by the /087 and /084 backtests -- it loads no OOS klines
and computes no forward-looking quantity. It is a Phase-7/8 adjudication
script, not a Phase-1-5 EDA script.

Run:  uv run python analysis/iteration_v3-087/roster_diff_oos.py
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

REPORTS = Path(__file__).resolve().parents[2] / "reports-v3"
ITER_087 = REPORTS / "iteration_v3-087"
ITER_084 = REPORTS / "iteration_v3-084"  # the cycle-3 EXPLORATION-MODE-REFERENCE

# 8h candle interval in milliseconds -- the unit the duration gap is measured in.
INTERVAL_MS = 480 * 60 * 1000

# brief Section 8.3(c)/(d) LOCKED falsifier threshold (candles)
SUBCHANNEL_THRESHOLD = 1.0

# the 3 incumbent symbols vs the 3 /087-added symbols
INCUMBENTS = {"BCHUSDT", "LDOUSDT", "TRXUSDT"}
ADDED_SYMBOLS = {"GALAUSDT", "MANAUSDT", "SANDUSDT"}


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open() as f:
        return list(csv.DictReader(f))


def trade_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    """Trade-identity key. A trade is the same trade across two rosters iff symbol,
    direction, entry candle open_time and entry_price all match."""
    return (row["symbol"], row["direction"], row["open_time"], row["entry_price"])


def duration_candles(row: dict[str, str]) -> float:
    return (int(row["close_time"]) - int(row["open_time"])) / INTERVAL_MS


def mean_dur(rows: list[dict[str, str]]) -> float:
    return sum(duration_candles(r) for r in rows) / len(rows) if rows else 0.0


def f4_roster_diff() -> bool:
    """F4 / Section 8.3(c) — added-vs-removed OOS-roster mean-duration gap."""
    print("=" * 72)
    print("F4 / Sec 8.3(c) -- OOS roster diff /087 vs /084 (trade-selection sub-channel)")
    print("=" * 72)

    o87 = load_csv(ITER_087 / "out_of_sample" / "trades.csv")
    o84 = load_csv(ITER_084 / "out_of_sample" / "trades.csv")

    s87 = {trade_key(r): r for r in o87}
    s84 = {trade_key(r): r for r in o84}

    added = [s87[k] for k in s87 if k not in s84]
    removed = [s84[k] for k in s84 if k not in s87]
    common = [k for k in s87 if k in s84]

    print(f"/087 OOS trades: {len(o87)}    /084 OOS trades: {len(o84)}")
    print(f"common (identical trade-identity key): {len(common)}")
    print(f"/087 ADDS: {len(added)}    /087 REMOVES: {len(removed)}")

    mean_add = mean_dur(added)
    mean_rem = mean_dur(removed)
    gap = mean_add - mean_rem

    print()
    print(f"added   mean duration : {mean_add:.4f} candles")
    print(f"removed mean duration : {mean_rem:.4f} candles")
    print(f">>> added-minus-removed OOS mean-duration gap: {gap:+.4f} candles")
    print(f">>> LOCKED Section 8.3(c) falsifier threshold : +{SUBCHANNEL_THRESHOLD:.1f} candles")
    fires = gap > SUBCHANNEL_THRESHOLD
    print(f">>> F4 SUSPICIOUS sub-channel (c): {'FIRES' if fires else 'does NOT fire'}")

    # robustness -- the gap must not be an artifact of the identity-key choice.
    print()
    print("robustness -- gap under alternative trade-identity keys:")
    for name, kf in [
        ("sym+dir+open+entry", trade_key),
        ("sym+open_time", lambda r: (r["symbol"], r["open_time"])),
        ("sym+dir+open", lambda r: (r["symbol"], r["direction"], r["open_time"])),
    ]:
        a = {kf(r): r for r in o87}
        b = {kf(r): r for r in o84}
        add = [a[k] for k in a if k not in b]
        rem = [b[k] for k in b if k not in a]
        print(
            f"  key={name:20s}: added={len(add):3d} removed={len(rem):3d}  "
            f"gap={mean_dur(add) - mean_dur(rem):+.4f}"
        )

    # exit-reason mix -- texture, not a gate
    print()
    print("added-set exit-reason mix :", dict(Counter(r["exit_reason"] for r in added)))
    print("removed-set exit-reason mix:", dict(Counter(r["exit_reason"] for r in removed)))
    return fires


def d_added_symbol_subchannel() -> bool:
    """Section 8.3(d) — GALA+MANA+SAND OOS-roster mean duration vs incumbents."""
    print()
    print("=" * 72)
    print("Sec 8.3(d) -- added-symbol target-axis sub-channel (brief Section 4.4)")
    print("=" * 72)

    o87 = load_csv(ITER_087 / "out_of_sample" / "trades.csv")
    added_rows = [r for r in o87 if r["symbol"] in ADDED_SYMBOLS]
    incumbent_rows = [r for r in o87 if r["symbol"] in INCUMBENTS]

    mean_added = mean_dur(added_rows)
    mean_incumbent = mean_dur(incumbent_rows)
    gap = mean_added - mean_incumbent

    print(f"GALA+MANA+SAND OOS trades : {len(added_rows)}  mean duration {mean_added:.4f}")
    print(f"BCH+LDO+TRX    OOS trades : {len(incumbent_rows)}  mean duration {mean_incumbent:.4f}")
    print(f">>> added-symbol-minus-incumbent OOS mean-duration gap: {gap:+.4f} candles")
    print(f">>> LOCKED Section 8.3(d) falsifier threshold: +{SUBCHANNEL_THRESHOLD:.1f} candles")
    fires = gap > SUBCHANNEL_THRESHOLD
    print(f">>> Sec 8.3(d) SUSPICIOUS sub-channel: {'FIRES' if fires else 'does NOT fire'}")

    print()
    print("per-added-symbol OOS mean duration:")
    for sym in sorted(ADDED_SYMBOLS):
        rows = [r for r in o87 if r["symbol"] == sym]
        print(f"  {sym:10s}: {len(rows):3d} trades  mean duration {mean_dur(rows):.4f}")
    return fires


def main() -> None:
    f4 = f4_roster_diff()
    d = d_added_symbol_subchannel()
    print()
    print("=" * 72)
    print("ADJUDICATION SUMMARY")
    print("=" * 72)
    print(f"F4  Sec 8.3(c) added-vs-removed gap   : {'FIRES' if f4 else 'does NOT fire'}")
    print(f"    Sec 8.3(d) added-symbol-subset gap: {'FIRES' if d else 'does NOT fire'}")
    print(f"SUSPICIOUS (c)/(d): {'FIRES' if (f4 or d) else 'does NOT fire'}")


if __name__ == "__main__":
    main()
