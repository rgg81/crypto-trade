# Phase 7.5 Critic Review — iter-v1/039

OVERALL: EXPLORATION-NEGATIVE-CATASTROPHIC — bundle OOS Sharpe Δ vs /036 anchor = +1.0393 − 1.7465 = **−0.7072**, sitting deep inside the brief's NEG-CAT band (Δ < −0.45). H1 stacking-compoundability hypothesis FALSIFIED; mechanism is universe-dependent (5-cohort), not universe-independent. Per-symbol diagnostic does NOT trigger PROMISING-DOT-ONLY (LINK OOS PnL +68.45pp is positive, not < −10pp). /044 routing LOCKED SEPARATE.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION

## QR Response Considered (Round 2 only)
Not invoked. Verdict bands resolve unambiguously from comparison.csv and per_symbol.csv; no clarification could move the verdict band from NEG-CATASTROPHIC. Skipping straight to FINAL.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Foundation: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` verified (grep confirms; iter-v3/058 fix preserved). `tests/test_lookahead_embargo.py` present. NO new src/ ML code touched in /039 — dispatch elif at `run_baseline_v1.py:4035-4140` is composition-only of /035 + /036 + /037 production paths. `cross_sectional.py:1325,1345` carry the corrected formula. Zero unexplained matches for A1 signature.

### Check 2 — Embargo Width: PASS
Unchanged from /036 + /037 baselines. Trend-scanning embargo (forward-window 21d max horizon) propagated via shipped `--label-mode trend_scanning` path; CV gap unchanged.

### Check 3 — Multiple-Testing Correction: FAIL (informational at TYPE=EXPLORATION)
- DSR = −11.4722 OOS (vs threshold 0.95); PSR_monthly_vs_1 = 0.4809 OOS (vs threshold 0.95); n_effective_trials = 9 (single-seed=42, n_trials=18). Per skill §5.1 Check 3 axis FAILs are INFORMATIONAL for EXPLORATION — not BLOCK-triggering. Noted for catalog.

### Check 4 — IC Correlation: N/A
No new features added. V1_FEATURE_COLUMNS_PRUNED (44 cols) unchanged. `ic_matrix.csv` present but uninformative for this iteration.

### Check 5 — ADF Stationarity: N/A
No new features. `adf_test.csv` present, no new rows.

### Check 6 — Pareto Dominance: N/A
Single seed=42 EXPLORATION. `basin_diagnostics/v1_cross_seed_variance.csv` records n_outer_seeds=1; Pareto evaluation deferred to /044 multi-seed.

### Check 7 — Reproducibility: PASS
HEAD at `2e5630e`. `"v1-039"` present in catch-all exclusion tuple at line 4157. Dispatch elif at 4035 fires BEFORE catch-all. Pre-flight asserts at 4045-4069 cover label_mode/optuna_objective/universe/vol_ceiling. Banner emitted at lines 4070-4083. Per-cohort isolation asserts at lines 4119-4126. `feature_columns=active_feature_columns` (explicit, not None).

### Check 8 — Hypothesis-Implementation Alignment: FAIL (H1 falsified, F-AXIS #1 NEG-CAT fires; mechanism resolution: UNIVERSE-DEPENDENT)
- **H1**: predicted Sortino × trend-scan substrate would compound, lifting OOS Sharpe ≥ /036's +1.7465 by +0.10 to +0.30 in PROMISING tails. **Observed**: bundle OOS Sharpe **+1.0393** → Δ vs /036 = **−0.7072**, deeply inside NEG-CAT band (< −0.45). H1 is FALSIFIED.
- **H1b falsifier**: brief explicitly says "if Δ vs /036 < +0.10 AND per-symbol LINK + DOT OOS roster ±25pp of /036 → REFUTED, /044 SEPARATE". Observed LINK OOS PnL **+68.45pp** vs /036's **+108.91pp** (Δ −40.46pp, outside ±25pp); DOT OOS PnL **+44.40pp** vs /036's **+113.63pp** (Δ −69.23pp, outside ±25pp). H1b REFUTED.
- **F-AXIS #3 per-symbol sign-match**: BOTH LINK and DOT regress in the SAME direction (both negative Δ); does NOT meet the directional-sign-mismatch PROMISING-DOT-ONLY condition (which requires LINK < −10pp AND DOT > +50pp — observed DOT is +44.40pp absolute, NOT a + Δ; it's a regression). MECHANISM RESOLUTION: Sortino × trend-scan substrate is **universe-dependent**; the /037 DOT-amplification lift was a 5-cohort-pooled artifact (Pool-A averaging with BTC/ETH/LTC) that does not survive substrate replacement.
- **F-AXIS #6 Jaccard**: OOS Jaccard vs /036 = **0.0878** (LINK 0.0625, DOT 0.1071) per `basin_diagnostics/v3_roster_overlap.csv`. Brief expected band [25%, 75%]; observed **far below 10% threshold → BASIN-RELOCATION-ARTIFACT** subtype. The composition fully relocated the basin away from /036's specialist optimum.
- **IS catastrophe**: IS Sharpe **−0.1530** (Δ −0.24 vs /036's +0.0843), IS Max DD **75.84%** (vs /036's 61.53%, +14.31pp WORSE), IS total_net_pnl **−17.64** (vs /036's +9.64, sign-flipped). Bundle blew up IS while OOS landed in lottery-PROMISING absolute (+1.04 standalone) but well below /036's substrate. Classic basin-relocation: IS over-fitted to a degenerate region; OOS happened to be in a less-painful corner but missed /036's edge by 0.71 Sharpe.

### Check 13 — Anti-Pattern Static Scan: PASS
- A1: 5 matches in src/ all carry `- embargo_ms` subtraction or appear in documentation comments. No bug signature.
- A2-A11: not applicable (no new labeling, no scaler, no parquet append, no new feature parquet path).
- A12-A13: not applicable (no new methodology-axis output fields).
- A14 (stateful gate deadlock): not applicable (no new stateful gate; R1/R2/R3 inherited from /036).

### Check 14 — Axis Family Validation: PASS
- Brief Section 0.6 declares `loss-function × per-cohort-specialization` DOUBLE-REPEAT COMBO. src/ diff at 2e5630e touches: `run_baseline_v1.py` (dispatch elif + V1_ITER039_UNIVERSE export + exclusion-tuple), `tests/test_iteration_v1_039.py` (NEW). No feature additions, no labeling changes (uses shipped `trend_scanning`), no Optuna search space changes (uses shipped `sortino` objective). Family declaration CLEAN.
- Counter at 2/5 for both `loss-function` (last /037) and `per-cohort-specialization` (last /036). 5+ monoculture rule cleanly clear. Justified as direct compoundability test of two PROMISING axes.

## Observed Results vs Verdict Bands (Section 11.6 — anchor /036)

| Metric | /036 anchor | BASELINE_V1 | /039 | Δ vs /036 | Δ vs baseline | Band |
|---|---|---|---|---|---|---|
| OOS Sharpe | +1.7465 | +0.6637 | **+1.0393** | **−0.7072** | +0.3756 | **NEG-CAT (< −0.45)** |
| IS Sharpe | +0.0843 | +0.2829 | **−0.1530** | **−0.2373** | −0.4359 | catastrophic |
| OOS Max DD | 23.28% | 40.94% | **27.52%** | +4.24pp | −13.42pp | mild OOS |
| IS Max DD | 61.53% | ~37% range | **75.84%** | +14.31pp | catastrophic | catastrophic IS |
| OOS trades | 105 | 189 | 87 | −18 | −102 | below /036 (within band [80,160]) |
| IS trades | 281 | 621 | 252 | −29 | −369 | within band [200,400] |
| LINK OOS PnL% | +108.91 | +34.23 | **+68.45** | −40.46pp | +34.22pp | regression (within F3 band [−30, +30]? **NO, −40 outside**) |
| DOT OOS PnL% | +113.63 | +1.96 | **+44.40** | −69.23pp | +42.44pp | regression (outside F3 band) |
| OOS Jaccard vs /036 | 1.000 | n/a | **0.0878** | −0.91 | n/a | BASIN-RELOCATION (< 10% floor) |
| OOS WR | 54.3% | 45.x% | 49.4% | −4.9pp | — | regression |
| OOS PF | 1.6117 | — | 1.4364 | −0.18 | — | regression |
| DSR (OOS) | −3.82 | (anchor) | **−11.47** | −7.65 | regression | informational |
| PSR_monthly_vs_1 (OOS) | 0.594 | 0.079 | 0.481 | −0.11 | +0.40 | regression vs /036 |

## Verdict Cell

**EXPLORATION-NEGATIVE-CATASTROPHIC** per brief Section 11.6 (Δ vs /036 < −0.45). The observed Δ −0.71 sits 0.26 below the NEG-CAT threshold — not borderline, not lottery: structurally inside catastrophic-collision territory. The mechanism resolves cleanly: **Sortino is universe-dependent**. The /037 Sortino-driven DOT amplification (+39.30pp OOS lift on 5-cohort) depended on the Pool-A averaging effect of BTC/ETH/LTC co-training; when stripped to a 2-cohort LINK+DOT substrate, the basin relocates 91% of trades away from /036's specialist optimum (Jaccard 0.088), IS collapses (Sharpe −0.15, Max DD 75.84%), and OOS lands in a +1.04 Sharpe corner that is far below /036 standalone. The two PROMISING axes ARE NOT independent gradients — they COMPETE on /036's substrate. **PROMISING-DOT-ONLY does NOT fire**: LINK OOS PnL is +68.45pp (POSITIVE absolute; the brief's PROMISING-DOT-ONLY requires LINK < −10pp). Both cohorts regress in absolute terms vs /036, with LINK losing 40pp and DOT losing 69pp.

**/044 routing finalization**: per brief Section 11.6 NEG-CAT row + Section 8 row 5, **/044 = TWO SEPARATE multi-seed CONFIRMATIONS**: /044-A = /036 alone (LINK+DOT trend-scan, --seeds 2/5/10, --n-trials 35, ENSEMBLE_SIZE=5); /044-B = /037 alone (5-cohort Sortino, same spec). NO HYBRID BUNDLE. The cycle-5 substrate has STABILIZED at /036 alone (PROMISING-CLEAN single-seed, +1.7465) + /037 weakly (PROMISING-CLEAN single-seed, +0.8388 but Pool-A-dependent). Sortino × per-cohort-specialization COMBO axis is **CLOSED at /039**.

## Recommendations to QR

1. **Hybrid axis (loss-function × per-cohort-specialization) is CLOSED for v1 cycle-5.** Do not re-launch at higher seed budget; do not propose tighter Optuna bounds; do not propose subset-substrate variations. The basin-relocation Jaccard (0.088) is structural evidence that the COMPOSITION's loss surface has no common region with /036's specialist optimum — multi-seed will not rescue a basin that lives in a different region of parameter space.
2. **Stacking-interaction probes require pre-EDA Jaccard prediction.** /039 EDA predicted Jaccard 0.30-0.50 (basin reuse with re-selection); observed 0.088 (full relocation). Future stacking probes should pre-register a Jaccard floor as a STAGE-1 falsifier: if predicted < 0.30, don't launch — the stacking question is moot when the basins don't overlap.
3. **Cycle-5 substrate has stabilized.** With /039 NEG-CAT closing the hybrid composition axis, cycle-5 PROMISING substrates reduce to: /036 (PROMISING-CLEAN, OOS +1.7465, single-seed, anchored) and /037 (PROMISING-CLEAN-weakly, OOS +0.8388, Pool-A-dependent). /044 must validate each SEPARATELY at multi-seed before any bundling discussion can occur in cycle-6.

## Path Forward (mandatory — proposed axes for /042 + /043; cycle-5 has /040 + /041 pre-drafted)

Prior 5 EXPLORATION families (cycle-5): /034 feature-family, /035 labeling, /036 per-cohort-specialization, /037 loss-function, /038 risk-primitive, /039 loss-function×per-cohort REPEAT-COMBO. /040 and /041 are pre-drafted (orchestrator confirmed). Three axes for /042 + /043 from families NOT used in the prior 5 EXPLORATIONs:

1. **Ternary prediction-architecture** — family: `prediction-architecture` (UNUSED in cycle-5). Replace the binary {long, short} class head with a ternary {long, neutral, short} head + per-symbol neutral-class threshold via Optuna. Mechanism: LightGBM MODELS the trade-skip directly rather than relying on a post-hoc confidence threshold. Orthogonal to loss-function (which is Sortino vs Sharpe scalar), labeling (triple-barrier vs trend-scan label generation), feature engineering, and risk-gate axes. Critic /037 + /038 reviews already nominated this axis; it remains the single highest-priority unexhausted family in cycle-5.

2. **Sample-weighting × meta-information** — family: `sample-weighting` (UNUSED in cycle-5 post-/032). Replace `abs_pnl` baseline weights with a META-information-driven weight scheme: weight each label by (1 − Σ overlap_with_other_labels_in_window) × IS-uniqueness-score per López de Prado AFML Ch. 4. Mechanism: down-weights label clusters that share information (overlapping forward windows), increasing effective sample size and reducing Optuna over-fit to label cluster artifacts. Orthogonal to /036 + /037 axes; complements either substrate.

3. **Cross-asset non-OHLCV feature import from v3 catalog** — family: `cross-asset-feature-family` (NON-OHLCV, UNUSED in v1). v3 catalog closed cross-asset OHLCV-derived primitives at iter-v3/123, but explicitly preserved non-OHLCV cross-asset (perpetual-spot basis from non-Binance source, on-chain stablecoin supply Z-score, funding-rate basis term-structure) as PERMITTED with rolling-window T5 importance test. Adopt one such primitive into V1_FEATURE_COLUMNS_PRUNED with strict |IC|<0.5 vs all 44 existing features + ADF stationarity + IS-only computation. Tests whether v1 has been over-anchored on price-derived features — an axis cycle-5 has not touched. Mechanism: orthogonal information stream.

All three from families NOT in the prior-5 EXPLORATIONs. None depend on the failed /039 mechanism. Critic is advisory; QR may adopt, modify, or reject. Acknowledged: cycle-5 substrate has STABILIZED at /036 + /037 as SEPARATE candidates; /044 routing locked to TWO SEPARATE multi-seed CONFIRMATIONs with NO HYBRID BUNDLE option.

---

### Critic Summary (under 500 words)

**OVERALL**: EXPLORATION-NEGATIVE-CATASTROPHIC. Bundle OOS Sharpe Δ vs /036 anchor = **−0.7072** (observed +1.0393, anchor +1.7465), sitting 0.26 below the NEG-CAT threshold (Δ < −0.45). H1 stacking-compoundability hypothesis FALSIFIED; H1b refuted (both per-symbol regressions outside ±25pp band — LINK −40pp, DOT −69pp).

**Mechanism resolution — universe-dependent CONFIRMED**: Sortino × trend-scan composition basin-relocated 91% of trades away from /036's specialist optimum (OOS Jaccard 0.088 vs predicted band [0.30, 0.75]). The /037 Sortino-driven DOT lift was a Pool-A-averaging artifact of 5-cohort training; on a 2-cohort LINK+DOT substrate it doesn't survive. IS collapsed catastrophically (Sharpe −0.15, Max DD 75.84%, total PnL −17.64); OOS landed in a +1.04 lottery corner well below /036. Per-symbol diagnostic does NOT fire PROMISING-DOT-ONLY (LINK OOS PnL +68.45 absolute is POSITIVE, not < −10pp required).

**/044 routing finalization**: LOCKED SEPARATE per brief Section 11.6 NEG-CAT row + Section 8 row 5.
- /044-A = /036 alone (LINK+DOT trend-scan specialist) — multi-seed
- /044-B = /037 alone (5-cohort Sortino) — multi-seed
- **NO HYBRID BUNDLE.** Hybrid axis (loss-function × per-cohort-specialization REPEAT-COMBO) CLOSED at /039.

**Path Forward — 3 axes for /042 + /043** (cycle-5 has /040 + /041 pre-drafted):
1. **Ternary prediction-architecture** — UNUSED family in cycle-5; LightGBM models trade-skip directly; nominated by /037 + /038 reviews.
2. **Sample-weighting × meta-information** — UNUSED since /032; López de Prado AFML Ch. 4 uniqueness-weighting; reduces label-cluster over-fit.
3. **Cross-asset non-OHLCV feature import** — UNUSED family in v1; port one v3-permitted non-OHLCV primitive (basis term-structure, on-chain Z-score) with strict |IC|<0.5 + ADF + IS-only.

Cycle-5 substrate has STABILIZED at /036 alone + /037 weakly. All Phase 6 mechanics PASSED (look-ahead, embargo, anti-pattern, reproducibility, axis-family); the FAIL is at Check 8 (Hypothesis falsified by NEG-CAT band) — methodology-clean negative result.

Relevant artifact paths:
- /home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-039/research_brief.md
- /home/roberto/crypto-trade/.worktrees/quant-research/reports-v1/iteration_v1-039/comparison.csv
- /home/roberto/crypto-trade/.worktrees/quant-research/reports-v1/iteration_v1-039/out_of_sample/per_symbol.csv
- /home/roberto/crypto-trade/.worktrees/quant-research/reports-v1/iteration_v1-039/in_sample/per_symbol.csv
- /home/roberto/crypto-trade/.worktrees/quant-research/reports-v1/iteration_v1-039/basin_diagnostics/v3_roster_overlap.csv
- /home/roberto/crypto-trade/.worktrees/quant-research/run_baseline_v1.py (lines 4035-4140, dispatch elif)
