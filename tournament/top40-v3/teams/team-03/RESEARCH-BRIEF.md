# Team 03 research brief: positive-jump variance and residual skew

## Mandate

Build a cross-sectional anti-euphoria factor from the composition of realized variance. The
hypothesis is that repeated or distributed positive-jump exposure and strongly positive residual
skew predict lower subsequent returns, beyond total volatility.

Primary evidence: [Variance Decomposition and Cryptocurrency Return Prediction](https://www.scheller.gatech.edu/directory/research/finance/lee/pdf/crypto_variance_leewang_5feb2024.pdf)
attributes negative weekly return predictability to positive-jump and jump-robust variance.
[Higher moments, extreme returns, and the cross-section of cryptocurrency returns](https://www.sciencedirect.com/science/article/pii/S1544612320303135)
provides complementary evidence on realized volatility, skewness, and kurtosis.

## Causal feature

For each completed 8-hour bar, subtract the contemporaneous eligible-crypto median return. Over a
strictly trailing window compute:

- positive residual semivariance: the sum of squared positive residuals;
- positive-tail share: positive semivariance divided by total residual variance;
- robust realized skew using clipped residuals;
- breadth of positive tail events, so the score is not merely the single maximum observation.

The reference score is the negative robust rank of positive-tail share and skew. Long low
positive-tail-risk coins and short high positive-tail-risk coins in a broad, net-neutral book.
Describe these as coarse 8-hour jump proxies, not as a formal high-frequency jump test.

## Required research

- Baselines: total realized variance, downside semivariance, ordinary trailing return, and
  low-MAX using identical turnover.
- Formation horizons: 21, 63, and 126 bars. Holding/rebalance horizons: 3, 9, and 21 bars.
- Sign tests: anti-positive-jump sign and its exact inversion.
- Neutralization: raw returns, median residuals, and causal rolling-beta residuals.
- Component ablations: semivariance only, positive-tail share only, skew only, remove the largest
  observation, and equal-weight versus magnitude-weight tail breadth.
- Report rank IC, sleeve PnL, costs, concentration, fold/quarter breadth, and regime attribution.

## Risk controls

The short sleeve can be exposed to persistent speculative rallies. Use winsorization, broad
sleeves, small symbol caps, an ex ante liquidity floor, close-confirmed stops with cooldown, and
a capped-downward volatility target. Test slower rebalance and a turnover limit. Risk gates must
be fixed from past-only OHLCV and cannot recognize named meme coins.

## Falsifiers

Pivot if the score is nonpositive after base and doubled costs, positive-jump composition does
not beat total variance, or the exact sign inversion wins. Sensitivity to the largest return,
nearby windows, illiquid micro-cohorts, regimes, and sleeve roles triggers diagnosis and lowers
robustness rather than automatically killing a strong aggregate system. If low-MAX alone explains
the result, concede collision and pivot rather than renaming it.

## Collision guard

Team 03 must measure a distributional positive-tail characteristic. It may not rank the single
maximum return as Team 02 does, trade a compensated downside premium as Team 04 does, or route
one-bar momentum/reversal as Team 07 does.
