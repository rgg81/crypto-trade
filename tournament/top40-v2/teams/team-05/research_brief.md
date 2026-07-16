# Team 05 research brief — CRTR v1

Status: **draft, unregistered, and not authorized for evaluation**. No performance observation was
used to create this family. The organizer must register the family and each material trial before
running it.

## Family and falsifiable thesis

Family ID: `team05-causal-residual-trend-reversal-v1`  
Base candidate: `team05-crtr-base-v1`

CRTR is a causal, deterministic, two-sided cross-sectional portfolio. Its primary mechanism is
intermediate-horizon residual trend: slow-moving capital and heterogeneous reaction speeds should
make relative winners and losers persist over 20–60 days. A smaller three-day reversal term is
strongest when the broad cross-section is non-directional, where temporary liquidity pressure is
more plausible than persistent direction. It fades continuously as broad direction strengthens.
Lower realized-volatility signals receive a small reliability preference, not leverage.

The thesis is falsified if the preregistered base cannot pass every hard development gate, if fewer
than five of six folds are profitable under Team-05's stricter rule, if bull-long, bear-short, or
combined-chop roles fail, if doubled costs fail, or if fewer than six of eight preregistered
one-axis neighbors are profitable. A failure is not eligible to become a submission.

## Causal signal and preconstruction score

At a scheduled boundary, the strategy takes only symbols in the supplied point-in-time eligible
set. It reads only positive finite `close` values timestamped no later than the decision. It does
not use funding, auxiliary data, an exposed transaction open, positions, fills, equity, or risk
state. Histories that are stale, sparse, invalid, or lack a time-valid 60-day anchor are omitted;
there is no imputation. Fewer than 12 valid symbols requests flat.

For every valid symbol:

1. Compute 3-, 20-, and 60-day close-to-close log returns and 20-day realized 8h volatility.
2. Divide each return by its matching square-root-of-bars volatility scale.
3. Cross-sectionally average-rank each normalized return into `[-1, 1]`; ties receive the exact
   average rank and symbols break all ordering ties lexicographically.
4. Estimate broad direction as `0.40 * median(20d return) + 0.60 * median(60d return)`.
5. In non-directional conditions use weights 45% slow trend, 35% medium trend, and -20% short
   trend (reversal). At full directionality use 60% slow, 35% medium, and -5% short trend. The
   interpolation is linear in clipped absolute broad direction.
6. Discount a 20d/60d sign disagreement to 65% and high cross-sectional volatility rank by at
   most 15%. The result is the preconstruction score, clipped to `[-1, 1]`.

`preconstruction_scores()` and `scores_to_target_weights()` are separate pure functions in
`strategy.py`. Their complete contract is frozen in `SCORE-ADAPTER-CONTRACT.md`.

## Portfolio construction

The strategy rebalances at 00:00 UTC every third day from a fixed 2020-01-01 anchor; other
boundaries return `None`. It selects the top and bottom 25% of scores, at least four per side,
subject to a soft absolute-trend preference. A fallback to the original ranking preserves both
sleeves when the soft preference is sparse. If the score span is below 0.10, it requests flat.

Requested gross is 0.60. Broad direction smoothly tilts net exposure by at most ±0.08: long and
short gross are `(0.60 ± net_tilt) / 2`. Within a sleeve, 70% is equal-weighted and 30% follows
absolute score magnitude. Every symbol is capped at 0.04; unused budget caused by the cap is not
levered or reassigned across sleeves. The target is therefore below organizer limits by design.

## Expected regime and sleeve roles

- Bull: the long sleeve owns persistent relative winners; net tilt modestly favors longs. Long
  sleeve return must be positive. The short sleeve remains materially active but smaller.
- Bear: the short sleeve owns persistent relative losers; net tilt modestly favors shorts. Short
  sleeve return must be positive. The long sleeve remains active in relatively resilient names.
- Chop: broad-direction scaling raises the three-day reversal contribution while the two roughly
  balanced sleeves express relative rather than market direction. Combined return must be
  positive.
- Stress: the signal may retain dispersion edge, but the portfolio-level volatility target,
  drawdown brakes, symbol stop, and turnover limit are expected to reduce exposure and forced
  trading. Stress need not be positive, but must clear the official worst-regime floor.

## Six chronological folds

The six test windows are contiguous, disjoint, and cover the complete visible development window.
Each fold is independently replayed from canonical history through its training cutoff, then emits
only that fold's test targets. The rule has no fitted coefficients, global scaler, feature
selection, or learned ensemble weight; a fold artifact therefore binds the frozen rule and the
past-only state established by that replay. Purge and embargo are not applicable because CRTR has
no forward labels, but a decision-close-to-next-open execution separation is mandatory. Exact
dates and artifact requirements are in `walk_forward_plan.json`.

## Hard noncompensatory development gates

No aggregate score, rank, or attractive regime can rescue a failed item. A candidate is viable
only if it passes every official development gate:

- net Sharpe ≥ 0.75; annualized return ≥ 0; Calmar ≥ 0.40; maximum drawdown ≤ 0.30;
- doubled-cost Sharpe ≥ 0.35; at least four positive folds; positive-quarter fraction ≥ 0.55;
- trial-adjusted probability of positive performance ≥ 0.90;
- bull, bear, and chop each have positive net return; at least three regime Sharpes are positive;
  worst-regime Sharpe ≥ -0.25;
- long-bull, short-bear, and combined-chop return are each positive;
- both sleeves clear every official exposure, active-bar, and executed-notional floor;
- profitable-neighbor fraction ≥ 0.70, neighbor median Sharpe ≥ 0.50, and positive-PnL
  concentration ≤ 0.40.

Team 05 additionally requires maximum drawdown ≤ 0.25, five of six profitable folds, positive PnL
concentration ≤ 0.35, at least six of eight profitable preregistered neighbors, neighbor median
Sharpe ≥ 0.55, and no future-invariance or reproducibility failure. These stricter gates are fixed
before evidence and cannot be waived.

Selection is binary and noncompensatory: freeze `team05-crtr-base-v1` only if it and its complete
predeclared neighborhood pass every gate. Neighbors are stability probes, never replacement
champions. Otherwise this family has no candidate; no metric ordering can promote a neighbor or a
least-bad cell.

## Fixed risk-control plan

The canonical combined policy is frozen in `risk_policy.json`:

- 30-day realized-volatility target of 18%, scale clamped to `[0.35, 1.00]`;
- drawdown scales 0.75/0.50/0.25/0.00 at 10%/16%/22%/28% drawdown;
- close-confirmed 12% position-loss stop with six 8h bars of cooldown;
- maximum one-way turnover 0.18 per boundary;
- no time stop, no side scaling, and no same-boundary reentry.

All actions remain evaluator-owned, next-open, costed, and capacity constrained. The complete
no-control, single-control, combined-control, base-cost, and doubled-cost grid is preregistered in
`ablations.json`; controls will not be selected opportunistically after seeing results.

## Research sequence and stopping rule

1. Organizer registers this family and the no-control base-cost signal trial.
2. Run the fixed risk/cost ablation grid, registering each cell before its result.
3. The combined-policy base earns a **provisional base pass** only after every non-neighborhood
   official and Team-05 gate above is known and passes.
4. Only after that provisional pass activate the eight already defined one-axis neighbors.
   Register every activated neighbor before reading it; do not replace a failed neighbor.
5. A final family pass exists only if the neighborhood gates also pass. Otherwise falsify this
   family or document a mechanism pivot; never submit the least-bad cell.

Planned maximum for this family is 20 material configurations (12 risk/cost cells and 8
neighbors), leaving budget for honest interruption or a separately registered pivot. No private
ticket is authorized by this draft.
