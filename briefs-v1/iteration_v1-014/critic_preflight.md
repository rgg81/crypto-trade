# Phase 6.0 Critic Pre-Flight — iter-v1/014

OVERALL: PASS

## Pre-Flight Checks

### Check 1 (mini) — Brief Look-Ahead Audit: PASS

Brief Section 4 + Section 7 + Section 10.1 explicitly describe σ_t as past-only EWMA at half-life=42 candles with mandatory `.shift(1)` AFTER `ewm(halflife=42).std()`. No forward-window construction. Brief Section 7 Failure Mode #3 explicitly pre-commits to `.shift(1)` requirement with Phase 6.0 verification.

### Check 13 (mini) — Anti-Pattern Static Scan: PASS

**A2 (forward-window σ_t) — CRITICAL**: grep returned ZERO matches. New σ_t computation at `lgbm.py:425-426`:

```python
ewma_std = log_ret.ewm(halflife=self.sigma_halflife_candles, adjust=False).std()
ewma_std_shifted = ewma_std.shift(1)  # A2 GUARD — past-only
```

The shift is documented as MANDATORY in docstring lines 388-401 with cross-reference to regression test. **`test_sigma_t_is_past_only` perturbs close[k] and asserts sigma[k] is UNCHANGED (proving sigma[k] does NOT incorporate return[k]) while sigma[k+1] IS changed** — strongest possible numerical proof of A2 absence.

A1 (train_end_ms = test_start_ms without subtraction): ZERO active-code regressions. `walk_forward.py:113` carries the documented subtraction.

A3 (fit_transform combined): ZERO matches.
A12 (psr/dsr granularity): no changes; existing wiring per /013.
A13 (report-file read before write): no new methodology-axis fields.

### Foundation Regression: PASS

`walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` — UNCHANGED by /014 QE diff. `compute_embargo_candles` helper single source of truth. 4 mandatory lookahead regression tests present.

### Cadence + Axis Sanity: PASS

phase5p5_gate.md OVERALL=PASS at `fec6cbd`. Brief Section 0.6 = `labeling` family. Prior-5 EXPLORATION: feature-family / risk-primitive×2 / methodology-substrate-test×2. `labeling` is UNUSED in cycle-2 (last used /004 cycle-1). Rotation VALID.

HIGH-RISK declared with mitigation = /015 = labeling CONFIRMATION binding pre-commit.

Cycle-2 cadence position 9/10. ≤2h cap.

### Axis Family Validation (Check 14 equivalent): PASS

`git diff 22f643c..1d24dc6 -- src/` shows additions to `labeling.py` (sigma_values parameters + use_sigma path at line 333+) and `lgbm.py` (sigma_source params + `_load_sigma_for_master()` method + branch in `_train_for_month()` at line 483). No risk-primitive, feature-family, model-arch, or universe modifications. Declared family MATCHES.

### Falsifier Presence: PASS

Brief Section 4 declares 8 falsifiers including:
- **F7-NEW** (per-symbol exit-mix direction): BTC/ETH TO% UP, alts TO% DOWN. PASS = all 5 match; FAIL = 2 or fewer match → EXPLORATION-NEGATIVE-WIRING per Section 8.1 cell 7
- **F8-NEW** (IS trade count band [466, 776] = 621 ± 25%)

Both pre-registered as MECHANICAL attribution falsifiers — the only axis-clean diagnostics at single-seed.

## Concerns Surfaced for Phase 7.5 Attention (NOT BLOCKING)

### Concern C1 — Barrier-Source Consistency Label-Time vs Execution-Time

Brief Section 10.1 RESOLUTION mandates "barrier-source consistency at both label-time AND execution-time". On audit:

- **Label-time**: `labeling.py:333` `use_sigma` branch uses `sigma_k × sigma × entry`. WIRED CORRECTLY for σ_t.
- **Execution-time**: `lgbm.py:907-915` `predict()` returns `tp_pct = natr * atr_tp_multiplier` (UNCHANGED from /013).

Per EDA Section 2.4, median EWMA/NATR ratio 1.11-1.13 BTC/ETH and 0.92-0.94 alts. Execution barriers will systematically diverge from label barriers by 7-13% per-symbol. Brief Section 10.1 explicitly warned of this.

**Why NOT a Phase 6.0 BLOCK**:
1. Introduces ATTRIBUTION ambiguity, NOT lookahead (A2 / Rec #3 risk satisfied).
2. F7-NEW falsifier is computed on EXECUTION-time roster — inconsistency is observable.
3. Engineering report (BLOCKING per Section 10.2) MUST disclose this. Phase 7.5 Critic will FAIL on Check 8 if engineering report doesn't address.
4. Execution-path is structural carry-forward from /013 — changing mid-flight would introduce SECOND axis and corrupt axis isolation.

**Phase 7.5 Critic action**: verify engineering report discloses barrier-source choice.

### Concern C2 — Engineering Report Runner Warning vs Hard-Block

`run_baseline_v1.py:1215-1222` emits `[WARNING]` (not non-zero exit) when engineering_report.md missing. Brief frames as "belt-and-suspenders; orchestrator-side enforcement is BLOCKING declaration". Acceptable design.

## Notes for QE / Orchestrator

- σ_t labeling A2 safety structurally correct AND numerically verified. LM Master Phase 4.5 Rec #3 SATISFIED.
- Phase 6 backtest may launch. Expected wall-clock 75-95 min ≤2h cap.
- Phase 7.5 surveillance: Concern C1 (barrier-source consistency disclosure) + F7-NEW (per-symbol exit-mix direction match across 5 symbols).
- HIGH-RISK pre-commit /015 = labeling CONFIRMATION BINDING regardless of /014 magnitude.

Backtest cleared to launch.
