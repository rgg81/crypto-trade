# Top40-v3 pure-crypto universe policy

Top40-v3 trades native crypto coins only. A Binance perpetual listing is not, by itself,
evidence that the underlying belongs in this tournament.

An eligible instrument must pass every point-in-time check below:

1. It is a Binance USD-M linear `USDT` perpetual with `USDT` quote and margin assets.
2. Binance classifies the underlying as a coin, and neither the underlying type nor subtype
   identifies equity, ETF, forex, index, commodity, metal, stock, pre-market, or other TradFi
   exposure.
3. Its base asset is not a fiat or stablecoin, a leveraged token, tokenized gold or commodity,
   or another synthetic non-crypto exposure. Examples explicitly excluded include stablecoin
   bases, `PAXG`, `XAUT`, `XAU`, `XAG`, oil, gas, copper, equity, and index contracts.
4. The symbol is active and passes the frozen history and liquidity rules at that week's
   Monday 00:00 UTC reconstruction. Future listings and future metadata cannot affect an earlier
   membership decision.

The authoritative implementation is the fail-closed audit in
`src/crypto_trade/tournament/pure_crypto_universe_v6.py`, together with its exact snapshot and
policy hashes. Top40-v3 binds that audit directly; it does not inherit the Top40-v2 amendment
dispatcher or rebuild membership through an older eligibility helper.

The organizer runs the audit before and after each lab, validation, formal qualification,
private qualification, and final-OOS execution. Any membership or metadata byte that no longer
matches the frozen authority stops the run. A changed snapshot requires a newly reviewed V3
audit with the same native-crypto policy; it never falls back to a broader universe.

Universe noncompliance is an integrity failure, not a performance penalty and not something a
robustness score can compensate for.
