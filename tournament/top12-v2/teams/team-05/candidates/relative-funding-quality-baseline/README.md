# relative-funding-quality-baseline

Tag: `baseline`

This candidate seeks only relative settled-funding carry. At each Monday 00:00 UTC decision it
uses funding settlements strictly before the boundary. For every settlement cross section, it
subtracts the eligible-symbol median rate. Slow and fast exponentially weighted relative rates
must agree in sign, and at least 60% of the slow weighted history must retain that sign.

The long pool contains the lowest persistent relative funding rates and the short pool contains
the highest. This orientation receives the forecast funding spread: longs pay less or receive
more than the cross section, while shorts receive more or pay less. The book activates only when
recent cross-sectional funding dispersion is at least 0.75 times its formation median, and gross
exposure rises from 0.50 to 1.00 as dispersion widens.

Price cannot supply alpha direction. Completed price bars only veto names with extreme absolute
moves or betas and veto long/short combinations whose average market betas differ by more than
0.35. Among price-feasible combinations, the chosen book is the one with the largest forecast
settled-funding spread. Three names per side are equal weighted, the target is dollar neutral,
rebalancing is weekly, and the risk policy limits one-way turnover to 0.20.

Economic hypothesis: wide funding dispersion reflects uneven demand for leveraged directional
exposure. If that pressure persists, providing the expensive side of relative perp demand should
earn a carry premium, provided the resulting book is not simply a directional price bet.

Falsifier: reject the mechanism if persistent relative settled-funding dispersion does not
produce stable positive net performance across development folds and elevated-cost checks, or if
the exact carry-sign inversion is comparably or more robust. Failure after the price-neutrality
veto would also indicate that observed behavior is not a clean relative carry effect.
