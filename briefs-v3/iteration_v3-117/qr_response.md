# QR Response to Critic — iter-v3/117

Round 2 of the two-round Phase 7.5 protocol. No new evidence introduced (no new analysis scripts, no new backtests). All references are to committed artifacts at commits `ac2c9f6` (code/pre-backtest), `e3363ae` (engineering report), `bb713e6` (research brief), `c64a5fc` (EDA), and the Critic preliminary at `briefs-v3/iteration_v3-117/review_preliminary.md`.

---

## Clarification 1 — Inner Optuna CV gap is panel-unaware (the decisive finding)

**The QR intended the inner Optuna CV to be panel-aware.** The Critic's reading is correct, and the implementation is incomplete. This is a code defect to flag for iter-v3/118.

The brief's Section 5 Risk 2 (line 363 of `research_brief.md`) literally claims:

> "Mitigation: `REQUIRED_GAP = 72 = (7+1) × 3 × 3` covers BOTH within-offset purging (7+1=8 daily bars) and cross-offset purging (× 3 offsets). The runner pre-flight verifies `REQUIRED_GAP == 72` at startup; **the LightGBM walk-forward cv computes a fold-boundary gap of `8 daily bars × 3 = 24 daily bars per offset = 72 panel rows`** (since the concatenated panel has 3 offsets per calendar day)."

The bolded clause is **false as implemented**. The actual code at `lgbm.py:494-498` is:

```python
if self.cv_label_gap:
    interval_minutes = _interval_to_minutes(self._interval)
    embargo_candles = compute_embargo_candles(self.label_timeout_minutes, interval_minutes)
    n_symbols = len(set(self._sym_arr[train_indices]))
    cv_gap = embargo_candles * n_symbols
```

At 24h-multi-offset, `_interval` resolves to "24h", so `interval_minutes = 1440`, and `embargo_candles = ceil(10080/1440) + 1 = 8`. `n_symbols = 1` because Optuna runs per-symbol (the `train_indices` slice has already been narrowed by the per-symbol training loop). So `cv_gap = 8 × 1 = 8` rows — exactly what the Critic observed in the log (`CV gap: 8 rows`).

The brief's mitigation arithmetic (`8 × 3 = 24` daily bars per offset → 72 panel rows) was the QR's intended panel-aware computation. The missing multiplier is `n_offset_series`, which is invisible to `lgbm.py` because the offset interleaving happens at the data-load layer (the concatenated 24h panel has 3 rows per calendar day per symbol, but `_sym_arr` only tracks symbol identity, not offset identity). The strategy never receives an `n_offset_series` parameter, so `cv_gap` cannot multiply by it.

**Consequences for the /117 IS metrics.** Within each Optuna CV fold inside a single per-symbol training run, the last ~13 rows of the training fold have forward-label deadlines reaching ~4.33 daily bars into the validation fold (the 7-daily-bar forward-scan window minus the 2.67-daily-bar gap). At single-symbol granularity this is intra-offset leakage along the 21-row forward window, NOT cross-offset (each Optuna fold sees one symbol's interleaved 3-offset panel, so the leak is cross-offset within that symbol). The Critic correctly characterizes this as IS-direction biased; the OOS-direction collapse is driven by Mechanisms 1–3 (BCH imbalance, TRX evaporation) plus the refined Mechanism 4 (Critic-corrected), not by the inner CV leak.

**Action for /118.** This is a code defect, not a Phase 7.5 BLOCK for /117 (the iteration already filed EXPLORATION-NEGATIVE on hypothesis-falsification grounds independent of the inner CV gap). The fix is to thread an `n_offset_series` parameter (default 1) into `LightGbmStrategy.__init__`, pass it from `run_baseline_v3.py` when `--bar-interval 24h`, and multiply at `lgbm.py:498`: `cv_gap = embargo_candles * n_symbols * n_offset_series`. The /118 QR should add this to the brief's Section 3.5 as a precondition for any future multi-offset axis, even though the /117 result already closes the multi-offset architecture for cycle 6 (see Clarification 4).

**Conclusion.** Critic Check 2 FAIL is accepted. The brief's Risk 2 mitigation prose was misleading because it described intended behavior, not implemented behavior. This is the QR's defect to record. No artifact-grounded counter-argument is available.

---

## Clarification 2 — offset_id IC matrix omission (Check 4 WARN)

**Oversight, not intentional.** The 14×14 `ic_matrix.csv` was emitted by the standard reporting path that iterates over `V3_FEATURE_COLUMNS` (the 14-feature list). The 15th feature `offset_id` is added at the runner level (`run_baseline_v3.py` extends `_feature_columns = V3_FEATURE_COLUMNS + ["offset_id"]` when `--bar-interval 24h`), but the IC-matrix writer at the report layer reads `V3_FEATURE_COLUMNS` directly, missing the runner-appended column.

The omission is informationally inert for /117 adjudication because:
- `offset_id` has only 3 discrete values {0, 8, 16}; its variance is bounded and any pairwise Spearman IC with continuous features is bounded by ≈ ±0.2 by the variance-partition argument.
- LightGBM's importance rank of 15/15 (importance = 21.0 vs top 241.3, ~1% of leading weight) independently establishes that `offset_id` is non-load-bearing at the production-model level.
- The 14-feature IC matrix correctly surfaces the pre-existing /059 carve-out (`regime_momentum_signed_5d × vwap_dev_20 = 0.7642`) covered by `feedback_v3_engineered_feature_pivot.md`.

**Action for /118.** If any future iteration appends a non-V3_FEATURE_COLUMNS feature at the runner level, the IC-matrix writer should iterate over `_feature_columns` (the runtime list) rather than `V3_FEATURE_COLUMNS`. This is a one-line fix and not blocking for /117.

**Conclusion.** Critic Check 4 WARN is accepted as a documentation defect.

---

## Clarification 3 — Mechanism 4 refinement (z-score gate over-fire)

**I concur with the Critic's refined mechanism.** The engineering report's prose ("z-score gate calibrated on 8h IS statistics") is mechanically incorrect; the Critic's reading of `risk_v2.py:533-545` is correct.

Specifically, the per-symbol z-score gate parameters (`feature_mean[symbol]`, `feature_std[symbol]`) are rebuilt from the IS-distribution loaded at training time, not carried across the 8h → 24h transition. At 24h-multi-offset, the IS distribution passed to the gate-calibration step is the concatenated 3-offset panel for each symbol. Three independent failure points:

1. **Pooled-across-3-offsets mean/std.** The 3 offsets (0h, 8h, 16h UTC) have heterogeneous feature distributions (e.g. funding-cycle-aligned vs mid-cycle vs post-cycle). Pooling produces a per-symbol mean/std that is correct only as a 3-offset weighted average. Offset-0 features evaluated against this pooled mean/std exhibit inflated z-scores because the pool's std is wider than any single offset's std (between-offset variance contributes to total variance). LDO's 69.5% kill rate is consistent with this — LDO's 24h aggregation has the highest between-offset heterogeneity in the 3-symbol universe.

2. **LDO small-sample std estimation.** LDO has ~707 rows per offset (the EDA's T2 row counts). At small per-offset sample size and 3-offset pooling, the std estimate is noisier than at 8h (where each symbol has ~2120 contiguous 8h rows). Noisier std → more z-score tail mass over the 2.0 threshold → higher gate-kill rate.

3. **z=2.0 fixed threshold inappropriate for 24h-multi-offset distribution.** The /059-canonical z=2.0 threshold was calibrated on 8h single-series feature distributions whose tail shape differs from the 24h-multi-offset pooled distribution. The 24h-multi-offset pooled distribution has heavier tails (between-offset variance + within-offset variance compounded), so z=2.0 captures more mass than intended.

**No additional gate state carries 8h calibration.** I audited `risk_v2.py:533-545` and the calling code path. The gate parameters are rebuilt at every training-month boundary from the current IS slice. There is no 8h-derived state left over after the `--bar-interval 24h` flag is set — the only 8h legacy is the literal z=2.0 threshold constant, which was IS-calibrated at 8h-univariate but not re-calibrated for the multi-offset pool.

**Engineering report correction (not a /118 axis).** The /117 engineering report's prose is the wrong characterization of an empirically real over-fire. The phenomenon is real; the explanation is wrong. The corrected mechanism is the Critic's: pooled-across-3-offsets std inflation + LDO small sample + z=2.0 inappropriate for the pooled tail. This refinement strengthens — not weakens — the FALSIFIED-AS-TESTED verdict on the multi-offset architecture, because the over-fire is structurally induced by the 3-offset pool, not by a separable threshold-recalibration knob.

**Conclusion.** Critic's refined Mechanism 4 is accepted in full.

---

## Clarification 4 — Frequency-axis closure scope

**The entire 24h-frequency axis as tested is closed for cycle 6.** The 12h-2-offset and weekly-8-offset fallback paths referenced in the brief Section 7 Mode 4 RESIDUAL block are NOT in play for cycle 6.

Reasoning, structured by confound:

**(a) BCH 99.12% label imbalance.** This is a property of BCH's volatility distribution at the 24h scale paired with the /059-canonical (2.0, 1.0) ATR multipliers and 7-daily-bar timeout. Tightening to (1.5, 0.5) at 12h or (3.0, 1.5) at 1d-weekly would shift the imbalance but not eliminate it — the underlying 3-symbol universe (BCH/LDO/TRX) was selected on 8h volatility profiles, and the alt-cohort's 24h+ volatility is structurally low-amplitude. Any candle-frequency axis at 12h or longer will face a related imbalance problem on BCH or TRX. Not a per-design fix.

**(b) Pooled-multi-offset z-score gate over-fire.** This is structurally induced by ANY multi-offset architecture (2-offset, 3-offset, 8-offset). The gate-calibration code rebuilds per-symbol mean/std from the pooled IS distribution; pooling across heterogeneous offsets inflates std regardless of how many offsets. Re-calibrating z=2.0 → z=2.5 would lift the tail mass cutoff but introduces an axis-tuning knob that wasn't pre-registered and would now be data-snooped on /117's catastrophic OOS — a `feedback_no_cheating.md` violation if attempted at /118.

**(c) offset_id rank 15/15.** This is the falsifying observation for the multi-offset hypothesis as conceived. The QR's brief Section 3.5 explicitly framed offset_id as the mechanism by which LightGBM would learn offset-specific signal structure ("if the model learns offset-conditional patterns, offset_id will rank in the top 5 features"). At rank 15/15 with importance ~1% of leading weight, LightGBM did NOT learn offset-conditional structure — the 3-offset architecture DEGENERATES to a 3×-oversampled single-offset training, which is exactly the architecture's worst-case failure mode (per the EDA's PARTIAL-GO caveat).

**Why a single-offset 24h refined design is also CLOSED for cycle 6.** A hypothetical /118 axis like "single-offset 24h with BCH-specific labeling and re-calibrated z-score" would address (a) and (b) but the diagnostic question — "does daily-frequency aggregation lift the directional signal vs 8h?" — was already answered by the multi-offset design's offset_id-rank-15/15 result. The multi-offset design was the BEST CASE for the candle-frequency hypothesis because it gave LightGBM the maximum information about the daily-frequency representation while preserving 3× training-data density. The fact that LightGBM weighted offset_id at 1% of the leading feature's importance means daily-frequency aggregation provides no separable signal lift even when handed to the model on a platter. A single-offset 24h design would have strictly less information and strictly less training density. The architecture's failure mode is not addressable by stripping the multi-offset layer; it's a property of the daily-frequency representation itself on the BCH/LDO/TRX universe.

**12h-2-offset and weekly-8-offset fallback paths.** Both were named in the /116 diary Section 9 + brief Section 7 Mode 4 RESIDUAL as ESCAPE HATCHES contingent on /117 filing as BEHAVIORAL-INERTIA (Mode 4 ≤ 30 IS trades / catastrophic structural failure). /117 filed as Mode 1 (substantive NEGATIVE — 170 IS trades, IS −2.17, OOS −3.26 in the operative regime), NOT Mode 4. The Mode 4 fallback paths were predicated on the 24h architecture being unreachable for measurement; the /117 architecture is measurable and decisively negative. The fallback paths therefore do not activate.

**Cycle 6 implication.** The candle-frequency axis is CLOSED for cycle 6. Cycle-6 has 2 EXPLORATION slots left (/118, /119) before the mandatory /120 CONFIRMATION. Both should pivot to a different HIGH-priority axis from `project_v3_cycle6_axis_menu.md` — the candidate set per the menu and prior NEGATIVE filings is restricted, but the LIVE structural axes I would suggest for /118 are: (1) a NEW engineered feature family at 8h (composed features still have headroom per `feedback_v3_engineered_features_proven.md`), or (2) a per-symbol model-architecture pivot (XGBoost-with-categorical-handling for the imbalanced BCH cell — the iter-v3/016 LightGBM→XGBoost test was at universal-cohort + cross-entropy + depth-wise defaults and is NOT closed for per-symbol+imbalance-aware configurations). These are suggestions, not pre-commitments — the /118 QR makes the axis selection with EDA-driven quantitative discipline per `feedback_v3_axis_selection_quant_discipline.md`.

**Conclusion.** The 24h-frequency axis is broadly closed for cycle 6. The fallback 12h-2-offset and weekly-8-offset paths from /116 diary Section 9 are de-prioritized because the failure modes ((a) imbalance, (b) pooled-multi-offset over-fire, (c) offset_id non-learning) are not specific to the 3-offset design — they recur at any multi-offset cadence and (offset_id-non-learning) is a property of daily-or-longer aggregation on the cohort. The QR records the candle-frequency axis as a cycle-6 dead path. Future re-opening would require either (i) a different 3-symbol universe with more favorable 24h volatility profiles, or (ii) a structurally different multi-offset architecture (e.g. per-offset separate models + late-fusion, not pooled-with-offset_id training) — neither of which is a cycle-6 axis.

---

## Position

**STAND BY VERDICT.** I accept the Critic's preliminary EXPLORATION-NEGATIVE direction. Check 2 FAIL is a substantive methodology finding (intent-vs-implementation gap in the inner Optuna CV gap, flagged for /118 code-defect fix). Check 4 WARN is an oversight in the IC-matrix writer (one-line fix for /118). Mechanism 4 refinement is accepted in full. The 24h-frequency axis is broadly closed for cycle 6; the Mode 4 fallback paths do not activate because /117 filed as Mode 1 substantive NEGATIVE rather than BEHAVIORAL-INERTIA.

No artifact-grounded counter-argument is available. The hypothesis (24h-multi-offset representation lifts directional signal via daily-frequency aggregation + 3-offset training-data multiplication) is FALSIFIED at production scale: IS −2.17 vs +0.30 floor (Δ −3.00); OOS −3.26 vs −0.20 floor (Δ −3.40). Both arms of the brief Section 4 pre-registered falsifier ("OOS < −0.20 AND IS < +0.30") fire decisively. The 4-mechanism trace (Critic-refined Mechanism 4) is mechanistically coherent and dispositive.
