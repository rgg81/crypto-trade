"""Config-sweep runner: python run_configs.py '<json list of configs>'

Config keys: kind ("fade"|"spread"), panel, W, E, mode, clip. Prints one metrics line each.
T0 fixed at 2023-01-13 (e01 honest-window rule)."""

import json
import sys

sys.path.insert(
    0,
    "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/tournament/crypto/teams/team-06/out/scratch",
)
import lib06
import pandas as pd

T0 = pd.Timestamp("2023-01-13")

configs = json.loads(sys.argv[1])
lib06.load()
for cfg in configs:
    kind = cfg.get("kind", "fade")
    if kind == "fade":
        raw = lib06.fade_signal(
            cfg.get("panel", "ls_accounts"),
            cfg["W"],
            ema_span=cfg.get("E", 1),
            mode=cfg.get("mode", "demean"),
            clip=cfg.get("clip", 3.0),
            min_periods=cfg.get("min_periods"),
        )
    elif kind == "spread":
        raw = lib06.spread_signal(
            cfg["W"], ema_span=cfg.get("E", 1), mode=cfg.get("mode", "demean"),
            clip=cfg.get("clip", 3.0),
        )
    elif kind == "combo":  # equal-weight mean of component signals (no weight optimization)
        parts = []
        for sub in cfg["components"]:
            if sub.get("kind", "fade") == "fade":
                parts.append(lib06.fade_signal(sub.get("panel", "ls_accounts"), sub["W"],
                                               ema_span=sub.get("E", 1),
                                               mode=sub.get("mode", "demean")))
            else:
                parts.append(lib06.spread_signal(sub["W"], ema_span=sub.get("E", 1),
                                                 mode=sub.get("mode", "demean")))
        raw = sum(p.fillna(0.0) for p in parts) / len(parts)
        raw = raw.where(sum(p.notna() for p in parts) > 0)
    else:
        raise ValueError(kind)
    m = lib06.score(raw, t0=T0)
    print(json.dumps({"cfg": cfg, "m": m}))
