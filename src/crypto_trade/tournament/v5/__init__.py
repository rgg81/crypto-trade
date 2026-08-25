"""Top-40 V5 tournament authority.

V5 is a single edition. Unlike the V4 package, no module in here branches on an edition name:
the V4 modules carry 81 ``TOP40_V4_LAYOUT.name.endswith("-r2")`` tests purely because V4 had to
keep its R1 edition alive after R2 forked, and a third edition would have silently taken the R1
arm at every one of them. An edition flag is added here only when a second V5 edition exists.
"""

from crypto_trade.tournament.v5.layout import TOP40_V5_LAYOUT, TournamentLayoutV5

__all__ = ["TOP40_V5_LAYOUT", "TournamentLayoutV5"]
