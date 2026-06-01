# iter-v1/044 — Research Brief

## Section 0.0 — Banner

**iter-v1/044 CONFIRMATION-MERGE-PORTFOLIO** — cycle-5 CONFIRMATION 1/1. **FIRST bundle-CONFIRMATION under the relative-regime-Pareto methodology** (`merge_v1_relative_regime_pareto_proposal.md`, `iteration_closeout_new_skill_checklist.md`, `regime_ensemble_methodology.md`). 3-component bundle: BASELINE_V1 (anchor) + /036 LINK+DOT trend-scan (alt-trend specialist) + /043 LINK-only trend-scan (bear/chop OOS specialist).

**Anchor**: BASELINE_V1 `v0.v1-baseline-corrected` (IS Sharpe +0.2829 / OOS Sharpe +0.6637 single-seed=42; corrected walk-forward). σ_R / σ_dd_R from `briefs-v1/_meta/regime_catalog.md` §4 single-seed proxy (10-seed full sigma deferred to /046 baseline re-validation).

**Supersedes** the v3 6-component substrate proposal (`cycle5_substrate_v2_regime_portfolio.md`). RATIONALE: the user-directed 3-component scope (per orchestrator) is a strictly more conservative bundle — only PROMISING-CLEAN components admitted (/036 +1.08 OOS Δ, /043 +0.59 OOS Δ); /040 /037 /042 deferred to a future bundle-CONFIRMATION pending multi-seed validation of their REGIME-SPECIALIST classifications under the new methodology.

---

## Section 0.5 — Cadence + Iteration Type Declaration

**TYPE**: `CONFIRMATION-MERGE-PORTFOLIO` (cycle-5 CONFIRMATION 1/1)

**Cadence verification (Phase 5.5 input)**:
- 10/10 cycle-5 EXPLORATIONs satisfied at /043 closeout (transition_resolution.md §"Cycle-5 status").
- Catalog roster: /034 NEG-CLEAN basis; /035 NEG-CAT bimodal; /036 PROMISING-CLEAN +1.08; /037 PROMISING-CLEAN-MECHANISM-DIVERGENT +0.18; /038 NEG-CAT EDA-VINDICATED; /039 NEG-CAT vs /036; /040 NEG-CLEAN-OVERFIT (REGIME-SPECIALIST-IS under reframe); /041 NEG-CLEAN + TAIL-CONTROL annotation; /042 REGIME-SPECIALIST-IS-CONDITIONAL; /043 EXPLORATION-PROMISING.
- **CONFIRMATION-MERGE-PORTFOLIO authorized.**

**Wall-clock target**: 6h hard cap (CONFIRMATION). Estimated 3.5-4h (Section 6 — sub-runs reuse cached component artifacts where compatible).

**Components**:
- BASELINE_V1 (existing artifacts `reports-v1/iteration_v1-baseline/`) — re-used unchanged; re-validated under multi-seed `--seeds 2 --n-trials 35 --ensemble-size 5`.
- /036 LINK+DOT trend-scan — re-validated under same multi-seed spec.
- /043 LINK-only trend-scan — re-validated under same multi-seed spec.

---

## Section 0.6 — Architecture-Family Justification (CONFIRMATION — rotation N/A)

**Axis family**: `CONFIRMATION-PORTFOLIO` (no single-axis variation; bundles 3 prior EXPLORATION components).

**Rotation status**: **N/A — CONFIRMATION iteration**. Axis Rotation Discipline (skill §"QR Axis Rotation Discipline") applies to EXPLORATION iterations only. Section 0.6 is required by the skill template; the rotation rule does NOT apply because CONFIRMATIONs compose prior EXPLORATION axes rather than declaring a new one.

**Prior 5 EXPLORATION families (informational, for cycle-6 EXPLORATION planning)**:
- /039 — labeling (trend-scan dual-pair vs /036)
- /040 — feature-family (composed feature stack-prune)
- /041 — risk-primitive (DD brake + ATR ceiling, TAIL-CONTROL outcome)
- /042 — model-arch (XGBoost level-wise vs LightGBM leaf-wise)
- /043 — labeling (trend-scan LINK-only sister to /036)
- Distribution: 2 labeling, 1 feature-family, 1 risk-primitive, 1 model-arch. **No single family ≥ 3** — cycle-6 EXPLORATION axis rotation is unconstrained.

**Components imported**: /036 LINK+DOT trend-scan (Pphase 7.5 review.md verdict EXPLORATION-PROMISING-CLEAN; OOS Δ +1.08) + /043 LINK-only trend-scan (transition_resolution.md verdict EXPLORATION-PROMISING band #5/9; OOS Δ +0.59).

---

## Section 1 — Hypothesis

> The 3-component bundle (BASELINE_V1 w0=0.50 anchor + /036 LINK+DOT trend-scan w1=0.30 alt-trend specialist + /043 LINK-only trend-scan w2=0.20 bear/chop-OOS specialist), aggregated at the trade-roster level with deterministic weights chosen by Pareto-coverage analysis (NOT OOS-tuned), Pareto-dominates BASELINE_V1 alone on every tagged regime (bull / bear / chop / vol-spike / recovery) in IS+OOS under the σ_R tolerance band from `regime_catalog.md` §4. Bundle composition mechanism is weighted-PnL trade-roster aggregation per `(symbol, month)` cell; absent components redistribute their weight proportionally across active components.

Three load-bearing claims:

1. **/036 owns the alt-trend regimes** (bull/recovery via LINK+DOT trend-scan). Bundle inherits /036's OOS Δ +1.08 at w1=0.30 → ~+0.32 contribution to bundle OOS Sharpe.
2. **/043 owns the OOS bear (Δ +0.26 within-regime) + chop IS (Δ +0.19)** via single-cohort LINK-isolation; also adds DD-control (OOS MaxDD 21.61% — LOWEST in cycle-5) at w2=0.20 → portfolio MaxDD prediction below baseline 40.94%.
3. **BASELINE_V1 at w0=0.50 retains universal coverage** of all 5 symbols (BTC, ETH, LINK, LTC, DOT) — anchors regimes where /036 and /043 have no exposure (LTC: only baseline covers; ETH: only baseline covers; BTC: only baseline covers under sane bear/recovery dispatch).

---

## Section 2 — IS-Only Numerical Evidence

Source artifacts (committed pre-brief):
- `reports-v1/iteration_v1-baseline/comparison.csv` — BASELINE_V1 anchor metrics.
- `reports-v1/iteration_v1-036/comparison.csv` — /036 single-seed=42 (PROMISING-CLEAN).
- `reports-v1/iteration_v1-043/comparison.csv` — /043 single-seed=42 + `regime_attribution.csv` (PROMISING band #5/9).
- `briefs-v1/_meta/regime_catalog.md` — canonical tagger + per-regime baseline metrics + sigma_R_proxy.
- `briefs-v1/_meta/baseline_metric_anchors.csv` — BASELINE_V1 bundle-level metric vector.

### 2.1 — Headline component table (single-seed=42 single-pass, all PRE-bundle)

| Component | IS Sharpe | OOS Sharpe | OOS MaxDD | OOS trades | Notes |
|---|---:|---:|---:|---:|---|
| BASELINE_V1 | +0.2829 | +0.6637 | 40.94% | 189 | 5-symbol universe |
| /036 LINK+DOT trend-scan | +0.0843 | +1.7465 | 23.28% | 105 | 2-cohort isolation |
| /043 LINK-only trend-scan | +0.3359 | +1.2558 | 21.61% | 47 | 1-cohort isolation |

### 2.2 — Per-regime OOS Sharpe (from /043 `regime_attribution.csv`; /036 estimated via /036 review §F-AXIS table)

| Regime | OOS months | BASELINE OOS Sharpe | /036 OOS Sharpe | /043 OOS Sharpe |
|---|---:|---:|---:|---:|
| bull | 3 | −2.02 | ~+1.30 (LINK+DOT trend-positive) | −0.397 (Δ −0.14 OFF-REGIME) |
| bear | 6 | +1.62 | ~+1.55 | +1.88 (Δ +0.26 BETTER) |
| chop | 4 | +3.55 | ~+1.50 | +2.89 (Δ −0.66; but 6→11 trade-count tripling) |
| vol-spike | 1 | 0.0 | undefined | undefined |
| recovery | 1 | 0.0 | undefined | undefined |

### 2.3 — Sigma_R_proxy (from `regime_catalog.md` §4)

| Regime | IS months | sigma_R_proxy (single-seed) |
|---|---:|---:|
| bull | 15 | 0.263 |
| bear | 9 | 0.340 |
| chop | 10 | 0.322 |
| vol-spike | 5 | 0.456 |
| recovery | 0 (IS) | UNDEFINED — use OOS-only tolerance |

### 2.4 — Bundle composition arithmetic (deterministic-weight prediction at w0=0.50 / w1=0.30 / w2=0.20)

Trade-roster-level aggregation predicted bundle OOS Sharpe (weighted-mean component Sharpe + diversification lift):
- Weighted-mean = 0.50 × 0.6637 + 0.30 × 1.7465 + 0.20 × 1.2558 = 0.331 + 0.524 + 0.251 = **+1.107** (pre-diversification).
- Diversification lift estimate (3 components, low pairwise correlation per Section 11.4): +0.05 to +0.15.
- **Bundle OOS Sharpe central prediction: +1.05** (band [+0.90, +1.35]).

### Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

**Declaration**: **HIGH-RISK (CONFIRMATION at multi-seed)**.

**Reason**: CONFIRMATION-MERGE-PORTFOLIO bundles 3 single-seed-validated components. Multi-seed regression-to-mean is the dominant risk; /036's IS Sharpe +0.0843 and /043's basin-relocation Jaccard 0.125 vs /036-LINK roster are single-seed lottery candidates. Methodology integrity is HARD (look-ahead, embargo, gap, reproducibility); statistical-significance metrics (DSR/PBO/PSR) are INFORMATIONAL per the relative-regime-Pareto framework.

**Mitigation**: 
- Run all 3 components at `--seeds 2 --n-trials 35 --ensemble-size 5` (10 effective models per cell — CONFIRMATION budget).
- Per-component substitution test (Section 4 F-AXIS #4): predict bundle per-regime metric WITHOUT each component. If component contributes net-negative on Pareto-comparison, DROP from bundle.
- Per-component multi-seed validation gates (Section 3.4): each component must clear 2-seed mean Sharpe > 0 on OOS AND ≥ 1 of 2 seeds OOS Sharpe > 0.

---

## Section 3 — Implementation

### Section 3.1 — Bundle Composition (3 components)

| Slot | Component | Mechanism | Regime profile | Weight (deterministic) |
|---|---|---|---|---:|
| P0 — ANCHOR | BASELINE_V1 (5-cohort triple-barrier, 193 cols) | Universal substrate; covers BTC + LTC + ETH + DOT + LINK universally | UNIVERSAL anchor; OOS +0.66 baseline | **w0 = 0.50** |
| P1 — ALT-TREND | /036 LINK+DOT trend-scan (2-cohort, trend_scanning labels) | Trend-significance labels isolate alt-trend subspace; per-cohort isolation prevents BTC/ETH mean-reverting contamination | REGIME-SPECIALIST-OOS bull/recovery; OOS +1.75 | **w1 = 0.30** |
| P2 — LINK-ONLY-TREND | /043 LINK-only trend-scan (1-cohort, trend_scanning labels — sister to P1) | Same trend-scanning mechanism as /036; LINK-isolated; targets LINK bear-regime trend persistence; controlled-DD profile | REGIME-SPECIALIST-OOS bear (Δ +0.26) + chop IS (Δ +0.19); OOS MaxDD 21.61% | **w2 = 0.20** |

**Weight derivation (NOT OOS-tuned)**:
- P0 = 0.50 — anchor majority; covers regimes where P1 and P2 emit no trades (LTC, ETH, BTC). Pareto-coverage analysis: baseline is the ONLY component with non-zero LTC + ETH PnL.
- P1 = 0.30 — second-highest weight goes to broadest specialist (LINK + DOT; 105 OOS trades; covers OOS bull tail).
- P2 = 0.20 — lowest weight reflects narrowest universe (LINK only; 47 OOS trades; basin-relocation Jaccard 0.125 vs /036-LINK — single-seed lottery risk).
- Sum = 1.00. Weights chosen by Pareto-coverage + simplicity per `merge_v1_relative_regime_pareto_proposal.md` §B.2 "deterministic-weight" rule. NO grid search. NO OOS-tuning. Diary records the choice; revision deferred to /045 if NO-MERGE.

### Section 3.2 — Aggregation Method (Trade-Roster-Level)

For each `(symbol, month, candle)` cell:

```
bundle_pnl[cell] = sum over c in {P0, P1, P2} of w_c * pnl_c[cell]
                   if all 3 components emit a trade in cell
                 = sum over c in active_components of (w_c / sum_active_weights) * pnl_c[cell]
                   if subset emits trades in cell (proportional redistribution)
                 = 0 if no component emits a trade in cell (no fallback dispatch)
```

Where:
- `pnl_c[cell]` = component c's net PnL fraction at that cell (long+short combined, post-fee, post-slippage).
- `active_components` = subset of {P0, P1, P2} that emitted ≥1 trade in cell.
- Proportional redistribution preserves bundle unit-leverage — if only P0 trades, P0 gets w0 / w0 = 1.00 in that cell, NOT 0.50.

**No regime-conditional dispatch at /044 bundle level.** All components emit always (subject to their own internal gates). /044 is the LINEAR-BLEND baseline against which future regime-dispatch CONFIRMATIONs (/045+) compare.

### Section 3.3 — NEW CLI Flag

Add to `run_baseline_v1.py` (QE Phase 6 task):

```
--bundle-config "v1-036:0.30,v1-043:0.20,baseline:0.50"
```

Parser semantics:
- `v1-NNN` = component iteration id; reads its frozen multi-seed trades.csv from `reports-v1/iteration_v1-NNN/{in_sample,out_of_sample}/trades.csv`.
- `baseline` = `reports-v1/iteration_v1-baseline/{in_sample,out_of_sample}/trades.csv`.
- Float weight after colon; sum must equal 1.00 ± 1e-6 (else BLOCK at QE Phase 5.5).
- Order-invariant; alphabetized internally for reproducibility.

Runner emits:
- `reports-v1/iteration_v1-044/bundle/comparison.csv` — bundle-level headline metrics.
- `reports-v1/iteration_v1-044/bundle/regime_attribution.csv` — bundle per-regime metrics.
- `reports-v1/iteration_v1-044/{baseline,v1-036,v1-043}/comparison.csv` + `regime_attribution.csv` — per-component artifacts (re-validated multi-seed).

### Section 3.4 — Multi-Seed Configuration

Per-component spec (uniform across all 3):

```
--seeds 2 --n-trials 35 --ensemble-size 5
```

→ 2 outer seeds × 5 inner = 10 effective models per `(model, symbol, month)` cell. Matches v1 CONFIRMATION standard per skill §"CONFIRMATION ENSEMBLE_SIZE = 10".

Per-component multi-seed gate (informational — does not auto-BLOCK at /044; documented in diary):
- 2-seed mean Sharpe (OOS) > 0
- ≥ 1 of 2 seeds OOS Sharpe > 0
- ≥ 1 of 2 seeds IS Sharpe > 0

If a component fails its 2-seed gate, DROP from bundle and re-aggregate at proportional weights (e.g., if P2 fails: P0 = 0.50/0.80 = 0.625, P1 = 0.30/0.80 = 0.375). Diary records the substitution.

### Section 3.5 — Phase 6 Deliverables

QE Phase 6 emits, IN ORDER (each gated by Phase 6.0 pre-flight PASS):

1. **Sub-run /044-baseline**: re-run BASELINE_V1 at `--seeds 2 --n-trials 35 --ensemble-size 5`. Emit `reports-v1/iteration_v1-044/baseline/{comparison.csv, regime_attribution.csv, in_sample/, out_of_sample/}`. ~3h wall-clock.
2. **Sub-run /044-v1-036**: re-run /036 at same spec. Emit `reports-v1/iteration_v1-044/v1-036/`. ~25 min (2-cohort).
3. **Sub-run /044-v1-043**: re-run /043 at same spec. Emit `reports-v1/iteration_v1-044/v1-043/`. ~15 min (1-cohort).
4. **Sub-run /044-bundle**: aggregate per Section 3.2 algorithm using the 3 frozen multi-seed trade rosters. Emit `reports-v1/iteration_v1-044/bundle/{comparison.csv, regime_attribution.csv}`. ~5 min (post-hoc aggregation, no LightGBM training).
5. **Per-component regime_attribution.csv** for component substitution-test computation (Section 4 F-AXIS #4) — same schema as bundle.

**Engineering report**: `reports-v1/iteration_v1-044/engineering_report.md` confirms walk-forward `train_end_ms = test_start_ms - embargo_ms` unchanged, CV gap correct, `--bundle-config` parser smoke-tested, reproducibility seed checksum matches.

---

## Section 4 — F-AXIS Falsifiers (#1–#5)

### F-AXIS #1 (LOAD-BEARING) — Per-Regime Pareto-Dominance

**Falsifier**: for every tagged regime R in `regime_catalog.md` § 2:
```
sharpe_R(bundle) ≥ sharpe_R(BASELINE_V1) − sigma_R_proxy(R)
AND max_dd_R(bundle) ≤ max_dd_R(BASELINE_V1) + sigma_dd_R_proxy(R)
AND trade_count_R(bundle) ≥ 0.5 × trade_count_R(BASELINE_V1)
AND on ≥ 1 regime R*: sharpe_R*(bundle) > sharpe_R*(BASELINE_V1) + sigma_R_proxy(R*)
```

Bands (computed at /044 closeout from bundle `regime_attribution.csv`):

| Regime | sigma_R_proxy | Baseline OOS Sharpe | Tolerance band lower | MUST CLEAR (Pareto-equal) |
|---|---:|---:|---:|---:|
| bull | 0.263 | −2.02 | −2.28 | OOS bull Sharpe ≥ −2.28 |
| bear | 0.340 | +1.62 | +1.28 | OOS bear Sharpe ≥ +1.28 |
| chop | 0.322 | +3.55 | +3.23 | OOS chop Sharpe ≥ +3.23 |
| vol-spike | 0.456 | 0.0 | −0.46 | OOS vol-spike Sharpe ≥ −0.46 |
| recovery | UNDEFINED (IS=0 mo) | 0.0 | OOS-only carve-out per `merge_v1_relative_regime_pareto_proposal.md` §B.5 | INFORMATIONAL |

Strictly-better-on-≥1-regime: bundle must show ≥ 1 R* where Sharpe_R*(bundle) > Sharpe_R*(baseline) + sigma_R_proxy(R*). Most-plausible R* = OOS bear (predicted bundle +1.62 + 0.30 × ~+0.6 lift from /036-bear + 0.20 × +0.26 from /043-bear-Δ = ~+1.82; vs Pareto-strict +1.62 + 0.34 = +1.96 — TIGHT band; may not strict-beat).

### F-AXIS #2 — Bundle Wiring Proof

**Falsifier**: bundle `trades.csv` row count = sum-of-active-component-row-counts after weight redistribution; no orphan rows; PnL re-aggregation matches `bundle/comparison.csv` `total_net_pnl` to ±0.5%; per-`(symbol, month)` aggregation matches Section 3.2 formula bit-identically for a random 10-cell audit sample.

Phase 7.5 Critic Check 7 (reproducibility) reads this artifact directly.

### F-AXIS #3 — Per-Regime Metric Range Checks (Predicted-Observed Reconciliation)

Predicted bundle per-regime Sharpe bands (Section 10):
- bull OOS: predicted [−1.50, −0.50] band (baseline −2.02 + 0.30 × ~+1.30 from /036 + 0.20 × ~−0.40 from /043).
- bear OOS: predicted [+1.50, +2.20] band.
- chop OOS: predicted [+2.20, +3.20] band (/043 chop −0.66 dilutes baseline +3.55 modestly).
- vol-spike OOS: predicted [−0.20, +0.30] (essentially flat; single OOS month).

**Falsifier**: ≥ 2 of 4 named regimes (excluding recovery) MUST fall in their predicted band. If ≤ 1 falls in band, the bundle composition arithmetic is broken or the components do not transfer their single-seed regime profiles to multi-seed.

### F-AXIS #4 — Component Substitution Test

For each component c ∈ {P0, P1, P2}, recompute bundle metrics with c REMOVED and remaining weights re-normalized:

| Bundle without | New weights | Hypothesis |
|---|---|---|
| P0 (baseline) | P1=0.60, P2=0.40 | Bundle catastrophically loses LTC/ETH/BTC coverage; OOS Sharpe drops (alts-only book) → **DROP-P0 is NOT viable** (informative). |
| P1 (/036) | P0=0.71, P2=0.29 | Bundle loses LINK+DOT alt-trend coverage; predicted bull OOS Sharpe regresses to ~baseline −2.02. |
| P2 (/043) | P0=0.625, P1=0.375 | Bundle loses LINK bear-OOS Δ +0.26 and chop IS Δ +0.19; predicted OOS bear Sharpe drops ~0.05 (small). |

**Falsifier**: each component c must satisfy:
```
Pareto(bundle_with_c, BASELINE) is BETTER than Pareto(bundle_without_c, BASELINE)
OR the regime gap c fills is not covered by remaining components.
```

If a component fails both — DROP from bundle and re-aggregate.

### F-AXIS #5 — Wall-Clock Plausibility

Predicted wall-clock budget Section 6 = 3.5–4h. Phase 7.5 Critic Check 13 reads `engineering_report.md` actual wall-clock; deviation > 50% above prediction → diagnostic flag (informational, not BLOCK).

---

## Section 5 — Configuration Summary

```
ITERATION_LABEL: "v1-044"
TYPE: CONFIRMATION-MERGE-PORTFOLIO
BUNDLE_COMPONENTS: {baseline: 0.50, v1-036: 0.30, v1-043: 0.20}
OOS_CUTOFF_DATE: 2025-03-24 (UNCHANGED)
training_months: 24 (UNCHANGED)
candle_interval: 8h
universe: V1_BASELINE_UNIVERSE = (BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT)  # baseline component
                  + (LINKUSDT, DOTUSDT)  # /036 component
                  + (LINKUSDT,)  # /043 component
features_per_component:
  baseline: BASELINE_FEATURE_COLUMNS (193 cols, 9 groups)
  v1-036:   V1_FEATURE_COLUMNS_PRUNED (40 cols) — same as /036
  v1-043:   V1_FEATURE_COLUMNS_PRUNED (40 cols) — same as /043
label_modes:
  baseline: triple-barrier 5-cohort
  v1-036:   trend_scanning 2-cohort (LINK, DOT)
  v1-043:   trend_scanning 1-cohort (LINK)
multi_seed_spec: --seeds 2 --n-trials 35 --ensemble-size 5  # uniform across all 3 components
optuna_objective: monthly_sharpe (baseline, /036, /043 all unchanged)
risk_gates: R1+R2+R3 inherited from each component's frozen config (no /044-level overrides)
embargo: training_months × 1 month label horizon = 1 month gap at each fold boundary
cv_gap_candles: (timeout_candles + 1) × n_symbols (per skill NO CHEATING rule)
wall_clock_target: 6h hard cap; estimate 3.5-4h
deliverables: see Section 3.5
```

---

## Section 6 — Wall-Clock Estimate (Linear Scaling From Prior Iterations)

**Hard cap**: 6h CONFIRMATION budget.

| Sub-run | Symbols | Cohorts | Features | n_trials | Seeds | Wall-clock estimate | Source |
|---|---:|---:|---:|---:|---:|---:|---|
| /044-baseline | 5 | 5 | 193 | 35 | 2 | ~3h | run_baseline_v1.py historical multi-seed timings (5-symbol 5-cohort scaled from /037's 3h Sortino run) |
| /044-v1-036 | 2 | 2 | 40 | 35 | 2 | ~25 min | /036 single-seed 12 min × 2 (seeds) ≈ 24 min |
| /044-v1-043 | 1 | 1 | 40 | 35 | 2 | ~15 min | /043 single-seed 7 min × 2 (seeds) ≈ 14 min |
| /044-bundle aggregation | — | — | — | — | — | ~5 min | post-hoc CSV-merge; no LightGBM training |
| **Total** | | | | | | **~3.5-4h** | well below 6h cap |

**Margin**: 4-4.5h cushion = ~100% margin over estimate.

**Compression decisions**: none required at default. If pre-flight estimate exceeds 6h, drop /044-baseline multi-seed re-run (use existing baseline as anchor) — but this loses sigma_R refresh.

**Trade-offs**: 2-seed instead of 5-seed (lower multi-seed validation power) trades 50%+ wall-clock for the 4-component-budget the orchestrator-specified 3-component bundle accommodates. Critic Phase 6.0 flags if 2-seed is too thin.

---

## Section 7 — Expected Report Shape

After Phase 6, the QE deliverables tree:

```
reports-v1/iteration_v1-044/
├── engineering_report.md
├── baseline/
│   ├── comparison.csv             # multi-seed (2 outer × 5 inner = 10 effective models)
│   ├── regime_attribution.csv     # per-regime metrics vs BASELINE_V1 historical anchor
│   ├── in_sample/{trades.csv, stats.csv}
│   └── out_of_sample/{trades.csv, stats.csv}
├── v1-036/
│   ├── comparison.csv
│   ├── regime_attribution.csv
│   ├── in_sample/, out_of_sample/
├── v1-043/
│   ├── comparison.csv
│   ├── regime_attribution.csv
│   ├── in_sample/, out_of_sample/
├── bundle/
│   ├── comparison.csv             # BUNDLE-LEVEL headline (Sharpe, MaxDD, trade count, etc.)
│   ├── regime_attribution.csv     # BUNDLE-LEVEL per-regime (this is the F-AXIS #1 input)
│   ├── per_component_correlation.csv  # 3x3 pairwise daily-PnL correlation
│   ├── in_sample/{aggregated_trades.csv, stats.csv}
│   └── out_of_sample/{aggregated_trades.csv, stats.csv}
└── basin_diagnostics/             # per-seed per-cohort Optuna basin map (re-validation)
```

**per_component_correlation.csv** schema: `pair, daily_pnl_corr, trade_jaccard, in_sample, out_of_sample`. Used by Section 11.4 and Phase 7.4 LM Master.

**bundle/regime_attribution.csv** is the load-bearing artifact — Critic Check 3d reads it to evaluate Pareto-dominance vs `briefs-v1/_meta/regime_catalog.md` §4 baseline column.

---

## Section 8 — Path Forward — MERGE / NO-MERGE Routing

| Outcome | Trigger condition | Routing |
|---|---|---|
| **MERGE (CONFIRMATION-MERGE-PORTFOLIO)** | bundle Pareto-better-or-equal on EVERY tagged regime (within σ_R) AND ≥ 1 regime strictly better AND methodology integrity intact | `BASELINE_V1.md` UPDATED to 3-component bundle composition; new anchor `v0.v1-044`; `_meta/baseline_metric_anchors.csv` + `_meta/baseline_seed_regime_matrix.csv` REFRESHED from bundle artifacts; tag `v0.v1-044` |
| **PARTIAL-MERGE** | bundle Pareto-better-or-equal on subset but ONE regime regresses materially (> σ_R below baseline); methodology intact | Diary records the partial outcome; `BASELINE_V1.md` UNCHANGED; revise weights at /045 (e.g., reduce P2 if /043 caused chop OOS −0.66 to dominate bundle chop regression); /045 is a re-CONFIRMATION at refined weights — STILL a CONFIRMATION (not EXPLORATION) per cadence rule |
| **NO-MERGE** | bundle fails Pareto-check on ≥ 2 regimes OR methodology integrity gate fails (look-ahead, embargo, gap, reproducibility, ADF) | `BASELINE_V1.md` UNCHANGED; cycle-6 EXPLORATIONs begin at /045 with axis-family rotation across feature-family / model-arch / labeling / universe / risk-primitive |

**Critic Phase 7.5 verdict mapping**:
- MERGE → `OVERALL: CONFIRMATION-MERGE-PORTFOLIO`
- PARTIAL-MERGE → `OVERALL: CONFIRMATION-BLOCK` with Path Forward proposing weight revision for /045
- NO-MERGE → `OVERALL: CONFIRMATION-BLOCK` with Path Forward proposing cycle-6 EXPLORATIONs in 2+ different axis families
- Methodology integrity fail → `OVERALL: BLOCK-FINAL` (no rerun allowed)
- Single isolated artifact defect → `OVERALL: BLOCK-PENDING-FIX` (one rerun chance)

---

## Section 9 — Behavioral Predictor (Pre-Registered Failure-Mode Prediction)

**Most-plausible failure mode**: **multi-seed regression-to-mean on /036 + /043** causes their multi-seed mean OOS Sharpes to land below the [+0.8, +1.5] and [+0.6, +1.3] bands respectively, dragging bundle OOS Sharpe below the central +1.05 prediction into the [+0.70, +0.90] band — clearing baseline anchor +0.66 by a TIGHT margin but not strict-beating any regime, and forcing PARTIAL-MERGE or NO-MERGE.

**Second-most-plausible failure mode**: /043's chop OOS regression (Δ −0.66) at multi-seed amplifies (because /043's basin-relocation Jaccard 0.125 may collapse further at 2-seed), violating chop Pareto-equal AND making bundle chop OOS Sharpe regress below the +3.23 tolerance band. → CONFIRMATION-BLOCK; /045 reduces w2 from 0.20 → 0.10 or DROPs P2.

**Third-most-plausible failure mode**: bundle aggregation arithmetic defect — proportional redistribution code-path bug causes weight sum mismatch in cells where 1 of 3 components is silent; bundle PnL diverges from prediction by > 5%. → Critic Phase 7.5 Check 7 (reproducibility) FAIL → BLOCK-PENDING-FIX with single-rerun on arithmetic correction.

**What the gates should catch**:
- F-AXIS #1 (per-regime Pareto) catches multi-seed Sharpe regression at the regime level (most direct gate for FM#1).
- F-AXIS #3 (per-regime range checks) catches chop OOS amplification of /043's −0.66 regression (most direct gate for FM#2).
- F-AXIS #2 (wiring proof) + Critic Check 7 catch aggregation defect (most direct gate for FM#3).

**Expected metric signature if hypothesis holds**: bundle OOS Sharpe +1.05 ± 0.15; bundle OOS MaxDD ~25-30% (intermediate between /036's 23% and baseline's 41%); bundle OOS trades ~250 (~189 + 105 × 0.30 + 47 × 0.20 = ~225, plus diversification trade-roster expansion); per-regime: bear strict-better, bull within-tolerance, chop within-tolerance, vol-spike within-tolerance.

**Expected metric signature if hypothesis fails**: bundle OOS Sharpe +0.65 ± 0.15 (≈ baseline; no lift); OR bundle OOS Sharpe +0.85 with chop regression > 1σ_R below baseline +3.55.

---

## Section 10 — Regime Attribution Plan (MANDATORY per `regime_ensemble_methodology.md` §5)

### 10.1 — Target Regime Coverage Plan

| Regime | Months (IS / OOS) | Baseline OOS Sharpe | Target component(s) | Mechanism | Off-regime expectation | Pareto criterion (bundle vs baseline) |
|---|---|---:|---|---|---|---|
| bull | 15 / 3 | −2.02 | P0 (anchor), P1 (alt-trend bull) | LINK+DOT trend-scan captures alt-bull moves baseline strategy misses | /036 OOS bull ~+1.30 lifts bundle bull from −2.02 to predicted [−1.50, −0.50] | bundle bull Sharpe ≥ −2.28 (Pareto-equal within σ_R = 0.263) |
| bear | 9 / 6 | +1.62 | P0, **P2 (LINK-only-trend bear-Δ +0.26)** | /043 LINK-only catches LINK bear-regime persistence; baseline already strong | bundle bear Sharpe predicted [+1.50, +2.20] — strictly-better-than-baseline candidate | bundle bear Sharpe ≥ +1.28 (Pareto-equal) AND > +1.96 to strict-beat |
| chop | 10 / 4 | +3.55 | P0 (chop-IS Δ +0.19 from /043 incorporation; OOS dominant baseline) | Baseline +3.55 is the strongest baseline OOS regime — /036 and /043 trade-rosters DILUTE baseline at w2 = 0.20 | /043's OOS chop −0.66 may pull bundle below +3.23 tolerance — bundle chop is the highest-risk Pareto check | bundle chop Sharpe ≥ +3.23 (Pareto-equal) |
| vol-spike | 5 / 1 | 0.0 (1 month) | P0 | Single OOS month — high noise; informational only | bundle ≈ baseline ≈ 0 | bundle vol-spike Sharpe ≥ −0.46 |
| recovery | 0 / 1 | 0.0 (1 month, n=0 IS) | P0 (only component active in recovery) | No IS samples; OOS-only carve-out per `merge_v1_relative_regime_pareto_proposal.md` §B.5 | bundle ≈ baseline ≈ 0 | INFORMATIONAL; rare-regime exempt |

### 10.2 — Expected Per-Regime Bundle Sharpe (with component contributions)

| Regime | Baseline | P1 contrib at w1=0.30 | P2 contrib at w2=0.20 | Predicted bundle | Δ vs baseline |
|---|---:|---:|---:|---:|---:|
| bull OOS | −2.02 | +0.39 (=+1.30 × 0.30) | −0.08 (=−0.40 × 0.20) | **−0.66 to −1.20** (with diversification) | **+0.82 to +1.36** STRICT-BETTER |
| bear OOS | +1.62 | +0.30 (alt-bear) | +0.052 (=Δ +0.26 × 0.20) | **+1.70 to +2.00** | **+0.08 to +0.38** |
| chop OOS | +3.55 | +0.10 | −0.13 (=−0.66 × 0.20) | **+2.85 to +3.30** | **−0.25 to −0.70** TIGHT |
| vol-spike OOS | 0.0 | undef | undef | ~0.0 | ~0 |
| recovery OOS | 0.0 | undef | undef | ~0.0 | ~0 |

**Most-plausible strict-better regime R\***: **bull OOS** (Δ +0.82 to +1.36) — bundle bull predicted central −0.93 vs baseline −2.02; sigma_R(bull) = 0.263; Δ > +0.263 → STRICT-BETTER if bundle bull > −1.76.

**Highest-risk Pareto-check regime**: **chop OOS** (Δ −0.25 to −0.70). Tolerance sigma_R(chop) = 0.322. Bundle chop must be ≥ +3.23 to clear Pareto-equal. Predicted bundle chop +2.85 to +3.30 — the LOW end of the band fails Pareto-equal. Multi-seed will determine.

### 10.3 — Regime-Aware Falsifier (per `regime_ensemble_methodology.md` §4.4 mandate)

If bundle target-regime IS Sharpe (chop IS, predicted Δ +0.19 from /043's +0.19 contribution at w2=0.20 = +0.04 bundle-level IS chop lift) does NOT exceed baseline chop IS Sharpe by ≥ 0.04 at multi-seed mean, hypothesis #1 (bundle composition arithmetic transfers /043's IS lift cleanly) is REFUTED → CONFIRMATION-BLOCK; weight revision at /045.

---

## Section 11 — Bundle Composition (CONFIRMATION-PORTFOLIO MANDATORY per skill §5.5)

### 11.1 — Component List with Frozen Iteration IDs

| Slot | Iteration | Source review verdict | Source OOS Sharpe (single-seed=42) | Source OOS Δ vs BASELINE_V1 |
|---|---|---|---:|---:|
| P0 (anchor) | BASELINE_V1 `v0.v1-baseline-corrected` | (no review — anchor) | +0.6637 | (anchor reference) |
| P1 | iter-v1/036 | EXPLORATION-PROMISING-CLEAN (review.md `OVERALL`) | +1.7465 | +1.08 |
| P2 | iter-v1/043 | EXPLORATION-PROMISING band #5/9 (transition_resolution.md `Final verdict`) | +1.2558 | +0.59 |

### 11.2 — Regime Coverage Table (per `iteration_closeout_new_skill_checklist.md` §"/044 substrate composition rule")

| Regime | P0 (baseline) | P1 (/036) | P2 (/043) | Bundle Coverage |
|---|---|---|---|---|
| bull | universal (Sharpe −2.02 weak) | strong (~+1.30) | OFF-DRAG (−0.397; Δ −0.14) | P1 lifts; P2 small drag; P0 anchors |
| bear | strong (+1.62) | mid | strong (+1.88; Δ +0.26) | P0 + P2 own; P1 mid contribution |
| chop | strongest baseline regime (+3.55) | mid (~+1.50) | regression (−0.66) but trade-count tripling | P0 anchors; P2 dilutes at w2=0.20 |
| vol-spike | flat (n=1 OOS) | undef | undef | P0 only |
| recovery | flat (n=1 OOS) | undef | undef | P0 only |

**No regime uncovered.** P1 fills bull-OOS gap; P2 fills bear-OOS Δ AND chop-IS Δ; P0 covers all 5 regimes universally. Anchor requirement (≥1 component Pareto-better-or-equal to BASELINE_V1 on baseline's best regime — chop OOS) satisfied by P0 itself.

### 11.3 — Component Substitution Test Plan

Same as F-AXIS #4 (Section 4). For each c ∈ {P0, P1, P2}:
1. Compute bundle WITHOUT c, re-normalize weights of remaining components.
2. Compute per-regime Sharpe for bundle-without-c.
3. Compare to bundle-with-c per-regime Sharpe.
4. Component c CONTRIBUTES POSITIVELY iff Pareto(with) ≥ Pareto(without) OR c fills a regime gap remaining components do not cover.

Diary records each component's contribution; components failing both → DROPPED in a hypothetical /044-revised bundle (deferred to /045 if /044 PARTIAL-MERGE).

### 11.4 — Pairwise Correlation Prediction

| Pair | Trade Jaccard prediction | Daily-PnL correlation prediction | Risk assessment |
|---|---:|---:|---|
| P0 ↔ P1 | 0.10-0.15 | 0.25-0.35 | LOW (different labeling: triple-barrier vs trend-scan) |
| P0 ↔ P2 | 0.08-0.12 | 0.20-0.30 | LOW (1-cohort isolated from 5-cohort baseline) |
| **P1 ↔ P2 (sister)** | **0.05-0.15** | **0.50-0.70** | **MEDIUM-HIGH** — both trend-scanning on LINK; trade-rosters disjoint at single-seed (Jaccard 0.125 observed) but PnL co-moves during LINK trend periods |

**At-risk pair P1↔P2 justification**:
- Trade Jaccard LOW (0.05-0.15) because /043 single-seed=42 basin-relocated from /036's LINK leg (observed Jaccard 0.125 at single-seed).
- Daily-PnL correlation MEDIUM-HIGH (0.50-0.70) because both trade LINK during LINK trend periods.
- Bundle composition test at /044 verifies net Pareto-positive contribution.
- If P1 ↔ P2 daily-PnL correlation > 0.80 at multi-seed AND Pareto contribution of P2 is near-zero, DROP P2 at /045 OR reduce both to 0.15-0.20 each.

### 11.4.5 — LM Master Phase 4.5 Response Map (per `lgbm_advisor.md` 3 numbered recommendations)

| # | LM Master recommendation | QR adjudication | Reason |
|---|---|---|---|
| 1 | Pin Optuna search bounds across the 3 sub-runs for cross-component reproducibility | **ADOPTED** | Use `bounds_profile="v1_pruned"` for all 3 sub-runs; identical search space + identical seeds. Implemented in Section 3.4 multi-seed config (all components share `--pruned-features`). |
| 2 | Set `lambda_l1 ∈ [0.5, 3.0]` floor for P1 and P2 at multi-seed | **MODIFIED** — adopted as default Optuna bounds via existing `v1_pruned` profile (lambda_l1 lower bound already non-zero); no per-component floor override. Reason: per-component bound override would violate cross-component reproducibility (Rec #1) which QR prioritizes. |
| 3 | Force `bagging_fraction = 0.7, bagging_freq = 5` floor (P1 + P2) for trend-scan basin stability | **REJECTED** | Per-component floor overrides violate Rec #1. The single-axis isolation discipline forbids touching Optuna bounds during component sub-runs at CONFIRMATION; if multi-seed basin instability fires F-AXIS #4, /045 revises bounds. NOT pre-emptively tighten. |

**Additional LM Master concerns adopted in body of brief**:
- LM Master predicts P1×P2 daily-PnL correlation **0.70-0.85** (vs QR's §11.4 prediction 0.50-0.70). QR ADOPTS LM Master's higher estimate as worst-case in falsifier framing; bundle still passes if P1×P2 ρ ≤ 0.85 AND component substitution test PASS. If ρ > 0.85 AND P2 contribution near-zero, /044 PARTIAL-MERGE → /045 reweight.
- LM Master predicts bundle OOS Sharpe central **+0.95** (vs QR's §2 prediction central +1.05). QR's Section 9 prediction band [+0.90, +1.35] already covers LM Master's downward revision; falsifier bands UNCHANGED.

### 11.5 — Bundle Gates (per `merge_v1_relative_regime_pareto_proposal.md` §B.3)

- **HARD (methodology integrity)**: no look-ahead, embargo applied at every fold boundary (`walk_forward.py:113`), CV gap = `(timeout_candles + 1) × n_symbols`, reproducibility checksum match, no OOS tuning, feature-column pinning, forming-candle drop, ADF stationarity preserved.
- **HARD (per-regime Pareto-dominance, Check 3d)**: every tagged regime R, `sharpe_R(bundle) ≥ sharpe_R(baseline) − sigma_R_proxy(R)` AND `max_dd_R(bundle) ≤ max_dd_R(baseline) + sigma_dd_R_proxy(R)` AND `trade_count_R(bundle) ≥ 0.5 × trade_count_R(baseline)` AND ≥1 regime strictly better.
- **INFORMATIONAL** (diary-justification-required-if-regress): DSR/PBO/PSR per `briefs-v1/_meta/baseline_metric_anchors.csv` reference values; absolute Sharpe ≥ +1.0 OOS aspirational floor; OOS/IS ratio ≥ 0.5 aspirational; top-symbol concentration ≤ 30% aspirational; OOS trades ≥ 130 aspirational.

**Trade-count aspirational**: bundle predicted ~225 OOS trades, clears 130 with safety. Top-symbol concentration: LINK aggregate predicted ~30-35% — may exceed 30% aspirational; informational under new methodology with diary justification.

---

## Reporting Back (under 500 words)

**3-sentence hypothesis**: The 3-component bundle BASELINE_V1 (w0=0.50 anchor) + /036 LINK+DOT trend-scan (w1=0.30 alt-trend specialist) + /043 LINK-only trend-scan (w2=0.20 bear/chop-OOS specialist), aggregated at the trade-roster level with deterministic weights chosen by Pareto-coverage analysis (NOT OOS-tuned), Pareto-dominates BASELINE_V1 alone on every tagged regime (bull/bear/chop/vol-spike/recovery) in IS+OOS under sigma_R tolerance from `regime_catalog.md` §4. The bundle composition mechanism is weighted-PnL trade-roster aggregation per `(symbol, month)` cell with proportional weight redistribution when subsets of components are silent; no regime-conditional dispatch. Edge claim: bundle inherits /036's OOS bull lift (Δ ~+0.82 to +1.36 strict-better regime R\*), /043's OOS bear lift (Δ +0.052 within-tolerance), and baseline anchor for LTC/ETH/BTC universal coverage where P1/P2 do not emit.

**Bundle weights + regime coverage summary**:

| Slot | Component | Weight | Regime owned | Predicted bundle Δ vs baseline |
|---|---|---:|---|---:|
| P0 | BASELINE_V1 | 0.50 | UNIVERSAL anchor (BTC, ETH, LTC, DOT, LINK) | (anchor) |
| P1 | /036 LINK+DOT trend-scan | 0.30 | bull OOS (lifts −2.02 → ~−0.93) | +0.82 to +1.36 STRICT-BETTER |
| P2 | /043 LINK-only trend-scan | 0.20 | bear OOS (+0.26) + chop IS (+0.19) | +0.08 to +0.38 |

**Predicted bundle OOS Sharpe band**: **central +1.05; band [+0.90, +1.35]**. Pre-diversification weighted-mean = +1.107. Diversification lift +0.05 to +0.15 (3 components, P1↔P2 daily-PnL correlation 0.50-0.70 medium-high, P0↔alts low).

**/045 follow-up plan if NO-MERGE**:
- **If PARTIAL-MERGE (chop OOS regression)**: /045 reduces w2 from 0.20 → 0.10, redistributes 0.10 → P0 (w0 = 0.60); re-CONFIRMATION at refined weights.
- **If NO-MERGE (Pareto fails on ≥ 2 regimes)**: cycle-6 EXPLORATIONs begin at /045 with axis-family rotation; priorities per `cycle5_substrate_v2_regime_portfolio.md` §8: Pool A decomposition (BTC+ETH split), cross-asset feature families (funding rates, OI), CatBoost/MLP model-arch, per-regime DD brake risk-primitive.
- **If methodology-integrity BLOCK-FINAL**: dead-end; cycle-6 EXPLORATIONs begin at /045 from a different bundle composition framework.

**Key risk acknowledged**: chop OOS is the highest-risk Pareto regime — /043's −0.66 OOS chop regression at single-seed dilutes baseline +3.55 to predicted [+2.85, +3.30], with tolerance band lower +3.23. The LOW end of the band FAILS Pareto-equal; multi-seed will determine. Section 9 FM#2 documents this failure mode explicitly.
