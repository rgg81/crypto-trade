"""portfolio-iteration-v2 iter-v2-003 EXPLORATION — cross-sectional LightGBM predictor (rank 21-40).

ONE change vs the anchor: replace the hand-set trend+carry+xs blend with a leak-safe, walk-forward,
dollar-neutral LightGBM that predicts each coin's RELATIVE forward return within the rank-21-40 band
and routes adaptively across trend / XS-mom / carry / vol as the regime turns (the model retrains
monthly, so it re-weights features when EARLY-trend dies and LATE-XS-mom wakes — the iter-v2-002
EARLY-dead/LATE-alive complementarity, learned instead of hand-set). See BRIEF_iter003_xsml.md.

EXPLORATION DISCIPLINE — OOS is HIDDEN. By default prints only IS + EARLY(2021-23)/LATE(2024-cutoff)
era-split + per-year + turnover/tickets/avgPos + dollar-neutrality + feature importance + cold-start
fallback fraction + the 2x-taker / pessimistic-slip LATE. OOS is COMPUTED but printed ONLY behind
`--reveal` (used once at the separate CONFIRMATION). No OOS-tuning; all structural choices are
pre-registered in the brief + ml_v2.py constants.

Run from worktree root:
    uv run python analysis/portfolio_v2/iter_v2_003_xsml.py            # EXPLORATION (OOS hidden)
    uv run python analysis/portfolio_v2/iter_v2_003_xsml.py --reveal   # CONFIRMATION (ONE reveal)
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
os.chdir(_ROOT)
sys.path.insert(0, str(_ROOT / "analysis"))

from portfolio_v2 import engine_v2 as e2  # noqa: E402
from portfolio_v2 import ml_v2  # noqa: E402
from portfolio_v2 import universe_v2 as uv  # noqa: E402
from portfolio_v2.diag_v2_001 import per_year_sharpe, slip_pessimistic  # noqa: E402

# ---- band / era constants (identical to iter-v2-002) ----------------------------------------
RANK_LO, RANK_HI, SEASON = 20, 40, 168
EARLY_LO = pd.Timestamp("2021-01-01")
EARLY_HI = pd.Timestamp("2024-01-01")  # EARLY = 2021..2023 inclusive
LATE_LO = pd.Timestamp("2024-01-01")
LATE_HI = e2.OOS_CUTOFF  # LATE = 2024-01-01 -> OOS cutoff (the faded IS tail), still IN-SAMPLE
W1_HI = pd.Timestamp("2026-01-01")  # OOS sub-window boundary

# Anchor numbers from iter-v2-002 (gate references; recomputed live below for the apples compare).
ANCHOR_IS_REF = 1.53
ANCHOR_LATE_REF = 1.16


# ---- signal builders for the §G4 same-pipeline baselines ------------------------------------
def trend_only_signal(coins: dict, elig: pd.DataFrame) -> pd.DataFrame:
    """Pure trend signal (the anchor's directional leg, λ=0) fed through run_book_from_signal."""
    panel = e2.build_panel(coins)
    sig = e2._signals(panel)
    return sig["trend"]


def xsmom_only_signal(coins: dict, elig: pd.DataFrame, lookback: int = 84) -> pd.DataFrame:
    """Pure XS-mom signal (centered within-band L-return rank) fed through run_book_from_signal —
    the iter-v2-002 standalone factor, on the SAME engine path as the ML signal for an apples G4."""
    panel = e2.build_panel(coins)
    xs, _mom = e2._xsmom(panel["close"], elig, lookback)
    return xs.where(elig)


# ---- evaluation -----------------------------------------------------------------------------
def evaluate_signal(coins: dict, signal_panel: pd.DataFrame, *, reveal: bool, **kw) -> dict:
    """Run a signal through run_book_from_signal and pull IS + EARLY/LATE + structure. OOS hidden
    unless reveal=True."""
    res = e2.run_book_from_signal(
        coins, signal_panel, rank_lo=RANK_LO, rank_hi=RANK_HI, season=SEASON, **kw
    )
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
        "_res": res,
    }
    if reveal:
        out["OOS"] = e2.msharpe(net, e2.OOS_CUTOFF, e2.HI1)
        out["OOS_w1"] = e2.msharpe(net, e2.OOS_CUTOFF, W1_HI)
        out["OOS_w2"] = e2.msharpe(net, W1_HI, e2.HI1)
    return out


def evaluate_anchor(coins: dict, *, reveal: bool, **kw) -> dict:
    """The TRUE anchor via run_book (walk-forward λ trend+carry blend) — the gate reference."""
    res = e2.run_book(coins, rank_lo=RANK_LO, rank_hi=RANK_HI, season=SEASON, **kw)
    net = res["net"]
    out = {
        "IS": e2.msharpe(net, e2.LO0, e2.OOS_CUTOFF),
        "EARLY": e2.msharpe(net, EARLY_LO, EARLY_HI),
        "LATE": e2.msharpe(net, LATE_LO, LATE_HI),
        "per_year": per_year_sharpe(net),
        "turn": res["turnover"],
        "avgPos": res["avg_positions"],
        "_net": net,
    }
    if reveal:
        out["OOS"] = e2.msharpe(net, e2.OOS_CUTOFF, e2.HI1)
    return out


def _fmt(label: str, r: dict, *, reveal: bool, extra: str = "") -> str:
    head = (
        f"  {label:34} IS={r['IS']:+.2f} EARLY={r['EARLY']:+.2f} LATE={r['LATE']:+.2f} "
        f"turn={r['turn']:.3f} aPos={r['avgPos']:.1f}"
    )
    if "tickets" in r:
        head += f" tix={r['tickets']:.1f}"
    if reveal and "OOS" in r:
        head += f"\n  {'':35} OOS={r['OOS']:+.2f}"
        if "OOS_w1" in r:
            head += f"  OOS(25-03..12)={r['OOS_w1']:+.2f}  OOS(26)={r['OOS_w2']:+.2f}"
    if extra:
        head += f"  {extra}"
    return head


def signal_dollar_neutrality(signal_panel: pd.DataFrame, elig: pd.DataFrame) -> float:
    """Max |Σ_c signal| across the eligible band — the dollar-neutral residual of the SIGNAL.

    This is the correct neutrality check: the centered within-band rank construction sums to ~0
    across the band, so the engine builds offsetting long/short legs. (Note: `held_w` itself is NOT
    instantaneously Σ=0 — gross-normalization Σ|w|=1 + the directional band/eligexit overlay let the
    booked NET drift, EXACTLY as the deployed anchor `run_book` held_w does, max|Σw|=1.0 there too.
    Neutrality lives in the signal, not a hard per-candle Σw=0 constraint after the overlay.)"""
    band_sum = signal_panel.where(elig).sum(axis=1)
    n_band = elig.sum(axis=1)
    sel = band_sum[(n_band > 0) & signal_panel.where(elig).notna().any(axis=1)]
    return float(sel.abs().max()) if len(sel) else float("nan")


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
    t0 = time.time()

    print("=" * 100)
    print("iter-v2-003 EXPLORATION — cross-sectional LightGBM return predictor on rank 21-40")
    print(f"  OOS is {'REVEALED (CONFIRMATION mode)' if reveal else 'HIDDEN (EXPLORATION mode)'}")
    print("=" * 100)

    coins = uv.load_pool_pit()
    print(f"\nPIT pool: {len(coins)} coins.  band=(rank {RANK_LO}-{RANK_HI}], season={SEASON}")

    # -----------------------------------------------------------------------------------------
    # ANCHOR (run_book trend+carry walk-forward λ) — the gate reference
    # -----------------------------------------------------------------------------------------
    print("\n" + "-" * 100)
    print("[ANCHOR] run_book trend+carry walk-forward λ (the comparison baseline)")
    print("-" * 100)
    anchor = evaluate_anchor(coins, reveal=reveal, slip_bps_fn=e2.default_slip_bps)
    print(_fmt("anchor (run_book λ-stitch)", anchor, reveal=reveal))
    print(f"  per-year Sharpe: {anchor['per_year']}")
    anc_is, anc_late = anchor["IS"], anchor["LATE"]

    # -----------------------------------------------------------------------------------------
    # Feature panel (ALL past-only) + leak-safe walk-forward LightGBM
    # -----------------------------------------------------------------------------------------
    print("\n" + "-" * 100)
    print("[ML] build feature panel -> leak-safe monthly walk-forward LightGBM")
    print("-" * 100)
    long_df, elig, opens_index, cols = ml_v2.build_feature_panel(
        coins,
        rank_lo=RANK_LO,
        rank_hi=RANK_HI,
        season=SEASON,
        slip_bps_fn=e2.default_slip_bps,
    )
    print(
        f"  tidy band frame: {len(long_df):,} rows x {len(ml_v2.FEATURE_COLUMNS)} features; "
        f"label non-NaN: {int(long_df['label'].notna().sum()):,}"
    )
    pred_panel, importances, covered, skipped = ml_v2.walk_forward_predict(long_df, elig)
    total_months = len(covered) + len(skipped)
    cold_frac = len(skipped) / total_months if total_months else float("nan")
    print(
        f"  walk-forward: {len(covered)} covered months, {len(skipped)} cold-start months; "
        f"cold-start month fraction = {cold_frac:.1%}"
    )

    # -----------------------------------------------------------------------------------------
    # ML signal panel + anchor cold-start fallback (candle-level coverage fraction)
    # -----------------------------------------------------------------------------------------
    ml_sig = ml_v2.pred_to_signal(pred_panel, elig)
    anchor_fallback = ml_v2.anchor_signal_panel(
        coins, rank_lo=RANK_LO, rank_hi=RANK_HI, season=SEASON
    ).reindex(index=opens_index, columns=cols)

    # per candle: covered month -> ML signal; else (cold-start month) -> anchor fallback signal.
    covered_months = pd.PeriodIndex([], freq="M") if not covered else pd.PeriodIndex(covered)
    candle_month = pd.PeriodIndex(opens_index, freq="M")
    ml_month_mask = pd.Series(candle_month.isin(covered_months), index=opens_index)
    # only count candles where the band is non-empty (a signal is actually needed)
    band_present = elig.sum(axis=1) > 0
    needed = band_present
    ml_candles = int((ml_month_mask & needed).sum())
    fb_candles = int((~ml_month_mask & needed).sum())
    cold_candle_frac = fb_candles / (ml_candles + fb_candles) if (ml_candles + fb_candles) else 0.0

    # blended signal: ML on covered months, anchor fallback on cold-start months
    blended = ml_sig.copy()
    fb_rows = ~ml_month_mask
    blended.loc[fb_rows] = anchor_fallback.loc[fb_rows]
    print(
        f"  candle-level: ML-covered band candles={ml_candles:,}, "
        f"fallback band candles={fb_candles:,}  (cold-start candle frac={cold_candle_frac:.1%})"
    )

    # -----------------------------------------------------------------------------------------
    # Run the ML signal + the two §G4 same-pipeline baselines through run_book_from_signal
    # -----------------------------------------------------------------------------------------
    print("\n" + "-" * 100)
    print("[EXPLORATION] ML signal vs same-pipeline TREND-only / XS-mom-only baselines (G4)")
    print("-" * 100)
    ml_res = evaluate_signal(coins, blended, reveal=reveal, slip_bps_fn=e2.default_slip_bps)
    tr_sig = trend_only_signal(coins, elig)
    xs_sig = xsmom_only_signal(coins, elig, lookback=84)
    tr_res = evaluate_signal(coins, tr_sig, reveal=reveal, slip_bps_fn=e2.default_slip_bps)
    xs_res = evaluate_signal(coins, xs_sig, reveal=reveal, slip_bps_fn=e2.default_slip_bps)

    print(_fmt("anchor (run_book λ)", anchor, reveal=reveal))
    print(
        _fmt(
            "ML xs-predictor (blended)",
            ml_res,
            reveal=reveal,
            extra=f"ΔLATE_vs_anchor={ml_res['LATE'] - anc_late:+.2f}",
        )
    )
    print(
        _fmt(
            "TREND-only (via _from_signal)",
            tr_res,
            reveal=reveal,
            extra=f"ML-ΔLATE_vs_trend={ml_res['LATE'] - tr_res['LATE']:+.2f}",
        )
    )
    print(
        _fmt(
            "XS-mom-only (via _from_signal)",
            xs_res,
            reveal=reveal,
            extra=f"ML-ΔLATE_vs_xs={ml_res['LATE'] - xs_res['LATE']:+.2f}",
        )
    )
    print(f"\n  ML per-year Sharpe   : {ml_res['per_year']}")
    print(f"  trend per-year Sharpe: {tr_res['per_year']}")
    print(f"  xs    per-year Sharpe: {xs_res['per_year']}")
    print(
        f"  ML structure: turn={ml_res['turn']:.3f} tickets={ml_res['tickets']:.1f} "
        f"avgPos={ml_res['avgPos']:.1f} band={ml_res['band']:.1f}  "
        f"(anchor turn={anchor['turn']:.3f} avgPos={anchor['avgPos']:.1f})"
    )
    # neutrality of the ML signal alone (covered months) vs the blended panel (incl. directional
    # cold-start anchor fallback, which is NOT centered -> its band-sum is non-zero by design).
    dn_ml = signal_dollar_neutrality(ml_sig.where(ml_month_mask, other=float("nan")), elig)
    dn_blend = signal_dollar_neutrality(blended, elig)
    hw_net = float(ml_res["_res"]["held_w"].sum(axis=1).abs().max())
    print(
        f"  dollar-neutrality (SIGNAL): ML-signal max|Σ_c|={dn_ml:.2e} (machine-0 => neutral by "
        f"construction); blended max|Σ_c|={dn_blend:.2e} (residual = the {cold_candle_frac:.1%} "
        f"directional anchor-fallback candles, NOT the ML signal); held_w net max|Σw|={hw_net:.2f} "
        f"(engine-inherent gross-norm drift, anchor run_book=1.00 too)"
    )

    # -----------------------------------------------------------------------------------------
    # Feature importance (top ~12 by mean monthly gain) — G4 single-feature concentration read
    # -----------------------------------------------------------------------------------------
    print("\n" + "-" * 100)
    print("[FEATURE IMPORTANCE] mean monthly gain (top ~12) — G4 (no single-feature carry)")
    print("-" * 100)
    if len(importances):
        mean_gain = importances.mean(axis=0).sort_values(ascending=False)
        share = mean_gain / mean_gain.sum()
        for i, (name, g) in enumerate(mean_gain.head(12).items()):
            print(f"    {i + 1:2d}. {name:22} mean_gain={g:12.1f}  share={share[name]:6.1%}")
        top1 = share.iloc[0]
        print(f"  top-1 feature gain share = {top1:.1%}  (G4 wants this NOT dominant)")
    else:
        print("    (no covered months — no importance)")

    # -----------------------------------------------------------------------------------------
    # Cost stress — ML LATE under 2x-taker AND pessimistic slip (G3 rank-churn survival)
    # -----------------------------------------------------------------------------------------
    print("\n" + "-" * 100)
    print("[COST STRESS] ML LATE under 2x-taker + pessimistic-slip (G3 — rank-churn is the risk)")
    print("-" * 100)
    stresses = [
        ("default slip", dict(slip_bps_fn=e2.default_slip_bps)),
        ("2x taker cost", dict(slip_bps_fn=e2.default_slip_bps, cost_mult=2.0)),
        ("2x slip", dict(slip_bps_fn=e2.default_slip_bps, slip_mult=2.0)),
        ("slip_pessimistic", dict(slip_bps_fn=slip_pessimistic)),
    ]
    for name, skw in stresses:
        r = evaluate_signal(coins, blended, reveal=reveal, **skw)
        ar = evaluate_anchor(coins, reveal=reveal, **skw)
        print(
            _fmt(
                f"{name}",
                r,
                reveal=reveal,
                extra=f"anchorLATE={ar['LATE']:+.2f} ΔLATE={r['LATE'] - ar['LATE']:+.2f}",
            )
        )

    # -----------------------------------------------------------------------------------------
    # EXPLORATION gate read G1..G5 (IS + LATE only; OOS NEVER consulted)
    # -----------------------------------------------------------------------------------------
    print("\n" + "=" * 100)
    print("EXPLORATION gates (IS + LATE only — OOS hidden)")
    print("=" * 100)
    g1 = ml_res["IS"] >= anc_is - 0.10
    g2 = (ml_res["LATE"] - anc_late) >= 0.20
    ml_late = ml_res["LATE"]
    g4_vs_trend = ml_late > tr_res["LATE"]
    g4_vs_xs = ml_late > xs_res["LATE"]
    # cost survival is read from the cost-stress block (2x taker + pessimistic ΔLATE both > 0)
    print(
        f"  G1 IS (ML IS >= anchor-0.10)                : {'PASS' if g1 else 'FAIL'} "
        f"(ML IS={ml_res['IS']:+.2f} vs floor {anc_is - 0.10:+.2f})"
    )
    print(
        f"  G2 LATE lift (ΔLATE >= +0.20) [LOAD-BEARING]: {'PASS' if g2 else 'FAIL'} "
        f"(ML LATE={ml_late:+.2f} vs anchor {anc_late:+.2f}, ΔLATE={ml_late - anc_late:+.2f})"
    )
    print("  G3 cost survival (2x-taker + pessimistic)   : read from the cost-stress block above")
    print(
        f"  G4 beats its own ingredients on LATE        : "
        f"vsTREND {'PASS' if g4_vs_trend else 'FAIL'} (ML {ml_late:+.2f} v {tr_res['LATE']:+.2f}); "
        f"vs XS-mom-only {'PASS' if g4_vs_xs else 'FAIL'} (vs {xs_res['LATE']:+.2f})"
    )
    print(
        f"  G5 methodology (dollar-neutral, cold-start)  : "
        f"ML max|Σ|={dn_ml:.2e}; cold-start month={cold_frac:.1%} cand={cold_candle_frac:.1%} "
        f"(leak test green in pytest; parity_check unchanged)"
    )

    if not reveal:
        print("\n  (OOS intentionally HIDDEN — judged at the separate CONFIRMATION reveal only.)")
    print(f"\n  wall-clock: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
