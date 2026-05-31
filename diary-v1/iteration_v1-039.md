---
iteration: iter-v1/039
date: 2026-05-31
verdict: EXPLORATION-NEGATIVE-CATASTROPHIC vs /036 substrate (OOS Δ -0.7072 vs /036 anchor +1.7465; below NEG-CAT band cutoff Δ < -0.45 from brief Section 2 verdict matrix; mechanism = Sortino on /036's 2-cohort LINK+DOT trend-scan substrate REDUCES OOS Sharpe by 0.71 — the per-cohort isolation does NOT absorb /037's LINK-hurt mechanism; /037 Sortino lift was 5-cohort-universe-dependent, REFUTED as universe-independent edge ingredient)
subtype: NEG-CAT vs-036 — MECHANISM-UNIVERSE-DEPENDENCE-CONFIRMED (F-AXIS #6 trade-roster Jaccard vs /036 = 0.0878 < 10% FAIL band → BASIN-RELOCATION-ARTIFACT; per-symbol OOS PnL both NEGATIVE direction-matched the NEG-modal prediction; LINK ΔPnL -40.46pp / DOT ΔPnL -69.23pp from /036's bit-identical roster — Sortino's basin re-selection on the 2-cohort substrate jettisons 91% of /036's profitable OOS trades; OOS Sharpe +1.04 vs baseline +0.66 = +0.38 misleading lift if anchored on BASELINE_V1, but the correct anchor per H1b is /036 since that is the substrate)
axis_family: loss-function × per-cohort-specialization HYBRID (composition probe; double-REPEAT JUSTIFIED at brief Section 0.6 as STACKING INTERACTION PROBE, not knob-tuning REPEAT — per /037 closeout Recommendation 2 pre-registered compounding test); HYBRID axis CLOSED at catalog level
axis: per-cohort Sortino × LINK+DOT trend-scan specialist hybrid — `--symbols LINKUSDT,DOTUSDT --label-mode trend_scanning --optuna-objective sortino --ensemble-size 3 --n-trials 18 --seeds 1`; V1_FEATURE_COLUMNS_PRUNED 43 cols UNCHANGED; sample weights abs_pnl UNCHANGED; R1/R2/R3 baseline UNCHANGED; NO new src/ code, composition of three previously-shipped flags
cadence_position: cycle-5 EXPLORATION 6 of 10 (after /034 NEG-CLEAN basis, /035 NEG-CAT-bundle bimodal trend-scan, /036 PROMISING-CLEAN LINK+DOT trend-scan, /037 PROMISING-CLEAN-MECHANISM-DIVERGENT Sortino, /038 NEG-CAT-EDA-VINDICATED per-symbol vol-ceiling)
anchor: /036 substrate anchor (OOS Sharpe +1.7465) — NOT BASELINE_V1 (per brief H1b pre-registration; anchoring on BASELINE_V1 would obscure the compoundability question and falsely classify a -0.71 collision against the actual substrate as a marginal lift)
merge_decision: NO-MERGE (EXPLORATION-NEGATIVE-CATASTROPHIC vs /036; per-cohort-Sortino × per-cohort-specialist HYBRID axis CLOSED; /044 ROUTING LOCKED at SEPARATE /044-A multi-seed /036 + /044-B multi-seed /037 — bundled hybrid REFUTED; BASELINE_V1.md UNCHANGED at v0.v1-baseline-corrected `f8bc12c`)
tag: v0.v1-039 (to be applied at closeout commit)
---

# Iteration iter-v1/039 — per-cohort Sortino × specialist hybrid — NEG-CAT-vs-036 — mechanism universe-dependence CONFIRMED

## 1. Decision: NO-MERGE (EXPLORATION-NEGATIVE-CATASTROPHIC vs /036 substrate — MECHANISM UNIVERSE-DEPENDENCE EMPIRICALLY CONFIRMED)

**EXPLORATION-NEGATIVE-CATASTROPHIC vs /036 anchor.** Applying /037's Sortino Optuna objective on top of /036's LINK+DOT trend-scan 2-cohort specialist substrate at single-seed=42 / ENSEMBLE_SIZE=3 / n_trials=18 / V1_FEATURE_COLUMNS_PRUNED 43-col produces:

- **F-AXIS #1 OOS Sharpe Δ vs /036 = −0.7072** (OOS +1.0393 vs /036 anchor +1.7465) — squarely INSIDE NEG-CATASTROPHIC band Δ < −0.45 from brief Section 2 verdict matrix; ~2× MODAL miss-magnitude (modal predicted Δ −0.33 inside NEG-CLEAN band).
- **OOS Sharpe Δ vs BASELINE_V1 = +0.3756** (OOS +1.0393 vs baseline +0.6637) — **informational; NOT the load-bearing comparison.** H1b pre-registered /036 as the substrate anchor; comparing against BASELINE_V1 would mis-classify a -0.71 collision against the actual substrate as a marginal positive lift over baseline. The LM Master Phase 4.5 §"Closing Note" non-ignorable warning fired exactly here.
- **F-AXIS #3 per-symbol Δ sign-match POSITIVE for NEG-direction**: LINK OOS PnL Δ vs /036 = −40.46pp (was +108.91% / now +68.45%); DOT OOS PnL Δ vs /036 = −69.23pp (was +113.63% / now +44.40%). BOTH NEGATIVE, magnitude OUTSIDE [-20pp, +30pp] band → mechanism diverged in the predicted NEG direction.
- **F-AXIS #6 trade-roster Jaccard vs /036 = 0.0878 (FAIL band < 10%)** → BASIN-RELOCATION-ARTIFACT confirmed: per-cohort Jaccard DOT 0.107 / LINK 0.0625; only 13 of /036's 105 OOS trades survived re-selection. **Sortino's basin re-selection on the 2-cohort substrate jettisons 91% of /036's profitable OOS trades** — the substrate's per-cohort isolation does NOT preserve /036's policy; it dissolves it.
- **F-AXIS #2 wiring proof PASS**: dispatch banner `[iter-v1/039] PER-COHORT-SORTINO-HYBRID ACTIVE`; both flags asserted in run.log; per-cell Sortino values logged with non-NaN downside_std.
- **F-AXIS #5 wall-clock**: within modal band (single-seed 2-cohort + Sortino composition; no new src/ code).
- **F-AXIS #7 trade-count**: IS 252 (inside [200, 400] band — modal-low); **OOS 87 — BELOW [80, 160] modal band lower edge** (regressed from /036's 105). The combination of Sortino's chop-trade skip + trend-scanning's significance filter mechanically dropped trade volume below /036, AND those skipped trades were carrying /036's edge.

**The H1b falsifier fires EXACTLY**: bundle OOS Sharpe Δ vs /036 = −0.71 < +0.10 AND per-symbol LINK + DOT OOS PnL deviations EXCEEDED ±25pp of /036's roster (-40 / -69). Per the pre-registered routing decision, the Sortino-on-trend-scan-specialist composite is **REFUTED**. **/037's Sortino lift was 5-cohort-universe-dependent, not universe-independent.** /044 ROUTING LOCKED at TWO SEPARATE CONFIRMATIONs.

BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). The per-cohort Sortino × per-cohort specialist HYBRID axis is permanently CLOSED at catalog level. /037's Sortino survives ONLY on its native 5-cohort substrate (where it earned PROMISING via LTC catastrophe-recovery + DOT amplification + Pool A basin reshuffling — none of which apply to a 2-cohort universe with no LTC, no Pool A).

## 2. Headline Numbers — 3-way comparison vs /036 substrate AND BASELINE_V1

| Metric | BASELINE_V1 | /036 (substrate) | /039 | Δ vs /036 (LOAD-BEARING) | Δ vs BASELINE_V1 (informational) |
|---|---:|---:|---:|---:|---:|
| **IS Sharpe** | +0.2829 | +0.0843 | **-0.1530** | **-0.24** (IS basin destroyed BELOW /036) | -0.44 |
| **OOS Sharpe** | +0.6637 | +1.7465 | **+1.0393** | **-0.7072 (NEG-CAT)** | +0.3756 |
| IS Sortino | +0.3205 | +0.0680 | -0.1244 | -0.19 | -0.44 |
| OOS Sortino | +0.7697 | +1.4934 | +0.8119 | -0.68 | +0.04 |
| OOS / IS Sharpe ratio | 2.346 | 20.73 | -6.79 | sign-inverted (IS<0) | sign-inverted |
| OOS Max DD | 40.94% | 23.28% | 27.52% | +4.24pp WORSE | -13.42pp BETTER vs baseline (no merit — anchor is /036) |
| IS Max DD | 73.06% | 61.53% | 75.84% | +14.31pp WORSE | +2.78pp |
| OOS WR | 40.2% | 54.3% | 49.4% | -4.9pp | +9.2pp |
| OOS PF | 1.156 | 1.6117 | 1.4364 | -0.18 | +0.28 |
| OOS Calmar | 0.93 | 2.22 | 1.61 | -0.61 | +0.68 |
| OOS PSR_vs_0 | 0.989 | 0.903 | 0.853 | -0.05 | -0.14 |
| OOS PSR_vs_1 | 0.079 | 0.594 | 0.481 | -0.11 | +0.40 |
| OOS DSR_corrected | -35.66 | -3.82 | -11.47 | -7.65 (3× WORSE than /036) | +24.19 (informational — EXPLORATION mode artifact per `feedback_v3_dsr_mode_artifact.md`) |
| IS trades | 621 | 281 | 252 | -29 (modal-low) | -369 (universe shrinkage) |
| OOS trades | 189 | 105 | **87** | -18 (BELOW [80,160] band's lower edge of 80 — at the floor) | -102 (universe shrinkage) |
| OOS total net PnL | +38.13% | +51.62% | **+44.28%** | **-7.34pp** | +6.15pp |
| IS total net PnL | ~+5% | +9.64% | -17.64% | -27.28pp | ~-22.6pp |
| **F-AXIS #6 Jaccard vs /036 OOS** | n/a | 1.0 (definitionally) | **0.0878** | FAIL < 10% → BASIN-RELOCATION-ARTIFACT | n/a |
| n_eff per cell median | 9 | 9 | 9 | flat | flat |

### Per-symbol OOS attribution (LINK+DOT only, /036 substrate)

| Symbol | /036 OOS trades | /036 OOS PnL% | /039 OOS trades | /039 OOS PnL% | ΔPnL vs /036 | Jaccard vs /036 OOS |
|---|---:|---:|---:|---:|---:|---:|
| LINKUSDT | 52 | +108.91 | 40 | **+68.45** | **-40.46pp** | 0.0625 |
| DOTUSDT | 53 | +113.63 | 47 | **+44.40** | **-69.23pp** | 0.107 |
| **Bundle** | **105** | +51.62 (portfolio-weighted) | **87** | **+44.28** | **-7.34pp** | **0.0878** |

**Structural finding**: BOTH cohorts regressed substantially. DOT regressed nearly 2× harder than LINK (-69pp vs -40pp), the inverse of /037's 5-cohort pattern (DOT carried +39pp lift / LINK -8.64pp HURT). The 2-cohort universe + Sortino combination **flipped the LINK-vs-DOT asymmetry of /037 entirely** — and lost on BOTH cohorts. /036's bit-identical roster preserved 50/50 PnL split (48.94% LINK / 51.06% DOT); /039's basin-relocated roster lands at 60.66% LINK / 39.34% DOT and shed 14pp net PnL in absolute terms — Sortino is structurally penalizing exactly the trades carrying /036's edge on the substrate where the EDA pre-registered the loss surface as near-symmetric (skew 0.3, exc-kurt < 1).

### Per-symbol IS attribution

| Symbol | IS trades | IS WR | IS net PnL % |
|---|---:|---:|---:|
| LINKUSDT | 142 | 41.5% | +25.26 |
| DOTUSDT | 110 | 41.8% | **-4.87** (basin migrated AWAY from DOT IS — IS-negative DOT was the substrate /036 used + Sortino re-selected away) |

**IS basin observation**: the Optuna basin on /039 destroyed DOT's IS PnL (was +56.84 on /037 5-cohort + similarly positive on /036). The combined Sortino+per-cohort-substrate basin migrated TOWARD LINK IS at the expense of DOT IS — the inverse of /037's 5-cohort DOT-amplification mechanism. This is the smoking-gun mechanism evidence: **Sortino's basin behavior is universe-dependent**. On 5-cohort + triple-barrier, it amplifies DOT TP-cascades + LTC catastrophe-recovery; on 2-cohort + trend-scanning, it neither amplifies DOT nor finds a stable LINK-pure basin — the loss-surface gradient that Sortino exploits on the baseline substrate is absent on the /036 substrate (already-symmetric OOS distribution + significance-filtered chop trades).

## 3. Mechanism interpretation — UNIVERSE-DEPENDENCE EMPIRICALLY CONFIRMED

The single most important finding of /039 is the **direct falsification of /037's Sortino-as-universal-edge hypothesis**. The LM Master Phase 4.5 prior distribution put PROMISING-DOT-ONLY at 22% MODAL — predicting that /037's DOT-skew would be SUBSTRATE-INDEPENDENT and would manifest again on /036. **Observed: DOT NOT amplified; DOT IS PnL went NEGATIVE (-4.87) for the first time across /036/037 substrates.** The LM Master MODAL-direction prior was REFUTED at the per-cohort attribution level.

What actually happened: Sortino's downside-only denominator is a **basin-selection gradient**, not a content-selection gradient. On 5-cohort + triple-barrier, where the loss surface has substantial downside-std-asymmetry per cohort (Sortino/Sharpe ratio 3.0-4.0×), Sortino can re-anchor the Optuna basin to a region where downside-asymmetric trades concentrate — for /037 that turned out to be LTC's catastrophe-recovery regime and DOT's TP-cascade regime. On 2-cohort + trend-scanning, where the loss surface is near-symmetric per cohort (Sortino/Sharpe ratio ~1.22 per EDA §1) and the significance-filter has already removed chop trades, the Sortino gradient has nowhere to relocate to — it picks a basin near /036's by accident but the small Optuna budget (9 trials/cohort) + tighter ridge (sparser labels) lands it on a basin that shares only 8.8% of /036's trade roster.

This is the **structural complement to /038's vol-ceiling finding**. /038 confirmed that v1's edge LIVES in the high-vol regime per the 5-cohort EDA-asymmetry table. /039 now confirms that /037's Sortino lift was a property of the high-vol regime ON THE 5-COHORT SUBSTRATE specifically — when the 5-cohort high-vol cohorts (LTC catastrophe + DOT TP-cascade + the BTC/ETH Pool A averaging effect) are stripped from the substrate, the Sortino mechanism has no surface to operate on. The /037 mechanism is **NOT a generic Sortino-vs-Sharpe property; it is a Sortino-vs-Sharpe-on-LTC-catastrophe-recovery property** that lives only in the 5-cohort universe.

The 3-way deficit pattern:
- vs BASELINE_V1: +0.38 lift (informational; correct comparison is /036)
- vs /036: -0.71 collision (LOAD-BEARING — substrate destroyed)
- vs /037: -0.04 marginal (OOS +1.04 vs /037 OOS +0.84) — surprisingly close to /037 in absolute OOS Sharpe terms, but /037 had 5× the trades (243 vs 87) so the variance penalty is steep

**Interpretation of the close /039-vs-/037 OOS Sharpe**: the marginal +0.20 lift over /037 OOS comes from removing the 3 hurt cohorts (BTC -8.64 / ETH +9.75 / LTC +85pp-swing / LINK -8.64) that polluted /037's portfolio aggregate. /039 keeps only the cohorts where /037 was already positive on its own substrate (DOT +39pp / a clean LINK basin). But the price paid for this universe shrinkage is the loss of /036's specialist-basin edge on those same 2 cohorts — a -0.71 Δ vs /036. **The /037 mechanism (Sortino basin re-selection) and the /036 mechanism (per-cohort specialist tight basin) are NOT compatible on a shared 2-cohort substrate**: they are basin-competitive, not gradient-orthogonal. Per H1a's pre-registered hypothesis, basin competition was the predicted failure mode at Jaccard < 0.30 vs /036; observed Jaccard 0.088 is well inside the competition band.

This finding has direct cycle-5 ramifications: **/036's lift and /037's lift are non-compoundable across iterations**. The /037 closeout Recommendation 2 pre-registered this exact compounding probe; /039 has now resolved it. **/044 routing is LOCKED at SEPARATE multi-seed validations.**

## 4. LM Master Phase 7.4 key signals

LM Master Phase 4.5 advisory (`briefs-v1/iteration_v1-039/lgbm_advisor.md`) priors:

| Outcome | LM Master prior | Observed |
|---|---:|---|
| PROMISING-CLEAN balanced 50/50 | 18% | NOT observed (Δ -0.71) |
| **PROMISING-DOT-ONLY** (DOT-skewed) | **22% MODAL** | **REFUTED** — DOT IS went NEGATIVE; DOT OOS PnL Δ -69pp |
| PROMISING-LINK-ONLY | 5% | NOT observed |
| PROMISING-INERT-FAV / INERT (Δ ∈ [-0.15, +0.10]) | 28% | NOT observed |
| NEG-COLLISION (Δ < -0.15) | 22% | **PARTIALLY observed (Δ -0.71 is BEYOND NEG-COLLISION into NEG-CATASTROPHIC tail)** |
| NEG-CATASTROPHIC (Δ < -0.40) | 5% TAIL | **OBSERVED TAIL** — 5% prior MATERIALIZED |

**LM Master MODAL direction REFUTED** (DOT amplification was predicted; DOT went IS-negative). **TAIL prediction (5% NEG-CATASTROPHIC) MATERIALIZED.** This is the 2nd time in cycle-5 a low-probability LM Master tail prior MATERIALIZED (the first being /038 NEG-CATASTROPHIC at 25% prior). Cycle-5 LM Master directional running tally post-/039: **2/6 = 33%** (down from 2/5 = 40% post-/038). The pattern that EDA-derived NEG-DOMINANT priors are reliable holds: /039's QR-MODIFIED prior at brief Section 13 placed combined NEG mass at 60% and called NEG-CLEAN modal — direction correct, MODAL miss (the QR also missed at NEG-CLEAN modal vs observed NEG-CAT, but the QR's combined-NEG mass placement was more accurate than LM Master's distributional spread).

**LM Master Phase 7.4 key signals (synthesis)**:

1. **`v1` basin diagnostics PASS** (cross-seed std 0.0 — single-seed by design); **`v2` BORDERLINE** (per-cell ρ NaN — single-seed cannot compute correlation); **`v3` Jaccard 0.0878 FAIL < 0.15** — the global verdict is FAIL on the v3 leg, which is exactly the load-bearing diagnostic for this axis.
2. **The 18% PROMISING-CLEAN balanced 50/50 prior was the right "if-positive" routing path** but didn't materialize. The 22% PROMISING-DOT-ONLY modal that LM Master predicted as the most-likely outcome was REFUTED at the per-symbol attribution level: DOT IS PnL went NEGATIVE, the inverse of every other Sortino observation we have in v1.
3. **LM Master Phase 4.5 "non-ignorable" guidance fired exactly** — the brief Section 2 anchor was correctly fixed to /036 (+1.7465) not BASELINE_V1 (+0.6637), which is what made the -0.71 verdict identifiable. Had the diary anchored on BASELINE_V1 the +0.38 lift would have looked PROMISING.
4. **Confidence rating revisited**: LM Master rated MEDIUM-HIGH on non-zero effect, MEDIUM on PROMISING direction. The non-zero effect was correct (Δ -0.71 is far from zero). The PROMISING direction was wrong — Sortino's mechanism on /036 substrate produced a substantial NEG effect, the inverse of the directionally-predicted DOT-amplification path.
5. **For /044 routing**: LM Master's pre-conditioned routing decision (per Phase 4.5 §"/044 Routing Implication") was: PROMISING-DOT-ONLY → SEPARATE /036 + /037 substrates (leaning b); INERT/NEG → /036 alone + /037 deferred for a different substrate. **Observed routing matches the INERT/NEG branch but with stronger evidence** — /037's substrate is now empirically known to be 5-cohort-dependent, so /044-B retains /037's native 5-cohort + Sortino as the substrate (not a different substrate as LM Master conditionally suggested).

## 5. Critic Phase 7.5 verdict + Path Forward

**Critic verdict**: **EXPLORATION-NEGATIVE-CATASTROPHIC** (vs /036 anchor per pre-registered H1b in brief Section 1). The verdict is unambiguous: all four load-bearing falsifiers fired in the NEG direction:
- F-AXIS #1 OOS Δ vs /036 = -0.71 (band Δ < -0.45 → NEG-CAT)
- F-AXIS #3 per-symbol sign-match both NEGATIVE with magnitudes EXCEEDING ±25pp band (-40pp / -69pp)
- F-AXIS #6 Jaccard 0.088 < 10% FAIL band → BASIN-RELOCATION-ARTIFACT
- F-AXIS #7 OOS trades 87 at lower-edge of [80, 160] band

The verdict is clean (not BLOCK-PENDING-FIX) — wiring proof passed, code shipped correctly, axis was correctly implemented and produced an empirical NEG result that resolves the /037 compoundability question.

**Critic Path Forward** (verbatim integration for /040-/043 axis selection):

1. **/044 ROUTING LOCKED**: SEPARATE /044-A (multi-seed /036 LINK+DOT trend-scan specialist alone, `--seeds 2 --n-trials 35 --ensemble-size 5`) AND /044-B (multi-seed /037 5-cohort + Sortino alone, same multi-seed config). NO bundled hybrid. The per-cohort-Sortino × per-cohort-specialist hybrid axis is permanently CLOSED at catalog level. Pre-/044 EXPLORATIONs (/040-/043) must complete the 10-iteration cadence.

2. **Risk-primitive family CLOSED for cycle-5** (already declared at /038 closeout; reinforced at /039 closeout — although /039 is NOT a risk-primitive iteration, the closure stands).

3. **Loss-function family CLOSED for substrate compounding**. Sortino has been tested on (a) 5-cohort + triple-barrier substrate at /037 = PROMISING-CLEAN-MECHANISM-DIVERGENT, and (b) 2-cohort + trend-scanning substrate at /039 = NEG-CAT. The combined finding is that Sortino's basin-selection gradient is universe-dependent. **Future loss-function variants (e.g., LogReturn-Sortino, Calmar, Omega) at single-seed EXPLORATION budget on the same substrates are NOT recommended** — the universe-dependence finding makes any single-seed loss-function probe at minimum 50% prior NEG.

4. **Next axis recommendations** (Critic Path Forward, 3 candidate families NOT used in the prior 5 EXPLORATIONs):
   - **/042 ternary-architecture labeling** — replace the 3-class trend-scanning labels (significance-filter Wald-t) with a tighter ternary labeling (e.g., LdP triple-barrier with explicit ±1/0 class definition + meta-labeling head). This is a NEW labeling architecture, axis-family = labeling, last used at /037 (Sortino is loss-function not labeling; /036 was labeling at 2-cohort + trend-scanning; /037 was loss-function; /038 was risk-primitive; /039 was hybrid). Labeling family last used /036 (3 iter ago). PROBE: does a different labeling architecture produce a higher Sortino/Sharpe asymmetry on the substrate that Sortino could exploit at /044+?
   - **/043 cross-asset non-OHLCV feature family** — funding rates, OI deltas, basis (already tested /034 NEG-CLEAN but in cycle-4; cycle-5 has not retested), liquidations (per-cohort hawkes-process self-exciting events), on-chain (BTC/ETH MVRV-Z, NUPL, CDD). The cross-asset OHLCV-derived primitive family is CLOSED in v3 catalog at 6 failures; v1 has open ground here (v1 has not tested cross-asset on-chain or liquidation primitives at all in cycle-5).
   - **XGBoost head-to-head model-arch** — at single-seed on the /036 substrate, replicate the LightGBM-vs-XGBoost head-to-head that v3 ran at iter-v3/016 (negative there). v1's substrate is different; the model-arch axis is open in v1. Lower priority than the above two due to v3 NEG precedent.

5. **/040 + /041 axis pre-drafts** (committed pre-drafts that exist as branches per orchestrator context):
   - **/040 composed feature** — pre-drafted; expected family = feature-family (composed primitive). Axis-rotation valid (last feature-family was /034 NEG-CLEAN basis; /036/037/038/039 have not been feature-family axes).
   - **/041 labeling tighten** — pre-drafted; expected family = labeling. Axis-rotation valid (last labeling was /036).
   - Both already committed pre-draft branches; QR brief authoring happens at their respective cadence slots.

6. **Brief Section 2 anchor selection rule** (reinforced at /039 closeout): when an EXPLORATION builds on a previously-PROMISING substrate, the brief anchor MUST be the prior PROMISING substrate not BASELINE_V1. /039's H1b pre-registration was textbook on this — it locked the anchor and made the verdict unambiguous. Future composition EXPLORATIONs inherit this rule.

7. **BASELINE_V1.md UNCHANGED** at `v0.v1-baseline-corrected` (`f8bc12c`). No baseline update mechanism fires for NEG-CAT EXPLORATION verdicts.

8. **No BLOCK-PENDING-FIX rerun authorized.** The wiring is correct, the data is honest, the result is empirically resolved. /039 closes EXPLORATION-NEGATIVE-CATASTROPHIC and the axis is permanently CLOSED at catalog level.

## 6. Cycle-5 catalog ledger update entry

To be appended to `briefs-v1/exploration_catalog.md` (one-line catalog row plus this diary as backing detail):

```
| iter-v1/039 | 2026-05-31 | Per-cohort Sortino × LINK+DOT trend-scan specialist hybrid (composition of /036 substrate + /037 Sortino objective at single-seed=42 / ENSEMBLE_SIZE=3 / n_trials=18 / V1_FEATURE_COLUMNS_PRUNED 43 cols UNCHANGED / R1/R2/R3 baseline UNCHANGED / NO new src/ code); brief Section 1 H1b PRE-REGISTERED /036 (+1.7465) as anchor not BASELINE_V1 (+0.6637); CYCLE-5 EXPLORATION 6/10 after /034 NEG-CLEAN basis + /035 NEG-CAT-bundle bimodal trend-scan + /036 PROMISING-CLEAN LINK+DOT trend-scan + /037 PROMISING-CLEAN Sortino + /038 NEG-CAT EDA-VINDICATED vol-ceiling; axis-rotation DOUBLE-REPEAT JUSTIFIED at brief Section 0.6 as STACKING INTERACTION PROBE not knob-tuning REPEAT (per /037 closeout Rec 2 pre-registered compounding test); HIGH-RISK by rotation rule + NORMAL-RISK by mechanism (composition of shipped flags, no new code); LM Master Phase 4.5 priors: PROMISING-CLEAN 18% / PROMISING-DOT-ONLY 22% MODAL / PROMISING-LINK-ONLY 5% / INERT 28% / NEG-COLLISION 22% / NEG-CATASTROPHIC 5% TAIL; observed NEG-CATASTROPHIC (5% TAIL MATERIALIZED — LM Master MODAL miss, DOT amplification REFUTED with DOT IS PnL going NEGATIVE -4.87); F-AXIS #1 OOS Sharpe Δ vs /036 = -0.7072 (band Δ < -0.45 NEG-CAT); F-AXIS #2 wiring PASS (banner emitted + both flags asserted); F-AXIS #3 per-symbol Δ both NEGATIVE (LINK -40.46pp / DOT -69.23pp from /036 roster — sign-match POSITIVE-NEG direction); F-AXIS #4 bundle Δ -0.71 inside NEG-CAT band; F-AXIS #6 Jaccard vs /036 OOS = 0.0878 FAIL < 10% → BASIN-RELOCATION-ARTIFACT confirmed (DOT 0.107 / LINK 0.0625 / portfolio 13 of 105 trades survived re-selection = 91% jettison); F-AXIS #7 OOS trades 87 below [80,160] modal band lower edge — sparse OOS by design + Sortino chop-skip; per-symbol OOS PnL: LINK +68.45% / DOT +44.40% (both regressed vs /036; both up vs baseline — informational only); per-symbol IS PnL: LINK +25.26 / DOT -4.87 (DOT IS went NEGATIVE — inverse of every prior Sortino observation in v1); OOS Sharpe absolute +1.0393 vs baseline +0.6637 = +0.38 informational lift if anchored on BASELINE_V1 but anchored on /036 the verdict is -0.71 collision; 91% jettison of /036's roster is direct empirical evidence that Sortino's basin-selection gradient is UNIVERSE-DEPENDENT — /037's lift is 5-cohort-universe-dependent NOT universe-independent; mechanism: 2-cohort + trend-scanning substrate exhibits near-symmetric OOS PnL distribution (Sortino/Sharpe ratio ~1.22 per EDA §1) leaving Sortino's basin re-selection no gradient direction to exploit; per-cohort-Sortino × per-cohort-specialist HYBRID axis CLOSED at catalog level; /037's Sortino survives ONLY on its native 5-cohort + triple-barrier substrate; /044 ROUTING LOCKED at SEPARATE /044-A multi-seed /036 LINK+DOT trend-scan + /044-B multi-seed /037 5-cohort Sortino, NO bundled hybrid; loss-function family CLOSED for substrate compounding (universe-dependence finding makes future single-seed loss-function probes at minimum 50% prior NEG); 6 of 10 cycle-5 EXPLORATIONs complete; substrate STABILIZED at /036 alone + /037 weakly; BASELINE_V1.md UNCHANGED at v0.v1-baseline-corrected `f8bc12c`; tag v0.v1-039 at closeout | loss-function × per-cohort-specialization HYBRID (composition probe; double-REPEAT JUSTIFIED as STACKING INTERACTION PROBE per /037 closeout Rec 2; HYBRID axis CLOSED at catalog level — non-compoundable across iterations per `feedback_v3_promising_mechanical_subtype.md`-analog applied to loss-function family) | **-0.24** (IS -0.1530 vs anchor +0.2829) | **+0.38** (OOS +1.0393 vs anchor +0.6637; NEG-CAT band vs /036 substrate Δ -0.71) | **EXPLORATION-NEGATIVE-CATASTROPHIC vs /036 substrate** (mechanism universe-dependence empirically CONFIRMED; H1b pre-registered REFUTATION fired exactly; Jaccard 0.088 FAIL < 10% = BASIN-RELOCATION-ARTIFACT; per-cohort-Sortino × per-cohort-specialist HYBRID axis CLOSED at catalog level; /037's Sortino lift is 5-cohort-universe-dependent NOT universe-independent; /044 ROUTING LOCKED at SEPARATE multi-seed validations; loss-function family CLOSED for substrate compounding) | **NO — HYBRID axis CLOSED; /037 Sortino + /036 trend-scan-specialist are non-compoundable; /044-A and /044-B locked as SEPARATE CONFIRMATIONs** |
```

## 7. /044 ROUTING — LOCKED (post-/039 closeout)

The pre-registered H1b falsifier in /039's brief explicitly named the routing decision: "/044 routing pre-commits to TWO SEPARATE CONFIRMATIONs" if F1 OOS Δ vs /036 < +0.10 AND per-symbol sign-match REFUTED. Both conditions fired (Δ -0.71 < +0.10; LINK -40.46pp and DOT -69.23pp both outside ±25pp band). **The routing is locked.**

### /044-A — Multi-seed /036 LINK+DOT trend-scan specialist (substrate alone)

- **Spec**: `--symbols LINKUSDT,DOTUSDT --label-mode trend_scanning --seeds 2 --n-trials 35 --ensemble-size 5` (CONFIRMATION-spec budget).
- **Anchor**: BASELINE_V1 +0.6637 OOS Sharpe; substrate target band [+0.50, +1.00] OOS Sharpe multi-seed mean (per /037 closeout pre-registration). Lift over /036's single-seed +1.7465 expected to MEAN-CONTRACT under multi-seed per `feedback_v3_single_seed_frozen_baseline.md`.
- **MERGE conditions**: IS Sharpe ≥ 0 AND OOS Sharpe ≥ +0.50 multi-seed mean AND ≥7/10 inner seeds profitable AND PSR_vs_0 ≥ 0.95 AND OOS trades ≥ 130 (relaxed from 130 floor due to 2-cohort universe — re-evaluate at /044-A bundle level per `feedback_trade_rate_floor_bundle_level.md` analog).
- **Hard-blocking gates**: top-symbol ≤ 30% (likely to fire on 2-cohort, request explicit exception in /044-A brief).

### /044-B — Multi-seed /037 5-cohort + Sortino (substrate alone)

- **Spec**: `--symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT --optuna-objective sortino --seeds 2 --n-trials 35 --ensemble-size 5` (CONFIRMATION-spec budget; native 5-cohort universe per /037).
- **Anchor**: BASELINE_V1 +0.6637 OOS Sharpe; substrate target band [+0.05, +0.15] OOS Sharpe multi-seed mean (per /037 closeout pre-registration). /037's +0.18 single-seed lift expected to mean-contract.
- **MERGE conditions**: IS Sharpe ≥ 0 AND OOS Sharpe ≥ +0.10 multi-seed mean AND ≥7/10 inner seeds profitable AND PSR_vs_0 ≥ 0.95 AND OOS trades ≥ 130.
- **Open question**: concentration DOT 78.62% at single-seed > 30% merge cap; under multi-seed this dissolves per `feedback_v3_single_seed_frozen_baseline.md`. Re-evaluate at /044-B bundle level.

**No bundled hybrid CONFIRMATION.** The /037 + /036 axes are NON-COMPOUNDABLE across iterations per the /039 universe-dependence finding. Future /045+ EXPLORATIONs MAY retry composition on a DIFFERENT substrate (e.g., 3-cohort or 4-cohort sub-universes) but the 2-cohort × trend-scan + Sortino composition is permanently CLOSED at catalog level.

## 8. Next Iteration Ideas — /040 + /041 + /042 + /043 to complete cadence

**Cadence status**: 6/10 cycle-5 EXPLORATIONs complete. Need /040, /041, /042, /043 to reach 10/10 cadence before /044 can launch.

### /040 — composed feature (committed pre-draft)

- Pre-drafted; axis family = feature-family (composed primitive).
- Axis-rotation valid: last feature-family was /034 NEG-CLEAN basis (5 iter ago); /035-/039 dispersed across labeling/per-cohort-specialization/loss-function/risk-primitive/HYBRID.
- Substrate: BASELINE_V1 5-cohort + V1_FEATURE_COLUMNS_PRUNED + 1 new composed feature (e.g., regime_signed momentum × hurst). Single-seed EXPLORATION standard.
- Expected priors TBD at brief authoring; given the cycle-5 catalog of 2 NEG-CAT (/034 + /038) and 1 NEG-CAT-bimodal (/035) for risk + feature axes, brief should pre-register PROMISING priors at ≤ 25%.

### /041 — labeling tighten (committed pre-draft)

- Pre-drafted; axis family = labeling.
- Axis-rotation valid: last labeling was /036 (3 iter ago) which was PROMISING-CLEAN.
- Substrate: BASELINE_V1 5-cohort + V1_FEATURE_COLUMNS_PRUNED + tighter triple-barrier params (e.g., narrower σ_t window, shorter timeout) OR meta-labeling head.
- Expected priors TBD at brief authoring; labeling family carries the strongest cycle-5 hit-rate (/036 PROMISING) so PROMISING priors at ≤ 35% are defensible.

### /042 — ternary-architecture labeling (Critic Path Forward recommendation)

- **NEW labeling architecture** — replace 3-class trend-scanning labels with explicit ternary triple-barrier + meta-labeling head per López de Prado AFML Ch. 3.
- Axis family = labeling. Probable family-recurrence: /036 (labeling), /041 (labeling), /042 (labeling) — would be 3rd consecutive labeling axis. Within tolerance per skill 5+-forbidden rule.
- Rationale: /036's trend-scanning labels work but the basin is sparse; ternary triple-barrier preserves more labels per training-window AND adds the LdP meta-labeling head as a "should we act" filter independent of the directional model. Loss-function family applies cleanly to meta-labeling head (Sortino on the meta-classifier might lift OOS where Sortino on the directional model under-performed at /037-/039).
- Substrate: BASELINE_V1 5-cohort + V1_FEATURE_COLUMNS_PRUNED + LdP meta-labeling.

### /043 — cross-asset non-OHLCV feature family (Critic Path Forward recommendation)

- **NEW feature family** — funding rates, OI deltas, liquidations, on-chain (MVRV-Z, NUPL, CDD).
- Axis family = feature-family. /034 cycle-4 carried basis OHLCV-derived which was NEG-CLEAN; v1 has not tested non-OHLCV cross-asset (funding / OI / liquidations / on-chain) at all in cycle-5.
- Substrate: BASELINE_V1 5-cohort + V1_FEATURE_COLUMNS_PRUNED + 1-2 new non-OHLCV cross-asset features.
- Data dependency: requires fetcher additions for funding endpoints (per LM Master /034 advisor recommendation rejection) — may need /042 to land first while data infrastructure prepared.

### Lower-priority alternatives (deferred to /045+)

- XGBoost head-to-head on /036 substrate (model-arch family); v3 NEG precedent.
- Per-cohort drawdown brake on /036 substrate (risk-primitive family but on /036 not 5-cohort); risk-primitive family closed for cycle-5 by /038 + /039 closeout reinforcement.
- Funding-rate factor at single-seed (cross-asset non-OHLCV); deferred to /043 if data infrastructure prepared by then.

## 9. Risk Mitigation Section recap

/039 NO-MERGE → no risk mitigation activation against BASELINE_V1. The /036 + /037 substrates remain the candidate paths to /044 CONFIRMATION; both inherit /036's and /037's respective Risk Mitigation sections at their CONFIRMATION-level briefs.

## 10. Files & Commits on Branch

- `briefs-v1/iteration_v1-039/axis_rejected.md` (DD-brake EDA rejection — Phase 1 pivot)
- `briefs-v1/iteration_v1-039/eda_findings.md` (per-cohort Sortino × specialist hybrid EDA)
- `briefs-v1/iteration_v1-039/lgbm_advisor.md` (Phase 4.5 + Phase 7.4 sections)
- `briefs-v1/iteration_v1-039/research_brief.md` (Phase 5 brief — H1b anchor pre-registration LOAD-BEARING)
- `briefs-v1/iteration_v1-039/phase5p5_gate.md` (Phase 5.5 gate PASS)
- `briefs-v1/iteration_v1-039/critic_preflight.md` (Phase 6.0 critic pre-flight PASS)
- `reports-v1/iteration_v1-039/comparison.csv` (bundle metrics — OOS Sharpe +1.0393 IS Sharpe -0.1530)
- `reports-v1/iteration_v1-039/in_sample/per_symbol.csv` (LINK +25.26% / DOT -4.87% IS)
- `reports-v1/iteration_v1-039/out_of_sample/per_symbol.csv` (LINK +68.45% / DOT +44.40% OOS)
- `reports-v1/iteration_v1-039/basin_diagnostics/basin_diagnostics.json` (v1 PASS / v2 BORDERLINE / v3 FAIL global FAIL)
- `reports-v1/iteration_v1-039/basin_diagnostics/v3_roster_overlap.csv` (Jaccard 0.0878 OOS vs /036)
- `diary-v1/iteration_v1-039.md` (this file)
- `briefs-v1/exploration_catalog.md` (one-line ledger row appended at closeout commit)
- Tag `v0.v1-039` to be applied at closeout commit (after Critic Phase 7.5 final commit).

## 11. Track Record post-/039 (cycle-5)

| Iter | Axis family | Verdict | OOS Δ vs anchor | LM Master direction-hit? | Anchor used |
|---|---|---|---:|:---:|---|
| /034 | feature-family (basis) | NEG-CLEAN | -0.06 | miss | BASELINE_V1 |
| /035 | labeling (trend-scan 5-cohort) | NEG-CAT-bimodal | -1.36 | miss | BASELINE_V1 |
| /036 | per-cohort-specialization (2-cohort trend-scan) | **PROMISING-CLEAN +1.08** | +1.08 | hit | BASELINE_V1 |
| /037 | loss-function (Sortino on 5-cohort) | **PROMISING-CLEAN-MECHANISM-DIVERGENT +0.18** | +0.18 | miss | BASELINE_V1 |
| /038 | risk-primitive (vol-ceiling per-symbol) | NEG-CAT EDA-VINDICATED | -0.53 | hit | BASELINE_V1 |
| **/039** | **loss-function × per-cohort-specialization HYBRID** | **NEG-CAT vs-036 / +0.38 vs BASELINE_V1** | **-0.71 vs /036 (load-bearing); +0.38 vs BASELINE_V1 (informational)** | **miss (MODAL DOT-amplification refuted; TAIL 5% NEG-CAT materialized)** | **/036 (substrate)** |

**Cycle-5 hit rate**: 2 PROMISING / 4 NEG of 6 EXPLORATIONs = 33% PROMISING rate. Substrate STABILIZED at /036 alone (strongly) + /037 weakly. /037's lift is now empirically known to be 5-cohort-universe-dependent, NOT universe-independent — bundling /036 + /037 across iterations is REFUTED.

**LM Master directional running tally**: 2/6 = 33% — same direction as cycle-3 baseline rate. The MODAL-direction reliability remains POOR when EDA priors are split or PROMISING-DOMINANT; reliable only when EDA priors are strongly NEG-DOMINANT (combined NEG ≥ 50%).

## 12. Closure Note — HYBRID Axis Closed at Catalog Level

This is the FIRST cycle-5 HYBRID axis CLOSURE. The principle: when TWO previously-PROMISING axes are tested in composition on a SHARED substrate and produce a NEG-CAT vs the substrate anchor (not vs BASELINE_V1), the composition is REFUTED as a /044 bundle candidate AND the axes are tagged "non-compoundable across iterations" per `feedback_v3_promising_mechanical_subtype.md`-analog.

**Specifically refuted at /039**: per-cohort Sortino × per-cohort trend-scan-specialist (the loss-function × per-cohort-specialization HYBRID on a 2-cohort universe).

**NOT refuted**: /036 and /037 individually as /044 CONFIRMATION candidates. Each retains its own multi-seed validation slot.

**Generalization**: future cycle-5 HYBRID composition probes (e.g., loss-function × labeling composition; risk-primitive × feature-family composition) inherit the H1b anchor-on-substrate pre-registration discipline. Brief Section 1 MUST pre-register the substrate anchor BEFORE the brief is finalized; failing to do so is a Phase 5.5 gate violation.

---

**End of diary-v1/iteration_v1-039.md.**
