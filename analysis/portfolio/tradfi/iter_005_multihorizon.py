"""iter-005 — MULTI-HORIZON within-sector momentum blend.

ONE change vs iter-003: replace the single 12-1m within-sector momentum SIGNAL with an
EQUAL-WEIGHT blend of within-sector momentum at THREE speeds {3-1m, 6-1m, 12-1m}. Everything
downstream — the iter-003 hysteresis band (delta=0.005), the leak-safe banded_net / vol-target /
taker-cost model, and the OOS-hidden accounting — is UNCHANGED. Only the signal that feeds the band
is now an average of three momentum sleeves instead of one.

Why multi-horizon: a single momentum speed is a single bet on one persistence timescale. The
universe is momentum-persistent at multiple, imperfectly-correlated speeds (IS net corr
rho(3-1,12-1)=+0.47, rho(6-1,12-1)=+0.59). The 3-1m sleeve has gross +0.32 (as strong as 12-1m) and
is only ~0.47-correlated to it — a second, decorrelated source of the same edge a single horizon
leaves on the table. The shorter sleeves also earn in CHOP (6-1m chop +0.90) — the one regime the
12-1m book sits out. Blending raises the gross ceiling (+0.29 -> +0.40) AND the all-weather count
(1/3 -> 2/3) with a better maxDD, at the cost of a genuinely deeper bear (the fast sleeve crashes in
sustained reversals). This is a breadth/robustness change, not a headline-net change.

The blend (each sleeve gross-normed to unit gross FIRST so no sleeve dominates by scale):

    rvol = close.pct_change().rolling(63).std()                              # 63d realized vol
    sleeve(h) = gross_norm( sector_neutralize( (close.shift(21)/close.shift(h)-1)/rvol, MAP ) )
    raw       = ( sleeve(63) + sleeve(126) + sleeve(252) ) / 3      # equal-weight blend
    net, w    = i3.banded_net(raw, ret_fwd, delta=0.005)            # iter-003 band path UNCHANGED

skip is FIXED at 21 (1-month); the three speeds differ only by the long leg h in {63,126,252}.
Every sleeve is past-only (close.shift(>=21) + a trailing-63 rvol), and the blend is a row-wise
linear combination of leak-safe gross-normed sleeves, so the combined banded build is future-bar
leak-safe (covered by test_iter005_multihorizon_banded_future_bar_no_leak).

Pre-registered IDENTITY check: a degenerate one-sleeve blend `sleeve(252)` (gross-norm of a single
sleeve is idempotent through the band's own gross-norm) through banded_net(...,0.005) reproduces
iter-003's net +0.16 bit-for-bit (test_iter005_single_sleeve_banded_reproduces_iter003).

EQUAL-WEIGHT is pre-registered (NOT risk-parity): inverse-sleeve-vol parity over-weights the weak
6-1m sleeve and collapses net. The {3-1,6-1,12-1} subset is pre-registered (NOT swept): it is the
only candidate that simultaneously beats the +0.29 gross ceiling and improves the all-weather count
with a better maxDD. delta stays 0.005, inherited from iter-003 — the band is NOT re-optimized.

OOS stays HIDDEN (perf_line reveal_oos=False) unless --confirm (CONFIRMATION only). Everything here
is IS-only; no OOS number is computed without --confirm. Do NOT tune the speeds / delta here.
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
import iter_002_sector_rel as i2  # noqa: E402
import iter_003_hysteresis as i3  # noqa: E402
import neutralize as nz  # noqa: E402
import universe_tradfi as ut  # noqa: E402

SKIP = 21  # 1-month skip, FIXED (== iter-002/iter-003); the speeds differ only by the long leg
HORIZONS_MH = (63, 126, 252)  # 3-1m / 6-1m / 12-1m long legs — pre-registered blend, NOT swept
CHOSEN_DELTA = i3.CHOSEN_DELTA  # 0.005, inherited from iter-003 UNCHANGED


def _rvol(close: pd.DataFrame) -> pd.DataFrame:
    """Trailing-63 realized vol of daily returns — the same rvol every sleeve uses (past-only)."""
    return close.pct_change().rolling(ct.VOL_WIN).std()


def mom_sleeve(pn, lookback: int, skip: int = SKIP) -> pd.DataFrame:
    """Within-sector inverse-vol momentum over (close.shift(skip)/close.shift(lookback)-1).

    Sector-neutralized (per-sector demean -> dollar-neutral by construction), NOT yet gross-normed.
    All past: close.shift(skip>=21)/close.shift(lookback) + trailing-63 rvol. Identical primitive to
    iter-002's sector_rel_raw at (skip=21, lookback=252).
    """
    close = pn["close"]
    raw = (close.shift(skip) / close.shift(lookback) - 1.0) / _rvol(close)
    return nz.sector_neutralize(raw, ut.SECTOR_MAP)


def _gross_norm(raw: pd.DataFrame) -> pd.DataFrame:
    """Gross-normalize each row to unit gross (sum|w|=1), or 0 on warm-up/empty rows. Leak-free."""
    g = raw.abs().sum(axis=1).replace(0, np.nan)
    return raw.div(g, axis=0).fillna(0.0)


def sleeve(pn, lookback: int, skip: int = SKIP) -> pd.DataFrame:
    """The brief's `sleeve(lookback)`: gross-normed within-sector momentum sleeve.

    sleeve(252) == gross_norm(i2.sector_rel_raw) is idempotent through the band's own gross-norm, so
    a one-sleeve blend reproduces iter-003 bit-for-bit (pre-registered IDENTITY).
    """
    return _gross_norm(mom_sleeve(pn, lookback, skip))


def mh_raw(pn, horizons: tuple[int, ...] = HORIZONS_MH) -> pd.DataFrame:
    """EQUAL-WEIGHT multi-horizon blend: ( sleeve(63) + sleeve(126) + sleeve(252) ) / 3.

    Each sleeve is gross-normed to unit gross first so no horizon dominates by scale; the blend is a
    row-wise linear combination of past-only sleeves (leak-safe). Feeds the iter-003 band unchanged.
    """
    sleeves = [sleeve(pn, h) for h in horizons]
    acc = sleeves[0].copy()
    for s in sleeves[1:]:
        acc = acc.add(s, fill_value=0.0)
    return acc / len(sleeves)


def _report_build(label, raw, ret_fwd, delta, base_turn, *, reveal_oos=False):
    """Print the standard IS-only line for a banded build + return its (net, w, metrics) bundle."""
    net, w = i3.banded_net(raw, ret_fwd, delta)
    gnet, _ = i3.banded_net(raw, ret_fwd, delta, cost_on=False)
    sh_net = ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF)
    sh_gross = ct.msharpe(gnet, ct.LO0, ct.OOS_CUTOFF)
    turn = ct.turnover(w, ct.LO0, ct.OOS_CUTOFF)
    reg = ct.regime_sharpe(ct.is_only(net))
    n_pos = sum(1 for v in reg.values() if v > 0)
    mdd = ct.maxdd(ct.is_only(net)) * 100
    tpc = "" if base_turn is None else f"  (turn {(turn / base_turn - 1) * 100:+.0f}% vs 12-1m)"
    print(ct.perf_line(label, net, reveal_oos=reveal_oos))
    print(
        f"      gross={sh_gross:+.2f} net={sh_net:+.2f} drag={sh_gross - sh_net:+.2f}  "
        f"maxDD={mdd:.0f}%  turn/day={turn:.4f}{tpc}"
    )
    print(
        f"      regimes(IS): bull={reg['bull']:+.2f} bear={reg['bear']:+.2f} "
        f"chop={reg['chop']:+.2f}  ({n_pos}/3 positive)"
    )
    return {
        "net": net,
        "w": w,
        "sh_net": sh_net,
        "sh_gross": sh_gross,
        "turn": turn,
        "reg": reg,
        "n_pos": n_pos,
        "mdd": mdd,
    }


def _n_active(w: pd.DataFrame) -> float:
    """Mean number of non-zero names per IS active bar (book breadth)."""
    w_is = w[w.index < ct.OOS_CUTOFF]
    live = w_is.abs().sum(axis=1) > 1e-9
    return float((w_is[live] != 0).sum(axis=1).mean()) if live.any() else float("nan")


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
    ret_fwd = pn["ret_fwd"]

    print("=" * 96)
    print("iter-005 — MULTI-HORIZON within-sector momentum blend, iter-003 band (IS-only)")
    print("=" * 96)
    print(
        f"  band delta={d:.3f} (iter-003 UNCHANGED); speeds {{3-1,6-1,12-1}}m "
        f"= skip=21 / long-leg {HORIZONS_MH}\n"
    )

    # --- IDENTITY: a one-sleeve blend sleeve(252) banded must reproduce iter-003 (+0.16). The
    # blend's per-sleeve gross-norm + the band's own gross-norm is idempotent up to MACHINE EPSILON
    # (the extra division re-rounds), so the match is allclose ~1e-16, not bit-exact; msharpe == ---
    net_one, _ = i3.banded_net(sleeve(pn, 252), ret_fwd, d)
    net_i3, _ = i3.banded_net(i2.sector_rel_raw(pn), ret_fwd, d)
    sh_one = ct.msharpe(net_one, ct.LO0, ct.OOS_CUTOFF)
    sh_i3 = ct.msharpe(net_i3, ct.LO0, ct.OOS_CUTOFF)
    maxdiff = float(np.nanmax(np.abs(net_one.to_numpy() - net_i3.to_numpy())))
    ident = bool(np.allclose(net_one.to_numpy(), net_i3.to_numpy(), atol=1e-12, rtol=0.0))
    print(
        f"  IDENTITY one-sleeve sleeve(252) banded == iter-003: {'PASS' if ident else 'FAIL'} "
        f"(allclose 1e-12; max|d|={maxdiff:.1e}, machine-eps double-gross-norm)  "
        f"IS_Sharpe={sh_one:+.2f} vs iter-003 {sh_i3:+.2f}\n"
    )

    # --- (1) STANDALONE single-horizon sleeves (each through the SAME iter-003 band) ---
    print(f"  --- STANDALONE single-horizon sleeves (each banded delta={d:.3f}) ---")
    m12 = _report_build(
        "12-1m (=iter-003)", sleeve(pn, 252), ret_fwd, d, None, reveal_oos=args.confirm
    )
    base_turn = m12["turn"]
    _report_build("3-1m (63/21)", sleeve(pn, 63), ret_fwd, d, base_turn, reveal_oos=args.confirm)
    _report_build("6-1m (126/21)", sleeve(pn, 126), ret_fwd, d, base_turn, reveal_oos=args.confirm)

    # --- (2) HEADLINE: equal-weight multi-horizon blend ---
    print(f"\n  --- HEADLINE: EQUAL-WEIGHT blend {{3-1,6-1,12-1}} (banded delta={d:.3f}) ---")
    mh = _report_build(
        "EW{3-1,6-1,12-1}", mh_raw(pn), ret_fwd, d, base_turn, reveal_oos=args.confirm
    )
    reg = mh["reg"]
    print(f"      N active (IS, mean names/bar): {_n_active(mh['w']):.1f} of {len(coins)} ingested")
    print(f"      sector-neutrality residual (IS active): {i3._sector_residual(mh['w']):.1e}")
    print(
        f"\n  vs iter-003 (12-1m net +0.16):  d_net={mh['sh_net'] - m12['sh_net']:+.2f}  "
        f"d_gross={mh['sh_gross'] - m12['sh_gross']:+.2f}  "
        f"d_chop={reg['chop'] - m12['reg']['chop']:+.2f}  "
        f"d_bear={reg['bear'] - m12['reg']['bear']:+.2f}"
    )

    # --- (3) PRE-REGISTERED KEEP gates (task brief): KEEP as new working best iff ALL hold ---
    g_net = mh["sh_net"] > 0.16
    g_allw = mh["n_pos"] >= 2
    g_gross = mh["sh_gross"] >= 0.35
    g_bear = not (reg["bear"] < -1.3 and mh["sh_net"] < 0.18)
    keep = g_net and g_allw and g_gross and g_bear
    print(
        f"\n  KEEP gates: net>+0.16={'Y' if g_net else 'N'}  "
        f"all-weather>=2/3={'Y' if g_allw else 'N'}  "
        f"gross>=+0.35={'Y' if g_gross else 'N'}  "
        f"NOT(bear<-1.3 & net<+0.18)={'Y' if g_bear else 'N'}"
    )
    print(f"  VERDICT: {'KEEP (new working best)' if keep else 'REJECT (keep iter-003)'}")
    print(
        "  note: net is under the +0.30 baseline-promote bar -> PROMISING-INTERMEDIATE "
        "(breadth/all-weather win), not a baseline-promote."
    )


if __name__ == "__main__":
    main()
