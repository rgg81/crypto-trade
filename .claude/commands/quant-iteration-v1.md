---
name: quant-iteration-v1
description: "Quant research/engineering iteration workflow for the crypto-trade LightGBM strategy — v1 TRACK (REFACTORED 2026-05-23: corrected walk-forward baseline + v3 rigor + four QR↔Critic dynamic improvements + new LightGBM Master advisor agent). Use this skill whenever the user mentions: v1 iteration, quant-iteration-v1, iter-v1, iter-v1/NNN, BASELINE_V1, briefs-v1, diary-v1, reports-v1, ITERATION_PLAN_8H_V1, run_baseline_v1, v1 research brief, v1 diary, v1 merge decision, v1 baseline comparison, Phase 4.5, Phase 5.5, Phase 6.0, Phase 7.4, Phase 7.5, Critic agent, Critic review, review.md, lgbm_advisor.md, LightGBM Master, lightgbm-master, Constructive Critic, BLOCK-PENDING-FIX, Axis Rotation Discipline, HIGH-RISK axis declaration, pre-Phase 6 review, V1_EXCLUDED_SYMBOLS, features_v1, validation_v1, run_baseline_v1, Pareto front, Pareto dominance, meta-labeling, primary plus meta model, fractional Kelly, fractional differentiation ADF, ADF stationarity, CPCV mandatory, PBO < 0.4, PSR > 0.95, pre-registered failure mode, pre-registered MERGE/NO-MERGE criteria, library stack declaration. Also trigger when the user says: 'start v1 iteration', 'run v1 phase', 'evaluate v1 reports', 'write v1 diary', 'v1 merge decision', 'invoke Critic for v1', 'invoke LM Master', 'invoke LightGBM Master'."
---

# Quant Iteration Skill — v1 (Rigor + Creator-Role-Augmented Track)

## Mission

v1 was the founding strategy track. After 186 iterations on `iteration_NNN/`, it was deployed to live trading on BTC/ETH/LINK/LTC/DOT. Then at iter-v3/058 we discovered a serious walk-forward look-ahead bug: `train_end_ms = test_start_ms` with no embargo, allowing training labels to scan forward into the test window. The fix landed at `walk_forward.py:113` (`train_end_ms = test_start_ms - embargo_ms`). Re-running the v1 stack under the corrected walk-forward produces materially worse OOS numbers than the historical `iteration_186` headline. The old v1 baseline was inflated by leaked labels.

This refactor restarts v1 from scratch with the **corrected stats as the formal baseline**, bringing v1 up to v3's rigor (CPCV, DSR, PBO, PSR, ADF, IC, meta-labeling, fractional Kelly) AND adding four structural improvements the v3 cycle-7 forensic identified:

1. **LightGBM Master agent** — a read-only ML specialist that fires Phase 4.5 (pre-design hyperparameter/feature recommendations) and Phase 7.4 (post-backtest interpretation). Closes the v3 cycle-7 gap where QR + Critic are both evaluators with no "creator" role to inject fresh structural axes.
2. **Constructive Critic** — every BLOCK verdict (EXPLORATION-NEGATIVE / CONFIRMATION-BLOCK / BLOCK-PENDING-FIX / BLOCK-FINAL) MUST include a "Path Forward" section proposing 2-3 alternative axes from families NOT used in the prior 5 EXPLORATIONs. Rigor unchanged; dead-end-feeling reduced.
3. **Critic pre-Phase 6 review (Phase 6.0)** — after Phase 5.5 PASS but BEFORE backtest launches, Critic does a SHORT review of (a) the brief for look-ahead / anti-patterns / missing falsifiers, and (b) QE's src/ diff vs baseline for anti-pattern Catalog hits. Catches issues BEFORE compute is spent. Output: `critic_preflight.md` with OVERALL=PASS or OVERALL=BLOCK.
4. **BLOCK-PENDING-FIX softening** — Phase 7.5 Critic verdict can be `BLOCK-PENDING-FIX` for a specific isolated defect, granting the QR/QE ONE chance to fix and re-run Phase 6 within the SAME iter-v1/NNN. After the fix attempt, next verdict can only be PASS or `BLOCK-FINAL` — no further recursion. Reduces wasted iterations on near-miss briefs without compromising rigor.

Plus a **QR creativity mandate** (Axis Rotation Discipline): if the last 5 EXPLORATIONs were from the same axis family, the next EXPLORATION MUST be from a different family. Codifies the v3 cycle-7 lesson — knob-tuning inertia within /121's architecture family produced 9/9 NEGATIVE.

v1 is now the **rigor + creator-role-augmented track**, parallel to v2 (diversification arm) and v3 (rigor-only arm). All three coexist.

We do not predict the future. We identify moments when the distribution of forward returns is skewed in our favor, and we bet accordingly, sized by our conviction and disciplined by our risk framework. We build strategies that would survive scrutiny by López de Prado, Bailey, Harvey, Carver. **No p-hacking. No overfitting. No self-deception.** If a strategy cannot withstand combinatorial purged cross-validation, deflated Sharpe ratio tests, probability-of-backtest-overfitting tests, AND adversarial Critic review, it does not trade.

The 186 historical iterations taught us what does not work. That knowledge is as valuable as what does. The corrected v1 baseline is the honest starting point for iteration v1-001+.

---

## Relationship to v2 and v3

Three sibling tracks. The user can run `/quant-iteration-v1` (this skill), `/quant-iteration-v2`, or `/quant-iteration-v3` at any time. None is frozen.

| Aspect | v1 (THIS — refactored 2026-05-23) | v2 | v3 |
|---|---|---|---|
| Symbols (initial baseline) | BTC, ETH, LINK, LTC, DOT (5 — original v1) | SOL, XRP, DOGE, NEAR (4) | BCH, LDO, TRX (3) |
| Symbol universe (available) | All Binance perpetuals minus `V1_EXCLUDED_SYMBOLS` | Fixed at SOL, XRP, DOGE, NEAR | All minus V3_EXCLUDED_SYMBOLS |
| Excluded symbols | SOL, XRP, DOGE, NEAR (v2), BCH, LDO, TRX (v3), BNB (reserved) | BTC, ETH, LINK, BNB | v1 + v2 universes + BNB + MKR |
| Features | `crypto_trade.features_v1` (193 cols, 9 groups — corrected) | `crypto_trade.features_v2` (34 cols) | `crypto_trade.features_v3` (14 cols top-N) |
| Risk layers | R1+R2+R3 (legacy) — v1 may evolve to v2/v3 patterns | RiskV2Wrapper (7 active gates) | RiskV3Wrapper (subclasses V2) |
| Validation | **CPCV mandatory + DSR + PBO + PSR (matches v3)** | TimeSeriesSplit + DSR | CPCV + DSR + PBO + PSR |
| Position sizing | **Meta-labeling (M1+M2) → fractional Kelly (matches v3)** | ATR-percentile vol scaling | M1+M2 + fractional Kelly |
| Roles | **QR + QE + Critic + LightGBM Master (4 roles)** | QR + QE | QR + QE + Critic |
| Phases | **12 (1, 2, 3, 4, 4.5, 5, 5.5, 6.0, 6, 7.4, 7.5, 7, 8)** | 8 | 10 (1-8 + 5.5 + 7.5) |
| Branch | `quant-research` ← `iteration-v1/NNN` | `quant-research` ← `iteration-v2/NNN` | `quant-research` ← `iteration-v3/NNN` |
| Tag | `v0.v1-NNN` | `v0.v2-NNN` | `v0.v3-NNN` |
| Reports | `reports-v1/iteration_v1-NNN/` | `reports-v2/iteration_v2-NNN/` | `reports-v3/iteration_v3-NNN/` |
| Briefs | `briefs-v1/iteration_v1-NNN/` (incl. `lgbm_advisor.md`, `phase5p5_gate.md`, `critic_preflight.md`, `review.md`) | `briefs-v2/iteration_v2-NNN/` | `briefs-v3/iteration_v3-NNN/` |
| Diaries | `diary-v1/iteration_v1-NNN.md` | `diary-v2/iteration_v2-NNN.md` | `diary-v3/iteration_v3-NNN.md` |
| EXPLORATION ENSEMBLE_SIZE | 3 (matches v3) | n/a (no cadence) | 3 |
| CONFIRMATION ENSEMBLE_SIZE | 10 (matches v3) | n/a | 10 |
| Outer seed loop | None — single-pass inner ensemble (matches v3 post-/059) | 5 outer seeds (v1-style) | None |
| Wall-clock targets | EXPLORATION 2h target / CONFIRMATION 8h target — design-time guidance only, NO runtime kill-switch (2026-05-30) | no formal cap | EXPLORATION 2h / CONFIRMATION 6h |
| Cadence | 10:1 EXPLORATION:CONFIRMATION | none | 10:1 |
| Auto-trigger | `iter-v1/NNN`, `BASELINE_V1`, `Phase 4.5`, `Phase 6.0`, `Phase 7.4`, `lgbm_advisor`, `LightGBM Master` | `iter-v2/NNN`, `BASELINE_V2.md` | `iter-v3/NNN`, `BASELINE_V3.md` |

**Shared (sacred across all three tracks):**
- `OOS_CUTOFF_DATE = 2025-03-24` — immutable
- `training_months = 24` — immutable
- 8h candles
- 10-seed pre-MERGE concentration validation (where applicable)
- Hard merge floor: IS Sharpe > 1.0 AND OOS Sharpe > 1.0
- ≥10 trades/month OOS, ≥130 OOS total
- Top symbol concentration ≤ 30% of OOS PnL (or explicit exception with justification)
- "QR uses IS data" — every Phase 5 brief must contain numerical tables from a committed `analysis/iteration_v1-NNN/*.py` script
- Walk-forward backtest runs on full data; reports split at `OOS_CUTOFF_DATE`
- Forming candles must be dropped (`fetcher.py:if k.close_time < now_ms`)
- **Walk-forward train_end_ms = test_start_ms - embargo_ms** (the iter-v3/058 fix; cannot regress)

**v1-only (compared to v2/v3):**
- 4-role workflow with LightGBM Master advisor (v3 has 3 roles)
- Phase 4.5 (LM Master pre-design)
- Phase 6.0 (Critic pre-flight review)
- Phase 7.4 (LM Master post-mortem)
- BLOCK-PENDING-FIX verdict semantics
- Axis Rotation Discipline (mandatory family rotation every 5 EXPs)
- HIGH-RISK axis declaration (brief Section 2.5 — mitigation = pre-commit to CONFIRMATION at next iter; NO seed-count bump at EXPLORATION; ENSEMBLE_SIZE=3 is non-negotiable per [[v1-seed-count-non-negotiable]])
- Path Forward section mandatory on every Critic BLOCK verdict

---

## Before You Start

Read these files in order, EVERY time this skill is triggered:

1. **`ITERATION_PLAN_8H_V1.md`** at the repo root — the v1 workflow doc
2. **`BASELINE_V1.md`** at the repo root — current v1 baseline metrics (corrected walk-forward), hard constraints, V1_EXCLUDED_SYMBOLS
3. **The last 3 entries in `diary-v1/`** — what's recently been tried; "Next Iteration Ideas" from the last diary often seeds the next iteration
4. **This skill file** (`.claude/commands/quant-iteration-v1.md`) — the workflow definition
5. **`/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/MEMORY.md`** — active decisions and feedback rules
6. **`briefs-v1/exploration_catalog.md`** — EXPLORATION ledger (for cadence + axis rotation tracking)

### Default Flow: Full Autopilot

When this skill is triggered, **do NOT ask which role to play or whether to proceed**. Default behavior:

1. Read the last v1 diary's "Next Iteration Ideas" and `BASELINE_V1.md`
2. Determine the next iteration number (next iter-v1/NNN)
3. Run the full flow:
   - QR Phases 1–4 (research design through feature selection) — uses `quant-researcher` agent
   - **Phase 4.5 — LightGBM Master pre-design advisory** — uses `lightgbm-master` agent (read-only); emits `lgbm_advisor.md`
   - QR Phase 5 (research brief authoring) — `quant-researcher` agent; integrates LM Master recommendations
   - **Phase 5.5 Gate** — `quant-engineer` agent verifies brief completeness; PASS or BLOCK
   - **Phase 6.0 — Critic pre-flight review** — `quant-critic` agent; reviews brief + src/ diff; PASS or BLOCK
   - QE Phase 6 (implementation + backtest) — `quant-engineer` agent
   - **Phase 7.4 — LightGBM Master post-mortem** — `lightgbm-master` agent; appends to `lgbm_advisor.md`
   - **Phase 7.5 Critic Review** — `quant-critic` agent; emits `review.md`; OVERALL=EXPLORATION-PROMISING / EXPLORATION-NEGATIVE / CONFIRMATION-MERGE / BLOCK-PENDING-FIX / BLOCK-FINAL
   - If `BLOCK-PENDING-FIX`: QR/QE addresses single defect, re-runs Phase 6, returns to Phase 7.5 ONCE; next verdict must be PASS or BLOCK-FINAL
   - QR Phase 7 (OOS evaluation) — `quant-researcher` agent
   - QR Phase 8 (diary + merge decision) — `quant-researcher` agent
4. Commit/tag per the v1 git workflow
5. After completing Phase 8, **immediately start the next iteration** — go back to step 1
6. Keep looping iterations until the user intervenes or context runs out
7. Only pause if there's an actual blocker (ambiguous brief that the QR can't resolve, unexpected error, decision that genuinely requires user input)

The user can override by specifying a role ("be the QR for iter-v1/003"), a phase ("run Phase 6.0"), or a track ("/quant-iteration-v3 instead"). Otherwise, go.

---

## NO CHEATING — ABSOLUTE RULES

**NEVER** do any of the following to improve metrics artificially:

- **NEVER change `start_time`** to skip bad IS months. The backtest MUST run from the earliest available data. Trimming the evaluation window is CHEATING — it hides losses instead of fixing the strategy.
- **NEVER cherry-pick date ranges** to make IS or OOS look better.
- **NEVER post-hoc filter trades** from the results to improve metrics.
- **NEVER tune parameters on OOS data** (the researcher sees OOS only in Phase 7).
- **NEVER allow labels to leak across CV fold boundaries.** The `gap` parameter MUST be set correctly: `gap = (timeout_candles + 1) × n_symbols`. The QE MUST verify this in EVERY iteration. This is non-negotiable.
- **NEVER allow labels to leak from live/prediction data to training data.** Each month's model trains ONLY on past klines. Labels for training samples must not scan past the training window boundary. **`train_end_ms = test_start_ms - embargo_ms` is law — anything else is the iter-v3/057-style bug.**
- **NEVER skip the Phase 5.5 gate.** The Engineer's gate file (`phase5p5_gate.md`) must exist with OVERALL=PASS before Phase 6.0 starts.
- **NEVER skip the Phase 6.0 pre-flight.** The Critic's pre-flight file (`critic_preflight.md`) must exist with OVERALL=PASS before Phase 6 backtest launches.
- **NEVER merge without `OVERALL=CONFIRMATION-MERGE` from the Critic.** Phase 7.5's `review.md` is a hard gate. OVERALL=BLOCK-FINAL means NO-MERGE regardless of headline metrics.
- **NEVER rerun the Critic on a "let me fix one thing" basis AFTER a BLOCK-FINAL verdict.** The single BLOCK-PENDING-FIX rerun is the ONLY allowed retry; after it produces a verdict, that verdict is final (no further recursion).
- **NEVER include a v2 or v3 symbol in v1's universe.** `V1_EXCLUDED_SYMBOLS` is enforced at runtime by the runner.
- **NEVER import from `crypto_trade.features_v2` (v2) or `crypto_trade.features_v3` (v3) in v1 code.** Track isolation is structural.
- **NEVER bypass the LightGBM Master advisory.** Phase 4.5 must produce `lgbm_advisor.md` before Phase 5 brief authoring; Phase 7.4 must produce the post-mortem before Phase 7.5 Critic review. LM Master's recommendations are advisory (QR can ignore) but the artifact MUST exist.

To improve IS Sharpe: improve the STRATEGY (features, model, labeling) — not the measurement window. A strategy that only works from 2023 onward is NOT robust.

---

## THE MOST IMPORTANT RULE: IS/OOS Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
training_months = 24             ← FIXED. NEVER CHANGES.
```

This split exists to prevent **researcher overfitting** — not model leakage. The walk-forward / CPCV backtest already prevents model-level leakage by training only on past data each month, with embargo.

### What the split means

- The **Quant Researcher** uses ONLY IS data (before 2025-03-24) during Phases 1–5 (design). This prevents the researcher from unconsciously tuning features, labeling, or parameters to fit recent patterns.
- The **walk-forward / CPCV backtest runs on ALL data** (IS + OOS) as one continuous process. No artificial wall at the model level. The backtest rolls through OOS exactly as it would in live trading.
- The **LightGBM Master** in Phase 4.5 uses only IS data, prior diaries, and prior iteration reports. NO OOS access.
- The **reporting layer** splits trade results at `OOS_CUTOFF_DATE` into `in_sample/` and `out_of_sample/` report directories plus a `comparison.csv` with OOS/IS ratios.
- The **Quant Researcher** sees OOS results for the FIRST time in Phase 7 (evaluation).

The IS/OOS gap in `comparison.csv` tells you whether the researcher's design choices generalize beyond the data they could see. Hard floor: `OOS_Sharpe / IS_Sharpe ≥ 0.5` per project memory.

This constant lives in `src/crypto_trade/config.py`.

---

## Four Roles

You operate as ONE of four roles for each phase. In autopilot mode (default), you switch roles automatically — no need to ask.

| Role | Phases | Agent | Tools | Model |
|---|---|---|---|---|
| **Quant Researcher (QR)** | 1, 2, 3, 4, 5, 7, 8 | `quant-researcher` | Read, Glob, Grep, Bash, WebFetch, WebSearch, NotebookRead, NotebookEdit, Edit, Write, TodoWrite | opus |
| **LightGBM Master (LM)** | **4.5, 7.4 (NEW)** | `lightgbm-master` | **Read, Glob, Grep, Bash (read-only)** | opus |
| **Quant Engineer (QE)** | 5.5 (gate), 6 | `quant-engineer` | Read, Glob, Grep, Bash, Edit, Write, TodoWrite | sonnet |
| **Quant Critic** | **6.0 (pre-flight, NEW), 7.5 (adversarial)** | `quant-critic` | **Read, Glob, Grep ONLY** (read-only by structural design) | opus |

### Quant Researcher (QR)
- **Owns:** data analysis (Phase 1), labeling decisions (Phase 2), symbol selection (Phase 3), feature design (Phase 4), research brief authoring (Phase 5), OOS evaluation (Phase 7), diary + merge decision (Phase 8)
- **Produces:** research briefs, diary entries, evaluation memos
- **Does NOT:** write production code in `src/`. Uses notebooks (`notebooks/`) and analysis scripts (`analysis/iteration_v1-NNN/*.py`) only.
- **Data access:** IS data only during Phases 1–5; sees OOS reports only in Phase 7.

### LightGBM Master (LM)
- **Owns:** Phase 4.5 (pre-design hyperparameter + feature recommendations), Phase 7.4 (post-backtest interpretation: feature-importance triage, hyperparameter instability flags, next-iter tuning ideas)
- **Produces:** `lgbm_advisor.md` (Phase 4.5 initial; Phase 7.4 appended or new section)
- **Does NOT:** edit src/ code, BLOCK iterations, make merge decisions, override the QR's hypothesis
- **Authority:** ADVISORY ONLY — QR can adopt, modify, or explicitly reject recommendations
- **Data access:** IS data only in Phase 4.5; reports (including OOS) in Phase 7.4

### Quant Engineer (QE)
- **Owns:** Phase 5.5 gate verification (refuses incomplete briefs), production Python code (`src/`), pipeline architecture, backtest engine, report generation, library installs
- **Produces:** `src/` implementation, `phase5p5_gate.md`, engineering reports, backtest reports (IS + OOS report batches), `comparison.csv`, companion files
- **Does NOT:** make research decisions. If the brief is ambiguous, BLOCKs at Phase 5.5 and returns to QR.
- **Backtest:** runs walk-forward / CPCV on full dataset; reports split at `OOS_CUTOFF_DATE`.

### Quant Critic
- **Owns:** Phase 6.0 (pre-flight review of brief + src/ diff), Phase 7.5 adversarial review of every iteration before merge
- **Produces:** `critic_preflight.md` (Phase 6.0: PASS or BLOCK), `review.md` (Phase 7.5: full 8 checks + OVERALL verdict)
- **Does NOT:** write code, briefs, or diaries. Cannot rerun backtests (read-only tools). Cannot negotiate verdict.
- **Verdict authority:** BLOCK-FINAL is non-negotiable. BLOCK-PENDING-FIX grants one rerun chance; PASS proceeds. **Path Forward section MANDATORY on every BLOCK verdict.**
- **Adversarial mindset by structure:** the Critic's job is to find reasons NOT to merge. "When in doubt, FAIL."

The four-role separation is v1's primary defense against the QR-implementing-and-self-reviewing failure mode AND the v3 cycle-7 "no creator role" failure mode. An engineer who just wrote the code is biased toward finding it correct; a separate Critic with fresh context catches errors that destroy strategies. AND a separate LightGBM Master with no role evaluative pressure can propose hyperparameters / features the QR + Critic loop would never generate.

### Critic Scope — What the Critic IS and IS NOT

**Critic's mandate (what the Critic checks):**
- **Anti-cheating**: no OOS tuning, no IS window trimming, brief Section 2 EDA ran on IS data only
- **Anti-look-ahead**: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms`, labels do not scan past training window boundary, no future data in feature construction
- **Anti-seed-fragility**: result is reproducible with same seed; Optuna seed sourcing is correct
- **Anti-methodology-mistake**: correct CV gap, correct training_months, correct atr_column for parquet, correct embargo applied, correct CPCV paths count

**Critic's mandate does NOT include:**
- Comparing trade-roster overlap between this iteration and the baseline — iterations use different configurations BY DESIGN (different features, labeling, weights, symbols, etc.). Different trades vs baseline is EXPECTED and correct.
- Demanding that all iterations produce similar trade rosters to the baseline
- Requiring frozen-HP ablation runs for every PROMISING headline
- Comparing to baseline via V3-style Jaccard trade-roster metrics

**The comparison metric is always OOS Sharpe / PnL / drawdown vs the BASELINE_V1 anchor**, not trade-roster similarity. Basin migration concern belongs in the LM Master post-mortem as informational context; it is NOT a Critic gate criterion.

---

## Sacred Constants

```
OOS_CUTOFF_DATE = 2025-03-24
training_months = 24
V1_EXCLUDED_SYMBOLS = ("SOLUSDT", "XRPUSDT", "DOGEUSDT", "NEARUSDT",
                       "BCHUSDT", "LDOUSDT", "TRXUSDT", "BNBUSDT")
V1_EXPLORATION_ENSEMBLE_SIZE = 3  # inner seeds for EXPLORATION
V1_CONFIRMATION_ENSEMBLE_SIZE = 10  # inner seeds for CONFIRMATION
ENSEMBLE_SEEDS = (42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006)
                  # first 3 for EXPLORATION, all 10 for CONFIRMATION
V1_OUTER_SEEDS_VALIDATION_ONLY = True
# LIVE-TRADING CONTRACT (IMMUTABLE, established framework/032+):
# Multi-outer-seed statistical validation (--seeds N) produces STATISTICAL
# VALIDATION artifacts only. The live engine ALWAYS runs single-outer-seed=42
# (inner-ensemble-averaged predictions). Live ONLY reads seed_42/ reports.
# Multi-outer-seed reports (seed_offset5/, etc.) are NEVER read by the live engine.
# Any change to this contract REQUIRES explicit user directive + diary entry.
```

Plus the v1 hard thresholds (mirroring v3):

```
DSR_threshold = 0.95     # Deflated Sharpe Ratio
PBO_threshold = 0.40     # Probability of Backtest Overfitting (LOWER is better)
PSR_threshold = 0.95     # Probabilistic Sharpe Ratio
IC_threshold  = 0.70     # |IC_pearson| between feature families (LOWER is better)
ADF_threshold = 0.05     # ADF p-value (LOWER is better — rejects unit root)
```

Plus inherited project-level merge gates:

- IS monthly Sharpe > 1.0
- OOS monthly Sharpe > 1.0
- OOS / IS Sharpe ratio ≥ 0.5
- ≥10 trades/month OOS, ≥130 OOS total trades
- Top symbol concentration ≤ 30% of OOS PnL (or explicit exception with justification)
- 10-seed pre-MERGE validation: mean Sharpe > 0, ≥7/10 profitable

**Any single gate failure = NO-MERGE.** This is by design — gates prevent weird trade-offs ("OOS Sharpe is 2.5 but only 8 trades" is not acceptable).

---

## Iteration Cadence Discipline

### Hard rules (inherited from v3 — proven; ENFORCED FROM CYCLE-3 v1 per user directive 2026-05-25)

**NON-NEGOTIABLE from cycle-3 onwards (user directive 2026-05-25):**

> "The QR should choose a combination of symbols, features, candles, Optuna iterations to fit in the exploration (3 seeds) and the confirmation (10 seeds). That's non negotiable from now on."

**Two dimensions FIXED (no QR/QE override):**
- Seed count: 3 inner seeds EXPLORATION / 10 inner seeds CONFIRMATION
- Wall-clock cap: 2h EXPLORATION / 6h CONFIRMATION

**Three dimensions QR-TUNABLE to fit the budget** (compress in this order):
1. **features**: 40 (PRUNED) → 30 → 20 (if axis isn't feature-family)
2. **candles**: 8h → 12h → daily (only if axis allows; re-anchor required)
3. **symbols**: 5 → 4 → 3 (if axis isn't universe)

**MANDATORY brief Section 3.6 (wall-clock estimate)**:
- Explicit wall-clock prediction from prior-iteration linear scaling
- Estimate ≤ cap with ≥20% margin
- Compression decisions documented if not at default
- Trade-off rationale (what's sacrificed for what)

**Phase 5.5 BLOCK criterion**: if wall-clock estimate is wildly unreasonable (>3× target cap) OR no explicit estimate present, BLOCK. QR must revise brief.

**NO RUNTIME KILL-SWITCHES (locked 2026-05-30 user directive).** Once a backtest is launched, it runs to natural completion or natural failure. Observed wall-clock feeds back into next-iteration estimate calibration. Killing mid-run wastes compute and produces no verdict — the cost of a 12h run that completes is FAR less than the cost of a 9h kill that produces nothing. Use the time as learning.

1. **EXPLORATION wall-clock target: 2h.** Brief MUST design to fit (single-axis variation, single-cohort preferred). If a brief estimates > 2h, Phase 6.0 Critic FLAGS as advisory — but the runtime is NOT auto-killed.

2. **CONFIRMATION wall-clock target: 8h.** Default `--confirmation --n-trials 35` + ENSEMBLE_SIZE=10. Brief Section 3.6 must show 5-step scaling. Critic Phase 6.0 FLAGS if estimate > 8h but no auto-kill. NO "CONFIRMATION-EXCEPTION" framing needed — design to fit; if it overruns, accept and learn.

3. **CONFIRMATION requires 10 EXPLORATION precedents.** A CONFIRMATION iteration's brief Section 0.5 MUST list ≥10 EXPLORATION iter-v1/NNN ids completed since the last CONFIRMATION (or since iter-v1/001 if no prior CONFIRMATION). Phase 5.5 gate verifies this count from `briefs-v1/exploration_catalog.md`.

4. **CONFIRMATION = bundle of best EXPLORATIONS.** The CONFIRMATION brief Section 3 lists which features/symbols/labels are imported from which prior EXPLORATION iter-v1/NNN ids. Not a fresh hypothesis — a curated combination.

5. **Only CONFIRMATION-MERGE updates BASELINE_V1.md.** EXPLORATION-PROMISING is a forward-pointer, not a baseline change. EXPLORATION-NEGATIVE is recorded in the catalog but never affects baseline.

The 10:1 ratio is the only cadence constraint. No daily/weekly limit — if 10 EXPLORATIONs complete in 6h of compute, the CONFIRMATION can launch immediately after.

### `briefs-v1/exploration_catalog.md` — the EXPLORATION ledger

Every EXPLORATION's diary appends a one-line entry to `briefs-v1/exploration_catalog.md` after Phase 8 commits. Schema:

```
| iter-v1-NNN | YYYY-MM-DD | axis varied | axis family | IS Sharpe Δ | OOS Sharpe (informational) | verdict | confirmation candidate? |
| ----------- | ---------- | ----------- | ----------- | ----------- | -------------------------- | ------- | ----------------------- |
| iter-v1/001 | 2026-MM-DD | example     | feature-family | +0.0500 | +0.0200 | EXPLORATION-PROMISING | YES |
```

The catalog accumulates across iterations. The next CONFIRMATION QR reads it, picks features/symbols/labels with positive deltas + PROMISING verdict, justifies the bundle in brief Section 3.

**Axis Family column is mandatory in v1** (new vs v3). It enables Axis Rotation Discipline enforcement — see §"QR Axis Rotation Discipline" below.

---

## QR Axis Rotation Discipline (NEW vs v3)

### The rule

Five axis families are catalogued:
- **feature-family** — adding/removing/modifying feature families (e.g., funding rates, OI, basis, on-chain, composed)
- **model-arch** — model architecture or family (LightGBM → XGBoost, depth → wide, native vs PyTorch)
- **labeling** — labeling method (triple-barrier params, meta-labeling architecture, threshold tuning)
- **universe** — symbol universe (adding/removing/substituting symbols)
- **risk-primitive** — risk gates, R1/R2/R3/RiskVN wrappers, vol scaling, exposure caps

**If the last 5 EXPLORATIONs were all from the same family**, the NEXT EXPLORATION MUST be from a different family. This is enforced in:

1. **Phase 5.5 gate** — QE counts the last 5 EXPLORATIONs in `briefs-v1/exploration_catalog.md`. If all 5 are same-family AND the new brief Section 0.6 declares the same family, BLOCK.
2. **Phase 7.5 Critic Check 14 (new check, v1-only)** — verifies axis family declared in brief Section 0.6 matches actual axis varied in src/ diff + reports.

**Why**: prevents knob-tuning inertia. The v3 cycle-7 lesson — 9/9 NEGATIVE within /121's same architecture family at single-seed budget — is codified here. After 5 same-family attempts produce no breakthrough, the search space within that family is exhausted at EXPLORATION budget; pivot.

### Brief Section 0.6 — Architecture-Family Justification (mandatory)

Every EXPLORATION brief's Section 0.6 declares:

```markdown
## Section 0.6 — Architecture-Family Justification

- **Axis family**: feature-family | model-arch | labeling | universe | risk-primitive
- **Prior 5 EXPLORATION families** (from exploration_catalog.md):
  - iter-v1/NNN-1: <family>
  - iter-v1/NNN-2: <family>
  - iter-v1/NNN-3: <family>
  - iter-v1/NNN-4: <family>
  - iter-v1/NNN-5: <family>
- **Rotation status**: VALID (different from majority of prior 5) | BLOCKED (same as last 5 — must rotate)
- **One-sentence rationale**: <why this family + axis is the right next step given the prior 5>
```

If the rotation status is BLOCKED, the brief must propose a different family OR explicitly request user override (which is logged in the diary as a deliberate exception).

---

## HIGH-RISK Axis Declaration (NEW vs v3 — lighter footing)

Every brief Section 2 must declare:

```markdown
## Section 2 — IS-Only Numerical Evidence

...
<existing IS evidence>
...

### Section 2.5 — HIGH-RISK Axis Declaration

**Does the proposed axis change Optuna's training-objective domain?**
(Yes if any of: risk-primitive constraint changes, universe substitution, label-mode change, feature-set replacement bar-interval change. No otherwise.)

- **Declaration**: HIGH-RISK | NORMAL-RISK
- **Reason**: <one sentence>
- **Mitigation (HIGH-RISK only)**: <if HIGH-RISK, QR MUST pre-commit to running this axis at CONFIRMATION budget (ENSEMBLE_SIZE=10) at iter-v1/NNN+1 if iter-v1/NNN produces EXPLORATION-PROMISING. No multi-seed validation at THIS iteration — EXPLORATION ALWAYS uses 3 inner seeds; CONFIRMATION is the ONLY 10-seed path.>
```

**SEED COUNT — NON-NEGOTIABLE (per user directive 2026-05-23, [[v1-seed-count-non-negotiable]]):**
- EXPLORATION = 3 inner seeds (`V1_EXPLORATION_ENSEMBLE_SIZE=3`), ALWAYS — even HIGH-RISK
- CONFIRMATION = 10 inner seeds (`V1_CONFIRMATION_ENSEMBLE_SIZE=10`), ONLY at CONFIRMATION
- NO outer-seed loop in v1 (single-pass inner ensemble, matches v3 post-/059 design)
- HIGH-RISK declaration is MANDATORY but does NOT permit a seed-count bump
- The HIGH-RISK mitigation is ONLY "pre-commit to CONFIRMATION at next iteration if PROMISING"
- Diary records the HIGH-RISK declaration + the PROMISING-triggers-CONFIRMATION pre-commit

If the iteration accumulates 3+ HIGH-RISK EXPLORATIONs producing >1σ negative deltas, the next HIGH-RISK iteration MUST be deferred to CONFIRMATION budget — i.e., CONFIRMATION at iter-v1/NNN+1 becomes mandatory rather than opt-in. This is the lighter-footing tripwire (vs v3's strict pre-emption).

---

## Symbol Universe — v1 (Expanded vs Historical)

Old v1 used a fixed 5-symbol universe (BTC, ETH, LINK, LTC, DOT). New v1 KEEPS those as the **initial baseline universe** (so the corrected baseline is comparable to the historical iteration_186 stack), but **expands the pool of available symbols** for EXPLORATIONs:

```python
V1_EXCLUDED_SYMBOLS = (
    # v2 traded (live, separate track)
    "SOLUSDT", "XRPUSDT", "DOGEUSDT", "NEARUSDT",
    # v3 traded (live, separate track)
    "BCHUSDT", "LDOUSDT", "TRXUSDT",
    # historical reservation (never traded; kept reserved)
    "BNBUSDT",
)
```

The runner enforces at startup:

```python
assert set(cfg.symbols).isdisjoint(V1_EXCLUDED_SYMBOLS), \
    f"v1 cannot trade v2/v3 symbols: {set(cfg.symbols) & set(V1_EXCLUDED_SYMBOLS)}"
```

### Initial baseline universe (BASELINE_V1.md anchor)

```python
V1_BASELINE_UNIVERSE = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT")
```

### Extended universe (available for EXPLORATIONs)

All Binance perpetuals NOT in `V1_EXCLUDED_SYMBOLS`. This includes:
- The 5 baseline symbols (BTC, ETH, LINK, LTC, DOT)
- MKR (dropped from v3 at iter-v3/013 — available for v1)
- AVAX, ADA, ATOM, MATIC, ICP, FIL, RUNE, AAVE, UNI, OP, ARB, LDO, etc.
- And ~80 other perpetuals

QR's universe-family EXPLORATIONs can add/swap symbols. CONFIRMATION-MERGE updates `V1_BASELINE_UNIVERSE` if the bundle changes universe.

---

## First Iteration Hard Rule (iter-v1/001 is the FIRST refactored iteration)

**iter-v1/001 is NOT a BOOTSTRAP.** The corrected v1 stack (5 symbols, models A/C/D/E, 193 features, RiskV1Wrapper) re-evaluated under the fixed walk-forward IS the baseline. `BASELINE_V1.md` is populated by re-running `iteration_186`'s config under the fixed `walk_forward.py:113` BEFORE iter-v1/001 starts.

Steps to populate the baseline (one-time, OUT OF SCOPE for iter-v1/001 but PREREQUISITE):

1. Confirm `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms`.
2. Run `uv run python run_baseline_v1.py --baseline-mode` (or whichever script reproduces the historical v1 baseline) on current data.
3. Capture all metrics: monthly_sharpe, daily_sharpe, max_drawdown, profit_factor, win_rate, n_trades, total_pnl, monthly_calmar, weighted_pnl_total, DSR, PBO, PSR, OOS trade count.
4. Write into `BASELINE_V1.md` as the "Headline Metrics" + "Corrected Walk-Forward Stats" sections.
5. Tag as `v0.v1-baseline-corrected`.

**iter-v1/001 ships:**
- First "real" EXPLORATION or first axis under the new workflow
- Any axis family is valid (Axis Rotation Discipline kicks in from iter-v1/006+ — needs 5 EXPLORATION history)
- Single-axis variation (EXPLORATION mode)
- Phase 4.5 LM Master advisory and Phase 7.4 post-mortem (both mandatory artifacts)
- Phase 6.0 Critic pre-flight (mandatory)
- Phase 7.5 Critic adversarial review (mandatory)

If iter-v1/001 produces an EXPLORATION-PROMISING verdict, the candidate is logged to the catalog and the next EXPLORATION begins. If EXPLORATION-NEGATIVE, recorded as dead-end, next EXPLORATION begins from a different axis (or different family per Axis Rotation Discipline once 5 EXPLORATIONs accumulate).

---

## Phase Quick Reference

| Phase | Role | Inputs | Outputs |
|---|---|---|---|
| 1. Data analysis & EDA | QR | IS data, last diary | Notebook scratch, observations |
| 2. Labeling decisions | QR | EDA findings | Brief Section 2 (params, σ_t source) |
| 3. Symbol selection | QR | EDA, V1_EXCLUDED_SYMBOLS | Brief Section 3 (universe + Gate 1–2 evidence) |
| 4. Feature design | QR | EDA, brief Sections 1–3 | Brief Section 4 (feature list with cluster-importance check) |
| **4.5 LM Master pre-design** | **LM** | QR's Phases 1-4 outputs, prior advisor, prior reports | `briefs-v1/iteration_v1-NNN/lgbm_advisor.md` (Phase 4.5 section) |
| 5. Research brief | QR | Sections 0–9 + LM advisor | `briefs-v1/iteration_v1-NNN/research_brief.md` (11 sections incl. 0.6, 2.5) |
| **5.5 Gate** | **QE** | Brief | `briefs-v1/iteration_v1-NNN/phase5p5_gate.md` (PASS or BLOCK) |
| **6.0 Critic pre-flight** | **Critic** | Brief, QE's src/ diff (after QE Phase 6 setup commit) | `briefs-v1/iteration_v1-NNN/critic_preflight.md` (PASS or BLOCK) |
| 6. Implementation + backtest | QE | Brief, both gates=PASS | `src/` commits, reports, `comparison.csv`, companion files, engineering report |
| **7.4 LM Master post-mortem** | **LM** | Engineering report, reports artifacts | `briefs-v1/iteration_v1-NNN/lgbm_advisor.md` (Phase 7.4 appended) |
| **7.5 Critic Review** | **Critic** | Brief, code, reports, lgbm_advisor | `briefs-v1/iteration_v1-NNN/review.md` (8+1 checks + OVERALL + Path Forward) |
| 7. OOS evaluation | QR | OOS reports, review.md, lgbm_advisor.md | Evaluation memo (informal; integrates Critic + LM findings) |
| 8. Diary + merge decision | QR | All above | `diary-v1/iteration_v1-NNN.md` (MERGE or NO-MERGE) |

Four gates are MANDATORY: **Phase 4.5, 5.5, 6.0, 7.5**. Skipping any is a process-integrity violation. Phase 7.4 LM Master post-mortem is mandatory in deliverable but does not BLOCK.

---

## Phase 4.5 — LightGBM Master Pre-Design Advisory (NEW)

After QR completes Phases 1–4 (EDA → Labeling → Symbol selection → Feature design) but BEFORE the QR begins Phase 5 (brief authoring), the orchestrator invokes the `lightgbm-master` agent.

### Orchestrator dispatch

```
Agent({
  description: "Run Phase 4.5 LM Master pre-design advisory for iter-v1/NNN",
  subagent_type: "lightgbm-master",
  prompt: "[Phase 4.5] Run pre-design advisory for iter-v1/NNN. Track: v1. Working dir: /home/roberto/crypto-trade/.worktrees/quant-research. Read: BASELINE_V1.md, last 3 v1 diaries, prior iter-v1/NNN-1 lgbm_advisor.md and engineering_report.md and feature_importance.csv, runner code, lgbm.py + optimization.py. QR's tentative axis: <one-line summary from last diary's 'Next Iteration Ideas' or current EDA notebooks>. Emit lgbm_advisor.md content as final message text per Phase 4.5 template — orchestrator persists at briefs-v1/iteration_v1-NNN/lgbm_advisor.md."
})
```

### LM Master's deliverable

`lgbm_advisor.md` (Phase 4.5 section) per the template in the `lightgbm-master` agent file. Approximately 300-500 words covering:

1. **Recommended hyperparameter direction** (2-4 items): specific param + range, expected effect, risk
2. **Recommended feature-engineering direction** (1-2 items): feature formula, why, expected importance rank
3. **Saturation risks to flag**: ML-side risks the QR may have missed
4. **What I did NOT recommend, and why**: prevents the QR from later asking "why didn't LM Master suggest X?"
5. **Closing note**: HIGH/MEDIUM/LOW confidence on the iteration

### QR's response

The QR reads `lgbm_advisor.md` BEFORE writing the brief. The brief's Section 3 (Proposed Changes) and Section 4 (Expected OOS Impact) must explicitly address each of LM Master's recommendations:

- **Adopted**: "LM Master recommended num_leaves 31→63; brief Section 3 includes this change."
- **Modified**: "LM Master recommended composed feature `momentum_regime_signed`; brief Section 4 uses a related but different formula because <reason>."
- **Rejected**: "LM Master recommended adding funding-rate features; brief rejects because v1 universe doesn't include funding endpoints yet (would require data infrastructure first)."

**The QR is NOT bound by LM Master's recommendations**, but the brief must show that LM Master was read and considered. Phase 5.5 gate verifies the brief contains LM Master responses.

---

## Phase 5.5 — Pre-Phase 6 Gate (MANDATORY)

This is the skill's first structural defense against rushed iterations. The Engineer refuses to start Phase 6.0 until the brief contains all 11 mandatory sections (10 v3-shared + Section 0.6 v1-only).

### The 11 Mandatory Brief Sections

The Engineer reads `briefs-v1/iteration_v1-NNN/research_brief.md` and verifies:

- **Section 0 — Data Split declaration.** Confirms `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are unchanged. Names the IS window and OOS window in absolute dates.
- **Section 0.5 — Iteration Type Declaration.** ONE of:
  - `TYPE: EXPLORATION` — single-axis variation. **Wall-clock target: 2h** (design-time guidance; NO runtime kill). Uses `--exploration` flag (`V1_EXPLORATION_ENSEMBLE_SIZE=3`, n_trials=18 default). Single-axis variation. Critic scores Checks 1, 2, 4, 5, 6, 8, 14 (methodology + look-ahead + axis-family axes only). Edge thresholds (Check 3 DSR/PSR/Sharpe) are SKIPPED. Critic emits `EXPLORATION-PROMISING` (signal found, candidate for CONFIRMATION inclusion) or `EXPLORATION-NEGATIVE` (no signal, recorded in catalog).
  - `TYPE: CONFIRMATION` — production config. Uses default `V1_CONFIRMATION_ENSEMBLE_SIZE=10`, full Optuna search space. Default `--n-trials 35`. **Wall-clock target: 8h** (design-time guidance; NO runtime kill). Critic scores all 8+1 checks AND optional 9-12 including Check 3 DSR/PSR thresholds. Critic emits `CONFIRMATION-MERGE`, `CONFIRMATION-BLOCK`, `BLOCK-PENDING-FIX`, or `BLOCK-FINAL`. **Only CONFIRMATION-MERGE updates BASELINE_V1.md.**
  - Brief MUST justify the type choice in 1-2 sentences. CONFIRMATION iterations require ≥10 EXPLORATION-PROMISING precedents (referenced by iter-v1/NNN ids) unless first-iteration.
- **Section 0.6 — Architecture-Family Justification (v1-only).** Per the Axis Rotation Discipline section above. BLOCK if rotation rule violated.
- **Section 1 — Hypothesis.** ONE sentence. What changes and why we expect OOS improvement. Vague hypotheses BLOCK; specific testable hypotheses PASS.
- **Section 2 — IS-Only Numerical Evidence.** Tables produced by a committed `analysis/iteration_v1-NNN/*.py` script. Reproducible, IS-data-only, concrete numbers. Category-matching ("similar to RSI") is NOT evidence — BLOCK.
  - **Section 2.5 — HIGH-RISK Axis Declaration (v1-only)** per the HIGH-RISK section above.
- **Section 3 — Proposed Changes.** Enumerated: labeling params, symbol set additions/removals (with V1_EXCLUDED_SYMBOLS check), feature additions/removals (with cluster-importance check), risk gate changes. **Must include LM Master responses** (adopted/modified/rejected).
- **Section 4 — Expected OOS Impact.** Predicted Sharpe delta with confidence interval, plus an explicit falsifier ("if OOS Sharpe falls below X, the hypothesis is rejected").
- **Section 5 — Risk Mitigation.** R1/R2/R3 / 7-gate / new-gate changes; IS-calibrated thresholds; simulated effect on prior iterations.
- **Section 6 — Risk Management Design.** 8-primitive table or v1 equivalent; fire-rate predictions; regime coverage analysis.
- **Section 7 — Pre-Registered Failure-Mode Prediction.** 1–2 paragraphs predicting how this iteration most plausibly fails OOS, what the gates should catch, what the failure looks like in metrics. Phase 8 diary verifies this prediction against actual outcomes.
- **Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria.** Locked numerical thresholds before backtest. Example: "MERGE iff `OOS_monthly_Sharpe ≥ +1.8` AND `PBO < 0.4` AND `PSR > 0.95` AND no symbol > 35% of OOS wpnl".
- **Section 9 — Library Stack Declaration.** Versions of mlfinlab/mlfinpy/pypbo/fracdiff used.

### Cadence Verification

Phase 5.5 gate ALSO verifies cadence rules:

**For TYPE=EXPLORATION**:
- Brief Section 0.5 declares wall-clock budget ≤ 2h. BLOCK if missing or > 2h.
- Brief Section 3.5 changes ONE axis (features OR symbols OR labels — not multiple). BLOCK if cross-axis.
- Brief Section 0.6 declares axis family + rotation status. BLOCK if rotation violated.

**For TYPE=CONFIRMATION**:
- Count EXPLORATION iter-v1/NNN ids in `briefs-v1/exploration_catalog.md` since the last CONFIRMATION (or since iter-v1/001 if first). MUST be ≥ 10. BLOCK if < 10.
- Brief Section 3 lists ≥1 imported feature/symbol/label per source EXPLORATION iter-v1/NNN id. BLOCK if Section 3 is a fresh hypothesis (CONFIRMATION ≠ EXPLORATION).
- `ENSEMBLE_SIZE=10` (no outer seed loop). BLOCK if config differs.

### Gate Output

The Engineer writes `briefs-v1/iteration_v1-NNN/phase5p5_gate.md`:

```markdown
# Phase 5.5 Gate — iter-v1/NNN

OVERALL: PASS  (or BLOCK)

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION  (or CONFIRMATION)

## Axis Family (from Brief Section 0.6)
FAMILY: feature-family  (or model-arch / labeling / universe / risk-primitive)
ROTATION_STATUS: VALID  (or BLOCKED — same as last 5)

## HIGH-RISK Declaration (from Brief Section 2.5)
HIGH-RISK: NO  (or YES, mitigation = <opted-in multi-seed | none>)

## Cadence Check
- Wall-clock budget declared: <2h for EXPLORATION / <6h for CONFIRMATION>: PASS / BLOCK
- (CONFIRMATION only) EXPLORATION precedents since last CONFIRMATION: <count, ≥10 required>: PASS / BLOCK
- (CONFIRMATION only) Section 3 lists imported variations from prior EXPLORATIONs: PASS / BLOCK

## LM Master Response Verification
- briefs-v1/iteration_v1-NNN/lgbm_advisor.md exists: PASS / BLOCK
- Brief Section 3 addresses each LM Master recommendation: PASS / BLOCK

## Per-Section Status
- Section 0 (Data Split): PASS / MISSING / INVALID
- Section 0.5 (Iteration Type): PASS / MISSING / INVALID
- Section 0.6 (Architecture-Family Justification): PASS / MISSING / INVALID
- Section 1 (Hypothesis): PASS / MISSING / INVALID
- Section 2 (IS-Only Numerical Evidence): PASS / MISSING / INVALID
- Section 2.5 (HIGH-RISK Axis Declaration): PASS / MISSING / INVALID
- Section 3 (Proposed Changes): PASS / MISSING / INVALID
- Section 4 (Expected OOS Impact): PASS / MISSING / INVALID
- Section 5 (Risk Mitigation): PASS / MISSING / INVALID
- Section 6 (Risk Management Design): PASS / MISSING / INVALID
- Section 7 (Pre-Registered Failure-Mode): PASS / MISSING / INVALID
- Section 8 (Pre-Registered Numerical Criteria): PASS / MISSING / INVALID
- Section 9 (Library Stack): PASS / MISSING / INVALID

## Reasons (if BLOCK)
- <Section X>: <specific gap>
```

**OVERALL=BLOCK → Phase 6.0 terminates immediately.** Engineer commits the gate as `docs(iter-v1/NNN): phase 5.5 gate BLOCK` and returns to QR. The QR addresses gaps and re-submits; the Engineer re-runs the gate.

**OVERALL=PASS → Phase 6.0 (Critic pre-flight) proceeds.** Engineer commits the gate as `docs(iter-v1/NNN): phase 5.5 gate PASS`.

---

## Phase 6.0 — Critic Pre-Flight Review (NEW vs v3)

After Phase 5.5 PASS but BEFORE the full backtest launches, the Critic does a SHORT pre-flight review to catch issues that would waste compute.

### What the pre-flight checks

The pre-flight is a **subset** of the Phase 7.5 review, focused on issues catchable WITHOUT the engineering report:

1. **Brief look-ahead audit (mini-Check 1)**: read brief Section 4 (proposed feature changes); check whether any feature description suggests forward data use (e.g., "uses 24-hour rolling close including current bar"). FLAG only obvious cases; no exhaustive trace.
2. **Anti-Pattern Static Scan (mini-Check 13)**: grep QE's src/ diff vs the parent baseline branch for known anti-pattern signatures (A1-A13 catalog). Each unexplained match → BLOCK with citation.
3. **Foundation regression check (mini-Check 1+Boot Step 9)**: re-verify `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` AFTER QE's commits. Catches regressions introduced by the iteration's src/ changes.
4. **Cadence + axis sanity**: confirm Phase 5.5 gate is PASS; confirm Section 0.6 axis family declared.
5. **Falsifier presence**: confirm brief Section 4 has an explicit OOS-Sharpe-below-X falsifier.

### Orchestrator dispatch

```
Agent({
  description: "Run Phase 6.0 Critic pre-flight review for iter-v1/NNN",
  subagent_type: "quant-critic",
  prompt: "[Phase 6.0 PRE-FLIGHT] Run pre-flight review for iter-v1/NNN. Read briefs-v1/iteration_v1-NNN/research_brief.md AND briefs-v1/iteration_v1-NNN/phase5p5_gate.md (confirm OVERALL=PASS). Read QE's src/ diff: `git diff iteration-v1/<prior>..iteration-v1/<NNN> -- src/`. Run mini-checks 1, 13, foundation, cadence, falsifier. Emit critic_preflight.md content as final message text with OVERALL=PASS or OVERALL=BLOCK + Path Forward (if BLOCK). DO NOT run the full Phase 7.5 8-check pass — that is post-backtest only."
})
```

### Pre-flight output template

```markdown
# Phase 6.0 Critic Pre-Flight — iter-v1/NNN

OVERALL: PASS  (or BLOCK — <one-line top concern>)

## Pre-Flight Checks

### Check 1 (mini) — Brief Look-Ahead Audit: PASS
<one paragraph>

### Check 13 (mini) — Anti-Pattern Static Scan: PASS
<one paragraph; cite specific files scanned>

### Foundation Regression: PASS
<one paragraph; confirm walk_forward.py:113 still carries the embargo subtraction>

### Cadence + Axis Sanity: PASS
<one paragraph>

### Falsifier Presence: PASS
<one paragraph; quote the falsifier from brief Section 4>

## Path Forward (mandatory on any BLOCK)

(Only present if OVERALL=BLOCK. 2-3 alternative axes the QR should consider for revising the brief OR proposing a different iteration. Each from an axis family the QR has NOT used in the prior 5 EXPLORATIONs.)

1. **[Axis name]** — [family] — [one sentence: what's the proposed change, what's the expected mechanism]
2. **[Axis name]** — [family] — [...]
3. **[Axis name]** — [family] — [...]
```

**OVERALL=BLOCK → backtest does NOT launch.** QE returns to QR for brief revision (small fix possible: re-edit brief, re-run Phase 5.5 → Phase 6.0). After 1 brief revision + Phase 6.0 rerun, if still BLOCK, the iteration is abandoned and the next iter-v1/NNN+1 starts fresh.

**OVERALL=PASS → Phase 6 backtest launches.** QE proceeds with the full backtest per the Engineer's Split Dispatch (long backtests) or single dispatch (under 30 min).

### Why this matters

The v3 cycle-7 forensic identified that Critic catches misses POST-backtest, after compute is already spent. Phase 6.0 catches a subset of those misses BEFORE compute is spent. Estimated savings: 1-2 wasted 2h backtests per 10 iterations. Phase 6.0 adds ~10-15 min latency per iteration — clear net win.

---

## Phase 6 — Implementation + Backtest (QE)

Standard QE workflow per `quant-engineer` agent. Highlights for v1:

- Runner: `run_baseline_v1.py`
- Features module: `crypto_trade.features_v1`
- Validation module: `crypto_trade.validation_v1`
- `V1_EXCLUDED_SYMBOLS` audit at runtime startup
- `V1_FEATURE_COLUMNS` explicit list passed to `LightGbmStrategy` (never None / auto-discovered)
- Per-symbol or pooled models per brief Section 3.5
- 5-seed ensemble [42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006] — first 3 for EXPLORATION (`V1_EXPLORATION_ENSEMBLE_SIZE=3`), all 10 for CONFIRMATION (`V1_CONFIRMATION_ENSEMBLE_SIZE=10`)
- No outer seed loop (single-pass inner ensemble)
- All v3 rigor outputs: CPCV 45 paths, DSR/PBO/PSR in dsr.json + comparison.csv, ADF + IC matrix, Pareto front

### Split Dispatch for long backtests (inherited from v3)

Backtests > 30 min wall-clock use the split dispatch pattern (see v3 skill §"Engineer Phase 6 — SPLIT DISPATCH"). Setup-only Engineer dispatch → orchestrator launches detached bash → report-only Engineer dispatch. Saves agent quota.

---

## Phase 7.4 — LightGBM Master Post-Mortem (NEW)

After QE commits the engineering report (`OVERALL=READY-FOR-CRITIC`) and BEFORE invoking Critic Phase 7.5, the orchestrator invokes LM Master for post-mortem interpretation.

### Orchestrator dispatch

```
Agent({
  description: "Run Phase 7.4 LM Master post-mortem for iter-v1/NNN",
  subagent_type: "lightgbm-master",
  prompt: "[Phase 7.4 POST-MORTEM] Run post-mortem interpretation for iter-v1/NNN. Track: v1. Read briefs-v1/iteration_v1-NNN/research_brief.md, briefs-v1/iteration_v1-NNN/engineering_report.md, briefs-v1/iteration_v1-NNN/lgbm_advisor.md (Phase 4.5 section), reports-v1/iteration_v1-NNN/{comparison.csv, in_sample/feature_importance.csv, out_of_sample/feature_importance.csv, pareto_front.csv (if multi-seed), cpcv_paths.csv, ic_matrix.csv}. Run `grep 'Trial [0-9]+ finished' reports-v1/iteration_v1-NNN/run.log` to extract Optuna trial trajectories. Emit Phase 7.4 section of lgbm_advisor.md as final message text per the LM Master template — orchestrator appends to briefs-v1/iteration_v1-NNN/lgbm_advisor.md."
})
```

### LM Master's deliverable

Phase 7.4 section appended to `lgbm_advisor.md`. ~500-1000 words covering:

1. **Feature importance triage**: top performers, dead weight (rank 14/14 candidates), unstable features
2. **Hyperparameter trial stability**: best-trial loss std/mean across months, which params jumped wildly, which converged tightly
3. **Gain concentration audit**: top-3 feature cumulative gain%
4. **Suspicious patterns**: anything ML-suspicious the Critic might miss in their 8-check pass
5. **Next-iteration tuning recommendations** (3-5 items): specific changes, mechanisms, risks
6. **What this iteration confirms / refutes about prior LM Master advisory**: honest accounting of Phase 4.5 predictions vs actual outcomes
7. **Closing note for Critic**: flags evidence the Critic should look at (NOT directing the verdict)

The Critic reads `lgbm_advisor.md` in Phase 7.5 boot but is NOT bound by LM Master interpretations. Critic's 8-check verdict remains independent.

---

## Phase 7.5 — Critic Adversarial Review (UPDATED vs v3)

After Phase 7.4 LM Master post-mortem, the orchestrator invokes the `quant-critic` subagent for the full Phase 7.5 review.

### Updates vs v3

**1. New Check 14 — Axis Family Validation (v1-only).** Critic verifies axis family declared in brief Section 0.6 matches actual axis varied in src/ diff + reports.
- PASS: declared family matches observed change.
- FAIL: declared "feature-family" but src/ diff shows only risk-gate threshold changes (mis-declared family).

**2. New OVERALL values.** In addition to `EXPLORATION-PROMISING / EXPLORATION-NEGATIVE / CONFIRMATION-MERGE`, v1 adds:
- `BLOCK-PENDING-FIX` — One specific defect, QR/QE has ONE chance to fix and re-run Phase 6 within same iter-v1/NNN. After fix, next verdict can only be PASS or BLOCK-FINAL.
- `BLOCK-FINAL` — Irrecoverable. No rerun. Iteration ends NO-MERGE.

**3. Constructive Path Forward — mandatory on every BLOCK verdict.** Every BLOCK verdict (EXPLORATION-NEGATIVE / CONFIRMATION-BLOCK / BLOCK-PENDING-FIX / BLOCK-FINAL) MUST include a "Path Forward" section proposing 2-3 alternative axes from families NOT used in the prior 5 EXPLORATIONs.

### BLOCK-PENDING-FIX rules

Critic chooses BLOCK-PENDING-FIX only when the defect is:
- **Specific** — one identifiable issue (not "the whole brief is wrong")
- **Isolated** — fixable without changing the iteration's hypothesis or axis
- **Fixable without methodology change** — examples: "comparison.csv missing PSR column", "feature scaling fit on combined train+test (line 142)", "Optuna seeds incorrectly derived from --seeds CLI"

Critic chooses BLOCK-FINAL when:
- Multi-defect (≥2 distinct failures)
- Methodology-level issue (e.g., look-ahead in the hypothesis itself, not a code bug)
- Axis-family mis-declaration (Check 14 FAIL is BLOCK-FINAL — methodology integrity issue)
- The defect would require a NEW iteration with a NEW brief

### BLOCK-PENDING-FIX flow

1. Critic emits `review.md` with `OVERALL: BLOCK-PENDING-FIX — <defect>` + Path Forward.
2. QR + QE read the defect. QR may NOT introduce a new hypothesis or change axis. QE makes the specific fix to src/ or comparison.csv.
3. The fix attempt is committed: `fix(iter-v1/NNN): <defect> — pending Critic re-eval`.
4. QE re-runs Phase 6 backtest (or just regenerates the specific affected output if a non-code fix).
5. The fix attempt is logged in `briefs-v1/iteration_v1-NNN/qr_response.md` (re-using existing v3 file convention) with:
   - Defect quoted from Critic's verdict
   - Fix made (cite commit SHA)
   - New reports artifacts
6. Critic re-runs Phase 7.5 (single pass; no PRELIMINARY round). Possible verdicts: PASS verdict (EXPLORATION-PROMISING / EXPLORATION-NEGATIVE / CONFIRMATION-MERGE) OR `BLOCK-FINAL`.
7. After this second verdict, the iteration cannot recurse further.

### Path Forward section template

Mandatory on EVERY BLOCK verdict (EXPLORATION-NEGATIVE / CONFIRMATION-BLOCK / BLOCK-PENDING-FIX / BLOCK-FINAL):

```markdown
## Path Forward (mandatory on any BLOCK verdict)

Propose 2-3 alternative axes the QR should consider for the next iteration:

1. **[Axis name]** — [family] — [one sentence: what's the proposed change, what's the expected mechanism]
2. **[Axis name]** — [family] — [...]
3. **[Axis name]** — [family] — [...]

Constraints honored: each proposed axis is from a family the QR has NOT used in the prior 5 EXPLORATIONs.
```

The Critic's Path Forward is advisory — QR can adopt, modify, or reject the suggestions. It exists to prevent the QR from feeling "dead-ended" by a BLOCK verdict.

**Constructive Critic Mandate:** A BLOCK verdict without a credible Path Forward is a Critic methodology failure, not a rigor signal. Every blocked verdict MUST propose axes that are:
- From DIFFERENT families than the last 5 EXPLORATIONs (Rotation Discipline enforced in suggestions too)
- Specific enough to be directly actionable by the QR (not vague "try different features")
- Ranked by expected signal-to-noise ratio given the iteration history

If the Critic cannot propose 2 credible alternatives, the Critic MUST explicitly state this constraint (e.g., "axis family space is exhausted — recommend user directive to expand search space") rather than offering generic advice.

### Verdict mechanics (round structure inherited from v3, with v1 additions)

**Round 1 — PRELIMINARY review** (same as v3 — preliminary findings + clarifications requested).

**Round 2 — QR Response** (same as v3 — qr_response.md).

**Round 3 — FINAL Verdict** (updated v1 set): one of `EXPLORATION-PROMISING / EXPLORATION-NEGATIVE / CONFIRMATION-MERGE / BLOCK-PENDING-FIX / BLOCK-FINAL`.

If verdict is `BLOCK-PENDING-FIX`, an additional ROUND 4 (post-fix re-evaluation, single pass) determines the iteration's final status.

**BLOCK-FINAL definition:** A BLOCK-FINAL verdict means the iteration is CLOSED with NO-MERGE status. The following are true:
- No further re-runs within this iter-v1/NNN are permitted
- The next iteration (iter-v1/NNN+1) starts fresh with a new brief
- Diary records the failure mode and the Critic's PATH FORWARD suggestions as the recommended next axes
- The Critic's Path Forward from a BLOCK-FINAL carries special weight: QR should treat the top suggestion as the default next axis unless there's strong IS evidence against it

---

## Verdict Cells

All verdict cells used in v1. Established through iteration history; new cells added as methodology evolves.

### EXPLORATION verdict cells

| Verdict | OOS Sharpe Δ | Condition | Next step |
|---|---|---|---|
| `EXPLORATION-PROMISING` | ≥ +0.05 | Single-seed lift, no confound flagged | Log to catalog, candidate for CONFIRMATION bundle |
| `EXPLORATION-NEGATIVE` | < 0 OR < +0.05 | No signal | Log to catalog as dead-end; next EXPLORATION |
| `NEGATIVE-no-effect` | main Δ ≈ 0 (within ±0.10 of baseline) | Axis had no effect; saturated or under-powered | Log to catalog; try higher n_trials or different axis |

Note: iterations CAN and SHOULD produce different configurations from the baseline (different features, labeling, weights, etc.) — this is the purpose of optimization. Different trades vs baseline is EXPECTED, not a flaw. OOS Sharpe/PnL/drawdown vs the BASELINE_V1 anchor is the comparison metric.

### CONFIRMATION verdict cells

| Verdict | Condition | Next step |
|---|---|---|
| `CONFIRMATION-MERGE` | All gates PASS; DSR > 0.95; PBO < 0.4; PSR > 0.95; Sharpe floors met | Update BASELINE_V1.md; tag commit |
| `CONFIRMATION-BLOCK` | ≥1 gate fails; Critic verdict non-MERGE | No baseline update; iterate on failed gates |
| `BLOCK-PENDING-FIX` | One specific isolable defect; NOT multi-defect | QE one-shot fix + re-run; next verdict is PASS or BLOCK-FINAL |
| `BLOCK-FINAL` | Irrecoverable (multi-defect OR methodology issue OR second BLOCK after BLOCK-PENDING-FIX) | NO-MERGE; next iter fresh brief |

---

## Mandatory Statistical-Significance Reporting

Every `comparison.csv` MUST include the following columns and rows (inherited from v3).

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
- `dsr` — Deflated Sharpe Ratio
- `pbo` — Probability of Backtest Overfitting (from CPCV's CSCV)
- `psr` — Probabilistic Sharpe Ratio
- `n_trials` — total Optuna trials
- `n_effective_trials` — PCA on trial-return matrix at 95% cumulative variance threshold

### Hard Thresholds

- **DSR > 0.95** — required for MERGE
- **PBO < 0.4** — required for MERGE (LOWER is better)
- **PSR > 0.95** — required for MERGE

**Any single threshold failure = automatic NO-MERGE.** Critic enforces this in Check 3.

---

## CPCV (Mandatory from iter-v1/001 onward)

### Recommended Configuration

```python
N = 10                  # number of test groups
k = 2                   # number of test groups in each split
n_paths = C(N, k) = 45  # total backtest paths
min_path_count = 10     # required minimum
```

### Constraints

- `min path_count = C(N, k) ≥ 10` for any reported result
- Purge gap = `(timeout_candles + 1) × n_symbols` symmetric on both sides of test boundary
- Embargo δ ≈ 1% of T per López de Prado convention (AFML Ch. 7)

### Walk-Forward as Fallback

Walk-forward (the existing `walk_forward.py` harness, with the iter-v3/058 embargo fix at `walk_forward.py:113`) is NOT removed. It is wrapped and kept for edge cases — specifically when label horizon × n_symbols is so large that purging eats the training window. Document the threshold in the brief's Section 9.

### Path-Level Statistics

The CPCV path matrix (45 paths × 4 metrics) is the input to PBO computation. The matrix is also persisted at `reports-v1/iteration_v1-NNN/cpcv_paths.csv`.

---

## Meta-Labeling Architecture

From iter-v1/001 onward, every iteration trains TWO models per symbol:

- **M1 — Primary (direction):** LightGBM classifier. Predicts side ∈ {long, short, no-trade}.
- **M2 — Meta (size/filter):** LightGBM classifier on M1-positive bars only. Target: "did M1's signal close at TP within the vertical timeout?"

### Position Sizing

Position size = `clip(0.5 · (2 · meta_proba − 1) · vol_target_adjustment, 0, 1)` (half-Kelly + vol targeting).

### Training Schedule

- M1 trained per walk-forward month (existing schedule)
- M2 trained per walk-forward month, separate Optuna study, same training window as M1
- Both M1 and M2 serialized per month for reproducibility

### Label Leakage Rule

M2's training labels are M1's binary outcomes. **M2's purge horizon must extend through M1's full label timeout** — otherwise M2 leaks M1's future correctness into M2's training set.

---

## Library Dependency Plan

iter-v1/001 verifies the following pinned dependencies in `pyproject.toml`:

- **`mlfinlab==1.4`** (or `mlfinpy` MIT fallback) — CombinatorialPurgedKFold, meta-labeling utilities, fractional differentiation
- **`pypbo`** — standalone PBO via CSCV
- **`fracdiff>=0.10`** — Numba-accelerated fractional differentiation with `FracdiffStat`
- **`statsmodels`** — ADF stationarity testing

Brief Section 9 declares which versions are used.

---

## Where v1 Lives (Filesystem Map)

```
.claude/
├── commands/
│   ├── quant-iteration-v1.md      (v1 — THIS FILE — refactored 2026-05-23)
│   ├── quant-iteration-v2.md      (v2 unchanged)
│   ├── quant-iteration-v3.md      (v3 unchanged)
│   └── quant-iteration.md         (legacy stub — points to quant-iteration-v1)
└── agents/
    ├── quant-researcher.md        (used for Phases 1-5, 7, 8 of v1/v2/v3)
    ├── quant-engineer.md          (used for Phases 5.5, 6 of v1/v2/v3)
    ├── quant-critic.md            (used for Phases 6.0, 7.5 of v1/v3)
    └── lightgbm-master.md         (used for Phases 4.5, 7.4 of v1)

ITERATION_PLAN_8H_V1.md            (workflow doc at repo root)
BASELINE_V1.md                     (current v1 baseline at repo root — corrected walk-forward stats)

src/crypto_trade/
├── features/                      (v1 legacy — superseded by features_v1)
├── features_v1/                   (v1 — new from refactor; mirrors v2/v3 isolation)
├── features_v2/                   (v2 — never imported by v1 or v3)
├── features_v3/                   (v3 — never imported by v1 or v2)
└── strategies/ml/
    ├── lgbm.py                    (shared backtest engine; track-aware)
    ├── walk_forward.py            (canonical; train_end_ms = test_start_ms - embargo_ms at line 113)
    ├── validation_v1.py           (NEW from refactor — CPCV, PBO, PSR for v1)
    ├── validation_v2.py           (DSR works; CPCV/PBO stubs)
    └── validation_v3.py           (v3 — CPCV, PBO, PSR)

run_baseline_v1.py                 (NEW from refactor — v1 runner with CPCV + V1_EXCLUDED_SYMBOLS audit)
run_baseline_v2.py                 (v2 runner)
run_baseline_v3.py                 (v3 runner)

reports-v1/
└── iteration_v1-NNN/
    ├── in_sample/
    ├── out_of_sample/
    ├── comparison.csv             (DSR + PBO + PSR + n_trials columns)
    ├── pareto_front.csv           (10-seed × 6-metric matrix — CONFIRMATION only)
    ├── cpcv_paths.csv             (45 CPCV paths)
    ├── adf_test.csv               (per-feature ADF p-value)
    ├── ic_matrix.csv              (pairwise feature-family IC)
    ├── dsr.json                   (DSR + PBO + PSR + N_eff)
    └── run.log                    (full stdout/stderr — used by LM Master Phase 7.4)

briefs-v1/
├── exploration_catalog.md         (EXPLORATION ledger — shared across iterations)
└── iteration_v1-NNN/
    ├── research_brief.md          (11 mandatory sections + 0.6 + 2.5)
    ├── lgbm_advisor.md            (Phase 4.5 + Phase 7.4 sections)
    ├── phase5p5_gate.md           (Engineer's PASS or BLOCK)
    ├── critic_preflight.md        (Critic's Phase 6.0 PASS or BLOCK)
    ├── engineering_report.md      (Engineer's Phase 6 output)
    ├── qr_response.md             (only if Critic Round 2 clarifications requested OR BLOCK-PENDING-FIX fix)
    └── review.md                  (Critic's Phase 7.5 output)

diary-v1/
└── iteration_v1-NNN.md            (QR's Phase 8 output)

analysis/
└── iteration_v1-NNN/
    └── *.py                       (committed scripts producing brief Section 2 evidence)
```

**Track isolation enforced via grep at runtime:**
- `grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v1/` must be empty
- `grep -r "from crypto_trade.features_v3" src/crypto_trade/features_v1/` must be empty
- v1 imports ONLY from stdlib, third-party packages, and `crypto_trade.features_v1`

---

## Git Workflow — v1 Refactored

### Starting an iteration

```bash
git checkout quant-research && git pull
git checkout -b iteration-v1/NNN
```

### Commit Discipline

Separate documentation from code. NEVER mix them in the same commit.

1. **Code commits** → prefix `feat(iter-v1/NNN):` or `fix(iter-v1/NNN):`
2. **Phase 4.5 LM Master advisor** → single commit: `docs(iter-v1/NNN): phase 4.5 LM master advisor`
3. **Research brief** → single commit: `docs(iter-v1/NNN): research brief`
4. **Phase 5.5 gate** → single commit: `docs(iter-v1/NNN): phase 5.5 gate PASS` (or BLOCK)
5. **Phase 6.0 pre-flight** → single commit: `docs(iter-v1/NNN): phase 6.0 pre-flight PASS` (or BLOCK)
6. **Engineering report + Phase 7.4 post-mortem + Critic review** → single commit: `docs(iter-v1/NNN): engineering report + LM post-mortem + Critic review`
7. **Diary entry** → LAST commit on branch: `docs(iter-v1/NNN): diary entry`

### Merge Decision — STRICT TRUNK DISCIPLINE

Same as v3's strict-trunk rule. `quant-research` holds only the source of truth for what RUNS today.

What IS allowed on trunk via an iteration merge:
- `src/` source code (feature modules, runners, risk wrappers)
- `tests/` test code that covers code now on trunk
- `BASELINE_V1.md` (when the iteration updates the baseline)
- Other top-level source files like `run_baseline_v1.py`, `pyproject.toml`, `uv.lock`
- `CLAUDE.md`, `.claude/`, `.gitignore` if the iteration touches them

What is NEVER allowed on trunk via an iteration merge:
- `briefs-v1/iteration_v1-NNN/**` (research brief, gates, LM advisor, engineering report, Critic review — stays on the iteration branch)
- `diary-v1/iteration_v1-NNN.md` (Phase 8 diary — stays on the branch)
- `analysis/iteration_v1-NNN/**` (per-iteration EDA/diagnostic scripts and their CSV outputs)
- `reports-v1/iteration_v1-NNN/**` (backtest output artifacts — excluded historically)

`briefs-v1/exploration_catalog.md` IS shared (one-line ledger entry per EXPLORATION) — that file aggregates the dead-paths catalog and is the trunk's index into iteration branches.

**MERGE** (iteration beats baseline AND Critic OVERALL=CONFIRMATION-MERGE):

```bash
git checkout quant-research
git cherry-pick <code-sha-1> <code-sha-2> ... <BASELINE_V1.md-update-sha>
git tag -a v0.v1-NNN -m "Iteration v1-NNN: OOS Sharpe X.XX, PBO Y.YY, PSR Z.ZZ"
```

**NO-MERGE** (iteration fails any gate OR Critic OVERALL=BLOCK-FINAL):

```bash
git tag -a v0.v1-NNN -m "Iteration v1-NNN: NO-MERGE — <one-line reason>"
git push origin iteration-v1/NNN v0.v1-NNN
```

Add the catalog ledger entry via a small `docs(iter-v1/NNN): catalog entry` commit ON `quant-research` directly.

---

## Research Brief — Mandatory v1 Sections

The brief at `briefs-v1/iteration_v1-NNN/research_brief.md` MUST contain all 11 sections. The Phase 5.5 gate maps 1:1 onto these sections; any missing section = BLOCK.

### Section Schema

```markdown
# Iteration v1-NNN — Research Brief

## Section 0 — Data Split Declaration
- OOS_CUTOFF_DATE: 2025-03-24 (unchanged)
- training_months: 24 (unchanged)
- IS window: [start_date, 2025-03-24)
- OOS window: [2025-03-24, end_date)

## Section 0.5 — Iteration Type Declaration
TYPE: EXPLORATION  (or CONFIRMATION)
- Wall-clock budget: <2h for EXP / 6h for CONF>
- (CONF only) EXPLORATION precedents since last CONF: <list iter-v1/NNN ids; must be ≥10>
- Justification: <1-2 sentences>

## Section 0.6 — Architecture-Family Justification (v1-only)
- Axis family: feature-family | model-arch | labeling | universe | risk-primitive
- Prior 5 EXPLORATION families: <list>
- Rotation status: VALID | BLOCKED
- One-sentence rationale: <why this family + axis is the right next step>

## Section 1 — Hypothesis
<one sentence: what changes and why we expect OOS improvement>

## Section 2 — IS-Only Numerical Evidence
<tables produced by analysis/iteration_v1-NNN/*.py — committed before brief>
- Path to script: analysis/iteration_v1-NNN/<name>.py
- Path to output: analysis/iteration_v1-NNN/<name>_output.csv
<numerical tables inline>

### Section 2.5 — HIGH-RISK Axis Declaration (v1-only)
- Declaration: HIGH-RISK | NORMAL-RISK
- Reason: <one sentence>
- Mitigation (HIGH-RISK only): <pre-commit to running this axis at CONFIRMATION budget (ENSEMBLE_SIZE=10) at iter-v1/NNN+1 if PROMISING; NO multi-seed at THIS iteration>

## Section 3 — Proposed Changes
- Symbols: <added / removed / kept; rationale; V1_EXCLUDED_SYMBOLS check>
- Labeling: <triple-barrier params, σ_t source, timeout>
- Features: <added / removed; cluster-importance check ran>
- Risk gates: <new gate? threshold? fire rate prediction>
- LM Master responses:
  - <recommendation 1>: adopted | modified | rejected (reason)
  - <recommendation 2>: ...
  - <recommendation 3>: ...

## Section 4 — Expected OOS Impact
- Predicted Sharpe delta: +X.X (CI: [Y.Y, Z.Z])
- Falsifier: "if OOS Sharpe falls below W, hypothesis is rejected"

## Section 5 — Risk Mitigation
<R1/R2/R3 / 7-gate / new-gate changes; IS-calibrated thresholds; simulated effect on prior iterations>

## Section 6 — Risk Management Design
<8-primitive table or v1 equivalent; fire-rate predictions; regime coverage analysis>

## Section 7 — Pre-Registered Failure-Mode Prediction
<1-2 paragraphs predicting how this iteration most plausibly fails OOS, what the gates should catch, what the failure looks like in metrics>

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria
<locked numerical thresholds before backtest. Example: "MERGE iff OOS_monthly_Sharpe ≥ +1.8 AND PBO < 0.4 AND PSR > 0.95 AND no symbol > 35% of OOS wpnl">

## Section 9 — Library Stack Declaration
- mlfinlab: 1.4 (or mlfinpy <version> if fallback)
- pypbo: <version>
- fracdiff: <version>
- statsmodels: <version> (for ADF)
<note any fallback rationale>
```

---

## Phase 8 Diary Template — v1

QR's `diary-v1/iteration_v1-NNN.md`:

```markdown
# Iteration v1-NNN — Diary

## Decision: MERGE or NO-MERGE
<single line, no hedging>
<if NO-MERGE due to Critic BLOCK-FINAL: name the failed Check>
<if NO-MERGE due to Critic BLOCK-PENDING-FIX then BLOCK-FINAL: name both verdicts and what was attempted>

## What Worked
<numerical results; OOS metrics; per-symbol attribution; comparison vs baseline>

## What Failed
<honest accounting; if NO-MERGE, why specifically>

## LM Master Advisory Tracking
- Phase 4.5 confidence: HIGH / MEDIUM / LOW (from lgbm_advisor.md Phase 4.5 closing note)
- Phase 4.5 recommendations: <list> — adopted / modified / rejected
- Phase 7.4 post-mortem highlights: <2-3 bullets>

## Critic Review Summary
- Check 1 (Look-Ahead): PASS
- Check 2 (Embargo): PASS
- Check 3 (DSR/PBO/PSR): PASS / FAIL
- Check 4 (IC): PASS / FAIL
- Check 5 (ADF): PASS / FAIL
- Check 6 (Pareto): PASS / WARN
- Check 7 (Reproducibility): PASS / FAIL
- Check 8 (Hypothesis-Implementation Alignment): PASS / FAIL
- Check 14 (Axis Family Validation): PASS / FAIL (v1-only)
- OVERALL: CONFIRMATION-MERGE | EXPLORATION-PROMISING | EXPLORATION-NEGATIVE | BLOCK-PENDING-FIX → final | BLOCK-FINAL

## Path Forward (from Critic, if any BLOCK)
<copy Critic's Path Forward verbatim — these become candidates for next iter's brief>

## Pareto Position (chosen seed, CONFIRMATION only)
<table from pareto_front.csv: chosen seed metrics + dominator (if any)>

## ADF Stationarity Report
<summary from adf_test.csv: count of features with p<0.05 vs p≥0.05>

## Pre-Registered Failure-Mode vs Reality
<from brief Section 7: "predicted failure was X via Y mechanism">
<actual: "iteration failed via PBO threshold, mechanism was Z">
<match? yes/partial/no — explain>

## Axis Rotation Status (v1-only)
- This iter's family: <family>
- Prior 5 families: <list>
- Rotation honored: YES / NO
- Cumulative same-family count: <integer> (resets to 0 on family switch)

## Lessons
<generalizable takeaways; new entries for the dead-paths catalog if applicable>

## Next Iteration Ideas
<3–5 specific, testable hypotheses for the next QR; ranked by expected impact>
<include Critic's Path Forward suggestions as candidates>
```

The "LM Master Advisory Tracking" section is the v1 diary's accountability mechanism — does LM Master's Phase 4.5 prediction match Phase 7.4 / Phase 7.5 outcome? Builds LM Master's track record honestly.

---

## Subagent Invocation Protocol

The orchestrating session uses Claude Code's `Agent` tool to delegate phase work.

### QR Phases (1–5, 7, 8)

```
Agent({
  description: "Run Phase X for iter-v1/NNN",
  subagent_type: "quant-researcher",
  prompt: "[mode: project] [track: v1] Run Phase X for iter-v1/NNN. Brief at briefs-v1/iteration_v1-NNN/research_brief.md (when applicable). Working directory: /home/roberto/crypto-trade/.worktrees/quant-research. Reference BASELINE_V1.md for current baseline."
})
```

### LightGBM Master Phase 4.5

```
Agent({
  description: "Phase 4.5 LM Master pre-design for iter-v1/NNN",
  subagent_type: "lightgbm-master",
  prompt: "[Phase 4.5] [track: v1] Run pre-design advisory for iter-v1/NNN. Working directory: /home/roberto/crypto-trade/.worktrees/quant-research. Read: BASELINE_V1.md, last 3 v1 diaries, prior iter-v1/NNN-1 lgbm_advisor.md and engineering_report.md and feature_importance.csv, runner code, lgbm.py + optimization.py. QR's tentative axis: <one-line summary>. Emit lgbm_advisor.md content as final message text per Phase 4.5 template — orchestrator persists at briefs-v1/iteration_v1-NNN/lgbm_advisor.md."
})
```

### Engineer Phase 5.5 Gate

```
Agent({
  description: "Verify Phase 5.5 gate for iter-v1/NNN",
  subagent_type: "quant-engineer",
  prompt: "[track: v1] Run the Phase 5.5 brief-completeness gate for iter-v1/NNN. Read briefs-v1/iteration_v1-NNN/research_brief.md AND briefs-v1/iteration_v1-NNN/lgbm_advisor.md (verify LM Master responses in brief Section 3). Verify all 11 mandatory sections (incl. 0.6, 2.5). Verify cadence + axis rotation. Verify exploration_catalog.md count for CONFIRMATION. Write phase5p5_gate.md with OVERALL=PASS or BLOCK + per-section status."
})
```

### Critic Phase 6.0 Pre-Flight

```
Agent({
  description: "Phase 6.0 Critic pre-flight for iter-v1/NNN",
  subagent_type: "quant-critic",
  prompt: "[Phase 6.0 PRE-FLIGHT] [track: v1] Run pre-flight review for iter-v1/NNN. Read briefs-v1/iteration_v1-NNN/research_brief.md AND briefs-v1/iteration_v1-NNN/phase5p5_gate.md (confirm OVERALL=PASS). Read QE's src/ diff: `git diff <parent-baseline>..iteration-v1/NNN -- src/`. Run mini-checks 1, 13, foundation regression, cadence, falsifier. Emit critic_preflight.md content as final message text with OVERALL=PASS or BLOCK + Path Forward (if BLOCK). DO NOT run the full Phase 7.5 8-check pass."
})
```

### Engineer Phase 6 — SPLIT DISPATCH (long backtests > 30 min)

Same as v3 (Engineer setup → orchestrator launches detached bash → Engineer report-only). Save agent quota.

### LightGBM Master Phase 7.4

```
Agent({
  description: "Phase 7.4 LM Master post-mortem for iter-v1/NNN",
  subagent_type: "lightgbm-master",
  prompt: "[Phase 7.4 POST-MORTEM] [track: v1] Run post-mortem interpretation for iter-v1/NNN. Working directory: /home/roberto/crypto-trade/.worktrees/quant-research. Read briefs-v1/iteration_v1-NNN/research_brief.md, briefs-v1/iteration_v1-NNN/engineering_report.md, briefs-v1/iteration_v1-NNN/lgbm_advisor.md (Phase 4.5 section), reports-v1/iteration_v1-NNN/{comparison.csv, in_sample/feature_importance.csv, out_of_sample/feature_importance.csv, pareto_front.csv, cpcv_paths.csv, ic_matrix.csv, run.log}. Emit Phase 7.4 section of lgbm_advisor.md as final message text per LM Master template — orchestrator appends to briefs-v1/iteration_v1-NNN/lgbm_advisor.md."
})
```

### Critic Phase 7.5

```
Agent({
  description: "Phase 7.5 Critic review for iter-v1/NNN",
  subagent_type: "quant-critic",
  prompt: "[Phase 7.5] [track: v1] Run Phase 7.5 adversarial review for iter-v1/NNN. Branch: iteration-v1/NNN. Report dir: reports-v1/iteration_v1-NNN. Brief dir: briefs-v1/iteration_v1-NNN. Read lgbm_advisor.md (both Phase 4.5 and Phase 7.4 sections) as supplemental input. Run all 8 mandatory checks + Check 14 (Axis Family Validation, v1-only) + optional 9-12. Emit review.md content as final message text with OVERALL ∈ {EXPLORATION-PROMISING, EXPLORATION-NEGATIVE, CONFIRMATION-MERGE, BLOCK-PENDING-FIX, BLOCK-FINAL}. **PATH FORWARD section MANDATORY on every BLOCK verdict.**"
})
```

### Hand-off Sanity Checks

- LM Master's Phase 4.5 final message starts with `# LightGBM Master Advisor — iter-v1/NNN — Phase 4.5 (Pre-Design)` — orchestrator persists as `lgbm_advisor.md`.
- Engineer's `OVERALL=PASS` in phase5p5_gate.md is the handshake to Phase 6.0.
- Critic's `OVERALL=PASS` in critic_preflight.md is the handshake to Phase 6.
- Engineer's `OVERALL=READY-FOR-CRITIC` in engineering_report.md is the handshake to Phase 7.4.
- LM Master's Phase 7.4 message starts with `# LightGBM Master Advisor — iter-v1/NNN — Phase 7.4 (Post-Mortem)` — orchestrator appends to `lgbm_advisor.md`.
- Critic's final message starts with `# Phase 7.5 Critic Review — iter-v1/NNN` and contains `OVERALL: <verdict>` — orchestrator parses.
- BLOCK-PENDING-FIX → orchestrator routes back through one QE re-fix + Critic single-pass re-review BEFORE Phase 7/8.

---

## Quick-Start Command (for the human user)

`/quant-iteration-v1` triggers the autopilot loop:

1. Read `BASELINE_V1.md` + last 3 v1 diaries + exploration_catalog.md
2. Determine next iteration number (next `iter-v1/NNN`)
3. `git checkout quant-research && git checkout -b iteration-v1/NNN`
4. QR Phases 1–4 → tentative axis identified
5. **LM Master Phase 4.5 → `lgbm_advisor.md`** (pre-design)
6. QR Phase 5 → research brief at `briefs-v1/iteration_v1-NNN/research_brief.md` (integrates LM Master responses)
7. Engineer Phase 5.5 gate → `phase5p5_gate.md` (PASS or BLOCK)
8. If BLOCK → return to QR; loop on QR Phase 5
9. If PASS → QE Phase 6 setup-only commit
10. **Critic Phase 6.0 pre-flight → `critic_preflight.md`** (PASS or BLOCK)
11. If BLOCK → return to QR for brief revision; loop on QR Phase 5
12. If PASS → QE Phase 6 backtest → engineering report + reports
13. **LM Master Phase 7.4 → `lgbm_advisor.md` (post-mortem appended)**
14. Critic Phase 7.5 → `review.md` (OVERALL=EXPLORATION-PROMISING / NEGATIVE / CONFIRMATION-MERGE / BLOCK-PENDING-FIX / BLOCK-FINAL)
15. If BLOCK-PENDING-FIX → QR/QE fixes specific defect → re-run Phase 6 → Critic single-pass re-review (Round 4) → final verdict (PASS or BLOCK-FINAL)
16. QR Phase 7 → OOS evaluation memo
17. QR Phase 8 → diary + merge decision
18. Commit/tag per git workflow
19. Loop back to step 1 with the new diary's "Next Iteration Ideas"

---

## Migration Notes (Legacy v1 → Refactored v1)

The historical 186 iterations on `iteration_NNN/` are archived (kept on `main`, never deleted). The **corrected v1 baseline** under the fixed walk-forward IS the iter-v1/001 anchor. Future iterations beat the corrected baseline — never the inflated historical v0.186.

`BASELINE_V1.md` populated by one-time re-run of `iteration_186`'s config under fixed `walk_forward.py:113`. This is a PREREQUISITE to iter-v1/001, NOT iter-v1/001's deliverable.

The legacy `/quant-iteration` skill is **deprecated** — `.claude/commands/quant-iteration.md` becomes a stub pointing to `quant-iteration-v1`. Existing references in MEMORY.md and elsewhere should be updated to `quant-iteration-v1` over time.

---

## Key Reminders — v1 (Refactored)

- The Critic is read-only by structural design. Tools: `Read, Glob, Grep` ONLY.
- The LightGBM Master is read-only by structural design. Tools: `Read, Glob, Grep, Bash` (Bash for inspection, NEVER edits).
- Phase 5.5 gate is the first structural defense. Engineer refuses to start Phase 6.0 without complete brief.
- Phase 6.0 Critic pre-flight is the second structural defense — catches issues BEFORE compute is spent.
- BLOCK-PENDING-FIX grants exactly ONE rerun. After it, verdict is final (PASS or BLOCK-FINAL).
- Path Forward section is MANDATORY on every Critic BLOCK verdict.
- PBO ≥ 0.4 is automatic NO-MERGE. Same for DSR < 0.95 and PSR < 0.95.
- v1 universe must exclude all v2+v3 symbols (V1_EXCLUDED_SYMBOLS enforced at runtime).
- Track isolation: v1 NEVER imports from `crypto_trade.features_v2` (v2) or `crypto_trade.features_v3` (v3).
- Axis Rotation Discipline: every 5 same-family EXPLORATIONs triggers mandatory family rotation.
- HIGH-RISK declaration is mandatory in every brief Section 2.5. Mitigation is pre-commit to CONFIRMATION at next iter — NOT a seed-count bump. EXPLORATION ALWAYS uses 3 inner seeds, even HIGH-RISK ([[v1-seed-count-non-negotiable]]).
- "QR uses IS data" — Phase 5 brief must contain numerical tables from a committed `analysis/iteration_v1-NNN/*.py` script.
- Pre-registered failure-mode prediction (Section 7) and MERGE/NO-MERGE criteria (Section 8) are MANDATORY in every v1 brief.
- BLOCK-FINAL from the Critic is FINAL. Re-running after a fix is selection bias (BLOCK-PENDING-FIX is the only sanctioned single-rerun mechanism).
- Sacred constants are sacred. `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` never change.
- `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms`. The iter-v3/058 fix is law — anything else is the iter-v3/057-style bug.
- LM Master is the missing "creator" role from v3 cycle-7's diagnosis. QR + LM Master + QE + Critic = the four-role v1 workflow.

The v1 refactor turns informal best-practices into structural gates AND adds a creator role to prevent the QR↔Critic loop from running out of ideas. The structure makes it harder to fool yourself, and harder to fool yourself is the entire game.
