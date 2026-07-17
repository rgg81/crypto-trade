# Team09 pivot-01 research brief

Status: **prospective, unregistered, unevaluated pivot**

## Diagnosis

The parent no-control rule achieved net Sharpe `1.1061`, annual return `30.78%`, and doubled-cost
Sharpe `0.4744`, with strong bull/chop/stress Sharpes. It nevertheless had `53.33%` drawdown and
bear Sharpe `-2.1891`. In a broad crypto decline, low funding can describe distressed contracts
rather than future rebound; the parent consequently risked buying falling knives and shorting
comparatively resilient contracts. This is a selection-mechanism failure, not permission to add a
drawdown brake. Parent controls are forbidden.

## Pivot mechanism

At 00:00 UTC, use only contiguous closed 8h bars and strictly past funding. Compute a causal
seven-day cross-sectional median return and negative breadth:

- normal route: retain confirmed opposite-funding-crowd selection;
- broad-decline route (median return at most `-4%`, negative breadth at least `65%`): rank `45%`
  relative trend, `35%` inverse downside beta, and `20%` inverse trailing drawdown, then rerank;
- require at least four longs and four shorts; keep `0.45` gross per side and `0.09` symbol cap.

The input universe is exclusively Amendment-0006-certified native crypto. Stablecoins and direct
TradFi, metal, commodity, equity, ETF, index, FX, premarket, or leveraged-token exposures are
ineligible even when Binance lists them as perpetual contracts.

The bear route changes which assets are long and short. It does not inspect portfolio drawdown,
reduce gross, call a risk policy, flip every funding sign, or use organizer regime labels. The
same 24h A5 schedule and open-to-open label remain economically aligned with daily decisions.

## Falsifier

The pivot fails if its no-control core has nonpositive bear return or Sharpe, drawdown above
`0.30`, nonpositive bull or chop return, inactive sleeves, failed costs/folds/quarters/stability,
or failed A5 diagnostics. Aggregate Sharpe cannot compensate. Optional controls remain dormant
unless the core passes every activation gate and cannot rescue failure.

## Prospective accounting

Pivot-01 consumes the first permitted mechanism pivot. Its center, six mechanism ablations, ten
predeclared neighbors, and any later policy are separate material configurations. The neighbor
set is fixed before results and follows a strict serial read barrier. No private or OOS view is a
research round.
