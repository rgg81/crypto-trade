# Team 05 final pivot-02 research brief — Liquidity Depth Migration

Status: prospective and unregistered. There is no LDM development, private, or OOS result.

## Diagnosis and genuinely new mechanism

The pivot-01 UDCC core was solvent but failed the noncompensatory center: net Sharpe was 0.5584,
only chop and stress had positive regime Sharpe, and bear was the worst regime at -0.4086. Controls,
neighbors, sign flips, and same-family replacements were forbidden. The failure therefore authorizes
Team 05's final mechanism pivot, not a repair of UDCC.

LDM measures temporal migration in effective depth. For each past timestamp it divides a contract's
unsigned `log(high / low)` range by its contemporaneous share of valid native-crypto quote volume.
It compares median impact over a 105-bar baseline with a disjoint 21-bar recent window:

`raw_depth_improvement = log(baseline_median_impact / recent_median_impact)`

The final score is the centered cross-sectional fractional rank of that value. Improving depth ranks
long; deteriorating depth ranks short. The signal contains no price direction, close location,
taker-side imbalance, funding, beta, residual return, shock, trend, reversal, volatility rank,
diffusion, or lead-lag input.

This separates LDM from the closest registered families. Team 02 auction absorption uses signed
taker-buy imbalance plus closing location and path efficiency. Team 03 reverses high-volume residual
price shocks. Team 10 uses a volume-weighted price anchor, with range and volume only as quarantine
filters. None scores the temporal migration of unsigned range per contemporaneous volume share.

## Causal data contract

Every 168 hours from the Unix epoch, the strategy uses only A6-supplied eligible symbols and
past-closed `open_time`, `high`, `low`, and `quote_volume` rows. Each admitted symbol needs an exact
contiguous suffix of 126 timestamps on the selected modal grid. The latest close may be at most 12
hours stale.

Nonfinite or nonpositive high, low, or quote volume, `high <= low`, and log range above 0.70 are
unavailable. They are never imputed and zero volume is never converted into artificial depth
deterioration. At least 12 symbols must be valid at a timestamp; a scored symbol needs at least 95
valid baseline and 19 valid recent impacts. Quote-volume share, rather than absolute volume, makes
the score invariant to market-wide volume scaling at a timestamp.

## Portfolio and regime hypothesis

The complete finite rank-score dictionary crosses A5 exactly once before score-span checks,
selection, raw-separation checks, sizing, caps, or organizer risk. A5-returned scores choose the top
and bottom `k=min(8,max(5,ceil(0.20*N)))` symbols. Selected sleeves must retain at least 0.10 median
raw-depth-improvement separation. Each sleeve receives 0.18 gross, weights are equal, net is exactly
zero, and each symbol is capped at 0.04.

- Bull: improving-depth longs should absorb expanding participation more efficiently.
- Bear: deteriorating-depth shorts should be more vulnerable to liquidity withdrawal, while the
  long sleeve should be relatively resilient.
- Chop: the unsigned, direction-free statistic should continue distinguishing stable two-sided
  depth from persistent deterioration during rotations.
- Stress: depth deterioration should identify fragile shorts; breadth, exact balance, 0.36 gross,
  and the cap are intrinsic construction rather than optional controls.

## Frozen disposition

Exactly one no-control candidate, `team05-ldm-pivot02-core-v1`, is authorized. Every gate in
`qualification_thresholds.json` is noncompensatory. Failure makes Team 05 DNF: no control,
ablation, sign flip, neighbor, same-family replacement, or further pivot may run. Private and OOS
data remain forbidden until formal development qualification.

Amendments 0005, 0006, and 0007 are active. Amendment 0008 is consumed historical CRTR authority
and gives LDM no authority.
