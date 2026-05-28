---
iteration: iter-v1/027
date: 2026-05-28
verdict: CONFIRMATION-TECHNICAL-FAILURE (no verdict; runner crashed at hard-assert post-training step)
subtype: TECHNICAL-FAILURE-NO-VERDICT (NEW v1 cell — runner crashed AFTER all 5 models trained but BEFORE comparison.csv emission; no Phase-7 evaluation possible; not a verdict cell on the F1/F3 reconciliation matrix)
axis_family: per-cohort-specialization (REPEAT; CONFIRMATION bundling /018 LINK + /019 ETH+gate; CONFIRMATIONs exempt from Axis Rotation Discipline)
axis: CONFIRMATION 5-model bundle (Pool A BTC-slice + Model C' LINK specialist + Model D LTC baseline + Model E DOT baseline + Model G ETH + asymmetric BTC-trend gate); --seeds 2 × ENSEMBLE_SIZE=5 inner × n_trials=35 = 10 paths/cell; pre-registered methodology-validation framing (NO-MERGE pre-committed regardless of outcome per /026 binding remediation #2)
cadence_position: cycle-3 CONFIRMATION (11th iter since /016 start; closes the cycle without verdict)
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c) — UNCHANGED
merge_decision: NO-MERGE (TECHNICAL FAILURE; comparison.csv never emitted; no Phase 7 evaluation possible; BASELINE_V1.md UNCHANGED regardless — /027 was pre-committed NO-MERGE under methodology-validation framing anyway)
tag: v0.v1-027-technical-failure (commit 9ce29c8)
---

# Iteration iter-v1/027 — Diary

## 1. Decision: NO-MERGE (CONFIRMATION-TECHNICAL-FAILURE — no verdict)

**CONFIRMATION-TECHNICAL-FAILURE.** All 5 models trained to completion across all walk-forward folds (13h wall-clock total — ~2.2× the 6h CONFIRMATION cap), but `run_baseline_v1.py` crashed at the F-AXIS #1 post-training hard-assert step with:

```
AttributeError: 'TradeResult' object has no attribute 'model_name'
```

The defensive runtime check mandated by LM Master Phase 4.5 §5 ("F-AXIS #1 hard-asserts MANDATE") to prevent /024-style dispatch defects was itself defective — the assert at `run_baseline_v1.py` referenced `r.model_name`, but `TradeResult` exposes the model attribution under a different name. The crash happened **after all 5 models had trained but before `comparison.csv` would have been emitted**, so the entire in-memory trade roster across the 10-path multi-seed bundle was lost. The only recoverable artifact is the per-cell OOF parquet (Optuna trial trajectories), which is insufficient to compute any F-falsifier or any Phase 7 evaluation metric.

**User decision 2026-05-28** (Option 3 of three options offered: Option 1 = rerun under fix; Option 2 = lighter targeted rerun; Option 3 = abandon /027 as TECHNICAL FAILURE without rerun): **ABANDON /027**. Cycle-3 closes without a CONFIRMATION verdict. Tag `v0.v1-027-technical-failure` issued at commit `9ce29c8`. No `v0.v1-027-final` tag will be issued.

**BASELINE_V1.md UNCHANGED** at `v0.v1-baseline-corrected` (`f8bc12c`). Note that /027 was already pre-committed to NO-MERGE under the methodology-validation framing per /026 Critic binding remediation #2 (pre-registered target band [+0.40, +0.75] absolute OOS Sharpe — structurally BELOW the +1.0 hard merge floor) — so even under a successful run, BASELINE_V1.md would not have been touched. The TECHNICAL FAILURE removes the methodology-validation *signal* (whether the per-cohort specialist architecture holds at multi-seed) but does not remove the *non-merge* outcome.

## 2. Backtest completion summary (compute did complete; only the post-processing crashed)

| Component | Trades | Wall-clock (s) | Notes |
|---|---:|---:|---|
| Model A (Pool BTC+ETH, BTC-slice filter applied at output stage) | 340 | 6,394 | trained successfully across all 25 walk-forward months |
| Model C' (LINK specialist, /018) | 192 | 7,688 | LINK-only training; R1 + R3 gates active |
| Model D (LTC baseline) | 147 | 9,779 | unchanged from baseline; R1 + R3 |
| Model E (DOT baseline) | 153 | 9,693 | unchanged from baseline; R1 + R2 + R3 |
| Model G (ETH + asymmetric BTC-trend gate, /019) | 199 | 13,224 | ETH-only training with post-hoc BTC-trend gate; fire-rate 19.60% inside /019's pre-registered [12%, 24%] band |
| **Total** | **1,031** | **~46,778 s (~13.0h)** | 2.2× the 6h CONFIRMATION cap |

**Diagnostic positives** (despite the crash):
- Model G fire-rate 19.60% landed inside /019's pre-registered [12%, 24%] band — the BTC-trend gate post-hoc filter is mechanically functioning.
- All 5 models completed all training folds across the full 24-month walk-forward window — no Optuna failures, no training-time crashes.
- The per-cell OOF parquet was emitted (Optuna trial trajectories captured) — recoverable but not sufficient for verdict.

## 3. What failed — runner post-training hard-assert was itself defective

The fault path:

1. LM Master Phase 4.5 §5 mandated F-AXIS #1 hard-asserts at the post-training output-assembly step of `run_baseline_v1.py`. Rationale: /024 had a dispatch defect that would have been caught earlier by a hard-assert; the lesson was codified into LM Master /027 §5 with three concrete assert templates.
2. QR brief Section 3.4 ADOPTED the mandate verbatim. Phase 5.5 PASSED. Critic Phase 6.0 PASS noted "F-AXIS #1 hard-asserts: 4 asserts at `run_baseline_v1.py` lines 2359/2363/2367/2380; all fire BEFORE comparison.csv emission".
3. The implementing code referenced `r.model_name`, which is NOT the attribute name on `TradeResult` (the dataclass exposes model attribution under a different identifier). The assert at runtime raised `AttributeError` before `comparison.csv` was written.
4. The 4 asserts had been "tested" only indirectly via the unit-test suite (33/33 pass per Critic Phase 6.0) — but the unit tests did not exercise the assert against a real `TradeResult` instance built from the production code path. The unit tests verified the assert *form*, not the assert's *semantic correctness against real objects*.

**The crash was preventable by a single integration smoke test** that constructs a `TradeResult` from the actual production code path and confirms the assert can read every attribute it touches.

## 4. Lesson (durable; carry-forward to cycle-4+)

**Defensive runtime checks must be unit-tested against real instances.** When a defensive assert references an object attribute, the unit-test suite must include a test that:
1. Constructs the object via the production code path (NOT a mock or partial fake).
2. Confirms the assert evaluates to True / False (depending on test expectation) WITHOUT raising `AttributeError`.

A passing "33/33 tests pass" + "Critic PASS" can both be silently downstream of a broken integration boundary. The lesson generalizes to ALL defensive checks added at Critic/LM Master mandate, NOT just F-AXIS #1 asserts. Phase 6.0 pre-flight is asked, at cycle-4 setup, to add a routine inspection step: "for every NEW defensive runtime assert mandated by LM Master, name the corresponding integration smoke test in the brief Section 9."

Secondary lesson on wall-clock budgeting: the 13h actual was 2.2× the 6h CONFIRMATION cap. The /027 brief Section 5.6 documented "4.5-5.5h modal parallel; 5.9-6.5h --seeds 1 fallback documented; kill 6.5h", but the runner exceeded both modal and fallback bands without triggering the kill-switch. The CONFIRMATION wall-clock observability is weaker than EXPLORATION; cycle-4 first CONFIRMATION should add explicit pre-flight progress logging at month-boundary granularity (one log line every walk-forward month, with median wall-clock per month) so the actual rate can be projected against the 6h cap before the run is half-finished.

## 5. Why NO RERUN — Option 3 rationale

The user offered three options at the crash:

- **Option 1**: rerun /027 in full under a fix. Cost: another ~13h compute. Risk: same hard-assert family could mask a different post-training defect.
- **Option 2**: lighter rerun — re-execute only the post-training assembly step from the OOF parquet (skip retraining). Cost: ~1-2h. Risk: the cached parquet may not have everything needed; the LightGBM in-memory state would need reconstruction; introduces a non-standard analysis path that doesn't match production semantics.
- **Option 3 (CHOSEN)**: abandon /027. Cost: no further compute. Risk: methodology validation question (specialists hold at multi-seed?) goes UNANSWERED. Cycle-3 closes with the question still open.

The user chose Option 3. Reasoning (per user directive): cycle-3 is already at the closing-iteration stage; the cycle-3 lessons are durable regardless of /027 outcome (10 EXPLORATIONs + /026 sanity have generated a structurally coherent finding set already); cycle-4 staging is more impactful than reproducing /027's methodology question, which can be re-asked under a CLEAN CONFIRMATION in cycle-4+ if the per-cohort architecture re-emerges as the natural bundling candidate.

## 6. Comparative impact on cycle-3 structural findings (the question /027 *would* have answered)

If /027 had succeeded:
- **PROMISING-METHODOLOGY outcome** (modal LM Master estimate +0.45 to +0.50 bundle OOS Sharpe, **at the NEGATIVE-leaning edge** of pre-registered [+0.40, +0.75]): cycle-3 would have closed with "per-cohort specialist architecture is **STRUCTURALLY VALIDATED at multi-seed**". Cycle-4 starts with high prior on D-specialist + 3-symbol pool composition (BTC+ETH+LINK with specialists overriding).
- **INERT outcome** (modal slightly above): cycle-3 closes with "partially validated — specialists hold but bundle does not lift". Cycle-4 pivots to methodology (sample-weighting; XGBoost head-to-head).
- **NEGATIVE outcome** (single-seed lottery dissolved at multi-seed): cycle-3 closes with "per-cohort isolation refuted at multi-seed". Cycle-4 re-questions per-cohort fundamentally.

With /027 abandoned, **the per-cohort architecture is held at "two single-seed PROMISING EXPLORATIONs + multi-seed unanswered"**. Cycle-4 first CONFIRMATION must address this question if and only if the per-cohort axis re-emerges as the natural bundling candidate. The structural lesson (per-cohort isolation only works with INDEPENDENT positive prior or orthogonal mechanism — /018 LINK isolated positive prior; /019 ETH only positive WITH gate; /020 BTC + /022 LTC both NEGATIVE catastrophic) carries forward to cycle-4 with multi-seed confirmation unanswered.

## 7. Cycle-3 ledger summary (closes here)

| iter | family | verdict |
|---|---|---|
| /016 | risk-primitive (R5 vol kill-switch) | EXPLORATION-NEGATIVE catastrophic |
| /017 | universe (+SOLUSDT 6-sym) | EXPLORATION-NEGATIVE anti-direction-INERT |
| **/018** | **per-cohort-specialization (LINK)** | **EXPLORATION-PROMISING-INERT favorable** (OOS Δ +0.80) |
| **/019** | **per-cohort-specialization (ETH+gate)** | **EXPLORATION-PROMISING** (OOS Δ +0.50) |
| /020 | per-cohort-specialization (BTC) | EXPLORATION-NEGATIVE catastrophic |
| /021 | methodology (basin diagnostic) | EXPLORATION-PROMISING-METHODOLOGY (H2 REFUTED, non-compoundable) |
| /022 | per-cohort-specialization (LTC) | EXPLORATION-NEGATIVE catastrophic |
| /023 | feature-family (funding rate z-score) | EXPLORATION-NEGATIVE LEARNED-clean |
| /024 | model-arch (regime-conditional) | EXPLORATION-NEGATIVE clean |
| /025 | feature-family (OI delta) | EXPLORATION-NEGATIVE LEARNED-CATASTROPHIC |
| /026 | pre-CONFIRMATION sanity | GREEN-WITH-FIX (analysis-only) |
| **/027** | **CONFIRMATION (per-cohort bundle)** | **TECHNICAL FAILURE (no verdict)** |

**Cycle-3 verdict distribution**: 2 PROMISING (/018 LINK, /019 ETH+gate) + 1 PROMISING-METHODOLOGY (/021) + 7 NEGATIVE + 1 sanity GREEN-WITH-FIX + 1 TECHNICAL FAILURE. **0 merges.** BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`).

## 8. Cycle-4 staging hooks (full cycle-3 closeout in `briefs-v1/cycle3_closeout.md`)

- **D-specialist MANDATORY**: /022 LTC NEGATIVE catastrophic at single-seed leaves the LTC drag (OOS Sharpe -1.05) unaddressed. Cycle-4 first or second EXPLORATION axis MUST be D-specialist or D-removal (universe contraction to 4 symbols).
- **C×E altcoin de-concentration required**: /026 5-model cross-correlation surfaced C_link × E_dot OOS +0.6027 breach (signal-level co-movement, not basin lottery). LM Master /027 §2 prediction "WILL NOT dissolve at multi-seed". Cycle-4 must address altcoin-cohort concentration explicitly (per-cohort drawdown brake; vol-target ceiling; regime-conditional kill switch — NOT per-symbol proportional caps, which are CLOSED at v1 catalog level per /020 closeout).
- **Sample-weighting + XGBoost candidates**: NEW NEVER-TRIED axes in v1 catalog. Sample-weighting (López de Prado AFML Ch. 4 uniqueness weighting; or hard-negative oversampling) is the obvious next labeling sub-axis. XGBoost head-to-head against LightGBM mirrors iter-v3/016 — though that closed at v3 catalog with NEGATIVE outcome, v1's substrate (LightGBM-specific basin) may respond differently.

## 9. Artifacts

- Brief: `briefs-v1/iteration_v1-027/research_brief.md` (Phase 5)
- LM Master Phase 4.5: `briefs-v1/iteration_v1-027/lgbm_advisor.md`
- Phase 5.5 gate: `briefs-v1/iteration_v1-027/phase5p5_gate.md` (PASS at `600fc42`)
- Critic Phase 6.0 pre-flight: `briefs-v1/iteration_v1-027/critic_preflight.md` (PASS at `4921226`)
- Implementation commit: `32cf7d5` (`feat(iter-v1/027): CONFIRMATION 5-model bundle dispatch + replacement semantics + hard-asserts`)
- TECHNICAL FAILURE closeout commit: `9ce29c8` (`docs(iter-v1/027): TECHNICAL FAILURE closeout — cycle-3 closes without CONFIRMATION`)
- Tag: `v0.v1-027-technical-failure` at `9ce29c8`
- Recoverable artifact: per-cell OOF parquet (Optuna trial trajectories only — not sufficient for verdict)
- LOST: comparison.csv, per_symbol.csv, feature_importance per cohort, trades.csv, Pareto front, multi-seed cross-correlation reanalysis

## 10. Critic / LM Master cycle-3 track record (forward-binding metadata)

- **LM Master methodology track cycle-3**: 6/6 PERFECT (every methodology recommendation /016-/025 that fired on a methodology axis was empirically validated; the /027 §5 hard-assert MANDATE is the exception that broke the streak — the *form* was right, but the *integration* was untested).
- **LM Master directional (verdict-class magnitude) track cycle-3**: 2/8 = 25% (modal priors hit on /018 + /019; missed on /016/017/020/022/023/024/025). Modal multi-seed +0.45-0.50 prediction for /027 is unverified.
- **Critic Phase 6.0 cycle-3**: every PASS was empirically validated for what it checked (look-ahead audit, anti-pattern scan, falsifier presence, cadence). The /027 PASS did NOT catch the defective hard-assert because Phase 6.0 inspects brief consistency + static code patterns, not integration semantics on real instances.

Forward-binding for cycle-4: a NEW pre-flight check item "integration smoke test for any NEW defensive runtime assert added at LM Master mandate" should be added to Phase 6.0's check list, with the brief Section 9 (test suite description) naming the specific test that exercises each NEW assert against a real instance.
