# iter-v3/103 — Cycle-5 EXPLORATION #3 — ENGINEERED COMPOSED FEATURES (formulaic-alpha operator toolkit, /102-corrected) — FILED NULL-AT-EDA — the deep IS-only EDA conclusively proved no engineered candidate clears an IS-predictive bar; no brief-mandated backtest was run

**Date**: 2026-05-19
**Type**: EXPLORATION (cycle-5 slot #3) — Phases 1-5 concluded at a NULL-AT-EDA verdict
**Verdict**: **NULL-AT-EDA** — the deep, multi-angle IS-only EDA (3 committed scripts, `e4d192d`; brief `a7386e7`) screened 7 engineered composed features built from the formulaic-alpha operator toolkit and conclusively proved no candidate is IS-predictive. The strongest stability survivor is INERT-by-importance (rank 15/15 on the IS-engine symbols). No Phase-6 backtest was run.
**Classification**: **NULL-AT-EDA** — reserved for an axis the deep EDA conclusively proves dead (high bar). Killing it at the EDA — rather than spending a 3-seed backtest to reproduce the documented `feedback_v3_inert_features_at_higher_budget.md` OOS-harm and the /102 IS-collapse — is the fail-fast WIN (`feedback_fail_fast.md`), not an iteration failure.
**Decision**: **NO-MERGE.** BASELINE_V3.md UNCHANGED — canonical **`v0.v3-059`** (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**, 10-seed CONFIRMATION).
**Branch**: `iteration-v3/103`

---

## 1. The axis committed — and why

iter-v3/103 is the second attempt at the user-directed WorldQuant-101 formulaic-alphas
axis. iter-v3/102 (cycle-5 slot #2) ported the literal Kakushadze (2015, arXiv 1601.00991)
Alpha#32 as a 15th `V3_FEATURE_COLUMNS` feature and closed **EXPLORATION-NEGATIVE** — the
3-seed multi-seed Optuna backtest collapsed the in-sample fit (IS monthly Sharpe +0.3993,
Falsifier F2 fires below the +0.60 floor) while the OOS headline spiked to +1.5458; the
Phase-7.5 Critic ruled out look-ahead, so /102 was the iter-v3/026/027/030/034/036/037
IS-collapse / OOS-spike overfitting signature.

The /102 closeout (Lesson 1 + Critic Recommendation 2) mandated two corrections for the
second attempt, and /103 implemented both:

1. **Engineer a v3-specific COMPOSED feature; do not port a literal alpha.** v3's only
   PROMISING post-bootstrap feature — iter-v3/025's `regime_momentum_signed_5d` =
   `ret_5d × sign(hurst_100 − 0.5)` — was an engineered composition that explicitly
   encodes a regime×momentum interaction a depth-3-5 tree cannot compose at split level
   (`feedback_v3_engineered_features_proven.md`). /103's candidates are built from the
   formulaic-alpha operator toolkit (`ts_argmax`, `ts_argmin`, `ts_rank`, `decay_linear`,
   `scale_ts`, `ts_corr`) into compositions of that same non-tree-representable class.

2. **The selection evidence must be IS-PREDICTIVE.** /102 selected `alpha032` on a
   held-out-tail single-classifier accuracy horse race — an OOS-leaning statistic whose
   own 95% CI straddled zero and which (the /102 closeout Lesson 1) does NOT predict the
   multi-seed Optuna IS fit. /103's screen is genuine IS feature→label Spearman IC,
   3-symbol sign-consistency, IS sub-period (half + quartile) sign-stability, and an
   IS-fold LightGBM gain-importance + IS-validation-logloss test. None of these touch the
   post-cutoff OOS; all four are directly predictive of what a multi-seed IS Optuna fit
   consumes. This is the correction of the /102 OOS-proxy trap.

Per `feedback_v3_axis_selection_quant_discipline.md` the axis was QR-led with a committed
`analysis/iteration_v3-103/*.py` EDA basis (`e4d192d`) preceding the brief
(`briefs-v3/iteration_v3-103/research_brief.md`, setup SHA `a7386e7`). The full 10-section
brief was written per the dispatch mandate so the Phase-5.5 gate had a complete,
gate-able artifact; Section 4 carried the NULL-AT-EDA recommendation with its complete
numerical basis. The brief documents `argmax_pullback_signed_20` as the *designated*
would-be axis — the EDA's strongest survivor — with a full implementation spec
(Section 3) and pre-registered falsifiers (Section 4), so that an override-to-backtest
would have had a gate-able spec.

---

## 2. The deep IS-only EDA — 7 engineered composed features, four IS-predictive axes

Three committed scripts under `analysis/iteration_v3-103/` (commit `e4d192d`), all
strictly IS-only — every row entering any IC, sign-stability, redundancy, or
LightGBM-importance computation has `open_time < OOS_CUTOFF_MS = 1742774400000`; the
post-cutoff OOS was never read by the QR in Phases 1-5.

### The candidate basket — 7 engineered composed features (`candidate_lib.py`)

Each candidate is built from the formulaic-alpha operator toolkit into a composition that
encodes a non-tree-representable interaction:

| Candidate | Construction | Encoded interaction |
|---|---|---|
| C1 `recency_weighted_momentum_5d` | `ret_5d × (1 − argmax20_recency/19)` | momentum down-weighted by trend staleness |
| C2 `extrema_recency_skew_30` | `(argmin30 − argmax30)/29` | recency asymmetry of windowed high vs low |
| C3 `vol_decayed_trend` | `decay_linear(ret,10) × sign(atr_rank200 − 0.5)` | recency-weighted momentum, vol-regime sign gate |
| C4 `corr_gated_momentum_5d` | `ret_5d × corr(close,volume,20)` | momentum gated by volume-confirmation |
| C5 `tsrank_dispersion_ratio` | `ts_rank(ret_std20/ret_std60, 50)` | 50-bar percentile of short/long return-dispersion ratio |
| C6 `scaled_reversal_pressure_signed` | `scale_ts(close − sma7, 100) × sign(hurst − 0.5)` | the alpha032 fast term, regime-conditioned |
| C7 `argmax_pullback_signed_20` | `(close/max20 − 1) × sign(ret60)` | signed pullback depth from the 20-bar high |

### The screen — and how it corrects /102's OOS-proxy trap

The /102 EDA selected on a held-out-tail single-classifier accuracy horse race; the
/102 closeout proved that proxy does not predict the multi-seed Optuna IS fit. /103's
screen uses **no held-out-tail proxy**. The selection evidence is four strictly-IS-only
axes, each directly predictive of what a multi-seed IS Optuna fit consumes:

- **T2/T3 — directional Spearman IC vs the /059 triple-barrier label + 3-symbol
  sign-consistency.** Five of the 7 candidates are sign-consistent across all 3 symbols
  — already a stronger basket than the /102 alpha basket (alpha032's IS IC flipped sign:
  BCH −0.0255, LDO +0.0413, TRX +0.0395). `tsrank_dispersion_ratio` has the strongest
  aggregate mean |IC| (0.0992, ~3× alpha032's 0.0354).

- **T4 — IS sub-period sign-stability, half-split AND quartile resolution.** The decisive
  refinement is the quartile test on the IS-engine symbols BCH+TRX (a half-split can mask
  a sign-flip averaged over half a window). `argmax_pullback_signed_20` is the **only**
  candidate holding one IC sign across all 4 BCH quartiles AND all 4 TRX quartiles
  (`corr_gated_momentum_5d` is runner-up, BCH all-positive but TRX flips once). The
  `tsrank_dispersion_ratio` cautionary case: its strong *aggregate* |IC| dissolves under
  the quartile breakdown (BCH full IC −0.0059 ≈ 0 with oscillating quartiles; LDO
  quartiles flip Q1→Q2; the strong number was an artifact of a thin 581-row LDO panel
  plus per-symbol aggregation hiding sign instability — the /102 trap in a different
  costume). The screen actively catches the failure mode.

- **T5 — incumbent redundancy.** `argmax_pullback_signed_20` passes the 0.70 hard
  redundancy gate by only 0.015 (max |IC| 0.6846 vs `ema_spread_atr_20` on BCH) —
  near-collinear with an incumbent, a fragility flag.

- **T6 — IS-fold LightGBM gain-importance — the DECISIVE IS-predictive test.** For each
  symbol a depth-4 LightGBM (the v3 architecture; `num_leaves=15`, `max_depth=4`) is fit
  on the IS panel with the 14 incumbents + the candidate, using a chronological 70/30
  IS train/validation split — no shuffling, no post-cutoff data, no leakage.

### T6 — the conclusive INERT finding

| candidate | symbol | gain_rank_of_15 | gain_share_pct | parity 6.67% | IS-val logloss Δ (15−14) |
|---|---|---:|---:|:--:|---:|
| `argmax_pullback_signed_20` | BCH | **15** | **0.000** | below | −0.00189 |
| `argmax_pullback_signed_20` | LDO | 5 | 8.643 | above | +0.00238 |
| `argmax_pullback_signed_20` | TRX | **15** | 1.056 | below | −0.00065 |
| `corr_gated_momentum_5d` | BCH | 11 | 1.446 | below | −0.00163 |
| `corr_gated_momentum_5d` | LDO | 6 | 2.550 | below | −0.00121 |
| `corr_gated_momentum_5d` | TRX | 13 | 0.274 | below | −0.00201 |

**The strongest survivor of the stability screen, `argmax_pullback_signed_20`, ranks dead
last (15/15) in BOTH BCH and TRX** — the two symbols carrying 99%+ of /059 IS PnL (BCH
alone is 95.76%) — with a BCH gain share of literally **0.000%**. It is above parity only
on the 581-row LDO panel, which is too thin to carry a feature verdict. This is the
textbook v3 **INERT** signature — the iter-v3/019/082/085/086 pattern, where the tree
declines to allocate ranked split capacity to the feature. The runner-up
`corr_gated_momentum_5d` is the same story: rank 11-13/15, below parity in all 3 symbols.
The IS-validation logloss deltas are all noise-floor (−0.0019 to −0.0020, except a small
*worsening* on LDO). A feature contributing 0.000% gain on the IS engine cannot move a
multi-seed Optuna fit in either direction by signal.

**EDA verdict.** Seven engineered composed features, screened on four IS-predictive axes.
Every candidate fails an IS-predictive bar. The strongest stability survivor is
INERT-by-importance on the IS-engine symbols. No candidate is IS-predictive.

---

## 3. The verdict — NULL-AT-EDA, no backtest — the fail-fast justification

The dispatch reserves NULL-AT-EDA for "an axis the deep EDA conclusively proves dead (high
bar)." The /103 EDA clears that bar — three committed scripts, four IS-predictive screens,
a rank-15/15 INERT finding on both IS-engine symbols. No backtest was run, for three
binding reasons:

1. **An INERT 15th feature is known to HARM, not help.**
   `feedback_v3_inert_features_at_higher_budget.md` is binding: a feature that ranks last
   in importance, added at higher Optuna budget, produced OOS Sharpe −1.07 vs +0.78
   (Δ −1.85) because the larger search space lets Optuna overfit IS noise *through* the
   dead column. `argmax_pullback_signed_20` is rank 15/15 on BCH+TRX with a 0.000% BCH
   gain share — the exact INERT profile that rule governs.

2. **A backtest would knowingly reproduce /102.** /102's failure was that its selection
   proxy (held-out-tail accuracy) did not predict the IS fit. /103's EDA uses an
   IS-predictive screen *and that screen returns a negative verdict*. To run the backtest
   anyway would discard the very evidence the /102 lesson tells us to trust, at material
   compute cost, to confirm a documented failure mode (the /102 IS-collapse / the /063
   mass-expansion IS-collapse). The brief's own Section 7 honest meta-prediction: the
   most likely thing a /103 backtest would do is spend compute to confirm the EDA's
   NULL-AT-EDA verdict.

3. **Fail-fast forbids a foreseeable-failure spend.** `feedback_fail_fast.md` — the
   cheap-kill discipline the /094/095/096/098/099/100 fail-fast EDAs established — directs
   that an axis a committed IS-only EDA conclusively kills is closed at the EDA: no
   `fetch`, no runner change, no backtest, no Critic, no agent dispatch. The honest move
   is to report the negative IS-predictive verdict with the numbers, which is what
   NULL-AT-EDA is.

No `src/` code was written — `V3_FEATURE_COLUMNS` stays at 14, bit-identical to /059;
there is nothing to revert. `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` were
untouched. Every Phase 1-5 measurement was strictly IS-only; the QR did not inspect the
post-cutoff OOS.

---

## 4. The formulaic-alphas axis closes at two data points

The user-directed WorldQuant-101 formulaic-alphas axis is now closed:

- **iter-v3/102** — literal alpha port (Kakushadze Alpha#32). **EXPLORATION-NEGATIVE** —
  IS collapse (F2 fires). ~18 alphas screened in the /102 EDA basket; the horse-race
  winner collapsed IS at the backtest.
- **iter-v3/103** — engineered composed features (/102-corrected: engineer, not port;
  IS-predictive screen, not OOS proxy). **NULL-AT-EDA** — 7 engineered candidates
  screened; the strongest is INERT-by-importance (rank 15/15 on the IS engine).

Across the two iterations ~25 candidates were screened — literal alphas and engineered
compositions, selected on both the OOS-leaning proxy (/102) and the corrected
IS-predictive screen (/103). None is viable. The /102-corrected /103 attempt removed the
specific methodological flaw the /102 closeout identified — and the corrected screen
returned an even more decisive negative (a conclusive at-EDA INERT verdict rather than a
backtest IS-collapse). The axis is closed.

**The structural read.** /103 is consistent with the recurring cycle-4 + cycle-5 finding:
*every* single-feature-addition axis to the v3 14-feature stack has failed —
the 7-FEED INERT verdict (funding ×4, microstructure ×1, basis ×1), /098 (off-the-shelf
families, NO-GO at EDA), /102 (a literal formulaic alpha, NEGATIVE-by-IS-collapse), and
now /103 (7 engineered composed features, NULL-AT-EDA-by-INERT). The binding constraint
is not the feature *family* — it is that the v3 per-symbol depth-3-5 LightGBM on a thin
8h triple-barrier signal has a saturated feature set; a 15th feature does not lift it and
tends to harm the IS fit. The training objective (/101), the model architecture
(/093/096/100), the label class structure (/099), the universe (/097), and now twice the
feature stack (/102 + /103) have all been attacked and closed.

---

## 5. Lessons

1. **An IS-predictive feature screen can — and should — kill a feature before a backtest.**
   The /102 closeout's central lesson was that a held-out-tail single-classifier accuracy
   proxy does not predict the multi-seed Optuna IS fit. /103 applied the correction: the
   screen is genuine IS feature→label IC, 3-symbol sign-consistency, quartile-resolution
   sub-period stability, and an IS-fold LightGBM gain-importance test — the
   gain-importance test in particular is a direct, cheap proxy for the exact question
   "will the multi-seed Optuna fit allocate split capacity to this feature." The screen
   returned a conclusive negative (rank 15/15 INERT on both IS-engine symbols), and the
   honest, fail-fast move is to act on it — close at the EDA rather than spend compute to
   reproduce a known failure mode. A NULL-AT-EDA on conclusive IS-predictive evidence is
   the risk-management design, not a process gap.

2. **The `tsrank_dispersion_ratio` case — a strong aggregate |IC| is not a stable
   relationship.** `tsrank_dispersion_ratio` had the basket's strongest mean |IC|
   (0.0992, ~3× alpha032) and was sign-consistent across symbols — superficially the
   best candidate. The quartile breakdown destroyed it: the aggregate number was an
   artifact of a thin 581-row LDO panel and per-symbol aggregation hiding within-symbol
   sign oscillation. This is the /102 trap in a different costume — a number that looks
   good in aggregate but does not reflect a stable IS relationship a multi-seed Optuna
   fit could consume. A feature screen must not stop at aggregate |IC|; sub-period
   (quartile-resolution) sign-stability on the IS-engine symbols is the binding test.

3. **Engineering a composed feature is necessary but not sufficient.** /103 correctly
   followed the `feedback_v3_engineered_features_proven.md` lesson — it engineered
   composed features encoding non-tree-representable interactions rather than porting
   literal alphas. But engineering the *form* right does not manufacture *signal*: 7
   well-constructed compositions all failed the IS-predictive screen, and the strongest
   was INERT. iter-v3/025's `regime_momentum_signed_5d` worked because the regime×momentum
   interaction it encodes carries genuine forward information; a composition's
   tree-non-representability is a property of its form, not evidence of its edge.

4. **The feature-stack frame is doubly closed for v3.** /103 is the second feature-stack
   axis to fail in cycle 5 alone (/102 + /103), and feature-addition has now failed across
   the 7-FEED verdict, /098, /102, and /103. The binding constraint
   (`feedback_v3_structural_over_knob_exploration.md`) is the thin per-symbol 8h
   triple-barrier signal; adding a 15th feature to the existing per-symbol architecture
   does not lift it. Future EXPLORATIONs should weight a *new edge source* or a *new
   architecture* over another feature on the existing stack — and on the cycle-4/5
   evidence (`feedback_fail_fast.md`), a new edge source requires a hard Phase-1 GO/NO-GO
   EDA before any build.

---

## 6. Next Iteration Ideas — cycle-5 EXPLORATION slot #4

The feature-stack frame is closed (the 7-FEED INERT verdict; /098 NO-GO; /102
NEGATIVE-by-IS-collapse; /103 NULL-AT-EDA-by-INERT). Per
`feedback_v3_structural_over_knob_exploration.md` and the /100/101/102 closeouts, the
recommended next axes for iter-v3/104, ranked:

1. **A genuinely new edge SOURCE requiring a data fetch + a hard Phase-1 GO/NO-GO EDA.**
   Funding rates, OI, and perp-spot basis are closed for v3 (/019/023/024/082/085/086).
   **Liquidation-cascade features** (`references/crypto-edge-deep.md`: self-exciting
   liquidation chaining, Hawkes-process intensity, long/short liquidation asymmetry) and
   **on-chain BTC-regime broadcasts** (Exchange Whale Ratio, MVRV-Z, NUPL/SOPR as a
   cross-asset regime input to the altcoin book) remain unattacked at the v3 per-symbol
   layer. These are genuinely new information layers, not a 16th OHLCV-derived feature.
   They MUST be killed-or-passed by a cheap committed IS-only GO/NO-GO EDA first
   (`feedback_fail_fast.md`) — the /094/095/096/098/099/100 cheap-kill pattern — before
   any `fetch` or build is committed. This is the top recommendation: it is the only
   axis class that attacks the binding constraint (a thin price-derived signal) by
   bringing in a non-price information source.

2. **A SAMPLE-WEIGHTING / LABEL-RECONSTRUCTION axis** (the /099/100 lineage
   recommendation, NOT yet cleanly exhausted). /101 closed the `weight_mode`
   rank-vs-magnitude rescale (SUSPICIOUS) and /099 closed the abstention triple-class
   label (NO-GO), but an AFML-Ch.4 uniqueness-weighted training objective combined with
   a magnitude-weighted sample weight — concentrating the existing thin signal at the
   training-objective level rather than re-partitioning the model or adding a feature —
   is gate-able with the same cheap held-out-fold horse-race harness the /099/100 EDAs
   built. Lower-priority than (1) because it is a model-side lever, and cycle-4/5
   evidence is that model-side levers do not lift a thin signal — but it is cheaper to
   GO/NO-GO than a new edge source and remains within the v3 mandate.

3. **Cycle-5 cadence and a CONFIRMATION-style re-validation.** Cycle 5 runs 10
   EXPLORATIONs before a CONFIRMATION (`feedback_v3_strict_10_to_1_cadence.md`); /103 is
   slot #3. Given that cycle 4 + cycle 5 have now produced a long run of
   NEGATIVE/NULL/SUSPICIOUS verdicts on every model-side and feature-side lever, the
   slot-#4 QR should also weigh — consistent with the /100 closeout's note — whether the
   remaining cycle-5 slots are best spent on further thin-signal levers or whether an
   earlier CONFIRMATION-style re-validation of the /059 baseline is the more honest use
   of compute. Per the user's standing "try a bit more" directive, axis (1) — the new
   edge source — is the recommended next altcoin axis.

Per `feedback_v3_axis_selection_quant_discipline.md`, the iter-v3/104 axis must be QR-led
with a committed `analysis/iteration_v3-104/*.py` EDA basis preceding the brief.

---

## 7. Commit chain

- EDA SHA: `e4d192d` — `analysis/iteration_v3-103/` (3 scripts: `candidate_lib.py`,
  `is_predictive_screen.py`, `is_importance_redundancy.py` + 6 result CSVs:
  `T1_is_panel_summary.csv`, `T2_is_directional_ic.csv`, `T4_is_subperiod_stability.csv`,
  `T2T4_screen_verdict.csv`, `T5_incumbent_redundancy.csv`, `T6_isfold_importance.csv`).
- Brief setup SHA: `a7386e7` — `briefs-v3/iteration_v3-103/research_brief.md` (the full
  10-section brief; Section 4 carries the NULL-AT-EDA recommendation).
- Diary SHA: this closeout — `docs(iter-v3/103): closeout diary — FILED NULL-AT-EDA / deep
  IS-only EDA proved no engineered candidate is IS-predictive`.
- Catalog update SHA: committed with this diary — `briefs-v3/exploration_catalog.md` /103
  row (classification NULL-AT-EDA).
- **No reports** (no backtest run — NULL-AT-EDA stopped the iteration at the EDA).
- **No `src/` change** (NULL-AT-EDA — nothing was implemented; `V3_FEATURE_COLUMNS` stays
  at 14, bit-identical to /059; nothing to revert).
- **Tag**: `v0.v3-103` — a closeout marker only, tagged by the orchestrator (NOT a
  baseline update — the `v0.v3-082`…`v0.v3-102` pattern; BASELINE_V3.md UNCHANGED at
  `v0.v3-059`, IS +1.0894 / OOS +0.5791).

iter-v3/103 is cycle-5 EXPLORATION slot #3; the cadence advances. iter-v3/104 is slot #4 —
the recommended NEW-EDGE-SOURCE iteration with a hard Phase-1 GO/NO-GO EDA (Section 6).

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` untouched. The walk-forward
embargo fix (`e149e9d`) is inherited unchanged. No cheating: the QR saw no OOS data —
no backtest was run; all Phase 1-5 EDA was strictly IS-only (`open_time < OOS_CUTOFF_MS`),
verified across the 3 committed EDA scripts.
