# QR Response to Critic — iter-v3/012

## Clarifications

### Clarification 1 — Catalog framing
**EXPLORATION-NEGATIVE-no-effect.** The hypothesis was "tightening BTC trend band 20% → 15% improves OOS Sharpe"; the iteration produced ZERO behavioral change (trade rosters IDENTICAL: 286 IS, 101 OOS) and the hypothesis is therefore UNSUPPORTED. The IS-Sharpe ≥ +0.40 mechanical pass is misleading because it inherits from the unchanged trade roster — cataloguing PROMISING would mislead future CONFIRMATION QR into bundling ±15% as an ingredient when the actual finding is "band width in (15%, 20%) is structurally inert"; catalog discipline > headline-metric mechanical pass.

### Clarification 2 — MKR rule trigger + diagnostic candidate
**Rule TRIGGERED.** Per `feedback_mkr_threshold_compression.md` (SHA `b9ebbb2`), iter-v3/013 MUST be a per-symbol-diagnostic axis (drop MKR, run 3-symbol BCH+LDO+TRX universe), and the rule cannot be renegotiated post-hoc. **MKR is the only drop candidate**: TRX has IS-negative but OOS-positive (+4.04% in iter-v3/012, +5.97% in iter-v3/011) — that's not a sustained pattern; only MKR shows 5 consecutive OOS-negatives with worsening or stationary-at-worst trajectory.

### Clarification 3 — MKR magnitude stationary
**Rule satisfied.** The pre-committed rule text is "5th consecutive negative" — a sign criterion, not a magnitude criterion; -25.75% in iter-v3/012 is the 5th consecutive negative and the counter increments. Stationary at -25.75% is itself a significant signal: BTC band tightening had ZERO effect on MKR's 16 OOS trades, indicating MKR is structurally bad regardless of axis perturbation.

### Clarification 4 — ±25% deferred
**Confirmed deferred to iter-v3/014+ at earliest.** The MKR pre-committed rule "cannot be renegotiated post-hoc" overrides the conditional ±25% looser-direction test from brief Section 7; per-symbol-diagnostic in iter-v3/013 takes priority, and ±25% returns to the queue only after diagnostic completion plus at least one additional non-BTC-band axis.

### Clarification 5 — IS Sharpe reconciliation
**YES — quantitative reconciliation paragraph in diary.** Diary will recompute IS Sharpe using iter-v3/011 `weight_factor` values applied to iter-v3/012's IS trade roster; if the Engineer's mechanism is correct (the -0.147 drop is purely the 17 additional zero-weight BTC-killed trades reducing weighted total_pnl while leaving IDENTICAL trade-level returns), the recomputation should reproduce iter-v3/011's +0.9566 exactly, strengthening the audit trail for future CONFIRMATION QR.

### Clarification 6 — Tail thickening
**YES — flag in catalog.** Per-cell tail count entry: `n_high_pbo_cells_99 = 4` (TRX/2025-10=1.00, TRX/2025-11=1.00, MKR/2025-04=0.995, MKR/2025-07=0.991), with the 2 new TRX 1.00 cells appearing in the newer OOS extent vs iter-v3/011's 3-cell tally. Future CONFIRMATION QR weighting must use `(1 - max_per_cell_pbo)` not just `(1 - mean_pbo)` to avoid masking concentrated worst-cell risk in symbols where PBO has saturated.

## Position
**STAND BY VERDICT — request OVERALL = EXPLORATION-NEGATIVE-no-effect with full caveat catalog including MKR rule trigger, IS Sharpe reconciliation, and per-cell tail flag.** The hypothesis "tightening helps" was not supported, the iteration produced no information gain on the BTC trend axis, and the MKR pre-committed compression rule is now the binding constraint on iter-v3/013 design.
