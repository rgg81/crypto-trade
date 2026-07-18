# Top40 V3 Amendment 0003: stitched public assessment

Status: prospective until the unique integration-freeze commit is verified.

Amendment 0002 released the four fixed validation packets but intentionally left the
train-plus-validation public assessment pending. This amendment fills only that reserved gap. It
does not change a candidate, split, seed, universe, evaluator, execution assumption, cost, floor,
probe budget, or nomination rule.

Before any organizer-owned private return row is read, activation binds the successful four-team
validation journal, its unique simultaneous-release record, every released packet hash, the
Amendment 0002 activation and durability authorities, and this amendment's committed source and
tests. The unique freeze commit must directly follow the implementation commit and may add only
the integration-freeze file.

The assessment verifies every terminal artifact hash and uses only each successful validation
run's primary artifacts. Those artifacts contain the deterministic replay from the training start
through the validation end. Their training slice must equal the immutable IS daily-return
artifacts, while independently recomputed IS and validation metrics must reproduce the already
released packets. The frozen BTC regime classifier is recomputed from the verified market
snapshot. A mismatch fails closed.

The exact daily train and validation series are then concatenated without weighting, rescaling,
or selection. The existing V3 metrics and qualification factories compute the public-core checks
and robustness score. Readiness still requires net Sharpe, annualized return, and doubled-cost
Sharpe to be strictly positive in each of IS and validation separately. Only a readiness-eligible
candidate that also passes every stitched public-core floor is nomination-ready.

The published report contains only aggregate IS, validation, and stitched statistics, fixed gate
vectors, immutable identity hashes, nomination ranking, and the automatic comeback decision. It
contains no raw observations, daily returns, positions, targets, events, trades, or private paths.
