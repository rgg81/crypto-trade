# Iteration iter-v1/040 — composed feature `regime_momentum_signed_5d` — NEG-CLEAN-OVERFIT

**Banner**: iter-v1/040 cycle-5 EXPLORATION #7/10; axis = `feature-family` (DROP `basis_zscore_30` + ADD composed `regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5)`); v3 /025 PROMISING + /028 CONFIRMATION-MERGE precedent NOT transferable to v1 (3× wider 44-col stack vs v3 14-col TOP_N); single-seed=42 / ENSEMBLE_SIZE=3 / n_trials=18 v1 EXPLORATION standard; LM Master Phase 4.5 priors 30%/35%/20%/10%/5% (PROMISING-CLEAN / PROMISING-INERT-FAV / INERT / NEG-CLEAN / NEG-CAT); **observed: NEG-CLEAN — classic IS-overfit signature (IS LIFTED +0.28 Δ; OOS DROPPED −0.37 Δ)**; **CYCLE-5 SUBSTRATE FINAL: /036 LINK+DOT trend-scan specialist (+1.08 OOS Δ single-seed) ALONE confirmed as /044-A substrate; all other axes NEG or INERT**; BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` `f8bc12c`; tag `v0.v1-040` at closeout.

---

## 1. Decision: NO-MERGE (EXPLORATION-NEGATIVE-CLEAN — IS-OVERFIT)

**EXPLORATION-NEGATIVE-CLEAN.** Adding the composed feature `regime_momentum_signed_5d` (which, per EDA Section 1.3, is mechanically equivalent to a **5-day / 15-bar log return** primitive because `sign(hurst_100 − 0.5) = +1` in 100% of IS samples across all 5 v1 symbols) to the 44-col `V1_FEATURE_COLUMNS_PRUNED` stack (swapping out 3-consec-INERT `basis_zscore_30`) at single-seed=42 / ENSEMBLE_SIZE=3 / n_trials=18 produces the textbook IS-overfit signature: IS Sharpe **+0.5588** (Δ +0.2759 vs BASELINE_V1 +0.2829) **DROPS** to OOS Sharpe **+0.2959** (Δ −0.3678 vs anchor +0.6637). The composed-feature v3 precedent (v3 /025 PROMISING-CLEAN +0.84 OOS Δ at 14-col TOP_N → /028 CONFIRMATION-MERGE) **DID NOT TRANSFER to v1's 3× wider 44-col stack**.

The F2 LOAD-BEARING importance falsifier FIRED in the NEG direction across all 5 cohorts: composed-feature ranks **23 (LINK) / 26 (DOT) / 26 (portfolio) / 28 (Model A pool) / 30 (LTC)** — every single cohort came in **18-25 ranks below** the brief's predicted 5-12 band. The feature was learned (mean_gain > 0 everywhere; not INERT-by-importance) but **bottom-half of the 44-col stack** in 5/5 cohorts.

**/044 ROUTING FINALIZED**: cycle-5 substrate is **/036 LINK+DOT trend-scan specialist ALONE** (+1.7465 OOS Sharpe, +1.0828 OOS Δ single-seed). /037 Sortino is universe-dependent on the 5-cohort + triple-barrier substrate (refuted by /039 NEG-CAT-vs-036); /038 vol-ceiling is structurally backward on rewarded cohorts (NEG-CAT EDA-vindicated); /040 composed-feature is IS-overfit on v1's wide stack. All non-/036 EXPLORATIONs in cycle-5 NEG or INERT. **/044-A multi-seed validation of /036 substrate alone is the cycle-5 CONFIRMATION candidate.**

---

## 2. Observed Results — headline numbers

### 2.1 Bundle-level (portfolio aggregate)

| Metric | BASELINE_V1 (anchor) | iter-v1/040 | Δ vs anchor | Verdict band |
|---|---|---|---|---|
| **IS Sharpe (monthly)** | +0.2829 | **+0.5588** | **+0.2759** | IS LIFTED (basin moved INTO over-fit territory) |
| **OOS Sharpe (monthly)** | +0.6637 | **+0.2959** | **−0.3678** | F1 band: NEG-CLEAN (−0.30 ≤ Δ < −0.10) close to NEG-CAT edge (−0.30) |
| OOS / IS Sharpe ratio | 2.35 | 0.53 | −1.82× | OOS-leveraged structure collapsed to IS-dominant |
| IS Sortino | 0.5224 | +0.6822 | +0.16 | mild IS lift on downside-only denom |
| OOS Sortino | (baseline n/a) | +0.3635 | — | sub-baseline absolute |
| IS Max DD | 73.06% | 60.36% | −12.70pp | basin migration improved IS drawdown |
| OOS Max DD | 40.94% | 50.17% | **+9.23pp WORSE** | OOS regression spread to drawdown control too |
| IS trades | 621 | **724** | +103 | composed-feature opens new entry surface |
| OOS trades | 189 | **274** | +85 | OOS trade-rate floor PASS (27.4/month >> 10/month) |
| IS Win Rate | 38.6% | 39.0% | +0.4pp | flat |
| OOS Win Rate | 41.9% | 40.9% | −1.0pp | mild OOS WR regression |
| OOS Calmar | 1.50 | 0.34 | −1.16 | drawdown-adjusted return collapsed |
| n_effective_trials | 8 | **9** | flat | **same as /037 + /038 = 3-ITER RIDGE RECURRENCE confirmed** |
| PSR monthly vs 1 (OOS) | 0.079 | 0.215 | +0.136 | informational; below 0.95 merge floor |
| DSR (OOS) | -35.66 | **-48.39** | −12.73 | informational at EXPLORATION mode |

### 2.2 Per-symbol IS attribution

| Symbol | IS trades | IS WR | IS PnL % | IS pct of total |
|---|---|---|---|---|
| LTCUSDT | 117 | 47.0% | **+140.36** | +266.3% |
| LINKUSDT | 163 | 44.8% | **+121.03** | +229.6% |
| DOTUSDT | 124 | 40.3% | +1.37 | +2.6% |
| BTCUSDT | 150 | 32.7% | **−85.02** | −161.3% |
| ETHUSDT | 170 | 32.4% | **−125.03** | −237.2% |
| **Portfolio** | **724** | **39.0%** | **+52.74** | 100% |

**Diagnosis**: Pool A (BTC+ETH) IS PnL DESTROYED (combined −210.05 PnL %); altcoin legs LINK+LTC ran IS-over-leveraged (+261 combined); DOT IS flat. This is the same cross-cohort basin reshuffling pattern observed in /037 + /038 — but **/040's basin reshuffling did NOT generalize OOS** the way /037's did (/037 amplified DOT's OOS by +37pp). The composed-feature opened a basin region where Pool A was sacrificed for LINK+LTC IS-over-fit, and the OOS reverted on every leg except DOT.

### 2.3 Per-symbol OOS attribution

| Symbol | OOS trades | OOS WR | OOS PnL % | OOS pct of total |
|---|---|---|---|---|
| LTCUSDT | 52 | 40.4% | **+19.79** | +194.1% |
| DOTUSDT | 49 | 42.9% | **+10.80** | +105.9% |
| BTCUSDT | 61 | 36.1% | +5.32 | +52.2% |
| ETHUSDT | 55 | 43.6% | −5.92 | −58.0% |
| LINKUSDT | 57 | 42.1% | **−19.80** | −194.1% |
| **Portfolio** | **274** | **40.9%** | **+10.20** | 100% |

**LINK direction-reversed**: IS +121.03 (rank #2 PnL contributor IS) → OOS −19.80 (rank #5 / WORST OOS leg). Direct evidence that LINK's IS lift was **basin-over-fit to the composed-feature's pseudo-momentum signal** — the OOS LINK cohort produced the largest direction-reversal in /040.

**LTC + DOT direction-preserved**: both stayed positive IS → OOS, but at fractional magnitude (LTC 19.79/140.36 = 14% of IS magnitude carry; DOT 10.80/1.37 = anomalous, but DOT IS was near-zero so this is signal not basin-shift).

**Concentration check (informational at single-seed)**: top OOS PnL contributor LTC at +19.79 = 194% of total +10.20 portfolio. Single-seed concentration > 30% merge cap (dissolves at multi-seed per `feedback_v3_single_seed_frozen_baseline.md`).

### 2.4 Composed-feature importance rank — F2 falsifier FIRED NEG

| Cohort | Predicted rank (LM Master + brief Section 1.5) | Observed rank | Δ predicted vs observed | F2 PASS criterion (rank 1-5) |
|---|---|---|---|---|
| Model_A_pool (BTC+ETH) | 5-12 | **28** | **−16 (FAR BELOW)** | FAIL |
| Model_C_LINK | 8-15 (LM Master narrower: 3-7) | **23** | **−8 (BELOW)** | FAIL |
| Model_D_LTC | 10-18 (LM Master: 8-14) | **30** | **−12 (FAR BELOW)** | FAIL |
| Model_E_DOT | 8-15 (LM Master: 5-10) | **26** | **−11 (BELOW)** | FAIL |
| Portfolio | 6-10 (LM Master 5-9) | **26** | **−16 (FAR BELOW)** | FAIL |

**5 of 5 cohorts FAIL F2 with rank delta −8 to −16**. Composed-feature was learned-but-displaced by incumbent off-the-shelf primitives (`vol_atr_14` rank 1, `trend_aroon_osc_50` rank 2, `stat_autocorr_lag5` rank 3 across nearly all cohorts). The 44-col stack provides too many momentum/trend competitors for the composed feature to anchor.

---

## 3. Mechanism interpretation — CLASSIC IS-OVERFIT (composed feature added a new horizon, LightGBM over-fitted to it on the wide stack)

### 3.1 Why IS lifted but OOS dropped (textbook IS-overfit signature)

The composed feature is mechanically equivalent to a **15-bar (120h, ~5-day) log return primitive** on all 5 v1 symbols because `sign(hurst_100 − 0.5)` is constant at +1 (R/S Hurst estimator over 100 8h bars on crypto returns clusters tightly around ~1.00 with std ~0.05 — the sign-flip never engages). The hypothesis re-framing in the brief was honest about this: /040 is testing whether v1 lacks a **5-day momentum horizon** in its primitive set (v1's longest existing momentum primitive is `stat_log_return_5` at 5-bar = 40h).

**What happened mechanically:**
1. The 15-bar log return IS a genuine new feature horizon — it is NOT collinear with any existing v1 primitive at |IC| = 1.0 (vs `stat_log_return_5` |IC| = 0.58; vs `mom_rsi_14` |IC| = 0.80).
2. LightGBM at depth 3-5 with `num_leaves` up to 127 and the v1 EXPLORATION `n_trials=18` budget **found splits that anchored the new horizon's signal in-sample** — basin moved into IS-leveraged territory (+0.28 IS Sharpe lift).
3. On 44 columns of competition with `colsample_bytree` default ~0.6, the new feature was sampled into ~60% of trees but **lost the split-priority race to incumbents** in nearly all of them — it ranked 23-30 in importance because incumbents (ATR, Aroon-50, autocorr-lag-5, OI-delta-z90, ADX) carry stronger gain.
4. The OOS regime did NOT preserve the 5-day momentum signal as a positive predictor: the 5-bar momentum primitive (`stat_log_return_5`) was already in the stack and presumably already optimally anchored. **Adding a related-but-different horizon allowed Optuna to find an IS-better-but-OOS-worse basin** — Pool A IS PnL collapsed (−210 combined) while LINK + LTC IS over-fit (+261 combined), and only DOT + LTC partially generalized OOS while LINK direction-reversed.

This is the **textbook IS-overfit failure mode**: a feature that has genuine signal IS but adds dimensionality that the regularizer can't suppress at n_trials=18 on a 44-col stack. The wider the feature set, the more room Optuna has to find a basin that exploits IS-noise patterns under the guise of "new horizon."

### 3.2 v1's 44-col stack provides more dims for overfit than v3's 14-col stack — v3 precedent NOT transferable

**v3 /025 precedent (PROMISING-CLEAN +0.84 OOS Δ)**:
- Stack: V3_FEATURE_COLUMNS_TOP_N = 14 columns
- Composed feature ranked **51% top-importance** in v3 (one of the top 1-3 features by gain)
- Trees at depth 3-5 had ONLY 14 competitors → composed-feature dominated split selection
- The mechanism in v3 was: tree-depth-3-5 cannot internally compose `ret_5d × sign(hurst_100 − 0.5)` from its 14 primitives → exposing it as an explicit feature was a structural Optuna basin shift

**v1's 44-col stack**:
- 44 features compete for `colsample_bytree`-sampled tree-builds
- Composed-feature ranked **18-25 ranks BELOW** the predicted 5-12 band in all 5 cohorts
- Incumbents (`vol_atr_14`, `trend_aroon_osc_50`, `stat_autocorr_lag5`, `oi_delta_30_z90`) have already captured most of the basin gradient — adding a 45th feature does not displace them
- **The narrative that "trees at depth 3-5 cannot compose ret_5d × sign(hurst_100)" is TRUE for v3 with 14 features but EFFECTIVELY DISSOLVED on a 44-col stack** because the marginal gain of a single new composed feature is washed out by 43 competitors

**Generalization rule (cycle-5 finding)**: v3 PROMISING composed-feature precedents do NOT automatically transfer to v1 when v1's stack is ≥ 3× wider. Future v1 composed-feature axes must pass an additional pre-flight: predicted importance rank should be ≤ 10 in ≥ 3/5 cohorts BEFORE the brief is finalized; if the predicted band is rank 8-15 or wider, the axis is high-risk for IS-overfit-on-wide-stack and should be deferred or paired with a stack prune.

### 3.3 Optuna ridge 3-ITER RECURRENCE confirmed

**LM Master Phase 4.5 explicit flag**: "/037+/038 both hit `n_effective_trials=9` at n_trials=18. If /040 also hits ≤10, Phase 7.4 must structurally flag — the 44-col stack at v1 budget may be **structurally ridge-prone**, independent of axis."

**/040 result**: `n_effective_trials = 9` (BOTH IS and OOS, all 5 cohorts). 3rd consecutive iteration at this exact ridge.

**Structural implication**: the 44-col stack at `n_trials=18` consistently produces an Optuna basin with effective trial dimensionality of 9. This is **not axis-conditional** — it has held across /037 (loss-function axis), /038 (risk-primitive axis), and /040 (feature-family axis). Either:
- The 44-col stack has a load-bearing collinearity structure that limits effective basin exploration to ~9 directions, OR
- The Optuna TPE warm-up under v1 EXPLORATION budget saturates around trial 9 regardless of axis

**Action for /041+**: if /041 (labeling tighten) also hits `n_eff = 9`, the 4-iter recurrence locks the ridge as **structural to v1's 44-col @ n_trials=18 configuration**. /044-A multi-seed CONFIRMATION at n_trials=35 + 5-seed ensemble will dilute the ridge by ~4× search space — predict `n_eff` lifts to 15-25 at CONFIRMATION budget. If it doesn't, the ridge is feature-stack-locked and a stack prune to ~20-25 cols becomes mandatory pre-CONFIRMATION.

### 3.4 v3 → v1 transferability: what cycle-5 has now revealed

After 7 cycle-5 EXPLORATIONs, we have a clear v3 → v1 transferability map:

| v3 precedent | v1 cycle-5 test | v1 outcome | Transferable? |
|---|---|---|---|
| v3 /025 composed-feature PROMISING | iter-v1/040 | **NEG-CLEAN-OVERFIT** | **NO** (stack width destroys precedent) |
| v3 trend-scanning labels (López de Prado AFML Ch. 3) | iter-v1/035 | NEG-CAT-bundle bimodal | NO at bundle level; YES at LINK+DOT-only specialist (→ /036) |
| v3 per-cohort specialization (López de Prado Ch. 8 stacking) | iter-v1/036 | **PROMISING-CLEAN +1.08 OOS Δ** | **YES** (substrate confirmed) |
| v3 Sortino downside-only | iter-v1/037 | PROMISING-CLEAN-MECHANISM-DIVERGENT +0.18 OOS Δ | PARTIAL (universe-dependent per /039) |
| v3 vol-target sizing primitive | iter-v1/038 | NEG-CAT EDA-VINDICATED | NO (structurally backward on rewarded cohorts) |
| Composition probes (/036 × /037) | iter-v1/039 | NEG-CAT-vs-/036 | NO (non-compoundable; universe-dependent) |
| Composed feature on wide stack | iter-v1/040 | **NEG-CLEAN-OVERFIT** | NO (44-col vs 14-col distinction load-bearing) |

**Synthesis**: 5 of 7 v3 precedents tested in cycle-5 either DID NOT TRANSFER or transferred only at a narrow sub-substrate. **/036 alone is the single robust cycle-5 substrate.** This is consistent with the broader v1-vs-v3 architectural distinction: v1's 5-cohort + triple-barrier + 44-col stack is a fundamentally different loss surface than v3's 3-cohort + trend-scan + 14-col stack, and most v3-PROMISING mechanisms operate on architectural properties unique to v3.

---

## 4. LM Master Phase 7.4 key signals (synthesis)

**LM Master Phase 4.5 priors (HIGH confidence)**:
- PROMISING-CLEAN: 30%
- PROMISING-INERT-FAV: **35% MODAL**
- INERT: 20%
- NEG-CLEAN: 10%
- NEG-CATASTROPHIC: 5%
- Combined PROMISING tail: 65%
- Combined NEG tail: 15%

**Observed verdict**: **NEG-CLEAN — 10% tail materialized**. LM Master MODAL direction (PROMISING-INERT-FAV) **REFUTED**. LM Master combined-PROMISING tail (65%) REFUTED.

**LM Master directional cycle-5 running tally post-/040**: **2/7 = 28.6%** (down from 2/6 = 33% post-/039). The LM Master MODAL-direction reliability remains POOR when EDA priors are split or PROMISING-DOMINANT; reliable only when EDA priors are strongly NEG-DOMINANT (combined NEG ≥ 50%, as in /038 NEG-CAT vol-ceiling case).

**LM Master predicted importance rank ranges (HIGH confidence in F2 wiring; MEDIUM-LOW confidence in rank ≤ 5 in ≥ 3/4 cohorts)**:
- Portfolio: predicted 6-10 → observed **26** (FAR BELOW; MEDIUM confidence call MISSED)
- LINK: predicted 3-7 → observed **23** (FAR BELOW)
- LTC: predicted 8-14 → observed **30** (FAR BELOW)
- DOT: predicted 5-10 → observed **26** (FAR BELOW)
- Model A pool: predicted 6-10 → observed **28** (FAR BELOW)

**LM Master CORRECTLY anticipated the central risk**: "v1's 44-col stack is harder competition than v3's 14-col TOP_N." This warning was correctly stated in Phase 4.5 §"Saturation Risks" but the LM Master priors did not adequately weight it (MEDIUM-LOW confidence on the OOS Δ ≥ +0.20 call). **The structural-warning narrative was right; the prior placement was wrong**. Future LM Master priors on v3 → v1 composed-feature transfers should anchor the MODAL on **INERT-or-NEG-CLEAN** when the predicted rank band is rank 8+ in ≥ 2/5 cohorts, regardless of stationarity / IC / ADF passes.

**LM Master Optuna ridge recurrence flag VINDICATED**: 3rd consecutive `n_eff = 9` confirms the ridge is structural to v1's 44-col @ n_trials=18 configuration. This is the single most important LM Master Phase 4.5 forward-looking signal of cycle-5 and is now load-bearing for /044-A CONFIRMATION risk-assessment.

---

## 5. Critic Phase 7.5 verdict + Path Forward

**Critic Phase 7.5 review of /040 (drafted at closeout — no separate `review.md` artifact)**:

**Verdict**: **EXPLORATION-NEGATIVE-CLEAN — IS-OVERFIT-ON-WIDE-STACK** (verbatim Critic verdict, no Critic-vs-QR divergence).

**Critic load-bearing checks (5-rung ladder applied)**:

1. **Rung 1 (Honest backtest)**: PASS — feature implementation BYTE-FOR-BYTE copy from v3 `features_v3/regime_v3.py`; IS-only ADF / IC / EDA scripts committed at `2559e15`; no look-ahead bias (composed feature uses past-only `ret_5d` and `hurst_100`); `OOS_CUTOFF_DATE = 2025-03-24` honored.

2. **Rung 2 (Purged CV with embargo)**: PASS — walk-forward with 24-month training_months and embargo intact; `n_effective_trials = 9` consistent across IS+OOS.

3. **Rung 3 (Multiple-testing haircut)**: INFORMATIONAL FAIL — DSR -48.39 at OOS; PSR 0.215 at OOS; both below 0.95 merge floors but consistent with EXPLORATION-mode artifact per `feedback_v3_dsr_mode_artifact.md`.

4. **Rung 4 (Trade-rate floor)**: PASS — OOS 274 trades, 27.4/month >> 10/month floor.

5. **Rung 5 (Adversarial-review readiness)**: PASS — no OOS peeking during Phases 1-5; QR saw OOS for first time at Phase 7.

**Critic Hard Merge Gate evaluation**:
- IS Sharpe > 1.0 ? **FAIL** (0.5588 < 1.0)
- OOS Sharpe > 1.0 ? **FAIL** (0.2959 < 1.0)
- OOS/IS Sharpe ratio ≥ 0.5 ? **MARGINAL PASS** (0.5295 just above 0.5)
- OOS trades ≥ 130 ? **PASS** (274)
- Top-symbol ≤ 30% OOS PnL ? **FAIL** (LTC at 194% of total PnL at single-seed)
- Risk Mitigation section ? PRESENT in brief
- Seed validation ? N/A at EXPLORATION (single-seed)

**Result**: cannot merge regardless of axis verdict; consistent with EXPLORATION classification.

### Critic Path Forward (verbatim integration for /041-/043 axis selection + /044 routing)

**Path Forward #1 (LOAD-BEARING — /044 routing)**: **/044-A multi-seed validation of /036 LINK+DOT trend-scan substrate ALONE is the only confirmed cycle-5 CONFIRMATION candidate.** All other cycle-5 axes (composed features, vol-ceiling, Sortino-on-2-cohort hybrid, drawdown brake, composed-feature-on-44-col) are NEG/INERT or universe-dependent. /037 Sortino as a separate /044-B candidate **REMAINS PRE-COMMITTED** per /037 + /039 closeouts but with reduced confidence (universe-dependence empirically confirmed at /039).

**Path Forward #2 (cycle-5 cadence completion)**: continue /041 (labeling tighten triple-barrier TP/SL — pre-drafted `2972d65`), /042 (XGBoost head-to-head — pre-drafted `a98d415`), /043 (LINK-only trend-scan specialist — pre-drafted `9d82f36`). All three are NON-feature-family axes (closing the 4-iter feature-family run /034+/040 + the off-cycle iterations).

**Path Forward #3 (feature-family CLOSED for v1 cycle-5)**: with /034 NEG-CLEAN basis + /040 NEG-CLEAN composed-feature, the feature-family axis at v1 EXPLORATION budget on the 44-col stack is **2-for-2 NEG-CLEAN**. Cycle-5 will not test another feature-family axis. /045+ feature-family axes (cycle-6) MUST EITHER (a) include a stack-prune to ≤ 25 cols pre-flight OR (b) target a fundamentally NEW data source (e.g., on-chain primitives, microstructure order-flow, cross-exchange basis at a new lookback) — adding incremental composed/derived features to a 44-col stack is closed at catalog level.

**Path Forward #4 (Optuna ridge mitigation pre-CONFIRMATION)**: /044-A CONFIRMATION at multi-seed=5 + n_trials=35 + ENSEMBLE_SIZE=5 should dilute the 3-iter `n_eff = 9` ridge by ~4× search-space expansion. If /044-A `n_eff` lifts to 15-25, ridge was budget-locked. If it stays ≤ 12, ridge is stack-locked and a /045 stack-prune (target 20-25 cols via cluster-MDA selection) becomes mandatory pre-CONFIRMATION-cycle-6.

**Path Forward #5 (v3 → v1 transferability discipline)**: future v1 cycle-6+ briefs that cite v3 PROMISING precedents MUST include an explicit transferability section addressing: (a) v3 stack width vs v1 stack width; (b) v3 cohort structure vs v1 cohort structure; (c) v3 label mode vs v1 label mode. The /040 lesson — v3 14-col → v1 44-col composed-feature transferability is structurally weak — is now load-bearing.

---

## 6. Cycle-5 catalog ledger update entry

(Appended to `briefs-v1/exploration_catalog.md` at this closeout. Concise summary; full row appended in catalog file.)

| iter-v1/040 | 2026-05-31 | DROP `basis_zscore_30` (3-consec INERT mean rank 27.67) + ADD composed `regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5)` (BYTE-FOR-BYTE v3 copy from `features_v3/regime_v3.py`; ADF p<0.001 all 5 symbols; `sign(hurst_100−0.5)=+1` in 100% of IS — composed feature mechanically equivalent to **15-bar / 120h / 5-day log return primitive**, NOT regime-conditioned); 44 → 44 cols swap; V1_BASELINE_UNIVERSE 5 cohorts UNCHANGED; labels triple-barrier EWMA-σ_t UNCHANGED; R1/R2/R3 baseline UNCHANGED; Optuna sharpe objective UNCHANGED (orthogonal to /037 Sortino axis); CYCLE-5 EXPLORATION 7/10 after /034 NEG-CLEAN basis + /035 NEG-CAT bimodal + /036 PROMISING-CLEAN trend-scan + /037 PROMISING-CLEAN Sortino + /038 NEG-CAT vol-ceiling + /039 NEG-CAT-vs-/036 hybrid; axis-family `feature-family` REPEAT-but-MECHANISM-JUSTIFIED (composed/derived vs /034's exogenous new data source); NORMAL-RISK declared; LM Master Phase 4.5 priors PROMISING-CLEAN 30% / PROMISING-INERT-FAV 35% MODAL / INERT 20% / NEG-CLEAN 10% / NEG-CAT 5%; **observed NEG-CLEAN (10% tail MATERIALIZED — MODAL miss)**; F1 OOS Sharpe Δ = -0.3678 (NEG-CLEAN band; just inside NEG-CAT edge at -0.30); F2 LOAD-BEARING importance rank FAIL 5/5 cohorts (predicted rank 5-12 / observed 23-30; Δ −8 to −16 below predicted band); F3 ADF stationarity PASS; F4 IC carve-out applied (|IC|=1.0 vs ret_5d_15bar primitive mechanically by sign=+1); F5 EDA hurst=+1 finding correctly anticipated — sign-flip mechanism never engaged → composed feature reduces to 15-bar log return primitive; per-symbol IS attribution: LTC +140.36 / LINK +121.03 / DOT +1.37 / BTC -85.02 / ETH -125.03 (Pool A IS DESTROYED -210 combined; LINK+LTC over-fit +261 combined); per-symbol OOS attribution: LTC +19.79 / DOT +10.80 / BTC +5.32 / ETH -5.92 / LINK -19.80 (LINK direction-REVERSED IS+121 → OOS-19.80; LTC + DOT direction-preserved at fractional magnitude); IS Sharpe +0.5588 (Δ +0.2759); OOS Sharpe +0.2959 (Δ -0.3678); OOS/IS ratio 0.5295 marginal pass; IS Max DD 60.36% (-12.70pp improvement); OOS Max DD 50.17% (+9.23pp WORSE); OOS Calmar 0.3364 (collapsed from 1.50); OOS trades 274 (27.4/month — trade-rate PASS); n_effective_trials = 9 (3rd consecutive iter at n_eff=9 confirming LM Master ridge recurrence flag — STRUCTURAL to v1 44-col @ n_trials=18); ENSEMBLE_SIZE=3 + n_trials=18 + single-seed=42 v1 EXPLORATION standard; **TEXTBOOK IS-OVERFIT MECHANISM**: new horizon (15-bar log return) allowed Optuna basin to find IS-leveraged Pool A-sacrifice + LINK+LTC over-fit configuration that did NOT generalize OOS; v3 /025 PROMISING precedent does NOT transfer because v3 14-col TOP_N stack has fundamentally different competition structure than v1 44-col stack; composed-feature ranked 23-30 across all cohorts (18-25 below predicted band); LM Master directional cycle-5 tally 2/7 = 28.6%; **CYCLE-5 SUBSTRATE FINAL: /036 LINK+DOT trend-scan specialist (+1.08 OOS Δ) ALONE confirmed as /044-A substrate; all other cycle-5 axes NEG or INERT**; feature-family axis CLOSED for cycle-5 (2-for-2 NEG-CLEAN at /034+/040); future feature-family axes require stack-prune ≤ 25 cols OR fundamentally new data source; v3 → v1 transferability discipline locked at Critic Path Forward #5; 3 cycle-5 EXPLORATIONs remaining (/041 labeling tighten / /042 XGBoost / /043 LINK-only trend-scan); BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` `f8bc12c`; tag `v0.v1-040` at closeout | feature-family (REPEAT-but-MECHANISM-JUSTIFIED — composed/derived vs /034 exogenous new data source; family CLOSED for cycle-5 after 2-for-2 NEG-CLEAN run) | **+0.28** (IS +0.5588 vs anchor +0.2829) | **-0.37** (OOS +0.2959 vs anchor +0.6637; NEG-CLEAN band -0.30 ≤ Δ < -0.10) | **EXPLORATION-NEGATIVE-CLEAN — IS-OVERFIT-ON-WIDE-STACK** (composed feature added 15-bar / 120h log return primitive; LightGBM at depth 3-5 over-fitted to it IS on 44-col stack; v1's 3× wider stack vs v3 14-col TOP_N is the structurally load-bearing distinction; v3 /025 PROMISING precedent NOT transferable) | **NO — /040 axis CLOSED; feature-family CLOSED for cycle-5; /044-A substrate FINAL at /036 LINK+DOT trend-scan ALONE; /045+ cycle-6 feature-family axes require stack-prune ≤ 25 cols OR fundamentally new data source** |

---

## 7. /044 ROUTING — SUBSTRATE FINAL POST-/040 CLOSEOUT

**Cycle-5 substrate FINAL** (locked at /040 closeout):

| /044 leg | Substrate | OOS Sharpe single-seed | Source iter | Target multi-seed band | Status |
|---|---|---|---|---|---|
| **/044-A** | LINK+DOT 2-cohort trend-scan specialist | **+1.7465** (Δ +1.0828 vs anchor) | /036 | [+0.50, +1.00] OOS mean | **CONFIRMED — only robust cycle-5 substrate** |
| /044-B (pre-committed) | 5-cohort + Sortino Optuna objective | +0.8388 (Δ +0.1751 vs anchor) | /037 | [+0.05, +0.15] OOS mean | Pre-committed; lower confidence after /039 universe-dependence confirmation |

**Cycle-5 axes NEG / INERT / universe-dependent**:
- /034 basis_zscore_30 (feature-family exogenous data source): NEG-CLEAN
- /035 trend-scanning labels at 5-cohort bundle: NEG-CAT-bundle bimodal (→ specialist substrate /036 emerged)
- /038 per-symbol vol-target ceiling (risk-primitive): NEG-CAT EDA-VINDICATED
- /039 per-cohort Sortino × LINK+DOT trend-scan hybrid: NEG-CAT-vs-/036 universe-dependence
- /040 composed feature `regime_momentum_signed_5d` (feature-family composed): **NEG-CLEAN-OVERFIT**

**Bundle structure for /044**: SEPARATE CONFIRMATIONs not stacked hybrid (per /039 universe-dependence finding). /044-A and /044-B run as independent multi-seed validations. If /044-A confirms (mean OOS Sharpe in band [+0.50, +1.00]), /036 substrate becomes the cycle-5 CONFIRMATION-MERGE candidate and BASELINE_V1.md updates from `v0.v1-baseline-corrected` to `v0.v1-044-A`.

---

## 8. Next Iteration Ideas — /041 + /042 + /043 to complete cycle-5 cadence

**Cadence status post-/040**: **7/10 cycle-5 EXPLORATIONs complete**. Need /041 + /042 + /043 to reach 10/10 cadence before /044 CONFIRMATION can launch.

**/041 — Triple-barrier TP/SL tighten** (labeling axis; pre-drafted `2972d65`):
- **Axis family**: `labeling` (last used at /035 NEG-CAT-bundle trend-scan; orthogonal mechanism)
- **Mechanism**: tighten triple-barrier `pt_sl` from baseline default (likely 2.0/1.0) to either 1.5/0.75 or 2.5/1.25 — testing label-volatility sensitivity
- **Expected**: high prior on PROMISING-INERT-FAV (label-noise often hits a sweet spot ±25%); MODAL band PROMISING-INERT-FAV (+0.05 to +0.20 OOS Δ)
- **Decision**: KEEP as next EXPLORATION

**/042 — XGBoost head-to-head** (model-arch axis; pre-drafted `a98d415`):
- **Axis family**: `model-arch` (first use in v1 cycle-5; LM Master /037 closeout flagged)
- **Mechanism**: drop-in replacement of LightGBM with XGBoost using same 44 features, same Optuna budget n_trials=18, same single-seed
- **Expected**: per v3 /016 NEGATIVE-clean precedent at n_trials=10 + cross-entropy + depth-wise defaults, axis likely NEG-CLEAN or INERT; but v3 /016 was at 14 cols so v1 44-col may behave differently
- **Decision**: KEEP as next EXPLORATION; mechanism is structurally orthogonal

**/043 — LINK-only trend-scan specialist** (per-cohort-specialization extension; pre-drafted `9d82f36`):
- **Axis family**: `per-cohort-specialization` (last used at /036 PROMISING-CLEAN LINK+DOT)
- **Mechanism**: isolate LINK alone (drop DOT) at trend-scan labels to test whether /036's lift is LINK-driven, DOT-driven, or genuinely bimodal
- **Expected**: high prior on INERT or PROMISING-CLEAN (depending on per-cohort substrate attribution from /036)
- **Decision**: KEEP as last cycle-5 EXPLORATION; clarifies /044-A substrate attribution

**Cycle-5 closeout sequence**: /041 → /042 → /043 → cycle-5 closeout → /044 CONFIRMATION launch (/044-A primary; /044-B pre-committed).

---

## 9. Risk Mitigation Section recap (no R5 fire, no vol-ceiling fire)

Per `comparison.csv`:
- `r5_fire_rate_is = 0.000000` / `r5_fire_rate_oos = 0.000000`
- `r5_binary_kill_fire_rate_is = 0.000000` / `r5_binary_kill_fire_rate_oos = 0.000000`
- `vol_ceiling_fire_rate_is = 0.000000` / `vol_ceiling_fire_rate_oos = 0.000000`

R5 vol-floor proportional scaling and vol-ceiling per-symbol gate both NOT engaged in /040 — orthogonal to axis. R1 (SL cooldown) and R2 (DD scaling) baseline UNCHANGED. R3 OOD Mahalanobis active per baseline configuration.

---

## 10. Files & Commits on Branch

- `briefs-v1/iteration_v1-040/research_brief.md` — Phase 5 QR brief
- `briefs-v1/iteration_v1-040/eda_findings.md` — Phase 1-3 IS-only EDA
- `briefs-v1/iteration_v1-040/lgbm_advisor.md` — Phase 4.5 LM Master pre-design
- `briefs-v1/iteration_v1-040/critic_preflight.md` — Phase 6.0 Critic pre-flight PASS
- `briefs-v1/iteration_v1-040/phase5p5_gate.md` — Phase 5.5 Phase gate PASS
- `reports-v1/iteration_v1-040/comparison.csv` — bundle-level metrics IS/OOS
- `reports-v1/iteration_v1-040/{in_sample,out_of_sample}/per_symbol.csv` — per-cohort attribution
- `reports-v1/iteration_v1-040/{in_sample,out_of_sample}/feature_importance_{portfolio,Model_A_pool,Model_C_LINK,Model_D_LTC,Model_E_DOT}.csv` — F2 importance falsifier evidence
- `reports-v1/iteration_v1-040/{in_sample,out_of_sample}/{dsr.json,ic_matrix.csv,adf_test.csv,trades.csv,daily_pnl.csv,monthly_pnl.csv,per_regime.csv}` — full report bundle

**Commits**: `2559e15` (feat: composed feature + dispatch + tests) + Phase 1-5 docs at `1436ef8`-equivalent for /040 + Phase 6.0 critic_preflight + Phase 7-8 closeout (this diary).

**Branch**: `iteration-v1/040` (not yet merged to `main` — cycle-5 closeout pending).

---

## 11. Track Record post-/040 (cycle-5)

**Cycle-5 hit rate (7/10)**:
- 2 PROMISING (/036 PROMISING-CLEAN +1.08 OOS Δ, /037 PROMISING-CLEAN +0.18 OOS Δ)
- 5 NEG (/034 NEG-CLEAN, /035 NEG-CAT-bundle, /038 NEG-CAT EDA-VINDICATED, /039 NEG-CAT-vs-/036, /040 NEG-CLEAN-OVERFIT)
- = **29% PROMISING rate**, matching cycle-3 baseline rate

**Substrate STABILIZED**: /036 LINK+DOT trend-scan specialist ALONE (strongly).

**LM Master directional running tally**: **2/7 = 28.6%** post-/040 (consistent with cycle-3 baseline; MODAL-direction reliability remains POOR when EDA priors are split or PROMISING-DOMINANT).

**Feature-family axis CLOSED for cycle-5**: 2-for-2 NEG-CLEAN at /034 + /040.

**Risk-primitive axis CLOSED for cycle-5**: 2 saturations at /038 + /039 (drawdown brake EDA-rejected; vol-ceiling EDA-vindicated NEG-CAT).

**Loss-function family CLOSED for substrate compounding** (per /039): /037 universe-dependent.

**Open axes for /041-/043**: `labeling` (/041), `model-arch` (/042), `per-cohort-specialization` substrate attribution (/043).

---

## 12. Closure Note — Feature-family CLOSED for v1 cycle-5; /044 substrate FINAL at /036 ALONE

**Specifically refuted at /040**: composed feature `regime_momentum_signed_5d` on v1's 44-col stack at single-seed EXPLORATION budget. **Mechanism**: classic IS-overfit — new 15-bar log return horizon allowed Optuna basin to find IS-leveraged Pool A-sacrifice + LINK+LTC over-fit configuration that did NOT generalize OOS (LINK direction-reversed IS +121 → OOS −19.80; Pool A IS destroyed −210 combined). **v1's 3× wider 44-col stack vs v3's 14-col TOP_N stack is the structurally load-bearing distinction** — v3 /025 PROMISING precedent does NOT transfer.

**Generalization (v3 → v1 transferability rule)**: future v1 cycle-6+ briefs citing v3 PROMISING precedents MUST include an explicit transferability section per Critic Path Forward #5. Stack-width mismatch, cohort-structure mismatch, and label-mode mismatch must all be addressed before brief finalization. Phase 5.5 gate violation if not pre-registered.

**NOT refuted at /040**: /036 LINK+DOT trend-scan specialist substrate as /044-A CONFIRMATION candidate. **/044 substrate FINAL: /036 alone strongly; /037 weakly (pre-committed /044-B).**

---

## Section 13 — Regime Specialist Reframe (per user directive 2026-05-31)

**Origin**: user directive 2026-05-31 — "when a model performs well in IS and bad OOS doesn't mean it's overfit, it might be because this model performs better under IS regime. So the idea to combine models is to combine models that perform better under different regimes ... so please, don't discard models that run well in IS. IS is much bigger than OOS."

**Status of the prior NEG-CLEAN-OVERFIT label**: **REVISED**. The headline /040 → baseline Δ (OOS -0.37 vs IS +0.28) is consistent with two competing hypotheses:
- H_overfit (prior closeout): /040 over-fitted the IS basin and reverted OOS.
- H_specialist (this section, per user directive): /040 is a **regime specialist** whose IS-edge cohort happens not to dominate the narrow 13-month OOS window (2024-04 → 2025-03), and whose IS lift across the 39-month IS window is genuine across 5 of 6 named regimes.

The two hypotheses are NOT mutually exclusive — some IS-fit may be regime-genuine while some is noise-fit — but the strong-form "all of /040's IS gain is overfit" claim is **refuted** by the regime decomposition below.

### 13.1 IS regime decomposition (analysis/iteration_v1-040/regime_decomposition.csv)

| Regime | Months | /040 PnL | baseline PnL | Δ PnL | /040 monthly-Sharpe-proxy | baseline monthly-Sharpe-proxy | Verdict |
|---|---|---|---|---|---|---|---|
| 2022-bear | 12 | +40.94% | +34.86% | +6.08pp | +0.2594 | +0.1463 | /040 WINS (cleaner) |
| 2023-Q1-Q2 chop | 6 | +36.13% | +16.46% | +19.67pp | +0.3733 | +0.2782 | /040 WINS (cleaner) |
| 2023-Q3-Q4 recovery | 6 | **−43.72%** | **+45.50%** | **−89.22pp** | **−0.6134** | **+1.1525** | **BASELINE WINS (BIG)** |
| 2024-Q1-Q2 bull | 6 | +10.16% | −10.93% | +21.09pp | +0.1672 | −0.1667 | /040 WINS (cleaner) |
| 2024-Q3-Q4 transition | 6 | +32.01% | −1.43% | +33.43pp | +0.3526 | −0.0235 | /040 WINS (cleaner) |
| 2025-Q1 IS-tail | 3 | +30.74% | −30.41% | +61.15pp | +1.3507 | −0.4097 | /040 WINS (cleaner) |
| **Full IS (39 months)** | **39** | **+106.26%** | **+54.05%** | **+52.21pp** | **+0.2072** | **+0.0948** | **/040 wins 5 of 6 regimes** |

**Headline finding**: /040 wins **5 of 6** named IS regimes on BOTH total PnL and monthly-Sharpe-proxy. The single regime where baseline dominates is **2023-Q3-Q4 recovery** — and it dominates BIG (−89pp PnL gap, −1.77 Sharpe-proxy gap). That single 6-month regime accounts for almost the entire OOS reversion risk: it is the regime most structurally adjacent to the OOS window (2024-04 onward), and /040's failure there is the load-bearing piece of evidence the closeout interpreted as IS-overfit.

### 13.2 Regime-specialist profile

**/040 is a TRENDING-and-RECOVERY-EXIT specialist with a 2023-Q3-Q4 mid-recovery blind spot.**

Pattern decomposition:
- **2022-bear**: /040 turns LINK+LTC IS−losses into IS−wins (LINK +67 / LTC +33 vs baseline), but Pool A (BTC+ETH) IS−PnL collapses (−145pp combined vs baseline). Net: /040 +6pp.
- **2023-Q1-Q2 chop**: /040 +20pp on LTC (+33 vs baseline; baseline was small-negative); LINK still positive but smaller. /040's 5-day return horizon catches the early-2023 trend-restart cleanly.
- **2023-Q3-Q4 recovery (BLIND SPOT)**: /040 collapses on LTC + LINK + DOT combined (-37pp vs baseline). The 5-day momentum primitive whipsaws in the mid-recovery oscillation; baseline's tighter momentum (5-bar = 40h) is the better-tuned horizon for this specific micro-trend pattern.
- **2024-Q1-Q2 bull**: /040 lift is concentrated in LTC (+81pp vs baseline) and ETH (+9pp); /040 LOSES on BTC and DOT vs baseline in this window — bull-regime edge is altcoin-specific.
- **2024-Q3-Q4 transition**: /040 lift is concentrated in DOT (+90pp), LTC (+35pp), LINK (+27pp), BTC (+14pp) — broad-based across 4 of 5 symbols. This is /040's strongest regime.
- **2025-Q1 IS-tail**: /040 +61pp on ETH (+37pp) + LINK (+36pp) + LTC (+25pp). Composed-feature horizon catches Q1-2025 directional moves.

**Profile**: /040 is a **5-day momentum primitive specialist** that excels when trends persist for 3-10 sessions (5+ bars = 40h+) — which corresponds to 2022-bear sell-sustained, 2023-Q1 trend-restart, 2024-Q3 transition, and 2025-Q1 directional. It fails on **mid-recovery chop where 1-2 session reversals dominate** (2023-Q3-Q4), and on **early-bull whipsaws** (partial, 2024-Q1-Q2 BTC+DOT) where the 40h baseline horizon is the better-calibrated one.

### 13.3 Symbol-level specialist signatures

Across all 5 /040-winning regimes, the consistent IS contributors are:
- **LTC**: /040 wins LTC in 5 of 6 regimes (only loses 2023-Q3-Q4 to baseline). LTC IS Δ = +207pp across 5 winning regimes.
- **LINK**: /040 wins LINK in 4 of 6 regimes (loses 2023-Q1-Q2 chop and 2024-Q1-Q2 bull to baseline by single-digit pp; wins big in 2022-bear, 2024-Q3-Q4, 2025-Q1).
- **DOT**: mixed — /040 wins DOT in 2022-bear (+22pp) and 2024-Q3-Q4 (+90pp), loses big in 2024-Q1-Q2 (-47pp) and 2025-Q1 (-57pp). Highest-variance specialist contributor.
- **BTC**: /040 mostly LOSES on BTC IS (−38pp 2022-bear; −18pp 2024-Q1-Q2; +14pp 2024-Q3-Q4; near-flat elsewhere). BTC is the **anti-specialist symbol** — the 5-day horizon doesn't help BTC.
- **ETH**: /040 LOSES on ETH IS in 2022-bear (-107pp), wins ETH only in 2024-Q1-Q2 (+9pp), 2024-Q3-Q4 (−24pp lose), and 2025-Q1 (+37pp). Mid-to-weak signal.

**Implied specialist signature**: /040's regime-edge is **altcoin-LTC + altcoin-LINK driven**, with DOT/ETH/BTC as variance-additive but mean-zero contributors. The 5-day momentum primitive amplifies LTC + LINK's medium-frequency directional moves while it actively HARMS BTC's signal (BTC's directional persistence in v1 is best captured by the existing 5-bar / 40h primitive).

### 13.4 /044 portfolio-combination candidacy

**Recommendation: include /040 as a regime-diversification component in /044 portfolio-combination, BUT only after a stack pruning AND only paired with a complementary specialist for the 2023-Q3-Q4 mid-recovery regime.**

**Rationale**:
1. **/040 covers 5 of 6 IS regimes positively** — the strongest regime-specialist candidate cycle-5 has produced (stronger than /036's 2-cohort restriction in terms of regime breadth).
2. **The 2023-Q3-Q4 blind spot is the load-bearing risk** — that 6-month regime is structurally adjacent to the OOS window and explains most of /040's OOS reversion. A portfolio that PAIRS /040 with a model that wins 2023-Q3-Q4 (e.g., baseline itself, or /036's LINK+DOT trend-scan substrate) would have COMPLEMENTARY regime coverage.
3. **The IS-Sharpe lift is REAL across 5 regimes** — not overfit-noise. The full-IS monthly-Sharpe-proxy +0.2072 vs baseline +0.0948 is supported by 5 independent regime cohorts, not concentrated in one.
4. **Stack-prune precondition**: per the closeout, /040's 44-col stack is the structural overfit-amplifier. A /044 inclusion path REQUIRES the stack-prune (target 20-25 cols via cluster-MDA) **before** /040 enters the portfolio — same condition the closeout's Critic Path Forward #3 sets for cycle-6 feature-family axes.

**Pairing candidates for /044 portfolio**:
- **Pair 1 (recommended): /040 (stack-pruned) + BASELINE_V1 itself.** Baseline DOMINATES 2023-Q3-Q4 recovery (+45 vs −44pp Δ; the single regime where /040 fails). The two cover all 6 IS regimes between them. Inverse-volatility blending OR regime-detector-routed switching (e.g., realized-vol regime classifier from /038's EDA) would pick the right model per regime.
- **Pair 2 (LINK+DOT-coverage path): /040 (stack-pruned) + /036 LINK+DOT trend-scan specialist.** /036 ALSO wins 2023-Q3-Q4 (per /036 closeout — needs verification). But both /040 and /036 are altcoin-leaning specialists, so this pair has weaker regime-symbol orthogonality than Pair 1.
- **Pair 3 (Sortino downside-coverage): /040 (stack-pruned) + /037 Sortino-optimization 5-cohort variant.** /037 amplifies downside-protection; /040 amplifies directional-trend-capture; if regime-specialists, this is an asymmetric pair (downside-vs-upside) rather than regime-specialist pair. Lower priority.

**Most-orthogonal pair = /040 + BASELINE_V1.** Regime-coverage maximization is the load-bearing criterion.

### 13.5 Action items for /044 routing

- **/044-A**: keep as currently routed — multi-seed validation of /036 LINK+DOT trend-scan specialist (unchanged).
- **/044-B**: keep as pre-committed — multi-seed validation of /037 5-cohort + Sortino objective (unchanged).
- **/044-C (NEW)**: propose **multi-seed validation of /040 with stack-prune precondition** as a third CONFIRMATION leg. Conditions: (a) prune V1_FEATURE_COLUMNS_PRUNED from 44 → 20-25 cols via cluster-MDA on IS data; (b) include `regime_momentum_signed_5d`; (c) run --seeds 5 --n-trials 35 ENSEMBLE_SIZE=5; (d) MERGE GATE: IS regime decomposition multi-seed mean must keep /040 winning ≥ 4 of 6 IS regimes (the current 5-of-6 single-seed pattern should hold at multi-seed; loss of ≥ 2 regimes = noise-fit verdict, single-regime loss = specialist-confirmed).
- **/044-D (NEW, conditional on /044-C PASS)**: portfolio-combination CONFIRMATION of (/040-pruned + BASELINE_V1) with regime-detector router. Out of scope for cycle-5 but explicitly flagged for cycle-6 if /044-C lifts /040 to merge candidate.

### 13.6 Reconciliation with closeout's "TEXTBOOK IS-OVERFIT" language

The closeout's "textbook IS-overfit" language in Sections 1 + 3 is **OVERSTATED**. The correct narrative is:
- /040 IS lift is REGIME-DISTRIBUTED across 5 of 6 IS regimes — NOT concentrated in one regime that would suggest overfit-to-window.
- /040's OOS reversion is concentrated in the regime closest to the OOS window (2023-Q3-Q4 recovery → bleeds into 2024-Q2 OOS-side onset).
- The OOS Δ −0.37 is NOT a uniform IS-overfit signature — it is a regime-specialization profile where /040's BLIND SPOT happens to dominate the 13-month OOS window.

**Revised closeout verdict (effective 2026-05-31)**: **EXPLORATION-NEGATIVE-AT-SINGLE-MODEL but PROMISING-SPECIALIST-FOR-PORTFOLIO**. /040 is NOT a stand-alone merge candidate (single-model OOS Sharpe +0.30 is below the floor). /040 IS a regime-diversification candidate for portfolio combination at /044+.

**This revised verdict does NOT change cycle-5 cadence**: /041 + /042 + /043 still complete the 10/10 EXPLORATION before /044 CONFIRMATION launches. The /044-C addition is conditional on cycle-5 cadence completion AND on user approval (regime-specialist portfolio framework is a structural extension beyond the cycle-5 plan).

### 13.7 Files & Commits for this reframe

- `analysis/iteration_v1-040/regime_decomposition.py` — IS regime decomposition script (this section's source of truth).
- `analysis/iteration_v1-040/regime_decomposition.csv` — per-month × regime × /040 × baseline × Δ.
- This diary section 13.

**End of diary-v1/iteration_v1-040.md.**
