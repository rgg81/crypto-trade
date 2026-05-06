# Phase 7.5 Critic Review — iter-v3/012 — ROUND 2 FINAL

**OVERALL: EXPLORATION-NEGATIVE-no-effect**

**Iteration Type**: EXPLORATION (catalog row #5 since last CONFIRMATION; BTC-trend-filter-band axis per Critic FINAL Rec 1 of iter-v3/011)
**Mode**: Round 2 — FINAL
**Brief SHA**: `8ceb2c6` | Phase 5.5 Gate SHA: `6d1e126` | Engineering Report SHA: `1465ef2` | Round 1 PRELIMINARY SHA: `bcc8f86` | QR Response SHA: `1f67cea` | Analysis SHA: `aadeb72` | Runner SHA: `93891a3`

The verdict subtype `NEGATIVE-no-effect` is a NULL-RESULT classification: the iteration's sub-fix executed cleanly and all methodology checks pass, but the registered hypothesis ("tightening BTC band helps") is unsupported AND the trade roster is byte-identical to iter-v3/011, indicating zero information gain on the BTC-trend-filter-band axis in the (15%, 20%) regime.

---

## QR Response Considered (6 Clarifications)

### Clarification 1 — Catalog framing as NEGATIVE-no-effect
**QR position**: NEGATIVE-no-effect. **Disposition**: ACCEPTED. Trade rosters IDENTICAL (286 IS, 101 OOS); per-symbol LDO/MKR EXACT match; PBO bit-identical at 0.1077; n_eff bit-identical at 7. The 17 additional BTC-filter kills materialized as zero-weight rows reducing IS total_pnl 97.31% → 73.42% but did not displace any trades. Cataloguing PROMISING would mislead future CONFIRMATION QR into bundling ±15% as ingredient when finding is "band width in (15%, 20%) is structurally inert."

### Clarification 2 — MKR rule TRIGGERED + drop candidate scope
**QR position**: Rule TRIGGERED. iter-v3/013 = per-symbol-diagnostic (drop MKR, 3-symbol BCH+LDO+TRX universe). MKR is only drop candidate. **Disposition**: ACCEPTED. TRX OOS-positive in 2 consecutive iterations — sign criterion does not apply. MKR-only drop is correct scope per `feedback_mkr_threshold_compression.md` (SHA b9ebbb2).

### Clarification 3 — MKR magnitude stationarity
**QR position**: Rule satisfied (sign criterion, not magnitude). Stationary at -25.75% is itself significant signal. **Disposition**: ACCEPTED. The pre-committed rule text is "5th consecutive negative" — sign criterion. Counter increments. Stationarity strengthens diagnostic case: BTC band tightening had ZERO effect on MKR's 16 OOS trades.

### Clarification 4 — ±25% looser direction deferred
**QR position**: Deferred to iter-v3/014+ at earliest. **Disposition**: ACCEPTED. MKR rule overrides conditional permission. Falsifier 1 NOT triggered would have prevented activation regardless.

### Clarification 5 — IS Sharpe reconciliation in diary
**QR position**: YES, quantitative reconciliation paragraph. Recompute IS Sharpe using iter-v3/011 weight_factor with iter-v3/012 trade roster; expected to reproduce +0.9566. **Disposition**: ACCEPTED. Informational-only but strengthens audit trail. If recomputation FAILS to reproduce, follow-up investigation required.

### Clarification 6 — Per-cell PBO tail thickening flagged
**QR position**: YES, `n_high_pbo_cells_99=4` in catalog. Future CONFIRMATION QR uses `(1 − max_per_cell_pbo)` not just `(1 − mean_pbo)`. **Disposition**: ACCEPTED. The two new TRX/2025-Q4 cells with PBO=1.00 are particularly concerning because they appear in OOS-extending months — suggesting either regime drift or per-cell sample-size collapse at OOS frontier.

---

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Single change `BTC_TREND_CONFIG.threshold_pct` 20.0 → 15.0 at `run_baseline_v3.py:121`. BTC trend filter at `risk_v2.py:806-869` is post-hoc; operates on `btc_closes[idx − lookback_bars]` with `idx ≤ trade.open_time`. No look-ahead.

### Check 2 — Embargo Width: PASS
CV gap = 88. Labeling unchanged. BTC band tightening doesn't touch CPCV.

### Check 3 — Multiple-Testing Correction: METHODOLOGY-PASS / EDGE-INFORMATIONAL
PBO = 0.1077 BIT-IDENTICAL to iter-v3/010/011. n_eff = 7 BIT-IDENTICAL. DSR/PSR single-seed artifact. Per-cell tail: `n_high_pbo_cells_99 = 4`.

### Check 4 — IC Correlation: PASS
Identical to iter-v3/011 (zero new features).

### Check 5 — ADF Stationarity: WARN (carry-forward)
Same as iter-v3/011.

### Check 6 — Pareto Dominance: WAIVED (single-seed)

### Check 7 — Reproducibility: PASS
Code SHA 93891a3 stamped; ITERATION_LABEL=v3-012 confirmed.

### Check 8 — Hypothesis-Implementation Alignment: PASS-mechanical / HYPOTHESIS-UNSUPPORTED
Single-axis cadence rule honored. Falsifier 1 NOT triggered. HOWEVER: registered hypothesis "IS Sharpe maintained or improved" — IS dropped from +0.96 to +0.81 (Δ -0.147, wrong direction). Mechanical pass coexists with substantive non-support, underpinning NEGATIVE-no-effect verdict.

### Checks 9-12: PASS

---

## Verdict Rationale

**EXPLORATION-NEGATIVE-no-effect** because:

1. **Hypothesis "tightening helps" UNSUPPORTED.** IS Sharpe direction wrong (-0.147).
2. **Trade roster IDENTICAL.** 286 IS, 101 OOS, LDO/MKR EXACT match, PBO bit-identical, n_eff bit-identical. The 17 additional BTC kills only zeroed weight on previously-low-performing trades.
3. **Catalog discipline overrides mechanical IS pass.** Cataloguing PROMISING misleads future CONFIRMATION QR.
4. **All 12 methodology checks PASS.** Zero BLOCK conditions. Engineer's null-result explanation mechanically plausible.
5. **Pre-committed MKR rule binds iter-v3/013.** iter-v3/013 MUST be drop-MKR per-symbol-diagnostic.
6. **Per-cell PBO tail thickening** is a future-CONFIRMATION constraint.

iter-v3/012 NEVER updates BASELINE_V3.md.

---

## Recommendations to QR

1. **iter-v3/013 must be drop-MKR per-symbol-diagnostic single-axis EXPLORATION (3-symbol BCH+LDO+TRX universe).** This is the only valid axis per pre-committed MKR rule. Test explicitly whether removing MKR's structural −25.75% drag improves IS+OOS edge OR merely shifts concentration to remaining symbols. Brief Section 4 prediction must enumerate both outcomes.

2. **iter-v3/012 catalog row must capture five distinct fields**: (a) `verdict = NEGATIVE-no-effect` (NULL-RESULT subtype); (b) `mkr_rule_triggered = TRUE` with explicit pointer to `feedback_mkr_threshold_compression.md` and 5-iteration trajectory; (c) `pm25_deferred = TRUE, earliest = iter-v3/014`; (d) `n_high_pbo_cells_99 = 4` with 2 new TRX/2025-Q4 entries; (e) `trade_roster_identity = TRUE` — load-bearing finding.

3. **Process meta-feedback — add `feedback_axis_saturation_predictor.md`**. When single-axis EXPLORATION produces zero behavioral change (trade roster identical, PBO bit-identical), future briefs Section 2 must include behavioral-effect predictor — explicit estimate of how many IS trades will change, with falsifier triggered if observed change is below predicted lower bound. iter-v3/012 brief predicted "~243-271 IS trades (5-15% reduction)" — observed was 286 (0% reduction). This calibration gap should be closed by predictor discipline.
