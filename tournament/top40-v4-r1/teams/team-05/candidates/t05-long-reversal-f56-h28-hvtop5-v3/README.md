# Team 05 volatile long-formation reversal pivot

This candidate replaces the failed three-bar liquidity-shock mechanism with a literature-led
long-formation reversal. At Monday 00:00 UTC it ranks the higher-volatility half of the eligible
universe outside the five liquidity leaders by its return over the preceding 56 completed days.
It buys the bottom quintile and shorts the top quintile.

Four weekly cohorts overlap, so each new cohort contributes one quarter of a 40% gross book. This
keeps annual turnover below the tournament ceiling while matching the calendar-time construction
used in the motivating research. Both sides are fixed ex ante and independently auditable; no
date-specific rule or observed future outcome changes their sign.

The only organizer-owned overlay is a symmetric 22% volatility target. All other stops and brakes
are disabled because the IS-only diagnostics found that sleeve breaks removed profitable episodes
instead of improving stability. Missing history fails closed, and all features use completed bars
from the point-in-time pure-crypto universe.
