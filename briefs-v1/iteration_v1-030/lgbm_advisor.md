# LightGBM Master Advisor — iter-v1/030 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1. Branch `iteration-v1/030`. Cycle-4 EXPLORATION-3/10. NEW axis family (**META-LABELING** — UNUSED in v1 history; sole prior precedent v3/017 NEGATIVE-clean over-filter).
- **Anchor**: BASELINE_V1.md `v0.v1-baseline-corrected` (`f8bc12c`) — IS Sharpe +0.2829 / OOS Sharpe +0.6637 / 621 IS / 189 OOS / per-model A=258/81, C=146/28, D=124/34, E=93/46.
- **/028 outcome**: PROMISING +0.598 OOS Δ (modal +0.30-0.60; upper edge land). **/029 TF** — wall-clock cap; LM-mandated CONFIRMATION-spec at EXPLORATION budget busted by DOT label rate 2× LTC's.
- **QR's axis evidence**: oracle top-3 worst-cell veto IS +77.87pp / OOS +58.55pp; H1/H2 worst-3 overlap = 1/3 (MODERATE); top-3 worst cells = 31.9% of IS trades; Model D LTC-long OOS catastrophe -45.44% concentrated in 19 trades.
- **My track entering /030**: methodology 7/7 (perfect); directional 3/9 = 33%. /029 directional not scored (TF — no observation).

---

## §1 Meta-Labeling Adjudication (BINDING ANALYSIS)

The oracle upper bound is **+58.55pp OOS** (top-3 perfect veto). The realistic-M2 lift is bounded by **M2 prediction accuracy on the M1-positive subset given 45 features × ~3-9 M1-positives/month/cohort**. Three structural facts compress the lift:

**Fact 1 — Sample sizes are tiny per M2 cohort.** Cumulative IS M1-positives over the 24-month training window: A ≈ 206, C ≈ 117, D ≈ 99, E ≈ 75. Per-month rolling, M2 sees ~3.1 (E) to ~8.6 (A) M1-positives. **n_eff << 50 per training window**, well below the threshold where LightGBM TPE Optuna can produce stable best-trial loss surfaces. v3/017's M2 best F1 was 0.4409 on similar-sized cohorts — barely above random discrimination.

**Fact 2 — v3/017 mechanism precedent: M2 filtered 42.7% of M1 candidates with NO per-trade economics lift.** That iteration's M2 was active (not INERT) but failed to improve quality of retained trades. The architecture WORKS at filtering; it FAILS at improving retained-trade economics on 13-feature input. v1/030 has 45 features (43+M1 conf+M1 dir) — more input dim, smaller signal-to-noise per sample.

**Fact 3 — H1/H2 worst-3 overlap = 1/3 (MODERATE), not stable.** Even a PERFECT classifier on IS-H1 worst cells generalizes only ~33% to IS-H2 worst cells. Out-of-distribution OOS shift adds another generalization hop. The realistic M2 captures at most ~30-50% of the oracle's perfect-veto lift, before further degradation from 45-feature noise.

**Spectrum localization**: Oracle lift OOS +58.55pp PnL → translate to Sharpe Δ ≈ +0.80 (using /028's PnL/Sharpe leverage ratio of +9.38 USD per +0.60 Sharpe). Realistic M2 captures 15-35% of that = **+0.12 to +0.28 OOS Sharpe Δ modal**, with FAT NEGATIVE tail (v3/017 was -0.48 IS / -2.15 OOS informational).

**The dominant verdict-determining variable is M2-fire-RATE × M2-fire-PRECISION.** v3/017 had 42.7% fire-rate × ~50% precision = wash. v1/030 needs ~25-35% fire-rate × ≥65% precision to net positive. n_trials_m2=10 + sample size ~75-200 + 45 features is structurally below where this precision is achievable. **Lift compression is mechanism-binding.**

---

## §2 Hyperparameter Region Recommendations for M2

M1 UNCHANGED (baseline). For M2 (LGBMClassifier binary, per `metalabeling.py:91-130`):

| Param | Current default in `_train_m2_binary` | **/030 recommendation** | Rationale |
|---|---|---|---|
| `n_estimators` | search [50, 500] | **search [50, 200]** | Cap upper bound; M2 training sets are 75-200 samples; >200 trees overfit |
| `max_depth` | search [3, 5] | **search [2, 4]** | TIGHTEN — small subset; depth=5 with 75 samples = 1 sample/leaf risk |
| `num_leaves` | search [15, 127] | **search [7, 31]** | TIGHTEN — 127 leaves with 75 samples is degenerate |
| `learning_rate` | search [0.01, 0.3] log | **search [0.02, 0.1] log** | Cap upper; smaller LR + more trees prevents single-shot memorization on tiny subset |
| `min_child_samples` | search [5, 50] | **search [8, 30]** | RAISE lower bound to 8 (current 5 too permissive for 75-sample data) |
| `reg_alpha` | search [1e-8, 10] log | **search [0.01, 5] log** | RAISE lower bound from 1e-8; L1 sparsity essential at 45 features × 100 samples |
| `reg_lambda` | search [1e-8, 10] log | **search [0.01, 5] log** | Same reasoning as L1 |
| `subsample` | search [0.5, 1.0] | **keep** | Acceptable |
| `colsample_bytree` | search [0.3, 1.0] | **search [0.4, 0.8]** | TIGHTEN ceiling — force feature subsampling to expose secondary features beyond M1 conf |
| `is_unbalance` | True | **`scale_pos_weight = n_neg/n_pos` explicit** | More deterministic than `is_unbalance=True` which uses internal heuristic; v3/017 lesson |

**Class weight reasoning**: per oracle table, ~55% of M1-positive bars in IS were eventual M1-losses (the loss-share cells dominate by trade count). Pos/neg ratio on M2 labels ≈ 45/55 — only mildly imbalanced. `is_unbalance=True` modifies loss in non-deterministic ways across CV folds. **Recommend explicit `scale_pos_weight = (n_neg/n_pos)` computed per M2 training cell.**

**Stratification**: `TimeSeriesSplit` in `_train_m2_binary` does NOT stratify by label. With small samples and ~45/55 split this matters: a TimeSeriesSplit's last fold can have 0 positive labels. **Recommend QR add fallback: if any fold has <3 positives, skip that fold (already partially present via `if len(train_idx) < 5 or len(val_idx) < 2`, but extend to label-presence check).**

**`n_trials_m2`**: Current default 10 (from M1's n_trials). QR proposes 10. **My recommendation: 18 — match M1's n_trials**. The argument for 10 was "M2 trains on sparse subset" but Optuna TPE needs ~15-20 trials for warmup to navigate the 9-dimensional hyperparameter space. v3/017 best F1=0.4409 at 10 trials is consistent with TPE not converging. Wall-clock impact: marginal (M2 trains on <200 samples, each fit takes <50ms; +8 trials × 4 models × 53 months × 50ms ≈ +85s, negligible).

---

## §3 4-Separate-M2 vs Unified-M2 Trade-Off (BINDING)

QR proposes 4-separate M2 (one per Model A/C/D/E).

**Per-model training sample sizes (cumulative 24-month rolling)**:
- A (BTC+ETH pooled): 258 IS trades × 24/30 ≈ **206 M1-pos** — adequate
- C (LINK): 146 × 24/30 ≈ **117 M1-pos** — marginal
- D (LTC): 124 × 24/30 ≈ **99 M1-pos** — marginal
- E (DOT): 93 × 24/30 ≈ **75 M1-pos** — **STRUCTURALLY TOO SMALL** for 45-feature LightGBM classifier

**Unified-M2 (single classifier on all M1-positive across A/C/D/E)**: ~497 IS samples over 24-month training window. That's 6.6× larger than Model E's per-M2 sample size — comfortably in LightGBM's adequate range.

**Specialization-vs-sample-size adjudication**:

The QR's per-model architecture aligns with M1's per-model dispatch, but **M2's job is "predict TP-vs-SL conditional on M1-features-plus-M1-confidence" — this is largely a SYMBOL-INVARIANT problem at the feature level** because V1_FEATURE_COLUMNS_PRUNED features are scale-normalized (returns, ratios, z-scores). The 8.6% pooled-symbol generalization gap that motivates separate M1 models does NOT necessarily replicate at the M2 layer — M2 is a second-order classifier on already-reduced signal.

**My recommendation: UNIFIED-M2 with `symbol` as a categorical input feature.** Specifically:
- Concatenate all M1-positive bars from A+C+D+E into one M2 training matrix
- Add `symbol` (one-hot or LightGBM categorical) + `model_name` (one-hot) as extra features
- M2 input dim becomes 43 + 1 (M1 conf) + 1 (M1 direction) + 5 (sym one-hot) + 4 (model one-hot) ≈ 54 cols
- M2 specializes via LightGBM's tree-structured splits on `symbol`/`model_name` while pooling samples

**If QR rejects unified (single-axis discipline argument)**: at minimum **drop M2 for Model E** (75 samples is below `n_train < 80` threshold where LightGBM produces meaningful classifiers). Trust M1 for E. Fire M2 for A/C/D only.

**This is a SOFT recommendation** — QR has authority. The 4-separate is the AFML Ch.3 textbook fit and the brief is single-axis tight. But sample-size risk is real and structurally binding for Model E.

---

## §4 Mechanism Recommendation (BINDING) + Prior Probability Table

**Recommendation**: **DO NOT cap M2 at 4 separate; pool to UNIFIED + categorical.** If QR retains 4-separate, **drop Model E's M2.**

### Verdict-class priors (Path = 4-separate-M2 with E included, current QR spec)

| Verdict cell | Probability | OOS Δ band | Rationale |
|---|---|---|---|
| **PROMISING-clean** (Δ ≥ +0.20) | **15%** | [+0.20, +0.55] modal +0.30 | Lift achievable if Model A M2 fires correctly (largest cohort); requires ≥65% precision @ 30%+ fire-rate |
| **PROMISING-INERT-FAV** (Δ +0.05 to +0.20) | **17%** | [+0.05, +0.20] modal +0.12 | Partial mechanism; M2 fires but caps below clean threshold |
| **INERT-NO-EFFECT** (M2 fire-rate <5% OR no headline change, Δ ∈ [-0.10, +0.10]) | **22%** | [-0.10, +0.10] modal +0.00 | Includes structural M2 degeneracy on Model E (75 samples → M2 returns None or trivial) |
| **NEGATIVE-OVER-FILTER** (Δ -0.40 to -0.10; v3/017 mirror) | **30%** | [-0.40, -0.10] modal -0.22 | Modal cell. v3/017 precedent (43% fire × no quality lift); v1 has more cohorts to break |
| **NEGATIVE-CATASTROPHIC** (Δ ≤ -0.40) | **16%** | [-0.80, -0.40] modal -0.55 | Model E M2 misfires (75-sample lottery) compounded with Model A M2 over-filtering high-quality OOS trades |
| **SUM** | **100%** | | |

**Modal verdict**: **NEGATIVE-OVER-FILTER 30%** with OOS Δ band centered **-0.22**. The combined PROMISING tail (PROMISING-clean + PROMISING-INERT-FAV = 32%) is materially smaller than the combined NEGATIVE tail (NEGATIVE-OVER + NEGATIVE-CAT = 46%).

**If QR adopts UNIFIED-M2 with categorical**: shift priors to: PROMISING-clean 22%, PROMISING-INERT-FAV 20%, INERT 25%, NEG-OVER 22%, NEG-CAT 11%. **Modal becomes INERT** with tied PROMISING-clean tail and reduced NEG-CAT. Net expected OOS Δ shifts from -0.10 (current spec) to **+0.05** (unified spec).

**Why I don't endorse the QR's STRONG potential framing**: the oracle upper bound is real (+58.55pp OOS PnL) but the realistic-M2 capture rate is mechanism-binding-low at sample sizes 75-200 with 45 features × n_trials_m2=10. **Oracle ≠ Realistic.** v3/017 had similar oracle headroom signal at its cohort and produced NEGATIVE-clean.

---

## §5 Falsifier Pre-Registration (F-AXIS #1-#5)

- **F-AXIS #1 — M2 dispatch binary [PASS criterion]**: At least one M2 model returns non-None for at least 1 (model, month) cell across all 4 models × 53 months. PASS if total M2-trained cells ≥ 80 of 212 expected (53 months × 4 models). If FAIL → TECHNICAL FAILURE not verdict. **Companion structural assert**: per `metalabeling.py:67`, `if len(m2_features) < 10` returns None — for Model E with 75 cumulative M1-pos over 24 months, expect ~10 M1-pos in some rolling windows; M2-skip threshold may fire frequently. Track frequency of M2-skip in run.log.

- **F-AXIS #2 — Post-M2 trade count band**:
  - **IS predicted [310, 500] modal 405** (baseline 621 × (1 - 0.35 average M2 fire-rate) = ~400; band reflects fire-rate variance 15%-50%)
  - **OOS predicted [95, 165] modal 130** (baseline 189 × similar fire-rate)
  - **CRITICAL THRESHOLD**: OOS trades < 90 → over-filter → caps verdict at NEGATIVE-OVER-FILTER regardless of headline Sharpe (v3/017's PBO=NaN signal from thin cells).

- **F-AXIS #3 — M2 calibration (LOAD-BEARING for verdict-positive)**: OOS true positive rate (M2 says PASS and trade is TP-exit) ≥ 50%. Baseline OOS WR = 40.2%. **PASS criterion: M2-pass OOS WR ≥ 48% (≥8pp lift over baseline 40.2%).** If M2-pass OOS WR < 42% → M2 not discriminating → NEGATIVE-OVER-FILTER classification.

- **F-AXIS #4 — n_eff for M2**: per (model, month) cell, n_eff_m2 ∈ [2, 6] modal 4. **Caveat**: v3/017 produced lowest n_eff in v3 catalog (=4) on M2. For v1/030 expect Model E M2 cells to dominate low-n_eff distribution (small training set). **Informational, not blocking.**

- **F-AXIS #5 — OOS TP-exit count [LOAD-BEARING]**: per /028 §6 transfer. Post-M2 OOS TP-exit count ≥ **15** (baseline OOS TP = 40; M2 should retain ≥40% of TP-class trades). **Below 15 → caps verdict at PROMISING-INERT regardless of F2.** Specifically — **Model A OOS TP count ≥ 6** (baseline A OOS TP ≈ 17); **Model D OOS TP count ≥ 3** (baseline D OOS TP ≈ 7). If Model D's M2 zeros OOS TP exits (catastrophic OOS LTC-long carries the model — M2 vetoing it could collapse upside), verdict caps regardless.

---

## §6 Track-Record Commentary

**Cumulative**: methodology **7/7 (perfect)**; directional **3/9 = 33%**. /029 unscored (TF).

**Calibration honest assessment for meta-labeling-specific call**:

I have **MEDIUM-LOW confidence** on /030 directional prediction. Three reasons:
1. The only meta-labeling precedent (v3/017) was NEGATIVE-clean — single data point, not a distribution.
2. v3/017 used a 13-feature M2 input; v1/030 uses 45-feature M2 input — more dim, smaller signal-to-noise, but also potentially more discriminative features. Direction of net effect: unknown.
3. The /029 TF means my last successful directional prediction was /028 (+0.598 inside band). I have no recent "miss" data point to recalibrate.

**Specifically for the prior table in §4**: my 30% NEG-OVER-FILTER modal is anchored on v3/017 mechanism precedent. If v1's larger 5-symbol universe + 45-feature stack produces qualitatively different M2 behavior than v3's 3-symbol + 13-feature, the priors are mis-shaped. **Honest uncertainty: NEG-OVER-FILTER could be 20-40%; PROMISING-clean could be 10-25%.**

---

## §7 Routing Recommendation for /031

Cycle-4 EXPLORATION-4/10 — 7 EXPLORATIONs remain after /030.

- **/030 PROMISING-clean or PROMISING-INERT-FAV (32%)** → **/031 = M2 threshold sweep** (test M2 threshold 0.45 / 0.55 / 0.60 single-axis follow-up — IF clean PROMISING fires, the threshold knob is the natural exploitation axis). Alternative: cross-feature M2 inputs (add R3 OOD score + BTC-trend bucket flag to M2 vector per Q1 — second-order specialization).
- **/030 INERT-NO-EFFECT (22%)** → **/031 = NEW feature family** (funding-rate z-scores top priority per /029 review §Path Forward). Meta-labeling axis CLOSED at v1; pivot to NEW signal source.
- **/030 NEGATIVE-OVER-FILTER (30% modal)** → **/031 = NEW feature family** (funding-rate). Meta-labeling axis CLOSED at v1 (mirror v3/017 closure). 3 cycles of structural attempts (cohort isolation /018-/028 + meta-labeling /030) saturated; the credible compounding path is multi-specialist bundle (/027 retry).
- **/030 NEGATIVE-CATASTROPHIC (16%)** → **/031 = closure-reconciliation + NEW feature family**. Meta-labeling axis PERMANENTLY CLOSED for v1. /027-retry bundle remains the credible path.

**Strong prior**: /031 = funding-rate-z-score family regardless of /030 verdict. Meta-labeling is a one-shot architectural axis; either it works (then /031 is exploitation) or it doesn't (then /031 is NEW signal source). NO third "modify meta-labeling parameters" iteration — the architectural commitment is single-shot.

---

## §8 Wall-Clock Risk Assessment

QR projects **59 min** total via 5-step scaling: M1 baseline ~50 min + M2 overhead ~9 min.

**Sanity check**:

**M1 cost**: Baseline 5-seed × 50 trials × 5 symbols × 53 months ≈ 66,250 trials at 7h total. /030 spec is 3-seed × 18 trials × 5 symbols × 53 months = 14,310 trials → linear ~1.5h. **QR's 50-min estimate is OPTIMISTIC** — ratio is 14310/66250 = 0.216, applied to 7h = 1.51h = 90 min. QR estimates 50 min using "/016 sample-weighting at same config = 50 min." That's a valid precedent IF /016 ran the full V1_FEATURE_COLUMNS_PRUNED at same months; I'll grant 50-80 min as the M1 band.

**M2 cost**: 4 models × 53 months × 10 trials × TimeSeriesSplit (3 folds) × ~100-200 samples × LightGBM fit at ~10ms/fit ≈ 4 × 53 × 10 × 3 × 0.01 = 64s × oversight factor 3 = ~3 min. **QR's 9 min is REASONABLE** (factoring Optuna overhead + Python dispatch).

**Total realistic band**: **65-95 min**, modal **80 min**. Well inside 2h cap.

**Wall-clock risk mitigations** (if estimate compresses tighter):
1. **Drop M2 for Model E** (75-sample structural minimum) — saves ~1 min M2 cost + reduces F-AXIS #1 dispatch risk (M2 may return None on E's small windows triggering many SKIP events).
2. **n_trials_m2 = 10 (not 18 as I recommended)** if wall-clock tight — accept TPE warmup degradation as cost.
3. **Pre-mortem checkpoint at month 10 (run.log monitor)**: if wall-clock projects > 100 min at month 10, abort and revise n_trials_m2 down or drop Model E M2.

**No CONFIRMATION-spec escalation** for /030 unlike /028/029 — meta-labeling is structurally different (M2 layer; not basin-relocation); single-seed EXPLORATION is the correct cadence for the NEW family axis.

---

## §9 Answer QR's 8 Adjudication Questions

**Q1 — M2 features 43 + m1_confidence + m1_direction = 45 (v1 spec); should we add R3 OOD score + BTC-trend bucket flag?**

**ANSWER: NO additional features for /030.** Single-axis discipline binds — M2 is the new architecture; adding cross-axis context features confounds attribution. If /030 fires PROMISING, **/031 single-axis follow-up could be "add OOD + BTC-bucket to M2 input"** — second-order specialization. For /030, stay at 45-dim AFML Ch.3 minimal + M1 direction (M1 direction is AFML-canonical M2 input per `metalabeling.py:269`).

**Q2 — 4-separate-M2 vs Unified-M2**

**ANSWER: UNIFIED-M2 with `symbol` + `model_name` categorical features is technically superior** (§3). However, **if QR retains 4-separate for single-axis discipline**, MANDATORILY drop Model E's M2 (75 cumulative samples is below LightGBM threshold). This is my strongest §3 recommendation — Model E M2 will produce noise classification at best, structural M2-skip at worst.

**Q3 — n_trials_m2 = 10 vs higher**

**ANSWER: 18 (match M1).** Optuna TPE needs ≥15 trials for warmup on M2's 9-dim search space. v3/017 best F1=0.4409 at n_trials_m2=10 is structurally consistent with TPE not converging. Wall-clock impact: ~+90 seconds total (negligible). If QR insists on 10, the modal NEGATIVE-OVER-FILTER cell weight shifts upward by ~3-5pp.

**Q4 — Secondary falsifier on H1/H2 stability with threshold?**

**ANSWER: YES — recommend F-AXIS #5b**: M2 OOS-fire-pattern overlap with M2 IS-fire-pattern measured at (symbol, model) cell level. Specifically: rank M2-fire-rate per (symbol, model) cell on IS H2 (last 12 months of IS) and OOS (16 months). Spearman rank correlation ≥ 0.35 = STABLE; < 0.20 = UNSTABLE → caps verdict at PROMISING-INERT regardless of headline. Threshold 0.35 chosen because oracle H1/H2 worst-3 overlap is 1/3 ≈ 0.33 — M2's stability floor should match the underlying mechanism's stability floor. Below 0.20 means M2 fitted to noise; above 0.35 means M2 fitted to mechanism. **This is informational addition, not blocking.**

**Q5 — F-AXIS pre-registration bands** — addressed §5. Synopsis:
- **F-AXIS #1**: ≥80 of 212 M2-trained cells = PASS
- **F-AXIS #2**: M2 OOS fire-rate band 15-50%; cap floor at 10%; cap ceiling at 60%
- **F-AXIS #3**: M2-pass OOS WR ≥ 48% (≥8pp lift over baseline 40.2%)
- **F-AXIS #4**: n_eff_m2 [2, 6] modal 4 informational
- **F-AXIS #5**: per-model differential — highest predicted lift is **Model D** (M2 vetoing LTC-long OOS catastrophe -45.44%) IF M2 generalizes; if M2 captures even 50% of LTC-long carnage, expect Model D Sharpe Δ +0.50-0.80. **Critical: Model D OOS TP count ≥ 3.**

**Q6 — Verdict-class priors** — addressed §4. Summary: **15/17/22/30/16** (PROMISING-clean / PROMISING-INERT-FAV / INERT / NEG-OVER / NEG-CAT). Modal: NEGATIVE-OVER-FILTER. Combined NEG tail 46% > combined PROMISING tail 32%.

**Q7 — Bundle-composition implications**

**ANSWER**: If /030 PROMISING-clean fires, meta-labeling is **NON-COMPOUNDABLE as bundled CONFIRMATION edge ingredient** in /027-retry. Per v3 PROMISING-MECHANICAL classification logic, M2 is an ORTHOGONAL filtering layer not a SIGNAL source — it doesn't compound with LINK +0.80 + ETH+gate +0.50 + LTC+atr_sl=1.0 the way those compound. M2 applied to the 3-specialist bundle would either (a) over-filter the LINK/ETH/LTC PROMISING signals reducing their lift OR (b) fire INERT (low fire-rate on already-selected specialists). **Bundle path**: meta-labeling is a SEPARATE CONFIRMATION axis at /027-retry, NOT bundled with the 3 specialists. If /030 PROMISING, the credible path is **2 separate CONFIRMATIONs**: one for 3-specialist bundle, one for meta-labeling as standalone v1 architecture upgrade. v3/PROMISING-MECHANICAL precedent (cycle-6 cross-layer orthogonality) supports this.

**Q8 — Critic Phase 6.0 implementation risk (defensive checks)**

**ANSWER — Mandate at runner level**:
1. **M2 dispatch trace assert**: per (model, month, symbol) cell, log to run.log: `M2_TRAINED=True/False` + sample count. If <50% of cells have `M2_TRAINED=True`, FLAG to QR Phase 7 (informational, not BLOCK).
2. **M2-skip rate cap**: if total M2-skip count > 35% of expected dispatch cells, Phase 6.0 should print a WARNING (informational). This is a v3/017-precedent-style check — v3/017 PBO=NaN traces to thin walk-forward cells where M2 had no labels.
3. **F-AXIS #1 assert**: at end of backtest, assert `(M2 fired at least once in OOS) AND (post-M2 OOS trade count >= 50)`. If FAIL, exit with TECHNICAL FAILURE code (not silent degraded run). This prevents /027-style ambiguous-result silent-pass.
4. **Per-model M2 active flag in trades.csv**: add column `m2_passed` (1 = M2 passed, NaN = M2 inactive). Critic Check 1 can audit M2 activity rate post-hoc.
5. **NO HARD-ASSERT that would crash on legitimate M2-skip** (Critic /027 lesson): the assertions above are post-hoc reporting, not runtime gating. Runtime M2-skip is a legitimate per-cell condition (e.g., Model E has thin cohort).
6. **Sample-size logging**: in `_train_m2_binary`, expand print at line 75 to include `(model_name, month_str)` so run.log post-hoc parsing identifies which cells fired M2 vs skipped. Saves Critic time.

---

## Closing Note

**MEDIUM-LOW directional confidence on /030.** The single v3/017 precedent is NEGATIVE-clean over-filter. v1's larger universe + 45-feature M2 input has potential to lift PROMISING tail vs v3, but sample-size structural constraints (especially Model E at 75 cumulative M1-positives) bind the lift below oracle's +58.55pp upper bound to a realistic +0.12 to +0.28 OOS Sharpe Δ modal.

**Three load-bearing calls staked**:

1. **Model E's M2 will not produce meaningful signal at 75 cumulative samples × 45 features × n_trials=10.** Strongly recommend dropping E's M2 OR pooling to UNIFIED-M2 (§3). If QR retains 4-separate with E included, my NEGATIVE-OVER tail weight raises 5pp (to 35%).

2. **n_trials_m2 = 18 NOT 10.** v3/017 best F1=0.4409 at 10 trials is the TPE-not-converging signature. Wall-clock cost negligible (+90 sec). If QR keeps 10, accept ~3-5pp shift toward NEGATIVE tail.

3. **F-AXIS #5 (Model D OOS TP-exit count ≥ 3) is LOAD-BEARING.** Per /028 §6 transfer. Model D is the highest-leverage M2 application (LTC-long OOS -45.44% catastrophe). If M2 zeros OOS Model D TP exits while filtering the catastrophe trades, the upside vanishes alongside the loss-clip — verdict caps at PROMISING-INERT regardless of D's headline Sharpe lift.

**Single most important point for QR**: the oracle headroom (+58.55pp OOS lift) is REAL but mechanism-binding-compressed to ~+0.12-0.28 realistic OOS Sharpe Δ at the proposed configuration. **The QR's brief Section 4 (Expected OOS Impact) should NOT cite the oracle number as the expected outcome — it should cite realistic-M2 modal +0.12-0.28 with explicit NEGATIVE-OVER-FILTER 30% modal tail. The brief MUST acknowledge v3/017's mirror outcome as Section-1 prior.**

**Critic Phase 7.5 priority items I'm flagging in advance**:
1. **F-AXIS #3 OOS M2-pass WR ≥ 48%** (LOAD-BEARING binary) — discriminating from over-filter
2. **F-AXIS #5 Model D OOS TP-exit count ≥ 3** (LOAD-BEARING; LTC-long catastrophe pre-vet)
3. **F-AXIS #2 OOS trade count ≥ 90** — below = NEGATIVE-OVER-FILTER cap
4. **Per-model M2-fire-rate audit** (run.log parse) — Model E expected to dominate M2-skip events; verify ≥50% of E cells produce M2_TRAINED=True
5. **v3/017 mirror condition**: if v1/030 OOS M2 veto rate 35-50% AND retained-trade per-trade Sharpe ≤ baseline → identical v3/017 NEGATIVE-clean fingerprint → unambiguous classification
