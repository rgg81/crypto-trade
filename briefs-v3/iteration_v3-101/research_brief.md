# iter-v3/101 — Research Brief — Cycle-5 EXPLORATION: VOLATILITY-NEUTRAL RANK RE-WEIGHTING of the training sample weight

**Type:** EXPLORATION (cycle-5 slot #1) — a RISK-MANAGEMENT-adjacent / TRAINING-OBJECTIVE axis.
**Branch:** `iteration-v3/101`
**Canonical baseline:** iter-v3/059 (`v0.v3-059`) — per-symbol LightGBM, triple-barrier
ATR 2.0/1.0 + 21-candle timeout, 14-feature `V3_FEATURE_COLUMNS`, IS monthly Sharpe
**+1.0894** / OOS monthly Sharpe **+0.5791**, unified 10-seed ensemble. **Unbeaten at 100 iterations.**
**Axis (ONE variable):** the LightGBM `sample_weight` vector — switch its normalization from
the current magnitude-linear `[1,10]` to a **cross-sectional rank-normalized** `[1,10]`. No
feature change, no label-geometry change, no model-arch change, no universe change.

---

## Section 0 — Data-Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24`, `OOS_CUTOFF_MS = 1742774400000` — **IMMUTABLE**, not touched.
- `training_months = 24` — **IMMUTABLE**, not touched.
- All Phase 1-5 EDA in this brief is **strictly IS-only**: every script filters
  `open_time < OOS_CUTOFF_MS` before any computation. OOS data was **never read** during
  axis design. Verified in all 4 committed EDA scripts (`load_is()` helper).
- The Phase-6 backtest runs on ALL data via `run_baseline_v3.py`; the reporting layer
  splits at `OOS_CUTOFF_DATE` into `in_sample/` and `out_of_sample/`. The QR sees OOS
  results for the first time in Phase 7.
- 8h candles. CPCV n_paths=45, embargo=27, REQUIRED_GAP=66. Walk-forward embargo fix
  (`e149e9d`) inherited unchanged.

## Section 1 — Hypothesis

**The v3 training objective up-weights the wrong samples. The fix is a one-line change
to how the sample weight is normalized — and it is the single un-attacked frame after
cycle 4 closed symbols, features, model architecture, the label's class structure, and
regime-switching.**

The v3 baseline trains each per-symbol LightGBM with a `sample_weight` vector. That
weight (`labeling.py:label_trades`, lines 352-380) is `|net-of-fee PnL of the labeled
direction|`, linearly rescaled to `[1, 10]`. EDA #2 (Section 2, ANGLE C) shows that on
LDO and TRX this weight has a **rank-correlation of +1.000 and +0.995 with the absolute
forward 21-candle return** — it is, on two of the three v3 symbols, an almost-pure
**realized-volatility weight**. The training objective therefore tells the model: *learn
the highest-volatility candles best*. That is a vol-chasing tilt — it concentrates the
model's fit on the fat-tail, hardest-to-predict regime, exactly the regime where
directional triple-barrier signal is thinnest and most regime-dependent.

The hypothesis: **rank-normalizing the weight preserves the useful ordering (high-`|net
PnL|` candles still rank above low ones) while stripping the ATR-magnitude scaling**, so a
30%-forward-move LDO candle no longer receives ~10× the training weight of a 3%-move
candle. The model still learns "big-edge candles matter more" but no longer over-fits the
volatility extremes. EDA #3's held-out-fold horse race (Section 2, ANGLE C-race) confirms
this lifts held-out directional accuracy +0.0218 vs the baseline weight, CI strictly
above zero, sign-consistent on all three symbols.

This is a **risk-management-adjacent axis** in the sense the user named explicitly
(2026-05-18 directive: "features, risk management, and other angles"): a vol-neutral
training objective is a structural defense against the model over-allocating capacity to
the volatile-regime tail — the same motivation as a vol kill-switch or vol-scaling gate,
applied at the training-objective layer rather than the live-gate layer.

## Section 2 — IS-Only Numerical Evidence

All numbers below are produced by the four committed EDA scripts under
`analysis/iteration_v3-101/` (commit `247c4d3`), strictly IS-only.

### ANGLE A + H — AFML-Ch.4 uniqueness weighting is a NEAR-NO-OP (kills the /100 recommendation's first half)

The /100 closeout recommended a sample-weighting axis = AFML-Ch.4 uniqueness weighting
**plus** magnitude weighting. EDA #1 ANGLE A and EDA #4 ANGLE H test the uniqueness half
and **kill it at the EDA**:

| Symbol | uniqueness mean | uniqueness std | uniqueness CV | rank-corr(W0, W0×uniq) |
|---|---:|---:|---:|---:|
| BCHUSDT | 0.046 | 0.002 | 0.0505 | **0.99706** |
| LDOUSDT | 0.046 | 0.003 | 0.0727 | **0.99740** |
| TRXUSDT | 0.046 | 0.003 | 0.0580 | **0.99168** |

The 21-candle triple-barrier label means every candle's label window overlaps ~21
neighbors; uniqueness collapses to ~1/21 ≈ 0.046 for **every** candle with near-zero
dispersion. Multiplying the magnitude weight by uniqueness barely re-orders it
(rank-correlation 0.992-0.997). Uniqueness weighting therefore cannot lift this label —
it would scale all weights by a near-constant. **The /100-recommended uniqueness half is
dropped; the axis is the magnitude-weight re-design alone.** (Source:
`T1_signal_weight_characterization.csv`, `eda4` ANGLE H stdout.)

### ANGLE C — the magnitude weight is a VOLATILITY proxy, not an EDGE proxy

EDA #2 ANGLE C decomposes the `[1,10]` weight (`T2_weight_decomposition.csv`):

| Symbol | corr(weight, ATR) | corr(weight, \|fwd-return\|) | corr(weight, winner) | labeled-win-rate |
|---|---:|---:|---:|---:|
| BCHUSDT | +0.145 | **−0.111** | **+0.560** | 0.576 |
| LDOUSDT | +0.117 | **+1.000** | +0.143 | 0.993 |
| TRXUSDT | +0.366 | **+0.995** | +0.206 | 0.985 |

The split is the central finding. On **LDO/TRX** the labeled side wins 98.5-99.2% of the
time (the timeout almost always resolves with PnL = forward return), so the weight
**equals `|fwd return|`** — pure volatility. On **BCH** the barrier resolves more noisily
(labeled-win-rate 57.7%), so the weight there genuinely tracks directional correctness
(corr with `winner` +0.560). The current weight is thus **inconsistent across the
universe**: an edge proxy on BCH, a vol proxy on LDO/TRX.

### ANGLE B/D — but the weight is NOT useless on BCH — so "drop weighting" is wrong

EDA #1 ANGLE B win-rate tercile spread (`T1_signal_weight_characterization.csv`):

| Symbol | win-rate lo-tercile | win-rate hi-tercile | spread | edge-free frac |
|---|---:|---:|---:|---:|
| BCHUSDT | 0.221 | 0.873 | **+0.652** | 0.423 |
| LDOUSDT | 0.977 | 1.000 | +0.023 | 0.008 |
| TRXUSDT | 0.956 | 1.000 | +0.044 | 0.015 |

On BCH the weight carries a large +0.652 win-rate spread. The EDA #3 horse race
confirms this with the **W1 (uniform-weight) ablation: dACC −0.0074** — removing the
weight entirely HURTS. So the axis is not "remove weighting"; it is "re-shape it".

### ANGLE C-race — the held-out-fold horse race: W2 (vol-neutral rank) wins

EDA #3 (`T3_horse_race_summary.csv`): a walk-forward-faithful held-out-fold horse race,
8 one-month IS folds × 3 symbols, each fold's model trained ONLY on prior IS candles, the
ONLY varied input being the `sample_weight` vector. Block-bootstrap 95% CI (block = the
21-bar label horizon, the /096/100 overlapping-label discipline):

| Design | description | dACC mean | dACC 95% CI | dPnL mean | syms+ |
|---|---|---:|---:|---:|---:|
| W1 | uniform (all ones) | −0.0074 | [−0.0255, +0.0069] | −0.66 | 1/3 |
| **W2** | **vol-neutral RANK → [1,10]** | **+0.0218** | **[+0.0088, +0.0333]** | **+0.150** | **3/3** |
| W3 | edge-floor (0 where best_edge≤0) | +0.0204 | [−0.0051, +0.0398] | −0.04 | 2/3 |
| W4 | rank + 90th-pct tail-clip | +0.0190 | [−0.0037, +0.0384] | −0.13 | 2/3 |

**W2 is the only design with a CI strictly above zero, positive held-out side-PnL, AND
sign-consistency across all three symbols** (BCH +0.0139, LDO +0.0111, TRX +0.0403). W3
and W4 lift accuracy but their CIs straddle zero and their side-PnL is negative —
informative but not selected.

### ANGLE F — W2 multi-seed stability

EDA #4 ANGLE F (`T4_w2_seed_stability.csv`) re-runs W2-vs-W0 over the 5 v3 inner-ensemble
seeds:

| seed | overall dACC | BCH | LDO | TRX |
|---|---:|---:|---:|---:|
| 42 | +0.0218 | +0.0139 | +0.0111 | +0.0403 |
| 123 | +0.0148 | +0.0167 | +0.0347 | −0.0069 |
| 456 | +0.0208 | +0.0208 | −0.0014 | +0.0431 |
| 789 | −0.0014 | +0.0083 | −0.0083 | −0.0042 |
| 1001 | +0.0014 | +0.0069 | −0.0083 | +0.0056 |

**4 of 5 seeds positive; mean +0.0115, std 0.0109.** The lift is real but seed-sensitive
— the held-out *proxy* is informative-but-not-overwhelming. This is the explicit
"deep-but-not-conclusive" case: the proxy points the right way; the full multi-seed
Optuna backtest is the resolving experiment. Note also that BCH — the 95.76%-IS-PnL
symbol — is **positive in all 5 seeds** (the most stable signal of the three).

### ANGLE G — BCH IS-fragility (the BASELINE_V3.md cycle-1 gate)

EDA #4 ANGLE G (`T4_bch_share.csv`) — held-out cumulative side-PnL per symbol:

| weight | BCH side-PnL | LDO side-PnL | TRX side-PnL | BCH share |
|---|---:|---:|---:|---:|
| W0 (baseline) | −155.86 | +650.40 | +212.23 | −15.3% |
| **W2** | **−142.63** | **+846.39** | **+326.76** | **−10.8%** |

W2 **improves held-out side-PnL on all three symbols** and moves BCH's negative share
toward zero. (The proxy harness uses an un-tuned classifier without the Optuna confidence
threshold, so absolute BCH side-PnL is negative under both weights — only the *relative*
W0→W2 comparison is load-bearing.) **No BCH-fragility flag is tripped**: W2 does not erode
the dominant symbol.

## Section 3 — Proposed Changes (the full implementation spec)

**ONE variable changes.** A new normalization mode for the sample weight.

1. **`labeling.py` — add a `weight_mode` parameter to `label_trades`.**
   - Signature: `label_trades(..., weight_mode: str = "magnitude")`.
   - `weight_mode="magnitude"` (default): byte-identical to current behavior — the
     existing lines 378-380 `weights = 1.0 + weights / weights.max() * 9.0`. **Every v1/v2
     caller and any caller not passing the parameter is unchanged** (the v3-isolation /
     no-regression discipline).
   - `weight_mode="rank_normalized"`: replace the final normalization with
     `ranks = pd.Series(weights).rank(pct=True).to_numpy(); weights = 1.0 + ranks * 9.0`.
     The pre-normalization `weights` array (`|labeled_pnl|`) is unchanged; only the final
     rescale switches from magnitude-linear to rank-percentile-linear.
   - Rank is computed **within the call** — `label_trades` is invoked once per
     walk-forward (model, month) cell on that cell's training indices
     (`lgbm.py:385`), so the rank is cross-sectional **within the training window**, never
     across the train/test boundary. No look-ahead: the weight of a training candle
     depends only on other training candles' labeled PnL, all with
     `open_time < train_end_ms`.

2. **`lgbm.py` — thread `weight_mode` through.**
   - Add `weight_mode: str = "magnitude"` to `LightGbmStrategy.__init__` (store as
     `self.weight_mode`).
   - Pass `weight_mode=self.weight_mode` in the `label_trades(...)` call at `lgbm.py:385`.
   - No change to the `sample_uniqueness` / `time_decay_half_life` blocks (lines 400-429)
     — both stay at their defaults (`False` / `None`). **`sample_uniqueness` is NOT
     enabled** (ANGLE A/H proved it a near-no-op).

3. **`run_baseline_v3.py` — set `weight_mode="rank_normalized"` in `common_kwargs`.**
   - Add the one line `weight_mode="rank_normalized"` to the `common_kwargs` dict
     (`run_baseline_v3.py:1844-1869`).
   - Bump `ITERATION_LABEL` to `"v3-101"`.

4. **No other change.** `V3_FEATURE_COLUMNS` (14) unchanged. `V3_MODELS`
   (BCH/LDO/TRX) unchanged. ATR multipliers (2.0/1.0) unchanged. Timeout (21 candles)
   unchanged. `RiskV2Config` 7-gate stack unchanged. `V3_EXCLUDED_SYMBOLS` unchanged
   (no v1/v2 coin enters). CPCV/embargo/walk-forward unchanged.

**EXPLORATION run spec** (per `feedback_v3_cadence_discipline.md` + `feedback_v3_exploration_n_trials_35.md`):
single-seed EXPLORATION, `--n-trials 35`, `ENSEMBLE_SIZE` per the unified architecture.
Command: `uv run python run_baseline_v3.py --clean-oof`. 2h EXPLORATION wall-clock cap.

## Section 4 — Expected OOS Impact + Pre-Registered Numerical Falsifiers

**Predicted OOS impact.** The EDA #3 held-out proxy shows a +0.0218 directional-accuracy
lift; the multi-seed mean (ANGLE F) is +0.0115. A ~1-1.5pp directional-accuracy lift on a
thin-signal book translates, by the rough v3 historical accuracy→Sharpe sensitivity (the
/025 PROMISING precedent: ~+0.84 OOS for a comparable-scale held-out lift), to a
**predicted OOS monthly Sharpe delta of roughly +0.15 to +0.45 vs the /059 anchor's
+0.5791** — i.e. a predicted OOS monthly Sharpe band of **[+0.73, +1.03]**. IS monthly
Sharpe is predicted to be approximately flat to mildly positive (W2 keeps the weight
ordering; ANGLE G shows no BCH erosion) — predicted IS band **[+0.95, +1.20]** vs /059's
+1.0894. This is an EXPLORATION, single-seed — the prediction is an estimate.

**Pre-registered numerical falsifiers** (these are GATES — distinct from the prediction;
per `feedback_v3_per_symbol_target_axis_falsifier.md`). The axis is FALSIFIED at Phase 7
if ANY of the following fires:

| # | Falsifier | Fires if |
|---|---|---|
| F1 | Headline OOS regression | OOS monthly Sharpe < **+0.30** (a material drop below the /059 anchor +0.5791 — the W2 re-weight made the book worse, not better) |
| F2 | IS collapse | IS monthly Sharpe < **+0.70** (the rank re-weight broke the in-sample fit — the vol-neutral objective discarded real signal) |
| F3 | BCH IS-share inversion | BCH IS net-PnL contribution flips negative OR BCH IS share rises above **99.5%** (W2 either killed BCH or hollowed out LDO/TRX — the ANGLE G prediction was wrong) |
| F4 | Trade-roster bit-identity | the OOS trade roster is **bit-identical** to /059 (the `weight_mode` change had zero behavioral effect — classify INERT/PROMISING-MECHANICAL, not a new edge) |
| F5 | Mechanical-only lift | OOS improves but the per-symbol added-vs-removed-trade mean-duration gap exceeds **+1.0** (the /076 trade-selection sub-channel signature — the lift is a roster-churn artifact, not signal) |

**Behavioral-effect predictor** (per `feedback_v3_axis_saturation_predictor.md`): the
`weight_mode` change re-weights training samples but does NOT change labels, features, or
the inference path. The model coefficients shift, so the predicted trade roster shifts.
**Predicted behavioral effect: the OOS trade count changes by 5-25% vs /059's 94 OOS
trades** (i.e. an OOS roster of roughly 70-118 trades). If the observed OOS roster change
is **below 5%**, the axis is behaviorally saturated (F4-adjacent) — classify
INERT/PROMISING-MECHANICAL.

## Section 5 — Risk Mitigation (R1-R5, IS-calibrated, simulated effect)

This axis touches the training objective only — it does not modify any live risk gate.
The R1-R5 stack is inherited from /059 unchanged and is itself the risk mitigation:

- **R1 (cooldowns):** unchanged. Not affected by `weight_mode`.
- **R2 (drawdown scaling):** the 7-gate `RiskV2Config` stack — vol scaling, ADX, Hurst,
  z-score OOD, low-vol filter, hit-rate (disabled), BTC-trend kill — is unchanged.
- **R3 (OOD detection):** the z-score OOD gate (`zscore_threshold=2.0`) is unchanged. The
  `weight_mode` change does not alter the OOD feature set or cutoff.
- **R4 (vol kill-switch):** the BTC-trend kill (`BTC_TREND_CONFIG.threshold_pct=15.0`)
  is unchanged.
- **R5 (concentration cap):** `enable_per_symbol_cap=False` unchanged (per /020 closeout —
  per-symbol PnL caps are CLOSED at catalog level).

**Simulated historical effect of the axis itself:** EDA #4 ANGLE G simulated the W2 vs W0
held-out side-PnL across the last 8 IS months — W2 improved side-PnL on all 3 symbols and
moved BCH share from −15.3% toward −10.8% (less concentrated). The axis is itself a
de-concentration / vol-de-risking measure at the training-objective layer. No new gate is
introduced, so no new gate needs IS-calibration.

## Section 6 — Risk-Management Design (the deeper structural defense)

The user's directive named risk management as a first-class axis. iter-v3/101's deeper
structural argument: **the v3 baseline has a latent risk defect in its training objective
that no live gate can fix.** A live vol-scaling gate de-risks *position size* after the
model has spoken; it cannot undo the fact that the model was *trained* to fit the
volatile-regime tail best. EDA #2 ANGLE C quantified this — corr(weight, |fwd-return|) =
+1.00 on LDO. The current objective spends the model's limited depth-3-5 capacity
disproportionately on the highest-volatility, hardest-to-predict candles.

The `weight_mode="rank_normalized"` change is a **training-objective risk control**: it
caps the marginal training influence of any single candle at the rank-percentile ceiling,
so a once-in-two-years 40%-move candle can no longer dominate the loss the way a 4%-move
candle does. This is the training-objective analogue of a per-trade exposure cap. It is
the structurally-correct place to apply vol-de-risking: at the objective, before the
model is fit, rather than only at the live gate after.

The design is also **deliberately conservative**: rank-normalization preserves the weight
*ordering* (it is monotone in `|net PnL|`), so it cannot discard the edge signal the W1
ablation proved is real on BCH — it only flattens the magnitude. This is why W2 was
selected over W3 (edge-floor, which deletes 42% of BCH candles — a far more aggressive
intervention with a CI straddling zero) and over W1 (uniform, which the ablation
falsified).

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most-likely failure mode, pre-registered:** **INERT / PROMISING-MECHANICAL.** The most
probable non-PROMISING outcome is that the `weight_mode` change shifts the model
coefficients only slightly — the rank transform is monotone, and LightGBM trees are
themselves partly rank-based at split selection — so the trade roster moves <5% and the
OOS Sharpe lands within noise of /059. In that case the axis is classified
PROMISING-MECHANICAL or INERT (Falsifier F4), recorded in BASELINE_V3.md Dead Ideas as
"sample-weight normalization is behaviorally saturated for the v3 per-symbol LightGBM",
and the sample-weighting frame closes.

**Second failure mode:** **NEGATIVE.** The rank re-weight could flatten away a genuinely
useful magnitude signal on BCH (where the weight IS an edge proxy, ANGLE B spread
+0.652), regressing IS and OOS. Falsifiers F1/F2 catch this. The ANGLE F seed sweep (BCH
positive in 5/5 seeds) is the main evidence against this mode, but single-seed
EXPLORATION variance keeps it live.

**Why this is still worth a backtest** (per the iteration mandate — a NULL-AT-EDA is
reserved for a conclusively-dead axis, a high bar): the EDA is deep (4 scripts, 8 angles)
and the design test (EDA #3) is genuinely positive (CI strictly above zero, 3/3 symbol
sign-consistency) — it is NOT a dead axis. It is the "deep-but-not-conclusive" case: the
held-out proxy points the right way but is seed-sensitive (4/5), and a held-out
single-classifier proxy is not the multi-seed Optuna backtest. The experiment must run.

## Section 8 — Classification Taxonomy (LOCKED, disjunctive precedence)

Evaluated in Phase 8 against the Phase-7 OOS results, in this precedence order (first
match wins):

1. **BLOCKED** — Critic Phase-7.5 OVERALL=BLOCK (methodology defect). NO-MERGE.
2. **NEGATIVE** — Falsifier F1 OR F2 fires (OOS Sharpe < +0.30 or IS Sharpe < +0.70).
   NO-MERGE; record the vol-neutral re-weight as NEGATIVE in Dead Ideas.
3. **SUSPICIOUS** — Falsifier F5 fires (mechanical roster-churn signature) OR a
   structurally-suspicious IS/OOS divergence (e.g. IS daily Sharpe / OOS daily Sharpe
   ratio outside [0.2, 5]). NO-MERGE; non-advancing.
4. **INERT / PROMISING-MECHANICAL** — Falsifier F4 fires (roster bit-identical or <5%
   change) with no signal lift. NO-MERGE; the sample-weighting frame closes.
5. **PROMISING** — none of F1-F5 fires AND OOS monthly Sharpe improves over /059's
   +0.5791 AND IS monthly Sharpe ≥ +0.70 AND the per-symbol picture is sign-consistent
   with the EDA (BCH not eroded). A PROMISING EXPLORATION does NOT update BASELINE_V3.md
   (only a CONFIRMATION-MERGE does, per `feedback_v3_baseline_update_policy.md`); it is
   carried to the cycle-5 CONFIRMATION for multi-seed validation.
6. **NULL-RESULT** — the run completes but the outcome fits none of the above cleanly
   (e.g. mixed IS-up/OOS-flat within noise). NO-MERGE; documented.

BASELINE_V3.md is **not** edited by this EXPLORATION regardless of outcome (the
`v0.v3-082`…`v0.v3-100` pattern). Tag `v0.v3-101` is a closeout marker only.

## Section 9 — Library Stack + Integration-Test Mandate

**Library stack:** no new library. The axis uses `pandas.Series.rank` (already a
dependency) inside `labeling.py`. Pinned versions inherited from /059: lightgbm 4.6.0,
optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels
0.14.6, pyarrow 23.0.1.

**Integration-test mandate** (per `feedback_v3_methodology_axis_integration_test.md` — the
`weight_mode` change adds a code path through `label_trades` and `lgbm.py`, so it needs
end-to-end coverage, not just a unit test on the rank math):

1. **Unit test** — `tests/strategies/ml/test_labeling.py`: assert
   `label_trades(..., weight_mode="magnitude")` returns weights **byte-identical** to a
   no-`weight_mode` call (the v1/v2 no-regression guarantee); assert
   `weight_mode="rank_normalized"` returns weights in `[1, 10]` that are a monotone
   transform of the `"magnitude"` weights (rank-correlation == 1.0); assert an invalid
   `weight_mode` raises.
2. **Integration smoke test** — a short end-to-end `LightGbmStrategy` train on one
   (symbol, month) cell with `weight_mode="rank_normalized"`, asserting the model trains,
   the `sample_weight` passed to `model.fit` is the rank-normalized vector, and no
   train/test boundary is crossed in the rank computation.
3. The Engineer's Phase-6 pre-flight verifies `common_kwargs` carries
   `weight_mode="rank_normalized"` and `ITERATION_LABEL == "v3-101"`.

**ADF / IC gates:** N/A — no new feature is added, so the per-family IC<0.7 gate and the
per-feature ADF gate have no new column to evaluate. `V3_FEATURE_COLUMNS` is bit-identical
to /059.

## Section 10 — QR Audit Trail

- **Axis selection** was QR-led with a committed EDA basis, per
  `feedback_v3_axis_selection_quant_discipline.md`. The /100 closeout *recommended* a
  sample-weighting axis (uniqueness + magnitude weighting). The QR did NOT rubber-stamp
  it: EDA #1 ANGLE A + EDA #4 ANGLE H **falsified the uniqueness half** (near-no-op,
  rank-corr 0.992-0.997), and the QR re-scoped the axis to the magnitude-weight
  re-design alone, then ran a 5-design horse race (EDA #3) to *select* W2 with a
  quantitative basis rather than assume it.
- The user's 2026-05-18 directive prioritized a FEATURE axis. The QR weighed this:
  cycle 4's slot #6 (/098) ran a full feature-expansion GO/NO-GO EDA and found **no
  candidate feature family clears the OOS-robustness bar — the binding constraint is the
  signal, not the feature space**. Adding another off-the-shelf or composed feature would
  re-attack a frame /098 just closed. The user's directive also explicitly named "risk
  management" and "other angles"; the vol-neutral training-objective re-weight is a
  risk-management-adjacent structural angle that attacks the binding constraint
  (thin signal) at the one layer — the training objective — that cycle 4's symbols /
  features / model-arch / label-class / regime-split iterations all left untouched. The
  QR judged this a stronger axis than an 8th feature family, with the EDA evidence (EDA
  #3 CI strictly above zero) to back it.
- **Setup commit SHA:** the runner change (`weight_mode` thread-through + `ITERATION_LABEL`
  bump) is the QE's Phase-6 setup commit — backfilled by the QE at the Phase 5.5 gate.
- **EDA commit SHA:** `247c4d3` (`analysis(iter-v3/101): sample-weight design EDA`).
- **Brief SHA:** `1abeea5` (`docs(iter-v3/101): research brief — vol-neutral rank re-weighting`).
- Branch `iteration-v3/101` carried 3 prior commits (a cycle-4 retrospective + a deferred
  excluded-coins analysis relocated to `analysis/excluded_coins_deferred/`). Those are
  unrelated to this axis and were not touched. iter-v3/101's real axis is the
  sample-weight re-design specified above.
