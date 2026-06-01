# iter-v1/045 — Pre-Brief Outline

**Status**: Pre-brief outline authored 2026-05-31 (post-veto of iter-v1/038 candidate). Synthesizes QR-substrate-045 + Critic adversarial pass + LM Master substrate validation. Full brief authored in Phase 5 of /045 proper; this file is the design substrate the brief draws from.

**TYPE**: `CONFIRMATION-PORTFOLIO` (first CONFIRMATION designed under new bundle discipline rules: No Coin Overlap, IS-Only Weights, Backtest-Live Parity).

**Cycle slot**: cycle-5 CONFIRMATION (under post-/044 reset). 10 EXPLORATION precedents from `briefs-v1/exploration_catalog.md` must be cited in Section 0.5.

---

## 1. Substrate Composition (Post-Synthesis Final)

Option III (Pure Cohort Federation) selected. Validated by LM Master, confirmed by QR substrate proposal, no Critic-flagged loopholes after the new rules apply.

### Components (3 — each owns disjoint coin set)

| Component | Source | Universe | Features | ATR TP/SL | R1 | R3 | IS Sharpe (daily) | IS sum PnL |
|---|---|---|---|---|---|---|---|---|
| C1 = `baseline_pool_A` | `baseline_v186` Model A | BTC + ETH | `BASELINE_FEATURE_COLUMNS` (193) | 2.9 / 1.45 | OFF | ON (70th pct) | +0.468 | +31.79 |
| C2 = `baseline_D` | `baseline_v186` Model D | LTC | `BASELINE_FEATURE_COLUMNS` (193) | 3.5 / 1.75 | ON (3, 27) | ON (70th pct) | +2.099 | +91.52 |
| C3 = `iter-v1/036` | iter-v1/036 trend-scan | LINK + DOT | /036 trend-scan feature set | per-/036 | per-/036 | per-/036 | -0.037 | -4.09 |

Models C (LINK) and E (DOT) from `baseline_v186` are EXCLUDED from /045 — their roles are now C3's responsibility under the No Coin Overlap rule.

### Universe Partition (Section 11.A pre-fill)

```
- Component C1 (baseline_pool_A): {BTCUSDT, ETHUSDT}
- Component C2 (baseline_D):       {LTCUSDT}
- Component C3 (iter-v1/036):      {LINKUSDT, DOTUSDT}
- Pairwise disjoint: YES (C1 ∩ C2 = C1 ∩ C3 = C2 ∩ C3 = {})
- Union: {BTCUSDT, ETHUSDT, LTCUSDT, LINKUSDT, DOTUSDT}
```

Coverage matches `BASELINE_V1` exactly — no coin is added or dropped at the bundle universe level; only the OWNERSHIP within the bundle is partitioned.

### Re-Composition Note (Section 11.D pre-fill)

LINK and DOT are dropped from baseline's pool components in this bundle (their cohort C and cohort E counterparts are excluded). LINK is now C3-owned; DOT is now C3-owned. The underlying `baseline_v186` Models C and E are NOT modified at the catalog level — they remain valid as standalone artifacts; only their inclusion in THIS bundle is suppressed.

---

## 2. Weight Derivation (Section 11.B pre-fill)

**Selected method**: EQUAL weights (1/3 each across C1, C2, C3).

**Rationale** (transcribed verbatim from QR substrate proposal §"Weight Derivation"):
1. C3 (/036) was admitted to the bundle because its OOS Δ vs LINK-in-pool was +1.08, not because its IS Sharpe is strong (it is ~0). IS-Sharpe-proportional would erase C3.
2. Trade-count-proportional gives C2 (LTC, highest IS edge) only 0.183 — wrong direction.
3. EQUAL minimizes researcher-degrees-of-freedom and leans on the OOS-validated baseline weighting convention.

**Required artifacts** (committed before Phase 6.0 Critic pre-flight):
- `analysis/iteration_v1-045/weight_calibration.py` — script that:
  - Loads ONLY `reports-v1/iteration_v1-186/in_sample/trades.csv` (NOT `out_of_sample/`), `reports-v1/iteration_v1-036/in_sample/trades.csv`
  - Asserts every loaded row's `close_time < OOS_CUTOFF_MS` (2025-03-24)
  - Computes and emits the EQUAL weight vector
  - Writes `bundle_weights.csv`
- `analysis/iteration_v1-045/bundle_weights.csv`:
  ```csv
  component_id,weight,derivation_method,is_window_start,is_window_end
  baseline_pool_A,0.333,equal,2021-03-24,2025-03-24
  baseline_D,0.333,equal,2021-03-24,2025-03-24
  iter-v1/036,0.333,equal,2021-03-24,2025-03-24
  ```

**Critic Check 17 will grep the script for `OOS_CUTOFF`, `>= OOS_CUTOFF_MS`, `oos_window`, `out_of_sample`, hard-coded post-2025-03-24 dates used for filtering IN.** None permitted.

---

## 3. Backtest-Live Parity Statement (Section 11.C pre-fill)

The /045 bundle's per-(symbol, candle) decision is the pure function:

```
def bundle_signal(symbol, t):
    if symbol in {BTCUSDT, ETHUSDT}:
        return baseline_pool_A.signal_at(symbol, t) * (1/3)
    if symbol == LTCUSDT:
        return baseline_D.signal_at(symbol, t) * (1/3)
    if symbol in {LINKUSDT, DOTUSDT}:
        return iter_v1_036.signal_at(symbol, t) * (1/3)
    return NO_SIGNAL
```

This rule:
- References ONLY each component's signal at the SAME timestamp t (same-time-snapshot).
- Multiplies by each component's frozen internal weight (1/3), pre-registered before Phase 6.
- Has NO aggregation, NO netting, NO post-trade information.
- Is implementable at `live/engine.py:_tick` by reading the owning model's signal and placing a single Binance order per symbol per tick.

Backtest and live produce identical trades because the function is total, deterministic, and uses only data available at time t.

---

## 4. Sub-Run Plan (Phase 6)

**Runner**: `run_iteration_045.py` (new; modeled on `run_baseline_v186.py`, but only invokes the two baseline cohorts surviving the rule + replays /036 trades).

### Sub-runs (sequential, independent)

1. `run_model("A (BTC/ETH)", ("BTCUSDT","ETHUSDT"), 2.9, 1.45, apply_r1=False)`
   - Identical call to `baseline_v186` Model A invocation.
   - Inherits 5-seed [42, 123, 456, 789, 1001] ensemble, 50 Optuna trials, R3 ON.
2. `run_model("D (LTC + R1)", ("LTCUSDT",), 3.5, 1.75, apply_r1=True)`
   - Identical call to `baseline_v186` Model D invocation.
3. Replay `iter-v1/036` trades from `reports-v1/iteration_v1-036/{in_sample,out_of_sample}/trades.csv`.
   - Re-running would burn ~3h and is mechanically equivalent under fixed seeds; reuse preserves determinism + saves compute.

### Aggregation

- Concatenate `results_a + results_d + trades_036`.
- Apply EQUAL weights via `weight_factor = 1/3` on every trade across all three components.
- Sort by `close_time`.
- Pipe through `generate_iteration_reports(..., iteration=45, ...)`.

### Wall-clock

- ~5h total (baseline_A ~3h + baseline_D ~2h + /036 replay <5min).
- Well under the 6h CONFIRMATION cap.

### Determinism

- Inherited ensemble seeds [42, 123, 456, 789, 1001].
- /036 trades are bit-identical replays from committed CSVs.
- `weight_calibration.py` is deterministic (EQUAL method has no IS dependence beyond N=3).

---

## 5. Expected /045 Outcome

### Hypothesis

Per-symbol PnL attribution under /045 EQUAL weights matches the underlying components (1/3 each), with LINK+DOT now sourced from /036's superior OOS trend-scan rather than baseline's pool. Predicted OOS bundle Sharpe Δ vs `BASELINE_V1`: +0.10 to +0.30 (from /036 LINK+DOT OOS lift), with C2 (LTC) carrying ~30-33% of bundle IS PnL (boundary of concentration soft cap; documented and accepted per QR risk mitigation note).

### Falsifier

If /045 OOS Sharpe Δ < -0.20 vs `BASELINE_V1` AND C3 (/036 LINK+DOT) shows negative OOS contribution: next iteration (iter-v1/046) replaces C3 with iter-v1/043 (LINK-only PROMISING +0.59 OOS Δ) and finds a new DOT sole-owner candidate (iter-v1/029 DOT-only TF is the top candidate). NOT in /045 scope.

### Concentration

C2 (LTC) drove ~30% of baseline IS PnL alone. Under /045 EQUAL weights it remains ~30-33% of bundle IS PnL. On the boundary of the 30% concentration soft cap; QR risk mitigation: documented as accepted; post-OOS mitigation (if needed) would vol-scale C2's weight down to ~0.25 in a future iteration.

### Bundle Methodology Compliance (Section 11 dry-run)

- 11.A Universe Partition: PASS (pairwise disjoint verified above)
- 11.B Weight Derivation: PASS (EQUAL, IS-only script + CSV pre-registered)
- 11.C Backtest-Live Parity Statement: PASS (pure dispatch function above)
- 11.D Re-Composition Note: PASS (LINK+DOT dropped from baseline pool, documented)
- Phase 7.5 Critic Checks 15, 16, 17: PASS (predicted; the design satisfies each rule by construction)

---

## 6. /044 Disposition Recommendation

**Recommendation**: LET-FINISH /044, but record the disposition.

**Rationale**:
- /044 was launched under the pre-2026-05-31 rules and is grandfathered. Its merge decision is handled under the prior Portfolio Composition Rules.
- /044 is a CONFIRMATION-PORTFOLIO bundle of (BASELINE_V1, iter-v1/036) — the SAME bundle composition that triggered the iter-v1/038 veto. It almost certainly has coin overlap (LINK, DOT) and likely uses ad-hoc weight derivation.
- If /044 produces a numerical headline that LOOKS strong, the temptation will be to cherry-pick it as MERGE. Killing /044 NOW removes that temptation cleanly.
- HOWEVER: letting /044 finish provides a comparison data point — the diary records "old-rules-bundle headline metrics" vs the "/045 new-rules-bundle headline metrics" so we can quantify the cost of the rule change.

**If LET-FINISH /044 (recommended)**:
- /044 diary closeout records: "GRANDFATHERED — pre-2026-05-31 rules. Headline metrics reported for comparison only. NOT MERGED regardless of numerical outcome because the bundle violates Rule 7 (Universe Overlap) and Rule 1 (weights derivation not pre-registered via committed IS-only script). MERGE decision deferred to iter-v1/045 under new rules."
- /045 brief Section 0.5 cadence list cites /044 as the 10th EXPLORATION precedent (it WAS launched as a CONFIRMATION but is effectively a 10:1 cadence-closing comparator).

**If KILL /044 (alternative)**:
- Stop the running job (estimated remaining wall-clock: check `briefs-v1/iteration_v1-044/engineering_report.md` for ETA).
- Record `briefs-v1/iteration_v1-044/_killed_pre_phase7.md` with the reason: "Bundle composition violates retroactively-applied Rules 7/1/8. Killing to free compute for /045 under new rules."
- /044 cadence slot becomes a NULL in `briefs-v1/exploration_catalog.md` (not a NEGATIVE; not a PROMISING; explicitly NULL — terminated mid-flight by methodology change).

---

## 7. Open Questions for /045 Phase 5 Authoring

1. Does `baseline_pool_A` need an updated R-config (R1 OFF stays the same; R3 70th pct stays the same; ATR 2.9/1.45 stays the same)? **A**: No — inherits unchanged from baseline_v186.
2. Should the EQUAL weight choice be sensitivity-tested at iter-v1/046 (varying the derivation method)? **A**: Not /045 scope. /046 candidacy decision depends on /045 OOS outcome.
3. Concentration soft cap — should C2's 30-33% bundle PnL share trigger a Phase 7.5 WARN even if Check 16/17 PASS? **A**: Document as accepted in brief; do not pre-register a WARN trigger (that would conflate edge concentration with rule violation).

---

## 8. Phase 5 Brief Authoring Checklist (for /045 proper)

The full /045 brief must contain all 11 sections of the v1 brief template, with these specific pre-fills from this outline:

- Section 0.5 (Cadence) — cite 10 EXPLORATION precedents including /034-/043 and /044 (with grandfather note).
- Section 0.6 (Axis Family) — `risk-primitive` (bundle composition is a risk-primitive axis) OR a new family `bundle-discipline` if axis taxonomy is extended. QR decides at brief authoring.
- Section 2 (EDA / IS evidence) — table from this outline §1 (component IS metrics).
- Section 2.5 (HIGH-RISK) — NORMAL-RISK declaration (no Optuna training-objective domain change; weights are deterministic from IS-only data; underlying models inherit unchanged).
- Section 3 (Proposed Changes) — address LM Master Phase 4.5 recommendations.
- Section 7 (Pre-Registered Failure-Mode Prediction) — per §5 of this outline.
- Section 8 (MERGE/NO-MERGE Criteria) — per the per-regime Pareto-dominance rule.
- Section 11 (Bundle Composition) — paste §§1, 2, 3, 4 of this outline into 11.A, 11.B, 11.C, 11.D, plus the existing required sub-blocks (components included, composition method, regime coverage, pairwise correlation, substitution test, OOS/IS prediction).
