"""iter-v1/030 (ETHUSDT) — IS-ONLY: (1) signal-family ORTHOGONALITY (Carver's <95%
correlation inclusion test) and (2) SUB-PERIOD stability of the winning family ensemble.

Why: multispeed_breadth.py showed SMA-only multi-speed (A/A') is INERT vs the SMA200
anchor (the windows are too correlated — Carver rejects >95%-correlated variations). The
de-concentration came from the signal-FAMILY ensemble (C): MA-cross + Donchian + TSMOM.
Here we (a) confirm those families are genuinely de-correlated (so the ensemble is real
diversification, not 3 copies of the same signal), and (b) test that C's lift holds in the
RECENT IS sub-period (the closest analogue to OOS) — the OOS-fingerprint test iter-028 used.

HARD RULE: open_time < OOS_CUTOFF_MS on every entry; drop horizon-crossing entries.
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
    CONV_Q,
    COST,
    HORIZON,
    SMA_WINDOWS,
    TSMOM_HORIZONS,
    donchian_breakout_sign,
    ma_cross_sign,
    majority,
    sma_sign,
    tsmom_sign,
)

CANDLES_PER_YEAR = 365 * 3


def main() -> None:
    full = load_full_for_label_horizon()
    full = add_forward_return(full, HORIZON)
    df = drop_horizon_crossing_oos(full, HORIZON)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "LEAK GUARD FAILED"

    # ---- the component direction signals ----
    comps = {
        "sma200": sma_sign(df, 200),
        "macross_50_200": ma_cross_sign(df, 50, 200),
        "donchian_55": donchian_breakout_sign(df, 55),
        "tsmom_42": tsmom_sign(df, 42),
        "tsmom_21": tsmom_sign(df, 21),
        "tsmom_84": tsmom_sign(df, 84),
    }
    comp_df = pd.DataFrame(comps)

    # ---- (1) ORTHOGONALITY: pairwise agreement-correlation of {+1,-1} signals ----
    # Carver's rule: don't combine variations whose correlation > 0.95. We report the
    # pairwise correlation of the sign series; lower = more diversifying.
    corr = comp_df.corr()
    corr.to_csv(Path(__file__).resolve().parent / "signal_family_correlation.csv")
    print("=== Signal-family correlation (Carver <0.95 inclusion test) ===")
    print(corr.round(3).to_string())

    # The chosen family ensemble C = MA-cross(50/200) + Donchian(55) + TSMOM(42)
    fam = [comps["macross_50_200"], comps["donchian_55"], comps["tsmom_42"]]
    c_dir = majority(fam)
    anchor_dir = comps["sma200"]
    # also the broader B (tsmom 21/42/84)
    b_dir = majority([comps["tsmom_21"], comps["tsmom_42"], comps["tsmom_84"]])

    # ---- (2) SUB-PERIOD stability ----
    conv = trend_strength_atr_norm(df, 200, 14).to_numpy()
    fwd = df["fwd_ret_h"].to_numpy()
    ot = df["open_time"].to_numpy()

    # IS sub-period boundaries (ms). RECENT = the closest analogue to OOS.
    bounds = {
        "2022": (1640995200000, 1672531200000),
        "2023": (1672531200000, 1704067200000),
        "2024H1": (1704067200000, 1719792000000),
        "RECENT_2024H2_2025Q1": (1719792000000, OOS_CUTOFF_MS),
    }

    def book(direction, mask):
        valid = mask & np.isfinite(conv) & np.isfinite(fwd) & np.isfinite(direction)
        if valid.sum() < 20:
            return None
        thr = np.nanquantile(conv[valid], CONV_Q)
        gate = valid & (conv >= thr)
        net = direction[gate] * fwd[gate] - COST
        cs = concentration_stats(net)
        return {
            "n": int(gate.sum()),
            "win_rate": round(cs["win_rate"], 4),
            "per_trade_sharpe_ann": round(
                annualized_sharpe_from_trade_pnls(net, CANDLES_PER_YEAR / HORIZON), 4),
            "net_sum": round(cs["net_sum"], 4),
            "top2_share_of_net": round(cs["top2_share_of_net"], 4)
            if np.isfinite(cs["top2_share_of_net"]) else np.nan,
        }

    rows = []
    for label, (lo, hi) in bounds.items():
        m = (ot >= lo) & (ot < hi)
        for nm, d in [("ANCHOR_sma200", anchor_dir), ("C_family", c_dir), ("B_tsmom", b_dir)]:
            r = book(d, m)
            if r:
                rows.append({"period": label, "book": nm, **r})
    sub = pd.DataFrame(rows)
    sub.to_csv(Path(__file__).resolve().parent / "subperiod_family.csv", index=False)
    print("\n=== Sub-period stability (ANCHOR vs C-family vs B-tsmom) ===")
    print(sub.to_string(index=False))

    # ---- direction-change rate: how OFTEN does C disagree with the anchor? ----
    # (a sanity check that C is a genuinely different direction primitive, not a relabel)
    valid = np.isfinite(c_dir) & np.isfinite(anchor_dir)
    disagree = float(np.mean(c_dir[valid] != anchor_dir[valid]))
    print(f"\nC-family disagrees with SMA200 anchor on {disagree:.1%} of rows "
          f"(0% would mean C is just the anchor relabeled).")


if __name__ == "__main__":
    main()
