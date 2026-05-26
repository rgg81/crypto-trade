# LightGBM Master Advisor — iter-v1/020 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1. Branch `iteration-v1/020`. HEAD `377c6af`. Cycle-3 EXPLORATION #5 of 10. **THIRD per-cohort EXPLORATION** (BTC after LINK /018 + ETH /019).
- **Anchor**: portfolio `v0.v1-baseline-corrected` IS +0.2829 / OOS +0.6637. **Per-cohort anchor**: BTC-in-pool IS net_pnl −37.28% (≈ −0.12 monthly Sharpe proxy) / OOS net_pnl +33.17% (≈ +0.30 monthly Sharpe proxy). 113 IS trades / 35 OOS trades.
- **/019 outcome**: PROMISING (OOS Δ +0.65 vs ETH-anchor; +0.30 above my predicted [+0.10, +0.40] band — favorable miss). Track now 2/4 directional + 11/14 mechanism-level.
- **Critical EDA finding**: H_POOL_ANCHOR **REFUTED** at ρ = −0.022 / Spearman +0.023 / same-sign 51.7%. Pool is essentially **independent training streams** across BTC↔ETH. My /019 §7 prior was rooted in "BTC is pool ANCHOR" intuition; the diagnostic shows pool isn't borrowing signal across symbols at single-seed=42.

## 1. Pool-anchor REFUTED — implication for verdict priors

**QR's 20/55/25 is approximately correct but INERT subtype distribution should be sharpened**. The ρ ≈ 0 finding means:

- **INERT modal STRENGTHENS** to ~55-60%, but predominantly **INERT-no-effect** (|Δ|<0.10) subtype, not "INERT-preserved-asymmetric" (|Δ|∈[0.10, 0.20]). Pool independence means Optuna basin converges close to the BTC-conditional optimum the pooled model already found.
- **PROMISING tail at 20% is plausible BUT mechanism shifts**: not "intrinsic-edge surfaces under isolation" (Section 0.4 framing), rather **"Optuna basin reorganization at single-cohort labels"**. Narrow mechanism — likely small magnitude lift (Δ +0.10 to +0.25).
- **NEGATIVE tail at 25%**: reduce slightly to 20% — independent-pool finding REDUCES "pool was load-bearing" failure mode. NEGATIVE-CATASTROPHIC at 2% (no plausible mechanism given ρ ≈ 0).

**Adjusted priors**: PROMISING 20% / **INERT 60%** (INERT-no-effect 40% + INERT-preserved-asymmetric 20%) / NEGATIVE 20%.

## 2. F-AXIS-MECHANISM #2 trade count band (LOAD-BEARING; pre-registered)

Per /019 Critic Rec #2: |BTC-in-pool IS Sharpe| ≈ 0.12 is at noise-floor threshold; F-AXIS #2 trade count is LOAD-BEARING.

| Scope | BTC-in-pool baseline | /020 BTC-only predicted (mid ± 30%) | LM Master point estimate |
|---|---|---|---|
| **IS trades** | **113** | **[79, 147]** | **~105** |
| **OOS trades** | **35** | **[25, 46]** | **~34** |

These bands are tighter (~±15% from baseline) than QR's brief F8 [70, 150] IS / [25, 55] OOS — because pool independence implies Optuna lands near the pooled BTC-conditional basin → trade-count compression marginal.

**F-AXIS #2 BREACH-low (IS<70 or OOS<25)** would indicate genuine mechanism failure.

## 3. n_eff_per_cell prediction [7, 10]

BTC-only training row count ≈ 113-130 IS labels. NO gate. Per /019 Phase 7.4 §5 correction (n_eff predicted from training row count). Point estimate **9** matching /018 LINK-only (9). INFORMATIONAL.

## 4. PROMISING-MECHANICAL Jaccard test — PRE-REGISTERED HYPOTHESIS

| Scope | LM predicted Jaccard | Verdict implication |
|---|---|---|
| /020 BTC-only kept vs BTC-in-pool baseline roster | **0.10 to 0.25** (HIGHER than /018=0.04 and /019=0.04) | >0.50 → PROMISING-MECHANICAL; <0.20 → NEW signal source |

**Why higher than /018 + /019**: pool independence at ρ ≈ 0 means pooled Model A's BTC-conditional optimum is close to BTC-only's basin. /018 LINK-only used Model C; /019 ETH-only used NEW Model G + post-hoc gate (further roster divergence). /020 BTC-only is Model H using Model A's SAME atr_tp/atr_sl + apply_r1 config — only difference is universe scope. Trade roster overlap should be HIGHER.

**If observed Jaccard ≈ 0.04** (matching /018+/019): pool independence claim is at higher-than-monthly granularity — within-month label timing IS coupling BTC+ETH. Surprise outcome.

**If observed Jaccard > 0.50**: PROMISING-MECHANICAL. /027 bundle: BTC-only specialist becomes "strictly accretive component decision" NOT "new edge ingredient" — non-compoundable per `feedback_promising_mechanical_subtype.md`. MODAL prediction.

**If observed Jaccard ∈ [0.20, 0.50]**: mixed mechanism — partial basin reorganization + partial label-noise restructuring. Most likely outcome at single-seed=42.

## 5. Most important point

**Modal verdict is INERT-no-effect (|OOS Δ|<0.10); BTC-only specialization is the DIAGNOSTIC EXPLORATION confirming pool-independence rather than a likely edge candidate; bundle role at /027 is informational baseline + diversification ingredient NOT additive Sharpe contribution — distinct from /018 LINK (additive +0.80) and /019 ETH+gate (additive +0.50).**

## 6. /021+ verdict-conditional pre-staging

- **PROMISING (Δ ≥ +0.20)** → /021 = LTC-only specialization. Probability: 20%.
- **INERT-no-effect (|Δ|<0.10, modal)** → /021 = **LTC-only specialization**. Probability: 40%.
- **INERT-preserved-asymmetric (|Δ|∈[0.10, 0.20])** → /021 = LTC-only specialization. Probability: 20%.
- **NEGATIVE-basin (Δ ∈ [−0.55, −0.20])** → /021 = **2-symbol pooled cohort (BTC+ETH separated)**. Probability: 13%.
- **NEGATIVE-INTRINSIC (Δ ≤ −0.55)** → /021 = methodology pivot: `_write_feature_importance` add per /019 §6. Probability: 5%.
- **NEGATIVE-CATASTROPHIC** → /021 = closeout-reconciliation. Probability: 2%.

**Modal /021 = LTC-only specialization** (combined 80%).

## 7. Hyperparameter recommendations — KEEP everything frozen

- KEEP `n_trials=18` (TPE above ~10 saturation; 25 min predicted)
- KEEP `ENSEMBLE_SIZE=3` (single-axis = SYMBOL DIMENSION only)
- KEEP `V1_FEATURE_COLUMNS_PRUNED` (40 cols; no feature axis)
- KEEP `bounds_profile=v1_pruned` (baseline-matched Optuna bounds)
- KEEP `apply_r1=False` (Model A pool semantics; baseline did NOT use R1)
- KEEP `seeds=[42, 123, 456]` (3-seed EXPLORATION)
- **No new src/ changes beyond runner dispatch (Model H elif branch, ~30 lines)**

## 8. Cycle-3 specialist bundle update for /027

| Specialist | Verdict | Single-seed Δ | /027 multi-seed regression target | Bundle role |
|---|---|---|---|---|
| LINK-only /018 | PROMISING-INERT favorable | +0.16 | **+0.80** anchor | Edge ingredient (additive) |
| ETH-only + gate /019 | PROMISING | +0.65 | **+0.50** anchor | Edge ingredient (additive, low cross-corr) |
| **BTC-only /020** (modal INERT) | TBD | **predicted 0 to +0.10** | **predicted 0 to +0.10** | **Diversification baseline** |
| LTC-only /021 | PENDING | TBD | TBD | TBD |

**/027 logic flow**: if /020 is INERT-no-effect, the /027 bundle should include BTC IN POOL (via Model A) NOT BTC-only (via Model H). The /020 PURPOSE is to determine the right BTC representation.

## Saturation Risks to Flag

**Single-seed=42 basin lottery on UNIQUE-prior cohort (HIGH-RISK)**: BTC's structural prior (5/5 IS-NEG / 4/5 OOS-POS asymmetric rotation) means basin-lottery downside variance can be wider. /027 multi-seed dissolves.

**INERT-no-effect attribution at single-seed**: if /020 lands at OOS Sharpe Δ near zero, single-seed=42 could be (a) genuine INERT-no-effect or (b) basin-lottery cancellation of opposing drift forces. /027 multi-seed mean will reveal.

## What I Did NOT Recommend, and Why

- **Multi-seed for /020**: HIGH-RISK forward-mandate (3 consecutive ≥1σ HIGH-RISK negatives) not triggered.
- **Adding BTC-trend gate**: would confound cohort-isolation axis with gate-axis. Pure-isolation control is the right design.
- **Adding `_write_feature_importance` at /020**: deferred to /021+ per single-axis discipline.
- **Pre-emptive Optuna bounds tightening**: would suppress basin discovery.
- **Forcing apply_r1=True**: introducing R1 confounds isolation with risk-gate axis.

## Closing Note

**MEDIUM-HIGH confidence in modal verdict** (60% INERT combined). LOWER PROMISING confidence than /018 or /019 — there is no specialization knob in /020 (NO gate, NO new feature); pool independence at ρ ≈ 0 means the cohort isolation axis is the WEAKEST mechanism in the per-cohort series. /020 is the DIAGNOSTIC iteration.

**Three calls staked**:

1. **INERT-no-effect modal at 40%** — |OOS Sharpe Δ| < 0.10 most likely. Combined INERT at 60%.
2. **Jaccard prediction 0.10-0.25** — higher than /018+/019. If observed >0.50 → PROMISING-MECHANICAL.
3. **BTC-only's /027 role is DIVERSIFICATION not ADDITIVE EDGE**.

**Single most important point for QR**: F-AXIS-MECHANISM #2 trade-count band is the LOAD-BEARING diagnostic given small IS anchor (|Sharpe| ≈ 0.12 at noise floor). Pre-registered IS [79, 147] / OOS [25, 46] are tighter bands inside QR's [70, 150] / [25, 55]. If observed outside QR's brief bands → BLOCK-PENDING-FIX or NEGATIVE-COHORT-FAIL per QR's Section 8 row 8. The Jaccard test at Phase 7.4 is the second-most-load-bearing diagnostic.

**Critic Phase 7.5 priority items**:
1. **F-AXIS-MECHANISM #1** (`df['symbol'].unique() == ['BTCUSDT']`) binary pass.
2. **F-AXIS-MECHANISM #2 trade count** (LOAD-BEARING pre-registration).
3. **F-AXIS-MECHANISM #3 IS_H1 catastrophic preservation** — regime-binding test.
4. **Verdict-cell interpretation**: H_INTRINSIC PREDICTS IS-NEG / OOS-POS sign-mismatch — F7 traditional framing INVERTS. SAME-SIGN-POSITIVE → PROMISING-IS-DISSOLVED surprise outcome.
5. **Cross-iteration anchor stability**: BTC-in-pool baseline (−37.28% IS / +33.17% OOS) verified.

---

# LightGBM Master Post-Mortem — iter-v1/020 — Phase 7.4

## 1. Phase 4.5 vs Phase 7.4 prediction-reality

| Dimension | Phase 4.5 prior | Phase 7.4 observed | Verdict |
|---|---|---|---|
| Verdict modal | INERT-no-effect 40% / INERT-preserved 20% / PROMISING 20% / NEGATIVE-basin 13% / NEGATIVE-INTRINSIC 5% / **CATASTROPHIC 2%** | **NEGATIVE-CATASTROPHIC** (OOS Δ -0.86) | **2% TAIL MATERIALIZED** |
| F-AXIS #2 IS trades | 113 baseline → predicted [79, 147] (mid 105) | observed **122** | **LM band PASS** (inside QR [70, 150] + LM [79, 147]) |
| F-AXIS #2 OOS trades | 35 baseline → predicted [25, 46] (mid 34) | observed **53** | **LM BREACH-HIGH +7**, inside QR [25, 55] |
| n_eff_per_cell | [7, 10] point 9 | observed **9** | **PASS** |
| OOS Sharpe Δ band | predicted [0, +0.10] modal; tail [-0.55, -0.20] negative; CATASTROPHIC ≤ -0.55 at 2% | observed **-0.86** | **2% tail outcome; worst-case prior** |
| Jaccard IS+OOS combined | predicted [0.10, 0.25] (higher than /018+/019 ≈ 0.04) | observed **0.084** (IS 0.098 / OOS 0.048) | **REFUTED**; matches /018+/019 alternative branch |

**Critical miss**: Phase 4.5 §1 reasoning treated ρ ≈ -0.022 monthly aggregate as evidence of training-time pool independence. That inference is wrong. Two pre-registered surprise hypotheses confirmed simultaneously: (a) Jaccard ≈ 0.04 alternative branch (§4 of advisory), and (b) NEGATIVE-CATASTROPHIC 2% tail.

## 2. PROMISING-MECHANICAL Jaccard test (CRITICAL diagnostic)

Computed from `reports-v1/iteration_v1-020/{in,out_of}_sample/trades.csv` and `reports-v1/iteration_v1-baseline/{in,out_of}_sample/trades.csv` filtered `symbol==BTCUSDT`, keyed on `open_time`:

| Scope | /020 BTC-only | Baseline BTC-in-pool | Overlap | Union | **Jaccard** |
|---|---|---|---|---|---|
| IS | 122 trades | 113 trades | 21 | 214 | **0.0981** |
| OOS | 53 trades | 35 trades | 4 | 84 | **0.0476** |
| IS+OOS combined | 174 (closed) | 148 | 25 | 298 | **0.0839** |

Phase 4.5 prediction was [0.10, 0.25] expecting basin proximity. Observed 0.084 IS+OOS combined; OOS 0.048 is BIT-IDENTICAL to /018+/019 pattern (≈ 0.04). **The "alternative branch" the orchestrator flagged is the realized branch**: pool independence at monthly aggregate ρ ≈ -0.022 does NOT imply training-time independence. Within-month label-timing coupling carries BTC. Containment ratios (|∩|/|/020| OOS = 0.076) show /020 retained only 4 of baseline's 35 OOS BTC trades — 31 OOS trades the pooled Model A took are NOT taken under BTC-only retraining; the 49 net-new /020 OOS trades are basin-relocation taken from a different region of feature space. **Verdict: NEGATIVE with NEW signal source, NOT PROMISING-MECHANICAL.**

## 3. H_INTRINSIC REFUTATION mechanism analysis

Why H_POOL_ANCHOR ρ ≈ -0.022 misled at QR EDA yet BTC-only failed catastrophically at retraining:

- **Monthly aggregate Pearson is a low-resolution stat** — captures month-level co-drift of two PnL series. LightGBM training sees per-8h-candle labels at sub-month resolution.
- **Pool model training implicitly co-fits BTC trades alongside ETH/LINK/LTC/DOT labels** via at least three channels:
  - **Shared feature normalization at training time**: rolling 50-bar features compute the same way per-symbol, but Optuna trial selection on COMBINED IS labels picks splits favoring features whose value distribution is regular across all 5 cohorts. BTC-alone trains on BTC's narrower NATR distribution and Optuna lands in a different basin.
  - **Label-timing co-location**: training months containing BTC labels also contain ETH/LINK/LTC/DOT labels — Optuna's IS loss surface is integrated over all of them. Best-trial selection optimizes for JOINT loss; BTC-conditional optimum within that joint solution differs from BTC-alone optimum.
  - **Sample weighting (abs_pnl)**: weighted by |net_pnl_pct|, BTC's large-magnitude trades are downweighted RELATIVE to LINK/LTC vol-amplified trades — BTC-only retraining REMOVES this implicit downweighting.
- **Why /018 LINK + /019 ETH succeeded**: LINK has INDEPENDENT positive prior (pool not load-bearing). /019 ETH added an ORTHOGONAL mechanism (counter-trend kill gate) — Sharpe lift came from the gate, not cohort isolation per se.
- **BTC's IS-NEG/OOS-POS asymmetric rotation is POOL-CONFERRED at training time**, NOT intrinsic. Removing the pool removes the asymmetric rotation.

## 4. Predictive failure analysis

Phase 4.5 §1 modal INERT-no-effect prior chain was:

`monthly ρ ≈ 0 → pool independent → Optuna basin proximity → trade roster overlap → small Sharpe Δ`

Each arrow is wrong:
- **Arrow 1**: monthly ρ ≈ 0 does NOT imply training-time independence (§3 mechanisms).
- **Arrow 2**: even if pool were independent, single-cohort retraining at single-seed has wide basin-lottery variance for cohorts with asymmetric IS/OOS priors.
- **Arrow 3**: Jaccard 0.084 confirms basin moved substantially.
- **Arrow 4**: small Jaccard need not produce small Sharpe Δ if the relocated basin samples a structurally adverse trade subset.

**Calibration update for /021+ cohort isolation reasoning**: audit at TRAINING-TIME granularity, not monthly aggregate:
1. Cohort's relative pool weight (BTC labels at ~24% of pool month-rows).
2. Cohort's label-timing co-location with other cohorts (8h candles: same `open_time` across symbols → labels are joint).
3. Cohort's label-noise dependence on cross-symbol sample weighting (abs_pnl integrates magnitudes across cohorts).
4. **Trained-IS-NEG / trained-OOS-POS asymmetry is a POOL-DEPENDENT artifact**, NOT an intrinsic property. Future cohorts with asymmetric priors (LTC, DOT) should be expected to LOSE the pool-conferred direction at single-cohort isolation.

## 5. /021 verdict-conditional staging revision

Phase 4.5 §6 staged /021 = closeout-reconciliation at NEGATIVE-CATASTROPHIC prior 2%. Three options:

- **Option A**: /021 = 2-symbol pooled cohort {BTC, ETH} separated. Tests "pooling-helps-by-feature-stack at smaller scope". Risky.
- **Option B**: /021 = /027 CONFIRMATION moved up with 2-specialist bundle {/018 LINK-only + /019 ETH-only+gate} regressing against BTC-in-pool baseline (BTC IN POOL). Drops /022-/026 cohort coverage.
- **Option C**: /021 = methodology pivot — (i) add `_write_feature_importance` per /019 §6; (ii) add TRAINING-TIME pool-anchor diagnostic (per-fold Optuna best-trial parameter delta between BTC-in-pool and BTC-only single-seed=42); (iii) compute per-cohort Jaccard against pool baseline OFFLINE for LTC + DOT to predict /022-/026 outcomes BEFORE spending wall-clock on full EXPLORATIONs.

**LM Master recommendation: hybrid Option C + Option B**. /021 = methodology pivot (Option C i + ii) on a cheap budget. If /021 diagnostic shows LTC + DOT also lose pool-anchor at training time, proceed directly to /022 = /027 CONFIRMATION (Option B) with 2-specialist bundle, BTC IN POOL. Methodology investment up-front saves 4-5 wasted EXPLORATIONs.

Caveat: this revision goes against strict axis-rotation discipline. QR decides; this is LM Master's reading.

## 6. n_eff = 9 PASS (predicted [7, 10])

Confirms /019 §5 methodology update: n_eff predicted from training row count. /020 IS labels 122 → n_eff 9, matching /018 (9). Methodology calibration accurate. The only Phase 4.5 prediction that landed cleanly.

## 7. Cycle-3 cumulative tracker update

Pre-/020: 2 PROMISING (/018, /019) + 2 NEGATIVE clean (/016, /017).
Post-/020: 1 NEGATIVE-CATASTROPHIC added.

Cycle-3 record: **5/10 EXPLORATIONs complete; 2 PROMISING + 2 NEGATIVE + 1 NEGATIVE-CATASTROPHIC**.

HIGH-RISK consecutive catastrophic tracker: **1 CATASTROPHIC** (no 3-in-a-row threat).

5 more EXPLORATIONs needed before /027 CONFIRMATION at strict 10:1 cadence. Per /019 §6, `_write_feature_importance` still outstanding — /020 produced an `ic_matrix.csv` (good) but NO `feature_importance.csv` (gap persists).

## 8. Most important Phase 7.4 finding

**Pool-anchor refutation at monthly aggregate ρ ≈ -0.022 was a methodological false-negative — within-month training-time label dynamics carry BTC's OOS positive rotation, and BTC-only isolation catastrophically loses it (Jaccard 0.084 confirms training-time basin relocation). The corrected mental model: cohort isolation success requires either (a) independent positive prior at pool level (LINK case, /018), or (b) ORTHOGONAL mechanism added on top of isolation (ETH+counter-trend-gate case, /019) — NOT pool-anchor-refutation per se. /021 should pivot to methodology (add `_write_feature_importance`, add training-time pool-anchor diagnostic) before continuing /022-/026 cohort coverage, and /027 CONFIRMATION must regress the 2-specialist bundle against BTC-IN-POOL baseline (not BTC-only).**

## What This Iteration Confirms / Refutes About Prior LM Master Advisory

Phase 4.5 advisory had three staked calls: (1) INERT-no-effect modal at 40% — **REFUTED**, 2% tail materialized. (2) Jaccard prediction 0.10-0.25 higher than /018+/019 — **REFUTED**, observed 0.084 combined. (3) BTC-only's /027 role as DIVERSIFICATION not ADDITIVE EDGE — **VINDICATED in direction but understated magnitude**: it has NEGATIVE additive contribution and is unsuitable for the /027 bundle at all (BTC must enter via Model A POOL). Phase 4.5 §4 PRE-REGISTERED the alternative-branch interpretation; that pre-registration was the only thing that prevented the post-mortem from being purely confessional. Track record: 0/3 directional calls, 1/1 methodology call (n_eff = 9 PASS), 1/1 alternative-branch pre-registration utility.

## Closing Note for Critic (Phase 7.5)

Three specific things Critic should weight in the 8-check pass:

1. **Check 3 (PBO/DSR/Pareto)**: PSR_monthly_vs_0 = 0.301 is BELOW PROMISING-INERT floor 0.40 but ABOVE Catastrophic floor 0.10 — the catastrophic-band classification is driven by OOS Sharpe Δ of -0.86, not by PSR. Worth Check 3 attention whether the Δ-based catastrophic verdict is the right framing.
2. **Check 4 (IC)**: `ic_matrix.csv` for /020 is present (unlike /018 + /019). Critic should examine whether BTC-only IC structure differs meaningfully from pool-aggregate IC.
3. **Check 7 (verdict consistency)**: catastrophic classification rests on OOS Sharpe Δ vs **proxy** baseline (BTC-in-pool monthly Sharpe proxy ≈ +0.30). Critic should audit whether this proxy is the right anchor.
