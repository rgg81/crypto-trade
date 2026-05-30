# Phase 7.5 Critic Review — iter-v1/033

OVERALL: **BLOCK-FINAL** — F2 trade-count fail (231 < 600 lower band) + F4 n_eff=3 collapse + IS Sharpe floor fail + LINK 58% concentration; single-outer-seed run cannot interpret +1.11 OOS as edge vs lottery.

## Iteration Type
TYPE: CONFIRMATION (cycle-4 first since /027 TF)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
`walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms`. Foundation regression intact. Bundle added no new features; no new label methodology.

### Check 2 — Embargo Width: PASS
Foundation embargo formula unchanged.

### Check 3 — Multiple-Testing Correction: FAIL (BLOCKING for CONFIRMATION)
- DSR = -15.5 (informational at n_eff=3)
- PSR_monthly_vs_1 = 0.4518 (52% gap below 0.95 merge tier; large improvement vs baseline 0.079 but still short)
- PBO N/A at single outer seed
- n_eff=3 = pathological Optuna degeneration (35-trial budget collapsed to 3 effective independent samples per cell). Brief Section 7 failure mode #4 (SAMPLE-WEIGHTING-DISSOLVES) fired INVERTED — compression instead of dissolution.

### Check 4 — IC Correlation: VACUOUS PASS

### Check 5 — ADF Stationarity: PASS

### Check 6 — Pareto Dominance: N/A (single outer seed)

### Check 7 — Reproducibility: PASS
HEAD `c842bf3`. Inner seeds [42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006] declared.

### Check 8 — Hypothesis-Implementation Alignment: FAIL
H1 PRIMARY ("bundle clears +1.0 OOS Sharpe hard merge floor at CONFIRMATION-standard multi-seed") REFUTED on full multi-falsifier formulation:
- F1 absolute OOS Sharpe (+1.108) PASS
- F2 trade count (231) FAIL by 62%
- F4 n_eff median=3 FAIL by 70%
- IS Sharpe -0.03 fails skill floor (`feedback_sharpe_floor.md` +1.0 floor)

H1a fallback fails — LTC contribution +10.56% bundle vs +33.10% /028 isolated = 68% of /028's specialist alpha LOST in bundle composition.

### Check 13 — Anti-Pattern Static Scan: PASS
A1-A14 clean. /027 + /030 LESSONS honored.

### Check 14 — Axis Family Validation: PASS
`confirmation-bundle` family. CONFIRMATIONs exempt from rotation. Bundle integrates 3 distinct families (per-cohort-specialization + upstream-label-shift + sample-weighting).

## Gate-by-Gate CONFIRMATION-MERGE Evaluation

| Gate | Required | Observed | Pass? |
|---|---|---|---|
| F1 OOS Sharpe Δ ≥ +0.336 | +0.336 | **+0.4447** | PASS |
| F1 absolute OOS Sharpe ≥ +1.0 | +1.00 | +1.1084 | PASS |
| F1 IS Sharpe ≥ +1.0 (skill floor) | +1.00 | **-0.0299** | **FAIL** (37× IS/OOS ratio structurally suspicious) |
| F2 OOS trade count [600, 1100] | [600, 1100] | **231** | **FAIL** (62% below lower band) |
| F3 ≥ 3/5 symbols positive | 3 | 4 (ETH NEGATIVE) | PASS |
| F4 n_eff per cell median [10, 25] | [10, 25] | **3** | **FAIL** (70% below lower band) |
| F5 OOS TP-exit count ≥ 15 | 15 | 54 | PASS |
| OOS trades ≥ 130 | 130 | 231 | PASS |
| ≥ 10 OOS trades/month | 10 | 16.5 | PASS |
| Top-symbol ≤ 30% OOS PnL | 30% | **LINK 58%** | **FAIL** |
| DSR ≥ 0.95 | 0.95 | -15.5 (n_eff=3) | FAIL (informational) |
| PSR_monthly_vs_1 ≥ 0.95 | 0.95 | 0.4518 | **FAIL** |

**Three hard methodology failures + one budget failure**: F2, F4, IS Sharpe floor, LINK concentration. Brief Verdict Matrix Row 6 (any F2/F3/F5 fail → BLOCK-FINAL) fires.

## Adversarial Findings

### Finding 1 — Bundle is LINK specialist + 4 hangers-on
LINK contributes 58% OOS PnL alone. The OOS Sharpe +1.108 is overwhelmingly LINK's specialist alpha (which independently delivered OOS +0.98 at /018). Other four models contributed marginal/negative. ETH Model G delivered -31.63% OOS, contradicting brief Section 1.1 projection of /019's +0.50 OOS Δ at multi-seed.

### Finding 2 — F4 n_eff=3 is structural Optuna degeneration
35 Optuna trials produced 3 effective independent samples per cell. composite_inv_concurrency × per-cohort × ES=10 stacked to OVER-compress trial diversity. IS performance catastrophe (Sharpe -0.0299) is the smoking gun — Optuna found 3 near-identical regions and over-fit to all of them. OOS Sharpe +1.11 is then a lucky draw of those 3 over-fit regions matching OOS regime.

### Finding 3 — IS Sharpe -0.03 with OOS Sharpe +1.11 (37× ratio)
Either:
- (a) Multi-seed lottery drew unusually favorable OOS regime — empirically supported by basin_diagnostics `v3_oos_trade_roster_jaccard = 0.061` (only 6% overlap with baseline)
- (b) IS regime structurally adversarial (LTC catastrophic -47% baseline OOS suggests deep IS difficulty)
- (c) n_eff=3 search degeneration produced Type-II false-positive OOS

Brief defect: IS Sharpe floor should have been pre-registered in Section 4 matrix; was treated as interpretive footnote.

### Finding 4 — OOS Max DD 52.56% vs baseline 40.94% (+11.6pp WORSE)
Bundle improved Sharpe but degraded drawdown profile. Direct attributable to LINK concentration (58% PnL → tail events on LINK amplify portfolio DD).

### Finding 5 — ETH Model G refutes /019 PROMISING at multi-seed
/019 EXPLORATION single-seed: ETH OOS +0.6990, +32.65% net PnL.
/033 multi-seed: ETH delivers **-31.63%** OOS — Δ = -64.28pp from /019 isolated to /033 bundle.

This refutes /019's robustness to multi-seed × composite_inv_concurrency interaction. Confirms `feedback_v3_engineered_features_dont_stack.md` lesson generalizes to MECHANISM stacking (gate × sample-weight × narrow Pool A), not just feature stacking.

### Finding 6 — basin_diagnostics OOS roster Jaccard = 0.061
6% overlap with baseline OOS roster. Bundle materially different from baseline. At single outer seed, indistinguishable from regime lottery.

## Verdict Cell Determination

Brief Section 4 Verdict Matrix Row 6 ("any FAIL F2/F3/F5 → BLOCK-FINAL"): F2 fail at -62% fires this row.

Brief Section 4 Row 7 ("F4 n_eff < 10 → BLOCK-PENDING-FIX"): F4 n_eff=3 fires this row.

When both fire, Row 6 (mechanism integrity broken) supersedes Row 7 (budget fix) — n_trials=50 rerun would not recover the missing 369-869 OOS trades. **Final verdict: BLOCK-FINAL.**

## Recommendations to QR (process-level for cycle-5+)

1. **Verdict Matrix MUST include IS Sharpe floor row** — /033's IS Sharpe -0.03 should have been pre-registered FAIL band.

2. **HIGH-RISK declarations need bidirectional n_eff failure-mode pre-registration** — both compression AND dissolution modes.

3. **Single-outer-seed CONFIRMATION cannot validate multi-axis bundles** — basin_diagnostics Jaccard=0.061 confirms regime-artifact indistinguishability. Future HIGH-RISK CONFIRMATIONs need `--seeds ≥ 2` outer (no kill-switch per 2026-05-30 directive enables this safely).

## Path Forward (mandatory on BLOCK-FINAL)

Per user directive 2026-05-30: PAUSE after /033 closeout, then cycle-5 EXPLORATIONs. Three alternative axes for /034+ (per Critic constructive mandate; cycle-5 menu already drafted at `briefs-v1/cycle5_axis_menu.md`):

1. **Funding-rate z-score (or velocity) — feature-family** (cycle-5 /034 or /035 per menu)
2. **Trend-scanning labels — labeling family** (cycle-5 /039 per menu)
3. **NEW signal source (liquidations / on-chain) — feature-family** (cycle-5 /034 / /038)

Bundle CONFIRMATION retry deferred to /044+ after cycle-5 produces more PROMISING ingredients. The /033 ablation roadmap (brief Section 11.1) is INVALID because /033 itself did not establish a valid reference point — sequential ablation requires a passing CONFIRMATION as anchor.

**Key bundle-architecture lessons for /044+ retry**:
- DROP /019 ETH+gate — multi-seed validation killed it
- KEEP /018 LINK specialist + /028 LTC+atr_sl=1.0 (both survived multi-seed)
- BUNDLE DESIGN must respect F2 trade-count band — specialist-cannibalization is the structural failure mode at narrow per-cohort dispatch
- Wall-clock calibration at ES=10 × n_trials=35 × 5 cohorts × composite_inv_concurrency ≈ 13h actual (per /033B observation); future bundle briefs MUST anchor on this

## Cycle-4 Cumulative

Post-/033:
- /028 PROMISING (LTC atr_sl=1.0; +0.598 OOS Δ; multi-seed CONFIRMED)
- /029 TF (DOT label rate)
- /030 NEG-CAT (meta-labeling closed)
- /031 PROMISING (composite_inv_concurrency, +1.04 OOS Δ single-seed)
- /032 PROMISING-AXIS-PARTIAL (frozen-HP isolated +0.22)
- **/033 BLOCK-FINAL (bundle multi-seed; specialist-cannibalization + n_eff collapse)**

Cycle-4 net: 2 PROMISING individual ingredients (LINK + LTC at multi-seed) + 1 PROMISING wrapper (composite_inv_concurrency; not yet multi-seed validated) + 1 TF + 1 NEG-CAT + 1 BLOCK-FINAL CONFIRMATION.

BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` `f8bc12c`.

## Tag

v0.v1-033 at closeout commit.
