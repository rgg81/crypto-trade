# iter-v3/109 — Cycle-5 EXPLORATION slot #9 — REPRESENTATIONAL CAPACITY: a neural / higher-capacity model class vs the depth-3-5 LightGBM on the identical 14 features — FILED NULL-AT-EDA — the gating EDA ran a walk-forward-faithful 4-class horse race AND a 100-shuffle permutation null on the v3 primary model and conclusively proved the 14-feature representation carries NO IS-detectable directional signal, for ANY model class; no backtest was run — and /109 is the TERMINAL finding of the /105→/106→/107→/108→/109 convergent chain

**Date**: 2026-05-19
**Type**: EXPLORATION (cycle-5 slot #9) — Phases 1-5 concluded at a NULL-AT-EDA verdict
**Verdict**: **NULL-AT-EDA** — iter-v3/109 was the /108 closeout's Recommendation #1 (TOP): attack the primary model's **representational capacity** itself. The /105→/106→/107→/108 convergent chain had localized v3's binding constraint to the primary per-symbol 8h LightGBM's representational capacity — its ability, fed the 14 `V3_FEATURE_COLUMNS`, to extract a sharper directional edge. /109 tested whether a higher-capacity / different-class model — a neural model (MLP), a temporal-window MLP (a TCN proxy for the sequential structure a per-bar tree discards) — extracts MORE signal than the depth-3-5 LightGBM on the **identical 14 features** against the /059 triple-barrier label. The QR ran the mandated `feedback_fail_fast.md` Phase-1 GO/NO-GO EDA — 2 committed IS-only scripts plus a shared /059-faithful labeler under `analysis/iteration_v3-109/` (commit `4f77b1a`), 9 result tables T1–T9 — a walk-forward-faithful, embargo-purged horse race. The EDA fired the decisive falsifier on every axis: **every neural class is WORSE than the tree** (pooled held-out AUC: LightGBM 0.4993, MLP 0.4891, temporal MLP 0.4836); a 5-capacity MLP sweep — **0 of 5 beat the tree**; and the decisive control — a **100-shuffle permutation null on the LightGBM itself** places the observed real-label held-out AUC of 0.497 **at the q50** of the no-signal band [0.483, 0.523], **permutation p=0.64**. No Phase-6 backtest was run.
**Classification**: **NULL-AT-EDA** — reserved for an axis the deep, committed, IS-only EDA conclusively proves dead before any backtest (the dispatch's high bar). Killing it at the EDA — rather than committing a neural `src/` strategy and a 3-seed backtest to reproduce a documented, permutation-confirmed no-signal result — is the fail-fast WIN (`feedback_fail_fast.md`), not an iteration failure. Matches the /098/100/103/104/106/107/108 NULL-AT-EDA precedent.
**Decision**: **NO-MERGE.** BASELINE_V3.md UNCHANGED — canonical **`v0.v3-059`** (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**, 10-seed CONFIRMATION).
**Branch**: `iteration-v3/109`

---

## 1. The axis — and why it was the right (and the last reachable) one to test

iter-v3/109 is cycle-5 EXPLORATION slot #9. The axis is the **primary model's representational capacity** — and it was the correct, and the *terminal*, frontier on the convergent cycle-5 evidence.

**The /105→/106→/107→/108 chain localized the binding constraint to the signal-generation capacity itself.** Each of the prior four iterations closed one candidate explanation for the thin v3 signal:

- **/105 falsified "the label / the estimand is the binding constraint."** A trend-scanning label the 14 features predict 31–52% *better* (robustness-checked, Wilcoxon p=0.013) *collapsed* the IS fit −0.61 rather than lifting it. Re-framing what the model is trained to predict does not fix v3.
- **/106 falsified "the loss months are a detectable / stoppable regime."** No causal regime separator (11 candidates, Mahalanobis OOD at 3 reference lengths) reaches a usable AUC; a trailing-drawdown brake is IS-Sharpe-negative at every trigger. The loss months are a **win-rate** phenomenon.
- **/107 falsified "the win-rate problem is an exit-timing artifact."** The static triple-barrier is not leaking profit (PF 1.48); no dynamic exit rescues the losers (best design: 0 rescued, 23 clipped). The low win rate is genuine directional-call quality.
- **/108 falsified "the bad calls can be triaged out by a selection model."** A meta-model on a genuinely-disjoint 18-feature set cannot separate the primary's winners from its losers (held-out AUC 0.56, permutation p=0.18). The errors are not predictable from orthogonal information.

The four iterations are not four unrelated nulls — they are a **localization**. Read together they corner v3's binding constraint to one place the chain had *not* yet attacked directly: the **primary per-symbol 8h LightGBM's representational capacity** — its ability, fed the 14 features, to extract a sharper directional edge. v3's one PROMISING feature ever (iter-v3/025's `regime_momentum_signed_5d`, a hand-*composed* interaction `ret_5d × sign(hurst_100 − 0.5)`) was direct prior evidence that depth-3-5 trees fail to compose the interactions that carry signal — which made "try a model class that *can* compose them" the precise, evidence-backed next axis.

Every prior axis attacked an input to, an estimator of, the label of, the execution of, or a filter on a fixed signal. iter-v3/109 attacked the **signal-generation capacity** itself — and per the /108 closeout's pre-registration it was QR-led: the committed EDA (2 scripts + a shared labeler, commit `4f77b1a`) preceded any brief. **The EDA's verdict is the finding of this iteration.**

## 2. The gating EDA — 2 committed IS-only scripts, the design, why it is decisive

The representational-capacity question is cleanly EDA-gateable: the EDA can run a **walk-forward-faithful horse race** — fit every candidate model class on the identical IS folds, on the identical 14 features, against the identical /059 triple-barrier label, and measure the held-out predictive AUC directly. No `src/` strategy and no backtest is needed to answer "does a higher-capacity model extract more signal" — the held-out AUC *is* that answer.

Two committed scripts plus a shared loader under `analysis/iteration_v3-109/` (commit `4f77b1a`):

- **`_shared.py`** — the IS-only data loader + the /059-faithful labeler. Loads each symbol's 8h feature parquet, gates strictly to `close_time < OOS_CUTOFF_MS`, and replicates `labeling.label_trades` (`label_mode="triple_barrier"`) exactly — ATR triple-barrier (`atr_tp=2.0` / `atr_sl=1.0`, ATR column `natr_21_raw`, 21-candle / 10080-min timeout, fee 0.1%, adverse-first intra-bar tie-break). The label is `sign(better-of long_pnl / short_pnl)` — the directional target the v3 primary model is trained to predict. `make_walk_forward_folds` builds 8 expanding-window folds, each embargo-purged by the /059 22-candle embargo.
- **`model_class_horse_race.py`** — the DECISIVE TEST. Per symbol, on each of 8 walk-forward folds, fits **4 model classes** on the IDENTICAL 14 features: **L** = LightGBM depth-3-5 (the v3 BASELINE — the incumbent representation); **M** = MLP (`sklearn.MLPClassifier`, 64-32 ReLU, L2-regularized, early-stopping) — a per-bar neural model that *can* learn the deep feature interactions depth-3-5 trees cannot compose; **T** = temporal-window MLP (a TCN proxy — the 14 features over a 4-bar / 32h causal lookback flattened to 56 inputs, into an MLP) — adds the sequential structure a per-bar tree discards; **C** = logistic regression — a linear floor. Each is 5-seed-averaged (the v3 inner-ensemble protocol). Outputs T1–T6.
- **`robustness_annex.py`** — the artifact controls. (A) a **5-capacity MLP sweep** (tiny-16 → base-64,32 → wide-128,64 → deep-64,32,16 → strong-reg) ruling out "the single MLP geometry was wrong." (B) a **100-shuffle permutation null on the LightGBM itself** — permute the training-fold labels, refit, re-score; if the real-label LightGBM AUC sits inside the no-signal band, the NULL is a property of the *data*, not of the neural architecture. Outputs T7–T9.

**The IS-only invariant.** `_shared.load_labeled_is()` asserts `(is_df["close_time"] < OOS_CUTOFF_MS).all()` per symbol and `(full["close_time"] < OOS_CUTOFF_MS).all()` on the assembled frame, with `OOS_CUTOFF_MS = 1742774400000` (2025-03-24). Every fold's training and test indices are drawn entirely from the IS frame; the embargo of 22 candles purges the train/test boundary so no triple-barrier label window straddles it. The post-cutoff OOS feature data and the post-cutoff /059 OOS roster were **never read by the EDA** — the QR did not inspect OOS in Phases 1-5 (and, on the NULL-AT-EDA verdict, Phase 7 does not occur). (The separate `/059-reconciliation` analysis — Section 6 — *does* inspect /059's OOS roster; it is explicitly a post-hoc diagnostic on a long-closed iteration, not Phase-1-5 design work, and is labelled as such throughout.)

## 3. The EDA result — the horse race, the capacity sweep, and the decisive permutation null

### T1–T3 — the horse race: every neural class is WORSE than the tree

`model_class_horse_race.py` → `T1_per_fold_metrics.csv` (24 symbol×fold cells per model), `T2_pooled_model_class.csv`, `T3_per_symbol_auc.csv`. The pooled held-out ROC-AUC across all 24 cells:

| model class | pooled held-out AUC | lift vs LightGBM |
|---|---:|---:|
| **L — LightGBM depth-3-5 (the v3 BASELINE)** | **0.4993** | — |
| M — MLP (per-bar neural) | 0.4891 | **−0.0102** |
| T — temporal-window MLP (TCN proxy) | 0.4836 | **−0.0157** |
| C — logistic (linear floor) | 0.4641 | −0.0352 |

**Every neural class is below the tree.** The MLP — the model class that *can* compose the deep feature interactions a depth-3-5 tree cannot — lands at 0.4891, a −0.0102 *deficit*, not a lift. The temporal MLP, which additionally has the 4-bar sequential context a per-bar tree discards, is *worse still* at 0.4836. The per-symbol cut (`T3`) confirms it is not a single-symbol artifact: LightGBM wins on all 3 — BCH 0.4965 / LDO 0.5102 / TRX 0.4910 — and every neural class is below it on every symbol.

### T4–T5 — the GO/NO-GO verdict: 0 of 3 non-tree classes clear the bar

`T4_subperiod_stability.csv` splits the 8 folds into 3 chronological thirds and reports each non-tree class's AUC lift over LightGBM within each third; `T5_go_nogo_verdict.csv` applies the pre-registered GO bar (pooled AUC lift ≥ +0.02 **AND** positive in ≥2 of 3 IS thirds):

| model | pooled AUC lift vs LightGBM | positive thirds | material lift ≥+0.02 | sub-period stable | verdict |
|---|---:|---:|:--:|:--:|:--:|
| M — MLP | −0.0102 | 1 / 3 | False | False | **NO-GO** |
| T — temporal MLP | −0.0157 | 0 / 3 | False | False | **NO-GO** |
| C — logistic | −0.0352 | 0 / 3 | False | False | **NO-GO** |

**0 of 3 non-tree model classes clear the GO bar.** None achieves a material pooled lift; none is sub-period-stable (the MLP is positive in 1 of 3 IS thirds, the temporal MLP in 0, the logistic in 0). The held-out rank-IC (`T6`) tells the same story — LightGBM mean IC −0.0156, MLP −0.0309, logistic −0.0637: all near zero, the tree marginally the least-bad.

### T7 — the 5-capacity MLP sweep: 0 of 5 capacities beat the tree

The headline MLP used one geometry (64-32). `robustness_annex.py` → `T7_mlp_capacity_sweep.csv` rules out "the geometry was wrong" — the F-AUC horse race re-run across 5 MLP capacities, against the LightGBM 3-seed reference AUC of 0.5000 on the identical folds:

| MLP capacity | pooled held-out AUC | beats LightGBM (0.5000)? |
|---|---:|:--:|
| deep (64,32,16) | 0.4935 | False |
| base (64,32) | 0.4876 | False |
| wide (128,64) | 0.4864 | False |
| tiny (16) | 0.4843 | False |
| base + strong reg (α=0.1) | 0.4841 | False |

**0 of 5 MLP capacities beat the tree.** The best — the deep 3-layer geometry — reaches 0.4935, still a −0.0065 deficit. Tiny, wide, deep, and heavily-regularized all land 0.484–0.494. The NULL is not a capacity-tuning artifact; no neural geometry recovers signal the tree misses, because there is no signal to recover.

### T8 — THE DECISIVE TEST — the 100-shuffle permutation null on the LightGBM itself

The horse race established no neural class beats the tree. But the tree itself sits at AUC ~0.50 — and a naive read ("trees are good; the neural classes just can't match a real tree edge") would be *wrong*. `robustness_annex.py` → `T8_lgbm_permutation_null.csv` settles it conclusively. The LightGBM's observed real-label held-out AUC (single seed=42, matched to the null) is compared against a 100-shuffle permutation null — training-fold labels permuted, model refit, AUC re-scored:

| quantity | value |
|---|---:|
| observed LightGBM held-out AUC (real labels) | **0.497** |
| permutation null mean AUC | 0.5014 |
| permutation null q05 | 0.4828 |
| permutation null **q50** | **0.5003** |
| permutation null q95 | 0.5228 |
| **permutation p-value** | **0.64** |

**The observed real-label AUC of 0.497 sits at the q50 of the no-signal permutation band [0.483, 0.523]. The permutation p-value is 0.64.** Under the no-signal null — where the model is fit on *shuffled* labels and therefore cannot, by construction, hold any directional information — an AUC of 0.497-or-better occurs 64% of the time by chance alone. The tree's "AUC ~0.50" is **not** "trees are good and neural models can't match it" — it is the **no-signal floor**: the 14-feature stack does not predict the triple-barrier direction better than chance, and this is a property of the data, not of any model class. The annex verdict (`T9`) is unambiguous: **NO-GO confirmed — no model class extracts signal; the NULL is a property of the 14-feature / triple-barrier / BCH-LDO-TRX 8h data.**

### EDA verdict — the axis is dead, and decisively

The representational-capacity axis is **conclusively falsified** before any backtest, on three independent axes:

1. **The horse race fires.** Every neural class is *worse* than the tree on the pooled held-out AUC (MLP −0.0102, temporal MLP −0.0157); 0 of 3 non-tree classes clear the GO bar; the tree wins on all 3 symbols.
2. **The capacity sweep fires.** 0 of 5 MLP capacities beat the tree. The NULL is not a geometry-tuning artifact.
3. **The permutation null fires — decisively.** The LightGBM's real-label AUC of 0.497 sits at the q50 of the no-signal band, p=0.64. There is no IS-detectable directional signal in the 14-feature representation for *any* model class to extract.

There is no higher-capacity model that extracts a sharper edge from the 14 features, because the 14 features do not contain a directionally-predictive edge to extract. The honest verdict is **NULL-AT-EDA**.

## 4. The verdict — NULL-AT-EDA, no backtest — the fail-fast justification

The dispatch reserves NULL-AT-EDA for "an axis the deep EDA conclusively proves dead (high bar)." The /109 EDA clears that bar — a two-script (plus shared labeler), nine-table, strictly-IS-only, walk-forward-faithful gating EDA that fired on the horse race, the capacity sweep, and the permutation null. No backtest was run, for three binding reasons:

1. **The gating EDA IS the decisive test of the axis.** The representational-capacity axis asks one question: does a higher-capacity / different-class model extract more signal from the 14 features than the depth-3-5 tree? The horse race measures exactly that — the held-out predictive AUC of every candidate class on the identical IS folds — and returns: 0 of 3 classes and 0 of 5 capacities beat the tree, and the permutation null shows there is no signal to extract. A Phase-6 backtest of a `NeuralStrategy` would re-derive this same negative (a model with no held-out predictive edge cannot produce a positive trade-Sharpe except by barrier geometry — see Section 6) at the cost of an `src/` strategy build, a new dependency, and a 3-seed run.
2. **A backtest would knowingly reproduce a documented, permutation-confirmed failure.** The pre-registered falsifier fires unambiguously and robustly across three independent controls. To build a neural strategy into `src/` and run the backtest anyway would spend compute and an `src/` re-architecture to manufacture a confirmation-shaped artifact around a hypothesis the cheap EDA — backed by a 100-shuffle permutation test — has already killed.
3. **Fail-fast forbids a foreseeable-failure spend.** `feedback_fail_fast.md` — the cheap-kill discipline of the /094–108 fail-fast EDAs — directs that an axis a committed IS-only EDA conclusively kills is closed at the EDA: no `src/` change, no runner change, no backtest, no Critic, no agent dispatch. The honest move is to report the negative verdict with the numbers, which is what NULL-AT-EDA is.

No `src/` code was written — there is no neural strategy; `src/crypto_trade/strategies/ml/` is untouched; `V3_FEATURE_COLUMNS` stays at 14; the primary model / triple-barrier label / universe / 7-gate RiskV2 stack are all /059-identical; there is nothing to revert. The horse race and the permutation null live entirely inside the three committed `analysis/iteration_v3-109/` files (a stock LightGBM + `sklearn` MLP/logistic fit — no new production dependency, no production wiring). `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` were untouched. Every Phase 1-5 measurement was strictly IS-only; the QR did not inspect the post-cutoff OOS.

## 5. The terminal meta-finding — the /105→/106→/107→/108→/109 convergent chain is complete; v3's binding constraint is the information content of the 14-feature representation, which a permutation test cannot distinguish from zero

This is the most informative output of /109, and it is what makes the iteration the terminal contribution of a five-step localization rather than a dead end.

iter-v3/105–109 form a **five-step convergent falsification chain** that has, step by step, eliminated every candidate explanation for the thin v3 signal *other than the information content of the representation itself*:

- **/105 cleared the label.** A re-framed estimand the features predict 31–52% better collapsed the IS fit. Not the label.
- **/106 cleared the regime / risk-overlay layer.** No causal regime separator; a drawdown brake is IS-negative. Not a detectable regime.
- **/107 cleared the exit / trade-construction layer.** The static triple-barrier is not leaking profit at PF 1.48; no dynamic exit rescues the losers. Not the exit geometry.
- **/108 cleared the selection / triage layer.** The primary's errors are not predictable from orthogonal information (a disjoint-feature meta-model, AUC 0.56, p=0.18). Not a triage-able residual.
- **/109 clears the model class — and identifies the residual constraint.** No higher-capacity model extracts more signal (horse race, capacity sweep); and the permutation null shows the LightGBM's own real-label AUC is 0.497, at the q50 of the no-signal band, p=0.64. The residual constraint is the **information content of the 14-feature representation on the BCH/LDO/TRX 8h universe** — and that information content is, to a 100-shuffle permutation test, **not distinguishable from zero.**

The five iterations are not five failures. They are a **complete localization.** /105 cleared the label, /106 the regime layer, /107 the exit layer, /108 the selection layer, /109 the model class — and /109's permutation null does the one thing the prior four could not: it *names* the residual constraint and measures it. v3's binding constraint is not a layer that can be re-architected within the current scope; it is the directional information content of the representation, and a permutation test puts that at ~0.

**"Exhausted" is, for the autopilot's reachable axis space, the correct and evidence-backed read** — not a failure of effort but the terminal finding of a five-step process of elimination. The reachable axes — every estimator, every label, every exit, every filter, every model class, all *within 8h candles, the BCH-LDO-TRX universe, and the 14-feature representation* — are now provably worked. The honest statement is not "we ran out of ideas"; it is "a 100-shuffle permutation test shows the 14-feature representation on this universe at this bar frequency does not carry an IS-detectable directional signal, and the convergent chain shows no re-architecture of any downstream layer manufactures one." The genuine remaining options are necessarily STRUCTURAL — and they are the user's call (Section 8).

## 6. The crux reconciliation — /059 has IS monthly Sharpe +1.09 yet the model's feature→label AUC is ~0.50

/109's permutation null surfaces a glaring tension that the rigor arm must resolve, and a committed analysis resolves it.

**The tension.** iter-v3/059 — the canonical v3 baseline — reports **IS monthly Sharpe +1.0894 / OOS +0.5791** (10-seed CONFIRMATION). Yet /109 shows the primary model's feature→label held-out AUC is **0.497, p=0.64** — random. A ~random directional AUC and a backtested Sharpe near +1 cannot *both* be the plain truth of "the model predicts direction." `analysis/iteration_v3-109/edge_reconciliation.py` (committed; outputs R1–R7) reconciles them.

**This is a post-hoc diagnostic on a long-closed iteration.** /059 has been the v3 baseline since 2026-05-12. The reconciliation is *not* Phase-1-5 design work; per the dispatch it MAY — and does — inspect /059's OOS roster, and it is labelled a closed-iteration diagnostic throughout. It changes no `src/` code and no baseline metric. It runs entirely on /059's own committed trade rosters (`reports-v3/iteration_v3-059/in_sample/trades.csv`, 171 trades; `.../out_of_sample/trades.csv`, 94 trades / 93 barrier-resolved).

**C1 — the gated-subset directional hit rate (R1, the decisive test).** The /109 horse race AUC ~0.50 is a *broad-population* statistic over every candle. /059 only *trades* the gated tail — the signals that clear the model's confidence threshold AND survive the 7-gate RiskV2 stack. The candidate explanation: does that gated tail have an above-random directional hit rate the broad-AUC horse race structurally cannot see? It does not:

| window | resolved trades | directional hit rate | hit rate − 50% | binomial p vs random |
|---|---:|---:|---:|---:|
| in-sample | 171 | **0.4152** | −0.0848 | 0.9892 |
| out-of-sample | 93 | **0.3871** | −0.1129 | 0.9890 |

The gated, traded subset's directional hit rate is **41.5% IS / 38.7% OOS — both *below* 50%.** The binomial p-value against random (one-sided, greater) is 0.99 in both windows. **There is no above-random gated tail.** The /059 model, even on the trades it actually takes, does not call direction better than a coin.

**C2 — the barrier geometry (R2).** /059's exit is a **2:1 ATR TP:SL** triple-barrier. A clean TP win pays +2 ATR, a clean SL loss costs −1 ATR; the mechanical breakeven win rate solves `WR·(+2) + (1−WR)·(−1) = 0 → WR_breakeven = 1/3 = 33.3%`. /059's realized win rate is **41.5% IS / 38.7% OOS** — *above* the 33.3% breakeven. And this is the resolution: **with a ~random directional call, a WR above the 33.3% breakeven is itself a mechanical artifact of the 2:1 geometry.** A coin-flip directional call entered into a 2:1 ATR barrier produces WR > 33% whenever the price path's TP-reachability exceeds its SL-reachability — which, in a market with any positive drift or any volatility-clustering structure, it generically does. The PnL is **geometry-carried, not signal-carried**: the 2:1 barrier is a PnL engine that converts a roughly-even directional coin-flip into a book whose win rate clears the geometric breakeven.

**C3 — the realized-edge-tranche monotonicity (R3, informational).** A roster sorted by realized gross-return magnitude shows the high-magnitude tranche hitting much harder (IS 0.81 vs 0.18 in the low tranche). This is *mechanically circular* — sorting by `|pnl_pct|` puts the TP hits (large favorable moves, by construction directional hits) in the high tranche — and is recorded as informational, not as evidence; the docstring states this. It is *not* a calibration curve (the roster CSV does not carry the raw model probability), so it cannot speak to confidence-tail calibration. The decisive evidence is C1 + C4 + C5.

**C4 — the IS→OOS decay (R4/R5, the overfit-vs-genuine tell).** A genuine (thin) edge degrades *gracefully* out of sample; pure selection-overfitting *collapses* near zero. /059's decay:

| metric | in-sample | out-of-sample | OOS / IS |
|---|---:|---:|---:|
| monthly Sharpe | +1.0894 | +0.5791 | **0.53** |
| daily Sharpe | +2.7092 | +1.4359 | 0.53 |
| profit factor | 1.4949 | 1.2107 | 0.81 |
| total PnL | 78.18 | 22.74 | 0.29 |

The monthly Sharpe retains **53%** of its IS value OOS; the profit factor degrades 1.49→1.21 but stays *above 1*. The edge does **not** collapse to zero — it degrades by roughly half. That is the signature of a **thin-but-real tilt partially eroded by selection-overfit**, not of a pure in-sample curve-fit (which would land near 0 OOS). The per-symbol stability (R5) is consistent: BCH and TRX preserve PnL sign IS→OOS; LDO flips sign (IS +0.89 → OOS −14.46) — LDO is a thin-roster lottery symbol, a known v3 concentration weakness, but the two PnL-carrying symbols hold.

**C5 — /059's own multiple-testing context (R6).** /059's CONFIRMATION ran **1050 Optuna trials** (n_eff=19 after PCA on the trial-return matrix). Its own deflated-Sharpe machinery — already in `reports-v3/iteration_v3-059/dsr.json` — returned **DSR = 0.0** (DSR_relative = 0.113). On its own trial-count-corrected significance metric, /059 does **not** clear the DSR > 0.95 bar. The +1.089 IS Sharpe is not a multiple-testing-corrected significant number. (PBO 0.128 *clears* the < 0.4 gate — /059 is not a flagrant curve-fit — and 0.644 of 45 CPCV paths are positive, a thin-but-real positive tilt.)

**The reconciliation verdict (R7).** /059's IS +1.0894 is reconciled as the sum of three things:

1. **A 2:1-barrier-geometry PnL engine.** WR > the 33.3% breakeven is mechanically produced even by a ~random directional call entered into a 2:1 ATR barrier. This is the bulk of the headline.
2. **On top of which sits a THIN, genuine, but NOT-statistically-significant tilt.** The OOS Sharpe retains ~53% of IS and 0.644 of CPCV paths are positive — more than a pure curve-fit would survive. There is *something* real and small.
3. **The gap between +1.089 IS and +0.579 OOS — roughly half the headline — IS the accumulated IS-overfitting of 59 iterations** of feature / gate / threshold selection. DSR = 0.0 confirms the IS number is not trial-corrected-significant.

**The decisive answer to the dispatch's question.** Is /059's edge a genuine (if thin) tail / gated-subset effect, or is /059's IS +1.09 substantially the accumulated IS-overfitting of 59 iterations? **Both, in identified proportion.** /059's edge is **real but THIN and barrier-geometry-dependent** — it is *not* a directional-prediction edge (the gated subset's hit rate is 41.5% IS / 38.7% OOS, *below* 50%, p=0.99; the model's feature→label AUC is 0.497, p=0.64). And **a material fraction of the IS headline — roughly the +1.089 → +0.579 gap — is selection overfit** (DSR = 0.0). /109's permutation null and this reconciliation agree completely: the 14-feature representation does not predict direction; /059 trades a 2:1-barrier-geometry edge, lightly tilted by a thin real signal, with about half the IS Sharpe being the in-sample fit of a 59-iteration search. The OOS +0.579 is the honest estimate of what survives — real, positive, geometry-carried, and not DSR-significant.

## 7. Lessons

1. **v3's binding constraint is the information content of the 14-feature representation itself — and a 100-shuffle permutation test cannot distinguish it from zero.** This is the terminal finding. The LightGBM's real-label held-out AUC is 0.497, at the q50 of the no-signal permutation band [0.483, 0.523], p=0.64. No neural class beats the tree (horse race); no MLP capacity beats the tree (5-capacity sweep). There is no directionally-predictive signal in the representation for any model class to extract. Combined with /105–/108 (label, regime, exit, selection all cleared), the /105→/106→/107→/108→/109 chain localizes and *measures* v3's binding constraint: the representation, and its directional information content is ~0 by a permutation test.

2. **Build the permutation null into any "is there signal here" EDA — it is what converts an eyeballed AUC into a verdict.** The horse race alone showed the tree wins, which a naive read could spin as "trees are good." The permutation null settled it: the tree's 0.50 is the *no-signal floor*, not a real edge the neural classes failed to match. An AUC near 0.50 is exactly the range where a permutation null is decisive and an eyeballed threshold is not — it converts "AUC 0.497, is that signal?" into "p=0.64, no." This generalizes the /108 lesson (the permutation null on the meta-model) to the primary-model representational-capacity axis.

3. **A backtested Sharpe near +1 does NOT imply a directional-prediction edge — barrier geometry is a PnL engine.** The /059 reconciliation is the central methodological lesson. /059 reports IS Sharpe +1.089 and yet its model calls direction at a *below-50%* hit rate (41.5% IS, 38.7% OOS). The 2:1 ATR TP:SL barrier mechanically converts a ~even directional coin-flip into a book whose WR clears the 33.3% geometric breakeven. Any future v3-style result must be checked: is the Sharpe coming from directional prediction (an above-random gated hit rate) or from barrier geometry (WR above the TP:SL breakeven with a ~random call)? The two are different things, and on /059 it is overwhelmingly the second.

4. **A real-but-thin edge degrades gracefully; pure overfit collapses — the IS→OOS retention ratio diagnoses which.** /059's monthly Sharpe retains 53% of IS OOS and its profit factor stays above 1 — the signature of a thin, genuine tilt partially eroded by selection-overfit, not of a pure curve-fit (which collapses near 0). The honest decomposition: /059's edge is real-but-thin and geometry-carried, and roughly half the +1.089 IS headline is the accumulated overfit of 59 iterations of selection (DSR = 0.0 confirms it). The OOS +0.579 is the defensible estimate of what is real.

5. **A convergent falsification chain that has cornered AND measured the constraint is a terminal finding — the next move is structural, and it is the user's call.** /105–/109 each closed a candidate explanation, and /109's permutation null did the decisive extra step: it named and measured the residual constraint (~0 directional information in the representation). When a five-step chain has both cornered the constraint and shown it is ~0 by a permutation test, "run another reachable axis" is not the disciplined move — there are no reachable axes left within the 8h / BCH-LDO-TRX / 14-feature scope. The disciplined move is to lay out the genuine STRUCTURAL options cleanly, with the evidence, and let the user decide (Section 8).

## 8. Terminal synthesis — v3's honest state after 109 iterations, and the genuine structural options

This section is the /105→/109 chain's terminal synthesis, as the dispatch requires. It is an honest, evidence-based account of where v3 stands and what genuinely remains.

### 8.1 What the /105→/109 chain has rigorously established

The chain is a complete, five-step convergent localization, each step a committed IS-only EDA:

- The v3 signal is **not** fixable by the training **label** (/105 — a label the features predict 31–52% better collapsed the IS fit).
- The v3 loss months are **not** a detectable or stoppable **regime** (/106 — no causal separator at a usable AUC; a drawdown brake is IS-negative).
- The v3 win-rate problem is **not** an **exit-timing** artifact (/107 — the static triple-barrier harvests at PF 1.48; no dynamic exit rescues the losers).
- The v3 bad calls are **not** **triage-able** by a selection model (/108 — the errors are not predictable from orthogonal information).
- The v3 signal is **not** recoverable by a higher-capacity **model class** (/109 — no neural class or MLP capacity beats the tree).

And /109's permutation null establishes the positive statement the prior four could only point at: **the 14-feature representation, on the BCH/LDO/TRX 8h universe, carries no IS-detectable directional signal — observed AUC 0.497 at the q50 of the no-signal band, p=0.64.** v3's binding constraint is the directional information content of the representation, and it is ~0 by a permutation test.

### 8.2 What the /059-reconciliation shows about whether v3 has a genuine edge

/059 — v3's canonical baseline — does **not** have a directional-prediction edge: its gated, traded subset calls direction at a *below-50%* hit rate (41.5% IS / 38.7% OOS, binomial p=0.99). What /059 *does* have is a **thin, real, barrier-geometry-carried edge**: the 2:1 ATR TP:SL barrier converts a ~even directional coin-flip into a book whose win rate clears the 33.3% geometric breakeven, and a small genuine positive tilt sits on top (OOS Sharpe retains 53% of IS; 0.644 of CPCV paths positive). Roughly half the +1.089 IS Sharpe is the accumulated IS-overfitting of 59 iterations of selection (DSR = 0.0 — not trial-corrected-significant). The honest one-line summary: **v3's edge is real but thin, geometry-carried not prediction-carried, and the defensible estimate of what survives out-of-sample is the +0.579 OOS monthly Sharpe — positive, but not statistically significant.**

### 8.3 The genuine remaining options — necessarily structural — for the user to choose among

The autopilot's reachable axes — every estimator, label, exit, filter, and model class, all *within 8h candles, the BCH-LDO-TRX universe, and the 14-feature representation* — are now provably exhausted. The genuine remaining options are necessarily **STRUCTURAL** — they change one of the three things the autopilot held fixed. **This synthesis lays them out; it does not choose among them — that is the user's decision.**

**Option A — a different universe.** Every v3 iteration traded BCH/LDO/TRX — itself the survivor of v3's symbol search (AAVE/AVAX/ATOM/ADA and others were closed). The /109 permutation null is specific to *this* universe's 8h feature distribution. The excluded liquid majors (and the v1/v2 symbol sets — BTC, ETH, SOL, XRP, DOGE, NEAR, LINK, LTC, DOT) are an un-tested representation-input change: a different universe is a different joint feature→label distribution, and the permutation-null result does not transfer to it. Supporting evidence: the BCH-LDO-TRX universe is small (3 symbols), concentration-fragile (LDO flips PnL sign IS→OOS; BCH carries ~96% of IS PnL), and was never re-opened after cycle 1. Caveat: v3's prior universe-expansion EXPLORATIONs (HBAR+AVAX at /021) were NEGATIVE — a universe change is not a free win and needs its own gating EDA.

**Option B — a different bar frequency.** Every v3 iteration ran 8h candles. A finer bar (1h, 4h) or a coarser bar (1d) is a fundamentally different signal-to-noise regime and — because every feature is a trailing-window transform of the bar — a genuinely different feature representation. The /109 null is an 8h result; it does not constrain a 1h or 1d representation. Supporting evidence: 8h was chosen for funding-cycle alignment and microstructure-noise filtering (both real advantages), but it was never *compared* against another frequency for directional predictability. Caveat: a finer bar multiplies the trade count and the fee drag; a coarser bar shrinks the sample — each is a different bias-variance trade-off that needs its own evaluation.

**Option C — a fundamental feature-representation change.** The /109 null is *representation-level* — it is not "we need 2 more tabular features." Adding more trailing-window transforms of the same 8h OHLCV will not clear a permutation test (this is exactly the /098/102/103 7-FEED INERT and the /070 lesson). A genuine representation change means a different *data class*: order-book / microstructure data, on-chain data, cross-asset / derivatives (funding, OI, basis) panels, or a learned representation (an autoencoder / sequence embedding rather than hand-built tabular features). Supporting evidence: v3's one PROMISING feature ever (/025) was a hand-*composed* interaction — weak evidence that interaction structure exists but is not in the current tabular form. Caveat: derivatives/on-chain feature families were probed at /093/094 (order-flow) and /019 (funding) and came back INERT *at 8h on this universe* — a representation change likely needs to be paired with Option A or B to escape the same null.

**Option D — accept /059 as v3's final state.** The reconciliation establishes that /059 trades a real-but-thin, barrier-geometry-carried edge that is OOS-positive (+0.579 monthly Sharpe) though not DSR-significant. Accepting /059 is a defensible terminal decision: v3 has a positive-expectancy book, the five-step chain has rigorously established that no autopilot-reachable axis improves it, and further EXPLORATION within the current scope is — on the /109 evidence — provably unproductive. The honest framing of this option: it is not a failure, it is recognizing that the reachable search is complete and the result is a thin positive edge.

These four options are genuinely distinct structural directions, each with supporting evidence and a real caveat. **The choice among them — including Option D — is the user's**, and is deliberately left open here.

## 9. Commit chain

- EDA SHA: `4f77b1a` — `analysis/iteration_v3-109/` (3 files: `_shared.py` the IS-only /059-faithful labeler, `model_class_horse_race.py` the 4-class horse race, `robustness_annex.py` the capacity sweep + permutation null; 9 result CSVs: `T1_per_fold_metrics.csv`, `T2_pooled_model_class.csv`, `T3_per_symbol_auc.csv`, `T4_subperiod_stability.csv`, `T5_go_nogo_verdict.csv`, `T6_rank_ic.csv`, `T7_mlp_capacity_sweep.csv`, `T8_lgbm_permutation_null.csv`, `T9_annex_verdict.csv`).
- Reconciliation SHA: committed with this diary — `analysis/iteration_v3-109/edge_reconciliation.py` (the /059 crux-reconciliation, a closed-iteration post-hoc diagnostic; 7 result CSVs `R1_gated_subset_hit_rate.csv` … `R7_reconciliation_verdict.csv`).
- Diary SHA: this closeout — `docs(iter-v3/109): closeout diary — FILED NULL-AT-EDA — representational-capacity axis FALSIFIED — no model class extracts signal, the 14-feature representation carries no IS-detectable directional signal (LightGBM real-label AUC 0.497, permutation p=0.64); the terminal finding of the /105→/109 convergent chain; the /059-reconciliation shows v3's edge is real-but-thin and barrier-geometry-carried`.
- Catalog update SHA: committed with this diary — `briefs-v3/exploration_catalog.md` /109 row (classification NULL-AT-EDA).
- **No reports** (no backtest run — NULL-AT-EDA stopped the iteration at the EDA).
- **No `src/` change** (NULL-AT-EDA — nothing was implemented; there is no neural strategy; `src/crypto_trade/strategies/ml/` is untouched; `V3_FEATURE_COLUMNS` stays at 14; the primary model / triple-barrier label / universe / 7-gate RiskV2 stack are all /059-identical; nothing to revert).
- **No brief** (NULL-AT-EDA at the gating EDA — the iteration concluded at Phase 1 before a Phase-5 brief was written; the 3 EDA files, the reconciliation script, and this diary are the iteration's record).
- **No BASELINE_V3.md change** — BASELINE_V3.md UNCHANGED at `v0.v3-059` (IS +1.0894 / OOS +0.5791, 10-seed CONFIRMATION); no baseline metric is touched.
- **Tag**: `v0.v3-109` — a closeout marker only, tagged by the orchestrator (NOT a baseline update — the `v0.v3-082`…`v0.v3-108` pattern).

iter-v3/109 is cycle-5 EXPLORATION slot #9 and the **terminal finding of the /105→/106→/107→/108→/109 convergent chain.** The chain has rigorously established that v3's binding constraint is the directional information content of the 14-feature representation on the BCH/LDO/TRX 8h universe, which a 100-shuffle permutation test cannot distinguish from zero. The autopilot's reachable axes are provably exhausted; the genuine remaining options are STRUCTURAL (Section 8.3 — a different universe, a different bar frequency, a fundamental feature-representation change, or accepting /059 as v3's final state) and are the user's decision to make.

**NO CHEATING.** `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` untouched. The walk-forward embargo fix (`e149e9d`) is inherited unchanged. This EXPLORATION does NOT update BASELINE_V3.md regardless of outcome — `v0.v3-109` is a closeout marker only. All Phase 1-5 EDA was strictly IS-only (`close_time < OOS_CUTOFF_MS` for every feature row — `_shared.load_labeled_is()` asserts the invariant per symbol and on the assembled frame); the QR did not inspect the post-cutoff OOS — no backtest was run. The /059-reconciliation (`edge_reconciliation.py`) DOES read /059's post-cutoff OOS roster — it is explicitly a post-hoc diagnostic on a long-closed iteration (/059, the baseline since 2026-05-12), NOT Phase-1-5 design work, and is labelled a closed-iteration diagnostic in its module docstring and throughout this diary.
