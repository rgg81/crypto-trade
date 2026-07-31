# Drawdown recovery confirmation baseline

This baseline trades recovery geometry, not drawdown extremity by itself. Each weekly decision uses
only completed 8h closes to locate the most recent peak inside an 84-day window, measure current
drawdown depth and time since that peak, and fit recovery slopes over trailing 12-day and 4-day
windows.

Long eligibility requires a material drawdown, a positive 12-day recovery slope, positive 4-day
confirmation, and a meaningful lift from the recent drawdown trough. Short eligibility requires a
material drawdown, negative slopes on both windows, and a current level still near the recent
trough. Thus recovery geometry determines direction; cross-sectional depth and duration ranks only
adjust conviction after the state gate. The highest-scoring two or three names on each side form a
dollar-neutral 1.0-gross book. If either state has fewer than two names, the strategy requests a
flat book rather than manufacturing a directional exposure.

The intended economic asymmetry is that an established rebound after a deep, persistent drawdown
can continue as forced selling abates, while an asset that resumes making drawdown progress after
failing to recover can continue to lag. Weekly rebalancing and the organizer-enforced 0.20 one-way
turnover limit make the baseline moderately low turnover.

The thesis is falsified if recovery-confirmed longs fail to outperform renewed-drawdown shorts
after costs across development folds, if depth-only controls explain the spread, or if sign
inversion is consistently superior. All features are past-only, seed-independent, and use no
calendar-date anchor.
