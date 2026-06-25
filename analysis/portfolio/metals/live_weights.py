"""Live parity bridge — extract the DEPLOYED per-metal position book from the iter-008 regime book.

The backtest book (`iter_008_allweather.regime_book`) returns only the NET return series. The live
paper engine needs the actual per-metal POSITIONS the desk holds each candle (to place paper orders
and to parity-check the live book). This module reconstructs them from the SAME functions/arithmetic
the backtest uses (`universe_metals.deployed_from_raw`), so the live target is bit-identical to what
the backtest deploys — proven by `tests/test_live_parity_metals.py`.

The desk is a portfolio of two independently vol-targeted sub-strategies (per the iter-008 design):
    leg1 = a_w · (flat-in-bear long anchor, DD-braked)          # braked sleeve
    leg2 = d_w(t) · (dollar-neutral dispersion, UNbraked)       # regime-scaled bear-payer
    d_w(t) = dw_bull + (dw_bear − dw_bull)·b[t]                 # b = confirmed-bear breadth flag

Per-metal DEPLOYED position during candle t (decided at close[t−1], held through t):
    desk[t,i] = a_w · dep_anchor[t,i] · brake[t]  +  d_w(t) · dep_disp[t,i]
where dep_*[t,i] = gross-normed-lagged-weight[t,i] × that leg's own vol-target scalar[t].

`next_target_weights_metals(coins)` returns the LAST ROW (the target for the just-opened candle),
the live analogue of the crypto `strategy.next_target_weights`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import iter_002_mn_overlay as ov  # noqa: E402
import iter_007_allweather as aw  # noqa: E402
import iter_007_calibrate as cal  # noqa: E402
import iter_008_allweather as r8  # noqa: E402
import universe_metals as um  # noqa: E402

CHAMP = r8.CHAMP  # frozen champion: {win, thresh, a_w, dw_bull, dw_bear}
BRAKE_FLOOR = 0.25  # iter-007 _brake default (floor=0; floor=0 self-locks)


def _legs_deployed(coins: dict[str, pd.DataFrame]):
    """Return the two legs' deployed-position books + their nets + the bear flag.

    (dep_anchor_braked, net_anchor_braked, dep_disp, net_disp, d_w, b) — every series/frame is the
    SAME arithmetic the backtest runs, so the live target is parity-exact.
    """
    pan = um.panels(coins)
    ret_fwd = pan["ret_fwd"]

    # ── leg 1: flat-in-bear long anchor → deployed positions → DD-brake (anchor sleeve only) ──
    a_raw, b = r8._anchor_flatbear_raw(coins, "ma", CHAMP["win"], CHAMP["thresh"], 0)
    net_a, dep_a = um.deployed_from_raw(a_raw, ret_fwd)
    c = cal.calibrate()  # IS-derived, bear-blind D_trip/D_rearm
    k_brake = aw.dd_brake_scalar(net_a, c["d_trip"], c["d_rearm"], BRAKE_FLOOR)
    k_on_book = k_brake.reindex(dep_a.index).fillna(1.0)
    dep_a_braked = dep_a.mul(k_on_book, axis=0)
    net_a_braked = net_a * k_brake  # == iter_008._brake(net_a)

    # ── leg 2: dollar-neutral dispersion → deployed positions (UNbraked) ──
    d_raw = ov.mn_dispersion_raw(pan["close"])
    net_d, dep_d = um.deployed_from_raw(d_raw, ret_fwd)

    # ── per-bar regime weight on the dispersion sleeve (LAGGED — uses b[t-1], leak-free; matches
    #    the iter_008.regime_book fix so live == backtest) ──
    d_w = CHAMP["dw_bull"] + (CHAMP["dw_bear"] - CHAMP["dw_bull"]) * b.shift(1).fillna(0.0)
    return dep_a_braked, net_a_braked, dep_d, net_d, d_w, b


def deployed_weight_book(coins: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.Series]:
    """Full per-candle DESK position book (per-metal weights) + the bear flag.

    desk[t,i] = a_w·dep_anchor_braked[t,i] + d_w(t)·dep_disp[t,i]  — the positions the desk holds.
    """
    dep_a_braked, _, dep_d, _, d_w, b = _legs_deployed(coins)
    cols = dep_a_braked.columns.union(dep_d.columns)
    a = CHAMP["a_w"] * dep_a_braked.reindex(columns=cols, fill_value=0.0)
    d = dep_d.reindex(columns=cols, fill_value=0.0).mul(
        d_w.reindex(dep_d.index).fillna(0.0), axis=0
    )
    return a.add(d, fill_value=0.0), b


def regime_net(coins: dict[str, pd.DataFrame]) -> pd.Series:
    """The desk NET return series (paper-PnL source of truth) — `regime_book` net, bit-exact."""
    net, _ = r8.regime_book(coins)
    return net


def next_target_weights_metals(coins: dict[str, pd.DataFrame], tol: float = 1e-9) -> dict:
    """Per-metal DEPLOYED position to hold during the just-opened forming candle — the live target.

    The last row of `deployed_weight_book`, the metals analogue of the crypto
    `strategy.next_target_weights`. Returns {ticker: signed_weight, ..., "_meta": {...}}.
    """
    desk, b = deployed_weight_book(coins)
    last = desk.iloc[-1]
    pos = last[last.abs() > tol]
    out = {s: float(v) for s, v in pos.items()}
    out["_meta"] = {
        "as_of": str(desk.index[-1]),
        "bear_flag": float(b.iloc[-1]),
        "gross": float(last.abs().sum()),
        "n_positions": int(len(pos)),
    }
    return out
