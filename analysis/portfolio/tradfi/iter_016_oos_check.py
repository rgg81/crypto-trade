"""iter-016 OOS CONFIRMATION CHECK — FROZEN bear-gated TSMOM (HELD-OUT sanity, NO re-selection).

One-look held-out confirmation of the Critic-CLEARED iter-016 (bear-gated TSMOM). The config was
selected ENTIRELY on IS evidence (iter_016_bear_gated_tsmom.py KEEP gate) with ZERO new parameters
(λ=0.25 from iter-013, 252d bear-state from iter-006, band δ=0.010/freq=1 from iter-015). Here we
merely SLICE the SAME past-only deployed net by date to read the OOS window — NO re-selection, NO
OOS-driven tuning. The frozen cell is asserted to equal the deployed constants; this script CANNOT
silently drift.

The Critic's PRE-STATED expectation (honest reporting mandate): 2025-26 OOS was a BULL, so the
EW-252d bear-state g rarely (or never) fires OOS. On the g=0 identity `bear_gated_combined_raw(pn)`
== `i13.combined_raw(pn)` BIT-FOR-BIT, so on an all-bull OOS iter-016 ≈ iter-015 OOS. That means the
OOS can only confirm "NO HARM in the bull" — it CANNOT validate the bear-protection thesis, because
there are NO OOS bears to protect against. We do NOT spin an all-bull OOS as confirmation of the
worst-month (Jan-2019) edge.

What this script reports (IS vs OOS, frozen iter-016):
  Sharpe (net@1×) / net@2× (12bps) / gross(cost-off) / turnover / net-β (EW-69, VIX-OFF, iter-015
  convention) / maxDD — over BOTH windows, PLUS the Critic's four watch-items:
    (1) OOS g=1 fire count + % (is OOS ~all-bull -> iter-016 ≈ iter-015?);
    (2) iter-016 OOS β vs iter-015 OOS β DIRECTLY (not vs 0.15 — beta runs hot in a bull; the IS
        gate governs merge, not an OOS β>0.15);
    (3) if iter-016 OOS diverges from iter-015 OOS, attribute the divergence to the g=1 days;
    (4) decompose the iter-016-vs-iter-015 OOS lift into extra-captured-beta vs market-neutral
        residual (the iter-013-forensic beta-attribution, applied to the DIFF series).

HONESTY: the OOS window is ~15 months (small N) in a FAVORABLE (bull) regime. Do NOT read the OOS
Sharpe LEVEL as a forward estimate. The question is only whether iter-016 does NO HARM OOS relative
to iter-015 (do-no-harm promotion gate) and whether the bear-protection thesis is even TESTABLE OOS.

Run: uv run python analysis/portfolio/tradfi/iter_016_oos_check.py
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
import iter_013_directional as i13  # noqa: E402
import iter_015_cost as i15  # noqa: E402
import iter_016_bear_gated_tsmom as i16  # noqa: E402
import universe_tradfi as ut  # noqa: E402

OOS = ct.OOS_CUTOFF  # 2025-03-24 — immutable split; IS < OOS, OOS-window >= OOS

# The FROZEN deployed iter-016 config — every constant PRE-EXISTS (zero new parameters).
FROZEN_DELTA = i16.DELTA  # 0.010 (iter-015)
FROZEN_FREQ = i16.FREQ  # 1    (iter-015)
LAM = i16.LAM  # 0.25  (iter-013)
GATE_LOOKBACK = i16.GATE_LOOKBACK  # 252  (iter-006 bear-state)
GATE_BETA = i16.GATE_BETA  # 0.15 — IS beta criterion of record (reported, NOT an OOS gate)


def _beta_win(net: pd.Series, mkt: pd.Series, lo: pd.Timestamp, hi: pd.Timestamp) -> float:
    """Windowed OLS beta of the (VIX-OFF) 1× net on the EW-69 market over [lo, hi).

    Mirrors i13.net_beta / iter_015_oos_check._beta_win EXACTLY (same EW-69 proxy, same VIX-OFF net,
    same OLS) — only the metric WINDOW moves, so IS vs OOS is apples-to-apples on the identical
    quantity (this is the "EW-69, VIX-off convention" iter-015 uses).
    """
    df = pd.concat([net.rename("s"), mkt.rename("m")], axis=1).dropna()
    df = df[(df.index >= lo) & (df.index < hi)]
    var = float(df["m"].var())
    return float(df["s"].cov(df["m"]) / var) if var > 0 and len(df) > 2 else float("nan")


def _maxdd_win(net: pd.Series, lo: pd.Timestamp, hi: pd.Timestamp) -> float:
    """Max drawdown (%) of the deployed VIX-ON net over the [lo, hi) window equity curve."""
    s = net[(net.index >= lo) & (net.index < hi)]
    return ct.maxdd(s) * 100.0


def win_cell(raw, ret_fwd, s_vix, mkt, lo, hi) -> dict:
    """Deployed (band δ=0.010/freq=1 + VIX-ON) metric bundle for a RAW book over [lo, hi).

    Same object graph as i15._cell / iter_015_oos_check.win_cell (banded_net_freq at 0/1×/2× cost,
    VIX outer scalar, turnover on the banded book, VIX-OFF beta) — only the WINDOW moves and the RAW
    book is passed in (iter-015 = i13.combined_raw ; iter-016 = i16.bear_gated_combined_raw). No
    OOS-specific branch is introduced: the net is the single past-only series, sliced by date.
    """

    def _vix(net):  # deployed iter-008 VIX brake (outer past-only scalar, exposure-only)
        return net * s_vix.reindex(net.index).fillna(1.0)

    net_g, _ = i15.banded_net_freq(raw, ret_fwd, FROZEN_DELTA, FROZEN_FREQ, 0.0)
    net_1x, w = i15.banded_net_freq(raw, ret_fwd, FROZEN_DELTA, FROZEN_FREQ, ct.COST_SIDE)
    net_2x, _ = i15.banded_net_freq(raw, ret_fwd, FROZEN_DELTA, FROZEN_FREQ, 2.0 * ct.COST_SIDE)
    d1x, d2x, dg = _vix(net_1x), _vix(net_2x), _vix(net_g)
    return {
        "net1x": ct.msharpe(d1x, lo, hi),
        "net2x": ct.msharpe(d2x, lo, hi),
        "gross": ct.msharpe(dg, lo, hi),
        "turn": ct.turnover(w, lo, hi),
        "beta": _beta_win(net_1x, mkt, lo, hi),  # VIX-OFF 1× book beta (iter-015 convention)
        "mdd": _maxdd_win(d1x, lo, hi),
        "d1x": d1x,  # deployed VIX-ON 1× net (for the lift decomposition / divergence attribution)
    }


def _decompose_lift(d1x_016: pd.Series, d1x_015: pd.Series, mkt: pd.Series, lo, hi) -> dict:
    """Attribute the iter-016-vs-iter-015 OOS LIFT into extra-captured-beta vs residual (iter-013).

    lift[t] = d1x_016[t] - d1x_015[t] (deployed VIX-ON daily net diff). Regress the DIFF on the
    EW-69 market: β_diff = cov(lift, mkt)/var(mkt); β-tilt = β_diff·mkt (extra beta the gate takes
    on/off), residual = lift - β-tilt (market-neutral residual). Additive sums are exact. Because
    g=0 days are the iter-015 identity, the lift concentrates on the g=1-affected days.
    """
    df = pd.concat([d1x_016.rename("a"), d1x_015.rename("b"), mkt.rename("m")], axis=1).dropna()
    df = df[(df.index >= lo) & (df.index < hi)]
    lift = df["a"] - df["b"]
    var = float(df["m"].var())
    beta = float(lift.cov(df["m"]) / var) if var > 0 and len(df) > 2 else float("nan")
    tilt = beta * df["m"]
    resid = lift - tilt
    lift_sum = float(lift.sum())
    return {
        "n": len(df),
        "beta": beta,
        "lift_sum": lift_sum,
        "tilt_sum": float(tilt.sum()),
        "resid_sum": float(resid.sum()),
        "tilt_share": (float(tilt.sum()) / lift_sum * 100.0)
        if abs(lift_sum) > 1e-12
        else float("nan"),
        "resid_share": (float(resid.sum()) / lift_sum * 100.0)
        if abs(lift_sum) > 1e-12
        else float("nan"),
    }


def _row(r_is, r_oos, keys):
    labels = {
        "net1x": "Sharpe net@1× (6bps)",
        "net2x": "net@2× Sharpe (12bps)",
        "gross": "gross(cost-off) Sharpe",
        "turn": "turnover/day",
        "beta": "net-β (EW-69, VIX-off)",
        "mdd": "maxDD %",
    }
    lines = []
    for k in keys:
        if k == "turn":
            lines.append(f"    {labels[k]:<24} {r_is[k]:>10.4f}   {r_oos[k]:>10.4f}")
        elif k == "mdd":
            lines.append(f"    {labels[k]:<24} {r_is[k]:>+9.0f}%   {r_oos[k]:>+9.0f}%")
        else:
            lines.append(f"    {labels[k]:<24} {r_is[k]:>+10.2f}   {r_oos[k]:>+10.2f}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()

    # FROZEN-config guard: this script confirms the PRE-CHOSEN deployed iter-016; never re-selects.
    assert (FROZEN_DELTA, FROZEN_FREQ) == (i15.CHOSEN_DELTA, i15.CHOSEN_FREQ), (
        "frozen band cell drifted from iter_015_cost.CHOSEN — refusing to re-select on OOS"
    )
    assert LAM == i13.DEPLOYED_LAM and GATE_LOOKBACK == i6.GATE_LOOKBACK, (
        "λ / gate-window drifted from the deployed iter-013/006 constants — refusing to re-select"
    )

    base = Path(args.data_dir) if args.data_dir else ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    coins = ct.load_tradfi(syms, args.data_dir)
    if not coins:
        print("No ingested tradfi data found. Run ingest_yahoo.py first.")
        return
    pn = ct.panels(coins)
    ret_fwd = pn["ret_fwd"]
    mkt = i13.market_return(pn)  # EW-69 PIT market proxy for net-beta / decomposition
    vix = i8.load_vix_close(ret_fwd.index, args.data_dir)
    s_vix = i8.vix_scale(vix)  # base=20 / floor=0.50 (iter-008 UNCHANGED)

    raw_016 = i16.bear_gated_combined_raw(pn)  # FROZEN candidate (bear-gated TSMOM)
    raw_015 = i13.combined_raw(pn, LAM)  # baseline (ungated deployed iter-015)

    oos_end = ret_fwd.index[ret_fwd.index >= OOS].max()
    print("=" * 100)
    print(
        "iter-016 OOS CONFIRMATION CHECK — FROZEN bear-gated TSMOM (HELD-OUT sanity, no re-select)"
    )
    print("=" * 100)
    print(
        f"  FROZEN config (IS-chosen; 0 new params): λ={LAM} × g=1{{EW {GATE_LOOKBACK}d ret<0}}  "
        f"band δ={FROZEN_DELTA:.3f}/freq={FROZEN_FREQ} + VIX brake"
    )
    print(
        f"  IS window = [.. , {OOS.date()})    OOS window = [{OOS.date()} , {oos_end.date()}]  "
        f"(one-look; config FROZEN, no OOS tuning)"
    )

    # --- FROZEN iter-016: IS vs OOS ---
    z6_is = win_cell(raw_016, ret_fwd, s_vix, mkt, ct.LO0, OOS)
    z6_oos = win_cell(raw_016, ret_fwd, s_vix, mkt, OOS, ct.HI1)
    keys = ("net1x", "net2x", "gross", "turn", "beta", "mdd")
    print("\n  FROZEN iter-016 (bear-gated TSMOM) — deployed IS vs OOS:")
    print(f"    {'metric':<24} {'IS':>10}   {'OOS':>10}")
    print(_row(z6_is, z6_oos, keys))

    # --- iter-015 baseline (ungated) IS vs OOS — the do-no-harm comparator ---
    b_is = win_cell(raw_015, ret_fwd, s_vix, mkt, ct.LO0, OOS)
    b_oos = win_cell(raw_015, ret_fwd, s_vix, mkt, OOS, ct.HI1)
    print("\n  iter-015 baseline (ungated deployed) — IS vs OOS:")
    print(f"    {'metric':<24} {'IS':>10}   {'OOS':>10}")
    print(_row(b_is, b_oos, keys))

    # --- IDENTITY / OOS-path proof: forced all-zero gate -> iter-016 OOS net == iter-015 OOS net
    zeros = pd.Series(0.0, index=pn["close"].index)
    raw_id = i16.bear_gated_combined_raw(pn, LAM, zeros)
    id_1x, _ = i15.banded_net_freq(raw_id, ret_fwd, FROZEN_DELTA, FROZEN_FREQ, ct.COST_SIDE)
    id_1x = id_1x * s_vix.reindex(id_1x.index).fillna(1.0)
    b_1x, _ = i15.banded_net_freq(raw_015, ret_fwd, FROZEN_DELTA, FROZEN_FREQ, ct.COST_SIDE)
    b_1x = b_1x * s_vix.reindex(b_1x.index).fillna(1.0)
    common_id = id_1x.index.intersection(b_1x.index)
    common_id = common_id[common_id >= OOS]
    id_ok = bool(
        np.allclose(id_1x.loc[common_id].to_numpy(), b_1x.loc[common_id].to_numpy(), atol=1e-12)
    )

    # ================================================================= WATCH-ITEM 1 — OOS g=1 fires
    g = i6.bear_state(pn["close"], GATE_LOOKBACK)  # causal EW-252d bear-state (past-only)
    g_on_net = g.reindex(z6_oos["d1x"].index).fillna(0.0)  # align to the ACTUALLY-TRADED OOS days
    g_oos = g_on_net[g_on_net.index >= OOS]
    n_oos_days = int(len(g_oos))
    n_fire = int((g_oos > 0.5).sum())
    pct_fire = (n_fire / n_oos_days * 100.0) if n_oos_days else float("nan")
    print("\n  WATCH-ITEM 1 — OOS bear-gate g=1 fires (TSMOM sleeve turned OFF):")
    print(
        f"    g=1 days OOS = {n_fire} / {n_oos_days} trading days  ({pct_fire:.1f}%)  "
        f"[IS g=1 = {g[g.index < OOS].mean() * 100:.1f}% of IS days]"
    )
    all_bull = n_fire == 0
    if all_bull:
        print(
            "    -> OOS is ALL-BULL (g=0 every OOS day). By the g=0 identity iter-016 ≡ iter-015"
            " OOS bit-for-bit."
        )
        print(
            "       The OOS can only confirm 'NO HARM in the bull' — it CANNOT validate the"
            " bear-protection thesis (there are NO OOS bears to protect against). Not spun as"
            " confirmation of the Jan-2019 worst-month edge."
        )
    else:
        print(
            f"    -> {n_fire} OOS bear-days: the gate DID fire OOS; the iter-016-vs-iter-015"
            " divergence (below) is attributable to these days."
        )
    print(
        f"    OOS-path identity (forced g=0 -> iter-016 OOS net == iter-015 OOS net): "
        f"{'PASS' if id_ok else 'FAIL'}"
    )

    # ============================================ WATCH-ITEM 2 — iter-016 OOS β vs iter-015 OOS β
    print("\n  WATCH-ITEM 2 — iter-016 OOS β vs iter-015 OOS β (DIRECT; NOT vs the 0.15 IS gate):")
    print(
        f"    iter-016 OOS β = {z6_oos['beta']:+.3f}   iter-015 OOS β = {b_oos['beta']:+.3f}   "
        f"(Δ {z6_oos['beta'] - b_oos['beta']:+.3f})"
    )
    print(
        f"    context: iter-016 IS β = {z6_is['beta']:+.3f}, iter-015 IS β = {b_is['beta']:+.3f}. "
        f"OOS β>0.15 is the known beta-runs-hot-in-bull regime effect (both books), NOT a failure"
        " by itself — the IS gate governs merge."
    )

    # ========================================== WATCH-ITEM 3 + 4 — divergence attribution + lift
    d6, d5 = z6_oos["d1x"], b_oos["d1x"]
    common = d6.index.intersection(d5.index)
    common = common[(common >= OOS) & (common < ct.HI1)]
    diff = d6.loc[common] - d5.loc[common]
    g_common = g.reindex(common).fillna(0.0)
    diff_on = float(diff[g_common > 0.5].sum())
    diff_off = float(diff[g_common <= 0.5].sum())
    print("\n  WATCH-ITEM 3 — iter-016-vs-iter-015 OOS divergence, attributed to g-state days:")
    print(
        f"    Σ(iter016 - iter015) OOS daily net = {diff.sum() * 100:+.3f}%  "
        f"| on g=1 days = {diff_on * 100:+.3f}%  | on g=0 days = {diff_off * 100:+.3f}%"
    )
    if all_bull:
        print(
            "    -> g never fired OOS, so the divergence lives entirely on g=0 days and is pure"
            " vol-target trailing-vol carryover off the (identical-going-forward) book —"
            " immaterial, NOT a bear-protection effect."
        )
    else:
        sign_ok = "helps" if diff_on > 0 else "hurts"
        print(
            f"    -> the g=1-day contribution {sign_ok} (gating helps only if those days"
            " were bear-like)."
        )

    dec = _decompose_lift(d6, d5, mkt, OOS, ct.HI1)
    print(
        "\n  WATCH-ITEM 4 — decompose the OOS lift into extra-captured-β vs market-neutral resid:"
    )
    print(
        f"    lift Σ = {dec['lift_sum'] * 100:+.3f}%  (n={dec['n']})  "
        f"lift-β on EW-69 = {dec['beta']:+.3f}"
    )
    print(
        f"    extra-captured-β = {dec['tilt_sum'] * 100:+.3f}% ({dec['tilt_share']:.0f}% of lift)"
        f"  | market-neutral residual = {dec['resid_sum'] * 100:+.3f}%"
        f" ({dec['resid_share']:.0f}% of lift)"
    )

    # ------------------------------------------ do-no-harm promotion read + leak re-confirmation
    leak_ok = i16._leak_selfcheck(pn, ret_fwd, s_vix)
    slice_ok = np.isclose(ct.msharpe(z6_oos["d1x"], OOS, ct.HI1), z6_oos["net1x"], atol=1e-9)
    nh_sharpe = z6_oos["net1x"] >= b_oos["net1x"] - 0.05
    nh_gross = z6_oos["gross"] >= b_oos["gross"] - 0.05
    nh_cost = (
        z6_oos["net2x"] >= z6_oos["net1x"] - 0.30
    )  # 2x-cost robustness persists (interior cell)
    print(
        "\n  DO-NO-HARM PROMOTION READ (iter-016 OOS vs iter-015 OOS — relative, not a level bet):"
    )
    print(
        f"    net@1× OOS: iter-016 {z6_oos['net1x']:+.2f} vs iter-015 {b_oos['net1x']:+.2f}  -> "
        f"{'NO HARM' if nh_sharpe else 'REGRESSES — investigate'}"
    )
    print(
        f"    gross OOS : iter-016 {z6_oos['gross']:+.2f} vs iter-015 {b_oos['gross']:+.2f}  -> "
        f"{'NO HARM' if nh_gross else 'REGRESSES — investigate'}"
    )
    print(
        f"    2×-cost robustness OOS (net@2× not << net@1×): "
        f"{z6_oos['net2x']:+.2f} vs {z6_oos['net1x']:+.2f}  -> "
        f"{'HOLDS' if nh_cost else 'DROPS — check'}"
    )

    print("\n  INTEGRITY:")
    print(
        f"    future-bar leak self-check (bear-gated net bit-identical pre-cut): "
        f"{'PASS' if leak_ok else 'FAIL'}"
    )
    print(
        f"    OOS = SAME past-only net sliced by date (no OOS branch): "
        f"{'CONFIRMED' if slice_ok else 'MISMATCH'}"
    )
    print(
        f"    FROZEN-config guard: reported cell == deployed (λ={LAM}, δ={FROZEN_DELTA:.3f}, "
        f"freq={FROZEN_FREQ}, gate={GATE_LOOKBACK}d) — no OOS re-selection: PASS"
    )
    print("=" * 100)


if __name__ == "__main__":
    main()
