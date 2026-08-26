# Phase S — scouting

You have the public internet and **no market data**. No repository, no prior tournament artifact,
no other team's work, and no evaluation surface. This phase exists so you can research the
professional literature on your assigned family rather than reinvent it from nothing.

Produce `scouting/THESIS.md` containing:

1. **A mechanism thesis.** What is the economic source of the return, and why should the premium
   persist specifically in Binance USD-M perpetual futures? Name who is on the other side.
2. **At least three public citations**, each with an access timestamp. Papers, practitioner
   research, exchange documentation. Say what each one establishes.
3. **A falsifier**, stated on visible development data, that you commit to before seeing a result.
4. **A declared parameter surface.** Every knob you intend to search, and its range.

That fourth item matters more than it looks. It makes your search space countable, which is what
the trial count in a deflated Sharpe is supposed to mean. This is the first edition where that
number will mean something.

This thesis is hash-bound and sealed before any market data is mounted. You cannot revise it after
seeing a result -- that is the point of preregistering it.

## What this dataset cannot support

Do not spend a trial discovering these. There is no open interest, no liquidation feed, no order
book, no spot price and therefore no true basis, no cross-venue data, no options, nothing on-chain,
and nothing below 8h resolution. Funding, OHLCV, quote volume, trade count and taker-buy volumes
are what exist.
