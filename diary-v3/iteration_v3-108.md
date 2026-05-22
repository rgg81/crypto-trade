# iter-v3/108 — Cycle-5 EXPLORATION slot #8 — META-LABELING DONE RIGHT (the /017-corrected experiment): a take/skip secondary model on a genuinely DISJOINT feature set — FILED NULL-AT-EDA — the gating EDA assembled a machine-checked-disjoint 18-feature meta set (the single discriminating fix vs /017) and then conclusively proved a meta-model CANNOT separate the primary model's IS winners from its IS losers (held-out AUC 0.56, sub-period-unstable, permutation p=0.18); no backtest was run

**Date**: 2026-05-19
**Type**: EXPLORATION (cycle-5 slot #8) — Phases 1-5 concluded at a NULL-AT-EDA verdict
**Verdict**: **NULL-AT-EDA** — iter-v3/108 was the /107 closeout's Recommendation #1 (TOP): a **meta-labeling secondary model** (López de Prado, AFML Ch. 3) — keep the primary per-symbol LightGBM's *direction* exactly as /059 produces it and add a **second binary classifier** whose only job is the *take / skip* triage on each primary signal. This is a re-attempt of iter-v3/017 (meta-labeling, closed EXPLORATION-NEGATIVE PATH C) — and it is **/017-CORRECTED**: /017's secondary model M2 was fed the SAME ~13 features M1 already used, so it had nothing orthogonal to learn (the /017 engineering report line 131 states the root cause verbatim). The /108 hard correction: the secondary model trains on a feature set **genuinely DISJOINT from `V3_FEATURE_COLUMNS`** — machine-checked zero name-overlap and low redundancy. The QR ran the mandated `feedback_fail_fast.md` Phase-1 GO/NO-GO EDA — 3 committed IS-only scripts under `analysis/iteration_v3-108/` (commit `698d52d`), 10 result tables T1–T9. The EDA fired the decisive pre-registered falsifier **F-AUC**: a disjoint-feature meta-model CANNOT separate the primary model's IS winners from its IS losers — held-out AUC 0.561 (< the 0.60 GO bar), sub-period-unstable [0.62, 0.67, 0.35], and a 200-shuffle permutation null places the observed AUC at the **q50 of the no-signal band** (p=0.18). No Phase-6 backtest was run.
**Classification**: **NULL-AT-EDA** — reserved for an axis the deep, committed, IS-only EDA conclusively proves dead before any backtest (the dispatch's high bar). Killing it at the EDA — rather than committing a `MetaLabelingStrategy` `src/` re-architecture with a disjoint-feature M2 and a 3-seed backtest to reproduce a documented failure — is the fail-fast WIN (`feedback_fail_fast.md`), not an iteration failure. Matches the /098/100/103/104/106/107 NULL-AT-EDA precedent.
**Decision**: **NO-MERGE.** BASELINE_V3.md UNCHANGED — canonical **`v0.v3-059`** (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**, 10-seed CONFIRMATION).
**Branch**: `iteration-v3/108`

---

## 1. The axis — and why it was the right one to test

iter-v3/108 is cycle-5 EXPLORATION slot #8. The axis is a **meta-labeling secondary model** — a binary take/skip classifier on the primary model's signals. It does not try to fix the directional calls and it does not try to fix the exits; it **triages** them — identifies which of the primary's calls to act on and which to skip, lifting the precision / win rate by dropping the unreliable calls. It is a selection / risk-layer axis, and it was the correct frontier on the convergent cycle-5 evidence.

**The /105→/106→/107 chain localized the binding constraint to the signal itself.** /105 falsified "the label is the binding constraint" (the trend-scanning label collapsed the IS fit −0.61 rather than lifting it). /106 falsified "the loss months are a detectable, stoppable regime" (no causal regime separator reaches a usable AUC; the loss months are a **win-rate** problem). /107 falsified "the win-rate problem is an exit-timing artifact" (the static triple-barrier is not leaking profit at PF 1.48; no dynamic exit rescues the losers — best design: 0 rescued, 23 clipped). The /107 closeout's decisive meta-finding: **the v3 loss months are genuine directional-call quality** — the model's calls are simply wrong more often, and no re-architecture of the label, the regime overlay, or the exit can manufacture edge the call did not contain.

Given that diagnosis, there are exactly two ways to attack the constraint: (1) make the primary model's calls *better* (the entire training side — features ×4 families, derivative/on-chain data, model architecture ×4, training objective, label class, label geometry, universe — comprehensively closed across /016/082/085/086/093/096–105); or (2) **identify which calls to trust and skip the rest.** Route 2 had been attempted exactly once — /017 — and failed for a now-understood, correctable reason. A meta-label filter is a structurally different attack on the precise constraint the convergent chain localized. It deserved — and got — a deep IS-only gating EDA. Per `feedback_v3_axis_selection_quant_discipline.md` the axis was QR-led: the committed EDA (3 scripts, commit `698d52d`) preceded any brief. **The EDA's verdict is the finding of this iteration.**

## 2. Why this is NOT a re-tread of iter-v3/017 — the precise /017-correction

iter-v3/017 ran a meta-labeling layer and closed **EXPLORATION-NEGATIVE, PATH C (over-filter)**: M2 vetoed 42.7% of M1 candidates but the kept trades showed no quality lift, and IS Sharpe dropped −0.48. It would be a methodology failure to re-propose the identical experiment. It is *not* the identical experiment. The /017 engineering report states the root cause in plain terms (line 131):

> *"The meta-label signal is not learnable from the same 13 features M1 already used — the precision-residual is uncorrelated with any accessible feature at this EXPLORATION budget."*

A secondary model fed the primary model's own feature set is asked to find structure in the *residual* of a fit those very features already produced — by construction it has almost nothing orthogonal to learn. /017 did not falsify meta-labeling; it falsified *meta-labeling with a redundant feature set.*

**The /108 correction, concretely and machine-checked.** The /108 secondary model must train on a feature set **genuinely DISJOINT from `V3_FEATURE_COLUMNS`** — and the gating EDA's first job (script 1) was to assemble that set and *prove* the disjointness, not assert it. This is the single discriminating fix vs /017, and it is verified, not claimed.

## 3. The gating EDA — 3 committed IS-only scripts, the design, why it is cheap and decisive

Meta-labeling is uniquely cheap to pre-test because the secondary model's entire training target already exists in the /059 IS roster: each trade's `is_winner` outcome (the binary primary-call result) is the meta-label. The EDA never needs to retrain the primary model — it joins candidate disjoint features onto the existing /059 IS trade entries and asks whether a secondary model can separate the winners from the losers.

Three committed scripts under `analysis/iteration_v3-108/` (commit `698d52d`):

- **`meta_feature_disjoint.py`** — the F-DISJOINT gate. Assembles the candidate disjoint meta-feature set; machine-checks (G1) zero column-name overlap with the 14 `V3_FEATURE_COLUMNS` and (G2) low aggregate redundancy (max |Pearson rho| vs the primary stack, on IS feature rows). Outputs T1–T3b.
- **`meta_model_auc.py`** — the **DECISIVE F-AUC test**. Joins the disjoint features onto every /059 IS trade entry, fits a depth-4 LightGBM (the v3 architecture depth) on `is_winner`, chronological 70/30 IS split, and reports the **held-out winner-vs-loser separation AUC** + sub-period stability. Outputs T4–T7.
- **`meta_model_robustness.py`** — the capacity-artifact control. Re-runs the F-AUC test across 5 model capacities (stump → depth-4 → logistic) and a 200-shuffle permutation null, so the NULL cannot be dismissed as an over-capacity artifact. Outputs T8–T9.

**The IS-only invariant.** Every script asserts at load `(trades["open_time"] < OOS_CUTOFF_MS).all()` and `(features["close_time"] < OOS_CUTOFF_MS).all()` with `OOS_CUTOFF_MS = 1742774400000` (2025-03-24). The roster is the canonical /059 10-seed unified-ensemble IS trade roster — `reports-v3/iteration_v3-059/in_sample/trades.csv`, **171 IS trades**. The disjoint features are drawn from the 85-column `data/features_v3/<SYM>_8h_features.parquet` (the production feature pipeline; every column trailing-window and causal). The post-cutoff OOS roster and OOS feature data were **never read** — the QR did not inspect OOS in Phases 1-5 (and, on the NULL-AT-EDA verdict, Phase 7 does not occur).

**The causal join key.** The /059 trade `open_time` (e.g. `1643587199999`) matches the feature parquet's `close_time` exactly (verified 83/83 for BCH, 171/171 joined overall, 0 unmatched). A v3 trade enters at a candle's *close*; that candle's trailing-window features are the causal signal known at the entry instant. Joining the meta-features on the entry-candle `close_time` is the correct causal join — bar `t` uses only data ≤ `t`. The 18-dim meta-feature vector at each trade is exactly the orthogonal context available to a take/skip decision the moment the primary model fires.

## 4. The EDA result — F-DISJOINT does not fire (the /017-correction succeeds); F-AUC fires (meta-labeling is dead)

### T1–T3b — the disjoint meta-feature set: F-DISJOINT does NOT fire — a genuinely orthogonal set was assembled

`meta_feature_disjoint.py` first assembled a 22-candidate set spanning 5 families chosen specifically to answer "is this a *hard call*" (the precision residual) rather than "*which way* does price go" (the directional signal the primary already extracts): regime context the 14-feature stack under-weights, volatility/dispersion state, microstructure/order-flow, funding/derivative context, and calendar context.

The G2 redundancy check (`T3b_redundancy_summary.csv`) then **enforced the /017-correction**: 4 of the 22 candidates had max |rho| > 0.70 against the primary stack — they *measure the same thing the primary already sees*, which is exactly the /017 failure mode. They were dropped:

| dropped meta-feature | max \|rho\| | vs primary feature |
|---|---:|---|
| `close_pos_in_range_20` | **0.91** | `vwap_dev_20` |
| `hurst_drift_50_200` | **0.87** | `hurst_diff_100_50` |
| `sym_vs_btc_vol_14d` | **0.76** | `range_realized_vol_50` |
| `candle_efficiency_20` | **0.72** | `vwap_dev_20` |

The retained **18 disjoint meta-features** (`hurst_200, adx_14, btc_vol_14d, cross_asset_divergence_norm, vol_regime_x_momentum, vol_transition_slope_20, atr_pct_rank_200, bb_width_pct_rank_100, parkinson_gk_ratio_20, volume_cv_50, range_efficiency_50, taker_buy_imbalance_20, obv_slope_50, funding_rate_zscore_30, funding_sign_persist_9, basis_zscore_30, candle_dow_sin, candle_dow_cos`):

| F-DISJOINT gate | result |
|---|---|
| **G1** — name-overlap with `V3_FEATURE_COLUMNS` | **0 columns** — PASS (fully disjoint) |
| **G2** — max \|rho\| vs the 14 primary features | **0.5709** (`volume_cv_50` vs `ret_kurt_50`) < 0.70 — PASS |

**F-DISJOINT does NOT fire.** A genuinely disjoint, non-redundant 18-feature secondary set was assembled and machine-verified — the single discriminating fix vs /017 was delivered. The disjoint set is real; whatever /108 finds is NOT the /017 redundancy artifact.

### T4–T5 — the decisive test: F-AUC FIRES — a disjoint-feature meta-model CANNOT separate the primary's winners from its losers

`meta_model_auc.py` joined the 18 disjoint features onto all 171 /059 IS trades (71 winners / 100 losers, WR 41.5%), fit the depth-4 LightGBM meta-model (5-seed-averaged) on `is_winner`, chronological 70/30 IS split (train = oldest 119, validation = newest 52), and measured the held-out winner-vs-loser ROC-AUC.

| split | train AUC | **held-out AUC** | GO bar |
|---|---:|---:|---|
| chronological 70/30 | 1.000 | **0.561** | ≥ 0.60 — **FAIL** |

The held-out AUC is **0.561** — below the 0.60 GO bar. The `train_auc = 1.000` shows the depth-4 model *memorizes* the 119-trade training fold completely and yet generalizes to 0.56 — the disjoint features carry essentially no information the meta-model can project onto unseen trades.

Sub-period stability (`T5_subperiod_stability.csv`) — the held-out AUC of each of 3 disjoint chronological IS thirds, each itself split 70/30:

| sub-period | held-out AUC | n_val |
|---|---:|---:|
| sub_period_1 (earliest) | 0.6154 | 18 |
| sub_period_2 (middle) | 0.6667 | 18 |
| sub_period_3 (latest) | **0.3500** | 18 |

The sub-period AUCs are **unstable** — they swing from 0.67 to 0.35, and the latest third (0.35) is *below* the 0.50 no-skill line: in the most recent IS period the disjoint-feature meta-model would have ranked losers *above* winners. **F-AUC fires on both criteria** — the headline held-out AUC is below 0.60 AND the separation is not sub-period-stable.

### T6 — what the meta-model "used": the importance is spread thin, no dominant separator

`T6_meta_feature_importance.csv`: the top-5 meta-features by gain were `adx_14, btc_vol_14d, basis_zscore_30, parkinson_gk_ratio_20, funding_rate_zscore_30` — a mix of regime, vol-state and funding context, importance spread broadly with no single feature dominating. This is the importance signature of a model fitting *noise* on the training fold: there is no concentrated orthogonal separator, because there is no orthogonal separator.

### T7 — the threshold trade-off: even at the most aggressive threshold the win-rate lift is thin and costly

`T7_threshold_tradeoff.csv` swept the M2 confidence threshold on the held-out fold (base WR 0.4615):

| M2 threshold | frac kept | WR kept | WR lift |
|---:|---:|---:|---:|
| 0.40 | 0.462 | 0.458 | −0.003 |
| 0.45 | 0.442 | 0.478 | +0.017 |
| 0.50 | 0.404 | 0.524 | +0.062 |
| 0.55 | 0.385 | 0.550 | +0.089 |
| 0.60 | **0.288** | 0.600 | +0.139 |

Even at threshold 0.60 the win-rate lift is only +0.139 — and it costs dropping 71% of trades, which would crater the bundle-level trade-rate floor. This is exactly the thin, threshold-dependent, marginal effect an AUC near the no-skill line produces. There is no threshold at which the filter is both materially precision-lifting and trade-rate-viable.

### T8–T9 — the robustness annex: the NULL is NOT a capacity artifact

The headline depth-4 model overfit the training fold (`train_auc = 1.0`), so `meta_model_robustness.py` ruled out the possibility that the NULL is a *capacity* artifact (an over-capacity model overfitting noise IS, deflating the held-out AUC below the meta-label's true power).

`T8_capacity_sweep.csv` — the F-AUC test re-run across 5 model capacities:

| model | held-out AUC | sub-period AUCs | min sub-AUC |
|---|---:|---|---:|
| LightGBM stump (depth 1, n=50) | **0.5997** | [0.50, 0.50, 0.50] | 0.50 |
| LightGBM depth 2, n=100, reg | 0.5893 | [0.50, 0.50, 0.50] | 0.50 |
| LightGBM depth 3, n=150, reg | 0.5878 | [0.68, 0.51, 0.20] | 0.20 |
| LightGBM depth 4, n=200 | 0.5610 | [0.62, 0.67, 0.35] | 0.35 |
| Logistic (C=0.5, balanced) | 0.4464 | [0.17, 0.31, 0.56] | 0.17 |

**No model capacity clears the GO bar.** The best held-out AUC across the entire sweep is **0.5997** (the depth-1 stump) — and even that 0.5997 fails the "≥ 0.60 *and* sub-period-stable" GO criterion (the stump's flat 0.50 sub-period AUCs mean it learned nothing within any sub-period). The shallow regularized models hover at 0.59 with degenerate sub-periods; the linear logistic baseline is actively *below* 0.50. **0 of 5 capacities clear the GO bar.**

`T9_permutation_null.csv` — the decisive statistical control. The depth-3 regularized model's observed held-out AUC was compared against a 200-shuffle permutation null (training-fold `is_winner` labels permuted, model re-fit, AUC re-scored):

| quantity | value |
|---|---:|
| observed held-out AUC | 0.5878 |
| permutation null mean AUC | 0.5030 |
| permutation null q05 | 0.3542 |
| permutation null **q50** | **0.5030** |
| permutation null q95 | 0.6741 |
| **permutation p-value** | **0.18** |

The observed AUC of 0.5878 sits essentially *at the q50* of the no-signal null band [0.35, 0.67], and the permutation p-value is **0.18** — the observed winner-vs-loser separation is **statistically indistinguishable from random**. Under the no-signal null, an AUC of 0.5878-or-better occurs 18% of the time by chance alone.

### EDA verdict — F-DISJOINT clears, F-AUC fires decisively — the axis is dead

The /017-corrected meta-labeling axis is **conclusively falsified** before any backtest:

1. **F-DISJOINT does NOT fire.** The /017-correction succeeded — an 18-feature secondary set with zero name-overlap and max |rho| 0.57 against the primary stack was machine-assembled. Whatever /108 finds is not the /017 redundancy artifact; the disjoint set is real and genuinely orthogonal.
2. **F-AUC FIRES.** A meta-model trained on that genuinely-disjoint set CANNOT separate the primary model's IS winners from its IS losers: held-out AUC 0.561 < 0.60; sub-period-unstable [0.62, 0.67, 0.35] with the latest third below the no-skill line; 0 of 5 model capacities (stump → depth-4 → logistic) clear the GO bar; the permutation null places the observed AUC at the q50 of the no-signal band with p=0.18.

There is no take/skip triage of the primary model's calls that is learnable from orthogonal information on this roster. The honest verdict is **NULL-AT-EDA**.

## 5. The decisive meta-finding — the primary model's directional errors are NOT predictable from orthogonal information

This is the most informative output of /108, and it is what makes the iteration a substantive contribution rather than a dead end.

The /017 closeout left a clean, specific open question: /017 failed because its M2 saw the same features as M1 — *would a meta-model fed genuinely orthogonal information be able to triage M1's calls?* iter-v3/108 was the decisive test of that question, and it **answers it: no.**

- The /017-correction was delivered and verified — the 18-feature meta set is machine-checked disjoint (G1, G2 both PASS). This is not /017's redundant feature set; the experiment /017 could not run was run.
- A meta-model on that disjoint set separates the primary's IS winners from its IS losers at AUC 0.56 — below the GO bar, sub-period-unstable, and statistically at the q50 of the no-signal permutation band (p=0.18).
- This holds across every model capacity from a depth-1 stump to a depth-4 tree to a linear logistic baseline. It is not a tuning failure and it is not a capacity failure.

**Therefore the primary model's directional errors are not predictable from orthogonal information.** When the per-symbol 8h LightGBM makes a call, *whether that call will win or lose* is not encoded — to any IS-detectable, sub-period-stable degree — in the regime context, the volatility state, the microstructure, the funding context, or the calendar. The primary model's losers do not sit in an identifiably different orthogonal-feature neighborhood from its winners. /017's NEGATIVE verdict was *not* an artifact of its redundant feature set — it **generalizes**: meta-labeling is dead for v3, and now for a fully understood and verified reason.

This is a profound finding because it removes the *last* selection-layer escape route. If the errors were predictable from orthogonal information, a meta-label filter would have lifted the precision; they are not, so no filter can. The next iteration's only remaining route is to attack the **primary model's own representational capacity** — to make the calls better, not to triage them.

### The /105 → /106 → /107 → /108 convergent chain — v3's binding constraint is the primary model's representational capacity

iter-v3/105–108 form a **four-step convergent falsification chain** that has, step by step, eliminated every candidate explanation for the thin v3 signal *other than the primary model's own predictive capacity*:

- **/105 falsified "the label / the estimand is the binding constraint."** A trend-scanning label the 14 features predict 31–52% *better* collapsed the IS fit −0.61. Re-framing *what the model is trained to predict* does not fix v3.
- **/106 falsified "the loss months are a detectable / stoppable regime."** No causal regime separator reaches a usable AUC; a trailing-drawdown brake is IS-Sharpe-negative. The loss months are a **win-rate** phenomenon, not an OOD condition.
- **/107 falsified "the win-rate problem is an exit-timing artifact."** The static triple-barrier is not leaking profit (PF 1.48); no dynamic exit rescues the losers (best design: 0 rescued, 23 clipped). The low win rate is genuine directional-call quality.
- **/108 falsifies "the bad calls can be triaged out by a selection model."** A meta-model on a genuinely-disjoint 18-feature set cannot separate the primary's winners from its losers (held-out AUC 0.56, permutation p=0.18). The errors are not predictable from orthogonal information.

The four iterations are not four unrelated nulls — they are a **localization**. /105 cleared the label. /106 cleared the regime/risk-overlay layer. /107 cleared the exit/trade-construction layer. /108 cleared the selection/triage layer. What the chain has *not* cleared, and what it now points at with near-certainty, is the **primary model's own directional accuracy — its representational capacity.** The signal is thin because the per-symbol 8h LightGBM, fed the 14 features, simply does not extract a sharper directional edge — and that is the one thing the chain has not yet attacked directly. **iter-v3/109 must attack the primary model's representational capacity itself** (Section 7).

## 6. The verdict — NULL-AT-EDA, no backtest — the fail-fast justification

The dispatch reserves NULL-AT-EDA for "an axis the deep EDA conclusively proves dead (high bar)." The /108 EDA clears that bar — a three-script, ten-table, strictly-IS-only gating EDA that delivered the /017-correction (F-DISJOINT PASS) and then fired the decisive F-AUC falsifier on four independent axes (held-out AUC below bar, sub-period instability, capacity-sweep universality, permutation-null indistinguishability). No backtest was run, for three binding reasons:

1. **The gating EDA IS the decisive test of the axis.** Meta-labeling's whole premise is that a secondary model can separate the primary's good calls from its bad ones. The EDA measures exactly that — the held-out winner-vs-loser AUC on the genuinely-disjoint feature set — and it returns 0.56, indistinguishable from no-signal. A Phase-6 backtest of a `MetaLabelingStrategy` with a disjoint-feature M2 would re-derive this same negative (a filter built on a 0.56-AUC discriminator cannot lift precision) at the cost of an `src/` re-architecture and a 3-seed run.
2. **A backtest would knowingly reproduce a documented failure.** The pre-registered falsifier F-AUC is the gate, and it fires unambiguously and robustly. To build the disjoint-feature M2 into `MetaLabelingStrategy` and run the backtest anyway would spend compute and an `src/` re-architecture to manufacture a confirmation-shaped artifact around a hypothesis the cheap EDA has already killed — and it would repeat /017's spend with a foreseeable outcome.
3. **Fail-fast forbids a foreseeable-failure spend.** `feedback_fail_fast.md` — the cheap-kill discipline of the /094–107 fail-fast EDAs — directs that an axis a committed IS-only EDA conclusively kills is closed at the EDA: no `src/` change, no runner change, no backtest, no Critic, no agent dispatch. The honest move is to report the negative verdict with the numbers, which is what NULL-AT-EDA is.

No `src/` code was written — there is no disjoint-feature `MetaLabelingStrategy`; `src/crypto_trade/strategies/ml/metalabeling.py` (the /017 class) is untouched and unused; `V3_FEATURE_COLUMNS` stays at 14; the primary model / triple-barrier label / universe / 7-gate RiskV2 stack are all /059-identical; there is nothing to revert. The meta-feature construction and the meta-model AUC test live entirely inside the three committed `analysis/iteration_v3-108/` EDA scripts (pure pandas + a stock LightGBM/sklearn fit — no new dependency, no production wiring). `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` were untouched. Every Phase 1-5 measurement was strictly IS-only; the QR did not inspect the post-cutoff OOS.

## 7. Lessons

1. **The primary model's directional errors are NOT predictable from orthogonal information — meta-labeling is dead for v3, for a verified reason.** This is the central finding. The /017-correction was delivered and machine-verified — an 18-feature secondary set with zero name-overlap and max |rho| 0.57 vs the primary stack. A meta-model on that genuinely-disjoint set separates the primary's IS winners from its IS losers at held-out AUC 0.56 — below the 0.60 GO bar, sub-period-unstable, and at the q50 of a no-signal permutation null (p=0.18), across every capacity from a stump to a depth-4 tree to a logistic baseline. /017's NEGATIVE verdict was not an artifact of its redundant feature set; it generalizes. The selection-layer escape route is closed.

2. **A re-attempt of a NEGATIVE axis must change the one thing that broke it — and must VERIFY the change before spending compute.** /108 did not re-run /017; it identified /017's exact root cause (M2 fed M1's own features), designed the precise correction (a disjoint feature set), and made the EDA's *first gate* a machine-check that the correction was real (F-DISJOINT: G1 zero overlap, G2 max |rho| < 0.70). The 4 redundant candidates that would have re-created /017's failure (`close_pos_in_range_20` at rho 0.91, etc.) were caught and pruned by that gate *before* the decisive test. A re-attempt whose corrective change is asserted rather than verified is just the original experiment with a new label.

3. **Build the permutation null into any "can a model separate X from Y" EDA.** The headline depth-4 meta-model overfit the training fold (`train_auc = 1.0`) — a held-out AUC of 0.56 from such a model could, naively, be argued to *understate* a real signal. The capacity sweep (stump → logistic) and the 200-shuffle permutation null settled it conclusively: 0 of 5 capacities clear the GO bar, and the observed AUC sits at the q50 of the no-signal band. An AUC near 0.55–0.60 is *exactly* the range where a permutation null is decisive and an eyeballed threshold is not — the null converts "AUC 0.56, is that signal?" into "p=0.18, no." Future separability EDAs should make the permutation null mandatory.

4. **A higher win rate at a costly threshold is not a usable filter.** The T7 threshold sweep showed the disjoint-feature meta-model *can* lift the held-out win rate to 0.60 (+0.139) — but only by dropping 71% of trades. This echoes the /107 lesson ("a higher win rate is not a higher Sharpe") in the selection layer: a filter that buys precision only by collapsing the trade count is not viable against the bundle-level trade-rate floor. When the AUC is near the no-skill line, every threshold is a bad trade-off — there is no operating point that is both precision-lifting and trade-rate-viable.

5. **A convergent falsification chain is a localization, not four dead ends.** /105, /106, /107, /108 each closed a different candidate explanation for the thin v3 signal — the label, the regime/risk layer, the exit layer, the selection layer. Read together they are not four failures; they are a process of elimination that has localized the constraint to the primary model's own representational capacity. "The search is exhausted" is the forbidden — and factually wrong — read: the chain has *cornered* the problem. The next axis must attack the cornered thing directly.

## 8. Next Iteration Ideas — iter-v3/109 (cycle-5 EXPLORATION slot #9)

**The diagnosis is now maximally sharp.** The /105→/106→/107→/108 chain has localized v3's binding constraint to **the primary per-symbol 8h LightGBM's representational capacity** — its ability, fed the 14 `V3_FEATURE_COLUMNS`, to extract a sharper directional edge. Not the label (/105), not a detectable regime (/106), not the exit geometry (/107), not a triage-able selection residual (/108). Every prior axis attacked an input to, an estimator of, the label of, the execution of, or a *filter on* a fixed signal. **iter-v3/109 must attack the signal-generation capacity itself.**

### Recommendation #1 (TOP) — primary-model representational capacity: a regime-conditional model ensemble

This is the /107 closeout's pre-registered runner-up, and the /108 NULL promotes it to the top axis exactly as the /107 closeout specified ("if /108 fires F-AUC … the only remaining route is to attack the primary model's own directional accuracy"). The axis: rather than one per-symbol LightGBM trained across all market regimes, train *separate* per-symbol models conditioned on a coarse, causally-known regime partition (BTC trend-up / trend-down / chop, or a realized-vol tercile), and route each bar's prediction to the model trained on the regime that bar is in. The hypothesis: the thin v3 signal is partly an **averaging artifact** — a single model fit across heterogeneous regimes learns a *blurred* directional rule, and a regime-specialized model would call its own regime more accurately. This is distinct from the closed regime *kill switch* (primitive 9) — it does not *stop* trading in a regime, it *specializes the predictor* per regime.

**The EDA-gateable test.** Per `feedback_fail_fast.md` + `feedback_v3_axis_selection_quant_discipline.md`, /109 must carry a committed `analysis/iteration_v3-109/*.py` IS-only GO/NO-GO EDA preceding the brief. The decisive IS-only test: partition the IS bars by the causal regime label; for each regime, measure the **feature→label predictive IC (or a cross-validated within-regime AUC)** of a model *trained only on that regime's bars*, and compare it to the pooled model's IC *restricted to the same bars*. GO bar: the regime-specialized models achieve a materially higher within-regime IC than the pooled model on at least 2 of 3 regimes — i.e. specialization recovers signal that pooling blurs away. If the per-regime IC is no better than the pooled IC (the regimes are not the source of the blur), that is itself a finding — it would mean the primary model's capacity ceiling is not a regime-averaging artifact, redirecting /110 to the feature representation itself (a learned-representation / deeper-model axis).

### Recommendation #2 (runner-up) — a fundamentally different primary learner on the same 14 features

If the /109 regime-conditional EDA fires NO-GO — the signal ceiling is *not* a regime-averaging artifact — then the constraint is the **representational form** of the primary learner: a depth-3-5 gradient-boosted tree on 14 tabular features may simply have hit its capacity ceiling for this problem. The runner-up axis tests a structurally different primary learner with the *same* 14-feature input and the *same* triple-barrier label — e.g. a small temporal model (a shallow 1D-CNN / GRU over a short lookback window of the 14 features, capturing sequential structure a per-bar tree discards) or a feature-interaction-explicit model. The /016 XGBoost head-to-head closed the *tree-vs-tree* model-architecture axis — this is not that; it is a *non-tree, sequence-aware* learner, a genuinely different representational class. Its EDA would measure, IS-only, whether a sequence model achieves a higher held-out directional AUC than the per-bar tree on the identical feature/label data.

Both recommendations attack the **primary model's representational capacity** the /105→/106→/107→/108 chain has localized as v3's binding constraint — #1 by specializing the predictor per regime, #2 by changing the learner's representational class — not another input, label, exit, or filter on a fixed signal, which is exactly what the convergent-chain evidence demands. Per `feedback_v3_axis_selection_quant_discipline.md` the iter-v3/109 axis must be QR-led with a committed `analysis/iteration_v3-109/*.py` EDA basis preceding the brief; per `feedback_fail_fast.md` it must carry the hard Phase-1 GO/NO-GO EDA before any `src/` build.

## 9. Commit chain

- EDA SHA: `698d52d` — `analysis/iteration_v3-108/` (3 scripts: `meta_feature_disjoint.py`, `meta_model_auc.py`, `meta_model_robustness.py`; 10 result CSVs: `T1_meta_feature_catalog.csv`, `T2_overlap_check.csv`, `T3_redundancy_matrix.csv`, `T3b_redundancy_summary.csv`, `T4_meta_model_auc.csv`, `T5_subperiod_stability.csv`, `T6_meta_feature_importance.csv`, `T7_threshold_tradeoff.csv`, `T8_capacity_sweep.csv`, `T9_permutation_null.csv`).
- EDA hygiene SHA: `1b85bd1` — drop an accidentally-committed `__pycache__` artifact.
- Diary SHA: this closeout — `docs(iter-v3/108): closeout diary — FILED NULL-AT-EDA — /017-corrected meta-labeling FALSIFIED — a disjoint-feature meta-model cannot separate the primary's IS winners from its losers (held-out AUC 0.56, permutation p=0.18); the binding constraint is the primary model's representational capacity`.
- Catalog update SHA: committed with this diary — `briefs-v3/exploration_catalog.md` /108 row (classification NULL-AT-EDA).
- **No reports** (no backtest run — NULL-AT-EDA stopped the iteration at the EDA).
- **No `src/` change** (NULL-AT-EDA — nothing was implemented; the /017 `MetaLabelingStrategy` class is untouched and unused; `V3_FEATURE_COLUMNS` stays at 14; the primary model / triple-barrier label / universe / 7-gate RiskV2 stack are all /059-identical; nothing to revert).
- **No brief** (NULL-AT-EDA at the gating EDA — the iteration concluded at Phase 1 before a Phase-5 brief was written; the 3 EDA scripts and this diary are the iteration's record).
- **Tag**: `v0.v3-108` — a closeout marker only, tagged by the orchestrator (NOT a baseline update — the `v0.v3-082`…`v0.v3-107` pattern; BASELINE_V3.md UNCHANGED at `v0.v3-059`, IS +1.0894 / OOS +0.5791, 10-seed CONFIRMATION).

iter-v3/108 is cycle-5 EXPLORATION slot #8; the cadence advances. iter-v3/109 is slot #9 — the recommended primary-model representational-capacity axis (a regime-conditional model ensemble) with a hard Phase-1 GO/NO-GO EDA (Section 8), attacking the primary model's representational capacity the /105→/106→/107→/108 convergent chain has localized as v3's binding constraint.

**NO CHEATING.** `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` untouched. The walk-forward embargo fix (`e149e9d`) is inherited unchanged. This EXPLORATION does NOT update BASELINE_V3.md regardless of outcome — `v0.v3-108` is a closeout marker only. All Phase 1-5 EDA was strictly IS-only (`open_time < OOS_CUTOFF_MS` for the /059 trade roster, `close_time < OOS_CUTOFF_MS` for every feature row entering any computation — each of the 3 committed EDA scripts asserts the IS-only invariant at load); the QR did not inspect the post-cutoff OOS — no backtest was run.
