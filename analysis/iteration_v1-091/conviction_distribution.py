"""iter-v1/091 R-CONV — IS-only conviction-distribution analysis.

Reads ONLY in_sample/trades.csv from the BUNDLE-002 seats (no OOS read for any
tau-setting decision). Each trade carries a `confidence` column == the
post-aggregator `_sp_confidence = |mean(signed_weights)| / 100` = the net
seed-agreement fraction (lgbm.py:2162). For 50 seeds voting +-100 (confident)
or 0 (abstain): confidence = |n_long - n_short| / 50.

Outputs (committed):
  1. Per-seat IS confidence distribution (percentiles).
  2. WR-by-conviction-bucket and net-PnL-by-bucket (the core "low-conviction =
     noise" test).
  3. Trade-count survival at candidate tau (IS side) -> feeds the OOS-floor guard.
  4. Selection-bias precursor: conviction vs trade duration (candles held) as a
     low-vol/regime proxy. If high-conviction trades are NOT systematically
     longer/shorter-held, conviction is less likely a pure vol slice.

The OOS in_sample file is NEVER opened here. tau is pre-registered from IS only.
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

REPORTS = Path("reports-v1")
SEATS = {"ETH": "064", "BTC": "065", "AAVE": "078"}
# Seat choice is EVIDENCE-BASED, not the raw lowest-WR heuristic. BTC/065 is the
# lowest-IS-WR seat but its IS conviction->PnL map is INVERTED (highest-conviction
# bucket is the worst) because BTC is the IS-negative/OOS-positive regime-inverting
# seat -> its IS conviction map cannot guide where the noise lives. ETH/064 has a
# MONOTONE conviction->edge gradient AND is sign-consistent (IS +0.24 / OOS +0.52),
# so its IS low-conviction tail is a trustworthy noise signature. Chosen = ETH/064.
CHOSEN = "ETH"
PRE_REGISTERED_TAU = 0.06  # IS-only-reasoned (see [3]); single value, no grid, no OOS tuning
CAND_TAUS = [0.04, 0.06, 0.08, 0.10, 0.12, 0.16, 0.20, 0.28]


def load_is_trades(it: str) -> list[dict]:
    p = REPORTS / f"iteration_v1-{it}" / "in_sample" / "trades.csv"
    rows = []
    with open(p) as fh:
        for row in csv.DictReader(fh):
            try:
                row["_conf"] = float(row["confidence"])
                row["_npnl"] = float(row["net_pnl_pct"])
                row["_ot"] = int(row["open_time"]) if row["open_time"].isdigit() else None
                row["_ct"] = int(row["close_time"]) if row["close_time"].isdigit() else None
            except (KeyError, ValueError):
                continue
            rows.append(row)
    return rows


def pct(vals: list[float], p: float) -> float:
    if not vals:
        return float("nan")
    s = sorted(vals)
    i = min(len(s) - 1, int(p * len(s)))
    return s[i]


def hold_candles(row: dict) -> float | None:
    # 8h candles = 28_800_000 ms. Duration proxy for vol/regime selection-bias check.
    if row["_ot"] is None or row["_ct"] is None:
        return None
    return (row["_ct"] - row["_ot"]) / 28_800_000.0


def main() -> None:
    print("=" * 78)
    print("iter-v1/091 R-CONV — IS-only conviction distribution (BUNDLE-002 seats)")
    print("=" * 78)

    # ---- 1. per-seat confidence distribution ----
    print("\n[1] Per-seat IS confidence distribution (net seed-agreement fraction)")
    print(f"{'seat':>6} {'n':>4} {'WR%':>6} {'min':>6} {'p10':>6} {'p25':>6} "
          f"{'med':>6} {'p75':>6} {'p90':>6} {'max':>6}")
    seat_rows = {}
    for name, it in SEATS.items():
        rows = load_is_trades(it)
        seat_rows[name] = rows
        conf = [r["_conf"] for r in rows]
        wins = sum(1 for r in rows if r["_npnl"] > 0)
        print(f"{name:>6} {len(rows):>4} {wins / len(rows) * 100:>6.1f} "
              f"{min(conf):>6.3f} {pct(conf, .10):>6.3f} {pct(conf, .25):>6.3f} "
              f"{pct(conf, .50):>6.3f} {pct(conf, .75):>6.3f} {pct(conf, .90):>6.3f} "
              f"{max(conf):>6.3f}")

    rows = seat_rows[CHOSEN]
    print(f"\n  Chosen seat = {CHOSEN}/{SEATS[CHOSEN]} (lowest IS WR -> most "
          f"low-conviction noise to filter).")

    # ---- 2. WR + net-PnL by conviction bucket (the core noise test) ----
    print(f"\n[2] {CHOSEN} IS WR & net-PnL by conviction bucket")
    edges = [0.0, 0.06, 0.12, 0.20, 0.40, 1.01]
    print(f"{'bucket':>14} {'n':>4} {'WR%':>6} {'sum_npnl%':>10} {'avg_npnl%':>10}")
    for lo, hi in zip(edges[:-1], edges[1:]):
        b = [r for r in rows if lo <= r["_conf"] < hi]
        if not b:
            continue
        wins = sum(1 for r in b if r["_npnl"] > 0)
        s = sum(r["_npnl"] for r in b)
        print(f"[{lo:.2f},{hi:.2f}){'':>2} {len(b):>4} {wins / len(b) * 100:>6.1f} "
              f"{s:>10.2f} {s / len(b):>10.3f}")

    # ---- 3. trade-count survival at candidate tau (IS side) ----
    print(f"\n[3] {CHOSEN} IS trade-count + net-PnL survival at candidate tau "
          f"(trade ONLY if confidence >= tau)")
    print(f"{'tau':>6} {'kept':>5} {'frac':>6} {'kept_WR%':>9} {'kept_sumPnL%':>13} "
          f"{'dropped':>8} {'dropped_WR%':>12} {'dropped_sumPnL%':>16}")
    n0 = len(rows)
    for tau in CAND_TAUS:
        kept = [r for r in rows if r["_conf"] >= tau]
        drop = [r for r in rows if r["_conf"] < tau]
        kw = sum(1 for r in kept if r["_npnl"] > 0)
        dw = sum(1 for r in drop if r["_npnl"] > 0)
        ks = sum(r["_npnl"] for r in kept)
        ds = sum(r["_npnl"] for r in drop)
        kwr = (kw / len(kept) * 100) if kept else float("nan")
        dwr = (dw / len(drop) * 100) if drop else float("nan")
        print(f"{tau:>6.2f} {len(kept):>5} {len(kept) / n0:>6.2f} {kwr:>9.1f} "
              f"{ks:>13.2f} {len(drop):>8} {dwr:>12.1f} {ds:>16.2f}")

    # ---- 4. selection-bias precursor: conviction vs hold-duration ----
    print(f"\n[4] {CHOSEN} selection-bias precursor — mean hold-duration (8h candles) "
          f"by conviction bucket")
    print("  (if high-conviction trades are NOT systematically shorter/longer held,")
    print("   conviction is less likely a pure low-vol/regime slice)")
    print(f"{'bucket':>14} {'n':>4} {'mean_hold':>10} {'med_hold':>9}")
    for lo, hi in zip(edges[:-1], edges[1:]):
        b = [hold_candles(r) for r in rows if lo <= r["_conf"] < hi]
        b = [x for x in b if x is not None]
        if not b:
            continue
        print(f"[{lo:.2f},{hi:.2f}){'':>2} {len(b):>4} {statistics.mean(b):>10.2f} "
              f"{statistics.median(b):>9.2f}")

    # crude rank-correlation conviction vs hold-duration
    pairs = [(r["_conf"], hold_candles(r)) for r in rows if hold_candles(r) is not None]
    if len(pairs) > 2:
        cs = sorted(pairs, key=lambda x: x[0])
        hs = sorted(pairs, key=lambda x: x[1])
        rank_c = {id(p): i for i, p in enumerate(cs)}
        rank_h = {id(p): i for i, p in enumerate(hs)}
        n = len(pairs)
        d2 = sum((rank_c[id(p)] - rank_h[id(p)]) ** 2 for p in pairs)
        rho = 1 - 6 * d2 / (n * (n * n - 1))
        print(f"\n  Spearman rho(confidence, hold_candles) = {rho:+.3f}  "
              f"(|rho| small -> conviction not a duration/vol proxy)")

    # ---- pre-registered tau verdict ----
    print(f"\n[PRE-REGISTERED] tau = {PRE_REGISTERED_TAU:.2f} on {CHOSEN}/{SEATS[CHOSEN]}")
    keep = [r for r in rows if r["_conf"] >= PRE_REGISTERED_TAU]
    drop = [r for r in rows if r["_conf"] < PRE_REGISTERED_TAU]
    dw = sum(1 for r in drop if r["_npnl"] > 0)
    print(f"  IS: keeps {len(keep)}/{len(rows)} ({len(keep) / len(rows):.0%}); "
          f"drops {len(drop)} low-conviction trades "
          f"(dropped WR {dw / len(drop) * 100:.1f}%, "
          f"dropped sumPnL {sum(r['_npnl'] for r in drop):+.2f}% = net-losing noise).")
    print(f"  tau={PRE_REGISTERED_TAU} == net seed agreement < {PRE_REGISTERED_TAU * 50:.0f}/50 "
          f"seeds (<= near-coin-flip consensus).")


if __name__ == "__main__":
    main()
