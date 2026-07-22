# Team 03 short-horizon state-gated volume trend

This candidate follows the preregistered IS diagnosis. It forms each coin's trend over 21 days, then uses the most recent 14 days of directional quote-volume share as confirmation. The former recent-versus-prior volume-level multiplier is removed because the top-40 universe already imposes a causal liquidity screen and the multiplier was not the supported edge.

A completed 60-day BTC return defines the side role with a ten-percent dead band. Bull states hold at most 25% long gross, bear states hold at most 25% short gross, and chop holds at most 12.5% per side. A missing signal sleeve stays cash; risk is never transferred to the unsupported side.

All state and signal inputs use completed eight-hour bars. The existing central volatility target, drawdown brakes, stops, cooldowns, and turnover throttle remain unchanged.
