# iter-v3/072 — Research Brief

**Cycle 2 EXPLORATION #2 of 10. Axis: ALTERNATIVE LABELING ARCHITECTURE (fixed-horizon return-sign label). Structural — Category 3 (NEW labeling).**

---

## Section 0 — Data Split Declaration

- **IS window**: data start → `OOS_CUTOFF_DATE` (2025-03-24). IMMUTABLE.
- **OOS window**: `OOS_CUTOFF_DATE` → data end. The QR does not see OOS results until Phase 7.
- **training_months**: 24. IMMUTABLE.
- **Walk-forward**: `generate_monthly_splits` applies `compute_embargo_candles(10080, 480) = 22` candles; `train_end_ms = test_start_ms - embargo_ms`. **UNCHANGED by this iteration** — see Section 3 (the label horizon stays 21 candles, so the embargo math is byte-identical).
- **Universe**: BCH, LDO, TRX (V3_MODELS unchanged; REQUIRED_GAP = 66 = (21+1) × 3 — UNCHANGED).
- **Sacred constants**: `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24` — UNCHANGED.

> **Walk-forward lookahead bug status.** Per `feedback_v3_walkforward_lookahead_bug.md`, the v3 worktree's walk-forward state is debated; BASELINE_V3.md and the /071 Critic FINAL `2fe38c5` both verify the FIXED state at `walk_forward.py:113` (`train_end_ms = test_start_ms - embargo_ms`, embargo 22). iter-v3/072 inherits this post-fix state and changes NOTHING in `walk_forward.py`. Absolute Sharpe values across all v3 iterations remain bias-comparable (same embargo); the deltas vs the /060 anchor are the load-bearing quantity.

## Section 0.5 — Iteration Type Declaration

- **TYPE**: EXPLORATION — cycle 2 #2 of 10 (iter-v3/071–080 = cycle 2 EXPLORATIONs; iter-v3/081 or later = cycle 2 CONFIRMATION). Cycle 2 #1 (iter-v3/071, same-feature meta-labeling) closed SUSPICIOUS-OOS-DOMINANT.
- **Axis category**: STRUCTURAL — **alternative labeling architecture (Category 3, NEW labeling)** per `feedback_v3_structural_over_knob_exploration.md`. This is the HIGH cycle-2 priority (#2 after meta-labeling) per BASELINE_V3.md "Cycle 2 Axis Priorities" §2: *"Labeling architecture — fixed-horizon return labels as an alternative to ATR triple-barrier. A different label DEFINITION, not a different multiplier."*
- **Axis = QR-chosen** with committed EDA backing (`5da9b1b`). The orchestrator suggested three candidates (alternative labeling / distinct-feature M2 / LDO replacement); the QR EDA selected alternative labeling. See Section 10.
- **Run mode**: `--exploration` → `EXPLORATION_ENSEMBLE_SIZE = 3` (`ENSEMBLE_SEEDS[0:3]`, outer=42 lineage subset: `191664963, 1662057957, 1405681631`), `--n-trials 35`. Per `feedback_v3_unified_10seed_baseline.md` EXPLORATION/CONFIRMATION mode separation and `feedback_v3_exploration_n_trials_35.md`.
- **Run command**: `uv run python run_baseline_v3.py --exploration --clean-oof` (`--model lgbm` is the default — restored from /071's `--model metalabeling`; this iteration is NOT a meta-labeling axis).
- **Anchor**: iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403). Confirmed valid — see Section 2.10.
- **Wall-clock estimate**: fixed-horizon labeling REMOVES the per-candle TP/SL barrier scan (the inner loop short-circuits on the first barrier; fixed-horizon runs straight to the timeout candle). The labeling cost is comparable to or marginally cheaper than ATR triple-barrier; the Optuna budget (35 × 3 syms × 3 seeds = 315 trials) is unchanged. **Estimated wall-clock: 0.6–1.0h** — comfortably within the 2h EXPLORATION cap. Reference: /060 EXPLORATION ran ≈0.7h, /071 (which ADDED an M2 study) ran 0.65h. iter-v3/072 adds nothing; it swaps one label rule for another.

## Section 1 — Testable Hypothesis (ONE sentence)

Replacing the ATR triple-barrier label (label = direction whose TP barrier is touched first within a 21-candle scan) with a **fixed-horizon return-sign label** (label = sign of the realized 21-candle-forward return; no barriers) lifts both IS and OOS monthly Sharpe vs the /060 EXPLORATION anchor by giving the M1 LightGBM a directionally cleaner training target — the barrier-first-hit rule injects path noise that contaminates the directional label, most acutely on LDO (LONG-side SL-hit rate 69%).

## Section 2 — IS-Only Numerical Evidence

EDA committed at SHA `5da9b1b` (`analysis/iteration_v3-072/axis_selection_eda.py` + 6 output files: `axis1_label_distribution.csv`, `axis1_label_agreement.csv`, `axis1_ldo_barrier_diagnosis.csv`, `axis1_label_economics.csv`, `axis2_distinct_feature_signal.csv`, `axis_selection_summary.csv`, `synthesis.md`). All tables computed on IS-window candles only (`open_time < 2025-03-24`).

### Section 2.1 — T0 Anchor-value declaration (Rule 1 compliance)

Per `feedback_v3_iter064_process_lessons.md` Rule 1, every anchor value is byte-exact from `reports-v3/iteration_v3-060/comparison.csv`.

| Metric | /060 value | Source |
|---|---:|---|
| IS monthly Sharpe | **+0.8325** | `comparison.csv:2` |
| OOS monthly Sharpe | **+0.1403** | `comparison.csv:2` |
| OOS/IS monthly Sharpe ratio | 0.1685 | `comparison.csv:2` |
| IS daily Sharpe | +1.7115 | `comparison.csv:3` |
| OOS daily Sharpe | +0.3659 | `comparison.csv:3` |
| IS n_trades | 159 | `comparison.csv:7` |
| OOS n_trades | 102 | `comparison.csv:7` |
| IS profit_factor | 1.2806 | `comparison.csv:5` |
| OOS profit_factor | 1.0482 | `comparison.csv:5` |
| IS win_rate | 31.4465% | `comparison.csv:6` |
| OOS win_rate | 39.2157% | `comparison.csv:6` |
| frac_positive_paths (CPCV) | 0.6444 | `dsr.json` |

/060 per-symbol OOS (from `comparison.csv:18-20`): BCH OOS wpnl **+1.9078** (37 trades, 32.4% WR); LDO OOS wpnl **-19.7208** (11 trades, 18.2% WR); TRX OOS wpnl **+23.3119** (54 trades, 48.1% WR). /060 per-symbol IS (from `in_sample/per_symbol.csv`): BCH 73 trades / 45.2% WR / +79.45% net_pnl / 176.68% of total; LDO 11 trades / 27.3% WR / -11.44% net_pnl / -25.44% of total; TRX 75 trades / 29.3% WR / -23.04% net_pnl / -51.25% of total. **LDO is the dominant OOS drag and a structural IS weak point** — the symbol this axis targets.

### Section 2.2 — T1: ATR triple-barrier vs fixed-horizon label distribution (IS, all candles)

`axis1_label_distribution.csv`. For each symbol, the current ATR triple-barrier (ATR-TB) label vs the fixed-horizon-N (FH-N) return-sign label, on all IS-scannable candles.

| Symbol | Labeling | n_labelable | long_frac | entropy (bits) | imbalance \|p-0.5\| |
|---|---|---:|---:|---:|---:|
| BCH | ATR_triple_barrier (21) | 5727 | 0.4901 | 0.9997 | 0.0099 |
| BCH | fixed_horizon_21 | 5727 | 0.4842 | 0.9993 | 0.0158 |
| LDO | ATR_triple_barrier (21) | 2741 | 0.4933 | 0.9999 | 0.0067 |
| LDO | fixed_horizon_21 | 2741 | 0.4881 | 0.9996 | 0.0119 |
| TRX | ATR_triple_barrier (21) | 5669 | 0.5505 | 0.9926 | 0.0505 |
| TRX | fixed_horizon_21 | 5669 | 0.5721 | 0.9850 | 0.0721 |

**Honest reading: label BALANCE is NOT the bottleneck.** Both labeling schemes are near-perfectly balanced (entropy ≈ 1.0 on every symbol). Fixed-horizon does not improve balance — it is marginally less balanced. The case for this axis is NOT "fixed-horizon balances the labels"; it is the directional-cleanliness argument in Section 2.4. This is stated explicitly so the brief does not over-claim.

### Section 2.3 — T2: ATR-TB vs fixed-horizon label agreement (IS — is this a genuine re-labeling?)

`axis1_label_agreement.csv`. On IS-scannable candles, the fraction where the ATR-TB label equals the FH-N label, and the mean magnitude of the realized N-candle forward move on the bars where they disagree.

| Symbol | Horizon | n_compared | TB-vs-FH agreement | n_disagree | mean \|fwd-ret\| on disagree (%) | mean \|fwd-ret\| all (%) |
|---|---:|---:|---:|---:|---:|---:|
| BCH | 21 | 5727 | 0.8174 | 1046 | 5.93 | 9.53 |
| LDO | 21 | 2741 | 0.7702 | 630 | 7.84 | 11.13 |
| TRX | 21 | 5669 | 0.8109 | 1072 | 4.41 | 7.18 |

For FH-21 specifically: ATR-TB and FH-21 **disagree on 18–23% of bars** (LDO 23.0%, BCH 18.3%, TRX 18.9%), and the disagreement bars carry material moves (mean |fwd-ret| 4.4–7.8%, not flat-bar noise). Fixed-horizon labeling **genuinely re-labels** a fifth of the data — it is a structural change, not a cosmetic perturbation. (The full agreement table also covers FH-7 / FH-14; the mean over all 9 (symbol, horizon) cells is 0.7940.)

### Section 2.4 — T3: label economics — matched 21-candle horizon (THE DECISIVE TABLE)

`axis1_label_economics.csv`. The directional spread of a label = `mean(realized forward return | label = +1) − mean(realized forward return | label = −1)`. A larger spread means the label separates the realized forward drift more sharply — a cleaner directional target for the M1 tree. **ATR-TB and FH-21 both scan exactly 21 candles forward**, so evaluating both at the 21-candle window is a matched, apples-to-apples comparison.

| Symbol | Labeling | spread @ matched 21-candle horizon (%) | label persistence (lag-1 autocorr) |
|---|---|---:|---:|
| BCH | ATR_triple_barrier | 14.77 | 0.7316 |
| BCH | fixed_horizon_21 | **19.14** | **0.7906** |
| LDO | ATR_triple_barrier | 15.06 | 0.7197 |
| LDO | fixed_horizon_21 | **22.30** | **0.7897** |
| TRX | ATR_triple_barrier | 10.82 | 0.7298 |
| TRX | fixed_horizon_21 | **14.21** | **0.7838** |
| **Mean (3 syms)** | ATR_triple_barrier | **13.55** | **0.727** |
| **Mean (3 syms)** | fixed_horizon_21 | **18.55** | **0.788** |

**At the matched 21-candle horizon, the FH-21 label separates the realized forward drift ~30–50% more sharply than the ATR-TB barrier-first-hit label on every symbol** (BCH +30%, LDO +48%, TRX +31%). The mechanism: the barrier-first-hit rule labels by the *first* barrier touched, which is path-dependent noise. A candle that ticks down to −1×ATR (SL barrier) before rallying +15% over the next 21 candles gets a SHORT label even though the net 21-candle drift was strongly positive. The barrier rule injects path noise into the directional target. FH-21 reads the *net 21-candle drift* directly — a cleaner target. FH-21 label persistence (0.788) also exceeds ATR-TB (0.727) — a stabler, more learnable label sequence.

(`axis1_label_economics.csv` also reports a common-7-candle ruler where FH-7 shows the largest spread — that is a horizon-mismatch artifact: a 7-candle label naturally tracks a 7-candle ruler. At matched horizons, FH-21 dominates. This is why the chosen horizon is 21, not 7 — see Section 3 and Section 10.)

### Section 2.5 — T4: LDO triple-barrier outcome diagnosis (the target symbol)

`axis1_ldo_barrier_diagnosis.csv`. The LONG-side barrier outcome distribution for LDO's IS candles, and the breakdown of which label-generating branch fired.

| Scope | n_labelable | LONG-side TP-hit rate | LONG-side SL-hit rate | LONG-side timeout rate |
|---|---:|---:|---:|---:|
| LDOUSDT_IS (LONG-side barrier) | 2741 | **27.33%** | **69.14%** | 3.54% |

Label-generating branch (which rule actually set the label):

| Branch | count | share of LDO IS labels |
|---|---:|---:|
| `timeout_fwd_sign` (no TP barrier hit either side → fwd-return sign) | 1125 | **41.04%** |
| `short_tp` | 867 | 31.63% |
| `long_tp` | 749 | 27.33% |

**LDO's ATR-TB label is SL-saturated.** Nearly 70% of LONG-side outcomes hit the stop (the 1×ATR SL barrier) before the 2×ATR TP barrier. More tellingly: **41% of LDO's labels are ALREADY effectively fixed-horizon** — for 41% of LDO IS candles no TP barrier is touched on either side, so `label_trades` already falls back to `sign(fwd_return)`. The triple-barrier mechanism is half-disengaged on LDO and what it does contribute is dominated by path-noise stop-outs. Switching LDO to a fixed-horizon label is a small, targeted, structurally-honest change — it makes uniform the rule that already governs 41% of its labels. (Note: this diagnosis is on the full LDO IS candle set, not the /060 trade roster — the trade-level subset is small per /071 T1 LDO 11 trades / 3 TP / 8 SL, which is the same SL-saturated pattern at trade granularity.)

### Section 2.6 — T5: AXIS 2 rejection evidence (distinct-feature M2 separability)

`axis2_distinct_feature_signal.csv`. The orchestrator's candidate AXIS 2 is a second meta-labeling EXPLORATION with M2 trained on features M1 does not use. The only distinct (non-14-set) features present in the `features_v3` parquets are the two funding-rate z-scores. On IS bars, the rank-AUC of each funding z-score vs a winner/non-winner outcome:

| Symbol | Distinct feature | n_bars | best \|AUC − 0.5\| | Verdict |
|---|---|---:|---:|---|
| BCH | funding_rate_zscore_30 | 5697 | 0.0067 | NEAR-ZERO-SIGNAL |
| BCH | btc_funding_rate_zscore_30 | 5635 | **0.0347** | NEAR-ZERO-SIGNAL |
| LDO | funding_rate_zscore_30 | 2711 | 0.0003 | NEAR-ZERO-SIGNAL |
| LDO | btc_funding_rate_zscore_30 | 2645 | 0.0109 | NEAR-ZERO-SIGNAL |
| TRX | funding_rate_zscore_30 | 5597 | 0.0101 | NEAR-ZERO-SIGNAL |
| TRX | btc_funding_rate_zscore_30 | 5577 | 0.0054 | NEAR-ZERO-SIGNAL |

Best |AUC−0.5| across all 6 cells = **0.0347** — far below the 0.12 residual-signal bar. Funding z-scores carry near-zero winner/loser discrimination, consistent with the funding family being PERMANENTLY CLOSED across 3 prior EXPLORATIONs (/019, /023, /024 — rank 14/14 importance). AXIS 2 is not viable as a distinct-feature M2 source, and there is no OI/basis feature module in `features_v3`. AXIS 2 is rejected — see Section 10.

### Section 2.10 — EXPLORATION anchor confirmation

The cycle-2 EXPLORATION anchor is **iter-v3/060 EXPLORATION-MODE-REFERENCE: IS +0.8325 / OOS +0.1403** (`comparison.csv:2`). Confirmed valid:
- /060 is the unified-architecture 3-seed EXPLORATION-mode reference per `feedback_v3_cycle1_axis_pass_criteria.md`.
- The current codebase post-iter-v3/071 closeout: /071's only code change was the cosmetic `ITERATION_LABEL` bump (it ran `--model metalabeling` but committed no model-code change); `DEFAULT_ATR_MULTIPLIERS` is `(2.0, 1.0)`; the 14-feature set, the 3-symbol universe, the risk-gate stack, the triple-barrier 21-candle timeout are all at the /060 state. The default `--model` is `lgbm`.
- Therefore the current codebase, run in EXPLORATION mode with `--model lgbm`, is **/060-trade-roster-equivalent**. /060 is the valid cycle-2 EXPLORATION anchor. BASELINE_V3.md still tags `v0.v3-059` as the canonical CONFIRMATION-mode baseline; /060 is the parallel EXPLORATION-mode reference, not a replacement.

## Section 3 — Proposed Changes (LOCKED — single-axis variation)

**ONE substantive change:** replace the ATR triple-barrier label rule with a **fixed-horizon return-sign label** at a **21-candle horizon**, for all 3 v3 models (BCH/LDO/TRX). The label horizon equals the current triple-barrier timeout (10080 min = 21 candles at 8h), so every downstream CV/embargo quantity is byte-identical.

- **Symbols**: BCH, LDO, TRX — UNCHANGED (V3_MODELS; `V3_EXCLUDED_SYMBOLS` check passes — no v1/v2 symbol added).
- **Labeling**: ATR triple-barrier → fixed-horizon return-sign. `label = +1 if fwd_return_21_candles ≥ 0 else −1`, where `fwd_return_21_candles` is the realized return from the candidate candle's close to the close of the candle 21 candles forward (the timeout candle). NO TP/SL barriers. The `long_pnl` / `short_pnl` arrays the optimizer consumes are the realized fixed-horizon return (long) and its negative (short), net of `fee_pct`. `timeout_minutes` / `label_timeout_minutes` stay 10080 — they now define the fixed horizon rather than the barrier-scan deadline.
- **Features**: 14 V3_FEATURE_COLUMNS — UNCHANGED. No feature added or removed; no `colsample_bytree` change; no IC exposure (Critic Check 4 is a no-op delta).
- **Risk gates**: 7-primitive stack (BTC trend kill, vol scaling, ADX 20, Hurst, z-score OOD 2.0, low-vol filter, hit-rate) — UNCHANGED.
- **Ensemble / Optuna**: EXPLORATION 3-seed, `--n-trials 35` — UNCHANGED.
- **ATR multipliers**: `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)` stays in the code but is **inert under fixed-horizon labeling** (no barriers to scale). The signal-time `tp_pct`/`sl_pct` execution barriers in `get_signal` (`lgbm.py:698-720`) are a SEPARATE mechanism (trade-exit barriers, not label barriers) and are UNCHANGED — see Section 3.2.

### Section 3.1 — Code edits (specification for the Engineer; QR does not write src/)

This axis requires a genuine `src/` change (unlike /071, where `MetaLabelingStrategy` pre-existed). The change is small and localized. The Engineer implements exactly the following — a `label_mode` parameter threaded from the runner to `label_trades`:

1. **`src/crypto_trade/strategies/ml/labeling.py`** — add a `label_mode: str = "triple_barrier"` parameter to `label_trades`. When `label_mode == "fixed_horizon"`: skip the TP/SL barrier detection inside the forward-scan loop (do NOT set `long_result`/`short_result` from barrier touches; do NOT `break` on barrier hits) — let the loop run to the timeout candle, capturing `last_close`. Then `fwd_return_pct = (last_close − entry) / entry × 100`; `label = 1 if fwd_return_pct ≥ 0 else −1`; `long_pnl = fwd_return_pct − fee_pct`; `short_pnl = −fwd_return_pct − fee_pct`; `weight = abs(labeled_pnl)`. The `neutral_threshold_pct` path stays available (label 0 if `|fwd_return_pct| < neutral_threshold_pct`) — v3 does not use it (`neutral_threshold_pct=None`), so it is a no-op. Default `"triple_barrier"` preserves byte-identical behaviour for v1/v2 and any caller that does not pass the parameter.

2. **`src/crypto_trade/strategies/ml/lgbm.py`** — add a `label_mode: str = "triple_barrier"` constructor parameter; store `self.label_mode = label_mode`; pass `label_mode=self.label_mode` in the `label_trades(...)` call at `lgbm.py:355`.

3. **`src/crypto_trade/strategies/ml/metalabeling.py`** — add the same `label_mode: str = "triple_barrier"` constructor parameter and forward it to the M1 `LightGbmStrategy` (parity; iter-v3/072 runs `--model lgbm` so this path is not exercised, but the parameter must exist so a future meta-labeling iteration can combine the axes).

4. **`run_baseline_v3.py`** — add `label_mode="fixed_horizon"` to the `common_kwargs` dict (`run_baseline_v3.py:1467-1486`); bump `ITERATION_LABEL` `"v3-071"` → `"v3-072"` (`run_baseline_v3.py:128`); add a pre-flight assertion that `_p13_lgbm.label_mode == "fixed_horizon"` (mirroring the existing `label_timeout_minutes` pre-flight assert at `run_baseline_v3.py:733-743`).

5. **No other change.** `label_timeout_minutes` stays 10080. `compute_embargo_candles(10080, 480)` still returns 22. `REQUIRED_GAP` stays 66. CPCV config unchanged. `BacktestConfig.timeout_minutes` stays 10080. The `BacktestConfig.timeout_minutes == LightGbmStrategy.label_timeout_minutes` consistency assert (`run_baseline_v3.py:819`) still passes.

### Section 3.2 — Disambiguation: label barriers vs trade-exit barriers

There are TWO barrier mechanisms in the v3 pipeline and this iteration changes exactly ONE:

- **Label barriers** (`label_trades` with `use_atr_labeling`): used at TRAINING time to assign each training candle a direction label. **This iteration replaces these with a fixed-horizon return-sign rule.** This is the axis.
- **Trade-exit barriers** (`get_signal` returns `tp_pct`/`sl_pct` per `lgbm.py:698-720`; the backtest engine closes a live trade when price hits TP/SL/timeout): used at INFERENCE time to manage an open position. **These are UNCHANGED** — the backtest still exits trades on the `natr × atr_tp_multiplier` TP and `natr × atr_sl_multiplier` SL. Changing the trade-exit barrier too would be a second axis.

This iteration changes how the model is *trained to predict direction*, not how a placed trade is *exited*. Single-axis discipline is preserved: the model learns from a fixed-horizon label, then the unchanged execution layer trades that direction with the unchanged ATR-based exits. (This is a legitimate and common design — the training label and the execution rule are independent degrees of freedom. The hypothesis is that a cleaner training label produces a better direction model; the execution barrier is held fixed precisely so the OOS delta is attributable to the label change alone.)

## Section 4 — Expected OOS Impact (LOCKED — predicted bands)

Anchor: /060 (IS +0.8325 / OOS +0.1403). Cycle-2 axis-PASS criteria per the orchestrator prompt: PROMISING-AT-EXPLORATION = (IS shift ≥ **+0.10** vs /060) **AND** (OOS shift ≥ **+0.20** vs /060). (Note: this matches `feedback_v3_cycle1_axis_pass_criteria.md`'s thresholds carried into cycle 2 — IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20. The orchestrator prompt's Section 4 text says "IS ≥ +0.10 AND OOS ≥ +0.20"; the prompt Phase-5 bullet says "IS shift ≥ +0.10 AND OOS shift ≥ +0.20 vs /060" — both agree on OOS +0.20. This brief uses **OOS Δ ≥ +0.20** as the binding PROMISING threshold.)

### Section 4.1 — PROMISING-AT-EXPLORATION bands

- IS monthly Sharpe ≥ **+0.9325** (Δ ≥ +0.10 vs /060) **AND**
- OOS monthly Sharpe ≥ **+0.3403** (Δ ≥ +0.20 vs /060) **AND**
- `frac_positive_paths` ≥ 0.50 (relaxed EXPLORATION threshold) **AND**
- no Critic methodology FAIL (13 checks + §11 anti-pattern scan).

Predicted probability PROMISING fires: **25%** (Section 7).

### Section 4.2 — NEGATIVE bands (closes axis at catalog level — DISJUNCTIVE OR)

- IS Δ < **−0.10** vs /060 (IS < +0.7325) **OR**
- OOS Δ < **−0.20** vs /060 (OOS < −0.0597).

A single-gate fail is sufficient (disjunctive OR — per `feedback_v3_iter064_process_lessons.md` Rule 4). Predicted probability NEGATIVE fires: **35%** (Section 7).

### Section 4.3 — INERT-AT-EXPLORATION zone

- IS Δ within **[−0.10, +0.10]** vs /060 **OR** OOS Δ within **[−0.20, +0.20]** vs /060 (noise band), and not NEGATIVE.

Predicted probability INERT fires: **30%** (Section 7).

### Section 4.4 — SUSPICIOUS gate (OOS/IS ratio — MANDATORY pre-registration per `feedback_v3_oos_is_ratio_gate.md`)

**Pre-registered OOS/IS ratio gate:** if the iteration's **OOS/IS monthly Sharpe ratio > 3.0**, classification is **SUSPICIOUS** regardless of absolute OOS Sharpe magnitude. A ratio above ~3.0 is the regime-exposure signature (the /065 / /070 SL-widening pattern; /026 / /027). The gate fires *in addition to* the Section 4.2 NEGATIVE bands.

SUSPICIOUS-OOS-DOMINANT sub-mode (per the /065 / /071 precedent): IS Δ < 0 (regression) AND OOS Δ ≥ +0.20 (lift) → the axis is regime-exposed, not robust edge.

Predicted probability SUSPICIOUS fires: **10%** (Section 7).

### Section 4.5 — Behavioral-effect predictor + saturation falsifier (per `feedback_axis_saturation_predictor.md`)

A fixed-horizon label is a *re-labeling*, not a trade-count filter. The trade count is NOT expected to collapse the way a meta-labeling M2 veto collapses it — the M1 tree still emits a directional signal on every eligible candle; only the *training label* changes, which changes *which* candles the model predicts LONG vs SHORT and with what confidence.

- **Predicted IS trade-count change**: 159 → roughly **135–185** (a moderate shift in either direction; the re-labeling changes the model's decision boundary, which shifts which inference-time candles clear the confidence threshold and the risk gates). The per-symbol roster will move because LDO's and BCH's models are retrained on a materially different label (Section 2.3: ~19–23% of bars re-labeled).
- **Behavioral-effect prediction**: the EDA (Section 2.3) shows FH-21 disagrees with ATR-TB on **18–23% of IS candles**. The trained model therefore *must* differ — a model fit on a label that disagrees on a fifth of the training set cannot produce a bit-identical trade roster. **Predicted: the IS trade roster changes by ≥ 15% of trades (≥ 24 of 159 IS trades differ in entry, direction, or both).**
- **Saturation falsifier FIRES** (axis is mechanically inert — NULL-RESULT) **if**: the IS trade count is within ±3 of /060's 159 **AND** the per-symbol IS counts are each within ±3 of /060's BCH 73 / LDO 11 / TRX 75 **AND** the IS monthly Sharpe is within ±0.03 of /060's +0.8325. That would mean the fixed-horizon label produced a trade roster indistinguishable from the ATR-TB roster — implying the `label_mode` switch did not actually take effect (a wiring failure). If the saturation falsifier fires, the classification is **NULL-RESULT** and the Engineering report must investigate whether `label_mode="fixed_horizon"` reached `label_trades`.
- The Engineering report MUST report: the IS and OOS trade counts, the per-symbol IS/OOS trade counts, and a confirmation (from `run.log`) that the labeling path ran in fixed-horizon mode (e.g. a `[label]` verbose line showing a `no_tp→fwd_return` or equivalent fixed-horizon reason, or the absence of TP/SL barrier outcomes).

### Section 4.6 — Per-symbol Δ prediction

Per `feedback_v3_per_symbol_target_axis_falsifier.md`, the target-symbol behavior is pre-registered:

- **LDO (the target symbol)**: LDO's ATR-TB label was 69% SL-saturated and 41% already fixed-horizon (Section 2.5). Fixed-horizon labeling has the largest matched-horizon directional-spread gain on LDO (+48%, Section 2.4). **Predicted: LDO IS net_pnl improves vs /060's −11.44%** (the directionally-cleaner label should let the LDO model find genuine edge rather than fitting stop-out noise). LDO OOS is informational at 11 trades — predicted to improve from −19.72 but the small sample makes the OOS LDO number low-confidence.
- **BCH**: BCH carries IS at 176.68% of total /060 IS PnL — a fragility flag (Section 4.7). FH-21 re-labels ~18% of BCH bars. **Predicted: BCH IS net_pnl moves materially in either direction** — this is the dominant driver of the headline IS Sharpe.
- **TRX**: TRX's ATR-TB label is the most imbalanced (long_frac 0.55) and FH-21 makes it slightly more imbalanced (0.57). TRX matched-horizon spread gain is +31%. **Predicted: TRX IS net_pnl moves modestly**; TRX is the /060 OOS carrier (+23.31) so a TRX OOS regression would drag the headline.
- **Falsifier**: if LDO IS net_pnl REGRESSES (falls below /060's −11.44%) while BCH/TRX are roughly flat, the core hypothesis — that a directionally cleaner label rescues the SL-saturated LDO label — is falsified for LDO specifically, and the Engineering report must state this.

### Section 4.7 — BCH IS concentration sensitivity (per Critic /059 Rec #3 + BASELINE_V3.md audit)

The /059 baseline has BCH at 95.76% of IS PnL; /060 has BCH at 176.68% of IS PnL — a structural fragility every cycle-2 brief must address. The fixed-horizon label re-labels ~18% of BCH's IS bars (Section 2.3), so the BCH model is genuinely retrained. **Pre-registered BCH sensitivity check**: if BCH IS net_pnl falls > 30% vs /060's +79.45% while LDO/TRX are flat, the headline IS Sharpe will likely collapse (the /063 / /064 pattern). The Engineering report MUST report BCH IS net_pnl explicitly. Conversely, if the cleaner label *lifts* BCH IS while also lifting LDO, that is the PROMISING path.

## Section 5 — Risk Mitigation

Per `feedback_v3_risk_mitigation_design.md`. iter-v3/072 is an EXPLORATION (not a merge candidate), but the section is included for completeness.

- **R1–R3 / 7-primitive gate stack**: UNCHANGED. The `RiskV3Wrapper` wraps `LightGbmStrategy` exactly as at /060 — the fixed-horizon label changes only the training target, not the strategy interface (`compute_features` / `get_signal` / `skip` are byte-identical). All 7 risk primitives operate identically on the signals the re-trained model emits.
- **The labeling change is itself a risk-relevant decision.** A fixed-horizon return-sign label removes the explicit downside-asymmetry the 2:1 TP:SL barrier encoded. Under the ATR-TB label, a candle whose forward path hit −1×ATR first was labeled by that stop-out; the model implicitly learned to avoid drawdown-prone setups. Under fixed-horizon, the model is trained purely on net 21-candle direction — it may select setups with deeper interim drawdowns. **The mitigating factor**: the trade-exit barriers (`get_signal` TP/SL, Section 3.2) are UNCHANGED — a live trade is still stopped out at 1×ATR. So the *execution* downside protection is intact; only the *training label* loses the path information. The risk this introduces is that the model may enter more trades that get stopped (interim drawdown) before the net-positive horizon completes — visible as a lower win rate with a higher average winner. The Engineering report should report win rate and profit factor so this is observable.
- **MaxDD watch**: pre-registered — if OOS MaxDD widens > 5pp vs /060's 35.78% AND the OOS Sharpe does not clear the PROMISING band, the Engineering report flags the labeling change as having traded drawdown control for nothing.
- **Look-ahead audit (non-negotiable)**: the fixed-horizon label scans FORWARD from the candidate candle, exactly as the triple-barrier label does — both consume future candles to assign a *training* label, which is correct and standard (the label is the supervised target). The leakage-prevention mechanism is the walk-forward embargo: `train_end_ms = test_start_ms − embargo_ms` with `embargo = compute_embargo_candles(10080, 480) = 22` candles ≥ the 21-candle label horizon. Because the label horizon is UNCHANGED at 21 candles, the embargo of 22 candles still strictly covers it — no training candle's 21-candle-forward label can reach into the test window. **The embargo is exactly as adequate for fixed-horizon-21 as it was for triple-barrier-21** — same horizon, same embargo. The Critic Check 1 / Check 2 delta is a no-op.

## Section 6 — Risk Management Design

8-primitive table (the v3 7-gate stack; "meta-labeling M2" is the 8th conceptual slot, not active here):

| # | Primitive | /060 state | iter-v3/072 | Fire-rate prediction |
|---|---|---|---|---|
| 1 | BTC trend kill | threshold ±15%, 14d | UNCHANGED | identical |
| 2 | Vol scaling | RiskV3Wrapper, TRX floor 0.5 | UNCHANGED | identical |
| 3 | ADX gate | adx_threshold 20 | UNCHANGED | identical |
| 4 | Hurst regime | active | UNCHANGED | identical |
| 5 | z-score OOD | zscore_threshold 2.0, 14 features | UNCHANGED | identical (same 14 features) |
| 6 | Low-vol filter | active | UNCHANGED | identical |
| 7 | Hit-rate feedback | DISABLED | DISABLED | n/a |
| 8 | Meta-labeling M2 | not active (this is the /071 axis) | not active | n/a |

The fixed-horizon label changes the *probabilities* the M1 model emits (a different training target → a different decision surface), so the *downstream* gate fire rates will shift slightly because the gates act on the model's signals. But no gate's *configuration* changes. Regime coverage is identical to /060: the 7-gate stack spans BTC-trend, volatility, trend-strength, Hurst-regime, feature-OOD, and low-vol regimes.

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode (NEGATIVE, 35%): the fixed-horizon label trades away load-bearing path information and the IS Sharpe regresses.** The ATR triple-barrier label, for all its path noise, encodes a real signal: a candle whose forward path hit the stop *first* is genuinely a worse long setup, and the 2:1 TP:SL asymmetry tells the model "only label LONG the setups where a 2×ATR move precedes a 1×ATR move." A fixed-horizon return-sign label discards this — it labels LONG any candle with a positive net 21-candle drift, including candles whose path was a deep drawdown then a late recovery. If the path information was load-bearing, the M1 model trained on the fixed-horizon label will be *worse* at distinguishing tradeable setups, the IS monthly Sharpe falls below +0.7325, and the axis closes NEGATIVE. The metric signature: IS Sharpe down, profit factor down (more stopped-out trades from setups the cleaner-looking label admitted), trade count up (the fixed-horizon label is less selective). Per `feedback_v3_iter064_process_lessons.md` Rule 3, a structural axis NEGATIVE is weighted ≥25%; the genuine risk of discarding the barrier asymmetry pushes this to 35%.

**Second failure mode (SUSPICIOUS-OOS-DOMINANT, 10%):** the fixed-horizon label happens to suit the trending OOS window (where net-drift labels and barrier labels agree more) but regresses the chop/bear IS window — IS Δ < 0, OOS Δ ≥ +0.20, OOS/IS ratio possibly > 3.0. This is the recurring v3 regime-exposure pattern; it is weighted only 10% because a labeling change is a global re-training, not a directional regime bet like SL-widening.

**Third failure mode (INERT, 30%):** the cleaner label and the noisier label produce similar enough models that the headline Sharpe sits in the noise band — the directional-spread advantage in the EDA (Section 2.4) is real on the *label* but the M1 tree at depth 3–5 with 14 features cannot convert it into a better *prediction*. The gates should catch nothing; the iteration is a clean INERT data point.

**What the gates should catch:** the Critic's hypothesis-implementation alignment check (Check 8) confirms `label_mode="fixed_horizon"` actually reached `label_trades`; the saturation falsifier (Section 4.5) catches a wiring failure where the switch silently did not take effect; the OOS/IS-ratio gate (Section 4.4) catches the regime-exposure mode. The PROMISING outcome (25%) requires the cleaner label to translate into both an IS lift ≥ +0.10 and an OOS lift ≥ +0.20 — the EDA supports the mechanism (the label IS cleaner) but a cleaner label is necessary, not sufficient, for a better model.

**Process predictions:**
- P1 — wall-clock 0.6–1.0h, well within the 2h cap (fixed-horizon labeling removes the barrier scan; no Optuna budget change). Probability it exceeds 2h: < 5%.
- P2 — the `src/` change (4 files, ~25 lines) is small and localized; the default `label_mode="triple_barrier"` preserves v1/v2 behaviour. Probability of an integration failure (runner crash, pre-flight assert fail): ~10%.
- P3 — the IS trade roster changes by ≥ 15% vs /060 (the behavioral-effect prediction, Section 4.5). Probability ≥ 80% (a label that disagrees on 18–23% of bars must retrain a materially different model).

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (LOCKED)

Anchor: /060 (IS +0.8325 / OOS +0.1403). All thresholds LOCKED at brief setup; cannot be post-hoc renegotiated. iter-v3/072 is an EXPLORATION — it never updates BASELINE_V3.md (only a CONFIRMATION-MERGE does). "PASS" here means PROMISING-AT-EXPLORATION (the axis carries forward to a cycle-2 CONFIRMATION bundle); it is NOT a merge.

### Section 8.1 — PROMISING-AT-EXPLORATION (conjunctive AND)

**PROMISING-AT-EXPLORATION** ⟺ ALL of:
- IS monthly Sharpe ≥ **+0.9325** (Δ ≥ +0.10 vs /060), AND
- OOS monthly Sharpe ≥ **+0.3403** (Δ ≥ +0.20 vs /060), AND
- `frac_positive_paths` ≥ 0.50, AND
- no Critic methodology FAIL.

→ axis carries forward to cycle-2 CONFIRMATION (iter-v3/081 or later), re-validated against /059's CONFIRMATION baseline at 10-seed mode.

### Section 8.2 — NEGATIVE-CLOSE (disjunctive OR)

**NEGATIVE** ⟺ EITHER:
- IS Δ < **−0.10** vs /060 (IS < +0.7325), **OR**
- OOS Δ < **−0.20** vs /060 (OOS < −0.0597).

A single-gate fail is sufficient. → the fixed-horizon-labeling axis CLOSED at catalog level (for the 21-candle horizon; a different horizon or a hybrid would require a fresh EDA + brief).

### Section 8.3 — INERT-AT-EXPLORATION (and NULL-RESULT sub-flavor)

**INERT-AT-EXPLORATION** ⟺ IS Δ ∈ [−0.10, +0.10] vs /060 **OR** OOS Δ ∈ [−0.20, +0.20] vs /060 (and not NEGATIVE).
- **NULL-RESULT sub-flavor**: the Section 4.5 saturation falsifier fired (IS trade count within ±3 of 159 AND per-symbol within ±3 AND IS Sharpe within ±0.03 of +0.8325) → the `label_mode` switch did not take effect; a wiring failure, not a clean EXPLORATION.

→ axis does NOT advance to cycle-2 CONFIRMATION.

### Section 8.4 — Disjunctive SUSPICIOUS gate (OOS/IS ratio — MANDATORY pre-registration)

**SUSPICIOUS** ⟺ EITHER:
- **OOS/IS monthly Sharpe ratio > 3.0** (pre-registered per `feedback_v3_oos_is_ratio_gate.md` — fires regardless of absolute OOS Sharpe), **OR**
- SUSPICIOUS-OOS-DOMINANT: IS Δ < 0 vs /060 AND OOS Δ ≥ +0.20 vs /060.

→ axis NOT eligible to advance to a CONFIRMATION bundle as an edge ingredient; re-examinable only with a structural mechanism hypothesis.

**Classification precedence**: SUSPICIOUS (8.4) takes precedence over NEGATIVE (8.2) when both fire (the ratio diagnostic identifies the *mechanism*). NEGATIVE takes precedence over INERT. PROMISING requires 8.1 to fire with no SUSPICIOUS/NEGATIVE.

### Section 8.5 — Trade-rate-floor safety net

Per `feedback_v3_trade_rate_floor.md` and `feedback_v3_trade_rate_floor_bundle_level.md`: the ≥10 OOS trades/month floor applies at CONFIRMATION-bundle level for v3, not per EXPLORATION row. For this EXPLORATION the OOS trade rate is **informational** (the /060 anchor is already at 102/14 = 7.29/month; the /059 canonical baseline at 6.7/month — both below the floor, both accepted as informational). The fixed-horizon label is a re-labeling, not an M2 veto — it is NOT expected to reduce the trade count toward zero (Section 4.5 predicts 135–185 IS trades, a moderate shift). **However**: if the OOS trade count falls below **52** (≈ 50% of /060's 102), the Engineering report MUST flag the OOS Sharpe as thin-sample and the Critic treats the OOS metric as low-confidence.

## Section 9 — Library Stack Declaration

No new external dependency. Fixed-horizon labeling is a pure-Python change inside `label_trades` (numpy already pinned). The M1 model is the same `lightgbm.LGBMClassifier`; the Optuna study is the same pinned `optuna`.

Pinned library stack (per BASELINE_V3.md Reproducibility Stamp): lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1.

**Integration test status.** Per `feedback_v3_methodology_axis_integration_test.md`, the end-to-end smoke-test mandate applies to methodology-only axes that ADD computed fields to report files (`dsr.json`, `comparison.csv`, etc.). **Fixed-horizon labeling is a LABELING-DEFINITION change, not a methodology-only computed-field axis** — it adds NO new field to any report file; it changes the training label, which changes the trained model, which changes the trade roster. The existing `comparison.csv` / `dsr.json` schema is unchanged. The rule explicitly carves out changes "caught by Hypothesis-Implementation alignment + result-verification" as NOT subject to the integration-test mandate; the `label_mode` switch is exactly such a change (Critic Check 8 confirms `label_mode="fixed_horizon"` reached `label_trades` and the trade roster differs). Therefore **no NEW integration test is required**.

However, because this axis DOES touch `src/` (unlike /071), the Engineer's Phase 6 pre-flight MUST include:
- **Unit-test parity**: the existing `tests/strategies/ml/test_*` suite must pass UNCHANGED with the new default `label_mode="triple_barrier"` — proving the change is backward-compatible (v1/v2 callers and any test not passing `label_mode` get byte-identical behaviour).
- **A new unit test** `test_labeling.py::test_fixed_horizon_label_mode` (or equivalent): on a small synthetic `master` frame, assert that `label_trades(..., label_mode="fixed_horizon")` returns `label == sign(fwd_return)` and ignores TP/SL barriers (e.g. a candle whose path touches the SL price but ends net-positive at the horizon gets label `+1`). This is a math-level unit test, sufficient for a labeling-rule change.
- **`run.log` verification**: confirm the labeling verbose lines show fixed-horizon reasons (no `long_tp`/`short_tp` barrier outcomes).
- **35/35 adversarial-test suite + `ruff check`**: standard pre-flight.

## Section 10 — QR Audit Trail

Per `feedback_v3_axis_selection_quant_discipline.md`, every EXPLORATION axis is QR-selected with committed EDA backing.

- **Cycle / slot**: cycle 2 EXPLORATION #2 of 10 (iter-v3/072). The cycle-2 #1 (iter-v3/071, same-feature meta-labeling) closed SUSPICIOUS-OOS-DOMINANT (Critic FINAL `2fe38c5`).
- **Orchestrator-suggested candidates**: the orchestrator prompt offered three axes — (1) alternative labeling architecture (fixed-horizon), (2) distinct-feature M2 meta-labeling, (3) LDO symbol replacement — and explicitly delegated the choice to the QR per `feedback_v3_axis_selection_quant_discipline.md`.
- **EDA SHA**: `5da9b1b` — `analysis/iteration_v3-072/axis_selection_eda.py` + 6 outputs (`axis1_label_distribution.csv`, `axis1_label_agreement.csv`, `axis1_ldo_barrier_diagnosis.csv`, `axis1_label_economics.csv`, `axis2_distinct_feature_signal.csv`, `axis_selection_summary.csv`) + `synthesis.md`.
- **QR axis decision — ALTERNATIVE LABELING (fixed-horizon-21)**, chosen over the other two candidates on the following quantitative basis:
  - **vs candidate 2 (distinct-feature M2)**: REJECTED. The EDA (Section 2.6) tested the only distinct (non-14-set) features available — the two funding-rate z-scores — and found best |AUC−0.5| = 0.0347 across all 6 (symbol, feature) cells, far below the 0.12 residual-signal bar. The funding family is PERMANENTLY CLOSED across 3 prior EXPLORATIONs (/019, /023, /024 — rank 14/14). There is no OI/basis feature module in `features_v3`. A distinct-feature M2 has no viable distinct features to train on. Additionally: running cycle-2 #2 as a second consecutive meta-labeling EXPLORATION would burn 2/10 cycle slots on the same architecture family, and the meta-labeling OOF wiring defect (`feedback_v3_metalabeling_oof_wiring.md`) is still open. Critic /071 Rec #4 itself framed distinct-feature M2 as "a follow-up — not necessarily the immediate cycle-2 #2 axis."
  - **vs candidate 3 (LDO replacement)**: DEFERRED, per BASELINE_V3.md cycle-2 priority ordering (universe revision is MEDIUM priority, "only if axes 1–2 fail"). Alternative labeling (HIGH priority #2) has not yet been tried; replacing LDO before testing a structural fix that the EDA shows directly targets LDO's failure mechanism would be premature.
  - **FOR alternative labeling (fixed-horizon-21)**: the EDA gives a positive, quantitative basis (not category-matching). (a) It genuinely re-labels — FH-21 disagrees with ATR-TB on 18–23% of IS bars, on material moves (Section 2.3). (b) At the matched 21-candle horizon, the FH-21 label separates the realized forward drift ~30–50% more sharply than the ATR-TB barrier-first-hit label on every symbol (Section 2.4) — a cleaner directional training target — and is more persistent (0.788 vs 0.727). (c) It directly targets the unresolved LDO weakness: LDO's ATR-TB label is 69% SL-saturated and 41% already fixed-horizon (Section 2.5); LDO has the largest matched-horizon spread gain (+48%). (d) It is the BASELINE_V3.md cycle-2 HIGH priority #2 ("a different label DEFINITION, not a multiplier") and structurally distinct from cycle-1's exhausted ATR-multiplier knob space.
- **Horizon choice — 21 candles** (not 7 or 14): two reasons. (i) Holding the label horizon equal to the existing triple-barrier timeout (10080 min = 21 candles) keeps `compute_embargo_candles(10080,480)=22`, `REQUIRED_GAP=66`, and the CPCV config byte-identical — the ONLY change is the label rule, a clean single-axis variation. A shorter horizon would shrink the label window and force an embargo change (a second axis). (ii) The EDA's matched-horizon economics (Section 2.4) confirm FH-21 is the strongest choice anyway — FH-7's larger common-7-ruler spread is a horizon-mismatch artifact (a 7-candle label trivially tracks a 7-candle ruler); at matched horizons FH-21 dominates ATR-TB and FH-14.
- **Honest framing / caveat (carried into Section 7)**: the fixed-horizon label removes the explicit downside-asymmetry the 2:1 TP:SL barrier encoded. The barrier-first-hit rule, despite its path noise, carries a real signal — a candle whose path hits the stop first is a genuinely worse long setup. If that path information was load-bearing for the M1 model, fixed-horizon labeling will REGRESS the IS Sharpe (the 35%-weighted NEGATIVE failure mode). The EDA establishes the label is *cleaner* in directional-spread terms; whether the M1 tree converts a cleaner label into a better prediction is the empirical question this EXPLORATION answers. No orchestrator pick was overridden mid-stream (the orchestrator delegated the choice; the QR made it from the EDA) — so no supersession entry is needed; this Section 10 records the QR's reasoned selection among the delegated candidates.
- **Setup commit SHA**: `<SETUP_SHA>` (this brief + the Phase 5.5 gate + ITERATION_LABEL bump — backfilled after commit).

---

**Brief LOCKED.** EDA SHA `5da9b1b`. Setup commit SHA `<SETUP_SHA>` (backfilled).
