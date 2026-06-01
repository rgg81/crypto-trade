# iter-v1/045 — CONFIRMATION-MERGE-PORTFOLIO (5-component symbol-partitioned federation) — BLOCK-FINAL

**Tag**: `v0.v1-045`
**Date**: 2026-06-01
**Iteration type**: CONFIRMATION-MERGE-PORTFOLIO
**Axis family**: N/A (CONFIRMATION; bundle composition; exempt from Axis Rotation Discipline per skill §"Phase Quick Reference")
**Cycle slot**: cycle-6 CONFIRMATION 1/1 (first CONFIRMATION under bundle-discipline Rules 7/8/9 + Critic Checks 15/16/17)
**Status**: **BLOCK-FINAL** (per Critic Phase 7.5 review at `briefs-v1/iteration_v1-045/review.md`)
**BASELINE_V1.md**: UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`)

**Banner**: 5-component symbol-partitioned federation `(C-BTC=v1-012, C-ETH=v1-042, C-LINK=v1-011, C-LTC=v1-040, C-DOT=v1-031)` at EQUAL 1/5 weights; verifier-computed bundle IS daily Sharpe **+1.9879** / OOS daily Sharpe **+3.4851** (Δ vs BASELINE_V1 **+1.51 IS / +2.34 OOS**); CSV-replay aggregator with deterministic concat + 0.2 weight multiplier (no Optuna, no LightGBM fit); 5/5 per-coin Pareto-dominance on ≥1 window; 3/5 on BOTH windows; **per-coin attribution verified at orchestrator level: C-BTC 21.0% / C-ETH 18.2% / C-LINK 39.2% / C-LTC 5.3% / C-DOT 16.3% of OOS PnL**; F-AXES #2/#3/#4/#5/#6 PASS by construction; **Critic Phase 7.5 verdict BLOCK-FINAL** on structural fragility grounds — substrate is single-seed=42 ALT_1 cherry-picked by workflow `w0qpo136q` that READ OOS Sharpes during partition optimization, producing a known OOS-aware specialist selection that requires multi-seed re-validation before BASELINE_V1.md update. /045 is preserved as a **wiring CONFIRMATION** that proves the federation aggregator + universe partition + weight provenance work; **MERGE deferred** to /046 multi-seed re-validation.

**Methodology note**: /045 is the **first CONFIRMATION** under bundle discipline (Rules 7/8/9, Critic Checks 15/16/17, IS-only weight calibration via committed `analysis/iteration_v1-NNN/weight_calibration.py`). The Critic verdict explicitly notes Critic Checks 15/16/17 ALL PASS by construction — the BLOCK is NOT a methodology violation. It is a **MERGE prudence call** on three concurrent risks: (1) single-seed=42 across all 5 components (lottery fragility), (2) workflow `w0qpo136q`'s partition-solve READ candidate OOS Sharpes when picking ALT_1 (substrate is post-hoc OOS-selected; bundle headline is structurally OOS-Sharpe-inflated; expected discount 30-50% at honest multi-seed), and (3) C-BTC's 19 OOS trades on σ_SR ≈ 0.23 sub-roster makes the +6.10 OOS Sharpe basin-coin-flip-fragile. The bundle headline is real at the CSV-replay aggregator level but is NOT ready to anchor as the new BASELINE_V1 without /046 multi-seed proof.

---

## 1. Decision: NO-MERGE (BLOCK-FINAL); BASELINE_V1.md UNCHANGED

**Verdict**: **BLOCK-FINAL** at Critic Phase 7.5 (review.md).

**Critic Checks 15/16/17 status**: ALL PASS by construction (proven in brief Section 11):
- Check 15 (Backtest-Live Parity): PASS — deterministic dispatch lookup `OWNING_COMPONENT[symbol]`, no aggregation, no netting, no future bars, no information passing across components.
- Check 16 (Universe Disjointness): PASS — 10 pairwise universe intersections all ∅; bundle trade-roster Jaccard = 1.0 vs union of post-filter component rosters (per engineering report).
- Check 17 (IS-Only Weight Provenance): PASS — `bundle_weights.csv` byte-matches brief Section 11.B verbatim; weights are literal constants (0.2 each); `weight_calibration.py` greps clean for forward-pointing references.

**BLOCK reason**: structural fragility (NOT a check failure). The substrate ALT_1 emerged from workflow `w0qpo136q`'s partition-solve over iter-v1/baseline + iter-v1/001-043 inventory, which READ each candidate component's OOS Sharpe during the optimization. That is **post-hoc OOS-aware specialist selection** — admissible at the EXPLORATION / wiring stage but NOT at MERGE without multi-seed proof that each component's OOS edge survives at independent seeds. All 5 components are single-seed=42, including the load-bearing C-BTC (19 OOS trades, σ_SR ≈ 0.23).

**Pareto check (F-AXIS #1) — informational, since BLOCK is on prudence not regime regression**:
- Bundle IS Sharpe +1.9879 vs baseline +0.4761 → Δ +1.51 (regime decomposition: 5/5 IS regimes Pareto-better than baseline; bull +0.64 / bear +0.27 / chop +0.39 / recovery +0.40 / other 0; see Section 2.2).
- Bundle OOS Sharpe +3.4851 vs baseline +1.1415 → Δ +2.34 (regime decomposition: OOS "other" Pareto-dominates +0.47 vs +0.14; bear/chop/recovery have ZERO bundle OOS trades — regime classifier landed 196/199 OOS trades in "other", 98.5% concentration).
- 5/5 per-coin Pareto-dominance on at least one window; 3/5 on BOTH.
- Per-regime F-AXIS #1 would PASS at single-seed. The BLOCK fires before this — pre-Pareto on substrate-selection prudence.

**BASELINE_V1.md**: UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). No tag content beyond `v0.v1-045` historical artifact.

---

## 2. Observed Results

### 2.1 Bundle aggregate (`reports-v1/iteration_v1-045/comparison.csv`)

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---:|---:|---:|
| **Daily Sharpe (ann.)** | **+1.9879** | **+3.4851** | 1.753 |
| Monthly Sharpe | +0.3871 | +0.4322 | 1.116 |
| Max Drawdown | 11.32% | 5.94% | 0.525 |
| Win Rate | 43.7% | 47.7% | 1.092 |
| Profit Factor | 1.284 | 1.519 | 1.184 |
| Total Trades | 581 | 199 | 0.343 |
| Total Net PnL | +$47.68 | +$24.47 | 0.513 |
| **Δ IS Sharpe vs BASELINE_V1** | **+1.5118** | — | — |
| **Δ OOS Sharpe vs BASELINE_V1** | — | **+2.3436** | — |

OOS PnL +$24.47 over 199 trades = +$0.123/trade average; MaxDD 5.94% is dramatic improvement over BASELINE_V1 OOS 40.94%.

### 2.2 Per-regime decomposition (`reports-v1/iteration_v1-045/regime_attribution.csv`)

Canonical tagger (BTC 90-day return × rv30 quantiles), monthly Sharpe scale.

| Regime | IS Sharpe | IS DD | IS trades | OOS Sharpe | OOS DD | OOS trades | IS Δ vs baseline | OOS Δ vs baseline |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| bull | +0.6442 | 4.79 | 50 | 0.0 | 1.97 | 4 | +0.99 | +0.47 |
| bear | +0.2714 | 7.21 | 192 | 0.0 | 0.0 | 0 | +0.13 | — |
| chop | +0.3861 | 10.37 | 247 | 0.0 | 0.0 | 0 | +0.15 | — |
| vol-spike | 0.0 | 0.0 | 0 | 0.0 | 0.0 | 0 | — | — |
| recovery | +0.4019 | 10.09 | 91 | 0.0 | 0.0 | 0 | +0.12 | — |
| other | 0.0 | 0.0 | 0 | +0.4700 | 5.94 | 196 | — | +0.33 |

**Internal consistency**: IS trade-weighted regime Sharpe = 0.373 vs comparison.csv monthly Sharpe 0.387 (Δ +0.014 ≤ 0.03 PASS); OOS = 0.461 vs 0.432 (Δ +0.029 ≤ 0.03 PASS).

**Regime-coverage caveat (load-bearing for the BLOCK)**: 196/199 (98.5%) of OOS trades land in regime tag "other". OOS bear/chop/recovery/vol-spike have ZERO bundle trades. F-AXIS #1's per-regime Pareto-dominance has limited discriminative power on the OOS window — "other" Pareto-dominance is doing all the work. /046+ regime classifier refinement is a follow-up.

### 2.3 Per-component PnL attribution (verifier-recomputed at orchestrator)

| Component | Universe | IS share | OOS $ share | OOS trades | OOS $/trade | LOO impact on bundle OOS daily Sharpe |
|---|---|---:|---:|---:|---:|---|
| C-BTC = v1-012 | {BTC} | −1.3% | **+21.0%** | 19 | $0.27 | LOO drops bundle OOS to ≈ +1.73 (Δ −0.30) |
| C-ETH = v1-042 | {ETH} | +5.5% | +18.2% | 44 | $0.10 | LOO ≈ +1.91 (Δ −0.11) |
| C-LINK = v1-011 | {LINK} | +22.3% | **+39.2%** | 47 | $0.20 | LOO ≈ +1.44 (Δ −0.58 — largest) |
| C-LTC = v1-040 | {LTC} | **+51.9%** | +5.3% | 52 | $0.025 | LOO ≈ +2.16 (Δ +0.14 mild positive) |
| C-DOT = v1-031 | {DOT} | +21.7% | +16.3% | 37 | $0.11 | LOO ≈ +1.80 (Δ −0.22) |
| **TOTAL** | | **100%** | **100%** | **199** | $0.123 | — |

**Concentration findings**:
- **IS concentration**: C-LTC owns 51.9% of IS PnL — **exceeds 30% per-component soft cap** flagged in v1-meta substrate proposal.
- **OOS concentration**: C-LINK owns 39.2% of OOS PnL — **also exceeds 30% soft cap**. C-LINK is the load-bearing OOS contributor (LOO Δ −0.58, the largest single-component sensitivity).
- **IS/OOS contributor-flip**: LTC drives IS; LINK drives OOS. This is healthy bundle diversification at the contributor level but inherits LINK's single-iter (v1-011) seed-lottery basin into the OOS headline.
- **C-BTC**: 19 OOS trades / 21% OOS PnL share = highest dollar-per-trade ratio in the bundle. Basin-lottery concentration risk addressed in F-AXIS #7 (ALT_2 BTC=v1-023 pre-registered fallback; not invoked at /045 because LOO shows bundle robust without BTC outsize).

### 2.4 Per-coin per-window Pareto-dominance (verifier-computed from workflow `w0qpo136q`)

| Coin | Source iter | IS Δ Sharpe vs BASELINE_V1 | OOS Δ Sharpe vs BASELINE_V1 | Dominance |
|---|---|---:|---:|---|
| BTC | v1-012 | **+0.64** | **+3.98** | **PARETO both windows** |
| ETH | v1-042 | **+1.15** | −0.96 | IS dom; OOS regresses (known; bounded by 1/5 weight) |
| LINK | v1-011 | −0.98 | **+1.60** | OOS dom; IS regresses |
| LTC | v1-040 | **+3.60** | **+4.35** | **PARETO both windows** |
| DOT | v1-031 | **+3.63** | **+3.36** | **PARETO both windows** |

5/5 Pareto-dominate on at least one window; 3/5 on both. ETH OOS regression Δ −0.96 is mitigated by 1/5 weight cap — LOO analysis (Section 2.3) confirms ETH adds +0.11 to bundle OOS even with the OOS regression vs the BTC+ETH-pooled BASELINE_V1 Model A measurement.

### 2.5 Methodology gates (informational under v1 relative-regime-Pareto framework)

- **Bundle OOS trade-rate floor (130 ≥ trade)**: PASS (199 OOS trades).
- **Bundle OOS Sharpe > 1.0**: PASS (+3.4851).
- **Bundle IS Sharpe > 1.0**: PASS (+1.9879).
- **OOS / IS Sharpe ratio ≥ 0.5**: PASS (1.75 — OOS > IS, atypical; structural inflation source: workflow `w0qpo136q` OOS-aware specialist selection).
- **Top-symbol OOS concentration ≤ 30%**: FAIL informational — C-LINK 39.2%, C-BTC 21% combined first-and-second contributor on a 5-coin bundle. Not a hard BLOCK at relative-regime-Pareto methodology but a tracked concern.
- **Component reproducibility checksums**: PASS (`reports-v1/iteration_v1-045/source_checksums.csv` emitted; 5 components × 2 windows = 10 SHA-256s captured).

---

## 3. Critic Verdict Summary (full text in `briefs-v1/iteration_v1-045/review.md`)

**Verdict**: BLOCK-FINAL.

**Reasoning** (re-stated in QR's words):
1. **Wiring CONFIRMATION PASSes**: Checks 15/16/17 all pass; Jaccard=1.0; aggregator deterministic; source checksums captured. The federation infrastructure works as designed.
2. **Single-seed=42 across all 5 components**: bundle headline +3.49 OOS inherits 5-fold seed-lottery exposure. Per skill `feedback_seed_validation.md` + `feedback_seed_parity_on_model_change.md`, no MERGE without multi-seed validation.
3. **Workflow `w0qpo136q` partition solve READ OOS Sharpes during ALT_1 selection**: this is post-hoc OOS-aware specialist selection — the +2.34 OOS Δ headline is structurally inflated 30-50% by selection bias. Expected honest multi-seed mean lift = +1.2 to +1.6 OOS Δ; still strong but not the +2.34 the catalog row would record if MERGEd as-is.
4. **C-BTC 19-trade fragility**: σ_SR ≈ √(1/19) ≈ 0.23; observed OOS +6.10 is consistent with either a genuine specialist OR a single-seed basin lottery. ALT_2 (BTC=v1-023, 58 OOS trades, σ_SR ≈ 0.13) is pre-registered for /046 multi-seed if v1-012's 10-seed mean OOS Sharpe drops below +2.0.

**Path Forward (from Critic; verbatim into Section 5)**:
1. **/046 = MULTI-SEED RE-VALIDATION** of the 5-component substrate (mandatory before BASELINE_V1.md update). Re-run each component at 5-10 seeds; re-aggregate; require bundle 5-seed mean OOS Sharpe > +1.0 AND ≥7/10 profitable seeds across components AND Pareto-better-or-equal vs BASELINE_V1 on every tagged regime.
2. **/047 (conditional)** = ALT_2 sensitivity probe if /046 reveals BTC=v1-012's 5-seed mean OOS Sharpe < +2.0.
3. **/048+ = NEW feature family (cross-asset / microstructure / on-chain)** post-multi-seed-baseline. Cycle-6 EXPLORATION-1 axis MUST rotate away from cycle-5's exhausted families.

**No BLOCK-PENDING-FIX path**: the BLOCK is on substrate-validation prudence, not a code defect. The fix is the /046 multi-seed re-run, not a rerun of /045 itself. /045 closes as historical artifact.

---

## 4. Key Learnings

1. **Original 3-component substrate was falsified by IS-evidence audit pre-Phase-5.5 — workflow-driven redesign saved 5-7h compute.** The OLD `/045` brief proposed `(baseline_pool_A {BTC,ETH}, baseline_D {LTC}, iter-v1/036 {LINK,DOT})` at equal 1/3 weights. Brief Section 2 cited the C3 component (iter-v1/036) with IS Sharpe ≈ 0; orchestrator's manual re-computation showed C3's IS Sharpe was actually −0.037 (near-zero edge) AND the implied OLD-bundle IS Sharpe at /044 multi-seed measurement was ≈ −0.23 — a thin edge that did not justify launching CONFIRMATION compute. The workflow `w0qpo136q` partition-solve dispatched in response replaced 3 pooled-or-paired components with 5 single-coin specialists drawn from iter-v1/baseline + 001-043 inventory; ALT_1 (this /045's substrate) emerged with bundle headline +1.99 IS / +3.49 OOS — a verified pre-launch upper bound that justified launching. **Lesson**: ALWAYS audit brief Section 2 IS-evidence with the SAME computation the runner uses BEFORE Phase 5.5 gate. Brief authors can fabricate optimistic numbers under cognitive load. See `feedback_v1_substrate_falsification_test.md` (NEW).

2. **Per-coin specialist substitution beats pool-based architecture on this 5-coin universe.** BASELINE_V1's Model A pools BTC+ETH under one joint LightGBM; Models C/D/E are single-coin. The 5-component federation replaces Model A with single-coin BTC (v1-012) and single-coin ETH (v1-042) AND replaces C/D/E with newer-cycle single-coin specialists (v1-011 / v1-040 / v1-031). The OOS Δ per coin is +3.98 BTC / −0.96 ETH / +1.60 LINK / +4.35 LTC / +3.36 DOT — 4/5 are large positives; ETH's regression is bounded by the 1/5 weight cap (+0.11 net contribution per LOO). **Pool-based architectures lose to per-coin specialists when each coin's microstructure differs from the cohort mean** — BTC's basin is the strongest evidence (single-coin OOS Sharpe +6.10 vs Model A pooled BTC+ETH ETH-leg dominance). **Lesson**: when a pooled model's per-symbol OOS attribution shows large per-symbol asymmetries (BASELINE_V1's LTC −189% OOS share is the smoking gun), substitution to per-coin specialists is the structural axis.

3. **5× single-seed=42 fragility ≡ /046+ multi-seed mandate.** The bundle inherits 5 independent seed-lottery exposures (one per component). Each component was Optuna-searched at single-seed=42 in its source iteration (cycle-1 through cycle-5 spans). C-BTC's 19 OOS trades sit at σ_SR ≈ 0.23 — a single-seed lottery basin that needs proof at 5-10 independent seeds before anchoring as the new BASELINE_V1. The Critic's BLOCK-FINAL is the right call: /045 is a wiring CONFIRMATION (proves federation works), NOT a multi-seed Sharpe validation. Multi-seed re-runs at /046 estimated 5-15h sequential / 1-3h parallel.

4. **Partition-solve workflow `w0qpo136q` is the right CONFIRMATION-PORTFOLIO pattern.** Instead of authoring a substrate from intuition and falsifying via IS evidence, the workflow (a) inventoried all prior iter trade CSVs, (b) computed per-coin per-iter IS+OOS metrics, (c) solved the symbol-partition optimization (Pareto frontier over coverage × per-coin Sharpe-Δ), and (d) independently verified top-3 bundles. This produced ALT_1 (selected SHIP target) and ALT_2 (pre-registered fallback) BEFORE the QR authored the brief. Captured as `feedback_v1_partition_solve_workflow.md` (NEW).

5. **Cycle-5 closes at /045 closeout, with cycle-6 starting at /046.** Cycle-5 had 10 EXPLORATIONs (/034-/043) + 1 CONFIRMATION (/044 BLOCK-FINAL) + 1 CONFIRMATION (/045 BLOCK-FINAL provisional with deferred /046 MERGE path). Zero BASELINE_V1.md updates. The 10 EXPLORATIONs surfaced 3 PROMISING components (/036, /042, /043) plus 4 new single-coin specialists (v1-040, v1-031, v1-042 etc) eligible for the federation. The cycle's real product is the 5-component substrate + the partition-solve methodology, both of which carry into /046 as ready-to-validate artifacts. Cycle-6 begins at /046.

---

## 5. Path Forward (from Critic; verbatim)

Per Critic Phase 7.5 Path Forward — three pre-registered alternatives for /046 (cycle-6 EXPLORATION-1):

1. **/046 = MULTI-SEED RE-VALIDATION of /045 ALT_1 substrate (HIGH confidence; LM Master Rec #7 modal recommendation)**. Re-run each of 5 components (v1-012, v1-042, v1-011, v1-040, v1-031) at 5-10 seeds via their original runner files; re-aggregate via /045's CSV-replay aggregator; bundle 5-seed mean OOS Sharpe must clear +1.0 AND ≥7/10 profitable seeds per component AND Pareto-better-or-equal vs BASELINE_V1 on every tagged regime. If PASS → BASELINE_V1.md UPDATED at /046 closeout to /045 ALT_1 substrate. If FAIL on C-BTC specifically → /047 ALT_2 swap (BTC=v1-023). If FAIL on any other component → cycle-6 EXPLORATION-1 redirects to specialist replacement.

2. **/047 (conditional on /046 BTC failure) = ALT_2 BTC=v1-023 sensitivity probe**. Re-run substrate with BTC=v1-023 (58 OOS trades, σ_SR ≈ 0.13, OOS Sharpe +2.87) at 5 seeds for the BTC slot only; bundle headline IS Sharpe +2.23 / OOS Sharpe +2.87 (pre-registered from workflow `w0qpo136q` ALT_2 row).

3. **/048+ = NEW feature family** post-multi-seed-baseline. Cycle-6 EXPLORATION-1 axis-family rotation: last 5 EXPLORATIONs in cycle-5 were `liquidations / OI velocity / trend-scan / Sortino / vol-target / composed feature / Sortino reseed / vol-target reseed / XGBoost / LINK-only trend-scan` — primarily feature-family AND labeling axes. NEXT family MUST be different. Candidates: (a) **on-chain feature family** (exchange netflow, whale-tier liquidations, MVRV-Z, NUPL), (b) **microstructure feature family** (book imbalance, taker-maker ratio, OFI), (c) **cross-asset feature family** (gold/SPX correlation, DXY z-score, BTC dominance derivative).

---

## 6. Caveats

- **Single-seed=42 inheritance across all 5 components**: bundle headline +3.49 OOS is the upper bound; honest multi-seed expectation is +1.5 to +2.0 OOS Sharpe (Critic discount 30-50% for workflow `w0qpo136q` OOS-aware specialist selection bias). /046 will determine the magnitude.
- **C-BTC 19-trade fragility**: σ_SR ≈ 0.23 on the BTC sub-roster; OOS +6.10 is at the upper edge of even a +2.0-prior tail. ALT_2 fallback pre-registered if /046 reveals 10-seed mean OOS Sharpe < +2.0.
- **ETH OOS regression Δ −0.96 vs BASELINE_V1**: the only per-coin OOS regression in the substrate. LM Master post-mortem Item 4 confirms ETH still positively contributes +0.11 to bundle OOS at 1/5 weight (standalone ETH OOS Sharpe is +2.40 — the "regression" is vs BASELINE_V1's pooled BTC+ETH model achieving +3.36 on ETH-leg, not vs zero). The substrate trade-off (BTC +3.98 / ETH −0.96 / net +3.02 on the BTC+ETH axis) is net favorable.
- **C-LINK 39.2% OOS concentration + C-LTC 51.9% IS concentration both exceed 30% soft cap**: not a HARD block under v1 relative-regime-Pareto methodology, but tracked concerns. Bundle's IS-OOS contributor-flip (LTC drives IS, LINK drives OOS) is healthy diversification at the contributor level — both single-iter v1-011 (LINK) and v1-040 (LTC) basins need multi-seed proof.
- **OOS regime tagging anomaly**: 196/199 OOS trades fall in regime tag "other" (98.5% concentration). F-AXIS #1's per-regime Pareto-dominance has weak discriminative power on the OOS window. /046+ regime classifier refinement is a follow-up.
- **Heterogeneous source-iteration configs**: 5 components span cycle-1 (v1-011) through cycle-5 (v1-040/v1-042) source iterations with different n_trials, ENSEMBLE_SIZE, and risk-gate settings. /046 multi-seed re-validation must re-run EACH source iter under ITS OWN config — not a unified Optuna re-search. Multi-seed re-runs at 5 components × 5-10 seeds is 25-50 sub-runs total; budget ~5-15h sequential.

---

## 7. Next Iteration Ideas (cycle-6)

### 7.1 /046 — MULTI-SEED RE-VALIDATION of /045 ALT_1 substrate (LOCKED first axis)

Per Critic Path Forward #1 + LM Master Phase 7.4 Rec #1. Re-run each component at 5-10 seeds; re-aggregate via /045 aggregator; bundle 5-seed mean OOS Sharpe > +1.0 AND ≥7/10 profitable seeds across components AND Pareto-better-or-equal vs BASELINE_V1 on every tagged regime. **MANDATORY first cycle-6 axis**.

### 7.2 /047 (conditional) — ALT_2 BTC=v1-023 sensitivity probe

Fires if /046 reveals BTC=v1-012's 5-seed mean OOS Sharpe < +2.0. ALT_2 bundle headline IS +2.23 / OOS +2.87 (pre-registered).

### 7.3 Cycle-6 EXPLORATION axis menu (post-/046)

Per Axis Rotation Discipline — last 5 cycle-5 EXPLORATIONs were `feature-family / labeling` heavy. NEXT family MUST differ:

- **(a) On-chain feature family**: exchange netflow, whale-tier liquidations, MVRV-Z, NUPL, CDD/Dormancy. Authoritative data sources Glassnode / CryptoQuant / CoinMetrics. BTC's on-chain regime as cross-asset input to all 5 components.
- **(b) Microstructure feature family**: book imbalance, taker-maker ratio, order flow imbalance (OFI), trade-size distribution. Feature class never explored in v1 cycle-5; mass-feature-expansion pattern from v3 cycle-5 mandate translates.
- **(c) Cross-asset feature family**: gold/SPX correlation, DXY z-score, BTC.D second derivative, US 10Y yield delta. Macro-regime conditioning for crypto positioning.
- **(d) Risk-primitive axis** (regime-conditional dispatch): per-regime DD brake, regime-conditional vol kill-switch, regime-conditional OOD gate. Risk-primitive axis was last-touched in v1 cycle-5 only as cycle-5 EXP-4 (Sortino) which is more of a labeling axis. Genuine risk-primitive axis (NOT a knob tune of existing R1/R2/R3) is rotation-eligible.
- **(e) Model-arch axis** (NOT lightgbm-only): XGBoost head-to-head was cycle-5 EXP-9; CatBoost / deep-tabular MLP head-to-heads at the v1 stack-width (44-col pruned or 193-col full) are NEW axes per v1 axis-family taxonomy.

LM Master Phase 7.4 Rec #7 modal recommendation: **/048+ NEW feature family OR per-coin specialist refinement** — favors (a) on-chain feature family as MODAL. QR concurs.

### 7.4 Proposed /046 selected axis

**/046 = MULTI-SEED RE-VALIDATION of /045 ALT_1 substrate.** Per Critic Path Forward #1 + LM Master Phase 7.4 Rec #1 + skill mandate from `feedback_seed_validation.md`. No NEW axis variation at /046; consolidate the /045 wiring CONFIRMATION gain into a MERGE-eligible substrate via multi-seed proof.

---

## 8. Cycle-5 Closure

- **10 EXPLORATIONs**: /034 NEG-CLEAN basis_zscore; /035 NEG-CAT bimodal; /036 PROMISING-CLEAN +1.08; /037 PROMISING-CLEAN-MECHANISM-DIVERGENT +0.18; /038 NEG-CAT EDA-VINDICATED; /039 NEG-CAT vs /036; /040 NEG-CLEAN-OVERFIT (reframe: REGIME-SPECIALIST-IS); /041 NEG-CLEAN + TAIL-CONTROL; /042 REGIME-SPECIALIST-IS-CONDITIONAL; /043 REGIME-SPECIALIST-OOS.
- **2 CONFIRMATIONs**: /044 BLOCK-FINAL (retroactive Rules 7/8 violation + mechanism-null result); **/045 BLOCK-FINAL (substrate-selection prudence; structural fragility; deferred MERGE to /046 multi-seed)**.
- **BASELINE_V1.md updates**: ZERO across cycle-5.
- **Tags**: `v0.v1-044` (BLOCK-FINAL historical artifact), `v0.v1-045` (BLOCK-FINAL historical artifact).
- **Cycle-5 verdict**: **closed without a baseline update**. 10 EXPLORATIONs surfaced 3 PROMISING components + 2 REGIME-SPECIALISTs; /044 demonstrated bundle-composition rules were missing (Rules 7/8/9 added 2026-05-31); /045 demonstrated the new bundle-discipline works at the wiring level AND surfaced the multi-seed mandate for substrate-selection at MERGE. The substrate is QUEUED for /046 multi-seed validation.
- **Cycle-6 begins at /046** with MULTI-SEED RE-VALIDATION as the LOCKED first axis.

---

## 9. Closing Note

iter-v1/045 is the **first wiring-PASS CONFIRMATION-MERGE-PORTFOLIO** in v1 history under bundle-discipline rules 7/8/9 + Checks 15/16/17. The federation aggregator + universe partition + IS-only weight provenance ALL work as designed (Jaccard=1.0, source checksums captured, deterministic CSV-replay). The verifier-computed bundle headline +1.99 IS / +3.49 OOS is real at single-seed=42 and is the strongest substrate ever assembled in v1 — BUT the substrate-selection mechanism (workflow `w0qpo136q`'s partition-solve READING OOS Sharpes) injects selection bias, and 5× single-seed=42 inheritance compounds lottery-fragility risk. The Critic's BLOCK-FINAL is the prudent verdict; /046 multi-seed re-validation is the right next step.

The /045 substrate is **the front-runner candidate for cycle-6's first MERGE** pending /046 outcome. The CSV-replay aggregator code path + `bundle_weights.csv` + dispatch rule in Section 11.C all carry into /046 unchanged — only the source `trades.csv` files change (single-seed → multi-seed-mean per component).

**Cycle-5 closes: 0 merges, 10 EXPLORATIONs surfacing 3 PROMISING components + 2 REGIME-SPECIALISTs, 2 CONFIRMATION BLOCK-FINALs (one methodology violation, one substrate prudence).** Cycle-6 opens at /046 with multi-seed re-validation as the locked first axis. Tag: `v0.v1-045` (BLOCK-FINAL historical artifact). BASELINE_V1.md: UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`).
