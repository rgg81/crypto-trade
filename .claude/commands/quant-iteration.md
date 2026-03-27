---
name: quant-iteration
description: "Quant research/engineering iteration workflow for the crypto-trade LightGBM strategy. Use this skill whenever the user mentions: starting an iteration, quant researcher, quant engineer, research brief, iteration diary, baseline comparison, merge decision, Phase 1-8, EDA on candle data, labeling strategy, feature engineering for the trading bot, running a backtest, evaluating backtest results, in-sample, out-of-sample, OOS cutoff, or comparison.csv. Also trigger when the user says 'start iteration', 'run phase', 'evaluate reports', 'write diary', 'merge decision', or references ITERATION_PLAN_8H.md or BASELINE.md."
---

# Quant Iteration Skill

This skill governs the iterative research/engineering workflow for building and improving the crypto-trade LightGBM strategy on 8h candles.

## Before You Start

Read `ITERATION_PLAN_8H.md` at the repo root. It contains the full plan with templates, baseline rules, and phase details. This skill is a quick-reference companion, not a replacement for the plan.

### Default Flow: Full Autopilot

When this skill is triggered, **do NOT ask which role to play or whether to proceed**. Default behavior:
1. Read the last diary's "Next Iteration Ideas" and BASELINE.md
2. Determine the next iteration number
3. Run the full flow: QR Phases 1-5 → QE Phase 6 → QR Phases 7-8
4. Only pause if there's an actual blocker (ambiguous brief, unexpected error, decision that genuinely requires user input)

The user can override by specifying a role (e.g., "be the QR") or a phase (e.g., "run Phase 6"). Otherwise, go.

## NO CHEATING — ABSOLUTE RULES

**NEVER** do any of the following to improve metrics artificially:
- **NEVER change `start_time`** to skip bad IS months. The backtest MUST run from the earliest available data. Trimming the evaluation window is CHEATING — it hides losses instead of fixing the strategy.
- **NEVER cherry-pick date ranges** to make IS or OOS look better.
- **NEVER post-hoc filter trades** from the results to improve metrics.
- **NEVER tune parameters on OOS data** (the researcher sees OOS only in Phase 7).

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
- **After 3+ consecutive NO-MERGE iterations**: Phases 1-4 are **MANDATORY**. The QR must complete at least **4 of 6 categories** from the Research Checklist. No skipping.
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

## Feature Normalization Awareness

When using a pooled model across multiple symbols with different price scales, the QR and QE must ensure features are **scale-invariant**:

- **SAFE features** (already normalized): RSI, Stochastic, %B, z-scores, returns (%), NATR, ratios, oscillators, boolean crosses
- **UNSAFE features** (price-scale dependent): raw SMA, raw EMA, raw ATR, raw VWAP, raw OBV, raw A/D, raw volume, raw Bollinger Band levels
- **LightGBM note**: Tree-based models are less sensitive to scale than linear models, but large absolute values (BTC price ~60K vs small-cap ~0.01) can still cause split-point issues

When proposing new features, the QR should prefer normalized/ratio-based features. When the model uses raw price-level features (SMA, EMA, VWAP), understand that these only work well within a single symbol or among symbols with similar price scales.

---

## Baseline Comparison Rules

Read `BASELINE.md` on main before evaluating. An iteration merges ONLY if:

1. **Primary**: OOS Sharpe > current baseline OOS Sharpe
2. **Hard constraints** (all must pass):
   - Max drawdown (OOS) ≤ baseline OOS max drawdown × 1.2
   - Minimum 50 OOS trades
   - Profit factor > 1.0 (OOS)
   - No single symbol > 30% of total OOS PnL
   - IS/OOS Sharpe ratio > 0.5 (researcher overfitting gate)

If primary metric improves but a constraint fails → NO-MERGE. Document trade-off in diary.

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

When running seed validation (10 seeds), run the **first seed fully**. If it's clearly unprofitable (OOS Sharpe < 0 or OOS PF < 1.0), **STOP. Don't run the other 9 seeds.** Only proceed to multi-seed validation when the first seed shows genuine profitability.

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

### Research Checklist

#### A. Feature Contribution Analysis
Using IS data only:
1. Run permutation importance (or train a single LightGBM on full IS period)
2. Group features by category (momentum, volatility, trend, volume, mean_reversion, statistical) — compute per-group cumulative importance
3. For each top-10 feature, provide an economic hypothesis for why it predicts direction
4. Propose **at least 2 NEW features** not in the current pipeline:
   - Cross-asset: BTC returns/volatility as leading indicator (`btc_return_lag1`, `btc_natr_14`)
   - Multi-timeframe: 1h or 4h indicators resampled to 8h (`mtf_1h_rsi_14`, `mtf_4h_adx_14`)
   - Microstructure: taker buy ratio momentum, volume imbalance, trade count vs volume
   - Calendar: hour of day (0/8/16), day of week
   - Interaction: RSI × ADX, volatility × trend strength
5. Propose a feature selection method (permutation pruning, RFE, or correlation dedup > 0.95)

#### B. Symbol Universe Analysis
Using IS data only:
1. Compute pairwise return correlation matrix (rolling 90-day windows)
2. Cluster symbols (hierarchical or k-means) — identify 3-5 natural groups
3. Rank symbols by per-symbol model WR
4. Analyze whether per-cluster or per-tier models outperform the pooled model
5. Document whether BTC/ETH should have dedicated models

#### C. Labeling Analysis
Using IS data only:
1. Label distribution: fraction long vs short, class imbalance beyond 55/45?
2. Label stability: for consecutive candles, how often does the label flip? Flip rate > 60% = noisy labels
3. Test alternatives:
   - Ternary: add "neutral" for timeout candles with |return| < 1%
   - Regression: forward 1-candle return as target, compute R²
   - Different RR ratios: 1:1, 1.5:1, 2:1, 3:1 — report WR and resolution for each
4. Per-regime label quality: which labeling produces more separable features in trending vs choppy?

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

### How to Use the Checklist

Pick categories based on the bottleneck:
- WR is the problem → A (features) + C (labeling)
- Some symbols work, others don't → B (symbols)
- Model trades too much/little → E (patterns) + C (labeling)
- Same approach failed 3+ times → F (statistical rigor) to verify if signal exists at all

---

## QR: Deep Analysis & Bold Ideas (Phase 7)

When the strategy is far from profitability (PF < 1.0, WR below break-even), the QR MUST:

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
5. **Reference the Research Checklist**: The diary must document which checklist categories (A-F) were completed, what was found, and how findings influenced the "Next Iteration Ideas." If the checklist was skipped (first iterations after a MERGE), explain why.
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

## Code Quality (QE)

- Type hints on all new functions
- Pure functions where possible
- Deterministic backtest (fixed random seed, logged in brief)
- No lookahead bias within walk-forward folds — `assert` checks on date ordering per monthly fold
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

### Exploration Idea Bank

The QR maintains a running list of untested exploration ideas. At minimum, these should always be considered:

**Feature Frequency & Noise Reduction (HIGH PRIORITY):**
- Slow features via 3-4x lookback multiplier: use period×3 to simulate daily indicators on 8h (e.g., SMA_300 ≈ daily SMA_100). Regenerate parquet with these.
- Smoothed-data features: compute indicators on 3-candle rolling mean of close/high/low — removes intra-day noise
- Long-period-only mode: drop all features with period < 20 — keep only stable, trend-level signals
- Resample 8h→1d, compute daily indicators, broadcast back to 8h candles

**Feature Generation:**
- Calendar features: hour_of_day (0/8/16 UTC), day_of_week (tried iter 026 — showed signal but didn't beat baseline)
- Interaction features: RSI × ADX, volatility × trend_strength
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

## Key Reminders

- The `reports/` directory is in `.gitignore`. Reports exist only locally. The diary captures the key metrics (both IS and OOS) in text form, which is what persists.
- Analysis charts are also untracked. Describe findings in text in the research brief. Never reference local file paths in tracked documentation.
- One variable at a time between iterations. The diary is only useful for learning if you can attribute changes to specific decisions.
- Read the previous iteration's diary before starting a new one. The "Next Iteration Ideas" section is the starting point.
- The OOS cutoff date appears in: `src/crypto_trade/config.py`, every research brief (Section 0), every diary entry, and `BASELINE.md`. It is always `2025-03-24`. Always.
