# Team 01 fast market-state trend: center

The accepted baseline and its controls-off replay show strong per-coin trend direction, but longs
fight 2022 while shorts fight 2020, 2021, and 2023. The slow cross-coin breadth repair reacted too
late. This candidate therefore restores the original 63/126-day score construction, including its
one-quarter disagreement weight, and changes only portfolio risk allocation.

At each weekly boundary it measures BTC's return over 28 completed days. Above +5%, 72% of target
gross is reserved for positive per-coin trends and 28% for negatives. Below -5%, the budgets
reverse. Inside the band the book is balanced. Missing sleeves are capped so absolute net remains
below 0.25. The overlay is causal, pure-crypto, and faster than the traded signals; it does not
change any coin's own trend sign.

The 0.55 target cap uses the baseline's low 0.157 realized gross and preserves the full risk stack
that held drawdown below 20%. Before evaluation, the five-point `(market_days, market_threshold)`
neighborhood is frozen at `(21,.035)`, `(24,.0425)`, `(28,.05)`, `(35,.06)`, and `(42,.075)`.

The candidate makes no performance claim and cannot access the sealed historical-OOS interval.
