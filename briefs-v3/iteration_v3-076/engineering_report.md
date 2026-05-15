# Engineering Report — iter-v3/076

## Headers

- Iteration: iter-v3/076
- Branch: iteration-v3/047 (cycle-2 shared branch)
- Commit chain (EDA → brief → backfill → setup → test-fix → Phase 5.5 gate):
  - EDA: `40b6e66` — `analysis/iteration_v3-076/axis_selection_eda.py`
  - Brief: `ed7b27b` — `briefs-v3/iteration_v3-076/research_brief.md`
  - Brief backfill: `45f4832` — Section 10.4 SHA backfill
  - Setup: `79a62b0` — `range_efficiency_50` feature + Primitive 12 revert
  - Pre-existing test fix: `9285505` — `TestPBOFromCPCV` NamedTuple API (unrelated to axis)
  - Phase 5.5 gate: `2ef683f` — PASS
  - HEAD at report time: `2ef683f`
- Hardware: WSL2 / Linux 6.6.114.1-microsoft-standard-WSL2
- Wall-clock time: 0.70h (within 1.0h budget; `--skip-features` because parquets were pre-regenerated at setup commit `79a62b0`)
- Run mode: `--exploration` (3-seed outer=42 lineage, `ENSEMBLE_SIZE=3`, `--n-trials 35`)
- Seeds: `[191664963, 1662057957, 1405681631]` (outer=42 lineage subset)
- Total Optuna trials: 315 (3 seeds × 3 symbols × 35 trials)

---

## Configuration Diff vs /060 EXPLORATION-MODE ANCHOR

Two changes vs /060 — one axis change (new feature `range_efficiency_50`) and one mandatory revert (Primitive 12 OFF):

| Parameter | /060 (anchor) | /076 |
|---|---|---|
| `V3_FEATURE_COLUMNS_TOP_N` | 14 features | **15 features** (`range_efficiency_50` added as 15th) |
| `enable_regime_size_scalar` | `False` | **`False`** (REVERTED from /075's `True`) |
| `regime_size_scalar_symbols` | `()` | **`()`** (baseline restored) |
| `V3_ATR_MULTIPLIERS_PER_SYMBOL` | `{}` | `{}` (unchanged) |
| `ITERATION_LABEL` | `"v3-060"` | `"v3-076"` |
| All other params | — | UNCHANGED |

Sacred constants confirmed: `OOS_CUTOFF_DATE = "2025-03-24"`, `TRAINING_MONTHS = 24`.

Pre-flight feature-column assertions (from run.log): 15-feature universal fallback PASS; `range_efficiency_50` PRESENT PASS; `efficiency_ratio_50` ABSENT PASS; `enable_regime_size_scalar=False` PASS (Primitive 12 REVERTED).

---

## Key Metrics Block

### Headline vs /060 anchor

| Metric | /060 IS | /076 IS | IS Δ | /060 OOS | /076 OOS | OOS Δ | /076 OOS/IS ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | +0.8325 | **+0.0431** | **-0.7894** | +0.1403 | **+0.6489** | **+0.5086** | **15.0422** |
| daily_sharpe | +1.7115 | +0.0984 | -1.6131 | +0.3659 | +1.2685 | +0.9026 | 12.8948 |
| max_drawdown | 31.87% | 61.69% | +29.82pp | 35.78% | 29.42% | -6.36pp | 0.4769 |
| profit_factor | 1.2806 | 1.0151 | -0.265 | 1.0482 | 1.1853 | +0.137 | 1.1677 |
| win_rate | 31.4% | 27.2% | -4.2pp | 39.2% | 39.2% | 0.0pp | 1.4408 |
| n_trades | 159 | 169 | +10 | 102 | 102 | 0 | 0.6036 |
| total_pnl | 51.89 | 3.00 | -48.89 | 5.50 | 22.36 | +16.86 | 7.4485 |
| monthly_calmar | 1.6282 | 0.0487 | -1.580 | 0.1537 | 0.7599 | +0.606 | 15.6179 |
| dsr | 0.0 | 0.0 | — | — | — | — | — |
| pbo | 0.1278 | 0.0974 | -0.030 | — | — | — | — |
| psr | — | 1.0000 | — | — | — | — | — |
| dsr_relative_b4 | n/a | 1.0000 | — | — | — | — | — |
| frac_positive_paths | 0.6444 | 0.6444 | 0.0 | — | — | — | — |
| n_trials | 315 | 315 | 0 | — | — | — | — |
| n_effective_trials | 19 | 18 | -1 | — | — | — | — |

### Per-symbol OOS section

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | +17.9866 | 43 | 37.2% | 80.46% |
| LDOUSDT | -12.5056 | 14 | 28.6% | -55.94% |
| TRXUSDT | +16.8742 | 45 | 44.4% | 75.48% |

Note: concentration_pct percentages are computed against the total OOS weighted_pnl (+22.36); LDO's negative concentration is a bookkeeping artifact. The 30% per-symbol cap is a CONFIRMATION gate not applied at EXPLORATION.

### Per-symbol IS section

| Symbol | trades | win_rate | net_pnl_pct | /060 net_pnl_pct | Δ |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 73 | 37.0% | -8.27% | +79.45% | **-87.72** |
| LDOUSDT | 14 | 35.7% | +16.78% | -11.44% | +28.22 |
| TRXUSDT | 82 | 24.4% | -41.20% | -23.04% | -18.16 |

**Critical IS finding.** The IS collapse is driven overwhelmingly by BCH: same trade count (73) but WR dropped from 45.2% to 37.0% (12 fewer wins), with pnl collapsing from +79.45% to -8.27% — a swing of -87.72%. The feature did not reduce the count of BCH IS trades; it changed WHICH BCH IS trades are in the roster (100 IS trades added / 90 removed, with BCH contributing 37 adds and 37 removes). The replaced BCH trades are worse: the IS bull-period split structure the /060 model learned for BCH was disrupted by adding a 15th feature whose within-IS-bear/chop AUC (0.697 for BCH) is measured on a different trade sub-population than the bull-period trades that carry the IS edge.

---

## Classification per Brief Section 8 LOCKED

Evaluation order per brief: SUSPICIOUS (8.4) → NULL-RESULT (8.5) → NEGATIVE (8.2) → PROMISING (8.1) → INERT (8.3). First match is canonical.

| Gate | Threshold | /076 result | Status |
|---|---|---|---|
| **SUSPICIOUS — OOS/IS ratio > 3.0** | > 3.0 | **15.0422** | **FIRES** |
| **SUSPICIOUS-OOS-DOMINANT — IS shift < 0 AND OOS shift ≥ +0.20** | IS<0 AND OOS≥+0.20 | IS -0.7894 (negative) AND OOS +0.5086 (≥+0.20) | **FIRES** |
| **SUSPICIOUS — holding-time violation > +1.0 candle** | > +1.0 | IS full-roster mean Δ = +0.0051, OOS full-roster mean Δ = +0.4804 | **PASS (does NOT fire)** |
| NULL-RESULT | IS roster bit-identical to /060 | IS: 100 adds, 90 removes — NOT identical | PASS (does not fire) |
| NEGATIVE-IS | IS Δ < -0.10 | -0.7894 (fires) | (subsumed by SUSPICIOUS precedence) |
| NEGATIVE-OOS | OOS Δ < -0.20 | +0.5086 (clear) | PASS |
| PROMISING | IS ≥+0.10 AND OOS ≥+0.20 AND frac_pos ≥0.50 | IS Δ -0.7894 < +0.10 | FAILS |
| INERT | noise band | (subsumed by SUSPICIOUS) | — |

**CLASSIFICATION: SUSPICIOUS-OOS-DOMINANT.**

The SUSPICIOUS gate fires on BOTH grounds simultaneously: (1) the OOS/IS monthly Sharpe ratio 15.04 exceeds the pre-registered 3.0 ceiling unconditionally; (2) the SUSPICIOUS-OOS-DOMINANT sub-mode fires — IS shift -0.79 < 0 AND OOS shift +0.51 ≥ +0.20. Per the Section 8 disjunctive order, SUSPICIOUS takes precedence over NEGATIVE and INERT with no magnitude qualifier. The holding-time gate (> +1.0 candle full-roster mean shift) does NOT fire: IS Δ = +0.005 candles, OOS Δ = +0.480 candles — both below the +1.0 threshold.

---

## Hypothesis Falsification

**The hypothesis is falsified.** The brief's Section 1 thesis was that `range_efficiency_50` — being sign-invariant with |regime-sign corr| = 0.010 (EDA T3) — is "structurally unable to produce the /071/073 SUSPICIOUS signature." Section 7 assigned SUSPICIOUS a ≈3% probability. The observed result is the SUSPICIOUS-OOS-DOMINANT signature with an OOS/IS ratio of 15.04 — the clearest instance of this pattern in cycle 2 (higher ratio than /071 and /073).

**Why the T3 "regime-orthogonal" argument failed.** The EDA T3 test measured the Pearson correlation of the MARGINAL feature distribution against the IS/OOS calendar label. This marginal correlation was 0.010 — genuine and correctly computed. However the SUSPICIOUS signature arises from the CONDITIONAL use of the feature by LightGBM — how the model integrates `range_efficiency_50` in interaction with the other 14 features to select trades. Even when a feature's marginal distribution is regime-orthogonal, the model's learned conditional use can still produce regime-correlated trade selection. The "structurally unable" claim was invalid because it conflated marginal feature orthogonality with conditional model orthogonality. These are distinct properties; the T3 test measures only the former.

---

## Holding-Time Forensic Analysis (Key Finding)

Brief Section 4.3 predicted "~0 duration change" on the grounds that "a feature has no duration-extension mechanism." This reasoning is materially flawed: a feature cannot widen a barrier mechanically, but it CAN change which trades the model selects — and if it preferentially selects longer-duration trades, the full-roster mean duration rises by roster-composition shift, not by per-trade duration extension.

### Roster-diff magnitudes

| Split | Added | Removed | Common | Net |
|---|---:|---:|---:|---:|
| IS | 100 | 90 | 69 | +10 |
| OOS | 40 | 40 | 62 | 0 |

The IS roster is NOT near-identical to /060 — 100 of 169 IS trades are new and 90 of 159 /060 IS trades are absent. The roster-composition shift is massive and confirms the feature was substantially learned (INERT falsifier does not fire).

### Duration statistics

| Split | /060 mean (candles) | /076 mean (candles) | Delta | Falsifier (>+1.0) |
|---|---:|---:|---:|---:|
| IS full-roster | 6.3145 | 6.3195 | **+0.005** | NOT FIRED |
| OOS full-roster | 6.4608 | 6.9412 | **+0.480** | NOT FIRED |
| OOS common-subset | 6.7419 | 6.7419 | **0.000** | n/a |

**The forensic finding.** The full-roster OOS mean duration shifted +0.480 candles, but the common-trade-subset duration is exactly 0.000 — the per-trade duration did not change at all (barriers are unchanged). The +0.480 candle shift is entirely attributable to ROSTER COMPOSITION: the 40 added OOS trades have mean duration 7.25 candles, versus the 40 removed OOS trades at 6.03 candles — the new model selected longer-duration OOS trades and dropped shorter-duration ones. This is a holding-time preference implicit in the feature's learned use, not a mechanical barrier extension.

**Mechanism interpretation.** `range_efficiency_50` measures the ratio of net directional displacement to total path length. In OOS (sustained uptrend), sustained directional moves score HIGH on efficiency — these are precisely the longer-duration timeout/sustained-TP trades. The model learned to prefer high-efficiency moments, which in OOS correlate with longer-duration uptrend continuation. This is the weak holding-time-proxy mechanism that generates the OOS/IS imbalance despite T3's |regime-sign corr| = 0.010: the CONDITIONAL interaction of efficiency × other directional features is regime-correlated even when the MARGINAL efficiency distribution is not.

The brief's Section 4.3 reasoning — "a feature has no duration-extension mechanism, so ~0 duration change" — was flawed because it considered only per-trade barrier effects, not roster-composition-driven mean shifts. This failure mode is NOT pre-registered in the brief Section 7; the brief explicitly weighted SUSPICIOUS at ≈3% precisely because it expected the holding-time argument to protect against the signature. The argument was directionally wrong.

---

## /043 Re-Evaluation Outcome

`range_efficiency_50` is mathematically identical to the dead-code `efficiency_ratio_50` (the same Kaufman path-efficiency formula: `|close[t]-close[t-50]| / sum(|close.diff()|, 50)`). The /043 DISASTROUS run showed IS Sharpe -0.84 and OOS Sharpe -0.90. The /076 re-evaluation was motivated by `feedback_v3_walkforward_lookahead_bug.md` (all v3 prior-to-fix runs biased) and by the hypothesis that `range_efficiency_50` in a DIFFERENT ROLE (a 15th regime-quality conditioning feature alongside 14 directional features, not a standalone signal) would behave differently.

**The re-evaluation did not vindicate the feature.** The IS Sharpe of +0.0431 (MaxDD 61.69%) is near-zero — the IS is still economically broken, just not as catastrophically negative as /043's -0.84. The feature produced the SUSPICIOUS-OOS-DOMINANT pattern (IS collapse + OOS soar), which is a different failure mode from /043's bilateral damage, but remains a failure. The IS collapse (-0.79 Δ) establishes that the feature cannot be used in the current v3 architecture without destroying the IS edge. The re-evaluation is closed; the feature is not vindicated.

---

## ADF and IC Matrix Notes

**ADF warning — `LDOUSDT/cusum_reset_count_200`:** `run.log` line 49284: `[ADF] WARNING: LDOUSDT/cusum_reset_count_200 not found in ADF output`. Identical benign artifact from /074 and /075 — LDO's shorter history (first valid bar 2022-09-22) means the 200-bar rolling `cusum_reset_count_200` feature is all-NaN in LDO's earliest walk-forward training windows, causing the ADF runner to omit that (symbol, feature) cell. Total ADF rows: 2355 (vs expected range [1395, 2835] for 3 syms × 15 feats × [31, 63] months). The missing cell does not affect the backtest result. Flag for Critic Check 5 as a persistent informational artifact.

**Additional ADF note — `TRXUSDT/range_efficiency_50/2020-02`:** `run.log` line 43: `[ADF] Error TRXUSDT/range_efficiency_50/2020-02: Invalid input, x is constant`. The TRX `range_efficiency_50` feature in the 2020-02 warm-up window is constant (all warm-up bars filled with 0.0 per the feature's `.fillna(0.0)` contract). ADF rejects a constant series as untestable. Benign — the warm-up fill is by design, and the walk-forward training splits skip the warm-up period. No impact on backtest results.

**IC matrix — 15×15 confirmed.** `ic_matrix.csv` is a 15×15 square matrix; `range_efficiency_50` is present in both the header and the row index. Max |IC| of `range_efficiency_50` vs the 14 baseline features: **0.216** (with `sym_vs_btc_ret_7d`). This exceeds the EDA T7 estimate of 0.206 but remains comfortably below the 0.70 gate and confirms the feature is genuinely orthogonal to the existing stack.

---

## Feature Importance

`range_efficiency_50` rank in the last walk-forward month's importance output:

| Symbol | rank | /15 | importance |
|---|---:|---:|---:|
| BCHUSDT | 15 | 15 | 51.3 |
| LDOUSDT | 12 | 15 | 169.7 |
| TRXUSDT | 10 | 15 | 107.7 |
| Portfolio | 15 | 15 | 328.7 |

**INERT-importance gate status.** The brief Section 4.1 INERT falsifier is triggered by rank 15/15 for ALL 3 symbols. Observed: BCH is rank 15/15; LDO is rank 12/15; TRX is rank 10/15. The feature is NOT rank-last for all 3 symbols — INERT importance falsifier is NOT triggered. However the SUSPICIOUS classification supersedes (first match in disjunctive order); the importance data is informational only at this point. BCH's rank 15/15 with importance 51.3 (vs its /060 analog regime_momentum_signed_5d at 70.0) is consistent with the BCH IS edge being destroyed — the feature was allocated minimal BCH splits, yet the massive roster shuffle still destroyed the BCH WR.

---

## Behavioral-Effect Assessment

### Trade-roster diff vs /060 (Section 4.4 falsifier)

| Split | /076 n | /060 n | Added | Removed | Common |
|---|---:|---:|---:|---:|---:|
| IS | 169 | 159 | 100 | 90 | 69 |
| OOS | 102 | 102 | 40 | 40 | 62 |

Brief Section 4.4 predicted IS roster changes of "at least 5 and at most ~60 trades." Observed: 100 IS trades added and 90 removed (100 distinct from /060, net +10). The net count of +10 falls within the predicted IS n_trades range, but the GROSS roster churn (100+90 = 190 total changed slots vs 159 IS trades in /060) is dramatically above the ~60 upper bound predicted for trades CHANGED. The NULL-RESULT falsifier (bit-identical roster → zero trades changed) is NOT triggered. However the gross churn magnitude substantially exceeds the upper bound, indicating the feature produced far more model re-learning than the T5 proxy estimate implied.

**IS added by symbol:** BCH 37, TRX 55, LDO 8. **IS removed by symbol:** BCH 37, TRX 48, LDO 5. The BCH IS roster is 37/73 replaced (51% gross churn) — explaining the WR collapse from 45.2% to 37.0% without changing the count.

---

## Seed Concentration Audit

Single-seed EXPLORATION (outer=42 lineage, 3 seeds: 191664963, 1662057957, 1405681631).

Per `feedback_v3_single_seed_frozen_baseline.md`, the frozen-baseline pattern applies: in /075, BCH was a non-target symbol (scope excluded it from Primitive 12) and thus bit-identical to /060. In /076, ALL 3 symbols are targets of the new universal feature — no frozen-baseline protection. The full roster churn (100 added IS, 90 removed IS) confirms all symbols are perturbed by the feature. This pattern dissolves at multi-seed CONFIRMATION (not applicable here — SUSPICIOUS axes do not advance).

Symbol concentration (OOS): BCH 80.46%, LDO -55.94%, TRX 75.48% — computed against the near-zero-split OOS total; interpretable only in aggregate. The 30% per-symbol cap is a CONFIRMATION gate.

---

## Gate Efficacy Table

| Primitive | State | IS fire count / rate | OOS fire count / rate |
|---|---|---|---|
| 1 — Feature OOD z>2.0 | ON | baseline | baseline |
| 2 — Hurst regime | ON | baseline | baseline |
| 3 — ADX gate | ON | baseline | baseline |
| 4 — Low-vol filter | ON | baseline | baseline |
| 5 — Vol-adjusted sizing | ON | baseline | baseline |
| 9 — Regime kill switch | OFF (/075 baseline) | 0 | 0 |
| 10 — Direction kill switch | OFF (reverted /051) | 0 | 0 |
| 11 — Per-symbol drawdown brake | OFF (closed /054) | 0 | 0 |
| 12 — BTC-trend-regime SIZE de-rate | **OFF (REVERTED from /075)** | 0 | 0 |

No new risk primitive in this iteration; the axis is a model feature. Gate stack is the /060 baseline.

---

## Label Leakage Audit

- REQUIRED_GAP = 66 = (21+1) × 3 symbols — confirmed unchanged.
- Embargo = 22 candles — unchanged.
- The new feature `range_efficiency_50` is computed with `.shift(1)` after the 50-bar rolling window: bar t's value uses `close[t-51 .. t-1]` only. The feature is past-only by construction; the `tests/features_v3/test_range_efficiency_50.py` assertion (b) asserts this property adversarially.
- `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}` confirmed: all symbols use `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)` with 21-candle timeout.
- The walk-forward lookahead-bias note (`feedback_v3_walkforward_lookahead_bug.md`) applies equally to /076. Cross-iteration deltas remain valid; absolute magnitudes are biased upward uniformly.

---

## Anomaly Notes

1. **ADF constant-series error on `TRXUSDT/range_efficiency_50/2020-02`:** Warm-up bars are filled with 0.0 (the feature contract); the earliest TRX training window catches this warm-up period. Benign — ADF test skips that cell; no impact on backtest result.

2. **IS MaxDD 61.69% (vs /060 31.87%):** Directly attributable to the IS PnL collapse. The BCH IS edge (which contributed the vast majority of /060 IS PnL) was destroyed; total IS PnL fell from +51.89 to +3.00. With near-zero IS PnL, the drawdown percentage is dominated by losing streaks that the BCH IS wins previously masked.

3. **OOS PnL +22.36 vs IS PnL +3.00 (ratio 7.4×):** Consistent with SUSPICIOUS-OOS-DOMINANT. The OOS uplift is real (BCH OOS pnl went from -8.69 to +6.98; LDO OOS improved; TRX OOS slight decline). This is NOT a spurious artefact — the model genuinely trades better OOS. The asymmetry is the SUSPICIOUS signature.

4. **Spot-check 10 random OOS trades — 0 issues:** Entry/exit/PnL math checks pass for all 10. Exit reasons (take_profit, stop_loss, timeout) are self-consistent. weight_factor values are non-negative. No anomalies detected.

5. **No NaN Sharpe, no zero-trade IS months, no NaN PnL:** All 37 IS monthly_pnl.csv rows have positive trade_count and numeric pnl_pct. All 15 OOS monthly rows similarly clean (confirmed from run.log final summary).

6. **frac_positive_paths unchanged at 0.6444:** CPCV architecture is invariant to the feature column addition; the 45 path-level CPCV result is structurally fixed by the walk-forward schedule. PBO improved from 0.1278 to 0.0974 — consistent with a model that selects better OOS trades (CPCV detects less per-cell overfitting in OOS paths even as IS collapses). Informational at EXPLORATION.

---

## Recommendations to QR

1. **Axis SUSPICIOUS-OOS-DOMINANT — does NOT advance to cycle-2 CONFIRMATION bundle.** Both SUSPICIOUS trigger conditions fire simultaneously. The axis is closed.

2. **The "marginal-vs-conditional orthogonality" lesson.** The T3 regime-sign-correlation test measures whether the MARGINAL distribution of the feature is correlated with the IS/OOS calendar label. It does NOT measure whether the model's CONDITIONAL use of the feature in interaction with other features is regime-correlated. These are different properties. Future briefs proposing "regime-orthogonal" features must address CONDITIONAL orthogonality, not just marginal — for example by measuring the correlation of the model's feature-split allocation (not the feature value) with the regime label. The current T3 methodology is necessary but not sufficient.

3. **The /043 efficiency-ratio axis is definitively closed.** /076 is the second test of the Kaufman path-efficiency formula, in a more favorable role (15th conditioning feature vs standalone signal). The IS collapse persists. The feature does not work in the current v3 architecture.

4. **IS collapse mechanism is holding-time-roster-composition, not barrier-extension.** The +0.480 candle OOS mean duration shift is NOT a holding-time-extension violation (below the +1.0 gate) but IS the forensic fingerprint of regime-loading via roster selection. Future EXPLORATION briefs for efficiency-type features should pre-register this channel as an additional SUSPICIOUS falsifier: if the model selects longer-duration OOS trades AND shorter-duration IS trades compared to anchor, the regime factor is loaded via composition, not marginal feature distribution.

5. **Cycle-2 axis #7 (/077) remains open.** QR should select the next axis via committed EDA per `feedback_v3_axis_selection_quant_discipline.md`. Cycle-2 so far: /071 SUSPICIOUS-OOS-DOMINANT, /072 NEGATIVE, /073 SUSPICIOUS-OOS-DOMINANT, /074 INERT, /075 INERT, /076 SUSPICIOUS-OOS-DOMINANT — 0/6 clean PROMISING. The IS bear/chop drag remains the structural target.

---

## Status

OVERALL = READY-FOR-CRITIC

Classification: **SUSPICIOUS-OOS-DOMINANT** — `range_efficiency_50` (15th universal Kaufman-efficiency feature) produced IS Δ -0.7894 (IS Sharpe +0.0431, MaxDD 61.69%) and OOS Δ +0.5086 (OOS Sharpe +0.6489), OOS/IS ratio 15.04. Both SUSPICIOUS gates fire: ratio gate (15.04 > 3.0) and OOS-dominant sub-mode (IS shift < 0 AND OOS shift ≥ +0.20). Holding-time falsifier NOT fired: full-roster IS mean Δ +0.005 candles, OOS mean Δ +0.480 candles — both below +1.0 threshold. The +0.480 OOS duration shift is driven entirely by roster composition (added OOS trades: mean 7.25 candles; removed: mean 6.03 candles; common-subset delta: exactly 0.000). Hypothesis falsified: the "structurally unable to produce SUSPICIOUS" argument relied on MARGINAL feature orthogonality (T3 |corr| 0.010) but CONDITIONAL model use can still load the regime factor. /043 re-evaluation outcome: IS still broken (+0.04, MaxDD 61.69%); feature not vindicated. `range_efficiency_50` / `efficiency_ratio_50` axis is definitively closed. ADF warning on `LDOUSDT/cusum_reset_count_200` and `TRXUSDT/range_efficiency_50/2020-02` are informational artifacts; ic_matrix.csv is 15×15 with `range_efficiency_50` present, max |IC| 0.216 (with `sym_vs_btc_ret_7d`).

---

Phase 6 complete. Engineering report committed. Phase 7.5 Critic review required before Phase 7. Orchestrator: invoke `quant-critic` with branch=`iteration-v3/047`, report_dir=`reports-v3/iteration_v3-076`, brief_dir=`briefs-v3/iteration_v3-076`.
