"""Pre-registered diagnostics for the trend-quality gate.

Predictions declared before the numbers were read:

P1  Continuation (sign(momentum) x forward return) rises monotonically with the efficiency ratio
    measured over the same formation window.
P2  The low-efficiency extreme-momentum bucket does NOT continue -- if the cascade/one-off-
    repricing story is right it should be flat or reverse.
P3  At fixed momentum, a high single-bar jump share predicts weaker continuation.

If P1 is flat, the lane's premise is false on this universe and the gate cannot be load-bearing.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

from panel import (  # noqa: E402
    forward_log_return,
    load_close_panel,
    load_membership_mask,
    rolling_stats,
    stacked,
)

FORMATIONS = (21, 45, 90, 135)
HORIZONS = (3, 9, 21, 45)


def bucket_table(frame: pd.DataFrame, key: str, horizon_col: str, quantiles: int = 5) -> pd.DataFrame:
    labels = pd.qcut(frame[key], quantiles, labels=False, duplicates="drop")
    grouped = frame.assign(bucket=labels).groupby("bucket", observed=True)
    out = grouped.apply(
        lambda g: pd.Series(
            {
                "n": len(g),
                f"{key}_mid": g[key].median(),
                "cont_bps": 1e4 * (np.sign(g["momentum"]) * g[horizon_col]).mean(),
                "hit": (np.sign(g["momentum"]) * g[horizon_col] > 0).mean(),
            }
        ),
        include_groups=False,
    )
    return out


def main() -> None:
    close, _ = load_close_panel()
    mask = load_membership_mask(close.index, close.columns)
    print(f"grid {close.index.min()} .. {close.index.max()}  bars={len(close)}")
    print(f"members per boundary: median {mask.sum(axis=1).median():.0f}")

    for formation in FORMATIONS:
        stats = rolling_stats(close, formation)
        frames = {
            "momentum": stats["momentum"],
            "efficiency": stats["efficiency"],
            "persistence": stats["persistence"],
            "jump_share": stats["jump_share"],
            "volatility": stats["volatility"],
        }
        for horizon in HORIZONS:
            frames[f"fwd{horizon}"] = forward_log_return(close, horizon)
        panel = stacked(frames, mask)
        panel = panel[panel["momentum"].abs() > 0]
        print(f"\n===== formation={formation} bars ({formation * 8 / 24:.0f}d)  n={len(panel)}")
        for horizon in HORIZONS:
            col = f"fwd{horizon}"
            base = 1e4 * (np.sign(panel["momentum"]) * panel[col]).mean()
            corr = np.corrcoef(
                np.sign(panel["momentum"]) * panel["efficiency"], panel[col] * np.sign(panel["momentum"])
            )[0, 1]
            print(
                f"  h={horizon:>3} ({horizon * 8 / 24:.0f}d)  ungated continuation "
                f"{base:8.2f} bps   corr(ER, cont) {corr:+.4f}"
            )
            table = bucket_table(panel, "efficiency", col)
            print("      ER quintile:", " ".join(f"{v:8.1f}" for v in table["cont_bps"]))
            print("      ER mid     :", " ".join(f"{v:8.3f}" for v in table["efficiency_mid"]))
            print("      hit rate   :", " ".join(f"{v:8.3f}" for v in table["hit"]))

        # P2 / P3: 2-D conditioning on |momentum| quintile x efficiency quintile, horizon 21.
        col = "fwd21"
        panel = panel.assign(
            abs_mom_q=pd.qcut(panel["momentum"].abs(), 5, labels=False, duplicates="drop"),
            er_q=pd.qcut(panel["efficiency"], 5, labels=False, duplicates="drop"),
            jump_q=pd.qcut(panel["jump_share"], 5, labels=False, duplicates="drop"),
        )
        panel["cont"] = 1e4 * np.sign(panel["momentum"]) * panel[col]
        pivot = panel.pivot_table(index="abs_mom_q", columns="er_q", values="cont", aggfunc="mean")
        print("  continuation bps @ h=21 by |mom| quintile (rows) x ER quintile (cols)")
        print(pivot.round(1).to_string())
        jump = panel.groupby("jump_q", observed=True)["cont"].mean()
        print("  continuation bps @ h=21 by jump-share quintile:", jump.round(1).to_list())
        pers = panel.groupby(
            pd.qcut(panel["persistence"], 5, labels=False, duplicates="drop"), observed=True
        )["cont"].mean()
        print("  continuation bps @ h=21 by persistence quintile:", pers.round(1).to_list())


if __name__ == "__main__":
    main()
