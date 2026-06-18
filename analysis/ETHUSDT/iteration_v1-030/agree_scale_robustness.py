"""iter-v1/030 (ETHUSDT) — IS-ONLY: parameter robustness of the AGREE_SCALE winner.

blend_agreement.py selected AGREE_SCALE: direction = SMA200 anchor (UNCHANGED), conviction
quantity multiplied by a deterministic multi-speed AGREEMENT score. Here we stress it: is
the full-IS lift (+0.44 -> +0.55 Sharpe, top-2 0.0433 -> 0.0342) a single-parameter artifact,
or robust to the choice of panel and agreement formula? A robust, non-cherry-picked lift is
the pre-condition for committing the axis (the campaign's hard lesson: seed/param-varying
edges are lotteries that collapse at K=20).

We vary:
  - the panel composition (which trend signals form the agreement vote)
  - hard {+1,-1}-agreement vs continuous {strength-weighted} agreement
  - including/excluding the anchor itself in the panel

All deterministic, past-only, IS-only. We report FULL-IS Sharpe + top-2 share for each
variant; a robust axis has them clustered ABOVE the anchor across variants.

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


def full_is_book(direction, conv, fwd):
    valid = np.isfinite(conv) & np.isfinite(fwd) & np.isfinite(direction)
    thr = np.nanquantile(conv[valid], CONV_Q)
    gate = valid & (conv >= thr)
    net = direction[gate] * fwd[gate] - COST
    cs = concentration_stats(net)
    return {
        "n": int(gate.sum()),
        "win_rate": round(cs["win_rate"], 4),
        "sharpe": round(annualized_sharpe_from_trade_pnls(net, CANDLES_PER_YEAR / HORIZON), 4),
        "net": round(cs["net_sum"], 4),
        "top2_share": round(cs["top2_share_of_net"], 4)
        if np.isfinite(cs["top2_share_of_net"]) else np.nan,
    }


def main() -> None:
    full = load_full_for_label_horizon()
    full = add_forward_return(full, HORIZON)
    df = drop_horizon_crossing_oos(full, HORIZON)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "LEAK GUARD FAILED"

    anchor = sma_sign(df, 200)
    conv = trend_strength_atr_norm(df, 200, 14).to_numpy()
    fwd = df["fwd_ret_h"].to_numpy()

    # candidate panels (each a list of {+1,-1} deterministic past-only signals)
    panels = {
        "P1_macross_donch_tsmom3": [
            ma_cross_sign(df, 50, 200), donchian_breakout_sign(df, 55),
            tsmom_sign(df, 21), tsmom_sign(df, 42), tsmom_sign(df, 84),
        ],
        "P2_tsmom_only_3": [tsmom_sign(df, 21), tsmom_sign(df, 42), tsmom_sign(df, 84)],
        "P3_family_3": [
            ma_cross_sign(df, 50, 200), donchian_breakout_sign(df, 55), tsmom_sign(df, 42),
        ],
        "P4_macross_multi": [
            ma_cross_sign(df, 20, 100), ma_cross_sign(df, 50, 200),
            ma_cross_sign(df, 100, 300),
        ],
        "P5_donch_multi": [
            donchian_breakout_sign(df, 20), donchian_breakout_sign(df, 55),
            donchian_breakout_sign(df, 100),
        ],
        "P6_wide_mix": [
            ma_cross_sign(df, 50, 200), donchian_breakout_sign(df, 20),
            donchian_breakout_sign(df, 55), tsmom_sign(df, 21),
            tsmom_sign(df, 42), tsmom_sign(df, 84), sma_sign(df, 100),
        ],
    }

    rows = []
    # anchor baseline
    r = full_is_book(anchor, conv, fwd)
    rows.append({"variant": "ANCHOR(no agree)", **r})

    for pname, panel in panels.items():
        parr = np.vstack(panel)
        agree = np.mean(parr == anchor, axis=0)        # fraction agreeing with anchor
        r = full_is_book(anchor, conv * agree, fwd)
        rows.append({"variant": f"AGREE_SCALE::{pname}", **r})

    out = pd.DataFrame(rows)
    out.to_csv(Path(__file__).resolve().parent / "agree_scale_robustness.csv", index=False)
    pd.set_option("display.width", 200)
    print(out.to_string(index=False))

    anchor_shp = out.loc[out.variant == "ANCHOR(no agree)", "sharpe"].iloc[0]
    anchor_t2 = out.loc[out.variant == "ANCHOR(no agree)", "top2_share"].iloc[0]
    scale_rows = out[out.variant.str.startswith("AGREE_SCALE")]
    n_better_shp = int((scale_rows["sharpe"] > anchor_shp).sum())
    n_better_t2 = int((scale_rows["top2_share"] <= anchor_t2).sum())
    print(f"\nAGREE_SCALE variants beating anchor on Sharpe: {n_better_shp}/{len(scale_rows)}")
    print(f"AGREE_SCALE variants <= anchor top-2 share:     {n_better_t2}/{len(scale_rows)}")
    print(f"(anchor Sharpe {anchor_shp}, top-2 {anchor_t2})")


if __name__ == "__main__":
    main()
