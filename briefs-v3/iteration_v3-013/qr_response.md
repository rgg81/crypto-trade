# QR Response to Critic — iter-v3/013

**Critic PRELIMINARY**: SHA 3f85e86 (Round 1, all 12 checks PASS or WARN-carry-forward; 4 clarifications + new subtype proposal).
**Round**: 2 (QR response).

---

## Clarifications

### Clarification 1 — ADF demotion (WARN → PASS)

(a) **YES** — confirm 384 non-stationary cells concentrate in early walk-forward (2020-2021 sparse-data months) where unit-root tests are underpowered (n_obs < 200). This pattern has held across iter-v3/006-012 and is a known small-sample artifact, not a feature-design defect.

(b) **YES** — V3_FEATURE_COLUMNS is byte-identical to iter-v3/009 (no feature additions/removals across iter-v3/010-013). Check 5 inherits iter-v3/009's audit and is informational-only for iter-v3/013. Demote WARN → PASS.

### Clarification 2 — Catalog framing (NEW subtype EXPLORATION-PROMISING-MECHANICAL)

**ACCEPT Critic's proposal (b) — EXPLORATION-PROMISING-MECHANICAL** as new catalog subtype (sister to NEGATIVE-no-effect). The framing is more honest: trade-roster bit-identity between iter-v3/012 and iter-v3/013 across BCH/LDO/TRX (verified Critic spot-check LDO row 5: 11.07% × 0.88 = 9.74 weighted) proves the +1.11 OOS Sharpe lift is *entirely* MKR-removal accounting cleanup with **zero positive interaction effect** from the 3-symbol Optuna re-optimization. This parallels iter-v3/012's NEGATIVE-no-effect discipline (which classified a null result as null rather than burying it) — future CONFIRMATION QR inherits the audit that iter-v3/013 contributes "drop-MKR is strictly accretive component removal" but **NOT** "model edge improved by signal discovery". Going forward, PROMISING-MECHANICAL becomes the standard catalog vocabulary when single-axis variations produce mechanical (not interaction) lifts.

### Clarification 3 — TRX caveat YES; drop-TRX rule NO

(a) **YES** — catalog row records `n_high_pbo_cells_99 = 2` (TRX/2025-10, TRX/2025-11), explicit pre-commit caveat that future CONFIRMATION QR aggregates per-cell PBO via **(1 − max_per_cell_pbo)** rather than (1 − mean_per_cell_pbo); the recurring TRX 2025-Q4 tail is real (carried forward from iter-v3/012's tail unchanged) and the max-aggregator prevents averaging it away.

(b) **NO drop-TRX rule** — TRX has 0/1 OOS-negative iterations (the iter-v3/011 z=2.0 negative was IS-only, not OOS) versus MKR's 5/5 OOS-negative streak that triggered the drop rule. TRX serves the diversifier role with high trade volume (61 OOS trades vs LDO's 10) and is currently the workhorse symbol. **Pre-commit**: TRX drop rule trigger requires **5 consecutive OOS-negative iterations**, parallel to the MKR threshold; nothing in iter-v3/013 satisfies that condition.

### Clarification 4 — Docstrings + saturation parametrization

(a) **YES** — iter-v3/014 first commit (or fast-follow within first 3 commits) parametrizes stale strings at `run_baseline_v3.py:206, 211, 218` from hardcoded `= 88` to `= REQUIRED_GAP` (or f-string interpolation of the validation_v3 constant) so docstrings track the runtime value across future universe-size variations.

(b) **YES** — iter-v3/014 brief saturation falsifier computes from derived value: `falsifier_threshold = ceil(1.2 × counterfactual_n_trades)` where `counterfactual_n_trades` is the IS trade count of the prior reference iteration on the same universe. This makes the falsifier robust to single-axis universe variations (replaces fragile hardcoded 240 with a per-iteration derivation).

---

## Position

**STAND BY VERDICT** — request OVERALL = **EXPLORATION-PROMISING-MECHANICAL** (NEW subtype, sister to NEGATIVE-no-effect). Mechanical-accretion classification preserves audit honesty and prevents future CONFIRMATION QRs from misattributing the +1.11 OOS Sharpe lift to signal discovery rather than MKR-removal accounting.
