---
name: quant-iteration
description: "Quant research/engineering iteration workflow for the crypto-trade LightGBM strategy. Use this skill whenever the user mentions: starting an iteration, quant researcher, quant engineer, research brief, iteration diary, baseline comparison, merge decision, Phase 1-8, EDA on candle data, labeling strategy, feature engineering for the trading bot, running a backtest, evaluating backtest results, in-sample, out-of-sample, OOS cutoff, or comparison.csv. Also trigger when the user says 'start iteration', 'run phase', 'evaluate reports', 'write diary', 'merge decision', or references ITERATION_PLAN_8H.md or BASELINE.md."
---

# Quant Iteration Skill

## Mission

Crypto markets are the most inefficient markets on earth. They trade 24/7 across fragmented venues populated by retail speculators, algorithmic bots with misaligned incentives, and institutions constrained by mandates that have nothing to do with price discovery. Fear and greed oscillate on 8-hour cycles. Liquidation cascades create mispricings that would be arbitraged away in seconds in equities but persist for hours in crypto futures. Funding rates distort positioning. Social media narratives move billions.

Our edge is systematic patience. We use LightGBM on 8-hour candles — a timeframe slow enough to avoid microstructure noise, fast enough to capture the behavioral patterns that human traders create and perpetuate. We do not predict the future. We identify moments when the distribution of forward returns is skewed in our favor, and we bet accordingly, sized by our conviction and disciplined by our risk framework.

The market's irrationality is our opportunity. Volatility is not risk — it is the raw material of profit. Every liquidation cascade, every panic sell, every euphoric FOMO spike creates a statistical edge for the patient, systematic trader who has done the work to distinguish signal from noise.

We build strategies that would survive scrutiny by the most rigorous quantitative finance researchers. No p-hacking. No overfitting to backtest. No self-deception. If a strategy cannot withstand combinatorial purged cross-validation, deflated Sharpe ratio tests, and out-of-sample evaluation on data the researcher never saw, it does not trade.

117+ iterations have taught us what does not work. That knowledge is as valuable as what does.

---

This skill governs the iterative research/engineering workflow for building and improving the crypto-trade LightGBM strategy on 8h candles.

## Before You Start

Read `ITERATION_PLAN_8H.md` at the repo root. It contains the full plan with templates, baseline rules, and phase details. This skill is a quick-reference companion, not a replacement for the plan.

### Default Flow: Full Autopilot

When this skill is triggered, **do NOT ask which role to play or whether to proceed**. Default behavior:
1. Read the last diary's "Next Iteration Ideas" and BASELINE.md
2. Determine the next iteration number
3. Run the full flow: QR Phases 1-5 → QE Phase 6 → QR Phases 7-8
4. **After completing Phase 8 (diary + commit), immediately start the next iteration** — go back to step 1 with the new diary's "Next Iteration Ideas"
5. Keep looping iterations until the user intervenes or context runs out
6. Only pause if there's an actual blocker (ambiguous brief, unexpected error, decision that genuinely requires user input)

The user can override by specifying a role (e.g., "be the QR") or a phase (e.g., "run Phase 6"). Otherwise, go.

## NO CHEATING — ABSOLUTE RULES

**NEVER** do any of the following to improve metrics artificially:
- **NEVER change `start_time`** to skip bad IS months. The backtest MUST run from the earliest available data. Trimming the evaluation window is CHEATING — it hides losses instead of fixing the strategy.
- **NEVER cherry-pick date ranges** to make IS or OOS look better.
- **NEVER post-hoc filter trades** from the results to improve metrics.
- **NEVER tune parameters on OOS data** (the researcher sees OOS only in Phase 7).
- **NEVER allow labels to leak across CV fold boundaries.** The `gap` parameter in `TimeSeriesSplit` MUST be set correctly: `gap = (timeout_candles + 1) * n_symbols`. The QE MUST verify this in EVERY iteration by reviewing the CV setup in `optimization.py`. This is non-negotiable — iter 089 proved that leaked labels inflate CV Sharpe by 5-10x.
- **NEVER allow labels to leak from live/prediction data to training data.** In the walk-forward backtest, each month's model trains ONLY on past klines. Labels for training samples must not scan past the training window boundary.

To improve IS Sharpe: improve the STRATEGY (features, model, labeling) — not the measurement window. A strategy that only works from 2023 onward is NOT robust.

---

## THE MOST IMPORTANT RULE: IS/OOS Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

This split exists to prevent **researcher overfitting** — not model leakage. The walk-forward backtest already prevents model-level leakage by training only on past data each month.

### What the split means:

- The **Quant Researcher** uses ONLY IS data (before 2025-03-24) during Phases 1-5 (design). This prevents the researcher from unconsciously tuning features, labeling, parameters to fit recent patterns.
- The **walk-forward backtest runs on ALL data** (IS + OOS) as one continuous process. No artificial wall at the model level. The backtest rolls through OOS exactly as it would in live trading.
- The **reporting layer** splits trade results at `OOS_CUTOFF_DATE` into `in_sample/` and `out_of_sample/` report directories plus a `comparison.csv` with OOS/IS ratios.
- The **Quant Researcher** sees OOS results for the FIRST time in Phase 7 (evaluation).

The IS/OOS gap in `comparison.csv` tells you whether the researcher's design choices generalize beyond the data they could see.

This constant lives in `src/crypto_trade/config.py`.

## Two Roles

You operate as EITHER the Quant Researcher (QR) OR the Quant Engineer (QE) for each phase. In autopilot mode (default), you switch roles automatically between phases — QR for phases 1-5 and 7-8, QE for phase 6. No need to ask.

### Quant Researcher (QR)
- Owns: data analysis, labeling decisions, symbol selection, filtering, feature design, evaluation, diary
- Produces: research briefs, diary entries, evaluation decisions
- Does NOT: write production code in `src/`. Uses notebooks and analysis scripts only
- DATA ACCESS: IS data only during Phases 1-5. Sees OOS reports only in Phase 7

### Quant Engineer (QE)
- Owns: production Python code, pipeline architecture, backtest engine, report generation
- Produces: implementation in `src/`, engineering reports, backtest reports (IS + OOS report batches)
- Does NOT: make research decisions. If the research brief is ambiguous, stop and ask
- BACKTEST: runs walk-forward on full dataset, then splits reports at OOS_CUTOFF_DATE

## Git Workflow — Non-Negotiable

### Starting
```bash
git checkout main && git pull
git checkout -b iteration/NNN
```

### Commit Discipline
Separate documentation from code. NEVER mix them in the same commit.

1. Code commits → prefix `feat(iter-NNN):` or `fix(iter-NNN):`
2. Research brief → single commit: `docs(iter-NNN): research brief`
3. Engineering report → single commit: `docs(iter-NNN): engineering report`
4. Diary entry → LAST commit on branch: `docs(iter-NNN): diary entry`

Why: failed iterations cherry-pick commits 2, 3, 4 to main. If diary is mixed with code, cherry-pick breaks.

### Merge Decision

After QR writes the diary with MERGE or NO-MERGE decision:

**MERGE** (iteration beats baseline):
```bash
git checkout main
git merge iteration/NNN --no-ff -m "merge(iter-NNN): [summary]"
# Update BASELINE.md with new IS and OOS metrics
git add BASELINE.md
git commit -m "baseline: update after iteration NNN"
git tag -a v0.NNN -m "Iteration NNN: OOS Sharpe X.XX, MaxDD Y.Y%"
```

**NO-MERGE** (iteration is worse):
```bash
git checkout main
git cherry-pick <research-brief-commit>
git cherry-pick <engineering-report-commit>
git cherry-pick <diary-commit>
# Branch stays — never delete iteration branches
```

**First iteration** (no baseline exists): always merge to main. It becomes the initial baseline.

### What Is Tracked

| Location | Tracked | Merges to main |
|----------|---------|----------------|
| `src/`, `tests/` | Yes | Only on MERGE |
| `diary/` | Yes | Always (cherry-pick or merge) |
| `briefs/` | Yes | Always (cherry-pick or merge) |
| `BASELINE.md` | Yes | Updated only on MERGE |
| `notebooks/` | Yes (strip outputs first) | Only on MERGE |
| `reports/` | No (.gitignore) | Never |
| `models/` | No (.gitignore) | Never |
| `analysis/` | No (.gitignore) | Never |
| `data/` | No (.gitignore) | Never |

Before committing notebooks: `uv run jupyter nbconvert --clear-output --inplace notebooks/*.ipynb`

## Phase Quick Reference

| Phase | Role | Data Access | Input | Output |
|-------|------|-------------|-------|--------|
| 1. EDA | QR | IS only | Parquet data | `briefs/iteration_NNN/research_brief_phase1.md` |
| 2. Labeling | QR | IS only | Phase 1 findings | `briefs/iteration_NNN/research_brief_phase2.md` |
| 3. Symbol Universe | QR | IS only | Phase 1 findings | `briefs/iteration_NNN/research_brief_phase3.md` |
| 4. Data Filtering | QR | IS only | Phase 1 findings | `briefs/iteration_NNN/research_brief_phase4.md` |
| 5. Brief Compilation | QR | IS only | Phases 1-4 | `briefs/iteration_NNN/research_brief.md` (single commit) |
| 6. Implementation | QE | Walk-forward on ALL data; reports split at cutoff | Research brief | Code, IS reports, OOS reports, comparison.csv, engineering report |
| 7. Evaluation | QR | IS + OOS reports (first time seeing OOS) | Reports + BASELINE.md | Merge decision |
| 8. Diary | QR | — | Evaluation | `diary/iteration_NNN.md` (last commit on branch) |

For subsequent iterations (not the first), the scope of phases 1-4 depends on iteration history:
- **After a MERGE**: Phases 1-4 may be partially skipped if the diary's "Next Iteration Ideas" only calls for changing one variable. The QR must still complete at least **2 categories** from the Research Checklist (see below).
- **After 3+ consecutive NO-MERGE iterations on the same model track**: Phases 1-4 are **MANDATORY**. The QR must complete at least **4 of 8 categories** from the Research Checklist (A-H). No skipping.
- **After an EARLY STOP**: Same as 3+ NO-MERGE — full research mandatory. Parameter-only changes are **banned**.

The research brief (Phase 5) is always required, and Section 0 (Data Split) is always included verbatim.

## Seed Robustness Validation (MANDATORY before MERGE)

When an iteration produces a MERGE-worthy result, the QE MUST validate it is NOT seed-dependent before merging:

1. Re-run the SAME configuration with **5 different seeds** (e.g., 42, 123, 456, 789, 1001)
2. Compute the **mean and std of OOS Sharpe** across all seeds
3. The iteration merges ONLY if:
   - **Mean OOS Sharpe > 0** (profitable on average)
   - **At least 4 of 5 seeds are profitable** (OOS Sharpe > 0)
4. Report the seed sweep results in the engineering report and diary

This was learned in iter 038: seed=42 gave OOS Sharpe +1.33, but seed=123 gave -1.15. Without seed validation, we'd believe the strategy was 3x better than it actually is.

## Symbol Addition Validation (MANDATORY before MERGE with new symbols)

When an iteration adds new symbol(s) to the universe, the QE MUST validate stability:

1. Run the configuration with the new symbol(s) included AND excluded (A/B test)
2. Compare per-symbol metrics for existing symbols (BTC, ETH):
   - WR must not degrade by more than 2pp
   - Sharpe must not degrade by more than 15%
3. Each new symbol's per-symbol metrics must show:
   - WR above break-even (33.3% for 8%/4%)
   - At least 20 OOS trades
   - Positive net PnL in OOS
4. Portfolio-level check:
   - No single symbol > 50% of OOS PnL (relaxed from 30% during expansion phase)
   - Total OOS Sharpe >= baseline × 0.95 (allow 5% Sharpe sacrifice for diversification)
5. Report the A/B comparison in the engineering report and diary

### Seed Parity on Model Add/Replace — NON-NEGOTIABLE

When an iteration ADDS a new model or REPLACES an existing one in the portfolio, the new model must be validated using the **same seed structure** as the models already in the portfolio. What "same" means depends on the architecture:

**Ensemble architecture (current baseline)** — Models A, C, D each train with `ensemble_seeds=[42, 123, 456, 789, 1001]` (5 inner seeds per monthly training, averaged). A new model satisfies parity if it uses the **same inner ensemble seed list**. The outer `self.seed` parameter on `LightGbmStrategy` is unused in this configuration (`lgbm.py:424` falls through `ensemble_seeds or [self.seed]`), so outer-seed sweeps produce bit-identical runs and have no power to validate anything (learned in iter-166).

**Single-seed architecture (legacy / per-candidate screens)** — if a runner uses `ensemble_seeds=None` or `ensemble_seeds=[single_value]`, the outer `seed=` parameter IS live. In that case, sweeping outer seeds {42, 123, 456, 789, 1001} with `yearly_pnl_check=True` is the correct stability test.

Workflow for a new/replacement model in the ensemble architecture:
1. Cheap Gate 1–2 checks (data quality, liquidity).
2. Gate 3 stand-alone screen with the same `ensemble_seeds` as the portfolio's existing models; fail-fast on.
3. If Gate 3 passes, merge on those numbers — no outer-seed sweep is needed because the ensemble is itself the variance-reduction mechanism.

Workflow for a single-seed candidate or architectural deviation:
1. Same Gates 1–3 at the first seed.
2. Four additional runs at the remaining outer seeds. Fail-fast each.
3. Merge only if ≥ 4 of 5 seeds show OOS Sharpe > 0 AND mean OOS Sharpe > 0.

This rule prevents "coasted" merges where a new model joins an over-validated portfolio on under-validated evidence **and** also prevents the dual pitfall of running redundant sweeps against dead-code RNG sources.

## Feature Normalization Awareness

When using a pooled model across multiple symbols with different price scales, the QR and QE must ensure features are **scale-invariant**:

- **SAFE features** (already normalized): RSI, Stochastic, %B, z-scores, returns (%), NATR, ratios, oscillators, boolean crosses
- **UNSAFE features** (price-scale dependent): raw SMA, raw EMA, raw ATR, raw VWAP, raw OBV, raw A/D, raw volume, raw Bollinger Band levels
- **LightGBM note**: Tree-based models are less sensitive to scale than linear models, but large absolute values (BTC price ~60K vs small-cap ~0.01) can still cause split-point issues

When proposing new features, the QR should prefer normalized/ratio-based features. When the model uses raw price-level features (SMA, EMA, VWAP), understand that these only work well within a single symbol or among symbols with similar price scales.

## Feature Count Discipline

**Fewer features = more stable models.** This is a key lesson from 117 iterations — but it is model-specific.

- **For new/small models** (<80 features, samples/feature >80): Target 30-50 features. Explicit pruning is effective (iter 117: meme model pruned 67→45, OOS Sharpe doubled from +0.29 to +0.66).
- **For mature co-optimized models** (100+ features, Optuna-tuned over many iterations): Explicit pruning destroys co-optimization. Use `colsample_bytree` for implicit selection instead. (Iter 094: pruning BTC/ETH to 50 features → IS Sharpe -1.46, catastrophic.)
- **Hard ceiling**: Never exceed 200 features without explicit justification
- **Samples-per-feature ratio**: Must stay above 50. With 4,400 samples and 50 features = ratio 88 (healthy). With 198 features = ratio 22 (dangerous)
- **Every added feature must displace a worse one.** Net feature count should decrease or stay flat, never balloon

## Feature Reproducibility — NON-NEGOTIABLE

Every iteration runner MUST pass an explicit `feature_columns` list to
`LightGbmStrategy`. Auto-discovery from Parquet schemas is **disabled at the code
level** — `LightGbmStrategy` raises `ValueError` if `feature_columns` is empty or
`None`. This rule is non-negotiable because auto-discovery caused a silent
divergence between the live engine and the backtest in April 2026 (iter-162's
entropy/CUSUM features were silently picked up, producing different trades from
the baseline).

Rules:
- **Runner declares the list**: every `run_iteration_NNN.py` / baseline runner
  must specify `feature_columns=[...]` (or import one of the canonical lists,
  e.g. `BASELINE_FEATURE_COLUMNS` from `src/crypto_trade/live/models.py`).
- **Parquet is the source of data, not the source of truth for columns**: new
  features can exist in the parquet without being used by an iteration. The
  iteration explicitly selects its inputs.
- **Canonical lists live in code, not in the parquet**: when a feature set is
  meant to be reused across iterations or environments, define it as a constant
  (like `BASELINE_FEATURE_COLUMNS`) and reference it.
- **When adding new features**: add them to the parquet via the feature pipeline,
  but do NOT use them in any iteration until the runner explicitly adds them to
  `feature_columns`. This keeps existing iterations reproducible even as the
  parquet schema evolves.
- **QE must verify in every iteration**: the engineering report states which
  `feature_columns` constant or literal list was passed, and confirms its length.

### Anti-patterns (learned the hard way)
- Iter 083: Added 85 features (113→198) without pruning — wrong direction
- Iter 078: 185 features with halved training data (per-symbol) — ratio 21, catastrophic overfitting
- Iter 094: Pruning BTC/ETH from 185→50 features destroyed co-optimization, IS Sharpe -1.46
- Iter 117: Pruning meme model from 67→45 features improved OOS Sharpe from +0.29 to +0.66

---

## LABEL LEAKAGE PREVENTION — NON-NEGOTIABLE

### The Rule

Labels MUST NOT leak across ANY boundary:
1. **CV fold boundaries** — training labels cannot see validation-period prices
2. **Walk-forward boundaries** — training labels cannot see future klines
3. **Live prediction** — the model predicts one step at a time, never trained on future data

Violation of this rule invalidates ALL metrics. Iter 089 proved leaked labels inflate CV Sharpe by **5-10x**. The QE MUST audit label leakage in EVERY iteration.

### CV Label Leakage: The Problem

Triple-barrier labels scan forward up to `timeout_minutes / candle_minutes` candles (e.g., 10080 / 480 = 21 candles for 7-day timeout on 8h). When training data is pooled across N symbols, the feature array interleaves symbols — so 21 candles of leakage per symbol = `21 * N` rows.

If a training sample's label scans into the validation fold, the model trains on information from the validation period. This is invisible but devastating.

### CV Label Leakage: The Fix

Use `TimeSeriesSplit` with a computed `gap` parameter:

```python
gap = (label_timeout_minutes // interval_minutes + 1) * n_symbols
tscv = TimeSeriesSplit(n_splits=cv_splits, gap=gap)
```

This excludes training samples whose labels could reach into the validation fold. The gap is **dynamic** — computed from the actual timeout, interval, and symbol count in `lgbm.py._train_for_month()`.

**Example**: 8h candles, 7-day timeout, 2 symbols → gap = (10080/480 + 1) * 2 = **44 rows**. Data loss: ~1% per fold boundary — negligible.

### Walk-Forward Label Leakage

The walk-forward backtest trains each month's model on a window of past data. The labeling function receives only klines within that window, so it cannot scan past the window boundary. This is correct by construction — but verify it hasn't been broken by code changes.

### What Failed: PurgedKFoldCV (iter 089-090)

A custom `PurgedKFoldCV` class (purge_window=21, embargo_pct=0.02) was tried. It removed ~4% of data per fold + embargo, which combined with Optuna's `training_days` parameter to create empty folds. IS Sharpe collapsed to -1.32 (iter 089) and -1.00 (iter 090). The approach was theoretically correct but practically catastrophic.

The `TimeSeriesSplit(gap=...)` solution (iter 091) achieves the same leakage prevention with ~1% data loss and zero complexity.

---

## Sample Weights: Uniqueness + Time Decay (AFML Ch. 4)

### The Overlap Problem

Triple barrier labels with timeout=7 days mean each label's outcome depends on the next 21 candles (168h / 8h). When two adjacent samples both have labels spanning the same future period, they are not independent observations. The current system (at `labeling.py:245-248`) treats them as independent, which inflates the effective sample size and causes the model to overweight periods with many overlapping labels.

### Uniqueness Weighting

For each sample i with label window [t_i, t_i + timeout]:
1. Compute c_t = number of active labels at each timestamp t within [t_i, t_i + timeout]
2. Uniqueness(i) = mean(1/c_t) for all t in [t_i, t_i + timeout]
3. Samples with fewer concurrent labels get higher uniqueness (closer to 1.0)
4. Samples during crowded periods (many overlapping labels) get lower uniqueness

### Combined Weight Formula

```
final_weight(i) = uniqueness(i) * time_decay(i) * abs_pnl_weight(i)
```

Where:
- **uniqueness(i)**: from the overlap computation above
- **time_decay(i)**: exponential decay with half-life = training_months / 2 (e.g., 12 months for a 24-month window). Most recent samples get weight ~1.0, oldest get weight ~0.25
- **abs_pnl_weight(i)**: the current |PnL| weight normalized to [1, 10] (kept)

### Implementation

Add `compute_sample_uniqueness()` to `src/crypto_trade/strategies/ml/labeling.py`. Input: candidate_indices, timeout_minutes, open_time array. Output: uniqueness weights array (same length as labels). Multiply with existing weights before passing to LightGBM's `sample_weight` parameter.

---

## Fractional Differentiation (AFML Ch. 5)

### The Stationarity-Memory Tradeoff

Most financial features face a tradeoff:
- **Returns (d=1.0)**: Stationary but memoryless. Yesterday's return tells you nothing about today's price level.
- **Prices (d=0.0)**: Maximum memory but non-stationary. Split points learned in 2021 (BTC at $40K) are meaningless in 2024 (BTC at $70K).

Fractional differentiation finds the minimum `d` that achieves stationarity while preserving as much memory as possible. This is one of the most impactful techniques in AFML.

### Implementation for 8h Candle Features

1. **New feature module**: `src/crypto_trade/features/fracdiff.py`
2. **Apply to**: log(close), log(volume), OBV, cumulative taker_buy_ratio
3. **Method**: Fixed-window fracdiff with window=100 candles (800 hours ~ 33 days)
   - For each series, find minimum d where ADF test p-value < 0.05
   - Typical d for crypto prices: 0.3-0.5 (vs d=1.0 for returns)
   - Use the `fracdiff` Python package or implement FFT-based weights
4. **Feature names**: `fracdiff_close_d{d}`, `fracdiff_volume_d{d}`, etc.
5. **Expected benefit**: Features that are both stationary (safe for LightGBM) AND retain long-term trend information (unlike returns)

### Why This Matters for 8h Candles

On 8h candles, a lookback of 100 candles = 33 days. Fractionally differentiated close prices with d~0.4 would preserve information about the price trajectory over the last month while remaining stationary. This is exactly the kind of feature that captures regime persistence — a rising market at d=0.4 retains the "memory" that prices have been trending up, something that 1-period returns completely lose.

### Practical Notes

- The `fracdiff` package (`pip install fracdiff`) provides `fracdiff.fdiff()` which handles the FFT-based computation efficiently
- With ~4,400 samples per training window, adding 3-4 fracdiff features (close, volume, OBV, taker_ratio) is well within the feature budget
- These should REPLACE some raw statistical features (e.g., redundant return periods), not add to them — net feature count stays flat

---

## Baseline Comparison Rules

Read `BASELINE.md` on main before evaluating. An iteration merges ONLY if:

1. **Minimum quality bars** (both must pass, absolute — not relative to baseline):
   - **OOS Sharpe > 1.0**
   - **IS Sharpe > 1.0**
   These floors exist because a Sharpe below 1.0 in either half is too
   weak to deploy confidently, regardless of how it compares to the
   previous baseline. A candidate that "beats baseline" by pushing
   baseline OOS from +0.95 to +0.98 is NOT a merge — both halves must
   clear 1.0 first.
2. **Primary**: OOS Sharpe > current baseline OOS Sharpe
3. **Hard constraints** (all must pass):
   - Max drawdown (OOS) ≤ baseline OOS max drawdown × 1.2
   - **Trade-rate floor**: OOS ≥ 10 trades/month (→ ≥ 130 total over
     the ~13-month OOS window) AND IS ≥ 10 trades/month
     (→ ≥ 400 total over the ~39-month IS window). Sharpe computed on
     too few trades is dominated by individual outcomes and cannot be
     trusted. Filters that raise Sharpe by starving the strategy (R3
     OOD, high-confidence thresholds, vol kill-switches) must clear
     this floor.
   - **Relative trade-count floor**: OOS trade count must not drop more
     than ~40% vs. the baseline being compared against. (If the filter
     is more aggressive than that, re-calibrate on IS, do not push
     further.)
   - Minimum 50 OOS trades (legacy floor; subsumed by the rate floor
     above for the current portfolio but kept for per-symbol screens).
   - Profit factor > 1.0 (OOS)
   - No single symbol > 30% of total OOS PnL
   - IS/OOS Sharpe ratio > 0.5 (researcher overfitting gate)

If the minimum quality bars fail → NO-MERGE, full stop. If primary or
hard constraints fail but the 1.0 floors hold → NO-MERGE with trade-off
documented in the diary.

**Diversification exception**: If an iteration adds new symbol(s) and:
- BOTH Sharpe floors (IS > 1.0, OOS > 1.0) still hold
- OOS Sharpe is within 5% of baseline (>= baseline × 0.95)
- OOS MaxDD improves by > 10%
- The 30% concentration constraint improves (moves closer to passing)
- All other hard constraints pass

Then the QR MAY recommend MERGE with justification, even if OOS Sharpe does not strictly
improve. Diversification has long-term value that single-period Sharpe does not capture.
The IS/OOS Sharpe > 1.0 floors are NEVER waived by this exception. Justification must be
explicit in the diary.

## Risk Mitigation Design — MANDATORY for every MERGE candidate

### Why this is its own phase

The walk-forward backtest measures expected performance under the training
distribution. It does NOT test the model's behaviour when the distribution
shifts — black swans, post-crisis regimes, liquidity crunches, exchange
failures, exogenous macro shocks. These events are by definition not in the
training data (or they are extreme outliers), and the model does not know to
be cautious. Left unchecked, it can generate cascades of losses as it
confidently signals trades the market punishes.

Iter 172's DOT analysis is the canonical motivating case. DOT in Dec 2022
took 6 consecutive LONG stop-losses on a persistent downtrend (entries at
5.538 → 5.293 → 5.061 → 4.705 → 4.602 → 4.486) for −26% before the model's
7th attempt finally hit a TP. A simple "3 consecutive SLs → pause N candles"
rule would have prevented trades 4, 5, 6, cutting the loss by more than half.
LTC in the same month, with the same regime, took only 3 trades because its
Optuna-tuned threshold was naturally more conservative — LTC "got lucky"
with a built-in defensive reflex. DOT had no equivalent protection.

**Before any iteration can merge, the QR must run the Risk Mitigation
Analysis below and propose (or verify existing) protective mechanisms.**

### Required Risk Mitigation Analyses

Each analysis uses IS data only and produces numerical evidence. At minimum
THREE of the following five categories must be completed in the research
brief for a merge-candidate iteration:

#### R1. Consecutive-loss cool-down calibration

Walk through IS trades.csv for each model. For every trade, compute the
number of consecutive SLs immediately preceding it (reset on TP or timeout).
Bucket trades by preceding-SL-streak length (0, 1, 2, 3, 4+). Report:

- Count of trades per bucket
- WR in each bucket
- Mean PnL in each bucket

**If WR drops monotonically with streak length (common)**, a cool-down rule
is justified. Pick the streak threshold K where bucket K's WR falls below
break-even. Propose: `after K consecutive SLs, pause trading on this symbol
for N candles`. Calibrate N by measuring how long adverse periods typically
last (e.g., 75th percentile of SL-streak duration in candles).

#### R2. Drawdown-triggered position scaling

Compute rolling 30-day / 60-day drawdown from running peak weighted-PnL.
Correlate drawdown depth with the next 10-trade WR. If trades taken during
deep drawdowns have lower WR, propose a position-size reduction: when
rolling drawdown exceeds X%, scale new trades by factor F < 1 until the
drawdown recovers.

Calibrate X and F from the IS evidence, not intuition. A candidate
framework: `weight_factor *= max(0.33, 1 - drawdown_pct / 60%)`.

#### R3. Out-of-distribution feature detection

Compute the IS distribution of each top-20 feature (or all 193 for pooled
models). For each live-candle's feature vector, compute a Mahalanobis-like
z-score against the trailing 24-month IS distribution. If any feature's
z-score is > 3 (or the aggregate OOD score exceeds a threshold), the
candidate is out-of-distribution — skip the trade.

This is the cleanest "black swan" detector: the model hasn't seen these
feature values before, so we don't trust its predictions. IS calibration:
count how often this trigger would fire per month historically, ensure
false-positive rate is < 10% of trades.

#### R4. Realized-volatility regime kill-switch

Compute per-symbol realized volatility (log-returns std over rolling 14-day
window) on IS data. Define a "vol regime" as extreme when the symbol's
realized vol exceeds the 95th percentile of its training-window distribution.
Measure: in historical extreme-vol months, what was the model's WR vs. the
non-extreme baseline?

**Important nuance** (learned iter 172): DOT's Dec 2022 catastrophe was in a
LOW-vol regime (BTC 30d vol 28%, vs. 65% in Sep 2022 when DOT was profitable).
A naive "high vol = pause" rule is wrong. If low-vol regimes after crashes
are the danger, flip the rule or use a drawdown-augmented indicator instead.

#### R5. Cross-model portfolio risk balance

For portfolios with 2+ models, examine the running per-symbol PnL share.
If any one symbol's weighted PnL contribution exceeds X% of the portfolio
total across a trailing window, propose portfolio-level rebalancing
(reduce weight on the concentrated symbol, increase on others). This is
the "never let one model dominate" constraint turned into a runtime
mitigation, not just an ex-post merge check.

### Implementation Hint — BacktestConfig risk controls

The backtest engine should accept (not yet implemented; iter-NNN task):

```python
BacktestConfig(
    ...
    risk_consecutive_sl_limit: int | None = None,  # R1
    risk_consecutive_sl_cooldown_candles: int = 0,
    risk_drawdown_scale_enabled: bool = False,     # R2
    risk_drawdown_scale_floor: float = 0.33,
    risk_ood_zscore_threshold: float | None = None,  # R3
    risk_vol_regime_threshold_pctile: float | None = None,  # R4
    risk_concentration_soft_cap: float | None = None,  # R5
)
```

Default all None / False so existing baselines are unchanged until a merge
explicitly introduces a risk control.

### Evidence Requirements

As with the rest of the QR Research Checklist, each R-category claimed as
completed must include:

- A numerical table from IS data (bucketed WR, correlation coefficient,
  z-score distribution, etc.)
- The proposed threshold, calibrated on IS evidence
- A backtest-like simulation of what the mitigation would have done on IS
  trades: "Applying R1 with K=3, N=18 candles to iter-172 DOT trades reduces
  2022 cumulative PnL from −19.1% to −4.7%"

A merge iteration that adds a risk control without this evidence is not
permitted. A merge iteration that skips risk mitigation entirely is only
allowed on grounds of "no new mechanism needed — existing controls already
address the identified risks", which itself must be justified against at
least R1 and R2 evidence.

### Worked example: DOT Dec 2022 (R1)

From iter-168 partial trades.csv, DOT Dec 2022 SL streak:

| Trade # | Date       | Result            | SL streak entering |
|---------|------------|-------------------|--------------------|
| 1 | 2022-12-05 | SL (−4.31) | 0 |
| 2 | 2022-12-08 | SL (−4.11) | 1 |
| 3 | 2022-12-13 | SL (−3.81) | 2 |
| 4 | 2022-12-17 | SL (−5.36) | 3  ← would trigger |
| 5 | 2022-12-20 | SL (−4.67) | 4  (still in cool-down) |
| 6 | 2022-12-23 | SL (−4.39) | 5  (still) |
| 7 | 2022-12-29 | TP (+7.54) | 6  (cool-down expires, trade allowed) |

Applying R1 with K=3, N=18 candles (6 days at 8h): trades 4, 5, 6 are
filtered out (they opened within 6, 9, 12 days of the triggering SL
respectively, all < 18). Trade 7 opens 12 days after the triggering SL —
**exceeds** the 18-candle cool-down? 12 days × 3 candles/day = 36 candles.
Wait — 18 candles = 6 days. Trade 7 opens 16 days after the K-triggering
event (Dec 13 → Dec 29). 16 days = 48 candles, well past the cool-down.
So trade 7 is allowed.

Effect: Dec 2022 goes from 7 trades (−19.11%) to 4 trades (−12.23 + 7.54 =
−4.69%). Year-1 sum: +10.99 + 1.63 − 4.69 = +7.93% (from −6.49% baseline,
a +14.4 pp swing). **DOT passes year-1 with R1 active.**

This is exactly the kind of quantitatively-calibrated mitigation the QR
is now required to propose for every merge-candidate iteration.

## Overfitting Quantification (AFML Ch. 11-12)

### Deflated Sharpe Ratio (DSR)

After 117+ iterations, the probability that the best OOS Sharpe is a statistical fluke increases with each trial. The Deflated Sharpe Ratio adjusts for multiple testing:

- **N** = number of independent trials (iterations)
- **E[max(SR_0)]** = expected maximum Sharpe under the null (all trials random)
- **DSR** = (SR_observed - E[max(SR_0)]) / SE(SR)

Formula: `E[max(SR_0)] ~ sqrt(2 * ln(N)) * (1 - gamma / (2 * ln(N))) + gamma / sqrt(2 * ln(N))` where gamma ~ 0.5772 (Euler-Mascheroni constant).

**If DSR < 0**, the observed Sharpe is likely explained by multiple testing alone.

**Implementation**: Add `compute_deflated_sharpe()` to `backtest_report.py`. Inputs: observed OOS Sharpe, number of iterations, OOS trade count, skewness and kurtosis of OOS returns. The QR must report DSR in every diary entry alongside raw Sharpe.

### Probability of Backtest Overfitting (PBO)

When using CPCV (15 paths from N=6, k=2):
1. For each trial (Optuna configuration), collect the 15 path Sharpe ratios
2. Rank the paths: for each path, rank the trial's Sharpe among all trials
3. PBO = fraction of paths where the best in-sample trial ranks below median out-of-sample
4. PBO > 0.5 -> more likely than not that the backtest is overfit

**Practical application**: Run PBO on the final monthly model. If PBO > 0.5 for more than 30% of months, the strategy's IS performance is unreliable.

### Application to the 117-Iteration Problem

With N=117 trials and baseline OOS Sharpe +1.01:
- E[max(SR_0)] ~ sqrt(2 * ln(117)) ~ 3.08 (expected max Sharpe under random)
- The observed +1.01 is far BELOW the expected random maximum
- This means DSR < 0 — the baseline Sharpe is within the range expected from 117 random trials

This is sobering but important. It does NOT mean the strategy has no signal (IS Sharpe +0.73 is consistent). But achieving statistical significance through individual iterations is extremely unlikely at N=117. The productive path is to: (1) reduce independent trials (fewer, bolder iterations), (2) focus on portfolio-level metrics across multiple models, and (3) validate via out-of-distribution regimes rather than DSR alone.

---

## Backtest Report Structure

```
reports/iteration_NNN/
├── in_sample/           # Trades with entry_time < 2025-03-24
│   ├── quantstats.html
│   ├── trades.csv
│   ├── daily_pnl.csv
│   ├── monthly_pnl.csv
│   ├── per_regime.csv
│   ├── per_symbol.csv
│   └── feature_importance.csv
├── out_of_sample/       # Trades with entry_time >= 2025-03-24
│   ├── quantstats.html
│   ├── trades.csv
│   ├── daily_pnl.csv
│   ├── monthly_pnl.csv
│   ├── per_regime.csv
│   └── per_symbol.csv
└── comparison.csv       # Side-by-side metrics with OOS/IS ratios
```

The comparison.csv is the first thing the QR opens in Phase 7. OOS/IS Sharpe ratio < 0.5 = researcher overfitting. > 0.9 = suspiciously good, check for bugs.

## Fail Fast Protocol — AGGRESSIVE

We are looking for a GOOD model, not an almost-break-even model. Time is the most valuable resource. Kill bad strategies fast.

### Yearly Checkpoints

The training window is **24 months maximum** (covers both bull and bear markets). The model starts predicting after 24 months of training data (first predictions ≈ Jan 2022). Check performance **at the end of each calendar year**:

**Year 1 checkpoint** (after ~12 months of predictions):
- If cumulative PnL is negative → **STOP IMMEDIATELY**
- If WR < 33% (below break-even) → **STOP IMMEDIATELY**
- A good model should be profitable from year 1. Period.

**Year 2 checkpoint** (after ~24 months):
- If cumulative PnL across years 1+2 is negative → **STOP**
- If any individual year has WR < 30% → **STOP**

**Implementation**: The QE adds checkpoints in the runner script. After each year of walk-forward results, compute cumulative WR and PnL. If thresholds are breached, abort and report.

### First Seed Rule

When running seed validation (5 seeds), run the **first seed fully**. If it's clearly unprofitable (OOS Sharpe < 0 or OOS PF < 1.0), **STOP. Don't run the other 4 seeds.** Only proceed to multi-seed validation when the first seed shows genuine profitability.

### When Early-Stopped

1. QE writes engineering report with partial results and the trigger
2. QR writes diary tagged **`NO-MERGE (EARLY STOP)`** with partial metrics
3. The diary "Next Iteration Ideas" MUST propose **structural changes only**. After an early stop, these are **BANNED**:
   - Changing TP/SL by less than 2x
   - Changing Optuna trial count
   - Changing confidence threshold range
   - Changing symbol count by less than 50%
4. At least one proposed change must come from the QR Research Checklist

### Don't Dismiss Positive IS Too Quickly

If an iteration shows **strong IS performance** (Sharpe > +1.0) but weak OOS with one seed, **run 2-3 more seeds before giving up**. OOS is heavily seed-dependent (learned in iter 038). A configuration with strong IS likely has real signal — the OOS result may just be an unlucky seed. Always test at least 3 seeds before NO-MERGE when IS is promising.

### Philosophy

We spent 40 iterations making tiny improvements to a barely-profitable model. That was too slow. A good trading strategy should be obviously profitable — not require statistical tricks to detect signal. If the model isn't profitable in its first year of predictions, the approach is wrong. Change it.

---

## QR Research Methodology — Mandatory Analysis

After 3+ consecutive NO-MERGE iterations (or after an EARLY STOP), the QR MUST execute the research checklist below before writing the Phase 5 brief. The brief MUST contain a "Research Analysis" section documenting findings from the required categories.

**Minimum completion**: 2 categories after a MERGE, 4+ categories after 3+ NO-MERGE or EARLY STOP.

### Research with Evidence — NON-NEGOTIABLE

Writing "B. Symbol Universe — AAVE is DeFi, different sector, pass Gate 3 at 3.5/1.75" is **not research**. It is a one-line hypothesis that was never tested. A Phase 5 brief that lists research checklist items without showing the numbers behind them IS a violation of the QR methodology.

Every research checklist category the QR claims to have completed MUST include in the research brief (or linked analysis file) at least one of:

- A table of numerical results computed from IS data (feature importances, correlations, per-regime metrics, WR distributions, etc.)
- A chart or printout (copy-pasted into the brief as text — remember `reports/` and `analysis/` are gitignored, so charts must be summarised in text)
- A comparison: "ran X on IS data, observed Y, therefore Z"

A Phase 5 brief without evidence of this sort is a rubber-stamp brief. The QE should REFUSE to run Phase 6 on such a brief and return it to the QR for actual analysis.

### When a Candidate Symbol Fails Gate 3

A single-seed Gate 3 fail is a **signal to investigate the candidate further** — not a rejection. Before moving to the next symbol, the QR MUST:

1. **A3 / A4 — Feature importance on the candidate's IS data**: train a reference model on the candidate alone (using same 193 features), extract MDI, identify which features are top-20 for this candidate vs. the baseline's successful models (LTC, LINK). Are there differences? Propose pruning or replacement.
2. **C — Labeling analysis for the candidate**: compute the candidate's IS label distribution under the baseline labeling rules (ATR 3.5/1.75). Is the class balance reasonable? Do labels flip at a reasonable rate? Is the implied WR floor achievable given the candidate's realized NATR?
3. **E — Trade pattern in the failing period**: for candidates that failed year-1, look at what specific events in 2022 caused the losses. Was it one bad month (e.g., LUNA collapse week) dominating? If so, is there a regime-detection feature that would have filtered those trades?
4. **D — Lookback sensitivity**: is 24-month training too short or too long for this candidate? Try candidate-specific lookback windows.

Only after at least two of these have been run and documented with numerical evidence does the candidate get a definitive "rejected" tag. Until then, it is on "investigation pending".

This rule exists because treating fail-fast as a rejection criterion for the **candidate** (rather than for the **config**) conflates two different things. A candidate may have signal that the default config cannot extract; the research checklist is how we find out.

### Research Checklist

#### A. Feature Contribution Analysis
Using IS data only:

##### A1. Feature Pruning Protocol (MANDATORY before adding features)

Fewer, high-quality features produce more stable models. **Always prune before adding.**

1. **Train a reference LightGBM** on full IS period (all symbols pooled, same hyperparams as
   baseline) and extract feature importances (gain-based or permutation).
2. **Correlation dedup**: Compute pairwise Spearman correlation matrix across all features.
   For each pair with |correlation| > 0.90, keep the one with higher importance and drop the
   other. Document which features were dropped and their correlated partner.
3. **Importance threshold**: Rank features by importance. Compute cumulative importance.
   Drop all features below the "elbow" — typically the bottom 30-50% of features contribute
   < 5% of total importance. Target: **30-50 features** for a 2-symbol model with ~4,400
   training samples (ratio ≥ 88 samples/feature).
4. **Stability check**: Repeat importance analysis on 3 non-overlapping IS sub-periods
   (e.g., 2020-2021, 2022-2023, 2024-2025). Features that appear in the top-20 in ALL
   sub-periods are "stable." Features that rank top-10 in one period but bottom-50 in
   another are "unstable" — drop them regardless of aggregate importance.
5. **Validation**: Run a quick IS-only backtest with the pruned feature set. IS Sharpe must
   not degrade by more than 15% from the full-feature baseline. If it does, relax the
   pruning threshold until the constraint is met.

##### A2. Feature Discovery Scope

**IMPORTANT**: Use symbol-scoped discovery (`symbols=["BTCUSDT","ETHUSDT"]`) instead of
global intersection. The global intersection across ~800 symbols drops 72+ features that
BTC+ETH both have (Stochastic, MACD, Aroon, ADX, etc.) because smaller symbols lack them.
This was discovered in iter 083. Always scope discovery to the trading universe.

##### A3. Feature Importance: MDA vs MDI (OPTIONAL)

LightGBM's default gain-based importance (MDI) is biased toward high-cardinality continuous features. MDA (permutation importance) is theoretically better. However, **MDA is not implemented in the pipeline** after 117 iterations, and MDI has been sufficient for feature analysis.

**When to consider implementing MDA**: If MDI-based feature pruning produces counterintuitive results (e.g., a feature with high MDI rank degrades the model when removed), MDA may clarify. Otherwise, MDI is adequate for tree-based models.

**If implementing MDA**:
1. After training each monthly model, shuffle each feature's values in the validation fold
2. Re-compute Sharpe (not accuracy) on the shuffled data
3. MDA = mean(original_Sharpe - shuffled_Sharpe) across CV folds
4. Features with MDA < 0 are actively harmful — remove them
5. Group features by category and compute per-group cumulative importance
6. For each top-10 feature, provide an economic hypothesis for why it predicts direction

**Note**: MDI was used for the successful meme model pruning (iter 117: 67→45 features, OOS doubled). It works.

##### A4. New Feature Proposals

Only after pruning, propose **at most 5 NEW features** (net feature count should stay ≤ 50):
   - Cross-asset: BTC returns/volatility as leading indicator (`xbtc_return_1`, `xbtc_natr_14`)
   - Multi-timeframe: 1h or 4h indicators resampled to 8h (`mtf_1h_rsi_14`, `mtf_4h_adx_14`)
   - Microstructure: taker buy ratio momentum, volume imbalance, trade count vs volume
   - Interaction: RSI × ADX, volatility × trend strength
   - Each new feature must have an economic rationale — no "let's try it and see"

#### B. Symbol Universe & Diversification Analysis

This section is CRITICAL. Symbol expansion has failed catastrophically every time it was attempted
naively (iter 001: 50 symbols, Sharpe -4.89; iter 071: 4 symbols, early-stopped). The only
successful configuration is BTC+ETH (iter 010 onward). Any symbol change requires rigorous
validation using the protocol below.

Using IS data only:

##### B1. Correlation & Lead-Lag Analysis

1. Compute pairwise return correlation matrix on 8h candles for candidate symbols using
   rolling 90-day windows. Report: mean correlation, min/max, and how many windows have
   correlation > 0.8 (redundant), 0.5-0.8 (moderate), < 0.5 (diversifying).
2. Compute REGIME-DEPENDENT correlations: split IS data into high-vol and low-vol periods
   (using BTC NATR_21 above/below median). Report correlation in each regime separately.
   Symbols that decorrelate during high-vol periods are the most valuable for diversification.
3. Lead-lag analysis: for each candidate symbol vs BTC, compute cross-correlation at lags
   0, 1, 2, 3 candles (0h, 8h, 16h, 24h). If BTC leads by 1+ candles, the lagged BTC
   return is a valid feature for that symbol. If correlation is highest at lag 0, there is
   no lead-lag edge.
4. Compute rolling correlation STABILITY: standard deviation of the rolling 90-day
   correlation. High stability (low std) means the relationship is exploitable.
   Unstable correlations are dangerous for pooled models.

##### B2. Symbol Screening & Qualification Protocol

Before adding ANY new symbol to the trading universe, it MUST pass ALL of these gates:

**Gate 1 — Data quality**: At least 1,095 IS candles (1 year of 8h data), no gaps > 3 days,
first candle before 2023-07-01. (Already enforced by `universe.py`.)

**Gate 2 — Liquidity**: Mean daily volume > $10M (8h candles × 3 per day). Low liquidity
symbols have unreliable price action and slippage risk.

**Gate 3 — Stand-alone profitability**: Train a SEPARATE LightGBM model on only this
symbol's IS data (same config as baseline: 24mo window, 5 CV folds, 50 Optuna trials,
TP=8%/SL=4%, ensemble 3 seeds). The symbol passes ONLY if:
   - IS Sharpe > 0.0 (profitable on its own)
   - IS WR > break-even for its TP/SL ratio (33.3% for 8%/4%)
   - At least 100 IS trades

**Gate 4 — Pooled compatibility**: Add the symbol to BTC+ETH and re-run the baseline.
Compare the 3-symbol result against the 2-symbol baseline. The symbol passes ONLY if:
   - IS Sharpe >= baseline IS Sharpe × 0.90 (no more than 10% degradation)
   - BTC and ETH per-symbol WR do not degrade by more than 2pp each
   - The new symbol's per-symbol WR is above break-even

**Gate 5 — Diversification value**: Compute the portfolio-level benefit:
   - Correlation with existing portfolio returns < 0.7
   - Adding this symbol reduces portfolio IS MaxDD or increases IS Sharpe

All candidates MUST pass all 5 gates individually before being pooled. Multiple symbols can
be added simultaneously if each passes gates independently. Iter 071 failed because symbols
were added without screening, not because multiple were added at once.

##### B3. Model Architecture Decision Framework

After screening, decide HOW to model the expanded universe:

**Option A — Pooled model** (current approach):
- Use when: All symbols have similar volatility regime (NATR within 2x), similar WR profile,
  and high correlation (> 0.6).
- Risk: Dilution. The model learns an average signal that may not work for any symbol well.

**Option B — Per-symbol models**:
- Use when: Symbols have fundamentally different dynamics (e.g., ETH SHORT 51% WR vs
  BTC LONG 43.6% WR as found in iter 076).
- Implementation: Train separate LightGBM per symbol. Each gets its own Optuna optimization,
  feature selection, and confidence threshold. Doubles compute but allows specialization.
- Risk: Fewer training samples per model (~2,200/year for one symbol on 8h). Only viable
  for symbols with 3+ years of IS data.
- Decision rule: If per-symbol IS Sharpe > pooled IS Sharpe for BOTH symbols → use per-symbol.

**Option C — Cluster models**:
- Use when: You have 5+ symbols that naturally group into 2-3 clusters (e.g., large-cap L1,
  mid-cap DeFi, high-vol meme coins).
- Implementation: Hierarchical clustering on IS return correlations, train one model per cluster.
- Risk: Cluster boundaries shift over time. Validate clusters are stable across rolling windows.
- Decision rule: Only use if clusters have at least 3 symbols each (for sufficient training data).

**Option D — Hierarchical model** (most sophisticated):
- A global model trained on all symbols, plus per-symbol or per-cluster fine-tuning.
- Implementation with LightGBM: Train a global model, then add its predictions as a feature
  for per-symbol models.
- Risk: Complexity. Only attempt after Options A and B are exhausted.

Document the decision in a matrix in the research brief:
```
| Symbol pair   | Correlation | NATR ratio | WR difference | Recommended architecture |
|---------------|-------------|------------|---------------|-------------------------|
| BTC ↔ ETH     | 0.82        | 1.3x       | 7pp           | Pooled or Per-symbol     |
| BTC ↔ SOL     | ???         | ???        | ???           | ??? (after Gates)        |
```

#### C. Labeling Analysis
Using IS data only:
1. Label distribution: fraction long vs short, class imbalance beyond 55/45?
2. Label stability: for consecutive candles, how often does the label flip? Flip rate > 60% = noisy labels
3. Test alternatives:
   - Ternary: add "neutral" for timeout candles with |return| < 1%
   - Regression: forward 1-candle return as target, compute R²
   - Different RR ratios: 1:1, 1.5:1, 2:1, 3:1 — report WR and resolution for each
4. Per-regime label quality: which labeling produces more separable features in trending vs choppy?
5. **Timeout sensitivity**: After establishing a working timeout, do NOT change it by less than 2x. Iter 116 proved that reducing timeout from 7d to 5d caused IS Sharpe +1.71 (overfitting signal) while OOS collapsed to -0.04. Small timeout changes alter label distribution in ways that cause catastrophic overfitting.

#### D. Feature Frequency & Lookback Analysis
Using IS data only:
1. Sensitivity of top-5 features to lookback window (e.g., RSI period 5,7,9,14,21,30 — best single-feature AUC)
2. Multi-timeframe proposal: compute 1h indicators, aggregate to 8h (mean/min/max over window)
3. Rolling window sensitivity for statistical features (autocorrelation, skewness, kurtosis)

#### E. Trade Pattern Analysis
Using IS trades.csv:
1. Per-month WR and PnL — identify good/bad quarters
2. Per-hour-of-day WR (8h candles: 00:00, 08:00, 16:00 UTC)
3. Exit reason breakdown: TP%, SL%, timeout% and average return per reason
4. Streak analysis: clusters of consecutive wins/losses and market conditions
5. Long vs short split: is the model better at one direction?

#### F. Statistical Rigor
Using IS data only:
1. Bootstrap WR: resample 1000 times, report 95% CI. If CI includes break-even, signal may exist but is noisy
2. Binomial p-value: is WR significantly different from 50%? From break-even?
3. For proposed changes: is the expected improvement larger than the bootstrap CI width?

#### G. Stationarity & Memory Analysis (AFML Ch. 5) — OPTIONAL

**Status**: Fracdiff tested in iter 100, inconclusive due to confounding factors. ADF tests never performed in any diary. Tree-based models (LightGBM) are inherently less sensitive to stationarity than linear models. **Revisit only if switching to a linear/neural model.**

If pursuing:
1. For each top-20 feature, run the ADF test. Report p-value. Features with p > 0.05 are non-stationary.
2. For non-stationary features, compute minimum d for ADF p < 0.05.
3. Compute correlation between original (d=0) and fracdiff version (d=d_min).
4. Report: table of (feature, ADF_p_original, d_min, correlation_original_fracdiff)

#### H. Overfitting Audit (AFML Ch. 11-12)
1. Compute the Deflated Sharpe Ratio for the baseline, accounting for N=117+ trials. At N=117, E[max(SR_0)] ~ 3.08. Current baseline OOS Sharpe +1.01 gives DSR < 0 — the observed Sharpe is within the range expected from 117 random trials. This does NOT mean no signal exists, but individual-iteration statistical significance is extremely unlikely.
2. If CPCV is implemented: compute PBO for the latest monthly model. Report the fraction of months with PBO > 0.5. (Not yet implemented — CPCV/PBO code does not exist in the codebase.)
3. Compute the variance of IS Sharpe across walk-forward months. High variance suggests regime sensitivity. Report: mean, std, min, max of monthly IS Sharpe.
4. **Decision rule**: At N=117+, focus on portfolio-level metrics and OOS regime consistency rather than DSR alone. Reduce independent trials (fewer, bolder iterations).

### How to Use the Checklist

Pick categories based on the bottleneck:
- WR is the problem → A (features) + C (labeling)
- Some symbols work, others don't → B (symbols)
- Model trades too much/little → E (patterns) + C (labeling)
- Same approach failed 3+ times → F (statistical rigor) to verify if signal exists at all
- Stuck on 2 symbols / need diversification → B (MANDATORY — use the full B1/B2/B3 protocol) + A (cross-asset features for new symbols)
- Single-symbol concentration > 30% → B (this constraint cannot be met without expanding the universe)
- High OOS Sharpe but thin trade count → B (diversify for more trades rather than lowering confidence threshold)
- **Too many features / overfitting suspected** → A1 (MANDATORY feature pruning protocol). Run correlation dedup + importance pruning BEFORE any other change. Target 30-50 features.
- **Adding new features** → A1 first (prune), then A4 (add ≤5 new). Net count must not increase.
- **Non-stationary features suspected** → G (stationarity analysis). Run ADF tests on top features, propose fracdiff replacements.
- **Multiple testing / 117+ iterations** → H (overfitting audit). Compute DSR before investing effort in a new iteration.
- **Methodological upgrade needed** → G + H together. These are the MLP foundation categories.

---

## Diversification Research Protocol

The strategy is currently concentrated in BTC+ETH (2 symbols, ETH contributing 91.6% of OOS PnL).
The 30% single-symbol concentration hard constraint is waived because it's structurally impossible
with 2 symbols. This section guides the QR on systematically expanding the symbol universe.

### Why Diversification Matters

1. **Risk reduction**: Correlated drawdowns are the #1 killer. BTC and ETH crashed together in
   every historical bear market. Adding uncorrelated symbols reduces portfolio MaxDD.
2. **Statistical robustness**: 87 OOS trades is thin. More symbols = more trades = tighter
   confidence intervals.
3. **Constraint compliance**: The 30% concentration constraint exists for a reason. Meeting it
   requires trading at least 4 symbols with balanced signal quality.
4. **Capacity**: With 2 symbols, the strategy has a hard capacity ceiling. More symbols =
   more deployment capital.

### Progressive Expansion Roadmap

The QR should follow this order, validating at each step before proceeding:

**Stage 1: Understand BTC/ETH dynamics deeply** (PREREQUISITE for any expansion)
- Run lead-lag analysis (Research Checklist B1.3)
- Compute regime-dependent correlation (B1.2)
- Evaluate per-symbol models vs pooled (B3 Option B)
- Answer: Does a per-symbol architecture improve the baseline? If yes, use it going forward.

**Stage 2: Screen candidate symbols**
- Run the Symbol Qualification Protocol (B2) for the top candidates by volume:
  SOL, XRP, DOGE, BNB, ADA, AVAX, LINK, MATIC/POL.
- Evaluate candidates in parallel — each must pass all 5 gates independently.
- Document each candidate's gate results in the research brief.

**Stage 3: Validate the expanded universe**
- Add all gate-passing symbols together and run full walk-forward.
- Check all hard constraints including per-symbol metrics.
- If the expanded configuration passes: update the baseline.

**Stage 4: Portfolio-level optimization** (only after 4+ symbols)
- Consider non-equal position sizing (e.g., inverse-volatility weighting)
- Evaluate if the 30% concentration constraint can be met
- Analyze portfolio-level MaxDD vs per-symbol MaxDD

### Cross-Asset Feature Strategy for Expanded Universe

When adding symbol X to a universe containing BTC+ETH:
- For X: add `xbtc_` features (BTC returns/volatility as leading indicators). These are
  genuinely new information for X.
- For BTC: do NOT add `xbtc_` features — they are redundant (iter 070 lesson).
- For ETH: the `xbtc_` features may help (BTC leads ETH by ~1 candle historically).
  Test with and without.
- If training per-symbol models: each model gets its own cross-asset features.
  X's model gets BTC features. BTC's model gets NO cross-asset features.
  ETH's model gets BTC features only if lead-lag analysis confirms a lag.

### Diversification Anti-Patterns (Learned from 77 Iterations)

1. **DO NOT add unscreened symbols.** Every candidate must pass all 5 qualification gates.
   Iter 071 added SOL+DOGE without screening → catastrophic collapse.

2. **DO NOT assume high-volume = high-signal.** SOL has massive volume but very different
   dynamics (NATR 5-15% vs BTC 2-4%). Volume does not imply predictability.

3. **DO NOT pool symbols with NATR ratios > 2x.** BTC NATR ~3% and DOGE NATR ~8% — when
   pooled, the model's confidence threshold and labeling barriers cannot serve both.
   Fixed TP=8%/SL=4% is reasonable for BTC but too tight for DOGE.

4. **DO NOT add symbols that lack stand-alone profitability.** If a per-symbol model for SOL
   is unprofitable in IS, adding SOL to the pooled model adds noise, not signal.

5. **DO NOT ignore the feature count / sample count ratio.** With 106 features and 2 symbols,
   monthly training has ~4,400 samples (ratio ~41). Adding more symbols increases samples
   which HELPS the model — but only if the new symbols' patterns are learnable.

---

## QR: Deep Analysis & Bold Ideas (Phase 7) — MANDATORY EVERY ITERATION

The QR MUST perform ALL of the following in every iteration (not just when strategy is unprofitable):

1. **Read the IS quantstats HTML report** (MANDATORY): Open `reports/iteration_NNN/in_sample/quantstats.html` using the browser/screenshot tool or parse its key sections. Extract insights from:
   - Monthly returns heatmap: which months/years are profitable vs losing?
   - Drawdown analysis: when are the worst drawdown periods? Do they coincide with specific market events?
   - Rolling Sharpe: is the strategy improving over time or degrading?
   - Worst 5 drawdowns: duration, depth, recovery time
   - Distribution of returns: skewness, fat tails, outliers
   - Document specific findings in the diary (e.g., "Q2 2022 lost 15% — coincides with LUNA crash")
2. **Analyze trades deeply**: Read trades.csv, compute per-symbol WR, monthly PnL patterns, exit reason breakdown (TP rate vs WR distinction!), long/short split, trade count variance. Don't just read comparison.csv.
3. **Propose BOLD, structural changes** — not incremental parameter tweaks. After 3+ failed iterations with minor changes, step back and consider:
   - Changing the model type (classification → regression, different loss function)
   - Changing the labeling approach fundamentally (triple barrier → forward return, add neutral class)
   - Per-symbol or per-cluster models instead of pooled
   - Adding entirely new feature categories (cross-asset features, on-chain data)
   - Fundamentally different trade entry/exit logic
4. **Review lgbm.py code** at the end of each iteration. Look for:
   - Bugs or inefficiencies that could affect results
   - Architectural improvements (feature discovery, walk-forward logic, caching)
   - Whether the model training pipeline works correctly
   - Document findings in the diary under "lgbm.py Code Review"
5. **Reference the Research Checklist**: The diary must document which checklist categories (A-H) were completed, what was found, and how findings influenced the "Next Iteration Ideas." If the checklist was skipped (first iterations after a MERGE), explain why.
6. **Quantify the gap explicitly**: State: "WR is X%, break-even is Y%, gap is Z pp. TP rate is A%, SL rate is B%. To close this gap, the strategy needs [specific mechanism]." Vague statements like "improve signal quality" are insufficient.

## QE: Trade Execution Verification (Phase 6)

After the backtest completes, the QE MUST verify trade execution by:

1. **Sampling 10-20 trades from trades.csv** and checking:
   - Entry price matches close price of the signal candle
   - SL price = entry ± sl_pct correctly
   - TP price = entry ± tp_pct correctly
   - Timeout time = open_time + timeout_minutes correctly
   - PnL calculation is correct: (exit - entry) / entry for long, (entry - exit) / entry for short
2. **Checking exit reasons are consistent**: SL trades should have PnL ≈ -sl_pct, TP trades ≈ +tp_pct
3. **Documenting any anomalies** in the engineering report
4. **Label leakage audit (MANDATORY every iteration)**: Verify that `TimeSeriesSplit` gap is correctly computed: `gap = (timeout_candles + 1) * n_symbols`. Check that no training label's forward scan extends into the validation period. Check that walk-forward training windows don't include future klines. This must be verified even when CV code hasn't changed — parameter changes (timeout, interval, symbols) affect the required gap.
5. **Feature reproducibility check (MANDATORY every iteration)**: The engineering report must state the exact `feature_columns` source used (constant name + count, e.g. "BASELINE_FEATURE_COLUMNS, 193 features"). If the iteration defines its own list, the report must paste the list or its hash. Auto-discovery is disabled in code — the runner must pass `feature_columns=[...]` explicitly or the backtest will not start.

## Code Quality (QE)

- Type hints on all new functions
- Pure functions where possible
- Deterministic backtest (fixed random seed, logged in brief)
- No lookahead bias within walk-forward folds — `assert` checks on date ordering per monthly fold
- No label leakage in CV — verify `TimeSeriesSplit` gap matches `(timeout_candles + 1) * n_symbols`
- No label leakage in walk-forward — training labels use only past klines
- Tests for labeling, feature generation, PnL calculation

## Exploration / Exploitation Protocol

Every iteration MUST be tagged as **EXPLORATION** or **EXPLOITATION** in the research brief header.

### Definitions

**EXPLOITATION** — improves the current best approach by tuning parameters within the existing architecture:
- Changing symbol count/selection within the same model
- Adjusting TP/SL by ≤50%, timeout, training window, CV folds, Optuna trials
- Adjusting confidence threshold range
- Changing start_time for the backtest

**EXPLORATION** — tests a fundamentally different approach or introduces new capabilities:
- **New feature generation**: Creating features that don't exist in the pipeline (calendar, cross-asset, interaction, multi-timeframe)
- **Model type change**: Classification ↔ regression, different loss function, ensemble
- **Labeling paradigm change**: Ternary classification, regression target, different barrier ratios (>2x change)
- **Architecture change**: Per-symbol models, stacked models, regime-switching
- **Data change**: Different candle interval, different data source
- **Bold parameter changes**: TP/SL changes >2x (e.g., TP=8%/SL=4%)

### Mandatory Ratio: 70% Exploitation / 30% Exploration

Over every rolling window of 10 iterations, at least **3 must be EXPLORATION**. The QR must track this:

```
Diary section: "## Exploration/Exploitation Tracker"
Last 10 iterations: [E, X, X, E, X, X, X, E, X, X]  (E=explore, X=exploit)
Exploration rate: 3/10 = 30% ✓
```

If the exploration rate drops below 30%, the NEXT iteration MUST be exploration. No exceptions.

### Exploration Idea Bank (Prioritized)

The QR maintains a running list of untested exploration ideas, organized by priority tier. MLP Foundation techniques should be implemented before advanced or existing ideas.

**AFML Technique Status (as of iter 117):**

| Technique | Status | Iter(s) | Outcome |
|-----------|--------|---------|---------|
| TimeSeriesSplit+gap | **ADOPTED** | 091-093 | Standard CV method. Works. |
| PurgedKFoldCV | **ABANDONED** | 089-090 | Removed 4% data/fold, caused empty folds. TSS+gap is better. |
| Sample Uniqueness | **FAILED** | 097 | Dense labels produce uniform ~0.046 uniqueness. Needs event-driven sampling first. |
| MDA/Permutation | **UNUSED** | 094 (ad-hoc) | Not in pipeline. MDI sufficient for 117 iterations. |
| Fractional Differentiation | **INCONCLUSIVE** | 100 | Confounded by parquet regeneration. Tree models less stationarity-sensitive. |
| Deflated Sharpe Ratio | **UNIMPLEMENTED** | — | No code exists. At N=117, DSR < 0 for baseline. |
| PBO/CPCV | **UNIMPLEMENTED** | — | No code exists. |
| Meta-labeling | **FAILED** | 102 | Over-filtered to 2 OOS trades. Needs more meta-features. |
| Kelly Sizing | **NEUTRAL** | 107 | Scales PnL magnitude but doesn't change WR. |

**TIER 1 — Active Priorities:**

1. **Portfolio combination optimization** — Combine BTC/ETH + DOGE/SHIB models to beat combined OOS Sharpe +1.01. This is the current project goal. Involves: allocation weighting, cross-model trade correlation, combined drawdown analysis.

2. **Meme model refinement** — Continue improving DOGE/SHIB OOS Sharpe from +0.66 toward +0.80+ to make portfolio viable. Feature pruning, barrier tuning, and training window optimization.

3. **Event-driven sampling** — Prerequisite for sample uniqueness. Generate labels only at "events" (volume spikes >3x, range spikes, structural breaks). Reduces label universe from ~4,400 to ~500-1,000 meaningful events. Would fix the uniqueness problem from iter 097.

4. **Entropy features (AFML Ch. 18)** — Shannon entropy of discretized returns over rolling 50-candle window. Genuinely novel features not captured by volatility or momentum. Untested.

5. **CUSUM structural breaks (AFML Ch. 17)** — Detect regime changes. Features: `struct_cusum_break_5`, `struct_candles_since_break`. Useful both as features and for event-driven sampling.

**TIER 2 — MLP Advanced:**

6. **Meta-labeling (AFML Ch. 3)** — Train a primary model (current LightGBM) to predict direction, then a secondary model on a NEW target: 1 if the primary model's predicted trade would have been profitable, 0 otherwise. Secondary model features: primary confidence, NATR quartile, ADX regime, rolling 10-trade WR, hour_of_day. The secondary model's output probability becomes the bet size. Critical: the secondary model must be trained on OUT-OF-FOLD predictions of the primary model, not in-sample predictions.

7. **CPCV with PBO** — Combinatorial Purged CV (N=6, k=2 -> 15 paths). Use path distribution to compute Probability of Backtest Overfitting. PBO > 0.5 = overfit likely.

8. **Entropy features (AFML Ch. 18)** — Shannon entropy of discretized returns over rolling 50-candle window: `stat_shannon_entropy_50`, `stat_approx_entropy_50`. High entropy = unpredictable market (avoid trading). Low entropy = patterned market (edge exploitable). Genuinely novel features not captured by volatility or momentum.

9. **CUSUM structural breaks (AFML Ch. 17)** — Cumulative sum of standardized log returns. Detect breakpoints where CUSUM exceeds 2-3 sigma. Features: `struct_cusum_break_5` (break in last 5 candles), `struct_candles_since_break`. Also useful for event-driven sampling.

10. **Event-driven sampling** — Instead of evaluating every candle, only generate labels at "events": structural breaks, volume spikes (>3x rolling mean), range spikes. Reduces label universe from ~4,400 to ~500-1,000 meaningful events with higher signal-to-noise ratio.

11. **Bet sizing via Kelly criterion (AFML Ch. 10)** — Replace fixed weight=100 with half-Kelly sizing: f* = p - (1-p)/b, where p = ensemble probability, b = TP/SL ratio = 2.0. For p=0.55: f*=0.325, weight=65. For p=0.70: f*=0.55, weight=110. Pairs naturally with meta-labeling: meta-model's P(profitable) feeds into Kelly.

**TIER 3 — Existing Ideas:**

**Feature Frequency & Noise Reduction:**
- Slow features via 3-4x lookback multiplier: use period x 3 to simulate daily indicators on 8h (e.g., SMA_300 ~ daily SMA_100). Regenerate parquet with these.
- Smoothed-data features: compute indicators on 3-candle rolling mean of close/high/low — removes intra-day noise
- Long-period-only mode: drop all features with period < 20 — keep only stable, trend-level signals
- Resample 8h->1d, compute daily indicators, broadcast back to 8h candles

**Feature Generation:**
- Calendar features: hour_of_day (0/8/16 UTC), day_of_week (tried iter 026 — showed signal but didn't beat baseline)
- Interaction features: RSI x ADX, volatility x trend_strength
- Cross-asset momentum: BTC return as leading indicator
- Regime indicator as feature: BTC ADX/NATR quartile

**Prediction Stability:**
- Signal cooldown: after opening a trade, don't predict opposite direction for N candles
- Trend-following labels: label based on multi-candle trend direction (e.g., majority of next 5 candles)
- Prediction smoothing: majority vote of last 3 predictions before generating signal
- "Momentum of predictions": add previous prediction direction as a feature

**Model Architecture:**
- Per-symbol models: separate LightGBM for BTC and ETH
- Ensemble: average predictions from classification + regression
- Stacking: use classification probabilities as features for a meta-model

**Labeling:**
- Ternary: long / short / neutral (timeout with |return| < 1%)
- Dynamic barriers: scale TP/SL by recent volatility (ATR-based)
- Multi-horizon: predict both 8h and 24h returns

**Bold Parameters:**
- TP=8%/SL=4% — tested iter 027: 46% WR! IS Sharpe -0.04. Very promising on BTC+ETH.
- TP=6%/SL=3% (2:1, middle ground between 4%/2% and 8%/4%)
- Timeout=1 week (7 days)

**Symbol Universe Expansion (REQUIRES Research Checklist B):**
- Per-symbol models for BTC and ETH (separate LightGBM, separate Optuna) — ETH has 51.1% SHORT
  WR vs BTC 43.6% LONG WR (iter 076). Different dynamics suggest different models.
- Expand to BTC+ETH+SOL (or other top candidates) with each symbol qualified through the
  5-gate protocol. Screen multiple candidates in parallel.
- Dynamic per-symbol barriers — instead of fixed 8%/4% for all symbols, use per-symbol
  ATR-scaled barriers. SOL might need TP=12%/SL=6% while BTC uses TP=6%/SL=3%.
- Sector rotation feature — compute rolling 30-day returns for L1 (BTC, ETH, SOL),
  DeFi (AAVE, UNI), and meme (DOGE, SHIB). Use sector-relative performance as a feature.
- BTC dominance as a feature — BTC market cap share. When dominance rises, altcoins tend
  to underperform (capital flows to BTC). Available from CoinGecko or on-chain APIs.
- Portfolio-level signal aggregation — instead of treating each symbol independently,
  consider portfolio constraints: max N positions at a time, inverse-volatility weighting.

### Dead Ideas (definitively disproven — do not retry)

| Idea | Iter(s) | Why it failed |
|------|---------|--------------|
| PurgedKFoldCV | 089-090 | 4% data loss/fold, empty folds with Optuna |
| Feature pruning on BTC/ETH (185→50) | 094-095 | Destroys Optuna co-optimization, IS Sharpe -1.46 |
| Per-symbol models (1 symbol each) | 099, 109 | Too few training samples (~2,200/year), collapses |
| Naive symbol pooling (BTC+ETH+X) | 071, 105 | Unscreened symbols destroy existing WR |
| Sample uniqueness with dense labels | 097 | Uniform ~0.046 uniqueness, needs event-driven sampling first |
| Meta-labeling with 2 meta-features | 102 | Over-filtered to 2 OOS trades, needs 5-6 features |
| Short timeout for meme (7d→5d) | 116 | Catastrophic overfitting (IS +1.71, OOS -0.04) |
| TP=8%/SL=4% (now baseline) | 027→093 | **ADOPTED** — not dead, but no longer an "idea" |

## Key Reminders

- The `reports/` directory is in `.gitignore`. Reports exist only locally. The diary captures the key metrics (both IS and OOS) in text form, which is what persists.
- Analysis charts are also untracked. Describe findings in text in the research brief. Never reference local file paths in tracked documentation.
- One variable at a time between iterations. The diary is only useful for learning if you can attribute changes to specific decisions.
- Read the previous iteration's diary before starting a new one. The "Next Iteration Ideas" section is the starting point.
- The OOS cutoff date appears in: `src/crypto_trade/config.py`, every research brief (Section 0), every diary entry, and `BASELINE.md`. It is always `2025-03-24`. Always.
