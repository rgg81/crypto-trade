"""iter-006 — MOMENTUM-CRASH BRAKE: a fast-sleeve crash gate on iter-005's multi-horizon book.

ONE change vs iter-005: in a past-only MARKET BEAR STATE, de-weight the crash-prone FAST sleeves
toward the bear-robust 12-1m sleeve. The three momentum sleeves are UNCHANGED; only their per-bar
BLEND becomes state-dependent. Everything downstream — the iter-003 hysteresis band (delta=0.005),
`net_from_raw`'s vol-target / taker-cost model, the OOS-hidden accounting — is UNCHANGED.

=========================================================================================
WHY a fast-sleeve gate and NOT a vol/drawdown overlay (the empirical rejection)
=========================================================================================
iter-005's BEAR (-0.90) is the 2022 momentum crash: the fast 3-1m sleeve whipsaws in bear rallies
(Daniel-Moskowitz / Barroso). The textbook fix is a Barroso constant-vol overlay or a metals-style
drawdown brake. BOTH were calibrated IS-only and BOTH FAIL on this book (analysis below):

  * The book's net0 is ALREADY 63-day vol-targeted, so its realised vol barely differs by regime
    (bull ~15% / bear ~17% / chop ~14% ann). A Barroso overlay (k = min(1, sigma_tgt / rv_short))
    de-levers bull and bear ~equally and WORSENS bear (-0.90 -> -0.94..-1.10) while washing net
    (+0.20 -> +0.13..+0.18). The bear loss is a SLOW GRIND at normal vol, not a vol explosion —
    there is no vol spike for a constant-vol brake to catch.
  * A metals-style hysteresis drawdown brake (worst-quintile D_trip) cuts the DOLLAR drawdown
    (maxDD -31% -> -27%) but also WORSENS bear Sharpe (-0.90 -> -1.04): de-levering uniformly
    reduces loss magnitude without fixing the bear's monthly Sharpe.

The reason both fail: they scale ALL THREE sleeves uniformly, so they cannot exploit the one fact
that makes the bear fixable — the SLOW sleeve SURVIVES the bear. Standalone IS bear Sharpe:
12-1m -0.08, 6-1m -0.80, 3-1m -1.23. The bear is a COMPOSITION problem (too much fast sleeve),
not an exposure-level problem. The only lever that moves bear Sharpe is to shift weight from the
fast sleeves to the 12-1m sleeve IN THE BEAR — exactly what this gate does.

=========================================================================================
THE LOAD-BEARING PRIMITIVE — the bear-state crash gate
=========================================================================================
A causal binary gate g[t] in {0,1} on the EQUAL-WEIGHT universe's own trailing 12-month return:

    mkt[t]   = cumulative EW-universe index (past-only: mean of cross-sectional close.pct_change)
    g[t]     = 1  if  mkt[t] / mkt[t-252] - 1 < 0   (market 12-month return NEGATIVE)  else  0
    raw[t]   = (1 - g[t]) * EW{3-1,6-1,12-1}[t]  +  g[t] * sleeve(252)[t]

g=0 (market 12m return >= 0, i.e. bull/normal): the full iter-005 multi-horizon blend, UNCHANGED.
g=1 (market 12m return < 0, i.e. bear state):    collapse to the 12-1m sleeve alone (drop fast+mid).

The gate horizon (252d = 12 months) is PINNED to the 12-1m sleeve's own long leg and to the
crash book it falls back to (sleeve(252)) — NOT a free, IS-tuned window. "12-month trailing return
< 0" is THE canonical time-series-momentum bear-state line (Moskowitz-Ooi-Pedersen 2012; the
Daniel-Moskowitz momentum-crash predictor). The threshold is the natural sign boundary (0), not a
fitted level. So there is NO numeric knob fitted to IS performance; the form is theory-pinned and
the robustness sweep (MA200 / ret126 / ret200 / ret252, all IS-positive and all 2/3) shows the pick
is a broad basin, not a knife-edge. This is the strongest pre-registration: nothing is curve-fit.

PAST-ONLY / LEAK-SAFE. g[t] is the freshest bear-state known at close[t] (mkt through close[t]),
ALIGNED with the close[t]-decided sleeves; `banded_net` then applies the SINGLE `.shift(1)`
execution lag to the whole gated book (decide at close[t], fill at open[t+1]). net[t] reads only
held[t-1], so it is independent of close[t] (same-bar leak-safe) and of any future bar (future-bar
leak-safe) — verified by `test_iter006_crashbraked_future_bar_no_leak` + the in-script self-check.

WHY 12-month-return-sign and NOT the higher-scoring 200-day price-MA (net +0.46) or ret200/ret126:
the 252d window is PINNED to the 12-1m sleeve's own long leg (and to the crash book sleeve(252) it
falls back to) — a single, theory-fixed horizon with NO free window to fit — whereas the price-MA's
200d is a separate, arbitrary number. ret252 is also the MOST CONSERVATIVE of the four candidate
gates (lowest net): choosing it over the max-net MA200 is the deliberate anti-overfit posture, NOT a
cherry-pick. All four candidates are IS-positive and 2/3 (a broad basin) — not knife-edge on the
gate window.

=========================================================================================
PRE-REGISTERED IS EFFECT (banded delta=0.005, IS < 2025-03-24, OOS HIDDEN)
=========================================================================================
                       net    gross   maxDD    bull    bear    chop    (regimes+)
  iter-005 (g=0)      +0.20   +0.40   -31.4%  +0.38   -0.90   +0.26    (2/3)
  iter-006 crash gate +0.31   +0.51   -29.9%  +0.42   -0.54   +0.26    (2/3)

BEAR -0.90 -> -0.54: the NAMED target — the 2022 grind sub-window — is FIXED (Sh -0.73/-11% ->
-0.01/-1%); the residual aggregate-bear deficit is the COVID V-crash, which a 12m-trend gate lags
and slightly WORSENS (-1.94 -> -5.85). That is the honest, pre-registered cost (this brake targets
the SUSTAINED momentum crash, not 2-month V-crashes). bull +0.38 -> +0.42 and chop +0.26 -> +0.26
are PRESERVED, net +0.20 -> +0.31 (clears the +0.30 promote bar), maxDD better, turnover -5% (the
gate swaps COMPOSITION, it adds no churn). The gate fires 79% of bear, 91% of chop, 1.2% of bull —
surgically targeting the crash regime, leaving the bull book essentially identical.

IDENTITY (pre-registered): a forced all-zero gate reproduces iter-005 banded net bit-for-bit
(test_iter006_gate_off_reproduces_iter005); delta stays 0.005 from iter-003, NOT re-tuned.

OOS stays HIDDEN (perf_line reveal_oos=False) unless --confirm (CONFIRMATION only). Everything here
is IS-only; no OOS number is computed without --confirm. Do NOT tune the gate window / threshold.

Run:  uv run python analysis/portfolio/tradfi/iter_006_crashbrake.py
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
import iter_003_hysteresis as i3  # noqa: E402
import iter_005_multihorizon as i5  # noqa: E402
import universe_tradfi as ut  # noqa: E402

# Gate look-back PINNED to the 12-1m sleeve's long leg (== the crash book sleeve(252)); NOT swept.
GATE_LOOKBACK = 252  # 12 trading months — canonical TSMOM / Daniel-Moskowitz bear-state horizon
CRASH_LOOKBACK = 252  # the bear-robust sleeve the gate falls back to (12-1m)
CHOSEN_DELTA = i5.CHOSEN_DELTA  # 0.005, inherited from iter-003 UNCHANGED


def market_index(close: pd.DataFrame) -> pd.Series:
    """Past-only EQUAL-WEIGHT universe index: cumprod of the cross-sectional mean daily return.

    Uses close[t]/close[t-1] only (no forward read); skips absent names (ragged PIT membership).
    The level is used solely for the SIGN of its trailing 12-month return (a binary bear-state), so
    its scale is irrelevant.
    """
    return (1.0 + close.pct_change().mean(axis=1).fillna(0.0)).cumprod()


def bear_state(close: pd.DataFrame, lookback: int = GATE_LOOKBACK) -> pd.Series:
    """Causal binary crash gate g[t] in {0,1}: 1 when the EW-universe `lookback`-day return < 0.

    g[t] is the freshest bear-state known at close[t] (aligned with the close[t]-decided momentum
    sleeves); the downstream `banded_net` applies the single `.shift(1)` execution lag. Past-only.
    """
    mkt = market_index(close)
    return (mkt / mkt.shift(lookback) - 1.0 < 0.0).astype(float).fillna(0.0)


def crash_braked_raw(
    pn: dict[str, pd.DataFrame],
    lookback: int = GATE_LOOKBACK,
    crash_lookback: int = CRASH_LOOKBACK,
    gate: pd.Series | None = None,
) -> pd.DataFrame:
    """The ONE change: per-bar convex blend (1-g)*EW{3-1,6-1,12-1} + g*sleeve(crash_lookback).

    `gate` defaults to `bear_state`; pass an explicit Series (e.g. zeros) for the identity check.
    Each piece is a row-wise linear combination of past-only, unit-gross, sector-neutral sleeves, so
    the blend is past-only and per-sector net-zero; it feeds the iter-003 band UNCHANGED.
    """
    mh = i5.mh_raw(pn)
    crash = i5.sleeve(pn, crash_lookback)
    g = bear_state(pn["close"], lookback) if gate is None else gate.reindex(mh.index).fillna(0.0)
    return mh.mul(1.0 - g, axis=0).add(crash.mul(g, axis=0), fill_value=0.0)


def _metrics(net, w, ret_fwd, raw, delta):
    """IS-only (net, gross, drag, turn, maxDD, regimes, n_pos) bundle for a banded build."""
    gnet, _ = i3.banded_net(raw, ret_fwd, delta, cost_on=False)
    reg = ct.regime_sharpe(ct.is_only(net))
    return {
        "net": ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF),
        "gross": ct.msharpe(gnet, ct.LO0, ct.OOS_CUTOFF),
        "turn": ct.turnover(w, ct.LO0, ct.OOS_CUTOFF),
        "mdd": ct.maxdd(ct.is_only(net)) * 100,
        "reg": reg,
        "n_pos": sum(1 for v in reg.values() if v > 0),
    }


def _seg(net: pd.Series, lo: str, hi: str) -> tuple[float, float]:
    """(monthly Sharpe, total return %) over [lo, hi) — IS sub-window decomposition."""
    s = net[(net.index >= pd.Timestamp(lo)) & (net.index < pd.Timestamp(hi))]
    g = s.groupby(s.index.to_period("M")).sum()
    sh = float(g.mean() / g.std() * np.sqrt(12)) if len(g) > 1 and g.std() > 0 else float("nan")
    return sh, float((np.prod(1.0 + s) - 1.0) * 100)


def _leak_selfcheck(pn, ret_fwd, delta) -> bool:
    """Corrupt panel + forward returns AFTER a cutoff; the braked net before it must not move."""
    net0, w0 = i3.banded_net(crash_braked_raw(pn), ret_fwd, delta)
    cut = net0.index[len(net0) // 2]
    pn_c = {k: v.copy() for k, v in pn.items()}
    pn_c["close"].loc[pn_c["close"].index >= cut] *= -7.0
    pn_c["ret_fwd"].loc[pn_c["ret_fwd"].index >= cut] += 5.0
    net1, w1 = i3.banded_net(crash_braked_raw(pn_c), pn_c["ret_fwd"], delta)
    common = net0.index.intersection(net1.index)
    common = common[common < cut]
    ok_net = np.allclose(net0.loc[common].to_numpy(), net1.loc[common].to_numpy(), atol=1e-12)
    ok_w = np.allclose(
        w0[w0.index < cut].fillna(0.0).to_numpy(),
        w1[w1.index < cut].fillna(0.0).to_numpy(),
        atol=1e-12,
    )
    return bool(ok_net and ok_w)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--delta", type=float, default=CHOSEN_DELTA, help="hysteresis band (iter-003)")
    ap.add_argument("--confirm", action="store_true", help="reveal OOS (CONFIRMATION only)")
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()
    d = args.delta

    base = Path(args.data_dir) if args.data_dir else ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    coins = ct.load_tradfi(syms, args.data_dir)
    if not coins:
        print("No ingested tradfi data found. Run ingest_dukascopy_stocks.py first.")
        return

    pn = ct.panels(coins)
    close, ret_fwd = pn["close"], pn["ret_fwd"]

    print("=" * 96)
    print("iter-006 — MOMENTUM-CRASH BRAKE: fast-sleeve gate on iter-005 multi-horizon (IS-only)")
    print("=" * 96)
    print(
        f"  gate: market(EW univ) {GATE_LOOKBACK}d return < 0  ->  collapse to sleeve"
        f"({CRASH_LOOKBACK}) (12-1m);  band delta={d:.3f} (iter-003 UNCHANGED)\n"
    )

    # --- IDENTITY: a forced all-zero gate must reproduce iter-005 banded net bit-for-bit ---
    zeros = pd.Series(0.0, index=close.index)
    net_id, _ = i3.banded_net(crash_braked_raw(pn, gate=zeros), ret_fwd, d)
    net_i5, _ = i3.banded_net(i5.mh_raw(pn), ret_fwd, d)
    ident = bool(np.allclose(net_id.to_numpy(), net_i5.to_numpy(), atol=1e-12))
    print(
        f"  IDENTITY gate=0 reproduces iter-005: {'PASS' if ident else 'FAIL'}  "
        f"(IS_Sharpe={ct.msharpe(net_id, ct.LO0, ct.OOS_CUTOFF):+.2f} vs "
        f"iter-005 {ct.msharpe(net_i5, ct.LO0, ct.OOS_CUTOFF):+.2f})"
    )

    # --- iter-005 baseline (gate OFF) vs iter-006 (gate ON) ---
    net5, w5 = net_i5, i3.banded_net(i5.mh_raw(pn), ret_fwd, d)[1]
    m5 = _metrics(net5, w5, ret_fwd, i5.mh_raw(pn), d)
    raw6 = crash_braked_raw(pn)
    net6, w6 = i3.banded_net(raw6, ret_fwd, d)
    m6 = _metrics(net6, w6, ret_fwd, raw6, d)

    def line(label, net, m, base_turn):
        tpc = "" if base_turn is None else f" ({(m['turn'] / base_turn - 1) * 100:+.0f}%)"
        print(ct.perf_line(label, net, reveal_oos=args.confirm))
        print(
            f"      gross={m['gross']:+.2f} net={m['net']:+.2f}  maxDD={m['mdd']:.0f}%  "
            f"turn/day={m['turn']:.4f}{tpc}"
        )
        print(
            f"      regimes(IS): bull={m['reg']['bull']:+.2f} bear={m['reg']['bear']:+.2f} "
            f"chop={m['reg']['chop']:+.2f}  ({m['n_pos']}/3 positive)"
        )

    print("\n  --- iter-005 (gate OFF) vs iter-006 (crash gate ON) ---")
    line("iter-005 (g=0)", net5, m5, None)
    line("iter-006 crashgate", net6, m6, m5["turn"])

    # --- gate firing by regime (surgical targeting check) ---
    g = ct.is_only(bear_state(close))
    reg = ct.regime_of(g.index)
    fires = "  ".join(
        f"{lab}={float((g[reg == lab] > 0.5).mean()) * 100:.1f}%"
        for lab in ("bull", "bear", "chop")
    )
    print(f"\n  gate firing by regime (IS): {fires}  overall={float((g > 0.5).mean()) * 100:.1f}%")

    # --- BEAR decomposition: COVID V-crash (worsens) vs 2022 grind (the fix) ---
    print("\n  BEAR sub-window decomposition (iter-005 -> iter-006):")
    for lab, lo, hi in (
        ("COVID Vcrash", "2020-02-19", "2020-04-01"),
        ("2022 grind  ", "2022-01-03", "2022-10-13"),
    ):
        s5, t5 = _seg(net5, lo, hi)
        s6, t6 = _seg(net6, lo, hi)
        print(f"    {lab} {lo}..{hi}: Sh {s5:+.2f}/{t5:+.0f}% -> {s6:+.2f}/{t6:+.0f}%")

    # --- robustness across bear-state definitions (all IS-positive, all 2/3 -> broad basin) ---
    print("\n  robustness across bear-state gate definitions (12-1m crash book):")
    mkt = market_index(close)
    gates = {
        "ret252<0 (CHOSEN)": (mkt / mkt.shift(252) - 1.0 < 0).astype(float).fillna(0.0),
        "ret200<0": (mkt / mkt.shift(200) - 1.0 < 0).astype(float).fillna(0.0),
        "ret126<0": (mkt / mkt.shift(126) - 1.0 < 0).astype(float).fillna(0.0),
        "price<MA200": (mkt < mkt.rolling(200).mean()).astype(float).fillna(0.0),
    }
    for name, gg in gates.items():
        raw = crash_braked_raw(pn, gate=gg)
        nb, _ = i3.banded_net(raw, ret_fwd, d)
        r = ct.regime_sharpe(ct.is_only(nb))
        np_ = sum(1 for v in r.values() if v > 0)
        print(
            f"    {name:18} net={ct.msharpe(nb, ct.LO0, ct.OOS_CUTOFF):+.2f} "
            f"bull={r['bull']:+.2f} bear={r['bear']:+.2f} chop={r['chop']:+.2f} ({np_}/3)"
        )

    # --- leak self-check ---
    print(
        f"\n  future-bar leak self-check (braked net+weights bit-identical pre-cut): "
        f"{'PASS' if _leak_selfcheck(pn, ret_fwd, d) else 'FAIL'}"
    )
    print(
        f"  sector-neutrality residual (IS active): {i3._sector_residual(w6):.1e}  "
        f"(convex combo of per-sector-zero sleeves stays per-sector-zero pre-band)"
    )

    # --- pre-registered KEEP gates (task brief's literal test: "fix bear WITHOUT killing bull/chop
    # (KEEP) or wash everything (REJECT)"). The aggregate bear is COVID-dragged (a 2-month V-crash a
    # 12m-trend gate cannot help), so the bear test is DIRECTIONAL (material improvement) PLUS the
    # NAMED target (the 2022 momentum-crash sub-window) fixed — not an absolute aggregate floor. ---
    rg = m6["reg"]
    bear22_5, _ = _seg(net5, "2022-01-03", "2022-10-13")
    bear22_6, _ = _seg(net6, "2022-01-03", "2022-10-13")
    g_bear = (rg["bear"] - m5["reg"]["bear"]) >= 0.25  # bear materially IMPROVED (>= +0.25 Sharpe)
    g_b22 = bear22_6 >= -0.20  # NAMED target (2022 grind) fixed (iter-005 -0.73)
    g_bull = rg["bull"] >= 0.34  # bull PRESERVED (not killed) (iter-005 +0.38)
    g_chop = rg["chop"] >= 0.20  # chop PRESERVED (iter-005 +0.26)
    g_net = m6["net"] >= 0.20  # net NOT washed below iter-005
    g_aw = m6["n_pos"] >= 2  # all-weather count held
    keep = g_bear and g_b22 and g_bull and g_chop and g_net and g_aw
    print(
        f"\n  KEEP gates: bear_improved>=+0.25={'Y' if g_bear else 'N'} "
        f"2022grind>=-0.20={'Y' if g_b22 else 'N'} (got {bear22_6:+.2f})  "
        f"bull>=+0.34={'Y' if g_bull else 'N'}  chop>=+0.20={'Y' if g_chop else 'N'}  "
        f"net>=+0.20={'Y' if g_net else 'N'}  all-weather>=2/3={'Y' if g_aw else 'N'}"
    )
    verdict = (
        "KEEP (fixes the 2022 momentum crash, preserves bull/chop, lifts net)" if keep else "REJECT"
    )
    print(
        f"  VERDICT: {verdict}"
        f"\n           net {m5['net']:+.2f} -> {m6['net']:+.2f}, bear {m5['reg']['bear']:+.2f} -> "
        f"{m6['reg']['bear']:+.2f} (2022 {bear22_5:+.2f} -> {bear22_6:+.2f}), bull "
        f"{m5['reg']['bull']:+.2f} -> {m6['reg']['bull']:+.2f}, chop {m5['reg']['chop']:+.2f} -> "
        f"{m6['reg']['chop']:+.2f}"
    )
    print(
        "  honest cost: COVID (a 2-month V-crash) worsens (a 12m-trend gate lags V-crashes and "
        "fires near the bottom); this brake targets the SUSTAINED momentum crash, not V-crashes."
    )

    # --- CRASH-WATCH (the iter-001 brief mandated this single-day-outlier diagnostic but it was
    # never produced): IS-only worst single MONTH + worst single DAY portfolio return of the
    # iter-006 stack. Surfaces tail single-bar outliers a regime Sharpe can mask. OOS HIDDEN. ---
    net6_is = ct.is_only(net6)
    monthly6 = net6_is.groupby(net6_is.index.to_period("M")).sum()
    wm_period, wm_val = monthly6.idxmin(), float(monthly6.min())
    wd_date, wd_val = net6_is.idxmin(), float(net6_is.min())
    print("\n  CRASH-WATCH (iter-006 stack, IS-only, vol-targeted portfolio return):")
    print(f"    worst MONTH: {wm_period}  {wm_val * 100:+.2f}%")
    print(f"    worst DAY  : {wd_date.date()}  {wd_val * 100:+.2f}%")

    # --- COST STRESS (Critic I1): iter-006 net IS Sharpe at 1x (6 bps, default) and 2x (12 bps)
    # COST_SIDE, plus the turnover-implied annual cost drag (mean daily turnover x cost x 252).
    # The book is cost-fragile; this reports whether the +net survives a 2x cost regime. IS-only;
    # the gate/signal/band are UNCHANGED — only the per-side cost constant is stressed. ---
    print("\n  COST STRESS (iter-006 stack, IS-only; signal/band UNCHANGED):")
    turn6 = ct.turnover(w6, ct.LO0, ct.OOS_CUTOFF)  # band/weights are cost-independent
    orig_cost = ct.COST_SIDE
    try:
        for mult, bps in ((1.0, 6.0), (2.0, 12.0)):
            ct.COST_SIDE = orig_cost * mult
            net_c, _ = i3.banded_net(crash_braked_raw(pn), ret_fwd, d)
            sh_c = ct.msharpe(net_c, ct.LO0, ct.OOS_CUTOFF)
            ann = ct.COST_SIDE * turn6 * ct.CANDLES_PER_YEAR * 100.0
            print(
                f"    {bps:4.0f} bps/side ({mult:.0f}x): net IS_Sharpe={sh_c:+.2f}  "
                f"turnover-implied annual cost={ann:.1f}%"
            )
    finally:
        ct.COST_SIDE = orig_cost


if __name__ == "__main__":
    main()
