# LightGBM Master Advisor — iter-v1/075 — Phase 4.5 (Pre-Design)

## Context Read
- Track: **v1** (specialist-mining mode, autopilot 2026-06-06 user directive: "find new specialists … using all the quantitative knowledge").
- Roster anchor: **BUNDLE-001** (v0.v1-071) = DOT/063 + ETH/064 + BTC/065. IS +0.5463 / OOS +0.9636 / 537+230 trades. ALL 5 v1-native symbols specialist-tested; LINK/066, LTC/067 ELIMINATED (positive-baseline trap).
- This iteration: **NEW SYMBOL universe-extension** — ATOMUSDT first cosmos-interop specialist candidate. **No prior baseline anchor** for ATOM. Verdict is measured against the implicit dispatch baseline (single-coin cohort `(ATOMUSDT,)`, methodology constants LOCKED to /063).
- Mine-phase composite rank 1/N (score 0.767). Features parquet **6933 rows × 230 cols, hash `0865537dc50a8d11`** — present at `data/features/ATOMUSDT_8h_features.parquet`. No fetch / regen needed.
- Recent FAIL precedents (/072 BTC R1=ON, /073 ETH feature subset, /074 ETH mid-bull SHORT VETO active) — all are BUNDLE-001 incremental-improvement axes, structurally orthogonal to NEW SYMBOL mining. /075 is the **first universe-extension EXPLORATION after BUNDLE-001 merge**.

## Mine-Phase Quantitative Verification (independent re-derivation)

I re-computed the load-bearing mine-phase metrics on raw `data/ATOMUSDT/8h.csv` to validate the rank-1 score before signing off:

| Lens | Threshold for advance | Observed ATOM | Verdict |
|---|---|---|---|
| Data extent | ≥ 4y for 24mo walk-forward | **6.32y** (2020-02-07 → 2026-06-06; 6933 8h candles) | PASS — longest in eligible set |
| Realized vol (IS, ann.) | Avoid duplication of DOT high-vol cluster (>100%) | **77.4% IS / 72.3% OOS** | PASS — mid-vol band, complements DOT (~110%), distinct from BTC (~45%) |
| Hurst exponent (IS / OOS) | Want ≠ 0.50 (random walk) | **0.489 IS / 0.412 OOS** | PASS — mean-reverting in OOS, near-random in IS; ML edge mechanism plausible |
| BTC return corr (IS / OOS) | Idiosyncratic, < 0.75 | **0.611 / 0.642** | PASS — strongest idiosyncratic diversity in CLEAN candidate set |
| ETH return corr (IS) | Secondary diversity | **0.680** | PASS — below DOT-ETH ~0.85 backbone |
| DOT return corr (IS) | Roster diversity check | **0.809** | MARGINAL — co-moves with DOT but Hurst mechanism is different (DOT is mom-leaning); accept on mechanism-divergence ground |
| Regime mix (50-bar IS) | Bull / bear / chop all represented (no zero bucket) | **bull 11% / bear 15% / chop 71%** | PASS — chop-dominant but all 3 represented |
| IS/OOS regime parity | OOS regime distribution should not be alien to IS | bull 9% / bear 16% / chop 72% (OOS) | PASS — near-identical regime shape, no train-test regime shift |
| TS-mom IS Sharpe (mom_5 → fwd_3) | Want NEGATIVE pooled-baseline-like signal | **+0.918** | **NUANCE FAIL — see Risk Flag 1** |
| Universe exclusion check | NOT in `v1_EXCLUDED_SYMBOLS` | confirmed clean | PASS |
| Cumulative IS / OOS return | Regime context | IS **−61.9%** / OOS **−66.5%** | DEEP-BEAR-IS + DEEP-BEAR-OOS — see Risk Flag 2 |

8 of 10 lenses PASS clean. The chosen-symbol rationale's claim of "TS-mom IS Sharpe +0.58" appears to use a different lookback / horizon than my replication (mom_5 / fwd_3 = +0.918, mom_10 / fwd_5 typically higher). This matters for the predicted-Sharpe calibration below.

## Recommended Hyperparameter Direction

**SCOPE NOTE:** the user directive freezes methodology constants — 50 seeds × 30 trials × ENSEMBLE_SIZE=1, max_depth=5, num_leaves=31, n_estimators≤500, n_startup_trials=10, 48-col `V1_FEATURE_COLUMNS_PRUNED`, ATR (2.9, 1.45), R1=OFF, R2=OFF, R3=ON-SHARED cutoff=0.70, R5=ON, mean-of-signed-weights aggregator. **I am NOT permitted to recommend changes to these.** My job is to predict whether the locked configuration extracts edge from ATOM.

### 1. Dispatch branch — verify single-coin cohort `(ATOMUSDT,)` and ITERATION_LABEL="v1-075"
- **What**: `run_iteration_075.py` = byte-identical clone of `run_iteration_063.py` except `SYMBOLS = ("ATOMUSDT",)` and `ITERATION_LABEL = "v1-075"`. New dispatch branch `elif iteration_label == "v1-075"` in `run_baseline_v1.py`, identical to the `v1-063` branch.
- **Why**: this is the **only** valid implementation of the user directive. Any deviation (different ATR, different R-config, different feature count) breaks the cross-specialist comparability that BUNDLE-002 assembly will need.
- **Expected effect**: methodology-axis invariant. The ONLY variable in /075 vs /063 is the symbol identity. This is the cleanest single-bit deviation.
- **Risk**: feature-stack hash divergence. `V1_FEATURE_COLUMNS_PRUNED` references columns that depend on cross-asset (`btc_*`, `eth_*`) features. Confirm at Phase 5.5 gate that the 48 columns are populated in `ATOMUSDT_8h_features.parquet` (i.e. no NaN columns from missing cross-asset window). The 230-col / 6933-row parquet preview shows the columns are present — but the QE Phase 5.5 must verify with a `df[V1_FEATURE_COLUMNS_PRUNED].isna().sum()` check.

### 2. n_estimators ceiling — observe, don't recommend changes
- **What**: keep `n_estimators ≤ 500` as locked. At 30 trials × 50 seeds, Optuna will probe the 200-500 range. Watch the realized distribution at Phase 7.4 post-mortem.
- **Why**: ATOM's 6.32y data extent + chop-dominated 71% IS regime means many flat / low-signal months will favor LOWER `n_estimators` (Optuna will pick 200-300 for those months) to avoid overfitting noise; the bear/bull months will favor 400-500. Realized variance of best-trial `n_estimators` across walk-forward months is a **diagnostic** of regime-fit basin instability.
- **Expected effect**: predictive of Phase 7.4 trial-stability triage. If best `n_estimators` jumps wildly across months (std > 150), flag basin-lottery risk despite 50-seed ensemble averaging.
- **Risk**: none — observation only, no change requested.

### 3. min_data_in_leaf and lambda_l1 — diagnostic only
- **What**: at locked `num_leaves=31` × `max_depth=5`, the bound `2^5 - 1 = 31` is saturated. `min_data_in_leaf` and `lambda_l1` are the only remaining regularization knobs in the Optuna search. Watch their realized best-trial distribution.
- **Why**: ATOM's deep-bear IS (cumret −62%) means triple-barrier labels will be **short-skewed** (more positive labels for direction=−1 than direction=+1). LightGBM at depth 5 with shallow leaves needs strong `min_data_in_leaf` (≥ 100) to avoid memorizing the short-bias.
- **Expected effect**: if Optuna picks `min_data_in_leaf < 50` for >40% of months, the model is overfitting; flag at Phase 7.4 even if headline IS Sharpe looks healthy.
- **Risk**: none — observation only.

## Recommended Feature-Engineering Direction

**SCOPE NOTE:** 48-col `V1_FEATURE_COLUMNS_PRUNED` is LOCKED. No additions, no removals. The /073 closeout (ETH feature subset) showed that at SPECIALIST mode with 50-seed × 30-trial × ENSEMBLE_SIZE=1 budget, feature-stack changes destabilize cross-seed Optuna trajectory diversity (the **dispersion-reservoir mechanism**). I am NOT recommending any feature changes for /075.

What I AM recommending the Phase 5.5 gate verify:
- `regime_momentum_signed_5d`, `hurst_100`, `vwap_dev_20` populate cleanly in `ATOMUSDT_8h_features.parquet` (these were the rank 1-3 features at /064/065 — primary signal-carriers).
- `btc_ret_30d`, `btc_rv_50`, `eth_ret_30d` (cross-asset features) have non-NaN values for the entire IS+OOS window. The chosen-symbol rationale's 0.61 BTC corr is the **mechanism** these cross-asset features must capture.
- `funding_rate_zscore_30` populates from `data/funding_rates/ATOMUSDT.csv` — funding rates were absent from older symbols' parquets and would auto-NaN-fill.

## Predicted IS Sharpe + Reasoning

**Modal prediction: IS Sharpe +0.30 (range [-0.10, +0.65], 90% band).**

Mechanism-grounded breakdown:

1. **Anchor**: DOT/063 (IS +0.43), ETH/064 (IS +0.24), BTC/065 (IS −0.18). Mean of v1-native specialist IS = **+0.163**. ATOM is universe-extension (no prior anchor); priors come from this distribution.
2. **Hurst signal**: ATOM IS Hurst 0.489 (near-random) is **less mean-reverting than DOT** (~0.43) and less trending than BTC (~0.53). ML edge mechanism is most analogous to ETH/064's mid-Hurst regime (which produced +0.24 IS). Implied prior: IS ~+0.20.
3. **Regime mix penalty**: 71% chop-dominant IS is the **highest chop fraction in the candidate set** vs DOT IS (~55% chop) and BTC IS (~60% chop). Chop regimes are where directional-momentum features (the 48-col stack's top-3 by historical importance) underperform. Adjustment: −0.05 to −0.15 vs ETH/064 implied prior.
4. **TS-mom IS Sharpe +0.918 lens**: this is **higher than DOT pre-/063** (which was ~+0.45 by recollection of cycle-6 pooled baseline). Higher trivial-signal Sharpe = LESS ML headroom (the positive-baseline trap that killed LINK/066 and LTC/067). However, the chop-dominant 71% regime and the deep-bear cumulative return (−62%) mean the trivial momentum signal IS Sharpe is driven by **short-bias short cohorts in 2024-Q2/Q3 bear-extension**, not balanced regime edge. ML can still extract edge from the chop and bull-transition regimes. Adjustment: −0.05 (partial positive-baseline trap risk, mitigated by regime decomposition).
5. **Cross-asset feature transfer**: 0.61 BTC corr + 0.68 ETH corr means `btc_*` and `eth_*` features in the 48-col stack will carry **less explanatory power** for ATOM than they did for DOT (0.85 mean cross-asset corr). However, this is exactly the **idiosyncratic diversity** mechanism mining selected for. The model will lean harder on within-symbol features (`hurst_100`, `regime_momentum_signed_5d`, `vwap_dev_20`, `atr_pct_50`) which is mechanism-orthogonal to BUNDLE-001's BTC-tilted backbone. Adjustment: +0.05 (idiosyncratic structure favors specialist isolation).
6. **6.32y data extent**: longest in eligible set; supports stable cross-month Optuna trajectories at 50-seed averaging. Adjustment: +0.05 (data-extent stability bonus).

**Aggregate: +0.20 (anchor) − 0.10 (chop) − 0.05 (positive-baseline trap) + 0.05 (idiosyncratic feature lean) + 0.05 (data extent) = +0.15 to +0.30 modal.** I lean +0.30 because the **mean-reverting Hurst 0.41 in OOS** is the most-distinct mechanism from BUNDLE-001's trend-leaning members — and the rare positive specialist-shaped signal in the candidate set.

**OOS predicted: −0.10 to +0.55 (modal +0.20).** Wider band because OOS has only 1318 candles (~5.5 months), few labels, large per-trade Sharpe noise. The deep-bear OOS regime (cumret −66.5%) is similar to IS — no obvious train-test regime shift — but a single OOS specialist with low trade count and a single regime cluster carries high variance.

## Risk Flags

### 1. TS-mom IS Sharpe +0.918 — possible positive-baseline contamination
The chosen-symbol rationale cites TS-mom IS +0.58 as "weakest among CLEAN candidates" → NEGATIVE-pooled-baseline-like profile (DOT-precedent). My replication on `mom_5 → fwd_3` returns +0.918, which would push ATOM toward the LINK/066–LTC/067 **positive-baseline trap territory** where ML has less to fix. The discrepancy is likely a different signal definition (mom_10 / fwd_5 or signed-return / fwd_1 produces different Sharpes). **Action for QR Phase 5**: Section 1 of the brief MUST cite the exact (lookback, horizon) used in mine-phase TS-mom Sharpe and confirm it is the formula used for cohort eligibility. If the +0.58 figure is mom_20 / fwd_5 (longer-horizon mean-reversion), the +0.918 short-horizon Sharpe is NOT contradictory — they measure different regimes. **Confidence in NEGATIVE-pooled-baseline profile: MEDIUM** (not HIGH).

### 2. Deep-bear IS + deep-bear OOS → short-cohort overfit risk
ATOM cumret −62% IS / −66% OOS. Triple-barrier labels at locked thresholds will skew toward direction=−1 hits. The ML may **memorize the bear-bias** and produce inflated IS Sharpe that fails to generalize. Mitigations:
- 50-seed averaging dampens single-seed bear-fit basins.
- R3=ON-SHARED cutoff=0.70 OOD filter will defend against bear-regime-shift OOS (if 2026-Q2 transitions to mid-bull, R3 fires more frequently).
- ATR-based SL/TP (2.9/1.45) is symmetric and doesn't bias toward short-PnL.
- Phase 7.4 post-mortem MUST report direction-asymmetric metrics: per-direction trade count, per-direction WR, per-direction Sharpe. If short Sharpe is +1.5 and long Sharpe is −0.5, the headline +0.3 is a regime-fit short-bias mirage.

### 3. 0.61 BTC corr is on the LOW end → cross-asset feature dilution
The 48-col `V1_FEATURE_COLUMNS_PRUNED` includes 8-12 cross-asset features (`btc_ret_30d`, `eth_ret_30d`, `btc_rv_50`, etc.). At ATOM's 0.61 BTC corr (vs DOT 0.85), these features carry less mutual information with the label. They are NOT noise (still positively correlated) but the ML edge they confer is reduced. **Mechanism-rational** for /075 but the cross-asset features may rank lower in feature importance than they did in DOT/063 — this is **expected behavior, not a bug**. Flag for Phase 7.4 importance triage: if `btc_*` family ranks rank 8-14 (not 1-3), that confirms idiosyncratic specialization is firing, not a stack failure.

### 4. v2 dead-paths catalog notes prior ATOM swap failure — orthogonal but worth pre-registering
The chosen-symbol rationale flags this as non-blocking because v2 cohort + 7-gate at single-seed is structurally distinct from v1 specialist + 50-seed. I concur — the v2 failure was a **cohort-pooled-with-7-gate-multi-bit** confound, NOT a per-symbol ATOM rejection. v1 specialist is single-coin + ATR + R3-only — clean single-bit test. **Pre-register at brief Section 1**: "Prior v2 ATOM swap failure does NOT predict /075 outcome; the methodology axis is structurally orthogonal."

### 5. 0.809 IS DOT correlation — secondary roster-diversity erosion
ATOM/DOT 0.81 IS return corr is the highest correlation in the proposed BUNDLE-002 addition slate. If /075 PROMISING, the BUNDLE-002 assembly QR must check whether ATOM+DOT are **mechanism-redundant** (both contribute to the same regime-state bucket → bundle PBO/HHI worsens). Hurst 0.41 (ATOM mean-reverting) vs DOT chop-momentum suggests mechanism-divergence is real, but rolling-correlation pyramid analysis at BUNDLE-002 assembly is mandatory. Flag for downstream, not /075 blocking.

## Saturation Risks to Flag

1. **First NEW SYMBOL mine after BUNDLE-001 — mining roster is unconstrained**: the chosen-symbol rationale claims composite score 0.767 highest. /075 is rank-1; rank-2 and rank-3 (presumably AVAX, MATIC, or ADA — see mine_phase artifacts) should be staged in the autopilot queue. If /075 PROMISING, validate the mine-phase composite predictor by checking whether rank-2 / rank-3 also PROMISING — if yes, the mining axis is open; if no, ATOM is the outlier and mining transitions to deep-EDA-per-candidate mode. Flag for QR cycle-7 expansion strategy.

2. **No prior LM Master advice on universe extension** — there is no precedent for predicting NEW SYMBOL outcomes at v1 specialist mode. My +0.30 modal prediction is a **prior** built from BUNDLE-001 member Sharpes adjusted by mechanism lenses. It is NOT a calibrated frequentist prediction. Confidence: MEDIUM. The honest signal: ATOM has the cleanest cross-cohort + idiosyncratic profile of any NEW SYMBOL candidate, but predicting LightGBM specialist IS Sharpe across a brand-new coin from EDA alone is structurally limited.

3. **50-seed × 30-trial × ENSEMBLE_SIZE=1 budget at single outer seed=42** — the basin-lottery vigilance per `feedback_v1_basin_lottery_vigilance.md` applies. Even at 50-seed averaging, the single outer seed makes the verdict TENTATIVE. If /075 lands PROMISING with per-seed spread > 0.50 or Jaccard < 0.40, downgrade verdict and mandate multi-outer-seed re-validation BEFORE BUNDLE-002 inclusion (same rule that BUNDLE-001 is still pending discharge on).

## What I Did NOT Recommend, and Why

- **Did NOT recommend Optuna search-space tightening** (e.g., narrowing `num_leaves` to [16, 31] or `learning_rate` to [0.02, 0.06]). Methodology constants are LOCKED per user directive. Even if the IS data preferred narrower bounds, the user mandate freezes them.
- **Did NOT recommend label-band shifts** (e.g., triple-barrier ATR multiplier away from 2.9/1.45). Same reason — locked methodology axis.
- **Did NOT recommend a SHORT VETO rule** (analogous to /074's mid-bull veto). ATOM's IS is deep-bear, not mid-bull; short trades are likely the PnL-positive cohort, not the bleed cohort. The /074 mechanism is mechanism-inverse for ATOM.
- **Did NOT recommend pre-applying R1 / R2 wrappers** to /075. They are OFF by methodology lock. /072's BTC R1=ON FAIL evidence supports the OFF default.
- **Did NOT recommend a different ATR pair** (e.g., 3.5/1.75 like DOT/063). /063's ATR was chosen pre-pruning at higher vol regime; 2.9/1.45 (the ETH/064 and BTC/065 default since pruning) is the locked path. ATOM's 77.4% IS realized vol is closer to ETH (~70%) than DOT (~110%), so 2.9/1.45 is mechanism-matched.

## 8-Band Verdict Prior Distribution

Based on (a) the BUNDLE-001 specialist IS Sharpe distribution (DOT +0.43, ETH +0.24, BTC −0.18; mean +0.16, std ~0.30), (b) the mine-phase Tier-1 composite score 0.767, (c) the 5 risk flags above, (d) the user directive that this is one of multiple NEW SYMBOL mines (positive selection bias slightly compensated by 6/7 strong lenses), my **subjective probability distribution over Phase 7 outcome bands**:

| Verdict band | Prior probability | Rationale |
|---|---|---|
| PROMISING-STRONG (IS ≥ +0.50, OOS ≥ +0.30, ≥50 trades each) | **0.08** | Would require both Hurst-MR mechanism + chop-survivor edge to fire — possible but uncommon |
| PROMISING (IS ≥ +0.30, OOS ≥ +0.10, ≥50 trades each) | **0.22** | Modal outcome on my mechanism analysis; BUNDLE-001 inclusion candidate |
| PROMISING-MARGINAL (IS ≥ +0.15, OOS ≥ 0, ≥50 trades each) | **0.18** | ETH/064-like profile; bundleable but signal is thin |
| NEGATIVE-NO-EFFECT (IS ∈ [−0.10, +0.15], OOS flat) | **0.20** | Chop-dominant 71% IS could absorb signal into noise; cross-asset feature dilution at 0.61 BTC corr |
| NEGATIVE-IS-OOS-DIVERGE (IS ≥ +0.20, OOS < −0.10) | **0.10** | Bear-bias short-cohort memorization → OOS regime change penalty; flagged as Risk 2 |
| NEGATIVE-CATASTROPHIC (IS or OOS ≤ −0.30) | **0.06** | Lower than typical NEW SYMBOL prior because data extent + regime parity are PASS |
| TRADE-COUNT-FAIL (IS or OOS < 50 trades) | **0.10** | R3 OOD cutoff=0.70 may over-fire on idiosyncratic ATOM features (low cross-cohort training overlap) and shrink trade count below floor |
| METHODOLOGY-FAIL (NaN columns, Phase 5.5 gate fail, parity break) | **0.06** | Cross-asset feature NaN coverage is the load-bearing risk; QE Phase 5.5 gate should catch |

**Aggregate PROMISING-or-better probability: 0.48.** **Aggregate NEGATIVE-or-worse probability: 0.46.** **Aggregate methodology / floor failure: 0.16.**

This is **near-coin-flip at the merge tier** (PROMISING+). That's not a vote against /075 — it's an honest reflection of the chop-dominant regime + locked-methodology + first-NEW-SYMBOL-precedent combination. The directive is to MINE; a 0.48 PROMISING base rate across 5-10 NEW SYMBOL candidates is exactly the autopilot yield surface the user is paying for.

## Closing Note

**Confidence: MEDIUM.** ATOM is the structurally-strongest NEW SYMBOL candidate in the eligible set on 8 of 10 lenses. The two soft FAILs (TS-mom +0.918 nuance + 0.81 DOT corr) are mechanism-explainable, not disqualifying. The most important thing the QR / QE should NOT ignore: **Risk Flag 2 (deep-bear IS + deep-bear OOS short-cohort memorization)**. If Phase 7 reports headline IS Sharpe ≥ +0.30 with ≥ 70% of trades in direction=−1, that is the failure mode to flag at Phase 7.4 triage, NOT a clean PROMISING. The fingerprint to look for in the post-mortem: per-direction Sharpe asymmetry > 1.5σ in favor of shorts, and OOS short-Sharpe collapse if the OOS window's last 30 days transition out of bear.

Single most important thing the QR should hardwire in the brief: **per-direction (long vs short) Sharpe + trade count + WR reporting in Section 4 falsifier table**. The /075 verdict cannot be cleanly interpreted without it given the −62% IS cumulative return.
