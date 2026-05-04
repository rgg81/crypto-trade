---
name: quant-iteration-v3
description: "Quant research/engineering iteration workflow for the crypto-trade LightGBM strategy — v3 TRACK (rigor upgrade: minimize seed bias and overfitting via mandatory CPCV, PBO, PSR, meta-labeling, fractional differentiation with ADF, crypto-native features, three-role workflow with adversarial Critic review). Use this skill whenever the user mentions: v3 iteration, quant-iteration-v3, iter-v3, iter-v3/NNN, BASELINE_V3, briefs-v3, diary-v3, reports-v3, ITERATION_PLAN_8H_V3, run_baseline_v3, v3 research brief, v3 diary, v3 merge decision, v3 baseline comparison, Phase 5.5, Phase 7.5, Critic agent, Critic review, review.md, Pareto front, Pareto dominance, meta-labeling, primary plus meta model, fractional Kelly, fractional differentiation ADF, ADF stationarity, funding rate features, basis features, open interest features, liquidation features, V3_EXCLUDED_SYMBOLS, features_v3, validation_v3, CPCV mandatory, PBO < 0.4, PSR > 0.95, pre-registered failure mode, pre-registered MERGE/NO-MERGE criteria, library stack declaration. Also trigger when the user says: 'start v3 iteration', 'run v3 phase', 'evaluate v3 reports', 'write v3 diary', 'v3 merge decision', 'invoke Critic'."
---

# Quant Iteration Skill — v3 (Rigor Arm)

## Mission

v3 exists for one reason: **to minimize seed bias and overfitting**. Every methodological gap that v2's 69 iterations exposed gets a structural defense in v3. Where v2 reports DSR, v3 also reports PBO and PSR with hard pass thresholds. Where v2 runs single-path walk-forward, v3 runs CPCV with 45 paths. Where v2 has two roles (QR/QE), v3 has three (QR/QE/Critic) — the Critic's adversarial review is a structural gate, not a suggestion. Where v2's Phase 5 brief can be rubber-stamped, v3's Phase 5.5 gate forces the Engineer to refuse incomplete briefs.

v3 is the rigor arm of the crypto-trade strategy stack. It coexists with v1 (main, BTC/ETH/LINK/LTC/DOT) and v2 (quant-research worktree, SOL/XRP/DOGE/NEAR) as a sibling track. **v3 picks a fresh symbol universe** in iter-v3/001's brief — no inheritance from v1 or v2. The v3 universe must exclude every symbol already traded in v1 or v2, forcing genuine diversification across all three tracks.

If v3 rediscovers v1's or v2's symbols, features, or risk regimes — it has failed at its only job. v3 is methodology + diversification.

The combined portfolio (v1 + v2 + v3) must have lower correlation, better tail behavior, and higher risk-adjusted returns than any single track alone. v3 is the third leg of that stool.

We do not predict the future. We identify moments when the distribution of forward returns is skewed in our favor, and we bet accordingly, sized by our conviction and disciplined by our risk framework. We build strategies that would survive scrutiny by the most rigorous quantitative finance researchers — López de Prado, Bailey, Harvey, Carver. **No p-hacking. No overfitting. No self-deception.** If a strategy cannot withstand combinatorial purged cross-validation, deflated Sharpe ratio tests, probability-of-backtest-overfitting tests, AND adversarial Critic review, it does not trade.

---

## Relationship to v1 and v2

Three sibling tracks. They coexist; none is frozen. The user can run any of `/quant-iteration`, `/quant-iteration-v2`, `/quant-iteration-v3` at any time.

| Aspect | v1 (main) | v2 (quant-research) | v3 (quant-research) |
|---|---|---|---|
| Symbols | BTC, ETH, LINK, LTC, DOT | SOL, XRP, DOGE, NEAR | TBD by iter-v3/001 brief (must exclude all v1+v2 symbols) |
| Features | `crypto_trade.features` (193 cols, 9 groups) | `crypto_trade.features_v2` (34 cols after pruning) | `crypto_trade.features_v3` (new package from iter-v3/001) |
| Risk layers | R1+R2+R3 | RiskV2Wrapper (7 active gates) | Inherits v2's structure; adds CPCV-derived path-level diagnostics |
| Validation | sklearn TimeSeriesSplit, DSR | TimeSeriesSplit + DSR | **CPCV mandatory** + DSR + PBO + PSR (all four with hard thresholds) |
| Position sizing | ATR-percentile vol scaling | Same | **Meta-labeling** (M1+M2) → fractional Kelly from iter-v3/002 |
| Roles | QR + QE | QR + QE | **QR + QE + Critic** (read-only adversarial reviewer) |
| Phases | 8 | 8 | **10** (8 + Phase 5.5 gate + Phase 7.5 Critic review) |
| Branch | `main` ← `iteration/NNN` | `quant-research` ← `iteration-v2/NNN` | `quant-research` ← `iteration-v3/NNN` |
| Tag | `v0.NNN` | `v0.v2-NNN` | `v0.v3-NNN` |
| Reports | `reports/iteration_NNN/` | `reports-v2/iteration_v2-NNN/` | `reports-v3/iteration_v3-NNN/` |
| Briefs | none structured | `briefs-v2/iteration_v2-NNN/` | `briefs-v3/iteration_v3-NNN/` (incl. `phase5p5_gate.md`, `review.md`) |
| Diaries | `diary/iteration_NNN.md` | `diary-v2/iteration_v2-NNN.md` | `diary-v3/iteration_v3-NNN.md` |
| Auto-trigger | `iteration`, `BASELINE.md` | `v2 iteration`, `BASELINE_V2.md`, `iter-v2/NNN` | `v3 iteration`, `iter-v3/NNN`, `Phase 5.5`, `Phase 7.5`, `Critic`, `PBO < 0.4` |

**Shared (sacred across all three tracks):**
- `OOS_CUTOFF_DATE = 2025-03-24` — immutable
- `training_months = 24` — immutable
- 8h candles
- Inner ensemble seeds `[42, 123, 456, 789, 1001]` (5-seed v1-style)
- 10-seed pre-MERGE concentration validation
- Hard merge floor: IS Sharpe > 1.0 AND OOS Sharpe > 1.0
- ≥10 trades/month OOS, ≥130 OOS total
- Top symbol concentration ≤ 30% of OOS PnL (or explicit exception with justification)
- "QR uses IS data" — every Phase 5 brief must contain numerical tables from a committed `analysis/iteration_*/` script
- Walk-forward backtest runs on full data; reports split at `OOS_CUTOFF_DATE`
- Forming candles must be dropped (`fetcher.py:if k.close_time < now_ms`)

**v3-only:**
- CPCV with N=10, k=2 → 45 backtest paths (mandatory from iter-v3/001)
- PBO threshold < 0.4 (hard NO-MERGE if violated)
- PSR threshold > 0.95 (hard NO-MERGE)
- DSR threshold > 0.95 (hard NO-MERGE)
- IC < 0.7 between any new feature family and existing families (Critic enforces)
- ADF p < 0.05 on every feature (Critic enforces; non-stationary features need explicit "regime indicator" justification)
- Meta-labeling architecture (M1 direction + M2 size) — mandatory from iter-v3/001
- Three-role workflow with Critic adversarial review (Phase 7.5)
- Pre-registered failure-mode prediction (brief Section 7)
- Pre-registered MERGE/NO-MERGE numerical criteria (brief Section 8)
- Library stack declaration (brief Section 9)

---

## Before You Start

Read these files in order, EVERY time this skill is triggered:

1. **`ITERATION_PLAN_8H_V3.md`** at the repo root — the v3 workflow doc (mirrors v2's plan with v3 distinctives)
2. **`BASELINE_V3.md`** at the repo root — current v3 baseline metrics, hard constraints, V3_EXCLUDED_SYMBOLS
3. **The last 3 entries in `diary-v3/`** — what's recently been tried; "Next Iteration Ideas" from the last diary often seeds the next iteration
4. **This skill file** (`.claude/commands/quant-iteration-v3.md`) — the workflow definition
5. **`/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/MEMORY.md`** — active decisions and feedback rules

**Note:** for iter-v3/001 specifically, also read `BASELINE_V2.md` to understand what v3 is diverging from. There is NO virtual `iter-v3/000` baseline — v3 starts genuinely fresh.

### Default Flow: Full Autopilot

When this skill is triggered, **do NOT ask which role to play or whether to proceed**. Default behavior:

1. Read the last v3 diary's "Next Iteration Ideas" and `BASELINE_V3.md`
2. Determine the next iteration number (next iter-v3/NNN)
3. Run the full flow:
   - QR Phases 1–5 (research design, brief authoring) — uses `quant-researcher` agent
   - **Phase 5.5 Gate** — `quant-engineer` agent verifies brief completeness; PASS or BLOCK
   - QE Phase 6 (implementation + backtest) — `quant-engineer` agent
   - **Phase 7.5 Critic Review** — `quant-critic` agent (read-only); emits `review.md`; OVERALL=MERGE or BLOCK
   - QR Phase 7 (OOS evaluation) — `quant-researcher` agent
   - QR Phase 8 (diary + merge decision) — `quant-researcher` agent
4. Commit/tag per the v3 git workflow
5. After completing Phase 8, **immediately start the next iteration** — go back to step 1
6. Keep looping iterations until the user intervenes or context runs out
7. Only pause if there's an actual blocker (ambiguous brief that the QR can't resolve, unexpected error, decision that genuinely requires user input)

The user can override by specifying a role ("be the QR for iter-v3/003"), a phase ("run Phase 6"), or a track ("/quant-iteration-v2 instead"). Otherwise, go.

---

## NO CHEATING — ABSOLUTE RULES

**NEVER** do any of the following to improve metrics artificially:

- **NEVER change `start_time`** to skip bad IS months. The backtest MUST run from the earliest available data. Trimming the evaluation window is CHEATING — it hides losses instead of fixing the strategy.
- **NEVER cherry-pick date ranges** to make IS or OOS look better.
- **NEVER post-hoc filter trades** from the results to improve metrics.
- **NEVER tune parameters on OOS data** (the researcher sees OOS only in Phase 7).
- **NEVER allow labels to leak across CV fold boundaries.** The `gap` parameter MUST be set correctly: `gap = (timeout_candles + 1) × n_symbols`. The QE MUST verify this in EVERY iteration. This is non-negotiable — iter 089 (v1) proved that leaked labels inflate CV Sharpe by 5-10x.
- **NEVER allow labels to leak from live/prediction data to training data.** Each month's model trains ONLY on past klines. Labels for training samples must not scan past the training window boundary.
- **NEVER skip the Phase 5.5 gate.** The Engineer's gate file (`phase5p5_gate.md`) must exist with OVERALL=PASS before Phase 6 starts. Skipping the gate is a process-integrity violation.
- **NEVER merge without `OVERALL=MERGE` from the Critic.** Phase 7.5's `review.md` is a hard gate. OVERALL=BLOCK means NO-MERGE regardless of headline metrics.
- **NEVER rerun the Critic on a "let me fix one thing" basis after BLOCK.** That is selection bias. If a methodology root-cause needs fixing, it becomes a NEW iter-v3/NNN+1 with new brief, new code, new backtest.
- **NEVER include a v1 or v2 symbol in v3's universe.** `V3_EXCLUDED_SYMBOLS` is enforced at runtime by the runner.
- **NEVER import from `crypto_trade.features` (v1) or `crypto_trade.features_v2` (v2) in v3 code.** Track isolation is structural.

To improve IS Sharpe: improve the STRATEGY (features, model, labeling) — not the measurement window. A strategy that only works from 2023 onward is NOT robust.

---

## THE MOST IMPORTANT RULE: IS/OOS Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
training_months = 24             ← FIXED. NEVER CHANGES.
```

This split exists to prevent **researcher overfitting** — not model leakage. The walk-forward backtest already prevents model-level leakage by training only on past data each month.

### What the split means

- The **Quant Researcher** uses ONLY IS data (before 2025-03-24) during Phases 1–5 (design). This prevents the researcher from unconsciously tuning features, labeling, or parameters to fit recent patterns.
- The **walk-forward / CPCV backtest runs on ALL data** (IS + OOS) as one continuous process. No artificial wall at the model level. The backtest rolls through OOS exactly as it would in live trading.
- The **reporting layer** splits trade results at `OOS_CUTOFF_DATE` into `in_sample/` and `out_of_sample/` report directories plus a `comparison.csv` with OOS/IS ratios.
- The **Quant Researcher** sees OOS results for the FIRST time in Phase 7 (evaluation).

The IS/OOS gap in `comparison.csv` tells you whether the researcher's design choices generalize beyond the data they could see. Hard floor: `OOS_Sharpe / IS_Sharpe ≥ 0.5` per project memory.

This constant lives in `src/crypto_trade/config.py`.

---

## Three Roles

You operate as ONE of three roles for each phase. In autopilot mode (default), you switch roles automatically — no need to ask.

| Role | Phases | Agent | Tools | Model |
|---|---|---|---|---|
| **Quant Researcher (QR)** | 1, 2, 3, 4, 5, 7, 8 | `quant-researcher` | Read, Glob, Grep, Bash, WebFetch, WebSearch, NotebookRead, NotebookEdit, Edit, Write, TodoWrite | opus |
| **Quant Engineer (QE)** | 5.5 (gate), 6 | `quant-engineer` | Read, Glob, Grep, Bash, Edit, Write, TodoWrite | sonnet |
| **Quant Critic** | 7.5 | `quant-critic` | **Read, Glob, Grep ONLY** (read-only by structural design) | opus |

### Quant Researcher (QR)
- **Owns:** data analysis (Phase 1), labeling decisions (Phase 2), symbol selection (Phase 3), feature design (Phase 4), research brief authoring (Phase 5), OOS evaluation (Phase 7), diary + merge decision (Phase 8)
- **Produces:** research briefs, diary entries, evaluation memos
- **Does NOT:** write production code in `src/`. Uses notebooks (`notebooks/`) and analysis scripts (`analysis/iteration_v3-NNN/*.py`) only.
- **Data access:** IS data only during Phases 1–5; sees OOS reports only in Phase 7.

### Quant Engineer (QE)
- **Owns:** Phase 5.5 gate verification (refuses incomplete briefs), production Python code (`src/`), pipeline architecture, backtest engine, report generation, library installs
- **Produces:** `src/` implementation, `phase5p5_gate.md`, engineering reports, backtest reports (IS + OOS report batches), `comparison.csv`, companion files
- **Does NOT:** make research decisions. If the brief is ambiguous, BLOCKs at Phase 5.5 and returns to QR.
- **Backtest:** runs walk-forward / CPCV on full dataset; reports split at `OOS_CUTOFF_DATE`.

### Quant Critic
- **Owns:** Phase 7.5 adversarial review of every iteration before merge
- **Produces:** `review.md` (8 checks PASS/FAIL + OVERALL=MERGE/BLOCK + Recommendations to QR)
- **Does NOT:** write code, briefs, or diaries. Cannot rerun backtests (read-only tools). Cannot negotiate verdict.
- **Adversarial mindset by structure:** the Critic's job is to find reasons NOT to merge. "When in doubt, FAIL."

The three-role separation is the v3 skill's primary defense against the QR-implementing-and-self-reviewing failure mode. An engineer who just wrote the code is biased toward finding it correct; a separate Critic with fresh context catches the class of errors that destroy strategies in production.

---

## Sacred Constants

```
OOS_CUTOFF_DATE = 2025-03-24
training_months = 24
ensemble_seeds = [42, 123, 456, 789, 1001]   # 5-seed inner ensemble
```

Plus the v3-specific hard thresholds:

```
DSR_threshold = 0.95     # Deflated Sharpe Ratio
PBO_threshold = 0.40     # Probability of Backtest Overfitting (LOWER is better)
PSR_threshold = 0.95     # Probabilistic Sharpe Ratio
IC_threshold  = 0.70     # |IC_pearson| between feature families (LOWER is better)
ADF_threshold = 0.05     # ADF p-value (LOWER is better — rejects unit root)
```

Plus the inherited project-level merge gates:

- IS monthly Sharpe > 1.0
- OOS monthly Sharpe > 1.0
- OOS / IS Sharpe ratio ≥ 0.5
- ≥10 trades/month OOS, ≥130 OOS total trades
- Top symbol concentration ≤ 30% of OOS PnL (or explicit exception with justification)
- 10-seed pre-MERGE validation: mean Sharpe > 0, ≥7/10 profitable

**Any single gate failure = NO-MERGE.** This is by design — gates prevent weird trade-offs ("OOS Sharpe is 2.5 but only 8 trades" is not acceptable).

---

## Symbol Universe — v3 Picks Fresh

iter-v3/001's brief selects the v3 universe from scratch. **v3 does not inherit v0.v2-069's universe (SOL/XRP/DOGE/NEAR).** This forces genuine diversification across the three tracks.

```python
V3_EXCLUDED_SYMBOLS = (
    # v1 traded
    "BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT",
    # v2 traded
    "BNBUSDT",  # historical v1-v2 reservation
    "SOLUSDT", "XRPUSDT", "DOGEUSDT", "NEARUSDT",
)
```

The runner enforces at startup:

```python
assert set(cfg.symbols).isdisjoint(V3_EXCLUDED_SYMBOLS), \
    f"v3 cannot trade v1/v2 symbols: {set(cfg.symbols) & set(V3_EXCLUDED_SYMBOLS)}"
```

iter-v3/001's Phase 3 (Symbol Selection) must produce Gate 1–2 evidence (data quality, liquidity, futures availability) for each candidate symbol. Universe selection is part of iter-v3/001's scope and shows up in the brief's Section 3 (Proposed Changes).

The v3 universe is expected to be 4 symbols (matching v2's count) to keep model complexity comparable. iter-v3/001's brief justifies the count.

---

## First Iteration Hard Rule — METHODOLOGY STACK + SYMBOL SELECTION

iter-v3/001 is the largest single iteration in the project's history. It ships:

1. **Symbol universe selection** — Phase 3 produces 4 candidate symbols with Gate 1–2 evidence; QR commits to the universe.
2. **CPCV implementation** — replaces `validation_v2.py:178`'s `NotImplementedError` stub. Mandatory from iter-v3/001 onward.
3. **PBO implementation** — replaces `validation_v2.py:185`'s stub. Reports `pbo` in `comparison.csv`.
4. **PSR implementation** — new function in `validation_v3.py`. Reports `psr` in `comparison.csv`.
5. **Meta-labeling baseline** — M1 (direction) + M2 (size) two-model architecture. M2 trained on M1-positive bars; target = "did M1's signal close at TP within timeout?". Position size remains vol-targeted in iter-v3/001 (no Kelly yet).
6. **ADF testing on existing fracdiff features** — `statsmodels.tsa.stattools.adfuller` runs at training time per feature; reports `adf_test.csv`. Existing `features_v2/fracdiff_v2.py` is wrapped (not removed) so v2 baselines stay reproducible.
7. **Library deps installed** — `mlfinlab==1.4` (or `mlfinpy` MIT fallback), `pypbo`, `fracdiff>=0.10` added to `pyproject.toml`.

**iter-v3/001 does NOT add new crypto-native feature families.** Funding rates, basis, OI, liquidations are iter-v3/002+ scope. iter-v3/001 is purely the methodology stack + universe selection. This bundling is unusual but necessary — v3 has no working baseline until both pieces are in place.

iter-v3/002 onward follows the **one-variable-at-a-time** rule: each iteration changes ONE primary thing (a feature family, a labeling param, a risk threshold) so attribution is clean.

---

## Phase Quick Reference

| Phase | Role | Inputs | Outputs |
|---|---|---|---|
| 1. Data analysis & EDA | QR | IS data, last diary | Notebook scratch, observations |
| 2. Labeling decisions | QR | EDA findings | Brief Section 2 (params, σ_t source) |
| 3. Symbol selection | QR | EDA, V3_EXCLUDED_SYMBOLS | Brief Section 3 (universe + Gate 1–2 evidence) |
| 4. Feature design | QR | EDA, brief Sections 1–3 | Brief Section 4 (feature list with cluster-importance check) |
| 5. Research brief | QR | Sections 0–9 above | `briefs-v3/iteration_v3-NNN/research_brief.md` (10 sections) |
| **5.5 Gate** | **QE** | Brief | `briefs-v3/iteration_v3-NNN/phase5p5_gate.md` (PASS or BLOCK) |
| 6. Implementation + backtest | QE | Brief, gate=PASS | `src/` commits, reports, `comparison.csv`, companion files, engineering report |
| **7.5 Critic Review** | **Critic** | Brief, code, reports | `briefs-v3/iteration_v3-NNN/review.md` (8 checks + OVERALL) |
| 7. OOS evaluation | QR | OOS reports, review.md | Evaluation memo (informal; integrates Critic findings) |
| 8. Diary + merge decision | QR | All above | `diary-v3/iteration_v3-NNN.md` (MERGE or NO-MERGE) |

Two new gates (5.5, 7.5) are MANDATORY. Skipping either is a process-integrity violation.

---

## Phase 5.5 — Pre-Phase 6 Gate (NEW, MOST IMPORTANT)

This is the v3 skill's single biggest defense against rushed iterations. The Engineer refuses to start Phase 6 until the brief contains all 10 mandatory sections.

### The 10 Mandatory Brief Sections

The Engineer reads `briefs-v3/iteration_v3-NNN/research_brief.md` and verifies:

- **Section 0 — Data Split declaration.** Confirms `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are unchanged. Names the IS window and OOS window in absolute dates.
- **Section 1 — Hypothesis.** ONE sentence. What changes and why we expect OOS improvement. Vague hypotheses BLOCK; specific testable hypotheses PASS.
- **Section 2 — IS-Only Numerical Evidence.** Tables produced by a committed `analysis/iteration_v3-NNN/*.py` script. Reproducible, IS-data-only, concrete numbers. Category-matching ("similar to RSI") is NOT evidence — BLOCK.
- **Section 3 — Proposed Changes.** Enumerated: labeling params, symbol set additions/removals (with V3_EXCLUDED_SYMBOLS check), feature additions/removals (with cluster-importance check), risk gate changes.
- **Section 4 — Expected OOS Impact.** Predicted Sharpe delta with confidence interval, plus an explicit falsifier ("if OOS Sharpe falls below X, the hypothesis is rejected").
- **Section 5 — Risk Mitigation.** R1/R2/R3 / 7-gate / new-gate changes; IS-calibrated thresholds; simulated effect on prior iterations.
- **Section 6 — Risk Management Design.** 8-primitive table or v3 equivalent; fire-rate predictions; regime coverage analysis.
- **Section 7 — Pre-Registered Failure-Mode Prediction (v3 mandatory).** 1–2 paragraphs predicting how this iteration most plausibly fails OOS, what the gates should catch, what the failure looks like in metrics. Phase 8 diary verifies this prediction against actual outcomes.
- **Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (v3 mandatory).** Locked numerical thresholds before backtest. Example: "MERGE iff `OOS_monthly_Sharpe ≥ +1.8` AND `PBO < 0.4` AND `PSR > 0.95` AND no symbol > 35% of OOS wpnl". Pre-registration eliminates post-hoc rationalization.
- **Section 9 — Library Stack Declaration (v3 mandatory).** Versions of mlfinlab/mlfinpy/pypbo/fracdiff used. If a fallback is used (e.g., mlfinpy because mlfinlab licensing failed), state which and why.

### The Gate Output

The Engineer writes `briefs-v3/iteration_v3-NNN/phase5p5_gate.md`:

```markdown
# Phase 5.5 Gate — iter-v3/NNN

OVERALL: PASS  (or BLOCK)

## Per-Section Status
- Section 0 (Data Split): PASS / MISSING / INVALID
- Section 1 (Hypothesis): PASS / MISSING / INVALID
- ...
- Section 9 (Library Stack): PASS / MISSING / INVALID

## Reasons (if BLOCK)
- <Section X>: <specific gap>
```

**OVERALL=BLOCK → Phase 6 terminates immediately.** Engineer commits the gate as `docs(iter-v3/NNN): phase 5.5 gate BLOCK` and returns to QR. The QR addresses gaps and re-submits; the Engineer re-runs the gate.

**OVERALL=PASS → Phase 6 proceeds.** Engineer commits the gate as `docs(iter-v3/NNN): phase 5.5 gate PASS` and starts implementation.

The Engineer NEVER attempts to "fix" the brief — that is role contamination. The gate is the QR's check on the QR's own work, mediated by the Engineer.

---

## Phase 7.5 — Critic Adversarial Review (NEW)

After the Engineer commits the engineering report (with `OVERALL=READY-FOR-CRITIC`), the orchestrating session invokes the `quant-critic` subagent via the `Agent` (or `Task`) tool with input:

```
{
  branch: "iteration-v3/NNN",
  report_dir: "reports-v3/iteration_v3-NNN",
  brief_dir: "briefs-v3/iteration_v3-NNN"
}
```

The Critic produces `review.md` content as its final assistant message. The orchestrator persists at `briefs-v3/iteration_v3-NNN/review.md`. The Critic's read-only tools (Read+Glob+Grep) are a structural guarantee that the Critic cannot rewrite history or "fix" findings by editing artifacts.

### The 8 Mandatory Checks

The Critic runs all eight in order:

1. **Look-Ahead Audit** — every feature computable from data with timestamp `< t`
2. **Embargo Width** — gap = `(timeout_candles + 1) × n_symbols`, symmetric on both sides
3. **Multiple-Testing Correction** — DSR > 0.95, PBO < 0.4, PSR > 0.95 (all three thresholds)
4. **IC Correlation Between Feature Families** — `|IC_pearson|` < 0.7 between new and existing
5. **ADF Stationarity** — every feature p < 0.05 (regime indicators may be exempt with brief justification)
6. **Pareto Dominance** — chosen seed non-dominated on the 6-metric vector; multi-metric winner
7. **Reproducibility** — commit SHA stamped, explicit `feature_columns`, ensemble seeds literal, trade PnL spot-check
8. **Hypothesis-Implementation Alignment** — brief Section 1 + Section 7 vs `git diff` actual code change

Plus optional checks 9–12 (symbol exclusion, feature isolation, forming-candle, library version).

### Verdict Mechanics

OVERALL=BLOCK on **any single FAIL**. The Critic does not balance — one methodology breach = NO-MERGE.

OVERALL=BLOCK is **FINAL for this iteration**. There is no "let me fix one thing and re-run". If a methodology root-cause needs fixing, it becomes a NEW iter-v3/NNN+1 with new branch, new brief, new backtest. Allowing rerun-after-fix is selection bias and defeats the Critic's purpose.

The QR's Phase 8 diary records the BLOCK verdict and the failure mode. The diary becomes part of the dead-paths catalog. The next iteration starts from the QR's Section 7 evaluation + the Critic's Recommendations to QR.

OVERALL=MERGE → QR proceeds to Phase 7 evaluation, then Phase 8 diary with MERGE decision (or NO-MERGE if QR finds an issue the Critic missed — Critic's PASS does not force a MERGE; it only enables one).

---

## Mandatory Statistical-Significance Reporting

Every `comparison.csv` MUST include the following columns and rows.

### Columns
```
metric, in_sample, out_of_sample, ratio
```

### Required Rows
- `monthly_sharpe`
- `daily_sharpe`
- `max_drawdown`
- `profit_factor`
- `win_rate`
- `n_trades`
- `total_pnl`
- `monthly_calmar`
- `weighted_pnl_total`
- `dsr` — Deflated Sharpe Ratio (probability the true Sharpe exceeds zero, after correcting for trials and non-normality)
- `pbo` — Probability of Backtest Overfitting (from CPCV's CSCV)
- `psr` — Probabilistic Sharpe Ratio (probability the observed Sharpe is non-spurious for the sample length)
- `n_trials` — total Optuna trials across all seed × symbol × walk-forward month cells
- `n_effective_trials` — PCA on trial-return matrix at 95% cumulative variance threshold

### Definitions

- **`n_trials`**: For v3-iter-NNN with `n_symbols × inner_seeds × monthly_trials × N_walk_forward_months` Optuna trials, the total count. Example: 4 × 5 × 50 × 24 = 24,000.
- **`n_effective_trials`**: rank of the PCA on the `n_trials × T` return matrix where T is the number of out-of-fold predictions per trial. The number of components capturing ≥95% of cumulative variance. Highly correlated trials collapse `n_eff` below the raw count, making DSR less punishing.

### Hard Thresholds

- **DSR > 0.95** — required for MERGE
- **PBO < 0.4** — required for MERGE (LOWER is better; PBO ≥ 0.4 means selecting IS-best is anti-correlated with OOS performance)
- **PSR > 0.95** — required for MERGE

**Any single threshold failure = automatic NO-MERGE.** Critic enforces this in Check 3.

### Compute Order

1. PSR first (unconditional — only depends on observed Sharpe and sample length)
2. DSR next (uses N_eff, depends on PSR's distributional inputs)
3. PBO last (requires CPCV path matrix from Check 6's input)

---

## CPCV Migration Plan

iter-v3/001's first deliverable: implement `crypto_trade.strategies.ml.validation_v3.combinatorial_purged_cv()` replacing the `NotImplementedError` stub at `validation_v2.py:178`. This is mandatory from iter-v3/001 onward — it is not optional, not phased, not delayed.

### Recommended Configuration

```python
N = 10                  # number of test groups
k = 2                   # number of test groups in each split
n_paths = C(N, k) = 45  # total backtest paths
min_path_count = 10     # required minimum
```

### Constraints

- `min path_count = C(N, k) ≥ 10` for any reported result
- Purge gap = `max_label_horizon × bars_per_horizon` symmetric on both sides of test boundary
- Embargo δ ≈ 1% of T per López de Prado convention (AFML Ch. 7)

### Walk-Forward as Fallback

Walk-forward (the existing `walk_forward.py` harness) is NOT removed. It is wrapped and kept for edge cases — specifically when label horizon × n_symbols is so large that purging eats the training window. Document the threshold in the brief's Section 9.

For iter-v3/001 ONLY: `comparison.csv` reports CPCV mean Sharpe AND legacy walk-forward Sharpe side-by-side to validate equivalence on the new universe. From iter-v3/002 onward, CPCV is canonical and walk-forward is informational.

### Path-Level Statistics

The CPCV path matrix (45 paths × 4 metrics) is the input to PBO computation. The matrix is also persisted at `reports-v3/iteration_v3-NNN/cpcv_paths.csv`:

```csv
path_id,sharpe,max_dd,n_trades
0,1.84,0.21,167
1,1.73,0.19,162
...
44,2.01,0.23,171
```

The Critic's Check 6 (Pareto Dominance) operates on the 10-seed pre-MERGE matrix, not the CPCV path matrix — distinguish carefully.

---

## Meta-Labeling Architecture

From iter-v3/001 onward, every iteration trains TWO models per symbol:

- **M1 — Primary (direction):** LightGBM classifier. Predicts side ∈ {long, short, no-trade}. Same architecture as v2's existing model.
- **M2 — Meta (size/filter):** LightGBM classifier on M1-positive bars only. Target: "did M1's signal close at TP within the vertical timeout?" (1 = yes, 0 = no). Output: P(M1 correct).

### Position Sizing (from iter-v3/002 onward)

Position size = `clip(0.5 · (2 · meta_proba − 1) · vol_target_adjustment, 0, 1)` (half-Kelly + vol targeting). The 0.5 is half-Kelly for parameter uncertainty. iter-v3/001 ships meta-labeling baseline with `vol_target_adjustment` only (no Kelly); iter-v3/002 adds the Kelly term.

### Training Schedule

- M1 trained per walk-forward month (existing schedule)
- M2 trained per walk-forward month, separate Optuna study (50 trials each, 5 inner seeds), same training window as M1
- Both M1 and M2 serialized per month for reproducibility

### Label Leakage Rule

M2's training labels are M1's binary outcomes. **M2's purge horizon must extend through M1's full label timeout** — otherwise M2 leaks M1's future correctness into M2's training set. The Engineer's runner enforces this via the `gap` parameter for M2's CV splits.

### Training Schedule for iter-v3/001

iter-v3/001 implements the M1/M2 architecture without Kelly. iter-v3/002 adds fractional Kelly. iter-v3/003+ explores M2 hyperparameter tuning if iter-v3/002's results justify.

---

## Crypto-Native Feature Roadmap

iter-v3/002 onward — one feature family per iteration. Each in its own `features_v3/` module.

### Roadmap

| Iteration | Family | Module | Hypothesis |
|---|---|---|---|
| iter-v3/001 | (methodology only — NO new features) | — | — |
| iter-v3/002 | **Funding rates** | `features_v3/funding.py` | 8h funding alignment with candle close; positioning crowding signal |
| iter-v3/003 | **Basis (perp − spot)** | `features_v3/basis.py` | Carry mispricing; cross-exchange dislocation |
| iter-v3/004 | **Open Interest** | `features_v3/oi.py` | Leverage stretch; venue rotation |
| iter-v3/005 | **Liquidations** | `features_v3/liquidations.py` | Self-exciting cascade events; Hawkes-process clustering |
| iter-v3/006 | **Cross-sectional ranking** | `features_v3/cross_section.py` | Momentum/vol rank within v3 universe |

### Feature Specifications (iter-v3/002 — funding)

- `funding_rate_8h` — current 8h funding rate (raw, lagged 1 candle)
- `funding_z_30` — z-score over rolling 30 candles (10 days at 8h)
- `funding_momentum_8h` — 1-bar funding rate change
- `funding_momentum_24h` — 3-bar funding rate change
- `funding_momentum_72h` — 9-bar funding rate change
- `premium_index` — raw mark-vs-index spread (responds faster than clamped funding rate)
- `funding_corr_price_14` — rolling Spearman correlation between funding and price returns over 14 candles

Data source: Binance funding history endpoint (`/fapi/v1/fundingRate`). Lagged 1 candle to ensure knowability at decision time.

### IC Correlation Enforcement

The Critic's Check 4 enforces `|IC_pearson(new_family, existing_family)| < 0.7` for each new family. Engineer produces `ic_matrix.csv` at backtest time:

```csv
family,momentum,volatility,volume,regime,fracdiff,funding (new)
momentum,1.00,0.12,0.08,0.31,0.05,0.18
volatility,0.12,1.00,0.42,0.28,0.09,0.22
...
funding,0.18,0.22,0.06,0.41,0.07,1.00
```

If any new-vs-existing pair `|IC| ≥ 0.7`, Critic Check 4 = FAIL. Iteration BLOCKED; QR drops one of the redundant features OR proves via paired-bootstrap CV that the new one is strictly better.

### Data-Availability Check (Engineer)

Before adding a feature, the Engineer verifies the fetcher produces data spanning the IS+OOS window. Missing-data rule: NaN (not zero) and feature masked at training time. Coverage gap > 5% of training samples = FAIL → escalate to QR.

---

## Pareto-Front Model Selection

The Critic's Check 6 enforces Pareto-front model selection on the 10-seed pre-MERGE validation matrix (NOT outer-seed sweeps during the autopilot's daily measurement — single-seed-canonical is preserved per project memory feedback rule).

### The Metric Vector

```
(OOS_Sharpe, OOS_MaxDD, OOS_Calmar, PBO, n_trades_OOS, max_symbol_concentration)
```

Higher is better for {Sharpe, Calmar, n_trades}. Lower is better for {MaxDD, PBO, concentration}.

### The Process

1. Engineer runs the iteration with 10 outer seeds (the 5 inner-ensemble seeds × 2 outer seeds, or a different 10-seed config — Engineer documents).
2. For each seed, compute the 6-metric vector on OOS.
3. Persist as `reports-v3/iteration_v3-NNN/pareto_front.csv`.
4. Engineer's report names the chosen seed (default: 42).
5. Critic Check 6 verifies:
   - Chosen seed is non-dominated on the 6-metric vector
   - Chosen seed wins on at least 2 of {OOS_Sharpe, OOS_MaxDD, n_trades_OOS}

### Reject Conditions

- **Dominated** — another seed beats the chosen seed on every metric and strictly better on at least one. BLOCK; recommend switching seeds or accepting the dominator's metrics.
- **Single-metric tunnel vision** — chosen seed wins ONLY on OOS_Sharpe. BLOCK; the iteration is over-fit to one number.
- **Lone non-dominated point** — the chosen seed is the only non-dominated seed in the 10. WARN (suspicious; possibly overfit to a metric quirk).

### Why This Matters

Selecting the seed with the highest OOS Sharpe and ignoring drawdown / concentration / trade count is the most common form of seed-bias in iterative research. Pareto-front enforcement makes this impossible to do silently.

---

## Library Dependency Plan

iter-v3/001 adds the following pinned dependencies to `pyproject.toml`:

- **`mlfinlab==1.4`** — primary choice. Provides `CombinatorialPurgedKFold`, meta-labeling utilities, `triple_barrier_method`, fractional differentiation. Post-1.4 versions are commercial; pin to 1.4.
- **`mlfinpy`** — fallback if `mlfinlab` license blocks pip install. MIT-licensed open-source fork covering the same techniques. Brief Section 9 declares which is used.
- **`pypbo`** — standalone PBO via CSCV. Small library (~500 LOC), readable. Use `pypbo.pbo()` directly.
- **`fracdiff>=0.10`** — Numba-accelerated fractional differentiation with scikit-learn-compatible `FracdiffStat` for auto-selecting `d*`. Replaces the custom `features_v2/fracdiff_v2.py` (which is wrapped, not removed, for v2 backward-compatibility).

### ADF Stationarity at Training Time

iter-v3/001 wires `statsmodels.tsa.stattools.adfuller` into the Engineer's pipeline:

- For every feature in `V3_FEATURE_COLUMNS`, compute ADF p-value at the end of the training window.
- Persist as `reports-v3/iteration_v3-NNN/adf_test.csv`.
- ADF p > 0.05 = stationarity-failed warning; Critic Check 5 = FAIL unless the brief documents the feature as a "regime indicator, not predictor" in Section 4.

### Migration of Existing fracdiff_v2

The current `features_v2/fracdiff_v2.py` uses fixed `d=0.4`. iter-v3/001 introduces `features_v3/fracdiff_v3.py` using `fracdiff.FracdiffStat` with auto-selected `d* = min{d : ADF(diff_d(x)) < 0.05}`. The v2 fracdiff implementation is wrapped (not removed) so v2 baselines stay reproducible.

---

## What v3 Does NOT Change from v2

The v3 skill is intentionally conservative on these axes — they're proven and changing them would conflate experiments:

- 8-phase backbone (extended to 10 with Phase 5.5 + 7.5 gates, but the 8 still exist)
- Sacred constants (`OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24`)
- 5-seed inner ensemble: `[42, 123, 456, 789, 1001]`
- Autopilot default behavior
- 4-commit git discipline (code, brief, engineering report, diary)
- 10-seed pre-MERGE concentration check
- Hard merge gates from project memory (Sharpe 1.0 floor, IS/OOS ratio ≥ 0.5, ≥130 OOS trades, ≤30% concentration)
- "QR uses IS data" — Phase 5 brief requires committed `analysis/iteration_v3-NNN/*.py`
- Forming-candle filter in `fetcher.py`
- Data freshness rule (CSVs within 16h of measurement time)

---

## Where v3 Lives (Filesystem Map)

```
.claude/
├── commands/
│   ├── quant-iteration.md         (v1)
│   ├── quant-iteration-v2.md      (v2)
│   └── quant-iteration-v3.md      (v3 — THIS FILE)
└── agents/
    ├── quant-researcher.md        (used for Phases 1-5, 7, 8 of v1/v2/v3)
    ├── quant-engineer.md          (used for Phases 5.5, 6 of v1/v2/v3)
    └── quant-critic.md            (used for Phase 7.5 of v3 only)

ITERATION_PLAN_8H_V3.md            (workflow doc at repo root)
BASELINE_V3.md                     (current v3 baseline at repo root; iter-v3/001 writes the first one)

src/crypto_trade/
├── features/                      (v1, never imported by v2 or v3)
├── features_v2/                   (v2, never imported by v3)
├── features_v3/                   (v3 — new from iter-v3/001)
└── strategies/ml/
    ├── lgbm.py                    (shared backtest engine; track-aware)
    ├── walk_forward.py            (legacy fallback for v3)
    ├── validation_v2.py           (DSR works; CPCV/PBO stubs)
    └── validation_v3.py           (NEW from iter-v3/001 — CPCV, PBO, PSR)

run_baseline.py                    (v1 runner)
run_baseline_v2.py                 (v2 runner)
run_baseline_v3.py                 (NEW — v3 runner with CPCV)

reports-v3/
└── iteration_v3-NNN/
    ├── in_sample/
    ├── out_of_sample/
    ├── comparison.csv             (DSR + PBO + PSR + n_trials columns)
    ├── pareto_front.csv           (10-seed × 6-metric matrix)
    ├── cpcv_paths.csv             (45 CPCV paths)
    ├── adf_test.csv               (per-feature ADF p-value)
    ├── ic_matrix.csv              (pairwise feature-family IC)
    └── dsr.json                   (DSR + PBO + PSR + N_eff)

briefs-v3/
└── iteration_v3-NNN/
    ├── research_brief.md          (10 mandatory sections)
    ├── phase5p5_gate.md           (Engineer's PASS or BLOCK)
    ├── engineering_report.md      (Engineer's Phase 6 output)
    └── review.md                  (Critic's Phase 7.5 output)

diary-v3/
└── iteration_v3-NNN.md            (QR's Phase 8 output)

analysis/
└── iteration_v3-NNN/
    └── *.py                       (committed scripts producing brief Section 2 evidence)

data/
├── funding/                       (NEW from iter-v3/002)
├── basis/                         (NEW from iter-v3/003)
├── oi/                            (NEW from iter-v3/004)
└── liquidations/                  (NEW from iter-v3/005)
```

**Track isolation enforced via grep at runtime:**
- `grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` must be empty
- `grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v3/` must be empty
- v3 imports ONLY from stdlib, third-party packages, and `crypto_trade.features_v3`

---

## Git Workflow — v3 Only

Same skeleton as v2's, with v3-specific naming.

### Starting an iteration

```bash
git checkout quant-research && git pull
git checkout -b iteration-v3/NNN
```

### Commit Discipline

Separate documentation from code. NEVER mix them in the same commit.

1. **Code commits** → prefix `feat(iter-v3/NNN):` or `fix(iter-v3/NNN):`
2. **Phase 5.5 gate** → single commit: `docs(iter-v3/NNN): phase 5.5 gate PASS` (or BLOCK)
3. **Research brief** → single commit: `docs(iter-v3/NNN): research brief`
4. **Engineering report + Critic review** → single commit: `docs(iter-v3/NNN): engineering report + Critic review`
5. **Diary entry** → LAST commit on branch: `docs(iter-v3/NNN): diary entry`

Why: failed iterations cherry-pick docs commits to `quant-research`. If diary is mixed with code, cherry-pick breaks.

### Engineering Report + Critic Review Co-Commit

The Critic emits `review.md` content as message text; the orchestrator persists at `briefs-v3/iteration_v3-NNN/review.md`. Both files (engineering report + review.md) are committed together as a single `docs(iter-v3/NNN): engineering report + Critic review` commit. This co-commit makes the audit trail atomic — anyone reading git log sees the engineering output and the Critic verdict in one revision.

### Merge Decision

After QR writes the diary with MERGE or NO-MERGE decision:

**MERGE** (iteration beats baseline AND Critic OVERALL=MERGE):
```bash
git checkout quant-research
git merge iteration-v3/NNN --no-ff -m "merge(iter-v3/NNN): [summary]"
# Update BASELINE_V3.md with new metrics
git add BASELINE_V3.md
git commit -m "baseline-v3: update after iteration v3-NNN"
git tag -a v0.v3-NNN -m "Iteration v3-NNN: OOS Sharpe X.XX, PBO Y.YY, PSR Z.ZZ"
```

**NO-MERGE** (iteration fails any gate OR Critic OVERALL=BLOCK):
```bash
# Cherry-pick docs commits (gate, brief, engineering report + review, diary) to quant-research
git checkout quant-research
git cherry-pick <gate-sha> <brief-sha> <eng+review-sha> <diary-sha>
# Iteration branch stays in repo as archaeological record
```

Failed iteration diaries are cherry-picked even when code is not — the project values the dead-paths catalog.

### Critic Review File Commit

The Critic's `review.md` is committed by the Engineer (the orchestrator that invoked the Critic) in the same commit as the engineering report. Single commit message: `docs(iter-v3/NNN): engineering report + Critic review`. The `review.md` file path is `briefs-v3/iteration_v3-NNN/review.md`.

---

## Research Brief — Mandatory v3 Sections

The brief at `briefs-v3/iteration_v3-NNN/research_brief.md` MUST contain all 10 sections (0–9). The Phase 5.5 gate maps 1:1 onto these sections; any missing section = BLOCK.

### Section Schema

```markdown
# Iteration v3-NNN — Research Brief

## Section 0 — Data Split Declaration
- OOS_CUTOFF_DATE: 2025-03-24 (unchanged)
- training_months: 24 (unchanged)
- IS window: [start_date, 2025-03-24)
- OOS window: [2025-03-24, end_date)

## Section 1 — Hypothesis
<one sentence: what changes and why we expect OOS improvement>

## Section 2 — IS-Only Numerical Evidence
<tables produced by analysis/iteration_v3-NNN/*.py — committed before brief>
- Path to script: analysis/iteration_v3-NNN/<name>.py
- Path to output: analysis/iteration_v3-NNN/<name>_output.csv
<numerical tables inline>

## Section 3 — Proposed Changes
- Symbols: <added / removed / kept; rationale; V3_EXCLUDED_SYMBOLS check>
- Labeling: <triple-barrier params, σ_t source, timeout>
- Features: <added / removed; cluster-importance check ran>
- Risk gates: <new gate? threshold? fire rate prediction>

## Section 4 — Expected OOS Impact
- Predicted Sharpe delta: +X.X (CI: [Y.Y, Z.Z])
- Falsifier: "if OOS Sharpe falls below W, hypothesis is rejected"

## Section 5 — Risk Mitigation
<R1/R2/R3 / 7-gate / new-gate changes; IS-calibrated thresholds; simulated effect on prior iterations>

## Section 6 — Risk Management Design
<8-primitive table; fire-rate predictions; regime coverage analysis>

## Section 7 — Pre-Registered Failure-Mode Prediction (v3 mandatory)
<1-2 paragraphs predicting how this iteration most plausibly fails OOS, what the gates should catch, what the failure looks like in metrics>

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (v3 mandatory)
<locked numerical thresholds before backtest. Example: "MERGE iff OOS_monthly_Sharpe ≥ +1.8 AND PBO < 0.4 AND PSR > 0.95 AND no symbol > 35% of OOS wpnl">

## Section 9 — Library Stack Declaration (v3 mandatory)
- mlfinlab: 1.4 (or mlfinpy <version> if fallback)
- pypbo: <version>
- fracdiff: <version>
- statsmodels: <version> (for ADF)
<note any fallback rationale>
```

---

## Backtest Report Structure — v3

`reports-v3/iteration_v3-NNN/` contains:

- **`in_sample/`** and **`out_of_sample/`** — quantstats.html, trades.csv, daily_pnl.csv, monthly_pnl.csv, per_regime.csv, per_symbol.csv, feature_importance.csv (per-track breakdown of MDI + MDA + SFI)
- **`comparison.csv`** — IS/OOS diff table with `dsr`, `pbo`, `psr`, `n_trials`, `n_effective_trials` columns added to v2's schema
- **`pareto_front.csv`** — 10-seed × 6-metric matrix (input to Critic Check 6)
- **`cpcv_paths.csv`** — 45 CPCV paths × 4 metrics (input to PBO computation)
- **`adf_test.csv`** — per-feature ADF p-value at end of training window (input to Critic Check 5)
- **`ic_matrix.csv`** — pairwise Pearson IC between feature families on IS data (input to Critic Check 4)
- **`dsr.json`** — `{"dsr", "pbo", "psr", "n_trials", "n_eff", "min_trl_months"}`
- **`run.log`** — full stdout/stderr from the backtest runner

The MinTRL (Minimum Track Record Length) field in `dsr.json` reports the number of months of OOS data needed to declare statistical significance at 95% confidence — a useful sanity check.

---

## Phase 8 Diary Template — v3

QR's `diary-v3/iteration_v3-NNN.md`:

```markdown
# Iteration v3-NNN — Diary

## Decision: MERGE or NO-MERGE
<single line, no hedging>
<if NO-MERGE due to Critic BLOCK: name the failed Check>

## What Worked
<numerical results; OOS metrics; per-symbol attribution; comparison vs baseline>

## What Failed
<honest accounting; if NO-MERGE, why specifically>

## Critic Review Summary
- Check 1 (Look-Ahead): PASS
- Check 2 (Embargo): PASS
- Check 3 (DSR/PBO/PSR): FAIL (PBO=0.43 > 0.4 threshold)
- Check 4 (IC): PASS
- Check 5 (ADF): PASS
- Check 6 (Pareto): WARN
- Check 7 (Reproducibility): PASS
- Check 8 (Hypothesis-Implementation Alignment): PASS
- OVERALL: BLOCK (PBO failure)

## Pareto Position (chosen seed)
<table from pareto_front.csv: chosen seed metrics + dominator (if any)>

## ADF Stationarity Report
<summary from adf_test.csv: count of features with p<0.05 vs p≥0.05>

## Pre-Registered Failure-Mode vs Reality
<from brief Section 7: "predicted failure was X via Y mechanism">
<actual: "iteration failed via PBO threshold, mechanism was Z">
<match? yes/partial/no — explain>

## Lessons
<generalizable takeaways; new entries for the dead-paths catalog if applicable>

## Next Iteration Ideas
<3–5 specific, testable hypotheses for the next QR; ranked by expected impact>
```

The "Pre-Registered Failure-Mode vs Reality" section is the heart of the v3 diary. Did the QR's prediction match what actually broke? If yes, the QR's intuition is well-calibrated; if no, the QR learns to predict differently. This is meta-research that compounds across iterations.

---

## Subagent Invocation Protocol

The orchestrating session uses Claude Code's `Agent` tool to delegate phase work:

### QR Phases (1–5, 7, 8)

```
Agent({
  description: "Run Phase X for iter-v3/NNN",
  subagent_type: "quant-researcher",
  prompt: "[mode: project] Run Phase X for iter-v3/NNN. Brief at briefs-v3/iteration_v3-NNN/research_brief.md (when applicable). Working directory: /home/roberto/crypto-trade/.worktrees/quant-research. Reference BASELINE_V3.md for current baseline."
})
```

### Engineer Phase 5.5 Gate

```
Agent({
  description: "Verify Phase 5.5 gate for iter-v3/NNN",
  subagent_type: "quant-engineer",
  prompt: "Run the Phase 5.5 brief-completeness gate for iter-v3/NNN. Read briefs-v3/iteration_v3-NNN/research_brief.md, verify all 10 mandatory sections, write phase5p5_gate.md with OVERALL=PASS or BLOCK + per-section status."
})
```

### Engineer Phase 6 (after gate=PASS)

```
Agent({
  description: "Run Phase 6 implementation for iter-v3/NNN",
  subagent_type: "quant-engineer",
  prompt: "Phase 5.5 gate PASSED. Run Phase 6 for iter-v3/NNN. Brief at briefs-v3/iteration_v3-NNN/research_brief.md. Implement changes in src/, run backtest with CPCV, produce reports + comparison.csv + companion files (pareto_front, cpcv_paths, adf_test, ic_matrix, dsr.json), commit code before backtest, write engineering report ending with OVERALL=READY-FOR-CRITIC."
})
```

### Critic Phase 7.5

```
Agent({
  description: "Run Phase 7.5 Critic review for iter-v3/NNN",
  subagent_type: "quant-critic",
  prompt: "Run Phase 7.5 adversarial review for iter-v3/NNN. Branch: iteration-v3/NNN. Report dir: reports-v3/iteration_v3-NNN. Brief dir: briefs-v3/iteration_v3-NNN. Run all 8 mandatory checks. Emit review.md content as final message text — orchestrator persists at briefs-v3/iteration_v3-NNN/review.md."
})
```

After the Critic returns, the orchestrator writes the final-message content to `briefs-v3/iteration_v3-NNN/review.md`, commits it together with the engineering report, and routes to QR for Phase 7.

### Hand-off Sanity Checks

- Engineer's `OVERALL=READY-FOR-CRITIC` line in the engineering report is the explicit handshake to Phase 7.5.
- Critic's final message starts with `# Phase 7.5 Critic Review — iter-v3/NNN` and contains `OVERALL: MERGE` or `OVERALL: BLOCK` — the orchestrator parses these.
- If the Critic's response doesn't match the template, the orchestrator re-invokes with a stricter prompt or escalates to user.

---

## Quick-Start Command (for the human user)

`/quant-iteration-v3` triggers the autopilot loop:

1. Read `BASELINE_V3.md` + last 3 v3 diaries
2. Determine next iteration number (next `iter-v3/NNN`)
3. `git checkout quant-research && git checkout -b iteration-v3/NNN`
4. QR Phases 1–5 → research brief at `briefs-v3/iteration_v3-NNN/research_brief.md`
5. Engineer Phase 5.5 gate → `phase5p5_gate.md` (PASS or BLOCK)
6. If BLOCK → return to QR; loop on QR Phase 5
7. If PASS → QE Phase 6 → engineering report + reports
8. Critic Phase 7.5 → `review.md` (OVERALL=MERGE or BLOCK)
9. QR Phase 7 → OOS evaluation memo
10. QR Phase 8 → diary + merge decision
11. Commit/tag per git workflow
12. Loop back to step 1 with the new diary's "Next Iteration Ideas"

---

## Migration Notes (v2 → v3)

There is NO `iter-v3/000`. iter-v3/001 produces the first true v3 baseline. v3 starts genuinely fresh:

- New symbol universe (selected by iter-v3/001's brief; must exclude V3_EXCLUDED_SYMBOLS)
- New methodology stack (CPCV, PBO, PSR, meta-labeling, ADF-tested fracdiff)
- New library stack (mlfinlab/mlfinpy, pypbo, fracdiff)
- New three-role workflow (QR/QE/Critic)

`BASELINE_V3.md` initially is a placeholder ("TBD by iter-v3/001 — universe and metrics to be determined"). After iter-v3/001 completes (assuming MERGE), BASELINE_V3.md is populated with the new metrics — which include CPCV/PBO/PSR for the first time in the project's history.

**v2's track stays open as an active sibling.** No `quant-iteration-v2` skill changes. The user can run v2 iterations whenever they want; v3 doesn't replace v2.

---

## Key Reminders — v3

- The Critic is read-only by structural design. Tools: `Read, Glob, Grep` ONLY.
- Phase 5.5 gate is the single biggest defense against rushed iterations. Engineer refuses to start without complete brief.
- PBO ≥ 0.4 is automatic NO-MERGE. Same for DSR < 0.95 and PSR < 0.95.
- v3 universe must exclude all v1+v2 symbols (V3_EXCLUDED_SYMBOLS enforced at runtime).
- Track isolation: v3 NEVER imports from `crypto_trade.features` (v1) or `crypto_trade.features_v2` (v2).
- iter-v3/001 ships methodology stack + universe selection together (the largest single iteration in project history).
- iter-v3/002+ follows one-variable-at-a-time rule.
- "QR uses IS data" — Phase 5 brief must contain numerical tables from a committed `analysis/iteration_v3-NNN/*.py` script.
- Pre-registered failure-mode prediction (Section 7) and MERGE/NO-MERGE criteria (Section 8) are MANDATORY in every v3 brief.
- OVERALL=BLOCK from the Critic is FINAL. Re-running after a fix is selection bias.
- Sacred constants are sacred. `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` never change.

The v3 skill turns informal best-practices into structural gates. The structure makes it harder to fool yourself, and harder to fool yourself is the entire game.
