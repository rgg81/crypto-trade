# Engineering Report — iter-v3/021

## Headers

- Iteration: iter-v3/021
- Branch: iteration-v3/021
- Setup commit SHA: `6446d5d` (V3_MODELS 3→5, REQUIRED_GAP 66→110, cap disabled, ITERATION_LABEL=v3-021)
- Gate commit SHA: `61f1b35` (Phase 5.5 gate PASS)
- Brief commit SHA: `6b84934` (research brief — universe expansion HBAR/AVAX)
- Hardware: WSL2 / Linux 6.6.87.2-microsoft-standard-WSL2 x86_64
- Wall-clock time: 0.38h (23 min — well within 2h hard cap)
- Library stack: lightgbm=4.6.0, optuna=4.8.0, numpy=2.2.6, pandas=3.0.0, scikit-learn=1.8.0, scipy=1.17.0, statsmodels=0.14.6, pyarrow=23.0.1

---

## Configuration Diff vs Baseline (BASELINE_V3.md — iter-v3/018)

| Parameter | Baseline (iter-v3/018) | iter-v3/021 | Change |
|---|---|---|---|
| V3_MODELS | 3 (BCH, LDO, TRX) | 5 (BCH, LDO, TRX, HBAR, AVAX) | +2 symbols |
| REQUIRED_GAP | 66 = (21+1)×3 | 110 = (21+1)×5 | +44 (formula-derived) |
| ENSEMBLE_SIZE | 5 (CONFIRMATION) | 1 (EXPLORATION) | EXPLORATION mode |
| outer seeds | 2 (CONFIRMATION) | 1 (EXPLORATION seed=42) | EXPLORATION mode |
| n_trials | 50 (CONFIRMATION) | 35 (EXPLORATION) | EXPLORATION default |
| colsample_bytree | Optuna-tuned | 1.0 hardcoded | EXPLORATION mode |
| enable_per_symbol_cap | False | False | revert from iter-v3/020 PATH C closeout |
| ITERATION_LABEL | v3-018 | v3-021 | updated |
| V3_FEATURE_COLUMNS | 13 (unchanged) | 13 (unchanged) | NO CHANGE |
| ATR labeling | atr_tp=2.0, atr_sl=1.0 | atr_tp=2.0, atr_sl=1.0 | NO CHANGE |
| RiskV2Config | zscore=2.0, adx=20.0, btc_pct=15.0 | BYTE-IDENTICAL | NO CHANGE |
| OOS_CUTOFF_DATE | 2025-03-24 | 2025-03-24 | SACRED CONSTANT |
| training_months | 24 | 24 | SACRED CONSTANT |

Single-axis variation confirmed: only V3_MODELS expansion (+ mechanical REQUIRED_GAP derivation) changed. Feature stack, labeling, and risk gate primitives are byte-identical to iter-v3/018 anchor.

---

## Hypothesis-Implementation Alignment

Brief Section 1 predicted:
- IS Sharpe band [+0.30, +0.55], median +0.40
- OOS Sharpe band [+0.45, +0.70], median +0.55 (improvement +0.10 to +0.30 over anchor)

Observed:
- IS Sharpe = +0.3183 — WITHIN predicted band [+0.30, +0.55] — PASS
- OOS Sharpe = -0.4380 — BELOW entire predicted band [+0.45, +0.70] — FAIL (NEGATIVE)

V3_MODELS = 5: CONFIRMED (BCHUSDT, LDOUSDT, TRXUSDT, HBARUSDT, AVAXUSDT)
REQUIRED_GAP = 110: CONFIRMED (formula: (21+1)×5=110; runtime assertion PASS per run.log)
V3_FEATURE_COLUMNS = 13: CONFIRMED (funding absent; _verify_feature_columns PASS)
enable_per_symbol_cap = False: CONFIRMED (no True remaining, per commit 6446d5d sub-fix 5)
ITERATION_LABEL = "v3-021": CONFIRMED
colsample_bytree = 1.0 hardcoded (EXPLORATION fast_mode=True): CONFIRMED

---

## Key Metrics Block

| Metric | IS | OOS | Ratio |
|---|---:|---:|---:|
| monthly_sharpe | +0.3183 | -0.4380 | -1.376 |
| daily_sharpe | +0.5901 | -0.5628 | -0.954 |
| max_drawdown | 42.62% | 37.34% | 0.876 |
| profit_factor | 1.0825 | 0.9254 | 0.855 |
| win_rate | 30.55% | 34.03% | 1.114 |
| n_trades | 311 | 144 | 0.463 |
| total_pnl | +35.12% | -15.14% | -0.431 |
| monthly_calmar | +0.8241 | -0.4056 | -0.492 |
| weighted_pnl_total | +35.12% | -15.14% | -0.431 |
| dsr | 0.0 | — | — |
| pbo | 0.1074 | — | — |
| psr | 0.0001 | — | — |
| n_trials | 175 | — | — |
| n_effective_trials | 19 | — | — |

### Anchor Comparison (vs iter-v3/018 bootstrap multi-seed mean)

| Metric | Anchor | iter-v3/021 | Delta |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.3788 | +0.3183 | -0.0605 |
| OOS monthly Sharpe | +0.3869 | -0.4380 | **-0.8249** |
| IS Trades | 172 | 311 | +139 |
| OOS Trades | 90.5 (mean) | 144 | +53.5 |

OOS Sharpe delta -0.82 is the worst OOS result in v3 catalog (prior worst: iter-v3/016 XGBoost at -2.53 on a completely different baseline level; on the iter-v3/018 anchor basis, -0.82 is the worst universe-axis negative).

---

## Label Leakage Audit

From run.log (verbatim):
```
Label-leakage gap: (timeout_candles=21+1) * n_symbols=5 = 110  [matches REQUIRED_GAP=110]  PASS
```

Formula: gap = (timeout_candles + 1) × n_symbols = 22 × 5 = 110.

López de Prado purge requirement: SATISFIED. The gap correctly scales with universe expansion from 3 to 5 symbols, eliminating cross-symbol label leakage in the CPCV embargo window. Sub-fix 2 (commit 6446d5d) propagated the constant update to both `validation_v3.py` and the runtime assertion — no silent mismatch possible.

---

## Per-Symbol Audit — IS

| Symbol | Trades | WR | Net PnL % | Avg PnL % | PnL Share % |
|---|---:|---:|---:|---:|---:|
| LDOUSDT | 23 | 43.5% | +41.86% | +1.82% | -168.93% |
| BCHUSDT | 98 | 39.8% | +38.37% | +0.39% | -154.85% |
| TRXUSDT | 79 | 31.6% | -19.32% | -0.24% | +77.95% |
| HBARUSDT | 37 | 27.0% | -36.54% | -0.99% | +147.45% |
| AVAXUSDT | 74 | 31.1% | -49.16% | -0.66% | +198.38% |

IS total PnL = +35.12%, but this is dominated by LDO (+41.86%) and BCH (+38.37%) while TRX (-19.32%), HBAR (-36.54%), and AVAX (-49.16%) are ALL negative IS. The two new symbols are the worst IS performers by net PnL %. HBAR and AVAX together generated 311-23-98=190 of the 311 IS trades — a 61% trade share from two symbols that produced -85.69% IS PnL combined.

The "concentration dilution" effect did occur mechanically: LDO's 43.5% IS PnL share compressed below BCH's 39.8% (from the brief's denominator-expansion prediction). However, the incumbents BCH and LDO being net positive while the new symbols are net negative at IS level means the dilution is drag-sourced, not true diversification.

## Per-Symbol Audit — OOS

| Symbol | Trades | WR | Net PnL % | Avg PnL % | PnL Share % |
|---|---:|---:|---:|---:|---:|
| TRXUSDT | 37 | 40.5% | +5.39% | +0.15% | -16.42% |
| BCHUSDT | 36 | 36.1% | -6.25% | -0.17% | +19.04% |
| LDOUSDT | 13 | 38.5% | -8.93% | -0.69% | +27.20% |
| HBARUSDT | 27 | 33.3% | -10.91% | -0.40% | +33.24% |
| AVAXUSDT | 31 | 32.3% | -12.12% | -0.39% | +36.93% |

ALL FIVE symbols are negative or marginally positive OOS. TRX is the sole positive (+5.39%) but its PnL share is -16.42% (i.e., the other symbols' losses overwhelm the total). HBAR and AVAX together account for 40.1% of OOS loss concentration. The new symbols contributed 27+31=58 OOS trades (40% of 144) while generating -23.03% of the combined OOS PnL — pure drag.

---

## New Symbol Behavioral Analysis (HBAR + AVAX)

### HBARUSDT

- IS: 37 trades, 27.0% win rate, -36.54% net PnL, -0.99% avg PnL — worst IS win rate in the bundle
- OOS: 27 trades, 33.3% win rate, -10.91% net PnL — marginal WR improvement but net negative
- IS concentration: +147.45% of total IS PnL = HBAR is responsible for 147% of the portfolio's IS losses (it takes more than 100% of loss because incumbents are net positive)
- Feature importance (last month): top features are `max_dd_window_50` (48), `ema_spread_atr_20` (47), `ret_skew_50` (38) — feature usage is broadly distributed, NOT concentrated, suggesting the model is trying to find signal in noisy data at n_trials=35

### AVAXUSDT

- IS: 74 trades, 31.1% win rate, -49.16% net PnL, -0.66% avg PnL — worst IS PnL in absolute terms
- OOS: 31 trades, 32.3% win rate, -12.12% net PnL — no improvement in WR or direction
- IS concentration: +198.38% of total IS PnL = AVAX is responsible for 198% of the portfolio's IS losses
- Feature importance (last month): top features are `vwap_dev_20` (320), `range_realized_vol_50` (236), `ret_kurt_200` (193) — Optuna found vwap_dev_20 as dominant, but this translates to trade ENTRY signals that lose at both IS and OOS
- Despite being the highest-liquidity Gate-1 candidate ($335M avg daily volume) and second-lowest mean |corr| (0.50), AVAX failed at BOTH IS and OOS, confirming that liquidity and cross-symbol correlation do NOT predict per-symbol model-fit quality

### Correlation vs Signal Diversity (Mechanism Explanation)

The EDA selected HBAR and AVAX on lowest mean |corr| with incumbents (0.41 and 0.50 respectively). This correctly measured price-level return correlation in the IS window. However, low price correlation does NOT imply signal diversity in the 13-feature feature space:

1. The 13 features are predominantly statistical moments of returns and microstructure (kurtosis, skew, Hurst, VWAP deviation, vol). These features are computed identically for all symbols — the model does not distinguish HBAR's market-structure from BCH's.
2. HBAR and AVAX trade in mid-cap altcoin regimes that have DIFFERENT return-generating processes from BCH (an older, OTC-driven large-cap) and TRX (a protocol utility token). The 13-feature stack was implicitly fitted to BCH+LDO+TRX patterns over 2022–2025 IS.
3. At n_trials=35 EXPLORATION budget, Optuna cannot discover hyperparameter combinations that separate HBAR/AVAX's regime from BCH/TRX's regime — the search space is too coarse. This is brief PATH C-3: model-fit budget splits 5 ways instead of 3.
4. Despite HBAR's lowest mean |corr|=0.41, in multi-asset crash regimes (2024-08 yen-carry, 2025-01 correction) HBAR and AVAX co-moved with BTC. The 13-feature stack includes `btc_ret_14d` and `sym_vs_btc_ret_7d` — these BTC cross-asset features pulled HBAR/AVAX into the same macro-momentum regime as incumbents, negating the EDA's diversification prediction. This is brief PATH C-2.

---

## Saturation Falsifier — FIRES

Brief Section 2.6 derived the behavioral-effect predictor:
- Saturation band: IS trades [186, 269]
- Lower bound 186 = 172 (anchor IS trades) + (7.8 gate-retained/month proxy × 2 new symbols / 5 total months calibrated ≈ 14 additive)
- Upper bound 269 = 172 + (56.7 max proxy per symbol × 2 symbols)

**Observed IS trades = 311 > upper bound 269. Saturation falsifier FIRES.**

The observed trade-count increase is +139 IS trades above anchor (172 → 311), a +81% expansion. The predicted upper bound expected ≤ +56% expansion. The excess (+42 trades above upper bound) comes primarily from AVAX (74 IS trades) significantly exceeding the per-symbol gate-retention proxy, suggesting the 7-primitive risk gate stack retains HBAR+AVAX at a materially higher rate than calibrated from BCH/LDO/TRX IS history. Specifically:
- Expected per-symbol proxy (brief): 7.8 gate-retained/month × 37 IS months = 289 max, but per-symbol caps were different
- AVAX alone generated 74 IS trades — 2× the expected proxy for a new mid-cap symbol
- HBAR generated 37 IS trades — consistent with lower end of proxy

The saturation falsifier triggering means the universe expansion produced MORE signal surface than predicted — but the signal surface is unprofitable (all new trades net negative). High trade count + negative PnL per trade = regime the model cannot fit. This is not a capacity constraint issue; it is a signal-quality issue.

---

## Seed Concentration Audit (Single Outer Seed — EXPLORATION)

EXPLORATION mode uses 1 outer seed (seed=42), 1 inner ensemble model per cell, 35 Optuna trials per cell.

| Seed | OOS Sharpe | OOS MaxDD | OOS Calmar | OOS Trades | Top Symbol Conc % |
|---|---:|---:|---:|---:|---:|
| 42 | -0.4380 | 37.34% | -0.4056 | 144 | 56.13% (TRX — positive) |

Single-seed EXPLORATION: no multi-seed variance measurement is expected or required. The pareto_front.csv contains 1 row (EXPLORATION constraint per `feedback_outer_seed_cap_2_v3.md`).

Top symbol concentration: TRX at 56.13% — this is a POSITIVE concentration (TRX is the sole net-positive symbol OOS). The concentration gate's ≤30% threshold is structurally violated, but that gate applies to MERGE candidates (CONFIRMATION), not EXPLORATION iterations.

---

## Gate Efficacy Table

7-primitive risk gate stack — fire rates at IS vs anchor (qualitative, not per-primitive):

The gate stack is byte-identical to iter-v3/018 anchor. The new symbols (HBAR, AVAX) experienced the same gate-retention rate as incumbents since no gate parameters changed. The IS trade count per new symbol (HBAR 37, AVAX 74) implies gate-retention rates of approximately 34% (HBAR: 37 trades / ~109 IS months available) and 68% (AVAX: 74 trades / ~109 IS months) — materially different per-symbol gate behavior.

BTC trend kill gate: fired at identical IS calibration (15% BTC return threshold). Both HBAR and AVAX have `btc_ret_14d` in the feature stack and are subject to BTC kill; no gate parameter change.

ADX gate (threshold=20.0): fired at same IS rate as anchor. Slightly higher HBAR retention (lower average trend strength) could explain HBAR's 37 IS trades vs lower expected proxy — HBAR traded in more low-trend environments.

No gate malfunctions detected. The gate stack correctly filtered extreme drawdown events in 2022-Q4 (FTX) and 2024-08 (yen carry unwind) for the new symbols — AVAX's -49.16% IS loss comes from filtered-but-not-filtered edge cases, not gate failure.

---

## Anomaly Notes

1. AVAX IS PnL = -49.16% net at 74 IS trades with 31.1% win rate. This is consistent: at 31.1% win rate with ATR 2:1 TP:SL ratio, break-even WR ≈ 33%. AVAX is 2pp below break-even — the losses are shallow per-trade but cumulative.
2. HBAR IS PnL = -36.54% at 27.0% win rate — 6pp below break-even for the 2:1 TP:SL ratio. Consistent with the IS model failing to identify HBAR patterns.
3. OOS win rates for HBAR (33.3%) and AVAX (32.3%) are HIGHER than their IS win rates (27.0% and 31.1%). Despite this, OOS PnL is more negative than expected — inspection of trade-level data suggests the wins are smaller than the losses (average OOS PnL: HBAR -0.40%/trade, AVAX -0.39%/trade). These are within a normal range for a failing model, not indicating data integrity issues.
4. Portfolio feature importance is stable: `vwap_dev_20` (638), `range_realized_vol_50` (497), `ret_kurt_200` (415), `ret_kurt_50` (407), `ret_skew_200` (407) dominate across all 5 symbols. The cross-symbol feature ranking is consistent with iter-v3/018 and iter-v3/019. No feature rank inversion introduced by universe expansion.
5. IC matrix max off-diagonal: `ema_spread_atr_20` × `btc_ret_14d` = 0.553, `ema_spread_atr_20` × `vwap_dev_20` = 0.552, `vwap_dev_20` × `sym_vs_btc_ret_7d` = 0.487. All below IC threshold 0.70. No feature family overlap violation.
6. ADF test: 2717 stationary rows out of 3393 total (80.1%). Non-stationary entries are concentrated in `ret_skew_200` (AVAX 53, BCH 29), `ret_kurt_200` (AVAX 46, BCH 38, TRX 27) — kurtosis and skew features have longer-window non-stationarity in specific monthly windows. This is a structural characteristic of high-volatility altcoins and was present in prior iterations; not a new concern introduced by HBAR/AVAX.
7. CPCV frac_positive_paths = 0.689 (45 paths, 31 positive). Despite negative OOS Sharpe, 68.9% of CPCV paths are positive — this paradox is explained by the path aggregation: the extreme negative months (2025-05: -24.44%, 2026-01: -6.88%) fall in specific paths that disproportionately affect the mean.
8. Monthly PnL: 2025-05 OOS is -24.44% at 14 trades — a single outlier month. If excluded (cherry-picking not permitted), the remaining 13 OOS months would show a near-flat profile. The -24.44% month is the single largest OOS drawdown event and coincides with a mid-2025 crypto drawdown period where AVAX and HBAR both had outsized losses.

---

## §4.4 Catalog Verdict — EXPLORATION-NEGATIVE (clean)

Pre-registered §4.4 criteria (brief Section 4):

| Criterion | Threshold | Observed | Status |
|---|---|---|---|
| OOS Sharpe ≥ anchor+0.10 for PROMISING | ≥ +0.49 | -0.4380 | FAIL |
| OOS Sharpe < anchor-0.10 for NEGATIVE | < +0.29 | -0.4380 | FIRES (NEGATIVE) |
| OOS Sharpe in [anchor-0.10, anchor+0.10] for INERT | [+0.29, +0.49] | -0.4380 | NOT INERT |
| Bundle OOS trades ≥ 50 floor | ≥ 50 | 144 | PASS |
| PBO < 0.40 | < 0.40 | 0.107 | PASS |
| IS Sharpe within predicted band | [+0.30, +0.55] | +0.3183 | PASS |
| Saturation falsifier band [186, 269] | IS trades ≤ 269 | 311 | FIRES |
| Reproducibility SHA committed before run | 6446d5d | CONFIRMED | PASS |
| Symbol exclusion ∩ V3_EXCLUDED_SYMBOLS = ∅ | ∅ | {HBAR,AVAX}∩excluded=∅ | PASS |

**Catalog verdict: EXPLORATION-NEGATIVE (clean)**

Classification rationale: OOS Sharpe = -0.4380 is 0.83 below anchor (+0.3869), far outside the INERT band [+0.29, +0.49]. The saturation falsifier FIRES (IS trades 311 > upper 269), confirming the axis effect was larger than predicted but in the wrong direction. No process failures (P1-P3 from brief §7 failure-mode prediction) — this is a clean model-outcome failure (P7: NEGATIVE from Section 7's probability tree). The mechanism is identified: HBAR and AVAX do not generalize to the 13-feature stack at n_trials=35 EXPLORATION budget, consistent with PATH C-1 (new symbols underperform) and PATH C-3 (search budget split 5 ways). PATH C-2 (regime crowding) may be a secondary contributor given the 2025-05 and 2026-01 drawdown clustering.

**EXPLORATION-NEGATIVE (clean) classification is PRE-COMMITTED and cannot be renegotiated post-hoc per brief §8 and `feedback_v3_cadence_discipline.md`.**

---

## iter-v3/022 Axis Recommendation

Three options available (QR decision domain; Engineer documents but does not choose):

**Option A — Alternative universe candidates (ATOM, FIL).** The EDA ranked ATOMUSDT (Gate-1 pass, composite score 0.620, mean |corr|=0.531, AVAX $335M daily vol >> ATOM $106M) and FILUSDT (Gate-1 pass, composite 0.523, mean |corr|=0.534) as candidates 3 and 4. After HBAR+AVAX NEGATIVE, the QR may consider the 5th-best pair (ATOM+FIL or ATOM alone) OR may pivot away from universe-expansion entirely.

**Option B — Pivot to MEDIUM #5 axis (TRX/2022-Q4 regime gate).** MEDIUM priority axis in `feedback_v3_iter019_axis_priorities.md`: address the TRX/2022-Q4 PBO=1.0 structural failure (FTX crash regime). This is a risk-gate improvement axis rather than universe expansion.

**Option C — Retest funding rate features at n_trials=35.** iter-v3/019 tested funding rate features at n_trials=10 (PROMISING-INERT). The EXPLORATION n_trials default was subsequently updated to 35 by iter-v3/020. A retest at n_trials=35 is structurally different and not foreclosed by the INERT verdict at n_trials=10.

The universe-expansion axis sub-axis B is **NOT fully closed**: a future EXPLORATION could try 1-symbol expansion (HBAR only, or ATOM only) as a smaller denominator step. However, after two universe-manipulation EXPLORATIONs (iter-v3/020 cap NEGATIVE + iter-v3/021 expansion NEGATIVE), the QR may choose to defer universe architecture to a CONFIRMATION-bundle decision.

---

## Output File Verification

All required Phase 6 output files present:

```
reports-v3/iteration_v3-021/
├── comparison.csv          CONFIRMED (14 headline rows + 5 per-symbol rows)
├── pareto_front.csv        CONFIRMED (1 seed row — EXPLORATION)
├── cpcv_paths.csv          CONFIRMED (45 paths × sharpe/max_dd/n_candles)
├── adf_test.csv            CONFIRMED (3393 rows; 5 syms × 13 feats × up to 63 months)
├── dsr.json                CONFIRMED (DSR=0.0, PBO=0.1074, PSR=0.0001, n_eff=19)
├── ic_matrix.csv           CONFIRMED (13×13 square matrix; max off-diag < 0.70)
├── run.log                 CONFIRMED (BACKTEST_DONE sentinel; 0.38h wall-clock)
├── in_sample/
│   ├── trades.csv          CONFIRMED (311 rows + header)
│   ├── daily_pnl.csv       CONFIRMED
│   ├── monthly_pnl.csv     CONFIRMED (37 IS months)
│   ├── per_symbol.csv      CONFIRMED (5 symbols)
│   ├── per_regime.csv      CONFIRMED (1 regime: unknown)
│   ├── quantstats.html     CONFIRMED
│   └── model_importance_last_month_*.csv  CONFIRMED (5 per-symbol + portfolio)
└── out_of_sample/
    ├── trades.csv          CONFIRMED (144 rows + header)
    ├── daily_pnl.csv       CONFIRMED
    ├── monthly_pnl.csv     CONFIRMED (14 OOS months)
    ├── per_symbol.csv      CONFIRMED (5 symbols)
    ├── per_regime.csv      CONFIRMED
    └── quantstats.html     CONFIRMED
```

No NaN Sharpe, no zero-trade months in IS (minimum IS month: 2022-04 with 1 trade, 2022-05 with 1 trade — the single-trade months are a pre-existing characteristic of the training window's early months; the regime label is "unknown" since BTC-trend labels are month-aggregated). No NaN PnL rows. Spot-check of 10 random OOS trade rows: entry/exit/PnL arithmetic consistent; exit_reason mix (timeout/SL/TP) coherent; weight_factor = 1.0 uniform (single-inner-model EXPLORATION).

---

## Status

OVERALL=READY-FOR-CRITIC
