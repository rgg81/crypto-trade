# Top-40 V2 methodology distillation

V2 retains V1's timestamp, feature-lineage, regime, execution, and engineering controls. It adds
qualification discipline so a team cannot confuse a fitted backtest with evidence of a viable
champion.

## Causal feature and label discipline

- Every raw field has an event timestamp, availability timestamp, lag, source, coverage statement,
  and missing-data rule.
- Rolling transforms use only observations available at the decision boundary. Full-window
  scalers, ranks, imputers, selectors, and winsorizers are forbidden.
- Learned preprocessing, feature selection, model fitting, ensemble weights, and adaptive regime
  estimates are fitted inside each chronological training fold.
- Forward labels begin strictly after their decision timestamp. Overlapping labels are purged and
  receive a documented embargo.
- Truncation, corrupt-future, append-invariance, and deterministic-rerun tests are executable.

## Development qualification

- Development evidence is a stitched series of predictions that were genuinely out of fold.
- At least six chronological folds are used. Random cross-validation is forbidden.
- Every material choice counts toward the cumulative trial budget, including manual alternatives
  and risk overlays.
- The selected parameter neighborhood is declared before final evaluation. An isolated peak cannot
  qualify.
- Fold and quarter PnL concentration, doubled-cost performance, long/short attribution, and common
  regime behavior are computed centrally from canonical artifacts.
- Passing the visible gate grants only a private-qualifier ticket. It does not guarantee finalist
  status.

## Regime and sleeve roles

The common one-day-lagged BTC labels remain bull, bear, chop, and stress. Bull, bear, and chop must
each have positive development net return; at least three regimes need positive Sharpe, and the
worst regime must meet the frozen floor.

The long sleeve is expected to contribute positively in bull, the short sleeve in bear, and the
combined portfolio in chop. V2 does not require every sleeve to be positive in every regime: that
would reward economically artificial tuning. Both sleeves must remain materially active and all
four regime-by-sleeve attribution cells are still published.

## Risk-control evidence

Every final risk policy is evaluated against no-control, individual-control, and combined-control
ablations at base and doubled costs. Reports include return, Sharpe, drawdown, tail loss, turnover,
regime effects, stop/brake counts, cooldown time, requested risk notional, filled risk notional,
and same-boundary reentry prevention.

Risk controls do not receive optimistic fills. A boundary-confirmed control acts at the next open.
Finer intrabar execution would require a separately frozen lower-frequency dataset and fill model.

## Interpretation

The private qualifier and final OOS are blind to fresh V2 teams, but the historical interval was
used by V1 and is not globally untouched. Prospective observations after winner freeze remain the
first untouched temporal evidence. Tournament rank and readiness for capital remain separate.
