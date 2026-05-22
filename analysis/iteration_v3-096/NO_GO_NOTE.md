# iter-v3/096 — Phase-1 FAIL-FAST GO/NO-GO — VERDICT: NO-GO

**Iteration**: iter-v3/096 — cycle-4 EXPLORATION slot #4 of 10
**Axis tested**: a POOLED cross-symbol model — one LightGBM trained on the
concatenated BCH+LDO+TRX sample (v1's Model A construction), replacing the
per-symbol-model architecture every v3 iteration in cycles 1-4 has used.
**Phase-1 GO/NO-GO**: **NO-GO** — the axis is killed at the EDA. No research
brief, no runner, no backtest.
**Cost**: two committed IS-only EDA scripts. No `fetch`, no runner, no
backtest, no Critic, no agent dispatch.
**Decision**: NO-MERGE. BASELINE_V3.md UNCHANGED — canonical /059 (IS monthly
Sharpe +1.0894 / OOS monthly Sharpe +0.5791, tag `v0.v3-059`).

---

## 1. Why this axis, and why it was chosen as cheaply EDA-gateable

Every v3 architecture across cycles 1-4 — per-symbol absolute-barrier
LightGBM (/082-087), cross-sectional `LGBMRanker` (/088-092), the
derivatives-microstructure regime overlay (/093) and order-flow alpha
(/094), cointegration stat-arb (/095) — has trained **one model per
symbol**. The single architecture v3 has never tried is a **pooled model**:
one LightGBM trained on the concatenated BCH+LDO+TRX sample, predicting the
per-symbol triple-barrier label. This is exactly v1's Model A (BTC+ETH
pooled — proven to work in v1) and it triples the training rows per model,
the textbook fix for the IS-overfitting root cause the /088 closeout named.

Crucially — and this is the fail-fast point — the axis admits a **cheap
Phase-1 GO/NO-GO**. Pooling adds signal **only if** the three symbols share
a *transferable* feature->label relationship. If a model trained on {A,B}
generalizes to held-out symbol {C}, the pooled rows are genuine extra
signal. If cross-symbol transfer collapses to zero, each symbol's map is
idiosyncratic and pooling just averages three unrelated signals into mush —
a foreseeably NEGATIVE backtest. That question is answerable with a
leave-one-symbol-out (LOSO) cross-symbol transfer IC measurement — minutes,
not a 1.6h backtest. The axis was chosen over the alternatives (the
un-EDA-gateable sequence model; the large-universe restructure, already
falsified by iter-v3/088 T5; regime-switching TSMOM, lowest-ambition)
*precisely because* its decisive premise is cheaply testable. See Section 5.

## 2. Method (IS-only, no-cheating)

`pooled_transfer_go_nogo_eda.py`:
- 3-symbol IS panels: each symbol's v3 feature parquet, 24-month listing
  burn-in dropped, restricted strictly to `open_time < OOS_CUTOFF_MS =
  1742774400000` (2025-03-24). OOS never touched.
- Triple-barrier label computed with the **exact /059 production params** —
  ATR multipliers (2.0, 1.0), timeout 10080 min = 21 candles, fee 0.1%,
  `label_mode=triple_barrier` — replicated from
  `src/crypto_trade/strategies/ml/labeling.py:label_trades`. ATR in price
  units from `natr_21_raw` (NATR-as-percentage).
- Feature stack: the 14-column `V3_FEATURE_COLUMNS` /059 anchor.
- **T2 — within-symbol benchmark**: purged 5-fold CV rank-IC, 22-candle
  embargo. The per-symbol architecture's own signal level — the reference.
- **T3 — LOSO cross-symbol transfer**: train a LightGBM on the OTHER two
  symbols' IS bars, measure rank-IC of its prediction vs the realized
  triple-barrier directional outcome on the held-out symbol's IS bars (rows
  AND a symbol the model never saw). This is the headline.

`transfer_ic_significance.py` (the adjudication — required because the T3
headline was borderline, not a clean kill):
- block-bootstrap 95% CI on each held-out symbol's transfer IC (2000
  resamples of contiguous 21-bar blocks = the label horizon, preserving the
  serial dependence of overlapping triple-barrier labels — the CI is not
  anti-conservative).
- headline recomputed excluding LDO's small 581-row sample.

## 3. The evidence — the decisive numbers

### T2 — within-symbol benchmark (the per-symbol architecture's own signal)

| symbol | within-symbol CV rank-IC |
|---|---|
| BCHUSDT | +0.0254 |
| LDOUSDT | +0.1779 |
| TRXUSDT | +0.0291 |
| **mean** | **+0.0775** |

The per-symbol architecture itself carries **thin** signal on BCH and TRX
(+0.025 / +0.029) — LDO is the only symbol with material per-symbol signal.

### T3 — LOSO cross-symbol transfer IC (the headline) + bootstrap CI

| held-out symbol | transfer IC (point) | block-bootstrap 95% CI | n IS rows | verdict |
|---|---|---|---|---|
| BCHUSDT | +0.0689 | **[−0.0159, +0.1502]** | 3567 | indistinguishable from zero |
| LDOUSDT | +0.1470 | **[−0.0588, +0.3478]** | 581 | indistinguishable from zero |
| TRXUSDT | −0.0065 | **[−0.0921, +0.0767]** | 3509 | indistinguishable from zero |
| **headline (mean)** | **+0.0698** | — | — | — |

**T5 headline +0.0698** — 90% of the within-symbol benchmark — looked
promising at the point-estimate level and *cleared* the pre-registered
gate-1 floor (+0.030). But the block-bootstrap CI is the decisive,
load-bearing statistic, and it is unambiguous:

> **Every one of the three held-out symbols' transfer ICs has a 95%
> confidence interval that straddles zero.**

The +0.0698 headline is a point estimate with **no statistical support**.
The cross-symbol transfer signal is **not significant** on any symbol.

## 4. The verdict — NO-GO, and why this is a genuine fail-fast kill

Three independent reasons, all pre-registered or load-bearing:

1. **The decisive premise is NOT supported.** The pooled-model axis rests
   entirely on the feature->label map *transferring* across symbols. The
   LOSO transfer IC measures exactly that, and the block-bootstrap CI shows
   it is indistinguishable from zero on **all 3** symbols. A pooled model
   has no statistically-supported reason to gain over the per-symbol
   baseline.

2. **TRX's transfer is point-negative — pooling can HURT, not just fail to
   help.** TRX's transfer IC point estimate is −0.0065 (retention −22% of
   its within-symbol benchmark). The CI straddles zero, so it is not
   *certainly* negative — but the central estimate says BCH+LDO actively
   mislead TRX. This is the iter-v3/094 sign-inconsistency failure mode, now
   at the model level, and it tripped the pre-registered sign-consistency
   gate (gate 3).

3. **Confirmed by the feature-level diagnostic (T4).** Only **4 of 14**
   features have a univariate IC whose *sign* is consistent across all 3
   symbols. 10 of 14 features flip sign across BCH/LDO/TRX — `hurst_100` is
   +0.20 on LDO but −0.04 on BCH and TRX; `hurst_diff_100_50` is +0.24 on
   LDO, −0.016 on TRX. A pooled model would be fed contradictory training
   signal on the majority of its features.

This is **not** a mechanical "the gate said NO" rejection, and it is **not**
fail-fast timidity. Fail-fast targets KNOWN failures, not genuinely-uncertain
EDA-validated tests (`feedback_fail_fast.md`) — so the borderline T3
headline was adjudicated honestly with a block-bootstrap before any verdict
was issued. The adjudication is what made the verdict decisive: the axis's
load-bearing statistic has a confidence interval containing zero on every
symbol. Running a 1.6h pooled-model backtest now would be a coin-flip-grade
bet, not a high-information test — which is exactly the foreseeable-modest
grind fail-fast exists to prevent.

**Honest scope of the kill.** This does NOT prove "pooling is universally
dead." It proves something more basic and worth recording: the 14-feature
price stack carries thin signal on BCH/TRX *period* (within-symbol IC
+0.025/+0.029), and the BCH/LDO/TRX symbols do not share a transferable map.
Pooling cannot manufacture cross-symbol signal that is not there. The
problem is the **signal**, not the per-symbol vs pooled *architecture* — and
that is consistent with the cycle 1-3 finding that the per-symbol price
problem is tapped out.

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are untouched;
every measurement is strictly `open_time < OOS_CUTOFF_MS`; OOS was never
touched.

## 5. Why the pooled axis was chosen over the /095-recommended sequence model

The /095 closeout recommended iter-v3/096 = a non-tree sequence model
(shallow temporal MLP / attention-pooled sequence model). Reckoned honestly
against `feedback_fail_fast.md`, that recommendation was **not** taken, for
three reasons:

- **(a) It cannot be cheaply EDA-gated.** A model-architecture question
  (does a sequence learner beat a tree on the same 14-feature stack?) can
  only be answered by a full build + backtest. The fail-fast directive
  explicitly disfavors committing an un-gateable multi-hour bet
  sight-unseen.
- **(b) iter-v3/016 already ran a model-architecture change** (LightGBM ->
  XGBoost) and it was the worst OOS Δ in v3 history (−2.53). The model-arch
  axis has a NEGATIVE precedent.
- **(c) The gap a sequence model targets is partly already addressed.** The
  /095 closeout argued a sequence model "attacks the depth-3-5 tree cannot
  compose interactions" limitation — but iter-v3/025's engineered-feature
  line *already* attacks that by hand-composing interactions
  (`regime_momentum_signed_5d` = `ret_5d × sign(hurst_100 − 0.5)`), and that
  produced the only multi-seed-validated edge in v3 history (iter-v3/028).

The pooled-model axis was chosen instead **because** its decisive premise
(cross-symbol transferability) is cheaply EDA-gateable — and it has now been
gated, cheaply, to NO-GO. That is the fail-fast workflow working as
designed: a dead axis dies at the EDA, for the cost of two scripts, with the
compute preserved for the next genuine test.

## 6. Recommended next axis — iter-v3/097

The honest cross-cycle pattern is now sharp. The per-symbol **price**
problem is tapped out (cycles 1-3); the genuinely-different cycle-4 swings —
derivatives microstructure (/093 BLOCKED, /094 NO-GO), cointegration
stat-arb (/095 NO-GO) — are exhausted; and iter-v3/096 has shown the 14
features carry thin, non-transferable signal on BCH/TRX. Two facts from
*this* EDA point the way:

- **LDO is the one symbol with real signal** — within-symbol IC +0.178, 7×
  BCH/TRX. The thin-signal problem is concentrated in BCH and TRX, not LDO.
- **The 14-feature stack is the binding constraint**, not the model.

**Recommended iter-v3/097 axis — a label-construction re-architecture: a
volatility-scaled / meta-labeled target, EDA-gated on whether a
re-engineered label lifts the within-symbol IC on BCH and TRX.** The cleanest
cheaply-gateable form: keep the per-symbol architecture and the 14-feature
stack fixed, and test whether a *different label* — a meta-label (López de
Prado AFML Ch. 3: a primary momentum/trend rule sets the side, a secondary
classifier predicts act/no-act, so the model solves a cleaner precision
problem) or a volatility-normalized return label — produces a materially
higher within-symbol CV IC on BCH+TRX than the +0.025/+0.029 triple-barrier
baseline this EDA measured. That is a Phase-1-gateable question (recompute
the within-symbol IC under the new label; GO only if BCH and TRX both lift
materially), it attacks the actual binding constraint (thin BCH/TRX signal),
and it is a genuine re-architecture, not a knob. NOTE: iter-v3/017
meta-labeling closed only the *over-filter* failure mode at one
configuration — a within-symbol-IC-lift EDA gate is a different, cheaper
test. Fallback: the prep-memo Candidate C (regime-switching TSMOM), recorded,
lowest-ambition.

Per `feedback_v3_axis_selection_quant_discipline.md` the iter-v3/097 QR must
commit an EDA-driven quantitative basis before the brief.

## 7. Artifacts

- `pooled_transfer_go_nogo_eda.py` — the headline GO/NO-GO EDA.
- `transfer_ic_significance.py` — the block-bootstrap adjudication.
- `T1_is_panel_summary.csv` — per-symbol IS panel (rows, dates, label balance).
- `T2_within_symbol_benchmark.csv` — purged 5-fold CV within-symbol IC.
- `T3_loso_transfer_ic.csv` — LOSO cross-symbol transfer IC + retention.
- `T4_feature_sign_consistency.csv` — per-feature cross-symbol IC sign (4/14 consistent).
- `T5_go_nogo_summary.csv` — the GO/NO-GO gate evaluation (VERDICT_GO=False).
- `T6_transfer_ic_significance.csv` — block-bootstrap 95% CIs (all straddle zero).
- `T7_adjudication.csv` — the adjudication answers.
