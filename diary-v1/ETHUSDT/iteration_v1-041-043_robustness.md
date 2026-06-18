# Diary — iter-v1/041-043 (ETHUSDT) — DIRECTION-ROBUSTNESS validation of the MERGED crown jewel — PASS (robust; SMA-200 well-chosen)

**Axis:** stress-test the merged iter-034 ETH baseline (pure-deterministic trend, OOS +0.41) on the ONE
primitive it rests on — the 200-SMA trend-state direction on ETH's own close. Vary the trend speed
(SMA 100 / 300) and the regime source (BTC cross-asset), holding the rest of the iter-034 stack identical.
All K-invariant (model bypassed, deterministic). Protective validation (Critic next-step #2), not a new edge.

## Robustness picture
| variant | IS Sharpe | OOS Sharpe | both-positive? |
|---|---|---|---|
| **SMA200 / ETH (MERGED baseline)** | **+0.6481** | **+0.4148** | ✓ (IS PEAK, balanced) |
| SMA100 / ETH (iter-041) | +0.1956 | +0.7227 | ✓ (IS-weak) |
| SMA300 / ETH (iter-042) | −0.1067 | +0.1601 | ✗ (IS<0 — too slow) |
| SMA200 / BTC-regime (iter-043) | +0.2852 | +0.7653 | ✓ (IS-weak) |

## Verdict: PASS — the crown jewel is ROBUST + the merged SMA-200 is well-chosen.
1. **Not a knife-edge.** Both-positive in 3 of 4 neighborhood variants — robust to FASTER trend speed
   (SMA-100) AND to a cross-asset regime source (BTC). Only the slow extreme (SMA-300) breaks (IS<0).
   The both-positive region spans ~SMA 100-200 (the code comment's "flat plateau 100-300" is really ~100-200).
2. **SMA-200 is the IS PEAK + correctly chosen.** As the window goes 100→200→300, IS goes
   +0.20→+0.65→−0.11 (peaks at 200) while OOS goes +0.72→+0.41→+0.16 (monotone down). The merged SMA-200
   maximizes the consistent (IS) edge while keeping a strong OOS — the balanced sweet spot.
3. **The higher-OOS variants are NOT better baselines.** SMA-100 (+0.72 OOS) and BTC-regime (+0.77 OOS)
   beat the merged on OOS but on a MUCH WEAKER IS (+0.20 / +0.29 vs +0.65). That low-IS/high-OOS profile
   is the regime-luck / inverse-overfit signature seen across the campaign (AGREE_SCALE, DOT) — the high
   OOS rides a thin, regime-dependent base, not a consistent edge. Chasing it would violate the cardinal
   "don't overfit OOS" rule. The merged SMA-200 (high IS = consistent edge + solid OOS) is the durable choice.

## Net: confidence in the merged ETH baseline (iter-034, OOS +0.41) is RAISED.
The +0.41 is a robust both-positive edge — deterministic (K-invariant), confirmed across trend speeds
(100-200) and a cross-asset regime, and sitting at the IS-peak sweet spot. The single-primitive
dependence (200-SMA-on-ETH) is NOT a fragility — the neighborhood is broadly both-positive. (Note: all
robustness variants ran R2 ETH-calibrated as in the merged stack; the BTC-regime variant used ETH's R2 +
BTC's direction/gate — a slight mix, but the both-positive read is clear.)

## Next
The crown jewel is merged + robustness-validated; the strip-model investigation is complete (ETH-specific,
thoroughly mapped). The remaining strategic fork awaits the user's steer: (1) portfolio path (model-gated
bootstraps for the hard coins → bundle, for real breadth — uncertain/bigger), (2) consolidate, (3) a new
ETH-specific edge class. The cheap, high-value protective work is now done; the next phase is a genuine
strategic investment decision.
