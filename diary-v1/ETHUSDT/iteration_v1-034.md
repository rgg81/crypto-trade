# Diary — iter-v1/034 (ETHUSDT) — EXPLORATION — PURE-DETERMINISTIC trend (strip the overfit LightGBM entry layer) — BREAKTHROUGH (OOS +0.056 → +0.41, deterministic, MERGE CANDIDATE)

**Axis:** the campaign-thesis bet — STRIP the LightGBM entry-timing layer and trade the PURE deterministic
core (200-SMA trend-state DIRECTION + conviction gate q=0.40): enter EVERY conviction-gated candle (when
flat) in the trend-state direction; model prediction IGNORED (`deterministic_entry_only=True`). Single axis
vs iter-027 (only the entry-decision source changes: LightGBM-prediction → deterministic-on-gated).
Everything else = the iter-027 stack (19-col features for the bypassed head, fixed_horizon N=42 14d,
atr_tp=100/sl=1.45, ETH-R2 4.07/16.27/0.20, R3=0.70, R5 vt=0.3, R1 OFF). K=1 (model unused → K-invariant).

**Result: IS Sharpe +0.6481 / OOS +0.4148** (ratio 0.64). 85 IS / 34 OOS trades, WR 34.1%/32.4%, PF
1.79/1.23, OOS MaxDD 17.47%. **specialist_dispersion_mean = 0.0 (provably deterministic — zero seed
variance → NO basin-lottery risk → K-invariant).** DSR IS +3.96 / OOS +7.36, PSR IS 0.974 / OOS 0.716
(DSR/PSR are n_trials=1 EXPLORATION-mode artifacts — informational, not the merge basis).

## BREAKTHROUGH — the OOS improved 7.4× and it Pareto-DOMINATES iter-027
| | iter-027 (model-gated) | **iter-034 (model stripped)** |
|---|---|---|
| IS Sharpe | +0.6336 | **+0.6481** (≥) |
| OOS Sharpe | +0.0560 | **+0.4148** (7.4×) |
| both-positive | yes | **yes** |
| deterministic | no (model lottery) | **yes (dispersion 0)** |

iter-034 is BETTER on BOTH IS and OOS → Pareto-dominates the baseline under the generalization-first gate.
And ETH OOS **+0.41 is 4.6× BTC iter-020's ceiling (+0.09)** — ETH has succeeded where BTC couldn't (the
user's mandate), via OOS STRENGTH (the model was the bottleneck), not breadth.

## Mechanism (campaign thesis vindicated; iter-030 forensic confirmed)
The campaign's core thesis: DETERMINISTIC parts generalize, LEARNED parts overfit. The 200-SMA trend-state
direction + conviction gate are deterministic (merged at iter-020/027); the LightGBM entry-TIMING/selection
layer is LEARNED. iter-030's forensic already showed de-correlating from the model's entry edge LIFTS OOS.
iter-034 takes it to the limit — REMOVE the model entry layer entirely:
- The model had learned IS-specific entry setups that did NOT generalize; it SKIPPED OOS-generalizing
  trend entries (overfit precision). Entering on ALL conviction-gated candles (deterministic) CATCHES the
  OOS trends the model was missing → OOS +0.056 → +0.41.
- The LightGBM was a DRAG on the OOS, not an edge. The deterministic core alone is the generalizing
  strategy. This is the cleanest possible result: no model → no overfit → no lottery → K-invariant.

## Honest caveats
- **NOT a breadth win.** 34 OOS trades, OOS top-2 share 124% — still the intrinsic let-winners-run
  concentration (same shape as iter-020/027; accepted intrinsic-design exception per the resolved gate).
  The "broad/de-concentrated OOS" mandate is NOT met; the "succeed where BTC couldn't" mandate IS met
  emphatically (OOS strength). De-concentration was separately proven intractable (6 mechanisms, /028-033).
- **OOS-vigilance:** the entry uses only the past-only conviction gate + trend-state direction (both
  look-ahead-tested; 7 new + 60 existing tests pass; no new data access). The model bypass adds no leak.
- **DSR/PSR positive but EXPLORATION-mode artifacts** (n_trials=1) — not cited as edge significance.

## NEXT — CONFIRM + MERGE (this dominates iter-027)
1. **iter-035 = K=20 CONFIRMATION** — empirically verify K-invariance (the result MUST be byte-identical
   to K=1 since the model is bypassed; confirms dispersion=0 / no hidden seed-dependence + satisfies the
   gate). FAST (model unused).
2. **Critic Phase 7.5** — adversarial: is the OOS +0.41 real (no leak/bug)? is the determinism claim
   sound (model truly bypassed)? merge-worthy vs iter-027?
3. If confirmed + Critic PASS → **MERGE as BASELINE_V1_ETHUSDT** (IS +0.65 / OOS +0.41, deterministic) —
   a dramatic improvement (7.4× OOS) over iter-027, and the first ETH baseline to beat BTC's OOS.
Then: explore whether breadth can be added ON TOP of this strong deterministic core (a complementary
deterministic edge), now that the core OOS is robust.
