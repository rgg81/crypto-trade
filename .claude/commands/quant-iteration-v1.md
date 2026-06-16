---
name: quant-iteration-v1
description: "Quant research/engineering iteration workflow for the crypto-trade LightGBM strategy — v1 TRACK (REDESIGNED 2026-06-15: SINGLE-SYMBOL parametrized, honest cost model with slippage, 5-role team, exploration/confirmation cadence only, relative merge gate). Use this skill whenever the user mentions: v1 iteration, quant-iteration-v1, iter-v1, iter-v1/NNN, BASELINE_V1, BASELINE_V1_<SYMBOL>, briefs-v1, diary-v1, reports-v1, run_baseline_v1, v1 research brief, v1 diary, v1 merge decision, v1 baseline, single-symbol v1, feature engineer, risk engineer, quant research, quant engineer, Critic, feature_report, risk_report, review.md, slippage, exploration, confirmation, lottery bias, training_days, V1_EXCLUDED_SYMBOLS, features_v1, CPCV, DSR, PBO, PSR, ADF, IC, meta-labeling, fractional Kelly. Also trigger when the user says: 'start v1 iteration', 'run v1 phase', 'evaluate v1 reports', 'write v1 diary', 'v1 merge decision', 'invoke Critic for v1'."
---

# Quant Iteration Skill — v1 (Single-Symbol, Honest-Cost, 5-Role Track)

## Mission

v1 builds **one per-symbol LightGBM specialist at a time**, under an honest execution-cost model
(fees + slippage), validated by a walk-forward backtest with embargo, and judged by **relative
improvement over the symbol's own previous baseline**. We start with **BTCUSDT**, the primary
asset. Each symbol gets its own baseline, its own reports tree, its own diary.

This is a **redesign (2026-06-15)** after a costly train/serve bug: the per-seed final retrain
once ignored Optuna's `training_days`, and a "full-window-training" patch meant to fix it
backfired (helped one symbol, collapsed another). The lesson: **train must equal serve**, costs
must be honest, and the methodology must be simple enough that a defect cannot hide. So v1 is now
deliberately lean — one symbol, two cadences, five clear roles, and a backtest that is the only
arbiter of truth.

We do not predict the future. We identify moments when the distribution of forward returns is
skewed in our favor and bet accordingly, sized by conviction and disciplined by risk. No
p-hacking. No overfitting. No self-deception. The backtest is the proof — no side-script
projections substitute for a real backtest run.

---

## Sacred Constants (IMMUTABLE)

```
OOS_CUTOFF_DATE = 2025-03-24          # FIXED. NEVER CHANGES.
training_months = 24                  # FIXED. NEVER CHANGES.
walk_forward: train_end_ms = test_start_ms - embargo_ms   # the embargo law; cannot regress
gap = (timeout_candles + 1) * n_symbols                   # CV label-leak guard (n_symbols = 1)

# ── THE SEED RULE (ONE knob, no ambiguity) ─────────────────────────────────
# v1's model = the SPECIALIST BAGGING ensemble: K independent Optuna studies per
# walk-forward month (each its own seed + hyperparameter search), combined by
# mean-of-signed-weights. K is the ONLY seed number that ever varies.
V1_EXPLORATION_BAGGING_K  = 3    # exploration: fast screen
V1_CONFIRMATION_BAGGING_K = 20   # confirmation: robust; bagging IS the lottery-bias control
#   inner ensemble (--ensemble-size) = 1, ALWAYS  (placeholder seed [42]; hard error if set)
#   outer seeds   (--seeds)          = 1, ALWAYS  (hard error if != 1)
#   K seeds = first K of V1_SPECIALIST_SEEDS=range(42,92): K=3→[42,43,44], K=20→[42..61]
#   n_trials = the per-seed Optuna budget = --n-trials (default 35), HONORED per seed.
#   specialist_dispersion.csv reports residual per-candle seed disagreement.
#   (K==0 in LightGbmStrategy = legacy full-50-seed roster, BIT-IDENTICAL; do not use for v1.)

slippage_bps_per_side = 2.0           # round-trip drag = 2x; v1 runner default (--slippage-bps)
training_days                          # Optuna-searched (10..500, step 10), applied at CV folds
                                       # AND final per-seed retrain. NO full-window mode. EVER.
```

**Model invariant — NO SONNET.** Every v1 agent (`feature-engineer`, `risk-engineer`,
`quant-researcher`, `quant-engineer`, `quant-critic`) runs `model: opus`. A v1 agent may never be
`sonnet`. Check: `grep -rl 'model: sonnet' .claude/agents/` must not list any v1 agent.

**Single-symbol invariant.** Exactly one symbol per run. The runner asserts `len(set(symbols)) == 1`.

---

## Cost Model (NEW — honest costs)

Every closed trade nets, at the `make_result` accounting site:

```
net_pnl_pct = pnl_pct - fee_pct - 2 * (slippage_bps_per_side / 100)
```

- `fee_pct` (round-trip fee, default 0.1%) + round-trip slippage (`2 × slippage_bps_per_side`).
- v1 backtests run at `slippage_bps_per_side = 2.0` (0.04% round-trip) by default; override with
  `--slippage-bps`. The Risk Engineer pre-registers a cost-stress sweep ({1×, 2×, 4×}).
- **Backtest-live parity:** the live engine applies the same slippage via `LiveConfig.slippage_bps_per_side`
  on the paper/dry-run + catch-up accounting paths (same `make_result`). A single-symbol v1 live
  deployment sets `LiveConfig.slippage_bps_per_side = 2.0` to match its backtest. The dataclass
  defaults are 0.0 so v2/v3 and the deployed engine stay byte-unchanged.
- An edge that only survives at zero cost is not an edge. Judge lift NET of costs.

---

## Five Roles (all `model: opus`)

| Role | Owns phases | Agent file | Produces |
|---|---|---|---|
| **Feature Engineer (FE)** | 4 (features + selection + ML/HP advisory) | `feature-engineer.md` | `feature_report.md` |
| **Risk Engineer (RE)** | 4.7 (risk calibration + scenario stress) | `risk-engineer.md` | `risk_report.md` |
| **Quant Research (QR)** | 1 (EDA), 2 (labeling), 5 (brief), 7 (OOS eval), 8 (diary+merge) | `quant-researcher.md` | brief, eval memo, diary |
| **Quant Engineer (QE)** | 5.5 (gate), 6 (backtest) | `quant-engineer.md` | `src/` diff, reports, comparison.csv |
| **Critic** | 7.5 (results-only review) | `quant-critic.md` | `review.md` |

FE and RE are the explicit investment priority of this track — feature engineering and risk
modeling are where edge is found and protected. The former LightGBM Master advisor is **folded
into the Feature Engineer** (HP regions, training_days range, trial-stability, feature-importance
interpretation). There is no standalone LM Master, no Phase 4.5 / 6.0 / 7.4.

---

## Phase Workflow

| # | Phase | Owner | Output |
|---|---|---|---|
| 1 | EDA / data analysis (IS-only) | QR | `analysis/<SYMBOL>/iteration_v1-NNN/eda.py` + tables |
| 2 | Labeling decision | QR | brief §2 |
| 4 | Feature construction + selection + ML/HP advisory | FE | `feature_report.md` |
| 4.7 | Risk calibration + scenario stress | RE | `risk_report.md` |
| 5 | Research brief synthesis | QR | `research_brief.md` |
| 5.5 | Brief-completeness gate | QE | `phase5p5_gate.md` (PASS/BLOCK) |
| 6 | Implementation + walk-forward backtest | QE | `src/` diff, IS+OOS reports, `comparison.csv` |
| 7 | OOS evaluation | QR | evaluation memo |
| 7.5 | Results-only adversarial review + improvement proposals | Critic | `review.md` |
| 8 | Diary + merge decision | QR | `diary-v1/<SYMBOL>/iteration_v1-NNN.md` |

Autopilot: run the full flow end-to-end without pausing between phases. Only stop on a genuine
blocker (ambiguous brief the QR can't resolve, an error, or a decision needing the user).

---

## Cadence — exploration vs confirmation (and NOTHING else)

There are exactly two iteration modes. No axis-rotation rules, no HIGH-RISK declarations, no
10:1 ratios, no verdict zoo. Just:

The ONLY thing that changes between modes is the bagging **K** (see THE SEED RULE above).
inner ensemble = 1 and outer seeds = 1 are FIXED in both modes.

- **EXPLORATION** (`--exploration`): bagging **K=3** (fast screen). Goal = test one focused
  hypothesis (a feature, an HP region, a risk knob) for signal-vs-noise. Fast turnaround. An
  exploration NEVER updates the baseline.
- **CONFIRMATION** (`--confirmation`): bagging **K=20** (robust). Goal = decide the merge. The
  20-study bagging IS the lottery-bias control — averaging 20 independent Optuna studies makes the
  aggregate seed-robust by construction; more K ⇒ lower lottery risk. Only a confirmation can
  update the baseline.

**Lottery-bias readout (confirmation):** `specialist_dispersion.csv` reports the residual
per-candle population std of the K signed-weights (how much the 20 studies still disagree per
candle). The aggregate prediction is the mean over all K studies; a single study cannot swing it.
(There is NO outer-`--seeds` re-run loop — robustness comes from K, not from N independent backtests.)

---

## Baseline bootstrap + Merge Gate (NEW — relative, no absolute floors)

**Start from scratch.** There is no inherited v1 baseline for the redesign. The **first run for a
symbol is a CONFIRMATION** that *establishes* `BASELINE_V1_<SYMBOL>.md` (it has no predecessor to
beat — it simply sets the bar).

**Merge gate (every confirmation after the first):** a candidate MERGES iff it is **better than
the symbol's current baseline** AND the methodology is intact. There are **no absolute Sharpe
floors** — the old "IS Sharpe > 1.0 AND OOS Sharpe > 1.0" rule is RETIRED for v1.

"Better than baseline" means, judged net of costs on the confirmation run:
- **Generalization-coherence FIRST (the primary lens).** Prefer a candidate whose **IS and OOS are
  BOTH positive with a healthy OOS/IS ratio (~0.5–1.0)** over a profile where IS and OOS disagree in
  sign. An OOS Sharpe that is positive *only while IS is negative* (an **inversion**, ratio < 0) is a
  regime artifact, NOT a generalizing edge — do **not** treat such a baseline's high OOS number as the
  bar to beat. A coherent both-positive candidate with a lower raw OOS Sharpe can still be **better**
  than an inverted baseline with a higher OOS Sharpe. Judge on coherent both-window performance + the
  ratio, not the OOS number in isolation. (Codified 2026-06-16 — the iter-001 BTC baseline was exactly
  such an inversion: IS −0.28 / OOS +0.64, ratio −2.29.)
- corroborated by OOS net PnL / profit factor moving the same direction, AND
- no material regression on IS, AND
- the K=20 bagging dispersion is healthy (`specialist_dispersion.csv`: the 20 studies don't wildly
  disagree per candle — the aggregate isn't riding a single study). The K=20 bagging is itself the
  lottery-bias control; there is no separate per-seed-Sharpe panel because confirmation is one
  aggregated backtest, not 20 independent re-runs.

DSR / PBO / PSR / ADF / IC are **informational context** the Critic weighs — not pass/fail floors.
Methodology integrity (no look-ahead, embargo intact, IS-only design, single-symbol, honest costs,
training_days consistent) is the only HARD gate. A methodology violation is an automatic NO-MERGE
regardless of headline numbers.

---

## The Critic — results-only, stage-aware, always-constructive

The Critic reviews **only the backtest RESULTS** (the produced reports: comparison.csv, trades,
per-seed dispersion, feature importance, regime breakdown). It does NOT pre-review the brief or
the `src/` diff (no Phase 6.0). Its review is **stage-aware**:

- At **EXPLORATION**, the goal is a fast screen. The Critic judges whether the hypothesis showed
  signal worth confirming (PROMISING) or not (NEGATIVE) — it does NOT apply the merge gate.
- At **CONFIRMATION**, the Critic applies the merge gate above (better-than-baseline + lottery-bias
  + methodology) and returns MERGE or NO-MERGE.

**Every Critic review — PASS or FAIL, exploration or confirmation — MUST end with a "Proposed
Backtest Changes" section: 2–3 concrete, runnable backtest modifications** (e.g. "re-run with
`--slippage-bps 4` to test cost-robustness", "widen training_days lower bound", "add R2 drawdown
scaling at trigger 8%", "drop INERT feature X and re-screen"). The Critic's job is not only to
catch problems but to push the next experiment forward.

The Critic still runs the methodology audit on results: look-ahead/embargo evidence, CV gap,
reproducibility (feature_columns pinned, seeds fixed), hypothesis-implementation alignment, and
the Anti-Pattern static scan over foundation code (`walk_forward`, labeling, `optimization`,
`lgbm._train_for_month`). A methodology violation found in results → NO-MERGE.

---

## NO CHEATING — absolute rules

- NEVER change `start_time` to skip bad IS months. The backtest runs from earliest data.
- NEVER cherry-pick date ranges, post-hoc filter trades, or tune parameters on OOS.
- NEVER let labels leak across CV folds: `gap = (timeout_candles + 1) * n_symbols` (n_symbols=1).
- NEVER let labels leak from the future: `train_end_ms = test_start_ms - embargo_ms` is law.
- NEVER reintroduce full-window training. `training_days` is searched and applied consistently.
- NEVER merge without a CONFIRMATION run and a Critic MERGE verdict.
- NEVER trust an offline trade-subtraction/addition projection to estimate an entry-gate effect —
  the v1 position model is sequential; suppressing an entry frees the slot and cascades later
  trades. Only a real backtest with the rule wired in is the verdict.
- NEVER include a v2/v3 symbol (`V1_EXCLUDED_SYMBOLS`). NEVER import from `features_v2`/`features_v3`.

To improve a result: improve the STRATEGY (features, labeling, model, risk) — not the measurement.

---

## Filesystem map (per-symbol; symbol attached to EVERYTHING)

```
reports-v1/<SYMBOL>/iteration_v1-NNN/{in_sample,out_of_sample}/...   # runner-generated
reports-v1/<SYMBOL>/iteration_v1-NNN/comparison.csv
briefs-v1/<SYMBOL>/iteration_v1-NNN/feature_report.md               # FE
briefs-v1/<SYMBOL>/iteration_v1-NNN/risk_report.md                  # RE
briefs-v1/<SYMBOL>/iteration_v1-NNN/research_brief.md               # QR
briefs-v1/<SYMBOL>/iteration_v1-NNN/phase5p5_gate.md                # QE
briefs-v1/<SYMBOL>/iteration_v1-NNN/review.md                       # Critic
diary-v1/<SYMBOL>/iteration_v1-NNN.md                               # QR
analysis/<SYMBOL>/iteration_v1-NNN/*.py                             # committed IS-only scripts
BASELINE_V1_<SYMBOL>.md                                             # per-symbol baseline
```

The runner nests `reports_dir = reports-v1/<SYMBOL>` automatically; briefs/diary/analysis dirs are
created by the orchestrator. The single-symbol assertion guards the symbol resolution.

---

## Running a backtest

```
# EXPLORATION (bagging K=3, fast screen; --n-trials = per-seed Optuna budget):
uv run python run_baseline_v1.py --exploration --iteration NNN --symbols BTCUSDT --n-trials 35 --slippage-bps 2

# CONFIRMATION (bagging K=20, merge decision):
uv run python run_baseline_v1.py --confirmation --iteration NNN --symbols BTCUSDT --n-trials 35 --slippage-bps 2
```

The first confirmation for a symbol bootstraps `BASELINE_V1_<SYMBOL>.md`.

---

## Before you start (read every time)

1. `BASELINE_V1_<SYMBOL>.md` for the symbol under study (or note none exists → first run = bootstrap CONFIRMATION).
2. The last 3 `diary-v1/<SYMBOL>/` entries — "Next Iteration Ideas" often seeds the next axis.
3. This skill file.
4. `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/MEMORY.md`.

Then determine the next iteration number and run the flow. Start with BTCUSDT.
