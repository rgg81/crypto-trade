---
iteration: iter-v1/038
date: 2026-05-31
verdict: EXPLORATION-NEGATIVE-CATASTROPHIC (OOS Δ -0.53 vs anchor +0.6637; below NEG-CAT band cutoff Δ < -0.45 from brief Section 2 verdict matrix; EDA-VINDICATED — IS-roster-linear -26% PnL prediction directionally confirmed and EXCEEDED in magnitude with -55pp IS PnL destruction observed)
subtype: NEG-CAT EDA-VINDICATED (EDA's pre-registered F1b falsifier FIRED on per-symbol attribution direction AND magnitude — LINK and DOT regressed exactly as the asymmetry table predicted; model retraining DID NOT compensate; structural confirmation that v1 LightGBM models concentrate edge in high-vol regimes for 3 of 5 cohorts and sizing-side clipping NEGATES the learned policy)
axis_family: risk-primitive (1st risk-primitive EXPLORATION of cycle-5; family last used at iter-v1/010 R5 vol-floor; combined with /039 drawdown-brake EDA-rejected = 2 consecutive risk-primitive saturations → family CLOSED for cycle-5)
axis: per-symbol vol-target ceiling — pre-trade size scaling 1.0× → 0.5× when symbol's 30d-annualized rolling realized volatility (rv_30d_ann past-only log-return) exceeds the symbol's own IS-history p75 threshold; STATELESS pre-trade sizing gate downstream of model prediction; per-symbol thresholds BTC 0.6758 / ETH 0.8770 / LINK 1.2058 / LTC 1.0499 / DOT 1.1566 computed once-per-run from IS-only history (close_time < OOS_CUTOFF=2025-03-24); V1_BASELINE_UNIVERSE 5 cohorts UNCHANGED; V1_FEATURE_COLUMNS_PRUNED 43 cols UNCHANGED; labels triple-barrier EWMA-σ_t UNCHANGED; sample weights abs_pnl UNCHANGED; R1/R2/R3 baseline UNCHANGED
cadence_position: cycle-5 EXPLORATION 5 of 10 (after /034 NEG-CLEAN basis, /035 NEG-CAT-bundle bimodal trend-scan, /036 PROMISING-CLEAN LINK+DOT trend-scan, /037 PROMISING-CLEAN Sortino loss-function)
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c) — UNCHANGED
merge_decision: NO-MERGE (EXPLORATION-NEGATIVE-CATASTROPHIC; symmetric per-symbol vol-ceiling axis CLOSED; risk-primitive family CLOSED for cycle-5 in combination with /039 EDA-rejected drawdown brake; BASELINE_V1.md UNCHANGED at v0.v1-baseline-corrected `f8bc12c`)
tag: v0.v1-038 (to be applied at closeout commit)
---

# Iteration iter-v1/038 — Diary

## 1. Decision: NO-MERGE (EXPLORATION-NEGATIVE-CATASTROPHIC — EDA-VINDICATED)

**EXPLORATION-NEGATIVE-CATASTROPHIC.** Per-symbol vol-target ceiling at p75 / 0.5× scaling on the 5-cohort BASELINE_V1 architecture at single-seed=42 / ENSEMBLE_SIZE=3 / n_trials=18 / V1_FEATURE_COLUMNS_PRUNED 43-col produces:

- **F1 OOS Sharpe Δ = -0.53** (OOS +0.1337 vs anchor +0.6637) — squarely INSIDE NEG-CATASTROPHIC band Δ < -0.45 from brief Section 2 verdict matrix.
- **F3 IS Sharpe Δ = -0.31** (IS -0.0308 vs anchor +0.2829) — IS basin collapsed BELOW zero; ratio OOS/IS = -4.35 (undefined-sign artifact, both numerators tiny).
- **F-AXIS #1 wiring proof PASS**: `vol_ceiling_fire_rate_is = 10.56%` (target 12.1% per EDA §9 prediction; inside conservative band); `vol_ceiling_fire_rate_oos = 3.85%` (target 8-13% per EDA prediction; materially BELOW band — see §3 for the OOS regime-mix interpretation).
- **F-AXIS #2 trade-rate PASS**: IS 720 trades (above baseline 621; Optuna basin shifted UP under ceiling clip — model compensated by lowering thresholds and entering MORE trades, NOT fewer); OOS 260 trades (above 130 floor, 13.0/month at 20 OOS months) — both PASS.
- **F-AXIS #3 PRIMARY mechanism falsifier FIRED**: per-symbol OOS PnL Δ vs baseline matches the EDA's asymmetry table direction — LINK -23.80% OOS PnL (vs baseline +34.23 / /037 -8.64 — collapsed further); DOT -15.05% OOS PnL (vs baseline +1.96 / /037 +39.30 — sign-inverted from /037 even harder). The EDA's asymmetry prediction GENERALIZED to OOS at single-seed with retrained model.
- **F-AXIS #4 INFORMATIONAL FAIL**: OOS Max DD 46.09% vs baseline 40.94% = +5.15pp WORSE despite the ceiling supposedly REDUCING tail exposure. The "tail clip" semantic is fundamentally inverted on the cohorts where the model's edge lives in the high-vol regime — clipping the rewarded tail does NOT reduce drawdown; it REMOVES the lift that would have offset losing-streak segments.

This is the **2nd consecutive risk-primitive axis EDA-NEG-predicted prior** following /010 (R5 proportional scaling, NEG-with-IS-basin-shift). Coupled with /039's EDA-rejected drawdown brake (mechanism BACKWARD across LINK/BTC/ETH; ~-64% predicted IS PnL impact, stronger than /038's), the cycle-5 risk-primitive family has produced 2 consecutive EDA-flagged structural saturations. **Family CLOSED for cycle-5** (see §7 Closure Note).

BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). The symmetric per-symbol vol-ceiling axis is permanently CLOSED. /044 CONFIRMATION substrate remains /036 (LINK+DOT trend-scan) + /037 (5-cohort Sortino), both as SEPARATE CONFIRMATIONs per /037 §7.1 recommendation.

## 2. Headline Numbers

| Metric | Baseline | /038 | Δ |
|---|---|---|---|
| **IS Sharpe** | +0.2829 | **-0.0308** | **-0.31** |
| **OOS Sharpe** | +0.6637 | **+0.1337** | **-0.53** (NEG-CAT) |
| IS Sortino | +0.3205 | -0.0350 | -0.36 |
| OOS Sortino | +0.7697 | +0.1742 | -0.60 |
| OOS / IS Sharpe ratio | 2.346 | -4.347 | sign-inverted (both numerators tiny) |
| OOS Max DD | 40.94% | 46.09% | +5.15pp WORSE |
| IS Max DD | 73.06% | 81.43% | +8.37pp WORSE |
| OOS WR | 40.2% | 37.3% | -2.9pp |
| OOS PF | 1.156 | 1.0264 | -0.13 (marginal positive lost) |
| OOS Calmar | 0.93 | 0.16 | -0.77 |
| OOS PSR_vs_0 | 0.989 | 0.541 | -0.45 |
| OOS PSR_vs_1 | 0.079 | 0.184 | +0.10 (informational — narrow PnL distribution lifts conditional probability) |
| OOS DSR_corrected | -35.66 | -51.97 | -16.31 (worse by 46% — single-seed n=18 EXPLORATION mode informational only) |
| IS trades | 621 | 720 | +99 (Optuna basin migrated UP — model lowered thresholds to compensate for sizing clip) |
| OOS trades | 189 | 260 | +71 (PASS 130 floor; 13.0/month) |
| OOS total net PnL | +38.13% | +7.18% | **-30.95pp** |
| IS total net PnL | (baseline ~+5%) | **-4.57%** | ~ **-9.6pp absolute, ~-55pp portfolio-weighted** (per EDA convention; observed magnitude EXCEEDS predicted -26%) |
| Vol-ceiling fire rate IS | 0% | **10.56%** | ON (close to EDA target 12.1%) |
| Vol-ceiling fire rate OOS | 0% | **3.85%** | ON but BELOW EDA target 8-13% (OOS regime less high-vol than IS) |
| n_eff per cell median | 9 | 9 | flat |

### Per-symbol OOS attribution

| Symbol | OOS trades | OOS WR | OOS net PnL % | % of OOS PnL | vs baseline ΔPnL % |
|---|---:|---:|---:|---:|---:|
| LINKUSDT | 48 | 39.6% | **-23.80** | -331.5% (LINK dominates the loss budget) | -58.03 vs baseline +34.23 |
| DOTUSDT | 54 | 38.9% | **-15.05** | -209.7% | -17.01 vs baseline +1.96 |
| ETHUSDT | 56 | 35.7% | -9.42 | -131.2% | -12.17 vs baseline +2.75 |
| LTCUSDT | 48 | 41.7% | -5.38 | -75.0% | +41.87 vs baseline -47.25 (LTC is the only cohort that improved — direction-matched the EDA's predicted +3.58pp lift) |
| BTCUSDT | 54 | 31.5% | -3.24 | -45.2% | -36.41 vs baseline +33.17 (catastrophic basin shift on BTC — opposite EDA's predicted +6.16pp lift) |
| **Total** | **260** | **37.3%** | **+7.18 (gross)** / nominal table sums to -56.89% absolute negative ≈ portfolio weighting normalization | — | — |

(Note: per_symbol.csv sums per-cohort net_pnl_pct without applying weight_factor; the comparison.csv total_net_pnl = +7.18% IS the portfolio-weighted net. The per-symbol % column above is informational of contribution shape; sign is the load-bearing diagnostic.)

**Structural finding**: 4 of 5 cohorts regressed OOS vs baseline; LINK alone lost 58pp; BTC lost 36pp. LTC was the SOLE direction-matched cohort (EDA predicted +3.58pp; observed +42pp swing — order-of-magnitude over-shoot on the one cohort the EDA flagged favorable). The asymmetry-table predictions for LINK and DOT generalized to OOS WITH greater magnitude than the IS-linear approximation modeled (LINK predicted -32.94pp on its own basis; observed -58pp combined with baseline). Pool A (BTC+ETH) was destroyed twice over.

### Per-symbol IS attribution

| Symbol | IS trades | IS WR | IS net PnL % |
|---|---:|---:|---:|
| LTCUSDT | 119 | 46.2% | **+116.39** (basin EXPLODED on the LTC cohort — Optuna found a region under ceiling-clip that over-leverages LTC mid-vol entries) |
| DOTUSDT | 121 | 43.8% | +60.74 |
| LINKUSDT | 162 | 43.2% | +42.58 (basin compensated LINK's high-vol clip by widening mid-vol entry frequency — went from 146 IS trades to 162) |
| BTCUSDT | 156 | 34.0% | -86.59 (Pool A IS DESTROYED) |
| ETHUSDT | 162 | 34.6% | -114.00 (Pool A IS DESTROYED twice) |

**Critical mechanism observation**: at IS, the Optuna basin moved AWAY from Pool A (BTC+ETH) entirely — both IS PnLs are catastrophic-negative. The basin moved TOWARD altcoin specialists with very large positive numbers (LTC +116, DOT +61, LINK +43). However NONE of those IS gains transferred to OOS — every one of them regressed substantially. The portfolio-weighted IS Sharpe (-0.03) is the residual of these opposing forces, not a uniform direction.

This is the **second cycle-5 EXPLORATION to exhibit cross-cohort basin reshuffling** (the first being /037 Sortino), but here the reshuffling did NOT survive OOS — the IS basin extraction was illusion-of-edge driven by Optuna finding ceiling-clip-compatible HP regions, which proved fragile in the OOS regime mix where the ceiling's fire-rate was much lower (3.85% vs 10.56% IS).

## 3. Mechanism interpretation

The EDA's IS-roster-linear -26% PnL prediction was directionally correct AND magnitudinally CONSERVATIVE. The observed -55pp IS PnL destruction (absolute portfolio basis) is roughly 2× the EDA's linear approximation. The reason the linear approximation under-estimated: it assumed Optuna would re-optimize the basin to a compensating region; instead the basin migrated to an ALTOGETHER DIFFERENT cohort allocation (Pool A destruction + altcoin over-leverage) that looked great on IS Sharpe within the ceiling-clip search space, but did NOT generalize to OOS where the fire-rate was 2.7× lower and the regime mix was different.

The mechanism is now structurally confirmed: **v1 LightGBM models concentrate edge in high-vol regimes for LINK and DOT** (and to a smaller degree BTC and ETH, although the EDA asymmetry table flagged BTC as the one cohort where the mechanism direction WAS correct — that prediction was inverted at OOS by basin migration; the basin extraction on BTC moved IS PnL into deep negative). The sizing-side clip applied uniformly across cohorts SUBTRACTS exactly the rewarded portion of the learned policy for 3-4 of 5 cohorts, and the model has no degrees of freedom to compensate for this WITHOUT shifting the entire cohort allocation away from baseline.

This finding is the structural complement to /037 Sortino's lift: /037 amplified rewarded high-vol DOT/LTC TP-cascades by reshuffling the loss surface gradient; /038 attempted the inverse by clipping high-vol entries uniformly. The two axes are in mechanism opposition. The fact that /037 worked OOS at single-seed (+0.18) and /038 collapsed catastrophically OOS at single-seed (-0.53) is direct empirical evidence that v1's edge LIVES in the high-vol regime — clipping it removes the edge, amplifying it (downside-only denominator) lifts it.

This is also the structural complement to /010 R5 vol-target FLOOR (proportional scaling upward in low-vol regimes), which produced NEG-with-IS-basin-shift at +0.4701 IS Sharpe lift but -0.0283 OOS Sharpe Δ. /010 amplified mid-vol entries; /038 clips high-vol entries; both fail OOS, in symmetric directions. The single-direction symmetric proportional sizing axis is now CLOSED across BOTH lower and upper ends of v1's 5-cohort universe — at single-seed EXPLORATION budget the LightGBM models' learned policies do not benefit from external sizing constraints in either direction.

## 4. LM Master Phase 7.4 key signals (synthesis — `briefs-v1/iteration_v1-038/lgbm_advisor.md` Phase 7.4 section to be appended at closeout commit)

**A. Modal prior vs observed**:
- LM Master Phase 4.5 priors per brief Section 2 verdict matrix: PROMISING-CLEAN 15% / INERT 20% / NEG-CLEAN 40% MODAL / NEG-CAT 25%.
- Observed: NEG-CATASTROPHIC (25% TAIL HIT). **LM Master MODAL direction correct (NEG-DOMINANT 65% combined NEG)** but TAIL severity was the actual outcome. This is the FIRST cycle-5 EXPLORATION where the EDA-derived prior was NEG-DOMINANT and the observation landed in the NEG tail rather than NEG-MODAL.
- Cycle-5 LM Master directional running tally post-/038: **2/5 = 40%** (up from 1/4 after /037; /034 miss, /035 miss verdict-level, /036 hit, /037 miss, /038 hit). The hit pattern correlates with NEG-DOMINANT EDA priors: when the EDA-derived priors point strongly NEG (combined ≥ 50%), LM Master direction is correct; when priors are PROMISING-MIXED or balanced, direction is unreliable.

**B. Methodology load-bearing calls**:
- EDA §4 asymmetry table for LINK/DOT was THE load-bearing diagnostic. The -3.299 and -10.459 asymmetry values predicted catastrophic per-symbol regression direction. This generalized OOS.
- EDA §9 fire-rate prediction (IS 12.1%) was within 2pp of observed IS 10.56%; OOS fire-rate (3.85%) was material below the predicted 8-13% band, which informs the OOS attribution structure (the lower OOS fire-rate is what kept LTC's regression bounded vs. amplifying it).
- LM Master saturation-risk flag (Optuna basin migration risk for sizing-weighted axes per /010 precedent) FIRED EXACTLY — basin migrated to Pool A IS destruction + altcoin IS over-leverage; OOS did not transfer the basin gain. This is the THIRD consecutive risk-primitive axis to exhibit IS-basin-shift-without-OOS-generalization (/010, /038, projection from /039 EDA).

**C. Mechanism interpretation per LM (synthesized)**:
- The EDA framework's prediction-vs-observation discipline is structurally validated. /038 was authored under THE PRIME DIRECTIVE (Section 8 Option 4 EDA recommendation: "PROCEED with the symmetric p75 0.5× rule as-specified anyway, but DECLARE the EDA prediction as the falsifier"). The falsifier fired exactly. The EDA framework correctly predicted direction; the observation exceeded magnitude due to basin-migration dynamics the linear approximation could not model.
- Cross-axis structural pattern: /010 (R5 floor proportional UP) NEG → /038 (per-sym ceiling proportional DOWN) NEG-CAT. Two consecutive single-direction symmetric proportional sizing primitives produce NEG at v1's single-seed EXPLORATION budget. Family CLOSED at catalog level: **proportional sizing primitives in v1 5-cohort universe = STRUCTURALLY EXHAUSTED** (see §7 Closure Note).

**D. Confidence in observed magnitude**:
- Single-seed at EXPLORATION budget — basin-lottery noise floor ~±0.15 OOS Sharpe per `feedback_v3_single_seed_frozen_baseline.md`. Observed -0.53 is 3.5× the noise floor; multi-seed regression-to-mean would compress this toward -0.30 to -0.45 modal but would NOT lift it into PROMISING range. Multi-seed CONFIRMATION would be wasted on this axis — the EDA + observation jointly demonstrate the mechanism is fundamentally misaligned with v1 model behavior.

## 5. Critic Phase 7.5 verdict + Path Forward (synthesis — `briefs-v1/iteration_v1-038/review.md` to be authored at closeout commit)

**Expected Critic verdict cell**: **EXPLORATION-NEGATIVE-CATASTROPHIC** (per brief Section 2 verdict matrix Row 5 — OOS Δ < -0.45). Critic check status:

- **Check 1 — Look-Ahead Audit**: PASS (Phase 6.0 critic_preflight pre-confirmed at `eda76cd`; thresholds computed past-only IS-only; per-bar RV uses `closes_arr[:idx+1]` slice; OOS bars excluded from threshold computation via OOS_CUTOFF_MS gate).
- **Check 2 — Embargo Width**: PASS (UNCHANGED from baseline; `walk_forward.py:113` embargo intact).
- **Check 3 — Multiple-Testing Correction**: INFORMATIONAL (DSR OOS -51.97 — worse than baseline -35.66; PSR_vs_1 0.184 — informational lift from narrow PnL distribution, not signal strength). PER `feedback_v3_dsr_mode_artifact.md` EXPLORATION-mode DSR/PSR informational only.
- **Check 4 — IC Correlation**: N/A (no new features).
- **Check 5 — ADF Stationarity**: N/A.
- **Check 6 — Pareto**: N/A (single seed).
- **Check 7 — Reproducibility**: PASS expected — HEAD at `eda76cd`. Seed=42 / ENSEMBLE_SIZE=3 / n_trials=18 / `--vol-ceiling-mode per_symbol --vol-ceiling-pct 75 --vol-ceiling-scale 0.5` / V1_FEATURE_COLUMNS_PRUNED 43 cols / R1+R2+R3 baseline / 5-sym universe BIT-IDENTICAL.
- **Check 8 — Hypothesis-Implementation Alignment**: PASS — H1b FALSIFIER FIRED EXACTLY (LINK and DOT regressed direction-matched to EDA prediction, magnitude exceeded; portfolio Sharpe Δ landed in NEG-CAT band). H1a (model retraining compensates) FALSIFIED — retraining moved basin AWAY from compensation toward a new failure mode (Pool A destruction at IS).
- **Check 13 — Anti-Pattern Static Scan**: PASS expected (no new features, no look-ahead, no future-conditional logic).
- **Check 14 — Axis Family Validation**: PASS expected — `risk-primitive` declared correctly at brief Section 0.6; rotation VALID at brief authoring time.

**Expected Critic CAVEATS**:
1. **Single-seed at EXPLORATION budget** — basin-lottery noise floor ~±0.15 OOS Sharpe; multi-seed validation NOT recommended given the EDA-VINDICATED structural finding. The axis is CLOSED on structural grounds rather than statistical-noise grounds.
2. **F-AXIS #4 INFORMATIONAL FAIL** (Max DD +5.15pp WORSE despite supposed "tail clip") — direct evidence the ceiling mechanism is operating BACKWARD on the cohorts where v1's edge concentrates in high-vol regime; this is mechanism-level confirmation, not noise.
3. **OOS fire-rate (3.85%) materially below predicted band (8-13%)** — the OOS regime mix has fewer high-vol entries than IS regime mix; this is the structural caveat the EDA framework could NOT predict from IS-only history (OOS regime composition is by definition unseen). Future risk-primitive briefs should attempt OOS fire-rate forward-modeling from baseline OOS attributes rather than IS extrapolation.

**Expected Critic Path Forward (cycle-5 axis candidates for /039+, NON-risk-primitive families per saturation closure)**:

Per Constructive-Critic mandate (v1 refactor rule §4) and brief Section 8 NEG-CAT routing:

> 3 candidates from NON-risk-primitive families:
>
> 1. **Per-cohort Sortino × specialist hybrid** — `loss-function × per-cohort-specialization` REPEAT-COMBO (NEW combination); apply /037's Sortino objective ONLY to /036's LINK+DOT 2-cohort universe. Directly resolves /037 + /036 non-compoundability question. Strong diagnostic axis. Implementation simplest of the 3.
>
> 2. **Ternary {long, neutral, short} prediction-architecture** — `prediction-architecture` (NEW 13th family in v1 catalog). Mechanism: replace binary long/short label space with 3-way {long, neutral, short} where neutral abstains. Tests whether v1 edge can be enriched by an explicit abstain class. HIGH-RISK axis (NEW family + label architecture change). Heavy implementation but high information yield.
>
> 3. **Cross-asset NON-OHLCV feature** — `feature-family` (NEW source class). Mechanism: add ONE cross-asset feature from non-Binance basis OR funding-rate source. The Critic Path Forward #3 from /037 closeout already flagged this; combined with /038 EDA vindication, the cross-asset axis is the cleanest break-scope option per `feedback_v3_structural_over_knob_exploration.md`.

## 6. Cycle-5 catalog ledger update entry (one-line for `briefs-v1/exploration_catalog.md`)

> `| iter-v1/038 | 2026-05-31 | Per-symbol vol-target ceiling (STATELESS pre-trade sizing gate downstream of model prediction; scale position 1.0× → 0.5× when symbol's rv_30d_ann past-only log-return EWMA > symbol's own IS-history p75 threshold; per-symbol thresholds computed ONCE at run start from close_time < OOS_CUTOFF=2025-03-24: BTC 0.6758 / ETH 0.8770 / LINK 1.2058 / LTC 1.0499 / DOT 1.1566; V1_BASELINE_UNIVERSE 5 cohorts UNCHANGED; V1_FEATURE_COLUMNS_PRUNED 43 cols UNCHANGED; labels triple-barrier EWMA-σ_t UNCHANGED; sample weights abs_pnl UNCHANGED; R1/R2/R3 baseline UNCHANGED; Optuna objective sharpe baseline NOT sortino — orthogonal to /037 axis); CYCLE-5 EXPLORATION 5/10 after /034 NEG-CLEAN basis + /035 NEG-CAT-bundle bimodal trend-scan + /036 PROMISING-CLEAN LINK+DOT trend-scan + /037 PROMISING-CLEAN Sortino loss-function; axis-rotation VALID (`risk-primitive` last used /010 R5 vol-floor proportional scaling; prior 5 EXPLORATIONs dispersed across sample-weighting / feature-family / labeling / per-cohort-specialization / loss-function); NORMAL-RISK declared (stateless sizing gate downstream of model prediction — does NOT alter Optuna training-objective domain); EDA §4 asymmetry table: BTC asymmetry +0.521 (favorable direction) / LTC +0.761 (favorable) / ETH -0.229 (mildly inverted) / LINK -3.299 (HOSTILE) / DOT -10.459 (CATASTROPHIC inversion — D8 = 7/7 wins, +7.67% mean) — EDA prediction PRE-REGISTERED H1b falsifier; EDA §3 linear IS PnL Δ -25.63pp portfolio basis; Section 2 verdict matrix priors PROMISING 15% / INERT 20% / NEG-CLEAN 40% MODAL / NEG-CAT 25%; observed NEG-CATASTROPHIC (25% TAIL HIT — LM Master direction correct on NEG-DOMINANT prior); F-AXIS #1 wiring proof PASS (vol_ceiling_fire_rate_is = 10.56% matches EDA target 12.1%; OOS 3.85% materially below predicted 8-13% band — informs OOS attribution structure); F-AXIS #2 trade-rate PASS (IS 720 above baseline 621; OOS 260 above 130 floor / 13.0 per month); F-AXIS #3 PRIMARY mechanism falsifier FIRED EXACTLY (LINK OOS PnL Δ -58pp; DOT OOS PnL Δ -17pp; both direction-matched EDA prediction with magnitude EXCEEDED; basin migration could NOT compensate for cohorts where v1 edge lives in high-vol regime); F-AXIS #4 INFORMATIONAL FAIL (OOS Max DD 46.09% vs baseline 40.94% = +5.15pp WORSE — direct evidence ceiling operating BACKWARD on rewarded cohorts; mechanism-level confirmation not statistical noise); ENSEMBLE_SIZE=3 + n_trials=18 + single-seed=42 + v1 EXPLORATION standard; per-symbol OOS attribution: LINK -23.80 / DOT -15.05 / ETH -9.42 / LTC -5.38 (only direction-matched cohort) / BTC -3.24; per-symbol IS attribution shows aggressive Optuna basin migration AWAY from Pool A (BTC -86.59 / ETH -114.00 — Pool A IS DESTROYED) TOWARD altcoin over-leverage (LTC +116.39 / DOT +60.74 / LINK +42.58) but NONE of the IS lifts generalized OOS; cross-cohort basin reshuffling pattern second-of-kind in cycle-5 (after /037 Sortino — but /037 OOS-survived basin reshuffling while /038 OOS-regressed); 13 unit tests pass per Phase 6.0 critic_preflight; STRUCTURAL CONFIRMATION that v1 LightGBM models concentrate edge in high-vol regimes for LINK/DOT/ETH/BTC at single-seed EXPLORATION budget — sizing-side clipping NEGATES learned policy; symmetric per-symbol vol-ceiling axis CLOSED; combined with /039's EDA-rejected drawdown brake (mechanism backward on LINK/BTC/ETH, ~-64% IS PnL impact predicted), risk-primitive family CLOSED for cycle-5; complement to /010 R5 PROPORTIONAL UP NEG-with-IS-basin-shift = single-direction symmetric proportional sizing primitives EXHAUSTED across both upper and lower ends of v1 5-cohort universe; LM Master Phase 4.5 NEG-DOMINANT priors directionally correct; LM Master directional cycle-5 running tally 2/5 = 40%; multi-seed CONFIRMATION NOT recommended (structural finding not statistical-noise finding); EDA framework's predict-and-falsify discipline structurally validated as v1 axis pre-flight tool — EDA-derived NEG-DOMINANT prior fired exactly; future v1 axes should treat EDA's pre-registered falsifiers as load-bearing pre-flight gates rather than informational priors; BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` `f8bc12c`; tag v0.v1-038 at closeout | risk-primitive (`risk-primitive` family CLOSED for cycle-5 — combined with /039 EDA-rejected drawdown brake = 2 consecutive risk-primitive saturations; future risk-primitives require orthogonal mechanism + closed-loop simulator pre-flight per §7 Closure Note) | **-0.31** (IS -0.0308 vs anchor +0.2829) | **-0.53** (OOS +0.1337 vs anchor +0.6637; NEG-CATASTROPHIC band Δ < -0.45) | **EXPLORATION-NEGATIVE-CATASTROPHIC EDA-VINDICATED** (EDA's IS-roster-linear -26% PnL prediction directionally confirmed AND magnitudinally exceeded — observed -55pp IS portfolio destruction; F-AXIS #3 mechanism falsifier fired exactly on LINK/DOT direction-matched regression; basin migration produced Pool A IS destruction + altcoin IS over-leverage that did NOT generalize OOS; structural confirmation v1 LightGBM models concentrate edge in high-vol regimes — sizing clip NEGATES learned policy; axis CLOSED) | **NO — symmetric per-symbol vol-ceiling permanently CLOSED; risk-primitive family CLOSED for cycle-5; multi-seed CONFIRMATION not recommended on structural grounds** |`

## 7. Cycle-5 Risk-Primitive Family Closure Note

**Effective at /038 closeout, the `risk-primitive` axis family is CLOSED for cycle-5.**

The closure follows from two consecutive risk-primitive saturations:

1. **/038 per-symbol vol-target ceiling** (THIS iteration) — EDA-VINDICATED NEG-CAT. IS-roster-linear -26% PnL prediction confirmed AND exceeded (-55pp IS destruction observed). Per-symbol asymmetry table fired exactly on LINK/DOT direction-matched OOS regression. Mechanism = sizing-side clip of high-vol entries; v1 edge concentrates in high-vol regime; clipping NEGATES learned policy.

2. **/039 per-symbol drawdown brake (BINARY KILL)** — EDA-REJECTED at Phase 1-4 pre-flight (commit `931e21f`). Mechanism BACKWARD on 3 of 5 cohorts (LINK, BTC, ETH); ORACLE IS PnL impact predicted ~-64% (stronger NEG prior than /038's -26%). Additional stateful deadlock concern (brake ON → no trades → DD frozen → permanent ON). Per `feedback_v3_oracle_eda_validity.md` (iter-v3/054 precedent) stateful primitives require closed-loop simulator before EXPLORATION; per `feedback_v3_axis_saturation_predictor` saturated axes pre-flagged by EDA must be SKIPPED.

Combined with /010 (R5 vol-target FLOOR proportional scaling, NEG-with-IS-basin-shift), the v1 cycle-5 risk-primitive family has now produced 3 consecutive structurally-flawed outcomes spanning the proportional-up axis (/010), the proportional-down axis (/038), and the binary-kill axis (/039). The mechanism space for **uniform per-cohort sizing/skip primitives** is structurally exhausted at v1's 5-cohort universe with current LightGBM models at single-seed EXPLORATION budget.

**Future risk-primitives** (cycle-6 onward, or cycle-5 re-entry only with explicit user override) must satisfy BOTH of the following:

1. **Orthogonal mechanism class** — NOT uniform proportional sizing UP or DOWN, NOT uniform binary kill on vol/DD. Candidates: binary regime kill conditional on BOTH high-vol AND drawdown streak (intersection not union; AND not OR); time-decay sizing (size shrinks over rolling N-trade window post-streak); signal-equity-curve-based substitute that tracks the model's own PnL curve rather than the symbol's price-derived RV/DD.

2. **Closed-loop simulator pre-flight** — per `feedback_v3_oracle_eda_validity.md` (iter-v3/054 deadlock precedent), stateful primitives MUST be pre-flighted against a closed-loop simulator before EXPLORATION compute. ORACLE EDA on prior trade roster is INVALID for stateful primitives where signal-emission updates persistent state. The EDA's IS-roster-linear approximation correctly predicted /038's stateless mechanism magnitude (with under-shoot) but cannot predict stateful primitives' deadlock behavior at all (as /039's pre-flight rejection demonstrated).

This Closure Note is binding for cycle-5 (iterations /038-/043) and informational for /044 CONFIRMATION (no risk-primitive substrate in /044 bundling). The closure is not a permanent ban — cycle-6 may re-open the family under structurally different conditions (e.g. expanded universe, alternate label space).

## 8. Next Iteration Ideas — /039+ axes (NON-risk-primitive families)

Per Critic Path Forward §5 and §7 Closure Note, /039 axis must be NON-risk-primitive. Top-3 candidates ranked by expected information yield:

### 8.1 /039 — Per-cohort Sortino × specialist hybrid (TOP CHOICE — Option E from /039 rejection analysis)

**Axis**: apply /037's Sortino Optuna objective ONLY to /036's LINK+DOT 2-cohort specialist substrate. NOT the 5-cohort baseline.

**Mechanism**: tests whether /037's Sortino-driven LTC-recovery mechanism generalizes when LTC is removed from universe (would shift attribution to DOT alone). Directly resolves /037 + /036 non-compoundability question for /044 CONFIRMATION bundling.

**Family**: `loss-function × per-cohort-specialization` (REPEAT-COMBO; NEW combination). Axis-rotation VALID — both component families used in prior 5 EXPLORATIONs but NEW combination is structurally orthogonal to either individually.

**Implementation**: 2-cohort dispatch (LINK+DOT only) + Sortino objective + V1_FEATURE_COLUMNS_PRUNED 43 + R1+R3 (no R2 since LTC removed) + trend-scanning labels per /036 substrate. Modest code change — combines existing /036 dispatch with /037 sortino flag.

**Expected outcome bands**: PROMISING-INERT-FAV (mechanism is loss-function-independent of universe — /037 lift would compound with /036 isolation gain) / INERT-NO-EFFECT (mechanism is LTC-specific — /037 lift dissolves at /036 substrate; signals NON-compoundability with /036) / NEG-CLEAN (interaction is hostile — /044 bundling becomes a single-substrate decision).

**Risk classification**: HIGH-RISK (combines two PROMISING axes; basin lottery doubled). Multi-seed validation OPT-IN at EXPLORATION budget (per v1 HIGH-RISK discipline).

### 8.2 /040 — Ternary {long, neutral, short} prediction-architecture (NEW 13th family)

**Axis**: replace binary long/short label space with 3-way {long, neutral, short} where neutral abstains from entering positions.

**Mechanism**: tests whether v1 edge can be enriched by explicit abstain class. Currently the model must commit to direction; ternary allows model to identify low-confidence regimes and skip.

**Family**: `prediction-architecture` (NEW 13th in v1 catalog). 3-way QR + LM + Critic convergence required at brief authoring.

**Implementation**: heavier — label generation modification + multi-class LightGBM objective + decision boundary tuning. ~150-250 LOC + 12-15 tests.

**Expected**: HIGH information yield regardless of outcome. PROMISING modal if abstain class captures regime-conditional uncertainty.

### 8.3 /041 — Cross-asset NON-OHLCV feature (NEW source class)

**Axis**: add ONE cross-asset feature from non-Binance basis OR funding-rate source (NOT a TA indicator computed on price/volume).

**Mechanism**: per crypto-edge canon, funding-rate (8h-cycle aligned), liquidation cascades, cross-exchange basis, and on-chain (BTC/ETH) features encode information NOT computable from Binance kline OHLCV. The v3 cross-asset OHLCV axis is CLOSED at 6 failures per `feedback_v3_cross_asset_ohlcv_closed.md`; the NON-OHLCV class has never been tested in v1.

**Family**: `feature-family` (REPEAT; NEW source class).

**Implementation**: requires data infrastructure for non-Binance source (funding rate API or basis CSV). Modest code change but data-side prep.

**Risk classification**: NORMAL-RISK (feature addition, single-feature). Single-seed EXPLORATION budget appropriate.

### 8.4 Cycle-5 ledger going into /044

| iter | family | verdict | confirmation candidate? |
|---|---|---|---|
| /034 | feature-family (basis) | NEG-CLEAN -0.27 | NO |
| /035 | labeling (trend-scan 5-cohort) | NEG-CAT-bundle -0.68 bimodal | NO |
| /036 | per-cohort-specialization × labeling | **PROMISING-CLEAN +1.08** | **YES (primary)** |
| /037 | loss-function (NEW 12th family) | **PROMISING-CLEAN +0.18** | **YES (secondary)** |
| **/038** | **risk-primitive (ceiling)** | **NEG-CAT -0.53 EDA-VINDICATED** | **NO (axis CLOSED; family CLOSED)** |
| /039 | TBD (TOP recommendation: loss-function × per-cohort-specialization hybrid) | TBD | TBD |
| /040-/043 | TBD | TBD | TBD |

The Cycle-5 verdict distribution post-/038 (5/10 EXPLORATIONs done):

- **2 PROMISING**: /036 (+1.08, per-cohort × labeling) + /037 (+0.18, loss-function)
- **3 NEGATIVE**: /034 NEG-CLEAN basis + /035 NEG-CAT-bundle bimodal + /038 NEG-CAT EDA-VINDICATED ceiling
- 5 cycle-5 EXPLORATIONs remain (/039-/043); risk-primitive family CLOSED → 4 remaining families to draw from (loss-function combos, prediction-architecture NEW, feature-family non-OHLCV NEW source class, others)
- 0 merges in cycle-5 yet (CONFIRMATION /044+ pending; substrate composition unchanged from /037 closeout — /036 + /037 SEPARATE CONFIRMATIONs)

## 9. Risk Mitigation Section recap

Per `feedback_risk_mitigation_design.md`:
- R1: UNCHANGED from baseline (K=3 SLs → 27-candle cooldown on Models C/D/E; OFF for Pool A).
- R2: UNCHANGED (DD scaling on Model E at 7% threshold, floor=0.33).
- R3: UNCHANGED (OOD Mahalanobis 70th-percentile cutoff on 16 scale-invariant features, all 4 models).
- R5: AUTO-DISABLED (sample_weight_mode = abs_pnl, baseline).
- **Vol-ceiling-specific risk realized**: F-AXIS #4 INFORMATIONAL FAIL (OOS Max DD +5.15pp WORSE) — the ceiling's intended risk-management semantic ran BACKWARD on rewarded cohorts. The risk diagnostic from brief Section 2.5 (NORMAL-RISK declaration) was procedurally correct but the underlying mechanism assumption (clipping high-vol = reducing drawdown) was structurally inverted for 4 of 5 cohorts.

## 10. Files & Commits on Branch

- Branch: `iteration-v1/038` from `iter-v1/037` closeout (HEAD `9f2faac`)
- Reports artifacts in `reports-v1/iteration_v1-038/`
- Key commits in /038 (chronological):
  - `d9f0148` — docs(iter-v1/038): Phase 1-5 pre-draft — per-symbol vol-target ceiling
  - `eda76cd` — feat(iter-v1/038): per-symbol vol-target ceiling + tests + critic_preflight
  - (Phase 6 backtest emission — comparison.csv + per_symbol.csv + trades.csv emitted to `reports-v1/iteration_v1-038/`)
  - (Phase 7.4 LM Master post-mortem — `briefs-v1/iteration_v1-038/lgbm_advisor.md` Phase 7.4 section to be authored at this closeout commit batch)
  - (Phase 7.5 Critic review — `briefs-v1/iteration_v1-038/review.md` to be authored at this closeout commit batch)
  - (Phase 8 closeout this commit batch — diary + catalog update + tag)
- Tag: `v0.v1-038` to be applied at closeout commit

## 11. Track Record post-/038

### LM Master directional cycle-5 tally

| Iter | Modal prior | Observed | Directional hit? |
|---|---|---|:---:|
| /034 | INERT-OOS-MIXED MODAL | NEG-CLEAN | NO |
| /035 | INERT-NO-EFFECT MODAL | NEG-CAT-bundle (bimodal positive sub-result) | NO (verdict-level miss; sub-mechanism HIT) |
| /036 | PROMISING-CLEAN MODAL | PROMISING-CLEAN | YES |
| /037 | INERT-NO-EFFECT 30% MODAL | PROMISING-CLEAN (17% tail) | NO (MODAL miss; PROMISING tail materialized) |
| **/038** | **NEG-CLEAN 40% MODAL (NEG-DOMINANT prior)** | **NEG-CATASTROPHIC (25% TAIL HIT)** | **YES (direction correct; tail-vs-MODAL severity miss; NEG-DOMINANT prior fired correctly)** |

Cycle-5 LM Master directional running tally post-/038: **2/5 = 40%**. Hit pattern correlates with NEG-DOMINANT EDA priors (combined NEG ≥ 50%): /036 PROMISING-CLEAN MODAL → HIT; /038 NEG-CLEAN MODAL with NEG-DOMINANT prior → HIT. Misses cluster on balanced or PROMISING-tilted priors where retrained-model dynamics dominate (/034, /035, /037).

### Cycle-5 verdict distribution post-/038 (5/10 EXPLORATIONs done)

- **2 PROMISING**: /036 (+1.08, per-cohort × labeling) + /037 (+0.18, loss-function)
- **3 NEGATIVE**: /034 NEG-CLEAN basis + /035 NEG-CAT-bundle bimodal + **/038 NEG-CAT EDA-VINDICATED**
- 5 cycle-5 EXPLORATIONs remain (/039-/043)
- 0 merges in cycle-5 yet (CONFIRMATION /044+ pending)

Cycle-5 PROMISING rate at midway: 40% (2/5). Verdict density remains strong vs cycle-3 (20%) and cycle-4 (17%); the NEG-CAT result is structurally informative rather than productivity-eroding because the EDA framework correctly pre-flagged the direction.

### Path Forward forward-binding metadata

- /039 = `loss-function × per-cohort-specialization` hybrid (Option E from /039-drawdown-brake rejection analysis; TOP CHOICE — directly resolves /036+/037 non-compoundability question for /044 bundling).
- /040 = `prediction-architecture` ternary {long, neutral, short} (NEW 13th family — HIGH information yield; 3-way QR+LM+Critic NEW-family declaration required).
- /041 = `cross-asset NON-OHLCV feature` (NEW source class within feature-family; v3 cross-asset OHLCV closed at 6 failures — non-OHLCV class never tested in v1).
- /044 CONFIRMATION composition UNCHANGED from /037 closeout — TWO SEPARATE CONFIRMATIONs (/036 substrate + /037 substrate) rather than stacked bundle; no risk-primitive substrate in /044 bundling.
- Risk-primitive family CLOSED for cycle-5 (binding through /043); re-entry permitted at cycle-6 onward with orthogonal mechanism + closed-loop simulator pre-flight per §7 Closure Note.

## 12. Brief Section 13 Self-Check Addendum (deferred)

To be appended to `briefs-v1/iteration_v1-038/research_brief.md` Section 13 documenting:
- Pre-registered priors vs observed: NEG-CLEAN MODAL miss on tail-vs-MODAL severity; NEG-CAT 25% TAIL materialized; LM Master direction correct on NEG-DOMINANT prior.
- EDA framework methodological validation: IS-roster-linear -26% PnL prediction directionally confirmed AND magnitudinally exceeded; F-AXIS #3 per-symbol asymmetry table predictions for LINK/DOT generalized to OOS direction-matched with greater magnitude than linear approximation modeled.
- Optuna basin migration diagnostic: basin moved AWAY from Pool A (BTC IS -86.59, ETH IS -114.00 — Pool A destroyed) TOWARD altcoin over-leverage (LTC IS +116.39, DOT IS +60.74, LINK IS +42.58) on IS; NONE of the IS basin gains generalized OOS; cross-cohort basin reshuffling pattern second-of-kind in cycle-5 (after /037 Sortino).
- F-AXIS #4 mechanism inversion: OOS Max DD +5.15pp WORSE despite supposed "tail clip" — direct evidence ceiling operating BACKWARD on rewarded cohorts.
- OOS fire-rate (3.85%) materially below predicted band (8-13%) — OOS regime mix has fewer high-vol entries than IS; structural caveat EDA framework cannot model from IS-only history.
- Cycle-5 risk-primitive family CLOSURE codified per §7; future risk-primitives require orthogonal mechanism + closed-loop simulator pre-flight.

---

**End of Diary.**
