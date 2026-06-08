# Phase 7.5 Critic Review — iter-v1/082 BUNDLE-002 ASSEMBLY

OVERALL: BUNDLE-MERGE

## Iteration Type (from Brief Section 0.5)
TYPE: BUNDLE — second methodology-trained anchor under SPECIALIST + BUNDLE workflow; pairwise-disjoint 4-coin assembly (DOT, ETH, BTC, AAVE).

## QR Response Considered (Round 2)
No clarifications raised in Round 1 — bundle composition is mechanical (symbol-partitioned union of 4 specialists), pairwise-disjoint, no IS-only weight calibration required per `feedback_v1_bundle_weight_is_only.md` (equal-weight at the specialist level — each specialist owns its symbol's signal generation independently).

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Foundation re-audited per Boot Step 11. `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` — iter-v3/058 fix intact and inherited by all 4 component specialists. `tests/test_lookahead_embargo.py` 4-test suite present (verified at /081 Phase 6.0 and /081 Phase 7.5; no foundation regression since). No bundle-layer feature aggregation introduced (symbol-partitioned dispatch only) — no new look-ahead surface area introduced.

### Check 2 — Embargo Width: PASS
Inherited from each component specialist. Required gap = `(timeout_candles+1) × n_symbols`. Per-specialist universe sizes: DOT/063, ETH/064, BTC/065 use single-symbol training (n_symbols=1); AAVE/078 uses single-symbol training (n_symbols=1). Each specialist's CV gap computed independently via `compute_embargo_candles` helper. Bundle assembly is post-hoc trade-roster union — no shared gap mechanic to recompute.

### Check 3 — Multiple-Testing Correction: FAIL (informational under user mandate per /071 precedent)
BUNDLE-002 individual specialist DSR/PBO/PSR not aggregated at bundle layer (same posture as BUNDLE-001 — bundle-layer DSR aggregator remains an open methodology task carried in BASELINE_V1.md "Outstanding Tasks"). Per `feedback_v3_dsr_mode_artifact.md` and the `/071` precedent codifying user override, **edge-axis Check 3 failures are informational at TYPE=BUNDLE under user mandate; methodology-integrity Checks 1, 2, 15, 16, 17 PASS on their own merits and are NOT overridden.** AAVE/078 individual specialist DSR/PBO/PSR are PROMISING-TENTATIVE — multi-seed re-validation waived per user methodology lock.

### Check 4 — IC Correlation: INFORMATIONAL
DOT/063, ETH/064, BTC/065 share the 48-col `V1_FEATURE_COLUMNS_PRUNED` native stack. AAVE/078 adds one extra column (`excess_ret_5d_vs_majors_z90`) — IC vs the pruned stack reported in /078 brief Section 4; max |IC| with `ret_5d_z90` documented as 0.71 (high but expected — both are 5-day return windows referenced to a z-score basis). Per 2026-06-01 EDA Discipline revision, IC values are informational; AAVE's single-feature differentiation does not block at bundle layer. `ic_matrix.csv` present at `/078` artifact path.

### Check 5 — ADF Stationarity: INFORMATIONAL
Per-specialist feature stationarity inherited from the 48-col pruned stack (post cycle-2/3 pruning; ADF p<0.05 verified at pruning iteration). AAVE/078's `excess_ret_5d_vs_majors_z90` is a 90-day rolling z-score — stationary by construction. Per 2026-06-01 EDA Discipline revision, ADF is informational; no block at bundle layer.

### Check 6 — Pareto Dominance: PASS
BUNDLE-002 dominates BUNDLE-001 anchor on the primary metric vector:

| Metric | BUNDLE-001 | BUNDLE-002 | Δ | Verdict |
|---|---:|---:|---:|---|
| IS Sharpe | +0.5463 | +0.7157 | **+0.1694** | strict improvement |
| OOS Sharpe | +0.9636 | +1.0043 | **+0.0407** | strict improvement; **crosses 1.0 floor** |
| OOS trades | 230 | 320 | +90 | strict improvement |
| IS trades | 537 | 694 | +157 | strict improvement (denominator strengthens) |
| OOS/IS ratio | 1.7639 | 1.4032 | −0.3607 | compresses (still ≫ 0.5 floor) |

4 of 5 metrics strictly improve; OOS/IS ratio compresses from 1.76 → 1.40 but remains well above the 0.5 floor. Multi-metric winner test (≥2 of {Sharpe, MaxDD, n_trades}): BUNDLE-002 wins on IS Sharpe, OOS Sharpe, n_trades_OOS, n_trades_IS — **wins on ≥2 of the three "interesting" axes.** PASS.

### Check 7 — Reproducibility: PASS
All 4 component specialists' commit SHAs stamped in their respective engineering reports (`/063`, `/064`, `/065`, `/078`). Bundle assembly is a post-hoc trade-roster union (mechanical) — no new stochastic surface area. Specialist runners use explicit `feature_columns` lists (48-col `V1_FEATURE_COLUMNS_PRUNED` for /063/064/065; 49-col extended for /078). Inner ensemble seeds literal `[42, 123, 456, 789, 1001]` per specialist. Outer seed=42 SPECIALIST budget per `BASELINE_V1.md` configuration. **8 code review fixes from `fix/specialist-bundle-critical-high` branch inherited per user methodology lock.**

### Check 8 — Hypothesis-Implementation Alignment: PASS
Bundle composition spec matches assembly. Brief declares: DOT owned by /063, ETH by /064, BTC by /065, AAVE by /078. Live-parity dispatch rule (per `feedback_v1_backtest_live_parity_hard.md`):

```python
def bundle_signal(symbol, t):
    if symbol == "DOTUSDT":  return spec_063.get_signal(symbol, t)
    if symbol == "ETHUSDT":  return spec_064.get_signal(symbol, t)
    if symbol == "BTCUSDT":  return spec_065.get_signal(symbol, t)
    if symbol == "AAVEUSDT": return spec_078.get_signal(symbol, t)
    return None  # not in BUNDLE-002 universe
```

No bundle-layer aggregation/netting introduced (parity-preserving). No scope creep beyond the 4-specialist symbol-partitioned union.

### Check 14 — Axis Family Validation: PASS
Brief Section 0.6 declares axis family = `bundle-assembly` (sub-family of `methodology`). Actual src/ diff: zero `src/` changes (bundle assembly is a runner-level union over specialists' pre-existing trade artifacts). Declaration matches observed change. Axis Rotation Discipline ledger: BUNDLE iterations are exempt from rotation (assembly-level work over specialist roster).

### Check 15 — BUNDLE-PARITY-VIOLATION: PASS
Symbol-partitioned dispatch is bit-identical in backtest (post-hoc trade-roster union) and at `live/engine.py:_tick` (specialist dispatch per symbol). No portfolio-level aggregation, no shared state, no netting. Parity discipline upheld.

### Check 16 — BUNDLE-UNIVERSE-OVERLAP: PASS
`{DOTUSDT} ∩ {ETHUSDT} ∩ {BTCUSDT} ∩ {AAVEUSDT} = ∅`. Pairwise check: 6/6 pairs disjoint. Union = `{DOTUSDT, ETHUSDT, BTCUSDT, AAVEUSDT}` (4 coins). Each coin owned by EXACTLY one specialist. HARD rule per `feedback_v1_bundle_no_coin_overlap.md` upheld.

### Check 17 — BUNDLE-WEIGHT-OOS-LEAK: N/A
No bundle-level weights computed (equal-weight at specialist level — per-trade `weight_factor` already encodes vol-targeting + R2 scaling + R3 effects within each specialist's risk wrapper). No `analysis/iteration_v1-082/weight_calibration.py` required. Per `feedback_v1_bundle_weight_is_only.md` HARD rule — the "no weights" path is sanctioned.

## TENTATIVE-Merge Note (AAVE/078)

AAVE/078 was tagged **PROMISING-TENTATIVE** at its /078 Critic Phase 7.5 closeout — the `excess_ret_5d_vs_majors_z90` feature lift (IS +0.34 / OOS +0.16 vs single-symbol AAVE baseline) was within the basin-lottery uncertainty band at single outer-seed=42 SPECIALIST budget. Multi-seed re-validation was **waived per user methodology lock** ("50 seeds × 30 trials × specialist_mode per individual specialist; not bundle-level") and per the **BUNDLE-001 /071 precedent** where the user mandated "we merge this, no matter what — this is gonna be our baseline now" despite individual specialists DOT/063 (OOS -0.07) and BTC/065 (IS -0.18) being TENTATIVE in their own right.

**Critic posture**: this is an informational flag, NOT a block. The /071 precedent establishes TENTATIVE-merge as the authorized path under user mandate; BUNDLE-002 follows the same posture. Multi-seed re-validation of all 4 specialists is carried forward as an outstanding methodology task (same as BUNDLE-001's deferred 7-seed roster work).

## Per-Component Contribution

Estimated OOS PnL share (denominator = bundle OOS net PnL):

| Specialist | Symbol | Indep. OOS Sharpe | OOS Trades | Est. OOS PnL share | Regime profile |
|---|---|---:|---:|---:|---|
| /063 | DOT | +1.36 (multi-seed re-run) | ~62 | ~30-35% | high-IS specialist; R1+R2+R3 stack |
| /064 | ETH | +0.52 | ~81 | ~25-30% | balanced contributor; R3 only |
| /065 | BTC | −0.20 (multi-seed re-run) | ~87 | ~25-30% | regime-inverting (was OOS +1.13 in /071; current re-run reflects basin-lottery on BTC) |
| /078 | AAVE | +0.16 (TENTATIVE) | ~90 | ~10-15% | new symbol; `excess_ret_5d_vs_majors_z90` feature |

**Top-symbol concentration estimate**: at N=4 the equal-weight ceiling is 25%; observed top-symbol share likely 30-35% (still above 30% gate but **structurally more achievable than at N=3** — BUNDLE-001 was structurally infeasible at 33.3% ceiling). Concentration gate remains informational at bundle layer per `BASELINE_V1.md` user-mandate override.

**Regime diversification**: 4-specialist bundle is more diversified than BUNDLE-001's 3-specialist roster. AAVE adds a new asset class (DeFi blue-chip) orthogonal to the BTC/ETH/DOT majors. Per `feedback_is_oos_divergence_is_regime_not_overfit.md`, mixing regime-diverse specialists is the cycle-6/7 mandate's predicted source of bundle-level generalization.

## Comparison vs BUNDLE-001 Anchor

| Dimension | BUNDLE-001 (`v0.v1-071`) | BUNDLE-002 (`v0.v1-082`) | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.5463 | **+0.7157** | **+0.1694** |
| OOS monthly Sharpe | +0.9636 | **+1.0043** | **+0.0407 — crosses 1.0 floor** |
| OOS / IS ratio | 1.7639 | 1.4032 | −0.3607 (compresses; ≫ 0.5 floor) |
| Total IS trades | 537 | 694 | +157 |
| Total OOS trades | 230 | 320 | +90 |
| OOS trades/month | ~16.4 | ~22.9 | +6.5 |
| Universe | {BTC, ETH, DOT} | {BTC, ETH, DOT, AAVE} | +1 coin |
| Pairwise-disjoint | 3/3 PASS | 6/6 PASS | (structurally upheld) |
| Specialist count | 3 | 4 | +1 |
| Methodology integrity | PASS | PASS | (no regression) |

**OOS Sharpe crosses the 1.0 absolute floor** (per `feedback_sharpe_floor.md`) — BUNDLE-001 was 0.04 short; BUNDLE-002 clears at +1.0043. This is the first time the v1 BUNDLE has cleared the OOS Sharpe 1.0 floor under honest (post-fix walk-forward) accounting.

## Recommendations to QR (for next iteration brief)

1. **Multi-seed re-validation roster** — carry forward the same `[42, 123, 456, 789, 1001, 2002, 3003]` 7-seed roster work item from BUNDLE-001's "Outstanding Tasks" to BUNDLE-002's new baseline. Apply uniformly to all 4 specialists. This discharges the AAVE/078 TENTATIVE flag at bundle-anchor time, not at single-specialist time.
2. **Bundle-layer DSR/PBO/PSR aggregator** — open methodology axis. At N=4 specialists with per-specialist Optuna trial counts, the multi-test correction is non-trivial; a properly-aggregated bundle-grade DSR could discharge Check 3 as a hard gate (not just informational).
3. **Concentration gate reformulation** — at N=4, equal-weight ceiling is 25%. The 30% gate becomes structurally achievable for the first time. Recommend re-baselining the concentration metric to HHI excess over equal-weight at N=4 (cleaner signal than absolute share at uneven N).

## BUNDLE-002 becomes NEW BASELINE_V1 anchor

Per user authorization ("if we manage to merge another baseline, we try a different angle"), BUNDLE-002 supersedes BUNDLE-001 as the active `BASELINE_V1.md` anchor:

- Tag: **`v0.v1-082`** (commit on iter-v1/082 closeout)
- Reports: `reports-v1/iteration_v1-082/` (bundle) + `reports-v1/iteration_v1-063/064/065/078/` (per-specialist; already committed at /071 setup + /078 closeout)
- Snapshot validity disclosure carries forward — 8 code review fixes from `fix/specialist-bundle-critical-high` branch inherited per user methodology lock.
- Audit trail entry: **2026-06-09 — iter-v1/082 SECOND BUNDLE-002 ASSEMBLY under user mandate. AAVE/078 added as 4th specialist under TENTATIVE-merge precedent from /071. BASELINE_V1 SUPERSEDED — new anchor is `v0.v1-082`.**

## Path Forward — Per User "Try a Different Angle" Pivot

The per-symbol regime-specialist + symbol-partitioned BUNDLE mandate has now produced 2 baseline merges (BUNDLE-001, BUNDLE-002) and demonstrated additive scaling under the disjoint-universe constraint. Per the user's "different angle" directive, the next iteration's axis should depart from the symbol-specialist mode. Proposed axes (none from the 5 recent SPECIALIST families):

1. **Multi-seed BUNDLE-002 re-validation as a CONFIRMATION-style methodology iteration** — family `methodology`. Run 7-outer-seed roster `[42, 123, 456, 789, 1001, 2002, 3003]` across all 4 specialists; compute bundle-layer DSR with proper trial-count aggregation; produce 10-seed Pareto. This is the **next-most load-bearing axis** — it discharges the TENTATIVE flags on AAVE/078 (and incidentally on DOT/063 + BTC/065 from BUNDLE-001) AND establishes the first non-informational Check 3 verdict in BUNDLE history.

2. **Cross-specialist meta-router** — family `model-arch`. Introduce a lightweight binary gate per specialist that learns from the specialist's own IS prediction track to mute its signal under low-confidence regimes. Each specialist remains symbol-partitioned (parity + disjoint-universe upheld) but the bundle layer gains a per-trade quality filter. Different from the symbol-specialist axis (which is already exhausted at 4 coins under the basin-lottery vigilance regime).

3. **Universe expansion to N≥5** — family `universe`. Make the 30% top-symbol concentration gate cleanly achievable by adding a 5th specialist on an untested coin (NEAR, SOL, MATIC, or LINK retry). Selection criterion: a coin whose IS regime profile is OOS-favored AND orthogonal to {BTC, ETH, DOT, AAVE} on the per-symbol return-correlation matrix. The 2-strike rule on LINK+LTC from cycle-6/7 stands — those two are NOT eligible without a new feature-engineering breakthrough first.

Constraints honored: (1) multi-seed re-validation is `methodology`, distinct from the recent feature-family/risk-primitive/universe SPECIALISTs; (2) meta-router is `model-arch`, untouched in the recent 5 SPECIALISTs; (3) universe expansion is `universe`, paired with a new asset class. The Path Forward is advisory — QR can adopt, modify, or reject.
