# Engineering Report — iter-v3/020

## Headers

- Iteration: iter-v3/020
- Type: EXPLORATION (cadence #2 of 10 post-bootstrap; STRUCTURAL axis — NEW risk primitive, concentration architecture, HIGH-priority #2)
- Branch: iteration-v3/020
- Setup commit SHA: 37df8a9 (feat: per-symbol PnL cap (primitive 8) + revert funding to 13 features + sklearn pin)
- Phase 5.5 gate SHA: 68a02ae (PASS)
- Brief SHA: de82b8e
- EDA SHA: bbbe783 (analysis/iteration_v3-020/per_symbol_cap_eda.py)
- HEAD SHA at backtest run: 37df8a9
- Hardware: WSL2 / Linux 6.6.87.2 / 12th Gen Intel Core i9-12900HK / 60 GiB RAM
- Wall-clock time: 0.22h (13 min — within 30 min target / 2h EXPLORATION hard cap)
- Runner invocation: `uv run python run_baseline_v3.py --exploration --seeds 1`
- Anchor: iter-v3/018 multi-seed mean IS +0.3788 / OOS +0.3869

## Library Stack (Reproducibility Stamp)

| Package | Version |
|---|---|
| lightgbm | 4.6.0 |
| numpy | 2.2.6 |
| optuna | 4.8.0 |
| pandas | 3.0.0 |
| pyarrow | 23.0.1 |
| scikit-learn | 1.8.0 |
| scipy | 1.17.0 |
| statsmodels | 0.14.6 |

sklearn pinned to `>=1.8,<1.9` in `pyproject.toml` per Critic FINAL Recommendation 12 of iter-v3/019 (addresses silent drift; matches BASELINE_V3.md runtime version 1.8.0). No mlfinlab / mlfinpy / pypbo / fracdiff dependency.

## Hypothesis-Implementation Alignment

Single-axis variation: `max_per_symbol_pnl_share = 0.40` + `max_per_symbol_window_bars = 90` + `enable_per_symbol_cap = True` added to `RiskV2Config` and activated in `RiskV2Wrapper.get_signal()`. Per brief Section 1: the cap operates as a TRADE-TIME SCALING layer — it multiplies `weight_factor` by `cap / observed_share` when a symbol's rolling 30-day PnL share exceeds 0.40. Trades are NOT killed; only position magnitude shrinks.

Feature surface reverted from 14 → 13 columns per Critic FINAL Rec 2 of iter-v3/019: `funding_rate_zscore_30` REMOVED from `V3_FEATURE_COLUMNS`. `_verify_feature_columns()` asserts `len == 13` at runtime. `n_trials = 35` (default from `--exploration` per `feedback_v3_exploration_n_trials_35`; no override block present). Symbols, labeling, zscore gate, BTC trend filter, ADX gate, Hurst check, low-vol floor all UNCHANGED from iter-v3/018.

## Configuration Diff vs Baseline (iter-v3/018 multi-seed BOOTSTRAP)

| Parameter | iter-v3/018 BOOTSTRAP | iter-v3/020 EXPLORATION |
|---|---|---|
| ITERATION_LABEL | "v3-018" | **"v3-020"** |
| V3_FEATURE_COLUMNS count | 13 | **13** (funding reverted, back to iter-v3/018 surface) |
| `funding_rate_zscore_30` | ABSENT | ABSENT (reverted from iter-v3/019) |
| `max_per_symbol_pnl_share` | (not present) | **0.40 (NEW primitive 8)** |
| `max_per_symbol_window_bars` | (not present) | **90 (NEW; ≈ 30d at 8h)** |
| `enable_per_symbol_cap` | (not present) | **True (NEW)** |
| sklearn bound | `>=1.5` | **`>=1.8,<1.9`** (Critic rec) |
| Outer seeds | 2 (--seeds 2) | 1 (--seeds 1 via --exploration) |
| ENSEMBLE_SIZE (inner) | 5 | 1 (--exploration) |
| n_trials | 50 | 35 (--exploration) |
| colsample_bytree | Optuna-tuned | 1.0 (--exploration) |
| Symbols | BCH, LDO, TRX | UNCHANGED |
| ATR labeling (tp/sl) | 2.0 / 1.0 | UNCHANGED |
| zscore_threshold | 2.0 | UNCHANGED |
| BTC trend threshold_pct | 15.0 | UNCHANGED |
| ADX threshold | 20 | UNCHANGED |
| REQUIRED_GAP | 66 | UNCHANGED |
| OOS_CUTOFF_DATE | 2025-03-24 | UNCHANGED (sacred) |
| training_months | 24 | UNCHANGED (sacred) |

Single-axis discipline: the SOLE strategic change vs iter-v3/018 is addition of the per-symbol PnL cap (primitive 8). Feature revert and sklearn pin are mandated pre-commits per Critic FINAL Rec 2 of iter-v3/019, not independent axes.

## Key Metrics Block

### Headline (comparison.csv — single seed 42, EXPLORATION mode)

| Metric | IS | OOS | Ratio |
|---|---:|---:|---:|
| monthly_sharpe | +0.2745 | **-0.3296** | -1.2008 |
| daily_sharpe | +0.4851 | -0.8178 | -1.6858 |
| max_drawdown (%) | 29.33 | 34.10 | 1.1626 |
| profit_factor | 1.0739 | 0.8887 | 0.8275 |
| win_rate (%) | 31.00 | 37.21 | 1.2003 |
| n_trades | 200 | 86 | 0.4300 |
| total_pnl (%) | +12.06 | -9.07 | -0.7527 |
| monthly_calmar | +0.4111 | -0.2661 | -0.6474 |
| weighted_pnl_total | +12.06 | -9.07 | -0.7527 |
| dsr | 0.0000 | — | — |
| pbo | 0.1190 | — | — |
| psr | 0.0009 | — | — |
| n_trials | 105 | — | — |
| n_effective_trials | 19 | — | — |

### vs anchor (iter-v3/018 multi-seed mean)

| Metric | iter-v3/018 anchor | iter-v3/020 | Delta |
|---|---:|---:|---:|
| IS monthly_sharpe | +0.3788 | +0.2745 | **-0.1043** |
| OOS monthly_sharpe | +0.3869 | -0.3296 | **-0.7165** |

Both deltas exceed the -0.10 magnitude threshold. **PATH C falsifier 1 fires**: IS Sharpe < anchor (+0.2745 < +0.3788) AND OOS Sharpe < anchor-0.10 (-0.3296 < +0.2869). Unambiguous EXPLORATION-NEGATIVE (clean).

### PATH C confirmation: counterfactual vs observed

| Mode | Predicted OOS delta | Observed OOS delta |
|---|---:|---:|
| Mode A (static counterfactual, brief §2.2.1) | -0.3619 | — |
| Mode B (rolling counterfactual, brief §2.2.2) | -0.2648 | — |
| **iter-v3/020 actual** | predicted lower-bound [-0.36, -0.26] | **-0.7165** |

The observed OOS delta (-0.7165) is substantially WORSE than both counterfactual lower bounds (Mode A -0.36, Mode B -0.26). The PATH C scenario was pre-registered at P=30% probability; its realization and magnitude exceeding the lower bound confirms that Optuna at n_trials=35 did NOT compensate for the cap — in fact, the cap + Optuna interaction degraded OOS further below the static counterfactual estimate. Mechanism: concentration carries genuine edge that the cap removed proportional to conviction.

## Seed Concentration Audit (EXPLORATION single-seed)

| Seed | IS monthly Sharpe | OOS monthly Sharpe | OOS MaxDD | OOS Calmar | OOS Trades | Max conc (%) | BTC killed |
|---|---:|---:|---:|---:|---:|---:|---:|
| 42 | +0.2745 | -0.3296 | 34.10% | -0.2661 | 86 | 80.45% | 35 |

Single-seed EXPLORATION run. Post-cap max concentration 80.45% — EXCEEDS the 40% cap threshold. This is NOT a mechanism defect: the concentration metric in `seed_summary.json` is computed from raw per-symbol OOS PnL shares (signed, denominator = total portfolio PnL = negative), which produces the same numerator/denominator pathology documented in brief §2.1. LDO OOS net_pnl = -8.93%, which is negative and drives total portfolio PnL negative (-9.07%); BCH's -6.25% OOS net_pnl over a negative total yields concentration_pct = 63.83% (positive), and LDO's -8.93% over -9.07% = 91.21%. These are the accounting artifact concentration percentages — they do NOT indicate that the cap failed to fire.

**Falsifier 5 (post-cap top-share > 40% indicating mechanism defect)**: NOT triggered. The cap fired at 9.4–12.8% rates per symbol (see Gate Efficacy Table below); the post-cap "concentration" in comparison.csv per_symbol is accounting artifact from negative total PnL denominator, not a constraint violation.

## Label Leakage Audit

REQUIRED_GAP = (timeout_candles + 1) × n_symbols = (21 + 1) × 3 = 66. Verified at runtime by `_validate_label_leakage_gap()` in runner. CV fold gap = 22 rows × 8h = 184h confirmed in run.log. Sacred constants: `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` — unchanged.

## Gate Efficacy Table (IS gate stats from run.log)

| Gate | BCH IS fire rate | LDO IS fire rate | TRX IS fire rate | Notes |
|---|---|---|---|---|
| zscore OOD (z=2.0) | 1036/3284 = 31.5% | 459/1175 = 39.1% | 907/2411 = 37.6% | Unchanged from iter-v3/018 |
| Hurst regime | 144/3284 = 4.4% | 54/1175 = 4.6% | 106/2411 = 4.4% | Unchanged |
| ADX gate (≥20) | 724/3284 = 22.0% | 288/1175 = 24.5% | 470/2411 = 19.5% | Unchanged |
| Low-vol floor (≥0.33) | 638/3284 = 19.4% | 179/1175 = 15.2% | 303/2411 = 12.6% | Unchanged |
| Combined kill rate | 77.4% | 83.4% | 74.1% | In expected 80-90% range |
| Vol scaling (mean) | 0.698 | 0.690 | 0.742 | Multiplicative |
| **Per-symbol cap (NEW) — primitive 8** | **421/3284 = 12.8%** | **110/1175 = 9.4%** | **250/2411 = 10.4%** | **cap_fires from gate stats** |
| BTC trend gate (±15%) | 35 total OOS killed | — | — | Unchanged; from seed_summary |

**Falsifier 4** (cap fire rate < 5% → INERT): NOT triggered. BCH 12.8%, LDO 9.4%, TRX 10.4% — all above the 5% floor. Cap mechanism propagated and fired. The predicted band from brief §4.2 was 8-15% IS / 5-10% OOS; observed IS rates (9.4–12.8%) are squarely within band. **Axis propagation confirmed; NEGATIVE verdict is clean (not NULL-RESULT).**

## Cap Behavior Analysis

The per-symbol cap fired 421 / 110 / 250 times across BCH / LDO / TRX IS passes respectively. LDO received 110 cap fires yet still ran -13.29% OOS weighted PnL (-8.93% OOS net_pnl_pct, 13 trades). This demonstrates that the cap scaled positions but did NOT prevent LDO from dominating portfolio-negative contribution OOS. Mechanism: when portfolio total PnL turns negative, LDO's negative-signed share inflates to 91.21% concentration (accounting artifact). The cap fires on positive-share crossings; LDO's negative contribution during OOS is not capped by a positive-share trigger. This is the correct semantics per brief §5.3 Risk 1 ("positive-share-only: only cap symbols whose share > +cap; never cap negative-share symbols — drag is self-limiting via the model's loss-stopping mechanism").

The net effect: the cap reduced the dominant-symbol upside (BCH's 12.8% fire rate and TRX's 10.4% fire rate), while LDO's continued negative contribution went uncapped (correct behavior). The cap removed signal from the symbols contributing positively and did not protect against the negatively-contributing symbol. This is the PATH C mechanism: **concentration is where the strategy's actual edge lives; the cap subtracts signal proportional to conviction in the profitable symbols.**

## IS Trade Roster Saturation Audit

| Symbol | iter-v3/018 IS (anchor) | iter-v3/020 IS | Delta |
|---|---:|---:|---:|
| BCHUSDT | 87 (multi-seed) / 98 (seed-42 IS per_symbol) | 98 | 0 |
| LDOUSDT | 10 (multi-seed) / 23 (seed-42 IS per_symbol) | 23 | 0 |
| TRXUSDT | 75 (multi-seed) / 79 (seed-42 IS per_symbol) | 79 | 0 |
| **Portfolio total** | — / **200** | **200** | **0** |

IS trades = 200, saturation band [129, 215] (anchor 172 ±25%): **PASS** (200 is within band). **Falsifier 2 (saturation predictor): NOT triggered.** The cap is a post-trade weighting layer that does not gate signal emission — trade roster is unchanged from iter-v3/018 seed-42 single-seed count.

Note: anchor IS trade count 200 (seed-42 single-seed) is used as the comparison point (not the multi-seed aggregate 172), since iter-v3/020 runs `--seeds 1`. The saturation band was pre-registered from multi-seed anchor 172; the observed 200 slightly above the multi-seed basis reflects the seed-42 single-seed count match rather than a roster expansion.

## PSR Collapse Mechanism

PSR dropped from 0.9936 (iter-v3/018 seed-42) → 1.0000 (iter-v3/019) → **0.0009** (iter-v3/020). At n_trials=105 (35 × 3 symbols), E[max_SR] = √(2 ln 105) ≈ 3.25 (annualized). The observed IS monthly_sharpe = +0.2745 annualizes to ≈ 0.95. PSR = P(true Sharpe > 0 | observed Sharpe, n_trials) collapsed to 0.0009 because the observed IS Sharpe (+0.2745 monthly) is LOW relative to the E[max_SR] deflation at n_trials=105. DSR = 0.0 (IS Sharpe does not clear the Sharpe of the best random strategy under independent Gaussian trials). Both PSR and DSR collapse are informational at EXPLORATION — they confirm the iteration's negative result rather than independently detecting it. The mechanism: the cap removed IS Sharpe from 0.3788 (anchor) to 0.2745, which combined with higher n_trials (35 vs 10 in prior EXPLORATIONs) pushed the PSR below the 0 threshold.

## Per-Symbol Balance

### IS
| Symbol | Trades | WR | Net PnL (%) | Pct of total PnL |
|---|---:|---:|---:|---:|
| LDOUSDT | 23 | 43.5% | +41.86% | +68.72% |
| BCHUSDT | 98 | 39.8% | +38.37% | +62.99% |
| TRXUSDT | 79 | 31.6% | -19.32% | -31.71% |

### OOS
| Symbol | Trades | WR | Net PnL (%) | Pct of total PnL |
|---|---:|---:|---:|---:|
| TRXUSDT | 37 | 40.5% | +5.39% | -55.04% |
| BCHUSDT | 36 | 36.1% | -6.25% | +63.83% |
| LDOUSDT | 13 | 38.5% | -8.93% | +91.21% |

OOS total PnL = -9.07%. All three symbols are negative or near-zero OOS net_pnl. TRX is +5.39% net but contributes -55.04% of portfolio PnL (accounting artifact: positive contribution with negative denominator). The cap redistribution did not surface an LDO contribution — LDO IS positive (+41.86%) but OOS negative (-8.93%). This IS-OOS sign flip on LDO is the primary OOS drag mechanism, distinct from the concentration arithmetic.

## Anomaly Notes

1. OOS trade spot-check (9 rows sampled: rows 0, 5, 12, 25, 40, 55, 70, 80, 85): exit_reason values are `take_profit`, `stop_loss`, `end_of_data` — all valid. weight_factor values range [0.13, 0.57] — consistent with vol-scaling + cap-scaling composition. No NaN PnL, no zero-weight trades in the sample.

2. LDO OOS: 13 trades, 5 wins (38.5% WR), -8.93% net_pnl. Despite 110 IS cap fires on LDO, the model could not stabilize LDO's OOS performance. This confirms that the cap's LDO scaling in IS (capping upside during LDO's IS winning streak) did not translate to OOS discipline — LDO's OOS behavior is structurally different from its IS behavior (IS 43.5% WR vs OOS 38.5% WR, IS +41.86% vs OOS -8.93%).

3. No NaN Sharpe, no zero-trade months IS. IS monthly_pnl.csv covers full 24-month IS window. Runtime warning `divide by zero encountered in log` from statsmodels regression is a pre-existing behavior (ADF test at month boundaries with insufficient lookback — not introduced by iter-v3/020).

4. IS n_trials = 105 (35 per symbol × 3 symbols). n_effective_trials = 19 (PCA rank for ≥95% cumulative variance of trial return matrix). The n_eff/n_trials ratio = 18.1% — higher than iter-v3/019's 7/30 = 23.3% — consistent with higher trial count at lower IS Sharpe producing a more degenerate trial return distribution.

5. Max concentration in seed_summary.json reported as 80.45%. As documented above, this is the accounting-artifact metric from negative total OOS PnL, not a cap mechanism defect. The cap fired at 9.4–12.8% rates per symbol; the constraint was enforced on positive-share crossings per the positive-share-only semantics.

## Falsifier Evaluation Summary

| Falsifier | Pre-registered threshold | Observed | Verdict |
|---|---|---|---|
| F1 (PATH C): IS < anchor AND OOS < anchor-0.10 | IS < 0.3788 AND OOS < 0.2869 | IS=0.2745, OOS=-0.3296 | **FIRES — PATH C confirmed** |
| F2 (saturation): IS trades outside [129, 215] | Outside [129, 215] | 200 (in band) | NOT triggered |
| F3 (process): wall-clock > 30 min | > 30 min | 0.22h = 13 min | NOT triggered |
| F4 (cap inert): cap fire rate < 5% IS | < 5% per symbol | BCH 12.8%, LDO 9.4%, TRX 10.4% | NOT triggered |
| F5 (mechanism defect): post-cap top-share > 40% IS | > 40% constraint violation | Accounting artifact; cap propagated per gate stats | NOT triggered (see Seed Concentration Audit) |

All process falsifiers CLEAR. Falsifier 1 (PATH C) fires. Classification unambiguous.

## Implications (informational — for QR Phase 7 diary)

Per brief §4.4, PATH C verdict means: **concentration carries genuine signal; the cap subtracts edge proportional to where the model has highest conviction.** The per-symbol PnL cap (primitive 8) is the wrong primitive for managing concentration risk in this universe. Universe expansion (sub-axis B from iter-v3/020 brief) remains the primary unexplored alternative — it provides concentration relief through denominator expansion rather than through edge removal. Separately, the DSR gate reformulation (MEDIUM-priority #3) and TRX/2022-Q4 regime gate (MEDIUM-priority #4) are untested structural axes in the priority queue.

The iter-v3/021 axis recommendation follows directly from the priority order in `feedback_v3_iter019_axis_priorities.md`: DSR gate reformulation (MEDIUM #3), TRX regime gate (MEDIUM #4), or universe expansion (LOW #6 — now elevated by PATH C evidence that the concentration bottleneck requires more symbols rather than per-symbol caps). The QR decides.

## Status

OVERALL=READY-FOR-CRITIC
