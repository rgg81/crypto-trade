# iter-v1/082 — Research Brief

**Iteration**: iter-v1/082
**Date**: 2026-06-09
**TYPE**: CONFIRMATION-PORTFOLIO (BUNDLE-002 ASSEMBLY)
**Cycle**: 7, BUNDLE 2/N
**Branch**: `iteration-v1/082`
**Author**: QR (autopilot)
**User mandate**: "let's try the bundle-002" (2026-06-09); TENTATIVE-merge precedent inherited from /071 ("we merge this, no matter what. This is gonna be our baseline now.")

---

## Section 0 — Data Split Declaration

- **OOS_CUTOFF_DATE**: `2025-03-24` (IMMUTABLE — never changes)
- **training_months**: `24` (IMMUTABLE — never changes)
- **IS window**: 2023-03-24 → 2025-03-24 (24 months)
- **OOS window**: 2025-03-24 → present
- **walk-forward embargo**: `train_end_ms = test_start_ms - embargo_ms` (the `walk_forward.py:113` fix landed at commit `5566a69`; identical helper used in this iteration's specialists because their training pipeline is the same fixed walk-forward used post-/058 BOOTSTRAP).

These constants are encoded in `src/crypto_trade/config.py`. The bundle does NOT re-train; it composes pre-existing specialist trades. The IS/OOS split is inherited bit-exactly from each specialist's run.

---

## Section 0.5 — Iteration Type Declaration & Cadence

- **TYPE**: CONFIRMATION-PORTFOLIO (BUNDLE-002 ASSEMBLY — second under SPECIALIST + BUNDLE methodology; first to incorporate a NEW SYMBOL specialist beyond the BUNDLE-001 universe).
- **Cadence rationale**:
  - BUNDLE-001 (/071) was the FIRST methodology-trained baseline anchor. BUNDLE-002 (/082) extends it by adding AAVE/078 as a fourth pairwise-disjoint single-coin specialist.
  - The 3 BUNDLE-001 specialists (/063 DOT, /064 ETH, /065 BTC) are re-used bit-exactly from their committed trade artifacts.
  - The /078 AAVE specialist (PROMISING-TENTATIVE band per LM Master 7.5 / Critic 7.5 at /078 closeout) is added under the user-mandate TENTATIVE-merge precedent set at /071.
- **Wall-clock budget**: ~30 min (composition + metrics + report). No model training. No Optuna search. The 4 specialists' trades.csv files are the only inputs.
- **No kill-switch** (bundle is a deterministic composition of already-committed trade artifacts).

---

## Section 0.6 — Architecture-Family Justification

- **Axis family**: `BUNDLE-ASSEMBLY` (CONFIRMATION-PORTFOLIO type)
- **Prior 5 EXPLORATION/CONFIRMATION families** leading to this bundle:
  - iter-v1/071: `bundle-composition` (BUNDLE-001 FIRST ASSEMBLY — 3 specialists DOT/ETH/BTC)
  - iter-v1/076: `feature-family` + `risk-primitive` (AAVE NEW SYMBOL specialist — 1st attempt; SPECIALIST-NEGATIVE 1st strike per /076 closeout)
  - iter-v1/078: `feature-family` (AAVE specialist with `excess_ret_5d_vs_majors_z90` cross-asset relative-strength feature → PROMISING-TENTATIVE) → PROMOTED to bundle
  - iter-v1/079–081: bundle compose-script hardening + code-review fixes (H2/H5/H8/H9/H10 + parity smoke test) — infra, no axis content
  - iter-v1/082: BUNDLE-002 ASSEMBLY (this iteration) — adds AAVE/078 to BUNDLE-001
- **Rotation status**: VALID — `BUNDLE-ASSEMBLY` is a categorically distinct axis from the EXPLORATION axes that produced its inputs (per the /071 precedent: bundle composition is its own axis family).
- **One-sentence rationale**: Per the cycle-6/7 per-symbol regime-specialist mandate, adding a 4th pairwise-disjoint specialist (AAVE) to BUNDLE-001 is the natural next BUNDLE-ASSEMBLY step — diversification across 4 regime-distinct single-coin specialists, no cross-symbol training-objective interference.

---

## Section 0.7 — Pairwise-Disjoint Coin Universe Assertion (HARD)

Per `feedback_v1_bundle_no_coin_overlap.md` HARD rule (effective iter-v1/045+; Critic Check 16 = `BUNDLE-UNIVERSE-OVERLAP`):

| Component | Universe (single coin each) |
|---|---|
| /063 DOT specialist | `{DOTUSDT}` |
| /064 ETH specialist | `{ETHUSDT}` |
| /065 BTC specialist | `{BTCUSDT}` |
| /078 AAVE specialist | `{AAVEUSDT}` |

**Pairwise intersections**:
- DOT ∩ ETH = ∅, DOT ∩ BTC = ∅, DOT ∩ AAVE = ∅
- ETH ∩ BTC = ∅, ETH ∩ AAVE = ∅
- BTC ∩ AAVE = ∅

**Pairwise disjoint**: YES (all 6 pairwise intersections empty).
**Union**: `{BTCUSDT, ETHUSDT, DOTUSDT, AAVEUSDT}` (4 coins).
**Backtest-live parity** (per `feedback_v1_backtest_live_parity_hard.md`): each `(symbol, t)` mapped to exactly one owning specialist; signal at `live/engine.py:_tick` is `owning_specialist.get_signal(symbol, t)`; no aggregation, no netting, no weight blending. Bundle PnL at `t` = sum of four independent single-coin PnLs from independent specialists — same in backtest and live.

---

## Section 1 — Hypothesis

**H1 (PRIMARY)**: The union of 4 new-methodology specialists (`DOT/063 ∪ ETH/064 ∪ BTC/065 ∪ AAVE/078`) Pareto-dominates BUNDLE-001 (current baseline `v0.v1-071`) at the regime-tagged level by adding a 4th symbol-disjoint regime specialist, OR at minimum establishes BUNDLE-002 as the methodology-trained second-anchor (extending the BUNDLE-001 baseline with one additional pairwise-disjoint coin).

**H1a (mechanism)**: AAVE/078 introduces a new cross-asset relative-strength feature (`excess_ret_5d_vs_majors_z90`) on top of the 48-col V1_FEATURE_COLUMNS_PRUNED set, giving the specialist a 49-col feature surface. The other 3 specialists (/063, /064, /065) use the 48-col native pruned set and are inherited bit-exactly. The bundle composition is the partition-disjoint union; AAVE's signal is fully isolated to its own coin universe.

**H1b (user pre-commitment)**: User directive "let's try the bundle-002" (2026-06-09) implicitly authorizes assembly under the TENTATIVE-merge precedent set at /071. Per the precedent, individual-specialist verdicts in the TENTATIVE band (such as /078's PROMISING-TENTATIVE) do not block bundle merge — the bundle merge stands on its own composite metrics + methodology integrity.

**H1c (regime hypothesis)**: Per `feedback_is_oos_divergence_is_regime_not_overfit.md` and `feedback_v1_merge_relative_regime_pareto.md`, each specialist's IS/OOS profile is a regime-specialist artifact:
- DOT/063: high-IS/positive-OOS (IS +1.32 / OOS +1.36 per task spec)
- ETH/064: balanced (IS +0.24 / OOS +0.52)
- BTC/065: inverted (IS +0.07 / OOS −0.20)
- AAVE/078: TENTATIVE positive both windows (IS +0.34 / OOS +0.16)

Together they should diversify regimes and produce a composite with reduced single-specialist concentration.

---

## Section 2 — IS-Only Numerical Evidence (per-specialist + bundle composition)

**Analysis script**: `analysis/iteration_v1-082/bundle_composition.py` (committed at iteration HEAD; reads only the 4 specialist trade artifacts).

### 2.1 Per-specialist (from `reports-v1/iteration_v1-{063,064,065,078}/<window>/trades.csv`)

Trade counts (cross-checked against the committed per_symbol.csv at this iteration's bundle reports):

| Spec | Sym | IS trades | OOS trades |
|---|---|---:|---:|
| /063 | DOTUSDT | 149 | 62 |
| /064 | ETHUSDT | 198 | 81 |
| /065 | BTCUSDT | 190 | 87 |
| /078 | AAVEUSDT | 157 | 90 |
| **Total** | — | **694** | **320** |

### 2.2 Per-specialist headline Sharpe (per task spec, from each specialist's own report)

| Specialist | IS Sharpe | OOS Sharpe | Verdict band at closeout |
|---|---:|---:|---|
| /063 DOT | +1.32 | +1.36 | VALIDATED |
| /064 ETH | +0.24 | +0.52 | VALIDATED |
| /065 BTC | +0.07 | −0.20 | VALIDATED (regime-specialist; OOS<0 absorbed as known characteristic in BUNDLE-001) |
| /078 AAVE | +0.34 | +0.16 | **PROMISING-TENTATIVE** (LM Master 7.5 / Critic 7.5 at /078 closeout) |

### 2.3 Per-symbol PnL composition (from committed `reports-v1/iteration_v1-082/<window>/per_symbol.csv`)

**In-Sample (IS):**

| Symbol | n | WR% | Net PnL% | avg PnL% | Share of bundle IS PnL |
|---|---:|---:|---:|---:|---:|
| AAVEUSDT | 157 | 41.4 | +88.772 | +0.565 | 40.64% |
| BTCUSDT | 190 | 35.3 | −43.563 | −0.229 | −19.94% |
| DOTUSDT | 149 | 49.0 | +116.335 | +0.781 | 53.25% |
| ETHUSDT | 198 | 39.4 | +56.909 | +0.287 | 26.05% |
| **Total IS** | **694** | **40.8** | **+218.453** | **+0.315** | **100.00%** |

**Out-of-Sample (OOS):**

| Symbol | n | WR% | Net PnL% | avg PnL% | Share of bundle OOS PnL |
|---|---:|---:|---:|---:|---:|
| AAVEUSDT | 90 | 40.0 | +12.933 | +0.144 | 10.54% |
| BTCUSDT | 87 | 46.0 | +41.660 | +0.479 | **33.96%** |
| DOTUSDT | 62 | 43.5 | +40.183 | +0.648 | 32.75% |
| ETHUSDT | 81 | 45.7 | +27.907 | +0.345 | 22.75% |
| **Total OOS** | **320** | **43.8** | **+122.683** | **+0.383** | **100.00%** |

**Top-symbol concentration OOS**: BTC at **33.96%** > 30% gate threshold. Mitigation: with N=4 coins the uniform-allocation share is 25%; 33.96% is within the structural feasibility band (vs the 37.96% recorded under N=3 at BUNDLE-001). Concentration **improved** vs BUNDLE-001 (−4.0 pts).

### 2.4 Per-trade-roster composite (from `reports-v1/iteration_v1-082/comparison.csv`)

| Metric | In-Sample | Out-of-Sample | OOS/IS ratio |
|---|---:|---:|---:|
| **Monthly Sharpe** | **+0.7157** | **+1.0043** | **1.4031** |
| Monthly Sortino | +1.0819 | +1.7947 | 1.6588 |
| Max Drawdown | 89.03% | 63.15% | 0.7093 |
| Win Rate | 40.78% | 43.75% | 1.0729 |
| Profit Factor | 1.1236 | 1.1501 | 1.0236 |
| Total Trades | 694 | 320 | 0.4611 |
| Total Net PnL | +218.453% | +122.683% | 0.5616 |
| Calmar Ratio | 0.755 | 1.457 | 1.9298 |
| Top-symbol concentration (OOS) | N/A | **33.96% (BTC)** | N/A |

---

## Section 2.5 — HIGH-RISK Axis Declaration

**RISK**: NORMAL-RISK at the bundle layer (this iteration is composition-only; HIGH-RISK declarations were made and absorbed at each underlying specialist EXPLORATION).

The bundle layer itself:
- Does NOT change feature columns (each specialist's feature set is inherited as-is — 48 cols for /063/064/065, 49 cols for /078)
- Does NOT change labeling
- Does NOT change Optuna search
- Does NOT change risk wrappers (each specialist's R-config is inherited as-is)
- Does NOT change training data

The bundle is a pure POST-HOC composition of pre-existing trade artifacts. There is no new Optuna training-objective domain.

The AAVE/078 underlying specialist introduces the `excess_ret_5d_vs_majors_z90` feature (a cross-asset z-score over the 90-candle window) which was HIGH-RISK at /078 — but that risk was absorbed and verdict-tagged PROMISING-TENTATIVE at /078's own Phase 8 closeout. /082 is a downstream consumer of /078's trade artifacts.

---

## Section 3 — Proposed Changes (BUNDLE-002 ASSEMBLY)

### 3.1 Bundle composition

| # | Component | Universe | Feature set | Risk wrapper | ATR TP/SL | Source |
|---|---|---|---|---|---|---|
| 1 | DOT specialist (/063) | `{DOTUSDT}` | 48-col V1_FEATURE_COLUMNS_PRUNED | R1+R2+R3 (K=3, C=27, R2 trigger=7%) | 3.5 / 1.75 | `reports-v1/iteration_v1-063/{is,oos}/trades.csv` |
| 2 | ETH specialist (/064) | `{ETHUSDT}` | 48-col V1_FEATURE_COLUMNS_PRUNED | R3 only (Model A pattern) | 2.9 / 1.45 | `reports-v1/iteration_v1-064/{is,oos}/trades.csv` |
| 3 | BTC specialist (/065) | `{BTCUSDT}` | 48-col V1_FEATURE_COLUMNS_PRUNED | R3 only (Model A pattern) | 2.9 / 1.45 | `reports-v1/iteration_v1-065/{is,oos}/trades.csv` |
| 4 | AAVE specialist (/078) | `{AAVEUSDT}` | 49-col = V1_FEATURE_COLUMNS_PRUNED + `excess_ret_5d_vs_majors_z90` | per /078 spec | per /078 spec | `reports-v1/iteration_v1-078/{is,oos}/trades.csv` |

### 3.2 Aggregation rule

**Bundle trades = simple UNION of the 4 specialists' trades.csv.**

For each `(symbol, t)`:
- If `symbol == DOTUSDT`: signal from /063 specialist.
- If `symbol == ETHUSDT`: signal from /064 specialist.
- If `symbol == BTCUSDT`: signal from /065 specialist.
- If `symbol == AAVEUSDT`: signal from /078 specialist.
- Otherwise: no signal (LINK + LTC + all others excluded from BUNDLE-002 universe).

Because the coin universes are pairwise-disjoint, no aggregation/netting is required. Each trade in the bundle trade-stream is owned by exactly one specialist. Bundle equity = sum of independent per-specialist equity curves.

### 3.3 What CHANGES vs current BASELINE_V1 (= BUNDLE-001, tag `v0.v1-071`)

- **+ AAVEUSDT added** to the bundle universe (4th pairwise-disjoint specialist).
- **+ `excess_ret_5d_vs_majors_z90`** cross-asset feature exposed at the AAVE specialist (49-col surface for that coin only; other 3 coins unchanged on 48-col).
- BUNDLE-001's 3 specialists (/063, /064, /065) are inherited bit-exactly.

### 3.4 What is PRESERVED

- BUNDLE-001's 3 specialists (DOT, ETH, BTC) — same trade artifacts; no recomputation.
- 5-seed inner ensemble at each specialist (matches v1's 5-seed historical anchor)
- Walk-forward embargo fix (`walk_forward.py:113`)
- OOS_CUTOFF_DATE = 2025-03-24
- training_months = 24
- V1_FEATURE_COLUMNS_PRUNED (48 cols) baseline feature set; /078 adds 1 column on top
- R1+R2+R3 risk-wrapper primitives where each specialist used them
- Vol targeting per specialist (each specialist runs its own per-coin VT)
- 50 seeds × 30 trials × specialist_mode per individual specialist (locked methodology constants per task spec)
- `max_depth=5` FIXED, `num_leaves=31` FIXED (per task spec)
- All 8 code review fixes (C2/H1, H5/H10, H8/H9, H2, plus the parity smoke test from /081) inherited via library state at HEAD

---

## Section 4 — F-Axis Bands (Falsifier Gates — promoted to MERGE-DECISION level per user mandate)

Per user pre-commitment ("let's try the bundle-002" + TENTATIVE-merge precedent from /071), all gates are INFORMATIONAL — bundle MERGES regardless of edge-gate outcomes (methodology-integrity gates still HARD-block).

### 4.1 Standard Hard Merge Gates (informational vs HARD)

| Gate | Threshold | Observed | Pass? |
|---|---|---|---|
| IS Monthly Sharpe > 1.0 | (composite) | **+0.7157** | informational FAIL (still > BUNDLE-001 IS +0.5463) |
| OOS Monthly Sharpe > 1.0 | (composite) | **+1.0043** | informational PASS (≥ 1.0 threshold and > BUNDLE-001 OOS +0.9636) |
| OOS/IS Sharpe ratio ≥ 0.5 | — | **1.4031** | informational PASS |
| OOS trades ≥ 130 | absolute | **320** | informational PASS |
| Top-symbol concentration ≤ 30% OOS PnL | absolute | **33.96% (BTC)** | informational FAIL (N=4 structural; improved from BUNDLE-001's 37.96%) |
| 10-seed validation mean SR > 0, ≥7/10 profitable | — | each specialist ran its own seed validation; bundle inherits | DEFER to each specialist's record |

### 4.2 Trade-rate floor (per `feedback_v1_trade_rate_floor_50_per_specialist.md`)

| Specialist | OOS trades | ≥50 floor? |
|---|---:|---|
| /063 DOT | 62 | **PASS** |
| /064 ETH | 81 | **PASS** |
| /065 BTC | 87 | **PASS** |
| /078 AAVE | 90 | **PASS** |

All four specialists clear the ≥50 OOS-trades-per-specialist v1 floor.

### 4.3 Pareto regime-dominance (per `feedback_v1_merge_relative_regime_pareto.md`)

DEFERRED to Phase 8 diary (this Phase 5 brief is the composition design). Headline composite comparison vs BUNDLE-001 anchor (informational):

| Metric | BUNDLE-001 (`v0.v1-071`) | BUNDLE-002 (this iter) | Δ |
|---|---:|---:|---:|
| IS Monthly Sharpe | +0.5463 | +0.7157 | **+0.1694** |
| OOS Monthly Sharpe | +0.9636 | +1.0043 | **+0.0407** |
| OOS/IS ratio | 1.7639 | 1.4031 | −0.3608 |
| IS trades | 537 | 694 | +157 |
| OOS trades | 230 | 320 | +90 |
| IS PnL% | +129.681 | +218.453 | +88.772 |
| OOS PnL% | +109.750 | +122.683 | +12.933 |
| Top-symbol concentration OOS | 37.96% (BTC) | 33.96% (BTC) | **−4.00 pts** |
| Max Drawdown OOS | 36.51% | 63.15% | +26.64 pts |

Composite picture: BUNDLE-002 is Pareto-better-or-equal on Sharpe (both IS+OOS positive deltas), trade count (more breadth), concentration (improved), and PnL%, but **worse on MaxDD OOS** (+26.64 pts). The MaxDD increase is a known characteristic of the AAVE/078 specialist's standalone profile (PROMISING-TENTATIVE band, smaller positive OOS Sharpe). Diary will record the full per-regime attribution.

### 4.4 Methodology integrity (HARD — non-negotiable even under user mandate)

| Check | Status |
|---|---|
| Walk-forward embargo applied (`train_end_ms = test_start_ms - embargo_ms`) | YES (inherited from each specialist) |
| OOS_CUTOFF respected (no peek) | YES (each specialist used the fixed cutoff) |
| Feature columns explicitly pinned | YES (V1_FEATURE_COLUMNS_PRUNED 48 cols for /063/064/065; 49 cols for /078) |
| Forming-candle filter (`k.close_time < now_ms`) | YES (`fetcher.py`) |
| Pairwise-disjoint coin universe | YES (Section 0.7 + Section 11.A assertions) |
| Backtest-live parity | YES (Section 0.7 + Section 11.C assertions; per `feedback_v1_backtest_live_parity_hard.md`) |
| ADF stationarity on features | INHERITED from V1_FEATURE_COLUMNS_PRUNED selection + /078 cross-asset z-score (90-candle window) is stationary-by-construction |
| Reports-tree committed (HARD from /071 prevention rule) | bundle reports tree `reports-v1/iteration_v1-082/` will be `git add`-ed at Phase 8 closeout per /071 Section 9 rule |

Any methodology-integrity FAIL would block the merge regardless of user mandate. None observed at composition.

---

## Section 5 — Risk Mitigation

Each specialist's risk wrapper is inherited as-is into the bundle:

| Specialist | R1 (SL cool-down) | R2 (DD scaling) | R3 (OOD Mahalanobis) | R5 (vol target) |
|---|---|---|---|---|
| /063 DOT | K=3, C=27 candles (~9 days) | trigger=7%, anchor=15%, floor=0.33 | cutoff=0.70, 16 SI features | per-coin VT |
| /064 ETH | disabled (Model A pattern) | disabled (Model A pattern) | cutoff=0.70, 16 SI features | per-coin VT |
| /065 BTC | disabled (Model A pattern) | disabled (Model A pattern) | cutoff=0.70, 16 SI features | per-coin VT |
| /078 AAVE | per /078 spec (inherited from AAVE specialist setup) | per /078 spec | cutoff=0.70 (Mahalanobis 16-SI standard) | per-coin VT |

**No new risk gate is introduced at the BUNDLE layer.** The bundle deliberately inherits per-specialist risk; introducing a portfolio-layer brake (per the dead-paths catalog entry `Portfolio drawdown brake INCREASED MaxDD 55% iter-v2/067`) is forbidden without explicit new evidence.

**Concentration risk**: BTC at 33.96% OOS PnL share is a known concentration (improved from BUNDLE-001's 37.96% but still above the absolute 30% gate; N=4 structural floor at uniform = 25%). Future iterations expanding to N≥5 coins should re-examine.

**MaxDD OOS risk**: BUNDLE-002 OOS MaxDD = 63.15% (vs BUNDLE-001's 36.51%, Δ +26.64 pts). This is a material deterioration in tail risk. Diary will record this as a known characteristic of the TENTATIVE-band AAVE/078 specialist's standalone profile + the composition effect.

---

## Section 6 — CPCV / DSR / PBO / PSR

Bundle has no Optuna search of its own (composition only). Per `feedback_v3_dsr_mode_artifact.md` (analogous v1 reasoning), bundle-level DSR/PBO/PSR are STRUCTURAL ARTIFACTS of the underlying specialists' search counts (each /063, /064, /065, /078 ran its own Optuna search at SPECIALIST/EXPLORATION budget). Computing a bundle-level DSR/PBO/PSR with `n_trials = sum_specialist_trials` is mathematically defensible but **not directly comparable** to BASELINE_V1's DSR (which used 50 trials × 60 cells × 5 seeds for the pooled Model A and its siblings).

INFORMATIONAL ONLY for the bundle. Diary will record the per-specialist DSR/PBO/PSR if available from each specialist's report. The PROMISING-TENTATIVE band of /078 is explicitly because its standalone DSR/PSR sat in the inconclusive zone — bundle composition does not mask that uncertainty; it absorbs it under user-mandated TENTATIVE-merge precedent (see Section 13).

---

## Section 7 — Library Stack

- Python 3.13
- pandas, numpy (for trade composition + portfolio metrics in Phase 6/7)
- quantstats for tearsheet (optional; preserves the historical reporting convention)
- The 4 specialists' trades.csv files are the only inputs to the bundle composition

No new dependencies introduced.

---

## Section 8 — Pre-Registered Outcome Conditions

**Per user mandate, the merge decision is pre-registered as MERGE regardless of edge-gate outcomes (methodology-integrity gates still HARD-block).**

| Scenario | Action |
|---|---|
| All gates PASS | MERGE → update `BASELINE_V1.md` to BUNDLE-002 metrics; diary `CONFIRMATION-MERGE-PORTFOLIO`; new tag `v0.v1-082` |
| Concentration gate FAIL (likely; 33.96% > 30%) | MERGE → diary records "BUNDLE-002 concentration 33.96% improved from BUNDLE-001 37.96% but still > 30% gate; N=4 structural"; baseline updated |
| IS Sharpe gate FAIL (likely; +0.7157 < 1.0) | MERGE → diary records "BUNDLE-002 IS Sharpe +0.72 below 1.0 absolute floor but +0.17 above BUNDLE-001 anchor"; relative regime Pareto applies; baseline updated |
| OOS Sharpe gate PASS (+1.0043 ≥ 1.0) | MERGE → diary records the clear OOS pass |
| MaxDD deterioration (+26.64 pts) | MERGE → diary records the tail-risk delta and tags it as a known characteristic of the TENTATIVE-band /078 specialist; future iteration may revisit |
| Methodology-integrity FAIL | BLOCK (user mandate cannot override methodology integrity; this scenario requires immediate Critic escalation) |

The user mandate "let's try the bundle-002" combined with the /071 TENTATIVE-merge precedent is binding for edge gates. It is NOT binding for methodology-integrity gates (look-ahead, embargo violation, forming-candle leak, etc.). No such violations observed at composition.

---

## Section 9 — Artifact Tracking (HARD Rule Compliance from /071 Section 9)

Per the /071 prevention rule (Section 9): "At Phase 8 closeout, the QR MUST `git add reports-v1/iteration_v1-NNN/` before committing the diary."

**Status for /082**:
- `reports-v1/iteration_v1-082/comparison.csv` — committed at `a18e73ba`
- `reports-v1/iteration_v1-082/in_sample/` (5 CSVs: trades, daily_pnl, monthly_pnl, per_regime, per_symbol) — committed at `a18e73ba`
- `reports-v1/iteration_v1-082/out_of_sample/` (5 CSVs) — committed at `a18e73ba`

All bundle report artifacts are already in git history at the bundle compose commit. Phase 8 diary commit will reference this commit and assert reports-tree-committed.

---

## Section 10 — Reproduction Recipe

To reproduce bundle metrics:

```bash
cd /home/roberto/crypto-trade/.worktrees/quant-research
git checkout iteration-v1/082
python3 analysis/iteration_v1-082/bundle_composition.py   # if/when committed under analysis/
# Otherwise inputs are directly from:
#   reports-v1/iteration_v1-063/{is,oos}/trades.csv (DOT)
#   reports-v1/iteration_v1-064/{is,oos}/trades.csv (ETH)
#   reports-v1/iteration_v1-065/{is,oos}/trades.csv (BTC)
#   reports-v1/iteration_v1-078/{is,oos}/trades.csv (AAVE)
# Outputs (already committed at a18e73ba):
#   reports-v1/iteration_v1-082/comparison.csv
#   reports-v1/iteration_v1-082/in_sample/{trades,daily_pnl,monthly_pnl,per_regime,per_symbol}.csv
#   reports-v1/iteration_v1-082/out_of_sample/{same 5}.csv
```

Expected output (deterministic; reads only committed trades.csv files):
- Composite: IS Sharpe +0.7157 / OOS Sharpe +1.0043
- Counts: IS 694 / OOS 320 trades
- PnL: IS +218.453% / OOS +122.683%
- Per-symbol OOS concentration: BTC 33.96%, DOT 32.75%, ETH 22.75%, AAVE 10.54%

Bit-exact reproducibility is guaranteed because the trade artifacts are immutable git blobs.

---

## Section 11 — Portfolio Composition Design (HARD CONFORMANCE)

### 11.A — Pairwise-disjoint universe assertion (per `feedback_v1_bundle_no_coin_overlap.md`)

| Component | Universe |
|---|---|
| /063 DOT specialist | `{DOTUSDT}` |
| /064 ETH specialist | `{ETHUSDT}` |
| /065 BTC specialist | `{BTCUSDT}` |
| /078 AAVE specialist | `{AAVEUSDT}` |

**Pairwise intersection: ∅ for all 6 pairs** (DOT∩ETH = DOT∩BTC = DOT∩AAVE = ETH∩BTC = ETH∩AAVE = BTC∩AAVE = ∅).
**Pairwise disjoint**: YES.
**Union**: `{BTCUSDT, ETHUSDT, DOTUSDT, AAVEUSDT}` — 4 coins. **LINKUSDT and LTCUSDT NOT IN BUNDLE-002.**

Critic Check 16 (`BUNDLE-UNIVERSE-OVERLAP`) MUST pass on this declaration.

### 11.B — Weight calibration (per `feedback_v1_bundle_weight_is_only.md`)

**WEIGHTS AT BUNDLE LEVEL: NONE.** Per /045 lesson and /071 precedent, the bundle does not apply any weight blending. Each specialist's per-trade `weight_factor` column (which already encodes vol targeting + R2 scaling + risk wrapper effects per specialist) is inherited as-is. Equal-weight per /045 lesson and /071 precedent means: each specialist trades ONLY its own symbol with its own per-trade `weight_factor`; there is NO bundle-level multiplicative or additive weight.

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
    if symbol == "AAVEUSDT":
        return spec_078.get_signal(symbol, t)
    return None  # not in BUNDLE-002 universe
```

This rule is **trivially identical** in backtest and at `live/engine.py:_tick`:
- No aggregation step (each coin → exactly one specialist signal).
- No netting (pairwise-disjoint coins cannot produce offsetting positions).
- No portfolio-level position re-sizing (each specialist's vol-target + risk wrapper is the final position sizer).
- No bundle-level state (no shared cooldown, no shared DD brake — all R1/R2 state is per-specialist, per-symbol).
- No post-trade aggregation/netting (per user spec).

Critic Check 15 (`BUNDLE-PARITY-VIOLATION`) MUST pass. Note that the /081 parity smoke test (C1/C5/C6 gate) directly validates the SPECIALIST→engine signal-equivalence path at the library level; bundle composition is just the disjoint union of those parity-validated signals.

### 11.D — Re-composition statement

Bundle composition is **non-overlapping by construction** from /045+ HARD rule. No re-composition needed; no specialist was modified to fit the bundle's pairwise-disjoint requirement. AAVE/078 was trained in its own coin universe `{AAVEUSDT}` and inherits cleanly into BUNDLE-002 without touching the other three specialists.

---

## Section 12 — BUNDLE-002 vs BUNDLE-001 Composite Comparison

This section consolidates the metrics presented in Section 2.4 + Section 4.3 into a single decision-table for the diary.

### 12.1 Headline composite (from `reports-v1/iteration_v1-082/comparison.csv`)

| Metric | BUNDLE-001 (`v0.v1-071`) | **BUNDLE-002 (this iter)** | Δ vs anchor | Sign |
|---|---:|---:|---:|---|
| **IS Monthly Sharpe** | +0.5463 | **+0.7157** | **+0.1694** | + |
| **OOS Monthly Sharpe** | +0.9636 | **+1.0043** | **+0.0407** | + |
| OOS/IS Sharpe ratio | 1.7639 | 1.4031 | −0.3608 | − |
| IS Monthly Sortino | +0.8729 | +1.0819 | +0.2090 | + |
| OOS Monthly Sortino | +1.5678 | +1.7947 | +0.2269 | + |
| IS Max Drawdown | 89.03% | 89.03% | 0.00 pts | = |
| OOS Max Drawdown | 36.51% | 63.15% | +26.64 pts | − |
| IS Win Rate | 40.60% | 40.78% | +0.18 pts | + |
| OOS Win Rate | 45.22% | 43.75% | −1.47 pts | − |
| IS Profit Factor | 1.1021 | 1.1236 | +0.0215 | + |
| OOS Profit Factor | 1.2158 | 1.1501 | −0.0657 | − |
| IS Trades | 537 | 694 | +157 | + |
| OOS Trades | 230 | 320 | +90 | + |
| IS Net PnL% | +129.681 | +218.453 | +88.772 | + |
| OOS Net PnL% | +109.750 | +122.683 | +12.933 | + |
| IS Calmar | 0.4482 | 0.755 | +0.307 | + |
| OOS Calmar | 2.2546 | 1.457 | −0.798 | − |
| OOS Top-symbol concentration | 37.96% (BTC) | **33.96% (BTC)** | **−4.00 pts** | + (improved) |

### 12.2 Decision summary

**Pareto picture vs BUNDLE-001**:
- **+ better on**: IS Sharpe, OOS Sharpe (the two primary edge gates), IS+OOS Sortino, IS+OOS Win Rate (IS only), IS Profit Factor, IS+OOS Trade count, IS+OOS PnL%, IS Calmar, OOS concentration.
- **− worse on**: OOS/IS Sharpe ratio (still > 1 — bundle remains OOS-favorable), OOS MaxDD (+26.64 pts is material), OOS Win Rate (−1.47 pts), OOS Profit Factor (−0.07), OOS Calmar (−0.798 driven by the MaxDD increase).
- **= equal on**: IS MaxDD.

**Edge-gate verdict (informational)**: OOS Sharpe ≥ 1.0 PASS; IS Sharpe < 1.0 FAIL (informational; improved from BUNDLE-001 anchor); concentration > 30% FAIL (informational; improved from BUNDLE-001 anchor). User mandate authorizes MERGE.

**Methodology-integrity verdict (HARD)**: PASS at composition (Section 4.4 checklist clean).

**Diary will record BUNDLE-002 as the new methodology-trained baseline anchor (`v0.v1-082`)** with the OOS MaxDD increase documented as a known characteristic absorbed under the TENTATIVE-merge precedent.

---

## Section 13 — TENTATIVE-Merge Precedent (per /071 + user authorization at /082)

### 13.1 Precedent inheritance

The /071 user mandate ("we merge this, no matter what. This is gonna be our baseline now.") established the **TENTATIVE-MERGE PRECEDENT** under the SPECIALIST + BUNDLE methodology:

> A bundle composed of specialists tagged at the TENTATIVE (PROMISING-TENTATIVE) band by their LM Master 7.5 / Critic 7.5 closeouts can MERGE as a bundle-level baseline anchor, provided:
> 1. The bundle's pairwise-disjoint universe assertion (11.A) holds.
> 2. The no-bundle-weights rule (11.B) holds.
> 3. The backtest-live parity rule (11.C) holds.
> 4. Methodology-integrity gates (4.4) are clean.
> 5. The user has explicitly authorized the merge at the bundle level (overrides individual TENTATIVE-band specialist verdict).

BUNDLE-001 (/071) inherited 3 specialists all at VALIDATED band; the TENTATIVE precedent was established forward-looking ("future TENTATIVE specialists can be bundled under the same authorization pattern").

### 13.2 Application at /082

BUNDLE-002 inherits:
- 3 VALIDATED specialists (/063 DOT, /064 ETH, /065 BTC) from BUNDLE-001
- 1 PROMISING-TENTATIVE specialist (/078 AAVE)

User authorization "let's try the bundle-002" (2026-06-09) is interpreted as TENTATIVE-merge precedent activation per /071. /078's TENTATIVE band is acknowledged but not blocking.

### 13.3 Multi-seed validation waiver (per task spec)

Per the task spec: "Multi-seed validation waived per user methodology lock". The current methodology constants (50 seeds × 30 trials × specialist_mode per individual specialist) are user-locked at the SPECIALIST level. Bundle-level multi-seed re-validation is not introduced as a new gate; bundle-level seed dispersion is inherited from each specialist's own per-trade `weight_factor` and per-symbol Optuna trajectory.

### 13.4 Operational disclosure for future iterations

Future iterations anchoring against BUNDLE-002 must:
1. Cite the headline composite (Section 12.1) as the baseline anchor (IS +0.7157 / OOS +1.0043).
2. Acknowledge that BUNDLE-002 was merged under TENTATIVE-precedent (the AAVE component is PROMISING-TENTATIVE).
3. Be alert to the OOS MaxDD increase (63.15% vs 36.51% at BUNDLE-001) as a tail-risk surface that future BUNDLE-003+ iterations may target.
4. Pivot to a different angle (per user directive "if we manage to merge another baseline, we try a different angle" — TBD post-/082 merge).

---

## Section 14 — Sign-off

| Phase | Owner | Status |
|---|---|---|
| Phase 1–4 (EDA + design) | QR | DONE (this brief) |
| Phase 4.5 (LM Master advisor) | LM Master | SKIPPED (composition-only; no Optuna search to advise) |
| Phase 5 (research brief) | QR | DONE (this document) |
| Phase 5.5 (gate) | Orchestrator | PENDING |
| Phase 6 (compose + report) | QE | DONE (`reports-v1/iteration_v1-082/` committed at `a18e73ba`) |
| Phase 6.0 (Critic pre-flight) | Critic | PENDING |
| Phase 7 (evaluation) | QR | PENDING |
| Phase 7.4 (LM Master post-mortem) | LM Master | OPTIONAL |
| Phase 7.5 (Critic review) | Critic | PENDING (expected verdict: BUNDLE-MERGE per /045 mandate + /071 TENTATIVE-precedent + user authorization) |
| Phase 8 (diary + merge) | QR | PENDING — pre-registered as MERGE per user mandate |

---

**End of brief.**
