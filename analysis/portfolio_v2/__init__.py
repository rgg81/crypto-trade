"""portfolio_v2 — survivorship-safe, parametrized port of the v1 portfolio backtest engine.

Two HIGH leak fixes from `diary-portfolio-v2/AUDIT_portfolio_v1.md`, with a v1-compat mode that
reduces to the deployed v1 book (trend+carry walk-forward λ → inverse-vol → gross-norm → lag →
hysteresis band δ=0.010 SNAP → eligibility-exit K=2 → renorm → vol-target) bit-for-bit:

1. Universe survivorship — `universe_v2.load_pool_pit()` loads every ex-stable USDT perp (incl.
   delisted) with NO lifetime filter; per-bar seasoning admits a coin only once it has ≥`season`
   trailing candles as of t. v1-compat (`season=None`) reproduces the old `rank<=TOP_N` mask.
2. Missing slippage — `engine_v2.run_book` adds a liquidity-scaled per-side slippage term to the
   taker cost. `slip_bps_fn=None` reduces the cost to v1's `COST_SIDE·Σ|Δw|` bit-for-bit.

The same engine runs v1 (rank band (0, 20]) and v2 (rank band (20, 40]).
"""
