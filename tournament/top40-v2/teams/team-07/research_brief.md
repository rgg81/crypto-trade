# Team 07 pivot 01: market-state and relative-opportunity ensemble

Status: implemented and serially validated as a prospective no-control mechanism pivot;
unregistered and unevaluated.

## Why the original family is terminal

The exact no-control `team07-shock-diffusion-center-v1` result falsified shock diffusion as a
tradable core. Net Sharpe was -0.9886, annualized return was -27.12%, doubled-cost Sharpe was
-2.0220, and maximum drawdown was 70.49%. Bull, bear, and chop Sharpe were all negative (-1.0801,
-2.9340, and -1.7135); stress Sharpe was +1.0084. Because the broad core-alpha gate failed,
controls, parameter neighbors, and lead-lag ablations are not activated and cannot repair it.

## New mechanism

The pivot does not estimate delayed reaction to liquid leaders. Every 48 hours it builds a robust
common crypto return from the cross-sectional median of each completed 8-hour return. Fast
21-bar and slow 126-bar normalized trends plus 21-bar sign breadth form a bounded common market
state. That common forecast is intended to supply positive long net exposure in persistent bull
conditions and negative net exposure in persistent bear conditions while both sleeves remain
active.

For relative selection, every coin is residualized against the same-bar median return. The
strategy combines 21- and 63-bar residual trend with three-bar residual reversal. The trend share
rises only when fast and slow common trends agree; when they do not, the blend shifts toward
short-horizon reversal. A small negative trailing-funding rank favors receiving rather than paying
crowded carry. The relative blend is rank-transformed for robustness.

The final captured score is the centered relative rank plus a common market-state offset. Its
cross-sectional order selects the long and short sleeves, and its mean determines their net tilt.
Consequently the exact dictionary returned from the A5 score boundary is the sole signal object
used in construction. Gross is fixed at 0.48, net is bounded at 0.20, each side has at least eight
names, and each name is capped at 0.04. These are construction limits, not retrospective risk
controls.

## Expected regime roles

- Bull: aligned fast/slow common trend and broad positive participation raise long gross; relative
  medium/slow strength ranks select leaders while the short sleeve remains active.
- Bear: aligned negative common trend raises short gross; relative weakness ranks select laggards
  for the short sleeve while the long sleeve remains active.
- Chop: fast/slow disagreement suppresses directional net and shifts relative scoring toward
  three-bar reversal and funding carry.
- Stress: the median market path, bounded trend transforms, broad sleeves, and coin caps reduce
  outlier dependence, but stress profitability and drawdown remain empirical gates.

## Causal and universe boundary

The strategy accepts exactly 190 completed close observations at exact 8-hour opens to form 189
returns. All transforms use those rows only. Funding events must be strictly earlier than the
decision timestamp. Future bars, bar high/low/open, auxiliary data, positions, fills, equity, PnL,
drawdown, evaluator actions, and private data are unused. Amendment 0006 supplies the only eligible
pure-crypto universe; Team 07 performs no symbol classification.

## Falsifier and tournament discipline

The new no-control reference is rejected if aggregate return or Sharpe is nonpositive at ordinary
or doubled costs; bull, bear, or chop return/Sharpe is nonpositive; long-bull, short-bear, or
combined-chop attribution is nonpositive; fewer than four folds or 55% of quarters are profitable;
either sleeve is inactive; A5 score coverage or IC gates fail; or positive PnL concentration
exceeds 40%. No negative candidate is eligible for controls or submission.

Only after the exact reference passes every broad gate may separately preregistered mechanism
ablations, neighbors, or risk-control trials be considered. A failed pivot reference triggers the
remaining documented mechanism pivot or DNF, never a stop-loss or drawdown overlay rescue.
