# iter-v3/097 — Cycle-4 EXPLORATION #5 — SYMBOL-UNIVERSE RE-SELECTION — FILED NEGATIVE (Section-8 class 8.2 NEGATIVE-no-transfer)

**Date**: 2026-05-18
**Type**: EXPLORATION (cycle-4 slot #5 of 10) — single-axis SYMBOL-UNIVERSE RE-SELECTION (`V3_MODELS` BCH/LDO/TRX → LDO/GALA/ADA)
**Critic OVERALL**: **EXPLORATION-NEGATIVE** (`briefs-v3/iteration_v3-097/review.md`, committed `0c31e35`) — a clean, methodologically-sound NEGATIVE. All 8 Critic checks PASS; no defect; DSR/PBO/PSR genuine; single-axis verified clean. The verdict is FINAL — the Critic was not re-run.
**Section-8 classification**: **8.2 NEGATIVE-no-transfer** (F1 first-fires under the brief's disjunctive precedence; F3 the named GALA falsifier additionally fires as compounding evidence).
**Decision**: **NO-MERGE.** BASELINE_V3.md UNCHANGED — canonical **`v0.v3-059`** (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**). The LDO/GALA/ADA re-anchor is **REJECTED**; /059's BCH/LDO/TRX universe stays canonical.
**Branch**: `iteration-v3/097`

---

## 1. What iter-v3/097 tested

iter-v3/097 was a SYMBOL-UNIVERSE RE-SELECTION — the sole axis was the `V3_MODELS` universe, re-anchored from the legacy BCH/LDO/TRX onto **LDO/GALA/ADA**. Everything else was /059-identical: the 14-feature `V3_FEATURE_COLUMNS_TOP_N` stack, the `(2.0, 1.0)`-ATR triple-barrier label, the 5-gate+BTC risk stack, the walk-forward refit, `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24`, `n_trials = 35`. EXPLORATION-mode single-seed=42, `ENSEMBLE_SIZE=3`, wall-clock 0.58h, exit 0.

The hypothesis (brief Section 1): the /096 EDA found feature→label IC is thin on BCH (+0.025) and TRX (+0.029) — two of three universe symbols carry no genuine signal — so the fix is to screen the broad 22-symbol universe on that exact within-symbol purged-CV rank-IC and re-anchor onto the symbols where the existing 14-feature stack already learns. The screen (committed EDA `f06eef7`, 22-symbol within-symbol CV-IC + a 4-seed robustness check) selected LDO (CV-IC +0.178, rank 1/22, seed-stable), GALA (+0.127, rank 2/22, the only OTHER GENUINE-band symbol, seed-stable), and ADA (the strongest seed-stable BORDERLINE third symbol, +0.053). This is a structural axis distinct from the closed universe-EXPANSION dead-path (/021/069/083/087): the count stays 3 — it is a REPLACEMENT, not a denominator-growth `√breadth` bet.

## 2. Result — worse than /059 on BOTH axes

Source: `reports-v3/iteration_v3-097/comparison.csv`.

| Metric | iter-v3/097 | /059 baseline | Δ vs /059 |
|---|---:|---:|---:|
| IS monthly Sharpe | **+0.7197** | +1.0894 | **−0.37** |
| OOS monthly Sharpe | **−0.3541** | +0.5791 | **−0.93 (sign flip)** |
| OOS/IS ratio | −0.4921 | 0.5316 | — |
| IS trades | 113 | 171 | −58 |
| OOS trades | 55 | 94 | −39 |
| frac_positive_paths (CPCV) | 0.511 | 0.6444 | −0.13 |

The re-anchored universe is worse than /059 on BOTH IS (−0.37) and OOS (−0.93, with an OOS sign flip from positive to negative). It clears no merge gate. Per `feedback_v3_strict_both_is_oos_baseline.md` (BOTH IS and OOS must improve to update the baseline), this is unambiguously NO-MERGE — and an EXPLORATION cannot update the baseline regardless of outcome.

## 3. The per-symbol picture — recorded honestly

Source: `reports-v3/iteration_v3-097/{in_sample,out_of_sample}/per_symbol.csv` (bit-faithful to the engineering report).

| Symbol | IS net PnL% | OOS net PnL% | Pattern |
|---|---:|---:|---|
| GALAUSDT | **+67.20** | **−18.50** | complete IS-up/OOS-down reversal — the /087 signature |
| ADAUSDT | **+46.96** | **−14.56** | IS-positive, OOS-negative |
| LDOUSDT | −11.44 | −15.80 | IS-negative and OOS-negative |

**All three symbols are negative OOS.** The IS→OOS inversion is complete: every symbol that was IS-positive (GALA +67.20, ADA +46.96) inverted to OOS-negative; LDO — the genuine-signal anchor kept from /059 — was negative on both windows in this single-seed run (a single-seed EXPLORATION artifact at n_trials=35 on LDO's thin 581-row IS panel; LDO's IS book at /059 was +0.89% — near-flat, not a reliable carrier either). The IS book here was carried by GALA+ADA — the exact inverse of /059, where LDO was the named signal carrier and BCH carried the OOS book.

**GALA reproduced its /087 reversal exactly.** GALA was added to the v3 universe once before, at iter-v3/087, where its per-symbol model scored +67.2% IS → −19.0% OOS. iter-v3/097's GALA: **+67.20% IS → −18.50% OOS** — the same sign reversal, near-identical magnitude. The brief did not hide this: Section 7.1 named the /087 GALA reversal as the central, specific, pre-registered risk, and Section 4.3 gave it its own named falsifier (F3). F3 fired exactly as designed.

## 4. The Phase-7 failure-mode-prediction check — CLEAN

Brief Section 7.3 pre-registered the predicted most-likely failure mode: **F3** — "GALA's genuine IS CV-IC failing to transfer to OOS per-symbol `weighted_pnl` (the /087 reversal recurring)" — named as the single most-likely failure, with F1 (loss of BCH's large /059 OOS contribution outweighing GALA/ADA additions) the second most-likely.

The realized outcome matches the pre-registration **on both counts**:
- **F3 fired** — GALA IS-positive (+67.20) / OOS-negative (−18.50): the named #1 predicted failure mode, the /087 reversal, recurred.
- **F1 fired** — OOS monthly Sharpe −0.3541 < +0.40: the named #2 predicted failure mode also realized; the re-selection did not transfer to OOS.

There is no post-hoc rationalization. Every falsifier that fired (F1, F2, F3, F5, F6) was a LOCKED numerical gate with an exact threshold set before Phase 6. The Section-8 disjunctive precedence resolves: 8.0 (F0) no → 8.1 (F4 / OOS-soars-on-flat-IS) no → **8.2 NEGATIVE-no-transfer fires first** (F1). The QE's classification of 8.2 is correct and the Critic's falsifier cross-audit (review §"Falsifier Cross-Audit") confirms all six QE evaluations bit-faithful to the committed CSVs. This is a clean, fully pre-registered NEGATIVE: a genuine, seed-stable, cross-validated IS feature→label IC (GALA +0.127, ADA +0.053) **did not predict OOS per-symbol PnL** — the precise IC-vs-OOS caveat the brief pre-registered in Sections 2.7 and 4.2. The brief said the IC screen is necessary-but-not-sufficient; iter-v3/097 confirmed it empirically.

## 5. The methodology read — symbol-screening as a lever is empirically exhausted

The Critic's Recommendation 2 states the structural finding plainly, and it is the central forward-facing lesson of this iteration. iter-v3/097 confirms what Sections 2.7 / 4.2 hypothesized: GALA's +0.127 within-symbol purged-CV rank-IC (seed-stable across 4 LightGBM seeds) did NOT transfer to a positive OOS per-symbol `weighted_pnl`, and neither did ADA's +0.053. **A genuine, cross-validated, seed-stable feature→label IC is not predictive of OOS per-symbol PnL in the v3 per-symbol framing.**

Three distinct universe families have now failed:
- **universe EXPANSION ×4** — /021 (+HBAR+AVAX), /069 (+ADA), /083 (+FIL), /087 (+GALA+MANA+SAND) — every one ADDED weak symbols; all NEGATIVE (the closed 4-failure axis in BASELINE_V3.md).
- **revision-by-swap** — the /096 pooled-model line and prior swaps.
- **this RE-SELECTION** — /097, screening on the exact within-symbol CV-IC metric, also NEGATIVE.

The IC screen was the explicit tool the /083 closeout said prior expansions lacked — and even with that tool, the re-selection failed. The 2-symbol LDO+GALA / LDO+ADA fallbacks named in brief Section 4.4 are likely to inherit the same non-transfer (the Critic flags this directly), so they are NOT pursued. **The conclusion: do not spend the next iteration on another universe permutation.** The binding constraint is the signal/label and the feature space, not which 3 symbols are in `V3_MODELS`.

## 6. The Critic's 3 Recommendations — integrated

The Critic (review §"Recommendations to QR") returned three process items. The verdict is final; these inform the next iteration:

1. **Commit every brief-named artifact.** Brief Section 9.2 mandated `analysis/iteration_v3-097/roster_diff_oos.py` as a committed reproducible F0-verification script; Phase 6 skipped it. Here F0 was structurally non-fireable (GALA+ADA contribute 43/55 OOS trades = 78%, both ABSENT from /059 — >50% OOS roster overlap is arithmetically impossible), so the skip caused no harm — but a future iteration where F0 *could* fire would have no reproducible roster-diff to adjudicate the NULL-vs-NEGATIVE branch. **Forward rule: either every brief-named artifact is committed in Phase 6, or the Phase 5.5 gate explicitly down-scopes artifacts that are provably unnecessary, so the brief and the delivered build agree.** This compounds the standing `feedback_v3_gate_flags_become_hard_tests.md` lesson — a brief-named deliverable should be a build-contract item, not advisory text.

2. **Symbol-screening as a lever is empirically exhausted — pivot to features.** (See Section 5 above.) A genuine seed-stable IS feature→label IC does NOT predict OOS per-symbol PnL in the v3 per-symbol framing; three universe families have failed. The next iteration must NOT be another universe permutation — it pivots to the directed feature-expansion axis (Section 7). This recommendation aligns exactly with the user's 2026-05-18 directive that FEATURES are the crucial lever.

3. **Separate the falsifier threshold from the predicted-band edge.** F1 was set at +0.40 — the exact lower bound of the brief's predicted OOS band [+0.4, +1.3], with zero margin. The observed −0.35 fired F1 by a wide margin so it did not matter here — but a result landing at +0.41 would have been a non-falsified PROMISING on a prediction the band itself called the floor. **Forward rule: future briefs must separate the falsifier threshold from the predicted-band edge by a stated margin, so a marginal result is unambiguous.** This is a binding pre-registration-discipline item for the /098 brief and every brief after it.

## 7. Next Iteration — iter-v3/098 = FEATURE EXPANSION

Per the user's 2026-05-18 directive (`feedback_v3_bold_research_mandate.md`, verbatim: "the features are crutial ... work on the features based on 8h candles. Plenty of work to be done") AND the Critic's Recommendation 2 (symbol-screening is exhausted — pivot to features), **iter-v3/098 is the feature-expansion iteration.** It is cycle-4 EXPLORATION slot #6 of 10; the cadence advances.

### 7.1 — The /098 axis: a genuine feature expansion

iter-v3/098's single axis is **FEATURES** — replace/augment the thin 14-feature `V3_FEATURE_COLUMNS_TOP_N` stack with a materially larger, better feature set. v3 has run the same 14 price-derived features since /007; the /096 EDA showed they carry thin (~+0.025) signal on BCH/TRX. The feature set is the binding constraint the Critic Rec 2 and the user directive both point at.

The /098 QR has a prepped candidate catalogue — `briefs-v3/iter098_feature_research_memo.md` (preparatory research, ~60 researched candidate features across 8 families: order-flow/microstructure, volatility estimators, momentum/oscillators, statistical/complexity/entropy, jump/tail decomposition, cross-asset/BTC-relative, funding/OI/basis, calendar). **The standout finding: the 8h klines carry `taker_buy_volume` and `trades` columns that ALL 14 incumbent features ignore** — a directly-observed signed-order-flow signal (Binance `taker_buy_volume` is the aggressor-buy volume, a real signed-flow proxy, not a tick-rule estimate; grounded in Kyle 1985 / Amihud 2002 / the VPIN literature). That order-flow family (Family A in the memo) is the highest-conviction candidate: genuine *new information* from unused kline columns, LOW redundancy vs the 14 incumbents, zero data-fetch cost. The /098 QR owns the final shortlist via its own Phase-1 IS-only EDA.

Note: order-flow has been catalogued before only as a *non-OHLCV crypto-native feed* (the 7-FEED INERT verdict; /094 NO-GO on order-flow-as-directional-alpha). The /098 framing is different — the order-flow signal here is the **per-kline `taker_buy_volume`/`trades` columns that are already in every `data/<SYM>/8h.csv`**, used to engineer price+volume features, not a separate cache. The /098 QR must weigh the 7-FEED prior honestly (the memo does so in §8) and design accordingly.

### 7.2 — The universe for /098: BCH/LDO/TRX (NOT a universe axis)

iter-v3/097's LDO/GALA/ADA re-anchor is REJECTED. **/098's canonical universe is /059's BCH/LDO/TRX** — the canonical baseline universe at `v0.v3-059`. Per the Critic's Recommendation 2, **/098 does NOT touch the universe** — there are no more universe permutations. /098's single axis is FEATURES. This keeps /098 a clean single-axis iteration: the universe is held at the /059 canonical so the Phase-7 feature read is unconfounded.

### 7.3 — THE BINDING DESIGN CONSTRAINT for /098: feature selection must be OOS-robust, NOT IS-CV-IC-ranked

This is the **critical methodology caveat** /098 must heed, and it is flagged here as the binding design constraint for the /098 QR's own Phase 1-5:

The Critic's Recommendation 2 establishes — empirically, at /096 and now confirmed at /097 — that **a genuine, seed-stable IS feature→label IC does NOT predict OOS in the v3 per-symbol framing.** /096 showed cross-symbol IC transfer CIs straddle zero; /097 showed within-symbol seed-stable CV-IC (GALA +0.127) does not predict OOS per-symbol PnL. A naive IS-CV-IC ranking is *exactly* the selection method that /096 and /097 demonstrated fails — it produces features that look strong IS and go flat or invert OOS (the IS-up/OOS-flat trap).

**Therefore /098's feature SELECTION must be designed to be OOS-robust — it must NOT be a naive IS-CV-IC ranking.** The /098 QR (in its own Phase 1-5) must explicitly address *how* features are selected so /098 does not repeat the IS-up/OOS-flat trap. Concretely, the /098 QR should:
- Use **multivariate** contribution screening (cluster-MDA, paired-bootstrap ΔSharpe) — never univariate Spearman / univariate IC ranking (the iter-v2/070 −38% lesson, reinforced now by /096/097). The prepped memo §10 already mandates this.
- Treat IS-CV-IC as, at most, a *necessary* pre-filter — never as the sufficient selection criterion. The selection criterion itself must have an OOS-robustness property: stability across regimes/sub-periods, low redundancy vs incumbents (the |IC|<0.7 gate), and a genuine *new-information* basis (the order-flow columns the incumbents ignore is the clearest example of new information, as opposed to a feature that merely re-expresses what the 14 incumbents already encode).
- Heed the `feedback_v3_inert_features_at_higher_budget.md` lesson — an INERT feature added at higher Optuna budget actively HARMS OOS; the screen must be able to *reject*, not just rank.
- Heed the `feedback_v3_mass_feature_expansion.md` amendment — mass expansion is attempted *either* phased (3-5 features/EXPLORATION, validated individually) *or* full only at multi-seed CONFIRMATION with `n_trials ≥ 100`; the naive 14→46 single-seed mass swap was falsified at /063. The /098 QR owns the phased-vs-mass call with its own EDA.

**This is the binding constraint: /098 cannot select features by IS-CV-IC rank. The whole point of /096/097's NEGATIVE results is that IS-IC does not predict OOS. /098's design must answer "how are features selected so the OOS trap is avoided" before it earns a backtest.** Per `feedback_v3_axis_selection_quant_discipline.md`, the /098 QR commits an IS-only EDA-driven quantitative basis (`analysis/iteration_v3-098/*.py`) BEFORE the brief, and the brief's Section 2 must contain the EDA-derived numerical tables justifying the selection method.

### 7.4 — The cycle-4 lever after /098: pooled-vs-single models

The third forward lever named in the user's 2026-05-18 directive — **pooled (cross-symbol) vs single (per-symbol) models** — is the cycle-4 lever AFTER /098. The /096 pooled-model EDA returned NO-GO on the *legacy thin* BCH/LDO/TRX universe (cross-symbol transfer CIs straddle zero, only 4/14 features sign-consistent across symbols). The honest reading: a pooled model is worth re-examining only once /098 has established a richer, OOS-robust feature set on which cross-symbol transfer might genuinely hold — pooling cannot manufacture transfer that the feature space does not support. So the sequence is: **/098 = features first, then a pooled-vs-single re-test on the /098 feature set.** This is recorded as the directed cycle-4 follow-on; /098's QR should name it in its own Section 10 forward plan.

## 8. Commit chain

- Setup commit SHA: `e6ed662` — `feat(iter-v3/097): V3_MODELS → LDO/GALA/ADA + 6-test integration suite`.
- EDA SHA: `f06eef7` — `analysis/iteration_v3-097/symbol_universe_screen_eda.py` + `seed_robustness_check.py` + T1-T6 CSVs.
- Brief: `briefs-v3/iteration_v3-097/research_brief.md` (the 10-section research brief).
- Engineering report: `briefs-v3/iteration_v3-097/engineering_report.md` (Phase 6, committed `540c5cd`).
- Critic review SHA: `0c31e35` — `briefs-v3/iteration_v3-097/review.md` (Phase 7.5, OVERALL=EXPLORATION-NEGATIVE).
- Diary SHA: this closeout — `docs(iter-v3/097): closeout diary + catalog row — FILED NEGATIVE (8.2 NEGATIVE-no-transfer)`.
- **Tag**: `v0.v3-097` (annotated closeout marker; NOT a baseline update — the `v0.v3-082`…`v0.v3-096` pattern; BASELINE_V3.md UNCHANGED at `v0.v3-059`).

iter-v3/097 is cycle-4 EXPLORATION slot #5 of 10; the cadence advances. iter-v3/098 is slot #6 — the FEATURE-EXPANSION iteration (Section 7).
