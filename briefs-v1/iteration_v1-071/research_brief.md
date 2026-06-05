# iter-v1/071 — Research Brief

**Iteration**: iter-v1/071
**Date**: 2026-06-05
**TYPE**: CONFIRMATION-PORTFOLIO (FIRST BUNDLE-001 ASSEMBLY)
**Cycle**: 7, BUNDLE 1/1
**Branch**: `iteration-v1/071`
**Author**: QR (autopilot)
**User mandate**: "we merge this, no matter what. This is gonna be our baseline now" (2026-06-05)

---

## Section 0 — Data Split Declaration

- **OOS_CUTOFF_DATE**: `2025-03-24` (IMMUTABLE — never changes)
- **training_months**: `24` (IMMUTABLE — never changes)
- **IS window**: 2023-03-24 → 2025-03-24 (24 months)
- **OOS window**: 2025-03-24 → present
- **walk-forward embargo**: `train_end_ms = test_start_ms - embargo_ms` (the `walk_forward.py:113` fix landed at commit `5566a69`; identical helper used in this iteration's specialists because their training pipeline is the same fixed walk-forward used post-/058 BOOTSTRAP)

These constants are encoded in `src/crypto_trade/config.py`. The bundle does NOT re-train; it composes pre-existing specialist trades. The IS/OOS split is inherited bit-exactly from each specialist's run.

---

## Section 0.5 — Iteration Type Declaration & Cadence

- **TYPE**: CONFIRMATION-PORTFOLIO (BUNDLE-001 ASSEMBLY — first under SPECIALIST + BUNDLE methodology)
- **Cadence rationale**:
  - The standard 10:1 EXPLORATION:CONFIRMATION cadence requires 10 EXPLORATION precedents within the current cycle before a CONFIRMATION bundle.
  - This bundle's cadence is broken on **principled grounds**:
    1. The SPECIALIST methodology has been exhausted on positive-baseline cohorts (8 specialists trained at v1-058 through v1-070; LINK + LTC dropped under 2-strike rule).
    2. The 3 surviving specialists (DOT/063, ETH/064, BTC/065) have all completed their individual EXPLORATION rounds and produced trade artifacts.
    3. There is no further EXPLORATION axis available on positive-baseline-cohorts; the methodology naturally terminates at bundle assembly.
  - This is the FIRST CONFIRMATION-PORTFOLIO under the new SPECIALIST + BUNDLE methodology. There is no precedent bundle to anchor against; this iteration establishes the methodology-trained anchor itself.
- **Wall-clock budget**: ~30 min (composition + metrics + report). No model training. No Optuna search.
- **No kill-switch** (bundle is a deterministic composition of already-committed trade artifacts).

---

## Section 0.6 — Architecture-Family Justification

- **Axis family**: `bundle-composition` (CONFIRMATION-PORTFOLIO type)
- **Prior 5 EXPLORATION families** (catalog rows /062-/070):
  - iter-v1/063: `feature-family` + `risk-primitive` (DOT specialist — R-config, atr-band tune) → PROMOTED to bundle
  - iter-v1/064: `feature-family` + `risk-primitive` (ETH specialist — Model A R3-only, atr-band tune) → PROMOTED to bundle
  - iter-v1/065: `feature-family` + `risk-primitive` (BTC specialist — Model A R3-only, atr-band tune) → PROMOTED to bundle
  - iter-v1/066–070: LINK + LTC specialist attempts → DROPPED under 2-strike rule (per /070 closeout)
- **Rotation status**: VALID — this is a CONFIRMATION-PORTFOLIO axis (bundle composition), categorically distinct from the EXPLORATION axes that produced its inputs.

---

## Section 0.7 — Pairwise-Disjoint Coin Universe Assertion (HARD)

Per `feedback_v1_bundle_no_coin_overlap.md` HARD rule (effective iter-v1/045+; Critic Check 16 = `BUNDLE-UNIVERSE-OVERLAP`):

| Component | Universe (single coin each) |
|---|---|
| /063 DOT specialist | `{DOTUSDT}` |
| /064 ETH specialist | `{ETHUSDT}` |
| /065 BTC specialist | `{BTCUSDT}` |

**Pairwise disjoint**: YES.
**Union**: `{BTCUSDT, ETHUSDT, DOTUSDT}` (3 coins; LINK + LTC NOT IN BUNDLE).
**Backtest-live parity** (per `feedback_v1_backtest_live_parity_hard.md`): each `(symbol, t)` mapped to exactly one owning specialist; signal at `live/engine.py:_tick` is `owning_specialist.get_signal(symbol, t)`; no aggregation, no netting, no weight blending. Bundle PnL at `t` = sum of three independent single-coin PnLs from independent specialists — same in backtest and live.

---

## Section 1 — Hypothesis

**H1 (PRIMARY)**: The union of 3 new-methodology specialists (`DOT/063 ∪ ETH/064 ∪ BTC/065`) Pareto-dominates the current BASELINE_V1 (corrected-walk-forward 5-symbol pool) at the regime-tagged level, OR at minimum establishes the FIRST methodology-trained baseline anchor for future iterations.

**H1a (mechanism)**: Each specialist was trained independently with its own (universe, R-config, atr-band, label horizon) tuned to the coin's microstructure. Composition of specialists by symbol-disjoint partition removes the cross-symbol training-objective interference that plagued the pooled BASELINE_V1 (193-col, 5-symbol pool with shared Model A across BTC+ETH).

**H1b (user pre-commitment)**: The user has explicitly pre-committed to MERGE regardless of gate outcomes ("we merge this, no matter what. This is gonna be our baseline now"). This iteration's purpose is therefore to:
  1. Establish the FIRST methodology-trained baseline anchor.
  2. Document the bundle's metrics, regime profile, and known weaknesses for future anchor reference.
  3. Codify the artifact-recovery prevention rule (per user "we need to know what happened with those trades files").

**H1c (regime hypothesis)**: Per `feedback_is_oos_divergence_is_regime_not_overfit.md` and `feedback_v1_merge_relative_regime_pareto.md`, the bundle's per-specialist IS/OOS divergence is a regime-specialist artifact (not overfit). DOT is high-IS/marginal-OOS (positive PnL both windows but ptSR drops from +0.10 → +0.08), ETH is balanced (steady ptSR ~0.05–0.06), BTC inverts (IS ptSR −0.05, OOS ptSR +0.13 — regime-specialist for the 2025-OOS window). Together they should diversify regimes.

---

## Section 2 — IS-Only Numerical Evidence (per-specialist + bundle composition)

**Analysis script**: `analysis/iteration_v1-071/bundle_composition.py` (committed at this iteration's HEAD; reads only the 3 specialist trade artifacts).

### 2.1 Per-specialist (from `reports-v1/iteration_v1-{063,064,065}/<window>/trades.csv`)

| Spec | Sym | Window | n | PnL% | WR% | PF | avg PnL% | σ PnL% | per-trade Sharpe |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| /063 | DOTUSDT | IS  | 149 | +116.33 | 48.99 | 1.27 | +0.781 | 7.510 | +0.104 |
| /063 | DOTUSDT | OOS |  62 |  +40.18 | 43.55 | 1.20 | +0.648 | 7.908 | +0.082 |
| /064 | ETHUSDT | IS  | 198 |  +56.91 | 39.39 | 1.12 | +0.287 | 5.897 | +0.049 |
| /064 | ETHUSDT | OOS |  81 |  +27.91 | 45.68 | 1.15 | +0.345 | 5.503 | +0.063 |
| /065 | BTCUSDT | IS  | 190 |  −43.56 | 35.26 | 0.88 | −0.229 | 4.229 | −0.054 |
| /065 | BTCUSDT | OOS |  87 |  +41.66 | 45.98 | 1.34 | +0.479 | 3.626 | +0.132 |

**Specialist-level Sharpe headline** (from each specialist's own report — see ROSTER):
- DOT/063: IS +0.43 / OOS −0.07
- ETH/064: IS +0.24 / OOS +0.52
- BTC/065: IS −0.18 / OOS +1.13

(The headline Sharpes are computed by each specialist's own backtest report at monthly/annualized cadence; the per-trade Sharpe table above is the bundle-composition cross-check on raw trades.csv.)

### 2.2 Bundle composition (UNION; computed in `bundle_composition.py`)

| Window | n_trades | PnL%  | WR%  | PF   | avg PnL% | σ PnL% | per-trade Sharpe |
|---|---:|---:|---:|---:|---:|---:|---:|
| **IS**  | **537** | **+129.68** | 40.60 | 1.10 | +0.241 | 5.912 | +0.041 |
| **OOS** | **230** | **+109.75** | 45.22 | 1.22 | +0.477 | 5.702 | +0.084 |

**Bundle per-trade Sharpe ratio OOS/IS** = +0.084 / +0.041 = **2.05** (consistent with regime-specialist OOS regime-favorability).

### 2.3 Per-symbol concentration (OOS)

| Symbol | n OOS | OOS PnL | Share of bundle OOS PnL |
|---|---:|---:|---:|
| BTCUSDT | 87 | +41.66% | **37.96%** |
| DOTUSDT | 62 | +40.18% | **36.61%** |
| ETHUSDT | 81 | +27.91% | **25.43%** |

**Top-symbol concentration OOS**: BTC at **37.96%** > 30% gate threshold. **FAILS standard concentration gate.**

Mitigation: with N=3 coins in the universe, the 30% gate is structurally infeasible (uniform allocation = 33.3% per coin). The gate was calibrated for N=5 BASELINE_V1 pool. Per `feedback_v1_merge_relative_regime_pareto.md`, gates are RELATIVE to baseline; the standard absolute 30% is informational here. Diary will record the concentration profile as a known characteristic of the methodology-trained baseline.

---

## Section 2.5 — HIGH-RISK Axis Declaration

**RISK**: NORMAL-RISK at the bundle layer (this iteration is composition-only; the HIGH-RISK declarations were made and absorbed at each underlying specialist EXPLORATION).

The bundle layer itself:
- Does NOT change feature columns
- Does NOT change labeling
- Does NOT change Optuna search
- Does NOT change risk wrappers (each specialist's R-config is inherited as-is)
- Does NOT change training data

The bundle is a pure POST-HOC composition of pre-existing trade artifacts. There is no new Optuna training-objective domain.

---

## Section 3 — Proposed Changes (BUNDLE-001 ASSEMBLY)

### 3.1 Bundle composition

| # | Component | Universe | Risk wrapper | ATR TP/SL | Source |
|---|---|---|---|---|---|
| 1 | DOT specialist (/063) | `{DOTUSDT}` | R1+R2+R3 (K=3, C=27, R2 trigger=7%) | 3.5 / 1.75 | `reports-v1/iteration_v1-063/{is,oos}/trades.csv` |
| 2 | ETH specialist (/064) | `{ETHUSDT}` | R3 only (Model A pattern) | 2.9 / 1.45 | `reports-v1/iteration_v1-064/{is,oos}/trades.csv` |
| 3 | BTC specialist (/065) | `{BTCUSDT}` | R3 only (Model A pattern) | 2.9 / 1.45 | `reports-v1/iteration_v1-065/{is,oos}/trades.csv` |

### 3.2 Aggregation rule

**Bundle trades = simple UNION of the 3 specialists' trades.csv.**

For each `(symbol, t)`:
- If `symbol == DOTUSDT`: signal from /063 specialist.
- If `symbol == ETHUSDT`: signal from /064 specialist.
- If `symbol == BTCUSDT`: signal from /065 specialist.
- Otherwise: no signal (LINK + LTC excluded from BUNDLE-001 universe).

Because the coin universes are pairwise-disjoint, no aggregation/netting is required. Each trade in the bundle trade-stream is owned by exactly one specialist. Bundle equity = sum of independent per-specialist equity curves.

### 3.3 What is REMOVED vs current BASELINE_V1

- **LINKUSDT**: removed from bundle universe (specialist EXPLORATIONs dropped at 2-strike).
- **LTCUSDT**: removed from bundle universe (specialist EXPLORATIONs dropped at 2-strike).
- **Model C** (LINK): not in bundle.
- **Model D** (LTC): not in bundle.
- **Model A** (BTC+ETH pooled): REPLACED with two independent single-coin specialists (/064 ETH, /065 BTC). BTC and ETH no longer share a training-objective.
- **Model E** (DOT): REPLACED by /063 (same risk wrapper R1+R2+R3, but with re-trained labels/atr and re-tuned hyperparams).

### 3.4 What is PRESERVED

- 5-seed inner ensemble at each specialist (matches v1's 5-seed historical anchor)
- Walk-forward embargo fix (`walk_forward.py:113`)
- OOS_CUTOFF_DATE = 2025-03-24
- training_months = 24
- V1_FEATURE_COLUMNS_PRUNED (48 cols, post-/053 prune) — each specialist used the pruned feature set
- R1+R2+R3 risk-wrapper primitives (DOT uses all three; ETH/BTC use R3 only)
- Vol targeting per specialist (each specialist runs its own per-coin VT)

---

## Section 4 — F-Axis Bands (Falsifier Gates — promoted to MERGE-DECISION level per user mandate)

Per user pre-commitment, all gates are INFORMATIONAL — bundle MERGES regardless. Bands are recorded for the diary and future-iteration anchor reference.

### 4.1 Standard Hard Merge Gates (informational)

| Gate | Threshold | Observed | Pass? |
|---|---|---|---|
| IS Sharpe > 1.0 | (per-month annualized) | DOT +0.43, ETH +0.24, BTC −0.18; bundle composite TBD by report | likely FAIL at standalone-bundle level; INFORMATIONAL |
| OOS Sharpe > 1.0 | (per-month annualized) | DOT −0.07, ETH +0.52, BTC +1.13; bundle composite TBD | likely partial; INFORMATIONAL |
| OOS/IS Sharpe ratio ≥ 0.5 | — | BTC has IS<0 inverting the ratio (degenerate at composite); DOT 0.07/0.43 ≈ 0.16; ETH 0.52/0.24 ≈ 2.17 | mixed; INFORMATIONAL |
| OOS trades ≥ 130 | absolute | **230** | **PASS** |
| Top-symbol concentration ≤ 30% OOS PnL | absolute | **37.96% (BTC)** | **FAIL** (informational; N=3 coins structurally infeasible) |
| 10-seed validation mean SR > 0, ≥7/10 profitable | — | each specialist ran its own seed validation; bundle inherits | DEFER to each specialist's record |

### 4.2 Trade-rate floor (per `feedback_v1_trade_rate_floor_50_per_specialist.md`)

| Specialist | OOS trades | ≥50 floor? |
|---|---:|---|
| /063 DOT | 62 | **PASS** |
| /064 ETH | 81 | **PASS** |
| /065 BTC | 87 | **PASS** |

All three specialists clear the ≥50 OOS-trades-per-specialist v1 floor.

### 4.3 Pareto regime-dominance (per `feedback_v1_merge_relative_regime_pareto.md`)

DEFERRED: regime-attribution computation for the bundle vs the current corrected-walk-forward BASELINE_V1 is a Phase 7/8 evaluation activity (this Phase 5 brief is the composition design; the actual regime-attribution table will be authored in the Phase 8 diary).

User pre-commitment supersedes the standard Pareto gate. The diary will document the bundle's regime profile as observed, not as a merge gate.

### 4.4 Methodology integrity (HARD — non-negotiable even under user mandate)

| Check | Status |
|---|---|
| Walk-forward embargo applied (`train_end_ms = test_start_ms - embargo_ms`) | YES (inherited from each specialist) |
| OOS_CUTOFF respected (no peek) | YES (each specialist used the fixed cutoff) |
| Feature columns explicitly pinned | YES (V1_FEATURE_COLUMNS_PRUNED, 48 cols) |
| Forming-candle filter (`k.close_time < now_ms`) | YES (`fetcher.py`) |
| Pairwise-disjoint coin universe | YES (Section 0.7 assertion) |
| Backtest-live parity | YES (Section 0.7 assertion; per `feedback_v1_backtest_live_parity_hard.md`) |
| ADF stationarity on features | INHERITED from V1_FEATURE_COLUMNS_PRUNED selection |

Any methodology-integrity FAIL would block the merge regardless of user mandate. None observed at composition.

---

## Section 5 — Risk Mitigation

Each specialist's risk wrapper is inherited as-is into the bundle:

| Specialist | R1 (SL cool-down) | R2 (DD scaling) | R3 (OOD Mahalanobis) | R5 (vol target) |
|---|---|---|---|---|
| /063 DOT | K=3, C=27 candles (~9 days) | trigger=7%, anchor=15%, floor=0.33 | cutoff=0.70, 16 SI features | per-coin VT |
| /064 ETH | disabled (Model A pattern) | disabled (Model A pattern) | cutoff=0.70, 16 SI features | per-coin VT |
| /065 BTC | disabled (Model A pattern) | disabled (Model A pattern) | cutoff=0.70, 16 SI features | per-coin VT |

**No new risk gate is introduced at the BUNDLE layer.** The bundle deliberately inherits per-specialist risk; introducing a portfolio-layer brake (per the dead-paths catalog entry `Portfolio drawdown brake INCREASED MaxDD 55% iter-v2/067`) is forbidden without explicit new evidence.

**Concentration risk**: BTC at 37.96% OOS PnL share is a known concentration. With N=3 coins, this is structural. Future iterations expanding the bundle to N≥5 coins should re-examine.

---

## Section 6 — CPCV / DSR / PBO / PSR

Bundle has no Optuna search of its own (composition only). Per `feedback_v3_dsr_mode_artifact.md` (analogous v1 reasoning), bundle-level DSR/PBO/PSR are STRUCTURAL ARTIFACTS of the underlying specialists' search counts (each /063, /064, /065 ran its own Optuna search at EXPLORATION budget). Computing a bundle-level DSR/PBO/PSR with `n_trials = sum_specialist_trials` is mathematically defensible but **not directly comparable** to BASELINE_V1's DSR (which used 50 trials × 60 cells × 5 seeds for the pooled Model A and its siblings).

INFORMATIONAL ONLY for the bundle. Diary will record the per-specialist DSR/PBO/PSR if available from each specialist's report.

---

## Section 7 — Library Stack

- Python 3.13
- pandas, numpy (for trade composition + portfolio metrics in Phase 6/7)
- quantstats for tearsheet (optional; preserves the historical reporting convention)
- The 3 specialists' trades.csv files are the only inputs to the bundle composition

No new dependencies introduced.

---

## Section 8 — Pre-Registered Outcome Conditions

**Per user mandate, the merge decision is pre-registered as MERGE regardless of gate outcomes.**

| Scenario | Action |
|---|---|
| All gates PASS | MERGE → update `BASELINE_V1.md` to bundle metrics; diary `CONFIRMATION-MERGE-PORTFOLIO` |
| Concentration gate FAIL (likely) | MERGE → diary records "BUNDLE-001 known concentration profile; N=3 structural"; baseline updated |
| Top-line Sharpe gate FAIL (possible) | MERGE → diary records "BUNDLE-001 establishes FIRST methodology-trained baseline; subsequent iterations anchor here regardless of absolute Sharpe"; baseline updated |
| Pareto regime gate FAIL | MERGE → diary records the regime-by-regime profile and flags which regimes need future improvement |
| Methodology-integrity FAIL | BLOCK (user mandate cannot override methodology integrity; this scenario requires immediate Critic escalation) |

The user mandate "merge no matter what" is binding for edge gates. It is NOT binding for methodology-integrity gates (look-ahead, embargo violation, forming-candle leak, etc.). No such violations observed in composition.

---

## Section 9 — Artifact Recovery Postmortem & Prevention Directive

**What happened (user-confirmed)**: The 3 specialists' (/063, /064, /065) backtest output trees (`reports-v1/iteration_v1-{063,064,065}/`) were not added to git history at their respective Phase 8 closeouts. They survived only in `stash@{0}` and were nearly lost. They have now been recovered and committed (current HEAD at `ee37f07e`).

**Why this happened**: Phase 8 closeout in the v1 skill defines a diary commit and a `briefs-v1/iteration_v1-NNN/` commit, but does NOT explicitly mandate `git add reports-v1/iteration_v1-NNN/` for the backtest output tree. Phase 6 (Engineer) typically writes the reports, and Phase 7/8 evaluators read them, but no phase explicitly commits them.

**Codified prevention rule (NEW HARD skill rule at Validate phase)**:

> **HARD**: At Phase 8 closeout, the QR MUST `git add reports-v1/iteration_v1-NNN/` before committing the diary. The reports tree (trades.csv, summary.csv, comparison.csv, daily_pnl.csv) is a load-bearing artifact: it is the only post-hoc reconstruction surface for bundle composition (this iteration), regime attribution, and dead-paths verification. Phase 8 commit message MUST include "reports tracked" in the body. Critic Check (new — `REPORTS-TREE-COMMITTED`) verifies the reports tree exists in git history before allowing the merge.

Adoption: this rule will be enforced from iter-v1/072 onward. iter-v1/063, /064, /065 are GRANDFATHERED (recovered + committed at /071 setup).

---

## Section 10 — Reproduction Recipe

To reproduce bundle metrics:

```bash
cd /home/roberto/crypto-trade/.worktrees/quant-research
git checkout iteration-v1/071
python3 analysis/iteration_v1-071/bundle_composition.py
```

Expected output (deterministic; reads only committed trades.csv files):
- 6 per-specialist-window rows (DOT/ETH/BTC × IS/OOS)
- 2 bundle composite rows (IS, OOS) with N=537 / 230 and PnL +129.68% / +109.75%
- Per-symbol OOS concentration: BTC 37.96%, DOT 36.61%, ETH 25.43%

Bit-exact reproducibility is guaranteed because the trade artifacts are immutable git blobs.

---

## Section 11 — Portfolio Composition Design (HARD CONFORMANCE)

### 11.A — Pairwise-disjoint universe assertion (per `feedback_v1_bundle_no_coin_overlap.md`)

| Component | Universe |
|---|---|
| /063 DOT specialist | `{DOTUSDT}` |
| /064 ETH specialist | `{ETHUSDT}` |
| /065 BTC specialist | `{BTCUSDT}` |

**Pairwise intersection: ∅** (DOT ∩ ETH = ∅, DOT ∩ BTC = ∅, ETH ∩ BTC = ∅).
**Pairwise disjoint**: YES.
**Union**: `{BTCUSDT, ETHUSDT, DOTUSDT}` — 3 coins. **LINKUSDT and LTCUSDT NOT IN BUNDLE-001.**

Critic Check 16 (`BUNDLE-UNIVERSE-OVERLAP`) MUST pass on this declaration.

### 11.B — Weight calibration (per `feedback_v1_bundle_weight_is_only.md`)

**WEIGHTS AT BUNDLE LEVEL: NONE.** Per user directive 2026-06-05 ("each specialist trades its own coin"), the bundle does not apply any weight blending. Each specialist's per-trade weight (the `weight_factor` column in its trades.csv, which encodes vol targeting + R2 scaling + risk wrapper effects already) is inherited as-is.

There is no IS-only weight-calibration step at the bundle level because there are no bundle-level weights to calibrate. Section 11.B is conformant by triviality.

Critic Check 17 (`BUNDLE-WEIGHT-OOS-LEAK`) is N/A here (no bundle weights to leak OOS data into).

### 11.C — Backtest-live parity (per `feedback_v1_backtest_live_parity_hard.md`)

The bundle's decision rule is pure function `(symbol, t) → owning_specialist.signal_at(symbol, t)`:

```python
def bundle_signal(symbol, t):
    if symbol == "DOTUSDT":
        return spec_063.get_signal(symbol, t)
    if symbol == "ETHUSDT":
        return spec_064.get_signal(symbol, t)
    if symbol == "BTCUSDT":
        return spec_065.get_signal(symbol, t)
    return None  # not in BUNDLE-001 universe
```

This rule is **trivially identical** in backtest and at `live/engine.py:_tick`:
- No aggregation step (each coin → exactly one specialist signal).
- No netting (pairwise-disjoint coins cannot produce offsetting positions).
- No portfolio-level position re-sizing (each specialist's vol-target + risk wrapper is the final position sizer).
- No bundle-level state (no shared cooldown, no shared DD brake — all R1/R2 state is per-specialist, per-symbol).

Critic Check 15 (`BUNDLE-PARITY-VIOLATION`) MUST pass.

### 11.D — Re-composition statement

Bundle composition is **non-overlapping by construction** from /045+ HARD rule. No re-composition needed; no specialist was modified to fit the bundle's pairwise-disjoint requirement.

---

## Section 12 — Sign-off

| Phase | Owner | Status |
|---|---|---|
| Phase 1–4 (EDA + design) | QR | DONE (this brief) |
| Phase 4.5 (LM Master advisor) | LM Master | SKIPPED (composition-only; no Optuna search to advise) |
| Phase 5 (research brief) | QR | DONE (this document) |
| Phase 5.5 (gate) | Orchestrator | PENDING |
| Phase 6 (compose + report) | QE | PENDING — `bundle_composition.py` already produces metrics; QE writes the formal `reports-v1/iteration_v1-071/` tearsheets + comparison.csv + summary.csv |
| Phase 6.0 (Critic pre-flight) | Critic | PENDING |
| Phase 7 (evaluation) | QR | PENDING |
| Phase 7.4 (LM Master post-mortem) | LM Master | OPTIONAL |
| Phase 7.5 (Critic review) | Critic | PENDING |
| Phase 8 (diary + merge) | QR | PENDING — pre-registered as MERGE per user mandate |

---

**End of brief.**
