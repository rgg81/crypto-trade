"""metals-portfolio CONFIRMATION — OOS REVEAL + full gauntlet on the 4-sleeve book.

THE CAPSTONE. The user has authorised revealing the held-out OOS (t >= OOS_CUTOFF 2025-03-24).
The four EXPLORATIONs (iter_001..iter_004) only ever scored IN-SAMPLE; the OOS data was on disk
the whole time but NEVER looked at. This is the moment it is allowed to be revealed.

This script MEASURES, it does NOT fit. Every parameter is FROZEN from the IS explorations:
  - anchor: EMA84/189, FLOOR 0.5          (iter_001 center)
  - dispersion: ALPHA 0.5, vol_win 84     (iter_002 center)
  - pt/pd: Z_WIN 126, BETA 0.25           (iter_003 center)
  - COT: GAMMA 0.25, Z_WIN 78             (iter_004 center)
The ONLY allowed change is the Critic's PRE-REGISTERED conservatism tightening: COT lag_days 6 -> 7
(strictly MORE conservative — Tuesday + 7d clears even a Monday-delayed holiday-week release with a
full extra day of slack; can only REMOVE information, never add it). IS at lag=7 is reported
alongside the committed lag=6 IS to confirm it is ~unchanged.

LAYERED books (parity-correct raw-sum -> ONE net_from_raw, reusing ov.gross_norm = gn):
  L1 anchor       : gn(it.build_raw(coins))
  L2 +dispersion  : + 0.5 ·gn(ov.mn_dispersion_raw(close))
  L3 +COT(ROBUST) : + 0.25·gn(cot_mm_contrarian_raw(..., z_win=78, lag_days=7))  [anchor+disp+COT]
  L4 +pt/pd(FULL) : + 0.25·gn(i3.ptpd_raw(close, 126))                           [the full 4-sleeve]
L3 is the DEFENSIBLE baseline candidate (pt/pd is PROMOTABLE=False/thin-n). L4 shows whether the
thin sleeve helps OOS. Books reported SEPARATELY.

The book is DETERMINISTIC (no RNG in any sleeve) -> "multi-seed" is N/A. Robustness here is
STRUCTURAL (the IS parameter sweeps already done in iter_001..iter_004), not seed-based.

OOS may DISAPPOINT. The numbers are reported STRAIGHT. A falsified-OOS result honestly reported is
the correct outcome, not a failure to hide.
"""

from __future__ import annotations

import iter_001_trend as it  # noqa: E402  (anchor; build_raw is the parity-correct raw book)
import iter_002_mn_overlay as ov  # noqa: E402  (gross_norm + mn_dispersion_raw — the 0.5· arm)
import iter_003_ptpd as i3  # noqa: E402  (ptpd_raw — the 0.25· arm + Z_WIN=126)
import iter_004_cot as i4  # noqa: E402  (cot_mm_contrarian_raw — the 0.25· arm)
import numpy as np
import pandas as pd
from universe_metals import (
    COST_SIDE,
    HI1,
    LO0,
    OOS_CUTOFF,
    PORT_VOL_WIN,
    VOL_WIN,
    load_metals,
    maxdd,
    msharpe,
    net_from_raw,
    panels,
    turnover,
    vol_target,
)

gn = ov.gross_norm  # gross-normalise a raw book to unit gross per bar (the parity primitive)

# ── FROZEN config (every value inherited from the IS explorations — NOT re-tuned here) ───────
ALPHA_DISP = ov.ALPHA  # 0.5   dispersion mixing weight        (iter_002 center)
BETA_PTPD = i3.BETA  # 0.25  pt/pd mixing weight             (iter_003 center)
PTPD_ZWIN = i3.Z_WIN  # 126   pt/pd z-score window            (iter_003 center)
GAMMA_COT = i4.GAMMA  # 0.25  COT mixing weight               (iter_004 center)
COT_ZWIN = i4.Z_WIN  # 78    COT z-score window              (iter_004 center)

# ── Critic PRE-REGISTERED conservatism tightening (the ONLY allowed change) ──────────────────
COT_LAG_IS = i4.RELEASE_LAG_DAYS  # 6  — the committed IS lag (Tuesday + 6d = next Monday)
COT_LAG_CONFIRM = 7  # 7 — strictly MORE conservative (a full extra day of release slack)

GS: tuple[str, ...] = ("XAUUSDT", "XAGUSDT")  # gold/silver — the deep-history (2015+) COT legs

# ── Cost-stress baseline (the foundation COST_SIDE = 6bps/side; stressed at 1x and 2x) ───────
_COST_SIDE = COST_SIDE

# ── OOS era markers ──────────────────────────────────────────────────────────────────────────
OOS_YEARS = (2025, 2026)  # any net falling in these years (and t >= OOS_CUTOFF) is OOS

NAMES = {"XAUUSDT": "gold", "XAGUSDT": "silver", "XPTUSDT": "platinum", "XPDUSDT": "palladium"}


# ── raw-book constructors (parity-correct; ONE net_from_raw per layer at call site) ─────────
def _raw_anchor(coins) -> pd.DataFrame:
    """L1 raw: gross-normed long-biased trend anchor."""
    return gn(it.build_raw(coins))


def _raw_disp(close) -> pd.DataFrame:
    """0.5· gross-normed dollar-neutral dispersion overlay (iter_002 center)."""
    return ALPHA_DISP * gn(ov.mn_dispersion_raw(close))


def _raw_cot(coins, cot, *, lag_days: int, cot_cols=i4.TRADEABLE) -> pd.DataFrame:
    """0.25· gross-normed COT managed-money contrarian sleeve (iter_004; lag pre-registered)."""
    return GAMMA_COT * gn(
        i4.cot_mm_contrarian_raw(coins, cot, COT_ZWIN, cols=cot_cols, lag_days=lag_days)
    )


def _raw_ptpd(close) -> pd.DataFrame:
    """0.25· gross-normed platinum-vs-palladium reversion sleeve (iter_003 center; thin-n)."""
    return BETA_PTPD * gn(i3.ptpd_raw(close, PTPD_ZWIN))


def build_layers(
    coins, cot, *, lag_days: int = COT_LAG_CONFIRM, cot_cols=i4.TRADEABLE
) -> dict[str, tuple[pd.Series, pd.DataFrame]]:
    """Construct L1..L4 as cumulative raw-sums, each through a SINGLE net_from_raw.

    L1 anchor; L2 +dispersion; L3 +COT (ROBUST baseline, no pt/pd); L4 +pt/pd (FULL 4-sleeve).
    Returns {layer: (net, weight_book)}.
    """
    pan = panels(coins)
    close, ret_fwd = pan["close"], pan["ret_fwd"]
    r_anchor = _raw_anchor(coins)
    r_disp = _raw_disp(close)
    r_cot = _raw_cot(coins, cot, lag_days=lag_days, cot_cols=cot_cols)
    r_ptpd = _raw_ptpd(close)
    raws = {
        "L1 anchor": r_anchor,
        "L2 +dispersion": r_anchor + r_disp,
        "L3 +COT(ROBUST)": r_anchor + r_disp + r_cot,
        "L4 +ptpd(FULL)": r_anchor + r_disp + r_cot + r_ptpd,
    }
    return {k: net_from_raw(v, ret_fwd) for k, v in raws.items()}


# ── cost-stress: rebuild the net with a scaled COST_SIDE (everything else frozen) ───────────
def _net_with_cost(raw: pd.DataFrame, ret_fwd: pd.DataFrame, cost_side: float) -> pd.Series:
    """net_from_raw with an OVERRIDDEN per-side cost (cost-stress table); same accounting."""
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w = raw.div(gross, axis=0).fillna(0.0).shift(1)
    pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
    cost = cost_side * (w - w.shift(1)).abs().sum(axis=1)
    net = (pnl - cost).dropna()
    return vol_target(net)


def _raw_for_layer(coins, cot, layer: str, *, lag_days: int) -> pd.DataFrame:
    """Reconstruct the cumulative raw book for a named layer (for the cost-stress rebuild)."""
    pan = panels(coins)
    close = pan["close"]
    r = _raw_anchor(coins)
    if layer in ("L2 +dispersion", "L3 +COT(ROBUST)", "L4 +ptpd(FULL)"):
        r = r + _raw_disp(close)
    if layer in ("L3 +COT(ROBUST)", "L4 +ptpd(FULL)"):
        r = r + _raw_cot(coins, cot, lag_days=lag_days)
    if layer == "L4 +ptpd(FULL)":
        r = r + _raw_ptpd(close)
    return r


# ── benchmarks (vol-targeted to the same ~15% so the comparison is risk-adjusted/fair) ──────
def bench_buy_hold_gold(coins) -> pd.Series:
    """Buy-and-hold GOLD, vol-targeted to ~15% (same target as the book) — fair bar."""
    pan = panels(coins)
    raw = pd.DataFrame(0.0, index=pan["close"].index, columns=pan["close"].columns)
    elig = pan["close"]["XAUUSDT"].notna()
    raw["XAUUSDT"] = elig.astype(float)  # constant unit long in gold while it has price history
    net, _ = net_from_raw(raw, pan["ret_fwd"])
    return net


def bench_equal_weight_basket(coins) -> pd.Series:
    """Equal-weight LONG-ONLY 4-metal basket, vol-targeted to ~15% — the diversified long bar."""
    pan = panels(coins)
    close = pan["close"]
    raw = close.notna().astype(float)  # +1 to every present metal each bar (gross-norm equalises)
    net, _ = net_from_raw(raw, pan["ret_fwd"])
    return net


# ── reporting helpers ────────────────────────────────────────────────────────────────────────
def _is_oos_sharpe(net: pd.Series) -> tuple[float, float]:
    """(IS Sharpe over [LO0, OOS_CUTOFF), OOS Sharpe over [OOS_CUTOFF, HI1))."""
    return msharpe(net, LO0, OOS_CUTOFF), msharpe(net, OOS_CUTOFF, HI1)


def _is_oos_maxdd(net: pd.Series) -> tuple[float, float]:
    """(IS-window maxDD%, OOS-window maxDD%) — each computed on its own slice (no cross-leak)."""
    is_dd = maxdd(net[net.index < OOS_CUTOFF]) * 100
    oos_dd = (
        maxdd(net[net.index >= OOS_CUTOFF]) * 100
        if (net.index >= OOS_CUTOFF).any()
        else float("nan")
    )
    return is_dd, oos_dd


def _is_oos_nettot(net: pd.Series) -> tuple[float, float]:
    """(IS net total %, OOS net total %) — additive per-candle net summed within each window."""
    is_tot = net[net.index < OOS_CUTOFF].sum() * 100
    oos_tot = net[net.index >= OOS_CUTOFF].sum() * 100
    return is_tot, oos_tot


def _year_net(net: pd.Series) -> dict[int, float]:
    """Per-year net% (sum of per-candle net within each calendar year, in percent) — full span."""
    return {int(y): round(v * 100, 1) for y, v in net.groupby(net.index.year).sum().items()}


def _sep(title: str) -> None:
    print(f"\n{'=' * 92}\n{title}\n{'=' * 92}")


# ════════════════════════════════════════════════════════════════════════════════════════════
def main() -> None:
    coins = load_metals()
    cot = i4.load_cot()
    pan = panels(coins)
    close, ret_fwd = pan["close"], pan["ret_fwd"]
    data_end = close.index.max()

    print("metals-portfolio CONFIRMATION — OOS REVEAL + full gauntlet on the 4-sleeve book")
    print(f"  universe {tuple(coins)}")
    print(f"  IS  window: data start .. {OOS_CUTOFF.date()}  (exclusive)")
    print(f"  OOS window: {OOS_CUTOFF.date()} .. {data_end.date()}  (the held-out reveal)")
    print(
        f"  FROZEN params: anchor EMA{it.EMA_FAST}/{it.EMA_SLOW} FLOOR{it.FLOOR} | "
        f"disp a={ALPHA_DISP} | COT g={GAMMA_COT} zwin={COT_ZWIN} | "
        f"ptpd b={BETA_PTPD} zwin={PTPD_ZWIN}"
    )
    print(
        f"  COT lag: IS committed=+{COT_LAG_IS}d  ->  CONFIRMATION=+{COT_LAG_CONFIRM}d "
        "(Critic pre-registered conservatism tightening; strictly more conservative)"
    )
    print("  DETERMINISTIC book (no RNG) -> multi-seed N/A; robustness is STRUCTURAL (IS sweeps).")

    # ── 0. NO-RE-TUNING / lag=7 ~ lag=6 IS confirmation ──────────────────────────────────────
    _sep("[0] NO-RE-TUNING CHECK — lag=7 IS ~ committed lag=6 IS (params otherwise frozen)")
    lay6 = build_layers(coins, cot, lag_days=COT_LAG_IS)
    lay7 = build_layers(coins, cot, lag_days=COT_LAG_CONFIRM)
    print(f"  {'layer':18} {'IS_Sharpe(lag6)':>16} {'IS_Sharpe(lag7)':>16} {'Δ(7-6)':>10}")
    for k in lay6:
        s6 = msharpe(lay6[k][0], LO0, OOS_CUTOFF)
        s7 = msharpe(lay7[k][0], LO0, OOS_CUTOFF)
        print(f"  {k:18} {s6:>16.3f} {s7:>16.3f} {s7 - s6:>+10.3f}")
    print(
        "  -> lag=7 only AFFECTS the two COT-bearing layers (L3/L4); L1/L2 IS bit-identical. "
        "Δ small ⇒ no re-tuning, just a strictly-conservative shift."
    )

    layers = lay7  # CONFIRMATION uses the pre-registered lag=7 throughout the rest of the gauntlet

    # ── 1. HEADLINE table (IS vs OOS side by side) ───────────────────────────────────────────
    _sep("[1] HEADLINE — IS vs OOS side by side (book at frozen params, COT lag=7)")
    hdr = (
        f"  {'layer':18} {'IS_SR':>7} {'OOS_SR':>7} {'IS_DD%':>8} {'OOS_DD%':>8} "
        f"{'turn/c':>8} {'IS_net%':>9} {'OOS_net%':>9}"
    )
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    headline: dict[str, dict[str, float]] = {}
    for k, (net, w) in layers.items():
        is_sr, oos_sr = _is_oos_sharpe(net)
        is_dd, oos_dd = _is_oos_maxdd(net)
        is_tot, oos_tot = _is_oos_nettot(net)
        tnov = turnover(w, LO0, HI1)
        headline[k] = {"is_sr": is_sr, "oos_sr": oos_sr, "is_dd": is_dd, "oos_dd": oos_dd}
        print(
            f"  {k:18} {is_sr:>7.2f} {oos_sr:>7.2f} {is_dd:>8.1f} {oos_dd:>8.1f} "
            f"{tnov:>8.4f} {is_tot:>9.1f} {oos_tot:>9.1f}"
        )

    # ── 2. PER-YEAR net% — full (L4) and robust (L3), every year, OOS years marked ──────────
    _sep("[2] PER-YEAR net% — L3 (ROBUST) and L4 (FULL); 2025/2026 are OOS (post-cutoff)")
    net_l3, net_l4 = layers["L3 +COT(ROBUST)"][0], layers["L4 +ptpd(FULL)"][0]
    y3, y4 = _year_net(net_l3), _year_net(net_l4)
    print(f"  {'year':>6} {'L3_net%':>10} {'L4_net%':>10}   window")
    for y in sorted(set(y3) | set(y4)):
        win = "OOS" if y in OOS_YEARS else "IS "
        note = "  (partial: OOS starts 2025-03-24)" if y == 2025 else ""
        print(f"  {y:>6} {y3.get(y, 0.0):>10.1f} {y4.get(y, 0.0):>10.1f}   {win}{note}")

    # ── 3. COST-STRESS — L3 & L4 OOS Sharpe at 1x and 2x COST_SIDE ───────────────────────────
    _sep(
        f"[3] COST-STRESS — OOS Sharpe at 1x ({_COST_SIDE * 1e4:.0f}bps/side) "
        f"and 2x ({_COST_SIDE * 2e4:.0f}bps/side)"
    )
    print(f"  {'layer':18} {'OOS_SR@1x':>11} {'OOS_SR@2x':>11} {'ΔSR':>8}")
    for k in ("L2 +dispersion", "L3 +COT(ROBUST)", "L4 +ptpd(FULL)"):
        raw = _raw_for_layer(coins, cot, k, lag_days=COT_LAG_CONFIRM)
        n1 = _net_with_cost(raw, ret_fwd, _COST_SIDE)
        n2 = _net_with_cost(raw, ret_fwd, 2 * _COST_SIDE)
        sr1 = msharpe(n1, OOS_CUTOFF, HI1)
        sr2 = msharpe(n2, OOS_CUTOFF, HI1)
        print(f"  {k:18} {sr1:>11.3f} {sr2:>11.3f} {sr2 - sr1:>+8.3f}")

    # ── 4. BENCHMARKS — buy-hold gold + equal-weight basket (vol-targeted, IS+OOS) ──────────
    _sep("[4] BENCHMARKS (vol-targeted to ~15% for fairness) — book must beat BOTH on OOS Sharpe")
    bh = bench_buy_hold_gold(coins)
    ew = bench_equal_weight_basket(coins)
    bh_is, bh_oos = _is_oos_sharpe(bh)
    ew_is, ew_oos = _is_oos_sharpe(ew)
    print(f"  {'series':28} {'IS_SR':>8} {'OOS_SR':>8}")
    print(f"  {'buy-hold gold (XAU, VT15%)':28} {bh_is:>8.2f} {bh_oos:>8.2f}")
    print(f"  {'equal-weight 4-metal (VT15%)':28} {ew_is:>8.2f} {ew_oos:>8.2f}")
    print("  --")
    for k in ("L3 +COT(ROBUST)", "L4 +ptpd(FULL)"):
        h = headline[k]
        beats_bh = h["oos_sr"] > bh_oos
        beats_ew = h["oos_sr"] > ew_oos
        print(
            f"  {k:28} {h['is_sr']:>8.2f} {h['oos_sr']:>8.2f}   "
            f"beats_gold={beats_bh}  beats_basket={beats_ew}"
        )

    # ── 5. COT OOS FALSIFIER — marginal lift FULL vs GOLD/SILVER-ONLY (palladium-reliance) ──
    _sep("[5] COT-SLEEVE OOS FALSIFIER — marginal lift must rest on gold/silver, not thin pt/pd")
    # Marginal COT lift = (anchor+disp+COT) - (anchor+disp), i.e. L3 - L2; FULL and GS-only.
    net_l2 = layers["L2 +dispersion"][0]
    l3_full = layers["L3 +COT(ROBUST)"][0]
    lay7_gs = build_layers(coins, cot, lag_days=COT_LAG_CONFIRM, cot_cols=GS)
    l3_gs = lay7_gs["L3 +COT(ROBUST)"][0]
    for label, l3 in (("FULL (XAU/XAG/XPT/XPD COT)", l3_full), ("GOLD/SILVER-ONLY COT", l3_gs)):
        is_lift = msharpe(l3, LO0, OOS_CUTOFF) - msharpe(net_l2, LO0, OOS_CUTOFF)
        oos_lift = msharpe(l3, OOS_CUTOFF, HI1) - msharpe(net_l2, OOS_CUTOFF, HI1)
        print(f"  COT marginal lift  {label:30} IS Δ={is_lift:+.3f}  OOS Δ={oos_lift:+.3f}")
    print(
        "  -> durable claim requires the GOLD/SILVER-ONLY OOS lift to be POSITIVE "
        "(edge not reliant on thin palladium/platinum COT)."
    )

    # ── 6. PRE-REGISTERED FALSIFIERS, now OOS ────────────────────────────────────────────────
    _sep("[6] PRE-REGISTERED FALSIFIERS (now OOS)")
    # (i) each added sleeve's marginal lift must stay POSITIVE in OOS (not just IS)
    print("  (i) per-sleeve MARGINAL lift (Δ vs the layer below) — IS and OOS:")
    order = ["L1 anchor", "L2 +dispersion", "L3 +COT(ROBUST)", "L4 +ptpd(FULL)"]
    nets = {k: layers[k][0] for k in order}
    print(f"      {'added sleeve':24} {'IS_Δ':>9} {'OOS_Δ':>9}  OOS_positive")
    for i in range(1, len(order)):
        below, above = order[i - 1], order[i]
        is_d = msharpe(nets[above], LO0, OOS_CUTOFF) - msharpe(nets[below], LO0, OOS_CUTOFF)
        oos_d = msharpe(nets[above], OOS_CUTOFF, HI1) - msharpe(nets[below], OOS_CUTOFF, HI1)
        print(f"      {above:24} {is_d:>+9.3f} {oos_d:>+9.3f}  {oos_d > 0}")
    # (ii) per-asset OOS active-candle count (flag thin pt/pd OOS)
    print("\n  (ii) per-asset OOS active-candle count (raw-book nonzero) — flag thin pt/pd:")
    w_l4 = layers["L4 +ptpd(FULL)"][1]
    w_oos = w_l4[w_l4.index >= OOS_CUTOFF]
    n_oos = len(w_oos)
    print(f"      OOS candles total = {n_oos}")
    for c in w_oos.columns:
        active = int((w_oos[c].abs() > 1e-12).sum())
        thin = "  <- THIN" if active < 0.5 * n_oos else ""
        print(
            f"      {c} ({NAMES.get(c, c):9}) active={active}/{n_oos} = "
            f"{100 * active / n_oos:4.0f}%{thin}"
        )

    # ── 7. DSR (deflated Sharpe) — deflate OOS Sharpe for multiple-testing across the program ──
    _sep("[7] DSR — deflate the book's OOS Sharpe for the EXPLORATION program's multiple testing")
    # Honest N_eff: ~6 axes (anchor / dispersion / ptpd / COT / 2 benchmark families) each with a
    # handful of reported config cells. We count the DISTINCT center-config decisions actually made
    # plus the sweep cells reported (no cherry-pick: every cell was printed). Upper-bound N_eff.
    n_axes = 6
    cells_per_axis = (
        12  # the largest reported sweep (iter_004 g×zwin = 12); conservative upper bound
    )
    n_eff = n_axes * cells_per_axis  # ~72 — deliberately generous (inflates the deflation hurdle)
    # Bailey/Lopez de Prado deflation, DIMENSIONALLY CORRECT:
    #   E[max SR | null] = SR_std · Z(N_eff),  where Z(N_eff) = expected max of N_eff iid N(0,1).
    # The annualised-monthly Sharpe estimator's std error ≈ sqrt(12 / n_months) (monthly SR std
    # ≈ 1/sqrt(n_months), annualised ×sqrt12). n_months is the OOS observation count — small here,
    # so SR_std is large and the hurdle is honestly demanding.
    gamma_em = 0.5772156649
    z = np.sqrt(2.0 * np.log(n_eff))
    z_factor = (1 - gamma_em) * z + gamma_em * (np.sqrt(2.0 * np.log(n_eff * np.e)) - z)
    # n_months from the L3 OOS slice (same for L4 — identical index)
    _oos_l3 = net_l3[(net_l3.index >= OOS_CUTOFF) & (net_l3.index < HI1)]
    n_months = len(_oos_l3.groupby(_oos_l3.index.to_period("M")).sum())
    sr_std = np.sqrt(12.0 / n_months)  # std error of the annualised-monthly Sharpe estimator
    e_max_sr = z_factor * sr_std  # expected-max annualised Sharpe under the null
    print(
        f"  N_eff={n_eff} (generous)  Z(N_eff)={z_factor:.3f}  OOS n_months={n_months}  "
        f"SR_std={sr_std:.3f}  ->  E[max_SR|null]={e_max_sr:+.3f}"
    )
    for k in ("L3 +COT(ROBUST)", "L4 +ptpd(FULL)"):
        oos_sr = headline[k]["oos_sr"]
        clears = oos_sr > e_max_sr
        print(f"  {k:18} OOS_Sharpe={oos_sr:+.3f}   clears E[max_SR|null]={clears}")
    print(
        "  (informational; small-OOS-N inflates SR_std and the hurdle; N_eff deliberately "
        "generous — honest deflation)."
    )

    # ── 8. LEAK RE-AUDIT at the boundary — IS book unchanged whether OOS data exists or not ──
    _sep("[8] LEAK RE-AUDIT — IS book is bit-identical with vs without OOS data on disk")
    # Truncate ALL inputs to < OOS_CUTOFF + buffer, rebuild, and assert pre-cutoff bit-identity.
    buffer = pd.Timedelta(days=40)  # > max rolling window (PORT_VOL_WIN 84 candles ≈ 28d) + COT lag
    cut_ms = int((OOS_CUTOFF + buffer).value // 1_000_000)
    coins_trunc = {s: d[d.index < cut_ms] for s, d in coins.items()}
    cot_trunc = cot[cot["date"] < (OOS_CUTOFF + buffer)]
    lay_trunc = build_layers(coins_trunc, cot_trunc, lag_days=COT_LAG_CONFIRM)
    bound = OOS_CUTOFF - pd.Timedelta(days=5)  # clear the open[t+1] / lag dependence at the seam
    all_ok = True
    print(
        f"  truncated inputs to < {(OOS_CUTOFF + buffer).date()}; comparing nets < {bound.date()}"
    )
    for k in layers:
        full_net = layers[k][0]
        trunc_net = lay_trunc[k][0]
        a = full_net[full_net.index < bound]
        b = trunc_net.reindex(a.index)
        try:
            pd.testing.assert_series_equal(a, b, check_names=False, rtol=0, atol=0)
            ok = True
        except AssertionError:
            ok = False
            all_ok = False
        print(
            f"  {k:18} pre-cutoff bit-identity (full vs OOS-truncated): {'PASS' if ok else 'FAIL'}"
        )
    print(
        f"  -> LEAK RE-AUDIT {'PASS' if all_ok else 'FAIL'} "
        f"(PORT_VOL_WIN={PORT_VOL_WIN}, VOL_WIN={VOL_WIN})"
    )

    # ── SUMMARY ─────────────────────────────────────────────────────────────────────────────
    _sep("[SUMMARY] pre-registered CONFIRMATION gates — read straight (OOS may disappoint)")
    for k in ("L2 +dispersion", "L3 +COT(ROBUST)", "L4 +ptpd(FULL)"):
        h = headline[k]
        print(
            f"  {k:18} IS_SR={h['is_sr']:+.2f}  OOS_SR={h['oos_sr']:+.2f}  "
            f"beats_gold={h['oos_sr'] > bh_oos}  beats_basket={h['oos_sr'] > ew_oos}"
        )
    # Critic CONFIRMATION-BOOTSTRAP verdict: L2 is the defensible baseline — the only layer where
    # every added sleeve's OOS marginal lift is non-negative (dispersion +0.010; full-COT is OOS
    # -0.137 = FALSIFIED, survives only restricted to gold/silver +0.044; pt/pd PROMOTABLE=False).
    # OOS is a single benign-bull regime (B&H gold reached ~1.45, basket ~1.58) — edge over B&H is
    # thin and ~entirely the directional anchor. See BASELINE_METALS.md for the recorded caveats.
    print(
        "  Defensible baseline = L2 (anchor+dispersion). COT confirmed GOLD/SILVER-ONLY; "
        "full-4-metal COT OOS-falsified (-0.137). pt/pd PROMOTABLE=False. OOS = benign bull."
    )


if __name__ == "__main__":
    main()
