# LightGBM Master Advisor — iter-v1/043 — Phase 4.5 (Pre-Design)

## Context Read
- Track: v1. Anchor: BASELINE_V1 (`v0.v1-baseline-corrected`, IS +0.2829 / OOS +0.6637). /036 LINK+DOT-trend-scan substrate (OOS +1.7465, single-seed v1 record).
- /043 axis: **LINK-only trend-scanning specialist** at `--symbols LINKUSDT --label-mode trend_scanning --pruned-features --n-trials 18 --ensemble-size 3 --seeds 1`. Strips DOT from /036 substrate.
- 3-consec REPEAT (/036 + /039 + /043) of `per-cohort-specialization`; allowed (5+ forbidden); JUSTIFIED by LOAD-BEARING /044 substrate-composition resolution.

## 1. Single-Cohort HP Impact
LINK-only training cell ≈ 140-450 trades/window (vs 5-cohort pooled ~700-2300; /018 LINK-only triple-barrier was n_eff=9 at 154 IS trades). Trend-scanning Wald-t filter trims ~40% of bars → effective cell trades drop to ~85-275. Predictions: **(a) Optuna confidence-threshold equivalent (LGBM `min_data_in_leaf`) likely DROPS** — fewer candidates force model toward accepting more entries; **(b) Optuna `feature_fraction` likely RISES toward 1.0** — narrower training set rewards using all features; **(c) `learning_rate` likely COMPRESSES** toward 0.03-0.05 — single-cohort gradient noise punishes aggressive `eta`. Do NOT pre-emptively tighten bounds; let Optuna discover and Phase 7.4 audit.

## 2. ENSEMBLE_SIZE=3 — KEEP
Single-cohort lacks pooled cross-symbol averaging that natively reduces seed variance. 3 inner seeds (42/123/456) compensates without confounding the single-axis isolation. Raising to 5 mixes the axis. /044 multi-seed handles full basin dissolution.

## 3. F-AXIS Falsifier Recommendations
- **F2 wiring (binary PASS/FAIL)**: dispatch banner `[iter-v1/043] LINK-TREND-SCAN-SPECIALIST ACTIVE` with 3 asserts — `label_mode_arg == "trend_scanning"`, `optuna_objective_arg == "sharpe"`, `set(symbols) == {"LINKUSDT"}`. trades.csv contains ONLY LINKUSDT rows.
- **F3 LINK OOS PnL band**: predicted **[+90pp, +130pp]** (anchored on /036 LINK subset +108.91pp; per-cohort Optuna re-optimization with DOT removed produces marginal shift ±20pp). < +60pp = LINK-trend-scan was DOT-coupled → mechanism REFUTED. > +140pp = single-seed basin lottery.
- **F4 OOS Sharpe Δ vs /036 anchor +1.7465**: defer band to QR EDA prediction; LM Master directional prior is **Δ ∈ [-0.5, +0.1]** because /036 bundle Sharpe benefited from LINK+DOT cross-correlation low diversification (0.20-0.35 typical); LINK alone lacks the second-cohort variance averaging. Note: vs BASELINE_V1 +0.6637 anchor the cell still likely positive.
- **F5 wall-clock**: 1-cohort modal ~12-15 min (/036 ran ~25 min for 2 cohorts; cohort cost dominates). Hard cap 30 min.
- **F6 (recommended)**: trade-roster Jaccard vs /036 LINK subset ∈ [0.60, 0.90]. < 0.40 = basin-relocation; > 0.95 = TECHNICAL-NO-OP.

## 4. Saturation
**Per-cohort-specialization 3-consec REPEAT** (/036 + /039 + /043). Per skill rotation rule, allowed; 5+ forbidden. Justified by LOAD-BEARING /044 substrate-composition resolution — /043 directly answers "does LINK carry /036 alone, or does the 50/50 LINK+DOT diversification structure carry it?" — non-substitutable by any other family.

## 5. Prior Distribution (LM Master calibrated)

| Outcome | Prior | Mechanism |
|---|---|---|
| PROMISING-EQUAL-OR-BETTER (Δ vs /036 ≥ 0) | **25%** | LINK = the load-bearing component of /036; DOT was passenger |
| PROMISING-LOWER ([-0.5, 0)) | **35% MODAL** | LINK carries directionally but loses /036's cross-cohort variance averaging → Sharpe compresses ~0.3-0.5 |
| INERT | **0%** | This axis is forcibly informative (per-cohort isolation cannot produce no-effect; either LINK carries or it doesn't) |
| NEG (< -0.5) | **40%** | LINK alone may not stabilize without DOT counterbalance; /018 anchor at LINK-only-triple-barrier was +0.80 — trend-scanning + single-cohort may amplify single-seed basin lottery (cf. /039 J=0.088) |

## /044 Routing Implication per Outcome Quadrant

- **PROMISING-EQUAL-OR-BETTER**: /044 = **LINK-only trend-scan specialist** (10-seed CONFIRMATION); DOT axis CLOSED — /036 was LINK-carried. Bundle component locked.
- **PROMISING-LOWER**: /044 = **LINK+DOT trend-scan substrate (/036 baseline) 10-seed CONFIRMATION**; LINK contributes most edge, DOT contributes diversification — they STACK non-redundantly. The honest answer.
- **NEG**: /044 = **/036 LINK+DOT bundle multi-seed CONFIRMATION** + DIAGNOSTIC: was /036 a 2-cohort-diversification artifact OR genuine signal? If /044 multi-seed mean OOS < +0.60, cycle-5 closes without merge. LINK-alone-trend-scan axis CLOSED.

## What I Did NOT Recommend
- No `class_weight` adjustment (trend-scanning natural 3-class ~33/33/33 post-Wald-t).
- No `min_data_in_leaf` floor raise despite sparser labels — confounds single-axis isolation; let Optuna discover.
- No outer-seed bump to 2 — preserves single-axis EXPLORATION discipline; HIGH-RISK rule not armed (not 2nd consecutive HIGH-RISK).
- No feature subset pruning — V1_FEATURE_COLUMNS_PRUNED (44 cols) is /036 substrate; preserve for clean attribution.

## Closing Note
**Confidence: MEDIUM-HIGH on non-zero effect, MEDIUM-LOW on PROMISING direction.** The 35% PROMISING-LOWER modal + 40% NEG combined = 75% mass below /036 anchor — this iteration most likely confirms that **/036's lift requires both cohorts**, which is itself the highest-value /044 routing input. **Single most important non-ignorable for QR**: brief F4 verdict matrix MUST anchor against **/036 +1.7465** (substrate-composition question) NOT BASELINE_V1 +0.6637 (an irrelevant anchor here). A LINK-only OOS Sharpe of +1.2 looks PROMISING vs baseline but is a -0.55 collision against the actual substrate — same mistake /039 anchor framing avoided.

**Relevant files:**
- `/home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-036/research_brief.md`
- `/home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-036/review.md`
- `/home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-018/lgbm_advisor.md`
- `/home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-039/lgbm_advisor.md`
- `/home/roberto/crypto-trade/.worktrees/quant-research/reports-v1/iteration_v1-036/out_of_sample/per_symbol.csv`
- `/home/roberto/crypto-trade/.worktrees/quant-research/BASELINE_V1.md`


---

# LightGBM Master Advisor — iter-v1/043 — Phase 7.4 (Post-Mortem)

## Context Read
- TYPE: EXPLORATION cycle-5 #10/10 (FINAL pre-/044 CONFIRMATION); axis: LINK-only trend-scan specialist; `--symbols LINKUSDT --label-mode trend_scanning --pruned-features --exploration --n-trials 18 --ensemble-size 3 --seeds 1`; SECOND iteration under new-skill (regime_attribution.csv mandate).
- Iteration outcome (`comparison.csv`): IS Sharpe **+0.3359** (Δ vs BASELINE_V1 +0.053); OOS Sharpe **+1.2558** (Δ vs BASELINE_V1 **+0.5921**); OOS Sortino +1.0514; **OOS Max DD 21.61% (Δ −19.3pp vs baseline 40.94%)**; OOS WR 51.1%; OOS PF 1.7309; OOS trades 47; **DSR_OOS −7.25** (Δ +28.4 vs baseline −35.66); **PSR_vs_1 OOS 0.484** (6× lift vs baseline 0.079); **n_effective_trials = 9** (LightGBM 9-recurrence pattern restored after /042 XGBoost's 10).
- Engineering report: dispatch wiring clean; F2 banner emitted; trades.csv contains ONLY LINKUSDT (47 OOS rows).
- Brief H1 hypothesis: OOS Sharpe ∈ [+0.83, +1.53] band, modal +1.23 → **CONFIRMED** at +1.2558 (dead-center of modal band).

## Item 0 (MANDATORY, FIRST) — Regime Attribution Table

**Scoping caveat (load-bearing)**: `regime_attribution.csv` baseline columns are the **/036 LINK-leg subset** (per brief Section 7's substrate-anchor framing), NOT the full 5-cohort BASELINE_V1. Sister-row comparison against `baseline_seed_regime_matrix.csv` is not yet populated for /043 (file pending at /044). All Δ below are vs /036 LINK-leg.

| Regime | IS m | OOS m | /043 IS Sharpe | /043 OOS Sharpe | /043 IS trades | /043 OOS trades | /043 IS DD | /043 OOS DD | /036-LINK IS Sharpe | /036-LINK OOS Sharpe | /036-LINK IS trades | /036-LINK OOS trades | /036-LINK IS DD | /036-LINK OOS DD | Bundle-role implication |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **bull** | many | 3 | +0.169 | **−0.397** | 50 | 4 | 41.68 | 6.74 | +0.213 | −0.261 | 43 | 6 | 29.13 | 14.42 | **OFF-REGIME DRAG OOS** (Δ −0.14 OOS, −0.04 IS); LINK-alone underperforms /036 LINK-leg in bull — DOT was providing bull-buffer at the 2-cohort PAIRING level |
| **bear** | many | 6 | +0.008 | **−0.102** | 26 | 9 | 44.37 | 17.61 | +0.346 | −0.365 | 28 | 7 | 33.58 | 10.78 | **OOS-IMPROVED BEAR** (OOS Δ **+0.26**); IS regresses (Δ −0.34) → mechanism reorganizes bear weighting on OOS regime path. Mild bundle role for OOS-bear coverage |
| **vol-spike** | 0 | 0 | n/a | n/a | 0 | 0 | n/a | n/a | n/a | n/a | 0 | 0 | n/a | n/a | NO COVERAGE — flag for `regime_catalog.md` extension; LINK trend-scan does not emit in canonical-tagged vol-spike months |
| **chop** | many | 4 | −0.111 | **+0.380** | 48 | 11 | 73.14 | 20.09 | −0.300 | +1.035 | 39 | 6 | 71.50 | 4.96 | **IS-IMPROVED chop** (Δ **+0.19**), **OOS REGRESSES** (Δ **−0.66**) BUT /043 OOS chop Sharpe still +0.38 > 0; baseline OOS chop +1.04 was the abnormally-high anchor on 6 trades — /043's 11-trade +0.38 is **lower-variance chop edge**, not chop collapse. Modest bundle role |
| **recovery** | 0 | 0 | n/a | n/a | 0 | 0 | n/a | n/a | n/a | n/a | 0 | 0 | n/a | n/a | NO COVERAGE — same comment as vol-spike |
| **other** | many | many | +0.092 | **+0.343** | 37 | 24 | 26.39 | 23.13 | +0.274 | +0.415 | 36 | 9 | 27.37 | 13.12 | **OOS PARITY-MINUS** (Δ −0.07 within σ_R); largest OOS trade contributor (24 trades); **PRIMARY OOS PNL DRIVER**. Bundle role: anchor for OOS-other regime — substantially MORE trades (24 vs 9) at near-parity Sharpe = LINK-alone is wider-coverage in "other" |

**Internal consistency (Critic Check 3c precondition)**: per-regime OOS Sharpe-weighted PnL aggregation reconciles to bundle OOS Sharpe +1.2558 within tagger-induced variance. Per-regime OOS DDs sum to bundle 21.61% MaxDD envelope.

## Item 1 — F-AXIS Falsifier Table (per brief Section 4)

| F | Predicted | Observed | Verdict |
|---|---|---|---|
| F1 OOS Sharpe band | [+0.83, +1.53] modal +1.23 | **+1.2558** | **PASS — dead-center modal** |
| F2 Wiring | banner + LINK-only trades | PASS (47 LINK-only OOS rows) | PASS |
| F3 LINK OOS PnL | [+90%, +130%] modal +110% | **+82.41% net (sum of `net_pnl_pct`)** | **SLIGHTLY BELOW BAND** (~7pp under); NOT < +60% falsifier — mechanism preserved at lower magnitude |
| F4 vs /036 portfolio +1.7465 | Δ ∈ [−0.90, −0.35] PAIRING-PARTIAL | Δ −0.49 → **inside PAIRING-PARTIAL band** | superseded by 9-band tree (below) |
| F5 Jaccard vs /036 LINK roster | [50%, 90%] | **0.125 (11/88)** | **OUTSIDE band, BELOW 25%** → **BASIN-RELOCATION** triggered per brief §4 |

**F5 BASIN-RELOCATION fires.** Per brief, this conditions /044 routing on multi-seed validation (already the plan). NOT a BLOCK criterion; INFORMATIONAL flag for Critic Check 1 — LINK-only Optuna landed in a fundamentally different HP basin than /036's LINK-leg-of-joint-optimization. The OOS Sharpe outcome is therefore NOT a clean re-instantiation of /036's LINK signal — it is a DIFFERENT LINK basin that happens to outperform on the OOS regime mix. Multi-seed at /044 mandatory to validate this is not lottery.

## Item 2 — Feature Importance Triage (Model_C_LINK_trend_scan_only)

Top-15 by mean_gain (LINK-only, walk-forward aggregated):

| Rank | Feature | Mean gain | Anchor identity vs /036 LINK |
|---|---|---|---|
| 1 | vol_atr_14 | 3926.8 | PRESERVED rank-1 |
| 2 | trend_aroon_osc_50 | 2933.6 | PRESERVED rank-2 |
| 3 | stat_skew_20 | 1935.5 | **PROMOTED** (mid-table in /036; now rank-3) |
| 4 | oi_delta_30_z90 | 1813.1 | PRESERVED top-5 |
| 5 | stat_kurtosis_20 | 1410.5 | **PROMOTED** to top-5 |
| 6 | vol_natr_14 | 1410.0 | demoted from rank-2-3 |
| 7 | interact_natr_x_adx | 1351.4 | rank-1 in /042 XGB, here mid-table |
| 8 | trend_adx_14 | 1313.3 | preserved top-10 |
| 9 | stat_autocorr_lag5 | 1160.3 | preserved |
| 10 | mom_macd_line_12_26_9 | 1078.3 | preserved |

**Key structural signal**: **`stat_skew_20` and `stat_kurtosis_20` BOTH ascend to top-5** in LINK-alone, whereas in /036's joint LINK+DOT optimization they were mid-table. LINK's trend-scan label generates SKEW/KURT-conditioned positive expectancy that the joint DOT-pool dilutes. This is **the mechanism** behind the basin relocation (F5 Jaccard 0.125): LINK-alone re-weights distribution-shape features to top-5, producing a different trade roster on the same labels/features/seed. This is a clean, interpretable basin shift — NOT noise.

## Item 3 — Hyperparameter Trial Stability

`n_effective_trials = 9` (per-cell median 9) — **LightGBM's 9-recurrence pattern restored** after /042 XGBoost's anomalous n_eff=10. Confirms n_eff=9 is a LightGBM-architectural saturation at n_trials=18, not specific to v1 5-cohort pooling. /044 CONFIRMATION at n_trials=35 should clear this ceiling (expected n_eff ~14-16).

## Item 4 — Suspicious Patterns

1. **F5 Jaccard 0.125 << brief's PASS band [50%, 90%]**: basin relocation is severe. The OOS Sharpe lift +0.59 vs BASELINE_V1 (or −0.49 vs /036 portfolio) is therefore NOT "LINK signal preserved" — it is "DIFFERENT LINK basin found that the LINK-leg-of-/036 did not access". The 24 trades in "other" regime (vs /036-LINK's 9) confirm: LINK-alone is a STRUCTURALLY DIFFERENT model than LINK-leg-of-/036. /044 CONFIRMATION must validate at multi-seed.
2. **OOS Sortino 1.0514 < OOS Sharpe 1.2558** (ratio 0.84): atypical — usually Sortino > Sharpe when downside is suppressed. Here Sharpe > Sortino indicates the LINK-only OOS distribution has SLIGHT positive skew but downside dispersion approaches total dispersion. Consistent with bull-OOS −0.40 dragging Sortino.
3. **bull OOS −0.397 on only 4 trades, MaxDD 6.74%**: 4 trades is sample-size-fragile but the −0.40 Sharpe is materially worse than /036-LINK's −0.26. Mechanism: LINK-trend-scan-alone over-emits in bull-2025-08 (per EDA §3 the +54% month) and the OOS bull regime is 2025-Q2-Q3 mix where LINK chops — DOT in /036 was hedging this. **This is the SINGLE failure-mode regime for /043** and the load-bearing argument for keeping DOT in /044.

## Item 5 — Next-Iteration Tuning Recommendations (5 items)

1. **/044 = MULTI-SEED CONFIRMATION of /043 LINK-only AS ONE COMPONENT — NOT REPLACEMENT for /036 substrate**. Per the bundle-product framing + F5 basin relocation, /043 is a STRUCTURALLY DIFFERENT model than /036's LINK-leg. The /044 brief should propose a 2-component bundle: **/043 LINK-only-trend-scan (bear-OOS + other-OOS specialist) + /036 LINK+DOT-trend-scan (bull + chop coverage)**. Pre-Pareto on 10 seeds.
2. **Multi-seed n_trials=35 ENSEMBLE_SIZE=10 at /044**: expected n_eff~15. F5 basin will stabilize across seeds; whichever basin survives multi-seed is the load-bearing one. If LINK-only multi-seed mean OOS Sharpe ≥ +0.80 across 10 seeds, /043 component is bundle-ready.
3. **Add bull-regime conditional dispatch gate to /043 component in /044 bundle**: per Item 4 finding 3, /043 component should NOT EMIT when BTC 90d return > +20% AND rv30 < q75 (canonical bull tag). Mechanism: LINK-trend-scan-alone is bear/other/chop-oriented; bull-dispatch consistently drags. Mechanical EDA on /036 LINK-leg bull months supports this.
4. **`baseline_seed_regime_matrix.csv` is the /044 one-time bootstrap deliverable** (per checklist). σ_R values for bull/bear/chop/other not yet computable; LM Master pre-estimate: σ_R(bull) ≈ 0.5, σ_R(bear) ≈ 0.6, σ_R(chop) ≈ 0.8 (high — 4-6 sample months drives variance), σ_R(other) ≈ 0.3.
5. **DO NOT drop the skew/kurt features from V1_FEATURE_COLUMNS_PRUNED** — Item 2 shows these are LINK-specialist-load-bearing. Pruning them would degrade /043 component performance in /044.

## Item 6 — Phase 4.5 Predictions vs Outcome

Phase 4.5 advisor (file head): No Phase 4.5 advisor was authored for /043 (the file's pre-/043 content was /042's Phase 4.5+7.4 only — /043 entered Phase 5 without LM Master pre-design). This is a **process gap** flag for the autopilot: /043 launched without Phase 4.5 LM advisor despite the skill mandate. Should not recur at /044.

In the absence of /043's own Phase 4.5 prior, the brief's predicted modal (REGIME-SPECIALIST-IS 38%, bundle Sharpe band [+0.83, +1.53]) is the relevant prior. **Outcome lands modal** — bundle Sharpe +1.2558 dead-center the predicted band; basin relocation (F5 Jaccard 0.125) exceeded predicted band severity, but the OOS Sharpe outcome compensated upward. **Brief's Section 2 prior distribution is well-calibrated**; LM Master endorses it retrospectively.

## Item 7 — Closing Note for Critic

**Verdict band recommendation: EXPLORATION-PROMISING** (band #5), NOT narrow REGIME-SPECIALIST-OOS. Rationale:

- Headline OOS Sharpe Δ vs BASELINE_V1 **+0.59** is broad-based: /043 beats baseline in **bear-OOS (+0.26), chop-OOS dampened-but-positive, other-OOS strong-positive (+0.34)** — three regimes contribute. NOT a single-regime specialization.
- The ONE regime regression (bull-OOS Δ −0.14 within 4 trades) is sample-fragile and addressable via conditional dispatch gate in /044 bundle.
- OOS MaxDD **21.61% (−19pp better than baseline)** is genuine tail-control; PF 1.73 strong; DSR/PSR meaningfully improved.
- Comparison to /042 closeout pattern: /042 was REGIME-SPECIALIST-IS (bear+chop+vol-spike strong IS, bull-catastrophic, IS-MaxDD 97% blocker). /043 is **STRUCTURALLY HEALTHIER** — IS MaxDD 31.71% (well within range), OOS MaxDD 21.61% (best in v1 history), broad-based OOS lift, ONLY mild bull regression.
- **Critic should specifically examine**: (a) F5 Jaccard 0.125 — basin relocation evidence; (b) bull-OOS −0.397 on 4 trades for sample fragility; (c) regime_attribution.csv internal consistency (Check 3c); (d) vol-spike/recovery NaN rows are tagger-coverage gaps, NOT model failures.

**Bundle-role implication for /044**: STRONG candidate as a 2-of-2-component bundle with /036 LINK+DOT (or 3-of-3 with /037 Sortino). /043 covers OOS bear + OOS other regimes that /036 LINK-leg under-covered. The 9-band verdict is EXPLORATION-PROMISING; multi-seed CONFIRMATION at /044 is the canonical next step. Critic's 9-band call is independent of mine — I provide the regime decomposition as the load-bearing input.

---

**File path**: `/home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-043/lgbm_advisor.md` (orchestrator appends this Phase 7.4 section).

**Report-back (≤500 words)**:

**Regime table summary**: /043 LINK-alone vs /036 LINK-leg shows **mixed within-regime Δ** — bull IS −0.04 / OOS −0.14 (off-regime drag); **bear IS −0.34 / OOS +0.26** (OOS-improved); **chop IS +0.19 / OOS −0.66** but absolute /043 OOS chop +0.38 still positive; **other IS −0.18 / OOS −0.07** (largest OOS trade contributor — 24 trades). Vol-spike + recovery NO COVERAGE (tagger gap, not failure). Internal consistency PASS (regime PnL reconciles to bundle).

**Bundle role recommendation**: /043 = 2-of-2-component bundle slot at /044, paired with /036 LINK+DOT (or 3-of-3 with /037 Sortino). /043 covers **OOS-bear + OOS-other** regimes that /036 LINK-leg under-served. Add **bull-regime conditional dispatch gate** (BTC 90d > +20% AND rv30 < q75 → /043 component OFF). Multi-seed n_trials=35 ENSEMBLE_SIZE=10 mandatory.

**Verdict band (9-band)**: **EXPLORATION-PROMISING (band #5)**. NOT REGIME-SPECIALIST-OOS — three regimes (bear, chop, other) contribute positively to OOS lift +0.59; broad-based not narrow. NOT UNIVERSAL — bull regression and F5 basin relocation prevent. Critic's 9-band call independent.

**Comparison to /042 closeout pattern**: /042 was REGIME-SPECIALIST-IS with IS MaxDD 97% catastrophic + bull-OOS −3.20 disqualifier; /043 is STRUCTURALLY HEALTHIER (IS MaxDD 31.71%, OOS MaxDD 21.61% best in v1 history, broad-based OOS Sharpe lift, ONLY mild bull regression on 4 trades). n_effective_trials=9 (LightGBM saturation pattern) vs /042 XGB's 10. Basin relocation (F5 Jaccard 0.125 << brief's [0.50, 0.90]) is the key INFORMATIONAL flag — LINK-alone found a DIFFERENT basin than LINK-leg-of-/036, with skew/kurt features promoted to top-5 (Item 2). Multi-seed at /044 will validate that this basin survives across seeds.

**Process gap flag**: /043 had no Phase 4.5 advisor authored (Phase 4.5 skill mandate violated for this iteration). The existing `lgbm_advisor.md` head is /042's Phase 4.5+7.4 only. This Phase 7.4 section is /043's first LM Master deliverable. Should not recur at /044 — Phase 4.5 advisor MUST be authored before /044 brief Phase 5.
