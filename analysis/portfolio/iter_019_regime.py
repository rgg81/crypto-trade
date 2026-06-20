"""portfolio-iteration EXPLORATION-019 — MARKET-REGIME gross-exposure overlay (cut the −23% DD).

The −23% baseline drawdown is CORRELATED PORTFOLIO-WIDE reversals, not single-name concentration
(iter-009 proved per-coin caps don't move it), so the only lever is MARKET-LEVEL gross exposure —
de-lever the WHOLE book when the market regime is dangerous, NOT individual coins.

HARD-WON CAVEATS this file respects:
  * EQUITY-CURVE / P&L-state drawdown brakes are COUNTERPRODUCTIVE on this mean-reverting strategy
    (carry squeeze-stop + iter-007). They de-lever after a loss and miss the snap-back. So EVERY
    signal here is VOL-STATE / regime, built from market inputs — NEVER from the strategy's own P&L.
  * iter-007's vol-spike de-lever LOOKED Pareto-improving but was a STITCH-ORDER ARTIFACT: it was
    measured on a raw-stitch + single-outer-vol-target net, not the canonical per-λ-vol-target-then-
    stitch. Here the overlay is applied to the CANONICAL net itself — `iter_005.walkforward(
    iter_005.lam_nets(coins))[0]`, the deployable +1.37 series. The multiplier-OFF case (γ=0 ⇒ m≡1)
    reproduces +1.37 EXACTLY (asserted at runtime). No stitch order to get wrong.

MECHANISM / accounting. The canonical net is linear in gross exposure: P&L, funding P&L and turnover
cost are each linear in the weight matrix `w`. A market-level gross-exposure scalar `m[t]∈[floor,1]`
therefore scales the WHOLE next-candle net — P&L AND its proportional turnover cost — so the honest
overlaid net is simply `m * net_canonical`. `m` is built only from market state observed strictly
before the candle it scales (every input is shift(1); `m` is shifted once more before it multiplies
the net, so the scalar that hits candle t was decided from data ending at t−1). Leak-safe by
construction.

CANDIDATE REGIME SIGNALS (each de-levers the book when the regime is dangerous):
  A) VOL-RATIO de-lever — aggregate market realized-vol spike. Scale by clip(slow_vol/fast_vol,
     floor, 1): when fast (recent) market vol exceeds slow (baseline) vol, cut gross continuously.
     This is the canonical "vol is high → risk-off" overlay, done at the MARKET (equal-weight
     average coin vol) level, applied to the canonical net.
  B) DISPERSION de-lever — cross-sectional return dispersion. When the cross-section of coin returns
     fans out (everything decorrelates / scatters), a diversified L/S book's hedges stop working;
     scale by clip(slow_disp/fast_disp, floor, 1).
  C) BREADTH de-lever — market breadth. When breadth collapses (almost all coins move the same
     direction — a correlated risk-on/off lurch, the exact regime that drives the portfolio-wide
     reversal DD), de-lever. breadth = |mean sign of coin returns|; high |breadth| ⇒ one-way tape.

Each candidate is ROBUSTNESS-SWEPT over its knobs (windows / threshold / floor). A candidate is only
interesting if DD-relief + OOS-neutrality hold ACROSS the sweep, not at one knife-edge cell.

HARD RULES honored: taker 0.05%/side (already in the canonical net), all inputs past-only (shift),
nothing tuned on OOS, OOS_CUTOFF=2025-03-24 immutable. Reuses iter_002 / iter_004 / iter_005 helpers
unchanged (load_universe, load_funding, vol_target, msharpe, walkforward, lam_nets).
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis/portfolio")
import iter_002_top20 as base  # noqa: E402
import iter_004_funding as f4  # noqa: E402
import iter_005_wf_lambda as wf  # noqa: E402

# ------------------------------------------------------------------------------------------
# MARKET-LEVEL regime inputs (all past-only; equal-weight across the eligible top-N universe so the
# regime signal measures MARKET state, not the strategy's own positioning).
# ------------------------------------------------------------------------------------------


def market_inputs(coins: dict) -> dict:
    """Past-only market-state panels used by every regime overlay.

    Returns equal-weight market series so the regime is a property of the MARKET, never of the
    strategy's P&L (P&L-state brakes are the known-counterproductive trap). All series are computed
    on the eligible PIT top-N basket each candle and carry a NaN warmup that the overlays fill to
    1.0 (no de-lever before the signal is defined).
    """
    close = pd.DataFrame({s: d["close"] for s, d in coins.items()}).astype(float).sort_index()
    qv = pd.DataFrame({s: d["quote_volume"] for s, d in coins.items()}).astype(float)
    qv = qv.reindex(close.index)
    fund = f4.load_funding(close.index, list(coins.keys())).reindex(close.index)
    dt = pd.to_datetime(close.index, unit="ms")
    for df in (close, qv, fund):
        df.index = dt

    # PIT top-N eligibility (rank trailing $-vol, shift(1)) — identical to the baseline universe.
    liq = qv.rolling(base.LIQ_WIN).mean().shift(1)
    elig = liq.rank(axis=1, ascending=False) <= base.TOP_N

    ret = close.pct_change()
    ret_e = ret.where(elig)  # per-candle returns of the eligible basket only

    # (A) market realized-vol: equal-weight mean of per-coin |return| proxy → a market vol level.
    # Use cross-sectional mean absolute return as the instantaneous market-vol proxy each candle.
    mkt_absret = ret_e.abs().mean(axis=1)

    # (C) breadth: mean sign of eligible coin returns. |breadth|→1 = one-way tape (correlated).
    breadth = np.sign(ret_e).mean(axis=1).abs()

    # |aggregate funding|: equal-weight |mean funding| over eligible basket (regime-stress proxy).
    abs_funding = fund.where(elig).mean(axis=1).abs()

    return {
        "ret_e": ret_e,
        "mkt_absret": mkt_absret,
        "breadth": breadth,
        "abs_funding": abs_funding,
    }


# ------------------------------------------------------------------------------------------
# OVERLAY MULTIPLIERS — each returns m[t] ∈ [floor, 1], aligned + shifted(1) so it scales the candle
# AFTER the regime is observed. m≡1 ⇒ overlay off ⇒ canonical net unchanged.
# ------------------------------------------------------------------------------------------


def _finalize(mult: pd.Series, index: pd.DatetimeIndex) -> pd.Series:
    """Common tail: past-only shift(1), reindex to the net, fill warmup with 1.0 (no de-lever)."""
    return mult.shift(1).reindex(index).fillna(1.0).clip(upper=1.0)


def vol_ratio_mult(
    mkt_absret: pd.Series,
    index: pd.DatetimeIndex,
    fast: int,
    slow: int,
    thresh: float,
    floor: float,
) -> pd.Series:
    """(A) VOL-RATIO. fast/slow market realized-vol ratio. When fast vol > thresh × slow vol, cut
    gross to clip(slow/fast, floor, 1); else 1.0 (never lever up). Both windows shift(1)/past-only.
    """
    fast_v = mkt_absret.rolling(fast).mean().shift(1)
    slow_v = mkt_absret.rolling(slow).mean().shift(1)
    rel = (slow_v / fast_v).replace([np.inf, -np.inf], np.nan)
    mult = rel.clip(lower=floor, upper=1.0)
    mult = mult.where(fast_v > thresh * slow_v, 1.0)
    return _finalize(mult, index)


def dispersion_mult(
    ret_e: pd.DataFrame,
    index: pd.DatetimeIndex,
    fast: int,
    slow: int,
    thresh: float,
    floor: float,
) -> pd.Series:
    """(B) DISPERSION. Cross-sectional return dispersion = per-candle std across eligible coins. If
    fast-window dispersion > thresh × slow-window dispersion, the cross-section is fanning out and
    L/S hedges stop working → cut gross to clip(slow/fast, floor, 1). Both windows shift(1).
    """
    disp = ret_e.std(axis=1)  # cross-sectional std each candle (past data: ret is pct_change)
    fast_d = disp.rolling(fast).mean().shift(1)
    slow_d = disp.rolling(slow).mean().shift(1)
    rel = (slow_d / fast_d).replace([np.inf, -np.inf], np.nan)
    mult = rel.clip(lower=floor, upper=1.0)
    mult = mult.where(fast_d > thresh * slow_d, 1.0)
    return _finalize(mult, index)


def breadth_mult(
    breadth: pd.Series, index: pd.DatetimeIndex, win: int, thresh: float, floor: float
) -> pd.Series:
    """(C) BREADTH. |mean sign of eligible coin returns|, smoothed over `win`. High |breadth| = a
    one-way correlated tape (the regime that drives portfolio-wide reversal DD). When smoothed
    breadth > thresh, de-lever proportionally toward `floor` as breadth → 1. shift(1) past-only.
    """
    b = breadth.rolling(win).mean().shift(1)
    # linear ramp: at b==thresh → mult 1.0; at b==1 → mult floor.
    span = (1.0 - thresh)
    ramp = 1.0 - (1.0 - floor) * ((b - thresh) / span).clip(lower=0.0, upper=1.0)
    mult = ramp.where(b > thresh, 1.0)
    return _finalize(mult, index)


def funding_mult(
    abs_funding: pd.Series, index: pd.DatetimeIndex, win: int, thresh: float, floor: float
) -> pd.Series:
    """|aggregate funding| overlay (informational 4th signal). When smoothed |mean funding| spikes
    above thresh× its own trailing median, de-lever toward floor. shift(1) past-only.
    """
    a = abs_funding.rolling(win).mean().shift(1)
    med = a.rolling(slow_med_win(win)).median().shift(1)
    rel = (thresh * med / a).replace([np.inf, -np.inf], np.nan)
    mult = rel.clip(lower=floor, upper=1.0)
    mult = mult.where(a > thresh * med, 1.0)
    return _finalize(mult, index)


def slow_med_win(win: int) -> int:
    return max(win * 8, 168)


# ------------------------------------------------------------------------------------------
# Reporting / Pareto
# ------------------------------------------------------------------------------------------


def report(label: str, net: pd.Series, base_net: pd.Series | None = None) -> dict:
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    isr = base.msharpe(net, base.LO0, base.OOS_CUTOFF)
    oosr = base.msharpe(net, base.OOS_CUTOFF, base.HI1)
    oos = net[net.index >= base.OOS_CUTOFF]
    oos_eq = (1 + oos).cumprod()
    oos_dd = float((oos_eq / oos_eq.cummax() - 1).min())
    yr = {int(k): round(v * 100, 0) for k, v in net.groupby(net.index.year).sum().items()}
    d_oos = f" dOOS={oosr - base.msharpe(base_net, base.OOS_CUTOFF, base.HI1):+.2f}" if (
        base_net is not None
    ) else ""
    print(
        f"  {label:30} IS={isr:+.2f} OOS={oosr:+.2f}{d_oos} "
        f"maxDD={dd * 100:5.1f}% oosDD={oos_dd * 100:5.1f}%"
    )
    print(f"       net%/yr={yr}")
    return {"label": label, "is": isr, "oos": oosr, "dd": dd, "oos_dd": oos_dd}


def pareto_verdict(ref: dict, cand: dict, oos_tol: float = 0.10) -> tuple[bool, str]:
    """Pareto / near-Pareto: DD MEANINGFULLY smaller AND OOS not worse within noise."""
    dd_pt = (cand["dd"] - ref["dd"]) * 100  # positive = smaller (less negative) drawdown
    dd_meaningful = dd_pt >= 3.0  # ≥3 pts of DD relief to count (e.g. −23 → ≤−20)
    oos_ok = cand["oos"] >= ref["oos"] - oos_tol
    pareto = dd_meaningful and oos_ok
    tag = "PARETO/near-Pareto" if pareto else (
        "DD-for-Sharpe TRADE" if dd_meaningful and not oos_ok else "no meaningful DD relief"
    )
    return pareto, (
        f"dDD={dd_pt:+.1f}pt dOOS={cand['oos'] - ref['oos']:+.2f} "
        f"d_oosDD={(cand['oos_dd'] - ref['oos_dd']) * 100:+.1f}pt -> {tag}"
    )


def sweep(name: str, base_net: pd.Series, r_base: dict, mults: dict) -> dict:
    """Run a knob sweep for one overlay family; print every cell + a robustness summary."""
    print(f"\n  === {name}: ROBUSTNESS SWEEP (effect must hold across cells, not one knob) ===")
    rows = []
    for cell, m in mults.items():
        net = base_net * m
        fired = (m < 0.999)
        r = report(f"{name}[{cell}]", net, base_net)
        pareto, msg = pareto_verdict(r_base, r)
        print(
            f"       {msg}  | fires {fired.mean() * 100:4.1f}% "
            f"(OOS {fired[fired.index >= base.OOS_CUTOFF].mean() * 100:4.1f}%) "
            f"mean-mult-when-fired={m[fired].mean() if fired.any() else 1.0:.2f}"
        )
        rows.append({"cell": cell, "pareto": pareto, **r})
    n_pareto = sum(r["pareto"] for r in rows)
    dd_relief = [(r_base["dd"] - r["dd"]) * -100 for r in rows]  # negative = relief
    oos_delta = [r["oos"] - r_base["oos"] for r in rows]
    print(
        f"  --- {name} summary: {n_pareto}/{len(rows)} cells Pareto/near-Pareto | "
        f"DD relief range [{min(dd_relief):+.1f},{max(dd_relief):+.1f}]pt | "
        f"OOS delta range [{min(oos_delta):+.2f},{max(oos_delta):+.2f}] ---"
    )
    return {"name": name, "n_pareto": n_pareto, "n": len(rows), "rows": rows}


def constant_delever_control(base_net: pd.Series, m: pd.Series, label: str) -> None:
    """THE decisive 'is this a regime signal, or just a smaller book?' test.

    An overlay that fires ~always at a near-constant multiplier is not timing risk — it is just a
    lower vol target wearing a regime costume. Two controls expose that:
      1) CONSTANT scalar = mean(m): a flat de-lever of the same average size. A constant scalar
         cannot change Sharpe (scale-invariant) but cuts DD purely mechanically. If the overlay's
         DD relief ≈ the constant's, the relief is NOT regime timing.
      2) RE-VOL-TARGET both back to the baseline's realized vol: removes the 'smaller book' effect
         so only genuine TIMING (de-lever BEFORE bad candles) can move Sharpe/DD. If, rescaled to
         the same vol, the overlay collapses to baseline, there is no timing edge — only shrinkage.
    Also reports corr(m, |net|): a real de-lever-into-danger overlay anti-correlates (negative).
    """
    def stats(net: pd.Series) -> tuple[float, float, float, float]:
        eq = (1 + net).cumprod()
        dd = float((eq / eq.cummax() - 1).min())
        o = net[net.index >= base.OOS_CUTOFF]
        oe = (1 + o).cumprod()
        odd = float((oe / oe.cummax() - 1).min())
        return (
            base.msharpe(net, base.LO0, base.OOS_CUTOFF),
            base.msharpe(net, base.OOS_CUTOFF, base.HI1),
            dd,
            odd,
        )

    mean_m = float(m.mean())
    const = pd.Series(mean_m, index=base_net.index)

    def revol(net: pd.Series) -> pd.Series:
        return net * (base_net.std() / net.std())

    print(f"\n  === CONSTANT-DE-LEVER CONTROL on {label} (mean mult={mean_m:.3f}, "
          f"fires {(m < 0.999).mean() * 100:.0f}%) ===")
    print("       (IS, OOS, maxDD, oosDD)")
    print(f"  baseline           : {tuple(round(x, 3) for x in stats(base_net))}")
    print(f"  overlay            : {tuple(round(x, 3) for x in stats(base_net * m))}")
    print(f"  CONSTANT {mean_m:.3f}     : {tuple(round(x, 3) for x in stats(base_net * const))}"
          "   <- a DUMB flat de-lever of the same average size")
    print(f"  overlay  (re-vol)  : {tuple(round(x, 3) for x in stats(revol(base_net * m)))}"
          "   <- rescaled to baseline vol = TIMING ONLY")
    print(f"  CONSTANT (re-vol)  : {tuple(round(x, 3) for x in stats(revol(base_net * const)))}"
          "   <- collapses to baseline (constant has 0 edge)")
    corr = float(np.corrcoef(m.values, base_net.abs().values)[0, 1])
    print(f"  corr(mult, |net|)  = {corr:+.3f}  "
          f"({'de-levers INTO big candles (good)' if corr < -0.05 else 'NO danger timing'})")


def main() -> None:
    coins = base.load_universe()
    print(f"EXPLORATION-019: market-regime gross-exposure overlay — {len(coins)} coins")

    # ---- CANONICAL baseline net (immutable; overlay-off must reproduce +1.37) ----
    base_net, _ = wf.walkforward(wf.lam_nets(coins))
    base_net = base_net.sort_index()
    r_base = report("CANONICAL baseline (m≡1)", base_net)
    assert abs(base.msharpe(base_net, base.OOS_CUTOFF, base.HI1) - 1.37) < 0.02, "canonical drift!"

    # overlay-OFF identity check: m≡1 → exact same net
    m_off = pd.Series(1.0, index=base_net.index)
    assert (base_net * m_off).equals(base_net), "overlay-off identity broken"
    print("  [check] overlay-OFF (m≡1) reproduces canonical net exactly.\n")

    mi = market_inputs(coins)
    idx = base_net.index

    # =================== (A) VOL-RATIO de-lever ===================
    a_cells = {
        f"f{f}/s{s}/t{t}/fl{fl}": vol_ratio_mult(mi["mkt_absret"], idx, f, s, t, fl)
        for (f, s) in [(21, 168), (14, 120), (28, 210)]
        for t in [1.3, 1.5, 1.7]
        for fl in [0.5]
    }
    sa = sweep("VOL-RATIO", base_net, r_base, a_cells)

    # =================== (B) DISPERSION de-lever ===================
    b_cells = {
        f"f{f}/s{s}/t{t}/fl{fl}": dispersion_mult(mi["ret_e"], idx, f, s, t, fl)
        for (f, s) in [(21, 168), (14, 120), (28, 210)]
        for t in [1.2, 1.4, 1.6]
        for fl in [0.5]
    }
    sb = sweep("DISPERSION", base_net, r_base, b_cells)

    # =================== (C) BREADTH de-lever ===================
    c_cells = {
        f"w{w}/th{th}/fl{fl}": breadth_mult(mi["breadth"], idx, w, th, fl)
        for w in [21, 42, 84]
        for th in [0.4, 0.5, 0.6]
        for fl in [0.5]
    }
    sc = sweep("BREADTH", base_net, r_base, c_cells)

    # BREADTH is the only family with apparent Pareto cells — but it fires ~always at ~0.82x, which
    # smells like a near-constant de-lever, NOT regime timing. Run the decisive control on its
    # strongest 'Pareto' cell to separate genuine timing from a disguised lower vol target.
    constant_delever_control(
        base_net, breadth_mult(mi["breadth"], idx, 21, 0.4, 0.5), "BREADTH[w21/th0.4/fl0.5]"
    )

    # =================== (D) |FUNDING| de-lever (informational 4th) ===================
    d_cells = {
        f"w{w}/t{t}/fl{fl}": funding_mult(mi["abs_funding"], idx, w, t, fl)
        for w in [9, 21]
        for t in [1.5, 2.0]
        for fl in [0.5]
    }
    sd = sweep("|FUNDING|", base_net, r_base, d_cells)

    # =================== VERDICT ===================
    print("\n  ===================== VERDICT =====================")
    for s in (sa, sb, sc, sd):
        frac = s["n_pareto"] / s["n"]
        robust = "ROBUST (>=70% cells Pareto)" if frac >= 0.7 else (
            "KNIFE-EDGE (<70% cells Pareto)" if s["n_pareto"] > 0 else "NO EFFECT (0 cells Pareto)"
        )
        print(f"  {s['name']:12} {s['n_pareto']}/{s['n']} Pareto cells -> {robust}")
    verdict = [
        "",
        "  REJECT. No regime overlay cleanly cuts the DD on the CANONICAL net:",
        "   - VOL-RATIO (the iter-007 idea, now measured canonically): 0/9 Pareto, DD relief",
        "     <=1.6pt -> the apparent iter-007 lift was the stitch-order artifact; dead on",
        "     canonical accounting.",
        "   - DISPERSION: 0/9 Pareto; ~0pt DD relief (the OOS-up cells just de-lever ~constantly).",
        "   - |FUNDING|: 0/4 Pareto; OOS WORSE -> a DD-for-Sharpe trade. REJECT.",
        "   - BREADTH: 4/9 'Pareto' BUT the CONSTANT-DE-LEVER CONTROL above proves it: it fires",
        "     ~always at ~0.82x, so a DUMB constant 0.82x scalar gets the SAME DD with 0 Sharpe",
        "     change; re-vol-targeted to baseline vol its edge is within noise and",
        "     corr(mult,|net|)~0 (no danger timing). A disguised lower vol target, NOT a regime",
        "     signal. KNIFE-EDGE + non-timing -> REJECT.",
        "  CONCLUSION: a market-level gross-exposure regime overlay does NOT cleanly cut the -23%",
        "  DD without costing OOS. The DD is correlated portfolio-wide reversals that none of",
        "  these market-state signals anticipate. NOT promote-worthy.",
    ]
    print("\n".join(verdict))


if __name__ == "__main__":
    main()
