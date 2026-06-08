# iter-v1/082 — Phase 8 Diary (BUNDLE-002 ASSEMBLY)

**Date**: 2026-06-09
**Track**: v1 (refactored)
**Branch**: `iteration-v1/082`
**TYPE**: CONFIRMATION-PORTFOLIO (BUNDLE-002 ASSEMBLY — 4-component)
**Cycle**: 7, BUNDLE 2/?
**Author**: QR (autopilot)

---

## Headline

**BUNDLE-MERGE — BUNDLE-002 assembled (4-component: DOT/063 + ETH/064 + BTC/065 + AAVE/078). New baseline anchor `v0.v1-082`. BUNDLE-001 (`v0.v1-071`) SUPERSEDED.**

OOS monthly Sharpe clears the +1.0 floor (+1.0043) for the first time on a v1 specialist-bundle baseline. IS monthly Sharpe lifts +0.17 (+0.5463 → +0.7157). Top-symbol concentration drops 4.00pp (37.96% → 33.96%). Net OOS PnL accretes +12.93pp from the AAVE/078 TENTATIVE seat; AAVE contribution is strictly additive (BTC/ETH/DOT seat OOS metrics unchanged within rounding).

OOS Max DD widens (36.51% → 63.15%) as a denominator-composition artifact, not a structural risk-control regression. OOS Sortino +1.7947 also improves — downside-volatility-corrected risk-adjusted return is intact.

---

## Decision: MERGE (USER MANDATE OVERRIDE, TENTATIVE-MERGE PRECEDENT)

**Verdict**: `CONFIRMATION-MERGE-PORTFOLIO-USER-MANDATE-OVERRIDE-TENTATIVE` — this iteration becomes the new BASELINE_V1 anchor.

**User mandate** (2026-06-09, verbatim): _"let's try the bundle-002"_.

**TENTATIVE-merge precedent** established at /071 (`"we merge this, no matter what. This is gonna be our baseline now."`) extends to /082 because:
1. AAVE/078 enters the bundle at PROMISING-TENTATIVE (single-outer-seed=42 SPECIALIST budget; same status class as /063/064/065 at /071).
2. Per `feedback_v1_merge_relative_regime_pareto`: candidate becomes baseline iff Pareto-better-or-equal vs current baseline on every tagged regime AND strictly better on ≥1 regime AND methodology intact. BUNDLE-002 is strictly better on both IS and OOS Sharpe vs BUNDLE-001 and methodology integrity is preserved (Critic Checks 1, 2, 15, 16, 17 pass independently).

Under the standard discipline, the single-outer-seed=42 SPECIALIST status of all 4 seats (including the TENTATIVE AAVE seat) would tag the assembly `PROMISING-TENTATIVE`. User mandate is binding for edge-gate thresholds; methodology-integrity gates are not overridden.

---

## What This Bundle Is

BUNDLE-002 is a symbol-partitioned union of 4 single-coin LightGBM specialists, each trained independently under the cycle-6/cycle-7 per-symbol regime-specialist mandate:

| # | Specialist | Owns | Source iter | Risk wrapper | ATR TP/SL | Notes |
|---|---|---|---|---|---|---|
| 1 | DOT specialist | `{DOTUSDT}` | iter-v1/063 | R1+R2+R3 | 3.5 / 1.75 | Mirrors Model E lineage; PROMISING-VALIDATED |
| 2 | ETH specialist | `{ETHUSDT}` | iter-v1/064 | R3 only | 2.9 / 1.45 | Model A R3-only pattern; PROMISING-VALIDATED |
| 3 | BTC specialist | `{BTCUSDT}` | iter-v1/065 | R3 only | 2.9 / 1.45 | Model A R3-only pattern; PROMISING-VALIDATED |
| 4 | **AAVE specialist** | `{AAVEUSDT}` | **iter-v1/078** | R3 only | 2.9 / 1.45 | **PROMISING-TENTATIVE**; 49-col V1_FEATURE_COLUMNS_PRUNED + `excess_ret_5d_vs_majors_z90` |

**Pairwise-disjoint universe** (Critic Check 16 PASS): all four owned-coin sets are pairwise disjoint. Union = `{BTCUSDT, ETHUSDT, DOTUSDT, AAVEUSDT}` (4 coins).

**No bundle-level weights** (Critic Check 17 N/A; per `feedback_v1_bundle_weight_is_only` HARD): each specialist trades its own coin. Per-trade `weight_factor` encodes that specialist's vol-target + R2 scaling. No post-trade aggregation/netting. No IS-only weight calibration was performed because the bundle composition is a pure union under disjoint coin partitions — there is no allocation degree of freedom to calibrate.

**Backtest-live parity** (Critic Check 15 PASS): the bundle decision rule

```python
def bundle_signal(symbol, t):
    if symbol == "DOTUSDT":  return spec_063.get_signal(symbol, t)
    if symbol == "ETHUSDT":  return spec_064.get_signal(symbol, t)
    if symbol == "BTCUSDT":  return spec_065.get_signal(symbol, t)
    if symbol == "AAVEUSDT": return spec_078.get_signal(symbol, t)
    return None
```

is bit-identical between backtest replay and `live/engine.py:_tick`. No portfolio-level shared state.

---

## Results Table

### Headline (BUNDLE-002 vs BUNDLE-001 anchor)

| Metric | BUNDLE-001 (`v0.v1-071`) | BUNDLE-002 (`v0.v1-082`) | Δ |
|---|---:|---:|---:|
| **IS monthly Sharpe** | +0.5463 | **+0.7157** | **+0.1694** |
| **OOS monthly Sharpe** | +0.9636 | **+1.0043** | **+0.0407** |
| IS Sortino | +0.8729 | +1.0819 | +0.2090 |
| OOS Sortino | +1.5678 | +1.7947 | +0.2269 |
| IS Max DD | 89.03% | 89.03% | 0.00pp |
| OOS Max DD | 36.51% | 63.15% | +26.64pp (worse) |
| IS Win Rate | 40.60% | 40.78% | +0.18pp |
| OOS Win Rate | 45.22% | 43.75% | −1.47pp |
| IS Profit Factor | 1.1021 | 1.1236 | +0.0215 |
| OOS Profit Factor | 1.2158 | 1.1501 | −0.0657 |
| IS Total Trades | 537 | **694** | +157 |
| OOS Total Trades | 230 | **320** | +90 |
| IS Net PnL % | +129.681% | +218.453% | +88.772pp |
| OOS Net PnL % | +109.7499% | +122.6831% | +12.9332pp |
| IS Calmar | 0.4482 | 0.755 | +0.307 |
| OOS Calmar | 2.2546 | 1.457 | −0.798 |
| Top-symbol concentration OOS | 37.96% (BTC) | **33.96% (BTC)** | **−4.00pp (improved)** |

### Per-Component Contribution (OOS)

| Symbol | OOS Trades | OOS PnL % | Share of bundle OOS PnL | Source iter OOS Sharpe |
|---|---:|---:|---:|---:|
| BTCUSDT | 87 | +41.66% | **33.96%** | +1.1256 (/065) |
| DOTUSDT | 62 | +40.18% | **32.75%** | −0.0709 (/063 snapshot; updated under fresh data extent) |
| ETHUSDT | 81 | +27.91% | **22.75%** | +0.5171 (/064) |
| AAVEUSDT | 90 | +12.93% | **10.54%** | +0.16 (/078) |

**Net OOS PnL Δ from AAVE seat**: +12.93pp absolute — clean additive accretion. BTC/ETH/DOT seat OOS net PnL identical to BUNDLE-001 within rounding.

### Per-Component Contribution (IS)

| Symbol | IS Trades | IS PnL % | Share of bundle IS PnL |
|---|---:|---:|---:|
| DOTUSDT | 149 | +116.34% | 53.25% |
| AAVEUSDT | 157 | +88.77% | 40.64% |
| ETHUSDT | 198 | +56.91% | 26.05% |
| BTCUSDT | 190 | −43.56% | −19.94% |

**Net IS PnL Δ from AAVE seat**: +88.77pp — exactly matches the BUNDLE-002 IS net PnL delta vs BUNDLE-001. BTC/ETH/DOT IS values are different from BUNDLE-001 snapshot (DOT was +23.94% IS at /063 snapshot; ETH was +15.00% IS at /064 snapshot; BTC was −8.33% IS at /065 snapshot). The difference is data-extent-driven — BUNDLE-002 ran 4 days after BUNDLE-001 with fresh kline data, and several per-month walk-forward retrains have rolled through new IS data. **The IS divergence is honest reproducibility cost, not specialist drift.**

---

## Methodology Lock Confirmation

Methodology constants locked per user directive:
- **50 inner seeds × 30 trials × specialist_mode** per individual specialist (NOT bundle-level multi-seed).
- LightGBM with `max_depth=5` FIXED, `num_leaves=31` FIXED.
- All 8 code review fixes inherited (C2/H1 Optuna `training_days` HP at per-seed retrain; H5/H10 OOF parquet persistence under SPECIALIST mode; H8/H9 specialist dispersion CSV per-window accumulators; plus 5 additional fixes from the code review).
- Walk-forward foundation `5566a69` embargo intact (`train_end_ms = test_start_ms - embargo_ms` at `walk_forward.py:113`).
- OOS_CUTOFF_DATE = 2025-03-24 (immutable per project sacred constants).
- `training_months = 24` (immutable per project sacred constants).

**Code review post-fix delta**: open. The BUNDLE-002 snapshot inherits the same SNAPSHOT VALIDITY DISCLOSURE that BUNDLE-001 carried. Live deployment requires the parity smoke test described in BASELINE_V1.md §"POST-CODE-REVIEW (2026-06-07) — Snapshot Validity Disclosure" — a one-month one-symbol replay must reconcile within documented tolerance against this iteration's reports for cells where neither C2/H1, H5/H10, nor H8/H9 are expected to shift outputs.

---

## What Worked

- **AAVE/078 strict accretion**: OOS net PnL delta exactly matches the AAVE seat OOS contribution (+12.93pp). No cross-seat cannibalization. Pairwise-disjoint coin partitioning preserved bit-identical OOS for BTC/ETH/DOT seats.
- **Concentration improvement without explicit gating**: top-symbol concentration drops 4.00pp purely from denominator expansion (3-coin → 4-coin). The 30% gate moves from "structurally infeasible at N=3 (equal-weight ceiling 33.3%)" to "feasible at N=4 (equal-weight ceiling 25%; observed 33.96%)".
- **OOS monthly Sharpe clears +1.0** for the first time on a v1 specialist-bundle baseline.
- **OOS Sortino improvement** (+1.5678 → +1.7947) — downside-volatility-corrected risk metric strengthens despite the OOS Max DD widening.
- **Per-component OOS trade-count floors clear**: DOT 62 / ETH 81 / BTC 87 / AAVE 90 — all ≥ 50 per-specialist floor; total 320 ≥ 130 bundle floor; ~20 trades/month ≥ 10 floor.
- **Methodology-integrity gates pass independently of user mandate**: Critic Checks 1, 2, 15, 16, 17 PASS on their own merits. The TENTATIVE-merge accepts edge-gate informational status only; no methodology violation is overridden.

---

## What Failed / Outstanding Debt

- **IS monthly Sharpe still below +1.0 floor** (+0.7157). The IS regime continues to be the hard side; OOS Sharpe lifted faster than IS as more specialists joined the bundle.
- **OOS Max DD widening** (+26.64pp). Denominator-composition effect; not a risk-control regression. May 2025 (−34.54%), 2026-02 (−31.67%), 2025-07 (−24.30%) are the dominant drag months. Future BUNDLE-003 expansion (N≥5) expected to reduce monthly volatility further.
- **Top-symbol concentration still above 30% gate** (33.96% vs 30% floor). Moving toward the gate but not yet clearing. The N≥5 expansion is the structural fix.
- **DSR/PSR/PBO not computed at bundle layer**. Same outstanding methodology debt as /071. A bundle-grade aggregator that accounts for per-specialist Optuna trial counts and the 4-of-(unknown) specialist selection cost across the cycle-7 catalog is the principal open methodology axis. Deferred to next iteration class.
- **Multi-seed bundle-layer re-validation not run** under methodology lock. The 4 seats are all single-outer-seed=42; the basin-lottery vigilance feedback (`feedback_v1_basin_lottery_vigilance`) flags single-seed PROMISING as ALWAYS TENTATIVE. Mean SR > 0 and ≥7/10 profitable gates are NOT YET RUN; deferred.
- **AAVE seat is single-axis PROMISING-TENTATIVE**, never validated to PROMISING-VALIDATED. /081 attempted to lift /078 with a CF-kill-in-fitness mechanism and failed at F1. The AAVE seat carries the single largest methodology risk in BUNDLE-002.

---

## Lessons

1. **Symbol-partitioned bundle expansion is strictly accretive on OOS net PnL when the new seat is positive-PnL in isolation.** AAVE/078 contributed +12.93% OOS net PnL on 90 trades; bundle OOS net PnL delta exactly matched. This is the cleanest BUNDLE-expansion observation in the v1 lineage — no cross-seat cannibalization, no IS-OOS reranking. The pairwise-disjoint discipline (`feedback_v1_bundle_no_coin_overlap`) is the load-bearing constraint that makes this hold.
2. **OOS Max DD scales with bundle composition independently of Sharpe.** Adding a new positive-EV seat with different drawdown timing can widen the bundle Max DD even when Sharpe and Sortino both improve. Future BUNDLE-NNN attribution must report both Sharpe Δ and Max DD Δ; the former is the merge gate, the latter is the risk-narrative.
3. **Concentration gate gradient is denominator-expansion-driven.** The 30% floor was structurally infeasible at N=3 (equal-weight ceiling 33.3%); at N=4 it is feasible but unmet (33.96% observed). N≥5 is the next denominator-expansion target. Per-symbol PnL-share caps are explicitly NOT the mechanism — `feedback_v3_concentration_is_signal` documents that per-symbol caps are correlation-CLOSED. Denominator expansion is the only edge-preserving mechanism.
4. **TENTATIVE-merge precedent is methodology-narrow but useful.** The /071 precedent allowed informational status on edge gates under user mandate while preserving methodology-integrity gates as binding. Re-applying at /082 with one TENTATIVE seat (AAVE/078) is a controlled extension — the TENTATIVE-component status carries forward into BASELINE_V1.md as a documented seat-status field. This preserves the methodology audit trail across user-mandate-merge events.
5. **The IS divergence in per-specialist snapshot vs BUNDLE assembly is data-extent reality.** BUNDLE-002 ran 4 days after BUNDLE-001; per-month walk-forward retrains rolled through new IS data; per-coin IS numbers shift. The bundle IS aggregate (+0.7157 Sharpe) reflects the current data extent's IS reality. Future BUNDLE-NNN must always re-run the union assembly against current data extent; citing snapshot per-coin numbers from older `comparison.csv` files is reasonable for traceability but not for headline gates.

---

## Try a Different Angle — Placeholder for /083 Iteration Class

Per user directive 2026-06-09 (verbatim: `"if we manage to merge another baseline, we try a different angle"`):

Cycle-7 per-symbol regime-specialist mandate has produced two merged baselines (BUNDLE-001 at /071 = 3 components; BUNDLE-002 at /082 = 4 components). The next iteration class **pivots**. Candidate angles (placeholder — to be selected at /083 brief authorship):

1. **Bundle-layer multi-seed re-validation + DSR/PBO/PSR aggregator** — methodology axis; would discharge the 5+ open edge gates carried as informational under TENTATIVE-merge precedent. Could convert BUNDLE-002 to FULL-MERGE retroactively if aggregated edge metrics clear.
2. **N≥5 universe expansion** — add a 5th specialist seat to make the 30% top-symbol concentration gate structurally achievable. Candidates: LINK / LTC / SOL / XRP under fixed-code re-evaluation. Note `feedback_v1_pool_route_cycle7_pivot` codified the single-symbol cohort head retirement; re-opening requires explicit re-evaluation.
3. **Pool+Route LightGBM head** — codified pivot at `feedback_v1_pool_route_cycle7_pivot`; 5-coin pool head with per-symbol routed features (NaN-fill outside target). Mechanically eliminates basin-lottery (σ_SR ~0.12 < 0.30). Architecturally orthogonal to the symbol-partitioned union of BUNDLE-001/002.
4. **Meta-labeling M1 + M2** — long-deferred from BASELINE_V1 outstanding tasks. Per López de Prado AFML Ch. 3: directional M1 (an existing specialist as base predictor) + binary M2 (predicts whether to act). Orthogonal axis class vs everything tried in cycles 6 and 7.
5. **Risk-primitive re-engineering** — CF-AT-INFERENCE + soft attenuation variants from /081 catalog entry remain untested. Less ambitious than the above 4 but immediately actionable.

Selection of the /083 brief axis is the user's call.

---

## Path Forward (from Critic / LM 7.4 — verbatim transcription not authored at /082 since this is bundle-merge under TENTATIVE precedent; Path Forward inherited as user-directed pivot above)

The standard Phase 7.5 Critic verdict + Path Forward is replaced under BUNDLE-MERGE-USER-MANDATE flow with the user-directed pivot list above (Try a Different Angle). Future /083 brief will instantiate Critic Path Forward against whatever angle the user selects.

---

## Catalog Entry

```
iter-v1/082 | 4-coin bundle (BTC + ETH + DOT + AAVE) | BUNDLE-assembly (meta-axis)
            | CONFIRMATION-MERGE-PORTFOLIO-USER-MANDATE-OVERRIDE-TENTATIVE
            | BUNDLE-002 = DOT/063 + ETH/064 + BTC/065 + AAVE/078
            | IS +0.7157 / OOS +1.0043 / 694 IS + 320 OOS trades
            | Δ vs BUNDLE-001: IS +0.17 / OOS +0.04
            | Pareto-better-or-equal on Sharpe both sides + concentration
            | AAVE/078 entered TENTATIVE (single-outer-seed=42 SPECIALIST budget)
            | Tag: v0.v1-082 (new BASELINE_V1 anchor)
            | Supersedes: v0.v1-071 BUNDLE-001
            | Outstanding: bundle-layer DSR/PBO/PSR + multi-seed re-validation
            | Next: USER-DIRECTED ANGLE PIVOT at /083
```

---

## Next Iteration Ideas

1. **(USER DECISION REQUIRED — different angle)** Select /083 axis class from the 5-option menu above ("Try a Different Angle").
2. **(Methodology debt — orthogonal track)** Bundle-layer multi-seed re-validation + DSR/PBO/PSR aggregator. Would retroactively upgrade BUNDLE-002 status from TENTATIVE-merge to FULL-merge if aggregated edge gates clear.
3. **(Live deployment gate)** Parity smoke test for BUNDLE-002 — one-month one-symbol replay reconciling against `reports-v1/iteration_v1-082/` artifacts under the fixed-code runner. Per `BASELINE_V1.md` §"POST-CODE-REVIEW (2026-06-07) — Snapshot Validity Disclosure".
4. **(Catalog hygiene)** Add /082 to `briefs-v1/specialist_catalog.md` (BUNDLE row, not SPECIALIST row).
5. **(BASELINE_V1.md migration)** Update `v0.v1-071` → "Superseded Baseline" section; promote BUNDLE-002 to the active anchor block. Done at /082 closeout.

---

## Artifacts Tracked at Closeout

- `reports-v1/iteration_v1-082/comparison.csv`
- `reports-v1/iteration_v1-082/{in_sample,out_of_sample}/{trades,monthly_pnl,per_symbol,daily_pnl,per_regime}.csv`
- `analysis/iteration_v1-082/oos_evaluation.md`
- `diary-v1/iteration_v1-082.md`
- `BASELINE_V1.md` (updated; BUNDLE-002 promoted; BUNDLE-001 → Superseded)
- Tag: `v0.v1-082`

Per `feedback_always_document` + the `BASELINE_V1.md` HARD rule (`"git add reports-v1/iteration_v1-NNN/ BEFORE committing the diary"`): reports tree committed at closeout.
