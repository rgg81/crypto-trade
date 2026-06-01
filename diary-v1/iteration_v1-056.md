# iter-v1/056 — CONFIRMATION-PORTFOLIO — symbol-partitioned 5-component federation (cycle-6 CONFIRMATION 1/1)

**Tag**: `v0.v1-056`
**Date**: 2026-06-01
**Iteration type**: CONFIRMATION-MERGE-PORTFOLIO (first cycle-6 CONFIRMATION; closes the cycle)
**Cycle slot**: cycle-6 CONFIRMATION **1/1** (cycle-6 cadence: 10 EXPLORATIONs at /046-/055 → 1 CONFIRMATION at /056)
**Critic verdict**: **CONFIRMATION-BLOCK**
**Status**: **NO-MERGE**; **BASELINE_V1.md UNCHANGED** at `v0.v1-baseline-corrected` (`f8bc12c`)

**Banner**: Five-component symbol-partitioned federation at equal weight (w=0.2 each) — C1-BTC, C2-ETH, C3-DOT freshly re-run at CONFIRMATION-budget (`--seeds 1 --ensemble-size 10 --n-trials 35`); C4-LINK and C5-LTC reused from `BASELINE_V1` trade rosters. **Bundle IS daily Sharpe +0.6291 / OOS daily Sharpe −1.3762** (Δ vs baseline IS +0.346 / OOS **−2.016**). 641 IS trades / 202 OOS trades (floor PASS both). MaxDD IS 18.15% / OOS 13.56%. **Per-component multi-seed regression: BTC IS Sharpe −0.36 vs /054 EXPLORATION single-seed=42 (+0.26 → −0.10); DOT IS Sharpe −0.35 vs /050/051 EXPLORATION (−0.24 → −0.59); ETH IS Sharpe +0.20 vs /055 EXPLORATION (−0.21 → −0.01).** 2 of 3 cycle-6 PROMISING specialists FAILED CONFIRMATION-budget multi-seed re-measurement. Cycle-6 closes with **0 baseline updates** (11/12 iterations CONFIRMATION-BLOCK; /056 is the 12th).

---

## 1. Decision: NO-MERGE; CONFIRMATION-BLOCK

**Critic verdict** (Phase 7.5): **CONFIRMATION-BLOCK**. Bundle metrics do NOT satisfy the pre-registered F1 per-regime Pareto-dominance MERGE gate. Explicit regressions in 2 of 3 fresh specialists rule out CONFIRMATION-MERGE-PROVISIONAL.

| Pre-registered MERGE gate | Threshold | Observed | Verdict |
|---|---|---:|---|
| F1 Per-regime Pareto-dominance vs BASELINE_V1 | PASS on all regimes within ε_sharpe(R); strict improvement on ≥1 | FAIL on OOS-other regime (-0.21 vs +0.14 baseline); IS regimes mixed | **FAIL** |
| F2 Bundle OOS total trades | ≥ 130 | **202** | PASS |
| F4 Pairwise universe disjointness | all 10 pairs empty | all 10 pairs empty | PASS |
| F5 Weight provenance | IS-only, equal weights | equal weights (no IS optimization) | PASS |
| F6 Source checksums reproducible | match at Phase 7.5 | match | PASS |
| F2′ Bundle OOS daily Sharpe | informational (no absolute floor per `feedback_v1_merge_relative_regime_pareto.md`) | **−1.3762** | (informational; Δ vs baseline −2.016) |
| Per-component multi-seed regression check | EXPLORATION→CONFIRMATION IS Δ within ±0.10 (lottery-tight) | BTC −0.36 / DOT −0.35 / ETH +0.20 | **FAIL** (2 of 3 specialists fall outside lottery-tight band) |

**Verdict**: NO-MERGE per F1 + per-component multi-seed regression. CONFIRMATION-MERGE-PROVISIONAL is NOT applicable because the F1 failure mode is "explicit per-specialist regression at CONFIRMATION-budget", not "single-regime near-miss within 2× ε_sharpe".

**`feature_columns_count` post-iter = 48** (V1_FEATURE_COLUMNS_PRUNED unchanged — bundle was CSV-replay aggregation, no feature changes).

**`BASELINE_V1.md` UNCHANGED** at `v0.v1-baseline-corrected` (`f8bc12c`).

---

## 2. Observed Results

### 2.1 Bundle Headline Metrics

Source: `reports-v1/iteration_v1-056/comparison.csv`.

| Metric | IS | OOS | Ratio | Baseline (anchor) IS | Baseline OOS | Δ vs baseline |
|---|---:|---:|---:|---:|---:|---:|
| daily Sharpe | **+0.6291** | **−1.3762** | -2.19 | +0.2829 | +0.6395 | +0.346 / **−2.016** |
| monthly Sharpe | +0.1120 | −0.1789 | -1.60 | (annualized via daily) | — | — |
| MaxDD | 18.15% | 13.56% | 0.747 | 73.06% | 40.94% | -54.9pp / -27.4pp |
| Win rate | 41.97% | 37.13% | 0.885 | 39.9% | 39.9% | +2.0pp / -2.7pp |
| Profit factor | 1.091 | 0.837 | 0.767 | 1.060 | 1.151 | +0.03 / -0.31 |
| n_trades | 641 | 202 | 0.315 | 621 | 193 | +20 / +9 |
| Total PnL (sum w_pnl) | +15.26% | **−9.22%** | -0.60 | +54.05% | +36.96% | -38.79pp / -46.18pp |

**Headline reading**: bundle IS daily Sharpe modestly above baseline (+0.346); bundle OOS catastrophic (Δ −2.016 daily Sharpe is the largest single-iteration OOS regression in cycle-6). MaxDD compression IS −54.9pp is a structural artifact of equal-weight portfolio diversification (5 components at w=0.2 each cap the per-component DD impact at 20% of any single-component drawdown) — NOT alpha. The portfolio-level MaxDD compression cannot be cited as a methodology improvement; it is a known property of diversified symbol-partitioning at equal weights.

### 2.2 Per-Component Headline (CONFIRMATION-budget vs EXPLORATION single-seed=42)

Sources: `reports-v1/iteration_v1-056/C{1,2,3}_*/comparison.csv` (fresh CONFIRMATION sub-runs); `reports-v1/iteration_v1-{050,051,054,055}/` (EXPLORATION precedents).

| Component | Symbol | EXPLORATION IS Sharpe | /056 CONFIRMATION IS Sharpe | **Δ** | /056 CONFIRMATION OOS Sharpe | Trades IS | Trades OOS |
|---|---|---:|---:|---:|---:|---:|---:|
| C1-BTC | BTCUSDT | **+0.2614** (/054 single-seed=42) | **−0.1028** | **−0.36** | −1.5877 | 132 | 45 |
| C2-ETH | ETHUSDT | **−0.2082** (/055 single-seed=42) | **−0.0074** | **+0.20** | −0.0280 | 122 | 51 |
| C3-DOT | DOTUSDT | **−0.2355** (/051 multi-seed mean) | **−0.5901** | **−0.35** | −1.0324 | 117 | 43 |
| C4-LINK | LINKUSDT | n/a (anchor reuse) | (BASELINE_V1 LINK Model C: IS +2.25 / OOS +2.79) | — | (baseline OOS +2.79) | 146 | (~30) |
| C5-LTC | LTCUSDT | n/a (anchor reuse) | (BASELINE_V1 LTC Model D: IS +0.17 / OOS −4.27) | — | (baseline OOS −4.27) | 123 | (~33) |

**Per-component diagnosis**:
- **C1-BTC**: /054 EXPLORATION's spread-only 47-col stack at single-seed=42 produced IS Sharpe +0.2614. At CONFIRMATION budget (10-ensemble × 35-trial Optuna), IS Sharpe collapses to −0.1028. **Δ = −0.36**, well outside the lottery-tight ±0.10 band that would have signalled stable specialist edge. Conclusion: /054's BTC IS positive was a basin-lottery draw at single-seed=42; the larger Optuna search at CONFIRMATION budget overfits-to-noise the same way iter-v3/023 demonstrated (INERT-rank features at higher budget actively HARM OOS).
- **C2-ETH**: /055 EXPLORATION single-seed=42 IS Sharpe −0.2082. At CONFIRMATION budget IS Sharpe is −0.0074. **Δ = +0.20**, the only positive multi-seed lift in the bundle. ETH specialist with `eth_vs_btc_ret_ratio_30` (cross-asset return ratio at 30d, z-scored) is the ONLY cycle-6 PROMISING specialist that did not regress at CONFIRMATION-budget. OOS Sharpe is −0.0280 (essentially flat), profit factor 0.989, 51 OOS trades — ETH is not adding alpha but it is not draining the bundle either.
- **C3-DOT**: /050 single-seed=42 IS Sharpe −0.1138; /051 multi-seed mean IS Sharpe −0.2355. At /056 CONFIRMATION budget IS Sharpe collapses further to −0.5901. **Δ vs /051 = −0.35**. DOT specialist with `dot_vs_btc_ret_ratio_30` regresses ~0.45 from /050 single-seed-best to /056 CONFIRMATION-multi-seed. /051 had been classified PARTIAL-CONFIRMED off a multi-seed mean -0.2355 at smaller ensemble; /056's larger ensemble × n_trials=35 search reveals additional regression.
- **C4-LINK / C5-LTC**: anchors. C4 is the bundle's IS workhorse (+2.25 baseline IS); C5 is the bundle's OOS drag (-4.27 baseline OOS — per `feedback_v1_merge_relative_regime_pareto.md`, LTC participates unconditionally at equal weights to avoid OOS-informed substrate manipulation, but it IS the dominant OOS-drag contributor regardless of any other component's behavior). Both behave exactly per baseline rosters by construction (trade extraction was identity-mapping).

### 2.3 Per-Regime Attribution (F1 MERGE gate)

Source: `reports-v1/iteration_v1-056/regime_attribution.csv`.

| Regime | Split | Candidate Sharpe | Baseline Sharpe | Δ | Trades (cand / base) | Verdict |
|---|---|---:|---:|---:|---:|---|
| bull | IS | -0.351 | -0.351 | 0.00 | 47 / 50 | TIE |
| bear | IS | +0.079 | +0.146 | -0.07 | 199 / 222 | REGRESS (within 1ε?) |
| chop | IS | +0.330 | +0.235 | **+0.10** | 283 / 224 | IMPROVE |
| recovery | IS | +0.358 | +0.278 | **+0.08** | 110 / 124 | IMPROVE |
| bull | OOS | 0.000 (4 trades) | 0.000 (3 trades) | n/a | 4 / 3 | INSUFFICIENT-N |
| bear | OOS | 0.000 (0 trades) | 0.000 (0 trades) | n/a | 0 / 0 | NO-OOS-DATA |
| chop | OOS | 0.000 (0 trades) | 0.000 (0 trades) | n/a | 0 / 0 | NO-OOS-DATA |
| recovery | OOS | 0.000 (0 trades) | 0.000 (0 trades) | n/a | 0 / 0 | NO-OOS-DATA |
| other | OOS | **−0.208** | +0.141 | **−0.35** | 200 / 191 | **REGRESS (>1ε; F1 FAIL)** |

**F1 verdict: FAIL.** The "other" OOS regime (which captures ~99% of OOS trade roster) regressed by −0.35 daily Sharpe vs baseline — well outside any reasonable ε_sharpe(R) tolerance band. The IS-side improvements on chop (+0.10) and recovery (+0.08) cannot offset an OOS regression of −0.35 on the dominant OOS regime under any Pareto-rigorous interpretation. The OOS-bull/bear/chop/recovery regimes have zero trades in both candidate and baseline (the regime tagger is producing nearly all OOS trades in "other" — a known limitation of the simple tagger inherited from /045 framework; this is a tagger fidelity issue, NOT a candidate failure). Within the regimes that DO have OOS data, the candidate regressed.

### 2.4 Basin Diagnostics Summary

Sources: `reports-v1/iteration_v1-056/C{1,2,3}_*/basin_diagnostics/basin_diagnostics.json`. v1/v2/v3 framework (cross-seed-variance / param-Spearman / roster-overlap). Cross-component patterns:
- **v1 cross-seed variance**: BTC and DOT specialists show >2× variance vs ETH — consistent with their larger multi-seed regression. ETH's relatively-tight cross-seed variance is consistent with its +0.20 lift surviving CONFIRMATION budget.
- **v2 param Spearman**: BTC specialist's top-3 hyperparam ranks across the 10-ensemble seeds show ρ < 0.40 (low convergence) — consistent with basin-lottery diagnosis. DOT shows similar low convergence. ETH shows higher convergence (ρ > 0.55) on the top-3 hyperparams.
- **v3 roster overlap**: cross-seed trade overlap is BTC ~62%, DOT ~58%, ETH ~74%. ETH's higher overlap is consistent with its CONFIRMATION budget surviving the EXPLORATION lottery; BTC and DOT's lower overlap is the structural signature of basin-lottery EXPLORATION verdicts.

---

## 3. What Worked

1. **CSV-replay aggregator + pairwise universe disjointness assertion ran clean.** All 10 pairs empty (F4 PASS). 641 IS + 202 OOS aggregated trades, sorted by close_time, with per-component source checksums reproducible (F6 PASS). The /045 framework reused successfully at scale on 5 components.
2. **ETH specialist (C2) was the ONLY PROMISING specialist that improved at CONFIRMATION budget.** /055 single-seed=42 IS Sharpe −0.2082 → /056 CONFIRMATION-budget IS Sharpe −0.0074 (Δ +0.20). This is the cleanest evidence in cycle-6 that the ETH specialist mechanism (cross-asset return-ratio feature + ETH-only cohort head) carries genuine signal that survives multi-seed lottery dispersion.
3. **Trade-rate floor PASS across both splits.** 641 IS / 202 OOS — well above floors (≥50 IS / ≥130 OOS). The bundle is signal-rich enough to be measured cleanly; the verdict is honest negative, not low-N noise.
4. **Equal-weight construction respected by design.** No OOS-informed weighting, no IS-Sharpe-proportional optimization, no concentration manipulation. LTC participated unconditionally despite known catastrophic OOS — methodology integrity preserved per `feedback_v1_merge_relative_regime_pareto.md`.
5. **CONFIRMATION-budget multi-seed re-measurement WORKED AS DESIGNED.** Two PROMISING specialists were exposed as basin-lottery artifacts. The CONFIRMATION discipline saved a baseline update that would have unmerged within 1-2 iterations had we merged off EXPLORATION verdicts alone.

---

## 4. What Failed / Limitations

1. **2 of 3 cycle-6 PROMISING specialists were basin-lottery.** BTC at /054 (single-seed=42) IS Sharpe +0.26 → CONFIRMATION-budget −0.10 (Δ −0.36). DOT at /050-/051 single-seed=42 to multi-seed mean −0.12 → −0.24 → CONFIRMATION-budget −0.59 (Δ −0.35 from /051 multi-seed). The EXPLORATION-budget verdicts were unreliable for these specialists.
2. **Bundle OOS daily Sharpe Δ −2.016 vs baseline.** Dominated by C1-BTC OOS −1.59 and C3-DOT OOS −1.03 (both regressed at CONFIRMATION budget); partially offset by C2-ETH OOS −0.03 (essentially flat). LTC (anchor) OOS catastrophic continues to drag at equal weights.
3. **The "specialist diversification reduces variance" hypothesis did NOT translate to OOS lift.** Even with 3 fresh specialists + 2 anchor components, the bundle OOS net PnL is −9.22% (vs baseline +36.96%). Equal-weight partitioning capped MaxDD (good) but did not provide regime-adaptive OOS edge (the actual hypothesis).
4. **F1 per-regime tagger fidelity remains low.** Almost all OOS trades fell into the "other" regime bucket (200/204 of OOS trades). The bull/bear/chop/recovery OOS buckets are empty, defeating the multi-regime Pareto comparison. This is a tagger debt accumulated since /049; it now blocks cleanly measuring whether any future bundle is regime-adaptive in OOS.
5. **Cycle-6 closed 0 baseline updates over 11 iterations.** /046-/056 produced no MERGE. The hypothesis "regime-specialist bundle composition will Pareto-dominate the pooled baseline" has not held at CONFIRMATION budget.

---

## 5. Lessons (Memory writes)

1. **Single-seed=42 EXPLORATION verdicts are BASIN-LOTTERY for v1.** Multi-seed CONFIRMATION revealed 2 of 3 cycle-6 PROMISING specialists regressed by ~−0.35 each between EXPLORATION-budget and CONFIRMATION-budget. The asymmetry is fundamental: EXPLORATION at `seeds=1 ensemble=3 n_trials=18` does not exercise the loss-surface basin structure enough to estimate the multi-seed posterior. Future cycle-6 / cycle-7 EXPLORATIONs should run at minimum 2-seed validation OR PROMISING verdicts should require a pre-CONFIRMATION 3-seed proof before being included in a bundle. → **New feedback: `feedback_v1_cycle6_exploration_lottery_terminal.md`**.
2. **PARTIAL-CONFIRMED verdicts are still single-seed=42 artifacts.** DOT @ /051 was a multi-seed mean of −0.2355 at smaller ensemble; /056 CONFIRMATION's larger ensemble × n_trials=35 produced −0.59. PARTIAL-CONFIRMED is NOT a "lottery-immune" verdict — it just means the lottery was sampled twice at SMALLER ensemble. Re-validation at full CONFIRMATION budget IS NECESSARY before bundling.
3. **Per-symbol regime-specialist mandate is SOUND IN PRINCIPLE; the issue is verdict reliability at EXPLORATION budget.** The hypothesis under test (per `feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md`) is that per-IS-regime-specialist bundles generalize OOS. We have NOT falsified that hypothesis — we have only shown that we cannot SELECT good specialists from EXPLORATION-budget verdicts. The mandate continues into cycle-7; the EXPLORATION budget needs to be reformed.
4. **Portfolio-level MaxDD compression is NOT alpha; it is diversification mathematics.** Bundle MaxDD IS 18.15% vs baseline 73.06% (compression -54.9pp) is structural. 5 equal-weight components mean any single component drawdown is capped at 20% of the portfolio. This is a known property of symbol-partitioning; it cannot be cited as a methodology improvement and should not be presented as an edge ingredient.
5. **The /045 CSV-replay framework scales cleanly to 5-component federations.** Pairwise universe disjointness, source checksum, equal-weight aggregation — all worked. The framework is production-ready for /057+ bundle iterations.

---

## 6. Per-`feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md` Status

The mandate continues into cycle-7 per the explicit pin: "I want you to keep this idea for the next 2 cycles minimum." Cycle-6 closes with 0 baseline updates; cycle-7 inherits the mandate with the following operational reforms drawn from /056 lessons:

- **EXPLORATION budget reform**: cycle-7 EXPLORATIONs run minimum 2-seed validation (not single-seed=42) OR a PROMISING-verdict precondition is a pre-CONFIRMATION 3-seed proof before the specialist can be bundled.
- **Verdict band tightening**: PROMISING-PARTIAL (IS Δ ∈ [+0.30, +0.61)) should require multi-seed confirmation before being marked CONFIRMATION-ELIGIBLE.
- **Roster pruning**: BTC (/054) and DOT (/050-/051) PROMISING specialists DOWNGRADED to LEARNED-NEGATIVE in the roster. Only ETH (/055) retains PROMISING status going into cycle-7.
- **Re-evaluation trigger**: per the mandate, "2 successful CONFIRMATION-PORTFOLIO MERGEs OR end of cycle-7" — neither has fired; cycle-7 continues.

---

## 7. Path Forward (recommended /057 axis)

Two viable directions for /057, both within the cycle-7 regime-specialist mandate:

**Option A (RECOMMENDED) — Multi-seed ensemble at EXPLORATION budget**:
- `/057` = first cycle-7 EXPLORATION (1/10) under reformed budget: **3-seed at EXPLORATION** (e.g. seeds `[42, 123, 456]`, ensemble=5, n_trials=20).
- Axis: continue per-symbol regime-specialist discovery; ONE new feature per iteration on ONE symbol cohort.
- Verdict band: PROMISING-PARTIAL requires multi-seed mean Δ ≥ +0.30 (not single-seed Δ); PROMISING-SPECIALIST requires multi-seed mean Δ ≥ +0.50.
- Rationale: directly addresses the /056 lottery-failure. Halves the EXPLORATION false-positive rate by requiring multi-seed lift at verdict time instead of at CONFIRMATION-time.

**Option B — ETH multi-seed deep validation**:
- `/057` = ETH specialist (`eth_vs_btc_ret_ratio_30`) re-validated at /056 CONFIRMATION budget with 3 fresh seeds at the EXPLORATION cohort to triangulate the +0.20 lift.
- Rationale: ETH is the ONLY surviving PROMISING specialist; pinning down ETH's posterior before any further bundle assembly is the highest-information-per-iteration option.
- Tradeoff: spends an EXPLORATION slot on a single-symbol triangulation rather than discovering a new specialist.

**Recommended choice**: **Option A** as /057. Then any future bundle (cycle-7 CONFIRMATION-PORTFOLIO at /067-ish) will be assembled from specialists whose verdicts already PASS the 3-seed verdict threshold — closing the basin-lottery loophole at its source.

**Reject**: any re-run of BTC/DOT specialist axes at /057 unless preceded by a NEW feature mechanism. The basin-lottery diagnosis is the FAULT of the verdict process, not the feature mechanism — but the feature mechanisms (`btc_funding_spread_30_90`, `dot_vs_btc_ret_ratio_30`) HAVE been tested at CONFIRMATION budget and produced regression. They are LEARNED-NEGATIVE for v1 at this point.

---

## 8. Roster Update

Cycle-6 specialist roster after /056 closeout:

| Symbol | Specialist iter | EXPLORATION verdict | /056 CONFIRMATION verdict | Final classification |
|---|---|---|---|---|
| BTC | /052 / /053 / /054 | PROMISING-PARTIAL → PARTIAL-CONFIRMED → IMPULSE-DROP-CONFIRMED | IS −0.10 / OOS −1.59 | **LEARNED-NEGATIVE-AT-CONFIRMATION** |
| ETH | /055 | PROMISING-PARTIAL | IS −0.01 / OOS −0.03 | **PROMISING-CONFIRMED-FLAT** (only surviving specialist) |
| DOT | /050 / /051 | PROMISING-PARTIAL → PARTIAL-CONFIRMED | IS −0.59 / OOS −1.03 | **LEARNED-NEGATIVE-AT-CONFIRMATION** |
| LINK | (anchor only) | n/a | (BASELINE reuse) | BASELINE-ANCHOR |
| LTC | (anchor only) | n/a | (BASELINE reuse) | BASELINE-ANCHOR (OOS-drag known) |

`briefs-v1/_meta/regime_specialist_roster.csv` updated: BTC and DOT specialist rows DOWNGRADED to `LEARNED-NEGATIVE-AT-CONFIRMATION` (recorded in catalog, NOT in roster CSV — roster CSV stays append-only per /045 framework; future iteration QRs must read the catalog to see CONFIRMATION-revised classifications).

---

## 9. Cycle-6 Summary

| Iter | Type | Axis family | Verdict | Baseline update? |
|---|---|---|---|---|
| /046 | EXPLORATION | methodology | PROMISING-DIVERGENCE | NO |
| /047 | EXPLORATION | feature-family | NEG-CLEAN-PRE-EDA | NO |
| /048 | EXPLORATION | feature-family | NEG-CLEAN-PRE-EDA | NO |
| /049 | EXPLORATION | feature-family | EXPLORATION-NEGATIVE | NO |
| /050 | EXPLORATION | feature-family+risk-primitive | PROMISING-PARTIAL | NO |
| /051 | EXPLORATION | validation (DOT multi-seed) | PARTIAL-CONFIRMED | NO |
| /052 | EXPLORATION | feature-family | PROMISING-SPECIALIST-CANDIDATE | NO |
| /053 | EXPLORATION | validation (BTC multi-seed) | PARTIAL-CONFIRMED | NO |
| /054 | EXPLORATION | feature-family | IMPULSE-DROP-CONFIRMED | NO |
| /055 | EXPLORATION | feature-family | PROMISING-PARTIAL | NO |
| /056 | **CONFIRMATION-PORTFOLIO** | bundle | **CONFIRMATION-BLOCK** | **NO** |

**Cycle-6 baseline updates: 0/11.** Hypothesis under test (per-symbol regime-specialist bundles Pareto-dominate the pooled baseline) NOT falsified — it has not been cleanly evaluated yet because the EXPLORATION budget produces too-noisy verdicts. Cycle-7 inherits the mandate with reformed EXPLORATION budget per Path Forward Option A.

---

## 10. Critic Verdict (Phase 7.5, quoted)

**Verdict: CONFIRMATION-BLOCK.**

Key finding: 2 of 3 EXPLORATION PROMISING specialists FAILED multi-seed validation at CONFIRMATION budget (BTC −0.36 Δ; DOT −0.35 Δ). Only ETH improved at higher Optuna budget (+0.20). Single-seed EXPLORATION verdicts at /050-/055 were BASIN-LOTTERY-CONFIRMED for 2 of 3 specialists. Bundle IS Sharpe modestly above baseline (+0.346) is dominated by the LINK anchor and the equal-weight portfolio structure; bundle OOS Sharpe catastrophic (Δ −2.016) is dominated by BTC and DOT specialist regressions. F1 per-regime Pareto-dominance FAIL on the dominant OOS "other" regime (Δ −0.35). MERGE gate NOT met; CONFIRMATION-MERGE-PROVISIONAL not applicable due to explicit per-specialist regressions.

---

**End of diary**.
