"""IS-ONLY, BEAR-BLIND calibration of the iter-007 drawdown-brake thresholds — reproducible.

The Critic correctly blocked promotion because the brake's calibration provenance was hard-coded
literals, not computed output. This script DERIVES the thresholds live from the IN-SAMPLE
(…→2025-03-24) L2 drawdown distribution ALONE and is structurally bear-blind (it asserts it never
loads the 2011–2015 `data_bear/`). Run it to reproduce the exact thresholds the scorecard uses.

PRE-STATED RULE (fixed BEFORE computing, so the value is DERIVED, not reverse-engineered):
  - Arm the brake in the worst quintile of IS drawdown states:
        D_trip = depth d such that P(IS drawdown ≤ −d) = ARM_QUANTILE  (= 20%).
  - Re-arm at half the trip depth (hysteresis):  D_rearm = REARM_FRAC · D_trip   (REARM_FRAC = 0.5).
  - floor = 0.25 — a conservative non-zero residual (floor = 0 is a self-locking full halt).

The bear (2011–2015) is NEVER read here; it is evaluated ONCE downstream with these frozen values.

Run:  uv run python analysis/portfolio/metals/iter_007_calibrate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import iter_001_trend as it  # noqa: E402
import iter_002_mn_overlay as ov  # noqa: E402
import universe_metals as um  # noqa: E402

MAIN_DIR = _HERE.parents[2] / "data"  # the 4 metals (IS + bull) — NEVER data_bear/
ARM_QUANTILE = 0.20  # arm in the worst 20% of IS drawdown states
REARM_FRAC = 0.5  # re-arm at half the trip depth (hysteresis)
FLOOR = 0.25  # conservative non-zero residual (floor=0 self-locks — see dd_brake_scalar)


def _l2_is_net(data_dir: Path = MAIN_DIR) -> pd.Series:
    """The L2 book's vol-targeted net, sliced to the IN-SAMPLE window (< OOS_CUTOFF). BEAR-BLIND."""
    if "bear" in str(data_dir).lower():
        raise AssertionError("calibration must NOT load bear data (IS-only discipline)")
    coins = um.load_metals(data_dir)
    pan = um.panels(coins)
    raw = ov.gross_norm(it.build_raw(coins)) + 0.5 * ov.gross_norm(
        ov.mn_dispersion_raw(pan["close"])
    )
    net, _ = um.net_from_raw(raw, pan["ret_fwd"])
    return net[net.index < um.OOS_CUTOFF]


def calibrate(data_dir: Path = MAIN_DIR) -> dict:
    """Derive (d_trip, d_rearm, floor) from the IS L2 drawdown distribution via the worst-quintile
    rule. Returns the thresholds plus provenance fields (all computed, none hard-coded)."""
    net_is = _l2_is_net(data_dir)
    eq = (1.0 + net_is).cumprod()
    dd = eq / eq.cummax() - 1.0  # running peak-to-trough drawdown over IS
    d_trip = float(round(-np.quantile(dd.to_numpy(), ARM_QUANTILE), 4))
    d_rearm = float(round(REARM_FRAC * d_trip, 4))
    return {
        "d_trip": d_trip,
        "d_rearm": d_rearm,
        "floor": FLOOR,
        "is_sharpe": float(um.msharpe(net_is, um.LO0, um.OOS_CUTOFF)),
        "is_maxdd": float(dd.min()),
        "pct_bars_armed": float((dd <= -d_trip).mean()),
        "pct_bars_below_20pct": float((dd <= -0.20).mean()),
        "n_is": int(len(net_is)),
    }


def main() -> None:
    c = calibrate()
    print("iter-007 brake calibration — IS-ONLY (bear-blind), pre-stated worst-quintile rule")
    print(
        f"  RULE: D_trip = depth at the {ARM_QUANTILE:.0%} IS-drawdown quantile; "
        f"D_rearm = {REARM_FRAC:.0%}·D_trip; floor = {FLOOR}"
    )
    print(
        f"  IS L2: Sharpe={c['is_sharpe']:+.2f}  maxDD={c['is_maxdd'] * 100:.1f}%  n={c['n_is']}"
    )
    print(
        f"  DERIVED → D_trip={c['d_trip']:.4f} ({c['d_trip'] * 100:.1f}%)  "
        f"D_rearm={c['d_rearm']:.4f} ({c['d_rearm'] * 100:.1f}%)  floor={c['floor']}"
    )
    print(
        f"  %IS bars armed (dd ≤ −D_trip) = {c['pct_bars_armed'] * 100:.1f}% "
        f"(target {ARM_QUANTILE:.0%})   %IS bars ≤ −20% = {c['pct_bars_below_20pct'] * 100:.1f}%"
    )
    print("  bear data: NOT loaded (guarded in _l2_is_net).")


if __name__ == "__main__":
    main()
