# Two Agents, 140 Iterations, and the Git Workflow That Taught Them to Be Honest

## Or: how I turned a trading bot into a self-improving research lab

There's a moment that happens somewhere around iteration 50 when you stop looking at the metrics and start looking at the **process**. You realize the interesting thing is no longer "is this strategy profitable." The interesting thing is: *how did the system get here, and can it keep going without me?*

Today the baseline reads **OOS Sharpe +2.32, Max Drawdown 62.8%, Win Rate 50.6%, 164 trades, +172% net PnL** on held-out data the model never trained on. That's iteration 138. The system is currently chewing through iteration 140 while I write this.

I didn't do it. Two agents did it. And the most beautiful thing in the whole project isn't the LightGBM model — it's the git workflow that keeps them honest.

Let me show you.

---

## The Setup: Two Roles, One Repo, One Absolute Rule

The `quant-iteration` skill defines two personas that take turns:

**The Quant Researcher (QR)** does data analysis, designs labels, picks symbols, writes research briefs, evaluates results, and decides whether an iteration is worth keeping. The QR is allowed to see IS data (everything before `2025-03-24`) and nothing else. No notebooks touching OOS. No peeking. Ever.

**The Quant Engineer (QE)** writes production code in `src/`, runs walk-forward backtests on the full dataset, splits results at the cutoff, and hands IS + OOS reports back. The QE does not make research decisions. If the brief is ambiguous, the QE stops and asks.

And above them both, one rule carved into the skill file in all caps:

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

This is the only thing between you and self-deception. A human quant researcher will unconsciously tune their features to "recent" patterns they've seen in the price history. They won't mean to. It happens anyway. The cutoff exists so that *the QR literally cannot see* what the strategy has to survive in Phase 7.

The first time each iteration's QR sees its OOS results, the decision is binary: **MERGE** or **NO-MERGE**.

No edits. No "let me just retune one knob." The number is the number.

---

## The Loop

Every iteration is eight phases:

1. **EDA** — QR explores IS data
2. **Labeling** — QR decides how trades are labeled
3. **Symbol Universe** — QR picks which coins the model trades
4. **Data Filtering** — QR decides what to keep or drop
5. **Brief Compilation** — QR writes a single document the QE will implement
6. **Implementation** — QE writes the code, runs the backtest, generates reports, validates seeds
7. **Evaluation** — QR opens the OOS reports for the first time, checks hard constraints, compares to baseline
8. **Diary** — QR writes what happened, what worked, what didn't, what to try next

Then the skill runs the loop again. Automatically. The next iteration reads the previous diary's "Next Iteration Ideas" section and starts Phase 1. No human intervention. It just keeps going.

After 140 iterations, there are 118 failed hypotheses and 22 successful merges. Every single one is still there, readable, traceable.

That is because of what I think is the most elegant part of the whole system.

---

## The Git Workflow — The Actual Art

Here's where it gets good.

Every iteration lives on its own branch: `iteration/NNN`. On that branch, commits are **strictly separated** by type, in strict order:

1. Code commits: `feat(iter-NNN):` or `fix(iter-NNN):`
2. Research brief: `docs(iter-NNN): research brief` — **one commit**
3. Engineering report: `docs(iter-NNN): engineering report` — **one commit**
4. Diary: `docs(iter-NNN): diary` — **always the last commit on the branch**

Why this obsessive discipline? Because of what happens at the end.

### When the iteration wins (MERGE)

```bash
git checkout main
git merge iteration/NNN --no-ff
# update BASELINE.md with the new numbers
git tag -a v0.NNN -m "Iteration NNN: OOS Sharpe X.XX, MaxDD Y.Y%"
```

The code, brief, report, and diary all land on main. The baseline moves. A tag marks the milestone.

### When the iteration loses (NO-MERGE)

```bash
git checkout main
git cherry-pick <research-brief-commit>
git cherry-pick <engineering-report-commit>
git cherry-pick <diary-commit>
```

**The code never touches main. The knowledge does.**

Read that again. This is the trick.

The research brief, the engineering report, and the diary — the three documents that explain *what we tried, what happened, and why we're not keeping it* — get cherry-picked into main as pure documentation. The broken code stays quarantined on the iteration branch. Forever.

This is why commits must be strictly separated. If the diary commit contained code changes, cherry-picking it would drag the broken strategy into main. So the skill enforces: **diary is its own commit, last on the branch, no code in it. Ever.**

And this is why iteration branches are **never deleted**. Every failure is a permanent, reproducible artifact. If you want to know exactly what Model A colsample_bytree 0.3–0.5 restriction did in iteration 140, you `git checkout iteration/140` and run it. You get the same -0.35 OOS Sharpe we got. The failure is a scientific record.

The git log on main looks like this:

```
b079782 docs(iter-139): diary — NO-MERGE, ETH standalone fails Gate 3, pooling essential
16dd760 baseline: update after iteration 138 — A(ATR)+C+D portfolio OOS Sharpe +2.32
96f4298 merge(iter-138): A(ATR)+C+D portfolio, OOS Sharpe +2.32, ATR labeling on Model A
c8a19de docs(iter-138): diary — MERGE, A(ATR)+C+D portfolio OOS Sharpe +2.32, best ever
828beeb docs(iter-138): engineering report — A(ATR)+C+D portfolio OOS Sharpe +2.32, WR 50.6%
955043e docs(iter-138): research brief — A(ATR)+C+D portfolio milestone
2fc2c78 docs(iter-137): diary — NO-MERGE pending portfolio, Model A ATR OOS Sharpe +1.67
```

Every line is a hypothesis, a test, and a verdict. The ledger is the model. The git history *is* the research journal.

---

## The NO-CHEATING Rules

The skill file has a section titled **NO CHEATING — ABSOLUTE RULES**. It reads like a list of temptations the system is forbidden from indulging:

- **Never change `start_time`** to skip bad IS months. The backtest runs from the earliest data. Trimming is cheating — it hides losses instead of fixing the strategy.
- **Never cherry-pick date ranges** to make IS or OOS look better.
- **Never post-hoc filter trades** to improve metrics.
- **Never tune parameters on OOS data.**
- **Never allow labels to leak across CV fold boundaries.** The `gap` must equal `(timeout_candles + 1) × n_symbols`. The QE must verify this every iteration. Iteration 089 proved that leaked labels inflate CV Sharpe by 5–10x.

These are rules the agents must internalize because nobody else is watching. When the QE runs a backtest at 2am on iteration 127, it's the skill file that tells it: *do not move the start date, fix the strategy instead.*

There's also **seed robustness validation**: before any MERGE, the QE must rerun the same config with 5 seeds (42, 123, 456, 789, 1001). At least 4 must be profitable. Mean must be positive. This rule was born in iteration 038, where seed=42 gave OOS Sharpe +1.33 and seed=123 gave -1.15. Without this check, we'd have believed the strategy was 3x better than it actually is.

Every one of these rules is a scar from a previous failure. The skill file is not a specification. It's a memoir.

---

## What Actually Happened in 140 Iterations

The headline: a portfolio of three LightGBM models — Model A (BTC+ETH pooled), Model C (LINK), Model D (BNB) — each trained on 24 months of walk-forward data with monthly retraining, 5 CV folds, 50 Optuna trials, 5-seed ensembles, 196 features, ATR-based TP/SL labeling aligned with execution.

OOS Sharpe **+2.32**. MaxDD **62.8%**. WR **50.6%**. Calmar **2.74**. +**172%** net PnL on data the researcher has never touched.

The journey to get here:

- Iterations 1–30: figuring out what features even work on 8h candles
- Iterations 30–60: labeling experiments, CV gap discovery, seed sweeps
- Iterations 60–90: the painful discovery that labels leak if you're not careful
- Iterations 90–120: symbol universe expansion, filtering strategies, the parquet rewrite
- Iterations 120–138: ATR labeling, portfolio construction, the breakthrough
- Iteration 138: **the single biggest improvement in 138 iterations** — one boolean flag, `use_atr_labeling=True` on Model A, aligned the training labels with execution barriers. OOS Sharpe jumped from +1.94 to +2.32. ETH's win rate jumped from 45.5% to 55.9%. In hindsight it was obvious: the model was training on 8%/4% static labels but executing with variable ATR barriers. They didn't match. Once they did, everything clicked.

118 iterations did not merge. Each one is documented, reproducible, and taught us something.

---

## Why This Matters

I don't think the important thing here is the trading strategy. Strategies decay. Markets change.

The important thing is that the **process** survives. A two-agent loop, constrained by a cutoff date it cannot move, disciplined by a git workflow that physically separates knowledge from code, auditable back to the first commit, where every failure is a permanent teacher and every success requires 5 seeds to prove itself — this is a machine that can keep learning long after I stop watching.

It runs overnight. It reads its own diary. It proposes the next hypothesis. It writes the brief, implements the code, runs the backtest, evaluates the result, decides MERGE or NO-MERGE, updates the baseline, writes tomorrow's plan, and starts the next iteration.

140 iterations in. Counting.

The model is good. The workflow is the art.

---

*The crypto-trade repo runs on Claude Code with the `quant-iteration` skill as a quick reference, plus `ITERATION_PLAN_8H.md` for the full eight-phase plan and templates. Together they define the no-cheating rules, the seed validation protocol, and the git workflow the agents follow before every iteration.*

*Every number in this post is pulled from `BASELINE.md` in the repo at iteration 138. The OOS cutoff has not moved. It will not move.*
