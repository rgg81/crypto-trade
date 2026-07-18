"""e02 — k x h grid at gamma=1, kline-only, 1x costs."""

import sys

sys.path.insert(
    0,
    "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/tournament/crypto/teams/team-09/out/scratch",
)
import sig

pn, aux, scoring = sig.te.load_is_panels()

for k in (1, 2, 3):
    for h in (3, 6, 9):
        raw = sig.build_signal(pn, aux, k=k, h=h, gamma=1.0)
        net, w, parts, m = sig.score(raw, pn, scoring)
        print(sig.brief_row(f"k={k} h={h}", m), flush=True)
