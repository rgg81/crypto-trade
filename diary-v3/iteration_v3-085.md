# iter-v3/085 — Cycle 3 #4 EXPLORATION — NEW funding-regime-conditioned ENGINEERED feature / SUSPICIOUS (trade-selection sub-channel)

**Date**: 2026-05-16
**Type**: EXPLORATION (cycle 3 slot #4 of 10). Single-axis: ONE Category-2 composed feature `funding_regime_momentum_5d = regime_momentum_signed_5d × sign(funding_z_30)` appended to `V3_FEATURE_COLUMNS_TOP_N` (14→15). EXPLORATION-mode 3-seed, `--n-trials 35`, 315 Optuna trials, wall-clock 0.71h.
**Axis**: Direction 1 — a NEW crypto-native ENGINEERED feature (funding-regime-conditioned momentum). QR-research-and-EDA-driven (brief Section 10: BIS WP 1087 "Crypto carry" 2025; Cakici et al. *IRFA* 94 2024 / SSRN 4295427; Gu/Kelly/Xiu NBER w25398; EDA `5264091`).
**Verdict**: EXPLORATION-MERGE per Critic FINAL `50f32be` — OVERALL=MERGE = methodology of a clean EXPLORATION certified clean (all 8 mandatory + 4 optional Checks PASS; the Critic gates methodology soundness, not advancement). The result classification is the QR's Section 8 call — and it **diverges from the Critic's preliminary result-read** (see Section 3).
**Classification**: **SUSPICIOUS** (brief Section 8.3, sub-channel (c) — the /076 trade-selection sub-channel). The LOCKED disjunctive precedence is SUSPICIOUS → NEGATIVE → PROMISING → INERT → NULL-RESULT; SUSPICIOUS fires and is canonical over the also-firing INERT importance clause.
**Advancement**: does NOT advance to the iter-v3/092 cycle-3 CONFIRMATION bundle — SUSPICIOUS axes never advance. The feature is dropped at the /086 setup.
**BASELINE_V3.md**: **UNCHANGED** — canonical /059 metrics (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791) and tag `v0.v3-059` stay canonical. An EXPLORATION cannot update the baseline regardless.
**Branch**: `iteration-v3/085`

---

## 1. What was done — the single axis

iter-v3/085 is the FOURTH EXPLORATION slot of v3 cycle 3 — the bold structural pivot governed by `briefs-v3/cycle3_plan.md`. Per `feedback_v3_strict_10_to_1_cadence.md`, cycle 3 runs 10 SEPARATE EXPLORATIONs (/082-/091) followed by 1 SEPARATE CONFIRMATION (/092); the 10th EXPLORATION is NOT collapsed into the CONFIRMATION.

The single axis: `V3_FEATURE_COLUMNS_TOP_N` grows 14 → 15 by appending exactly one Category-2 composed feature

```
funding_regime_momentum_5d  =  regime_momentum_signed_5d  ×  sign(funding_z_30)
```

— momentum sign-switched by the prevailing funding-crowding regime. The hypothesis (brief Section 1): momentum into a crowded long is exhaustion (fade), momentum into a crowded short is a squeeze setup (follow), and the depth-4 LightGBM cannot compose that funding×momentum interaction from raw inputs. Nothing else changed — no labeling change, no symbol change, no risk-gate change, no model-architecture change, no seed change. The funding-rate data feed (`data/funding_rates/`) was already built at iter-v3/019; this was a contained feature addition (`compute_funding_regime_momentum_5d` in `engineered_v3.py`), not a new fetcher. The 11-knob `_canonical_v059` config-accretion check confirmed all 11 RiskV3 knobs /059-canonical.

The QR override (Section 10 of the brief, per `feedback_v3_axis_selection_quant_discipline.md`): the orchestrator's lead candidate was a multi-symbol-pooled model (Direction 3). The /085 QR ran three IS-only EDA probes against the pooled model — `pooled_model_cross_symbol_structure.py`, `pooled_with_symbol_dummy.py`, `ldo_donor_augmentation.py` — and all three falsified it (mean cross-symbol transfer lift −0.0188; only 7/14 features sign-agree on feature→label IC across symbols; pooled+`symbol_id` breaks BCH). The pooled model was SUPERSEDED by EDA, not by orchestrator preference, and the QR committed the funding-regime engineered-feature axis instead.

## 2. Results — vs the cycle-3 EXPLORATION-MODE-REFERENCE (/084)

Per the MANDATORY two-anchor structure (Critic /084 Rec #2): the intra-cycle Δ is classified against **ANCHOR 1 — the /084 EXPLORATION-MODE-REFERENCE, IS +0.8325 / OOS +0.3322 (3-seed EXPLORATION-mode, current data)** — architecturally matched to /085's own 3-seed EXPLORATION run. **ANCHOR 2 — the /059 CONFIRMATION baseline, IS +1.0894 / OOS +0.5791 (10-seed)** — is RESERVED for the iter-v3/092 CONFIRMATION and is NOT the comparison point here.

| Metric | /084 EXPLORATION-MODE-REFERENCE | /085 (this run) | Δ /085 − /084 |
|---|---:|---:|---:|
| IS monthly Sharpe | **+0.8325** | **+0.9743** | **+0.1418** |
| OOS monthly Sharpe | **+0.3322** | **+0.2854** | **−0.0468** |
| OOS/IS monthly Sharpe ratio | 0.3990 | **0.2930** | — |
| IS daily Sharpe | 1.7115 | 2.0420 | — |
| OOS daily Sharpe | 0.8745 | 0.8768 | — |
| IS MaxDD | 31.87% | 19.30% | — |
| OOS MaxDD | 35.78% | 44.04% | — |
| IS n_trades | 159 | 168 | +9 |
| OOS n_trades | 104 | 102 | −2 |
| PBO (per-cell mean) | 0.1278 | **0.0921** | — |
| frac_positive_paths (CPCV) | 0.644 | **0.644** | 0 |
| PSR | 1.0000 | 1.0000 | — |
| DSR (legacy) | 0.0000 | 0.0000 | EXPLORATION-mode artifact |
| DSR_relative_B4 | 0.8154 | 0.8239 | EXPLORATION-mode artifact |
| n_trials (Optuna total) | 315 | 315 | — |
| n_eff | 19 | 19 | — |

CPCV path Sharpe distribution: q25 = −0.243, q50 = +0.335, q75 = +0.838. `frac_positive_paths = 0.644` clears the 0.55 Gate-10-CPCV threshold — the run is a clean, valid measurement, not a methodology failure.

**Per-symbol OOS attribution** (`comparison.csv` per_symbol block, `weighted_pnl`):

| Symbol | OOS weighted_pnl | OOS n_trades | OOS WR | OOS concentration_pct |
|---|---:|---:|---:|---:|
| TRXUSDT | +11.0717 | 53 | 41.5% | 73.28% |
| LDOUSDT | +8.2949 | 15 | 40.0% | 54.90% |
| BCHUSDT | −4.2582 | 34 | 32.4% | −28.18% |

**Per-symbol IS attribution** (`in_sample/per_symbol`, `net_pnl%`): BCH 84 trades / 42.9% WR / +52.31 (95.3% of IS PnL); TRX 74 / 35.1% / +7.21; LDO 10 / 40.0% / −4.62. BCH IS-PnL concentration at 95.3% persists — the known v3 fragility, not /085's scope.

**`funding_regime_momentum_5d` importance** (last IS month, 3-seed mean): rank **13/15 (BCH)**, **14/15 (LDO)**, **15/15 (TRX)** — portfolio rank 15/15, share ~2.9–4.1% (absolute importance 59/78/55, all >30). The IC analysis is clean: max |IC| vs the 14-anchor stack = 0.0840 (`range_realized_vol_50`); |IC| vs its own primitive `regime_momentum_signed_5d` = 0.0065 — the feature is genuinely orthogonal in IC terms, the sign-switch genuinely restructures rather than rescales. The binding gate failure is on model importance RANK, not collinearity.

## 3. PATH classification — SUSPICIOUS (trade-selection sub-channel) — and the divergence from the Critic's preliminary read

The brief Section 8 LOCKED taxonomy runs disjunctive precedence, first match canonical: **SUSPICIOUS → NEGATIVE → PROMISING → INERT → NULL-RESULT.** Anchor for all Δ: ANCHOR 1 (/084, IS +0.8325 / OOS +0.3322).

### 3.1 SUSPICIOUS (8.3) — evaluated FIRST, and it FIRES

Section 8.3 fires on ANY of three sub-channels:

- **(a) OOS/IS monthly Sharpe ratio > 3.0** — /085 ratio = 0.2854 / 0.9743 = **0.2930** → does NOT fire.
- **(b) OOS-DOMINANT sub-mode — IS Δ < 0 AND OOS Δ ≥ +0.20** — /085 IS Δ = **+0.1418 > 0** → mechanically foreclosed; does NOT fire.
- **(c) the /076 trade-selection sub-channel — the added-vs-removed OOS-roster mean-duration gap > +1.0 candle** — the brief Section 4.3 LOCKED text: "on the /084-anchor OOS roster diff, the mean trade duration of the trades /085 ADDS minus the trades it REMOVES must be ≤ +1.0 candle. If the added set skews > +1.0 candle longer-held than the removed set, the regime factor is loaded via selection → SUSPICIOUS."

**The Phase 7/8 roster-diff (the Critic-mandated check, `analysis/iteration_v3-085/roster_diff_oos.py` `b86364c`):** comparing the /085 and /084 OOS trade rosters by trade-identity key `(symbol, direction, open_time, entry_price)` — /085 has 102 OOS trades, /084 has 104; **68 are identical**, /085 **ADDS 34** and **REMOVES 36**. The added set mean duration = **6.912 candles**; the removed set mean duration = **5.333 candles**:

```
added-minus-removed OOS mean-duration gap  =  6.912 − 5.333  =  +1.578 candles
```

**+1.578 > +1.0 — the LOCKED Section 8.3(c) sub-channel falsifier FIRES.** The result is robust: re-run under three distinct trade-identity keys (`sym+dir+open+entry`, `sym+open_time`, `sym+dir+open`) the gap is +1.578 / +1.571 / +1.578 — not a key artifact.

**SUSPICIOUS therefore fires, and by the LOCKED disjunctive precedence it is canonical.** The brief pre-registered this sub-channel as a numeric falsifier with a hard +1.0 trigger. The observed +1.578 crosses it. Per the standing no-cheating discipline and the explicit memory rules against post-hoc renegotiation of LOCKED falsifiers (`feedback_v3_per_symbol_target_axis_falsifier.md`: "predictions are estimates; falsifiers are gates"), a LOCKED numeric falsifier that fires CANNOT be waved away with a mechanism argument. The classification is **SUSPICIOUS**.

### 3.2 The divergence from the Critic's preliminary read — and why the QR call stands

The Phase 7.5 Critic review's preliminary result-read was **INERT** — the Critic explicitly noted (Central Adjudication, final paragraph) that "the /076 trade-selection sub-channel is a QR Phase-7/8 roster-diff check, not yet adjudicated here — flagged for the QR." The Critic did NOT run the roster-diff; it delegated the sub-channel-(c) adjudication to this Phase 8. **This Phase 8 ran it, and the falsifier fires.** The QR's final Section 8 call therefore diverges from the Critic's preliminary read: the verdict is **SUSPICIOUS**, not INERT. This is not a contradiction of the Critic — the Critic's OVERALL=EXPLORATION-MERGE (methodology certification) stands fully, and the Critic explicitly assigned this check to the QR; the divergence is the QR completing the delegated work and the data landing on the SUSPICIOUS side of a LOCKED gate.

### 3.3 The substantive texture — for the record (does NOT overturn the LOCKED-falsifier call)

The classification is SUSPICIOUS on the LOCKED gate. For honest completeness, the substantive forensics show this is the *mild* form of the /076 pattern, not the full one:

- **The OOS effect direction is wrong for full regime-loading.** The /076 SUSPICIOUS mechanism loads the OOS regime factor and pushes OOS Sharpe UP (the /076 / /082 signature: IS flat-or-down, OOS soars). /085's OOS Sharpe went **DOWN** (Δ −0.0468) and the OOS/IS ratio is **0.293** (a regime-loaded roster shows an ELEVATED ratio). The net OOS wpnl from the roster swap is only +1.515 (added set +13.42, removed set +11.91).
- **The duration gap is not uniform across symbols.** Per-symbol OOS dur-gap: BCH **+3.44**, LDO **+3.67**, TRX **−1.42**. TRX — the dominant OOS positive-PnL symbol (53 trades, +11.07 wpnl) — shows a NEGATIVE dur-gap. LDO's +3.67 is on only 6 added / 3 removed trades (LDO has 15 OOS trades total — small-n). The aggregate +1.578 is pulled up by BCH (a net OOS detractor at −4.26) and a tiny-n LDO set.
- **The added set's PnL is not concentrated in the long-held trades in the regime-loading way.** Added winners: 11 trades, mean dur 9.73, +62.02 wpnl; added losers: 23 trades, mean dur 5.57, −48.60 wpnl — the long-held added trades carry both the wins and a wide loss spread; this is dispersion, not a clean long-held-trades-ride-the-uptrend signature.

This texture is recorded so the closeout is honest: /085 is a *partial / mild* trade-selection SUSPICIOUS, not the textbook /076 case. **But the LOCKED falsifier is a numeric gate, and +1.578 > +1.0 — the classification is SUSPICIOUS regardless of the texture.** Allowing the texture to downgrade SUSPICIOUS → INERT would be exactly the post-hoc LOCKED-falsifier renegotiation the memory rules forbid. SUSPICIOUS stands as the FINAL classification.

### 3.4 The other taxonomy branches (foreclosed, for completeness)

- **NEGATIVE (8.2)** does NOT fire: IS Δ +0.1418 ≥ −0.10 AND OOS Δ −0.0468 ≥ −0.20.
- **PROMISING (8.1)** is mechanically foreclosed on TWO independent terms: (i) SUSPICIOUS fires and 8.1 explicitly requires NOT SUSPICIOUS; (ii) the binding Category-2 importance gate (rank ≤ 10/15 AND absolute importance ≥ 30 on ≥ 1 symbol) FAILS the rank leg on all three symbols — no symbol clears rank ≤ 10 (BCH 13, LDO 14, TRX 15).
- **INERT (8.4)** — the importance clause "rank ≥ 14/15 across ≥ 2/3 symbols" DOES fire (LDO 14, TRX 15) — but INERT is *behind* SUSPICIOUS in the disjunctive precedence and is therefore not the canonical classification. Had sub-channel (c) not fired, /085 would have been INERT; it did fire, so SUSPICIOUS is canonical.
- **NULL-RESULT (8.5)** does NOT fire: the /085 OOS roster is NOT bit-identical to /084's (68 common of 102/104; 34 added, 36 removed).

### 3.5 The +0.142 IS lift is an Optuna-search-perturbation artifact, NOT signal

The +0.1418 IS monthly Sharpe lift vs the /084 anchor is real in the metrics but is **NOT attributable to `funding_regime_momentum_5d` as signal.** A feature ranked 13/14/15-of-15 by importance on all three symbols cannot have *produced* +0.142 of IS Sharpe — an effectively-unused 15th column has no path to the objective except via the search-space-perturbation side channel. This is the documented `feedback_v3_inert_features_at_higher_budget.md` mechanism: adding a 15th column expands the Optuna hyperparameter search space, and at 3-seed single-lineage EXPLORATION resolution the perturbed search lands a different (here favorable) IS hyperparameter draw. The brief pre-registered exactly this (Section 7, PROMISING-INERT at ≈45%): the T3 quick-probe had already ranked the feature 14.0/15 mean with −0.0016 mean accuracy lift. The +0.142 IS lift is an artifact of an unused column, not a funding×momentum edge discovery. (This is also why SUSPICIOUS, not PROMISING, is the honest read of the +0.142: the IS lift is an Optuna artifact AND the roster swap that produced it is duration-loaded past the +1.0 sub-channel gate.)

## 4. Section 7 prediction check — INERT/SUSPICIOUS both inside the pre-registered set

The brief Section 7 pre-registered the failure-mode distribution: **≈45% PROMISING-INERT, ≈20% SUSPICIOUS (SUSPICIOUS-OOS-DOMINANT), ≈15% NEGATIVE, ≈20% PROMISING.** The realized classification is **SUSPICIOUS** — via the trade-selection sub-channel (c), not the OOS-DOMINANT sub-mode (b) the brief named under its ≈20% SUSPICIOUS bucket. Two honest readings, both recorded:

- The realized outcome IS inside the pre-registered set — SUSPICIOUS was pre-registered at ≈20%, and the brief's Section 8.3 LOCKED taxonomy explicitly enumerated sub-channel (c) as one of the three SUSPICIOUS triggers. The classification did not land outside what was pre-registered.
- BUT the brief's Section 7 *prose* tied its ≈20% SUSPICIOUS estimate specifically to the OOS-DOMINANT sub-mode (the /082 mechanism) and named PROMISING-INERT (≈45%) as the single most-likely outcome. The realized SUSPICIOUS fired on a *different* sub-channel than the prose anticipated. Calibration verdict: **the taxonomy was complete (sub-channel (c) was a LOCKED trigger, correctly enumerated) but the Section 7 prose under-weighted the trade-selection sub-channel** — it treated (c) as a tail and leaned the narrative on INERT. The pre-registered INERT importance clause ALSO fired (LDO 14 / TRX 15), so the brief's central INERT forecast was directionally correct on the importance evidence; it was the duration-loading of the roster swap that the prose did not foresee. Recorded for /086+ brief calibration: when a feature is expected INERT-by-importance, the Section 7 prose must still give the trade-selection SUSPICIOUS sub-channel a non-tail weight — an INERT-by-importance feature that nonetheless perturbs the Optuna search can shift the roster toward longer-held trades, which is precisely sub-channel (c).

## 5. Critic integration — OVERALL=EXPLORATION-MERGE + 4 Recommendations

**Critic FINAL `50f32be`** (`briefs-v3/iteration_v3-085/review.md`): a single-round full review, OVERALL=**EXPLORATION-MERGE**. The MERGE verdict CERTIFIES the methodology of a clean EXPLORATION — it is a methodology certification, NOT an advancement or an edge endorsement.

- **All 8 mandatory Checks + 4 optional Checks PASS.** Check 1 (look-ahead) PASS — `compute_funding_regime_momentum_5d` traced through all three legs; `funding_z_30` uses `funding_rate.shift(1)` before the 30-bar rolling window so bar t's own settlement never enters its own z-score; the mandated spike-perturbation test (`test_funding_regime_momentum_v3.py::test_past_only_no_lookahead`, perturb `funding_rate[250]`, assert all bars <250 bit-identical) verified independently. Check 2 (embargo) PASS — `REQUIRED_GAP = (21+1)×3 = 66`, `PER_CELL_GAP = 22` (the corrected /084 value), both with self-asserting `expected_gap` guards. Check 3 (multiple-testing) — per-cell PBO 0.0921 < 0.40 PASS; `frac_positive_paths` 0.6444 ≥ 0.55 PASS; DSR/PSR informational at EXPLORATION mode per `feedback_v3_dsr_mode_artifact.md`. Check 4 (IC) PASS — max |IC| 0.0840, far below the 0.50 strict target. Check 5 (ADF) PASS — `funding_regime_momentum_5d` strongly I(0) (ADF −8.47/−12.43/−8.12). Check 6 (Gate-10-CPCV) PASS. Check 7 (reproducibility) PASS — explicit 15-element `feature_columns`, 3-tuple `ENSEMBLE_SEEDS` literal, 5-row OOS trade-PnL spot-check reconciles. Check 8 (hypothesis-implementation alignment) PASS — exactly one axis, zero scope creep, the 4 closed `funding_family` columns asserted ABSENT. Checks 9-12 all PASS.
- **Central Adjudication — INERT-by-importance.** The Critic's forensic input: `funding_regime_momentum_5d` is INERT-by-importance (rank 13/14/15-of-15), the PROMISING binding gate fails the rank leg on all three symbols, the +0.142 IS lift is the `feedback_v3_inert_features_at_higher_budget.md` Optuna-perturbation artifact. The Critic's preliminary classification call was INERT — explicitly delegating the sub-channel-(c) roster-diff to this Phase 8. **This Phase 8 ran the delegated roster-diff; sub-channel (c) fires; the FINAL classification is SUSPICIOUS** (Section 3 above). The Critic's INERT-by-importance forensics are not contradicted — they are the reason the +0.142 IS lift is not signal — but the LOCKED disjunctive precedence places the firing SUSPICIOUS sub-channel above the firing INERT clause.
- **Four Critic Recommendations — all integrated:**
  1. **Drop `funding_regime_momentum_5d` at the /086 setup + add the runner ABSENT ban.** RECORDED as a MANDATORY iter-v3/086-setup action (Section 6) — revert `V3_FEATURE_COLUMNS_TOP_N` to the 14-feature /059 anchor and add `funding_regime_momentum_5d` to the runner's pre-flight ABSENT-assertion list (the established `vol_normalized_ret_5d` / `range_efficiency_50` pattern). Per `feedback_v3_inert_features_at_higher_budget.md` an INERT feature is not carried forward and not retested at higher budget.
  2. **Confirm the per-cell-PBO aggregation in the diary.** DONE (Section 7) — the Critic's flat 127-row mean came to ≈0.102 by hand-arithmetic; the runner's "iter-v3/004 cross-cell mean" IS a flat mean and reproduces the reported 0.0921 EXACTLY when recomputed programmatically. The number is traceable; the verdict is unaffected (both <0.40).
  3. **Clean up the stale `validation_v3.py:594` docstring.** RECORDED as a /086-setup cleanup (Section 6) — the CPCV-iterator docstring still says "gap=88 4-symbol BCH+LDO+TRX+ADA" (leftover from the reverted /069); the live constant is correctly 66. Cosmetic; fix it before it misleads.
  4. **For /086, pivot away from feature constructions on existing OHLCV/funding data.** RECORDED as the /086 axis directive (Section 8) — cycle 3 is 4/10 with 0 clean PROMISING; the highest-value untried structural axes are a NEW crypto-native data feed (OI / basis / liquidations — a real Phase-6 fetcher build) or a re-thought universe/architecture axis. A fifth consecutive feature-construction EXPLORATION on the same 3-symbol parquets risks the cycle-1/cycle-2 null-result pattern.

## 6. The v3 funding axis is now a 5-data-point CLOSED verdict + the /086-setup mandates

### 6.1 The funding axis — CLOSED across BOTH constructions, 5 data points

iter-v3/085 is the **fifth** EXPLORATION data point on the v3 funding axis, and it closes the axis across BOTH construction families:

- **/019, /023, /024 — funding-as-direct-feature (Category-1 z-scores).** `funding_rate_zscore_30` (/019, /023) and `btc_funding_rate_zscore_30` (/024) — three single-z-score attempts, all INERT-by-importance (the model never split on raw funding).
- **/082 — funding-as-direct-feature (the 4-channel family).** `funding_sign_persist_9` / `funding_momentum_3` / `funding_accel_3` / `funding_price_divergence_6` — a literature-grounded 4-channel direct family; ranked 15/16/17/18 of 18 by importance, SUSPICIOUS-OOS-DOMINANT.
- **/085 — funding-as-regime-conditioner (the Category-2 composed sign-switch).** `funding_regime_momentum_5d` — the explicitly DIFFERENT construction (funding enters only as a `sign()` switch inside a composed feature, never as a splittable column). The Phase 5.5 gate's funding-differentiation adjudication was legitimate — the construction IS structurally distinct, and running the EXPLORATION to test it was correct. But the RESULT reproduced the INERT-by-importance pattern (rank 13/14/15-of-15) AND the roster swap loaded the trade-selection regime factor (SUSPICIOUS sub-channel (c)).

**Across two structurally orthogonal constructions — direct-feature (/019/023/024/082) and composed-sign-switch (/085) — the v3 LightGBM declines to allocate ranked importance to funding-derived information on the BCH/LDO/TRX universe.** The v3 funding axis is a **5-data-point CLOSED verdict**, now closed in ALL feature constructions on the funding rate. Future "funding" axes require a fundamentally different VEHICLE — a new data feed (open interest / basis / liquidations) or a non-tree model that can compose the interaction differently — NOT another feature construction on the same funding rate. This is recorded in BASELINE_V3.md Dead Ideas.

### 6.2 MANDATORY iter-v3/086-setup actions (Critic Recs #1 and #3)

1. **(Rec #1) Drop `funding_regime_momentum_5d` + add the runner ABSENT ban.** The /086 setup MUST: (a) revert `V3_FEATURE_COLUMNS_TOP_N` to the 14-feature /059 anchor stack (drop `funding_regime_momentum_5d`, count 15→14); (b) add `funding_regime_momentum_5d` to the runner's pre-flight ABSENT-assertion list, the established `vol_normalized_ret_5d` / `range_efficiency_50` pattern, so a future iteration cannot silently re-inherit it; (c) the `funding_regime_momentum_5d` literal name joins the runner-banned set. Per `feedback_v3_inert_features_at_higher_budget.md` — an INERT feature is not carried forward and not retested at a higher Optuna budget. (SUSPICIOUS reinforces this — the feature both fails importance AND loads the trade-selection regime factor.)
2. **(Rec #3) Fix the stale `validation_v3.py:594` docstring.** The CPCV-iterator docstring at `src/crypto_trade/strategies/ml/validation_v3.py:594` still reads "Default gap = REQUIRED_GAP = (timeout_candles+1)*n_symbols = 88 (4-symbol BCH+LDO+TRX+ADA universe; iter-v3/069 UNIVERSE EXPANSION...)" — a leftover from the reverted /069 4-symbol era. The live `REQUIRED_GAP` constant is correctly **66**; the `_canonical_v059` check and the `expected_gap` self-assertion guard it, so the run is sound. Fix the docstring to the live 66 = (21+1)×3 at the /086 setup (the next runner-touching iteration).

## 7. The per-cell-PBO aggregation is traceable — the reported 0.0921 reproduces EXACTLY (Critic Rec #2)

The Critic flagged that an independent flat mean of the 127 `per_cell_pbo.csv` rows came to ≈0.102 against the reported `dsr.json` PBO of 0.0921, and asked the diary to state the exact aggregation convention.

**Resolution: the reported 0.0921 IS a flat 127-row mean, and it reproduces EXACTLY.** `dsr.json`'s `pbo_note` cites an "iter-v3/004 cross-cell mean" — and that convention is, in fact, a flat (unweighted, un-subsetted) arithmetic mean of the per-cell `pbo` column. Recomputing programmatically (`analysis/iteration_v3-085/roster_diff_oos.py` `b86364c`, the per-cell-PBO block): `per_cell_pbo.csv` has **127 rows** with a `pbo` column; the flat mean of those 127 values = **0.09211**, which matches `dsr.json`'s reported PBO **0.0921** to 4 decimals. The Critic's ≈0.102 was hand-arithmetic error over 127 floats — flat-mean reproduction by code is exact. The aggregation convention is: flat unweighted mean of the `pbo` column across all `(symbol, train_month)` cells, no n_candles weighting, no subsetting. The verdict is unaffected — 0.0921 clears the 0.40 PBO threshold with a wide margin, and `frac_positive_paths` 0.6444 (the binding v3 CPCV gate) PASSES. The number is now traceable.

## 8. Decision — NO-MERGE

**NO-MERGE. BASELINE_V3.md is UNCHANGED — canonical /059 metrics (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791) and tag `v0.v3-059` stay canonical. The /084 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.3322, 3-seed) stays the cycle-3 intra-cycle anchor.**

iter-v3/085 classified **SUSPICIOUS** (trade-selection sub-channel (c) — the added-vs-removed OOS-roster mean-duration gap +1.578 > +1.0). SUSPICIOUS axes never advance to the CONFIRMATION bundle, and an EXPLORATION cannot update the baseline regardless. `funding_regime_momentum_5d` is dropped at the /086 setup per Critic Rec #1. **No new git tag for a baseline update.** An EXPLORATION closeout marker tag `v0.v3-085` is issued (annotated; explicitly NOT a baseline update — the same pattern as `v0.v3-082` / `v0.v3-083` / `v0.v3-084`).

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are untouched. `V3_MODELS` stays the 3-symbol BCH/LDO/TRX /059-canonical universe. `PER_CELL_GAP` stays corrected at 22.

## 9. Cycle-3 progress + Next Iteration

### Cycle 3 progress — 4/10 EXPLORATION slots done, 0 clean PROMISING

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /082 | NEW crypto-native FEATURE FAMILY (funding-rate 4-channel, Direction 1) | SUSPICIOUS-OOS-DOMINANT |
| #2 | /083 | symbol-universe EXPANSION 3→4 (+FILUSDT, Direction 2) | NEGATIVE |
| #3 | /084 | REFERENCE / METHODOLOGY — PER_CELL_GAP 43→22 fix + clean /059-config 3-symbol anchor re-run | REFERENCE-REANCHOR |
| #4 | /085 | NEW funding-regime-conditioned ENGINEERED feature (Category-2 composed, Direction 1) | **SUSPICIOUS** (trade-selection sub-channel) |
| #5-#10 | /086-/091 | TBD per QR research + EDA, Directions 1-3 | — |
| CONFIRMATION | /092 | best cycle-3 bundle (multi-seed validation) | pre-registered MERGE gates |

Cycle 3 has used 4 of its 10 EXPLORATION slots — outcome distribution so far: 1 SUSPICIOUS-OOS-DOMINANT, 1 NEGATIVE, 1 REFERENCE-REANCHOR, 1 SUSPICIOUS — **0 clean PROMISING.** The pattern matches cycles 1 and 2 (each 0 clean PROMISING) and is now reinforced: /082 (funding 4-channel) and /085 (funding composed sign-switch) prove no feature construction on the existing OHLCV/funding data finds a v3 edge ingredient.

### iter-v3/086 — what it should be

**iter-v3/086 (cycle 3 #5) should be a NEW crypto-native data feed (open interest / basis / liquidations — a real Phase-6 fetcher build) OR a re-thought universe/architecture axis — NOT another feature construction on the existing OHLCV/funding parquets** (Critic Rec #4). The case is structural and now dispositive: /082 and /085 both proved that feature constructions on the funding rate are INERT-by-importance at v3's per-symbol scale + EXPLORATION budget; the v3 funding axis is CLOSED across both construction families (5 data points). The highest-value untried structural axes are (a) a NEW crypto-native data feed — open-interest delta, perp-spot basis, or liquidation-cascade features — which is a genuine Phase-6 engineering build (a new fetcher, a new `features_v3/` extension, a documented look-ahead lag), and (b) the cycle-3 plan's Direction 2 (symbol-universe EXPANSION — denominator expansion) or Direction 3 (multi-symbol-pooled model), which directly attack the BCH ~95% IS-concentration / 3-symbol-denominator fragility that makes every v3 OOS number fragile. Per `feedback_v3_axis_selection_quant_discipline.md` + the cycle-3 research mandate, the /086 QR must do genuine WebSearch/WebFetch literature research, commit an `analysis/iteration_v3-086/*.py` IS-EDA script before the brief, and state BOTH anchors in brief Section 4 (the /084 EXPLORATION-MODE-REFERENCE IS +0.8325 / OOS +0.3322 for intra-cycle Δ; the /059 CONFIRMATION baseline IS +1.0894 / OOS +0.5791 reserved for /092).

**Hard constraints on /086** (carried from prior closeouts + the /085 Critic):
- /086 setup MUST drop `funding_regime_momentum_5d` (revert `V3_FEATURE_COLUMNS_TOP_N` 15→14) and add it to the runner ABSENT-assertion list (Critic /085 Rec #1).
- /086 setup MUST fix the stale `validation_v3.py:594` docstring (88 4-symbol → 66 3-symbol) (Critic /085 Rec #3).
- Anchor intra-cycle Δ against the /084 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.3322, 3-seed); reserve the /059 CONFIRMATION baseline (IS +1.0894 / OOS +0.5791, 10-seed) for /092. State BOTH anchors explicitly in brief Section 4 — the two-anchor structure is MANDATORY.
- Pre-register the OOS/IS Sharpe ratio bound (> 3.0 → SUSPICIOUS), the OOS-DOMINANT sub-mode, AND the /076 trade-selection sub-channel (added-vs-removed OOS-roster mean-duration gap > +1.0 → SUSPICIOUS) in Section 4/8. The /085 outcome shows the trade-selection sub-channel is NOT a tail — give it a non-tail weight in the Section 7 prose.
- Pre-register the holding-time / roster-composition predictor per `feedback_v3_is_oos_regime_divergence.md`.
- Genuine WebSearch/WebFetch literature research in Phases 1-4, documented in brief Section 10.
- `V3_MODELS` is BCH/LDO/TRX at the /086 starting point; `PER_CELL_GAP` stays corrected at 22. Per-cell PBO comparisons across the /084 boundary are gap-regime-discontinuous (Critic /084 Rec #3).
- CLOSED — do not re-propose: the v3 funding axis (now 5 data points /019/023/024/082/085 — CLOSED across both direct-feature and composed-sign-switch constructions); the Kaufman path-efficiency axis (`efficiency_ratio_50` / `range_efficiency_50`); the regime-conditional kill switch (primitive 9); the LDO→ADA universe swap; per-symbol PnL-share caps; the naive multi-symbol-pooled model (EDA-falsified at /085 Section 2.0 — only 7/14 features sign-agree across symbols); HBAR/AVAX (CLOSED at /021), ADA (CLOSED at /078), FILUSDT (CLOSED at /083) as universe-expansion candidates; gate-threshold knobs, ATR-multiplier tweaks, labeling tweaks on the same 14 features, instrumentation-only axes (all cycle-3 Section-1 CLOSED families).

---

**Commit chain:**
- EDA SHA: `5264091` — `analysis/iteration_v3-085/{pooled_model_cross_symbol_structure,pooled_with_symbol_dummy,ldo_donor_augmentation,funding_regime_engineered_feature}.py`
- Brief SHA: `2bc25d1` (LOCKED); brief SHA-backfill `ec6c353`; brief Section 10 EDA-SHA backfill `0b8b250`
- Setup SHA: `ae38f1e` — `setup(iter-v3/085): funding_regime_momentum_5d composed feature + ITERATION_LABEL v3-085`
- Phase 5.5 gate SHA: `0a67b71` (PASS — QR-driven funding-differentiation analysis certified)
- Engineering report SHA: `d1f8b36`; engineering report follow-up `2908caf`
- Critic FINAL SHA: `50f32be` (OVERALL=EXPLORATION-MERGE)
- Phase 8 roster-diff analysis SHA: `b86364c` — `analysis/iteration_v3-085/roster_diff_oos.py` (the Critic-mandated sub-channel-(c) check + the per-cell-PBO aggregation reproduction)
- Diary + catalog + cycle3_plan + BASELINE_V3.md Dead-Ideas SHA: `894ab8e` (this closeout; SHA backfilled by the immediately-following commit)
**Reports**: `reports-v3/iteration_v3-085/`
**Tag**: `v0.v3-085` (EXPLORATION closeout marker; NOT a baseline update — BASELINE_V3.md UNCHANGED at `v0.v3-059`)
