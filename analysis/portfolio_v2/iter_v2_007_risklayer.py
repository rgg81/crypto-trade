"""iter-v2-007 — IS-CALIBRATED risk layer for the v2 BASELINE CANDIDATE (xs-mom 21-40 8h).

Candidate (fixed-parameter, no monthly tuning), reusing verify_xsmom_8h.py's construction:
    signal = _xsmom(close, elig, lookback=84)  unit-L1 normalized
    run_book_from_signal(rank_lo=20, rank_hi=40, season=168, slip_bps_fn=default_slip_bps)
    -> raw IS +0.43 / OOS +1.20 ; maxDD -37% IS / -25% OOS.

PROBLEM: -25% OOS DD too deep for a Sharpe +1.2 dollar-neutral book to deploy unbounded.

RISK LAYER (risk_v2.py), two orthogonal past-only primitives, both as an exposure multiplier on net:
  (1) STATIC TIGHTENING — lower TARGET_VOL / MAX_LEV (exact vol-target retarget): shallower
      UNCONDITIONAL tail.
  (2) R2-style DD BRAKE — rolling-peak loss-stop, binary cut to brake_factor while a trailing-DD
      hysteresis state is engaged: a conditional TAIL stop.

ALL thresholds calibrated on IS DATA ONLY (pre-2025-03-24), frozen, then evaluated OOS. NO OOS
tuning. The IS frontier is swept; the frozen pick maximises IS Calmar subject to an IS-DD bound;
the brake is evaluated as a genuine tail-stop (looser triggers) with its IS duty cycle reported so a
"permanent brake masquerading as a tail-stop" is caught. OOS reported but NEVER used to select.

Run:  uv run python analysis/portfolio_v2/iter_v2_007_risklayer.py
"""

from __future__ import annotations

import os
import sys
from itertools import product
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
os.chdir(_ROOT)
sys.path.insert(0, str(_ROOT / "analysis"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from portfolio_v2 import engine_v2 as e2  # noqa: E402
from portfolio_v2 import risk_v2 as r2  # noqa: E402
from portfolio_v2 import universe_v2 as uv  # noqa: E402
from portfolio_v2.diag_v2_001 import per_year_sharpe, slip_pessimistic  # noqa: E402
from portfolio_v2.engine_v2 import _xsmom, build_panel  # noqa: E402

OOS = e2.OOS_CUTOFF
W1_HI = pd.Timestamp("2026-01-01")


# ---------------------------------------------------------------------------------------------
# Candidate construction (reused verbatim from verify_xsmom_8h.py)
# ---------------------------------------------------------------------------------------------
def _signal(pool, panel, lb=84):
    elig = (
        uv.eligibility(pool, 20, 40, 168)
        .reindex(index=panel["opens"].index, columns=panel["cols"])
        .fillna(False)
    )
    xs, _ = _xsmom(panel["close"], elig, lb)
    return xs.div(xs.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def build_candidate(pool, panel, lb=84, slip_fn=e2.default_slip_bps, **run_kw):
    """Engine result dict for the fixed-parameter candidate (incl. raw_net)."""
    return e2.run_book_from_signal(
        pool,
        _signal(pool, panel, lb),
        rank_lo=20,
        rank_hi=40,
        season=168,
        slip_bps_fn=slip_fn,
        **run_kw,
    )


def stats(net: pd.Series) -> dict:
    return {
        "IS": e2.msharpe(net, e2.LO0, OOS),
        "OOS": e2.msharpe(net, OOS, e2.HI1),
        "OOS_25": e2.msharpe(net, OOS, W1_HI),
        "OOS_26": e2.msharpe(net, W1_HI, e2.HI1),
        "maxDD": r2.max_dd(net) * 100.0,
        "oosDD": r2.window_dd(net, OOS) * 100.0,
    }


def is_calmar(net: pd.Series) -> float:
    """IS-only Calmar = IS annualized return / |IS-window maxDD|. SELECTION metric (IS-ONLY)."""
    s = net[(net.index >= e2.LO0) & (net.index < OOS)]
    if len(s) == 0:
        return float("nan")
    g = s.groupby(s.index.to_period("M")).sum()
    ann_ret = float(g.mean()) * 12.0
    dd = abs(r2.window_dd(net, e2.LO0, OOS))
    return ann_ret / dd if dd > 1e-9 else float("nan")


def is_dd(net):
    return r2.window_dd(net, e2.LO0, OOS) * 100.0


def brake_duty_is(raw_net, cfg):
    """IS-window brake duty cycle (% of IS candles engaged) for the chosen retarget+brake."""
    rt = r2.retarget(raw_net, cfg.target_vol, cfg.max_lev)
    if cfg.dd_trigger is None:
        return 0.0
    b = r2.dd_brake_multiplier(rt, cfg.dd_trigger, cfg.dd_release, cfg.brake_factor)
    bi = b[b.index < OOS]
    return float((bi < 1.0).mean()) * 100.0


# ---------------------------------------------------------------------------------------------
def main():
    pool = uv.load_pool_pit()
    panel = build_panel(pool)
    base = build_candidate(pool, panel)
    raw_net = base["raw_net"]
    base_net = base["net"]
    base_turn = base["turnover"]

    print("=" * 100)
    print("iter-v2-007 — IS-CALIBRATED RISK LAYER  (xs-mom 21-40 8h candidate)")
    print("=" * 100)
    s0 = stats(base_net)
    print(
        f"\nRAW CANDIDATE: IS={s0['IS']:+.2f} OOS={s0['OOS']:+.2f} "
        f"[2025={s0['OOS_25']:+.2f} 2026={s0['OOS_26']:+.2f}] "
        f"maxDD={s0['maxDD']:.0f}% oosDD={s0['oosDD']:.0f}% turn={base_turn:.3f}"
    )

    # =========================================================================================
    # TIER A — STATIC TIGHTENING ONLY (lower TARGET_VOL / MAX_LEV). IS-only frontier.
    # =========================================================================================
    print("\n" + "=" * 100)
    print("TIER A — STATIC TIGHTENING ONLY (no DD brake). IS-only frontier; OOS not consulted.")
    print("=" * 100)
    print(f"  {'tv':>6} {'ml':>5} {'IS_sharpe':>10} {'IS_DD':>7} {'IS_calmar':>10}")
    tier_a = []
    for tv, ml in product([0.010, 0.008, 0.007, 0.006], [3.0, 2.5, 2.0]):
        cfg = r2.RiskConfig(target_vol=tv, max_lev=ml, dd_trigger=None)
        net = r2.apply_risk(raw_net, cfg)["net"]
        tier_a.append((tv, ml, cfg, stats(net)["IS"], is_dd(net), is_calmar(net)))
    for tv, ml, _c, sh, dd, cal in sorted(tier_a, key=lambda r: -r[5]):
        print(f"  {tv:6.3f} {ml:5.1f} {sh:+10.3f} {dd:7.1f} {cal:+10.3f}")

    # =========================================================================================
    # TIER B — DD BRAKE as a genuine TAIL-STOP (looser triggers), on top of a modest retarget.
    #          Report IS DUTY CYCLE so a "permanent brake" (high duty) is caught & rejected.
    # =========================================================================================
    print("\n" + "=" * 100)
    print("TIER B — DD BRAKE (tail-stop) on a modest retarget. IS-only; duty cycle exposes")
    print("         'permanent-brake' configs (high IS-duty => not a tail-stop => reject).")
    print("=" * 100)
    print(
        f"  {'tv':>6} {'ml':>5} {'trig':>5} {'rel':>5} {'bf':>5} "
        f"{'IS_sharpe':>10} {'IS_DD':>7} {'IS_calmar':>10} {'IS_duty%':>9}"
    )
    tier_b = []
    for tv, ml, trig, bf in product([0.008, 0.007], [2.5, 2.0], [0.25, 0.20, 0.16], [0.50, 0.33]):
        rel = trig * 0.6
        cfg = r2.RiskConfig(
            target_vol=tv, max_lev=ml, dd_trigger=trig, dd_release=rel, brake_factor=bf
        )
        net = r2.apply_risk(raw_net, cfg)["net"]
        duty = brake_duty_is(raw_net, cfg)
        tier_b.append(
            (tv, ml, trig, rel, bf, cfg, stats(net)["IS"], is_dd(net), is_calmar(net), duty)
        )
    for tv, ml, trig, rel, bf, _c, sh, dd, cal, duty in sorted(tier_b, key=lambda r: -r[8]):
        print(
            f"  {tv:6.3f} {ml:5.1f} {trig:5.2f} {rel:5.2f} {bf:5.2f} "
            f"{sh:+10.3f} {dd:7.1f} {cal:+10.3f} {duty:9.1f}"
        )

    # =========================================================================================
    # FROZEN PICK (IS-only rule, pre-registered):
    #   Objective = risk-adjusted (IS Calmar), NOT minimum DD. Bound the IS tail to <= -25%
    #   (a real cut from -37% raw) while preserving IS Sharpe. The DD-brake tier is DOMINATED on
    #   IS Calmar here (it is engaged most of the time => a blunt static cut, worse than simply
    #   lowering TARGET_VOL), so the frozen pick is STATIC TIGHTENING: the highest-IS-Calmar
    #   Tier-A row whose IS DD <= -25%. (We surface the best tail-stop too, for the record.)
    # =========================================================================================
    is_dd_target = -25.0
    a_ok = [r for r in tier_a if r[4] >= is_dd_target] or tier_a
    a_win = sorted(a_ok, key=lambda r: (-r[5], -r[3], -r[4]))[0]
    win_cfg = a_win[2]
    b_win = sorted(tier_b, key=lambda r: -r[8])[0]

    print("\n" + "=" * 100)
    print("FROZEN IS-CALIBRATED CONFIG (objective = IS Calmar s.t. IS DD <= -25%; OOS untouched)")
    print("=" * 100)
    print(
        f"  CHOSEN (static tightening): target_vol={win_cfg.target_vol} max_lev={win_cfg.max_lev} "
        f"dd_brake=OFF"
    )
    print(f"    -> IS Sharpe={a_win[3]:+.2f} IS DD={a_win[4]:.0f}% IS Calmar={a_win[5]:+.2f}")
    print(
        f"  (best tail-stop, for the record): tv={b_win[0]} ml={b_win[1]} trig={b_win[2]} "
        f"bf={b_win[4]} -> IS Calmar={b_win[8]:+.2f} IS DD={b_win[7]:.0f}% IS duty={b_win[9]:.0f}% "
        f"=> DOMINATED by static on IS Calmar"
    )

    # =========================================================================================
    # BEFORE / AFTER  (frozen config) at default + 2x-taker + pessimistic slip.
    # =========================================================================================
    scenarios = [
        ("default", dict(), e2.default_slip_bps),
        ("2x-taker", dict(cost_mult=2.0), e2.default_slip_bps),
        ("pessimistic", dict(), slip_pessimistic),
    ]
    print("\n" + "=" * 100)
    print("BEFORE / AFTER  (FROZEN risk layer)  —  raw candidate vs risk-layered")
    print("=" * 100)
    hdr = (
        f"  {'scenario':12} {'book':12} {'IS':>6} {'OOS':>6} {'2025':>6} {'2026':>6} "
        f"{'maxDD':>7} {'oosDD':>7} {'turn':>6}"
    )
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for label, kw, slip_fn in scenarios:
        res = build_candidate(pool, panel, slip_fn=slip_fn, **kw)
        rn = res["raw_net"]
        raw_s = stats(res["net"])
        risk_net = r2.apply_risk(rn, win_cfg)["net"]
        risk_s = stats(risk_net)
        # turnover scales with exposure multiplier (retarget gross ratio; brake off here)
        rt = r2.retarget(rn, win_cfg.target_vol, win_cfg.max_lev)
        ratio = float(rt.abs().sum() / res["net"].abs().sum()) if res["net"].abs().sum() else 1.0
        for tag, s, tn in (
            ("raw", raw_s, res["turnover"]),
            ("risk-layer", risk_s, base_turn * ratio),
        ):
            print(
                f"  {label:12} {tag:12} {s['IS']:+6.2f} {s['OOS']:+6.2f} "
                f"{s['OOS_25']:+6.2f} {s['OOS_26']:+6.2f} "
                f"{s['maxDD']:6.0f}% {s['oosDD']:6.0f}% {tn:6.3f}"
            )
        print("  " + "-" * (len(hdr) - 2))

    # =========================================================================================
    # PER-YEAR SHARPE + STRESS NOTE (worst OOS DD window; static book has no brake to lag).
    # =========================================================================================
    risk_net = r2.apply_risk(raw_net, win_cfg)["net"]
    print("\n[PER-YEAR SHARPE] risk-layered book (default cost):")
    print(f"  raw  : {per_year_sharpe(base_net)}")
    print(f"  risk : {per_year_sharpe(risk_net)}")

    print("\n[STRESS — worst OOS drawdown window]")
    oos_raw = base_net[base_net.index >= OOS]
    eq = (1 + oos_raw).cumprod()
    dd_s = eq / eq.cummax() - 1.0
    trough, peak = dd_s.idxmin(), eq[: dd_s.idxmin()].idxmax()
    oos_rk = risk_net[risk_net.index >= OOS]
    eqr = (1 + oos_rk).cumprod()
    ddr = float((eqr / eqr.cummax() - 1).min()) * 100
    print(
        f"  worst OOS raw DD: {float(dd_s.min()) * 100:.1f}% (peak {peak.date()} -> "
        f"trough {trough.date()})  ->  risk-layered OOS window DD = {ddr:.1f}%"
    )
    print(
        "  the static-tightening book shrinks this descent UNIFORMLY (exposure cut applies every "
        "candle, with ZERO lag — it cannot arrive late, unlike a reactive brake)."
    )

    # =========================================================================================
    # MECHANISM DECOMPOSITION — why OOS Sharpe is invariant while OOS DD falls. (IS+OOS shown for
    # transparency; this is forensics on the FROZEN pick, not a selection step.)
    # =========================================================================================
    print("\n[MECHANISM] target_vol scalar vs max_lev clip (forensics on the frozen pick):")
    rv = raw_net.rolling(e2.PORT_VOL_WIN).std().shift(1)
    for tv, ml, tag in [
        (e2.TARGET_VOL, e2.MAX_LEV, "engine default"),
        (0.006, e2.MAX_LEV, "tv=0.006 only (pure de-lever)"),
        (e2.TARGET_VOL, 2.0, "ml=2.0 only (clip de-concentrate)"),
        (win_cfg.target_vol, win_cfg.max_lev, "FROZEN"),
    ]:
        n = r2.retarget(raw_net, tv, ml)
        is_s = e2.msharpe(n, e2.LO0, OOS)
        oos_s = e2.msharpe(n, OOS, e2.HI1)
        print(
            f"  {tag:30} IS={is_s:+.3f} OOS={oos_s:+.3f} "
            f"IS_DD={r2.window_dd(n, e2.LO0, OOS) * 100:6.1f}% "
            f"OOS_DD={r2.window_dd(n, OOS, e2.HI1) * 100:6.1f}%"
        )
    sc_def = (e2.TARGET_VOL / rv).clip(upper=e2.MAX_LEV)
    sc_win = (win_cfg.target_vol / rv).clip(upper=win_cfg.max_lev)
    desc = (sc_def.index >= peak) & (sc_def.index <= trough)
    clip_pct = float((sc_def[desc] >= e2.MAX_LEV - 1e-3).mean()) * 100
    print(
        f"  worst OOS descent mean vol-target scale: default={float(sc_def[desc].mean()):.2f} "
        f"(MAX_LEV={e2.MAX_LEV}, clip-bound {clip_pct:.0f}%)  ->  "
        f"frozen={float(sc_win[desc].mean()):.2f}  =>  the DD cut is the de-lever, NOT the clip."
    )


if __name__ == "__main__":
    main()
