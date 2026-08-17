# Fresh lane centres

The twelve `strategy.py` files in this directory were written for CUP-50 from the lane mandates;
they do not port or import an earlier tournament candidate. They are initial centre sources, not
performance claims, nominations, or observed results. A centre becomes official only through the
trial journal, source archive, deterministic neighbourhood freeze, authenticated field close, and
one-shot observation lifecycle.

Every source exposes `build_strategy()` and the `TargetStrategyV2` interface. The files deliberately
contain no fitted object or cached data. Stateful learning, where introduced during research, must
be reconstructed from the streamed past-only context.
