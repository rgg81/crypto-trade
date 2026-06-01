# Phase 7.5 Critic Review — iter-v1/027 — TECHNICAL FAILURE

OVERALL: **CONFIRMATION-TECHNICAL-FAILURE — NO VERDICT**

## Iteration Type
TYPE: CONFIRMATION cycle-3 closing — TECHNICAL FAILURE

## What happened

After all 5 models trained successfully (13h compute), the runner crashed at the F-AXIS #1 hard-assert post-processing step:

```
File "run_baseline_v1.py", line 2378, in <genexpr>
    if r.symbol == "ETHUSDT" and "A (BTC+ETH pool)" in r.model_name
AttributeError: 'TradeResult' object has no attribute 'model_name'
```

The defensive check that LM Master Phase 4.5 §5 mandated to prevent /024-style dispatch defects was itself defective — used wrong attribute name. The check crashed AFTER comparison.csv would normally be emitted; all in-memory trade rosters were lost.

## Backtest completion status

All 5 models RAN to completion:
- Model A (Pool BTC+ETH): 340 trades / 6394s
- Model C' (LINK specialist): 192 trades / 7688s
- Model D (LTC + R1): 147 trades / 9779s
- Model E (DOT + R1 + R2): 153 trades / 9693s
- Model G (ETH-only + BTC-trend gate): 199 trades / 13224s

Total wall-clock: **13h** (vs 6h CAP) — wall-clock breach 2.2×.

ETH+gate BTC-trend gate fire-rate (G model): 19.60% (39/199 killed) — within /019 pre-registered bands.

## Recoverable artifacts

- `data/v1_iter_v1-027_trial_oof.parquet` — Optuna trial OOF (per-fold returns; sufficient for hyperparameter analysis)
- Per-model wall-clock + trade counts (from log)
- BTC-trend gate fire-rate stats (from log)
- F-AXIS #1 dispatch verification — NOT VERIFIED (the check crashed before running)

NOT recoverable:
- comparison.csv (per-symbol OOS Sharpe / portfolio Sharpe / DSR / PSR / PBO)
- per_symbol.csv (per-cohort OOS attribution)
- feature_importance per-model
- trades.csv (per-trade rosters; were in RAM)
- Multi-seed Pareto front analysis
- Cross-correlation reconciliation at multi-seed

## Verdict

**NO VERDICT POSSIBLE** — comparison.csv missing. Cannot determine PROMISING-METHODOLOGY / INERT / NEGATIVE.

Per user decision (2026-05-28): **Option 3 — abandon /027 as TECHNICAL FAILURE**. Cycle-3 closes without CONFIRMATION verdict.

## Defect codification

Memory entry created: `feedback_v1_defensive_check_must_be_tested.md` (commit pending).

Rule: defensive runtime checks accessing data-model attributes MUST be unit-tested against real instances before deployment. Attribute names must be verified against dataclass definitions, not assumed.

## Cycle-3 closure

Without /027 verdict, cycle-3 closes with:
- **10 EXPLORATIONs** (016-025) — 2 PROMISING + 1 PROMISING-METHODOLOGY + 7 NEGATIVE
- **1 sanity slot** (/026) — GREEN-WITH-FIX
- **1 TECHNICAL FAILURE** (/027) — no CONFIRMATION verdict
- **0 merges** — BASELINE_V1.md UNCHANGED at v0.v1-baseline-corrected

The standalone /018 LINK +0.80 OOS Δ and /019 ETH+gate +0.50 OOS Δ remain in the catalog as cycle-3's structural findings. Multi-seed validation deferred to cycle-4 or later.

## Path Forward (cycle-4)

Per LM Master /027 §9 (unchanged from pre-run mandate; was MANDATORY regardless of verdict):

1. **D-specialist (LTC) EXPLORATION** — family `per-cohort-specialization` — LTC -1.05 OOS Sharpe is dominant ceiling. Single-seed EXPLORATION budget (n_trials=18, ENSEMBLE_SIZE=3). Uses existing cached LTC data. Per-cohort specialist with INDEPENDENT cohort training avoids Pool A joint-loss-surface trap.

2. **C×E altcoin de-concentration** — risk-primitive or weighting — LINK+DOT joint risk (OOS Pearson +0.60 at /026) requires mitigation.

3. **Sample-weighting axis** — UNUSED cycle-3. AFML Ch.4 inverse-concurrency. Mechanism: reduce basin formation around overlapping label windows.

4. **XGBoost head-to-head** — model-arch REPEAT but different instance vs /024 partition. Level-wise growth + cross-entropy may distribute split allocation more uniformly than LightGBM leaf-wise.

## BLOCK-PENDING-FIX Rerun Protocol

N/A — user accepted Option 3 (abandon /027). NO rerun. Cycle-3 closes.

## Recommendations

1. **Pre-commit unit test pattern for runtime asserts** — every `assert <expr involving r.attr>` requires sample-instance unit test in same commit.

2. **Critic Phase 6.0 enhancement** — when reviewing dispatch hard-asserts, READ the dataclass definition at source of `r.attr` and verify attribute exists; don't assume from variable names.

3. **Persistence-before-verification pattern** — for CONFIRMATION-budget iterations, EMIT comparison.csv + reports BEFORE running expensive post-processing asserts. Defensive checks should fail gracefully (log warning + emit BLOCK-PENDING-FIX) rather than crashing the entire post-processing pipeline.
