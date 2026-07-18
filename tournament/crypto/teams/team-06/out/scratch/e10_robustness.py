"""e10 — robustness of (ls_accounts, W=90, E=3, rank): min_periods, clip, extra lag."""

import sys

sys.path.insert(
    0,
    "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/tournament/crypto/teams/team-06/out/scratch",
)
import json

import lib06
import pandas as pd

T0 = pd.Timestamp("2023-01-13")
lib06.load()

runs = [
    ("base", dict()),
    ("mp=30", dict(min_periods=30)),
    ("mp=60", dict(min_periods=60)),
    ("clip=2", dict(clip=2.0)),
    ("clip=4", dict(clip=4.0)),
]
for name, kw in runs:
    raw = lib06.fade_signal("ls_accounts", 90, ema_span=3, mode="rank", **kw)
    m = lib06.score(raw, t0=T0)
    print(json.dumps({"run": name, "sharpe_1x": m["sharpe_1x"], "sharpe_hw": m["sharpe_hw"],
                      "sharpe_2x": m["sharpe_2x"]}))

raw = lib06.fade_signal("ls_accounts", 90, ema_span=3, mode="rank").shift(1)
m = lib06.score(raw, t0=T0)
print(json.dumps({"run": "extra_lag_1", "sharpe_1x": m["sharpe_1x"],
                  "sharpe_hw": m["sharpe_hw"], "sharpe_2x": m["sharpe_2x"]}))
