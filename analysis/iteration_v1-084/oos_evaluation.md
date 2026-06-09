# iter-v1/084 — Phase 7 OOS Evaluation Memo (CRVUSDT SPECIALIST)

**Date**: 2026-06-09
**Track**: v1 (refactored)
**Branch**: `iteration-v1/084`
**TYPE**: SPECIALIST — single-coin cohort `("CRVUSDT",)`; 5th BUNDLE-003 candidate; FIRST under the REFORMED negative-baseline selector.
**Commit under eval**: `78b9411d` (Phase 7.5 Critic review) / model run at `b3c6a9dd`
**Verdict**: SPECIALIST-NEGATIVE (catastrophic), subtype NEGATIVE-MOMENTUM-DOMINATED

---

## 1. Headline result — IS −2.47 / OOS −1.59, catastrophic

| Metric | In-Sample | Out-of-Sample | OOS/IS ratio |
|---|---|---|---|
| Monthly Sharpe | **−2.4717** | **−1.5886** | 0.6427 |
| Monthly Sortino | −1.5529 | −1.9222 | 1.2378 |
| Max drawdown | **188.74%** | 48.14% | 0.2551 |
| Win rate | 29.8% | 30.3% | 1.0169 |
| Profit factor | 0.4564 | 0.6526 | 1.4297 |
| Total trades | 181 | 89 | 0.4917 |
| Net PnL (equity-curve return) | −188.74% | −45.84% | — |
| Net PnL (sum-of-trade-returns) | −326.29% | −123.72% | — |
| DSR | −26.30 | −29.91 | — |
| PSR(monthly vs 0) | 0.000062 | 0.008852 | — |

IS Sharpe −2.4717 is the **single worst result in the entire v1 campaign**. It is not underperformance against a positive baseline — it is a directional anti-signal that craters in both samples. The OOS Sharpe of −1.5886 confirms the failure is stable, not an IS fluke. The OOS/IS Sharpe ratio of 0.64 is meaningless here (both terms are deeply negative); it does not indicate generalization.

**F4 falsifier (TS-momentum-beat)**: ML IS Sharpe −2.4717 vs the +0.069 min-horizon trivial-momentum baseline CRV was *selected* to beat. The ML head is ~2.5 Sharpe units BELOW the trivial baseline it was supposed to exploit headroom against. F4 FAILS catastrophically.

---

## 2. Structure diagnosis — negative-baseline is necessary, NOT sufficient

This is the central finding. CRV was selected by the REFORMED negative-baseline selector (min-horizon trivial Sharpe +0.069, the flattest of 12 ≥4y candidates; bear-regime trivial −0.924). The reform hypothesis was: "most-negative/near-zero trivial-momentum Sharpe ⇒ ML edge headroom." CRV decisively falsifies the *sufficiency* of that rule.

A near-zero trivial baseline admits **two populations**:

- **Case (a) — directional structure that trivial momentum mis-handles but ML can exploit.** DOT/063 (IS +1.32), AAVE/078 (rescue +0.34). Negative/weak baseline + structure present → WORKED.
- **Case (b) — no directional structure at all (pure noise).** CRV/084. Near-zero baseline + structure absent → the depth-5 head fits IS noise into a spurious sign-rule that INVERTS OOS, and craters.

CRV is unambiguously case (b). Confirmed on three independent axes:

### 2.1 Symmetric ~30% win rate in BOTH directions = anti-signal, not no-signal
- Long WR 31.2% (96 trades), short WR 28.2% (85 trades), aggregate 29.8% IS / 30.3% OOS.
- On a near-symmetric triple-barrier label a directionally-blind model floors near ~50% binary. **30% in both signs means the model systematically picked the WRONG side.** It fit IS noise into a sign-pattern that is anti-correlated with realized forward returns, and the OOS WR 30.3% confirms the inversion is stable, not luck.
- Profit factor 0.4564 IS (lose ~$2.19 per $1 won); 115/181 = 63.5% stop-out rate.

### 2.2 Diffuse feature importance = noise-fitting across the whole space
- Top feature `vol_atr_14` = 8452 gain. The committed NEW feature `oi_price_divergence_30` landed rank **2/49** (gain 7025).
- On a structure-present symbol, top-2 importance for a purpose-built feature is good. On a **no-structure** symbol it is the WORST outcome: the tree routed top-tier split budget through a feature that encodes no CRV forward edge — high importance here means "the model leaned hard on noise," not "the model found signal."
- LM Master Phase 4.5 explicitly predicted rank 8–14 with the suspicion-flag "if it lands rank 1–3, treat as SUSPICIOUS." **The flag fired** (rank 2). Gain is spread across 47 of 49 active features (only the two cross-asset ratio features at zero) — the textbook diffuse-importance fingerprint of a tree fitting noise.

### 2.3 Max-DD 188% = it blew up, it did not merely underperform
- A symbol with weak-but-real structure produces a small negative Sharpe with a contained drawdown. CRV went **188.74% underwater IS** — fully past zero equity and beyond.
- Corroborated by the EDA's own near-zero return autocorrelation: lag1 −0.026, lag3 −0.024, lag7 −0.003 (all within noise of zero). CRV is choppy/mean-reverting with no persistent directional structure at the 8h horizon. The +0.069 trivial baseline was the **absence of edge in the symbol**, not headroom for ML to exploit.

**Look-ahead is NOT the cause.** Critic Check 1 traced `add_oi_price_divergence_30_feature` (double-`.shift(1)`, sign-difference of `pct_change(30)` legs, exact-int OI left-join) — strictly ≤ t−1, no leak. The foundation embargo (`walk_forward.py:113`, iter-v3/057 fix `5566a69`) is intact. The catastrophic Sharpe is a genuinely, repeatably wrong model — not a hygiene artifact.

---

## 3. Per-regime bleed

The committed per-regime CSV collapses ALL bars to `regime=unknown` — the regime tagger did not partition this single-symbol run. This is a reporting gap, not a verdict issue (IS Sharpe is catastrophic regardless of regime split). The brief-mandated per-regime decomposition (the "bear-localized edge" thesis, where trivial momentum was −0.924) **cannot be tested against this run's artifact.**

| Regime | Trades | WR | Net PnL % | Sharpe |
|---|---|---|---|---|
| IS `unknown` | 181 | 29.8% | −326.29 | −0.2358 |
| OOS `unknown` | 89 | 30.3% | −123.72 | −0.1731 |

(The CSV's daily-Sharpe figures −0.2358 / −0.1731 differ from `comparison.csv`'s monthly Sharpe −2.4717 / −1.5886 by the daily-vs-monthly aggregation convention. The monthly figures are the verdict-relevant ones.)

The bear-localized headroom thesis is therefore **untested, not refuted** — but moot: the IS catastrophe swamps any plausible regime-localized edge. If the program ever revisits, the regime tagger must be wired into single-symbol runs.

---

## 4. Per-month bleed — concentrated blow-up, not steady bleed

The −188.74% IS equity-curve loss is a **blow-up signature**. 20 of 30 IS months are negative (67%), but **two months carry ~56% of the total loss**:

| Month | IS PnL % | Trades | Share of total IS loss |
|---|---|---|---|
| 2022-09 | −54.84 | 7 | ~29% |
| 2025-01 | −51.16 | 6 | ~27% |
| (sum) | **−106.01** | 13 | **~56%** |

Outside those two months the bleed is a survivable ~−83% over 28 months. The two crater months are CRV's hot-vol regimes: at fixed ATR 2.9/1.45 on CRV's hot loss surface (NATR p50 ~7.9%, p90 10.0%), a cluster of confidently-wrong, max-conviction trades in a single high-vol month compounds into a >50%/month crater. **The catastrophe is the interaction of (anti-signal) × (CRV vol regime) × (181 leveraged trades)** — not a deeper-negative version of FIL/083's clean drift.

The OOS curve repeats the pattern: **2026-01 −20.55% in a single month (11 trades)** dominates the OOS loss; the rest of OOS is a contained chop of small wins and losses (best month 2025-09 +5.22%, 2025-05 +3.50%).

| OOS month | PnL % | Trades |
|---|---|---|
| 2026-01 | **−20.55** | 11 |
| 2025-04 | −8.16 | 4 |
| 2025-09 | +5.22 | 5 |
| 2025-05 | +3.50 | 7 |

This confirms a per-cell PBO/DSR average would mask a regime-clustered blow-up behind a 30-month mean. The model is not steadily wrong; it is catastrophically wrong in CRV's high-vol clusters, exactly where conviction × leverage is most punishing.

---

## 5. Component attribution — feature ACCELERATED, R-FADE NEUTRAL-to-harmful; the SYMBOL caused it

- **`oi_price_divergence_30`**: cleared F2's INERT branch (rank 2/49, gain 7025 — not inert), but on a no-structure symbol this is the harmful outcome. The model amplified the noise fit by spending top-tier split budget on a feature with no CRV forward edge. The feature itself is verified-clean (binds, no leak) — the problem is the symbol it was aimed at.
- **R-FADE gate (76 fires)**: cleared F3 branch-a (not inert) and branch-b (OOS 89 trades held above the ≥50 floor). But a VETO-only gate cannot rescue a model whose *surviving* trades are themselves anti-signal — the 181 that remained still ran WR 29.8% / PF 0.46. It pruned noise from a noise distribution: net-neutral-to-mildly-harmful. The IS fade-z calibration was non-monotone and reversed past |z|≥2.5 (brief's own honest read), consistent with no exploitable divergence relationship on CRV.
- **F3 control gap**: the R-FADE-OFF control cell was pre-registered (F3, Kill-Switch L406) and flagged at Phase 6.0, but the runner shipped only the R-FADE-ON cell. F3 is therefore UNVERIFIABLE. Moot here (the catastrophic ML head swamps any gate effect) but a process gap for future runners.

**Attribution verdict**: feature ACCELERATED (top-2 gain on noise), R-FADE NEUTRAL-to-mildly-harmful. Neither *caused* the catastrophe — the SYMBOL did. Stacking two new axes on a no-structure symbol merely gave the overfit more surface area.

---

## 6. Methodology integrity — clean

- Look-ahead: PASS (double-shift trace; foundation embargo intact).
- Embargo: PASS (single-symbol cohort, train/test boundary embargo bit-inherited from /063→/078→/083 family).
- Reproducibility: PASS (commit SHA stamped; explicit `V1_ITER084_FEATURE_COLUMNS` 49-col LOCAL asserted; global `V1_FEATURE_COLUMNS_PRUNED` held at 48 — DOT/ETH/BTC/AAVE specialists unaffected; one-variable-at-a-time discipline intact; `OI_DIVERGENCE_FADE_Z == 2.0` anti-tuning assertion present; sacred constants OOS_CUTOFF_MS=1742774400000 and training_months=24 held).
- Hypothesis-implementation alignment: PASS — the three pre-registered changes (CRV cohort, `oi_price_divergence_30`, R-FADE) were faithfully implemented. **No scope creep, no hypothesis-faking.** This is the ideal adversarial outcome: a clean test that produces a clean, decisive NEGATIVE.
- Axis-family validation: PASS — declared `per-cohort-specialization-CRV` matches the src/ diff under the cycle-6/7 per-symbol regime-specialist mandate (5-family rotation SUSPENDED).

The DSR/PSR/PBO floors (Check 3 FAIL) are floored by the deeply-negative underlying Sharpe and are informational at the SPECIALIST EXPLORATION layer (CONFIRMATION/BUNDLE-layer gates). They confirm there is no statistically defensible edge, consistent with F4.

**Reporting defects to note for the next runner**: (1) per-regime CSV collapsed to `unknown`; (2) `comparison.csv` IS net_pnl_pct −188.74% vs per_symbol/per_regime −326.29% is a compounded-equity-curve-return vs sum-of-trade-returns definition mismatch on the same trade set (does not alter the verdict); (3) the committed `ic_matrix.csv` is a family-vs-family redundancy matrix, NOT feature-vs-LABEL IC — there is therefore NO measurement of whether any feature carries forward predictive signal vs the triple-barrier label, which is precisely the methodological hole that let a no-structure symbol through.

---

## 7. What this means — the reform is REFINED, not refuted

The reformed negative-baseline selector is **necessary but not sufficient**, empirically confirmed across four data points:

| Iter | Baseline | Structure | Outcome | Case |
|---|---|---|---|---|
| DOT/063 | negative/weak | present | IS +1.32 | (a) WORKED |
| AAVE/078 | negative | present | rescue +0.34 | (a) WORKED |
| FIL/083 | **POSITIVE +1.45** (clean trend) | n/a (no headroom) | IS −0.82 | the trap GATE 1 correctly removed |
| **CRV/084** | near-zero +0.069 | **ABSENT (pure noise)** | **IS −2.47** | **(b) the catastrophic branch GATE 1 cannot screen** |

GATE 1 (negative-baseline) screens out FIL-type positive baselines but admits BOTH case (a) structure-present and case (b) structure-absent symbols. **A near-zero trivial baseline means EITHER ML edge headroom OR pure noise.** The selector needs a SECOND gate measuring LEARNABLE STRUCTURE before a symbol enters a specialist brief.

**The refined rule**: a symbol enters a specialist brief iff
`trivial_baseline_min_horizon ≤ +0.15` (GATE 1, unchanged)
**AND** `probe_IS_Sharpe ≥ +0.30` (GATE 2 primary: fast single-seed LightGBM probe, max_depth=5, seed=42, n_trials=10, full stack, exact label, walk-forward IS-only)
**AND** `max single-feature-vs-LABEL |IC| ≥ 0.04` (GATE 2 secondary — REQUIRES replacing the family-redundancy ic_matrix with a direct feature-vs-label computation)
**AND** `max(|acf_lag1|, |acf_lag3|, |acf_lag7|) ≥ 0.03` (GATE 2 tertiary, informational confirmer).

The probe is the load-bearing gate. CRV would have been rejected at the probe stage (minutes) instead of a ~5.5–8h specialist that cratered. **CRITICAL CAVEAT**: GATE 2 would have correctly rejected CRV, but it does NOT establish that a structure-PRESENT fresh alt yields a POSITIVE specialist under the locked stack — that conjunction (negative-baseline AND structure-present → positive specialist) is UNTESTED. GATE 2 alone does not produce a winner.

---

## 8. Adversarial — fresh-alt mining is at 0/4

The fresh-mining scorecard: **ATOM, ICP, FIL, CRV — all NEGATIVE.** The ONLY rescuable seat (AAVE/078) was an EXISTING-ROSTER rescue, not a fresh mine. Two selection rules have now been tried (narrative-orthogonality at FIL, negative-baseline at CRV); both produced fresh-mine NEGATIVEs.

This is strong evidence that the binding constraint may not be the selector at all, but the locked methodology's (50-seed × 30-trial × max_depth=5/num_leaves=31 × 48-col stack) inability to extract edge from any symbol outside the original {BTC, ETH, DOT} core + the AAVE rescue. Before spending another ~5.5–8h on a 6th fresh mine, the burden of proof has shifted to demonstrating the locked architecture CAN produce a fresh-mine winner at all.

---

## 9. Decision

**SPECIALIST-NEGATIVE (catastrophic), subtype NEGATIVE-MOMENTUM-DOMINATED — the reform-falsifying outcome the brief pre-registered as its second-most-plausible failure mode.**

- CRV DROPPED from the BUNDLE-003 candidate roster.
- **BUNDLE-002 (`v0.v1-082`) UNCHANGED.** No BUNDLE-003.
- Value of the iteration: the GATE-2 methodology refinement (negative-baseline AND learnable-structure), and the 0/4 fresh-mine evidence recommending a MINING PAUSE.
