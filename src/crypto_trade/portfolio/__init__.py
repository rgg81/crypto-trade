"""Live portfolio strategy — the deployable baseline-v2 (trend+carry+hysteresis).

Parity-first: the live executor computes target weights by calling the EXACT validated backtest code
(analysis/portfolio/iter_002,004,005,020) via `strategy`, never a reimplementation.
"""
