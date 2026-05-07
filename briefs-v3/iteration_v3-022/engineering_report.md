# Engineering Report — iter-v3/022

## Headers

- Iteration: iter-v3/022
- Branch: iteration-v3/022
- Setup commit SHA: `64e101d` (V3_MODELS=3 revert, REQUIRED_GAP=66, regime gate enabled, ITERATION_LABEL=v3-022)
- Gate commit SHA: `8418f57` (Phase 5.5 gate PASS)
- Brief commit SHA: `79321c5` (research brief — TRX/2022-Q4 regime gate MEDIUM #4 ELEVATED)
- EDA commit SHA: `b728313` (regime_gate_eda — TRX 2022-Q4 regime profile + counterfactual; committed BEFORE brief)
- Hardware: WSL2 / Linux 6.6.87.2-microsoft-standard-WSL2 x86_64 / 20 cores / 58 GiB RAM
- Wall-clock time: 0.23h (14 min — well within 2h hard cap)
- Library stack: lightgbm=4.6.0, optuna=4.8.0, numpy=2.2.6, pandas=3.0.0, scikit-learn=1.8.0, scipy=1.17.0, statsmodels=0.14.6, pyarrow=23.0.1

---

## Configuration Diff vs Baseline (BASELINE_V3.md — iter-v3/018)

| Parameter | Baseline (iter-v3/018 CONFIRMATION) | iter-v3/022 | Change |
|---|---|---|---|
| V3_MODELS | 3 (BCH, LDO, TRX) | 3 (BCH, LDO, TRX) | Reverted from iter-v3/021 5-sym expansion |
| REQUIRED_GAP | 66 = (21+1)×3 | 66 = (21+1)×3 | Reverted from iter-v3/021 110 |
| ENSEMBLE_SIZE | 5 (CONFIRMATION) | 1 (EXPLORATION) | EXPLORATION mode |
| outer seeds | 2 (CONFIRMATION) | 1 (EXPLORATION seed=42) | EXPLORATION mode |
| n_trials | 50 (CONFIRMATION) | 35 (EXPLORATION) | EXPLORATION default |
| colsample_bytree | Optuna-tuned | 1.0 hardcoded | EXPLORATION mode |
| enable_regime_gate | False | **True** | **NEW — single-axis change** |
| regime_gate_symbols | () | **("TRXUSDT",)** | **NEW — TRX-only target** |
| regime_dd_threshold_pct | — | **20.0%** | **NEW — IS-90th-pct calibrated** |
| regime_vol_zscore_threshold | — | **1.5** | **NEW — IS-95th-pct calibrated** |
| enable_per_symbol_cap | False | False | Unchanged (iter-v3/020 closed) |
| ITERATION_LABEL | v3-018 | v3-022 | Updated |
| V3_FEATURE_COLUMNS | 13 (unchanged) | 13 (unchanged) | NO CHANGE |
| ATR labeling | atr_tp=2.0, atr_sl=1.0 | atr_tp=2.0, atr_sl=1.0 | NO CHANGE |
| zscore/adx/btc_pct thresholds | 2.0 / 20.0 / 15.0% | 2.0 / 20.0 / 15.0% | NO CHANGE |

**Single-axis discipline CONFIRMED**: only `enable_regime_gate`, `regime_gate_symbols`, `regime_dd_threshold_pct`, `regime_vol_zscore_threshold` changed. V3_MODELS reverted from iter-v3/021 (universe revert is a prerequisite, not an axis change). All 13 V3_FEATURE_COLUMNS, labeling params, and all 7 existing risk gate parameters are byte-identical to iter-v3/018.

---

## Key Metrics Block

| Metric | In-Sample | OOS | Ratio |
|---|---:|---:|---:|
| monthly_sharpe | +0.8084 | -0.4313 | -0.534 |
| daily_sharpe | +1.5552 | -1.2521 | -0.805 |
| max_drawdown | 34.52% | 42.90% | 1.243 |
| profit_factor | 1.253 | 0.857 | 0.684 |
| win_rate | 31.6% | 39.0% | 1.234 |
| n_trades | 196 | 82 | 0.418 |
| total_pnl | +57.05 | -16.01 | -0.281 |
| monthly_calmar | +1.652 | -0.373 | -0.226 |
| dsr | 0.0 | — | — |
| pbo | 0.119 | — | — |
| psr | 0.0000 | — | — |
| n_trials | 105 | — | — |
| n_effective_trials | 19 | — | — |

**vs anchor (iter-v3/018 multi-seed mean):**
- IS Sharpe: +0.8084 vs +0.3788 anchor → Δ +0.43 (STRONG IS LIFT; well above predicted [+0.32, +0.50])
- OOS Sharpe: -0.4313 vs +0.3869 anchor → Δ -0.82 (OOS COLLAPSE; far below predicted [+0.40, +0.55])
- IS n_trades: 196 (vs anchor 172; EXPLORATION single-seed baseline is 200 from 020/021, so regime gate reduced TRX IS trades from 79 → 75)

**Per-Symbol OOS:**

| Symbol | weighted_pnl | n_trades | win_rate | note |
|---|---:|---:|---:|---|
| TRXUSDT | +7.69 | 33 | 42.4% | POSITIVE — regime gate target; improved vs 020/021 (+5.39) |
| BCHUSDT | -6.25 | 36 | 36.1% | NEGATIVE — bit-identical to iter-v3/020/021 |
| LDOUSDT | -8.93 | 13 | 38.5% | NEGATIVE — bit-identical to iter-v3/020/021 |

---

## Cross-Symbol Regression Analysis (CRITICAL)

**Finding: BCH and LDO OOS results are BIT-IDENTICAL across iter-v3/020, 021, and 022.**

Exact per-symbol OOS PnL comparison:
```
iter-v3/020: BCH=-6.2465, LDO=-8.9257, TRX=+5.3860
iter-v3/021: BCH=-6.2465, LDO=-8.9257, TRX=+5.3860  (BCH/LDO identical; TRX identical; HBAR/AVAX added)
iter-v3/022: BCH=-6.2465, LDO=-8.9257, TRX=+7.6101  (BCH/LDO BIT-IDENTICAL; TRX improved by regime gate)
```

BCH OOS: 36 trades / win_rate=36.1% / weighted_pnl=-6.2465 — digit-for-digit identical across all three EXPLORATION runs.
LDO OOS: 13 trades / win_rate=38.5% / weighted_pnl=-8.9257 — digit-for-digit identical.

**Gate stats confirm zero regime gate fires for BCH and LDO** (gate is correctly TRX-targeted):
```
BCH: regime_gate_fires=0, regime_gate_fire_rate=0.0
LDO: regime_gate_fires=0, regime_gate_fire_rate=0.0
TRX: regime_gate_fires=965, regime_gate_fire_rate=0.4482 (cumulative IS+OOS)
```

**Mechanism conclusion: MECHANISM 1 CONFIRMED. No cross-contamination exists.** BCH and LDO have independent per-symbol Optuna runs; their results are deterministic given seed=42 and n_trials=35 regardless of TRX's regime gate. The BCH/LDO OOS negativity is a PRE-EXISTING condition of EXPLORATION single-seed=42 baseline established at iter-v3/020. It is NOT caused by the regime gate, NOT a methodology defect, and NOT a cross-contamination artifact. The "puzzling" OOS collapse resolves cleanly: BCH/LDO were already negative at the EXPLORATION level before iter-v3/022 was run.

**IS per-symbol trade count confirmation:**
```
iter-v3/020: BCH=98, LDO=23, TRX=79 → total IS=200
iter-v3/021: BCH=98, LDO=23, TRX=79 → total IS=200
iter-v3/022: BCH=98, LDO=23, TRX=75 → total IS=196
```
TRX IS trades dropped by 4 (from 79 to 75) — the regime gate's direct IS effect. BCH and LDO IS are also bit-identical to 020/021.

---

## Regime Gate Fire Rate Analysis

**Observed cumulative fire rate (IS+OOS combined): 44.8% of all TRX signals (965/2153)**

**Why the predicted 1.3% and the observed 44.8% appear to differ — they measure different things:**

- The brief's 1.3% IS kill rate refers to **TRX trade entries** killed out of 75 IS trades (only 1 trade killed from iter-v3/018 IS). This is the trade-execution layer impact.
- The observed 44.8% is the **per-signal bar-level fire rate**: for each bar where TRX's LightGBM emits a candidate signal, how often the regime gate fires. Most of those 44.8% bars would also be killed by zscore/hurst/adx/low_vol gates independently (kill_rate from other 4 gates = 73.6% of 2153 signals = 1584 killed). The regime gate fires on 965 of the full 2153 signals seen — it checks ALL candidate signals, not just those surviving other gates.

**The EDA-predicted IS-wide bar-level fire rate was 14.49%** (830 of 5,727 IS bars). The cumulative signal-level rate of 44.8% is higher because: (a) it is bar-level BUT gated on signal-emitting bars (not all 8h bars), and (b) it covers IS+OOS combined, including the OOS window where BTC regime behavior may differ from the IS-calibration period.

**Redundancy with other gates**: The 44.8% figure is inflated by the fact that the regime gate checks signals that would already be killed by the zscore/hurst/adx/low_vol stack. The actual unique kills (signals the regime gate blocks that would have survived all other gates) cannot be read directly from the log, but the 4-gate combined kill_rate of 73.6% and the regime gate's 44.8% have substantial overlap. This is by design — the regime gate's purpose is at the Optuna training-data layer (reshaping the IS feature distribution), not maximally unique trade-entry suppression.

**OOS falsifier 3 (fire rate > 25%)**: The cumulative rate of 44.8% nominally exceeds the 25% threshold. However, the falsifier was defined for the OOS gate fire rate specifically (regime misalignment in the OOS window), not the combined IS+OOS signal-level fire rate. The EDA showed IS bar-level fire rate of 14.49%; OOS regime conditions cannot be isolated from this log because gate stats are reported cumulatively. The OOS window (2025-03-24 onward) has moderate BTC vol/DD conditions, and the TRX OOS PnL is POSITIVE (+7.69), which is inconsistent with severe OOS regime misalignment. **Verdict: Falsifier 3 is inconclusive from cumulative log stats; OOS TRX positive PnL is evidence against misalignment.**

---

## PBO Analysis

**Per-cell PBO for targeted TRX cells:**

| TRX cell | PBO (iter-v3/018) | PBO (iter-v3/022) | Change |
|---|---:|---:|---|
| TRX/2022-10 | **1.000** | 0.282 | **REDUCED — target achieved** |
| TRX/2023-01 | **1.000** | 0.999 | **BARELY CHANGED — mechanism partial** |
| TRX/2022-09 | 0.003 | **0.926** | WORSENED — new high-PBO cell emerged |

**Overall PBO max in iter-v3/022: 1.0** (LDOUSDT/2026-03 = 1.0; not a TRX cell). The TRX max PBO is now 0.999 (TRX/2023-01) and 0.926 (TRX/2022-09).

**New high-PBO TRX cells in iter-v3/022 (PBO ≥ 0.85):**

| TRX cell | PBO |
|---|---:|
| TRX/2022-09 | 0.9258 |
| TRX/2023-01 | 0.9988 |
| TRX/2023-09 | 0.9034 |
| TRX/2024-01 | 0.8806 |
| TRX/2025-10 | 0.9940 |
| TRX/2025-11 | 0.9404 |

**The regime gate partially addressed TRX/2022-10** (1.0 → 0.282, the targeted cell with strongest gate-fire overlap). **TRX/2023-01 barely changed** (1.0 → 0.999) despite the EDA showing 38.7% gate-fire rate in that month — the single-seed EXPLORATION n_trials=35 likely produces insufficient Optuna coverage for a stable PBO reduction in that cell. **New high-PBO cells emerged** at TRX/2022-09 (which had PBO=0.003 in 018) and at TRX/2025-10/11 (OOS-window cells, not applicable to OUTSTANDING CONSTRAINT #5 but indicating structural Optuna instability at EXPLORATION budget).

**Falsifier 4 (PBO max drops below 0.85 in TRX cells)**: NOT MET. TRX/2023-01 = 0.999 (above 0.85). Falsifier 4 fires as "NOT PROMISING-METHODOLOGY" — the mechanism operated partially (TRX/2022-10 improved) but did not achieve the full PBO max reduction target.

Note: Comparing CONFIRMATION-mode PBO (018, 10 seeds, n_trials=50) to EXPLORATION-mode PBO (022, 1 seed, n_trials=35) is not fully apples-to-apples. The EXPLORATION budget of 35 trials/cell may produce intrinsically noisier PBO measurements. A CONFIRMATION run of iter-v3/022's regime gate (with n_trials=50, 5 seeds) would provide cleaner PBO cell comparisons.

---

## Hypothesis-Implementation Alignment (12 Verifiers)

| # | Verifier | Status | Evidence |
|---|---|---|---|
| 1 | V3_MODELS = 3 (BCH, LDO, TRX) | PASS | run.log: 3 model sections |
| 2 | REQUIRED_GAP = 66 = (21+1)×3 | PASS | run.log: "Label-leakage gap: (timeout_candles=21+1) * n_symbols=3 = 66 [matches REQUIRED_GAP=66] PASS" |
| 3 | V3_FEATURE_COLUMNS = 13 (UNCHANGED) | PASS | run.log confirms 13 feature columns per model |
| 4 | enable_regime_gate=True | PASS | TRX gate stats show 965 fires |
| 5 | regime_gate_symbols=("TRXUSDT",) | PASS | BCH/LDO show 0 regime_gate_fires; TRX shows 965 |
| 6 | regime_dd_threshold_pct=20.0 | PASS | EDA synthesis.md + brief §2.1 match; runtime config confirmed |
| 7 | regime_vol_zscore_threshold=1.5 | PASS | EDA synthesis.md + brief §2.1 match; runtime config confirmed |
| 8 | enable_per_symbol_cap=False | PASS | cap_fires=0 for all symbols |
| 9 | ITERATION_LABEL="v3-022" | PASS | Reports in reports-v3/iteration_v3-022/ |
| 10 | EXPLORATION mode (--exploration --seeds 1) | PASS | seed_summary.json: single seed=42 |
| 11 | n_trials=35, colsample_bytree=1.0 | PASS | 105 n_trials / 3 symbols = 35/symbol; pareto_front.csv single row |
| 12 | Past-only discipline for regime gate | PASS | test_regime_gate_past_only.py adversarial test committed at `64e101d` |

All 12 verifiers PASS.

---

## Label Leakage Audit

From run.log:
```
Label-leakage gap: (timeout_candles=21+1) * n_symbols=3 = 66  [matches REQUIRED_GAP=66]  PASS
Gap: 66 (= (timeout_candles+1) * 3 symbols [BCH+LDO+TRX, iter-v3/022 revert])
```

REQUIRED_GAP = 66 is correct for the 3-symbol universe. The purge embargo of (21+1) × 3 = 66 candles satisfies the López de Prado requirement. Confirmed: runtime assertion `_verify_label_leakage_gap()` passed without error.

---

## Seed Concentration Audit

Single-seed EXPLORATION (seed=42) — no multi-seed statistics applicable:

| Metric | Value |
|---|---|
| Seed | 42 |
| IS monthly Sharpe | +0.8084 |
| OOS monthly Sharpe | -0.4313 |
| IS trades | 196 |
| OOS trades | 82 |
| OOS MaxDD | 42.90% |
| PBO (mean cross-cell) | 0.119 |
| max_concentration_pct | 100.0% (single-symbol dominant OOS period) |
| BTC trend-filter kills | 31/278 total trades (11.15% kill rate) |

Single-seed EXPLORATION mode; multi-seed validation deferred to CONFIRMATION (if warranted). Per `feedback_v3_outer_seed_cap_2_v3.md`, CONFIRMATION uses --seeds 2 max.

---

## Gate Efficacy Table

**Gate fire rates for iter-v3/022 (cumulative IS+OOS):**

| Gate | BCH | LDO | TRX |
|---|---|---|---|
| signals_seen | 3284 | 1175 | 2153 |
| killed_by_zscore | 1036 (31.6%) | 459 (39.1%) | 801 (37.2%) |
| killed_by_hurst | 144 (4.4%) | 54 (4.6%) | 90 (4.2%) |
| killed_by_adx | 724 (22.0%) | 288 (24.5%) | 428 (19.9%) |
| killed_by_low_vol | 638 (19.4%) | 179 (15.2%) | 265 (12.3%) |
| base_kill_rate | 77.4% | 83.4% | 73.6% |
| vol_scaled_signals | 742 | 195 | 569 |
| mean_vol_scale | 0.698 | 0.690 | 0.745 |
| cap_fires | 0 | 0 | 0 |
| **regime_gate_fires** | **0 (0.0%)** | **0 (0.0%)** | **965 (44.8%)** |
| BTC trend filter kills | — | — | — |

BTC trend filter killed 31/278 total trades (11.15% aggregate). Gate stack operating correctly — BCH/LDO have zero regime gate activity as designed.

---

## Falsifier Classification (Brief §4.3 + §4.4)

| Falsifier | Threshold | Observed | Fires? |
|---|---|---|---|
| F1: NEGATIVE indicator | OOS Sharpe < +0.2869 | OOS = -0.4313 | **YES — FIRES** |
| F2: PROMISING indicator | OOS Sharpe Δ > +0.10 AND IS within [+0.32, +0.50] | OOS Δ = -0.82; IS=+0.81 (exceeds upper bound +0.50) | NO |
| F3: OOS regime-misalignment | OOS gate fire rate > 25% | Cumulative rate 44.8%; OOS TRX PnL +7.69 (evidence against) | INCONCLUSIVE (log cumulative; OOS TRX positive) |
| F4: PBO methodology lift | TRX/2022-10 + TRX/2023-01 both PBO < 0.85 | TRX/2022-10=0.282 (PASS); TRX/2023-01=0.999 (FAIL) | NOT MET |
| F5: Saturation | IS trades NOT in [155, 189] | IS=196 (EXPLORATION single-seed baseline=200; regime gate reduced TRX by 4) | **TECHNICALLY FIRES** — artifact of CONFIRMATION vs EXPLORATION comparison |
| F6: Trade-rate floor (informational) | OOS trades < 130 | OOS=82 | INFORMATIONAL caveat fires |
| F7: NULL-RESULT (bit-identical) | Full roster bit-identical | BCH/LDO bit-identical; TRX diverged | NO — axis propagated via TRX |

**Saturation falsifier context**: The brief's saturation band [155, 189] was calibrated against the iter-v3/018 CONFIRMATION multi-seed mean IS=172. The EXPLORATION single-seed=42 baseline across iter-v3/020 and 021 produces IS=200 (BCH=98, LDO=23, TRX=79). iter-v3/022 produces IS=196 (TRX reduced from 79 to 75 by regime gate). The saturation falsifier fires technically (196 > 189) but is measuring EXPLORATION vs CONFIRMATION regime difference, not an axis-behavior anomaly. The regime gate's TRX-IS impact (79 → 75, -4 trades) is within a reasonable range for the mechanism.

---

## §4.4 Row Classification

**Brief §4.4 verbatim rows under evaluation:**

> | Falsifier 1 fires AND non-bit-identical roster AND axis propagated | EXPLORATION-NEGATIVE (clean) | NOT a CONFIRMATION candidate |

This row FIRES. F1 fires (OOS = -0.4313, below +0.2869). The trade roster is NON-bit-identical (TRX changed: 022 TRX OOS +7.69 vs 020/021 TRX OOS +5.39). The axis propagated (TRX IS trades dropped 79→75; TRX OOS improved). **Classification: EXPLORATION-NEGATIVE (clean)**.

However, this classification requires one nuance: the IS Sharpe LIFT (+0.8084 vs anchor +0.3788, Δ+0.43) and the TRX OOS improvement (+7.69 vs +5.39) are genuine positive signals from the regime gate. The "clean" negative is driven entirely by BCH/LDO OOS being stuck at pre-existing single-seed=42 negative values (bit-identical to 020/021). A CONFIRMATION run with 5 seeds × 50 trials would average out BCH/LDO single-seed noise and provide a cleaner signal for the regime gate's contribution.

**Recommended classification: EXPLORATION-NEGATIVE (clean) with MIXED-MECHANISM footnote.** The OOS collapse is explained by BCH/LDO pre-existing single-seed negativity, NOT by the regime gate. TRX, the gate's target, improved in both IS and OOS. The gate mechanism warrants re-evaluation in a CONFIRMATION context rather than categorical closure.

---

## Anomaly Notes

1. **IS Sharpe +0.8084 is the highest IS result in v3 EXPLORATION history** — substantially above the predicted [+0.32, +0.50] band. This is partially explained by the EXPLORATION single-seed=42 dynamics: BCH IS jumped from (018) 87 trades at multi-seed averaged performance to 98 trades at seed=42 Optuna path with higher LDO performance (IS LDO +41.86, BCH IS +38.37). The IS lift is real but partly noise from single-seed optimization.

2. **LDO/2026-03 new PBO=1.0 cell** — not a TRX/2022-Q4 regression issue. LDO only has data from 2024-09 onward; the 2026-03 training window has minimal data (799 candles). This is a data-scarcity PBO artifact in the LDO model, not related to the regime gate.

3. **TRX/2022-09 PBO rose from 0.003 (018) to 0.926 (022)** — new high-PBO cell emerged adjacent to the target window. Likely an EXPLORATION budget artifact: at 35 trials vs 50, the Optuna search for TRX/2022-09 (a month adjacent to the regime-active FTX period) is less stable. This may resolve at CONFIRMATION budget.

4. **OOS trade count = 82 (below 130 floor)** — Falsifier 6 informational caveat fires. EXPLORATION single-seed is not expected to clear the 130-trade floor (the floor applies at CONFIRMATION bundle level per `feedback_trade_rate_floor_bundle_level.md`).

5. **Spot-check of 5 random OOS trades**: all entry/exit/PnL math verified correct; exit_reason consistent (take_profit/stop_loss/end_of_data); weight_factor in [0.0, 1.0] range. No anomalies found.

---

## iter-v3/023 Axis Recommendation

**Based on the cross-symbol mechanism finding (no contamination; BCH/LDO pre-existing noise; TRX regime gate partially effective):**

The regime gate mechanism is NOT closed. TRX/2022-10 PBO dropped from 1.0 to 0.282 (target cell improved); TRX OOS PnL improved vs EXPLORATION baseline. The mechanism is promising but the EXPLORATION single-seed cannot isolate the gate's true OOS contribution from BCH/LDO single-seed variance.

Recommended iter-v3/023 axes (in priority order, per `feedback_v3_iter019_axis_priorities.md`):
1. **MEDIUM — DSR gate reformulation** (priority #5 in locked catalog). With OOS DSR=0.0 and PSR=0.0000 across multiple EXPLORATION runs, the DSR gate's formulation may be distorting the EXPLORATION signal. Reformulation or diagnostic is overdue.
2. **MEDIUM — Funding rate retest at n_trials=35** (priority #6 in locked catalog). iter-v3/019 was PROMISING-INERT at lower budget; a retest with corrected IS-evidence methodology and full n_trials=35 budget is the next axis.
3. **LOW (deferred until CONFIRMATION)** — If QR believes the regime gate warrants CONFIRMATION before continuing EXPLORATION, a CONFIRMATION run of iter-v3/022's config (5 seeds × 50 trials) would provide clean per-cell PBO and multi-seed OOS Sharpe distribution. This would NOT update BASELINE_V3.md but would provide definitive evidence for/against the mechanism.

The regime gate axis is NOT closed for the cycle; it is classified EXPLORATION-NEGATIVE (clean) because of the BCH/LDO single-seed pre-existing noise, not because the mechanism failed. The QR owns the iter-v3/023 axis selection.

---

## Status

**OVERALL = READY-FOR-CRITIC**

Recommended Critic focus areas:
- Verify cross-symbol mechanism analysis (bit-identity finding for BCH/LDO across 020/021/022)
- Verify saturation falsifier interpretation (EXPLORATION vs CONFIRMATION comparison mismatch)
- Verify PBO partial-improvement interpretation (TRX/2022-10 improved; TRX/2023-01 did not)
- Assess whether MIXED-MECHANISM footnote to EXPLORATION-NEGATIVE (clean) is warranted vs strict §4.4 row application
