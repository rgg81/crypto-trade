# Iteration 043 — EARLY STOP (1372s)
Year 2021: PnL=-1124%, WR=28.1%, 2717 trades. 50 symbols worse than 2 symbols.

## FUNDAMENTAL FINDING
After testing 4%/2%, 5%/2.5%, 8%/4% barriers on 2 and 50 symbols — ALL fail year 1 (2021).

The model starts predicting in Jan 2021 with only 12 months of 2020 data. In 2020, BTC went from $7K→$29K (pure bull). The model learned bull patterns and cannot generalize to 2021's volatile consolidation, May crash, and recovery.

## Year 1 cannot be profitable with 12 months of 8h training data. This is a data limitation, not a model limitation.

## The question for the user: is year-1 profitability a realistic requirement? Or should we accept that the first 12-24 months of any walk-forward are a "learning period" where the model adapts?

## If year-1 profitability IS required, we need fundamentally different data:
1. Use daily (1d) candles instead of 8h — 3x more data per training period
2. Use 4h candles — 2x more data
3. Use multi-timeframe: 8h for prediction but incorporate daily indicators from a longer history
4. Use a much simpler model (e.g., 3 features, shallow depth) that generalizes from fewer examples
