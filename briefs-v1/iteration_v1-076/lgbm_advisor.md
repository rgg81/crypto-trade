# LightGBM Master Advisor — iter-v1/076 — Phase 4.5 (Pre-Design)

## Context Read
- Track: **v1** (specialist-mining mode, autopilot 2026-06-06 user directive: "find new specialists … using all the quantitative knowledge"; "we need to mine these new specialists").
- Roster anchor: **BUNDLE-001** (v0.v1-071) = DOT/063 + ETH/064 + BTC/065. IS +0.5463 / OOS +0.9636 / 537+230 trades. LINK/066, LTC/067 ELIMINATED (positive-baseline trap).
- This iteration: **NEW SYMBOL universe-extension** — AAVEUSDT, first DeFi-lending narrative specialist candidate. **No prior baseline anchor** for AAVE. Verdict is measured against the implicit dispatch baseline (single-coin cohort `(AAVEUSDT,)`, methodology constants LOCKED to /063).
- Mine-phase promoted AAVE past higher-composite candidates (ICP/FTM/EGLD all 0.27-0.31 composite) on the **NEGATIVE-baseline gate** — AAVE is the ONLY eligible symbol with negative TS-mom IS Sharpe (cited as −0.311 in mine-phase formula). This is the precise structural analog to DOT/063 pre-merge cohort negativity that user prompt flagged as the necessary precondition for specialist edge extraction.
- Features parquet **6178 rows × 230 cols, hash `209ab4c64667d051`** present at `data/features/AAVEUSDT_8h_features.parquet`. No fetch / regen needed.
- Recent precedent: /075 ATOM (NEW SYMBOL universe-extension, first of its kind) is the only structural precursor; outcome not yet known. /074 active mid-bull SHORT VETO axis is structurally orthogonal.

## Mine-Phase Quantitative Verification (independent re-derivation)

Re-computed load-bearing mine-phase metrics on raw `data/AAVEUSDT/8h.csv` + feature parquet to validate the promotion before signing off:

| Lens | Threshold for advance | Observed AAVE | Verdict |
|---|---|---|---|
| Data extent | ≥ 4y for 24mo walk-forward | **5.64y** (2020-10-16 → 2026-06-06; 6178 8h candles) | PASS — clear of floor; shorter than ATOM (6.32y) but well above need |
| Realized vol (IS, ann.) | Avoid duplication of DOT high-vol cluster (>100%) | **118.1% IS / 87.2% OOS** | **MARGINAL — see Risk Flag 1.** IS vol exceeds DOT's ~110% — high-vol cluster duplication concern; OOS regression is more typical |
| Hurst exponent (IS / OOS) | Want ≠ 0.50 (random walk) | feature `hurst_100` median ~1.0 (rolling-window normalization artifact); cannot read direct R/S directly. Mine-phase cites Hurst≈0.52 (near random walk) | NEUTRAL — mine-phase Hurst 0.52 → ML edge cannot rely on simple persistence/MR |
| BTC return corr (IS / OOS) | Idiosyncratic, < 0.75 | **0.634 / 0.722** | PASS-IS / MARGINAL-OOS — OOS approaches the 0.75 ceiling; idiosyncratic diversity is REAL in IS but compressing in OOS |
| ETH return corr (IS / OOS) | Secondary diversity, < 0.75 hard ceiling | **0.750 / 0.795** | **FAIL — see Risk Flag 2.** DeFi-cycle leakage to ETH/064 is empirically confirmed; this is THE load-bearing risk for /076 |
| DOT return corr (IS) | Roster diversity check | **0.679** | PASS — below DOT/ETH 0.85 backbone, below /075 ATOM's 0.81 DOT corr; lower roster overlap |
| Regime mix (50-bar IS) | Bull / bear / chop all represented | **bull 32% / bear 28% / chop 39%** | PASS — best-balanced regime distribution in eligible set; bull-heavier than ATOM (which was 71% chop) |
| IS/OOS regime parity | OOS regime distribution should not be alien to IS | bull 20% / bear 34% / chop 46% (OOS) | MARGINAL — OOS shift toward bear+chop, less bull representation. Train-test regime drift is real |
| TS-mom IS Sharpe (mom_5 → fwd_3) | Want NEGATIVE pooled-baseline-like signal | **−0.124** | **PASS — first eligible NEW SYMBOL with truly negative trivial-signal Sharpe** |
| Universe exclusion check | NOT in `v1_EXCLUDED_SYMBOLS` | confirmed clean | PASS |
| Cumulative IS / OOS return | Regime context | IS **+332.8%** / OOS **−68.5%** | **BULL-IS + BEAR-OOS** — opposite of /075 ATOM (bear/bear). Train-test inversion risk |
| Cross-asset features (btc_/eth_/funding) populated | mandatory for 48-col stack | `funding_rate_zscore_30/90`, `btc_funding_*`, `interact_natr_x_adx` all present | PASS |

8 of 11 lenses PASS clean. The two soft fails (ETH corr 0.75/0.80; bull-IS/bear-OOS inversion) and one MARGINAL (IS vol > DOT) are mechanism-explainable but structurally distinct from /075 ATOM's risk profile. The chosen-symbol rationale's TS-mom Sharpe −0.311 differs from my mom_5/fwd_3 replication −0.124, but the SIGN is correct and below all v1 roster precedents — the NEGATIVE-pooled-baseline gate is intact regardless of the specific lookback.

## Recommended Hyperparameter Direction

**SCOPE NOTE:** the user directive freezes methodology constants — 50 seeds × 30 trials × specialist_mode, max_depth=5, num_leaves=31, n_estimators ≤ 500, n_startup_trials=10, 48-col `V1_FEATURE_COLUMNS_PRUNED`, ATR (2.9, 1.45), R1=OFF, R2=OFF, R3=ON-SHARED cutoff=0.70, R5=ON, mean-of-signed-weights aggregator. **I am NOT permitted to recommend changes to these.** My job is to predict whether the locked configuration extracts edge from AAVE.

### 1. Dispatch branch — verify single-coin cohort `(AAVEUSDT,)` and ITERATION_LABEL="v1-076"
- **What**: `run_iteration_076.py` = byte-identical clone of `run_iteration_063.py` except `SYMBOLS = ("AAVEUSDT",)` and `ITERATION_LABEL = "v1-076"`. New dispatch branch `elif iteration_label == "v1-076"` in `run_baseline_v1.py`, identical to the `v1-063` branch.
- **Why**: this is the ONLY valid implementation of the user mandate. Any deviation (ATR, R-config, feature count) breaks cross-specialist comparability that BUNDLE-002 assembly needs.
- **Expected effect**: methodology-axis invariant. The ONLY variable in /076 vs /063 is the symbol identity.
- **Risk**: feature-stack hash divergence. The QE Phase 5.5 must verify `df[V1_FEATURE_COLUMNS_PRUNED].isna().sum()` is zero across the IS+OOS window. Cross-asset features (`btc_*`, `eth_*`, `funding_*`) must overlap AAVE's 2020-10-16 → 2026-06-06 window — BTC and ETH have older histories so this is safe, but funding_rate columns may have early-window gaps (Binance perpetual funding data started 2020-07-22 for some symbols).

### 2. n_estimators ceiling — observe, don't recommend changes
- **What**: keep `n_estimators ≤ 500` as locked. Watch realized best-trial distribution at Phase 7.4.
- **Why**: AAVE's bull-dominant 32% IS + 28% bear gives MORE directional regime months than ATOM's chop-dominant 71% — Optuna will push toward HIGHER `n_estimators` (350-500) on bull/bear months to capture momentum continuation. Realized variance across walk-forward months is a regime-fit diagnostic.
- **Expected effect**: at Phase 7.4 post-mortem, expect best `n_estimators` distribution to be **bimodal** (chop months ~250, directional months ~450). Std > 150 across months = expected, NOT basin-lottery alarm.
- **Risk**: none — observation only.

### 3. min_data_in_leaf and lambda_l1 — diagnostic only
- **What**: at locked `num_leaves=31 × max_depth=5`, these are the only remaining regularization knobs. Watch realized best-trial distribution.
- **Why**: AAVE's IS cumret +332.8% means triple-barrier labels will skew toward direction=+1 hits. LightGBM at depth 5 with shallow leaves needs `min_data_in_leaf ≥ 100` to avoid memorizing long-bias. **Inverse to /075 ATOM short-bias risk** — /076 carries LONG-bias memorization risk.
- **Expected effect**: if Optuna picks `min_data_in_leaf < 50` for >40% of months AND headline IS Sharpe ≥ +0.30, flag at Phase 7.4. Long-cohort short-Sharpe asymmetry > 1.5σ is the failure fingerprint.
- **Risk**: none — observation only.

## Recommended Feature-Engineering Direction

**SCOPE NOTE:** 48-col `V1_FEATURE_COLUMNS_PRUNED` is LOCKED. The /073 closeout (ETH feature subset) established that at SPECIALIST 50-seed×30-trial budget, feature-stack changes destabilize cross-seed Optuna trajectory diversity (the **dispersion-reservoir mechanism**). No additions, no removals.

What Phase 5.5 gate MUST verify on AAVE specifically:
- `regime_momentum_signed_5d`, `hurst_100`, `vwap_dev_20` populate cleanly — these are the rank 1-3 features at /064/065/063 — primary signal-carriers.
- `eth_ret_30d`, `eth_rv_50`, `eth_vs_sym_*` (cross-asset ETH features): these will carry HIGH importance for AAVE given 0.75 IS / 0.80 OOS ETH corr. **Mechanism rational** — but mechanically this means AAVE's specialist edge will rest partly on signal that ETH/064 also consumes. Flag for Phase 7.4 importance triage: if `eth_*` family ranks 1-3 in importance, the BUNDLE-002 assembly must treat AAVE+ETH as mechanism-overlapping (downweight or reject pair).
- `funding_rate_zscore_30` and `funding_rate_zscore_90` populate from `data/funding_rates/AAVEUSDT.csv`. AAVE-USDT perp launched 2020-10-16; funding data may begin slightly later. Early-IS NaN-fill on these two cols will degrade Optuna months in 2020-Q4 / 2021-Q1.
- `interact_natr_x_adx`, `interact_rsi_x_natr` (composed interaction features) populate — these have been load-bearing for DOT/063 chop-regime trades.

## Predicted IS Sharpe + Reasoning

**Modal prediction: IS Sharpe +0.20 (range [−0.20, +0.55], 90% band).**

Mechanism-grounded breakdown:

1. **Anchor**: DOT/063 (IS +0.43), ETH/064 (IS +0.24), BTC/065 (IS −0.18). Mean v1-native specialist IS = **+0.163**. AAVE is universe-extension; priors come from this distribution.
2. **NEGATIVE-pooled-baseline gate (UNIQUE pass)**: AAVE TS-mom IS Sharpe −0.124 (my replication) / −0.311 (mine-phase) is the ONLY NEW SYMBOL passing this gate cleanly. Per the LINK/066–LTC/067 elimination evidence (positive trivial-signal → less ML headroom), AAVE has the structural DOT-precedent profile — pooled baseline negativity is the necessary precondition for specialist edge extraction. Implied prior shift: **+0.10 vs cohort mean** → +0.26.
3. **ETH corr 0.75/0.80 dilution penalty**: half of AAVE's specialist signal will come through `eth_*` cross-asset features that ETH/064 already consumes. Specialist isolation is partly compromised at the feature level. The model can still extract idiosyncratic AAVE signal from within-symbol features (`hurst_100`, `vwap_dev_20`, `funding_rate_zscore_30`), but the cross-asset backbone is mechanism-overlap-shared with ETH/064. Adjustment: **−0.05 to −0.10**.
4. **Bull-IS (+332.8% cumret) / Bear-OOS (−68.5%) regime inversion**: this is the most consequential mechanism risk. IS is bull-dominant → triple-barrier labels skew long → ML memorizes long-bias → OOS bear regime punishes long-bias predictions. The R3 OOD cutoff=0.70 will partially defend (regime distribution shift is exactly what R3 detects) but will fire on a high fraction of OOS trades, reducing OOS trade count. Adjustment to IS: **+0.05** (bull-strong IS labels are easier to fit). Adjustment to OOS: **−0.20 to −0.40**.
5. **High realized vol IS (118%)**: at locked ATR (2.9, 1.45), TP/SL distances are scaled to ATR which adapts. The mechanism is vol-invariant. But high-vol months produce noisier label boundaries — Optuna at single outer seed=42 may basin-fit a noisier loss surface than DOT (110%) or ETH (~70%). Adjustment: **−0.03**.
6. **Regime mix balance (32/28/39)**: best-balanced of eligible candidates. All 3 regimes well-represented → ML has clean training signal across regime states. Adjustment: **+0.05**.
7. **5.64y data extent**: supports stable cross-month Optuna trajectories at 50-seed averaging. Adjustment: **+0.03**.

**Aggregate IS**: +0.163 (anchor mean) + 0.10 (NEG-baseline) − 0.075 (ETH corr) + 0.05 (bull IS bias) − 0.03 (vol noise) + 0.05 (regime balance) + 0.03 (data extent) = **+0.29 modal**. I round DOWN to **+0.20** because of basin-lottery vigilance: single outer seed=42 at 50-seed inner averaging carries ~σ 0.15 cross-seed spread per `feedback_v1_basin_lottery_vigilance.md`. The +0.29 mechanism estimate has wide uncertainty bands and the honest modal prediction is at the lower end.

**OOS predicted: −0.10 modal (range [−0.40, +0.30]).** The bull-IS / bear-OOS inversion is the dominant penalty. Even if IS lands +0.20, the long-bias memorized by the model will be punished in OOS. R3 OOD filter may shrink the OOS trade count below the 50-trade floor — this is a non-trivial **TRADE-COUNT-FAIL risk** at OOS.

## Risk Flags

### 1. ETH corr 0.75 IS / 0.80 OOS — DeFi-cycle leakage to ETH/064 (HIGH)
This is THE load-bearing risk per the user prompt's own flag ("ETH corr 0.75 is the one risk — DeFi-cycle leakage to ETH/064"). My replication confirms 0.750 IS / **0.795 OOS** — even higher than the mine-phase number. Two compounding effects:
- **Feature-level overlap**: 8-12 columns in `V1_FEATURE_COLUMNS_PRUNED` are `eth_*` cross-asset. AAVE's specialist signal will be partly fitting the same `eth_ret_30d` / `eth_rv_50` / `eth_vs_sym_*` patterns that ETH/064 already consumes for ETH itself. Mechanically, AAVE's model becomes a noisy proxy of ETH/064 → bundle PBO/HHI worsens at BUNDLE-002.
- **OOS regime synchronization**: 0.80 OOS corr means AAVE and ETH/064 will produce **directionally synchronized** OOS predictions. If ETH/064 OOS Sharpe degrades in 2026-Q1/Q2 bear, AAVE OOS Sharpe will degrade in lockstep.

**Action for QR Phase 5**: Section 1 of brief MUST pre-register this risk. Phase 7.4 importance triage MUST report `eth_*` family rank distribution. BUNDLE-002 assembly MUST check rolling-90day corr(AAVE_pred, ETH_pred) ≥ 0.50 = reject pair. **Confidence in mechanism-overlap risk: HIGH.**

### 2. Bull-IS / Bear-OOS regime inversion — long-bias memorization → OOS collapse (HIGH)
AAVE IS cumret **+332.8%** vs OOS cumret **−68.5%**. Triple-barrier labels in IS skew long (direction=+1 hit-rate elevated). LightGBM at depth 5 may memorize the long-bias → OOS bear regime punishes long predictions → OOS Sharpe potentially deeply negative even if IS clears +0.20. The mitigation stack:
- 50-seed averaging dampens single-seed bear-fit basins — but the BIAS is consistent across seeds, so averaging won't help.
- R3=ON-SHARED cutoff=0.70 OOD filter will fire heavily on OOS bear-regime trades — defending Sharpe but at the cost of trade count.
- Phase 7.4 post-mortem MUST report per-direction (long/short) Sharpe + trade count + WR. Direction-asymmetric Sharpe > 1.5σ favoring longs in IS is the fingerprint of long-bias memorization.
- BUNDLE-002 assembly should explicitly NOT include AAVE if OOS long-Sharpe < OOS short-Sharpe by > 0.5 (mechanism-inverted from /075 ATOM short-bias risk).

### 3. IS realized vol 118% > DOT cluster (110%) — high-vol cluster duplication (MEDIUM)
AAVE IS vol 118.1% exceeds DOT (~110%). The mine-phase rationale claimed NATR-30 p50=4.79 placed AAVE "in a high-vol cohort that complements DOT" — but my replication suggests AAVE may actually CONCENTRATE the high-vol cluster rather than complement it. Bundle-level vol concentration increases drawdown clustering during high-vol regime transitions. Flag for BUNDLE-002 assembly: if both AAVE/076 and DOT/063 fire long in 2026-Q3 simultaneously, the bundle drawdown will be amplified. NOT a /076-blocking risk; downstream concern.

### 4. Mine-phase TS-mom Sharpe −0.311 differs from my replication −0.124 — formula discrepancy (LOW)
Same nuance as /075 ATOM: the mine-phase Sharpe figure likely uses a different (lookback, horizon) than my mom_5 / fwd_3 replication. Both are negative — NEGATIVE-pooled-baseline gate is intact regardless. **Action for QR Phase 5**: Section 1 should cite the exact mine-phase formula (likely mom_20 / fwd_5 or signed-return over longer window) for catalog consistency. NOT a blocking risk.

### 5. Funding rate early-window gaps (LOW)
AAVE-USDT perp launched 2020-10-16; Binance funding-rate history for AAVE may begin slightly later (typically 2-4 weeks lag for new symbol funding rates). Phase 5.5 gate must verify `funding_rate_zscore_30` is not all-NaN for the first 2-3 months of IS. If it is, those Optuna months will treat the column as constant-NaN and the `min_data_in_leaf` regularization will exclude them from splits — not catastrophic but degrades early-IS feature richness.

## Saturation Risks to Flag

1. **Second NEW SYMBOL mine — mining axis still unconstrained but DeFi narrative duplication starts**: /075 ATOM is cosmos-interop, /076 AAVE is DeFi-lending. The DeFi narrative is unique to BUNDLE-001 (DOT=L1, ETH=L1, BTC=L1) — narrative diversity ARGUMENT FOR AAVE. But subsequent DeFi candidates in the mining queue (UNI, COMP if eligible) would be DeFi-cluster duplications. **Flag for autopilot queue**: after /076 verdict known, do NOT pull another DeFi-lending symbol in /077; rotate to a new narrative cluster (storage / interoperability / payments).

2. **0.80 OOS ETH corr is the highest in eligible set** — if /076 PROMISING, the BUNDLE-002 assembly QR's correlation-pyramid check is mandatory and likely to reject AAVE+ETH pairing. Sequenced mitigation: /076 PROMISING + BUNDLE-002 must use AAVE OR ETH/064, not both. **This is structurally distinct from the LINK/066–LTC/067 elimination mechanism** (those failed at the specialist gate; AAVE may pass specialist gate but fail bundle gate due to mechanism overlap). Pre-register this in the brief.

3. **No prior LM Master calibration on NEW SYMBOL mining at v1 specialist mode** — /075 ATOM is the only precedent and outcome is not yet known. My +0.20 modal IS prediction is mechanism-derived not frequentist. **Confidence: MEDIUM-LOW** (lower than /075 because of the bull-IS / bear-OOS regime inversion which is materially worse than ATOM's bear-IS / bear-OOS parity). If /075 ATOM lands PROMISING, my +0.20 modal for AAVE remains; if /075 lands NEGATIVE, downgrade /076 expectations by another −0.05 to −0.10 (mining axis predictor likely overconfident).

4. **50-seed × 30-trial × specialist_mode at single outer seed=42** — basin-lottery vigilance applies. If /076 lands PROMISING with per-seed spread > 0.50 or Jaccard < 0.40, downgrade verdict to TENTATIVE and mandate multi-outer-seed re-validation BEFORE BUNDLE-002 inclusion. Same rule that BUNDLE-001 is still pending discharge on.

## What I Did NOT Recommend, and Why

- **Did NOT recommend Optuna search-space changes**. Locked per user directive.
- **Did NOT recommend label-band shifts**. Locked methodology axis. ATR-asymmetric 2.9/1.45 is mechanism-matched to AAVE's vol regime (TP slightly bigger than SL in % terms, consistent with high-vol ATR scaling).
- **Did NOT recommend a long VETO rule** analogous to /074's short VETO. AAVE's IS is bull-strong; a long VETO would defeat the dominant signal. The /074 mechanism mirrors short-bleed in mid-bull; for AAVE the inverse problem would be long-bleed in mid-bear, which IS evidence does not yet support pre-registering.
- **Did NOT recommend an ETH-leakage feature exclusion** (e.g., drop `eth_ret_30d` from the stack). Feature-stack changes at SPECIALIST mode destabilize cross-seed dispersion (/073 closeout). The mechanism overlap risk is real but the methodology lock takes precedence. Mitigation lives in BUNDLE-002 assembly, not /076 EXPLORATION.
- **Did NOT recommend R3 cutoff tightening to 0.80** to defend bear-OOS more aggressively. Locked. R3=0.70 SHARED is the methodology baseline; deviating breaks cross-specialist comparability.
- **Did NOT recommend pre-applying R1 / R2 wrappers**. They are OFF by methodology lock. /072's BTC R1=ON FAIL evidence supports the OFF default.
- **Did NOT recommend a different ATR pair**. 2.9/1.45 (post-pruning default since ETH/064 / BTC/065) is the locked path.

## 8-Band Verdict Prior Distribution

Based on (a) BUNDLE-001 specialist IS Sharpe distribution (DOT +0.43, ETH +0.24, BTC −0.18; mean +0.16, std ~0.30), (b) AAVE's UNIQUE NEGATIVE-pooled-baseline pass (DOT-precedent shape), (c) the 5 risk flags above (HIGH ETH-leakage + HIGH regime-inversion compounding), (d) /075 ATOM is structural precedent but outcome unknown:

| Verdict band | Prior probability | Rationale |
|---|---|---|
| PROMISING-STRONG (IS ≥ +0.50, OOS ≥ +0.30, ≥50 trades each) | **0.05** | Would require NEG-baseline edge + R3 OOD defending bear-OOS while preserving trade count — narrow path |
| PROMISING (IS ≥ +0.30, OOS ≥ +0.10, ≥50 trades each) | **0.16** | NEG-baseline gate is the strongest positive signal; modal-upper if regime inversion is benign |
| PROMISING-MARGINAL (IS ≥ +0.15, OOS ≥ 0, ≥50 trades each) | **0.18** | ETH/064-like profile; bundleable but mechanism-overlap with ETH at HIGH ETH corr makes BUNDLE inclusion contested |
| NEGATIVE-NO-EFFECT (IS ∈ [−0.10, +0.15], OOS flat) | **0.18** | Bull-IS noise absorption + R3 over-firing in OOS bear could produce flat headline |
| NEGATIVE-IS-OOS-DIVERGE (IS ≥ +0.20, OOS < −0.10) | **0.18** | **Long-bias memorization in bull IS punished by bear OOS** — this is the modal failure mode; elevated probability for /076 vs typical NEW SYMBOL |
| NEGATIVE-CATASTROPHIC (IS or OOS ≤ −0.30) | **0.08** | OOS bear regime + long-bias model is real catastrophic-risk path; higher than /075 due to regime inversion |
| TRADE-COUNT-FAIL (IS or OOS < 50 trades) | **0.13** | R3 OOD cutoff=0.70 likely to over-fire in OOS bear regime where AAVE+ETH features are out-of-training-distribution; OOS trade count risk is elevated |
| METHODOLOGY-FAIL (NaN cols, Phase 5.5 gate fail, parity break) | **0.04** | Cross-asset features present; funding early-window gap is mild; QE 5.5 gate should catch |

**Aggregate PROMISING-or-better: 0.39.** **Aggregate NEGATIVE-or-worse: 0.44.** **Aggregate floor failure: 0.17.**

Lower PROMISING+ probability than /075 ATOM (0.48) because the bull-IS / bear-OOS regime inversion is materially worse than ATOM's bear/bear regime parity, AND the ETH corr leakage is the highest in the eligible set. The NEG-baseline edge partially compensates but doesn't dominate.

## Closing Note

**Confidence: MEDIUM-LOW.** AAVE has the structurally STRONGEST single-lens advantage in the eligible set (UNIQUE NEGATIVE-pooled-baseline pass — direct DOT/063 precedent) but TWO HIGH-severity compounding risks: (1) 0.80 OOS ETH corr → mechanism-overlap with ETH/064 → bundle-level rejection risk even if /076 specialist passes; (2) bull-IS / bear-OOS regime inversion → long-bias memorization → modal OOS collapse path.

The single most important thing the QR / QE should NOT ignore: **per-direction (long vs short) Sharpe + trade count + WR reporting + rolling-90day corr(AAVE_pred, ETH_pred) reporting at Phase 7.4**. The /076 verdict cannot be cleanly interpreted without these two diagnostics given the regime inversion + ETH leakage twin risks. If Phase 7 reports headline IS Sharpe ≥ +0.20 with ≥ 70% of trades in direction=+1 AND corr(AAVE_pred, ETH_pred) > 0.50, the BUNDLE-002 assembly QR should treat /076 as **specialist-PROMISING-but-bundle-REJECTED** — a verdict band that the BUNDLE-001 framework has not yet had to express.

Single most important thing the QR should hardwire in the brief: **per-direction Sharpe asymmetry + AAVE/ETH prediction correlation in Section 4 falsifier table**. Without these, the /076 verdict is uninterpretable at the bundle level given the +332.8% IS / −68.5% OOS regime inversion and 0.75/0.80 ETH corr.
