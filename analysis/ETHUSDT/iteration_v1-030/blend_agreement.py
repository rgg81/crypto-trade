"""iter-v1/030 (ETHUSDT) — IS-ONLY: the COMPOSITE that resolves the sub-period tension.

orthogonality_and_subperiod.py revealed the key trade-off:
  - the single SMA200 anchor is BEST in the recent strong-trend regime (+1.31) but
    CATASTROPHIC in chop (2022 -0.67, 2024H1 -0.61) -> that chop is the source of its
    OOS-concentration fragility (a few big trend captures vs many wrong-way losses).
  - the family/TSMOM ensembles are ROBUST across regimes (much smaller chop losses) but
    GIVE UP recent-regime peak (+0.45 vs +1.31).

A pure REPLACEMENT therefore is NOT the right axis. The robust, de-concentrating design is
an AGREEMENT / FORECAST-COMBINATION architecture (Carver / AQR): keep the anchor's
direction, but use multi-speed AGREEMENT as a conviction modulator — size up / only-trade
when fast+medium+slow trend signals AGREE, stand aside (or shrink) when they conflict
(a chop signature). This is exactly Carver's forecast-combination + scaling, and AQR's
"low cross-correlation across horizons" diversification, expressed as a DETERMINISTIC,
past-only gate. Direction stays the SMA200 anchor (so recent-regime strength is preserved);
the multi-speed ensemble enters ONLY as an agreement-conviction filter.

Configs tested (all deterministic, past-only, IS-only):
  ANCHOR              : SMA200 direction, conviction gate q=0.40 (the iter-027 baseline)
  AGREE_GATE          : SMA200 direction; trade only when N-of-M trend signals agree with it
  AGREE_SCALE         : SMA200 direction; conviction-quantity *multiplied* by agreement score
                        (so disagreement rows are pushed below the gate => stand aside)
  ENSEMBLE_DIR_AGREE  : ensemble (signed-avg) DIRECTION + agreement gate (for contrast)

HARD RULE: open_time < OOS_CUTOFF_MS; drop horizon-crossing entries.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    OOS_CUTOFF_MS,
    add_forward_return,
    annualized_sharpe_from_trade_pnls,
    concentration_stats,
    drop_horizon_crossing_oos,
    load_full_for_label_horizon,
    trend_strength_atr_norm,
)
from multispeed_breadth import (  # noqa: E402
    COST,
    HORIZON,
    donchian_breakout_sign,
    ma_cross_sign,
    sma_sign,
    tsmom_sign,
)

CANDLES_PER_YEAR = 365 * 3
CONV_Q = 0.40

BOUNDS = {
    "2022": (1640995200000, 1672531200000),
    "2023": (1672531200000, 1704067200000),
    "2024H1": (1704067200000, 1719792000000),
    "RECENT": (1719792000000, OOS_CUTOFF_MS),
    "FULL_IS": (0, OOS_CUTOFF_MS),
}


def book_stats(direction, conv, fwd, ot, lo, hi, q=CONV_Q):
    m = (ot >= lo) & (ot < hi)
    valid = m & np.isfinite(conv) & np.isfinite(fwd) & np.isfinite(direction)
    if valid.sum() < 20:
        return None
    thr = np.nanquantile(conv[valid], q)
    gate = valid & (conv >= thr)
    if gate.sum() < 5:
        return None
    net = direction[gate] * fwd[gate] - COST
    cs = concentration_stats(net)
    ap = np.abs(net)
    hhi = float(np.sum((ap / ap.sum()) ** 2)) if ap.sum() > 0 else np.nan
    return {
        "n": int(gate.sum()),
        "win_rate": round(cs["win_rate"], 4),
        "sharpe": round(annualized_sharpe_from_trade_pnls(net, CANDLES_PER_YEAR / HORIZON), 4),
        "net": round(cs["net_sum"], 4),
        "top2_share": round(cs["top2_share_of_net"], 4)
        if np.isfinite(cs["top2_share_of_net"]) else np.nan,
        "hhi": round(hhi, 5),
    }


def main() -> None:
    full = load_full_for_label_horizon()
    full = add_forward_return(full, HORIZON)
    df = drop_horizon_crossing_oos(full, HORIZON)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "LEAK GUARD FAILED"

    anchor = sma_sign(df, 200)
    # multi-speed agreement panel (deterministic, past-only): does each trend signal point
    # the SAME way as the anchor? agreement_score = fraction of the panel agreeing w/ anchor.
    panel = [
        ma_cross_sign(df, 50, 200),
        donchian_breakout_sign(df, 55),
        tsmom_sign(df, 21),
        tsmom_sign(df, 42),
        tsmom_sign(df, 84),
    ]
    panel_arr = np.vstack(panel)                       # (5, N)
    agree_with_anchor = np.mean(panel_arr == anchor, axis=0)   # in [0,1], 1=unanimous agree

    conv = trend_strength_atr_norm(df, 200, 14).to_numpy()
    fwd = df["fwd_ret_h"].to_numpy()
    ot = df["open_time"].to_numpy()

    # AGREE_GATE: require >=4/5 of the panel to agree with the anchor (stand aside in chop)
    agree_mask = agree_with_anchor >= 0.8
    conv_agree_gate = np.where(agree_mask, conv, -np.inf)

    # AGREE_SCALE: multiply conviction by agreement (smooth version — low-agreement rows
    # get pushed below the q=0.40 gate). agreement in [0,1]; conv>=0.
    conv_agree_scale = conv * agree_with_anchor

    # ensemble direction (signed majority of the panel) for the contrast row
    ens_dir = np.where(np.sum(panel_arr, axis=0) > 0, 1.0, -1.0)

    configs = {
        "ANCHOR": (anchor, conv),
        "AGREE_GATE_4of5": (anchor, conv_agree_gate),
        "AGREE_SCALE": (anchor, conv_agree_scale),
        "ENSEMBLE_DIR": (ens_dir, conv),
        "ENSEMBLE_DIR_AGREE": (ens_dir, conv_agree_gate),
    }

    rows = []
    for period, (lo, hi) in BOUNDS.items():
        for name, (d, c) in configs.items():
            r = book_stats(d, c, fwd, ot, lo, hi)
            if r:
                rows.append({"period": period, "config": name, **r})
    out = pd.DataFrame(rows)
    out.to_csv(Path(__file__).resolve().parent / "blend_agreement.csv", index=False)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    # pivot Sharpe for a quick regime read
    piv = out.pivot(index="config", columns="period", values="sharpe")
    cols = [c for c in ["2022", "2023", "2024H1", "RECENT", "FULL_IS"] if c in piv.columns]
    print("=== per-trade Sharpe by regime (rows=config) ===")
    print(piv[cols].to_string())
    print("\n=== full table ===")
    print(out.to_string(index=False))

    # agreement distribution (how often is the panel in chop disagreement?)
    print("\nagreement-with-anchor distribution (IS):")
    for thr in [1.0, 0.8, 0.6, 0.4]:
        print(f"  >= {thr:.1f} : {np.mean(agree_with_anchor >= thr):.1%} of rows")


if __name__ == "__main__":
    main()
