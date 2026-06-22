"""portfolio-iteration-v2 iter-v2-002 EXPLORATION — cross-sectional momentum (XS-mom) on rank 21-40.

Adds a dollar-neutral cross-sectional-momentum tilt (γ on a centered within-band return-rank, L=84)
to the rank-21-40 trend+carry book, parity-preserving at γ=0. The bet: the anchor died because
*directional* trend on mid-caps faded, but the *relative* ordering within the band still carries
information. See diary-portfolio-v2/BRIEF_iter002_xsmom.md.

EXPLORATION DISCIPLINE — OOS is HIDDEN. By default this prints only IS + the EARLY(2021-23)/LATE
(2024->cutoff) in-sample era-split + per-year + turnover/tickets/avgPos + dollar-neutrality +
gate-fire-rate. OOS is COMPUTED but printed ONLY behind `--reveal` (used once at CONFIRMATION).
No OOS-tuning. γ and L get robustness SWEEPS (not per-month fits); disp_min_v is the IS-only p20 of
dispersion, resolved ONCE and frozen.

Run from worktree root:
    uv run python analysis/portfolio_v2/iter_v2_002_xsmom.py            # EXPLORATION (OOS hidden)
    uv run python analysis/portfolio_v2/iter_v2_002_xsmom.py --reveal   # CONFIRMATION (ONE reveal)

§5.3 config matrix:
  1. Parity guard      : γ=0 -> assert net == anchor net (printed max|Δ|).
  2. Standalone (A)    : γ=1.0, L=84, no gate — diagnostic raw XS-mom read.
  3. Blended γ-sweep   : γ in {0.15,0.25,0.40,0.60}, L=84, gate ON — the deploy search.
  4. L-robustness      : at the best γ, L in {42,84,126,168}.
  5. Gate on/off + grid: best (γ,L) gate OFF vs ON; then N_MIN {6,8,10} x DISP_MIN {p10,p20,p30}.
  6. Cost stress       : best (γ,L,gate) at slip_mult=2, cost_mult=2, slip_pessimistic.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
os.chdir(_ROOT)
sys.path.insert(0, str(_ROOT / "analysis"))

from portfolio_v2 import engine_v2 as e2  # noqa: E402
from portfolio_v2 import universe_v2 as uv  # noqa: E402
from portfolio_v2.diag_v2_001 import per_year_sharpe, slip_pessimistic  # noqa: E402

# ---- band / era constants -------------------------------------------------------------------
RANK_LO, RANK_HI, SEASON = 20, 40, 168
EARLY_LO = pd.Timestamp("2021-01-01")
EARLY_HI = pd.Timestamp("2024-01-01")  # EARLY = 2021..2023 inclusive
LATE_LO = pd.Timestamp("2024-01-01")
LATE_HI = e2.OOS_CUTOFF  # LATE = 2024-01-01 -> OOS cutoff (the faded IS tail), still IN-SAMPLE
W1_HI = pd.Timestamp("2026-01-01")  # OOS sub-window boundary

# Deploy-candidate primary (pre-registered): γ=0.25 is filled in after the γ-sweep prints; the
# script computes the IS+LATE-best γ on the sweep and reports it as the deploy candidate row.
L_PRIMARY = 84
GAMMA_SWEEP = [0.15, 0.25, 0.40, 0.60]
L_SWEEP = [42, 84, 126, 168]


# ---- disp_min_v resolution (IS-only p20 of cross-sectional dispersion, frozen ONCE) -----------
def resolve_disp_thresholds(coins: dict, lookback: int) -> dict[str, float]:
    """Compute the IS-only percentile thresholds of the past-only cross-sectional dispersion of the
    L-return over the rank-21-40 eligible band. disp[t] = std over the eligible band's `mom`; the
    gate compares disp[t-1] (shift(1)) so we percentile the same past-only series, restricted to IS
    (< OOS_CUTOFF) and to candles with a defined band. Returns {'p10','p20','p30'} — p20 is the
    pre-registered DISP_MIN; p10/p30 are the gate-robustness neighbors. Frozen, never perf-swept.
    """
    panel = e2.build_panel(coins)
    elig = (
        uv.eligibility(coins, RANK_LO, RANK_HI, SEASON)
        .reindex(index=panel["opens"].index, columns=panel["cols"])
        .fillna(False)
    )
    mom = panel["close"] / panel["close"].shift(lookback) - 1.0
    disp = mom.where(elig).std(axis=1).shift(1)  # past-only, matches the engine gate
    disp_is = disp[(disp.index < e2.OOS_CUTOFF)].dropna()
    disp_is = disp_is[disp_is > 0]  # drop empty/degenerate band candles
    return {
        "p10": float(np.percentile(disp_is, 10)),
        "p20": float(np.percentile(disp_is, 20)),
        "p30": float(np.percentile(disp_is, 30)),
    }


# ---- gate-fire-rate + dollar-neutrality diagnostics -----------------------------------------
def gate_fire_rate(coins: dict, lookback: int, n_min: int, disp_min: float | None) -> float:
    """Fraction of IS candles (with a defined band) on which the XS-mom term is gated OFF."""
    panel = e2.build_panel(coins)
    elig = (
        uv.eligibility(coins, RANK_LO, RANK_HI, SEASON)
        .reindex(index=panel["opens"].index, columns=panel["cols"])
        .fillna(False)
    )
    mom = panel["close"] / panel["close"].shift(lookback) - 1.0
    gate = e2._xs_gate_mask(mom, elig, n_min, disp_min)
    band_ok = (elig.sum(axis=1) > 0) & (mom.where(elig).notna().sum(axis=1) > 0)
    sel = gate[(gate.index < e2.OOS_CUTOFF) & band_ok]
    return float(sel.mean()) if len(sel) else float("nan")


def dollar_neutrality(coins: dict, lookback: int) -> dict:
    """Σ_c xs over the eligible band across IS candles at γ=1, no gate (the Σw≈0 / dollar-neutral
    check). Returns {typ_max, abs_max, n_band_eq_ranked, n_total} where `typ_max` is the residual on
    candles where every eligible name is ALSO rankable (mom defined) — i.e. the true neutrality of
    the centered rank — and `abs_max` includes the handful of warmup candles where an eligible name
    has a seasoned rank but an undefined L-return (mom NaN). On the latter, the v1-identical
    construction's `n = elig.sum(axis=1)` over-counts vs the number ranked, so the centered ranks
    do not sum to exactly 0. This is the EXACT behavior of v1's iter_002 xsec_mom (bit-identity per
    brief 2.1), confined to <0.2% of candles; typical-case residual is the honest neutrality."""
    panel = e2.build_panel(coins)
    elig = (
        uv.eligibility(coins, RANK_LO, RANK_HI, SEASON)
        .reindex(index=panel["opens"].index, columns=panel["cols"])
        .fillna(False)
    )
    mom = panel["close"] / panel["close"].shift(lookback) - 1.0
    xs, _ = e2._xsmom(panel["close"], elig, lookback)
    band_sum = xs.where(elig).sum(axis=1)
    n_elig = elig.sum(axis=1)
    n_ranked = mom.where(elig).notna().sum(axis=1)
    is_mask = (n_elig > 0) & (band_sum.index < e2.OOS_CUTOFF)
    no_gap = is_mask & (n_elig == n_ranked)  # every eligible name is also rankable
    return {
        "typ_max": float(band_sum[no_gap].abs().max()) if no_gap.any() else float("nan"),
        "abs_max": float(band_sum[is_mask].abs().max()) if is_mask.any() else float("nan"),
        "n_gap": int((is_mask & (n_elig > n_ranked)).sum()),
        "n_total": int(is_mask.sum()),
    }


# ---- per-config evaluation ------------------------------------------------------------------
def evaluate(coins: dict, *, reveal: bool, **kw) -> dict:
    """Run one config and pull IS + EARLY/LATE era-split + per-year + structure. OOS computed but
    returned for printing ONLY when reveal=True."""
    res = e2.run_book(coins, rank_lo=RANK_LO, rank_hi=RANK_HI, season=SEASON, **kw)
    net = res["net"]
    out = {
        "IS": e2.msharpe(net, e2.LO0, e2.OOS_CUTOFF),
        "EARLY": e2.msharpe(net, EARLY_LO, EARLY_HI),
        "LATE": e2.msharpe(net, LATE_LO, LATE_HI),
        "per_year": per_year_sharpe(net),
        "turn": res["turnover"],
        "tickets": res["tickets"],
        "avgPos": res["avg_positions"],
        "band": float(res["elig"].sum(axis=1).groupby(res["elig"].index.year).mean().mean()),
        "_net": net,
    }
    if reveal:
        out["OOS"] = e2.msharpe(net, e2.OOS_CUTOFF, e2.HI1)
        out["OOS_w1"] = e2.msharpe(net, e2.OOS_CUTOFF, W1_HI)
        out["OOS_w2"] = e2.msharpe(net, W1_HI, e2.HI1)
    return out


def _fmt(label: str, r: dict, *, reveal: bool, extra: str = "") -> str:
    head = (
        f"  {label:33} IS={r['IS']:+.2f} EARLY={r['EARLY']:+.2f} LATE={r['LATE']:+.2f} "
        f"turn={r['turn']:.3f} tix={r['tickets']:.1f} aPos={r['avgPos']:.1f} band={r['band']:.1f}"
    )
    if reveal:
        head += (
            f"\n  {'':34} OOS={r['OOS']:+.2f}  "
            f"OOS(25-03..12)={r['OOS_w1']:+.2f}  OOS(26)={r['OOS_w2']:+.2f}"
        )
    if extra:
        head += f"  {extra}"
    return head


def _is_late_score(r: dict) -> float:
    """The EXPLORATION deploy metric: IS + LATE (OOS NEVER consulted). Picks the γ that lifts the
    faded LATE tail the most without sacrificing IS — the load-bearing anti-regime read."""
    return r["IS"] + r["LATE"]


# ---- main -----------------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--reveal",
        action="store_true",
        help="CONFIRMATION ONLY — reveal the hidden OOS + sub-windows. Do NOT use in EXPLORATION.",
    )
    args = ap.parse_args()
    reveal = args.reveal

    print("=" * 100)
    print("iter-v2-002 EXPLORATION — cross-sectional momentum (XS-mom) on rank 21-40")
    print(f"  OOS is {'REVEALED (CONFIRMATION mode)' if reveal else 'HIDDEN (EXPLORATION mode)'}")
    print("=" * 100)

    coins = uv.load_pool_pit()
    print(f"\nPIT pool: {len(coins)} coins.  band=(rank {RANK_LO}-{RANK_HI}], season={SEASON}")

    # --- frozen disp_min_v (IS p20 at the primary lookback) ---
    disp_thr = resolve_disp_thresholds(coins, L_PRIMARY)
    disp_min_v = disp_thr["p20"]
    print(
        f"\nFROZEN disp_min_v = IS-p20 of dispersion @ L={L_PRIMARY} = {disp_min_v:.6f}  "
        f"(p10={disp_thr['p10']:.6f}, p30={disp_thr['p30']:.6f})  N_MIN=8"
    )

    # ---------------------------------------------------------------------------------------
    # ANCHOR (γ=0) — the comparison baseline (IS +1.53 / LATE faded)
    # ---------------------------------------------------------------------------------------
    print("\n" + "-" * 100)
    print("[ANCHOR] trend+carry, γ=0 (the parity baseline)")
    print("-" * 100)
    anchor = evaluate(coins, reveal=reveal, slip_bps_fn=e2.default_slip_bps)
    print(_fmt("anchor (γ=0)", anchor, reveal=reveal))
    print(f"  per-year Sharpe: {anchor['per_year']}")
    anc_is, anc_late = anchor["IS"], anchor["LATE"]

    # ---------------------------------------------------------------------------------------
    # 1. PARITY GUARD — γ=0 must reproduce the anchor net bit-for-bit
    # ---------------------------------------------------------------------------------------
    print("\n" + "-" * 100)
    print("[1] PARITY GUARD — run_book(xs_gamma=0) net == anchor net")
    print("-" * 100)
    guard = e2.run_book(
        coins,
        rank_lo=RANK_LO,
        rank_hi=RANK_HI,
        season=SEASON,
        slip_bps_fn=e2.default_slip_bps,
        xs_gamma=0.0,
        xs_lookback=L_PRIMARY,
        xs_nmin=8,
        xs_disp_min=disp_min_v,
    )
    a, b = anchor["_net"], guard["net"].reindex(anchor["_net"].index)
    max_d = float((a - b).abs().max())
    print(f"  max|Δ(anchor, γ=0)| = {max_d:.3e}   ({'PASS == 0.0' if max_d == 0.0 else 'FAIL'})")

    # ---------------------------------------------------------------------------------------
    # 2. STANDALONE (A) — γ=1.0, L=84, NO gate (diagnostic raw XS-mom read)
    # ---------------------------------------------------------------------------------------
    print("\n" + "-" * 100)
    print("[2] STANDALONE (A) — γ=1.0, L=84, NO gate (diagnostic, not the deploy candidate)")
    print("-" * 100)
    standalone = evaluate(
        coins,
        reveal=reveal,
        slip_bps_fn=e2.default_slip_bps,
        xs_gamma=1.0,
        xs_lookback=L_PRIMARY,
        xs_disp_min=None,
        xs_nmin=8,
    )
    print(_fmt("standalone γ=1 L=84 noGate", standalone, reveal=reveal))
    print(f"  per-year Sharpe: {standalone['per_year']}")
    dn = dollar_neutrality(coins, L_PRIMARY)
    print(
        f"  dollar-neutrality: typical max|Σ_c xs| = {dn['typ_max']:.2e} (≈0 => neutral); "
        f"abs max = {dn['abs_max']:.2e} on {dn['n_gap']}/{dn['n_total']} warmup candles where an "
        f"eligible name has no L-return (v1-identical n-overcount; <0.2%)"
    )

    # ---------------------------------------------------------------------------------------
    # 3. BLENDED γ-SWEEP (B) — L=84, gate ON (the deploy search)
    # ---------------------------------------------------------------------------------------
    print("\n" + "-" * 100)
    print(
        f"[3] BLENDED γ-SWEEP — L={L_PRIMARY}, gate ON (N_MIN=8, disp_min_v=p20).  anchor: "
        f"IS={anc_is:+.2f} LATE={anc_late:+.2f}"
    )
    print("-" * 100)
    gamma_results = {}
    for g in GAMMA_SWEEP:
        r = evaluate(
            coins,
            reveal=reveal,
            slip_bps_fn=e2.default_slip_bps,
            xs_gamma=g,
            xs_lookback=L_PRIMARY,
            xs_nmin=8,
            xs_disp_min=disp_min_v,
        )
        gamma_results[g] = r
        gfr = gate_fire_rate(coins, L_PRIMARY, 8, disp_min_v)
        dlate = r["LATE"] - anc_late
        extra = f"ΔLATE={dlate:+.2f} gateFire={gfr:.1%}"
        print(_fmt(f"blended γ={g:.2f} L=84 gateON", r, reveal=reveal, extra=extra))
    # deploy γ* = max IS+LATE on the sweep (OOS NEVER consulted)
    gamma_star = max(gamma_results, key=lambda g: _is_late_score(gamma_results[g]))
    print(
        f"\n  deploy γ* (max IS+LATE, OOS hidden) = {gamma_star:.2f}  "
        f"(IS+LATE={_is_late_score(gamma_results[gamma_star]):+.2f})"
    )

    # ---------------------------------------------------------------------------------------
    # 4. L-ROBUSTNESS — at γ*, L in {42,84,126,168}
    # ---------------------------------------------------------------------------------------
    print("\n" + "-" * 100)
    print(f"[4] L-ROBUSTNESS — γ={gamma_star:.2f}, gate ON, L in {L_SWEEP} (no knife-edge check)")
    print("-" * 100)
    l_results = {}
    for ell in L_SWEEP:
        # DISP_MIN frozen at the L=84 p20 (a fixed pre-registered threshold across all configs).
        r = evaluate(
            coins,
            reveal=reveal,
            slip_bps_fn=e2.default_slip_bps,
            xs_gamma=gamma_star,
            xs_lookback=ell,
            xs_nmin=8,
            xs_disp_min=disp_min_v,
        )
        l_results[ell] = r
        dlate = r["LATE"] - anc_late
        print(
            _fmt(
                f"γ={gamma_star:.2f} L={ell} gateON", r, reveal=reveal, extra=f"ΔLATE={dlate:+.2f}"
            )
        )
    l_star = L_PRIMARY  # deploy L is the pre-registered primary; the sweep proves robustness only

    # ---------------------------------------------------------------------------------------
    # 5. GATE ON/OFF + GATE-ROBUSTNESS GRID — best (γ*, L*)
    # ---------------------------------------------------------------------------------------
    print("\n" + "-" * 100)
    print(f"[5] GATE ON/OFF + ROBUSTNESS GRID — γ={gamma_star:.2f}, L={l_star}")
    print("-" * 100)
    # gate fully OFF: nmin=0 (never trips the names leg) + disp_min=None (disables dispersion leg).
    off = evaluate(
        coins,
        reveal=reveal,
        slip_bps_fn=e2.default_slip_bps,
        xs_gamma=gamma_star,
        xs_lookback=l_star,
        xs_nmin=0,
        xs_disp_min=None,
    )
    print(
        _fmt(
            "gate OFF",
            off,
            reveal=reveal,
            extra=f"gateFire={gate_fire_rate(coins, l_star, 0, None):.1%}",
        )
    )
    print("  gate-robustness grid  N_MIN x disp_min_v (IS / EARLY / LATE / gateFire):")
    for nm in (6, 8, 10):
        for pk in ("p10", "p20", "p30"):
            dm = disp_thr[pk]
            r = evaluate(
                coins,
                reveal=reveal,
                slip_bps_fn=e2.default_slip_bps,
                xs_gamma=gamma_star,
                xs_lookback=l_star,
                xs_nmin=nm,
                xs_disp_min=dm,
            )
            gfr = gate_fire_rate(coins, l_star, nm, dm)
            line = (
                f"    N_MIN={nm:2d} disp_min_v={pk}({dm:.5f})  "
                f"IS={r['IS']:+.2f} EARLY={r['EARLY']:+.2f} LATE={r['LATE']:+.2f} "
                f"gateFire={gfr:5.1%}"
            )
            if reveal:
                line += f"  OOS={r['OOS']:+.2f}"
            print(line)

    # ---------------------------------------------------------------------------------------
    # 6. COST STRESS — best (γ*, L*, gate ON p20) at 2x slip, 2x cost, slip_pessimistic
    # ---------------------------------------------------------------------------------------
    print("\n" + "-" * 100)
    print(f"[6] COST STRESS — γ={gamma_star:.2f}, L={l_star}, gate ON (N_MIN=8, disp_min_v=p20)")
    print("-" * 100)
    base_kw = dict(xs_gamma=gamma_star, xs_lookback=l_star, xs_nmin=8, xs_disp_min=disp_min_v)
    stresses = [
        ("default slip", dict(slip_bps_fn=e2.default_slip_bps)),
        ("2x slip", dict(slip_bps_fn=e2.default_slip_bps, slip_mult=2.0)),
        ("2x taker cost", dict(slip_bps_fn=e2.default_slip_bps, cost_mult=2.0)),
        ("slip_pessimistic", dict(slip_bps_fn=slip_pessimistic)),
    ]
    for name, skw in stresses:
        r = evaluate(coins, reveal=reveal, **skw, **base_kw)
        # anchor under the SAME cost model for the apples-to-apples ΔLATE
        ar = evaluate(coins, reveal=reveal, **skw)
        dlate = r["LATE"] - ar["LATE"]
        print(
            _fmt(
                f"{name}",
                r,
                reveal=reveal,
                extra=f"anchorLATE={ar['LATE']:+.2f} ΔLATE={dlate:+.2f}",
            )
        )

    # ---------------------------------------------------------------------------------------
    # DEPLOY CANDIDATE — single row carried to CONFIRMATION (IS + LATE only)
    # ---------------------------------------------------------------------------------------
    dep = gamma_results[gamma_star] if l_star == L_PRIMARY else l_results[l_star]
    print("\n" + "=" * 100)
    print("DEPLOY CANDIDATE (carried to CONFIRMATION — IS + LATE only, OOS hidden)")
    print("=" * 100)
    print(
        f"  γ*={gamma_star:.2f}  L*={l_star}  gate ON (N_MIN=8, disp_min_v=IS-p20={disp_min_v:.6f})"
    )
    print(
        f"  IS={dep['IS']:+.2f} (anchor {anc_is:+.2f}, Δ={dep['IS'] - anc_is:+.2f})   "
        f"LATE={dep['LATE']:+.2f} (anchor {anc_late:+.2f}, Δ={dep['LATE'] - anc_late:+.2f})   "
        f"EARLY={dep['EARLY']:+.2f}"
    )
    print(
        f"  turn={dep['turn']:.3f} (anchor {anchor['turn']:.3f})  "
        f"avgPos={dep['avgPos']:.1f}  band={dep['band']:.1f}"
    )

    # --- EXPLORATION gate read G1..G6 (IS + LATE only; OOS NEVER consulted) ---
    print("\n  EXPLORATION gates (IS + LATE only — OOS hidden):")
    g1 = dep["IS"] >= anc_is - 0.10
    g2 = dep["LATE"] - anc_late >= 0.15
    # G3 L-robustness: sign of (IS+LATE lift) preserved at L=42 and L=126
    lift = lambda r: (r["IS"] - anc_is) + (r["LATE"] - anc_late)  # noqa: E731
    g3 = np.sign(lift(l_results[42])) == np.sign(lift(l_results[84])) and (
        np.sign(lift(l_results[126])) == np.sign(lift(l_results[84]))
    )
    # G4 γ-robustness: lift positive across the contiguous γ-neighborhood of γ*
    sg = sorted(GAMMA_SWEEP)
    i = sg.index(gamma_star)
    nbrs = [sg[j] for j in (i - 1, i, i + 1) if 0 <= j < len(sg)]
    g4 = all(lift(gamma_results[g]) > 0 for g in nbrs)
    print(
        f"    G1 IS lift (IS >= anchor-0.10)            : {'PASS' if g1 else 'FAIL'} "
        f"({dep['IS']:+.2f} vs {anc_is - 0.10:+.2f})"
    )
    print(
        f"    G2 LATE-era lift (ΔLATE >= +0.15)         : {'PASS' if g2 else 'FAIL'} "
        f"(ΔLATE={dep['LATE'] - anc_late:+.2f})  [LOAD-BEARING anti-regime gate]"
    )
    print(f"    G3 L-robustness (sign agree L=42,126)     : {'PASS' if g3 else 'FAIL'}")
    print(f"    G4 γ-robustness (lift>0 on {nbrs})        : {'PASS' if g4 else 'FAIL'}")
    print("    G5 cost survival (see section [6] ΔLATE)  : read from cost-stress block above")
    print(
        "    G6 dollar-neutral + structure (Σw≈0)      : "
        f"{'PASS' if dn['typ_max'] < 1e-9 else 'FAIL'} (typical max|Σxs|={dn['typ_max']:.2e}; "
        f"abs={dn['abs_max']:.2e} on {dn['n_gap']}/{dn['n_total']} warmup candles; "
        f"avgPos={dep['avgPos']:.1f} vs anchor {anchor['avgPos']:.1f})"
    )

    if not reveal:
        print("\n  (OOS intentionally HIDDEN — judged at the separate CONFIRMATION reveal only.)")


if __name__ == "__main__":
    main()
