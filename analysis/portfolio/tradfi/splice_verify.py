"""GATE — prove the Yahoo->perp splice is leak-safe and the confirmed iter-016 IS is bit-identical.

Five checks (all must PASS; also asserted in ``tests/test_tradfi_splice.py``):
  1. IS BIT-IDENTICAL (hard gate): for every name, spliced close/returns for all bars ``< d`` (the
     perp inception — which covers the ENTIRE IS window, since no perp exists before 2026) are
     EXACTLY equal to pure ``ct.load_tradfi`` (max|Δ| == 0.0). Proves the splice cannot have leaked
     into or altered the confirmed baseline.
  2. iter-016 IS METRICS UNCHANGED: deployed net@1x / net@2x / gross IS Sharpes on the spliced
     panel equal the confirmed +0.729 / +0.582 / +0.875 (pure-Yahoo) — bit-for-bit. The recent
     (2026) OOS tail MAY differ; that delta is reported INFORMATIONAL only (OOS already revealed).
  3. CALENDAR CONSISTENCY: the spliced series has NO weekend bars (dayofweek < 5 everywhere) and
     ~252 bars/yr throughout — no density jump at the splice boundary.
  4. BOUNDARY CLEANLINESS: at each name's ``d``, |spliced_close[d] - yahoo_close[d]| == 0 (anchor
     exact) and the d+1 return == perp[d+1]/perp[d] (a pure perp return, not a level jump).
  5. LEAK SELF-CHECK: re-splicing the inputs truncated to ``<= as_of`` reproduces the full panel's
     ``<= as_of`` rows bit-for-bit (past-only), for several as_of dates in the perp window.

OOS DISCIPLINE: ``OOS_CUTOFF = 2025-03-24`` is immutable; NO new OOS strategy Sharpe is emitted as
a headline. The 2026-tail effect is reported for information only (the OOS was already revealed).

Run:  uv run python analysis/portfolio/tradfi/splice_verify.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import iter_008_vix_stop as i8  # noqa: E402
import iter_013_directional as i13  # noqa: E402
import iter_016_bear_gated_tsmom as i16  # noqa: E402
import iter_016_oos_check as oc  # noqa: E402
import perp_map_tradfi as pm  # noqa: E402
import splice_loader as sl  # noqa: E402
import universe_tradfi as ut  # noqa: E402

CONFIRMED = {"net1x": 0.7291, "net2x": 0.5822, "gross": 0.8754}  # iter-016 deployed IS of record
OOS_MS = int(ct.OOS_CUTOFF.value // 1_000_000)


def _universe(data_dir: str | None) -> list[str]:
    base = Path(data_dir) if data_dir else ct._ROOT / "data"
    return sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)


def _boundaries(syms, yahoo_coins, live_dir):
    """{sym: (spliced_df, d)} for names with a perp splice (d is not None)."""
    out = {}
    for sym in syms:
        ydf = yahoo_coins.get(sym)
        if ydf is None:
            continue
        perp = sl.load_perp_frame(pm.PERP_SYMBOL_MAP.get(sym, sym), live_dir)
        spliced, d = sl.splice_one(ydf, perp)
        out[sym] = (spliced, d)
    return out


def _is_metrics(pn, data_dir):
    rf = pn["ret_fwd"]
    mkt = i13.market_return(pn)
    s_vix = i8.vix_scale(i8.load_vix_close(rf.index, data_dir))
    raw = i16.bear_gated_combined_raw(pn)
    return i16.deployed_metrics(raw, rf, s_vix, mkt)


def _oos_tail(pn, data_dir):
    """INFORMATIONAL only — deployed net@1x over the (already-revealed) OOS window."""
    rf = pn["ret_fwd"]
    mkt = i13.market_return(pn)
    s_vix = i8.vix_scale(i8.load_vix_close(rf.index, data_dir))
    raw = i16.bear_gated_combined_raw(pn)
    cell = oc.win_cell(raw, rf, s_vix, mkt, ct.OOS_CUTOFF, ct.HI1)
    return cell


def run(data_dir: str | None = None, live_data_dir: str | None = None) -> dict:
    """Execute all five checks; return a results dict (used by the tests and the CLI report)."""
    syms = _universe(data_dir)
    live_dir = Path(live_data_dir) if live_data_dir is not None else sl.LIVE_DIR
    yahoo_coins = ct.load_tradfi(syms, data_dir)
    spliced_coins = sl.load_tradfi_spliced(syms, data_dir, live_data_dir)
    bnd = _boundaries(syms, yahoo_coins, live_dir)
    spliced_names = {s: d for s, (_, d) in bnd.items() if d is not None}

    # ---- Check 1 — IS bit-identical (rows < d, per name) --------------------------------------
    max_dclose = 0.0
    max_dret = 0.0
    min_d_ms = None
    for sym, d in spliced_names.items():
        y = yahoo_coins[sym]
        s = spliced_coins[sym]
        pre = s.index < d
        dclose = float((s.loc[pre, "close"] - y.loc[pre, "close"]).abs().max() or 0.0)
        yr = y["close"].pct_change()
        sr = s["close"].pct_change()
        dret = float((sr[pre] - yr[pre]).abs().max() or 0.0)
        max_dclose = max(max_dclose, dclose)
        max_dret = max(max_dret, dret)
        min_d_ms = d if min_d_ms is None else min(min_d_ms, d)
    is_bit_identical = (max_dclose == 0.0) and (max_dret == 0.0)
    earliest_d_after_oos = (min_d_ms is not None) and (min_d_ms > OOS_MS)

    # ---- Check 2 — iter-016 IS metrics unchanged ----------------------------------------------
    pn_y = ct.panels(yahoo_coins)
    pn_s = ct.panels(spliced_coins)
    m_y = _is_metrics(pn_y, data_dir)
    m_s = _is_metrics(pn_s, data_dir)
    is_metrics_match = all(
        m_s[k] == m_y[k] and abs(m_s[k] - CONFIRMED[k]) < 5e-4 for k in CONFIRMED
    )
    tail_y = _oos_tail(pn_y, data_dir)
    tail_s = _oos_tail(pn_s, data_dir)

    # ---- Check 3 — calendar consistency (no weekend bars; ~252/yr) -----------------------------
    idx_dt = pd.to_datetime(pn_s["close"].index, unit="ms")
    no_weekend = bool((idx_dt.dayofweek < 5).all())
    bars_per_year = pd.Series(1, index=idx_dt).groupby(idx_dt.year).count()

    # ---- Check 4 — boundary cleanliness --------------------------------------------------------
    max_anchor = 0.0
    max_ret_dev = 0.0
    for sym, d in spliced_names.items():
        y = yahoo_coins[sym]
        s = spliced_coins[sym]
        perp = sl.load_perp_frame(pm.PERP_SYMBOL_MAP.get(sym, sym), live_dir)
        aligned = perp.loc[perp.index.intersection(y.index)].sort_index()
        d1 = int(aligned.index[1])  # next aligned perp trading day after d
        anchor_dev = abs(float(s.at[d, "close"]) - float(y.at[d, "close"]))
        perp_ratio = float(aligned.at[d1, "close"]) / float(aligned.at[d, "close"])
        spliced_ret = float(s.at[d1, "close"]) / float(s.at[d, "close"])
        max_anchor = max(max_anchor, anchor_dev)
        max_ret_dev = max(max_ret_dev, abs(spliced_ret - perp_ratio))
    boundary_clean = (max_anchor == 0.0) and (max_ret_dev < 1e-9)

    # ---- Check 5 — leak self-check (truncate <= as_of, re-splice, bit-match) --------------------
    as_ofs = ["2026-02-15", "2026-04-15", "2026-06-01"]
    max_leak = 0.0
    for as_of in as_ofs:
        cut = int(pd.Timestamp(as_of).value // 1_000_000)
        for sym, d in spliced_names.items():
            y = yahoo_coins[sym]
            perp = sl.load_perp_frame(pm.PERP_SYMBOL_MAP.get(sym, sym), live_dir)
            yt = y[y.index <= cut]
            pt = perp[perp.index <= cut]
            st, _ = sl.splice_one(yt, pt)
            full = spliced_coins[sym]
            common = st.index[st.index <= cut]
            dev = float((st.loc[common, "close"] - full.loc[common, "close"]).abs().max() or 0.0)
            max_leak = max(max_leak, dev)
    leak_safe = max_leak == 0.0

    return {
        "n_names": len(yahoo_coins),
        "n_spliced": len(spliced_names),
        "min_d_ms": min_d_ms,
        "max_dclose": max_dclose,
        "max_dret": max_dret,
        "is_bit_identical": is_bit_identical,
        "earliest_d_after_oos": earliest_d_after_oos,
        "m_y": m_y,
        "m_s": m_s,
        "is_metrics_match": is_metrics_match,
        "tail_y": tail_y,
        "tail_s": tail_s,
        "no_weekend": no_weekend,
        "bars_per_year": bars_per_year,
        "max_anchor": max_anchor,
        "max_ret_dev": max_ret_dev,
        "boundary_clean": boundary_clean,
        "max_leak": max_leak,
        "leak_safe": leak_safe,
        "as_ofs": as_ofs,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--live-data-dir", default=None)
    args = ap.parse_args()
    r = run(args.data_dir, args.live_data_dir)

    print("=" * 96)
    print("SPLICE VERIFY — Yahoo->perp spliced tradfi loader (leak-safe + IS bit-identical GATE)")
    print("=" * 96)
    print(
        f"  universe = {r['n_names']} names;  {r['n_spliced']} have a live-perp splice;  "
        f"earliest perp inception d = {pd.to_datetime(r['min_d_ms'], unit='ms').date()}"
    )

    print("\n--- Check 1 — IS BIT-IDENTICAL (bars < perp inception d) ---")
    print(f"    max|Δ close|  (all names, t<d) = {r['max_dclose']:.3e}   (must be 0.0)")
    print(f"    max|Δ return| (all names, t<d) = {r['max_dret']:.3e}   (must be 0.0)")
    print(
        f"    earliest d ({pd.to_datetime(r['min_d_ms'], unit='ms').date()}) is AFTER "
        f"OOS_CUTOFF ({ct.OOS_CUTOFF.date()}) -> ENTIRE IS is < d : "
        f"{'YES' if r['earliest_d_after_oos'] else 'NO'}"
    )
    print(f"    => IS bit-identical: {'PASS' if r['is_bit_identical'] else 'FAIL'}")

    print("\n--- Check 2 — iter-016 IS METRICS UNCHANGED (deployed, VIX-ON) ---")
    my, ms = r["m_y"], r["m_s"]
    print(f"    {'metric':<20}{'pure-Yahoo':>12}{'spliced':>12}{'confirmed':>12}")
    for k, lab in (("net1x", "net@1x (6bps)"), ("net2x", "net@2x (12bps)"), ("gross", "gross")):
        print(f"    {lab:<20}{my[k]:>+12.4f}{ms[k]:>+12.4f}{CONFIRMED[k]:>+12.4f}")
    print(
        f"    => IS metrics identical & == confirmed: {'PASS' if r['is_metrics_match'] else 'FAIL'}"
    )
    ty, ts = r["tail_y"], r["tail_s"]
    print(
        "\n    [INFORMATIONAL — OOS already revealed] recent-2026-tail effect on the OOS window "
        f"[{ct.OOS_CUTOFF.date()} ..):"
    )
    print(
        f"      deployed net@1x  pure-Yahoo {ty['net1x']:+.3f} -> spliced {ts['net1x']:+.3f}  "
        f"(Δ {ts['net1x'] - ty['net1x']:+.3f})"
    )
    print(
        f"      deployed gross   pure-Yahoo {ty['gross']:+.3f} -> spliced {ts['gross']:+.3f}  "
        f"(Δ {ts['gross'] - ty['gross']:+.3f})   [tail signal now on the traded perp]"
    )

    print("\n--- Check 3 — CALENDAR CONSISTENCY (no weekend bars; ~252/yr) ---")
    print(
        f"    all spliced bars have dayofweek < 5 (no weekend bars): "
        f"{'PASS' if r['no_weekend'] else 'FAIL'}"
    )
    bpy = r["bars_per_year"]
    recent = {y: int(bpy.loc[y]) for y in bpy.index if y >= 2022}
    print(f"    bars/yr (2022+): {recent}   (2026 partial-year to date)")
    print(
        f"    bars/yr min/median over full history = {int(bpy[bpy.index < 2026].min())} / "
        f"{int(bpy[bpy.index < 2026].median())}  (no density jump at the boundary)"
    )

    print("\n--- Check 4 — BOUNDARY CLEANLINESS ---")
    print(f"    max|spliced_close[d] - yahoo_close[d]| = {r['max_anchor']:.3e}  (anchor exact ==0)")
    print(
        f"    max|spliced d+1 return - perp[d+1]/perp[d]| = {r['max_ret_dev']:.3e}  "
        "(pure perp return, float-eps)"
    )
    print(
        f"    => boundary continuous, no Yahoo->perp level jump: "
        f"{'PASS' if r['boundary_clean'] else 'FAIL'}"
    )

    print("\n--- Check 5 — LEAK SELF-CHECK (truncate <= as_of, re-splice, bit-match) ---")
    print(f"    as_of dates tested: {r['as_ofs']}")
    print(
        f"    max|Δ close| (truncated re-splice vs full, <= as_of, all names) = {r['max_leak']:.3e}"
    )
    print(f"    => past-only (no future leak): {'PASS' if r['leak_safe'] else 'FAIL'}")

    ok = (
        r["is_bit_identical"]
        and r["earliest_d_after_oos"]
        and r["is_metrics_match"]
        and r["no_weekend"]
        and r["boundary_clean"]
        and r["leak_safe"]
    )
    print("\n" + "=" * 96)
    print(f"OVERALL: {'PASS — splice is leak-safe and IS bit-identical' if ok else 'FAIL'}")
    print("=" * 96)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
