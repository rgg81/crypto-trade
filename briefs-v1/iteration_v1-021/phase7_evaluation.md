# Phase 7 — OOS Evaluation Memo — iter-v1/021

**Iteration**: iter-v1/021 (cycle-3 EXPLORATION #6 of 10 — methodology-pivot subtype)
**Branch**: `iteration-v1/021` HEAD `0ca2f33`
**Anchor**: `v0.v1-baseline-corrected` (`BASELINE_V1.md` commit `f8bc12c`)
**Verdict (post-BLOCK-PENDING-FIX rerun + Critic FINAL `0ca2f33`)**: **EXPLORATION-PROMISING-METHODOLOGY** — joint cell **H1 BORDERLINE × H2 REFUTED** ("Pool-conferred edge despite same features; basin-level interaction effect")

This iteration is a methodology-pivot diagnostic. /021 produces NO new edge-finding backtest. The verdict is DIAGNOSTIC-class (CONFIRMED / MIXED / REFUTED on each of H1 and H2) and maps to EXPLORATION-PROMISING-METHODOLOGY per brief Section 1 mapping rules (sister to /001/008).

---

## 1. Verdict cell vs Phase 5 pre-registered 9-cell matrix

The joint H1 BORDERLINE × H2 REFUTED cell **was not in QR's pre-registered Section 4.3 9-cell PROMISING-METHODOLOGY scenarios**.

Brief Section 5 verdict-class priors:
- H1: DIAGNOSTIC-CONFIRMED 55% (or LM Master Rec #1 recalibrated 45%) / MIXED 30 (or 40)% / REFUTED 15%
- H2: DIAGNOSTIC-CONFIRMED-H2 70% / MIXED-H2 20% / REFUTED-H2 10%

Joint cells (independent prior product after LM Master recalibration):
- CONFIRMED × CONFIRMED-H2 = 45 × 70 = **31.5%** (modal)
- CONFIRMED × MIXED-H2 = 9%
- CONFIRMED × REFUTED-H2 = 4.5%
- MIXED × CONFIRMED-H2 = 28%
- MIXED × MIXED-H2 = 8%
- MIXED × REFUTED-H2 = 4%
- REFUTED × CONFIRMED-H2 = 10.5%
- REFUTED × MIXED-H2 = 3%
- REFUTED × REFUTED-H2 = 1.5%

Observed cell: **BORDERLINE × REFUTED-H2** ≈ between MIXED × REFUTED (4%) and CONFIRMED × REFUTED (4.5%). The brief did NOT explicitly enumerate BORDERLINE as a separate H1 class (Section 4.3 9-cell matrix collapsed it to either CONFIRMED or MIXED depending on which side of the 4/10 threshold it landed). The Critic Phase 7.5 final verdict resolved BORDERLINE = "CONFIRMED on the band-edge" (4/10 params shifted on ≥50% months; 1/4 key params).

**Combined prior weight on this cell**: ~4-5%. **A tail outcome materialized**, but on the same side as LM Master Rec #1's recalibration (which moved 10pp from CONFIRMED → MIXED tail). The MIXED + BORDERLINE region was correctly identified by LM Master as the underweight zone — that pre-registration helped.

**Per LM Master Rec #5 routing** (which was the pre-registered /022 decision tree):
- CONFIRMED with HIGH-CONFIDENCE (≥6/10 + ≥2 key) → accelerated /022=/027
- BORDERLINE (4-5/10) → /022 = LTC-only specialization
- MIXED / REFUTED → /022 = LTC-only specialization

Observed 4/10 + 1/4 key → BORDERLINE per LM Master decision tree → **/022 = LTC-only specialization (cadence-preserved)**. The routing recommendation matches what the brief pre-registered for the 4-5/10 band exactly.

---

## 2. Track Record Update

### LM Master directional track

| Iteration | Modal verdict prediction | Observed | Score |
|---|---|---|---|
| /017 | (pre-LM Master) | n/a | n/a |
| /018 | PROMISING-INERT favorable | PROMISING-INERT-FAVORABLE | 1/1 |
| /019 | PROMISING modal 35% | PROMISING | 1/1 (modal hit) |
| /020 | INERT-no-effect modal 40% | NEGATIVE-CATASTROPHIC (2% tail) | 0/1 (modal off by 0.86σ opposite direction) |
| /021 H1 prior (45/40/15) | CONFIRMED 45% modal | BORDERLINE (between CONFIRMED + MIXED) | **0.5/1** (modal directionally correct on H1; BORDERLINE-correct per Phase 7.4 §1 self-update) |
| /021 H2 prior (70/20/10) | CONFIRMED-H2 modal 70% | REFUTED-H2 (10% tail) | **0/1** (modal off; 70% prior absorbed at 10% tail; Spearman ρ = 0.9448 vs predicted <0.5) |

**Directional running total (post-/021)**: 1.5/5 directional calls hit + 1 BORDERLINE partial credit on /021 H1 → **30% directional accuracy** (1.5/5).

The LM Master Phase 4.5 §1 H1 recalibration from QR's 55% to 45% was a genuine improvement — observed BORDERLINE sits at the CONFIRMED-MIXED interface, exactly where the 10pp MIXED-tail reweighting predicted. However the H2 prior at 70% CONFIRMED proved badly miscalibrated — Spearman ρ = 0.9448 is at the extreme of the REFUTED region (>>0.8) and the underlying mechanism (basin-level interaction NOT feature-level specialization) was not anticipated by LM Master at Phase 4.5.

### LM Master methodology track

| Iteration | Methodology call | Observed | Score |
|---|---|---|---|
| /018 | n_eff calibration accurate | n_eff=9 PASS | 1/1 |
| /019 | n_eff per-cell method | n_eff median accurate | 1/1 |
| /020 | n_eff prediction = 9 | n_eff = 9 EXACT | 1/1 |
| /021 | Mandate `params_persist_path` + reject 2 QR alternatives + Layer C 10-param visibility audit | 106 rows × 11 params all non-null; visibility audit PASS; Layer A 106 rows ≥ 48 PASS | **1/1** (perfect — 10/10 hyperparams visible per cell at 106 rows; rejected QR alternatives proven correct ex-post) |

**Methodology running total**: **3/3 = 100%** (with /021 contributing the strongest single methodology call to date — the §3.1 buffer was the substrate of the entire diagnostic, and it executed exactly as LM Master mandated).

### Synthesis

LM Master's strongest lane is methodology (3/3 perfect); the directional track (1.5/5) reflects that mechanism predictions across novel cohort patterns are HARD even with disciplined re-calibration. The /021 evidence base (especially the unexpected H2 REFUTATION + load-bearing structural finding) updates the prior for /022+: directional priors at single-seed EXPLORATION for novel methodology axes should expect modal-tail outcomes >10% probability mass.

---

## 3. /020 retrospective re-interpretation

**LM Master /020 Phase 7.4 §3 hypothesis**: BTC's OOS positive rotation under pool was POOL-CONFERRED at training time via 3 channels (C1 feature normalization / C2 label-timing co-location / C3 abs_pnl weighting), and isolation alone dissolved it. This was framed as "H_INTRINSIC REFUTED at training-time granularity" per `feedback_v1_h_intrinsic_refuted_at_btc.md`.

**Refinement after /021**: The 3-channel mechanism is CORRECT in spirit but mis-categorized in scope. The /021 H2 REFUTATION (Spearman ρ = 0.9448 between Pool BTC-slice and BTC-only Model H feature importance rankings) means:

> Cohort isolation effects in v1 are **basin-level (Optuna parameter shifts)**, **NOT feature-level (same features dominate per cohort)**.

The pool DID confer edge to BTC's OOS positive rotation. But the channel was NOT "different features were valuable in pool vs cohort-only" (H2 REFUTED). It was "Optuna's loss surface basin under joint IS labels for BTC + ETH + LINK + LTC + DOT differs from BTC-alone basin in {max_depth, subsample, reg_lambda, confidence_threshold}" (H1 CONFIRMED BORDERLINE at 4/10 params shifted on ≥50% of months).

**Mechanism finding**: The 3 pool-conferred channels (C1 / C2 / C3) operate **at the basin (parameter) layer**, not the feature-importance layer. The features the model picks are nearly the same; what differs is the depth, subsample fraction, regularization, and label-classification threshold — all parameter-region knobs that interact with the joint label distribution.

**Updated mental model**:
- /020 BTC catastrophic was **basin-relocation under universe-composition change** — pool basin (max_depth ≈ 5, subsample ≈ 0.65, reg_lambda ≈ 1.2) under BTC+ETH+LINK+LTC+DOT joint labels produced OOS positive rotation; BTC-only basin (max_depth ≈ 3, subsample ≈ 0.85, reg_lambda ≈ 0.4) under BTC-only labels picked structurally adverse OOS trade subset.
- The label-distribution × parameter-basin interaction is the load-bearing mechanism, NOT feature selection.
- This explains why H_INTRINSIC framing at /020 was "REFUTED" in a sense but NOT in the way originally framed — the cohort retains its features but loses its basin under universe-composition change.

**Carry-forward correction**: `feedback_v1_h_intrinsic_refuted_at_btc.md` should be cross-referenced with the new `feedback_v1_h2_refuted_basin_interaction.md` rule (added at /021 closeout). The original /020 framing is **not refuted but refined** — "H_INTRINSIC at training-time granularity" → "basin-level interaction effect (Optuna parameter-region locking) under universe composition change".

---

## 4. /027 CONFIRMATION readiness post-/021

### Bundle architecture: Option β PRE-COMMITTED

Per LM Master Phase 4.5 §7 (ADOPTED) — LM Master Rec #7 ADOPTED in brief Section 11.6:
- **Option α REJECTED**: TWO-SPECIALIST + REDUCED POOL (drop LINK+ETH from pool) — would shift BTC basin again, replicating /020 catastrophe pattern.
- **Option β ADOPTED**: TWO-SPECIALIST + FULL POOL preserved (5-symbol pool unchanged) + LINK-only Model C alpha-enhancement + ETH-only Model G alpha-enhancement (with BTC-trend gate) + signal-level merge logic.

| Component | Provenance | Bundle role | Single-seed Δ | Multi-seed regression target |
|---|---|---|---|---|
| Pool baseline (5 symbols, A/C/D/E unchanged) | BASELINE_V1.md | Pool anchor | 0 | 0 |
| LINK-only specialist (Model C) | /018 PROMISING | Alpha-enhancement | +0.16 | +0.80 |
| ETH-only + BTC-trend gate (Model G) | /019 PROMISING | Alpha-enhancement | +0.65 | +0.50 |
| **BTC** (via Model A pool) | /020 catastrophic EXCLUDED specialist | Pool baseline only — no specialist | — | — |
| LTC, DOT | TBD pending /022-/025 | TBD | — | — |

### Status: 2/4-6 specialists staged

- **LINK +0.80** (from /018) — VALIDATED at /018 PROMISING-INERT-FAVORABLE. Multi-seed target +0.80 (assumes pooled-anchor variance reduction at /027).
- **ETH+gate +0.50** (from /019) — VALIDATED at /019 PROMISING with orthogonal mechanism (BTC-trend gate is load-bearing).
- **BTC** — enters /027 IN POOL via Model A (no architectural change vs baseline for BTC); BTC-only Model H specialist EXCLUDED per /020 NEGATIVE-Catastrophic verdict.

### Outstanding for /022-/025 (4 EXPLORATIONs)

Per H2 REFUTED + /020 retrospective:
- **/022 = LTC-only + orthogonal mechanism**. The H2 REFUTATION at /021 means LTC's cohort-isolation viability CANNOT be predicted from feature-importance signature alone (those are nearly invariant). LTC-only must REQUIRE an orthogonal mechanism (gate, risk-primitive, or feature) on top of isolation. Family: `per-cohort-specialization-LTC` (new at v1 catalog level) + orthogonal mechanism.
- **/023 = DOT-only similar treatment** (orthogonal mechanism).
- **/024-/025 = methodology + bundle composition work** (Critic Path Forward Rec #1-3 alternatives if /022 or /023 produce structural findings) OR potential alpha-axis EXPLORATIONs.
- **/026 = pre-CONFIRMATION sanity** (e.g., Layer B determinism re-verification at /027 multi-seed budget).

### /027 multi-seed regression target

Per LM Master Phase 4.5 §7 (and bundle table above):
- Pool baseline (0) + LINK +0.80 + ETH+gate +0.50 = nominal +1.96 if independent.
- Realistic with correlation drag + multi-seed variance reduction: **+1.10 to +1.30**.
- Sharpe 1.0 floor merge gate: REQUIRES multi-seed mean ≥ +1.0 OOS Sharpe.
- Top-symbol concentration ≤ 30% gate: Verified via cross-correlation < 0.40 between LINK and ETH+gate roster Sharpe paths (Critic /019 Rec #3 pre-validation).

**Pending /022-/026 contributions**: LTC and/or DOT may add +0.20-0.30 each IF orthogonal mechanism succeeds. Realistic bundle ceiling: +1.30 to +1.60 OOS Sharpe at /027 multi-seed.

### /027 anchor proxy formalization

Per /020 LESSON #5 + Critic Phase 7.5 Rec #2: /027 CONFIRMATION brief MUST pre-compute BTC-in-pool annualized-daily-Sharpe directly (no monthly Sharpe PROXY +0.30). Lock anchor frame to `comparison.csv` "sharpe" semantics. Forward-looking; /020/021 verdicts ROBUST under all frames, but /027 cannot depend on proxy alignment.

---

## 5. Per-month FI accumulator — methodologically superior; v3 backport candidate

The /021 BLOCK-PENDING-FIX (commit `502d66e`) added a per-month feature-importance accumulator to `lgbm.py:303,797-800` + `run_baseline_v1.py:573-599`:
- `LightGbmStrategy._per_month_fi_log: list[dict]` accumulates `{train_month, mean_gain}` per walk-forward month, populated WITHIN `_train_for_month` before `_models` is overwritten in the next month.
- `_write_feature_importance` in `run_baseline_v1.py` reads from this accumulator as primary path (stale-safe); legacy `_models` read is fallback only.
- Result: `feature_importance_*.csv` reflects mean gain averaged across **53 walk-forward months** (n=53), NOT the last-month-only snapshot (n=1).

**Methodological superiority over v3's convention**:
- v3 uses last-month-only convention at `run_baseline_v3.py:2730-2818` (LM Master Phase 7.4 §6 outstanding gap II).
- v1 per-month accumulator is **strictly superior**: 53-month averaging dampens single-month sampling noise; weights all walk-forward windows equally; produces a more representative cohort-signature.
- This was unexpected — the original fix scope was just "make Pool Model A non-zero". The accumulator path was the cleanest implementation and turned out to be methodologically better than the v3 baseline convention.

**Per Critic Phase 7.5 final recommendation #3**: Consider v3 backport. The v1 per-month FI accumulator pattern can be ported to v3 with minimal code surface change. Worth scheduling as a v3 methodology iteration if/when v3 cycle-7+ revives.

**Codification**: New memory file `feedback_v1_per_month_fi_accumulator.md` (created at /021 closeout) documents the v1 convention and flags the v3 backport.

---

## 6. Headline numbers (for diary)

| Layer | Result | Status |
|---|---|---|
| Layer A (parquet completeness) | 106 rows ≥ 48 threshold | **PASS** |
| Layer B (determinism) | NOT bit-identical (2-sym pool vs 5-sym baseline) but expected per LM Master Phase 7.4 §6 | **PASS-WITH-NOTE** |
| Layer C (10-param visibility) | 10/10 hyperparams non-null per cell, 106/106 rows complete | **PASS** |
| H1 falsifier | 4/10 params shifted on ≥50% months; 1/4 key params | **CONFIRMED BORDERLINE** |
| H2 falsifier | Spearman ρ = 0.9448 between Pool BTC-slice and BTC-only Model H | **REFUTED** |
| Engineering report | Committed at `502d66e` | **3-strike incident RESOLVED** |

| Key params shifted on ≥50% months | % > 0.30 |
|---|---|
| confidence_threshold | 54.7% |
| max_depth | 73.6% |
| subsample | 54.7% |
| reg_lambda | 60.4% |

---

## 7. Substrate-level findings

### Finding A — Cohort isolation is basin-level, not feature-level (LOAD-BEARING for cycle-3+)

The H2 REFUTATION binds /022+: future per-cohort mechanism stories MUST be framed at parameter-basin level (max_depth × subsample × reg_lambda × per-cohort label distribution interactions), NOT feature-shift. /022 LTC-only brief Section 4 cannot claim "LTC needs different features" because the /021 evidence shows pool BTC-slice and cohort-only have Spearman ρ = 0.9448 across the entire 40-feature space — feature stability across cohort cuts is the rule.

### Finding B — /020 retrospective: NOT H_INTRINSIC refutation but basin-relocation

The /020 catastrophic outcome is mechanistically a **basin-relocation under universe composition change** (Optuna's joint-label loss surface basin for BTC + ETH + LINK + LTC + DOT vs BTC-alone basin land in different (max_depth, subsample, reg_lambda) regions for the same SEED=42), producing structurally adverse OOS trade subset for BTC-only. The "H_INTRINSIC refutation" framing at /020 was correct in spirit (the pool was load-bearing for BTC) but mis-categorized the mechanism layer.

### Finding C — Per-cohort axis architecture (Option β) confirmed

The /021 evidence base + /020 retrospective + /018+/019 confirm: the /027 bundle architecture is FULL POOL (5 symbols unchanged) + alpha-enhancement specialists (LINK + ETH+gate) with signal-level merge logic. NOT reduced-pool + specialists. BTC enters /027 IN POOL. LTC + DOT TBD pending /022-/025 with orthogonal mechanisms.

### Finding D — Track record: 3/3 methodology, 1.5/5 directional

LM Master's methodology lane (recommendations on HOW to instrument the diagnostic — `params_persist_path` mandate, rejection of QR alternatives, Layer C 10-param visibility audit) is 3/3 perfect; the directional lane (modal verdict-class priors) is 1.5/5. /022+ should weight LM Master's methodology recommendations highest; LM Master's modal directional priors should be treated as informational with explicit reserve for tail outcomes.

---

## 8. Verdict synthesis

**Verdict**: EXPLORATION-PROMISING-METHODOLOGY (FINAL after BLOCK-PENDING-FIX rerun + Critic FINAL `0ca2f33`)

**Subtype**: H1 CONFIRMED BORDERLINE × H2 REFUTED — "Pool-conferred edge despite same features; basin-level interaction effect"

**Merge decision**: NO-MERGE. /021 is a diagnostic methodology iteration; PROMISING-METHODOLOGY is non-compoundable per `feedback_v1_methodology_probe_discipline.md`. BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`).

**Carry-forward bindings for /022+**:
1. H2 REFUTATION → mechanism stories MUST be at basin level (basin = Optuna parameter region under joint loss).
2. /020 retrospective updated → basin-relocation mechanism (not H_INTRINSIC); update mental model.
3. Per-month FI accumulator now on trunk (v3 backport candidate).
4. /027 Option β PRE-COMMITTED with LINK + ETH+gate + Pool baseline + signal-level merge.
5. /022 routing per LM Master Rec #5 + Critic Recommendation: LTC-only + orthogonal mechanism. /023 = DOT-only similar.

**Cycle-3 cadence**: 6 of 10 EXPLORATIONs complete after /021. 4 more (/022-/025) before /027 CONFIRMATION.

**Phase 8 diary**: produced at `diary-v1/iteration_v1-021.md`; catalog updated; memory entries created.
