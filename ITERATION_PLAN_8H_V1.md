# Iteration Plan — 8h Track v1 (Refactored)

**Sibling to:** `ITERATION_PLAN_8H_V2.md` (v2) and `ITERATION_PLAN_8H_V3.md` (v3). All three coexist.

**Refactored:** 2026-05-23. The original `ITERATION_PLAN_8H.md` is kept for backward-compatible reference to the 186 historical iterations; this file is the canonical anchor for new v1 iterations.

## Mission

v1 was the founding crypto-trade strategy track. After 186 iterations on `iteration_NNN/`, it was deployed to live trading on BTC/ETH/LINK/LTC/DOT. Then we discovered a serious walk-forward look-ahead bug: `train_end_ms = test_start_ms` with no embargo, allowing training labels to scan forward into the test window. Fixed at `walk_forward.py:113` (`train_end_ms = test_start_ms - embargo_ms`). Re-running v0.186 under the corrected walk-forward produces materially worse OOS numbers — the old v1 baseline was inflated.

The v1 refactor restarts with the **corrected stats as the formal baseline** and brings v1 up to v3's rigor (CPCV, DSR, PBO, PSR, ADF, IC, meta-labeling, fractional Kelly) AND adds four structural improvements the v3 cycle-7 forensic identified:

- **LightGBM Master agent** — a read-only ML specialist that fires Phase 4.5 (pre-design hyperparameter/feature recommendations) and Phase 7.4 (post-backtest interpretation). Closes the v3 cycle-7 gap where QR + Critic were both evaluators with no "creator" role.
- **Constructive Critic** — every BLOCK verdict includes a "Path Forward" section proposing 2-3 alternative axes from families NOT used in the prior 5 EXPLORATIONs.
- **Critic pre-Phase 6 review (Phase 6.0)** — short pre-flight after Phase 5.5 PASS, before backtest launches. Catches issues BEFORE compute is spent.
- **BLOCK-PENDING-FIX softening** — Phase 7.5 verdict can grant ONE rerun chance for isolated defects; final verdict must then be PASS or BLOCK-FINAL.

Plus a **QR creativity mandate** (Axis Rotation Discipline): if the last 5 EXPLORATIONs were from the same axis family, the next MUST rotate.

v1 is the **rigor + creator-role-augmented track**, parallel to v2 (diversification arm) and v3 (rigor-only arm).

## Workflow

See `.claude/commands/quant-iteration-v1.md` (the v1 skill).

**Thirteen phases** (8 original + 4.5 + 5.5 + 6.0 + 7.4 + 7.5):

1. Data analysis & EDA (QR)
2. Labeling decisions (QR)
3. Symbol selection (QR; V1_EXCLUDED_SYMBOLS enforced)
4. Feature design (QR)
4.5. **LightGBM Master pre-design advisory** (LM Master; new; advisory only)
5. Research brief authoring (QR; 11 mandatory sections incl. Section 0.6 + Section 2.5)
5.5. **Phase 5.5 Gate** (QE; refuses incomplete briefs)
6.0. **Phase 6.0 Critic pre-flight** (Critic; mini-checks on brief + src/ diff; new)
6. Implementation + backtest (QE; CPCV from iter-v1/001)
7.4. **LightGBM Master post-mortem** (LM Master; new; feature importance + Optuna trial interpretation)
7.5. **Phase 7.5 Critic Review** (Critic; 8+1 mandatory checks; OVERALL ∈ {EXPLORATION-PROMISING, EXPLORATION-NEGATIVE, CONFIRMATION-MERGE, BLOCK-PENDING-FIX, BLOCK-FINAL})
7. OOS evaluation (QR)
8. Diary + merge decision (QR)

Four gates are MANDATORY: Phase 4.5, 5.5, 6.0, 7.5. Skipping any is a process-integrity violation.

## Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    # IMMUTABLE — never changes across all three tracks
training_months = 24             # IMMUTABLE — never changes
```

Defined in `src/crypto_trade/config.py`. The walk-forward / CPCV backtest runs on ALL data; the reporting layer splits results at `OOS_CUTOFF_DATE` into `in_sample/` and `out_of_sample/` directories plus `comparison.csv`.

The QR sees OOS results for the FIRST time in Phase 7. Hard floor on `OOS_Sharpe / IS_Sharpe ≥ 0.5`.

## Git & Code Management

- **Branch:** `quant-research` worktree, feature branches `iteration-v1/NNN`
- **Tag:** `v0.v1-NNN` after MERGE
- **Reports:** `reports-v1/iteration_v1-NNN/`
- **Briefs:** `briefs-v1/iteration_v1-NNN/` (research_brief.md, lgbm_advisor.md, phase5p5_gate.md, critic_preflight.md, engineering_report.md, review.md, qr_response.md if applicable)
- **Diaries:** `diary-v1/iteration_v1-NNN.md`
- **Analysis scripts:** `analysis/iteration_v1-NNN/*.py` (committed; produce brief Section 2 evidence)
- **Source code:** new `src/crypto_trade/features_v1/` package (introduced at the refactor); new `src/crypto_trade/strategies/ml/validation_v1.py` for CPCV/PBO/PSR; new `run_baseline_v1.py` runner

**Track isolation enforced at runtime:**
- `grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v1/` must be empty
- `grep -r "from crypto_trade.features_v3" src/crypto_trade/features_v1/` must be empty

## Baseline Rules

See `BASELINE_V1.md`. The v1 baseline is the corrected walk-forward stats from re-running v0.186 under fixed `walk_forward.py:113` (NOT the inflated historical v0.186 headline). CONFIRMATION-MERGE decisions update `BASELINE_V1.md` in a separate commit (`baseline-v1: update after iteration v1-NNN`).

Hard merge gates (inherited project-level):
- IS Sharpe > 1.0 AND OOS Sharpe > 1.0
- OOS / IS Sharpe ratio ≥ 0.5
- ≥10 trades/month OOS, ≥130 OOS total trades
- Top symbol concentration ≤ 30% of OOS PnL (or explicit exception with justification)
- 10-seed pre-MERGE validation: mean Sharpe > 0, ≥7/10 profitable

v1 rigor gates (mirror v3; any single failure = NO-MERGE):
- DSR > 0.95
- PBO < 0.4
- PSR > 0.95
- IC between any new family and existing < 0.7 (Critic Check 4)
- ADF p < 0.05 on every feature (or explicit "regime indicator" justification in brief Section 4)
- Pareto-non-dominated chosen seed on the 6-metric vector (Critic Check 6, CONFIRMATION only)

v1-only structural gates:
- Phase 5.5 gate PASS (Engineer)
- Phase 6.0 pre-flight PASS (Critic)
- Phase 7.5 review verdict ∈ {EXPLORATION-PROMISING, CONFIRMATION-MERGE} (not BLOCK-FINAL)
- Axis Rotation Discipline honored (Section 0.6; Phase 5.5 enforces; Critic Check 14 verifies)
- LM Master advisory artifact exists (`lgbm_advisor.md` at Phase 4.5 + Phase 7.4)

## Feature Column Pinning

MANDATORY for every v1 iteration. The runner must pass `feature_columns=list(V1_FEATURE_COLUMNS)` to `LightGbmStrategy`. Never `None`, never empty, never auto-discovered. LightGBM's `colsample_bytree` samples by position; column order silently produces different models.

The `V1_FEATURE_COLUMNS` constant lives in `src/crypto_trade/features_v1/__init__.py` (introduced at the refactor — starts as the 193-column historical v1 list, future iterations may mutate).

## Symbol Universe

```python
V1_EXCLUDED_SYMBOLS = (
    # v2 traded (live, separate track)
    "SOLUSDT", "XRPUSDT", "DOGEUSDT", "NEARUSDT",
    # v3 traded (live, separate track)
    "BCHUSDT", "LDOUSDT", "TRXUSDT",
    # historical reservation
    "BNBUSDT",
)

V1_BASELINE_UNIVERSE = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT")
```

The runner enforces at startup:

```python
assert set(cfg.symbols).isdisjoint(V1_EXCLUDED_SYMBOLS), \
    f"v1 cannot trade v2/v3 symbols: {set(cfg.symbols) & set(V1_EXCLUDED_SYMBOLS)}"
```

iter-v1/001+ can EXPLORE adding/swapping any symbol NOT in `V1_EXCLUDED_SYMBOLS` (so BTC, ETH, LINK, LTC, DOT, plus AVAX, ADA, ATOM, MATIC, MKR, ICP, FIL, etc.). CONFIRMATION-MERGE updates `V1_BASELINE_UNIVERSE` if the bundle changes universe.

## Candle Integrity & Freshness

Inherited from v3:
- `fetcher.py` drops forming candles: `if k.close_time < now_ms`
- Every kline CSV in `data/<SYMBOL>/8h.csv` must have `close_time` within 16h of measurement time
- Engineer's pre-flight check (Phase 6) verifies both before running backtest

Stale data + forming candles silently corrupt features and labels.

## Iteration Cadence Discipline

**Hard rules** (inherited from v3):

1. **EXPLORATION wall-clock HARD CAP: 2h.** Engineer kills the backtest if exceeded. Default config: `--exploration --n-trials 35`. Single-axis variation.
2. **CONFIRMATION wall-clock HARD CAP: 6h.** `--n-trials 35`, `ENSEMBLE_SIZE=10`.
3. **CONFIRMATION requires 10 EXPLORATION precedents.** Brief Section 0.5 lists ≥10 EXPLORATION iter-v1/NNN ids; Phase 5.5 gate verifies count from `briefs-v1/exploration_catalog.md`.
4. **CONFIRMATION = bundle of best EXPLORATIONS** — not a fresh hypothesis.
5. **Only CONFIRMATION-MERGE updates BASELINE_V1.md.** EXPLORATION never updates baseline.

The 10:1 ratio is the only cadence constraint. No daily/weekly limit.

**v1-specific cadence additions**:

6. **Axis Rotation Discipline**: if the last 5 EXPLORATIONs are all same-family, the next EXPLORATION MUST rotate. Enforced in Phase 5.5 gate (Section 0.6) and Phase 7.5 Critic Check 14.

## QR Axis Rotation Discipline (NEW vs v3)

Five axis families:
- **feature-family** — adding/removing/modifying feature families
- **model-arch** — model architecture or family
- **labeling** — labeling method or params
- **universe** — symbol universe
- **risk-primitive** — risk gates, R1/R2/R3/RiskVN wrappers

If the last 5 EXPLORATIONs were all from the same family, the NEXT EXPLORATION MUST be from a different family. Codifies the v3 cycle-7 lesson — knob-tuning inertia within /121's same family produced 9/9 NEGATIVE.

Brief Section 0.6 declares the axis family + prior 5 families + rotation status (VALID or BLOCKED).

## HIGH-RISK Axis Declaration (NEW vs v3)

Brief Section 2.5 declares whether the proposed axis changes Optuna's training-objective domain (HIGH-RISK) or not (NORMAL-RISK). HIGH-RISK declaration is mandatory; multi-seed validation is opt-in (lighter footing than v3).

If 3+ HIGH-RISK single-seed EXPLORATIONs produce >1σ negative deltas, the next HIGH-RISK iteration becomes mandatorily multi-seed (codified at that point via a feedback rule update).

## Phase 4.5 — LightGBM Master Pre-Design Advisory

See `.claude/commands/quant-iteration-v1.md` §"Phase 4.5 — LightGBM Master Pre-Design Advisory (NEW)" for the complete specification. Summary: LM Master agent reads BASELINE_V1.md + last 3 diaries + prior iteration reports + QR's Phase 4 outputs; emits `lgbm_advisor.md` with 2-4 hyperparameter recommendations, 1-2 feature-engineering ideas, saturation risks, and confidence assessment. ADVISORY ONLY — QR can adopt, modify, or reject.

## Phase 5.5 Gate

See `.claude/commands/quant-iteration-v1.md` §"Phase 5.5 — Pre-Phase 6 Gate (MANDATORY)" for the complete specification. Summary: Engineer verifies 11 mandatory brief sections (incl. v1-only Section 0.6 + Section 2.5), cadence rules, axis rotation, LM Master response integration. OVERALL=BLOCK terminates Phase 6.0 immediately. The Engineer NEVER attempts to fix the brief.

## Phase 6.0 Critic Pre-Flight

See `.claude/commands/quant-iteration-v1.md` §"Phase 6.0 — Critic Pre-Flight Review (NEW vs v3)" for the complete specification. Summary: after Phase 5.5 PASS but before backtest launches, Critic does a SHORT pre-flight: mini-Check 1 (brief look-ahead), mini-Check 13 (anti-pattern static scan on QE's src/ diff), foundation regression check (re-verify `walk_forward.py:113`), cadence + axis sanity, falsifier presence. OVERALL=PASS allows backtest launch. OVERALL=BLOCK returns to QR for brief revision; one revision + Phase 6.0 rerun allowed.

## Phase 7.4 — LightGBM Master Post-Mortem

See `.claude/commands/quant-iteration-v1.md` §"Phase 7.4 — LightGBM Master Post-Mortem (NEW)" for the complete specification. Summary: LM Master reads engineering_report.md + comparison.csv + feature_importance.csv (IS + OOS) + Optuna trial logs; emits Phase 7.4 section of `lgbm_advisor.md` covering feature importance triage, hyperparameter trial stability, gain concentration audit, suspicious patterns, next-iteration tuning recommendations, and accountability against Phase 4.5 predictions.

## Phase 7.5 Critic Review

See `.claude/commands/quant-iteration-v1.md` §"Phase 7.5 — Critic Adversarial Review (UPDATED vs v3)" and `.claude/agents/quant-critic.md` for the complete specification. Summary: Critic runs 8 mandatory checks (Look-Ahead, Embargo, DSR/PBO/PSR, IC, ADF, Pareto, Reproducibility, Hypothesis-Implementation Alignment) PLUS v1-only Check 14 (Axis Family Validation) PLUS optional 9-12. Emits `review.md`.

v1 verdict set: `EXPLORATION-PROMISING / EXPLORATION-NEGATIVE / CONFIRMATION-MERGE / BLOCK-PENDING-FIX / BLOCK-FINAL`.

BLOCK-PENDING-FIX grants ONE rerun chance for an isolated specific defect. After re-evaluation, verdict can only be PASS or BLOCK-FINAL.

BLOCK-FINAL is irrevocable.

**Path Forward section is MANDATORY on every BLOCK verdict** — Critic proposes 2-3 alternative axes from families the QR has NOT used in the prior 5 EXPLORATIONs.

## Relationship to v2 and v3

| | v1 (THIS) | v2 | v3 |
|---|---|---|---|
| Track focus | **Refactored: rigor + creator role + edge discovery** | Diversification | Methodological rigor |
| Branch | `quant-research` (`iteration-v1/`) | `quant-research` (`iteration-v2/`) | `quant-research` (`iteration-v3/`) |
| Symbols (initial) | BTC, ETH, LINK, LTC, DOT (+ extended pool) | SOL, XRP, DOGE, NEAR | BCH, LDO, TRX |
| Validation | **CPCV + DSR + PBO + PSR + ADF + IC** | Walk-forward + DSR | CPCV + DSR + PBO + PSR + ADF + IC |
| Roles | **QR + QE + Critic + LightGBM Master** (4) | QR + QE (2) | QR + QE + Critic (3) |
| Phases | **13** (1-8 + 4.5 + 5.5 + 6.0 + 7.4 + 7.5) | 8 | 10 (1-8 + 5.5 + 7.5) |
| BLOCK semantics | **PENDING-FIX | FINAL** | N/A | FINAL only |
| Axis Rotation | **Mandatory every 5 EXPs** | None | None |
| Status | Active (refactored 2026-05-23) | Active sibling | Active sibling |

All three tracks share: `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24`, 8h candles, 10-seed pre-MERGE concentration check, fixed walk-forward embargo at `walk_forward.py:113`.

## NO CHEATING — Inherited and Extended

- NEVER change `start_time` to skip bad IS months
- NEVER cherry-pick date ranges
- NEVER post-hoc filter trades
- NEVER tune parameters on OOS data
- NEVER allow labels to leak across CV fold boundaries (`gap = (timeout_candles + 1) × n_symbols`)
- NEVER allow labels to leak from live/prediction data to training data

v1-refactored adds:

- NEVER skip the Phase 4.5 LM Master advisory
- NEVER skip the Phase 5.5 gate
- NEVER skip the Phase 6.0 pre-flight
- NEVER merge without Critic OVERALL ∈ {EXPLORATION-PROMISING (catalog only), CONFIRMATION-MERGE}
- NEVER recurse beyond ONE BLOCK-PENDING-FIX rerun
- NEVER include a v2 or v3 symbol in v1's universe
- NEVER import from `crypto_trade.features_v2` (v2) or `crypto_trade.features_v3` (v3) in v1 code
- NEVER bypass Axis Rotation Discipline at brief Section 0.6
- NEVER regress `walk_forward.py:113` (`train_end_ms = test_start_ms - embargo_ms`)

## Library Stack (iter-v1/001+)

- `mlfinlab==1.4` (primary) or `mlfinpy` (MIT fallback) — CPCV, meta-labeling utilities
- `pypbo` — Probability of Backtest Overfitting
- `fracdiff>=0.10` — Numba-accelerated fractional differentiation with `FracdiffStat` for auto-selected `d*`
- `statsmodels` (already installed) — `adfuller` for ADF stationarity testing

Brief Section 9 declares versions used and any fallbacks.

## Outstanding Tasks (Pre-iter-v1/001)

Before iter-v1/001 can launch:

1. `src/crypto_trade/run_baseline_v1.py` — v1 runner (fork of `run_baseline_v3.py`)
2. `src/crypto_trade/features_v1/__init__.py` — `V1_EXCLUDED_SYMBOLS`, `V1_FEATURE_COLUMNS`, `V1_BASELINE_UNIVERSE`
3. `src/crypto_trade/strategies/ml/validation_v1.py` — CPCV, PBO, PSR, ADF, IC for v1
4. Re-run v0.186 under v1 stack to populate TBD CPCV-derived fields in `BASELINE_V1.md` (PBO, PSR); tag as `v0.v1-baseline-corrected`
5. `briefs-v1/exploration_catalog.md` — empty initial ledger

These are listed in BASELINE_V1.md's "Outstanding Tasks Before First v1 Iteration" section.

## See Also

- `.claude/commands/quant-iteration-v1.md` — the v1 skill (workflow definition)
- `.claude/agents/quant-researcher.md` — Researcher agent (Phases 1-5, 7, 8 — shared across all tracks)
- `.claude/agents/quant-engineer.md` — Engineer agent (Phases 5.5, 6 — shared across all tracks)
- `.claude/agents/quant-critic.md` — Critic agent (Phases 6.0 + 7.5 of v1/v3)
- `.claude/agents/lightgbm-master.md` — LightGBM Master agent (Phases 4.5, 7.4 of v1)
- `BASELINE_V1.md` — current v1 baseline (refactored anchor)
- `BASELINE.md` — legacy v1 baseline (kept for reference; superseded by BASELINE_V1.md)
- `BASELINE_V2.md` — sibling baseline (v2)
- `BASELINE_V3.md` — sibling baseline (v3)
- `ITERATION_PLAN_8H.md` — legacy v1 iteration plan (historical 186 iterations; kept for reference)
- `ITERATION_PLAN_8H_V2.md` — sibling iteration plan (v2)
- `ITERATION_PLAN_8H_V3.md` — sibling iteration plan (v3)
