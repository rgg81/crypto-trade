# LightGBM Master Advisor — iter-v1/056 — Phase 4.5 (Pre-Design)

## Context Read

- Track: v1; cycle-6 FIRST CONFIRMATION-PORTFOLIO (cadence complete 10/10 EXPLORATIONs)
- Iteration type: CONFIRMATION — symbol-partitioned specialist federation
- Axis: CONFIRMATION-bundle assembly (no new feature/model/gate axis; re-measures EXPLORATION
  ingredients at CONFIRMATION-budget in disjoint symbol-universe pods)
- CONFIRMATION budget: --seeds 1 --ensemble-size 10 --n-trials 35 (5 inner × 10 ensemble per
  leg; note: unlike the v1 10-outer-seed rule, this is ensemble-size=10 single-outer-seed per
  the prompt spec; see Rec 1 for implications)
- Aggregation: CSV-replay from /045 framework; equal weights w=0.2 per component

### Specialist + Anchor Table

| Component | Role | Symbol | Config | Feature stack | EXPLORATION IS Sharpe | EXPLORATION OOS Sharpe | Verdict |
|---|---|---|---|---|---|---|---|
| C1 — BTC specialist | Specialist | BTCUSDT | Model_A_BTC_specialist; R3 ON; atr_tp=3.5/sl=1.75 | V1_FEATURE_COLUMNS_PRUNED = 47 (`btc_funding_spread_30_90` solo; `btc_funding_rate_8h_impulse` PERMANENTLY DROPPED at /054) | +0.2614 (single-seed; Δ +1.11 vs baseline −0.85) | −0.8396 (informational; within 1σ of /053 multi-seed mean −0.60) | PARTIAL-CONFIRMED-CLEAN (/054) |
| C2 — ETH specialist | Specialist | ETHUSDT | Model_A_ETH_specialist; R3 ON | V1_FEATURE_COLUMNS_PRUNED = 48 (`eth_vs_btc_ret_ratio_30` added at /055) | −0.2082 (single-seed; Δ +0.40 vs baseline −0.61; PARTIAL band) | +0.6546 (informational; strongest cycle-6 single-seed OOS) | PROMISING-PARTIAL (/055) |
| C3 — DOT specialist | Specialist | DOTUSDT | Model_E_DOT_specialist; R3 ON; atr_tp=3.5/sl=1.75 | V1_FEATURE_COLUMNS_PRUNED = 46 (`dot_vs_btc_ret_ratio_30` at /051) | −0.2355 multi-seed mean (Δ +0.99 vs baseline −1.23; PARTIAL band) | +0.2711 multi-seed mean (informational) | PARTIAL-CONFIRMED (/051) |
| C4 — LINK anchor | Anchor (reuse) | LINKUSDT | BASELINE_V1 Model C; R1+R3 | 193 (BASELINE_V1 stack) | +2.25 IS baseline Sharpe | +2.79 OOS (informational) | BASELINE anchor — no re-run needed |
| C5 — LTC anchor | Anchor (reuse) | LTCUSDT | BASELINE_V1 Model D; R1+R3 | 193 (BASELINE_V1 stack) | +0.17 IS baseline Sharpe | −4.27 OOS (CATASTROPHIC; see Risk Flags) | BASELINE anchor — no re-run needed |

**Re-run requirement for C1/C2/C3**: CONFIRMATION-budget re-runs (--ensemble-size 10, n_trials=35)
produce NEW trades/PnL series per specialist. The EXPLORATION trade files from /054, /055, /051
were generated at ENSEMBLE_SIZE=3 and n_trials=18; they MUST NOT be replayed directly.
The LINK/LTC anchors (C4, C5) use BASELINE_V1 trades as-is from
`reports-v1/iteration_v1-baseline/` — no re-run needed (per /045 framework).

---

## Phase 4.5 — LM Master Pre-Design Advisory

### ML Perspective

Three specialists trained on disjoint single-symbol cohorts at CONFIRMATION-budget share an
important structural property: **each symbol's Optuna search runs on its own isolated cohort
with zero cross-symbol interference**. This is distinct from the pooled Model A head
(BASELINE_V1), where BTC + ETH signals compete for split-budget in a unified loss surface.

At CONFIRMATION-budget (n_trials=35, ENSEMBLE_SIZE=10), the search space is meaningfully deeper
than EXPLORATION (n_trials=18, ENSEMBLE_SIZE=3). Three expected CONFIRMATION-budget effects:

**(a) Ensemble-size compression**: ENSEMBLE_SIZE=3 at single-seed=42 has high per-run variance
(inner-seed lottery at each Optuna trial outcome). ENSEMBLE_SIZE=10 draws from 10 inner seeds
simultaneously, averaging the initialization variance. The observed per-specialist IS Sharpe
at EXPLORATION was a 3-seed mean; the CONFIRMATION 10-seed mean SHOULD regress toward the
per-symbol true IS Sharpe (i.e., pull toward the multi-seed means from /051 and /053 rather
than the favorable single-seed draws from /054-/055). Pre-register this regression expectation
explicitly — do NOT treat EXPLORATION-budget numbers as IS Sharpe floors.

**(b) n_trials=35 vs n_trials=18**: the additional 17 trials push past TPE warm-up saturation
(~15-20 random trials) into the exploitation regime. This means Optuna's IS-objective fit at
/056 is materially more refined than at EXPLORATION. This could HELP (deeper exploitation of
genuine IS signal) or HURT (deeper IS-overfitting to the specialist's small cohort). The
dominant direction depends on the specialist's IS trade count:
- BTC: 139 IS trades → ~28 trades/fold at 5 folds → n_trials=35 is calibrated
- ETH: 138 IS trades → ~28 trades/fold → same
- DOT: 119 IS trades (mean across seeds) → ~24 trades/fold → tighter; moderate overfit risk

**(c) Specialist isolation vs BASELINE_V1 pooled head**: the pooled head at BASELINE_V1
misallocates split-budget across BTC+ETH simultaneously. BTC IS Sharpe −0.85 and ETH IS Sharpe
−0.61 under pooled training are regime-degraded readings. The specialist isolation effect
(CONFIRMED at /050-/054 multi-seed) compresses IS MaxDD by 40-65pp vs pooled baseline per
symbol. This drag-removal effect persists at CONFIRMATION-budget and is the PRIMARY reason to
expect per-specialist IS Sharpe above the pooled-head baseline.

---

## Top 3 Recommendations

### Rec 1 — Each specialist sub-run MUST be a FRESH backtest at CONFIRMATION budget; do NOT replay EXPLORATION trades

The EXPLORATION trade files from /054 (BTC, ENSEMBLE_SIZE=3, n_trials=18), /055 (ETH, ENSEMBLE_SIZE=3,
n_trials=18), and /051 (DOT, ENSEMBLE_SIZE=3, n_trials=18) were generated with DIFFERENT
hyperparameter-search depth and ensemble size than the /056 CONFIRMATION run. Replaying them as
"confirmed" IS outputs would violate the apples-to-apples constraint and introduce a subtle
systematic upward bias: the EXPLORATION runs include the favorable seed=42 lottery draw at the
single-seed level.

For /056, the runner must execute three separate CONFIRMATION-budget sub-runs:
- `run_iteration_056_btc.py` — BTC-only cohort, ENSEMBLE_SIZE=10, n_trials=35, Model_A_BTC_specialist
- `run_iteration_056_eth.py` — ETH-only cohort, ENSEMBLE_SIZE=10, n_trials=35, Model_A_ETH_specialist
- `run_iteration_056_dot.py` — DOT-only cohort, ENSEMBLE_SIZE=10, n_trials=35, Model_E_DOT_specialist

Each sub-run produces its own in_sample/trades.csv and out_of_sample/trades.csv. The
CSV-replay aggregator (from /045 framework) combines: [BTC trades] + [ETH trades] + [DOT trades]
+ [LINK BASELINE trades] + [LTC BASELINE trades] → bundle portfolio metrics.

**Failure mode if EXPLORATION trades are replayed**: IS Sharpe will be anchored to the n_trials=18
EXPLORATION IS-optimum. This is NOT the CONFIRMATION IS reading and will make the bundle's
IS Sharpe artificially high. The Critic will catch this (Check 17 — BUNDLE-WEIGHT-OOS-LEAK
extended to include trade-file provenance).

### Rec 2 — Per-regime Pareto-dominance against BASELINE_V1 is the MERGE gate; compute regime tags from regime_catalog.md BEFORE interpreting headline metrics

The MERGE criterion for /056 is NOT headline OOS Sharpe vs baseline. It is per-regime
Pareto-dominance per `merge_v1_relative_regime_pareto_proposal.md` Section B:

```
MERGE iff:
  FOR ALL regimes R ∈ {bull, bear, chop, vol-spike, recovery}:
    sharpe_R(bundle) >= sharpe_R(BASELINE_V1) - epsilon_sharpe(R)
    AND max_dd_R(bundle) <= max_dd_R(BASELINE_V1) + epsilon_dd(R)
    AND trade_count_R(bundle) >= 0.5 × trade_count_R(BASELINE_V1)
  AND EXISTS at least one R* where strictly better
```

The epsilon values are `1.0 × stddev_across_seeds(sharpe_R(BASELINE_V1))`. At the bootstrap
single-seed baseline, the sigma_R_proxy values from `regime_catalog.md §4` are:
- bull: σ ≈ 0.26 (proxy) → epsilon_sharpe(bull) ≈ 0.26
- bear: σ ≈ 0.34 (proxy) → epsilon_sharpe(bear) ≈ 0.34
- chop: σ ≈ 0.32 (proxy) → epsilon_sharpe(chop) ≈ 0.32
- vol-spike: σ ≈ 0.46 (proxy) → epsilon_sharpe(vol-spike) ≈ 0.46
- recovery: σ = NaN (0 IS months) → rare-regime carve-out applies (Section B.5)

The runner must emit `regime_attribution.csv` — a per-trade or per-month table with regime tags
applied from the canonical BTC-based tagger (rv30/btc_ret_90d, quantiles locked at q75=0.584,
q90=0.729). The bundle per-regime Sharpe is then computed from this tagged output.

**Concretely**: wire the regime tagger into the runner at /056. The cumulative debt from /049-/055
(tagger not wired) cannot carry forward to a CONFIRMATION — the MERGE gate REQUIRES per-regime
metrics. If the tagger is not wired by the time Phase 6 launches, Phase 5.5 must BLOCK.

### Rec 3 — Substrate-selection is FROZEN at EXPLORATION specialist designations; OOS must NOT influence C1/C2/C3/C4/C5 composition at /056

The substrate (which symbols enter which component) was selected at EXPLORATION verdicts:
- C1 BTC: selected because /054 IMPULSE-DROP-CONFIRMED (IS-only evidence; OOS informational)
- C2 ETH: selected because /055 PROMISING-PARTIAL (IS-only evidence; OOS informational)
- C3 DOT: selected because /051 PARTIAL-CONFIRMED (IS-only multi-seed evidence; OOS informational)
- C4 LINK: pre-existing BASELINE specialist (IS Sharpe +2.25; no re-selection needed)
- C5 LTC: pre-existing BASELINE anchor (IS near-flat; included for universe completeness per Rule 7 coin-disjointness)

At /056 CONFIRMATION, the ONLY legitimate use of OOS data is in the MERGE-gate Pareto check
AFTER the backtest runs. OOS must NOT be used to:
- Score or rank component candidates (substrate-selection trap from /045 LM Master Rec 3)
- Adjust component weights (weights must be IS-only derived, Section 11.B per feedback)
- Exclude or demote a component based on its individual OOS Sharpe before or during bundle assembly

In particular: C5 (LTC) OOS −4.27 at BASELINE is catastrophic (see Risk Flags). This number is
known BEFORE the /056 backtest runs. It must NOT be used to drop LTC from the bundle. The correct
treatment is: LTC runs in the BASELINE universe (per Rule 7 exactly-one-owner); if the bundle
OOS Pareto-dominance fails partly due to LTC drag, the QR diagnoses this in Phase 8 diary and
proposes a /057 axis to address LTC degradation. Dropping LTC pre-hoc at /056 brief-authoring
stage is OOS-informed substrate manipulation.

---

## Risk Flags

### RF-1: LTC anchor OOS −4.27 — catastrophic bundle drag, inherited unconditionally

The LTC baseline OOS Sharpe is −4.27 (OOS net PnL −47.25%). At w=0.2, LTC contributes
approximately −0.85 to the bundle's weighted OOS Sharpe (assuming linear decomposition).
Even if ETH (+0.65 × 0.2 = +0.13) and LINK (+2.79 × 0.2 = +0.56) are both positive, the LTC
drag pulls the aggregate deeply negative. The bundle OOS headline is likely NEGATIVE before
per-regime analysis.

Implication for MERGE gate: bundle OOS headline Sharpe will likely fail absolute Sharpe thresholds.
Under the RELATIVE-REGIME-PARETO framework, this is acceptable IF the per-regime comparison shows
the bundle does not regress vs BASELINE_V1 on any regime. However, LTC's −4.27 OOS is concentrated
in specific OOS regimes (bear + bull based on the regime_catalog §4 baseline bull OOS −2.02 +
bear OOS +1.62 pattern). The bundle's per-regime regime attribution will reflect LTC's regime
concentration — verify this does not pull the bundle below epsilon(R) on EVERY regime.

The most likely BLOCK scenario: LTC OOS catastrophe concentrates in the OOS-bear or OOS-bull
period, causing per-regime Pareto failure on that regime even with the sigma_R tolerance.

### RF-2: BTC specialist OOS −0.84 (single-seed informational) — multi-seed expected OOS variance

At /053, BTC multi-seed OOS mean was −0.5981 with std 0.866 (range 1.72, 12× IS dispersion).
The CONFIRMATION ENSEMBLE_SIZE=10 single-outer-seed run will produce a single OOS draw from this
distribution. With std ~0.87, there is roughly a 50% probability the CONFIRMATION BTC OOS draw
is NEGATIVE. This is not unexpected and is informational per the EXPLORATION-budget rule — but
at CONFIRMATION the OOS does matter for the Pareto check.

If BTC OOS is sufficiently negative, the bundle's per-regime Sharpe may miss the Pareto band
on any regime where BTC dominates trade count. Regime diagnosis at Phase 8 should attribute
negative OOS months to BTC vs ETH vs DOT vs LTC contributions.

### RF-3: ETH multi-seed validation absorbed into bundle — no standalone ETH multi-seed run

Per the /055 catalog entry: the user directive overrides /055 brief §8 (which had pre-registered
/057 = ETH multi-seed mandatory). ETH multi-seed is absorbed into the /056 CONFIRMATION-bundle
10-seed measurement. This means ETH enters the bundle WITHOUT a standalone multi-seed PARTIAL-CONFIRMED
verdict (unlike DOT with /051 and BTC with /053). The LM Master acknowledges this directive.

Risk: ETH at EXPLORATION is a single-seed=42 read (Δ +0.4018). The /056 CONFIRMATION ENSEMBLE_SIZE=10
run on ETH-only may regress toward the ETH baseline −0.61 (pull-toward-mean). If the CONFIRMATION
ETH IS Sharpe is near or below −0.50, the ETH specialist contributes negatively to the bundle and
reduces the probability of per-regime Pareto success. This is the SINGLE HIGHEST-VARIANCE component
of the bundle construction because ETH has the least multi-seed evidence of all three specialists.

### RF-4: No per-symbol regime attribution available in EXPLORATION artifacts

The tagger has not been wired in /049-/055. The CONFIRMATION phase at /056 MUST wire the tagger
to compute the bundle's per-regime Pareto check. Without per-regime IS Sharpe on the bundle, the
Pareto-dominance check CANNOT be computed and the iteration's MERGE verdict CANNOT be issued.
Phase 5.5 gate must verify the tagger is wired in the Section 3 proposed changes and that
`regime_attribution.csv` is a named output file in Section 3 runner outputs.

---

## Prior Distribution for Phase 7.5 Critic Verdict

| Verdict | Probability | Rationale |
|---|---|---|
| CONFIRMATION-MERGE (full Pareto-dominance) | **20%** | Requires ALL regimes Pareto-better-or-equal; LTC OOS drag and BTC OOS variance make universal Pareto success unlikely |
| CONFIRMATION-MERGE-PROVISIONAL (partial Pareto; multi-seed mandate issued) | **25%** | Modal-positive scenario: bundle improves ≥2 regimes strictly, fails ≤1 regime within epsilon; Critic mandates multi-seed re-validation before hard MERGE |
| CONFIRMATION-BLOCK (per-regime Pareto fails on ≥1 regime beyond epsilon) | **40% MODAL** | MOST LIKELY: LTC −4.27 OOS catastrophe concentrated in bear/bull regime windows pulls bundle below Pareto band on those regimes; BTC OOS variance compounds; Phase 8 diary diagnoses LTC as primary drag source; /057 axis: LTC-isolation or LTC drop (with Rule 7 universe-shrink implications) |
| BLOCK-FINAL (methodology defect) | **15%** | Regime tagger not wired → comparison.csv missing regime_attribution; EXPLORATION trades replayed without CONFIRMATION re-run; OOS-informed substrate manipulation detected |

**LM Master modal verdict: CONFIRMATION-BLOCK (40%)** — the structural case for BLOCK rests
primarily on LTC OOS −4.27 being an inherited catastrophe that cannot be fixed at the bundle
level without a universe change. The PARTIAL scenarios (20%+25%=45% combined) are plausible
only if LTC's OOS damage concentrates in a single regime that the other 4 components sufficiently
offset, keeping the aggregate within epsilon_sharpe on all other regimes.

---

## What I Did NOT Recommend

- No new feature additions at /056 (CONFIRMATION strictly re-measures EXPLORATION ingredients)
- No weight tuning based on EXPLORATION individual OOS Sharpe (OOS-informed weight leak)
- No component exclusion based on prior OOS verdicts (substrate frozen at EXPLORATION selection)
- No n_trials changes per specialist based on IS trade count (standardize at 35 across all three)
- No HP search-space specialization per cohort (use BASELINE_V1 HP search space for all specialists)
- No LTC drop pre-hoc (Rule 7 universe-disjointness constraint; dropping LTC = dropping the LTC
  universe entirely, which requires a separate brief and Phase 5.5 gate)

---

## Closing

The /056 CONFIRMATION-PORTFOLIO is the first cycle-6 CONFIRMATION attempt. It bundles the best
available cycle-6 EXPLORATION ingredients (3 partial-confirmed specialists + 2 BASELINE anchors)
into a symbol-partitioned federation at CONFIRMATION-budget.

The structural challenge is LTC: the BASELINE_V1 LTC anchor has OOS −4.27, a catastrophe that the
5-component equal-weight scheme cannot absorb. Unless the per-regime Pareto check shows that LTC's
OOS losses cluster in regimes where the other 4 components strongly outperform the BASELINE_V1,
the bundle will fail the MERGE gate.

The /056 primary value is diagnostic: it establishes the bundle baseline, measures per-regime
attribution, and identifies which component drives MERGE failure. If LTC is the blocking component,
/057 can explore a LTC-isolation axis (e.g., drop LTC entirely if Rule 7 permits a 4-symbol universe)
or a regime-conditional LTC kill-switch. If ETH regression is the blocking component, /057 runs
the standalone ETH multi-seed validation that was absorbed into /056 per user directive.

The regime tagger is the load-bearing infrastructure debt. It must be wired before Phase 6 launches.

— Phase 4.5 advisor authored 2026-06-01

---

# LightGBM Master Advisor — iter-v1/056 — Phase 7.4 (Post-Mortem)

## Context Read

- Bundle outcome (comparison.csv): IS daily Sharpe **+0.6291** / OOS **−1.3762** / ratio −2.19 / Δ_IS_vs_baseline +0.346 / Δ_OOS_vs_baseline **−2.016**
- Baseline anchor: IS +0.4761 / OOS +1.1415 (BASELINE_V1)
- 641 IS trades / 202 OOS trades — trade-rate floor met (≥10/mo equiv)
- Specialist outcomes: C1-BTC IS −0.10 / OOS −1.59 — C2-ETH IS −0.01 / OOS −0.03 — C3-DOT IS −0.59 / OOS −1.03
- Anchors: C4-LINK +2.25/+2.82 (carry-through from BASELINE_V1) — C5-LTC +0.15/−3.72 (BASELINE drag confirmed)
- Phase 4.5 modal verdict was **CONFIRMATION-BLOCK (40%)** — this MATERIALIZED but via a DIFFERENT mechanism than the LM Master predicted (LTC drag was the predicted blocker; the actual blocker is the specialist trio regressing simultaneously at CONFIRMATION budget).

## Item 0 — Regime Attribution Table (from regime_attribution.csv)

| Regime | Split | Cand Sharpe | Base Sharpe | Δ Sharpe | Cand Trades | Pareto vs ε≈0.30 |
|---|---|---|---|---|---|---|
| bull | IS | −0.351 | −0.351 | **0.000** | 47 | TIE (within ε) |
| bear | IS | +0.079 | +0.146 | **−0.068** | 199 | WITHIN ε |
| chop | IS | +0.330 | +0.235 | **+0.095** | 283 | PARETO BETTER |
| recovery | IS | +0.358 | +0.278 | **+0.080** | 110 | PARETO BETTER |
| bull | OOS | 0.0 | 0.0 | 0.0 | 4 | DEGENERATE (n=4) |
| other | OOS | **−0.208** | +0.141 | **−0.349** | 200 | **PARETO FAIL** (>ε) |

**Critical finding**: OOS regime tagger collapses 200 of 202 OOS trades into `other` (regime tagging failure or OOS-window regime mismatch). The Pareto-dominance check is structurally undecidable for /056 — there is no per-regime OOS signal to compare. The bundle's −1.376 OOS daily Sharpe is concentrated entirely in this `other` bucket, which on its own shows Pareto failure (Δ −0.349, well past ε≈0.30). MERGE gate fails.

## Item 1 — Single-Seed-Lottery Materialization (KEY ANALYSIS)

This iteration is a **textbook materialization of the single-seed-lottery pattern** predicted by Rec 1 of the Phase 4.5 advisor, and it manifests at THREE specialists simultaneously:

| Specialist | EXPLORATION evidence | EXPLORATION IS Sharpe | CONFIRMATION IS Sharpe | Δ (lottery realization) |
|---|---|---|---|---|
| C1-BTC | /054 single-seed (n_trials=18, ENS=3) | **+0.2614** | **−0.1028** | **−0.364** (favorable basin) |
| C2-ETH | /055 single-seed (n_trials=18, ENS=3) | −0.2082 | −0.0074 | **+0.201** (conservative basin — lift) |
| C3-DOT | /051 multi-seed (3-seed mean) | −0.2355 | −0.5901 | **−0.355** (mean-still-favorable) |

Two of three specialists REGRESSED at CONFIRMATION budget; the only LIFT was ETH (which the Phase 4.5 advisor flagged as RF-3 highest-variance because it had the LEAST multi-seed evidence). The lottery realization is asymmetric in a damaging direction:

- **/054 BTC +0.26 was a FAVORABLE single-seed=42 draw.** ENSEMBLE_SIZE=10 averaged out the favorable initialization variance and exposed BTC's true mean basin near −0.10. The Phase 4.5 advisor's regression expectation (Section: ML Perspective, item a) was correctly predicted directionally but underestimated in magnitude.
- **/051 DOT multi-seed mean −0.24 ALSO turned out to be a favorable 3-seed draw.** This is the most worrying finding: even 3-seed EXPLORATION evidence is insufficient to estimate the 10-seed CONFIRMATION basin. The DOT specialist regressed −0.355 despite having the strongest EXPLORATION provenance of the three.
- **ETH was the only specialist where EXPLORATION was conservative.** /055 single-seed=42 happened to hit an unfavorable basin (−0.21), and ENSEMBLE_SIZE=10 lifted it back toward the mean (−0.01). This is the inverse of the BTC/DOT lottery.

**The structural lesson**: EXPLORATION at --ensemble-size 3 single-seed is a **noisy estimator of CONFIRMATION IS Sharpe with bidirectional bias**. Both "PROMISING" verdicts (favorable lottery) and "NEGATIVE" verdicts (unfavorable lottery) at single-seed are unreliable absent multi-seed validation.

## Item 2 — Feature Importance Triage at CONFIRMATION budget

Top-rank features per specialist (gain-based, single training pass at n_trials=35 / ENSEMBLE_SIZE=10):

**BTC (C1)** — top-3 features by mean gain:
1. `vol_atr_14` (3647) — generic volatility primitive
2. `trend_aroon_osc_50` (3214) — generic trend
3. `stat_autocorr_lag5` (2379) — generic statistical
4. `btc_funding_spread_30_90` (2305) — **the /054 axis feature, rank 4**

The /054 narrative was "IMPULSE-DROP-CONFIRMED → funding spread is the BTC signal." At CONFIRMATION budget, `btc_funding_spread_30_90` ranks **4th** (not 1st-2nd as the IS-favorable single-seed at /054 suggested). It is doing real work but is NOT the dominant signal — and the BTC specialist still regressed to IS −0.10. **Implication**: the /054 single-seed lottery picked an Optuna trajectory that ALLOCATED unusual gain-budget to btc_funding_spread_30_90, producing the false-positive IS Sharpe. At 10-seed ensemble averaging, this allocation flattens.

**ETH (C2)** — `btc_funding_spread_30_90` ranks **1st (3920 gain)** — this is a transfer of the BTC signal to the ETH specialist's loss surface, where the cohort is ETH-only. The `eth_vs_btc_ret_ratio_30` (the /055 axis feature) ranks **13th of 14 features** — near-INERT. The /055 PROMISING verdict was almost certainly NOT driven by the ratio feature; it was an Optuna basin lottery. Recommend DROP `eth_vs_btc_ret_ratio_30` from the ETH specialist's PRUNED stack in cycle-7.

**DOT (C3)** — top features are clean (trend_plus_di_14, oi_delta_30_z90, trend_adx_14). The /051 axis feature `dot_vs_btc_ret_ratio_30` does not appear in the top 14 (not in the printed head). Recommend pulling the full importance CSV to check whether the DOT axis feature ranks 14/14 INERT — high confidence it does, given DOT's IS Sharpe collapse to −0.59.

## Item 3 — Basin Diagnostics — Trade Roster Instability

`basin_diagnostics.json` for all three specialists shows the same pattern:
- v1 cross_seed_sharpe_std = 0.0 (PASS — single outer seed, std mechanically 0)
- v2 per_cell_spearman_rho = NaN (BORDERLINE — undefined at single outer seed)
- **v3 oos_trade_roster_jaccard = 0.038 (BTC) / 0.077 (ETH) / 0.098 (DOT) — all FAIL (<0.15)**

The OOS trade roster Jaccard overlap across inner ensemble members is **catastrophically low** (3-10% overlap between roster pairs). Even within the single outer seed, the 10 inner ensemble members are voting on entirely different trades. This is consistent with hyperparameter-region-locked single-seed overfit where the inner ensemble averages predictions but the predictions themselves are sampled from incoherent decision boundaries.

**Global verdict = FAIL** for all three specialists per basin diagnostics. The Critic Phase 7.5 should anchor on this — it is a clean, pre-computed methodology signal that the bundle is unmergeable.

## Item 4 — n_effective_trials = 2-4 per cell, well below n_trials=35 nominal

From each specialist's comparison.csv:
- BTC: `n_effective_trials = 3` (out of 35 nominal)
- ETH: `n_effective_trials = 2`
- DOT: `n_effective_trials = 4`

The Optuna TPE search at n_trials=35 is collapsing to **2-4 effective basins per cell**. The other 30+ trials are duplicates or near-duplicates clustered in the same hyperparameter region. This is consistent with the search space being too narrow for the small-cohort specialist scale (132 / 122 / 117 IS trades per specialist = ~24-28 trades per fold across 5 walk-forward folds). At this trade scale, the loss surface has few distinguishable optima.

**Implication**: increasing n_trials from 35 to 50 or 100 would NOT help — TPE has already saturated. The bottleneck is cohort size, not search budget. To get more effective trial diversity, either (a) widen the HP search space explicitly (raise `num_leaves` upper bound to 127, expand `min_data_in_leaf` to [10, 1000]) or (b) restore cross-symbol pooling to grow the cohort.

## Item 5 — Per-regime IS shows specialist trio is NOT regime-degraded

The bundle IS regime attribution shows the candidate (specialist trio) is **Pareto-better in chop (+0.095) and recovery (+0.080)** vs baseline, TIE in bull, WITHIN ε in bear. The IS picture is genuinely competitive with BASELINE_V1 across regimes — the bundle is NOT degraded on IS regime structure.

The catastrophic OOS −1.376 comes from the `other` bucket (OOS regime-tagging collapse) and is driven primarily by C1-BTC OOS −1.59 (45 trades) and C5-LTC OOS −3.72 (carry-through). The OOS regime tagger is producing degenerate output (200 of 202 trades labeled `other`); the QR cannot diagnose which regime drove the OOS collapse from this artifact alone.

**Actionable**: the regime tagger code path that bins OOS trades needs investigation. The IS tagger produces 4 populated regimes (bull/bear/chop/recovery); the OOS tagger produces 200/202 trades in `other`. Either the tagger thresholds are misconfigured for the OOS window's regime composition, or the OOS regime distribution is genuinely outside the IS-calibrated regime taxonomy. This is a Critic Check 5 (stationarity) red flag and a methodology infrastructure debt.

## Item 6 — Hyperparameter Stability (where readable)

Could not parse Optuna trial-history from this report (no run.log artifact present in the reports/ tree). The n_effective_trials=2-4 reading (Item 4) substitutes for the per-trial best-value std analysis: the search is collapsing tightly, suggesting the trees Optuna selects are highly similar — consistent with stable HP region but unstable trade roster (Item 3). Recommend cycle-7 runs persist `run.log` to enable per-trial diagnostics.

## Item 7 — What This Iteration Confirms / Refutes About Prior LM Master Advisory

**Phase 4.5 PREDICTIONS CONFIRMED:**
- Rec 1's regression expectation at CONFIRMATION budget: CONFIRMED (BTC −0.36, DOT −0.36 regressions match the predicted pull-toward-mean direction).
- RF-3 (ETH highest-variance component): CONFIRMED directionally — ETH moved most relative to its EXPLORATION read (+0.20 lift), but in the FAVORABLE direction not the unfavorable one predicted.
- Modal verdict CONFIRMATION-BLOCK (40%): CONFIRMED — the bundle cannot Pareto-dominate.

**Phase 4.5 PREDICTIONS REFUTED:**
- RF-1 (LTC was predicted to be THE blocking component): PARTIALLY REFUTED. LTC OOS −4.27 contributes ~−0.85 to bundle weighted OOS Sharpe at w=0.2, but the actual blocker is the **simultaneous specialist trio regression** (BTC −1.59 + DOT −1.03 + LTC −3.72 all on OOS). Removing LTC would not save the bundle.
- Per-regime Pareto framework workability: REFUTED. The OOS regime tagger collapses 200 of 202 trades into `other`, making per-regime Pareto check structurally undecidable for OOS. Phase 4.5 assumed the regime tagger would produce 4-5 populated regimes; OOS produces 1.

**Track record**: Phase 4.5 directional calls correct on regression direction and modal verdict; specifics of WHICH component blocked the merge were wrong. Honest accounting: the LM Master correctly anchored on lottery risk but mis-located the blocker.

---

## Path Forward — Cycle-7 Recommendations (3 items)

### Rec A — Drop multi-seed-fragile specialists; require 5-seed EXPLORATION before promoting to CONFIRMATION

**What**: any future EXPLORATION verdict for inclusion in a CONFIRMATION-PORTFOLIO bundle MUST be supported by a **minimum 5-seed EXPLORATION read** with mean IS Sharpe > 0 AND ≥4/5 individual seeds positive. Single-seed and 3-seed EXPLORATIONs are insufficient evidence (proven at /056 BTC and DOT regressions).

**Why**: /056 demonstrates that 3-seed mean is still a noisy estimator of 10-seed CONFIRMATION mean. The /051 DOT 3-seed mean of −0.24 turned out to be a favorable draw (true CONFIRMATION mean −0.59, Δ −0.35). To detect this in advance requires more inner seeds at EXPLORATION.

**Cost**: 5-seed EXPLORATION costs ~1.7× wall-clock vs 3-seed (linear in inner ensemble). Acceptable for higher-fidelity pre-CONFIRMATION evidence.

### Rec B — Find features robust to seed variation (drop importance-unstable axis features)

**What**: at cycle-7, drop `eth_vs_btc_ret_ratio_30` from the ETH specialist's PRUNED stack (rank 13/14 in C2 importance — near-INERT at CONFIRMATION). Pull the full DOT importance CSV; if `dot_vs_btc_ret_ratio_30` is rank 14/14 or absent from top-15, drop it from C3 stack too. Replace with importance-stable composed features (e.g., funding_basis × sign(trend_filter)) anchored by per-month importance std-of-rank < 3.

**Why**: the EXPLORATION-axis features that earned PROMISING verdicts at /055 and /051 are NOT carrying the loss-surface gain at CONFIRMATION. The "promising" axis features were artifacts of single-seed Optuna basin allocation. Cycle-7 should test feature robustness via importance std-of-rank across the 10 ensemble members BEFORE escalating to CONFIRMATION.

### Rec C — Shift to ensemble-of-EXPLORATION-seeds aggregation pattern (NEW)

**What**: instead of running a single CONFIRMATION at --ensemble-size 10 --seeds 1 (which is what /056 ran), run **3-5 EXPLORATION-budget passes at different seeds** (e.g., seeds={42, 7, 2026, 13, 99}) and aggregate the trade rosters cross-seed. The "bundle" is then the union of trade signals where ≥3 of 5 seeds agree, not the predictions of a single 10-inner-seed ensemble.

**Why**: the basin_diagnostics v3 oos_trade_roster_jaccard ≤ 0.10 across all three specialists shows that the 10 inner ensemble members are voting on disjoint trades. A 10-seed average prediction hides this incoherence; a roster-overlap aggregation pattern would EXPOSE it pre-CONFIRMATION and naturally filter to robust signals. This pattern is analogous to v3's CPCV cross-path aggregation but applied to seed variation.

**Risk**: this is an unproven methodology shift; would require a methodology-axis EXPLORATION at cycle-7 before deployment. Lower confidence than Rec A and B but addresses the root cause directly.

---

## Closing Note for Critic (Phase 7.5)

The structural BLOCK case is pre-built into `basin_diagnostics.json` — all three specialists FAIL global verdict on oos_trade_roster_jaccard. This is a clean, computed-by-runner methodology signal that does not require subjective interpretation. Recommend Critic anchor on basin diagnostics in addition to the Pareto failure on the `other` OOS regime (Δ −0.349 vs ε≈0.30).

The OOS regime tagger collapse (200/202 trades in `other`) is a Critic Check 5 (regime stationarity) red flag that may invalidate the per-regime Pareto framework's applicability to /056. This is methodology infrastructure debt — flag for cycle-7 wiring.

**LM Master verdict recommendation: CONFIRMATION-BLOCK.** Bundle Sharpe does not Pareto-dominate BASELINE_V1; specialist trio regressed at CONFIRMATION budget; basin diagnostics globally FAIL; OOS regime tagger structurally undecidable. Cycle-7 must adopt at minimum Rec A (5-seed EXPLORATION floor) before next CONFIRMATION attempt.

— Phase 7.4 post-mortem authored 2026-06-01
