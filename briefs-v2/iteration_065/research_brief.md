# iter-v2/065 Research Brief — NEAR cap parameter sweep

**Type**: EXPLOITATION (parameter sweep, no model re-training)
**Parent baseline**: iter-v2/059-clean
**Prior**: iter-v2/064 (NEAR 0.7× cap: OOS monthly −14%, too aggressive)

## Section 0 — Data Split

`OOS_CUTOFF_DATE = 2025-03-24` — immutable.

## 1. Problem

iter-v2/064 proved that per-symbol position capping fixes NEAR
concentration but 0.7× was too aggressive (OOS monthly -14%). Need to
find the cap that satisfies both concentration rules AND preserves most
of the baseline Sharpe.

## 2. Method

Parameter sweep over cap values [1.00, 0.90, 0.85, 0.80, 0.75, 0.70].
Reuse iter-v2/059-clean's trade list, apply each cap, compute
concentration + Sharpe. Since models are identical across caps (only
post-processing differs), this is essentially free compute.

## Section 6 — Risk Management Design

Unchanged from iter-v2/064. Concentration cap is a sizing intervention,
not a gate.

## 3. Success criteria for the sweep

The optimal cap is the LARGEST cap value (smallest intervention) that
passes:

- NEAR concentration ≤ 40% (n=4 inner rule)
- Max share (any symbol) ≤ 40%

Subject to:
- OOS monthly Sharpe ≥ 0.85 × baseline (+1.41) per the skill's balance
  guard

## 4. Expected finding & validation plan

Math from iter-v2/064:
- 0.80: NEAR wpnl 28.43 → share 39.02% (just under 40%)
- 0.85: NEAR wpnl 30.21 → share 40.47% (just over 40%)

Prediction: 0.80 is the sweet spot. If confirmed, iter-v2/066 runs the
full baseline backtest with cap=0.80 + 10-seed validation for a proper
MERGE candidate.
