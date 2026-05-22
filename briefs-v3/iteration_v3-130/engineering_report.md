# Engineering Report — iter-v3/130

## Headers

- Iteration: iter-v3/130
- Branch: iteration-v3/130
- Commit SHA: e77e2b66b762e91f1e79673aad4670fbd4087a55
- Hardware: WSL2 Linux 6.6.114 / x86_64
- Wall-clock time: 1.02h

---

## Configuration Diff vs /121 Baseline

| Parameter | /121 Baseline | /130 (this run) |
|---|---|---|
| bar_interval | 8h | **4h** |
| K (triple-barrier candles) | 21 (168h = 7d) | 21 (84h = 3.5d) |
| label_timeout_minutes | 10080 | **5040** |
| enable_per_symbol_drawdown_brake | False | False (REVERT from /127) |
| enable_per_symbol_drawdown_scaling | False | False (REVERT from /129) |
| enable_no_confirm_exit | True | True |
| no_confirm_trigger_atr | 0.50 | 0.50 |
| no_confirm_k_candles | 4 | 4 |
| REQUIRED_GAP | 66 | 66 (candle-count unchanged) |
| V3_FEATURE_COLUMNS_TOP_N | 14 | 14 (UNCHANGED) |
| n_trials | 35 | 35 |
| ENSEMBLE_SIZE | 3 | 3 (EXPLORATION mode) |
| Universe | BCH/LDO/TRX | BCH/LDO/TRX (UNCHANGED) |
| features cache dir | data/features_v3/ | **data/features_v3_4h/** |
| ITERATION_LABEL | v3-121 | **v3-130** |

Single axis variation: bar_interval 8h → 4h. All other parameters bit-identical to /121 in candle-count terms.

---

## Key Metrics Block

| Metric | In-Sample | Out-of-Sample | OOS/IS Ratio |
|---|---|---|---|
| monthly_sharpe | **-1.3028** | +0.3276 | -0.2515 |
| daily_sharpe | -2.7168 | +0.6083 | -0.2239 |
| max_drawdown | 79.79% | 19.53% | 0.2448 |
| profit_factor | 0.6894 | 1.0856 | 1.5747 |
| win_rate | 26.4% | 30.6% | 1.1554 |
| n_trades | 242 | 108 | 0.4463 |
| total_pnl_pct | -69.08 | +7.39 | -0.1070 |
| monthly_calmar | -0.8658 | +0.3783 | -0.4369 |
| weighted_pnl_total | -69.08 | +7.39 | -0.1070 |
| DSR | 0.0000 | — | — |
| PBO | 0.0978 | — | — |
| PSR | 0.9999 | — | — |
| n_trials | 315 | — | — |
| n_effective_trials | 20 | — | — |

### vs /121 Anchor

| | IS | OOS |
|---|---|---|
| /121 CONFIRMATION-MERGE baseline | +1.3108 | +0.9682 |
| /130 (this run) | **-1.3028** | +0.3276 |
| Delta | **-2.6136** | -0.6406 |
| Delta vs ADJUSTED anchor (+1.06 / +0.85) | **-2.3628** | -0.5224 |

IS Δ -2.61 is 6.5× the -0.40 catastrophic threshold magnitude. WORST IS Sharpe in v3 history.

### Per-Symbol (OOS comparison.csv section)

| Symbol | OOS wpnl | OOS trades | OOS WR% | Concentration% |
|---|---|---|---|---|
| BCHUSDT | +8.04 | 48 | 33.3 | 108.81 |
| LDOUSDT | +6.49 | 27 | 37.0 | 87.79 |
| TRXUSDT | -7.14 | 33 | 21.2 | -96.60 |

---

## Per-Symbol Attribution

### In-Sample per-symbol breakdown

| Symbol | IS trades | IS WR% | IS net PnL% | IS % of total |
|---|---|---|---|---|
| BCHUSDT | 126 | 30.2 | -38.17 | 58.9 |
| TRXUSDT | 108 | 35.2 | -9.75 | 15.1 |
| LDOUSDT | 8 | 25.0 | -16.87 | 26.0 |

**BCH IS catastrophic**: 126 IS trades at 30.2% WR → -38.17% cumulative PnL. BCH is the primary IS destroyer: Optuna at 4h-density searched a region of the hyperparameter space that produces high-frequency entries but sub-30% win rates. The feature stack calibrated for 8h noise/signal patterns does not transfer cleanly at 4h.

**LDO IS near-zero trade emission**: only 8 IS trades vs 27 OOS — a 3.4× inversion of the normal IS>OOS trade-count ratio. Optuna at 4h-density found near-degenerate LDO models that emit almost no IS signals, then OOS the model encounters a different regime and fires freely. The 8 IS LDO trades at 25.0% WR contributed -16.87% PnL.

**TRX IS moderate but structurally negative**: 108 trades at 35.2% WR → -9.75% PnL. TRX's 4h cycle structure at K=21 (84h label horizon) does not support 35% WR profitability at the ATR multipliers calibrated for 8h (TP=1.0×ATR, SL=2.0×ATR).

### Falsifier fire-check (Section 8 C1)

IS monthly Sharpe = -1.3028 < +0.91 threshold → **C1 FIRES immediately**. First-match-wins classification: **NEGATIVE-catastrophic**.

Brief pre-registered this modal outcome at 30% prior probability (Section 7 outcome mode "NEGATIVE-catastrophic" = 30%).

---

## Mechanism Diagnosis

The 4h bar-interval transition CATASTROPHICALLY degrades IS performance because the V3_FEATURE_COLUMNS_TOP_N 14-feature stack was calibrated implicitly for 8h candle noise/signal patterns. At 4h, the same feature lookbacks span halved absolute time: `range_realized_vol_50` covers 200h (8.3 days) instead of 400h (16.7 days); `hurst_100` covers 400h (16.7 days) instead of 800h (33.3 days); `ret_skew_200` covers 800h (33.3 days) instead of 1600h (66.7 days). Optuna's IS hyperparameter search — operating on the compressed feature distributions — explored a qualitatively different region of the objective landscape than it did at 8h: BCH produced 126 high-frequency IS trades at only 30.2% WR (vs /121's IS WR approximately 50%+), and LDO degenerated to a near-zero 8 IS trade emission. The halved K=21 label horizon (84h = 3.5 days vs 168h = 7 days) exacerbates this: crypto alt-coin mean-reversion cycles in the 5–7 day range are systematically shorter than the TP target the model is trying to predict, so the 4h label distribution is dominated by SL hits and timeouts rather than TP captures. The brief's pre-flight simulator (T3b) correctly predicted ZERO probability of reaching the IS ≥ +0.91 gate threshold from the bootstrap proxy — but the actual IS result (-1.30) was FAR worse than even the T3b pessimistic tail (-0.30 lower bound), confirming that bootstrap-upsampled 4h proxy CANNOT capture the Optuna search-region shift from 2× IS candle density. The OOS result (+0.33) is marginally positive only because OOS is shorter (14 months), has fewer BCH trades (48 vs 126 IS), and BCH/LDO happened to be in a regime where even a confused 30% WR model captured some TP targets. The /128 cohort-shape finding now formally extends to FREQUENCY axis: the /121 architecture is cohort-AND-frequency-shaped — changing either the symbol set OR the bar interval destroys its IS behaviour.

---

## Seed Concentration Audit

EXPLORATION mode, single outer seed (outer=42), ENSEMBLE_SIZE=3.

ensemble_summary.json confirms seeds: [191664963, 1662057957, 1405681631] all from outer=42 lineage.

Single-seed mode: no multi-seed concentration audit applicable. Per-symbol OOS concentration: BCH 108.81%, LDO 87.79%, TRX -96.60% (TRX net negative). Concentration is extreme but structurally expected in a 3-symbol EXPLORATION-mode run with one catastrophically negative symbol.

---

## Label Leakage Audit

REQUIRED_GAP = 66 = (K + 1) × n_symbols = (21 + 1) × 3 = 66 candles.

This satisfies the Lopez de Prado purge requirement. The walk-forward embargo was verified at the iter-v3/058 RE-ANCHOR (commit e149e9d); `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms`. No regression to the pre-/058 lookahead bug. The 4h bar-interval does not alter the candle-count REQUIRED_GAP formula — it changes absolute embargo duration from 66×8h = 528h (22 days) to 66×4h = 264h (11 days), which remains well beyond any plausible label autocorrelation window at K=21 (84h label horizon).

---

## Gate Efficacy Table

All trades recorded under regime='unknown' — the per_regime.csv aggregates are single-row for both IS and OOS. Regime-conditional gate fire-rate breakdown is not available at this granularity. The 7-gate RiskV2 stack is UNCHANGED from /121 (/127 binary brake disabled, /129 continuous scaling disabled per REVERT). Gate fire-rate analysis would require per-gate instrumentation not present in /130 outputs.

### CPCV Path Distribution

45 paths from CPCV:

- Positive paths: 27/45 = 0.600 (gate threshold 0.55 → PASS per dsr.json `cpcv_frac_positive_paths_gate_pass: true`)
- Negative paths: 18/45 = 0.400
- Path Sharpe q25: -0.2972, q50: +0.3562, q75: +0.7959
- PBO = 0.0978 (well below 0.40 gate)
- PSR = 0.9999 (above 0.95 gate)
- DSR = 0.0000 (IS Sharpe is negative — DSR degenerates to 0)
- n_effective_trials = 20

The CPCV/PBO/PSR metrics all PASS their individual gates despite the catastrophic IS Sharpe. This is structurally consistent: PBO measures the probability that IS outperforms OOS (low PBO = IS does NOT outperform OOS), which is satisfied here because IS is catastrophically negative. PSR at 0.9999 reflects the OOS Sharpe distribution having high probability of being positive. DSR = 0 because the formula requires IS Sharpe > 0 as denominator. These metrics do not indicate "goodness" — they indicate that OOS Sharpe is reliably positive despite IS catastrophe, which is the mechanistic fingerprint of a model that overfits IS to lose money there and finds its signal OOS by accident.

---

## ADF Stationarity Summary

ADF tests conducted over 4h feature parquets (data/features_v3_4h/):

- Stationary features (p < 0.05): 1803/2198 = 82.0%
- Non-stationary: 395/2198 = 18.0%

Feature stationarity at 4h is comparable to 8h (expected — the same raw features are computed over the same candle-count lookbacks). Non-stationary rows correspond predominantly to early 2020-01 months where data depth is shallow for LDOUSDT.

---

## High-IC Feature Pairs (IC Matrix)

| Feature pair | Pearson IC |
|---|---|
| vwap_dev_20 × regime_momentum_signed_5d | 0.764 |
| sym_vs_btc_ret_7d × regime_momentum_signed_5d | 0.619 |
| ret_skew_200 × ret_kurt_200 | 0.613 |
| max_dd_window_50 × range_realized_vol_50 | -0.685 |

The vwap_dev_20 × regime_momentum_signed_5d high IC (0.764) was pre-declared by the brief per the iter-v3/025 engineered-feature IC carve-out policy. The max_dd_window_50 × range_realized_vol_50 inverse correlation (-0.685) is structural (high volatility windows correlate with max drawdown events). No new IC concerns emerge at 4h vs 8h.

---

## Anomaly Notes

**Trade row spot-check (10 random OOS rows, seed=99)**: all 10 rows pass PnL math verification (net_pnl_pct = raw_return - fee_pct within 0.01 tolerance). Exit reasons span stop_loss, take_profit, timeout, and no_confirm — all mechanically consistent. Weight_factor and confidence values in expected ranges (wf 0.52–1.00, conf 0.72–0.93).

**IS trade count 242 vs brief projected 346**: The brief's F7 falsifier registered [260, 433] as the expected IS trade-count range at 4h. Actual 242 is below the 260 lower bound — F7 fires. This indicates Optuna at 4h-density found models with LOWER signal-emission rate than the 2× density naive projection, consistent with the hyperparameter region shift hypothesis: the model found lower-confidence threshold parameters that emit fewer trades rather than more.

**LDO IS 8 trades**: Extremely low — Optuna at LDO 4h found a near-degenerate solution emitting 8 IS trades out of 39 months. This is mechanically valid (the walk-forward trainer found low-emission optimal configurations for LDO at 4h) but indicates catastrophic signal degradation for LDO at the 4h feature distributions. LDO IS per_symbol.csv shows only 8 trades at 25.0% WR.

**IS Win Rate 26.4%**: Far below the profitability threshold. With TP=1.0×ATR and SL=2.0×ATR (reward:risk = 1:2), breakeven WR is 66.7%. Observed IS WR of 26.4% means the model is directionally ANTI-predictive at 4h — it consistently picks the wrong direction in the training window. This is the signature of a feature stack that has been implicitly calibrated for 8h periodicity and produces inverted signals at 4h.

---

## Section 8 Gate Evaluation (first-match-wins)

**C1**: IS monthly Sharpe = -1.3028 < +0.91 threshold AND OOS monthly Sharpe = +0.3276 < +0.67 threshold.
**C1 FIRES. Classification: NEGATIVE-catastrophic.**

No further criteria evaluated per first-match-wins protocol.

**Bar-interval axis status**: This is the 9th NEGATIVE in cycle-7 (8/8 prior + /130 = 9/9 consecutive NEGATIVE). The bar-interval axis CLOSES per brief Section 8 C1 explicit closure clause: "If C1 fires at /130: bar-interval axis CLOSED for cycle-7; /131 = cycle-7 EXPLORATION slot #10, axis TBD by QR." The /128 cohort-shape finding now extends to FREQUENCY: /121 architecture is cohort-AND-frequency-shaped.

---

## Status

OVERALL=READY-FOR-CRITIC
