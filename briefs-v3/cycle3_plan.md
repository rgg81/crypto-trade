# v3 Cycle 3 Plan — iter-v3/082-091 (10 EXPLORATIONs) + iter-v3/092 CONFIRMATION

**Date**: 2026-05-16 (authored at the iter-v3/081 cycle-2 CONFIRMATION closeout)
**Author**: QR (autopilot)
**Supersedes**: the prior `cycle3_plan.md` dated 2026-05-09 (an obsolete plan written under the pre-RE-ANCHOR iter-v3/040-050 cycle numbering — fully superseded)
**Anchor**: BASELINE_V3.md UNCHANGED at iter-v3/059 — `v0.v3-059`, **IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791** (the BASELINE_V3.md / CONFIRMATION anchor). iter-v3/081 freshly RE-VALIDATED this config at unified-10-seed CONFIRMATION rigor: IS +1.0894 (exact) / OOS +0.5999 — the canonical baseline is confirmed live and pristine.
**Cycle structure**: cycle 3 = 10 SEPARATE EXPLORATIONs (iter-v3/082-091) + 1 SEPARATE CONFIRMATION (iter-v3/092), per the strict 10:1 cadence (`feedback_v3_strict_10_to_1_cadence.md`). The 10th EXPLORATION (/091) is NOT collapsed into /092.

---

## 1. The Mandate — cycle 3 is a step-change in ambition

This plan is governed by two user directives:

- **`feedback_v3_bold_research_mandate.md`** (user directive 2026-05-16, verbatim): *"do not stop by any means. Be creative, there are so many symbols and possibilities, be bold, ask the QR to research, and force him to do his job best way possible."*
- **`feedback_v3_mass_feature_expansion.md`** — research papers / internet / domain literature to identify production-grade quant features; v3's 14-feature stack is undersized vs production-grade systems that run 50-200+ features.

**The evidence that forces a pivot.** Cycle 2 produced **0 clean PROMISING across all 10 EXPLORATIONs** (4 SUSPICIOUS-OOS-DOMINANT, 1 NEGATIVE, 3 INERT, 2 NULL-RESULT). Cycle 1 produced the identical outcome — a /070 CONFIRMATION that was a NO-MERGE re-validation because no cycle-1 EXPLORATION reached the bundle-grade bar. Two full cycles, 20 EXPLORATIONs, 0 edge ingredients. The conclusion is dispositive: **the conservative axis families — gate-threshold knobs, risk primitives, single-symbol swaps, labeling tweaks, instrumentation — are EXHAUSTED against the narrow 3-symbol BCH/LDO/TRX universe.** A narrow universe + incremental axes will not find an edge.

**Cycle 3 axis-family CLOSURE (binding).** The following families are CLOSED for cycle 3 — no cycle-3 EXPLORATION may pick an axis in these families:

| CLOSED family | Why | Evidence |
|---|---|---|
| Gate-threshold knobs (ADX, z-score OOD, BTC-trend band, vol-scale ceiling/floor, confidence threshold floor) | Saturated | `feedback_axis_saturation_predictor.md`; cycle-1 /066/067, cycle-2 /074/075 all INERT; ADX axis closed at `feedback_v3_adx_axis_asymmetric_v3.md` |
| ATR-multiplier labeling knobs (tighten or widen) | Dead axis | /065 widening + /042 tightening both failed; `project_v3_cycle1_outcome.md` |
| Risk primitives (kill switches, position-size de-rates, drawdown brakes, conviction de-rates) | Most-tried-least-productive cycle-2 category — 2 INERT + 1 NULL-RESULT | cycle-2 /074, /075, /079 |
| Single-symbol swaps / universe revision *by replacement* (swap one symbol for another within a 3-symbol universe) | Loads the regime factor via the added symbol's roster | /078 SUSPICIOUS-OOS-DOMINANT; `feedback_v3_is_oos_regime_divergence.md` extension |
| Labeling tweaks (fixed-horizon, per-symbol triple-barrier asymmetry, meta-labeling on the same 14 features) | Exhausted | cycle-2 /071, /072, /073 |
| Instrumentation / passive-diagnostic axes | Produce no edge ingredient by construction | cycle-2 /077, /080 |

Boldness is in the **axis design and the research depth** — NOT in bypassing the workflow. All standing cadence, no-cheating, sacred-constant, and merge-gate rules hold in full.

## 2. The Research Mandate — every cycle-3 QR must do genuine literature research

**This is the defining process change for cycle 3.** Every cycle-3 EXPLORATION QR (starting iter-v3/082) MUST, in Phases 1-4, do genuine **WebSearch / WebFetch research** into quant-finance papers, domain literature, and crypto-native alpha sources. EDA on the existing 3-symbol parquets alone is no longer sufficient — it is the activity that produced two cycles of null results.

Concretely, each cycle-3 QR must:

1. **Research before EDA.** Use WebSearch/WebFetch to survey the current literature on the axis family the QR is pursuing (see Section 3 priority axes). Funding-rate microstructure, OI dynamics, basis/premium, liquidation-cascade modeling, on-chain flow, and crypto-universe construction all have a real 2023-2025 research literature. The companion reference `references/crypto-edge-deep.md` is a starting index, not a substitute for fresh research.
2. **Document the research path in brief Section 10 (QR Audit Trail)** — papers consulted (with arXiv/SSRN IDs or DOIs where available), the specific finding each contributes, and the selection criteria that took the QR from "literature says X" to "the iter-v3/0NN axis is Y."
3. **Ground Section 2 (IS-only numerical evidence) in committed analysis** — per `feedback_v3_axis_selection_quant_discipline.md`, the axis must be QR-EDA-driven with a committed `analysis/iteration_v3-0NN/*.py` script producing numerical tables BEFORE the brief. Research motivates the axis; EDA on IS data validates it is worth a backtest slot.
4. **Reject incremental knob-tweaks at the brief stage.** If a proposed axis is in a Section-1 CLOSED family, the Phase 5.5 gate BLOCKS it. The orchestrator must push the QR hard in every dispatch — demand depth and ambition, reject the conservative reflex.

The orchestrator's `quant-researcher` agent has WebSearch and WebFetch tools. Use them.

## 3. Priority Axes for Cycle 3 — three directions (QR EDA-picks the specific axis each iteration)

Cycle 3 has THREE priority directions. Each cycle-3 QR selects the specific axis for its iteration via genuine research + IS EDA, within one of these directions. This plan sets direction and priority — it deliberately does NOT pre-prescribe all 10 axes (per `feedback_v3_axis_selection_quant_discipline.md`, axis selection is QR-EDA-driven, not orchestrator-pre-committed).

### Direction 1 (HIGHEST) — NEW crypto-native feature families, researched from literature

v3's 14-feature `V3_FEATURE_COLUMNS_TOP_N` stack is entirely price/return/volatility/regime features computed from OHLCV. It contains **zero crypto-native alpha sources**. This is the single largest structural gap. Crypto markets generate edge sources that do not exist in equities — and the v3 8h candle cadence is uniquely well-suited to capture them (an 8h candle is exactly one funding-settlement period on Binance/OKX/Bybit).

Feature families to research and bring into v3 (the QR EDA-picks which, and the specific feature construction, per iteration):

- **Funding-rate term structure and regimes** — funding settles every 8h; persistent funding regimes encode positioning crowding. Raw rate, 8/24/72h funding momentum, funding z-score (rolling), premium index. Per BIS WP 1087 (2025), a carry shock predicts a liquidation jump — the most actionable empirical result for a crypto futures bot. (Note: cycle-1 /019/023/024 tried a single `funding_rate_zscore_30` feature and it was INERT — but that was ONE feature added by univariate rank at n_trials=10/35; a researched funding *family* with proper construction is a different axis. The QR must address why this attempt differs.)
- **Open-interest dynamics** — OI delta as a leverage-stretch signal: 8h OI delta, OI/MarketCap, venue-concentration, cross-OI correlation. Rising OI + flat price = stealth leverage build.
- **Basis / perp-spot premium** — mark-vs-index, cross-exchange basis, 8h basis delta, basis z-score. The premium index trades faster than the funding clamp.
- **Liquidation cascades** — self-exciting via stop-loss/liquidation-price chaining (Hawkes-process structure); liquidation count/notional by side over 1/4/8/24h windows, cluster booleans, long/short asymmetry.
- **On-chain flow** (BTC/ETH, used as a cross-asset regime input for the alt-symbols) — Exchange Whale Ratio, MVRV-Z, NUPL/SOPR. Lag ≥1 candle behind block-publication time.

Per `feedback_v3_mass_feature_expansion.md`, **mass feature expansion toward the 50-100 feature target is in scope** — but per that memory's AMENDMENT 2026-05-14, mass expansion is structurally inadequate at single-seed EXPLORATION (iter-v3/063 falsified 14→46 features at single-seed: IS Sharpe collapsed to NEGATIVE). The cycle-3 methodology for mass expansion: either **phased single-feature-family EXPLORATIONs** at single-seed (add a researched 3-5-feature crypto-native family at a time, validated as a family), OR **full mass expansion attempted only at the /092 CONFIRMATION** in multi-seed mode with n_trials ≥ 100. The cycle-3 QRs should favor phased crypto-native-family additions across the EXPLORATION slots; /092 may attempt the full mass-expansion bundle.

**Engineering note (cycle-3 prerequisite):** the crypto-native families above require data feeds v3 does not currently fetch (funding rate, open interest, basis, liquidations). The first cycle-3 EXPLORATION that pursues Direction 1 must include, in its brief, the data-acquisition plan — which feed, which endpoint, the look-ahead lag, and the `features_v3/` extension. This is a real engineering cost and a legitimate one; it is the structural investment cycle 3 exists to make.

### Direction 2 (HIGH) — Symbol-universe EXPANSION

v3 has been LOCKED to BCH/LDO/TRX for the **entirety of cycles 1 AND 2** — every one of 20+ iterations. This is a structural fragility, not a setting:

- The /078 finding: BCH dominates **~77% of IS wpnl**. A positive-edge change to any non-BCH symbol washes against BCH's dominance of the aggregate. The 3-symbol universe makes the portfolio a near-single-symbol bet.
- LDO directional weakness (OOS WR 25.0%) is unresolved — and a 3-symbol universe gives no room to dilute it.

**Universe EXPANSION** — adding symbols to grow the denominator — is the structural fix for both. It is distinct from the CLOSED "universe revision by replacement" family (/078 swapped LDO→ADA within a 3-symbol universe and loaded the regime factor via the added symbol's roster). Expansion grows the count; it is denominator expansion, the orthogonal mechanism.

The allowed universe is wide. v3's `V3_EXCLUDED_SYMBOLS` excludes only the v1/v2 symbols (BTC, ETH, LINK, LTC, DOT, SOL, XRP, DOGE, NEAR, BNB) plus MKR. **Dozens of liquid Binance-futures symbols are available.** The cycle-3 QR pursuing Direction 2 must:

1. Research the candidate-symbol set — liquidity, listing date (drop the first 30-60 days of any newly-listed symbol per the crypto non-stationarity pitfall), data depth, and whether the symbol has a genuine independent edge signal.
2. **Screen candidates on a genuine IS-edge screen, not feature-space distance alone.** Prior universe expansions failed precisely here: /021 (HBAR+AVAX) and /069 (ADA) used feature-space-distance / price-correlation screens that captured price diversity, not signal diversity. The cycle-3 screen must measure per-symbol IS edge AND portfolio-aggregate IS-Sharpe contribution under BCH dominance (the /078 lesson: a per-symbol Sharpe screen does not transfer to portfolio-aggregate Sharpe lift).
3. Pre-register the holding-time / roster-composition predictor per `feedback_v3_is_oos_regime_divergence.md` — an added symbol whose roster is duration-loaded relative to the existing universe loads the regime factor.

A larger universe (5-8 symbols) directly dilutes BCH concentration and gives the portfolio genuine breadth — the Fundamental Law (IR = IC × √breadth) says breadth is the lever v3 has never pulled.

### Direction 3 (MEDIUM) — NEW model architectures / multi-symbol-pooled models

v3 runs one independent LightGBM model per symbol. Two structural alternatives worth a cycle-3 EXPLORATION slot:

- **Multi-symbol-pooled model** — a single model trained on the pooled cross-section of all universe symbols (the v1 Model A precedent: BTC+ETH pooled). Pooling shares statistical strength across symbols and is the natural architecture for a *larger* universe (Direction 2) — a pooled model over 6-8 symbols has far more training data per fit than 6-8 thin per-symbol models. Pooling requires scale-invariant features (the project convention) — which the crypto-native families of Direction 1 (z-scores, ratios) satisfy.
- **NEW model architecture** — cycle-1 /016 closed a LightGBM→XGBoost head-to-head, but only at `n_trials=10 + cross-entropy + depth-wise defaults`; it was explicitly NOT closed for all configs. A cycle-3 retest would need a genuine structural rationale (a Sharpe-objective Optuna, a different growth policy) AND should be paired with the new feature families — not run on the stale 14-feature stack.

Direction 3 is MEDIUM priority because it compounds best *after* Direction 1 (new features) or Direction 2 (larger universe) have given the model something new to learn. A cycle-3 QR may pick Direction 3 if the EDA motivates it — but the highest-expected-value cycle-3 EXPLORATIONs are Directions 1 and 2.

## 4. Standing Constraints Carried into Cycle 3

Every cycle-3 EXPLORATION brief must carry and, where its axis touches them, target these three unresolved constraints:

1. **LDO directional weakness** — OOS WR 25.0%, well below the 50% baseline for a triple-barrier classifier; a drag through every cycle-1 and cycle-2 iteration. Universe expansion (Direction 2) dilutes it; a multi-symbol-pooled model (Direction 3) may rescue it via shared strength; crypto-native features (Direction 1) may give the LDO model signal it currently lacks.
2. **BCH IS-PnL / OOS concentration** — BCH dominates ~77% of IS wpnl. Universe expansion is the direct denominator-expansion fix. The aspirational top-symbol concentration gate is ≤ 30%.
3. **OOS Sharpe gap** — /059's OOS +0.60 is +0.42 short of the aspirational +1.0 floor. The aspirational merge floors (IS and OOS Sharpe ≥ +1.0) inform cycle-3 priorities; per `feedback_v3_baseline_update_policy.md` they do not block a baseline update, but BOTH IS and OOS must improve over /059 for /092 to update BASELINE_V3.md (`feedback_v3_strict_both_is_oos_baseline.md`).

## 5. Per-Iteration Discipline (every cycle-3 EXPLORATION brief)

- **Section 2** — committed `analysis/iteration_v3-0NN/*.py` IS-only EDA with numerical tables, per `feedback_v3_axis_selection_quant_discipline.md`. Axis must be QR-EDA-driven.
- **Section 4 — TWO-ANCHOR STRUCTURE (MANDATORY, established iter-v3/084 closeout, Critic FINAL `16b4cc1` Recommendation #2).** Every /085-091 brief Section 4 MUST explicitly state TWO anchors: **(1) the cycle-3 EXPLORATION-MODE-REFERENCE — iter-v3/084: IS +0.8325 / OOS +0.3322 (3-seed EXPLORATION-mode, current data)** — used for intra-cycle Δ classification (PROMISING / NEGATIVE / INERT / SUSPICIOUS bands); an EXPLORATION runs 3-seed, so it must be compared to a 3-seed reference. **(2) the /059 CONFIRMATION baseline — IS +1.0894 / OOS +0.5791 (10-seed CONFIRMATION-mode, tag `v0.v3-059`)** — RESERVED for the iter-v3/092 CONFIRMATION (which runs 10-seed CONFIRMATION-mode and must be compared to a 10-seed baseline). **Mixing the two — comparing a 3-seed EXPLORATION number against the 10-seed CONFIRMATION number — is precisely the /082-/083 reference-architecture mismatch the iter-v3/084 closeout corrected.** The ~0.26 IS gap between a 3-seed EXPLORATION-mode run of the canonical config (~+0.83 IS, evidenced by /077≈/084) and the 10-seed CONFIRMATION (~+1.09 IS) is the EXPLORATION-vs-CONFIRMATION ensemble-architecture gap, NOT config staleness — see BASELINE_V3.md's "EXPLORATION-Mode Anchor Staleness" subsection.
- **Section 4** — pre-register the falsifier band AND the holding-time / roster-composition predictor (`feedback_v3_is_oos_regime_divergence.md`); for a per-symbol or universe axis, pre-register the target-symbol-axis falsifier band, not just the non-target bands (`feedback_v3_per_symbol_target_axis_falsifier.md`).
- **Section 4 SUSPICIOUS gate** — pre-register "OOS/IS Sharpe ratio > 3.0 → SUSPICIOUS" as a supplemental classifier (`feedback_v3_oos_is_ratio_gate.md`).
- **Section 8** — LOCKED classification criteria. For a NEW feature family, pre-register a conditional-orthogonality test (model-split-allocation / SHAP attribution vs the regime label) — marginal orthogonality is necessary but not sufficient (the /076 lesson).
- **Section 10** — QR Audit Trail, documenting the literature-research path (Section 2 of this plan).
- **NO-CHEATING** — `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` IMMUTABLE; `start_time` never trimmed; no date-range cherry-picked; QR sees OOS only in Phase 7.
- **Config-accretion pre-flight** — per Critic /081 Rec #3, the cycle-3 runner should carry a generalized "config == last-CONFIRMATION-MERGE (/059) config" pre-flight diff so a future accretion (like the /061 vol-floor that rode 19 iterations) is caught at runtime, not by archaeology. The first cycle-3 EXPLORATION that touches `run_baseline_v3.py` setup should add it.

## 6. iter-v3/092 — the THIRD v3 cycle CONFIRMATION

**Trigger**: 10/10 cycle-3 EXPLORATIONs (iter-v3/082-091) complete.

**Bundle**: the cycle-3 PROMISING findings. Unlike cycles 1 and 2 (which produced 0 PROMISING and whose CONFIRMATIONs were re-validations), cycle 3's structural-pivot axes are designed to produce genuine edge ingredients — /092 is intended to be a real edge-bundle CONFIRMATION. If, after a genuine bold cycle, cycle 3 also produces 0 PROMISING, /092 is a re-validation by the cycle-1/-2 precedent — but the cycle-3 mandate is explicitly to break that pattern.

**Spec**: unified 10-seed CONFIRMATION mode, `--n-trials 35` default (`feedback_v3_confirmation_n_trials_35.md`) — OR n_trials ≥ 100 if /092 attempts the full mass-feature-expansion bundle (`feedback_v3_mass_feature_expansion.md` AMENDMENT point 6). 6h wall-clock HARD CAP (`feedback_v3_cadence_discipline.md`).

**Baseline-update rule**: /092 updates BASELINE_V3.md only if it beats /059 on BOTH IS Sharpe AND OOS Sharpe (multi-seed mean) with both Pareto/CPCV checks positive (`feedback_v3_strict_both_is_oos_baseline.md`, `feedback_v3_baseline_update_policy.md`). Hard-blocking gates retained: Gate 3 (OOS/IS ≥ 0.50), Gate 6 (PSR > 0.95), Gate 10 (frac_positive_paths ≥ 0.55).

## 7. Cadence Summary

| Iteration | Type | Direction | Status |
|---|---|---|---|
| iter-v3/082 | EXPLORATION #1 | Direction 1 — NEW crypto-native funding-rate FEATURE FAMILY (4 features, `V3_FEATURE_COLUMNS` 14→18) | **DONE — SUSPICIOUS-OOS-DOMINANT (NO-MERGE)**; funding axis CLOSED at 4 data points (/019/023/024/082, all INERT-by-importance) |
| iter-v3/083 | EXPLORATION #2 | Direction 2 — symbol-universe EXPANSION 3→4 (add FILUSDT) | **DONE — NEGATIVE (NO-MERGE)**; IS monthly Sharpe collapsed −0.9156 (FIL's own −32% IS edge + ~68% incumbent data-extent drift); FILUSDT CLOSED as a universe-expansion candidate; the /082-vs-/083 decomposition exposed a ~70pp /059 anchor-staleness drift |
| iter-v3/084 | REFERENCE / METHODOLOGY (slot #3) | fresh /059-config 3-symbol anchor re-run on current data + the `PER_CELL_GAP` 43→22 fix | **DONE — REFERENCE-REANCHOR (NO-MERGE)**; IS +0.8325 / OOS +0.3322 (3-seed EXPLORATION-mode) — both deltas vs /059's recorded numbers ≈ −0.25, the brief Section 4.3 LOCKED re-anchor rule fired; **/084's IS +0.8325 / OOS +0.3322 is the cycle-3 EXPLORATION-MODE-REFERENCE** for /085-091; the ~0.26 IS gap is mostly the EXPLORATION-vs-CONFIRMATION architecture gap (/077 3-seed +0.8236 ≈ /084 3-seed +0.8325 vs /059 10-seed +1.0894), not config staleness; `PER_CELL_GAP` 43→22 fix landed as a permanent methodology correction |
| iter-v3/085 | EXPLORATION #4 | QR EDA-picks within Directions 1-3 (Direction 2 universe expansion / Direction 3 pooled model preferred) | TBD |
| iter-v3/086 | EXPLORATION #5 | QR EDA-picks within Directions 1-3 | TBD |
| iter-v3/087 | EXPLORATION #6 | QR EDA-picks within Directions 1-3 | TBD |
| iter-v3/088 | EXPLORATION #7 | QR EDA-picks within Directions 1-3 | TBD |
| iter-v3/089 | EXPLORATION #8 | QR EDA-picks within Directions 1-3 | TBD |
| iter-v3/090 | EXPLORATION #9 | QR EDA-picks within Directions 1-3 | TBD |
| iter-v3/091 | EXPLORATION #10 | QR EDA-picks within Directions 1-3 | TBD |
| iter-v3/092 | THIRD v3 CONFIRMATION | best cycle-3 bundle (multi-seed validation) | pre-registered MERGE gates |

**STRICT 10:1 cadence** — iter-v3/082-091 are 10 SEPARATE EXPLORATIONs; iter-v3/092 is a SEPARATE CONFIRMATION. Do NOT collapse the 10th into the CONFIRMATION (`feedback_v3_strict_10_to_1_cadence.md`).

The specific axis for each EXPLORATION is deliberately left TBD — it is selected by that iteration's QR via genuine research + IS EDA, within Directions 1-3. The orchestrator should sequence the early slots toward Direction 1 (crypto-native features) and Direction 2 (universe expansion), since those carry the highest expected value and Direction 3 compounds best after them.

## 8. What Cycle 3 Must NOT Do

- **No axis in a Section-1 CLOSED family** — no gate-threshold knobs, no ATR-multiplier tweaks, no risk primitives, no single-symbol swaps, no labeling tweaks on the same 14 features, no instrumentation-only axes. The Phase 5.5 gate BLOCKs them.
- **No axis selected without genuine literature research** — Section 2 of this plan is binding; brief Section 10 must document the research path.
- **No feature added by univariate rank alone** — test multivariate contribution (cluster-MDA), not univariate Spearman ρ (`feedback_v3_inert_features_at_higher_budget.md`; the iter-v3/070-era lesson).
- **No mass feature expansion at single-seed EXPLORATION** — phased single-family additions at EXPLORATION, full mass expansion only at /092 CONFIRMATION with n_trials ≥ 100 (`feedback_v3_mass_feature_expansion.md` AMENDMENT).
- **No cherry-picked date range, no OOS-cutoff drift, no OOS peeking in Phases 1-5** — `feedback_no_cheating.md`.
- **No CONFIRMATION-bundle assembly outside iter-v3/092** — only /092 runs CONFIRMATION-spec.
- **No stopping the autopilot loop** — per `feedback_v3_bold_research_mandate.md`, never offer the user a stopping point; iterate until the user explicitly intervenes.

## 9. Status

**Cycle 3 plan COMMITTED at the iter-v3/081 cycle-2 CONFIRMATION closeout (this document).** Cycle 3 EXPLORATIONs commence at iter-v3/082. The iter-v3/082 specific axis is deferred to the iter-v3/082 brief — it will be QR research-and-EDA-driven, within Directions 1-3, Direction 1 or 2 strongly preferred as the first bold axis.

**UPDATE — iter-v3/084 closeout (2026-05-16): cycle 3 has used 3 of 10 EXPLORATION slots; the measurement axis is now CLEAN.** iter-v3/084 was the cycle-3 REFERENCE / METHODOLOGY slot — the two declared mandates (the `PER_CELL_GAP` 43→22 fix + the clean /059-config 3-symbol anchor re-run reverting /083's FILUSDT expansion). It classified **REFERENCE-REANCHOR** — NO-MERGE. /084 (clean /059-config, 3-seed EXPLORATION-mode, current data) landed at **IS +0.8325 / OOS +0.3322**; both deltas vs /059's recorded IS +1.0894 / OOS +0.5791 are ≈ −0.25, outside the ±0.10 band, so the brief Section 4.3 LOCKED re-anchor rule fired. **The cycle-3 EXPLORATION-MODE-REFERENCE is now /084: IS +0.8325 / OOS +0.3322 (3-seed)** — /085-091 anchor their intra-cycle Δ against it (the /060→/077 precedent). **The ARCHITECTURE-GAP DECOMPOSITION (Critic Rec #1): the ~0.26 IS gap is mostly the EXPLORATION-vs-CONFIRMATION architecture gap, NOT config staleness** — /084's +0.8325 is a 3-seed EXPLORATION-mode number while /059's +1.0894 is a 10-seed CONFIRMATION-mode number; cycle 2's reference re-run /077 landed at IS +0.8236 (3-seed), near-identical to /084's +0.8325, proving essentially the entire gap is the 3-seed-vs-10-seed ensemble-architecture difference with only a small residual data-extent component. The honest finding: /082-/083 were anchoring their 3-seed EXPLORATION-mode deltas against a non-comparable 10-seed CONFIRMATION number — /084 corrects that reference-architecture mismatch. The **TWO-ANCHOR STRUCTURE** (Critic Rec #2) is now MANDATORY in every /085-091 brief Section 4 (see Section 5 above): the EXPLORATION-MODE-REFERENCE /084 for intra-cycle Δ; the /059 CONFIRMATION baseline reserved for /092. The /082 (SUSPICIOUS-OOS-DOMINANT) and /083 (NEGATIVE) classifications STAND — not reopened. The `PER_CELL_GAP` 43→22 fix landed as a permanent strictly-accretive methodology correction (the over-purge biased per-cell PBO pessimistically — no prior result invalidated); per-cell-PBO comparisons across the /084 boundary are gap-regime-discontinuous (Critic Rec #3). BASELINE_V3.md UNCHANGED — canonical /059 metrics + tag `v0.v3-059`; /084 tagged `v0.v3-084` as an EXPLORATION/REFERENCE closeout marker. **Cadence accounting: cycle 3 has used slots /082 (bold axis — Direction 1), /083 (bold axis — Direction 2), /084 (REFERENCE / METHODOLOGY). /085-091 are 7 more SEPARATE bold EXPLORATIONs (Directions 1-3; Direction 2 universe expansion / Direction 3 pooled model preferred — /082 proved no feature axis fixes the 3-symbol denominator problem); /092 is the SEPARATE 10-seed CONFIRMATION. The 10th EXPLORATION /091 is NOT collapsed into /092 (`feedback_v3_strict_10_to_1_cadence.md`).** Detail: `diary-v3/iteration_v3-084.md`.

**UPDATE — iter-v3/083 closeout (2026-05-16): cycle 3 is 2/10, 0 clean PROMISING.** iter-v3/083 ran Direction 2 (symbol-universe EXPANSION 3→4, adding FILUSDT) and classified **NEGATIVE** — NO-MERGE. IS monthly Sharpe collapsed −0.9156 (from +1.0894 to +0.1738); IS MaxDD blew out 30.97%→73.18%; CPCV `frac_positive_paths` 0.4667 FAILED the 0.55 gate. **Decomposition** of the −101.56pp IS-PnL collapse: FIL's own negative edge −32.45pp (32% — FIL standalone IS net_pnl% −32.45, 36.7% WR, a genuine net detractor; FIL does NOT transfer) + incumbent (BCH/LDO/TRX) drift −69.11pp (68%). The brief Section 4.3 incumbent-aggregate falsifier band [−20,+20] was BREACHED at −69.11pp. **The incumbent drift is data-extent drift, NOT FIL-perturbation** — proven cleanly by /082 (the same 3 incumbents on the same fresh data, FIL absent) already showing the incumbent aggregate ~70pp below /059. The engineering report's "FIL reshaped the incumbents' Optuna landscape" claim is mechanistically false (the Critic traced the runner — per-symbol Optuna studies are fully independent of `len(V3_MODELS)`); the correct mechanism is the /077 anchor-staleness finding. FILUSDT is now a CLOSED universe-expansion candidate (joining HBAR/AVAX at /021 and ADA at /078). Detail: `diary-v3/iteration_v3-083.md`.

**TWO MANDATES recorded at the /083 closeout (carried into Section 7 and the iter-v3/084 setup):**

1. **MANDATORY iter-v3/084-setup fix — `PER_CELL_GAP` 43→22** (per /083 Critic FINAL `1116124` Rec #2). `PER_CELL_GAP = 43` (`run_baseline_v3.py:1497`) is stale — it is the value `(42+1)` left over from the reverted iter-v3/068 42-candle timeout-widening; with `timeout_candles = 21` the per-cell single-symbol CSCV purge gap must be `(21+1) = 22`. It over-purges (the conservative direction — it biases per-cell PBO pessimistically, so it did NOT invalidate /083) but it is wrong. The iter-v3/084 setup (the next runner-touching iteration) MUST: (a) correct `PER_CELL_GAP` 43→22 at `run_baseline_v3.py:1497`; (b) add an `expected_gap` guard to the per-cell `combinatorial_purged_cv` call (`run_baseline_v3.py:1586-1592`) so the constant cannot silently drift again; (c) fix the stale runner string literals at `run_baseline_v3.py:2539` ("asserts REQUIRED_GAP == 66") and `:2593` ("Gap: 88 (= (21+1)*3=66 ...)") — cosmetic-only but flagged by the /083 Phase 5.5 gate and not fixed before the /083 run. This mandate cannot be renegotiated post-hoc.

2. **iter-v3/084 anchor-staleness recommendation — a fresh /059-config anchor re-run on current data.** The /082-vs-/083 decomposition proved the /059 anchor is stale by ~70pp of incumbent IS PnL — every cycle-3 Δ-vs-/059 comparison is confounded by data-extent drift the EXPLORATION cannot attribute to its axis. This is exactly the situation cycle 1 faced and handled at the /077 closeout (which established a fresh current-code /060-config EXPLORATION-MODE-REFERENCE). The /083 QR recommends **iter-v3/084 be a no-axis EXPLORATION-mode 3-seed run of the canonical 3-symbol BCH/LDO/TRX / 14-feature / `(2.0,1.0)`-ATR / 7-gate /059 configuration on the freshly-fetched current data** — establishing a current-code/current-data EXPLORATION-MODE-REFERENCE for cycle 3. Cycle-3 EXPLORATIONs /085-091 then re-anchor their Δ against that fresh reference; the /092 CONFIRMATION continues to anchor against the canonical /059 CONFIRMATION baseline (separate, per BASELINE_V3.md's anchor-staleness note). The canonical /059 CONFIRMATION baseline and tag `v0.v3-059` are UNCHANGED — this is an EXPLORATION-mode-reference correction, not a baseline change; `OOS_CUTOFF_DATE` and `training_months` are untouched. /084 is not a wasted slot — it converts cycle 3's measurement axis from confounded to clean. The orchestrator should sequence /084 as the next iteration before any further structural EXPLORATION.

**UPDATE — iter-v3/082 closeout (2026-05-16): cycle 3 is 1/10, 0 clean PROMISING.** iter-v3/082 ran Direction 1 (a NEW crypto-native funding-rate feature family) and classified **SUSPICIOUS-OOS-DOMINANT** — NO-MERGE, the funding family ranked bottom-4/18 by importance (9.90% combined), the +1.21 OOS lift was the INERT-feature Optuna-perturbation / 3-seed-lottery artifact, not funding signal. The v3 funding-rate axis is now a **4-data-point structural verdict** (/019/023/024/082, all INERT-by-importance) and is **CLOSED for the remainder of cycle 3** absent a fundamentally different construction (multi-symbol-pooled model or open-interest data). **Per /082 Critic Rec #3, the remaining cycle-3 EXPLORATIONs (/083-091) should weight Direction 2 (symbol-universe EXPANSION) higher up the priority list**: /082's OOS Sharpe is ~104%-concentrated in BCH on a 3-symbol universe — the OOS is structurally a single-symbol bet and **no feature-family axis can fix that denominator problem.** Direction 2 (universe expansion = denominator expansion, distinct from the CLOSED swap-by-replacement family) and Direction 3 (multi-symbol-pooled model) directly attack the BCH-concentration fragility that makes every v3 OOS number fragile. **iter-v3/083 should prioritize Direction 2 — symbol-universe expansion.** Detail: `diary-v3/iteration_v3-082.md` Section 11.

**Anchor for cycle 3**: iter-v3/059 (BASELINE_V3.md, `v0.v3-059`, IS +1.0894 / OOS +0.5791) — freshly re-validated at the iter-v3/081 CONFIRMATION (IS +1.0894 exact / OOS +0.5999).

## See Also

- `feedback_v3_bold_research_mandate.md` — the cycle-3 ambition + research mandate (user directive 2026-05-16)
- `feedback_v3_mass_feature_expansion.md` — mass feature expansion methodology (target 100, 50 minimum) + the 2026-05-14 phased-expansion AMENDMENT
- `project_v3_cycle2_outcome.md` — the cycle-2 outcome this plan responds to
- `project_v3_cycle1_outcome.md` — cycle 1 (the first 0-PROMISING cycle)
- `diary-v3/iteration_v3-081.md` — the cycle-2 CONFIRMATION closeout
- `briefs-v3/iteration_v3-081/` — cycle-2 CONFIRMATION artifacts (research brief, engineering report, Critic FINAL `f8c8474`)
- `briefs-v3/exploration_catalog.md` — cycle history
- `feedback_v3_strict_10_to_1_cadence.md` — cycle structure
- `feedback_v3_strict_both_is_oos_baseline.md` + `feedback_v3_baseline_update_policy.md` — the /092 baseline-update rule
- `feedback_v3_axis_selection_quant_discipline.md` — QR-EDA-driven axis selection
- `feedback_v3_is_oos_regime_divergence.md` — the holding-time / roster-composition predictor
- `feedback_v3_oos_is_ratio_gate.md` — the OOS/IS ratio SUSPICIOUS gate
- `references/crypto-edge-deep.md` — crypto-native alpha-source index (a research starting point, not a substitute for fresh research)
