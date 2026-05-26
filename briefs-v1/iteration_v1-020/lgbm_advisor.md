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
