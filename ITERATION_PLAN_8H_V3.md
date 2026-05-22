# Iteration Plan — 8h Track v3 (Rigor Arm)

**Sibling to:** `ITERATION_PLAN_8H.md` (v1) and `ITERATION_PLAN_8H_V2.md` (v2). All three coexist.

## Mission

v3 is the rigor arm. Where v1 chases edge and v2 chases diversification, v3 chases methodological soundness. Every gap that v2's 69 iterations exposed gets a structural defense in v3:

- Single-path walk-forward → **CPCV with 45 paths** (mandatory from iter-v3/001)
- Naive Sharpe → **DSR + PBO + PSR with hard pass thresholds** (DSR > 0.95, PBO < 0.4, PSR > 0.95)
- Two-role workflow → **three roles with adversarial Critic review** (Phase 7.5)
- Phase 5 brief can be rubber-stamped → **Phase 5.5 gate** (Engineer refuses incomplete briefs)
- Direction-only model → **meta-labeling architecture** (M1 + M2)
- Custom fixed-d fracdiff → **fracdiff package with auto-selected d via ADF**
- Implicit feature redundancy → **IC < 0.7 enforced between feature families** (Critic Check 4)
- Headline-metric tunnel vision → **Pareto-front model selection** (Critic Check 6)

v3 picks a fresh symbol universe in iter-v3/001's brief. The universe must exclude every symbol traded by v1 or v2 — see `V3_EXCLUDED_SYMBOLS` in `BASELINE_V3.md`. This forces genuine diversification across all three tracks.

If v3 rediscovers v1's or v2's symbols, features, or risk regimes, it has failed at its only job.

## Workflow

See `.claude/commands/quant-iteration-v3.md` (the v3 skill).

**Ten phases** (8 original + Phase 5.5 gate + Phase 7.5 Critic):

1. Data analysis & EDA (QR)
2. Labeling decisions (QR)
3. Symbol selection (QR; iter-v3/001 selects fresh universe)
4. Feature design (QR)
5. Research brief authoring (QR; 10 mandatory sections)
5.5. **Phase 5.5 Gate** (QE; refuses incomplete briefs)
6. Implementation + backtest (QE; CPCV from iter-v3/001)
7.5. **Phase 7.5 Critic Review** (Critic; 8 mandatory checks; OVERALL=MERGE or BLOCK)
7. OOS evaluation (QR)
8. Diary + merge decision (QR)

The two new gates (5.5 and 7.5) are MANDATORY. Skipping either is a process-integrity violation.

## Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    # IMMUTABLE — never changes across all three tracks
training_months = 24             # IMMUTABLE — never changes
```

Defined in `src/crypto_trade/config.py`. The walk-forward / CPCV backtest runs on ALL data; the reporting layer splits results at `OOS_CUTOFF_DATE` into `in_sample/` and `out_of_sample/` directories plus `comparison.csv`.

The QR sees OOS results for the FIRST time in Phase 7. Hard floor on `OOS_Sharpe / IS_Sharpe ≥ 0.5`.

## Git & Code Management

- **Branch:** `quant-research` worktree, feature branches `iteration-v3/NNN`
- **Tag:** `v0.v3-NNN` after MERGE
- **Reports:** `reports-v3/iteration_v3-NNN/`
- **Briefs:** `briefs-v3/iteration_v3-NNN/` (research_brief.md, phase5p5_gate.md, engineering_report.md, review.md)
- **Diaries:** `diary-v3/iteration_v3-NNN.md`
- **Analysis scripts:** `analysis/iteration_v3-NNN/*.py` (committed; produce brief Section 2 evidence)
- **Source code:** new `src/crypto_trade/features_v3/` package (introduced from iter-v3/001); new `src/crypto_trade/strategies/ml/validation_v3.py` for CPCV/PBO/PSR

**Track isolation enforced at runtime:**
- `grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` must be empty
- `grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v3/` must be empty

## quant-research Worktree Purity Principle

The `quant-research` worktree hosts BOTH v2 and v3 development. v2 lives in `iteration-v2/NNN` branches; v3 lives in `iteration-v3/NNN` branches. Both merge to `quant-research`. Neither merges to `main` (v1's branch). The `main` branch hosts only v1 development plus shared infrastructure.

## Baseline Rules

See `BASELINE_V3.md`. The first v3 baseline is written by iter-v3/001 (no virtual `iter-v3/000`). MERGE decisions update `BASELINE_V3.md` in a separate commit (`baseline-v3: update after iteration v3-NNN`).

Hard merge gates (inherited project-level):
- IS Sharpe > 1.0 AND OOS Sharpe > 1.0
- OOS / IS Sharpe ratio ≥ 0.5
- ≥10 trades/month OOS, ≥130 OOS total trades
- Top symbol concentration ≤ 30% of OOS PnL (or explicit exception with justification)
- 10-seed pre-MERGE validation: mean Sharpe > 0, ≥7/10 profitable

v3-specific hard gates (also enforced; any single failure = NO-MERGE):
- DSR > 0.95
- PBO < 0.4
- PSR > 0.95
- IC between any new family and existing < 0.7 (Critic Check 4)
- ADF p < 0.05 on every feature (or explicit "regime indicator" justification in brief Section 4)
- Pareto-non-dominated chosen seed on the 6-metric vector (Critic Check 6)

## Feature Column Pinning

MANDATORY for every v3 iteration. The runner must pass `feature_columns=list(V3_FEATURE_COLUMNS)` to `LightGbmStrategy`. Never `None`, never empty, never auto-discovered. LightGBM's `colsample_bytree` samples by position; column order silently produces different models.

The `V3_FEATURE_COLUMNS` constant lives in `src/crypto_trade/features_v3/__init__.py` (introduced in iter-v3/001).

## Candle Integrity & Freshness

Inherited from v2:
- `fetcher.py` drops forming candles: `if k.close_time < now_ms`
- Every kline CSV in `data/<SYMBOL>/8h.csv` must have `close_time` within 16h of measurement time
- Engineer's pre-flight check (Phase 6) verifies both before running backtest

Stale data + forming candles silently corrupt features and labels. iter-v2/059 lost 50 days of OOS data this way; the v3 Engineer's pre-flight check is non-negotiable.

## Phase 5.5 Gate

See `.claude/commands/quant-iteration-v3.md` §"Phase 5.5 — Pre-Phase 6 Gate (NEW, MOST IMPORTANT)" for the complete specification. Summary: Engineer reads `briefs-v3/iteration_v3-NNN/research_brief.md`, verifies all 10 mandatory sections (data split declaration, hypothesis, IS-only numerical evidence, proposed changes, expected OOS impact, risk mitigation, risk management design, **pre-registered failure-mode prediction**, **pre-registered MERGE/NO-MERGE criteria**, **library stack declaration**), and writes `phase5p5_gate.md` with OVERALL=PASS or BLOCK.

OVERALL=BLOCK → Phase 6 terminates immediately. Engineer commits the gate file as `docs(iter-v3/NNN): phase 5.5 gate BLOCK` and returns to QR. The Engineer NEVER attempts to fix the brief.

## Phase 7.5 Critic Review

See `.claude/commands/quant-iteration-v3.md` §"Phase 7.5 — Critic Adversarial Review (NEW)" and `.claude/agents/quant-critic.md` for the complete specification. Summary: after Engineer commits the engineering report, the orchestrating session invokes the `quant-critic` subagent (read-only tools: Read, Glob, Grep). Critic runs 8 mandatory checks (Look-Ahead, Embargo, DSR/PBO/PSR, IC, ADF, Pareto, Reproducibility, Hypothesis-Implementation Alignment) plus 4 optional checks. Emits `review.md` content as final assistant message; orchestrator persists at `briefs-v3/iteration_v3-NNN/review.md`.

OVERALL=BLOCK is FINAL — no rerun-after-fix (selection bias). If methodology root-cause needs fixing, becomes a NEW iter-v3/NNN+1 with new branch, brief, and backtest.

## Relationship to v1 and v2

| | v1 | v2 | v3 |
|---|---|---|---|
| Track focus | Edge discovery | Diversification | **Methodological rigor** |
| Branch | `main` | `quant-research` (`iteration-v2/`) | `quant-research` (`iteration-v3/`) |
| Symbols | BTC, ETH, LINK, LTC, DOT | SOL, XRP, DOGE, NEAR | TBD by iter-v3/001 (must exclude v1+v2) |
| Validation | Walk-forward + DSR | Walk-forward + DSR | **CPCV + DSR + PBO + PSR** |
| Roles | QR + QE | QR + QE | **QR + QE + Critic** |
| Phases | 8 | 8 | **10** (8 + 5.5 + 7.5) |
| Status | Active | Active sibling | Active sibling |

All three tracks share: `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24`, 8h candles, 5-seed inner ensemble `[42, 123, 456, 789, 1001]`, 10-seed pre-MERGE concentration check.

## NO CHEATING — Inherited from v1 and v2

- NEVER change `start_time` to skip bad IS months
- NEVER cherry-pick date ranges
- NEVER post-hoc filter trades
- NEVER tune parameters on OOS data
- NEVER allow labels to leak across CV fold boundaries (`gap = (timeout_candles + 1) × n_symbols`)
- NEVER allow labels to leak from live/prediction data to training data

v3 adds:

- NEVER skip the Phase 5.5 gate
- NEVER merge without Critic OVERALL=MERGE
- NEVER rerun the Critic after BLOCK ("let me fix one thing" = selection bias)
- NEVER include a v1 or v2 symbol in v3's universe
- NEVER import from `crypto_trade.features` (v1) or `crypto_trade.features_v2` (v2) in v3 code

## Library Stack (iter-v3/001+)

- `mlfinlab==1.4` (primary) or `mlfinpy` (MIT fallback) — CPCV, meta-labeling utilities
- `pypbo` — Probability of Backtest Overfitting
- `fracdiff>=0.10` — Numba-accelerated fractional differentiation with `FracdiffStat` for auto-selected `d*`
- `statsmodels` (already installed) — `adfuller` for ADF stationarity testing

iter-v3/001 adds these to `pyproject.toml`. Brief Section 9 declares versions used and any fallbacks.

## See Also

- `.claude/commands/quant-iteration-v3.md` — the v3 skill (workflow definition)
- `.claude/agents/quant-engineer.md` — Engineer agent (Phase 5.5 + Phase 6)
- `.claude/agents/quant-critic.md` — Critic agent (Phase 7.5, read-only)
- `.claude/agents/quant-researcher.md` — Researcher agent (Phases 1-5, 7, 8 — shared across all tracks)
- `BASELINE_V3.md` — current v3 baseline; iter-v3/001 writes the first one
- `BASELINE_V2.md` — sibling baseline (v2)
- `BASELINE.md` — sibling baseline (v1)
