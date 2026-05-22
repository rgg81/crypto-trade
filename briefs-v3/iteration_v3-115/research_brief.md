# iter-v3/115 — Research Brief

**A coherent horizon-exit labeling architecture: a fixed-horizon directional label PAIRED with fixed-horizon execution exit.**

Cycle-6 EXPLORATION slot #6 of 10 (iter-v3/115–119 remain; iter-v3/120 is the mandatory cycle-6 CONFIRMATION). A NEW labeling architecture — the structural axis the iter-v3/114 closeout recommended and `feedback_v3_structural_over_knob_exploration.md` ranks above the now-closed risk-primitive-knob family.

---

## Section 0 — Provenance & Honesty Statement

This brief cites no tuned scalar parameter. The single parameter the design specifies — the label/exit **horizon N** — is **NOT tuned**: it is FIXED at **21 candles**, the value of the v3-canonical triple-barrier timeout (`label_timeout_minutes = 10080 min / 480 min-per-candle = 21`). N is hand-fixed at the incumbent by design (the same fixed-N discipline iter-v3/072 used) so the CV embargo (22 candles) and `REQUIRED_GAP` (66) stay byte-identical to /059 — see Section 3.5 and Section 10. There is no horizon sweep, no confidence threshold, no barrier ratio, nothing IS-tuned. Per `feedback_v3_brief_parameter_provenance.md` (established by the iter-v3/114 Check-1 FAIL), a hand-chosen parameter must be DECLARED hand-chosen: **N = 21 is hand-chosen, declared here, and chosen for embargo-invariance, not for IS performance.** Because nothing is IS-calibrated, there is no IS-only selection table to fence and no OOS annex — the EDA (`analysis/iteration_v3-115/`) is strictly IS-only with no OOS-window file touched by any script (Section 2.7).

---

## Section 0.5 — Iteration Type Declaration

- **TYPE = EXPLORATION** (cycle-6 EXPLORATION slot #6 of 10).
- **Run spec:** `uv run python run_baseline_v3.py --exploration --n-trials 35` — `--exploration` sets `ENSEMBLE_SIZE = 3` (the outer=42 seed lineage: 191664963, 1662057957, 1405681631), single-seed EXPLORATION mode.
- **Wall-clock budget:** ≤ 2h (the v3 EXPLORATION cap; /110–/114 EXPLORATIONs ran 0.43–1.09h — a labeling-mode change adds no per-candle cost).
- **Single axis (Section 3.5):** the **labeling architecture**. The horizon-exit labeling architecture is ONE axis with two inseparable components — a fixed-horizon label and the fixed-horizon execution that makes it coherent. iter-v3/072's Critic Recommendation 1 established that these two are not separable: "A coherent fixed-horizon design needs BOTH a fixed-horizon label AND fixed-horizon execution exit." A fixed-horizon label without fixed-horizon execution is the iter-v3/072 NEGATIVE the Critic explicitly said must not be re-tested. Label-execution consistency is a *defining property* of a labeling architecture, not a second axis — exactly as the triple-barrier label is execution-consistent with the TP/SL/timeout backtest by construction. Section 3.5 and Section 10 argue this in full.

---

## Section 1 — Hypothesis

Replacing the v3-canonical triple-barrier labeling architecture (a +2/−1 ATR price-barrier label, executed through TP/SL/timeout barriers) with a **coherent horizon-exit architecture** — a fixed-horizon directional label (`sign` of the realized 21-candle forward return) executed through a fixed 21-candle time exit — will change the OOS monthly Sharpe; the committed IS-only EDA (`analysis/iteration_v3-115/`, T6 verdict = **NO-GO**) predicts the change is **non-positive**, because the IS counterfactual shows the price-barrier exit geometry itself produces a materially higher monthly Sharpe than a fixed time exit on identical directional calls.

---

## Section 2 — IS-Only Numerical Evidence

All numbers below are produced by the committed `analysis/iteration_v3-115/*.py` scripts (EDA SHA — see Section 10), strictly IS-only (every feature/label row has `close_time < OOS_CUTOFF_MS = 1742774400000`, 2025-03-24). Six result tables T1–T6.

### 2.1 The axis, and why it is genuinely un-spent

The v3-canonical label (`labeling.py:label_trades`, `label_mode="triple_barrier"`) labels each candle by "does a +2 ATR take-profit hit before a −1 ATR stop-loss or the 21-candle timeout"; the backtest **execution** matches — a trade exits at the first of TP / SL / timeout. The label and the execution are consistent **by construction**. The horizon-exit architecture trains the model on a different estimand — `sign` of the realized N-candle forward return (`label_mode="fixed_horizon"`) — and changes execution to match: every trade is held to candle N, the TP/SL barriers made non-binding. Label and execution stay consistent, on a time-exit geometry instead of a price-barrier one.

This is **not** iter-v3/072. iter-v3/072 swapped *only* the label (`label_mode="fixed_horizon"`) and left the TP/SL barrier execution untouched — EXPLORATION-NEGATIVE (IS −0.31 / OOS −0.66). The iter-v3/072 diary root-cause (Section 3): a label-execution mismatch — "a trade can have positive 21-candle forward return YET hit SL on candle 3." The iter-v3/072 Critic Recommendation 1 (diary Section 8, verbatim): *"A coherent fixed-horizon design needs BOTH a fixed-horizon label AND fixed-horizon execution exit — a 2-axis change requiring its own brief. Do NOT re-test fixed-horizon-label-only at a different horizon."* iter-v3/115 IS that brief. The /072 NEGATIVE does not constrain it: /072 closed "label-execution decoupled", not "horizon-exit coherent".

It is also **not** /017 / /108 (meta-labeling — a secondary take/skip model on the existing primary roster; /108 conclusively dead, held-out AUC 0.56, permutation p=0.18), **not** /099 (a 3-class abstention label, NO-GO at EDA), and **not** /105 (a trend-scanning label — and /105, like /072, was a label-only change executed through the unchanged triple-barrier geometry; the /105 diary's own meta-finding names that label-vs-execution geometry mismatch as the failure). iter-v3/115 is the **first v3 axis to change the primary model's estimand AND make the execution geometry consistent with it.**

### 2.2 T1 — label balance + label-vs-label agreement (g1: PASS)

Triple-barrier vs horizon-exit directional labels on the IS panel:

| symbol | n_candles | tb_label_long_frac | hz_label_long_frac | tb↔hz agreement | balance_ok | label_differs |
|---|---:|---:|---:|---:|:--:|:--:|
| BCHUSDT | 5706 | 0.6174 | 0.4855 | 0.7390 | ✔ | ✔ |
| LDOUSDT | 2720 | 0.6309 | 0.4886 | 0.7004 | ✔ | ✔ |
| TRXUSDT | 5648 | 0.6710 | 0.5722 | 0.7465 | ✔ | ✔ |

The horizon-exit label is a balanced, non-degenerate directional target (long fraction 0.49–0.57, vs ~0.50 ideal) on all 3 symbols, and it **differs materially** from the triple-barrier label — the two labels agree on only 70–75% of candles, i.e. ~25–30% of candles receive a *different* directional training label. The horizon-exit label is a real, distinct estimand, not a relabel of the same thing. **g1 PASS (3/3 balanced, 3/3 differ).**

### 2.3 T2 — label-vs-execution-consistency diagnostic (g2: PASS) — the iter-v3/072 Critic Rec 3 mandate

The iter-v3/072 Critic Recommendation 3 mandated that every labeling-axis EDA must include a label-vs-execution-consistency diagnostic. T2 delivers it. The model that exists today is trained on the triple-barrier label, so its directional call = `tb_label`. T2 asks whether that direction is the *winning* side under each execution geometry:

| symbol | dir_consistency_tb_exec | dir_consistency_hz_exec (/072 number) | /072 mismatch frac | sanity_tb_exec_ok |
|---|---:|---:|---:|:--:|
| BCHUSDT | 1.0000 | 0.7390 | **0.2610** | ✔ |
| LDOUSDT | 1.0000 | 0.7004 | **0.2996** | ✔ |
| TRXUSDT | 1.0000 | 0.7465 | **0.2535** | ✔ |

`dir_consistency_tb_exec = 1.0` on all 3 symbols is the structural sanity check — the triple-barrier label IS the argmax of the triple-barrier-execution PnL, by construction. `mismatch_frac_072` is the iter-v3/072 failure surface: the fraction of trades where a triple-barrier-trained model's direction is the **losing** side under horizon-exit execution — i.e. exactly the "positive 21-candle return yet hits SL early, or vice versa" mismatch the /072 diary named. It is a real, sizeable **25–30%**. The coherent horizon-exit design (fixed-horizon label + fixed-horizon execution) drives that mismatch to **0 by construction** — the label IS the N-candle-return sign, the execution holds to candle N, so the labelled direction is always the winning side of the realized executed trade. **g2 PASS (3/3 sanity, 3/3 /072-mismatch ≥ 0.05): horizon-exit is a genuinely different geometry and the /072 mismatch it fixes is large.**

### 2.4 T3 — IS counterfactual book comparison (g3: FAIL) — THE DECISIVE GATE

T3 is the substantive, non-circular test — the test iter-v3/072 skipped (the /072 Critic Rec 3 called /072's label-space "directional spread" metric "a misleading PROMISING signal"). The EDA cannot run the LightGBM, so it must avoid a perfect-foresight ORACLE: using a labeler's own label as the model's direction is circular (the horizon-exit label = `sign`(forward return), so its better-side N-candle return is always large and positive — that book trivially "wins"). T3 instead **holds the triple-barrier label's direction FIXED** (the direction the model that exists today would call) and compares what that **identical direction sequence** earns under (i) triple-barrier execution vs (ii) horizon-exit execution. Both books trade the same calls; only the exit rule differs — a pure execution-geometry comparison, zero perfect-foresight bias.

| symbol | tbdir to tb-exec Sharpe | tbdir to hz-exec Sharpe | hz minus tb Sharpe | hz >= tb |
|---|---:|---:|---:|:--:|
| BCHUSDT | **2.2487** | 1.1385 | **-1.1102** | NO |
| LDOUSDT | **2.3649** | 1.5641 | **-0.8008** | NO |
| TRXUSDT | **1.4172** | 1.0446 | **-0.3725** | NO |

Horizon-exit execution monthly Sharpe is **WORSE than triple-barrier execution on all 3 of 3 symbols** — Sharpe delta −1.11 (BCH), −0.80 (LDO), −0.37 (TRX). On identical directional calls, the +2/−1 ATR price-barrier exit produces a materially higher monthly Sharpe than holding to a fixed 21-candle time exit. The asymmetric price barrier — a tight −1 ATR stop that cuts losers and a +2 ATR target that books winners — is *itself* a source of trade-Sharpe that a symmetric time exit discards. **g3 FAIL (0/3): the decisive substantive gate fails — the horizon-exit geometry does NOT recover trade-Sharpe.**

### 2.5 T4 — feature→label IC (supporting context, NOT a gate)

Walk-forward-faithful (last 6 IS test months, per `feedback_v3_eda_walkforward_faithful.md`) mean |Spearman IC| of the 14 `V3_FEATURE_COLUMNS`:

| symbol | tb_label mean \|IC\| | hz_label mean \|IC\| | hz/tb IC ratio |
|---|---:|---:|---:|
| BCHUSDT | 0.20714 | 0.30992 | 1.50 |
| LDOUSDT | 0.20802 | 0.33205 | 1.60 |
| TRXUSDT | 0.22361 | 0.34068 | 1.52 |

The horizon-exit label is in fact **more feature-predictable** — the 14 features predict it ~1.5× better than they predict the triple-barrier label, on all 3 symbols. **This is exactly the iter-v3/105 trap, and it is why T4 is explicitly NOT a gate.** iter-v3/105 proved that a label the features predict +52% better still *collapsed* the IS trade fit, because feature→label IC is a property of the labeling problem, not of the trade-construction problem. T3 (the trade-book test), not T4 (the IC test), is decisive — and T3 fails. T4 is recorded only to pre-empt the misread that "the horizon-exit label is more learnable, so it should help" — it should not, and the /105 precedent says so.

### 2.6 T5 — no-signal permutation null (supporting context, NOT a gate)

A depth-3 LightGBM on the 14 features predicting `hz_label` on the pooled IS panel, chronological 70/30 split, vs a 100-shuffle permutation null:

| pooled_n | observed held-out AUC | null mean | null q95 | permutation p | clears q95 |
|---:|---:|---:|---:|---:|:--:|
| 13774 | 0.5625 | 0.5007 | 0.5473 | 0.00 | ✔ |

The pooled horizon-exit label clears its permutation null (AUC 0.5625 > q95 0.5473, p = 0.00) — there is genuine, non-spurious feature→label directional signal in the horizon-exit estimand. Same /105 caveat as T4: a non-spurious feature→label signal does not imply a profitable trade book when the execution geometry destroys the Sharpe. Supporting context only.

### 2.7 EDA verdict — pre-registered GO rule, NO-GO

The pre-registered GO rule (`horizon_exit_synthesis.py`, fixed before the script touched any table): **GO iff g1 AND g2 AND g3.**

- **g1 LABEL VALIDITY — PASS** (3/3 balanced, 3/3 differ from triple-barrier).
- **g2 EXECUTION COHERENCE — PASS** (3/3 sanity, /072 mismatch a real 25–30% on 3/3).
- **g3 TRADE-BOOK GAIN — FAIL** (0/3: horizon-exit execution Sharpe worse on every symbol).
- **VERDICT = NO-GO.**

Per **THE PRIME DIRECTIVE** the EDA designs the experiment; it does **not** terminate the iteration. iter-v3/115 runs a Phase-6 backtest. The NO-GO sets the brief's modal prediction (Section 4: a non-positive OOS effect) and Section 7's pre-registered modal failure mode (the geometry-does-not-transfer mode). Running the backtest is mandatory and is also genuinely informative: T3 is an ORACLE counterfactual on perfect-direction calls; the production backtest tests whether the *real* LightGBM, trained on the more-feature-predictable horizon-exit label (T4/T5), produces a different trade selection that could partially offset the −0.4 to −1.1 geometry penalty T3 measures. The honest modal prediction is that it will not — but that is a backtest finding, not an EDA assertion.

**IS-only invariant.** Every script in `analysis/iteration_v3-115/` asserts `close_time < OOS_CUTOFF_MS` at load. No script reads any OOS-window file — there is no OOS annex, because there is no IS-tuned scalar parameter to fence (Section 0). The QR did not inspect the post-cutoff OOS in Phases 1–5.

### 2.8 Recorded EDA process note — a latent bug fixed vs the /114 EDA

The /114 EDA `_shared.py` triple-barrier labeler used the raw `natr_21_raw` value directly as an ATR *price distance*. `natr_21_raw` is a NATR **percentage** (IS median ~3–5). The production v3 labeler (`lgbm.py:_load_atr_for_master`) converts it: `atr_price = close × natr_pct / 100`. The /114 labeler's omission inflated the barrier 100–6000× for LDO/TRX (close ~$0.09–$1.9), making every candle time out. The iter-v3/115 `_shared.py` applies the correct `atr_price = close × natr_pct / 100` conversion, so the barrier mix matches production (BCH IS: ~57% TP, ~42% SL, ~1% timeout — the realistic mix). This is a real bug fix; the /114 axis (a kill-switch) did not depend on the barrier mix being right, so the bug was latent there. It is recorded here per the no-rationalization discipline.

---

## Section 3 — Proposed Changes

ONE axis: the **labeling architecture**, swapped from triple-barrier to coherent horizon-exit.

- **Labeling** — `label_mode`: `"triple_barrier"` → `"fixed_horizon"`. The training label becomes `sign` of the realized 21-candle forward net return (`labeling.py` already implements the `fixed_horizon` branch — lines 411–423; no new labeling code). Horizon N = 21 candles, FIXED (Section 0).
- **Execution** — the backtest exit geometry is made horizon-coherent: every trade exits at the fixed 21-candle timeout, the TP/SL barriers made non-binding. This is the inseparable second component of a horizon-exit *labeling architecture* (Section 0.5, Section 3.5, Section 10). It is achieved with zero new backtest-engine code — see Section 3.5#2.
- **Symbols** — UNCHANGED. `V3_MODELS` = BCHUSDT, LDOUSDT, TRXUSDT. No `V3_EXCLUDED_SYMBOLS` interaction (no symbol added).
- **Features** — UNCHANGED. The 14 `V3_FEATURE_COLUMNS` (the /059-canonical stack, reverted from /113's 22 at the /114 setup). No feature added → no cluster-importance / IC check applies. Critic Check 4 is non-applicable.
- **Risk gates** — UNCHANGED. The 7-primitive RiskV2 stack is /059-identical; RiskV3 primitive 9 stays DISABLED (CLOSED at /114).
- **Model** — UNCHANGED. Per-symbol LightGBM, `--model lgbm`, the unified 3-seed EXPLORATION ensemble (outer=42 lineage).

### Configuration Diff vs /059

| Knob | /059 canonical | iter-v3/115 | Changed? |
|---|---|---|:--:|
| `label_mode` | `triple_barrier` | **`fixed_horizon`** | ✔ (the axis) |
| Execution exit geometry | TP/SL/timeout (ATR ×2/×1 barriers) | **fixed 21-candle timeout** (barriers non-binding) | ✔ (the axis — inseparable) |
| label/exit horizon N | 21 candles (10080 min) | 21 candles (10080 min) | ✗ |
| `V3_MODELS` | BCH/LDO/TRX | BCH/LDO/TRX | ✗ |
| `V3_FEATURE_COLUMNS` | 14 | 14 | ✗ |
| `REQUIRED_GAP` | 66 = (21+1)×3 | 66 = (21+1)×3 | ✗ |
| CV embargo | 22 candles | 22 candles | ✗ |
| 7-gate RiskV2 stack | as /059 | as /059 | ✗ |
| ENSEMBLE / seeds / `n_trials` | 3-seed EXPLORATION, 35 | 3-seed EXPLORATION, 35 | ✗ |
| `OOS_CUTOFF_DATE` / `training_months` | 2025-03-24 / 24 | 2025-03-24 / 24 | ✗ |

---

## Section 3.5 — Precise `src/` Changes for the QE (Phase 6)

The QE makes ONLY the changes below. Do NOT edit features, symbols, or the risk stack. PRESERVE `V3_MODELS` = (BCH, LDO, TRX), the 14-feature `V3_FEATURE_COLUMNS`, the per-symbol LightGBM architecture, the unified ensemble seeds.

**Change 1 — the label (`run_baseline_v3.py`, `_build_v3_model`, `common_kwargs`, ~line 1978).**
Set `label_mode="fixed_horizon"` (currently `"triple_barrier"`). Update the multi-line comment block above it (lines ~1966–1977) to state the iter-v3/115 axis. `labeling.py`'s `fixed_horizon` branch already exists and is correct (verified — lines 349, 411–423: no barriers scanned, label = `sign` of the realized N-candle net return, scan runs to the timeout candle). **No `labeling.py` change.** Leave `neutral_threshold_pct` unset / `None` (a 2-class fixed-horizon label, matching /072 — a 3-class version is the /099 abstention dead path and must NOT be introduced).

**Change 2 — the execution exit geometry (`run_baseline_v3.py`, `_build_v3_model`).**
The coherent horizon-exit design requires every trade to exit at the fixed 21-candle timeout. The v3 LightGBM emits per-trade `tp_pct = natr × atr_tp_multiplier` and `sl_pct = natr × atr_sl_multiplier` (`lgbm.py:get_signal` lines 737–745); the backtest `check_order` checks timeout first (`backtest.py:483`), then SL/TP. Make the SL/TP barriers **non-binding** so every trade reaches the timeout: in `common_kwargs` set `atr_tp_multiplier` and `atr_sl_multiplier` to a large constant — **`100.0`** (a per-trade `tp_pct/sl_pct` of ~370%+ on an IS NATR median of ~3.7%, far beyond any 21-candle move; verified — see note below). This produces a true fixed-horizon execution with **zero new backtest-engine code**. `atr_tp_multiplier`/`atr_sl_multiplier` under `label_mode="fixed_horizon"` do NOT affect the label (the `fixed_horizon` labeler ignores barriers entirely — `labeling.py:411`), so this is purely an execution change. Keep `use_atr_labeling=True` and `atr_column="natr_21_raw"` unchanged (still consumed for the `tp_pct/sl_pct` arithmetic).
- **Verification the QE must run before the backtest** (and report in the engineering report): on the IS panel, confirm `(21-candle max favourable / adverse excursion as a fraction of entry) < 100 × natr_pct/100` for ≥ 99% of candles — i.e. confirm the ×100 barrier is non-binding on essentially all IS trades. If any symbol shows > 1% of candles where a ×100 ATR barrier would still bind, raise `atr_tp_multiplier`/`atr_sl_multiplier` to `1000.0` and re-verify. The engineering report must state the realized exit-reason mix (target: ≥ 99% `timeout`, the signature of coherent horizon execution).
- The `BacktestConfig.stop_loss_pct=4.0` / `take_profit_pct=8.0` (line 1927–1928) are the *fallback* SL/TP used only when a Signal carries no `tp_pct/sl_pct`; the v3 LightGBM always sets them from ATR, so these fallbacks are never reached and need NOT change. `BacktestConfig.timeout_minutes=10080` is correct as-is (the 21-candle horizon) and must NOT change — `_verify_timeout_consistency` (line 1247) asserts it equals `label_timeout_minutes=10080`; both stay 10080.

**Change 3 — the `label_mode` accretion guard (`run_baseline_v3.py`, ~line 1090).**
The `_canonical_v059` config-accretion guard hard-asserts `("label_mode", _acc_inner.label_mode, "triple_barrier")`. Update the expected value to `"fixed_horizon"`. Update the iter-v3/111 comment block above it (lines ~1088–1096) to record the iter-v3/115 deliberate `label_mode` change (this is NOT the /110 stale-knob confound — it is the intended axis; the guard's purpose is to catch *un*intended carry-over, so the expected value is updated in lockstep with the deliberate change). Also update the per-model `label_mode` assertion (lines ~1186–1196, `expected_label_mode = "triple_barrier"`) to `"fixed_horizon"`, with a comment recording the iter-v3/115 axis. The two guard messages' prose ("/059-canonical", "triple_barrier restored") must be rewritten so they do not contradict the new state.

**Change 4 — `ITERATION_LABEL` (`run_baseline_v3.py`, line 131).** `"v3-114"` → `"v3-115"`.

**Change 5 — revert the iter-v3/114 LDO kill-switch state to /059-canonical (`run_baseline_v3.py`, `_build_v3_model`, `RiskV2Config` block, lines ~2018–2028).** Branch `iteration-v3/115` was cut from `iteration-v3/114`, so the /114 risk-primitive-9 state is LIVE in the runner. Sections 3 and 6 declare the risk stack "/059-identical, primitive 9 DISABLED (CLOSED at /114)" — Change 5 is the edit that makes the runner match that declaration. Without it the /114 LDO realvol kill gate runs through the /115 backtest and co-varies with the labeling-architecture axis (the iter-v3/110 `trend_scanning` stale-knob confound, exactly). The current state and the intended /059-canonical state:

| Line | Current (/114 state, live on branch) | iter-v3/115 (/059-canonical) |
|---|---|---|
| ~2020 | `regime_gate_symbols=("LDOUSDT",),  # CHANGED from () — LDO is the gate target` | `regime_gate_symbols=(),` |
| ~2026 | `enable_ldo_realvol_gate=True,  # NEW — iter-v3/114 axis: kill_LOW gate ON` | `enable_ldo_realvol_gate=False,` |
| ~2027 | `ldo_realvol_zscore_floor=0.30,  # NEW — IS-calibrated (EDA SHA d8a9725)` | `ldo_realvol_zscore_floor=0.30,` — KEEP (inert when the gate is off) |
| ~2028 | `ldo_realvol_lookback_bars=90,  # NEW` | `ldo_realvol_lookback_bars=90,` — KEEP (inert when the gate is off) |

Set `regime_gate_symbols=()` (revert from `("LDOUSDT",)`) and `enable_ldo_realvol_gate=False` (revert from `True`). Leave `ldo_realvol_zscore_floor=0.30` and `ldo_realvol_lookback_bars=90` as-is — they are inert when `enable_ldo_realvol_gate=False`, and keeping them avoids touching the RiskV2Config field set. Rewrite the iter-v3/114 comment block (lines ~2023–2025, the three lines beginning `# iter-v3/114: kill_LOW-polarity LDO-realvol-zscore trigger`) to record that the iter-v3/114 primitive-9 axis is CLOSED and iter-v3/115 reverts to the /059-canonical risk stack (primitive 9 DISABLED) — so the comment does not contradict the reverted state. `enable_regime_gate=False` at line 2018 is already /059-canonical and must NOT change. This restores the 7-primitive RiskV2 stack to /059-identical exactly as Sections 3 and 6 declare. Note: the 13-knob `_canonical_v059` accretion guard (lines ~1079–1107) does NOT cover `enable_ldo_realvol_gate` / `regime_gate_symbols`, so Change 5 is not enforced by that guard — it is enforced only by Change 6's pre-flight guard, which makes Change 5 mandatory in lockstep.

**Change 6 — update the iter-v3/114 pre-flight guard to assert the reverted state (`run_baseline_v3.py`, `_build_v3_model`, lines ~847–869).** The /114 setup added a hard pre-flight guard — two `if` blocks raising `RuntimeError` — that asserts the /114 LDO kill-switch state. After Change 5 reverts that state, this guard will CRASH the runner on pre-flight unless it is updated. The QE must REPLACE the current guard (the comment block at lines ~847–854 plus the two `if` blocks at lines ~855–869) with a guard that asserts the /059-canonical reverted state.

The current code to replace (lines ~847–869 verbatim):

```python
    # iter-v3/114: Primitive 9 is RE-TARGETED from TRX to LDO with a NEW
    # kill_LOW-polarity ldo_realvol_zscore trigger (the cycle-6 EXPLORATION #5
    # risk axis). The /075-era "regime_gate_symbols must be ()" guard is
    # superseded: /114's axis REQUIRES the LDO-scoped kill_LOW gate ON. The
    # guard now asserts exactly the /114 state — LDO is the sole gate target
    # AND the kill_LOW realvol gate is enabled — so an accidental drift
    # (empty symbols, wrong symbol, or the gate left off) still crashes
    # pre-flight.
    if strat_check.config.regime_gate_symbols != ("LDOUSDT",):
        raise RuntimeError(
            f"RiskV2Config.regime_gate_symbols = {strat_check.config.regime_gate_symbols} "
            '— expected ("LDOUSDT",). iter-v3/114: primitive 9 is re-targeted to '
            "LDO with the kill_LOW realvol trigger; regime_gate_symbols must be "
            '("LDOUSDT",).'
        )
    if not strat_check.config.enable_ldo_realvol_gate:
        raise RuntimeError(
            "RiskV2Config.enable_ldo_realvol_gate = False — expected True. "
            "iter-v3/114: the LDO-realvol kill_LOW gate (primitive 9 variant) "
            "IS the iteration axis and must be ON. Set "
            "enable_ldo_realvol_gate=True in RiskV2Config init in "
            "_build_v3_model."
        )
```

The intended replacement (asserts the reverted /059-canonical state):

```python
    # iter-v3/115: the iter-v3/114 primitive-9 axis (LDO-scoped kill_LOW
    # ldo_realvol_zscore gate) is CLOSED. iter-v3/115 reverts to the
    # /059-canonical risk stack — primitive 9 DISABLED, no LDO regime-gate
    # target. The /075-era "regime_gate_symbols must be ()" semantics are
    # restored. This guard now asserts the reverted /059-canonical state, so
    # an accidental carry-over of the /114 kill-switch state (the
    # iter-v3/110 trend_scanning stale-knob confound) crashes pre-flight.
    if strat_check.config.regime_gate_symbols != ():
        raise RuntimeError(
            f"RiskV2Config.regime_gate_symbols = {strat_check.config.regime_gate_symbols} "
            "— expected (). iter-v3/115: the iter-v3/114 LDO primitive-9 axis is "
            "CLOSED; the /059-canonical risk stack has no regime-gate target. Set "
            "regime_gate_symbols=() in RiskV2Config init in _build_v3_model."
        )
    if strat_check.config.enable_ldo_realvol_gate:
        raise RuntimeError(
            "RiskV2Config.enable_ldo_realvol_gate = True — expected False. "
            "iter-v3/115: the iter-v3/114 LDO-realvol kill_LOW gate (primitive 9 "
            "variant) axis is CLOSED; iter-v3/115 reverts to the /059-canonical "
            "risk stack with primitive 9 DISABLED. Set "
            "enable_ldo_realvol_gate=False in RiskV2Config init in "
            "_build_v3_model."
        )
```

Equivalently the QE MAY delete the iter-v3/114-specific guard entirely (the comment block at ~847–854 plus both `if` blocks at ~855–869) — the guard is iter-v3/114-axis-specific and the /059-canonical risk stack has no live primitive-9 state for it to protect. Either action — replace with the reverted-state assertion above, OR remove the /114-specific guard — is acceptable; the replacement is preferred because it keeps an anti-drift guard against a future accidental re-enable of primitive 9. What is NOT acceptable is leaving the guard as-is: after Change 5 the current guard's two `RuntimeError` branches both fire and the runner crashes on pre-flight. Change 5 and Change 6 MUST land together — Change 5 without Change 6 crashes the runner; Change 6 without Change 5 crashes the runner the other way.

**`REQUIRED_GAP` — NO CHANGE.** The label/exit horizon N = 21 candles is identical to the v3 triple-barrier timeout. The CV embargo is `compute_embargo_candles(10080, 480) = 21 + 1 = 22` candles; `REQUIRED_GAP = (timeout_candles + 1) × n_symbols = (21 + 1) × 3 = 66`. Both are byte-identical to /059. The horizon N being fixed at 21 is precisely why (Section 0). The QE must NOT touch `REQUIRED_GAP` or the embargo helper. `_assert_required_gap` (line ~1224) and `_verify_timeout_consistency` (line 1247) both still pass unchanged — the QE must confirm this in the Phase-6 pre-flight.

**Track isolation:** no `features_v3` change, so no `crypto_trade.features` / `features_v2` import risk. All six changes are confined to `run_baseline_v3.py` — `_build_v3_model` (the `common_kwargs` label/execution change, the `RiskV2Config` /114-revert of Change 5, and the /114 pre-flight guard of Change 6), the 2 `label_mode` accretion-guard sites of Change 3, and `ITERATION_LABEL`. No other file is touched.

**Smoke test (brief Section 9 / Phase 5.5 integration-test requirement):** the QE adds one integration test asserting that, with `label_mode="fixed_horizon"` and `atr_tp_multiplier=atr_sl_multiplier=100.0`, a short backtest slice produces a trade roster whose `exit_reason` is ≥ 99% `timeout` (the coherent-horizon-execution signature) — the end-to-end check that the label change and the execution change landed together. `labeling.py`'s existing `fixed_horizon` backward-compat behaviour is already test-covered; the new surface is the label+execution *pairing*, which this test exercises.

---

## Section 4 — Expected OOS Impact

**Anchor:** the /060 EXPLORATION-mode reference — IS monthly Sharpe **+0.8325** / OOS monthly Sharpe **+0.1403** (3-seed, the standard cycle-6 EXPLORATION anchor; the CONFIRMATION /059 anchor is IS +1.0894 / OOS +0.5791 and is not the EXPLORATION comparator).

**Modal prediction (EDA verdict = NO-GO, so the prediction is centred at or below the anchor):**
- **IS monthly Sharpe point estimate: +0.30**, 80% interval **[−0.40, +0.85]**. The T3 counterfactual shows the horizon-exit execution geometry costs −0.4 to −1.1 monthly Sharpe vs triple-barrier on identical direction calls (an ORACLE upper-bound metric); production Optuna fits the *new, more-feature-predictable* horizon-exit label (T4/T5) so the realized IS could land above the raw T3 penalty if the model's trade selection partially offsets the geometry loss — but the modal expectation is an IS reduction. The interval is centred below the anchor and is wide because T3 is an ORACLE proxy, not a production measurement.
- **OOS monthly Sharpe point estimate: +0.05**, 80% interval **[−0.55, +0.55]**. Centred at/below the anchor's +0.1403 per the NO-GO discipline (`feedback_v3` /113 Lesson 3: when the decisive EDA gate fails, centre BOTH the IS and the OOS interval at or below the anchor). The wide interval reflects the genuine residual uncertainty — the production LightGBM on the more-learnable horizon-exit label is a real degree of freedom the ORACLE T3 cannot resolve.

**Falsifier (the hypothesis "horizon-exit coherence helps" is REJECTED if):** OOS monthly Sharpe < +0.34 (i.e. fails to clear the cycle-6 axis-PASS bar of OOS Δ ≥ +0.20 above the /060 anchor +0.1403). Given the NO-GO EDA, the falsifier is *expected* to fire — that is the honest modal call.

**Supplemental SUSPICIOUS gate** (per `feedback_v3_oos_is_ratio_gate.md`, mandatory for every cycle-2+ EXPLORATION brief): if OOS/IS monthly Sharpe ratio > 3.0, the result is flagged SUSPICIOUS regardless of absolute OOS Sharpe — a horizon-exit label is a different estimand and a 21-candle hold is a longer-duration trade, so an IS-collapse / OOS-spike divergence (the /105 signature, and /105 is the direct structural cousin of this axis) is a live risk; the ratio-gate catches it.

---

## Section 5 — Risk Mitigation

iter-v3/115 changes the labeling architecture only; it adds no new risk primitive, so there is no new IS-calibrated threshold to simulate. The risk posture is the existing /059 7-gate RiskV2 stack, unchanged. Two axis-specific risks and their mitigations:

1. **Longer effective trade duration.** A fixed 21-candle hold means every trade runs the full horizon (vs the triple-barrier mix where ~57% of BCH trades exit early on a TP and ~42% on an SL — T2.8). Longer holds raise per-trade drawdown exposure. **Mitigation:** the existing vol-scaling and BTC-trend gates in the RiskV2 stack act on entry regardless of exit geometry; the timeout horizon (21 candles ≈ 7 days) is itself a hard exposure cap. The engineering report must report IS and OOS MaxDD vs /059 (IS 30.97% / OOS 34.53%) — a MaxDD blow-out is a pre-registered failure signature (Section 7).
2. **The /072 catastrophic-LDO precedent.** iter-v3/072 (fixed-horizon label, mismatched execution) drove LDO OOS to −32.49 wpnl / 21.4% WR. iter-v3/115's *coherent* design removes the /072 mismatch mechanism (T2: the /072 mismatch goes to 0 by construction), so the /072 LDO collapse should not recur for the /072 reason. **Mitigation / monitor:** the engineering report must give per-symbol OOS attribution with ONE named metric (`net_pnl_pct` from `per_symbol.csv` if the OOS book total is near zero, else `concentration_pct` — per the /111 Critic Rec 2 + /114 Lesson 3 process rule); if LDO OOS collapses again it is a *new* mechanism (the time-exit geometry itself), distinct from /072, and must be reported as such.

There is no kill-switch, no drawdown brake, no OOD-threshold change — nothing IS-tuned, so per `feedback_v3_brief_parameter_provenance.md` there is no provenance fence to construct.

---

## Section 6 — Risk Management Design

No new risk-management primitive is introduced. The 7-primitive RiskV2 gate stack is /059-identical and is summarised here for completeness; all fire-rates and regime coverage are inherited from /059 unchanged (the labeling change does not alter the gate logic — the gates act on entry features, which are unchanged).

| # | Primitive | iter-v3/115 state | Fire-rate / note |
|---|---|---|---|
| 1 | BTC-trend kill | as /059 (±15% band, 14d) | unchanged — acts on BTC price, label-independent |
| 2 | Vol scaling | as /059 | unchanged — entry-feature gate |
| 3 | ADX threshold | as /059 (20.0) | unchanged |
| 4 | Hurst regime | as /059 | unchanged |
| 5 | Feature z-score OOD | as /059 (\|z\|>2.0) | unchanged |
| 6 | Low-vol filter | as /059 | unchanged |
| 7 | Hit-rate feedback | DISABLED (as /059) | unchanged |
| 9 | Regime kill-switch | DISABLED (CLOSED at /114) | unchanged — not re-opened |

**Regime coverage:** the gate stack's coverage of the IS window (2022-09→2025-03, bear+chop) and the OOS window (2025-03→2026-05, uptrend) is identical to /059. The single behavioural change vs /059 is the *exit geometry* — every trade now exits at a fixed 21-candle horizon rather than at a price barrier. The expected behavioural effect (per `feedback_v3_axis_saturation_predictor.md`): the IS trade roster will change **materially** — T1 shows ~25–30% of candles get a different directional label, and the exit geometry change is total (100% of exits move from a TP/SL/timeout mix to timeout-only). This is NOT a behaviorally-inert axis; the falsifier for inertia (IS roster Δ < 8% vs /060) is *not* expected to fire — if it does, the `label_mode`/execution change did not land and is an implementation bug (Section 7, Mode 3).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Modal failure mode (the EDA verdict is NO-GO, so this is the most likely outcome — probability ~60%): the horizon-exit geometry does not transfer — IS and/or OOS Sharpe lands at or below the /060 anchor.** The T3 counterfactual is unambiguous: on identical directional calls, the fixed-horizon time exit produces a monthly Sharpe −0.4 to −1.1 *below* the triple-barrier price-barrier exit, on all 3 symbols. The mechanism: the asymmetric +2/−1 ATR barrier — a tight stop that cuts losers fast and a wide target that lets winners run — is itself a Sharpe-generating device; a symmetric 21-candle time exit holds losers to the full horizon and caps winners at the 21-candle mark, discarding that asymmetry. In metrics this failure looks like: IS monthly Sharpe in [−0.40, +0.85] (modal ~+0.30, below the +0.8325 anchor), OOS monthly Sharpe in [−0.55, +0.55] (modal ~+0.05, below the +0.1403 anchor), profit factor down, MaxDD up (longer holds), and the trade roster materially changed (so it is NOT inert — the axis genuinely ran and genuinely underperformed). The pre-registered Section 8 NEGATIVE criterion fires. This is the honest modal call.

**Second failure mode (~25%): IS-collapse / OOS-spike SUSPICIOUS divergence — the /105 signature.** iter-v3/115 is the direct structural cousin of iter-v3/105 (a different estimand for the primary model). /105 collapsed the IS fit (−0.61) yet spiked OOS (+1.19) — an overfitting signature, not an edge, because the IS Optuna fit on a noisier/different estimand overfits in-sample while the OOS uptrend rewards the longer-held trades. The horizon-exit label is a different estimand AND a 21-candle hold is a longer-duration trade than the triple-barrier mean — both vectors the `feedback_v3_is_oos_regime_divergence.md` rule identifies. If iter-v3/115 lands IS low and OOS high with OOS/IS ratio > 3.0, the Section-4 supplemental SUSPICIOUS gate fires and the iteration is classified SUSPICIOUS-OOS-DOMINANT, not PROMISING — the OOS number would be a regime artifact, not a discovered edge.

**Third failure mode (~10%, low-probability — an implementation bug): behavioral inertia or a mis-landed change.** If the engineering report shows the IS roster Δ < 8% vs /060, or the exit-reason mix is not ≥ 99% `timeout`, the `label_mode="fixed_horizon"` change and/or the ×100-ATR execution change did not land — Change 1, 2, or 3 was incomplete. The Section 3.5 smoke test and the engineering-report exit-mix verification exist to catch exactly this; a Critic Check 8 (Hypothesis-Implementation Alignment) FAIL would flag it.

**Residual upside (~5%): coherence genuinely helps.** The least-likely outcome — assessed low because the EDA verdict is NO-GO and T3 is unambiguous across all 3 symbols. The only mechanism by which it could happen: the production LightGBM, trained on the more-feature-predictable horizon-exit label (T4: IC ratio ~1.5×; T5: clears the permutation null), selects a *materially better* set of trades than the ORACLE-perfect-direction T3 proxy assumes — enough to overcome the −0.4 to −1.1 geometry penalty. T4/T5 establish the horizon-exit label is genuinely more learnable, so this is not impossible — but per the iter-v3/105 lesson, a more-learnable label does not imply a better trade book, and T3 says the geometry itself is the bottleneck. If it does happen, the iteration is EXPLORATION-PROMISING and the labeling architecture advances to the iter-v3/120 CONFIRMATION.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

iter-v3/115 is an EXPLORATION; it cannot MERGE and cannot update `BASELINE_V3.md` regardless of outcome (`v0.v3-115` will be a closeout marker only; canonical baseline remains `v0.v3-059`). The criteria below are the pre-registered EXPLORATION classification thresholds, locked before the Phase-6 backtest, anchored on the **/060 EXPLORATION-mode reference (IS +0.8325 / OOS +0.1403)** per `feedback_v3_cycle1_axis_pass_criteria.md`. First-match-wins disjunctive taxonomy:

1. **EXPLORATION-NEGATIVE** if IS monthly Sharpe Δ < **−0.10** vs the /060 anchor (IS < +0.7325) **OR** OOS monthly Sharpe Δ < **+0.20** vs the /060 anchor (OOS < +0.3403). Either leg fires → NEGATIVE. **(This is the modal pre-registered outcome — Section 7 Mode 1.)**
2. **SUSPICIOUS-OOS-DOMINANT** if criterion 1 does not fire AND the OOS/IS monthly Sharpe ratio > **3.0** (`feedback_v3_oos_is_ratio_gate.md`) — the result is classified SUSPICIOUS, not PROMISING, regardless of the absolute OOS Sharpe. (Section 7 Mode 2.)
3. **EXPLORATION-INERT** if criterion 1 does not fire AND the IS trade roster changed < **8%** vs the /060 roster (the behavioral-inertia falsifier) — the `label_mode`/execution change did not materially alter the gated roster (Section 7 Mode 3 — an implementation-bug signature; would also draw a Critic Check 8 FAIL).
4. **EXPLORATION-PROMISING** if none of 1–3 fires AND IS monthly Sharpe Δ ≥ **+0.10** (IS ≥ +0.9325) AND OOS monthly Sharpe Δ ≥ **+0.20** (OOS ≥ +0.3403) AND `frac_positive_paths` ≥ **0.50** — the coherent horizon-exit architecture advances to the iter-v3/120 CONFIRMATION as a candidate bundle ingredient. (Section 7 residual-upside outcome.)

The bundle-level OOS trade-rate floor (≥130 OOS trades, `feedback_v3_trade_rate_floor_bundle_level.md`) applies at the iter-v3/120 CONFIRMATION, not per-EXPLORATION-row; iter-v3/115's OOS trade count is reported and informational only. DSR / PSR are EXPLORATION-mode structural artifacts at the 3-seed/35-trial budget (`feedback_v3_dsr_mode_artifact.md`) — informational only; only PBO is meaningful at EXPLORATION budget. The Pareto check is non-applicable to a single-roster EXPLORATION under the unified-ensemble architecture.

---

## Section 9 — Library Stack Declaration

iter-v3/115 introduces no new library. The labeling change uses the existing `labeling.py:label_trades` `fixed_horizon` branch (pure numpy/pandas — already in the tree, already test-covered for backward compatibility). The execution change is a `_build_v3_model` kwargs change — no new code. Pinned stack, unchanged from /059:

- `lightgbm 4.6.0`, `optuna 4.8.0`, `numpy 2.2.6`, `pandas 3.0.0`, `scikit-learn 1.8.0`, `scipy 1.17.0`, `statsmodels 0.14.6`, `pyarrow 23.0.1`.
- CPCV / PBO / PSR / DSR via the in-tree `validation_v3.py` (no `mlfinlab` / `pypbo` external dependency at runtime — the v3 in-tree implementation, as for all prior v3 iterations).
- The EDA (`analysis/iteration_v3-115/`) uses only `numpy`, `pandas`, `lightgbm`, `scikit-learn` (`roc_auc_score`) — all already pinned.
- **Phase-6 integration test:** the QE adds one smoke test (Section 3.5) asserting the `label_mode="fixed_horizon"` + ×100-ATR execution pairing produces a ≥99%-`timeout` exit-reason mix — the end-to-end verification that both axis components landed (per `feedback_v3_methodology_axis_integration_test.md`, generalised: any axis whose correctness depends on two coupled changes landing together needs an end-to-end test, not just unit tests on each part).

---

## Section 10 — QR Audit Trail & Dead-Path Disclosure

**Axis selection (per `feedback_v3_axis_selection_quant_discipline.md`).** The axis was QR-chosen with committed IS-only EDA backing (`analysis/iteration_v3-115/`, 3 scripts + 6 tables, EDA SHA — Section 10 commit chain) preceding this brief. The iter-v3/114 closeout recommended "a NEW labeling architecture — triple-barrier + meta-labeling secondary filter, OR a directional fixed-horizon return label." The QR adjudicated between the two:

- **Meta-labeling was rejected on existing committed evidence.** iter-v3/108 ran the /017-corrected meta-labeling EDA — a take/skip secondary model on a genuinely disjoint 18-feature set, on the canonical /059 IS roster — and conclusively proved it dead: held-out winner-vs-loser AUC 0.561 (< the 0.60 bar), sub-period-unstable, 0 of 5 model capacities clear the bar, permutation p = 0.18. The /108 finding ("the primary model's directional errors are NOT predictable from orthogonal information") closes the take/skip meta-labeling route. Re-proposing it would re-tread a NULL-AT-EDA. (This is the dead-path disclosure the iter-v3/114 brief applied for RiskV3 primitive 9, applied here for meta-labeling.)
- **The directional fixed-horizon label was chosen — but the QR identified that the *naive* fixed-horizon-label-only design is ALSO a dead path.** iter-v3/072 tested fixed-horizon-label-only (execution unchanged) → EXPLORATION-NEGATIVE. The QR did NOT re-propose /072. The QR proposes the **specific 2-component design iter-v3/072's own Critic Recommendation 1 named as the un-spent structural axis**: "A coherent fixed-horizon design needs BOTH a fixed-horizon label AND fixed-horizon execution exit — a 2-axis change requiring its own brief." iter-v3/115 is that brief. The EDA's decisive test (T3) is precisely the iter-v3/072 Critic Recommendation 3 mandate ("a label-vs-execution-consistency diagnostic … reframe disagreement-with-execution as a falsifier"). The /072 dead path is disclosed, and the design is distinguished from it on a committed-Critic-recommendation basis, not a hand-wave.

**Why "label + execution" is ONE axis, not a cross-axis violation (the Phase 5.5 single-axis question).** The v3 EXPLORATION single-axis rule forbids changing *features OR symbols OR labels* simultaneously. iter-v3/115 changes none of those in combination — it changes the **labeling architecture**, and label-execution consistency is a *defining property* of a labeling architecture, exactly as the triple-barrier label is inseparable from TP/SL/timeout execution. A fixed-horizon label with mismatched barrier execution is not "a labeling architecture with one knob held back" — it is the iter-v3/072 *incoherent* design the Critic explicitly ruled a dead path. iter-v3/072's own runner threaded `label_mode` as the axis; the /072 Critic ruled the coherent 2-component change the *single correct* test. The Phase 5.5 gate should read the axis as: ONE axis = the labeling architecture; the label and the exit are the two inseparable halves of it, not two axes.

**Provenance discipline (per `feedback_v3_brief_parameter_provenance.md`, established by the iter-v3/114 Check-1 FAIL).** This brief cites exactly one design parameter — the horizon N — and it is **hand-fixed at 21 candles, DECLARED hand-chosen (Section 0), and chosen for embargo-invariance, not IS performance.** There is no IS-tuned scalar, no sweep, no threshold; nothing is laundered as an optimization output. There is therefore no IS-only selection table to commit and no OOS annex to fence — the EDA is wholly IS-only. The iter-v3/114 failure mode (a hardcoded constant with a false "T3 sweep" provenance) is structurally impossible here because nothing is tuned.

**No baseline change.** iter-v3/115 is an EXPLORATION; `BASELINE_V3.md` is UNCHANGED at `v0.v3-059`. `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are untouched. The walk-forward embargo fix (`e149e9d`) is inherited unchanged.

**Commit chain.**
- EDA: `analysis/iteration_v3-115/` — `_shared.py` (the /059-faithful triple-barrier + horizon-exit labelers, walk-forward folding), `horizon_exit_gating_eda.py` (T1–T5), `horizon_exit_synthesis.py` (T6 GO/NO-GO) + 6 result tables. EDA SHA `d871b22` (`analysis(iter-v3/115): coherent horizon-exit labeling gating EDA`).
- Brief: `briefs-v3/iteration_v3-115/research_brief.md` — this file (SHA: this commit).
- Setup commit (this brief + the `ITERATION_LABEL` is bumped by the QE in Phase 6, not here): the QE's Phase-6 commit carries Changes 1–6 of Section 3.5 — Changes 1–4 are the labeling-architecture axis; Changes 5–6 revert the iter-v3/114 LDO kill-switch state (live on this branch, cut from `iteration-v3/114`) back to /059-canonical, added per the Phase 5.5 gate (commit `2ee9119`).
