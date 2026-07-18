# Team 02 research brief: low-MAX anti-lottery

## Mandate

Test whether coins with an extreme recent positive return become overpriced relative to quieter
coins. The intended trade is long low-MAX and short high-MAX, implemented as a cautious,
market-neutral anti-lottery portfolio.

Primary evidence: [Speculation and lottery-like demand in cryptocurrency markets](https://www.sciencedirect.com/science/article/pii/S1042443121000081)
finds a large low-MAX minus high-MAX return spread using the maximum daily return from the prior
week.

## Causal feature

At a fixed daily or weekly decision boundary, construct completed UTC daily returns from the
8-hour bars. For each coin:

- compute the largest positive daily return in the previous 7, 14, or 28 days;
- repeat after subtracting each day's eligible-crypto median return;
- rank the negative of MAX, with cross-sectional winsorization and no forward filling;
- require complete history and a minimum trailing quote-volume eligibility floor.

The reference book is equal-dollar long the lowest-MAX quantile and short the highest-MAX
quantile, net neutral, with next-open execution. MAX is one realized positive tail observation;
do not dilute the mandate into a generic reversal blend.

## Required research

- Baselines: recent total return reversal, realized volatility, the previous period's minimum
  return, and an equal-turnover random rank.
- Formation windows: 7, 14, and 28 days. Holding/rebalance windows: 1, 3, and 7 days.
- Sign tests: low-minus-high MAX and exact high-minus-low inversion.
- Neutralization: raw MAX, median-residual MAX, and beta-residual MAX.
- Mechanism checks: control separately for trailing volatility, ordinary momentum, quote volume,
  price gaps, and listing age. Report whether the factor survives within the liquid half of the
  eligible universe.
- Sleeve evidence: high-MAX short PnL must be independently positive rather than being concealed
  by a generic low-volatility long sleeve.

## Risk controls

High-MAX shorts can squeeze. Use broad sleeves, tight per-symbol caps, capped total short gross,
close-confirmed position stops, cooldown after a stop, and a time stop no longer than the
formation window. Test a causal residual-momentum veto as a risk-only ablation, but do not tune it
until it removes all losing observations. Volatility targeting may scale down but never lever up.

## Falsifiers

Pivot if the long-short factor is nonpositive after base and doubled costs or MAX adds nothing
beyond total volatility or one-week reversal. Weakness in the liquid cohort, meme-episode
concentration, unstable nearby windows, a weak short sleeve, and regime weakness trigger repair
and lower robustness but are not standalone vetoes. A squeeze filter that alone creates all
profitability falsifies the claimed MAX mechanism.

## Opening-probe coaching record

Trial 1 (`t02-residual-low-max-7d-v1`) falsified the opening anti-lottery sign. Its train
Sharpe was -0.635, annualized return was -11.60%, doubled-cost Sharpe was -1.002, and only 20%
of quarters were positive. Bear Sharpe was -1.666 and the run generated 18,346 trades.

The mandatory artifact-level sign audit reconciled the evaluator return to within
`2.58e-16`. Before costs, the exact inversion improved Sharpe from -0.376 to +0.380 and had
60% positive quarters. The same realized costs reduced inverted Sharpe to +0.120; doubling
those costs reduced it to -0.140. This is evidence for a weak high-MAX continuation effect and
strong evidence that daily whole-book replacement is uneconomic. Merely negating Trial 1 is
therefore prohibited as the next candidate.

The preregistered Trial 2 pivot will admit the failed original thesis: it will test high-MAX
attention persistence using seven overlapping, equally weighted daily vintages. Each vintage
expires after seven days, so stable-universe one-way replacement is structurally limited to
one seventh of the book. A parameter-free 7/28-day common-crypto tape sign router will assign
the larger sleeve to longs in bull conditions, shorts in bear conditions, and equal sleeves
when the two horizons disagree. Rankings remain exclusively the single largest seven-day
median-residual return. This is one fixed revision, not a horizon or threshold search.

## Collision guard

Do not use the full distribution of positive squared residuals or realized skew as the main
score; that is Team 03. Do not add downside-risk compensation from Team 04, generic residual
reversal from Team 07, or clock effects from Team 10. Team 02 owns the single largest recent
positive daily observation.
