# iter-v3/091 — Cycle 3 #10 EXPLORATION (FINAL cycle-3 EXPLORATION) — the MODEL-FREE CROSS-SECTIONAL MOMENTUM BOOK: parameter-free trailing-21-bar-return scoring / CONSTRUCTION-FALSIFIED / Critic Phase-7.5 OVERALL=MERGE (clean NEGATIVE, FILE)

**Date**: 2026-05-17
**Type**: EXPLORATION (cycle 3 slot #10 of 10 — the FINAL cycle-3 EXPLORATION) — a SCORING-FUNCTION axis on the RETAINED /088 cross-sectional `LGBMRanker` architecture + the /089 cost-aware construction. Single-axis: the cross-sectional scoring function — replace the trained `LGBMRanker` prediction with a **parameter-free trailing-21-bar-return cross-sectional score** (a model-free cross-sectional momentum book); the /089 cost-aware quintile long-short construction RETAINED verbatim. Two correctness/instrumentation SETUP items accompany the axis (the walk-forward embargo bug fix; the gross-Sharpe runner artifact) — neither a second edge axis. EXPLORATION-mode; the primary model-free book has no Optuna and no seed (deterministic); the reference `LGBMRanker` comparator runs single-seed (seed=42), `ensemble_size=1`, `--n-trials 35`, 22-symbol panel. Wall-clock 0h 24m 40s (model-free book ~45s; reference book ~24m).
**Verdict**: **Critic Phase-7.5 OVERALL = MERGE** — `briefs-v3/iteration_v3-091/review.md`, committed `d686b41`. This is the EXPLORATION "file the closeout" verdict: "MERGE" is the orchestrator-routing token meaning the iteration is methodologically clean enough to record as a NEGATIVE — it is NOT a baseline merge. /091 does NOT update BASELINE_V3.md; /059 stays canonical. The Critic was NOT re-run; the verdict is FINAL.
**Classification**: **CONSTRUCTION-FALSIFIED** (brief Section 8.2) — F1 (OOS net monthly Sharpe ≤ /089's −0.0985) AND F2 (OOS gross monthly Sharpe ≤ /089's +0.1717) both FIRE.
**Decision**: **NO-MERGE.** The model-free scoring function reverts to the trained `LGBMRanker` for any future cross-sectional work. The cross-sectional architecture + `cross_sectional.py` infrastructure + the 22-symbol `XS_UNIVERSE` + the /089 cost-aware construction are RETAINED (8.2 falsifies only the /091 scoring change, not the architecture — the /088/089 OOS rank-IC stands; the /091 model-free book itself has OOS rank-IC +0.014 > 0).
**BASELINE_V3.md**: **UNCHANGED** — canonical /059 metrics (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791), tag `v0.v3-059`. An EXPLORATION never updates the baseline regardless of classification.
**Branch**: `iteration-v3/091`

---

## 1. What was done — the model-free cross-sectional scoring axis

iter-v3/091 is the TENTH and FINAL EXPLORATION slot of v3 cycle 3 and the next build on /088's RETAINED `cross_sectional.py` infrastructure. The single edge axis is the **cross-sectional scoring function**: the score that feeds the /089 cost-aware quintile long-short construction changes from the trained `LGBMRanker` prediction to a **parameter-free trailing-`H`-bar return** — `score(sym, ts) = close(sym, ts) / close(sym, ts − H·interval) − 1`, with `H = 21` (~7 days, the literature weekly cross-sectional-momentum horizon). The /089 cost-aware construction — quintile legs (`XS_QUANTILE_FRAC = 0.20`), inverse-vol weighting, portfolio vol-targeting, overlapping `H`-bar holds, the no-trade band (`XS_NO_TRADE_BAND = 0.020`), the HARD turnover ceiling (`XS_TURNOVER_CEILING = 0.138`) — is RETAINED verbatim. Only the score changes.

Six changes vs /090 (the axis + the SETUP items):
1. **The /091 edge axis** — `score_mode` parameter added to `run_cross_sectional_backtest` (default `"trained"`, preserving /088/089/090). `score_mode == "model_free"` computes `mom_wide.loc[ts]` (the trailing-21-bar return) as the score and SKIPS `_train_for_month` — no model, no Optuna, no seed.
2. **`XS_HORIZON` / `XS_HOLD_BARS` 3 → 21** — the model-free book's trailing-return lookback IS its hold; horizon-matched.
3. **`XS_REQUIRED_GAP` 88 → 484** — the mechanical consequence `(H+1)×N = (21+1)×22`.
4. **SETUP item 1 (CORRECTNESS) — the walk-forward embargo bug fix.** The Phase 5.5 gate BLOCKed the prior /091 draft for a walk-forward embargo bug: `embargo_ms = XS_REQUIRED_GAP × interval_ms` over-embargoed by `N = 22×`. Fixed to `embargo_ms = (XS_HORIZON+1) × interval_ms` at both `cross_sectional.py:998` and `run_cross_sectional_v3.py:915`. NOT an edge axis.
5. **SETUP item 2 (INSTRUMENTATION) — the gross-Sharpe runner artifact** (the Critic /090 Rec #1 mandate). `gross_monthly_sharpe` (IS + OOS) now emitted to `comparison.csv` and `dsr.json` via ONE shared `_monthly_sharpe(sub, pnl_col)` helper — the identical per-calendar-month code path as the net `monthly_sharpe`. Closes the /090 BLOCK root cause. NOT an edge axis.
6. **The /090 feature expansion REVERTED** — `expand_downside=True → False`; `XS_FEATURE_COLUMNS` back to the 13-feature base. A revert, not a new axis (the model-free book uses no feature stack at all; the revert matters only for the reference `LGBMRanker` comparator and for not leaving the /090-FALSIFIED features in `src`).

The runner emits a **dual book**: the model-free book is the /091 primary (`reports-v3/iteration_v3-091/`); the trained `LGBMRanker` runs on the identical panel/construction as a reference comparator (`reports-v3/iteration_v3-091/reference_lgbmranker/`).

### 1.1 — The /091 design history — the honest record

iter-v3/091's design path was not a straight line, and the closeout records it honestly:

1. **The original /091 brief** proposed a holding-horizon extension of the trained `LGBMRanker` (`XS_HOLD_BARS` 3→21) — the axis the /090 closeout RECOMMENDED.
2. **The Phase 5.5 gate (`c56c457`, OVERALL=BLOCK) caught a real walk-forward embargo bug** in `cross_sectional.py` — `embargo_ms` was computed as `XS_REQUIRED_GAP × interval_ms`, over-embargoing the walk-forward training window by `N = 22×`. The bug was harmless at the /088/089/090 H=3 runs (a too-wide embargo is over-conservative, never leaking) but at H=21 it would consume ~160 days of the 24-month training window.
3. **The EDA was re-worked with the embargo fixed.** The corrected `holding_horizon_eda.py` then surfaced a finding the horizon-extension brief did not exploit: at the weekly horizon a *parameter-free* trailing-return cross-sectional sort beats the trained `LGBMRanker` by a wide IS net spread margin. A confirming focused EDA (`model_free_vs_ranker_eda.py`) corroborated it.
4. **The QR pivoted the /091 axis** from horizon-extension to the model-free scoring function, per `feedback_v3_axis_selection_quant_discipline.md` (the axis follows the EDA). The brief was re-written; the Phase 5.5 gate was re-run (`905b6c8`, brief SHA `9d3d525`, OVERALL=PASS).

This is the design history a top-quant-firm closeout records without varnish: a Phase 5.5 gate caught a genuine bug, the EDA re-work changed the conclusion, and the axis was re-pointed at the evidence. The pivot was disciplined. **But — see Section 4 — the re-worked EDA itself carried an IS-window-mismatch fidelity flaw that the brief, the Phase 5.5 gate, and the QE engineering report all missed.** Both facts are true and both are recorded.

---

## 2. Results — the model-free book is near-breakeven IS and net-negative OOS

iter-v3/091 produces a market-neutral cross-sectional long-short book; per the /088/089/090 brief Section 4.1 it is **not directly comparable** to the per-symbol-book Sharpes of the /059 CONFIRMATION baseline (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791) — a different return distribution, beta, turnover. The operative evaluation is the absolute floors + the architecture-internal diagnostics + the /089-specific HARD turnover gate, and a Δ vs the honest internal anchor — the /089 cross-sectional book.

### 2.1 — The model-free primary book

| Metric | iter-v3/089 (trained `LGBMRanker` cross-sectional book) | iter-v3/091 (model-free cross-sectional book) | Δ vs /089 |
|---|---:|---:|---:|
| IS monthly Sharpe (NET) | −0.1960 | **+0.0170** | +0.2130 |
| OOS monthly Sharpe (NET) | −0.0985 | **−0.0995** | −0.0010 |
| **IS gross monthly Sharpe** | +0.0925 | **+0.1170** | +0.0245 |
| **OOS gross monthly Sharpe** | +0.1717 | **−0.0178** | **−0.1895** |
| OOS/IS net monthly Sharpe ratio | 0.502 | −5.85 (negative — IS+/OOS−) | — |
| IS turnover/bar | 0.1153 | **0.0268** | −0.0885 (−77%) |
| OOS turnover/bar | 0.0710 | 0.0180 | — |
| **HARD turnover gate (≤ 0.138)** | PASS (0.1153) | **PASS (0.0268)** | — |
| OOS rank-IC (mean) | +0.0279 | **+0.0142** | −0.0137 |
| frac_positive_paths (CPCV, IS) | 0.356 | **0.489** | +0.133 |
| IS MaxDD | 7.4775 | 1.4835 | tighter |
| OOS MaxDD | 2.7614 | 1.5610 | tighter |
| max OOS symbol concentration | ICPUSDT 12.18% | HBARUSDT 14.84% | — |
| IS n_trades | — | 68,372 | — |
| OOS n_trades | — | 27,025 | — |

**The headline read.** The model-free book is near-breakeven IS (net monthly Sharpe +0.0170) and **net-negative OOS (−0.0995)**. The 21-bar overlapping hold cut IS turnover/bar to 0.0268 — a 77% reduction vs /089's 0.1153, far inside the 0.138 HARD gate — exactly as designed. But the OOS book did not turn net-positive: OOS net −0.0995 is essentially at /089's −0.0985 anchor (Δ −0.0010, a marginal *worsening*), and the **OOS gross monthly Sharpe COLLAPSED to −0.0178** — net-negative gross, a −0.1895 fall from /089's +0.1717. The model-free score did not strengthen the gross signal OOS; it produced a net-negative gross book OOS. The OOS rank-IC is faintly positive (+0.0142 > 0) — the trailing-momentum score's prediction rank does still correlate weakly with the realised 21-bar-forward cross-sectional rank — but the realised long-short book lost gross.

### 2.2 — The reference `LGBMRanker` comparator — a single-seed inversion artifact

| Metric | reference `LGBMRanker` book (`reference_lgbmranker/`) |
|---|---:|
| IS monthly Sharpe (NET) | −0.1107 |
| OOS monthly Sharpe (NET) | **+0.4613** |
| IS gross monthly Sharpe | −0.0435 |
| OOS gross monthly Sharpe | +0.4868 |
| OOS/IS net monthly Sharpe ratio | **−4.17** |
| OOS rank-IC (mean) | +0.0306 |
| frac_positive_paths (CPCV, IS) | 0.356 |
| n_trials (Optuna) | 35 |

The reference `LGBMRanker` book shows IS-negative / OOS-positive — an IS/OOS ratio of −4.17. **This is a single-seed comparator artifact, NOT a /091 finding, and the closeout records it as such (Critic Scrutiny Item 4).** Three reasons it does not escalate: (a) the reference book runs at the EXPLORATION single-seed (`seed=42`, `ensemble_size=1`, `n_trials=35`) and v3 has a documented single-seed-inversion precedent (`feedback_v3_engineered_features_dont_stack.md`, iter-v3/026/027); (b) it shares the identical /089 cost-aware construction with the model-free book, which does NOT invert (model-free IS +0.0170 / OOS −0.0995, same-sign-ish) — so the construction is not the cause; the trained model's Optuna single-seed lottery is; (c) the reference book's `frac_positive_paths` is 0.356 — sub-0.5, IS-weak, consistent with a noisy single-seed fit that drew a lucky OOS window. The reference book is the comparator, not the /091 strategy — the /091 strategy is the model-free book.

**This single-seed lottery draw must NOT be cited as evidence the trained `LGBMRanker` "works."** The honest cross-sectional record stands: across /088→/091 the trained ranker has produced no multi-seed-validated net-positive OOS book. The reference book's OOS +0.4613 is one single-seed draw; the model-free book's OOS −0.0995 is deterministic. The /092 (or cycle 4) must treat the reference book as an artifact.

### 2.3 — Per-symbol attribution — diversification is structural

OOS concentration (model-free book): HBARUSDT the largest profit at +0.0259 weighted_pnl / 14.84%; GALAUSDT the largest loss at −0.0155 / 8.88%; no single symbol exceeds 15% of the OOS book. F5 (no single symbol > 50% of OOS PnL) PASSES decisively. The quintile dollar-neutral construction delivers the structural diversification it was designed for — and unlike the /059 per-symbol baseline (BCH 95.76% IS concentration), the cross-sectional book has no single-symbol fragility flag. HBARUSDT is the *only* net-positive top contributor; the loss is spread across GALA/LDO/ICP/RUNE (8.9%/8.6%/8.0%/7.3%). The construction's *diversification* worked; its *profitability* did not.

---

## 3. PATH classification — CONSTRUCTION-FALSIFIED — the disjunctive-precedence walk

The brief Section 8 LOCKED taxonomy runs in disjunctive precedence, first match canonical: **8.1 SUSPICIOUS → 8.2 CONSTRUCTION-FALSIFIED → 8.3 CONSTRUCTION-VALIDATED-PROMISING → 8.4 CONSTRUCTION-PARTIAL → 8.5 NULL/INCONCLUSIVE.** The pre-registered falsifiers, anchored on /089's documented OOS figures (OOS gross +0.1717, OOS net −0.0985):

| Falsifier | Gate | Observed | Verdict |
|---|---|---:|---|
| F1 — OOS net monthly Sharpe ≤ /089's −0.0985 | OOS net > −0.0985 | OOS net = −0.0995 | **FIRES** (marginal, Δ −0.0010) |
| F2 — OOS gross monthly Sharpe ≤ /089's +0.1717 | OOS gross > +0.1717 | OOS gross = −0.0178 | **FIRES** (substantial, Δ −0.1895) |
| F3 — IS mean gross turnover/bar > 0.138 | IS turnover ≤ 0.138 | IS turnover = 0.0268 | PASS |
| F4 — OOS rank-IC ≤ 0 | OOS rank-IC > 0 | OOS rank-IC = +0.0142 | PASS |
| F5 — single symbol > 50% OOS PnL | max conc ≤ 50% | HBARUSDT 14.84% | PASS |

### 3.1 — 8.1 SUSPICIOUS — evaluated FIRST, does NOT fire

8.1 fires on EITHER (a) OOS net monthly Sharpe / IS net monthly Sharpe **> 3.0** (the OOS-soars-on-flat-IS signature — N/A if IS is negative), OR (b) OOS rank-IC ≥ 2× the model-free book's IS rank-IC magnitude, OR (c) OOS gross monthly Sharpe ≥ 3× /089's +0.1717 (i.e. ≥ +0.515). **(a) does not fire** — OOS net / IS net = −0.0995 / +0.0170 = **−5.85**, a *negative* ratio (the SUSPICIOUS signature is OOS soaring on a flat-or-positive IS — here OOS is negative, the 8.1(a) N/A case). **(b) does not fire** — OOS rank-IC +0.0142 is not ≥ 2× the model-free book's own IS rank-IC. **(c) does not fire** — OOS gross −0.0178 is not ≥ +0.515; it is net-negative. **SUSPICIOUS does NOT fire.** (The Critic confirmed this independently — review Scrutiny Item 4: "model_free OOS net/IS net = −0.0995/+0.0170 = −5.85 (negative ratio, the 8.1(a) N/A case); model_free OOS rank-IC +0.0142 is not ≥ 2× its own IS rank-IC; model_free OOS gross −0.018 is not ≥ 3× +0.1717.")

### 3.2 — 8.2 CONSTRUCTION-FALSIFIED — FIRES, and is canonical

8.2 fires if (NOT SUSPICIOUS) AND **F3 fires (IS turnover > 0.138) OR F1 fires (OOS net ≤ −0.0985) OR F2 fires (OOS gross ≤ +0.1717)**. NOT SUSPICIOUS holds (3.1). **F1 FIRES** — OOS net monthly Sharpe −0.0995 ≤ /089's −0.0985 (the model-free score did not improve the net OOS book vs the /089 `LGBMRanker` predecessor). **F2 FIRES** — OOS gross monthly Sharpe −0.0178 ≤ /089's +0.1717 (the model-free score did not strengthen the gross signal OOS — it produced a net-negative gross book OOS). The disjunction is satisfied twice over. **8.2 CONSTRUCTION-FALSIFIED FIRES — the /091 model-free-scoring hypothesis is falsified for the cycle. NO-MERGE.** The scoring function reverts to the trained `LGBMRanker`; the cross-sectional architecture and `cross_sectional.py` infrastructure are RETAINED (8.2 falsifies only the /091 scoring change — the /088/089 OOS rank-IC stands, and the /091 model-free book's own OOS rank-IC +0.0142 is faintly positive).

The two-fire is a strong, robust verdict. F1 alone is marginal (Δ −0.0010, within the precision of 15-month OOS Sharpe estimation) — but F2 is decisive: the OOS gross book is net-NEGATIVE (−0.0178), a −0.1895 fall from /089's +0.1717. There is no ambiguity about the direction: the model-free score did not produce a stronger OOS book.

### 3.3 — 8.3 / 8.4 — do NOT fire

Both 8.3 (CONSTRUCTION-VALIDATED-PROMISING) and 8.4 (CONSTRUCTION-PARTIAL) require, as a necessary conjunct, **OOS gross monthly Sharpe > /089's +0.1717 AND OOS net monthly Sharpe > /089's −0.0985**. Both fail: OOS gross −0.0178 ≤ +0.1717, OOS net −0.0995 ≤ −0.0985. Neither 8.3 nor 8.4 can fire. (8.2 also matches first under disjunctive precedence.)

### 3.4 — 8.5 NULL/INCONCLUSIVE — does NOT fire

8.5 fires only if the Phase-6 build did not reach a runnable cross-sectional backtest. The /091 build ran in full — `comparison.csv`, per-symbol attribution, `cpcv_paths.csv` (non-degenerate, 45 paths, `frac_positive_paths` 0.489), `rank_ic.csv`, `dsr.json`, both the model-free book and the reference comparator — exit status 0. 8.5 does NOT apply.

**The canonical classification is CONSTRUCTION-FALSIFIED (8.2).** This converges with the Critic's expectation — review Recommendations preamble: "The /091 result is a clean NEGATIVE — CONSTRUCTION-FALSIFIED (brief 8.2: F1 and F2 both fire) — and the diary should file it as such."

---

## 4. The Critic's key finding — the EDA-vs-runner IS-window mismatch (a Phase-1-5 EDA-fidelity flaw)

This is the load-bearing process finding of the /091 closeout, and the QR owns it explicitly. **It is the analogue of the /090 BLOCK lesson — but it is a Phase-1-5 flaw, not a Phase-6 defect, and it is NOT BLOCK-class.**

### 4.1 — The anomaly and the Critic's root cause

The QE engineering report's Anomaly Note 3 flagged a gap: the committed /091 EDA predicted IS gross monthly Sharpe ~+0.30 for the model-free book (the brief's headline `M1_model_free_H21_net_spread_monthly_sharpe = 0.2964`); the runner produced IS gross +0.1170 and IS net only +0.0170. The QE hypothesized the gap was a construction difference (no overlapping-hold tranche, no no-trade band) or a CPCV-gap data-loss effect.

**The Critic root-caused it, and both QE hypotheses are wrong. The actual cause is an IS-window mismatch:**

- The EDA's headline +0.2964 is produced by `holding_horizon_eda.py::model_free_horizon_scan` and re-confirmed by `model_free_vs_ranker_eda.py::_run_cost_aware_book` — both iterate **every** timestamp in `mom_wide.index` with **zero walk-forward segmentation**. The EDA console confirms: `[panel] IS panel 103492 rows, 5547 timestamps` — the EDA scores the **full IS panel, 2020-04 → 2025-03**.
- The runner's model-free book is run inside `run_cross_sectional_backtest`, whose outer loop iterates `_generate_xs_monthly_splits(training_months=24)` — and even in `score_mode="model_free"` (which trains nothing) the runner STILL iterates only the walk-forward **test windows**, which begin after the first 24 calendar months. The runner's IS book is **2022-03 → 2025-03 (37 months)**: `in_sample/monthly_pnl.csv` first row is `2022-03`; `in_sample/trades.csv` first `open_time` = 2022-03-01.
- The EDA's own M1b sub-period table (`M1b_model_free_subperiod_stability.csv`) shows the 5-year window the EDA scored is dominated by one regime: `third_1` (2020-04→2021-12) net **+0.5564**; `third_2` (2021-12→2023-08) net **−0.1039**; `third_3` (2023-08→2025-03) net **+0.1552**. **The runner's IS window (2022-03→2025-03) excludes the entire +0.5564 third_1 bull regime** and consists of ~75% of the −0.1039 third_2 plus all of the +0.1552 third_3. A model-free book restricted to that span lands near breakeven — the runner's IS net **+0.017** is fully consistent with the EDA's own sub-period decomposition.

There is no construction mystery: the Critic diffed `_run_cost_aware_book` against `build_positions` + the `run_cross_sectional_backtest` tranche/no-trade-band loop and they match — corrected-sign quintile, inverse-vol, `_scale_to_vol_target`, overlapping `H`-tranches, `_apply_no_trade_band`, `searchsorted` PnL, turnover fee — all faithful. **The EDA simply measured a different and far more favourable IS window than the runner structurally can.**

### 4.2 — Why this is a genuine Phase-1-5 EDA-fidelity flaw — and the QR owns it

The brief's entire Section 2 evidence base — the +0.2964 IS net headline, the M1a [17,25] plateau, the M2 "+0.2020 gap" — was computed over a 2020-04→2025-03 window that the production walk-forward cannot reproduce. The brief Section 1's predicted "+0.2020 IS net spread improvement" and Section 4.2's "modal OOS net [+0.00, +0.20]" therefore rested on an inflated, non-runner-faithful base. **The brief, the Phase 5.5 gate, and the QE engineering report all missed it** — the Phase 5.5 gate's "Additional Notes" even cross-checked +0.2964 against the committed CSV and called it verified, without noticing the CSV itself is a non-walk-forward measurement (verifying a number against a non-walk-forward CSV verifies the wrong thing).

This is a methodology weakness in the iteration's design phase, and the QR owns it without varnish: **the /091 brief's quantitative predictions rested on an EDA harness that did not measure the runner's evaluation window.** A top-quant-firm closeout records this as a process failure, not a footnote.

### 4.3 — Why this is NOT a BLOCK-class defect — and the precise contrast with /090

The /090 closeout's BLOCK was a defect in the **engineering report's classification-driving number**: `gross_monthly_sharpe` was hand-computed on a non-per-month basis with a mathematically-impossible /089 anchor (+0.5947), and that corrupt number fed falsifier F3, which fed the Section 8 classification. The defect was *inside the artifact that determines the verdict*.

Here, the opposite holds. **The /091 run is clean**, and the Section 8 classification rests **entirely on the runner's own reproducible artifacts**: F1 reads `comparison.csv` `monthly_sharpe` OOS = −0.0995; F2 reads `gross_monthly_sharpe` OOS = −0.0178 — both produced by the shared `_monthly_sharpe` helper on the genuine walk-forward book. The EDA's inflated +0.2964 appears NOWHERE in the falsifier evaluation. The flaw corrupted the brief's *predictions* — which are estimates, not gates — and a NEGATIVE result delivered against over-optimistic predictions is exactly the outcome the pre-registered falsifier mechanism exists to catch and FILE. The classification (8.2 CONSTRUCTION-FALSIFIED) is filed on sound, reproducible evidence. The flaw is a recorded process lesson, not a verdict-invalidating defect — which is precisely why the Critic returned OVERALL=MERGE (clean NEGATIVE, FILE) rather than BLOCK. The Critic's own framing: "A real Phase-1-5 EDA-fidelity flaw — but NOT a BLOCK-class defect, because the /091 run is clean and the NEGATIVE classification rests on reproducible runner artifacts."

The honest reconciliation: the runner's IS +0.017 is NOT a surprise — it is the EDA's own M1b sub-period evidence read correctly. The EDA was not *wrong* about the model-free book in 2020-21; it was wrong to present a 2020-04→2025-03 number as the runner's IS-fidelity target when the runner's IS window is 2022-03→2025-03.

---

## 5. Phase 7 failure-mode-prediction check (brief Section 7)

The brief Section 7 pre-registered the outcome distribution. Did /091 fail the way the brief predicted?

- **≈45% modal** — "the model-free score MATERIALLY improves the OOS net book and it is net-positive but thin; OOS net lifts from /089's −0.0985 to roughly [+0.00, +0.20]; OOS gross clears /089's +0.1717."
- **≈22% — F1/F2 fire** — "the model-free score does NOT improve the net/gross OOS book (OOS net ≤ −0.0985 OR OOS gross ≤ +0.1717). The dominant mechanism: the 2025-03→2026-05 OOS window contains a cross-sectional-momentum-compressing regime (a deleveraging crash, an analogue of the M1b 2022 third), or the crypto 'faster metabolism' reversed the H=21 signal faster OOS."
- **≈22%** OOS clearly net-positive [+0.20,+0.40]; **≈8%** marginal hover; **≈3%** full success.

**The realized outcome IS the brief's ≈22% F1/F2 path.** The brief named this scenario precisely: F1 and F2 both fire; OOS net −0.0995 ≤ −0.0985 and OOS gross −0.0178 ≤ +0.1717. The brief Section 4.4 even named the implication: "If F1 fires (and F3/F4 do not) — the model-free score did not improve the net OOS book; the /091 hypothesis is falsified for the cycle; most likely an OOS regime where cross-sectional momentum compressed." That is the realized result.

**Calibration verdict — MIXED, and honestly so.** The brief named the F1/F2 failure path, weighted it at ≈22%, and identified the exact mechanism (an OOS cross-sectional-momentum-compressing regime). On the *failure-path identification*, the calibration is clean — Section 7 was forthright that a momentum-family axis carries a real regime-break risk and weighted it second-highest. **But the calibration has a real miss, and it is the Section 4 EDA-window flaw bleeding through:** the brief weighted the ≈45% modal "net-positive but thin" outcome highest, and that modal weight rested on the inflated +0.2964 IS base. Had the brief's IS evidence been measured on the runner's 2022-03→2025-03 walk-forward window, the IS net would have read ~+0.017 — near breakeven, regime-sensitive, ~75% inside the −0.1039 crash third — and the *honest* modal prediction would have been a near-breakeven or net-negative OOS book, NOT "net-positive but thin." The brief's failure-mode distribution was anchored too optimistically because its IS base was inflated. The F1/F2 path should have carried more than ≈22% weight. **The brief named the right failure path but under-weighted it — and the under-weighting traces directly to the EDA-window-mismatch flaw.** Recorded as a calibration lesson, integral to the Section 4 process lesson.

---

## 6. The honest cross-sectional trajectory — /088 → /091 — near-breakeven, never net-positive

The cross-sectional line is v3's most sustained structural research direction — four consecutive iterations — and the closeout states its trajectory honestly:

| Iter | Type | OOS net monthly Sharpe | OOS gross monthly Sharpe | Classification | What it established |
|---|---|---:|---:|---|---|
| /088 | RE-ARCHITECTURE | −0.5418 | ≈ −0.043 (flipped est.) | ARCHITECTURE-PARTIAL | the cross-sectional MODEL transfers OOS (rank-IC +0.043, t ≈ 4.6) — v3's first OOS signal transfer; the BOOK loses (sign inversion + turnover drag) |
| /089 | CORRECTED build | −0.0985 | +0.1717 | CONSTRUCTION-PARTIAL | **MECHANICAL** lift (+0.44 vs /088): a sign fix + a turnover cut — removing drag, NOT adding edge. The book turns gross-positive; net still sub-zero |
| /090 | feature expansion | −0.0770 | +0.1558 (recomputed) | FEATURE-EXPANSION-FALSIFIED [Critic BLOCK] | the first genuine attempt to ADD gross edge — and it did NOT transfer; OOS gross FELL |
| /091 | scoring function | **−0.0995** | **−0.0178** | **CONSTRUCTION-FALSIFIED** | the model-free score did NOT recover a stronger book; OOS gross turned net-NEGATIVE; F1+F2 fire |

The honest read:

1. **The cross-sectional line never produced a net-positive OOS book.** Four iterations: /088 −0.5418 → /089 −0.0985 → /090 −0.0770 → /091 −0.0995. The line reached *near-breakeven* (the −0.08 to −0.10 band across /089/090/091) but never crossed zero net OOS.
2. **The /089 +0.44 lift was a one-time mechanical correction** — a sign error and a turnover excess are *bugs*; fixing them recovers performance that was always latent in the signal, it does not create new edge. There is no second sign error to fix.
3. **Two consecutive genuine edge attempts FAILED.** /090 (a researched downside-risk feature expansion) did not strengthen the gross signal — OOS gross FELL. /091 (a parameter-free model-free score, the lowest-overfitting-risk strategy possible) did not recover a stronger book — OOS gross turned net-negative. The cross-sectional gross signal in the current 22-altcoin / momentum-rank construction does not respond to feature work (/090) and is not the trained `LGBMRanker` "destroying" a clean signal that a model-free score recovers (/091 — the model-free score's OOS gross is net-negative).
4. **The /091 result, read against the corrected EDA window, is unsurprising.** The model-free book's IS net on the runner's actual 2022-03→2025-03 window is +0.017 — near breakeven, regime-sensitive. A book that is near-breakeven IS, restricted to a window ~75% inside a momentum-compressing crash regime, going faintly net-negative OOS is exactly what the EDA's own M1b sub-period evidence predicts.

This is not defeatism — it is the honest ledger cycle 3 hands cycle 4. The cross-sectional architecture produced v3's first genuine OOS *signal transfer* (the rank-IC), which is real; but across four iterations it never produced a net-positive *book*, and the last two genuine edge attempts both failed. **On honest evidence the cross-sectional momentum-rank architecture is tapped out as a route to a merge-grade book.** Section 9 takes that conclusion forward.

---

## 7. Critic integration — OVERALL=MERGE + 3 Recommendations

**Critic FINAL `d686b41`** (`briefs-v3/iteration_v3-091/review.md`): a single-round full review, OVERALL=**MERGE** — the EXPLORATION "file the closeout" verdict certifying /091 as a methodologically-clean NEGATIVE. All 8 mandatory Checks PASS (Check 1 look-ahead, Check 2 embargo width, Check 7 reproducibility, Check 8 hypothesis-implementation alignment — all PASS; Check 3 multiple-testing FAIL is informational and non-blocking for EXPLORATION per `feedback_v3_dsr_mode_artifact.md`, and is doubly vacuous for the model-free primary book which has zero fitted parameters; Checks 4/5/6 PASS by inapplicability — no new feature family, no new price-derived feature, deterministic primary book). Optional Checks 9-12 all PASS. The Critic root-caused the EDA-vs-runner gap (Section 4 above) and verified the two SETUP items: the embargo fix is correct at both `cross_sectional.py:998` and `run_cross_sectional_v3.py:915` (Item 2 PASS), and the gross-Sharpe figures are genuine reproducible runner outputs via the shared `_monthly_sharpe` helper, NOT hand-computations — the structural opposite of the /090 BLOCK root cause (Item 3 PASS, Critic /090 Rec #1 closed).

The Critic closed with **three process-level Recommendations** — all integrated:

**Recommendation 1 — The EDA-runner IS-window mismatch must be documented as a process lesson, and the cross-sectional EDA harness must be made walk-forward-faithful.** INTEGRATED — Section 4 of this diary documents the IS-window mismatch in full: the EDA scored the full 2020-04→2025-03 IS panel with no walk-forward segmentation; the runner's model-free book is structurally restricted to the 2022-03→2025-03 post-training-window span; the EDA's own M1b shows the excluded 2020-21 third carries net +0.5564; the runner's +0.017 IS net is the EDA's own sub-period evidence read correctly. **The forward fix (recorded for any future cross-sectional EDA — see Section 9.4):** any cross-sectional EDA whose number is cited as a runner-fidelity target MUST run the model-free book through `_generate_xs_monthly_splits(training_months=24)` — score only the post-burn-in walk-forward test windows — so the EDA's IS span is bit-identical to the runner's. The /090 closeout established that *falsifier-driving* numbers must be reproducible runner artifacts; the /091 lesson is the dual — EDA *prediction-driving* numbers must be measured on the runner's actual evaluation window. The Phase 5.5 gate's cross-check of an EDA number against a committed CSV must, in future, also verify the CSV was produced on the walk-forward span.

**Recommendation 2 — The /092 CONFIRMATION must NOT bundle a model-free cross-sectional book as a validated edge ingredient; the honest finding is that the cross-sectional line has produced no net-positive OOS book in four iterations.** INTEGRATED — Section 6 of this diary states the four-iteration ledger plainly (/088 −0.5418 → /089 −0.0985 mechanical → /090 −0.0770 FALSIFIED → /091 −0.0995 FALSIFIED); the /091 model-free book scores IS +0.017 / OOS −0.0995 on the runner's real window — at or below the /089 anchor it was meant to beat. The reference `LGBMRanker` book's OOS +0.4613 is explicitly recorded (Section 2.2) as a single-seed lottery draw (IS −0.1107; `frac_positive_paths` 0.356) that must NOT be cited as evidence the trained model "works." Section 9 carries this directly into the /092 recommendation: /092 must NOT bundle the cross-sectional book as a validated edge.

**Recommendation 3 — Future cross-sectional EXPLORATION briefs must pre-register a falsifier on the EDA-vs-runner IS-window equivalence, not only on the OOS outcome.** INTEGRATED — recorded as a forward methodology mandate (Section 9.4): any future cross-sectional axis whose brief derives predictions from a separate EDA harness must pre-register a gate of the form "the EDA model-free book and the runner model-free book must agree on IS net monthly Sharpe to within ±0.05 on the shared 2022-03→2025-03 walk-forward span." This is the EDA-fidelity analogue of `feedback_v3_methodology_axis_integration_test.md` and would have caught the +0.28 gap at the Phase 5.5 gate, turning a wasted EXPLORATION slot into a corrected brief. (As Section 9 concludes the cross-sectional momentum-rank architecture is tapped out, this mandate applies to any *future* cross-sectional axis cycle 4 might still run as a sub-experiment — it does not bind cycle 4's primary re-architecture if that re-architecture is not cross-sectional.)

---

## 8. Cycle-3 retrospective — the /082-091 10-EXPLORATION cadence is COMPLETE

iter-v3/091 CLOSES cycle 3. The 10-EXPLORATION cadence /082-091 is complete; iter-v3/092 is the cycle-3 CONFIRMATION slot. The honest retrospective:

### 8.1 — The cycle-3 10-EXPLORATION ledger

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /082 | NEW crypto-native FEATURE FAMILY — funding-rate 4-channel (per-symbol) | SUSPICIOUS-OOS-DOMINANT |
| #2 | /083 | symbol-universe EXPANSION 3→4 (+FILUSDT, per-symbol) | NEGATIVE |
| #3 | /084 | REFERENCE / METHODOLOGY — PER_CELL_GAP fix + clean /059-config 3-symbol re-anchor | REFERENCE-REANCHOR |
| #4 | /085 | NEW funding-regime-conditioned ENGINEERED feature (Category-2 composed, per-symbol) | SUSPICIOUS |
| #5 | /086 | NEW crypto-native DATA FEED — perp-spot basis 3-feature family (per-symbol) | INERT |
| #6 | /087 | symbol-universe EXPANSION 3→6 WHOLESALE (+GALA+MANA+SAND, per-symbol) | NEGATIVE |
| #7 | /088 | RE-ARCHITECTURE — cross-sectional `LGBMRanker` relative-value ranking model | ARCHITECTURE-PARTIAL |
| #8 | /089 | CORRECTED cross-sectional — sign fix + CPCV-proxy fix + cost-aware construction | CONSTRUCTION-PARTIAL |
| #9 | /090 | cross-sectional downside-risk FEATURE EXPANSION (13→15) | FEATURE-EXPANSION-FALSIFIED [Critic OVERALL=BLOCK] |
| #10 | **/091** | **cross-sectional model-free trailing-21-bar-return SCORING function** | **CONSTRUCTION-FALSIFIED** |

### 8.2 — The cycle-3 bottom line

**Cycle 3 produced ZERO clean PROMISING results across all 10 EXPLORATIONs.**

- **Slots /082-087 — six per-symbol axes — all NEGATIVE-class.** Two SUSPICIOUS-OOS-DOMINANT (funding-rate features /082, funding-regime engineered feature /085), one SUSPICIOUS, one INERT (perp-spot basis /086), two NEGATIVE (universe expansion /083, /087). The per-symbol absolute-barrier LightGBM architecture — the /059 baseline architecture — absorbed three different crypto-native feature families and two universe expansions and produced not one clean PROMISING. This confirmed the /087 closeout diagnosis: the binding constraint is architectural, not feature-level.
- **Slots /088-091 — the four-iteration cross-sectional re-architecture — produced v3's first genuine OOS signal transfer but never a net-positive OOS book.** /088 stood up the pooled `LGBMRanker` cross-sectional architecture and produced an OOS rank-IC of +0.043 (t ≈ 4.6) — genuinely the first time in v3 history a new axis transferred a signal OOS rather than IS-overfitting and inverting. /089 corrected the sign and cut turnover (a +0.44 OOS lift, but MECHANICAL — drag removal, not edge). /090 attempted to ADD gross edge via a feature expansion — it FAILED (OOS gross fell; Critic BLOCK on a defective hand-computed metric). /091 attempted to recover a stronger book via a parameter-free model-free score — it FAILED (OOS gross turned net-negative; F1+F2 fire). The cross-sectional OOS net trajectory /088 −0.54 → /089 −0.10 → /090 −0.08 → /091 −0.10 reached near-breakeven but never crossed zero.

**The honest cycle-3 verdict.** Cycle 3 was the boldest v3 cycle to date — it included v3's first re-architecture since iter-v3/001, genuine crypto-native feature families, and aggressive universe expansion, exactly as the `feedback_v3_bold_research_mandate.md` directive demanded. It delivered one real structural finding — the cross-sectional architecture transfers a signal OOS where the per-symbol architecture does not — and that finding is worth carrying forward as *knowledge*. But it produced zero merge-grade results: zero clean PROMISING, zero net-positive OOS book on the cross-sectional line, and the per-symbol line confirmed dead to feature/universe work. **Cycle 3's ledger is honest and it is sobering: two architectures explored to their limits (per-symbol absolute-barrier LightGBM; cross-sectional momentum-rank), neither producing a merge-grade book.** Cycle 4 cannot be a third construction tweak on either. It must be a genuine re-architecture into a different signal class. Section 9 makes that the forward plan.

---

## 9. Forward plan — the /092 recommendation + the cycle-4 re-architecture direction

This is the key deliverable. iter-v3/091 closes cycle 3; iter-v3/092 is the cycle-3 CONFIRMATION slot; and the cross-sectional momentum-rank architecture is, on honest evidence, tapped out.

### 9.1 — The /092 problem: a CONFIRMATION slot with no PROMISING result to confirm

A v3 CONFIRMATION normally multi-seed-validates the cycle's best clean PROMISING result. **Cycle 3 has none.** And the Critic's Recommendation 2 is explicit and binding: /092 must NOT bundle the cross-sectional model-free book (or the trained `LGBMRanker` reference book) as a validated edge ingredient — the cross-sectional line has produced no net-positive OOS book in four iterations, and the reference book's OOS +0.4613 is a single-seed lottery draw. There is no edge to confirm.

This is not an unprecedented situation — iter-v3/039 (cycle-2 CONFIRMATION) ran CONFIRMATION-NO-MERGE on a bundle that failed, and iter-v3/018 ran the BOOTSTRAP CONFIRMATION. But /092 is different: there is no bundle to even attempt. The /092 slot must be re-purposed.

### 9.2 — The /092 recommendation: a multi-seed CONFIRMATION-grade verdict that FORMALLY CLOSES the cross-sectional line

**Recommended: /092 = a multi-seed CONFIRMATION-grade evaluation that formally closes the cross-sectional momentum-rank line before cycle 4 — NOT opening the cycle-4 re-architecture at /092.**

The reasoning, weighed against the alternative (open the cycle-4 re-architecture at /092 itself):

1. **The cross-sectional line deserves a formal, multi-seed verdict before it is set down.** Across /088-091 every cross-sectional result is single-seed (the model-free book is deterministic; the reference `LGBMRanker` is `seed=42`/`ensemble_size=1`). The reference book's OOS +0.4613 single-seed inversion is precisely the artifact a multi-seed run resolves. A /092 that runs the trained-`LGBMRanker` cross-sectional book at the CONFIRMATION spec (`--seeds 2`, `ensemble_size=5`, `n_trials=35` per `feedback_v3_outer_seed_cap_2_v3.md` + `feedback_v3_confirmation_n_trials_35.md`) — and reports the multi-seed-mean IS/OOS, the Pareto front, and the full DSR/PBO/PSR — produces the *definitive* statement of whether the cross-sectional momentum-rank architecture has a multi-seed-robust edge. The honest expectation per Section 6 is that it does not (the single-seed +0.4613 will regress to the IS-weak `frac_positive_paths` 0.356 mean) — and a CONFIRMATION-grade NO-MERGE verdict formally closes the line on rigorous evidence, rather than leaving it set down on a single-seed result. This is the disciplined close: the line that produced v3's first OOS signal transfer is not abandoned mid-air; it is given a multi-seed verdict and then closed.
2. **It respects the 10:1 cadence and the CONFIRMATION slot's purpose.** `feedback_v3_strict_10_to_1_cadence.md` makes /092 the cycle-3 CONFIRMATION. Re-purposing it as a CONFIRMATION-grade *multi-seed validation* (of the cross-sectional line, to a NO-MERGE verdict) keeps /092 a CONFIRMATION in spec and in spirit — a multi-seed, full-DSR/PBO/PSR, Pareto-front run — without manufacturing a fake edge bundle. Opening a cycle-4 re-architecture at /092 would collapse the cadence: a re-architecture is a single EXPLORATION's axis (cf. /088), and it belongs at the *first slot of cycle 4* (iter-v3/093), single-seed, EXPLORATION-spec — not crammed into a CONFIRMATION slot at CONFIRMATION cost.
3. **It gives the cycle-4 re-architecture a clean start.** A re-architecture into a new signal class (Section 9.3) deserves its own brief, its own committed EDA, its own Phase 5.5 gate, and the full 2h EXPLORATION budget — as iter-v3/093, the first slot of cycle 4. Forcing it into /092 under CONFIRMATION spec and the 6h CONFIRMATION cap would rush exactly the iteration that most needs care.

**The /092 spec (recommended):** run the trained-`LGBMRanker` cross-sectional book (`score_mode="trained"`, the /089 cost-aware construction, the 13-feature stack, the corrected embargo) at the CONFIRMATION spec — `--seeds 2`, `ENSEMBLE_SIZE=5`, `n_trials=35`, the full DSR/PBO/PSR + multi-seed Pareto. Pre-registered outcome: a CONFIRMATION-grade verdict. If — against expectation — the multi-seed mean clears BOTH IS and OOS floors with both Pareto seeds positive, the cross-sectional line is revived and BASELINE_V3.md is evaluated per `feedback_v3_baseline_update_policy.md`. The honest prediction is CONFIRMATION-NO-MERGE: the single-seed OOS +0.4613 regresses, and /092 formally closes the cross-sectional momentum-rank line. Either way, the cycle-4 re-architecture opens cleanly at iter-v3/093. **The /092 QR makes the final call with its own committed analysis — this diary recommends the direction (a formal multi-seed close, not a cycle-4 open) on the reasoning above; it does not prescribe it.**

### 9.3 — The cycle-4 re-architecture direction — three bold candidates

v3 has now explored two architectures to their limits: **per-symbol absolute-barrier LightGBM** (the /059 baseline — overfits IS, confirmed dead to feature/universe work across cycles 1-3) and **cross-sectional momentum-rank** (/088-091 — transfers a signal OOS but never a net-positive book). Per `feedback_v3_bold_research_mandate.md` (the 2026-05-17 SHARPENED section: top-quant-firm-grade bar, "exhausted" forbidden, re-architecture encouraged), cycle 4 must be a genuine RE-ARCHITECTURE into a different signal class — NOT another cross-sectional construction tweak. Three candidates, each a genuinely different signal class / problem framing, with research grounding from genuine literature search:

**Candidate A — DERIVATIVES-MICROSTRUCTURE STATE-CONDITIONING: a funding-rate / open-interest / liquidation regime model (RECOMMENDED).**

The signal class. Every v3 architecture to date has predicted from *price-derived* features (OHLCV transforms, momentum, volatility, the cross-sectional return rank). Crypto perpetual futures carry a *second, orthogonal* information layer that price-only models structurally cannot see: the **derivatives-microstructure state** — the funding rate (the 8h cost-of-carry, a direct read on positioning crowding), open-interest dynamics (the leverage-stretch gauge), and liquidation flow (the self-exciting deleveraging signal). The 2025 derivatives-signal literature is specific and consistent: funding rates above ~15% APR signal crowded long positioning; open interest rising faster than price is a "classic fragility indicator"; declining OI plus sustained extreme funding "frequently precedes significant price movements"; and "integrated frameworks combining open interest, funding rates, and liquidation data achieved substantially higher accuracy than single indicators alone" ([gate.com derivatives signals 2025](https://web3.gate.com/crypto-wiki/article/how-do-derivatives-market-signals-predict-crypto-price-movements-in-2025-futures-open-interest-funding-rates-and-liquidation-data-explained-20260206); [amberdata, the $31B deleveraging](https://blog.amberdata.io/leverage-liquidations-the-31b-deleveraging)). The October 2025 $19B liquidation cascade and the November $2B cascade ([coinchange](https://www.coinchange.io/blog/bitcoins-2-billion-reckoning-how-novembers-liquidation-cascade-exposed-cryptos-structural-fragilities)) are not noise — they are deterministic, mechanically-triggered deleveraging events that a derivatives-state model can anticipate via OI + funding extremes.

Why this is a genuine re-architecture, not a feature add. iter-v3/082 added funding-rate *features* to the per-symbol price-prediction model and they fired SUSPICIOUS-OOS-DOMINANT — but that bolted a funding feature onto a price-prediction architecture whose label was a price barrier. Candidate A is the opposite: a model whose **label and signal are both derivatives-microstructure objects** — e.g. predict the forward realized-vol regime or the forward deleveraging-event probability from {funding z-score, OI delta, OI/market-cap, liquidation-flow asymmetry, basis}, and trade a regime-conditional book (long carry in stable funding regimes, flat-or-short into OI-stretch + extreme-funding states). This is the "predict the regime, not the price" reframing. The architecture is a state classifier, not a return predictor.

The honest caveat — and why it is still the recommendation. The crypto *carry* strategy itself has decayed: the funding-driven carry Sharpe fell to 4.06 in 2024 and turned negative in 2025 ([The Crypto Carry Trade, Christin et al.](https://www.andrew.cmu.edu/user/azj/files/CarryTrade.v1.0.pdf); confirmed by the [arXiv 2510.14435 investable-asset survey](https://arxiv.org/html/2510.14435v2)) — and the v3 OOS window is 2025-03→2026-05. **A naive long-carry book would be tested on the exact window where carry stopped working.** But that decay is precisely the argument for the *regime-conditional* framing rather than naive carry: the 170-predictor study found 63 statistically significant total-return strategies sorted on basis/momentum/liquidity/size/volatility, with a two-factor log-basis + price-volume model explaining all 63 ([ScienceDirect S2096720925000818](https://www.sciencedirect.com/science/article/pii/S2096720925000818)) — the derivatives state is a rich predictor space; the edge in 2025 is not "collect funding" but "be flat into the deleveraging regime the funding+OI state predicts." Candidate A's edge is regime *avoidance* and regime *conditioning*, which is robust to carry decay. The data is available for the v3 universe (Binance publishes per-symbol funding history and OI). This is the boldest genuinely-orthogonal re-architecture on the table — a new signal class, a new label, a new problem framing — and it directly attacks the structural fact that every prior v3 architecture was price-myopic.

**Candidate B — CRYPTO STATISTICAL ARBITRAGE: a cointegration / mean-reversion pairs architecture.**

The signal class. Every v3 architecture has been *directional* (predict whether a symbol/cross-section goes up). Statistical arbitrage is the orthogonal class: predict *convergence* — trade the spread between cointegrated symbols, market-neutral, mean-reverting. The 2024-25 crypto stat-arb literature is encouraging: a cointegration study on 2022-01→2024-10 daily data found "a high level of cointegration among major cryptocurrencies" and a BTC-ETH pairs book delivering a 2.45 Sharpe vs 0.14 for BTC buy-and-hold ([IJSRA 2026-0283](https://ijsra.net/sites/default/files/fulltext_pdf/IJSRA-2026-0283.pdf)); a PCA-factor stat-arb study found tradeable mean-reversion in the residuals ([Jung, SSRN 5263475](https://papers.ssrn.com/sol3/Delivery.cfm/5263475.pdf?abstractid=5263475&mirid=1)); and the practitioner consensus is that "cointegration beats correlation" for crypto pairs ([amberdata](https://blog.amberdata.io/crypto-pairs-trading-why-cointegration-beats-correlation)). The architecture: screen the 22-symbol universe for cointegrated pairs (Engle-Granger / Johansen on a rolling IS window), trade the z-score of each pair's spread with a mean-reversion entry/exit, size by spread half-life. This is a genuinely different architecture — the model is a cointegration screen + an Ornstein-Uhlenbeck spread tracker, not a tree.

The honest caveat. Crypto cointegration relationships are less stable than equity-sector pairs — the literature's strongest results are BTC-ETH and major-cap pairs, and the v3 universe excludes BTC/ETH (v1/v2 symbols). The 22-symbol altcoin universe's cointegration structure must be screened IS-only and is likely thinner and more regime-fragile. Stat-arb is also turnover-sensitive — the same fee drag that sank the cross-sectional book applies. Candidate B is a real re-architecture and the mean-reversion signal class is genuinely untried in v3, but the altcoin-universe cointegration instability makes it a higher-risk second choice. It is recommended as the cycle-4 fallback if Candidate A's EDA is inconclusive.

**Candidate C — A REGIME-SWITCHING TIME-SERIES-MOMENTUM ARCHITECTURE: an HMM/regime-classifier gating a trend book.**

The signal class. v3's per-symbol architecture predicted an absolute price barrier; the cross-sectional architecture predicted a relative rank. Neither is *time-series momentum* (TSMOM) — the Moskowitz-Ooi-Pedersen trend-following class — and neither has an explicit *regime model*. Candidate C is a two-layer architecture: (1) a regime classifier — a Hidden Markov Model or k-means regime model on per-symbol returns/volatility, which the 2024-26 literature finds "outperform other models in forecasting regime shifts" and reliably separate low-vol/high-vol and bull/bear/sideways states ([Preprints.org 202603.0831](https://www.preprints.org/manuscript/202603.0831); [HMM-RL portfolio management](https://www.cloud-conf.net/datasec/2025/proceedings/pdfs/IDS2025-3SVVEmiJ6JbFRviTl4Otnv/966100a067/966100a067.pdf)); (2) a time-series-momentum book that the regime layer *gates* — full trend exposure in persistent bull/bear regimes, flat in the "transitional buffer" sideways regime. The edge is that TSMOM is documented to work in trending regimes and bleed in choppy ones, and an explicit regime gate harvests the trend only when the regime model says it is persistent.

The honest caveat. This is the *closest* of the three to v3's existing toolkit — v3 already uses Hurst and ADX as regime *features*, and a regime *gate* is conceptually adjacent to v3's existing 7-gate stack. The risk is that Candidate C is not bold enough — it could collapse into "another gate on a momentum book," which `feedback_v3_structural_over_knob_exploration.md` warns against. It is a genuine re-architecture only if the regime model is the *primary* object (the HMM state drives position sizing) rather than a binary filter. Candidate C is the lowest-risk and lowest-ambition of the three — recorded as a third option, not recommended over A.

### 9.4 — The recommended cycle-4 direction + the forward methodology mandate

**Recommended cycle-4 re-architecture: Candidate A — the derivatives-microstructure state-conditioning architecture (funding-rate / open-interest / liquidation regime model), opening at iter-v3/093 as the first EXPLORATION of cycle 4.**

The case, in one paragraph: it is the only candidate that attacks the structural fact uniting every v3 failure — *every v3 architecture to date has been price-myopic*. The per-symbol model, the cross-sectional ranker — both predict from OHLCV transforms. Crypto perpetual futures carry a second, orthogonal, mechanically-causal information layer (funding, OI, liquidations) that price-only models cannot see, and the 2025 literature is specific that an integrated derivatives-state framework beats single indicators and beats price-only models. The carry-decay caveat is real but it argues *for* the regime-conditional framing (be flat into the predicted deleveraging regime) and *against* naive carry — and regime avoidance is robust to the very decay that kills naive carry. It is a genuine new signal class, a genuine new label (a derivatives-state / regime target, not a price barrier), and a genuine new problem framing (predict the regime, not the price). The iter-v3/093 QR must commit a derivatives-data EDA before the brief, per `feedback_v3_axis_selection_quant_discipline.md`: fetch per-symbol Binance funding + OI history, IS-screen the funding/OI/liquidation feature space for genuine forward predictive content on the 22-symbol universe, and pre-register the regime-conditional book construction.

**The forward methodology mandate (Critic Rec 1 + Rec 3, recorded for cycle 4):** if cycle 4 runs *any* iteration whose brief derives quantitative predictions from a separate EDA harness (rather than from the runner itself), that brief MUST (a) run the EDA on the runner's exact walk-forward evaluation window — `_generate_xs_monthly_splits(training_months=24)` post-burn-in test windows, IS span bit-identical to the runner — and (b) pre-register an EDA-vs-runner IS-fidelity falsifier ("EDA IS metric and runner IS metric agree to within ±0.05 on the shared walk-forward span"). This is the EDA-fidelity analogue of `feedback_v3_methodology_axis_integration_test.md`, and it is the direct lesson of the /091 IS-window-mismatch flaw.

---

## 10. Decision

**NO-MERGE. Critic Phase-7.5 OVERALL = MERGE (the EXPLORATION "file the closeout" verdict — a methodologically-clean NEGATIVE, certified to FILE; NOT a baseline merge).** iter-v3/091 classified **CONSTRUCTION-FALSIFIED** (brief Section 8.2) — F1 (OOS net monthly Sharpe −0.0995 ≤ /089's −0.0985) AND F2 (OOS gross monthly Sharpe −0.0178 ≤ /089's +0.1717) both FIRE. The model-free trailing-21-bar-return scoring function did not recover a stronger cross-sectional book; OOS gross turned net-negative. The scoring function reverts to the trained `LGBMRanker` for any future cross-sectional work.

The Critic root-caused the EDA-vs-runner gap as a Phase-1-5 EDA-fidelity flaw — the brief's predictions rested on a full-2020-04→2025-03 IS-panel EDA window that the runner's walk-forward (2022-03→2025-03) structurally cannot reproduce — NOT a BLOCK-class defect, because the /091 run is clean and the classification rests entirely on reproducible runner artifacts. The QR owns the flaw as a process lesson (Section 4); the forward fix (a walk-forward-faithful cross-sectional EDA harness + an EDA-vs-runner IS-fidelity falsifier) is recorded for cycle 4 (Section 9.4). The reference `LGBMRanker` book's OOS +0.4613 is a single-seed lottery artifact (Section 2.2) and must NOT be cited as evidence the trained model works.

**BASELINE_V3.md is UNCHANGED** — canonical /059 metrics (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791), tag `v0.v3-059`. An EXPLORATION never updates the baseline. `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are untouched — the QR saw OOS for the first time in Phase 7.

**iter-v3/091 CLOSES cycle 3.** The /082-091 10-EXPLORATION cadence is complete; iter-v3/092 is the cycle-3 CONFIRMATION slot. The honest cycle-3 retrospective (Section 8): zero clean PROMISING results across all 10 EXPLORATIONs; the per-symbol architecture confirmed dead to feature/universe work (/082-087); the cross-sectional momentum-rank architecture produced v3's first genuine OOS signal transfer but never a net-positive OOS book (/088 −0.54 → /089 −0.10 → /090 −0.08 → /091 −0.10). The cross-sectional architecture, `cross_sectional.py` infrastructure, the 22-symbol `XS_UNIVERSE`, and the /089 cost-aware construction are RETAINED as code (8.2 falsifies only the /091 scoring change) — but on honest evidence the cross-sectional momentum-rank architecture is tapped out as a route to a merge-grade book.

**The forward plan (Section 9):** /092 — the recommended direction is a multi-seed CONFIRMATION-grade evaluation that formally closes the cross-sectional momentum-rank line (run the trained-`LGBMRanker` cross-sectional book at `--seeds 2` / `ENSEMBLE_SIZE=5` / `n_trials=35` + full DSR/PBO/PSR + Pareto; honest expectation CONFIRMATION-NO-MERGE), NOT opening the cycle-4 re-architecture at /092. Cycle 4 — a genuine RE-ARCHITECTURE into a new signal class, opening at iter-v3/093; the recommended direction is Candidate A, a derivatives-microstructure state-conditioning architecture (a funding-rate / open-interest / liquidation regime model — the only candidate that attacks the structural fact that every prior v3 architecture was price-myopic), with crypto statistical arbitrage (Candidate B) and a regime-switching TSMOM architecture (Candidate C) as recorded alternatives.

An EXPLORATION closeout marker tag `v0.v3-091` is issued (annotated; NOT a baseline update — the `v0.v3-082`…`v0.v3-090` pattern).

---

**Commit chain:**
- EDA SHAs: `d4ad137` — `analysis/iteration_v3-091/holding_horizon_eda.py` (corrected-embargo horizon grid); `a2c3a3f` — `analysis/iteration_v3-091/model_free_vs_ranker_eda.py` + M1a/M1b/M2/M3/M4 CSVs (the focused confirming EDA — carrying the IS-window-mismatch fidelity flaw, Section 4)
- Brief SHA: `9d3d525` — `briefs-v3/iteration_v3-091/research_brief.md` (the model-free scoring-function axis, superseding the horizon-extension brief `e913d3e`); brief Section 11 SHA backfill `905b6c8`
- Phase 5.5 gate SHA: `e4e638f` (PASS — brief SHA `9d3d525`; supersedes the prior gate `c56c457` OVERALL=BLOCK, embargo bug); brief setup-SHA backfill `2b996fd`
- Setup SHA: `b94b90f` — the model-free scoring path (`score_mode`) + the walk-forward embargo fix + the gross-Sharpe runner artifact + the /090 feature revert + 3 integration tests; `ITERATION_LABEL "v3-091"`
- Engineering report SHA: `5a8f4fc` — `briefs-v3/iteration_v3-091/engineering_report.md` + backtest results
- Critic FINAL SHA: `d686b41` — `briefs-v3/iteration_v3-091/review.md` — **OVERALL=MERGE** (EXPLORATION FILE verdict; clean NEGATIVE; 3 Recommendations; the EDA-vs-runner IS-window mismatch root-caused)
- Diary + catalog SHA: this closeout — `docs(iter-v3/091): closeout diary + catalog + cycle-3 retrospective — CONSTRUCTION-FALSIFIED / Critic OVERALL=MERGE (clean NEGATIVE, FILE)`
**Reports**: `reports-v3/iteration_v3-091/` (model-free primary book); `reports-v3/iteration_v3-091/reference_lgbmranker/` (trained `LGBMRanker` reference comparator)
**Tag**: `v0.v3-091` (EXPLORATION closeout marker; NOT a baseline update — BASELINE_V3.md UNCHANGED at `v0.v3-059`)
