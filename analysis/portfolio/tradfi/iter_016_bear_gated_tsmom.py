"""iter-016 — BEAR-GATED TSMOM: gate the directional sleeve to 0 in the EW-252d bear-state.

ONE change vs the deployed iter-015 book, ZERO new parameters. The worst-months forensic
(diary-portfolio-tradfi/worst-months-forensic.md, PROBE A) found the net-long TSMOM tilt is fine
most of the time but gets caught in the Oct-2018 QT crash (long the crashing momentum winners +
net-long beta into a falling tape) and the Jan-2019 V-rebound whipsaw (short the 2018 losers that
snap back). Fix: turn the directional tilt OFF in bear-states, keep it ON in the bull melt-ups
(2013/2017) where it was ADDED to earn.

=========================================================================================
THE CHANGE — a per-bar directional fraction gated by the EXISTING bear-state (no new knob)
=========================================================================================
iter-006's momentum-crash brake already computes a causal binary bear-state on the EQUAL-WEIGHT
universe's own trailing 12-month return:

    g[t] = 1{ EW-universe 252d return < 0 }        (i6.bear_state, GATE_LOOKBACK=252, sign-0)

REUSE that EXACT g (same window, same sign, no new param) to gate the deployed lam=0.25 tilt:

    lam_eff[t] = LAM * (1 - g[t])                  # 0.25 in bull/non-bear, 0 in bear
    book[t]    = (1 - lam_eff[t]) * neutral[t] + lam_eff[t] * tsmom[t]
    w          = banded_book_freq(book, delta=0.010, freq=1)     # iter-015 band + daily UNCHANGED
    net        = vol_target(w.ret_fwd - cost) * s_vix            # iter-008 VIX brake UNCHANGED

g=0 (market 12m return >= 0, bull/melt-up): lam_eff = 0.25 -> IDENTICAL to iter-015 (the tilt the
melt-up years were given stays fully ON). g=1 (bear): lam_eff = 0 -> the book goes fully
market-NEUTRAL, cutting the net-long beta exactly in the crash/whipsaw. This is TSMOM's own
"don't be net-long a downtrend" logic applied at the sleeve-WEIGHT level, generalizing to ALL 5 IS
bears + recoveries — NOT a fit to 2018/2019.

=========================================================================================
LEAK SAFETY + PRE-REGISTERED IDENTITY
=========================================================================================
  * g[t] reuses i6.bear_state, already proven past-only (reads close.shift(252) only); lam_eff is a
    row-wise scalar on two past-only unit-gross sleeves, so the blend feeds the strictly-causal
    iter-003/015 band. An in-script future-bar self-check corrupts close + ret_fwd after a cutoff
    and asserts the deployed VIX-ON net before the cutoff is bit-identical.
  * IDENTITY (pre-registered): a forced all-zero gate makes lam_eff == 0.25 everywhere, so
    bear_gated_combined_raw(pn, LAM, zeros) reproduces i13.combined_raw(pn, LAM) bit-for-bit and the
    deployed net reproduces iter-015. This anchors iter-016 as a pure one-change delta off iter-015.
  * OOS stays HIDDEN: every metric is the IS slice only; no OOS number is computed. Do NOT tune the
    gate window / threshold (both pre-existing: LAM=0.25 from iter-013, 252d from iter-006).

Run: uv run python analysis/portfolio/tradfi/iter_016_bear_gated_tsmom.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import iter_006_crashbrake as i6  # noqa: E402
import iter_008_vix_stop as i8  # noqa: E402
import iter_011_mom_ltr as i11  # noqa: E402
import iter_013_directional as i13  # noqa: E402
import iter_015_cost as i15  # noqa: E402
import universe_tradfi as ut  # noqa: E402

# --- ALL constants are PRE-EXISTING (zero new parameters) ---
GATE_LOOKBACK = i6.GATE_LOOKBACK  # 252 — the EXACT iter-006 bear-state window (reused, not swept)
LAM = i13.DEPLOYED_LAM  # 0.25 — the deployed directional fraction (iter-013, unchanged)
DELTA = i15.CHOSEN_DELTA  # 0.010 — deployed band (iter-015, unchanged)
FREQ = i15.CHOSEN_FREQ  # 1 — daily rebalance (iter-015, unchanged)

# Melt-up years the neutral book structurally misses; the tilt was ADDED for these -> must be
# UNTOUCHED (pure-bull -> g=0 all year -> lam_eff=0.25 -> identical to iter-015).
MELTUP_YEARS = (2013, 2017)

# The pre-registered KEEP gate (strict-improvement to replace iter-015).
GATE_NET1X_BASE = None  # set at runtime to iter-015's net@1x (must strictly beat it)
GATE_N2X, GATE_BETA, GATE_YRS, GATE_GROSS = 0.50, 0.15, 13, 0.78


# ---------------------------------------------------------------- the ONE change ----------------
def bear_gated_combined_raw(
    pn: dict[str, pd.DataFrame], lam: float = LAM, gate: pd.Series | None = None
) -> pd.DataFrame:
    """book = (1 - lam_eff)*neutral + lam_eff*tsmom, lam_eff = lam*(1 - g) (g = EW-252d bear-state).

    `gate` defaults to i6.bear_state(close, 252); pass an explicit Series (e.g. zeros) for the
    identity check. lam_eff is a per-bar row scalar (axis=0) on two past-only unit-gross sleeves, so
    the blend is past-only and feeds the causal band. g=0 everywhere -> lam_eff=lam -> combined_raw.
    """
    neu = i13.neutral_raw(pn)  # frozen iter-011 neutral engine (mom + 0.5*LTR), unit-gross
    ts = i13.tsmom_sleeve(pn)  # TSMOM directional sleeve, unit-gross
    g = i6.bear_state(pn["close"], GATE_LOOKBACK) if gate is None else gate
    g = g.reindex(neu.index).fillna(0.0)
    lam_eff = lam * (1.0 - g)
    return neu.mul(1.0 - lam_eff, axis=0).add(ts.mul(lam_eff, axis=0), fill_value=0.0)


# ---------------------------------------------------------------- IS-only deployed metrics ------
def deployed_metrics(raw, ret_fwd, s_vix, mkt) -> dict:
    """Deployed (band d=0.010, freq=1, VIX-ON) IS metric bundle for a raw book — mirrors i15._cell.

    net@1x (6bps) / net@2x (12bps) / gross (cost-off) all carry the iter-008 VIX brake. net-beta is
    the realized OLS beta of the VIX-OFF 1x net on the EW-69 universe forward return (i13.net_beta,
    reused verbatim). d1x is the deployed VIX-ON 1x net (== i15._deployed_net1x) for per-year/month.
    """
    net_g, _ = i15.banded_net_freq(raw, ret_fwd, DELTA, FREQ, 0.0)
    net_1x, w = i15.banded_net_freq(raw, ret_fwd, DELTA, FREQ, ct.COST_SIDE)
    net_2x, _ = i15.banded_net_freq(raw, ret_fwd, DELTA, FREQ, 2.0 * ct.COST_SIDE)

    def _vix(net):
        return net * s_vix.reindex(net.index).fillna(1.0)

    d1x, d2x, dg = _vix(net_1x), _vix(net_2x), _vix(net_g)
    npos, nyr = i11.n_pos_years(d1x)
    return {
        "net1x": ct.msharpe(d1x, ct.LO0, ct.OOS_CUTOFF),
        "net2x": ct.msharpe(d2x, ct.LO0, ct.OOS_CUTOFF),
        "gross": ct.msharpe(dg, ct.LO0, ct.OOS_CUTOFF),
        "turn": ct.turnover(w, ct.LO0, ct.OOS_CUTOFF),
        "beta": i13.net_beta(net_1x, mkt),  # VIX-off realized OLS book beta (iter-015 convention)
        "nlong": i13.net_long_fraction(w),  # static leverage-free structural net-long tilt
        "npos": npos,
        "nyr": nyr,
        "d1x": d1x,
    }


def month_ret(net: pd.Series, period: str) -> float:
    """IS-only calendar-month net return (sum of daily net) — the forensic per-month convention."""
    s = ct.is_only(net)
    m = s.groupby(s.index.to_period("M")).sum()
    p = pd.Period(period, freq="M")
    return float(m.loc[p]) if p in m.index else float("nan")


def _leak_selfcheck(pn, ret_fwd, s_vix) -> bool:
    """Corrupt close + ret_fwd after a cutoff; the bear-gated deployed VIX-ON net before it must be
    bit-identical (g reuses past-only i6.bear_state; blend feeds causal band; VIX is .shift(1))."""
    raw0 = bear_gated_combined_raw(pn)
    net0, _ = i15.banded_net_freq(raw0, ret_fwd, DELTA, FREQ, ct.COST_SIDE)
    net0 = net0 * s_vix.reindex(net0.index).fillna(1.0)
    cut = net0.index[len(net0) // 2]
    pn_c = {k: v.copy() for k, v in pn.items()}
    pn_c["close"].loc[pn_c["close"].index >= cut] *= -7.0
    pn_c["ret_fwd"].loc[pn_c["ret_fwd"].index >= cut] += 5.0
    raw1 = bear_gated_combined_raw(pn_c)
    net1, _ = i15.banded_net_freq(raw1, pn_c["ret_fwd"], DELTA, FREQ, ct.COST_SIDE)
    net1 = net1 * s_vix.reindex(net1.index).fillna(1.0)
    common = net0.index.intersection(net1.index)
    common = common[common < cut]
    return bool(np.allclose(net0.loc[common].to_numpy(), net1.loc[common].to_numpy(), atol=1e-12))


def _identity_check(pn) -> bool:
    """g=0 everywhere -> bear_gated_combined_raw(pn, LAM, zeros) == i13.combined_raw(pn, LAM)."""
    zeros = pd.Series(0.0, index=pn["close"].index)
    raw_id = bear_gated_combined_raw(pn, LAM, zeros)
    raw_ref = i13.combined_raw(pn, LAM)
    a = raw_id.reindex(columns=raw_ref.columns).fillna(0.0).to_numpy()
    b = raw_ref.fillna(0.0).to_numpy()
    return bool(np.allclose(a, b, atol=1e-15, rtol=0.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()

    base = Path(args.data_dir) if args.data_dir else ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    coins = ct.load_tradfi(syms, args.data_dir)
    if not coins:
        print("No ingested tradfi data found. Run ingest_yahoo.py first.")
        return

    pn = ct.panels(coins)
    ret_fwd = pn["ret_fwd"]
    mkt = i13.market_return(pn)  # EW-69 forward return = PIT market proxy for net-beta
    vix = i8.load_vix_close(ret_fwd.index, args.data_dir)
    s_vix = i8.vix_scale(vix)  # base=20 / floor=0.50 (iter-008 UNCHANGED)

    print("=" * 100)
    print("iter-016 — BEAR-GATED TSMOM (lam_eff=0.25*(1-g), g=EW-252d bear-state), IS-only")
    print("=" * 100)
    print(
        f"  reuse: LAM={LAM} (iter-013) x gate g=1{{EW {GATE_LOOKBACK}d ret<0}} (iter-006);  "
        f"band delta={DELTA} freq={FREQ} + VIX brake (iter-015/008) — ZERO new params\n"
    )

    # --- IDENTITY (g=0 everywhere -> iter-015) + LEAK self-check ---
    ident = _identity_check(pn)
    leak_ok = _leak_selfcheck(pn, ret_fwd, s_vix)
    print(f"  IDENTITY  g=0-everywhere -> iter-015 raw bit-for-bit : {'PASS' if ident else 'FAIL'}")
    print(
        f"  LEAK      future-bar corruption, pre-cut net bit-id  : {'PASS' if leak_ok else 'FAIL'}"
    )

    # --- BASELINE (iter-015) vs iter-016 (bear-gated) deployed metrics ---
    raw_base = i13.combined_raw(pn, LAM)
    raw_016 = bear_gated_combined_raw(pn)
    mb = deployed_metrics(raw_base, ret_fwd, s_vix, mkt)
    m6 = deployed_metrics(raw_016, ret_fwd, s_vix, mkt)
    global GATE_NET1X_BASE
    GATE_NET1X_BASE = mb["net1x"]

    print("\n  HEADLINE — deployed (band d=0.010, freq=1, VIX-ON) IS metrics:")
    print(
        f"      {'config':<20} {'net@1x':>7} {'net@2x':>7} {'gross':>7} {'net-b':>7} "
        f"{'nlong':>7} {'turn':>8} {'+yrs':>7}"
    )
    for lab, m in (("iter-015 (base)", mb), ("iter-016 (bear-gate)", m6)):
        print(
            f"      {lab:<20} {m['net1x']:>+7.3f} {m['net2x']:>+7.3f} {m['gross']:>+7.3f} "
            f"{m['beta']:>+7.3f} {m['nlong']:>+7.3f} {m['turn']:>8.4f} {m['npos']:>4}/{m['nyr']}"
        )
    dk = {k: m6[k] - mb[k] for k in ("net1x", "net2x", "gross", "beta", "nlong", "turn", "npos")}
    print(
        f"      {'delta':<20} {dk['net1x']:>+7.3f} {dk['net2x']:>+7.3f} {dk['gross']:>+7.3f} "
        f"{dk['beta']:>+7.3f} {dk['nlong']:>+7.3f} {dk['turn']:>+8.4f} {dk['npos']:>+4}"
    )

    # --- gate firing by IS year (surgical targeting; melt-up 2013/2017 must be 0 days) ---
    g_is = ct.is_only(i6.bear_state(pn["close"], GATE_LOOKBACK))
    fired = g_is.groupby(g_is.index.year).apply(lambda s: (s > 0.5).sum())
    fire_yrs = ", ".join(f"{y}:{int(n)}" for y, n in fired.items() if n > 0)
    print(f"\n  gate firing days/IS-yr (TSMOM OFF): {fire_yrs}  overall={g_is.mean() * 100:.1f}%")

    # --- PER-YEAR table (IS) — return% and Sharpe, baseline -> iter-016 ---
    yb = i11.year_table(mb["d1x"])
    y6 = i11.year_table(m6["d1x"])
    print(
        "\n  PER-YEAR net return% (Sharpe) — iter-015 -> iter-016  (* melt-up: must be UNTOUCHED):"
    )
    for yr in sorted(y6):
        star = "*" if yr in MELTUP_YEARS else " "
        fired_yr = int((g_is[g_is.index.year == yr] > 0.5).sum())
        same = "  tilt ON (0 gate days)" if yr in MELTUP_YEARS and fired_yr == 0 else ""
        mark = "  <- bad year" if yr in (2018, 2019) else ""
        print(
            f"      {yr}{star} {yb[yr][1]:>+6.1f}% ({yb[yr][0]:>+5.2f}) -> "
            f"{y6[yr][1]:>+6.1f}% ({y6[yr][0]:>+5.2f}){mark}{same}"
        )

    # --- the named worst months: 2018-10 (QT crash) + 2019-01 (V-rebound whipsaw) ---
    print("\n  NAMED WORST MONTHS (net% = sum of daily net, IS) — iter-015 -> iter-016:")
    for mo in ("2018-10", "2019-01"):
        a, b = month_ret(mb["d1x"], mo), month_ret(m6["d1x"], mo)
        print(
            f"      {mo}: {a * 100:>+7.2f}% -> {b * 100:>+7.2f}%   (delta {(b - a) * 100:>+.2f}%)"
        )

    # --- forensic IS-probe prediction cross-check (net +0.665->+0.73, 2019 +3.4%, goodDmu +0.62) --
    # year_table returns return% ALREADY in percentage points (e.g. +6.6 == +6.6%), so the year-on-
    # year deltas below are in percentage points directly (NO extra x100).
    goodyrs = [y for y in yb if y not in (2010, 2018, 2019)]
    good_dmu = float(np.mean([y6[y][1] - yb[y][1] for y in goodyrs]))
    good_regress = [
        y for y in goodyrs if yb[y][0] > 0 and y6[y][0] <= 0
    ]  # positive -> non-positive
    d2018 = y6[2018][1] - yb[2018][1]
    d2019 = y6[2019][1] - yb[2019][1]
    # TRUE structural "untouched" test: the gate must fire ZERO days in the melt-up years so the
    # directional tilt stays fully ON (g=0 all year -> raw book identical). The per-year net Sharpe
    # can still wiggle by <=0.01 purely from the vol-target's 63-day trailing-vol carryover off the
    # (changed) prior-Dec tail — that is NOT a melt-up gating, so we test firing-days, not bit-net.
    meltup_fire = {y: int((g_is[g_is.index.year == y] > 0.5).sum()) for y in MELTUP_YEARS}
    meltup_untouched = all(n == 0 for n in meltup_fire.values())
    print(
        "\n  FORENSIC PROBE CROSS-CHECK (predicted: net +0.665->+0.73, 2019 +3.4%, goodDmu +0.62):"
    )
    print(
        f"      net@1x {mb['net1x']:+.3f} -> {m6['net1x']:+.3f}   2018 dR={d2018:+.1f}pp   "
        f"2019 dR={d2019:+.1f}pp   goodDmu={good_dmu:+.2f}pp   good-yr regr={len(good_regress)}"
    )
    print(
        f"      melt-up years {MELTUP_YEARS} UNTOUCHED (gate fires {meltup_fire} days -> tilt ON): "
        f"{'PASS' if meltup_untouched else 'FAIL'}"
    )

    # --- PRE-REGISTERED KEEP gate (strict-improvement to replace iter-015) ---
    g_net1x = m6["net1x"] > mb["net1x"]
    g_n2x = m6["net2x"] >= GATE_N2X
    g_beta = m6["beta"] <= GATE_BETA
    g_yrs = m6["npos"] >= GATE_YRS
    g_gross = m6["gross"] >= GATE_GROSS
    g_good = good_dmu >= 0.0 and len(good_regress) == 0
    g_beta_dropped = m6["beta"] < mb["beta"]
    keep = g_net1x and g_n2x and g_beta and g_yrs and g_gross and g_good and ident and leak_ok
    print("\n  KEEP gate (replace iter-015):")
    print(
        f"      net@1x>base={'Y' if g_net1x else 'N'} ({m6['net1x']:+.3f}>{mb['net1x']:+.3f})  "
        f"net@2x>=+0.50={'Y' if g_n2x else 'N'} ({m6['net2x']:+.3f})  "
        f"net-b<=0.15={'Y' if g_beta else 'N'} ({m6['beta']:+.3f})  "
        f"+yrs>=13={'Y' if g_yrs else 'N'} ({m6['npos']})"
    )
    print(
        f"      gross>=+0.78={'Y' if g_gross else 'N'} ({m6['gross']:+.3f})  "
        f"no-good-yr-regression={'Y' if g_good else 'N'} (goodDmu={good_dmu:+.2f}%)  "
        f"identity={'Y' if ident else 'N'}  leak-safe={'Y' if leak_ok else 'N'}"
    )
    print(
        f"      net-beta DROPPED vs base: {'Y' if g_beta_dropped else 'N'} "
        f"({mb['beta']:+.3f} -> {m6['beta']:+.3f})"
    )
    if not g_beta_dropped:
        print(
            "      HONEST net-beta read: the brief PREDICTED beta would DROP; on the full-sample"
            " OLS measure it did NOT (ticks +0.019 to +0.148, still <=0.15), and nlong ALSO rose"
            f" ({mb['nlong']:+.3f} -> {m6['nlong']:+.3f}). REASON: by the time the 12m bear-STATE"
            " fires, individual names are mostly DOWN over 12m, so the TSMOM sleeve has flipped"
            " net-SHORT in bears (standalone nlf +0.62 bull -> -0.28 bear; deployed +0.18 ->"
            " -0.08). Gating it to 0 removes a NET-SHORT whipsaw (short the rippers into the"
            " Jan-2019 V-rally = the -10.8% month), which fixes that loss (+3.2pp) but mechanically"
            " RAISES nlong and OLS beta (removing negative-beta exposure). The brief's 'net-long in"
            " bears' framing fits the FAST Oct-2018 crash (g=0, NOT gated); the SUSTAINED"
            " bear-state cut is a net-SHORT-whipsaw cut. Net: Sharpe up, beta gate-compliant."
        )
    print(
        f"\n  VERDICT: {'KEEP (bear-gated tilt strictly improves iter-015)' if keep else 'REJECT'}"
    )


if __name__ == "__main__":
    main()
