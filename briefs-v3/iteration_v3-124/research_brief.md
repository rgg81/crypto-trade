# iter-v3/124 Research Brief — Cycle-7 EXPLORATION #3 (LONGER-CADENCE LABELS axis-3, K=63 with Branch B ATR scaling)

**Axis**: NON-FEATURE TRAIN-TIME LABELING DURATION axis. `label_timeout_minutes` 10080 → **30240** (21 → **63 candles** at 8h; +200% forward-scan window). Coupled per EDA T4 with **Branch B** ATR scaling: `atr_tp_multiplier` 2.0 → **3.464** (≈ 2.0 × sqrt(3)) and `atr_sl_multiplier` 1.0 → **1.732** (≈ 1.0 × sqrt(3)). The DURATION extension and MAGNITUDE scaling are PROPORTIONALLY COUPLED — Branch B preserves the K=21 random-walk barrier-hit probability across the K extension.

**Cycle**: 7 EXPLORATION slot **#3 of 10**. Cycle-7 catalog state at /123 closeout: 2 EXPLORATIONs done (slot #1 /122 NEGATIVE-INERT, slot #2 /123 NEGATIVE-catastrophic; the cycle-7 cross-asset OHLCV-derived axis is CLOSED at 6th consecutive failure). /124 = first EXPLORATION on the LABELING DURATION axis since /068 NEGATIVE-catastrophic precedent (cycle 1 #9 at /060 anchor; IS Δ −0.35 / OOS Δ −0.48; K=42 with retained ATR (2.0, 1.0)).

**Lineage discipline**: /124 pivots AWAY from cross-asset entirely per /123 closeout Critic Rec 3 (the cross-asset OHLCV axis is CLOSED at 6th consecutive failure: /082/085/086/119/122/123). The longer-cadence labels axis-3 is the candidate recommended by Critic Rec 3 (the "1d or 3d horizon-extended triple-barrier" formulation). /068's K=42 NEGATIVE-catastrophic precedent at retained ATR (2.0, 1.0) drives Branch B's ATR scaling design: K=63 with proportional barrier scaling tests a STRUCTURALLY DIFFERENT hypothesis ("can horizon extension under preserved label semantics reveal incremental signal?") rather than the /068 hypothesis ("can horizon extension under fixed-barrier semantics reveal signal?", which was falsified).

**Anchor (EXPLORATION-mode comparison)**: iter-v3/121 multi-seed CONFIRMATION-MERGE BASELINE_V3.md numbers (IS monthly Sharpe **+1.3108** / OOS monthly Sharpe **+0.9682**) — the canonical anchor per `BASELINE_V3.md`. Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode 3-seed results compress relative to CONFIRMATION-mode 10-seed; the /077 vs /059 IS gap was ~−0.27 (3-seed-vs-10-seed proba-averaging effect). The /124 brief Section 4 reports against BOTH the /121 multi-seed baseline (the public anchor for documentation and Section 8 NEGATIVE-catastrophic threshold) AND the /121-architecturally-adjusted EXPLORATION-mode estimate (the falsifier band reference).

---

## Section 0 — Data Split declaration

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are UNCHANGED. The sacred constants are immutable across all three tracks; no /124 modification touches them.

- **IS window**: data extent start (per-symbol earliest 8h candle close ≥ 2020-01-01) through `OOS_CUTOFF_DATE = 2025-03-24` (exclusive).
- **OOS window**: `OOS_CUTOFF_DATE = 2025-03-24` through current data extent (~2026-05-20).
- **Walk-forward training window**: 24 calendar months ending at each test-month's start; rolling by 1 month.
- **Reporting layer**: `comparison.csv` and `in_sample/` / `out_of_sample/` directories split on `OOS_CUTOFF_DATE` exactly.
- **Bar interval**: 8h (cycle-6 candle-frequency axis broadly CLOSED per /117 closeout; cycle-7 stays at 8h).

**Hand-chosen parameter declaration (per `feedback_v3_brief_parameter_provenance.md`)**:

| Parameter | Value | Provenance |
|---|---|---|
| `label_timeout_minutes` | **30240** (= 63 × 480 min; K=63 candles at 8h) | Pre-selected per task spec / /123 closeout Critic Rec 3 ("63-candle timeout, recommended middle ground"). NOT tuned; structural choice based on K=42 (/068 NEGATIVE) and K=84 (most-extreme sample-uniqueness loss). |
| `atr_tp_multiplier` (Branch B) | **3.4641** (= 2.0 × sqrt(3); preserves K=21 σ-units barrier height) | EDA T4 derivation: random-walk variance σ_K = sqrt(K) × σ_1bar. K=63/K=21 = 3, sqrt(3) ≈ 1.7321. Preserves the K=21 (+2.0, -1.0) barrier ratio in K=63 σ-units (TP barrier at 0.44σ in both K=21 and K=63 σ-units; see EDA T4 print output). NOT tuned for /124; structurally fixed by the sqrt(K) random walk variance scaling. |
| `atr_sl_multiplier` (Branch B) | **1.7321** (= 1.0 × sqrt(3); same scaling logic) | Same scaling as `atr_tp_multiplier`. |
| `REQUIRED_GAP` (runner-local override) | **192** (= (63 + 1) × 3) | Per validation_v3.py formula: gap = (timeout_candles + 1) × n_symbols. validation_v3.py REQUIRED_GAP=66 constant requires runner-local override (precedent: /068 at K=42 = 129). |
| `per_cell_embargo` | **64** (= 63 + 1; per AFML purge convention) | Inherited from `compute_embargo_candles(label_timeout_minutes=30240, interval_minutes=480) = 30240 // 480 + 1 = 64`. |
| `_verify_timeout_consistency` runtime override | `expected_timeout_minutes = 30240` (NOT 10080) | The runner's `_verify_timeout_consistency` HARDCODES `10080`; /124 setup must override the hardcoded assertion (precedent at /068 setup `06a8cc2` and impl `0e9eb30` where the same assertion was rewritten). |

**Auditable temporal fence**: the EDA (`analysis/iteration_v3-124/`, commit SHA `e814bb2`) was committed in ONE atomic commit BEFORE this brief. The EDA script asserts `close_time < OOS_CUTOFF_MS = 1742774400000`; 0 OOS-leaked rows verified at runtime.

---

## Section 0.5 — Iteration Type Declaration

- **TYPE**: `EXPLORATION` (single structural axis: label-DURATION+MAGNITUDE coupled at sqrt(K) scaling per EDA T4)
- **Cycle 7 slot**: **#3 of 10**. iter-v3/131 is the projected final EXPLORATION (cycle-7 ends with iter-v3/132 CONFIRMATION per the strict 10:1 cadence; `feedback_v3_strict_10_to_1_cadence.md`).
- **CLI invocation**: `uv run python run_baseline_v3.py --exploration --n-trials 35` (default `--bar-interval 8h`)
- **ENSEMBLE_SIZE**: 3 (`EXPLORATION_ENSEMBLE_SIZE` per `feedback_v3_outer_seed_cap_2_v3.md`; first 3 seeds of the unified 10-seed lineage)
- **n_trials**: 35 (per `feedback_v3_exploration_n_trials_35.md` — above TPE warmup ~30)
- **Wall-clock cap**: ≤ 2h (cycle-7 EXPLORATION cap per `feedback_v3_cadence_discipline.md`)
- **Single axis variation (axis-isolation discipline per `feedback_v3_engineered_features_dont_stack.md`)**: ONE coupled axis = DURATION extension to K=63 + PROPORTIONAL MAGNITUDE scaling at sqrt(K) per EDA T4 adjudication. Both legs of the coupling are STRUCTURALLY MANDATED by random-walk variance scaling, NOT independently tunable — they constitute ONE substantive axis change (analogous to /068's single axis at K=42 with retained ATR). All other knobs (universe, gates, ensemble seeds, Optuna search space, /116 no_confirm primitive) are bit-identical to the /121 baseline.

---

## Section 1 — Hypothesis

> Extending the labeling horizon from K=21 → K=63 (3× forward scan) with PROPORTIONAL ATR barrier scaling at sqrt(K) (preserving the K=21 random-walk barrier-hit probability) carries incremental directional signal beyond the /121 baseline by allowing the model to learn predictors of MEDIUM-TERM directional moves (21–63 candles ≈ 7–21 days) that the K=21 horizon truncates. The hypothesis is TESTABLE via single-axis EXPLORATION; OR the longer-cadence labels axis-3 is FALSIFIED at production by an EXPLORATION-NEGATIVE result, closing the labeling-DURATION axis bilaterally (K=42 NEGATIVE at /068; K=63 NEGATIVE at /124) and informing cycle-7's axis-selection priors toward non-labeling-non-cross-asset axes (per Critic Rec 3 menu: "creative out-of-box" alternatives such as the per-symbol drawdown brake at closed-loop simulator layer).

---

## Section 2 — IS-Only Numerical Evidence

EDA (`analysis/iteration_v3-124/`, commit SHA `e814bb2`): 6 T-tables produced. The /124 EDA follows the /068 labeling_timeout_eda.py methodology pattern (first-order counterfactual on existing trade roster + sample-uniqueness analysis + ATR scaling adjudication), updated for /121-anchored evidence.

### Section 2.1 — T1 first-order counterfactual at K=21/42/63/84 on /121 trade roster

See `analysis/iteration_v3-124/T1_first_order_counterfactual.csv`:

| K_candles | sample | n_orig | n_resolved | n_truncated | pct_truncated | n_TP | n_SL | n_no_confirm | n_TIMEOUT |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 21 | in_sample | 173 | 173 | 0 | 0.00% | 56 | 91 | 10 | 16 |
| 21 | out_of_sample | 98 | 98 | 0 | 0.00% | 39 | 46 | 9 | 3 |
| 42 | in_sample | 173 | 173 | 0 | 0.00% | 56 | 91 | 10 | 16 |
| 63 | in_sample | 173 | 173 | 0 | 0.00% | 56 | 91 | 10 | 16 |
| 84 | in_sample | 173 | 173 | 0 | 0.00% | 56 | 91 | 10 | 16 |

**First-order INVARIANCE**: every /121 trade roster trade resolves within 21 candles. Counterfactual at K=42, K=63, K=84 leaves the trade roster bit-identical. This replicates /068's first-order finding (where Path C K=42 left /060 roster invariant — yet production at K=42 was IS Δ −0.35 / OOS Δ −0.48 catastrophic). **T1 is INFORMATIONAL ONLY**: the /068 NEGATIVE outcome was second-order dominated (Optuna re-convergence on changed LABEL POPULATION, not changed trade roster). T2-T6 capture the second-order mechanisms (sample-uniqueness, label-semantic shift).

### Section 2.2 — T2 per-symbol IS training sample count + F2 BINDING falsifier evaluation

See `analysis/iteration_v3-124/T2_per_symbol_training_samples.csv` (AFML Ch. 4 effective-sample-size approximation):

| symbol | K | is_candles_total | afml_eff_sample_size | sample_loss_pct_vs_K21 | per_cell_embargo | REQUIRED_GAP_at_K |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 21 | 6022 | 301 | +0.00% | 22 | 66 |
| BCHUSDT | 42 | 6022 | 146 | +51.50% | 43 | 129 |
| BCHUSDT | 63 | 6022 | 97 | +67.77% | 64 | 192 |
| BCHUSDT | 84 | 6022 | 72 | +76.08% | 85 | 255 |
| LDOUSDT | 21 | 2741 | 137 | +0.00% | 22 | 66 |
| LDOUSDT | 42 | 2741 | 66 | +51.22% | 43 | 129 |
| LDOUSDT | 63 | 2741 | 44 | **+67.74%** | 64 | 192 |
| LDOUSDT | 84 | 2741 | 33 | +75.90% | 85 | 255 |
| TRXUSDT | 21 | 5669 | 283 | +0.00% | 22 | 66 |
| TRXUSDT | 42 | 5669 | 138 | +51.22% | 43 | 129 |
| TRXUSDT | 63 | 5669 | 91 | +67.74% | 64 | 192 |
| TRXUSDT | 84 | 5669 | 68 | +75.90% | 85 | 255 |

**F2 BINDING falsifier (LDO IS training sample loss > 15% vs K=21) — TRIGGERED**: LDO sample loss at K=63 = **+67.74%**. The /124 axis is pre-flagged HIGH-RISK at EDA pre-flight. Per task spec, F2 is BINDING — the iteration MUST proceed with brief Section 6 explicit address of LDO mitigation. Branch B's proportional barrier scaling provides PARTIAL mitigation (preserves random-walk barrier-hit probability, so the model's per-candle decision quality is preserved even under reduced sample size) but is NOT a full mitigation (the absolute number of independent labels is still 1/3 of K=21 baseline). **The /124 axis is HIGH-RISK under F2 by construction; this is a known cost of the K=63 EXPLORATION**.

### Section 2.3 — T3 REQUIRED_GAP recompute + AFML sample-uniqueness loss

See `analysis/iteration_v3-124/T3_required_gap_uniqueness.csv`:

| K_candles | per_cell_embargo | cross_cell_gap_REQUIRED_GAP | afml_uniqueness_weight_per_label | uniqueness_ratio_vs_K21 | effective_sample_loss_pct |
|---:|---:|---:|---:|---:|---:|
| 21 | 22 | 66 | 0.02439 | 1.000 | +0.00% |
| 42 | 43 | 129 | 0.01205 | 0.494 | +50.60% |
| 63 | 64 | **192** | 0.00800 | 0.328 | **+67.20%** |
| 84 | 85 | 255 | 0.00599 | 0.246 | +75.45% |

REQUIRED_GAP at K=63 = 192 candles (3× current 66). validation_v3.py constant must be runner-locally overridden (precedent: /068 setup at K=42 = 129). AFML sample-uniqueness loss at K=63 = +67.20% effective sample size reduction. Optuna at n_trials=35 will see ~67% fewer independent labels per WF month → variance up. At K=84 the penalty grows to +75% (strictly worse than K=63; this is one reason K=84 is NOT the chosen extension level).

### Section 2.4 — T4 (LOAD-BEARING) ATR multiplier adjudication Branch A vs Branch B

See `analysis/iteration_v3-124/T4_atr_branch_adjudication.csv`. Per-symbol natr_21_raw IS-window statistics (mean):

| symbol | natr_21_mean_pct | branch_A_TP_pct_at_mean_natr | branch_B_TP_pct_at_mean_natr | branch_A_TP_in_K63_σ-units | branch_B_TP_in_K63_σ-units | branch_A_TP_in_K21_σ-units |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 4.21% | 8.43% | 14.60% | **0.25σ** | **0.44σ** | 0.44σ |
| LDOUSDT | 5.36% | 10.71% | 18.55% | 0.25σ | 0.44σ | 0.44σ |
| TRXUSDT | 3.27% | 6.54% | 11.32% | 0.25σ | 0.44σ | 0.44σ |

**T4 ADJUDICATION — Branch B SELECTED**. The QR decision is based on LABEL SEMANTIC PRESERVATION:

**Branch A risk (REJECTED)**: SAME barrier height in absolute % at K=63 vs K=21. In K=63 σ-units, the +2.0 ATR TP barrier is 0.25σ — MUCH CLOSER than K=21's 0.44σ. Random walk with 3× more steps has ~2× more chance of crossing either barrier in the larger search window. Predicted IS timeout rate at K=63 Branch A: 2–5% (LOWER than current 9.2%). The trade roster shifts toward TP/SL resolutions at very EARLY exit times. CORE RISK: **LABEL SEMANTIC SHIFT** — the same +1/-1 labels at K=21 vs K=63 Branch A encode DIFFERENT real-world events. At K=21 a +1 label means "TP at < 21 candles forward with embedded random walk over 21 steps"; at K=63 Branch A it means "TP at < 63 candles forward, often at 1–3 candles (the earliest barrier-hit moment in a much-larger random walk window)". The model trained on K=63 Branch A labels learns to predict random-walk barrier crossings, NOT directional momentum. Per /068's mechanism: trade-roster invariance does not protect against label-semantic regime shift in Optuna re-convergence.

**Branch B selected**: WIDER barriers (ATR scaled by sqrt(3)), 3× more scan time. In K=63 σ-units, the +3.46 ATR TP barrier is 0.44σ — SAME as K=21 baseline σ-units. Random-walk barrier-hit probability is PRESERVED across the K extension. Predicted IS timeout rate at K=63 Branch B: ~9–15% (similar to K=21's 9.2%). Label distribution preserves the K=21 SEMANTIC CHARACTER. The /124 axis tests "does longer forward scan reveal incremental signal under PRESERVED label semantics?" — a cleaner hypothesis than Branch A's "does the K=63-on-K=21-barriers regime work?" (which is a different and less-tractable hypothesis).

**Branch B residual risk (MAGNITUDE-coupling, documented in Section 6)**: inherits the /065 SUSPICIOUS-OOS-DOMINANT pattern (CONFIRMATION DROP at /070). /065 widened SL alone (K=21 fixed; SL 1.0 → 1.5 = +50%) and broke at multi-seed (IS Sharpe collapse −0.97). Branch B widens SL+TP proportionally with DURATION extension (SL 1.0 → 1.73 = +73%, larger than /065's +50%). HOWEVER: the mechanism that broke /065 was longer-hold of adverse trades — at Branch B the proportional barrier scaling MAY mitigate this since random-walk barrier-hit probability is preserved per-step. This is the GAMBLE — the residual risk is unfalsifiable at EDA and is the dominant probability mass for NEGATIVE outcomes in Section 7.

### Section 2.5 — T5 per-symbol baseline resolution distribution at K=21 (/121)

See `analysis/iteration_v3-124/T5_baseline_resolution_distribution.csv`:

| sample | symbol | n_trades | pct_TP | pct_SL | pct_TIMEOUT | pct_NO_CONFIRM | median_dur |
|---|---|---:|---:|---:|---:|---:|---:|
| in_sample | BCHUSDT | 85 | 36.5% | 45.9% | **12.9%** | 4.7% | 5.0 |
| in_sample | LDOUSDT | 9 | 33.3% | 44.4% | **0.0%** | 22.2% | 4.0 |
| in_sample | TRXUSDT | 79 | 27.8% | 60.8% | 6.3% | 5.1% | 4.0 |
| out_of_sample | BCHUSDT | 35 | 42.9% | 42.9% | 5.7% | 8.6% | 4.0 |
| out_of_sample | LDOUSDT | 12 | 25.0% | 66.7% | 0.0% | 8.3% | 4.0 |
| out_of_sample | TRXUSDT | 51 | 41.2% | 45.1% | 2.0% | 9.8% | 4.0 |

/121 baseline universe IS timeout rate = 9.2% (16/173); LDO has ZERO timeouts at K=21 in /121 (replicating the /068 T3 finding at /060). LDO is INSENSITIVE to timeout extension at trade-roster level; the failure mode for LDO is **sample-uniqueness loss (F2)**, NOT timeout-distribution change. BCH has the HIGHEST IS timeout rate (12.9%) — extending K is most likely to affect BCH's trade roster via the label-semantic preservation mechanism (T4 analysis).

### Section 2.6 — T6 falsifier set (Brief Section 4 binding falsifiers)

See `analysis/iteration_v3-124/T6_falsifier_set.csv`:

| Falsifier | Threshold | Binding | Trigger condition |
|---|---|---|---|
| **F1_catastrophic_IS_collapse** | IS Sharpe Δ < −0.40 vs /121 (+1.3108) | YES (NEGATIVE-catastrophic gate) | IS monthly Sharpe < +0.9108 |
| **F2_LDO_sample_loss** (TRIGGERED at EDA) | LDO IS training sample loss > 15% vs K=21 | YES (BINDING — task spec mandate) | LDO AFML eff-sample loss = +67.74% — TRIGGERED at EDA pre-flight |
| **F3_OOS_MaxDD_doubling** | OOS MaxDD > 2 × /121 OOS MaxDD = 51.40% | YES (the /068 mechanism — replicated) | /124 production OOS MaxDD > 51.40% |
| **F4_IS_timeout_rate_branch_check** | Branch B IS timeout rate NOT in [5%, 20%] | Branch B PRE-FLIGHT CHECK | /124 production IS timeout rate outside [5%, 20%] (RECLASSIFIED from task-spec original; EDA T4 refuted Branch A high-timeout-rate assumption) |
| **F5_universe_cascade** | All 3 symbols IS-negative weighted_pnl | YES (/123 mechanism — replicated) | BCH IS wpnl < 0 AND LDO IS wpnl < 0 AND TRX IS wpnl < 0 |
| **F6_OOS_Sharpe_collapse** | OOS Sharpe Δ < −0.40 vs /121 (+0.9682) | PAIRED-with-F1 | OOS monthly Sharpe < +0.5682 |

### Section 2.7 — T6 verdict synthesis

**EDA verdict: PROCEED-WITH-HIGH-RISK** at Branch B (K=63, ATR sqrt(3)-scaled). F2 is ALREADY TRIGGERED at EDA pre-flight (+67.74% LDO sample loss), but per task spec PRIME DIRECTIVE = brief + backtest (NO EDA-kill). The brief proceeds with explicit acknowledgment of F2 HIGH-RISK posture; Section 6 addresses LDO mitigation; Section 7 pre-registers F1-F6 falsifier outcomes with calibrated probabilities favoring NEGATIVE outcomes given the K=42 (/068) precedent.

The /068 K=42 retained-ATR result (IS Δ −0.35 / OOS Δ −0.48) is the BEST AVAILABLE PRIOR for the /124 K=63 axis. Branch B's sqrt(K) ATR scaling is a STRUCTURALLY DIFFERENT design from /068, motivating an EXPLORATION (not a pre-registered NEGATIVE). The /065 (+SL widening at K=21) → /070 CONFIRMATION DROP is a CORRELATED PRIOR — the MAGNITUDE-coupling component of Branch B inherits /065's risk profile.

---

## Section 3 — Proposed Changes (single-axis vs /121 baseline)

### Section 3.1 — Labeling-axis changes

1. **`label_timeout_minutes`**: 10080 → **30240** (21 → 63 candles at 8h).
2. **`atr_tp_multiplier`** (DEFAULT_ATR_MULTIPLIERS): 2.0 → **3.4641** (= 2.0 × sqrt(3)).
3. **`atr_sl_multiplier`** (DEFAULT_ATR_MULTIPLIERS): 1.0 → **1.7321** (= 1.0 × sqrt(3)).
4. **`BacktestConfig.timeout_minutes`**: 10080 → 30240 (must be consistent with `label_timeout_minutes`; the runner's `_verify_timeout_consistency` assertion enforces this — see Section 3.5).
5. **REQUIRED_GAP**: validation_v3.py constant 66 → runner-locally overridden to **192** (= (63 + 1) × 3).

### Section 3.2 — Carry-forward axes (UNCHANGED from /121)

- /116 no_confirm RULE-layer primitive STAYS ENABLED (`enable_no_confirm_exit=True`, `no_confirm_trigger_atr=0.50`, `no_confirm_k_candles=4`) per /121 BASELINE_V3.md canonical and user directive (locked constraint).
- /119 C6 (`ret5d_signed_tbi`) STAYS BANNED per /121 closeout PERMANENT DROP decision.
- /122 `eth_ret_3d` STAYS REMOVED per /122 NEGATIVE-INERT closeout.
- /123 `eth_vs_sym_rv_50` STAYS REMOVED per /123 NEGATIVE-catastrophic closeout. **V3_FEATURE_COLUMNS_TOP_N reverts to /121's 14-feature stack** (the cycle-7 cross-asset OHLCV axis is CLOSED).
- BCH/LDO/TRX universe UNCHANGED.
- LightGBM model UNCHANGED (per /016 model-arch closure).
- 5-gate RiskV2 stack + BTC trend filter UNCHANGED.

### Section 3.3 — Single-axis discipline

Per `feedback_v3_engineered_features_dont_stack.md`: ONE substantive axis change per EXPLORATION. The /124 axis is the COUPLED DURATION+MAGNITUDE pair at sqrt(K) proportional scaling, treated as ONE axis per EDA T4 structural mandate (random-walk variance σ_K = sqrt(K) × σ_1bar; the two legs are not independently tunable — the sqrt(3) coefficient is STRUCTURALLY FIXED by the K=63 choice). This is methodologically analogous to /068's single axis (DURATION extension to K=42 with retained ATR = ONE choice, not two).

### Section 3.4 — Risk-gate axes UNCHANGED

The 7-gate RiskV2 stack (vol scaling, ADX threshold, Hurst regime, z-score OOD, low-vol filter, hit-rate (OOS), BTC trend filter) is UNCHANGED. No new risk primitive at /124. The MAGNITUDE-coupling component of Branch B (SL widening to 1.73) is NOT a risk-gate change — it's a labeling-layer change that affects the LABEL POPULATION Optuna sees during training.

---

## Section 3.5 — Precise `src/` Changes for the QE (Phase 6)

| File | Change |
|---|---|
| `run_baseline_v3.py` | (a) `ITERATION_LABEL` "v3-123" → **"v3-124"**. (b) Line 2076 `BacktestConfig.timeout_minutes`: 10080 → **30240**. (c) Line 2112 `common_kwargs label_timeout_minutes`: 10080 → **30240**. (d) Lines 1253-1270 `_verify_model_config` block — UPDATE hardcoded `expected_label_timeout = 10080` to **`expected_label_timeout = 30240`**, with comment updating /069 history note to add /124 entry. (e) Line 1361 `_verify_label_leakage_gap`: at 8h, recompute `timeout_candles = 30240 // 480 = 63`; `required_gap = (63 + 1) * 3 = 192`; runner-local override on REQUIRED_GAP (do NOT update validation_v3.py constant). (f) Lines 1384-1404 `_verify_timeout_consistency`: UPDATE hardcoded `expected_timeout_minutes = 10080` to **`expected_timeout_minutes = 30240`**, with comment update for /124 axis. |
| `src/crypto_trade/features_v3/__init__.py` | UPDATE `DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.0)` → **`(3.4641, 1.7321)`** (Branch B sqrt(3) scaling). Add docstring history entry for /124 axis. `V3_ATR_MULTIPLIERS_PER_SYMBOL` stays empty `{}` (universal scaling, no per-symbol override). |
| `src/crypto_trade/strategies/ml/validation_v3.py` | The `REQUIRED_GAP` module-level constant STAYS at 66 (the 8h baseline; do NOT update; the /117 24h conditional formula stays at 72). Runner-local override at `_verify_label_leakage_gap` is the canonical pattern (mirrors /068 setup). The `_compute_per_cell_pbo` PER_CELL_GAP comment update only — no constant change. Per the task spec: "**REQUIRED_GAP 66 → 192 = (63+1) × 3 (per validation_v3 formula; runner-local override needed)**" — implements as a runner-local variable, not a module constant change. |
| `tests/strategies/ml/test_label_timeout_minutes.py` | NEW test additions: assert `compute_embargo_candles(30240, 480) == 64` (per-cell embargo); assert `compute_embargo_candles(10080, 480) == 22` (unchanged at K=21); assert the runner-side `_verify_timeout_consistency` accepts `expected_timeout_minutes = 30240`. |
| `tests/strategies/ml/test_cpcv_embargo_assert.py` | UPDATE: `TIMEOUT_CANDLES` 21 → **63**; `CORRECT_GAP` 66 → **192**; assert runner-local override matches formula `(63 + 1) * 3 = 192`. |
| `tests/strategies/ml/test_default_atr_multipliers.py` (if exists) OR `tests/test_features_v3/test_atr_multipliers.py` | UPDATE: assert `DEFAULT_ATR_MULTIPLIERS == (3.4641, 1.7321)` (Branch B); add inline math comment showing sqrt(3) = 1.7321. |

**Files NOT touched** (negative scope):
- `src/crypto_trade/strategies/ml/labeling.py` (label-trade barrier scan code unchanged; ATR multipliers passed via `atr_tp_multiplier` / `atr_sl_multiplier` parameters which the runner now sets to (3.4641, 1.7321)).
- `src/crypto_trade/strategies/ml/lgbm.py` (LightGbmStrategy params unchanged; only the values it receives change).
- `src/crypto_trade/strategies/ml/walk_forward.py` (`compute_embargo_candles` formula unchanged; it now returns 64 instead of 22 at K=63 because the input `label_timeout_minutes=30240` changes).
- `src/crypto_trade/features_v3/` (feature columns unchanged; V3_FEATURE_COLUMNS_TOP_N stays at /121's 14-feature stack — `eth_ret_3d` REMOVED per /122 NEGATIVE; `eth_vs_sym_rv_50` REMOVED per /123 NEGATIVE).
- `src/crypto_trade/strategies/risk_v2.py` (7-gate stack unchanged).
- `src/crypto_trade/backtest.py` (no new exit primitive; /116 no_confirm STAYS ENABLED with unchanged parameters).
- `src/crypto_trade/strategies/ml/validation_v3.py` REQUIRED_GAP CONSTANT (stays at 66; runner-locally overridden per Section 3.5 row 3).
- `OOS_CUTOFF_DATE`, `training_months` — sacred constants, immutable.

---

## Section 4 — Expected OOS Impact (predicted bands) — PER-CRITERION ANCHOR ANNOTATED

### Section 4.1 — Anchor-architecture adjustment (per /122 Critic Rec 3)

Per `feedback_v3_dsr_mode_artifact.md` and BASELINE_V3.md "EXPLORATION-vs-CONFIRMATION architecture-gap" finding: /121 baseline IS +1.3108 / OOS +0.9682 is a 10-seed CONFIRMATION-mode number. /124 runs at EXPLORATION 3-seed mode. The /077 vs /059 IS gap was ~−0.27 attributed entirely to the 3-seed-vs-10-seed proba-averaging architecture component.

| Anchor | Mode | IS Sharpe | OOS Sharpe | Use |
|---|---|---:|---:|---|
| /121 CONFIRMATION (canonical) | 10-seed | +1.3108 | +0.9682 | For CONFIRMATION-mode forward-looking gates AND Section 8 NEGATIVE-catastrophic threshold |
| **/121 EXPLORATION-mode estimate (architecturally adjusted)** | 3-seed estimate | **+1.06** | **+0.85** | **For /124 EXPLORATION-mode Δ classification (Section 7 modes)** |

The adjustment factor: IS −0.25, OOS −0.12 (cycle-2 calibration from /077 vs /059).

### Section 4.2 — Predicted bands (per-criterion anchor annotated)

Per /068 closeout mandate, labeling-DURATION axes pre-register WIDER bands than feature axes ([-0.50, +0.50] envelope vs feature axis ±0.30 typical). The /124 K=63 brief uses the task-spec mandated envelope IS Δ [−0.50, +0.50] / OOS Δ [−0.50, +0.50] (3–5× /122/123 envelopes).

| Arm | Modal predicted Δ vs /121 EXPLORATION-mode estimate (IS +1.06 / OOS +0.85) | Lower (catastrophic) | Upper (success) | **Anchor used** |
|---|---:|---:|---:|---|
| IS monthly Sharpe Δ | **−0.30 to +0.10** | **−0.50** (F1-equivalent at EXPLORATION estimate) | **+0.30** | /121 EXPLORATION-mode estimate |
| OOS monthly Sharpe Δ | **−0.30 to +0.20** | **−0.50** | **+0.40** | /121 EXPLORATION-mode estimate |

**Modal prediction band (EXPLORATION-mode reference):** IS Sharpe ∈ [+0.76, +1.16]; OOS Sharpe ∈ [+0.55, +1.05].

**Modal prediction band (against published /121 CONFIRMATION baseline):** IS Sharpe ∈ [+1.01, +1.41]; OOS Sharpe ∈ [+0.67, +1.17] (informational; subject to architecture compression).

### Section 4.3 — Prior calibration from /068 + /065

| Precedent | Setup | Outcome | Implication for /124 |
|---|---|---|---|
| /068 K=42 retained ATR | DURATION-only, /060 anchor | IS Δ −0.35 / OOS Δ −0.48 NEGATIVE-catastrophic | If /124 follows /068 mechanism (label-semantic shift dominant), expect NEGATIVE catastrophic at K=63 (larger K → larger effect). Branch B mitigates this via proportional ATR scaling. |
| /065 K=21 SL widened to 1.5 | MAGNITUDE-only, /060 anchor | IS Δ −0.97 OOS Δ +X SUSPICIOUS-OOS-DOMINANT at /070 CONFIRMATION | If /124 inherits /065 MAGNITUDE-coupling risk, expect IS-collapse + OOS-soar pattern. Branch B's MAGNITUDE leg (SL 1.0 → 1.73) is +73%, LARGER than /065's +50%. |

The /124 axis is a NOVEL COMBINATION of /068's DURATION extension and /065's MAGNITUDE scaling, proportionally coupled at sqrt(K). NEITHER /068 nor /065 isolated this design — /124 is a structurally new EXPLORATION. The combined-precedent prior is NEGATIVE-dominant (both legs broke individually) but not certain (the proportional coupling may dissolve one or both individual risks).

### Section 4.4 — Behavioral-effect predictor (per `feedback_v3_axis_saturation_predictor.md`)

The /124 axis changes the LABEL POPULATION Optuna sees during training — labels at K=21 vs K=63 Branch B encode the SAME random-walk barrier-hit semantics but over a 3× LONGER forward window. Expected first-order changes:

- **IS trade roster behavioral change**: 30–60% of /121 IS trades will be DIFFERENT (the label distribution is meaningfully changed even under preserved semantics because new training samples capture longer-horizon directional moves). If common-trade fraction with /121 > 90%, the axis is FULLY INERT at production → file NEGATIVE-no-effect.
- **IS trade count change**: expected ± 20% vs /121's 173. Trade-count gating thresholds at /124: < 100 IS trades → file Mode 8 trade-rate floor breach.
- **Per-symbol shift prediction**: LDO has 0 timeouts at K=21 → INSENSITIVE to K extension at trade-roster level (per /068 T3 + /124 T5). BCH (12.9% IS timeouts) is MOST sensitive — expect largest BCH trade-count change. TRX (6.3% IS timeouts) intermediate.

---

## Section 5 — Risk Mitigation

| Risk | Mitigation | IS-calibrated threshold / simulated effect |
|---|---|---|
| R1: F2 BINDING falsifier TRIGGERED at EDA (+67.74% LDO sample loss) | Branch B preserves per-step barrier-hit probability → per-candle decision quality preserved; absolute sample count reduced but quality per-sample maintained | LDO sample loss = +67.74% (BINDING); brief Section 6 explicit LDO posture; Section 7 + Section 8 F2-conditional outcomes pre-registered |
| R2: /068 K=42 NEGATIVE-catastrophic precedent at retained ATR | Branch B structurally different from /068 (proportional ATR scaling preserves K=21 σ-unit barrier height) | EDA T4 shows Branch A would replicate /068; Branch B's preservation of σ-units mitigates the dominant /068 failure mechanism |
| R3: /065 MAGNITUDE-only at K=21 SUSPICIOUS-OOS-DOMINANT precedent | Branch B couples MAGNITUDE with DURATION; the /065 longer-hold-of-adverse-trades mechanism may dissolve under proportional barrier scaling | Section 7 Mode 6 SUSPICIOUS-OOS-DOMINANT pre-registered with 15% probability; F3 OOS MaxDD doubling binding |
| R4: Sample-uniqueness loss + reduced effective training samples (−67% per AFML) | Optuna at n_trials=35 will sample a smaller effective label space; may overfit | Section 7 Mode 4 catastrophic regime artifact pre-registered with 25% probability (the LARGEST single mode mass); F1 binding |
| R5: LDO ZERO timeouts at K=21 → LDO INSENSITIVE to K extension via trade roster | Per /068 T3 + /124 T5: LDO failure mode is sample-uniqueness (F2), not timeout-redistribution; Branch B provides PARTIAL mitigation (preserves per-step probability) but cannot replenish lost samples | Brief Section 6 LDO-specific posture; expected LDO trade count < /121 (9 IS / 12 OOS) — predict 5–10 IS / 7–15 OOS |
| R6: Look-ahead via ATR or label horizon change | ATR multipliers are configured TRAIN-TIME (no real-time feature change); label horizon change affects label generation only (per AFML; canonical purge); embargo recomputes from `label_timeout_minutes` via `compute_embargo_candles` | walk_forward POST-FIX `e149e9d` intact — `train_end_ms = test_start_ms - embargo_ms` with embargo_ms = compute_embargo_candles(30240, 480) × 480 × 60_000 = 64 × 28_800_000 = 1_843_200_000 ms (about 21.3 days). Test must PASS in CI before merge |
| R7: REQUIRED_GAP runner-local override silently inconsistent with validation_v3.py constant | Engineer pre-flight reads validation_v3.REQUIRED_GAP = 66 (unchanged 8h baseline); runner-local override computes (63+1)*3 = 192 and asserts | `_verify_label_leakage_gap` print line at runner startup; precedent at /068 setup `06a8cc2` |
| R8: `_verify_timeout_consistency` HARDCODE drift | Runner setup MUST update the hardcoded `expected_timeout_minutes = 10080` to `= 30240` in 2 places (lines 1256 and 1384); precedent at /068 impl `0e9eb30` | Engineer pre-flight banner shows `Universal label_timeout_minutes: 30240 min PASS` |
| R9: ATR scaling at LDO disproportionate to BCH/TRX (LDO natr 5.36% vs BCH 4.21% vs TRX 3.27%) | DEFAULT_ATR_MULTIPLIERS applied uniformly; per-symbol natr difference is intrinsic to triple-barrier design (high-vol symbols get wider barriers in absolute %) | No per-symbol override (V3_ATR_MULTIPLIERS_PER_SYMBOL stays {}) — UNIVERSAL scaling is the cycle-7 axis-isolation discipline |

---

## Section 6 — Risk Management Design

The 7-gate RiskV2 stack is UNCHANGED:
1. Vol scaling (vol_scale_floor_per_symbol = {} → no floor)
2. ADX threshold (20.0; no per-symbol override)
3. Hurst regime check
4. z-score OOD gate (threshold = 2.0)
5. Low-vol filter
6. Hit-rate feedback (OOS only)
7. BTC trend alignment filter

The /116 no_confirm RULE-layer primitive is ENABLED at baseline (`enable_no_confirm_exit=True`, `no_confirm_trigger_atr=0.50`, `no_confirm_k_candles=4`) per /121 CONFIRMATION-MERGE — UNCHANGED at /124.

**Hard-merge gate implications for /132 CONFIRMATION** (if /124 lands PROMISING — low probability given /068 + /065 precedents):

| Gate | /124 EDA estimate | /132 CONFIRMATION requirement |
|---|---|---|
| IS Sharpe > 1.0 (Sharpe floor) | EDA models modal IS Sharpe ∈ [+0.76, +1.16] EXPLORATION-mode — UNCERTAIN margin (probably crosses 1.0 floor only at PROMISING-strong tail) | CONFIRMATION must clear at multi-seed mean (BOTH-must-improve gate per `feedback_v3_strict_both_is_oos_baseline.md`) |
| OOS Sharpe > 1.0 (Sharpe floor) | EDA models modal OOS Sharpe ∈ [+0.55, +1.05] EXPLORATION-mode — even more uncertain | CONFIRMATION must clear |
| OOS/IS ratio ≥ 0.5 | /121 has 0.74; /124 unknown | needs multi-seed validation |
| Trade-rate ≥ 10/month OOS | /121 at 7.0/month — outstanding constraint; /124 expected to REDUCE OOS trade count (longer-horizon labels often → tighter Optuna selection) | NEEDS structural axis at later cycle |
| Top-symbol ≤ 30% | /121 at BCH 95.76% — structural property of universe | unchanged |
| 10-seed validation | Single-seed-cohort at /124 EXPLORATION; full 10-seed at /132 | /132 |

The /124 brief does NOT promise merge-eligibility — it promises a single-axis EXPLORATION result that informs the cycle-7 axis-prior catalog. **Given the /068 + /065 precedents and F2 already TRIGGERED at EDA, /124 is most likely NEGATIVE at production** (Section 7 modal probability mass 60% NEGATIVE family; 15% SUSPICIOUS family; 25% PROMISING-or-null family).

**LDO-specific posture (F2 TRIGGERED)**: LDO has 0 timeouts at K=21 (insensitive at trade-roster level) and +67.74% sample loss at K=63 (most-affected in absolute count). Branch B's proportional barrier scaling preserves per-step label quality (mitigation) but cannot replenish lost samples (residual cost). Predicted LDO IS trade count at /124: 5–10 (vs /121's 9); predicted LDO OOS trade count: 7–15 (vs /121's 12). If LDO IS trade count drops below 4 → file Mode 9 LDO-failure (structural).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

Nine modes pre-registered (Mode 1 = success; Modes 2–9 = failure/surprise variants). **First-match-wins**: classify by the FIRST mode whose condition matches the observed outcome.

| Mode | Condition (BEFORE checking the result) | Probability prior | Verdict if matches |
|---|---|---:|---|
| **Mode 1 (Modal success)** | IS Sharpe Δ ∈ [+0.05, +0.30] vs /121 EXPLORATION-mode estimate AND OOS Sharpe Δ ∈ [+0.10, +0.40] AND IS timeout rate ∈ [5%, 20%] AND common-trade fraction with /121 ∈ [30%, 70%] | **10%** | EXPLORATION-PROMISING (Branch B's sqrt(K) scaling reveals incremental medium-term signal; /132 bundle candidate) |
| **Mode 2 (NEGATIVE-catastrophic — /068 replication)** | IS Sharpe Δ < −0.40 vs /121 EXPLORATION estimate OR IS Sharpe Δ < −0.50 vs /121 multi-seed baseline | **25%** | EXPLORATION-NEGATIVE-catastrophic (the /068 K=42 mechanism replicated at K=63 despite Branch B mitigation; labeling-DURATION axis CLOSED bilaterally) |
| **Mode 3 (NEGATIVE-no-effect)** | IS Sharpe Δ ∈ [−0.10, +0.05] AND common-trade fraction with /121 > 90% AND IS timeout rate within [5%, 20%] | 5% | NEGATIVE-no-effect (Optuna re-converges to nearly-same trade set despite changed labels; axis SATURATED) |
| **Mode 4 (SUSPICIOUS-OOS-DOMINANT — /065 replication)** | OOS Sharpe Δ > +0.30 vs /121 EXPLORATION estimate BUT IS Sharpe Δ < +0.05 | **15%** | SUSPICIOUS-OOS-DOMINANT per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`. The /065 MAGNITUDE-only IS-collapse + OOS-soar pattern replicated under the MAGNITUDE-coupling component of Branch B |
| **Mode 5 (NEGATIVE-cascade — /123 replication)** | All 3 symbols IS-negative weighted_pnl (F5 TRIGGERED) | **10%** | NEGATIVE-cascade (universe-wide IS failure; /123-style broadcast cost via universal labeling change) |
| **Mode 6 (Mixed PROMISING-PARTIAL)** | IS Sharpe Δ > +0.10 AND OOS Sharpe Δ < +0.00 AND per-symbol decomposition shows 1 IS-strong-positive symbol AND 2 IS-negative symbols | 5% | PROMISING-PARTIAL — single-symbol carrier; needs SSC-RISK gate at CONFIRMATION |
| **Mode 7 (LDO-failure structural)** | LDO IS trade count < 4 OR LDO IS PnL < −5pp | 5% | EXPLORATION-NEGATIVE-LDO (F2 binding propagates to LDO production collapse; the sample-uniqueness loss dominates per-symbol prediction quality) |
| **Mode 8 (Trade-rate breach)** | Total IS trades < 100 (vs /121's 173) | 5% | NEGATIVE-trade-rate-breach (Optuna's label set shrink + sample-uniqueness reduces trade emission below sustainable threshold) |
| **Mode 9 (Catastrophic OOS regime collapse)** | OOS Sharpe Δ < −0.50 vs /121 multi-seed baseline OR OOS MaxDD > 51.40% (F3 TRIGGERED) | **20%** | NEGATIVE-OOS-regime-collapse (Branch B's longer-hold of adverse trades + larger SL = larger drawdown excursions in adverse regimes) |

**EDA Modal predictions (sum probabilities)**:
- NEGATIVE family (Mode 2 + 3 + 5 + 7 + 8 + 9) = 70%
- SUSPICIOUS family (Mode 4) = 15%
- PROMISING family (Mode 1 + 6) = 15%

The NEGATIVE-family dominant probability (70%) reflects:
1. F2 BINDING TRIGGERED at EDA pre-flight (+67.74% LDO sample loss)
2. /068 K=42 NEGATIVE-catastrophic precedent at retained ATR (Mode 2 at 25%)
3. /065 MAGNITUDE-only SUSPICIOUS at /070 CONFIRMATION (Mode 4 at 15%, NEGATIVE adjacent)
4. /123 universe-cascade mechanism replicated for universal labeling changes (Mode 5 at 10%)

PROMISING family is 15% (Mode 1 + 6) — Branch B's sqrt(K) ATR scaling is a STRUCTURALLY DIFFERENT design that mitigates known failure mechanisms; there is genuine residual probability that K=63 with preserved semantics reveals incremental signal that K=21 truncates.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria — PER-CRITERION ANCHOR ANNOTATED

EXPLORATION-mode criteria (first-match-wins; the post-result classification the QR commits to BEFORE looking at the result). Per /122 Critic Rec 3, each criterion explicitly states which anchor is used.

### NEGATIVE criteria (any-of-the-below)

1. **NEGATIVE-catastrophic**: IS Sharpe Δ < **−0.40** vs **/121 multi-seed baseline (+1.3108)** OR OOS Sharpe Δ < **−0.40** vs **/121 multi-seed baseline (+0.9682)** → file EXPLORATION-NEGATIVE-catastrophic. *Anchor*: /121 multi-seed CONFIRMATION baseline. Axis CLOSE recommendation: the labeling-DURATION extension axis is CLOSED bilaterally (K=42 NEGATIVE at /068; K=63 NEGATIVE at /124). Cycle-7 axis-selection narrows further toward non-labeling/non-cross-asset axes (per Critic Rec 3 menu).

2. **NEGATIVE-no-effect**: IS Sharpe Δ ∈ **[−0.05, +0.05]** vs **/121 EXPLORATION-mode estimate (+1.06)** AND common-trade fraction with /121 > 90% → file EXPLORATION-NEGATIVE-no-effect. *Anchor*: /121 EXPLORATION-mode architecturally-adjusted estimate. Axis CLOSE-PROVISIONAL (the K extension is SATURATED in the current architecture; future iteration may revisit at different ensemble/seeds spec).

3. **NEGATIVE-cascade**: All 3 symbols IS-negative weighted_pnl (F5 TRIGGERED) → file EXPLORATION-NEGATIVE-cascade. *Anchor*: per-symbol weighted_pnl values (sign check, no anchor needed). Axis CLOSE recommendation: universal labeling changes broadcast cost symmetrically (/123-replication); future labeling axes must be per-symbol-bounded.

4. **NEGATIVE-LDO-structural**: LDO IS trade count < 4 OR LDO IS PnL < −5pp → file EXPLORATION-NEGATIVE-LDO. *Anchor*: /121 LDO baseline (9 IS trades). Axis-CLOSE: the K extension is incompatible with LDO's low-trade-count posture; cycle-7 axis-selection must avoid universal label-DURATION changes when LDO is in universe.

5. **NEGATIVE-trade-rate-breach**: Total IS trades < 100 (vs /121's 173; ~42% reduction) → file EXPLORATION-NEGATIVE-trade-rate-breach. *Anchor*: /121 IS trade count (173). Cycle-7 axis-selection narrows toward axes that preserve trade-rate.

6. **NEGATIVE-clean**: IS Sharpe Δ < +0.05 vs /121 EXPLORATION estimate AND OOS Sharpe Δ < +0.05 vs /121 EXPLORATION estimate AND none of Modes 2-5 match → file EXPLORATION-NEGATIVE-clean.

### PROMISING criteria (all-of-the-below for each leg)

7. **PROMISING-strong**: IS Sharpe Δ ≥ **+0.10** vs **/121 EXPLORATION-mode estimate (+1.06)** AND OOS Sharpe Δ ≥ **+0.10** vs **/121 EXPLORATION-mode estimate (+0.85)** AND IS timeout rate ∈ [5%, 20%] (F4 PASS) AND common-trade fraction with /121 ∈ [30%, 70%] AND no Mode 2-5/7 falsifier match → file EXPLORATION-PROMISING strong. *Anchor*: /121 EXPLORATION-mode architecturally-adjusted estimate (the falsifier band reference). Bundle candidate for /132 CONFIRMATION (subject to multi-seed validation).

8. **PROMISING-medium**: IS Sharpe Δ ≥ **+0.05** vs **/121 EXPLORATION-mode estimate (+1.06)** AND OOS Sharpe Δ ≥ **+0.05** vs **/121 EXPLORATION-mode estimate (+0.85)** AND no Mode 2-5/7 falsifier → file EXPLORATION-PROMISING medium. *Anchor*: /121 EXPLORATION-mode estimate. Not bundled at /132 unless paired with separate-axis evidence at later EXPLORATION.

9. **PROMISING-partial**: Single-symbol carrier (1 symbol IS-positive with Δ > +3pp AND another symbol IS-negative Δ < −1pp) → file EXPLORATION-PROMISING-PARTIAL. *Anchor*: per-symbol IS PnL values (absolute, no anchor).

10. **SUSPICIOUS-OOS-DOMINANT**: OOS Sharpe Δ > **+0.20** vs **/121 EXPLORATION-mode estimate (+0.85)** BUT IS Sharpe Δ < **+0.00** vs **/121 EXPLORATION-mode estimate (+1.06)** → file SUSPICIOUS per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`. *Anchor*: /121 EXPLORATION-mode estimate (both legs). Classify per /065 pattern at /070 CONFIRMATION DROP (regime exposure artifact, NOT robust edge).

### Anchor — multi-anchor reporting convention

The /124 backtest reports against THREE anchors:
1. **/121 multi-seed CONFIRMATION baseline (IS +1.3108 / OOS +0.9682)** — the public canonical anchor for BASELINE_V3.md comparison and Section 8 NEGATIVE-catastrophic threshold.
2. **/121 EXPLORATION-mode architecturally-adjusted estimate (IS +1.06 / OOS +0.85)** — the EXPLORATION-mode Δ classification anchor (Section 7 modes, Section 8 PROMISING criteria).
3. **/068 K=42 NEGATIVE-catastrophic outcome (IS −0.35 / OOS −0.48 vs /060)** — the precedent anchor for comparing /124's K=63 result to the prior K=42 attempt (informational).

---

## Section 9 — Library Stack Declaration

**No new library dependencies** — /124's axis is a TRAIN-TIME labeling parameter change (`label_timeout_minutes` 10080 → 30240; `atr_tp_multiplier` 2.0 → 3.4641; `atr_sl_multiplier` 1.0 → 1.7321). All required functions are already imported in `run_baseline_v3.py` and the LightGbmStrategy interface.

**Library inventory** (verified at /121):
- `lightgbm == 4.6.0` (unchanged)
- `numpy >= 2.0` (unchanged)
- `pandas >= 2.2` (unchanged)
- `scikit-learn` (used only in EDA, not in production runner)
- No `statsmodels` / `optuna` / `pyarrow` version change

**Adversarial integration test** (per `feedback_v3_methodology_axis_integration_test.md`): the Section 3.5 tests assert:
- `DEFAULT_ATR_MULTIPLIERS == (3.4641, 1.7321)` at module load
- `BacktestConfig.timeout_minutes == 30240` for BCHUSDT model
- `LightGbmStrategy.label_timeout_minutes == 30240` for BCHUSDT model
- `_verify_timeout_consistency(cfg, lgbm_strategy)` PASSES with both == 30240
- `_verify_label_leakage_gap("8h")` PASSES with computed gap = 192 (runner-local override)
- `compute_embargo_candles(30240, 480) == 64` (per-cell embargo)
- The runner-local REQUIRED_GAP override is materially visible in the per-cell PBO assertion (PER_CELL_GAP = 64; cross-cell gap = 192)

These 7 assertions cover the end-to-end integration boundary (labeling parameter → strategy → CV embargo → walk-forward → trade emission) at the runtime call-site.

---

## Section 10 — QR Audit Trail

**Provenance of the /124 axis selection**:

1. **/123 closeout diary directives** (`diary-v3/iteration_v3-123.md` Section 8 Critic Recommendation 3): "Pivot /124 axis AWAY from cross-asset entirely". Candidate axes listed: (a) Longer-cadence labels axis-3 (1d or 3d horizon-extended triple-barrier) with explicit note that /068's NEGATIVE-catastrophic precedent must inform axis design; (b) Creative out-of-box (per-symbol drawdown brake at closed-loop simulator layer with deadlock-impossibility proof). The user-task spec pre-selected option (a) with K=63 and explicitly mandated Branch A vs Branch B adjudication via EDA T4.

2. **Task-spec design constraints**:
   - K=42 retry FORBIDDEN per /068 precedent
   - K=84 NOT chosen — most-extreme sample-uniqueness loss (T2/T3 confirm: K=84 → −76% AFML sample loss vs K=63's −67%)
   - K=63 chosen as middle ground (3× current 21-bar horizon)
   - REQUIRED_GAP recompute mandatory: 66 → 192
   - `_verify_timeout_consistency` runtime override mandatory at /124 setup

3. **EDA T4 LOAD-BEARING adjudication**: Branch B (sqrt(3) ATR scaling) SELECTED on LABEL SEMANTIC PRESERVATION grounds. Branch A would have shifted label semantics qualitatively (TP/SL hit rates at K=63 would differ from K=21 in distribution character); Branch B preserves the K=21 random-walk barrier-hit probability under proportional scaling. EDA T4 SHA = `e814bb2`.

4. **Falsifier set**: F1 catastrophic IS, F2 LDO sample loss (TRIGGERED at EDA), F3 OOS MaxDD doubling, F4 Branch B label-semantic preservation check, F5 universe cascade, F6 OOS Sharpe collapse. F4 was RECLASSIFIED from task-spec original (EDA T4 refuted the Branch A high-timeout-rate assumption — Branch A would REDUCE timeout rate, not increase it, requiring F4 reclassification as Branch B integrity check).

5. **Prediction-band envelope per /068 closeout mandate**: IS Δ [−0.50, +0.50] / OOS Δ [−0.50, +0.50] (3-5× /122/123 envelopes). Labeling-DURATION axes inherently wider variance.

6. **Anchor annotation per /122 Critic Rec 3**: each Section 7 mode and Section 8 criterion explicitly states which anchor (/121 multi-seed vs /121 EXPLORATION-mode estimate) is used for Δ computation.

**Cycle-7 progress at /124 BRIEF**:

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /122 | cross-asset axis-1 sub-axis A4 (eth_ret_3d) | NEGATIVE-INERT |
| #2 | /123 | cross-asset axis-1 sub-axis B1 (eth_vs_sym_rv_50) | NEGATIVE-catastrophic — cross-asset OHLCV AXIS CLOSED at 6th failure |
| **#3** | **/124** | **Longer-cadence labels axis-3 K=63 with Branch B sqrt(3) ATR scaling** | **TBD (IN PROGRESS)** |
| #4-#10 | /125-/131 | TBD per /124 outcome | TBD |
| CONFIRMATION | /132 | Anchors against /121 multi-seed baseline | TBD |

**Permitted cycle-7 axis-selection menu post-/124** (regardless of /124 outcome):
- If /124 PROMISING: NEXT EXPLORATION = K=84 retry (the most-extreme cadence) OR /124-bundle with a separate per-symbol axis to test cross-axis interaction
- If /124 NEGATIVE-catastrophic: labeling-DURATION axis CLOSED bilaterally; NEXT EXPLORATION must be from /123 Critic Rec 3 menu item (b) "creative out-of-box" — per-symbol drawdown brake at closed-loop simulator OR symbol universe expansion (4th symbol candidate) OR /017-style fixed-horizon labeling REVISIT (label-mode axis is different from label-timeout axis; closed at /017 NEGATIVE PATH C but the fixed-horizon variant has not been tested at /121 anchor)
- If /124 SUSPICIOUS-OOS-DOMINANT: classified per /065 + /070 precedent; the MAGNITUDE-coupling component is the suspect; NEXT EXPLORATION should isolate either DURATION-only at preserved ATR (i.e., /068 retry — but at /121 anchor instead of /060) OR MAGNITUDE-only at K=21 (different value than /065's 1.5; e.g., asymmetric TP+SL with TP unchanged)

**Cannot be retroactively renegotiated post-axis-selection**: the /124 axis is K=63 with Branch B sqrt(3) ATR scaling. The Branch B selection in EDA T4 is BINDING — Phase 6 implements Branch B; if the QE finds an alternative Branch (e.g., Branch C = different scaling exponent), the QR must re-run EDA T4 and rewrite the brief.

PRIME DIRECTIVE: brief + backtest. NO EDA-kill. The brief proceeds despite F2 BINDING falsifier TRIGGERED at EDA pre-flight per task spec mandate — the /124 backtest will produce a numerical verdict against the pre-registered Section 7 modes + Section 8 criteria, anchored against /121 multi-seed BASELINE_V3.md canonical and /121 EXPLORATION-mode architecturally-adjusted estimate.
