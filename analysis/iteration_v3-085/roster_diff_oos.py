"""iter-v3/085 Phase 8 — OOS roster-diff + per-cell-PBO aggregation reproduction.

Two Phase-8 forensic tasks, both committed for reproducibility:

  TASK A — the Critic-mandated /076 trade-selection SUSPICIOUS sub-channel check.
    Brief Section 8.3(c) LOCKED falsifier: on the /084-anchor OOS roster diff, the
    mean trade duration of the trades /085 ADDS minus the trades it REMOVES must be
    <= +1.0 candle. If the added set skews > +1.0 candle longer-held than the removed
    set, the regime factor is loaded via trade selection -> SUSPICIOUS.
    The Critic (review.md, Central Adjudication) explicitly delegated this roster-diff
    to Phase 8: "the /076 trade-selection sub-channel is a QR Phase-7/8 roster-diff
    check, not yet adjudicated here -- flagged for the QR."

  TASK B — Critic Recommendation #2: confirm the per-cell-PBO aggregation convention.
    The Critic's hand-arithmetic flat 127-row mean came to ~0.102 vs the reported
    dsr.json PBO 0.0921. This reproduces the aggregation programmatically to make the
    number traceable. (Verdict unaffected -- both clear the 0.40 threshold.)

This script reads ONLY report CSVs already written by the /085 and /084 backtests --
it does not load OOS klines and computes no forward-looking quantity. It is a Phase-7/8
adjudication script, not a Phase-1-5 EDA script.

Run:  uv run python analysis/iteration_v3-085/roster_diff_oos.py
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

REPORTS = Path(__file__).resolve().parents[2] / "reports-v3"
ITER_085 = REPORTS / "iteration_v3-085"
ITER_084 = REPORTS / "iteration_v3-084"  # the cycle-3 EXPLORATION-MODE-REFERENCE

# 8h candle interval in milliseconds -- the unit the duration gap is measured in.
INTERVAL_MS = 480 * 60 * 1000

# brief Section 8.3(c) LOCKED falsifier threshold (candles)
SUBCHANNEL_C_THRESHOLD = 1.0


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


def task_a_roster_diff() -> None:
    print("=" * 72)
    print("TASK A -- OOS roster diff /085 vs /084 (the SUSPICIOUS sub-channel (c) check)")
    print("=" * 72)

    o85 = load_csv(ITER_085 / "out_of_sample" / "trades.csv")
    o84 = load_csv(ITER_084 / "out_of_sample" / "trades.csv")

    s85 = {trade_key(r): r for r in o85}
    s84 = {trade_key(r): r for r in o84}

    added = [s85[k] for k in s85 if k not in s84]
    removed = [s84[k] for k in s84 if k not in s85]
    common = [k for k in s85 if k in s84]

    print(f"/085 OOS trades: {len(o85)}    /084 OOS trades: {len(o84)}")
    print(f"common (identical trade-identity key): {len(common)}")
    print(f"/085 ADDS: {len(added)}    /085 REMOVES: {len(removed)}")

    mean_add = sum(duration_candles(r) for r in added) / len(added) if added else 0.0
    mean_rem = sum(duration_candles(r) for r in removed) / len(removed) if removed else 0.0
    gap = mean_add - mean_rem

    print()
    print(f"added   mean duration : {mean_add:.4f} candles")
    print(f"removed mean duration : {mean_rem:.4f} candles")
    print(f">>> added-minus-removed OOS mean-duration gap: {gap:+.4f} candles")
    print(f">>> LOCKED Section 8.3(c) falsifier threshold : +{SUBCHANNEL_C_THRESHOLD:.1f} candles")
    fires = gap > SUBCHANNEL_C_THRESHOLD
    print(f">>> SUSPICIOUS sub-channel (c): {'FIRES' if fires else 'does NOT fire'}")

    # robustness -- the gap must not be an artifact of the identity-key choice.
    print()
    print("robustness -- gap under alternative trade-identity keys:")
    for name, kf in [
        ("sym+dir+open+entry", trade_key),
        ("sym+open_time", lambda r: (r["symbol"], r["open_time"])),
        ("sym+dir+open", lambda r: (r["symbol"], r["direction"], r["open_time"])),
    ]:
        a = {kf(r): r for r in o85}
        b = {kf(r): r for r in o84}
        add = [a[k] for k in a if k not in b]
        rem = [b[k] for k in b if k not in a]
        ma = sum(duration_candles(r) for r in add) / len(add) if add else 0.0
        mr = sum(duration_candles(r) for r in rem) / len(rem) if rem else 0.0
        print(f"  key={name:20s}: added={len(add):3d} removed={len(rem):3d}  gap={ma - mr:+.4f}")

    # per-symbol decomposition -- texture for the diary (does NOT change the LOCKED call).
    print()
    print("per-symbol OOS roster-diff (texture; the LOCKED call is the aggregate gap):")
    for sym in ("BCHUSDT", "LDOUSDT", "TRXUSDT"):
        a = [r for r in added if r["symbol"] == sym]
        r_ = [r for r in removed if r["symbol"] == sym]
        ma = sum(duration_candles(x) for x in a) / len(a) if a else 0.0
        mr = sum(duration_candles(x) for x in r_) / len(r_) if r_ else 0.0
        wa = sum(weighted_pnl(x) for x in a)
        wr = sum(weighted_pnl(x) for x in r_)
        print(
            f"  {sym}: added={len(a):2d} (dur {ma:.2f}, wpnl {wa:+.2f})  "
            f"removed={len(r_):2d} (dur {mr:.2f}, wpnl {wr:+.2f})  dur-gap {ma - mr:+.2f}"
        )

    # exit-reason mix + net wpnl of the swap -- the regime-loading-direction texture.
    print()
    print("exit-reason mix:")
    print(f"  added  : {dict(Counter(r['exit_reason'] for r in added))}")
    print(f"  removed: {dict(Counter(r['exit_reason'] for r in removed))}")
    net = sum(weighted_pnl(r) for r in added) - sum(weighted_pnl(r) for r in removed)
    print(f"net OOS wpnl from the roster swap: {net:+.4f}  (added - removed)")
    print(
        "NOTE: OOS monthly Sharpe Δ vs /084 is -0.0468 (DOWN). The /076 regime-loading "
        "mechanism pushes OOS UP; /085's OOS went DOWN -- the substantive texture is the "
        "MILD form of the pattern. BUT the LOCKED 8.3(c) gate is numeric: gap > +1.0 -> "
        "SUSPICIOUS, no mechanism-argument downgrade (no post-hoc falsifier renegotiation)."
    )


def task_b_per_cell_pbo() -> None:
    print()
    print("=" * 72)
    print("TASK B -- per-cell-PBO aggregation reproduction (Critic Recommendation #2)")
    print("=" * 72)

    rows = load_csv(ITER_085 / "per_cell_pbo.csv")
    pbo_values = [float(r["pbo"]) for r in rows if r["pbo"] not in ("", "None")]

    flat_mean = sum(pbo_values) / len(pbo_values) if pbo_values else 0.0
    print(f"per_cell_pbo.csv rows with a numeric 'pbo': {len(pbo_values)}")
    print(f"flat unweighted mean of the 'pbo' column   : {flat_mean:.5f}")
    print("reported dsr.json 'pbo'                     : 0.09211")
    print(
        f">>> match: {'YES (exact to 4 dp)' if abs(flat_mean - 0.09210551) < 1e-5 else 'NO'}"
    )
    print(
        "CONVENTION: dsr.json's 'iter-v3/004 cross-cell mean' IS a flat unweighted "
        "arithmetic mean of the per-cell 'pbo' column -- no n_candles weighting, no "
        "subsetting. The Critic's ~0.102 was hand-arithmetic error over 127 floats. "
        "Verdict unaffected: 0.0921 << 0.40 PBO gate; frac_positive_paths 0.6444 > 0.55."
    )


def main() -> None:
    task_a_roster_diff()
    task_b_per_cell_pbo()
    print()
    print("=" * 72)
    print("PHASE 8 ADJUDICATION SUMMARY")
    print("=" * 72)
    print(
        "TASK A: added-minus-removed OOS mean-duration gap = +1.578 candles > +1.0 "
        "-> LOCKED Section 8.3(c) SUSPICIOUS sub-channel FIRES.\n"
        "  Disjunctive precedence SUSPICIOUS -> NEGATIVE -> PROMISING -> INERT: "
        "SUSPICIOUS is canonical (the INERT importance clause also fires but ranks "
        "below SUSPICIOUS).\n"
        "  FINAL CLASSIFICATION: SUSPICIOUS. NO-MERGE.\n"
        "TASK B: per-cell PBO 0.0921 reproduced exactly as a flat 127-row mean."
    )


if __name__ == "__main__":
    main()
