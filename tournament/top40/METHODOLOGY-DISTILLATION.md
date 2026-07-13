# Quant methodology distillation

This competition uses the methodological controls from the local `feature-engineering`,
`regime-detection`, and `walk-forward-validation` skill files. Their illustrative indicators,
strategy mappings, markets, thresholds, and trade examples are deliberately **not** an idea menu.
Teams must propose mechanisms independently and may not cite this distillation as economic support
for a signal.

## Feature and label discipline

- Give every raw field an event timestamp, an availability timestamp, an explicit lag, a source,
  a historical-coverage statement, and a missing-data rule.
- Prefer stationary transformations such as returns, differences, past-only ratios, and rolling or
  cross-sectional ranks. Treat levels and secularly trending quantities as suspect.
- Compute rolling transforms from observations available at the decision boundary. Never use a
  full-window mean, variance, rank, imputer, winsorizer, selector, or scaler.
- Fit every learned transform inside its training fold. Preserve a fixed feature order and record
  which transformations are fitted.
- Align a feature observed at `t` only with a forward label whose information interval starts
  after `t`. Record the label end time so overlapping observations can be purged.
- Remove or explicitly justify near-constant and highly redundant inputs using training data only.
  Feature selection is part of the model search and counts toward the trial budget.
- Prove truncation, corrupt-future, and append invariance. These are executable tests, not prose
  assurances.

## Regime discipline

- The common lagged BTC `bull`, `bear`, `chop`, and `stress` labels are fixed evaluation buckets.
  A team's internal state model cannot replace or redefine them for scoring.
- Any adaptive regime estimate is an ordinary strategy feature: it must be past-only, timestamped,
  fitted within each training fold, deterministic, and stable under future-data corruption.
- Analyze transitions and sparse states explicitly. Never select a model because a post-hoc regime
  partition makes its aggregate result look better.
- Report performance and exposure in every common regime and on both long and short sleeves. A
  hostile regime reduces confidence or score; it is not by itself an integrity disqualification.

## Time-series validation discipline

- Use chronological rolling or expanding walk-forward folds inside IS and explain why the chosen
  memory length matches the mechanism. Random cross-validation is forbidden.
- Purge every training observation whose label interval overlaps a validation interval. Add a
  documented embargo appropriate to the label horizon and residual serial dependence.
- If CPCV is used, form contiguous temporal groups and apply purging/embargo at every boundary.
  Never treat shuffled combinations as independent evidence.
- Keep preprocessing, feature selection, hyperparameter choice, ensemble weighting, and regime
  fitting inside the fold. Aggregate only predictions produced when their timestamp was genuinely
  out of fold.
- Log every material alternative, including manual variants, abandoned candidates, and feature
  subsets. DSR, PBO, bootstrap intervals, and related diagnostics inform the Critic but create no
  additional veto.
- The visible two-year public OOS may be viewed only through the organizer gate and at most three
  times. It is selection evidence, not an untouched holdout; prospective forward paper is the first
  sealed temporal evaluation.

## Engineering handoff

The QR must specify exact features, lags, labels, fold boundaries, purge and embargo rules,
training/refit cadence, normalization, missing-value behavior, portfolio mapping, parameters, and
seeds before QE implementation. The QE blocks on ambiguity and implements that specification
without introducing a new research choice.
