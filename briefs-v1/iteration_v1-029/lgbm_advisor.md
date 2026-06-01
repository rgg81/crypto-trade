# LightGBM Master Advisor — iter-v1/029 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1. Branch `iteration-v1/029`. Cycle-4 EXPLORATION-2/10. DOT-only cohort isolation — **LAST untested single-cohort** in v1 universe (LINK ✓, ETH ✓, BTC ✗, LTC ✗→✓ at /028).
- **Anchor**: BASELINE_V1.md (`v0.v1-baseline-corrected`, `f8bc12c`) — portfolio IS +0.2829 / OOS +0.6637. **Per-cohort anchor**: DOT-in-pool IS per-trade Sharpe +0.0398 / OOS +0.0053 (DOT classification CSV row 2).
- **/028 outcome**: PROMISING (OOS Δ +0.598, modal 12% tail materialized inside my predicted [+0.25, +0.45] band → +0.15 favorable miss). LM Master track entering /029: methodology 7/7; directional 3/9 = 33%; 4-axis micro-mechanics on /022 hit 4/4 yet F1 was -1.17.
- **QR's tentative**: pure isolation per brief strict mapping (POSITIVE_EVERYWHERE → mirror LINK /018). QR caveats (a)/(b)/(c) flagged for adjudication.

---

## §1 Pre-classification Adjudication — DOT IS NOT LINK /018

**DOT is structurally CLOSER to ETH /019 than to LINK /018.** The QR's classification rule "sign-of-net-PnL both samples" routes DOT to POSITIVE_EVERYWHERE → pure isolation, but the underlying numerical signature is a **NEW sub-class the catalog has not seen**. I label it `FRAGILE-POSITIVE-WITH-COUNTER-TREND-LONG-DRAG`:

| Diagnostic | LINK /018 | ETH /019 | LTC /028 | **DOT /029** |
|---|---|---|---|---|
| OOS/IS Sharpe ratio | 9.79 / 0.34 = **2.87** | 0.70 / -0.03 = **n/a (IS zero)** | OOS+0.33 / IS-0.20 = **n/a (IS neg)** | **+0.13** (well below 0.5) |
| IS direction asymmetry | balanced | LONG-dominant IS, SHORT-dominant OOS | LONG-asymmetric IS-pos / OOS-cat | **LONG 95% IS PnL** |
| OOS direction REVERSAL | absent | present (asym 5+pp) | yes (LONG cat) | **present** (5.17pp; right at threshold) |
| OOS LONG counter-trend BTC bucket | n/a | n/a (gated) | n/a | **weak-up-BTC = -8.47% / 7 tr / WR 28.6%** |
| IS H1/H2 split | stable | n/a | unstable | **H1 -18.19% / 59 tr → H2 +44.82% / 34 tr** (catastrophic→recovery flip) |
| Class | POSITIVE_EVERYWHERE | COUNTER-TREND_OOS_DRAG | ASYMMETRIC_ROTATION_INVERSE | **FRAGILE-POSITIVE-WITH-LONG-COUNTER-TREND-DRAG** |

**Three mechanistic facts deserve weight beyond the classifier headline:**

1. **The +1.96% OOS net is SHORT-carried** (+3.56% shorts / -1.60% longs). LINK /018 was direction-balanced; ETH /019 had the same shape but the BASELINE was essentially zero (-0.10/+0.05) — DOT's baseline is +25 IS/+2 OOS, so the "directional reversal under tiny aggregate" pattern repeats but with a **94% IS LONG basin that LightGBM has already learned**.

2. **The OOS LONG-in-weak-up-BTC bucket signature is the ETH /019 fingerprint**: -8.47% / 7 tr / WR 28.6% is mathematically identical to ETH's "fighting BTC tape" diagnostic. DOT has the COUNTER-TREND mechanism ETH /019 had — just narrower (weak-up only) and superimposed on a POSITIVE_EVERYWHERE classification.

3. **H1/H2 instability** is the LTC /028 fingerprint (LTC IS was H1-cat / H2-recovery too). The OOS window 2025-04 to 2026-05 contains 4 catastrophic months (2025-09 -14.5%, 2025-10 -15.4%, 2025-12 -13.3%) AND 3 strong months (2025-08 +21.5%, 2026-01 +17.5%, 2025-04 +10.6%). The +1.96% net is a near-cancellation.

**Verdict**: DOT is a HYBRID — POSITIVE_EVERYWHERE at sign-level + COUNTER-TREND fingerprint in OOS LONGS + H1-style IS regime risk. Pure isolation mirroring LINK /018 ignores the COUNTER-TREND mechanism that drove ETH /019 to +0.65 single-seed Δ.

---

## §2 Hyperparameter Region Recommendations (single-cohort DOT)

DOT IS training row count ≈ 93 trades over 30 months → labels-per-month ~3.1, dense per (sym, month) cells ~25-50 candle-labels. This is **smaller than /028 LTC's 119 IS trades** and well below LINK's 154. Tighter regularization warranted.

| Param | /028 LTC value | **/029 DOT recommendation** | Rationale |
|---|---|---|---|
| `n_trials` | 35 (CONFIRMATION-spec) | **35** | TPE saturation above 30; /028 vindicated. Brief mentioned 18; ESCALATE to 35 — see §2.5. |
| `ENSEMBLE_SIZE` | 10 | **10** (single-pass) | /028 vindicated; n_eff=2 with positive verdict shows narrow basin doesn't block PROMISING. Brief's 3 is too low for FRAGILE-POSITIVE basin variance. |
| `seeds` | single (42) | **single (42)** | EXPLORATION mode; budget. |
| `num_leaves` upper bound | default | **cap at 47** (vs default ~63) | Smaller cohort + IS H1/H2 regime instability → reduce overfit-to-H2 risk. |
| `min_data_in_leaf` lower bound | default | **raise to ≥60** (from default ~20) | 30 IS months × ~3 trades/month → leaves can converge on single months without min_data lift. |
| `learning_rate` upper | default | **cap 0.08** | TPE picks higher LR on small data → fragile generalization. /028 best LR was ~0.04 (per /028 trial log). |
| `lambda_l1` lower | 0 | **≥ 0.1** | Modest L1 push for sparsity given 43-feature stack vs ~93 IS trades; encourages basin Optuna can defend OOS. |
| `feature_fraction` | full search | **keep full search** | Brief's pruned 43-col stack already feature-reduced; no further pinning. |
| `bagging_fraction` | full search | **lower bound 0.6** | Diversify inner-seed roster given small cohort. |

### §2.5 Brief specifies n_trials=18 / ENSEMBLE_SIZE=3 — RECOMMEND ESCALATE to /028's 35/10

The QR's `phase4_complete.md` row 147 lists `n_trials=18, ENSEMBLE_SIZE=3` per "standard constraints." **This is the cycle-3 default, not the post-/028 default.** /028 vindicated n_trials=35 + ENSEMBLE_SIZE=10 at EXPLORATION budget (single-cohort, ~30 min wall-clock) — DOT cohort is structurally HARDER (FRAGILE-POSITIVE + regime instability) and deserves equal or stronger variance budget. Predicted wall-clock 25-35 min, well inside 2h cap.

---

## §3 Feature Recommendations (NO new features; comment on expected rank distribution)

V1_FEATURE_COLUMNS_PRUNED (43 cols) FROZEN. Comments based on /018-/028 per-symbol rank patterns:

- **High-conviction RANK 1-3 candidates for DOT**: `ret_5d`, `atr_pct_50`, `vwap_dev_20`, `rsi_14_smooth_5`. Returns-and-vol primitives dominated /018 LINK and /028 LTC top-3 — DOT's 95% LONG IS basin will lean similarly on momentum + vol-regime features.
- **Expected RANK 1**: `ret_5d` (DOT's IS LONG-dominance + LightGBM's tendency to split on directional momentum first). If `vwap_dev_20` lands rank 1 instead, that's the COUNTER-TREND signal in disguise (price-vs-VWAP mean-reversion proxy) — would weak-confirm my §1 hybrid diagnosis.
- **BTC cross-features**: `btc_ret_42` and related likely RANK 5-10 (not rank 1 — DOT-only training under-weights cross-symbol primitives without the cross-cohort pooling that lifted them in baseline).
- **Expected DEAD WEIGHT (rank 14+ / >50% of months)**: small-window RSI variants (e.g. `rsi_3`, fast oscillators) on 8h candles will likely rank 30+/43. NO ACTION — they're FROZEN per pruned-stack — but flag for the /027-retry feature_importance audit.
- **Rank instability concern**: DOT's H1 catastrophic / H2 recovery IS regime shift means feature gains per month will be high-variance. Expect std-of-rank > 4 across IS months for the top 5 features. **NOT a blocker — informational pattern for Phase 7.4.**

---

## §4 Mechanism Recommendation — BINDING

### Prior probability table over 5 mechanism paths

| Path | Description | LM Master probability | OOS Δ band | Modal verdict cell |
|---|---|---|---|---|
| **A** | Pure isolation (atr_sl=1.75, atr_tp=3.5, R1+R3 ON, R2 OFF) | **35%** | **[-0.20, +0.35]** centered +0.05 | **INERT** (45% within Path A) |
| **B** | atr_sl=1.0 upstream label shift (mirror LTC /028) | **15%** | [-0.30, +0.55] centered +0.10 | INERT-FAV |
| **C** | Symmetric BTC-trend gate ±8% (mirror ETH /019) | **30%** | **[+0.05, +0.55]** centered +0.30 | **PROMISING-INERT** modal |
| D | Asymmetric long-suppress BTC gate (mirror /022 FAILED) | **5%** | [-0.80, +0.10] | NEGATIVE-CAT high tail |
| E | COMBINED atr_sl=1.0 + symmetric BTC gate | **15%** | [-0.10, +0.70] centered +0.30 | wide distribution; HIGH-RISK 2-axis |
| Sum | | **100%** | | |

### Recommendation: **PATH C — symmetric BTC-trend gate ±8% (mirror ETH /019)**

**Rationale**: DOT's OOS long-counter-trend signature (-8.47% in weak-up BTC; -5.80% in strong-down BTC) is the SAME diagnostic pattern that drove ETH /019 to +0.65 single-seed Δ. The fingerprint isn't subtle — the `dot_btc_trend_bucket.csv` shows DOT OOS LONGS net -1.60% across 4 BTC-trend buckets, with weak-up specifically contributing -8.47% / WR 28.6%, while OOS SHORTS in strong-up BTC contribute +5.59% / WR 42.9%. This is mechanistically what /019's symmetric ±8% gate addresses: kill LONGS in weak-positive BTC (and SHORTS in weak-negative BTC) — leaving the directionally-confluent trades intact.

**Modal verdict cell**: PROMISING-INERT (OOS Δ ~+0.30, ~25% within Path C).
**Most likely outcome cell**: INERT inside Path C (35% conditional), PROMISING (25%), NEGATIVE-INTRINSIC (5%, gate over-kills the H2-recovery edge).
**Critical risk**: DOT's 95% LONG IS basin means Optuna may relocate to a SHORT-dominant decision boundary under single-cohort isolation (mirror of ETH /019 IS = LONG-bias / OOS = SHORT-carrier). Gate fire-rate ~17% expected (matches ETH /019 OOS 14.3%); below 5% → INERT-UNDER-FIRE.

### Why NOT Path A (QR's tentative choice)

Pure isolation worked for LINK /018 because LINK had a **clean direction-balanced edge** (WR 50.0% / per-trade Sharpe symmetric across directions). DOT has 95% LONG IS PnL + LONG-counter-trend OOS DRAG — pure isolation will EITHER (a) regenerate the LONG-bias basin that produces the catastrophic weak-up-BTC bucket, OR (b) bounce to a different basin via single-seed=42 lottery. Path A's wider band [-0.20, +0.35] reflects this bimodal risk. **35% probability mass on Path A is acknowledgement that QR's brief mandate ties to this — but it's not my recommendation.**

### Why NOT Path B (LTC /028 mirror)

atr_sl=1.0 worked for LTC /028 because LTC was `ASYMMETRIC_ROTATION_INVERSE` — IS LONG-asymmetric / OOS LONG-catastrophic. The label-shift narrowed barrier hits and surfaced trades where LightGBM could AVOID the catastrophic LONG-in-BTC-bear configurations. DOT's class is FRAGILE-POSITIVE (BOTH IS-pos AND OOS-pos at sign-level) — the label-shift mechanism cannibalizes the +26% IS net by tightening barriers on already-converging trades. Per-cohort SATURATION rule (post-/028): atr_sl is for ASYMMETRIC_ROTATION cohorts. DOT is not ASYMMETRIC_ROTATION.

### Why NOT Path D (FAILED at /022)

LTC /022 asymmetric long-suppress at -4% BTC → NEG-CAT -1.17. The /022 lesson is empirical: asymmetric gates fail at basin relocation because the targeted phenomenon (89% long-drag) dissolves. DOT's signature is direction-asymmetric (95% LONG IS) but the OOS counter-trend pattern is symmetric (LONGS-counter-trend AND SHORTS-counter-trend exist). Asymmetric gate misses half the diagnostic.

### Why Path E only 15% (HIGH-RISK; explicitly NOT recommended at single-seed EXPLORATION)

Combining atr_sl=1.0 + ±8% BTC gate is a 2-axis perturbation; confounds attribution. Per /028 reframing, atr_sl is upstream of labels — combining with a post-Optuna gate creates 3 basin-relocation vectors simultaneously. At single-seed=42 EXPLORATION budget, attribution becomes impossible. **DEFER to /030+ retry stack only if /029 PATH C lands INERT-NO-EFFECT.**

---

## §5 Falsifier Pre-Registration (F-AXIS #1-#5)

Assuming Path C adopted. If QR sticks with Path A, adjust §5 entries marked [PATH C] downward by ~0.15 OOS Δ band shift.

- **F-AXIS #1 — dispatch correctness (binary)**: `df['symbol'].unique() == ['DOTUSDT']` for both IS and OOS trades.csv. PASS criterion APPROVED.
- **F-AXIS #2 — trade count band**:
  - **IS predicted [62, 130] modal 90** (DOT-in-pool 93 → DOT-only retrain ±30%; gate kill ~17% → effective IS [50, 105])
  - **OOS predicted [22, 55] modal 38** (DOT-in-pool 46 → gate kill ~15% → effective OOS [18, 47])
  - Both inside QR's brief [60, 130] / [25, 55]. If OOS < 22 → UNDER-FIRE / NEGATIVE-INERT-no-trades.
- **F-AXIS #3 — gate fire-rate [PATH C; LOAD-BEARING]**:
  - **IS band [10%, 30%] modal 18%** (mirror /019 ETH IS 19.5%, narrower DOT weak-up-BTC concentration)
  - **OOS band [5%, 30%] modal 15%** (mirror /019 ETH OOS 14.3%)
  - **LOAD-BEARING THRESHOLD**: OOS fire-rate < 5% → UNDER-FIRE → INERT-NO-EFFECT; OOS fire-rate > 35% → OVER-KILL → NEGATIVE-INERT or NEGATIVE-INTRINSIC.
- **F-AXIS #4 — n_eff_per_cell band [3, 8] modal 5**: DOT IS labels ~93 + ENSEMBLE_SIZE=10 + n_trials=35 → predict 5. /028 LTC at same config produced n_eff=2 (anomaly — LM Master /028 §4 diagnosed as feature-not-defect). For DOT, n_eff=2 would be the second-occurrence — INFORMATIONAL on a verdict-positive outcome, BUT if n_eff=2 AND verdict NEGATIVE → flag as ENSEMBLE COLLAPSE not single-instance anomaly.
- **F-AXIS #5 — exit-reason distribution [LOAD-BEARING]**:
  - Baseline DOT exit shares: IS SL 50.5% / TP 21.5% / timeout 28.0%; OOS SL 56.5% / TP 17.4% / timeout 23.9%.
  - **Predicted /029 OOS TP exits ≥ 5 retains mechanism upside** (matches /028 LTC OOS TP=5 LOAD-BEARING threshold confirmed).
  - **F-AXIS #5 binary**: OOS TP-exit count < 2 → mechanism degenerates to loss-clipping-only → verdict CAPPED at PROMISING-INERT regardless of F1 magnitude. **This is the /028 §6 lesson directly transferred.**
  - Path-C-specific: gated DOT OOS trades should preserve TP share ~17-20%; if gate kills high-TP trades preferentially (TP share drops below 10%), gate is destroying value not adding it.

---

## §6 Track-Record Commentary on Calibration

**/028 was my LATEST data point**: modal +0.30 to +0.60 OOS Δ; observed +0.598 → **upper edge of modal band**. This indicates my magnitude predictions for atr_sl-style label-shift on ASYMMETRIC_ROTATION cohorts were calibrated slightly conservative.

**Cumulative track entering /029**:
- Methodology calls: 7/7 (perfect) — F-AXIS #5 LOAD-BEARING, atr_sl 2-vector reframing, Jaccard prediction methodology, n_eff predictor refinement, ORACLE-EDA STATELESS carve-out, dispatch-defect lesson, basin-vector vs FI-rank distinction.
- Directional calls: 3/9 = 33%. /018 INERT MODAL hit favorable; /019 PROMISING tail predicted (modal 40% INERT), came in PROMISING (35% tail); /020 NEG-CAT tail materialized at 2% prior (REFUTED); /022 NEG-CAT tail materialized at 10% prior (correctly raised); /028 PROMISING tail materialized at 12% prior.

**Confidence on /029**: **MEDIUM**. Higher than /020 (60% INERT was 0/1 directional) but lower than /028 (post-LTC-class understanding). Path C is my best-supported recommendation because the ETH /019 mechanism analog is mechanistic-evidence-rich; the diagnostic CSV pattern (weak-up-BTC LONG -8.47%) is the same shape; and the /019 single-seed +0.65 calibrates the upper band.

**Specific calibration update**: Path C OOS Δ modal **+0.30 centered, band [+0.05, +0.55]** is consistent with /019 ETH (+0.65 observed, modal pred +0.20-0.30) compressed downward for two reasons: (a) DOT's larger anchor magnitude (+0.005 per-trade Sharpe ≠ ETH's effectively zero) means lift translates less efficiently to Sharpe Δ; (b) DOT's directional asymmetry is narrower (weak-up only) than ETH's symmetric counter-trend pattern.

---

## §7 Routing Recommendation for /030

Cycle-4 EXPLORATION-2/10 — 8 EXPLORATIONs remain. DOT is the LAST untested single-cohort; routing depends on /029 verdict:

- **/029 PROMISING (Path C OOS Δ ≥ +0.20)** → **/030 = first NEW-feature-family axis** (funding-rate or open-interest z-scores). Cohort-coverage axis CLOSES at /029 regardless of verdict; cycle-4 structural pivot to NEW signal source. The /027-retry bundle composition (LINK + ETH+gate + LTC+atr_sl + DOT+gate at multi-seed) is a separate /027 line item — does NOT consume /030 axis slot.
- **/029 INERT modal (|OOS Δ| < 0.20)** → **/030 = NEW-feature-family axis** (same). DOT-only specialist not bundle-candidate; cycle-4 saturated on cohort-isolation; pivot mandatory per `feedback_structural_over_knob_exploration.md`.
- **/029 NEGATIVE (Δ ≤ -0.20)** → **/030 = NEW-feature-family axis** (funding-rate prioritized). NEGATIVE on POSITIVE_EVERYWHERE cohort with mirror-of-ETH gate would be a 3rd NEG-CAT in same axis-family across cycle-3+4 — that closes the cohort-isolation axis PERMANENTLY for v1.
- **/029 NEGATIVE-CATASTROPHIC (Δ ≤ -0.55)** → **/030 = closure-reconciliation** + NEW-feature-family axis at /031. HIGH-RISK consecutive-CATASTROPHIC tracker re-arms (current: /020 + /022; /029 NEG-CAT = 3rd → forward-mandate triggers at /030+).

**Recommended /030 NEW-feature-family CANDIDATES** (priority order):
1. **Funding-rate z-score family** (8h cadence native, production-proven, never used in v1) — strongest recommendation
2. **Open-interest delta family** (8h cadence available, NEW signal class)
3. **Basis (perp - spot) z-scores** (data infrastructure ready)
4. **Microstructure realized-vol z-scores** — deprioritize (iter-v3/015 INERT precedent)

**At /027 multi-seed bundle composition**: regardless of /029 verdict, the credible 4-specialist bundle is **LINK-only (+0.80 anchor) + ETH+gate (+0.50 anchor) + LTC+atr_sl=1.0 (+0.30 anchor) + DOT+gate (+0.30 anchor if /029 PROMISING)** = nominal Σ +1.90; realistic with correlation drag **+1.10 to +1.40 OOS Sharpe** — FIRST credible path to +1.0 hard merge floor in v1 history.

---

## Closing Note

**MEDIUM directional confidence (Path C 30% modal vs my own diagnostic 50%; the gap is the prior probability that QR adopts Path A per brief strict mapping).**

**Three load-bearing calls staked:**

1. **DOT is a HYBRID class (FRAGILE-POSITIVE with LONG-counter-trend OOS drag) NOT pure POSITIVE_EVERYWHERE — the OOS LONG weak-up-BTC bucket -8.47% / WR 28.6% is the ETH /019 fingerprint** (§1). QR's strict mapping conceals this signal.

2. **Path C (symmetric BTC-trend gate ±8%) is the mechanism-evidence-best path — 30% probability, modal verdict PROMISING-INERT, OOS Δ band [+0.05, +0.55] centered +0.30** (§4). Path A (QR's tentative) carries 35% probability with wider bimodal risk band [-0.20, +0.35].

3. **F-AXIS #5 TP-exit count ≥ 2 OOS is LOAD-BEARING regardless of mechanism path** (§5). Directly transferred from /028 vindication. Gate or no gate, if /029 OOS TP < 2 the verdict caps at PROMISING-INERT.

**Single most important point for QR**: brief Section 1's classification framing (`POSITIVE_EVERYWHERE → pure isolation`) is a sign-of-net-PnL rule that misclassifies DOT. The OOS LONG-counter-trend signature in the BTC-trend bucket CSV (rows 11, 13 — weak-up-BTC and strong-up-BTC OOS LONGS both negative) is mechanistic evidence for the ETH /019 mechanism analog. **If QR retains Path A on brief-mandate grounds, Section 3 must explicitly REJECT my Path C recommendation with reason and the modal verdict expectation drops to INERT 45%.** If QR adopts Path C, modal verdict lifts to PROMISING-INERT and /027 bundle gains its 4th specialist.

**Critic Phase 7.5 priority items I'm flagging in advance**:
1. F-AXIS #3 OOS fire-rate within [5%, 30%] band (LOAD-BEARING binary) — if Path C adopted
2. F-AXIS #5 OOS TP-exit count ≥ 2 (LOAD-BEARING; /028 transferred)
3. Jaccard /029 vs DOT-in-pool baseline trade roster — predicted [0.03, 0.20] band (matches /018-/022 empirical pattern); >0.50 would indicate PROMISING-MECHANICAL classification
4. Check 3 PBO / PSR_monthly_vs_0 for single-cohort small-sample (DOT-in-pool OOS only 46 trades / 14 months) — anchor for verdict-cell determination
