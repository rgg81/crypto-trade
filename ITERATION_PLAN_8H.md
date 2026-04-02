# Crypto-Trade: LightGBM 8H Candle Iteration Plan

## Mission

Crypto markets are the most inefficient markets on earth. They trade 24/7 across fragmented venues populated by retail speculators, algorithmic bots with misaligned incentives, and institutions constrained by mandates that have nothing to do with price discovery. Fear and greed oscillate on 8-hour cycles. Liquidation cascades create mispricings that would be arbitraged away in seconds in equities but persist for hours in crypto futures. Funding rates distort positioning. Social media narratives move billions.

Our edge is systematic patience. We use LightGBM on 8-hour candles — a timeframe slow enough to avoid microstructure noise, fast enough to capture the behavioral patterns that human traders create and perpetuate. We do not predict the future. We identify moments when the distribution of forward returns is skewed in our favor, and we bet accordingly, sized by our conviction and disciplined by our risk framework.

The market's irrationality is our opportunity. Volatility is not risk — it is the raw material of profit. Every liquidation cascade, every panic sell, every euphoric FOMO spike creates a statistical edge for the patient, systematic trader who has done the work to distinguish signal from noise.

We build strategies that would survive scrutiny by the most rigorous quantitative finance researchers. No p-hacking. No overfitting to backtest. No self-deception. If a strategy cannot withstand combinatorial purged cross-validation, deflated Sharpe ratio tests, and out-of-sample evaluation on data the researcher never saw, it does not trade.

88 iterations have taught us what does not work. That knowledge is as valuable as what does. We are closer than we think.

---

## Context

- **Repo**: `crypto-trade` (Python 3.13, uv, Binance Futures USD)
- **Data**: ~800 symbols, parquet files, already downloaded
- **Timeframe**: 8h candles
- **Model**: LightGBM (fixed for this iteration)
- **Existing infra**: Feature generation pipeline, Binance futures fee model, quantstats report generation, walk-forward backtest (monthly retraining with timeseries CV, 1-year minimum training window)
- **Goal**: Build a profitable, regime-robust LightGBM strategy on 8h candles through a structured researcher/engineer workflow, using rigorous quantitative methods from Marcos Lopez de Prado's AFML framework to avoid the pitfalls that destroyed 88 prior iterations

---

## Data Split: In-Sample / Out-of-Sample

This is the most important section of the entire plan. Everything else is subordinate to this.

### What Problem This Solves

The walk-forward backtest already prevents model-level leakage — every month, it trains only on past data using timeseries CV and predicts the next month. That mechanism is sound and does not change.

The IS/OOS split solves a DIFFERENT problem: **researcher overfitting**. When a researcher can see how the strategy performed in recent months, they unconsciously tune features, labeling rules, stop-loss thresholds, and strategy parameters to fit that recent data. This is survivorship bias at the research level. The model never sees future data, but the researcher's decisions are contaminated by it.

The fix: the researcher designs everything using only historical data, and a recent window is held back that the researcher NEVER sees until evaluation.

### The OOS Cutoff Date

There is ONE project-level constant:

```
OOS_CUTOFF_DATE = 2025-03-24
```

This date is fixed for the lifetime of this project. It does NOT change between iterations. Every iteration uses the same split so results are directly comparable.

- **In-sample (IS) period**: all data before 2025-03-24
- **Out-of-sample (OOS) period**: all data from 2025-03-24 onward (~1 year)

### How the Backtest Works (Unchanged)

The walk-forward backtest runs exactly as it does today, on the **entire dataset** (IS + OOS combined) as one continuous process:

```
Month 1: Train on [start → month_0] → Predict month_1
Month 2: Train on [start → month_1] → Predict month_2
...
Month N: Train on [start → month_N-1] → Predict month_N
```

There is no artificial wall between IS and OOS at the model level. The walk-forward naturally rolls through the OOS period using only past data for each prediction, exactly as it would in live trading. This is correct behavior — the walk-forward simulates real deployment.

### What IS Different: Two Report Batches

After the backtest completes, the reporting layer splits results at `OOS_CUTOFF_DATE` to produce two separate report sets:

```
reports/iteration_NNN/
├── in_sample/                # Trades with entry_time < 2025-03-24
│   ├── quantstats.html
│   ├── trades.csv
│   ├── daily_pnl.csv
│   ├── monthly_pnl.csv
│   ├── per_regime.csv
│   ├── per_symbol.csv
│   └── feature_importance.csv
├── out_of_sample/            # Trades with entry_time >= 2025-03-24
│   ├── quantstats.html
│   ├── trades.csv
│   ├── daily_pnl.csv
│   ├── monthly_pnl.csv
│   ├── per_regime.csv
│   └── per_symbol.csv
└── comparison.csv            # Side-by-side IS vs OOS key metrics
```

The `comparison.csv` provides the overfitting diagnostic:

```csv
metric,in_sample,out_of_sample,ratio
sharpe,1.45,0.82,0.57
sortino,2.10,1.05,0.50
max_drawdown,-12.3%,-18.7%,1.52
win_rate,54.2%,51.1%,0.94
profit_factor,1.38,1.12,0.81
total_trades,2847,892,0.31
calmar_ratio,1.18,0.44,0.37
```

The `ratio` column (OOS / IS) tells you how much the strategy degrades in the period the researcher could not see. Rules of thumb:
- Sharpe ratio > 0.5 → acceptable degradation
- Sharpe ratio < 0.5 → researcher overfitting likely, do not merge
- Sharpe ratio > 0.9 → suspiciously good, verify nothing is wrong

### Who Sees What

| Role | IS Data | OOS Data |
|------|---------|----------|
| Quant Researcher (Phases 1-5: research & design) | Full access | **NO ACCESS. NEVER.** |
| Quant Engineer (Phase 6: implementation & backtest) | Full access | Full access (walk-forward uses all data) |
| Quant Researcher (Phase 7: evaluation) | Reads IS report | Reads OOS report (**first time seeing OOS**) |

The critical restriction is on the **researcher during design phases**. When analyzing data, designing features, choosing labeling approaches, tuning strategy parameters, and writing the research brief — the researcher works ONLY with data before 2025-03-24. The OOS period exists so the researcher can honestly assess whether their design decisions generalize.

### Why This Works

The walk-forward backtest with monthly retraining already handles model-level integrity. Adding the researcher-level IS/OOS split on top gives you two layers of protection:

1. **Model level** (walk-forward): Each month's predictions use only past data. Prevents the model from seeing the future.
2. **Researcher level** (IS/OOS cutoff): The researcher's design decisions are based only on historical data. Prevents the researcher from unconsciously fitting to recent patterns.

If the walk-forward performance degrades significantly in the OOS window compared to IS, it means the researcher's choices (features, labeling, parameters) were tuned to patterns that existed in the IS period but didn't persist. That's the signal you need.

---

## Git & Code Management

### Branch Strategy

Every iteration lives on its own branch. Code only reaches `main` if the iteration beats the current baseline.

```
main (current best strategy)
 ├── iteration/001  (first attempt — becomes baseline if viable)
 ├── iteration/002  (beats baseline → merged to main)
 ├── iteration/003  (worse than baseline → branch kept, only diary/briefs cherry-picked)
 └── iteration/004  (beats baseline → merged to main)
```

### Starting an Iteration

```bash
git checkout main
git pull
git checkout -b iteration/NNN
```

All work (code, notebooks, diary, briefs) happens on the iteration branch. No direct commits to `main` during an iteration.

### Commit Discipline

Commits on the iteration branch MUST be separated by concern. This is non-negotiable because it enables clean cherry-picks from failed iterations.

Use this commit structure (in order):

1. **Code commits** — all `src/` changes, feature engineering, labeling, model, backtest logic. Prefix: `feat(iter-NNN):` or `fix(iter-NNN):`
2. **Research brief commit** — a SINGLE commit containing only `briefs/iteration_NNN/research_brief.md`. Message: `docs(iter-NNN): research brief`
3. **Engineering report commit** — a SINGLE commit containing only `briefs/iteration_NNN/engineering_report.md`. Message: `docs(iter-NNN): engineering report`
4. **Diary commit** — a SINGLE commit containing only `diary/iteration_NNN.md`. This MUST be the last commit on the branch. Message: `docs(iter-NNN): diary entry`

Why this order matters: commits 2, 3, and 4 are pure file additions in their own directories. They never conflict with `main`. When an iteration fails, you cherry-pick exactly these commits. If diary and code are mixed in the same commit, this falls apart entirely.

### After Evaluation: The Merge Decision

The Quant Researcher evaluates reports and writes the diary entry. Then:

**If iteration BEATS baseline** (see Baseline Rules below):

```bash
# On main
git checkout main
git merge iteration/NNN --no-ff -m "merge(iter-NNN): [1-line summary of what improved]"

# Update baseline
# Edit BASELINE.md with new metrics from diary
git add BASELINE.md
git commit -m "baseline: update after iteration NNN"

# Tag for easy reference
git tag -a v0.NNN -m "Iteration NNN: OOS Sharpe X.XX, MaxDD Y.Y%"
```

**If iteration is WORSE than baseline**:

```bash
# On main — cherry-pick ONLY documentation commits
git checkout main
git cherry-pick <brief-commit-hash>
git cherry-pick <engineering-report-commit-hash>
git cherry-pick <diary-commit-hash>
```

The branch is NOT deleted. It stays in the repo as a record. But it is never merged.

**If this is iteration 001** (no baseline yet):

The first iteration always merges to main (there is nothing to compare against). It becomes the initial baseline regardless of absolute performance. If results are clearly broken (negative expectancy before fees, zero trades, errors), fix the code on the same branch before merging — don't start a new iteration for bug fixes.

### Baseline Rules

`BASELINE.md` lives on `main` and is the source of truth for "current best". It is updated ONLY when a successful iteration merges.

**Primary metric**: Out-of-sample Sharpe ratio. An iteration must achieve a higher OOS Sharpe to be considered "better".

**Hard constraints** (must ALL be satisfied, or the iteration fails regardless of Sharpe):
- Max drawdown (OOS) ≤ current baseline OOS max drawdown × 1.2 (cannot worsen by more than 20%)
- Minimum 50 out-of-sample trades (prevents statistical flukes)
- Profit factor > 1.0 out-of-sample
- No single symbol contributes more than 30% of total OOS PnL (fragility check)
- IS/OOS Sharpe ratio > 0.5 (overfitting gate — if OOS Sharpe is less than half of IS Sharpe, the researcher's design decisions are overfit)

**Edge cases**:
- If OOS Sharpe improves but a hard constraint is violated → does NOT merge. Researcher documents the trade-off in the diary and proposes a fix for the next iteration.
- If OOS Sharpe is marginally better (< 0.05 improvement) but the strategy is structurally simpler → researcher MAY recommend merging with justification in the diary. Simpler strategies with equal performance are preferred.
- If two metrics improve significantly but Sharpe is flat → does NOT merge by default. The researcher can override with explicit justification in the diary, but the bar is high.

**Template for `BASELINE.md`**:

```markdown
# Current Baseline

Last updated by: iteration NNN (YYYY-MM-DD)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)
| Metric          | Value  |
|-----------------|--------|
| Sharpe          |        |
| Sortino         |        |
| Max Drawdown    |        |
| Win Rate        |        |
| Profit Factor   |        |
| Total Trades    |        |
| Calmar Ratio    |        |

## In-Sample Metrics (trades with entry_time < 2025-03-24)
| Metric          | Value  |
|-----------------|--------|
| Sharpe          |        |
| Sortino         |        |
| Max Drawdown    |        |
| Win Rate        |        |
| Profit Factor   |        |
| Total Trades    |        |
| Calmar Ratio    |        |

## Overfitting Diagnostics
| Metric   | IS     | OOS    | Ratio (OOS/IS) |
|----------|--------|--------|----------------|
| Sharpe   |        |        |                |
| Sortino  |        |        |                |
| Win Rate |        |        |                |

## Hard Constraints Status
| Constraint                        | Value  | Threshold | Pass |
|-----------------------------------|--------|-----------|------|
| Max Drawdown (OOS)                |        | ≤ X%      |      |
| Min OOS Trades                    |        | ≥ 50      |      |
| Profit Factor (OOS)               |        | > 1.0     |      |
| Max Single-Symbol PnL Contribution|        | ≤ 30%     |      |
| IS/OOS Sharpe Ratio               |        | > 0.5     |      |

## Strategy Summary
- Labeling: [method]
- Symbols: [universe]
- Features: [count]
- Validation: [method]

## Notes
[Any caveats about the current baseline]
```

### What Gets Tracked vs Ignored

**.gitignore additions** (add these to the existing `.gitignore`):

```gitignore
# Iteration artifacts — regenerable, large, binary
reports/
models/
analysis/

# Notebook outputs (keep .ipynb source, strip outputs before commit)
notebooks/.ipynb_checkpoints/
```

**Always tracked on `main`** (survives every iteration, win or lose):
- `diary/` — every iteration's diary entry
- `briefs/` — every iteration's research brief + engineering report
- `BASELINE.md` — current best metrics
- `CLAUDE.md` — Claude Code project instructions
- `src/` — production code (updated only by successful iterations)
- `tests/` — test suite
- `pyproject.toml`, `uv.lock`, config files

**Tracked on iteration branch only** (merged to main ONLY if iteration succeeds):
- `src/` changes (new/modified modules)
- `notebooks/` (researcher analysis notebooks)

**Never tracked**:
- `reports/` — backtest outputs (quantstats HTML, CSVs, etc.)
- `models/` — trained LightGBM artifacts (.pkl, .joblib, .txt)
- `analysis/` — EDA charts, plots, images
- `data/` — parquet data files

### Notebook Hygiene

Notebooks are useful for the researcher's analysis but toxic for git. Rules:

1. Strip output cells before committing: `uv run jupyter nbconvert --clear-output --inplace notebooks/*.ipynb`
2. Keep notebooks small and focused — one notebook per analysis question
3. All findings that matter MUST be written as text in the research brief or diary. Notebooks are working scratchpads, not documentation.
4. After a failed iteration, notebooks stay on the branch (not cherry-picked to main). The diary captures what was learned.

---

## Agent Roles

### Quant Researcher (QR)
Owns all decisions about **what** to do: data analysis, labeling, feature design, symbol selection, filtering, strategy evaluation, and the iteration diary. Does NOT write production code — only analysis notebooks/scripts and written briefs. Works EXCLUSIVELY with IS data (before 2025-03-24) during Phases 1-5. Only sees OOS results during Phase 7, when reading the reports the engineer generated.

### Quant Engineer (QE)
Owns all decisions about **how** to implement: production-quality Python code, pipeline architecture, backtest engine, report generation. Follows the researcher's spec exactly. Does NOT make research decisions — raises questions back to QR when spec is ambiguous. Runs the walk-forward backtest on the full dataset (IS + OOS), then splits the results at `OOS_CUTOFF_DATE` to produce two report batches.

### Handoff Protocol
- **QR → QE**: A structured `briefs/iteration_NNN/research_brief.md` (see template below)
- **QE → QR**: Backtest reports in `reports/iteration_NNN/{in_sample,out_of_sample}/` + `reports/iteration_NNN/comparison.csv` + `briefs/iteration_NNN/engineering_report.md`
- All handoffs are files in the repo, never verbal/implicit

---

## Execution Steps (in strict order)

### Phase 1: Exploratory Data Analysis (QR)

**Objective**: Understand the 8h candle data deeply before making any modeling decisions.

**DATA RESTRICTION**: Load ONLY data where `open_time < 2025-03-24`. If the data loading code does not filter by default, the researcher must apply the filter explicitly. Every notebook and script in this phase must start with this filter.

**Tasks**:
1. Load parquet files for a representative sample (e.g., top 20 by volume + 20 random mid/low-cap), filtered to IS period only
2. Compute per-symbol statistics: number of candles available, date range, missing data gaps, volume distribution
3. Analyze return distributions on 8h candles: fat tails, skewness, autocorrelation
4. **Regime identification**: Cluster market conditions using volatility (e.g., rolling ATR), trend strength (e.g., ADX or rolling slope), and correlation structure. Define at least 3 regimes (e.g., trending-volatile, mean-reverting-quiet, choppy-volatile). Tag each 8h candle with its regime
5. Analyze cross-symbol correlation structure: are there natural clusters? How does correlation change across regimes?
6. Check for survivorship bias: how many symbols were delisted? What's the distribution of symbol lifespans?

**Output**: `briefs/iteration_NNN/research_brief_phase1.md` with findings. Charts saved in `analysis/eda/` (untracked — findings must be described in text).

---

### Phase 2: Labeling Strategy (QR)

**Objective**: Define what the model is predicting. This determines everything downstream.

**DATA RESTRICTION**: All labeling analysis uses ONLY IS data (`open_time < 2025-03-24`).

**Tasks**:
1. Evaluate labeling approaches for 8h candles:
   - **Fixed-horizon return**: forward 1-candle (8h), 2-candle (16h), 3-candle (24h) returns
   - **Triple barrier method**: profit-take / stop-loss / max-holding-period barriers
   - **Trend-following labels**: label based on whether price continues in the direction of a detected trend
2. For each approach, analyze:
   - Class balance (long/short/neutral distribution)
   - Label stability (how often does the label flip on adjacent candles?)
   - Regime dependency (does one labeling method degrade in specific regimes?)
3. **Meta-labeling evaluation** (AFML Ch. 3):
   - Generate out-of-fold predictions from the primary model using PurgedKFoldCV
   - Label each prediction as 1 (would have been profitable) or 0 (would have lost)
   - Train a secondary model with features: primary confidence, NATR quartile, ADX regime, rolling 10-trade WR, hour_of_day
   - Compare: meta-labeled bet sizing vs fixed confidence threshold
   - Metric: IS Sharpe with meta-labeling vs IS Sharpe with current approach
4. **Sample overlap analysis** (AFML Ch. 4):
   - For the chosen labeling method, compute average label uniqueness (mean number of concurrent labels per timestamp)
   - If average uniqueness < 0.5 (each timestamp participates in 2+ labels), plan for uniqueness-based sample weighting
   - This determines whether the 4,400 "samples" are really 4,400 independent observations or closer to ~2,000 effective observations
5. **Decision**: Pick ONE labeling strategy with clear justification
6. Define the exact label generation function signature and parameters

**Output**: Labeling decision documented in `briefs/iteration_NNN/research_brief_phase2.md`

---

### Phase 3: Symbol Universe Selection (QR)

**Objective**: Decide whether to train on all ~800 symbols, a subset, or per-symbol models.

**DATA RESTRICTION**: All analysis uses ONLY IS data (`open_time < 2025-03-24`).

**Tasks**:
1. Analyze if a single model generalizes across symbols or if symbol-specific behavior dominates
2. Test grouping strategies:
   - **All symbols**: One model trained on pooled data
   - **Cluster-based**: Group symbols by sector/correlation cluster, one model per cluster
   - **Liquidity-tiered**: Top 50 by volume vs. rest
   - **Per-symbol**: Individual models (likely too few samples on 8h)
3. Consider sample size: with 8h candles, each symbol has ~1,095 candles/year. Per-symbol models may have insufficient data
4. **Decision**: Pick the symbol universe approach with justification

**Output**: Decision in `briefs/iteration_NNN/research_brief_phase3.md`

---

### Phase 4: Data Filtering (QR)

**Objective**: Decide if/how to filter data before feature engineering.

**DATA RESTRICTION**: All analysis uses ONLY IS data (`open_time < 2025-03-24`).

**Tasks**:
1. Evaluate whether adaptive spike range filter (or similar) is needed for 8h candles
2. Analyze outlier candles: flash crashes, exchange outages, extreme wicks
3. Decide on:
   - Outlier handling (clip, remove, winsorize)
   - Minimum volume thresholds
   - Minimum symbol history length
   - Whether to exclude specific date ranges (e.g., known exchange manipulation events)
4. **Decision**: Document exact filtering rules

**Output**: Filtering spec in `briefs/iteration_NNN/research_brief_phase4.md`

---

### Phase 5: Research Brief Compilation (QR → QE Handoff)

**Objective**: Compile all research decisions into a single actionable spec for the engineer.

**Git**: This is committed as a SINGLE standalone commit: `docs(iter-NNN): research brief`

**Template for `briefs/iteration_NNN/research_brief.md`**:

```markdown
# Research Brief: 8H LightGBM Iteration [N]

## 0. Data Split & Backtest Approach
- OOS cutoff date: 2025-03-24 (project-level constant, applies to all iterations)
- The researcher used ONLY IS data (before 2025-03-24) for all design decisions below
- The walk-forward backtest runs on the FULL dataset (IS + OOS) as one continuous process
- Monthly retraining with timeseries CV, 1-year minimum training window (existing approach, unchanged)
- The report layer splits backtest results at OOS_CUTOFF_DATE into two report batches

## 1. Labeling
- Method: [exact method]
- Parameters: [thresholds, horizons, barriers]
- Label function signature: [input/output spec]

## 2. Symbol Universe
- Approach: [all/clustered/tiered/per-symbol]
- Exact symbols or selection criteria: [list or rule]

## 3. Data Filtering
- Outlier handling: [method + thresholds]
- Volume filter: [min threshold]
- History filter: [min candles required]
- Date exclusions: [if any]

## 4. Feature Candidates
- Use existing features from the pipeline: [list which ones]
- New features to add: [list with exact computation spec]
- Feature selection method: [e.g., MDA-based pruning after first run]

## 4b. Stationarity Assessment (AFML Ch. 5)
- Non-stationary features identified: [list with ADF p-values]
- Fractional differentiation plan: [which features, target d values]
- Features to replace with fracdiff versions: [list]

## 5. Model Spec
- Model: LightGBM
- Task: [classification/regression]
- Hyperparameters: [starting params or "use Optuna"]
- Class weighting: [if classification, how to handle imbalance]
- Random seed: [fixed seed for reproducibility]

## 5b. Sample Weighting (AFML Ch. 4)
- Average label uniqueness: [value — compute from label overlap analysis]
- Weighting scheme: uniqueness * time_decay * abs_pnl
- Time decay half-life: [months]
- Effective independent samples: [estimate]

## 5c. Cross-Validation (AFML Ch. 7)
- Method: PurgedKFoldCV (n_splits=5, purge_window=[candles], embargo_pct=0.02)
- Effective training samples per fold after purging: [estimate]
- CPCV enabled: [yes/no — only if sample count > 3,000]

## 5d. Overfitting Budget (AFML Ch. 11)
- Current trial count: [N iterations]
- Deflated Sharpe threshold: [minimum OOS Sharpe to reject null]
- Expected max random Sharpe: [E[max(SR_0)] given N]

## 6. Walk-Forward Configuration
- Retraining frequency: monthly (existing)
- Minimum training window: 1 year (existing)
- CV method: PurgedKFoldCV with embargo (replaces TimeSeriesSplit)
- CV folds: [number]
- Purge window: [candles, derived from timeout_minutes / candle_hours]
- Embargo: 2% of training set

## 7. Backtest Requirements
- Position sizing: [fixed fractional / volatility-scaled / equal-weight]
- Fees: Binance futures taker/maker rates (already implemented)
- Funding rate: [include or exclude]
- Slippage model: [fixed bps or volume-dependent]
- Max positions: [concurrent position limit]
- Risk limits: [max drawdown threshold, per-trade stop-loss]

## 8. Report Requirements
Two separate report directories split at OOS_CUTOFF_DATE: in_sample/ and out_of_sample/
Each containing:
- Per-trade log with entry/exit prices, PnL, holding period
- Daily/monthly PnL aggregation
- Quantstats tearsheet (already integrated)
- Per-regime performance breakdown
- Per-symbol attribution (top/bottom contributors)
- Feature importance ranking (IS only)

Plus a comparison.csv with side-by-side IS vs OOS metrics and OOS/IS ratios.
```

---

### Phase 6: Implementation (QE)

**Objective**: Build the full pipeline following the research brief exactly.

**Tasks**:
1. **[ITERATION 001 PRIORITY]** Implement the report-splitting layer:
   - Define `OOS_CUTOFF_DATE = "2025-03-24"` as a project-level constant in `src/crypto_trade/config.py`
   - After the walk-forward backtest completes, split the trade results at `OOS_CUTOFF_DATE`
   - Generate `in_sample/` reports from trades with `entry_time < OOS_CUTOFF_DATE`
   - Generate `out_of_sample/` reports from trades with `entry_time >= OOS_CUTOFF_DATE`
   - Generate `comparison.csv` with side-by-side metrics and OOS/IS ratios
2. Implement labeling function per spec
2b. **Replace TimeSeriesSplit with PurgedKFoldCV** (AFML Ch. 7): Implement purged cross-validation with embargo in `src/crypto_trade/strategies/ml/purged_cv.py`. Parameters: purge_window = timeout_minutes / (candle_hours * 60) candles, embargo_pct = 0.02. Update `optimization.py` to use PurgedKFoldCV instead of TimeSeriesSplit.
2c. **Implement sample uniqueness weighting** (AFML Ch. 4): Add `compute_sample_uniqueness()` to labeling.py. Combine with existing |PnL| weights and time decay before passing to LightGBM.
2d. **Implement MDA feature importance** (AFML Ch. 8): Add `compute_mda_importance()` to compute permutation importance using Sharpe as the scoring metric on validation folds. Report alongside MDI in feature_importance.csv.
3. Implement data filtering per spec
4. Generate features (extend existing pipeline with any new features from brief, including fracdiff if specified)
5. Configure walk-forward parameters per spec (retraining frequency, PurgedKFoldCV, embargo)
6. Run walk-forward backtest on the FULL dataset (IS + OOS combined, no artificial split at model level)
7. Generate split reports
8. Save trained model artifacts and feature importance (both MDI and MDA)

**Code quality requirements**:
- All new code must have type hints
- Functions must be pure where possible (no hidden state)
- Backtest must be deterministic (same input → same output, given fixed seed)
- No lookahead bias within the walk-forward (verify with `assert` checks on date ordering per monthly fold)
- Tests for critical functions (labeling, feature generation, PnL calculation)

**Git**: Code commits use prefix `feat(iter-NNN):` or `fix(iter-NNN):`. Engineering report is committed separately: `docs(iter-NNN): engineering report`

**Output**:
- Code committed to iteration branch
- Reports saved in `reports/iteration_NNN/{in_sample,out_of_sample}/` (untracked)
- `reports/iteration_NNN/comparison.csv` (untracked)
- `briefs/iteration_NNN/engineering_report.md` documenting any deviations from the research brief and why

---

### Phase 7: Evaluation & Merge Decision (QR)

**Objective**: Assess backtest results, decide merge/no-merge, write diary.

This is the FIRST and ONLY time the researcher sees OOS results.

**Tasks**:
1. Open `reports/iteration_NNN/comparison.csv` — start here. Look at the OOS/IS ratios first. If the Sharpe ratio is < 0.5, the researcher's design decisions are likely overfit to the IS period. Note this immediately.
2. Review OOS quantstats report: Sharpe, Sortino, max drawdown, Calmar ratio
3. Review IS quantstats report: compare with OOS. Large gaps indicate the researcher's feature/labeling/parameter choices don't generalize.
4. Review OOS per-regime breakdown: does the strategy survive all regimes or only thrive in one?
5. Review OOS per-symbol attribution: are returns concentrated in a few symbols?
6. Review IS feature importance: do the top features make economic sense?
7. **Red flags to check**:
   - OOS Sharpe < 50% of IS Sharpe → researcher overfitting (also a hard constraint)
   - Performance concentrated in 1 regime in OOS → not regime-robust
   - Top 3 symbols account for >50% of OOS PnL → fragile
   - Features with high importance but no economic intuition → suspicious
   - OOS max drawdown significantly worse than IS → possible regime shift or overfit parameters
8. **Compare against `BASELINE.md`**: Check primary metric (OOS Sharpe) and ALL hard constraints
9. **Deflated Sharpe check** (AFML Ch. 11): Compute DSR accounting for all N iterations run to date. If DSR < 0, the OOS Sharpe is within the expected range of random trials. Note this in the diary but do not automatically NO-MERGE — the strategy may still have genuine signal that needs more OOS data to confirm.
10. **PBO check** (if CPCV available): Compute Probability of Backtest Overfitting from CPCV paths. Report in diary.
11. **Merge decision**: Document as MERGE or NO-MERGE with justification

**Output**: `diary/iteration_NNN.md` (see template below), committed as the LAST commit on the branch: `docs(iter-NNN): diary entry`

---

### Phase 8: Diary Entry (QR)

**Template for `diary/iteration_NNN.md`**:

```markdown
# Iteration [N] Diary - [Date]

## Merge Decision: [MERGE / NO-MERGE]
Justification: [why this iteration does or does not beat the baseline]

## Hypothesis
What was the core hypothesis for this iteration?

## Configuration Summary
- OOS cutoff: 2025-03-24 (fixed)
- Labeling: [method]
- Symbols: [universe]
- Features: [count, key ones]
- Walk-forward: monthly retraining, [N] CV folds, [min training window]
- Random seed: [value]

## Results: In-Sample (trades with entry_time < 2025-03-24)
| Metric | Value |
|--------|-------|
| Sharpe | |
| Sortino | |
| Max Drawdown | |
| Win Rate | |
| Profit Factor | |
| Total Trades | |
| Calmar Ratio | |

## Results: Out-of-Sample (trades with entry_time >= 2025-03-24)
| Metric | Value | Baseline OOS |
|--------|-------|--------------|
| Sharpe | | |
| Sortino | | |
| Max Drawdown | | |
| Win Rate | | |
| Profit Factor | | |
| Total Trades | | |
| Calmar Ratio | | |

## Overfitting Diagnostics (Researcher Bias Check)
| Metric   | IS     | OOS    | Ratio (OOS/IS) | Assessment |
|----------|--------|--------|----------------|------------|
| Sharpe   |        |        |                |            |
| Sortino  |        |        |                |            |
| Win Rate |        |        |                |            |

## Hard Constraints Check (all evaluated on OOS)
| Constraint                        | Value  | Threshold | Pass |
|-----------------------------------|--------|-----------|------|
| Max Drawdown                      |        | ≤ X%      |      |
| Min OOS Trades                    |        | ≥ 50      |      |
| Profit Factor                     |        | > 1.0     |      |
| Max Single-Symbol PnL Contribution|        | ≤ 30%     |      |
| IS/OOS Sharpe Ratio               |        | > 0.5     |      |

## Per-Regime Performance (OOS)
| Regime | Sharpe | # Trades | Win Rate |
|--------|--------|----------|----------|
| Trending-Volatile | | | |
| Mean-Reverting-Quiet | | | |
| Choppy-Volatile | | | |

## What Worked
- [finding 1]
- [finding 2]

## What Failed
- [finding 1]
- [finding 2]

## Overfitting Assessment
[Honest narrative assessment. The IS/OOS gap reflects whether the researcher's
design choices generalize — not model leakage (walk-forward handles that).
A large gap means features, labeling, or parameters were tuned to IS-period
patterns that didn't persist. What specifically might have caused this?]

## Next Iteration Ideas
- [idea 1: what to change and why]
- [idea 2: what to change and why]

## MLP Diagnostics (AFML)
| Metric | Value |
|--------|-------|
| Deflated Sharpe Ratio (DSR) | |
| Expected max random Sharpe (N=?) | |
| Average label uniqueness | |
| PBO (if CPCV used) | |
| Non-stationary features used | |
| CV method | [PurgedKFoldCV / TimeSeriesSplit] |

## Lessons Learned
- [insight that applies beyond this specific iteration]
```

---

## Critical Rules

1. **OOS cutoff date is 2025-03-24 and NEVER changes**: This is a project-level constant. Every iteration uses the same split. If you change it, all previous baselines and diary comparisons become meaningless
2. **The researcher NEVER sees OOS data during Phases 1-5**: All exploratory analysis, labeling experiments, feature brainstorming, parameter tuning, and hypothesis formation use ONLY IS data (before 2025-03-24)
3. **The walk-forward backtest runs on ALL data**: The IS/OOS split does NOT affect the backtest or the model. The walk-forward runs on the full dataset as one continuous process. The split is applied ONLY at the reporting layer
4. **The reporting layer splits results into two batches**: `in_sample/` and `out_of_sample/` directories plus `comparison.csv`. This report-splitting is a required engineering feature from iteration 001
5. **No lookahead bias within walk-forward**: Each monthly fold trains only on past data. Verify with `assert` checks on date ordering within each fold
6. **Diary is mandatory**: Every iteration must produce a diary entry, even if results are bad. Especially if results are bad
7. **One variable at a time**: Each iteration should change ONE major thing from the previous iteration (labeling OR features OR symbol universe, not all at once). This makes the diary useful
8. **Researcher does not touch engineer's code**: If the researcher wants something changed, it goes in the next research brief
9. **Engineer does not make research decisions**: If something is ambiguous in the brief, the engineer asks the researcher rather than guessing
10. **Commit discipline is sacred**: Documentation commits (brief, engineering report, diary) MUST be separate from code commits. Never mix them. This enables clean cherry-picks from failed iterations
11. **Branches are never deleted**: Failed iteration branches stay in the repo as archaeological records
12. **Baseline is the gatekeeper**: No code reaches `main` without beating `BASELINE.md` on the primary metric (OOS Sharpe) AND satisfying all hard constraints including the IS/OOS Sharpe ratio gate

---

## Directory Structure

```
crypto-trade/
├── .claude/
│   └── skills/
│       └── quant-iteration/
│           └── SKILL.md             # Claude Code skill for this workflow
├── briefs/                          # Always tracked — survives every iteration
│   ├── iteration_001/
│   │   ├── research_brief.md
│   │   ├── research_brief_phase1.md
│   │   ├── research_brief_phase2.md
│   │   ├── research_brief_phase3.md
│   │   ├── research_brief_phase4.md
│   │   └── engineering_report.md
│   └── iteration_002/
│       └── ...
├── diary/                           # Always tracked — survives every iteration
│   ├── iteration_001.md
│   └── iteration_002.md
├── reports/                         # UNTRACKED (.gitignore)
│   └── iteration_001/
│       ├── in_sample/
│       │   ├── quantstats.html
│       │   ├── trades.csv
│       │   ├── daily_pnl.csv
│       │   ├── monthly_pnl.csv
│       │   ├── per_regime.csv
│       │   ├── per_symbol.csv
│       │   └── feature_importance.csv
│       ├── out_of_sample/
│       │   ├── quantstats.html
│       │   ├── trades.csv
│       │   ├── daily_pnl.csv
│       │   ├── monthly_pnl.csv
│       │   ├── per_regime.csv
│       │   └── per_symbol.csv
│       └── comparison.csv
├── models/                          # UNTRACKED (.gitignore)
├── analysis/                        # UNTRACKED (.gitignore)
├── src/crypto_trade/                # Tracked — updated only by successful iterations
│   ├── config.py                    # OOS_CUTOFF_DATE lives here
│   ├── features/
│   ├── labeling/
│   ├── models/
│   ├── backtest/
│   └── reports/
├── notebooks/                       # Tracked on branch, merged only if iteration succeeds
├── tests/                           # Tracked
├── data/                            # UNTRACKED (.gitignore)
├── BASELINE.md                      # Tracked — updated only on successful merges
├── CLAUDE.md                        # Tracked
├── ITERATION_PLAN_8H.md             # This file — tracked
├── pyproject.toml
└── uv.lock
```

---

## How to Use This Plan with Claude Code

The skill at `.claude/skills/quant-iteration/SKILL.md` provides Claude Code with the workflow context. When starting work, tell Claude Code which role and phase:

**Starting a new iteration:**
> "Start iteration NNN. You are the Quant Researcher. Create the branch `iteration/NNN` from main, then execute Phase 1 (EDA). Read ITERATION_PLAN_8H.md for the full workflow. Remember: you work ONLY with IS data (before 2025-03-24)."

**Handing off to engineer:**
> "You are the Quant Engineer for iteration NNN. Read the research brief at `briefs/iteration_NNN/research_brief.md` and execute Phase 6. The walk-forward backtest runs on ALL data. After it completes, split the reports at OOS_CUTOFF_DATE. Follow commit discipline from ITERATION_PLAN_8H.md."

**Evaluation and merge decision:**
> "You are the Quant Researcher. Evaluate the reports in `reports/iteration_NNN/`, starting with comparison.csv. Compare OOS results against BASELINE.md, write the diary entry, and execute the merge decision per ITERATION_PLAN_8H.md."

For the first iteration, start with Phase 1 and work through sequentially. For subsequent iterations, read the previous diary's "Next Iteration Ideas" and start at Phase 2 (or wherever the change is).
