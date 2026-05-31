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
