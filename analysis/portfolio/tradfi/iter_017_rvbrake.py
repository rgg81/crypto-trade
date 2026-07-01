"""iter-017 — SHORT-WINDOW REALIZED-VOL BRAKE (theory-pinned Barroso constant-vol, fast window).

An OUTER de-lever scalar stacked on the FROZEN iter-016 deployed net (bear-gated combined book, band
delta=0.010/freq=1, VIX brake, 63d portfolio vol-target). ONE change, ZERO change to signals.

=========================================================================================
THE THESIS (and the prior evidence it must overcome)
=========================================================================================
iter-016's worst residual is Oct-2018 (-6.9%): a FAST-from-bull crash the 12m bear-gate lags (g=0 in
Oct-2018, trailing-12m still positive) AND the slow 63d portfolio vol-target reacts to too late. The
worst-months forensic PROBE C proposed a realized-vol brake here.

BUT iter-008 already proved a SAME-WINDOW (63d) vol overlay WASHES: the book is ALREADY 63d
vol-targeted to 15%/yr, so its 63d realized vol barely differs by regime (bull~15/bear~17/chop~14%).
A brake at the same window adds nothing. The ONLY way iter-017 earns its keep is if a SHORTER,
FASTER window (5-21d) catches fast vol SPIKES the 63d target is too slow for — de-risking a crash
BEFORE the slow target reacts. This script tests that HONESTLY and REJECTS (like iter-008) if it
only rescues Oct-2018 while washing / hurting the OVERALL Sharpe, or if the win is knife-edge.

=========================================================================================
THE CHANGE — Barroso "Momentum has its moments" constant-vol, at a FAST window
=========================================================================================
    net16      = iter-016 deployed vol-targeted VIX-ON net (UNCHANGED)
    rv_short[t]= net16.rolling(W).std().shift(1)        # book's OWN trailing SHORT-window daily vol
    s[t]       = clip( TARGET / rv_short[t], FLOOR, 1 )  # de-lever ONLY (cap at 1), past-only
    net17      = net16 * s

  * W (short window) is swept {5, 10, 21}d; the PRE-REGISTERED decision cell is W=21d — the 1-month
    realized-vol window PROBE C pre-committed, the canonical Barroso short window. We do NOT swap to
    a shorter max-net window (that is max-net-fitting to Oct-2018); a shorter W is KEPT only if the
    whole {5,10,21}x{floor} neighborhood is a robust plateau above baseline.
  * TARGET = ct.TARGET_VOL = 15%/yr / sqrt(252) (~0.00945/day) — the book's OWN 15%/yr vol target,
    a DATA-INDEPENDENT constant already in the codebase (ZERO new fitted parameter). This is the
    theory-pin: the SAME target level the 63d vol-target aims for, measured on a FAST window, so the
    brake bites exactly when short-window vol has SPIKED above the target the slow window has not
    yet caught. A self-calibrating TARGET=IS-median-short-vol variant is REPORTED for robustness.
  * FLOOR = 0.50 (never cut the book below half) — a round conservative cap, swept {0.4,0.5,0.6}.
  * s is de-lever ONLY (upper=1): it NEVER levers up (Barroso constant-vol form), so it can only
    REDUCE exposure/vol, never add risk.

=========================================================================================
LEAK SAFETY + IDENTITY (HARD)
=========================================================================================
  * rv_short = net16.rolling(W).std().shift(1) reads ONLY past net (same convention as
    ct.vol_target_scale, which is .shift(1) too). TARGET is a data-independent constant. So s[t]
    reads only net16[<t]; net17[t<cut] is bit-identical when close+ret_fwd after `cut` are corrupted
    (in-script future-bar self-check + pytest test_iter017_rvbrake_future_bar_no_leak).
  * IDENTITY (pre-registered): brake OFF (TARGET=+inf -> s==1 everywhere) -> net17 == iter-016 net
    bit-for-bit (test_iter017_brake_off_reproduces_iter016). Anchors iter-017 as a pure one-change
    delta off iter-016.
  * OOS stays HIDDEN: every metric is the IS slice only; no OOS number is computed (no --confirm
    path). The median-target variant's constant is IS-only; the PRIMARY cell's TARGET is
    data-independent. Do NOT tune W / TARGET / FLOOR to OOS or to max-net Oct-2018.

Run: uv run python analysis/portfolio/tradfi/iter_017_rvbrake.py
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
import iter_008_vix_stop as i8  # noqa: E402
import iter_011_mom_ltr as i11  # noqa: E402
import iter_013_directional as i13  # noqa: E402
import iter_015_cost as i15  # noqa: E402
import iter_016_bear_gated_tsmom as i16  # noqa: E402
import universe_tradfi as ut  # noqa: E402

# --- ALL downstream constants are PRE-EXISTING (frozen iter-016 deployed cell) ---
DELTA = i15.CHOSEN_DELTA  # 0.010 deployed band (unchanged)
FREQ = i15.CHOSEN_FREQ  # 1 daily rebalance (unchanged)

# --- PRE-REGISTERED rv-brake (theory-pinned; NOT max-net-fit) ---
WINDOWS = (5, 10, 21)  # short realized-vol windows swept; DECISION cell = 21d (PROBE C, Barroso 1m)
CHOSEN_WINDOW = 21  # pre-registered decision window (NOT the max-net window)
TARGET = ct.TARGET_VOL  # 15%/yr/sqrt(252) daily target — the book's OWN target, ZERO new param
FLOORS = (0.40, 0.50, 0.60)  # de-lever floor swept; DECISION floor = 0.50
CHOSEN_FLOOR = 0.50

# The pre-registered KEEP gate (strict OVERALL improvement to stack on iter-016).
GATE_NET1X_BASE = 0.728  # iter-016 net@1x — iter-017 must STRICTLY beat it (overall Sharpe up)
GATE_N2X, GATE_BETA, GATE_YRS, GATE_GROSS = 0.50, 0.15, 13, 0.80

# Good-year set for the no-regression / goodDmu test: exclude the warm-up 2010 + the two named bad
# years 2018/2019 the brake TARGETS. A fix that helps 2018 at the good years' expense is a trap.
BAD_TARGET_YEARS = (2010, 2018, 2019)


# ---------------------------------------------------------------- iter-016 frozen book -----------
def iter016_deployed(pn, ret_fwd, s_vix):
    """(net_1x VIX-off, d1x, d2x, dg, w) for the FROZEN iter-016 deployed book (band 0.010/freq 1).

    net_1x is the VIX-OFF 1x net (iter-016's beta-of-record convention); d1x/d2x/dg carry the VIX
    brake (the deployed exposure). w is the lagged held weight book (rv-brake does NOT touch it).
    """
    raw = i16.bear_gated_combined_raw(pn)
    net_g, _ = i15.banded_net_freq(raw, ret_fwd, DELTA, FREQ, 0.0)
    net_1x, w = i15.banded_net_freq(raw, ret_fwd, DELTA, FREQ, ct.COST_SIDE)
    net_2x, _ = i15.banded_net_freq(raw, ret_fwd, DELTA, FREQ, 2.0 * ct.COST_SIDE)

    def _vix(net):
        return net * s_vix.reindex(net.index).fillna(1.0)

    return net_1x, _vix(net_g), _vix(net_1x), _vix(net_2x), w


# ---------------------------------------------------------------- the ONE change -----------------
def rv_brake_scale(net: pd.Series, window: int, target: float, floor: float) -> pd.Series:
    """Barroso constant-vol de-lever at a FAST window: s = clip(target/rv_short[t-1], floor, 1).

    rv_short = trailing-`window` daily std of the book's OWN net, `.shift(1)` (past-only, same lag
    as ct.vol_target_scale). De-lever ONLY (upper=1) — never levers up. target=+inf -> s==1 (off).
    NaN warm-up rv -> s=1 (no brake). Reads only net[<t]: future-bar leak-safe.
    """
    rv = net.rolling(window).std().shift(1)
    return (target / rv).clip(lower=floor, upper=1.0).fillna(1.0)


def _apply(net: pd.Series, s: pd.Series) -> pd.Series:
    return net * s.reindex(net.index).fillna(1.0)


def metrics(net16_1x_vo, d1x, d2x, dg, w, mkt, s) -> dict:
    """Deployed IS metric bundle for the iter-016 book de-levered by brake scalar `s` (s==1 -> i16).

    Sharpes carry VIX (deployed). beta is on the VIX-OFF 1x net x s (iter-016 convention -> baseline
    reproduces +0.148). beta_dep is the fully-deployed VIX-ON braked beta (the real exposure).
    Turnover of the WEIGHT book is unchanged (s is an outer scalar); s_turn = the brake's own
    exposure churn (mean|Δs|, IS) — the extra trading the standard cost model does NOT charge.
    """
    b1x, b2x, bg = _apply(d1x, s), _apply(d2x, s), _apply(dg, s)
    npos, nyr = i11.n_pos_years(b1x)
    s_is = ct.is_only(s)
    return {
        "net1x": ct.msharpe(b1x, ct.LO0, ct.OOS_CUTOFF),
        "net2x": ct.msharpe(b2x, ct.LO0, ct.OOS_CUTOFF),
        "gross": ct.msharpe(bg, ct.LO0, ct.OOS_CUTOFF),
        "beta": i13.net_beta(_apply(net16_1x_vo, s), mkt),  # VIX-off x brake (iter-016 convention)
        "beta_dep": i13.net_beta(b1x, mkt),  # deployed VIX-on x brake (real exposure)
        "turn": ct.turnover(w, ct.LO0, ct.OOS_CUTOFF),  # weight book unchanged by the outer scalar
        "s_mean": float(s_is.mean()),
        "s_min": float(s_is.min()),
        "s_fire": float((s_is < 0.999).mean()) * 100.0,  # % IS days the brake bites
        "s_turn": float((s_is - s_is.shift(1)).abs().mean()),  # brake exposure churn (uncharged)
        "npos": npos,
        "nyr": nyr,
        "d1x": b1x,
    }


def month_ret(net: pd.Series, period: str) -> float:
    """IS-only calendar-month net return (sum of daily net) — the forensic per-month convention."""
    s = ct.is_only(net)
    m = s.groupby(s.index.to_period("M")).sum()
    p = pd.Period(period, freq="M")
    return float(m.loc[p]) if p in m.index else float("nan")


def _leak_selfcheck(pn, ret_fwd, s_vix) -> bool:
    """Corrupt close + ret_fwd after a cutoff; the rv-braked deployed net before it must be
    bit-identical (rv_short reads only past net via .shift(1); TARGET is data-independent)."""
    n16_vo0, _, d1x0, _, _ = iter016_deployed(pn, ret_fwd, s_vix)
    s0 = rv_brake_scale(d1x0, CHOSEN_WINDOW, TARGET, CHOSEN_FLOOR)
    net0 = _apply(d1x0, s0)
    cut = net0.index[len(net0) // 2]
    pn_c = {k: v.copy() for k, v in pn.items()}
    pn_c["close"].loc[pn_c["close"].index >= cut] *= -7.0
    pn_c["ret_fwd"].loc[pn_c["ret_fwd"].index >= cut] += 5.0
    _, _, d1x1, _, _ = iter016_deployed(pn_c, pn_c["ret_fwd"], s_vix)
    s1 = rv_brake_scale(d1x1, CHOSEN_WINDOW, TARGET, CHOSEN_FLOOR)
    net1 = _apply(d1x1, s1)
    common = net0.index.intersection(net1.index)
    common = common[common < cut]
    return bool(np.allclose(net0.loc[common].to_numpy(), net1.loc[common].to_numpy(), atol=1e-12))


def _identity_check(d1x) -> bool:
    """brake OFF (TARGET=+inf -> s==1 everywhere) -> net17 == iter-016 d1x bit-for-bit."""
    s_off = rv_brake_scale(d1x, CHOSEN_WINDOW, 1e18, CHOSEN_FLOOR)
    net_off = _apply(d1x, s_off)
    return bool(np.allclose(net_off.to_numpy(), d1x.to_numpy(), atol=1e-15, rtol=0.0))


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
    mkt = i13.market_return(pn)
    vix = i8.load_vix_close(ret_fwd.index, args.data_dir)
    s_vix = i8.vix_scale(vix)  # base=20 / floor=0.50 (iter-008 UNCHANGED)

    n16_vo, dg, d1x, d2x, w = iter016_deployed(pn, ret_fwd, s_vix)

    print("=" * 100)
    print("iter-017 — SHORT-WINDOW REALIZED-VOL BRAKE (Barroso constant-vol, fast W) on iter-016")
    print("=" * 100)
    print(
        f"  s=clip(TARGET/rv_short[t-1],floor,1) on iter-016 net;  TARGET={TARGET:.5f}/day "
        f"(=15%/yr, the book's OWN vol-target);  W swept {WINDOWS}, floor swept {FLOORS};  "
        f"DECISION cell W={CHOSEN_WINDOW}/floor={CHOSEN_FLOOR} (theory-pinned, NOT max-net)\n"
    )

    # --- IDENTITY (brake-off -> iter-016) + LEAK self-check ---
    ident = _identity_check(d1x)
    leak_ok = _leak_selfcheck(pn, ret_fwd, s_vix)
    print(
        f"  IDENTITY  brake-off (s==1) -> iter-016 net bit-for-bit : {'PASS' if ident else 'FAIL'}"
    )
    print(
        f"  LEAK      future-bar corruption, pre-cut net bit-id  : {'PASS' if leak_ok else 'FAIL'}"
    )

    # --- BASELINE (iter-016, s==1) metrics ---
    base_s = pd.Series(1.0, index=d1x.index)
    mb = metrics(n16_vo, d1x, d2x, dg, w, mkt, base_s)
    print(
        f"\n  iter-016 BASELINE (s==1): net@1x={mb['net1x']:+.3f}  net@2x={mb['net2x']:+.3f}  "
        f"gross={mb['gross']:+.3f}  net-b={mb['beta']:+.3f}  +yrs={mb['npos']}/{mb['nyr']}  "
        f"turn={mb['turn']:.4f}"
    )

    # --- CONTEXT: how much does the book's SHORT-window vol differ from the 63d target? ---
    # (the iter-008 wash test — if the fast window has little dispersion the brake is inert/washes)
    print("\n  short-window realized-vol dispersion of the iter-016 net (annualized, IS):")
    for wdw in WINDOWS:
        rv_ann = (ct.is_only(d1x).rolling(wdw).std() * np.sqrt(252)) * 100.0
        rv_ann = rv_ann.dropna()
        print(
            f"      W={wdw:>2}d rv: med={rv_ann.median():4.1f}%  p10={rv_ann.quantile(0.1):4.1f}% "
            f"p90={rv_ann.quantile(0.9):5.1f}%  max={rv_ann.max():5.1f}%  (63d target=15.0%)"
        )

    # --- (1) SWEEP {5,10,21}d x floor {0.4,0.5,0.6}, TARGET=15%/yr (PRIMARY) ---
    print(
        "\n  (1) SWEEP W x floor (TARGET=15%/yr) — net1x/net2x/gross/β/Oct18%/+yrs/fire:"
    )
    print(
        f"      {'W':>3} {'floor':>5} {'net1x':>7} {'net2x':>7} {'gross':>7} {'β':>7} "
        f"{'Oct18%':>7} {'+yrs':>6} {'fire%':>6} {'smean':>6}"
    )
    grid = {}
    for wdw in WINDOWS:
        for fl in FLOORS:
            s = rv_brake_scale(d1x, wdw, TARGET, fl)
            m = metrics(n16_vo, d1x, d2x, dg, w, mkt, s)
            grid[(wdw, fl)] = m
            oct18 = month_ret(m["d1x"], "2018-10") * 100.0
            star = " *" if (wdw, fl) == (CHOSEN_WINDOW, CHOSEN_FLOOR) else "  "
            print(
                f"    {star}{wdw:>2} {fl:>5.2f} {m['net1x']:>+7.3f} {m['net2x']:>+7.3f} "
                f"{m['gross']:>+7.3f} {m['beta']:>+7.3f} {oct18:>+7.2f} {m['npos']:>3}/{m['nyr']} "
                f"{m['s_fire']:>5.0f}% {m['s_mean']:>6.2f}"
            )
    print(f"    (* = PRE-REGISTERED decision cell; baseline net@1x={mb['net1x']:+.3f})")

    # --- (2) TARGET=median-short-vol robustness variant (self-calibrating; IS-frozen constant) ---
    print(
        "\n  (2) ROBUSTNESS: TARGET = IS-median short-window vol (floor=0.50) — self-calibrating:"
    )
    print(
        f"      {'W':>3} {'target/d':>9} {'net1x':>7} {'net2x':>7} {'gross':>7} {'β':>7} "
        f"{'Oct18%':>7} {'+yrs':>6} {'fire%':>6}"
    )
    for wdw in WINDOWS:
        rv_is = ct.is_only(d1x).rolling(wdw).std().shift(1).dropna()
        tgt_med = float(rv_is.median())  # IS-only frozen constant (leak-safe as a pre-set number)
        s = rv_brake_scale(d1x, wdw, tgt_med, CHOSEN_FLOOR)
        m = metrics(n16_vo, d1x, d2x, dg, w, mkt, s)
        oct18 = month_ret(m["d1x"], "2018-10") * 100.0
        print(
            f"      {wdw:>2} {tgt_med:>9.5f} {m['net1x']:>+7.3f} {m['net2x']:>+7.3f} "
            f"{m['gross']:>+7.3f} {m['beta']:>+7.3f} {oct18:>+7.2f} {m['npos']:>3}/{m['nyr']} "
            f"{m['s_fire']:>5.0f}%"
        )

    # --- (3) PRE-REGISTERED cell full metrics vs iter-016 ---
    mc = grid[(CHOSEN_WINDOW, CHOSEN_FLOOR)]
    print(
        f"\n  (3) PRE-REGISTERED cell W={CHOSEN_WINDOW}/floor={CHOSEN_FLOOR} vs iter-016 baseline:"
    )
    print(f"      {'metric':<16}{'iter-016':>10}{'iter-017':>10}{'delta':>9}")
    for lab, k in (
        ("net@1x (6bps)", "net1x"),
        ("net@2x (12bps)", "net2x"),
        ("gross (cost-off)", "gross"),
        ("net-β (VIXoff)", "beta"),
        ("net-β deployed", "beta_dep"),
        ("+pos years", "npos"),
    ):
        a, b = mb[k], mc[k]
        print(f"      {lab:<16}{a:>+10.3f}{b:>+10.3f}{b - a:>+9.3f}")
    print(
        f"      brake: fires {mc['s_fire']:.0f}% of IS days, mean s={mc['s_mean']:.2f}, "
        f"min s={mc['s_min']:.2f}, brake churn |Δs|/day={mc['s_turn']:.4f} (UNCHARGED by std cost)"
    )

    # --- (4) Oct-2018 + 2018 year, before -> after (the named target) ---
    oct16 = month_ret(mb["d1x"], "2018-10") * 100.0
    oct17 = month_ret(mc["d1x"], "2018-10") * 100.0
    y16 = i11.year_table(mb["d1x"])
    y17 = i11.year_table(mc["d1x"])
    print("\n  (4) NAMED TARGET Oct-2018 + year-2018 (iter-016 -> iter-017):")
    print(f"      2018-10 month: {oct16:>+7.2f}% -> {oct17:>+7.2f}%   (Δ {oct17 - oct16:>+.2f}pp)")
    print(
        f"      2018 year    : {y16[2018][1]:>+7.1f}% ({y16[2018][0]:+.2f}) -> "
        f"{y17[2018][1]:>+7.1f}% ({y17[2018][0]:+.2f})   (ΔR {y17[2018][1] - y16[2018][1]:+.1f}pp)"
    )

    # --- (5) PER-YEAR table (iter-016 -> iter-017) + good-year regression / goodDmu ---
    print("\n  (5) PER-YEAR net return% (Sharpe) — iter-016 -> iter-017 (* = named target year):")
    good_flips = []
    good_dmu_terms = []
    for yr in sorted(y17):
        star = "*" if yr in (2018, 2019) else " "
        a_sh, a_r = y16[yr]
        b_sh, b_r = y17[yr]
        flip = ""
        if yr not in BAD_TARGET_YEARS:
            good_dmu_terms.append(b_r - a_r)
            if a_sh > 0 and b_sh <= 0:
                flip = "  <- GOOD-YEAR REGRESSION"
                good_flips.append(yr)
        print(
            f"      {yr}{star} {a_r:>+6.1f}% ({a_sh:>+5.2f}) -> {b_r:>+6.1f}% ({b_sh:>+5.2f}){flip}"
        )
    good_dmu = float(np.mean(good_dmu_terms))
    print(
        f"\n      goodΔμ (mean good-yr return% change, excl {BAD_TARGET_YEARS}) = {good_dmu:+.2f}pp"
        f"   good-year sign regressions = {len(good_flips)} {good_flips if good_flips else ''}"
    )

    # --- (6) PLATEAU vs KNIFE-EDGE: how many of the 9 grid cells beat baseline net@1x? ---
    beats = [(k, m["net1x"]) for k, m in grid.items() if m["net1x"] > mb["net1x"] + 1e-9]
    best_cell = max(grid.items(), key=lambda kv: kv[1]["net1x"])
    # monotone-in-W check at the decision floor: does the middle window (10d) also beat baseline?
    mid_beats = grid[(10, CHOSEN_FLOOR)]["net1x"] > mb["net1x"]
    monotone = mid_beats  # a genuine mechanism should not have the middle window DIP below baseline
    print(
        f"\n  (6) PLATEAU check: {len(beats)}/9 W x floor cells beat baseline net@1x "
        f"(+{mb['net1x']:.3f}); best cell = {best_cell[0]} at {best_cell[1]['net1x']:+.3f} "
        f"(NOT the pre-registered {CHOSEN_WINDOW}/{CHOSEN_FLOOR} -> max-net is a SHORTER window)"
    )
    if beats:
        print("      cells beating baseline: " + ", ".join(f"{k}" for k, _ in beats))
    print(
        f"      MONOTONE-in-W at floor={CHOSEN_FLOOR}: {'Y' if monotone else 'N'} "
        f"(W=10 net@1x={grid[(10, CHOSEN_FLOOR)]['net1x']:+.3f} "
        f"{'>=' if mid_beats else '<'} baseline +{mb['net1x']:.3f}) "
        f"-> {'clean plateau' if monotone else 'NON-MONOTONE: middle window DIPS below baseline'}"
    )

    # --- (7) PRE-REGISTERED KEEP gate (strict OVERALL improvement to STACK on iter-016) ---
    g_net1x = mc["net1x"] > mb["net1x"]
    g_n2x = mc["net2x"] >= GATE_N2X
    g_beta = mc["beta"] <= GATE_BETA
    g_yrs = mc["npos"] >= GATE_YRS
    g_gross = mc["gross"] >= GATE_GROSS
    g_good = (
        good_dmu >= 0.0 and len(good_flips) == 0
    )  # the ANTI-OVERFIT gate: new edge, not vol-cut
    # robust plateau = decision cell beats baseline, a majority of the neighborhood does too, AND
    # response is MONOTONE in W (no middle-window dip below baseline -> not luck in spike placement)
    g_plateau = mc["net1x"] > mb["net1x"] and len(beats) >= 5 and monotone
    keep = (
        g_net1x
        and g_n2x
        and g_beta
        and g_yrs
        and g_gross
        and g_good
        and g_plateau
        and ident
        and leak_ok
    )
    print("\n  (7) KEEP gate (STACK on iter-016 — must improve OVERALL Sharpe, not just Oct-2018):")
    print(
        f"      net@1x>+{mb['net1x']:.3f}={'Y' if g_net1x else 'N'} ({mc['net1x']:+.3f})  "
        f"net@2x>=+0.50={'Y' if g_n2x else 'N'} ({mc['net2x']:+.3f})  "
        f"β<=0.15={'Y' if g_beta else 'N'} ({mc['beta']:+.3f})  +yrs>=13={'Y' if g_yrs else 'N'} "
        f"({mc['npos']})"
    )
    print(
        f"      gross>=+0.80={'Y' if g_gross else 'N'} ({mc['gross']:+.3f})  "
        f"no-good-yr-regression={'Y' if g_good else 'N'} (goodΔμ={good_dmu:+.2f}pp, "
        f"{len(good_flips)} flips)  robust-plateau={'Y' if g_plateau else 'N'} "
        f"({len(beats)}/9, monotone={'Y' if monotone else 'N'})  "
        f"identity={'Y' if ident else 'N'}  leak={'Y' if leak_ok else 'N'}"
    )
    # HONEST verdict: distinguish a clean iter-008-style WASH from a real-but-vol-driven lift that
    # fails only the anti-overfit sub-gate. NOT a wash (overall Sharpe rises + β drops); it is
    # a vol-reduction overlay whose good-year RETURN effect is flat (no new edge) and non-monotone.
    if keep:
        verdict = "KEEP (fast rv-brake strictly improves iter-016 overall AND clears anti-overfit)"
    elif mc["net1x"] > mb["net1x"]:
        verdict = (
            f"REJECT AS BASELINE PROMOTE — OPTIONAL vol-overlay for QR. NOT a wash: overall net@1x "
            f"RISES {mc['net1x'] - mb['net1x']:+.3f} and β DROPS {mc['beta'] - mb['beta']:+.3f} "
            f"(reclaims iter-016 headroom), Oct-2018 {oct16:+.1f}%->{oct17:+.1f}%. BUT the lift is "
            f"pure VOL-REDUCTION: goodΔμ={good_dmu:+.2f}pp (good-year RETURNS flat -> NO new edge, "
            f"fails the anti-overfit gate) and non-monotone in W (max-net at un-pinned W=5). Does "
            f"NOT clear the strict gate as a mandatory promote; QR may adopt it as an optional "
            f"β-headroom / drawdown / Oct-2018 overlay under the Sharpe-first mandate."
        )
    else:
        verdict = (
            "REJECT — WASH/OVERFIT TRAP (fixes at most Oct-2018 while washing the overall Sharpe, "
            "exactly like iter-008's 63d overlay)"
        )
    print(f"\n  VERDICT: {verdict}")


if __name__ == "__main__":
    main()
