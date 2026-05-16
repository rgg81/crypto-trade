# iter-v3/074 — Cycle 2 #4 EXPLORATION / Regime-conditional kill switch (primitive 9, TRX-scoped) / INERT-AT-EXPLORATION

**Date**: 2026-05-15
**Type**: EXPLORATION (cycle 2 #4 of 10; NEW RISK PRIMITIVE axis — holding-time-ORTHOGONAL by design)
**Axis**: regime-conditional kill switch (primitive 9) — `enable_regime_gate=True`, `regime_gate_symbols=("TRXUSDT",)`. The gate suppresses TRX trade entries when BTC is in a regime-stress state (BTC drawdown_30d > 20% OR |vol_z_30d| > 1.5).
**Verdict**: EXPLORATION-MERGE per Critic FINAL `2371324` — OVERALL=MERGE; **INERT-AT-EXPLORATION classification certified clean** (closeout-integrity / methodology certification, NOT an advancement)
**Classification**: **INERT-AT-EXPLORATION** per brief Section 8.3 LOCKED criteria (both shifts inside the noise bands; SUSPICIOUS does not fire; gate fired so NULL-RESULT is excluded)
**Advancement**: does NOT advance to the cycle-2 CONFIRMATION bundle — the regime gate suppressed too few trades (3 IS + 5 OOS) to move headline metrics
**BASELINE_V3.md**: **UNCHANGED** — /059 stays canonical (IS +1.0894 / OOS +0.5791; tag `v0.v3-059`). One BASELINE_V3.md edit at this closeout: regime-conditional kill switch added to "Dead Ideas" (see Section 7).
**Branch**: `iteration-v3/074`

---

## 1. What was done

iter-v3/074 is the FOURTH EXPLORATION of v3 cycle 2 (post-cycle-1-CONFIRMATION at iter-v3/070). Per `feedback_v3_strict_10_to_1_cadence.md`, cycle 2 runs 10 SEPARATE EXPLORATIONs (/071-/080) followed by 1 SEPARATE CONFIRMATION.

The axis is **primitive 9 — a regime-conditional kill switch**, a NEW RISK PRIMITIVE axis chosen specifically to satisfy the Critic /073 hard constraint. After three consecutive SUSPICIOUS-OOS-DOMINANT iterations (/065, /071, /073 — all holding-time-EXTENSION axes), the /073 Critic mandated that /074 be a **holding-time-ORTHOGONAL axis** OR a dedicated IS/OOS regime-diagnostic axis. The QR EDA-driven axis selection (`feedback_v3_axis_selection_quant_discipline.md`) chose the regime-conditional kill switch — orthogonal to holding time by mechanism: the gate removes trades but does not systematically lengthen the duration of the kept roster. The brief Section 2.3 holding-time-effect predictor (mandated by `feedback_v3_is_oos_regime_divergence.md`) pre-registered a near-zero kept-roster duration delta and a +1.5-candle falsifier.

Gate scope: `regime_gate_symbols=("TRXUSDT",)` — the kill switch fires ONLY on TRX. BCH and LDO are untouched by construction. The hypothesis (brief Section 7) is that the gate's value is the **training-distribution shift** — TRX training months that include FTX/LUNA-crash bars (2022-10, 2023-01: the BASELINE_V3.md PBO=1.0 cells) lose those bars from the Optuna optimization landscape, so a TRX model trained without crash-regime bars generalizes better. The post-hoc counterfactual cannot measure this; only the backtest can.

A mandatory secondary edit reverted /073's leftover: `V3_ATR_MULTIPLIERS_PER_SYMBOL` was re-populated for BCH/LDO at /073 (the per-symbol triple-barrier asymmetry axis). It was reverted to `{}` so all symbols return to `DEFAULT_ATR_MULTIPLIERS (2.0, 1.0)`. This is a revert to the established cycle-2 baseline labeling, not a second varied axis.

Run mode: EXPLORATION (`--exploration` → `EXPLORATION_ENSEMBLE_SIZE = 3`, ENSEMBLE_SEEDS outer=42 lineage subset `[191664963, 1662057957, 1405681631]`), `--n-trials 35`, 3-symbol universe (BCH/LDO/TRX), REQUIRED_GAP=66, embargo 22. Total 315 Optuna trials. Anchor for EXPLORATION-mode comparison: iter-v3/060 (IS +0.8325 / OOS +0.1403).

Commit chain: setup `a5d5cdd` → Phase 5.5 gate `0c01d8f` (PASS) → brief LOCKED → engineering report `79a8181` → Critic review `2371324`.

## 2. Results — vs /060 EXPLORATION-mode anchor

| Metric | /060 anchor | /074 | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | **+0.8325** | **+0.8454** | **+0.013** (inside ±0.10 noise band) |
| OOS monthly Sharpe | **+0.1403** | **+0.2090** | **+0.069** (inside ±0.20 noise band) |
| OOS/IS monthly Sharpe ratio | 0.28 | **0.247** | healthy — no regime-divergence |
| frac_positive_paths (CPCV) | 0.6444 | 0.6444 | 0 (architecture-invariant) |
| PBO mean | 0.1278 | 0.1278 | 0 |
| DSR (legacy) | — | 0.0 | structural FAIL (informational at EXPLORATION) |
| DSR_relative_B4 | n/a | 0.0715 | informational FAIL (EXPLORATION-mode artifact) |
| PSR | 0.9763 | 0.9985 | informational |
| n_trials (Optuna total) | 315 | 315 | 0 |
| n_eff | 19 | 19 | 0 |

Both headline shifts are inside their noise bands (IS +0.013 ∈ ±0.10; OOS +0.069 ∈ ±0.20). The OOS/IS ratio of 0.247 is healthy and does NOT trip the SUSPICIOUS gate (>3.0). DSR_relative_B4 = 0.0715 and legacy DSR = 0.0 FAIL their 0.95 thresholds but are **informational at EXPLORATION** per `feedback_v3_dsr_mode_artifact.md` — the EXPLORATION-mode `n_trials=315` regime is not comparable to CONFIRMATION-mode `n_trials=1050`, and these gates do not trigger a BLOCK for an EXPLORATION iteration.

### 2.1 Per-symbol OOS decomposition

| Symbol | /074 OOS wpnl | /074 OOS n_trades | /074 OOS WR | Note |
|---|---:|---:|---:|---|
| BCHUSDT | **+1.9078** | 37 | — | **BIT-IDENTICAL to /060** — gate scoped to TRX only; QE verified 37/37 trades field-by-field |
| LDOUSDT | **−18.41** | — | — | unchanged; gate does not touch LDO |
| TRXUSDT | **+24.80** | — | 51.0% | the gate's only target symbol |

BCH bit-identity is the positive control: the gate `regime_gate_symbols=("TRXUSDT",)` cannot touch BCH, and the QE confirmed BCH 37/37 OOS trades field-by-field identical to /060. Single-axis discipline is verified. LDO is likewise untouched.

### 2.2 Gate efficacy

The regime gate fired: **3 IS + 5 OOS TRX trade suppressions.** The TRX kept-roster duration delta was **−0.389 candles IS / −0.240 OOS** — near-zero and slightly NEGATIVE, well inside the +1.5-candle falsifier and in the OPPOSITE direction from the holding-time-extension family (/065/071/073). The gate did fire — so the verdict is INERT, not NULL-RESULT (brief Section 8.5 defines NULL-RESULT strictly as `regime_gate_fires total = 0`).

## 3. Key finding — holding-time-orthogonal hypothesis CONFIRMED

This is the scientific deliverable of the iteration.

The prior three SUSPICIOUS-OOS-DOMINANT iterations (/065, /071, /073) were ALL holding-time-EXTENSION axes. They loaded a structural IS/OOS regime-divergence factor: v3's IS window (2022-09 → 2025-03) spans bear + chop + bull and **penalizes longer-held trades**; v3's OOS window (2025-03 → 2026-05) is a persistent BCH/LDO/TRX uptrend that **rewards longer-held trades**. Any axis that lengthens effective trade holding time mechanically loads this regime difference — OOS Sharpe soars, IS Sharpe collapses, the OOS/IS ratio inflates.

/074 — deliberately a holding-time-ORTHOGONAL axis — did NOT reproduce the SUSPICIOUS pattern:

- OOS/IS monthly Sharpe ratio = **0.247** (vs the SUSPICIOUS family's escalating 1.56 / 0.68 / 6.85 — see Section 4 for the corrected ratios).
- TRX kept-roster duration delta = **−0.389 candles IS / −0.240 OOS** — slightly NEGATIVE, the OPPOSITE direction from the extension family.

The discriminating fact is the **sign and direction** of the duration delta, not merely its magnitude. A holding-time-extension axis loads the regime factor by lengthening the kept roster regardless of how few trades it touches; /074's kept roster is marginally SHORTER-held, which is mechanistically incompatible with regime-factor loading. The small headline shift and the orthogonality are two independent observations that happen to agree, not one observation double-counted (Critic Check 8 / adversarial question 4).

This **confirms the regime-divergence diagnosis** recorded in `feedback_v3_is_oos_regime_divergence.md`: holding-time-extension axes load the regime factor; holding-time-orthogonal axes do not. The 3-SUSPICIOUS-then-1-orthogonal-confirmation evidence chain is now closed.

## 4. CORRECTED prior-iteration OOS/IS ratios (Critic Rec #1)

The /074 engineering report cited the prior SUSPICIOUS OOS/IS ratios for /065/071/073 as **"5.04 / 4.51 / 12.55"**. Per Critic FINAL `2371324`, this is **factually wrong** — those numbers reconcile to no source artifact, and the engineering report's "/073 = 12.55" directly **contradicts /073's own byte-confirmed `comparison.csv` ratio of 6.8468.**

The /073 diary table ("2.87 / 4.51 / 6.85") and the /071 diary ("0.6774") already disagreed with each other. The cycle has been drifting between constructions. Per Critic Rec #1, the **byte-confirmed within-iteration `comparison.csv` `monthly_sharpe` ratio column** is the single canonical definition (because that is the value the Section 8.4 SUSPICIOUS gate actually consumes). The corrected ratios are:

| Iter | Axis (all holding-time-EXTENSION) | OOS/IS ratio (CORRECTED — within-iteration `comparison.csv`) | Eng-report's WRONG value |
|---|---|---:|---:|
| /065 | Universal SL widening (2.0,1.0)→(2.0,1.5) | **1.56** | 5.04 |
| /071 | Meta-labeling (same-feature M2 take/skip) | **0.68** | 4.51 |
| /073 | Per-symbol triple-barrier asymmetry (BCH/LDO SL→1.25) | **6.85** | 12.55 |

For comparison, **/074's ratio is 0.247** — byte-confirmed against `/074 comparison.csv` line 2, and it is the only ratio the Section 8 classifier consumes for this iteration. NOTE: the corrected /065 (1.56) and /071 (0.68) ratios do NOT individually exceed the 3.0 SUSPICIOUS gate — their SUSPICIOUS classification fired on the OOS-DOMINANT sub-mode (OOS shift ≥ +0.20 AND IS shift < +0.10), not on the ratio gate. Only /073 (6.85) trips the ratio gate. The "monotonically escalating ratios" framing in the /073 diary used the unreconciled numbers; the corrected sequence is 1.56 → 0.68 → 6.85 (not monotone), but the qualitative finding — 3 holding-time-extension axes all classified SUSPICIOUS-OOS-DOMINANT — is unchanged and robust to the ratio correction.

**Cycle-2 action carried forward:** ONE definition of "OOS/IS ratio" is now fixed — the within-iteration `comparison.csv` `monthly_sharpe` ratio column. Future briefs, engineering reports, and diaries must use it and must not introduce alternative constructions.

## 5. Critic verdict summary

**OVERALL=MERGE** per Critic FINAL `2371324`. The MERGE verdict certifies the INERT-AT-EXPLORATION classification clean — it is a closeout-integrity / methodology certification, NOT an advancement to CONFIRMATION. /074 does NOT advance to the cycle-2 CONFIRMATION bundle.

- **8/8 Checks PASS or informational.** PBO=0.1278 PASS; `frac_positive_paths=0.6444 ≥ 0.55` PASS (independently verified: 29 of 45 CPCV paths positive); DSR (legacy) 0.0 + DSR_relative_B4 0.0715 informational-FAIL at EXPLORATION; PSR=0.9985 informational; ADF all 14 features pass at 2025-03 (the final IS month) for all 3 symbols.
- **Foundation Audit (Boot Steps 9-11) CLEAN.** Walk-forward fix intact (`train_end_ms = test_start_ms - embargo_ms`; `compute_embargo_candles(10080,480)=22`; `REQUIRED_GAP=66`). §11 anti-pattern static scan zero matches.
- **Check 1 (look-ahead) PASS — the load-bearing check.** The BTC-regime classification is past-only on TWO independent layers: Layer 1 — `_build_btc_regime_lookup` shifts both `close` and `log_ret` by `.shift(1)` before any rolling computation, so BTC bar `t`'s DD/vol-z see only `close[t-1 .. t-lookback]`; Layer 2 — `_regime_gate_fires` uses `np.searchsorted(..., side="left") - 1`, selecting the last BTC bar strictly OLDER than the symbol's bar time. Brief Section 5's disclosure that the expanding stats are full-series (not IS-only) is a deliberate conservative-OOS-estimate choice, honestly documented, not a leak.
- **Single-axis discipline confirmed** — brief Section 3 declares exactly two changes (the axis + the mandatory `V3_ATR_MULTIPLIERS_PER_SYMBOL` revert); both verified in source. `block_long_for=()` / `block_short_for=()` confirmed (primitive 10 stays reverted from /051) — no scope creep.

Adversarial questions resolved:
- **Q1 — regime classification past-only?** YES, two independent layers (Check 1).
- **Q2 — engineering report's "5.04/4.51/12.55"?** Factually wrong; flagged non-blocking; corrected ratios recorded in Section 4 above.
- **Q3 — should a near-zero-effect axis be NULL-RESULT?** No — INERT is LOCKED-criteria-correct. NULL-RESULT is strictly `regime_gate_fires total = 0`; the gate fired (3 IS + 5 OOS), so NULL-RESULT is excluded by its own definition. INERT requires shifts within noise bands AND not-SUSPICIOUS; /074 satisfies both.
- **Q4 — OOS/IS 0.247 genuine orthogonality evidence?** YES — the discriminating fact is the slightly-negative duration delta (mechanistically incompatible with regime-factor loading), not just the small headline shift.

## 6. PATH classification — INERT-AT-EXPLORATION

**INERT-AT-EXPLORATION** per brief Section 8.3 LOCKED criteria. The classifier requires (a) both shifts within the noise bands — IS Δ +0.013 ∈ ±0.10, OOS Δ +0.069 ∈ ±0.20 — and (b) SUSPICIOUS does not fire (OOS/IS ratio 0.247 < 3.0; OOS-DOMINANT sub-mode does not fire because OOS shift +0.069 < +0.20). Both satisfied.

- **NULL-RESULT ruled out** — brief Section 8.5 defines NULL-RESULT strictly as `regime_gate_fires total = 0`. The Gate Efficacy table confirms 3 IS + 5 OOS suppressions — the gate fired, so NULL-RESULT is explicitly excluded.
- **NEGATIVE ruled out** — neither shift is below its NEGATIVE threshold (IS −0.10 / OOS −0.20).
- **PROMISING ruled out** — neither shift clears its PROMISING threshold (the brief's cycle-1-style PASS bar of IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20).
- **SUSPICIOUS ruled out** — see Section 3.

The regime gate suppressed too few trades (3 IS / 5 OOS) to move headline metrics — that is the mechanism of the INERT outcome, and it is the central point the cycle-2 #5 guidance acts on (Section 9).

## 7. BASELINE_V3.md status

**UNCHANGED** — /059 stays canonical at `v0.v3-059` (IS +1.0894 / OOS +0.5791). An INERT-AT-EXPLORATION iteration does not advance to CONFIRMATION and does not update BASELINE_V3.md. **No new tag issued.**

**ONE BASELINE_V3.md edit at this closeout** (per Critic Rec #2): the regime-conditional kill switch (primitive 9) is added to the BASELINE_V3.md "Dead Ideas" section as **tested-twice-no-signal** — NEGATIVE-pre-fix at /022, INERT-post-fix at /074. The post-fix re-evaluation cleanly discharged the `feedback_v3_walkforward_lookahead_bug.md` re-eval eligibility for this axis, so it is now closed across two data points and must not be re-proposed in cycle 2 or cycle 3. The baseline metrics and anchor are NOT touched — /059 stays canonical.

## 8. Hypothesis check — pre-registered INERT mode fired

The QR brief Section 7 pre-registered **INERT at probability ≈ 35%** as the most plausible failure mode, with an explicit mechanism: the gate suppresses only a small-N set of TRX trades on the /060 roster, and if the training-distribution shift (crash-regime bars dropped from TRX's Optuna landscape) does not materially change the TRX model — plausible because TRX's 24-month training windows mostly do not include 2022-10/2023-01 — then /074 lands within the noise bands. The pre-registered metric signature was: IS+OOS Sharpe within the noise bands, TRX trade count down by only 1-5/IS and 1-8/OOS, BCH and LDO byte-identical to /060.

**Observed: every element of the INERT signature fired.** IS Δ +0.013 and OOS Δ +0.069 both inside the noise bands; TRX suppressions 3 IS / 5 OOS (within the pre-registered 1-5/IS and 1-8/OOS bands); BCH byte-identical to /060 (QE-verified 37/37). The QR calibration was accurate on both the mechanism AND the outcome — the 35%-probability mode is exactly what happened. (For completeness: the QR also pre-registered NEGATIVE at ≈25% and SUSPICIOUS-OOS-DOMINANT at ≈10% as a tail; neither fired.)

## 9. Critic Recommendations carried forward

1. **Fix the engineering-report prior-iteration ratio forensics; standardize ONE OOS/IS ratio definition.** Done in Section 4 of this diary — the corrected within-iteration `comparison.csv` ratios are /065 = 1.56, /071 = 0.68, /073 = 6.85. The canonical definition for the rest of cycle 2 (and cycle 3) is the within-iteration `comparison.csv` `monthly_sharpe` ratio column. Future briefs, engineering reports, and diaries must not introduce alternative constructions.

2. **The regime-gate axis is closed across two data points — recorded.** Primitive 9 = NEGATIVE-pre-fix /022 + INERT-post-fix /074. Added to BASELINE_V3.md "Dead Ideas" at this closeout (Section 7). Not to be re-proposed.

3. **Cycle-2 #5 should target the IS bear/chop drag directly with a holding-time-orthogonal mechanism that acts on the FULL roster.** The /074 brief's EDA PART 1 (the IS/OOS regime-stratified diagnostic limb — a genuine deliverable) localized the structural drag to the IS bear/chop sub-period: monthly Sharpe **−0.0242**, only **27.8% positive months**. The regime gate confirmed holding-time-orthogonal axes do not load the regime factor, but its kill-switch mechanism touched too few trades (3 IS / 5 OOS) to lift that drag. The next EXPLORATION must pre-register a behavioral-effect predictor estimating a MATERIALLY LARGER trade-population effect. The suggested direction: a new feature family that discriminates bear vs bull regimes WITHIN the IS window — holding-time-orthogonal by mechanism, acting on the full roster rather than a stress-bar subset.

## 10. Next Iteration Ideas

### Cycle 2 progress — 4/10 EXPLORATIONs done

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /071 | META-LABELING (same-feature M2 take/skip) | SUSPICIOUS-OOS-DOMINANT |
| #2 | /072 | ALTERNATIVE LABELING (fixed-horizon-21) | NEGATIVE |
| #3 | /073 | PER-SYMBOL LABELING (per-symbol triple-barrier asymmetry) | SUSPICIOUS-OOS-DOMINANT |
| #4 | /074 | NEW RISK PRIMITIVE (regime-conditional kill switch, primitive 9) | **INERT-AT-EXPLORATION** |
| #5 | /075 | TBD per QR EDA — see candidates below | — |
| #6-#10 | /076-/080 | TBD | — |

Cycle 2 so far has produced NO clean PROMISING. The labeling-architecture family (/071/072/073) is substantially exhausted; /074 confirmed the holding-time-orthogonal hypothesis but the kill-switch mechanism was too narrow to lift the IS drag. **The defining unresolved problem remains the IS bear/chop drag** (brief EDA PART 1: IS bear/chop monthly Sharpe −0.0242, 27.8% positive months) and the standing LDO structural weakness.

### iter-v3/075 (cycle 2 #5) axis candidates — seeding only

Per Critic Rec #3, /075 should target the IS bear/chop drag directly with a **holding-time-orthogonal mechanism that acts on the FULL roster** (not a stress-bar subset). The /075 actual axis is QR-EDA-driven and will be selected fresh in Phase 1-2 of /075 with a committed `analysis/iteration_v3-075/*.py` EDA script (`feedback_v3_axis_selection_quant_discipline.md`); the brief Section 2 must contain EDA-derived numerical tables AND a pre-registered behavioral-effect predictor estimating a materially larger trade-population effect than /074's 3-IS/5-OOS suppression. Candidates to seed the QR EDA:

1. **NEW feature family discriminating bear vs bull regimes within the IS window** (Critic Rec #3 suggested direction; HIGHEST). A regime-discriminating feature is holding-time-orthogonal by mechanism and acts on the full roster — it changes the model's predictions in bear/chop months without lengthening trade duration. Candidate constructions: a slow trend-state feature (e.g. long-window price-vs-MA sign or a smoothed Hurst-regime label), a realized-vol-regime z-score, or a BTC-dominance / BTC-trend regime feature broadcast to all 3 symbols. Must clear the engineered-feature falsifiers (importance ≥30 per `feedback_v3_engineered_feature_pivot.md`) and be tested ALONE — single-seed SAME-FAMILY stacking is forbidden per `feedback_v3_engineered_features_dont_stack.md`.
2. **A regime-conditional position-SIZE modulation acting on the full roster** (vol-target ceiling or a bear/chop exposure scalar — one of the permitted orthogonal mechanisms per `feedback_v3_concentration_is_signal.md`). Unlike the /074 binary kill switch (which touched 3 IS / 5 OOS trades), a roster-wide size scalar changes the contribution of EVERY bear/chop-month trade — addressing the "too few trades" failure mode directly. Holding-time-orthogonal: it scales exposure, not duration.
3. **A dedicated IS bear/chop sub-period diagnostic axis** — extend the brief EDA PART 1 limb into a full regime-stratified attribution: which symbols and which feature families carry / drag the IS bear/chop −0.0242 monthly Sharpe, and whether ANY candidate change lifts IS bear/chop performance without OOS-bull-only inflation. This would directly characterize the drag the cycle keeps failing to lift.

**Hard constraints on /075** (carried from prior closeouts):
- Holding-time-orthogonal — the brief Section 2 must include the holding-time-effect predictor (`feedback_v3_is_oos_regime_divergence.md`); any axis that lengthens mean/median trade duration loads the regime factor and must be rejected at brief stage.
- Pre-register the OOS/IS Sharpe ratio bound (>3.0 → SUSPICIOUS) in Section 4 per `feedback_v3_oos_is_ratio_gate.md`, using the now-canonical within-iteration `comparison.csv` ratio definition.
- Pre-register a behavioral-effect predictor with a falsifier (`feedback_v3_axis_saturation_predictor.md`) — and the predictor must estimate a MATERIALLY LARGER trade-population effect than /074's 3-IS/5-OOS, or the axis is too narrow to lift the drag.
- Per-symbol IS-axis discipline (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`) if the candidate is per-symbol.
