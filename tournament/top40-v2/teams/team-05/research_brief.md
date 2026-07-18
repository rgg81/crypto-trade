# Team 05 pivot-01 research brief — Up/Down Capture Convexity

Status: prospective and unregistered. There is no UDCC development, private, or OOS result.

## Diagnosis and pivot

The parent CRTR family produced a positive no-control core but its fixed combined candidate failed
noncompensatory positive-quarter, fold, trial-adjusted-confidence, chop, worst-regime, and
concentration gates. Controls and parameter neighbors cannot rescue that result. UDCC changes the
forecast object, input statistic, cadence, and construction rather than tuning or reversing CRTR.

## Economic mechanism

Native-crypto contracts can differ structurally in their participation in the common crypto tape.
Deep, broadly held and collateral-useful coins may capture more of market advances while
transmitting less of declines; fragile leverage-sensitive coins may exhibit the opposite
asymmetry. UDCC seeks the spread between those convex and concave response profiles. It does not
forecast whether the next common-tape move will be positive or negative.

Every 168 hours from the Unix epoch, the strategy uses only A6-supplied eligible symbols and
past-closed `open_time`/`close` rows. Each valid symbol needs an exact contiguous suffix of 253
prices, giving 252 eight-hour log returns. At every timestamp the common return is the
cross-sectional median native-crypto return. Separate contemporaneous slopes are estimated on
positive and negative common-return observations. The final score is:

`0.50 * (centered_rank(beta_up) - centered_rank(beta_down))`

The statistic is invariant to a shared permutation of paired observations. It therefore contains
no trend, reversal, acceleration, diffusion, lead-lag, or holding-period return level. Funding,
volume, OHLC shape, auxiliary data, positions, and organizer regime labels are unused.

## Portfolio and roles

The complete finite score dictionary crosses A5 exactly once before score-span checks, selection,
capture-separation gates, sizing, caps, or organizer risk. The A5-returned scores choose the top and
bottom `k=min(8,max(5,ceil(0.20*N)))` symbols. Both median capture separations must be at least 0.10.
Each sleeve receives 0.24 gross, weights are equal, net is exactly zero, and each symbol is capped
at 0.05.

- Bull: higher-upside-capture longs should earn more of broad advances.
- Bear: higher-downside-capture fragile shorts should contribute while resilient longs lose less.
- Chop: alternating positive and negative tape moves should favor the same convex-minus-concave
  spread without a directional router.
- Stress: there is no crisis-alpha claim beyond observed downside-capture separation; breadth,
  exact balance, 0.48 gross, and the cap are intrinsic construction.

## Frozen disposition

Exactly one no-control candidate, `team05-udcc-pivot01-core-v1`, is authorized. Every gate in
`qualification_thresholds.json` is noncompensatory. Failure rejects the UDCC family: no control,
ablation, sign flip, neighbor, or same-family replacement may run. Team 05's second pivot remains
available only for a separately documented genuinely different future mechanism. Private and OOS
data remain forbidden until formal development qualification.

Amendments 0005, 0006, and 0007 are active. Amendment 0008 is historical and gives UDCC no
authority.
