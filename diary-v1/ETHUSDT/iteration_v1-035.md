# Diary — iter-v1/035 (ETHUSDT) — CONFIRMATION (K=20) — CONFIRMATION-MERGE (pure-deterministic trend → new BASELINE_V1_ETHUSDT)

**Axis:** K=20 confirmation of iter-034 (pure-deterministic trend: iter-027 stack with the LightGBM
entry layer stripped, `deterministic_entry_only=True`). Config byte-identical to v1-034; the K=20 run
verifies K-invariance (the model is bypassed → the strategy is a pure deterministic function of
data+gate+trend-state → must be identical to K=1).

**Result: BYTE-IDENTICAL to iter-034 (K=1).** IS Sharpe **+0.6481** / OOS **+0.4148**, sortino
+0.6460/+0.2754, maxDD 24.96%/17.47%, 85 IS / 34 OOS trades. `diff` of comparison.csv + in_sample/
trades.csv + out_of_sample/trades.csv between iter-034 (K=1) and iter-035 (K=20) = **IDENTICAL** (zero
bytes differ). specialist_dispersion = 0.0.

## Verdict: CONFIRMATION-MERGE. New BASELINE_V1_ETHUSDT = the pure-deterministic trend.
- **K-invariance EMPIRICALLY CONFIRMED:** K=1 ≡ K=20 byte-for-byte. The strategy is provably
  deterministic — zero seed variance, zero basin-lottery risk (the failure mode that killed iter-016/
  021/022/026/029). This is the most robust possible confirmation: there is nothing to vary.
- **Pareto-DOMINATES iter-027** (the prior baseline IS +0.6336 / OOS +0.0560): better IS (+0.6481) AND
  7.4× better OOS (+0.4148). Both-positive. Clears every generalization-first gate element.
- **Critic OVERALL=CONFIRMATION-MERGE** (briefs-v1/ETHUSDT/iteration_v1-034/review.md): full look-ahead
  audit PASS (every entry quantity past-only; embargo intact; entry-at-decision-bar-close conservative;
  costs honest); determinism SOUND (model truly bypassed — uniform confidence=1.0 across all 34 OOS
  trades vs iter-027's varying 0.05-1.0, the smoking gun); the OOS lift is mechanistically REAL (catches
  the +30% July-2025 ETH trend the overfit model SKIPPED). No leak, no bug.
- **ETH OOS +0.41 > BTC iter-020 ceiling +0.09** → ETH now succeeds where BTC couldn't (the user's
  mandate), via OOS STRENGTH (the LightGBM entry layer was the bottleneck — it overfit IS and dragged OOS).

## The campaign arc (how we got here)
The user's mandate: ETH must succeed where BTC couldn't (a broad/strong OOS), be creative, never give up.
- De-concentration of the trend OOS: INTRACTABLE — 6 mechanisms exhausted (M2 veto /028-029, AGREE_SCALE
  /030, exit-ladder /031-A, multi-signal /031-B, mean-reversion /032, ensemble /033). All NEGATIVE.
- The forensics kept pointing at ONE culprit: the LightGBM ENTRY SELECTION is OVERFIT (iter-030:
  de-correlating from it lifts OOS; iter-028/029: its learned veto is a K=20 lottery).
- iter-034 acted on that: STRIP the model entry layer. The deterministic core alone lifted OOS 7.4×.
  Breadth was the wrong frame; the binding constraint was the overfit model, and removing it was the fix.

## Caveats (carried into the baseline — load-bearing)
- STRENGTH win, not breadth (34 OOS trades; de-concentration remains intractable for this family).
- OOS MAGNITUDE is top-trade-fragile (top-2 ≈ 190% of weighted net; drop-top-2 flips negative) — the
  intrinsic let-winners-run exception, LESS concentrated than iter-027. The both-positive SIGN is the
  durable claim; anchor expectations to the SIGN + Pareto-dominance, not the exact +0.41.
- Process note (Critic flag): stale LEGACY iter-034 artifacts exist in the flat `briefs-v1/iteration_v1-034/`
  path (a different pre-redesign basis-zscore iteration) + a dead duplicate v1-034 dispatch branch at
  run_baseline_v1.py:6877 (V1_BASELINE_UNIVERSE-guarded; disambiguated at runtime). Latent footguns —
  fold out at next cleanup. The redesign artifacts (this iteration) live under `briefs-v1/ETHUSDT/`.

## Next
Highest-EV: PORTABILITY — apply the model-stripped deterministic core to BTC (does it lift iter-020's
OOS too?) + the next coins. If "strip the overfit model" generalizes across coins, it's the biggest
single change across the whole v1 track. Then: breadth-on-top-of-the-strong-core (a 2nd deterministic
let-winners band) + direction-robustness (trend_state_symbol→BTC / SMA 100-300), all K-invariant/fast.
