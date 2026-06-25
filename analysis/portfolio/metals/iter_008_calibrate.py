"""iter-008 — IS-ONLY, BEAR-BLIND calibration of the RISK-ARSENAL thresholds (reproducible).

Every threshold the arsenal uses is DERIVED here from the IN-SAMPLE (…→2025-03-24) data ALONE, by a
PRE-STATED rule fixed BEFORE the value is computed. The bear (2011–2015 data_bear/) is NEVER read
here — it is the one-shot validation set, evaluated downstream with these FROZEN numbers. The module
asserts it is pointed at `data/`, not `data_bear/`, so the discipline is structural, not a promise.

The IS data carries REAL regime transitions to calibrate transition-risk on: the 2015 gold bear,
2018, 2021, the 2022 shock, the 2020 COVID V. The regime-short PROXY runs ON the IS window so each
threshold sees how the short behaves at IS flips/squeezes — then the same numbers are frozen for
the unseen 2011–2015 bear.

PRE-STATED RULES (fixed before computing):
  R-A transition T      = the MEDIAN IS run-length of the regime flag (how long a regime persists);
                          taper = 0.5 (carry half gross through the uncertain fresh-flip window).
  R-B short_frac        = min(pre-registered ½ floor, IS long/short downside-semivol ratio) — the
                          short leg gets LESS gross than the long (secular tailwind is UP). The ½
                          floor is a ½-Kelly-style asymmetry; data-implied value reported alongside.
  R-C squeeze z, K, win = z at the 90th pct of the IS counter-rally-while-short move distribution
                          (a genuine fast rally, not noise); K = T/2 (half a regime run); win = 6
                          (2-day fast move, inherited cadence, not fit).
  R-D short trip/rearm  = the long band (iter-007 IS-derived D_trip/D_rearm) SCALED by the ratio of
                          IS short-leg semivol to long-leg semivol (shorts draw down faster → a
                          tighter trip); re-arm stays D_trip_short/2 (hysteresis preserved).

Run:  uv run python analysis/portfolio/metals/iter_008_calibrate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import iter_007_calibrate as c7  # noqa: E402  (the IS-derived long-band D_trip/D_rearm)
import iter_008_risk_arsenal as ar  # noqa: E402
import universe_metals as um  # noqa: E402

MAIN_DIR = _HERE.parents[2] / "data"  # IS + bull — NEVER data_bear/
TAPER = 0.5  # R-A: carry half gross through the fresh-flip window (pre-stated)
SHORT_FRAC_FLOOR = (
    0.5  # R-B: pre-registered ½-asymmetry floor (short ≤ ½ long unless data says less)
)
SQUEEZE_PCT = 0.90  # R-C: z at the 90th pct of the IS counter-rally-while-short move dist
SQUEEZE_WIN = 6  # R-C: 2-day fast-move window (inherited cadence, not fit)
SQUEEZE_FLOOR = 0.25  # R-C: cut to a quarter unit during a squeeze (matches DD-brake floor)


def _guard(data_dir: Path) -> None:
    if "bear" in str(data_dir).lower():
        raise AssertionError("calibration must NOT load bear data (IS-only discipline)")


def _run_length_median(s: pd.Series) -> int:
    """Median consecutive-run length of a binary series over IS (regime persistence, in candles)."""
    sv = s.to_numpy()
    runs = []
    if len(sv):
        cur = 1
        for i in range(1, len(sv)):
            if sv[i] == sv[i - 1]:
                cur += 1
            else:
                runs.append(cur)
                cur = 1
        runs.append(cur)
    return int(np.median(runs)) if runs else 0


def calibrate(data_dir: Path = MAIN_DIR) -> dict:
    """Derive every arsenal threshold from the IS window (bear-blind). Returns thresholds + prov."""
    _guard(data_dir)
    coins = um.load_metals(data_dir)

    # regime flag + regime-short proxy net, sliced IS-only
    net0, s = ar.book_rs_net0(coins)
    is_mask = net0.index < um.OOS_CUTOFF
    net0_is = net0[is_mask]
    s_is = s[is_mask]

    # ── R-A: transition window T = median IS regime-run length; taper pre-stated 0.5 ──────────
    t_candles = _run_length_median(s_is)
    n_flips_is = int((s_is.to_numpy()[1:] != s_is.to_numpy()[:-1]).sum())

    # ── R-B: short_frac from long-up-capture vs short-down-pain on the IS regime-short ────────
    #   long-leg mean per-candle net while LONG (s=0); short-leg mean while SHORT (s=1).
    long_net = net0_is[s_is < 0.5]
    short_net = net0_is[s_is >= 0.5]
    long_up = float(long_net[long_net > 0].mean()) if (long_net > 0).any() else np.nan
    short_dn = float(-short_net[short_net < 0].mean()) if (short_net < 0).any() else np.nan
    # downside-semivol of each leg (the tail the asymmetry must respect)
    long_semivol = float(long_net[long_net < 0].std()) if (long_net < 0).any() else np.nan
    short_semivol = float(short_net[short_net < 0].std()) if (short_net < 0).any() else np.nan
    # data-implied asymmetry: how much MORE downside-vol does the short leg carry?
    semivol_ratio = (
        float(np.clip(long_semivol / short_semivol, 0.0, 1.0))
        if short_semivol and short_semivol > 0
        else np.nan
    )
    # short_frac = min(pre-registered ½ floor, semivol-implied) → shorts get LESS gross than long
    short_frac = (
        float(round(min(SHORT_FRAC_FLOOR, semivol_ratio), 3))
        if semivol_ratio == semivol_ratio
        else SHORT_FRAC_FLOOR
    )

    # ── R-C: squeeze z = 90th pct of the counter-rally-while-short move; K = T/2; win fixed ───
    close = um.panels(coins)["close"]
    mret = close.pct_change(SQUEEZE_WIN).mean(axis=1)
    band = mret.rolling(126).std().shift(1)
    zmove = (mret / band).reindex(s.index)
    # restrict to IS bars where the book is net-short and band is valid → the squeeze-relevant dist
    relevant = zmove[is_mask][(s_is >= 0.5) & np.isfinite(zmove[is_mask])]
    z = (
        float(round(np.quantile(relevant.to_numpy(), SQUEEZE_PCT), 3))
        if len(relevant) > 10
        else 2.0
    )
    k_candles = max(1, t_candles // 2)

    # ── R-D: short-band = long-band scaled by long/short semivol ratio (shorts trip sooner) ───
    long_band_trip = c7.calibrate(data_dir)["d_trip"]
    long_band_rearm = c7.calibrate(data_dir)["d_rearm"]
    # tighten the trip in proportion to how much MORE downside-vol the short leg carries
    tighten = semivol_ratio if (semivol_ratio == semivol_ratio and semivol_ratio > 0) else 0.7
    d_trip_short = float(round(long_band_trip * tighten, 4))
    d_rearm_short = float(round(d_trip_short * 0.5, 4))

    # ── R-D′: rolling-peak window = 2× the median regime run (the brake forgets a stale peak once
    #   roughly one full regime cycle has elapsed; pre-stated multiple, not fit to any DD number) ──
    peak_win = max(t_candles, 2 * t_candles) if t_candles else 252

    return {
        # R-A
        "taper": TAPER,
        "t_candles": t_candles,
        "n_flips_is": n_flips_is,
        # R-B
        "short_frac": short_frac,
        "long_up": long_up,
        "short_dn": short_dn,
        "long_semivol": long_semivol,
        "short_semivol": short_semivol,
        "semivol_ratio": semivol_ratio,
        # R-C
        "squeeze_z": z,
        "squeeze_k": k_candles,
        "squeeze_win": SQUEEZE_WIN,
        "squeeze_floor": SQUEEZE_FLOOR,
        "n_squeeze_relevant": int(len(relevant)),
        # R-D
        "d_trip_long": long_band_trip,
        "d_rearm_long": long_band_rearm,
        "d_trip_short": d_trip_short,
        "d_rearm_short": d_rearm_short,
        "peak_win": peak_win,
        "floor": SQUEEZE_FLOOR,
        # provenance
        "n_is": int(len(net0_is)),
        "pct_is_short": float((s_is >= 0.5).mean()),
    }


def main() -> None:
    c = calibrate()
    print("iter-008 RISK-ARSENAL calibration — IS-ONLY (bear-blind), pre-stated rules")
    print(
        f"  IS candles={c['n_is']}  %IS net-short (proxy)={c['pct_is_short'] * 100:.1f}%  "
        f"regime flips IS={c['n_flips_is']}"
    )
    print("  ── R-A TRANSITION DE-RISK ──")
    print(f"     T (median IS regime-run) = {c['t_candles']} candles  taper={c['taper']}")
    print("  ── R-B ASYMMETRIC GROSS CAP ──")
    print(f"     long up-capture={c['long_up']:.5f}  short down-pain={c['short_dn']:.5f}")
    print(
        f"     long semivol={c['long_semivol']:.5f}  short semivol={c['short_semivol']:.5f}  "
        f"ratio(long/short)={c['semivol_ratio']:.3f}"
    )
    print(
        f"     → SHORT_FRAC = {c['short_frac']}  (pre-reg floor {SHORT_FRAC_FLOOR}; min of floor & "
        f"semivol-ratio → short ≤ long)"
    )
    print("  ── R-C SQUEEZE STOP ──")
    print(
        f"     z(90th pct rally-while-short)={c['squeeze_z']}  K={c['squeeze_k']}  "
        f"win={c['squeeze_win']}  floor={c['squeeze_floor']}  (n_rel={c['n_squeeze_relevant']})"
    )
    print("  ── R-D REGIME-AWARE DD-BRAKE ──")
    print(
        f"     long band  D_trip={c['d_trip_long'] * 100:.1f}%  "
        f"D_rearm={c['d_rearm_long'] * 100:.1f}%"
    )
    print(
        f"     short band D_trip={c['d_trip_short'] * 100:.1f}%  "
        f"D_rearm={c['d_rearm_short'] * 100:.1f}% (tightened by long/short semivol ratio)"
    )
    print("  bear data: NOT loaded (guarded).")


if __name__ == "__main__":
    main()
