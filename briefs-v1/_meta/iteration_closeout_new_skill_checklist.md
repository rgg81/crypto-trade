# Iteration Closeout — New-Skill Checklist (v1, 2026-05-31 reframe)

**Scope**: applies to EVERY iter-v1/NNN closeout under the regime-ensemble + relative-regime-Pareto framework, starting iter-v1/043.
**Roles**: QE (Phase 6 deliverables), LM Master (Phase 7.4), Critic (Phase 7.5), QR (Phases 7+8).
**Reads**: brief Section 10 + 8 + 0.5; `briefs-v1/_meta/baseline_seed_regime_matrix.csv`; `briefs-v1/_meta/regime_catalog.md`.
**Sister docs**: `regime_ensemble_methodology.md`, `merge_v1_relative_regime_pareto_proposal.md`.

---

## Phase 6 — QE deliverables (closeout-relevant)

- [ ] `reports-v1/iteration_v1-NNN/comparison.csv` — DSR/PBO/PSR columns present (informational).
- [ ] **`reports-v1/iteration_v1-NNN/regime_attribution.csv`** — schema: `regime_tag, in_sample, candidate_sharpe, candidate_max_dd, candidate_trade_count, baseline_sharpe, baseline_max_dd, baseline_trade_count`. Rows for every regime tag in `regime_catalog.md` × `{IS, OOS}`. Baseline columns read from `baseline_seed_regime_matrix.csv` median. Missing → BLOCK at Phase 7.5 Check 3c.
- [ ] `engineering_report.md` confirms walk-forward `train_end_ms = test_start_ms - embargo_ms` and CV gap unchanged.

---

## Phase 7.4 — LM Master mandate

### Item 0 (NEW, MANDATORY, FIRST) — Regime Attribution Table

LM Master MUST emit a markdown table tagging IS+OOS months by regime AND computing per-regime metrics for THIS iter AND BASELINE_V1.

**Required schema (columns, in order):**

| Regime | IS months | OOS months | This iter IS Sharpe | This iter OOS Sharpe | This iter IS trades | This iter OOS trades | This iter IS MaxDD | This iter OOS MaxDD | This iter IS PnL | This iter OOS PnL | Baseline IS Sharpe | Baseline OOS Sharpe | Baseline IS trades | Baseline OOS trades | Baseline IS MaxDD | Baseline OOS MaxDD | Baseline IS PnL | Baseline OOS PnL | Bundle-role implication |

- Regime tags from canonical `briefs-v1/_meta/regime_catalog.md` (BTC 90-day return × 30-day realized vol quantiles): `bull`, `alt-rotation`, `chop`, `bear`, `vol-spike`, `liq-cascade`, `ETF-flow`, `recovery`, `other`.
- LM Master MUST propose a one-phrase **bundle-role implication** per regime row (e.g., "UNIVERSAL contributor", "bull specialist; drop chop", "TAIL-CONTROL in vol-spike only", "off-regime drag — exclude from chop dispatch").
- Reads `reports-v1/iteration_v1-NNN/regime_attribution.csv` for per-regime PnL.
- The table is the **load-bearing input to Critic Check 3c and 3d**. Absence = BLOCK-PENDING-FIX.

### Items 1–7 (unchanged from skill §Phase 7.4)

Feature importance triage; HP trial stability; gain concentration; suspicious patterns; next-iteration tuning; Phase 4.5 predictions vs outcome; closing note for Critic.

---

## Phase 7.5 — Critic checks (closeout-critical reframe)

| Check | Iter type | Verdict authority |
|---|---|---|
| **3a — DSR/PSR per-regime + bundle** | CONFIRMATION: INFORMATIONAL. **EXPLORATION: SKIP** | flag-only; never BLOCK |
| **3b — PBO bundle-level** | CONFIRMATION: INFORMATIONAL. **EXPLORATION: SKIP** | flag-only; never BLOCK |
| **3c — Regime Attribution Clarity (NEW)** | **EXPLORATION + CONFIRMATION: MANDATORY** | reads §Item 0 table; PASS if regime decomposition is internally consistent (per-regime PnL sums to bundle PnL ±2%) AND bundle-role implications are non-vacuous; BLOCK-PENDING-FIX if table missing or rows incoherent |
| **3d — BUNDLE-level per-regime Pareto-dominance vs BASELINE_V1 (NEW)** | **BUNDLE-CONFIRMATION-only**. EXPLORATIONs + component-CONFIRMATIONs EXEMPT | PASS iff: every tagged regime has `sharpe_R(cand) ≥ sharpe_R(base) − σ_R` AND `max_dd_R(cand) ≤ max_dd_R(base) + σ_dd_R` AND `trade_count_R(cand) ≥ 0.5 × trade_count_R(base)` AND ≥1 regime is strictly better. σ_R / σ_dd_R sourced from `baseline_seed_regime_matrix.csv`. Otherwise BLOCK |

Checks 1, 2, 4, 5, 6, 7, 8, 13, 14 unchanged — methodology integrity gates remain HARD.

### OVERALL verdict — 9-band regime-aware (replaces old PROMISING/NEGATIVE binary)

For **EXPLORATION** iterations, Critic emits ONE band, decided by the following decision tree applied **to the regime decomposition** (NOT to bundle OOS Sharpe alone):

1. IS Δ ≥ +σ_R in ≥3 regimes AND no regime regresses > σ_R → **UNIVERSAL**
2. IS Δ ≥ +σ_R in target regime(s) AND OOS Δ ∈ [−σ_R, +σ_R] (within noise) AND no regime regresses > σ_R AND regime-attribution-clean → **REGIME-SPECIALIST-IS**
3. OOS Δ ≥ +σ_R in target regime(s) AND IS within noise AND OOS regime recurring per catalog → **REGIME-SPECIALIST-OOS**
4. max_dd_R(cand) ≤ max_dd_R(base) − σ_dd_R in vol-spike OR liq-cascade AND sharpe_R within σ_R elsewhere → **TAIL-CONTROL**
5. Bundle Sharpe Δ ≥ +σ_R, regime attribution not yet decomposable (rare; <1 month per regime) → **EXPLORATION-PROMISING**
6. Δ ≤ −σ_R in target regime(s) AND Δ < 0 in ≥half non-target → **TRUE-NEG** (== EXPLORATION-NEGATIVE)
7. |Δ| ≤ 0.1·σ_R across all regimes AND trade-roster Jaccard > 95% → **NEGATIVE-no-effect**
8. Δ ≤ −σ_R in target regime AND mechanism mechanically broken by axis (cohort removal kills load-bearing signal; F-AXIS load-bearing falsifier on importance/wiring layer fires) → **LEARNED-NEG**
9. IS Sharpe ≫ OOS Sharpe with abnormal regime asymmetry OR Critic Check 1/2 fails → **WALK-FORWARD-LEAKAGE** (BLOCK-FINAL)

For **CONFIRMATION** iterations: additionally evaluate Check 3d. If PASS → `CONFIRMATION-MERGE` or `CONFIRMATION-MERGE-PORTFOLIO`; if FAIL → `CONFIRMATION-BLOCK`.

Path Forward section MANDATORY on every BLOCK verdict (EXPLORATION-NEGATIVE / TRUE-NEG / NEGATIVE-no-effect / LEARNED-NEG / WALK-FORWARD-LEAKAGE / CONFIRMATION-BLOCK / BLOCK-PENDING-FIX / BLOCK-FINAL).

---

## Phase 7+8 — QR diary mandate

- [ ] Reframe all NEG-CLEAN / NEG-CAT / INERT bespoke bands to the canonical 9-band regime-aware vocabulary above.
- [ ] Diary populates the per-regime comparison table directly from `regime_attribution.csv` and the LM Master Item-0 table.
- [ ] Document the iteration's `/044` (or next CONFIRMATION) bundle composition role candidacy under each plausible regime — even if the verdict is REGIME-SPECIALIST-IS or TAIL-CONTROL, the diary records WHICH bundle slot this component fills.
- [ ] **DO NOT use "OVERFIT"** as a verdict tag without an F-AXIS load-bearing falsifier firing on the importance/wiring layer (importance-INERT mechanism + mechanism congruence broken). IS-strong / OOS-weak alone is regime mismatch, NOT overfit.
- [ ] DSR / PBO / PSR regressions (Δ < 0 vs baseline) are **documented in diary with a one-paragraph justification** but do NOT auto-block.
- [ ] Adopt Critic's Path Forward verbatim into the diary's "Next Iteration Ideas" section.

---

## /044 substrate composition rule (CONFIRMATION-only — applies whenever a bundle-CONFIRMATION runs)

- [ ] **Per-regime Pareto-dominance vs current BASELINE_V1 is THE merge gate** (Check 3d). No absolute Sharpe / OOS-trade / concentration floors.
- [ ] **Component substitution test**: for every component in the bundle, predict bundle within-regime metrics WITHOUT it. Each component must contribute Pareto-positive within-regime OR fill a regime gap the baseline does not cover. Components failing both → DROPPED or explicit user-directive exception.
- [ ] **Anchor requirement**: ≥1 component must, on its own, be Pareto-better-or-equal to BASELINE_V1 on the regime the baseline covers best. Pure-specialist bundles (no anchor) require explicit user-directive exception.
- [ ] Correlation diversification preferred but NOT BLOCKING; pairs > 0.70 require a one-paragraph "correlation justification" in the diary.

---

## Operational artifacts to author at /044 (and maintain thereafter)

These files are ONE-TIME bootstrap deliverables of the first bundle-CONFIRMATION; subsequent CONFIRMATIONs update them.

- [ ] **`briefs-v1/_meta/baseline_metric_anchors.csv`** — bundle-level DSR, PBO, PSR, monthly_sharpe, daily_sharpe, max_drawdown, profit_factor, win_rate, n_trades, total_pnl for current BASELINE_V1 (IS + OOS columns).
- [ ] **`briefs-v1/_meta/baseline_seed_regime_matrix.csv`** — 10 seeds × N regimes × {Sharpe, max_dd, trade_count} for the current baseline. **This file is the source of σ_R and σ_dd_R** used by Check 3d and the 9-band decision tree. σ_R = stdev across the 10 baseline seeds' within-regime Sharpe.
- [ ] **`briefs-v1/_meta/regime_catalog.md`** — canonical regime tag definitions (regime name → tagging rule using BTC 90-day return quantile + 30-day realized vol quantile, or explicitly documented alternative).
- [ ] **Per-iteration**: `reports-v1/iteration_v1-NNN/regime_attribution.csv` per QE Phase 6 schema above.

---

## REPORT BACK — Process delta summary

### Top 5 process changes (OLD → NEW)

1. **Verdict vocabulary**: bespoke binary (PROMISING / NEGATIVE with ad-hoc TAIL-CONTROL annotation hack) → canonical 9-band regime-aware decision tree applied to per-regime Δ vs σ_R.
2. **MERGE gate authority**: absolute Sharpe / DSR / PBO / PSR / OOS-trade / concentration FLOORS → per-regime Pareto-dominance vs BASELINE_V1 (Check 3d). DSR / PBO / PSR demoted to INFORMATIONAL.
3. **LM Master Phase 7.4 first deliverable** changed from "feature importance triage" to **Regime Attribution Table** (Item 0). Triage moves to Item 1.
4. **New Critic checks 3c (MANDATORY both EXP+CONF) and 3d (BUNDLE-CONFIRMATION-only)**. Checks 3a/3b reframed informational; SKIPPED at EXPLORATION budget.
5. **QE artifact mandate**: `regime_attribution.csv` per iteration, plus 3 one-time `_meta/` artifacts (`baseline_metric_anchors.csv`, `baseline_seed_regime_matrix.csv`, `regime_catalog.md`) authored at /044.

### Single highest-leverage change

**LM Master Item-0 Regime Attribution Table.** It is the load-bearing artifact that converts the entire framework from absolute-threshold to relative-regime-Pareto. Without it, Check 3c has no input, Check 3d has no baseline-σ tolerance, the 9-band decision tree collapses back to bundle-Sharpe-Δ-vs-baseline, and the diary cannot reframe NEG-CLEAN/NEG-CAT into regime-aware bands. Every other change in this reframe is downstream of this single artifact existing.

### How /043 closeout differs from /041 (OLD-methodology TAIL-CONTROL annotation hack)

- **/041** ran the OLD skill: bespoke verdict bands, TAIL-CONTROL was a hand-typed annotation grafted onto an EXPLORATION-NEGATIVE/PROMISING binary; LM Master Phase 7.4 led with importance triage; Critic Check 3 evaluated DSR > 0.95 + PSR > 0.95 + Sharpe-floor as HARD; no `regime_attribution.csv`; diary discussed regime context only narratively.
- **/043 (new skill)**: LM Master MUST emit the Item-0 table FIRST with bundle-role implications per regime. Critic SKIPs Checks 3a/3b (EXPLORATION), RUNS Check 3c (regime clarity is BLOCK-eligible if table missing/incoherent), and EXEMPTS Check 3d (component, not bundle). Verdict resolves on the 9-band tree per-regime — modal `REGIME-SPECIALIST-IS` for the predicted /043 LINK-only outcome (where the OLD framework would have stamped `EXPLORATION-NEGATIVE` for the predicted Δ ≈ −0.52 vs /036 portfolio, killing a legitimate bundle component). DSR/PBO/PSR regressions noted, not blocking. Diary documents `/044` bundle role candidacy (bull-2025-08, recovery-2025-11 specialist) directly. The TAIL-CONTROL annotation hack disappears entirely — TAIL-CONTROL is now band #4 in the canonical tree with a precise definition (`max_dd_R ≤ baseline − σ_dd_R` in vol-spike/liq-cascade).
