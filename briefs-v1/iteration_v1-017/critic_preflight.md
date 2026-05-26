# Phase 6.0 Critic Pre-Flight — iter-v1/017

OVERALL: PASS (with R5 default fix at `5fffe8a`)

## Pre-Flight Checks

### Check 1 (mini) — Brief Look-Ahead Audit: PASS

Brief Section 3.2 "Features: V1_FEATURE_COLUMNS_PRUNED unchanged (40 cols)". Section 3.1 introduces only new universe constant + runner-local elif dispatch + Model F. No new feature derivations. SOL A14 pre-screen PASS (max_consecutive_flat_close=1; zero_volume_candles=0). SOL data starts 2020-09-14 (≥4yr buffer before 2023-04-04 training start).

### Check 13 (mini) — Anti-Pattern Static Scan: PASS

- A1: `walk_forward.py:113` carries `- embargo_ms` subtraction; zero raw matches
- A2: zero matches in labeling.py
- A3: zero matches across src/
- A4: V1_ITER017_UNIVERSE is static literal tuple
- A5: 4 mandated regression tests present
- A7: OOF parquet unlink guard at runner startup
- A12/A13: methodology bookkeeping not touched

src/ diff scope: V1_ITER017_UNIVERSE addition + elif dispatch + Model F + SOL feature regen + R5 default fix.

### Foundation Regression: PASS

`walk_forward.py:113` `train_end_ms = test_start_ms - embargo_ms` UNCHANGED. compute_embargo_candles single source of truth. No regression.

### Cadence + Axis Sanity: PASS

- phase5p5_gate.md OVERALL=PASS at `5a1883c` (post-BLOCK recovery)
- Brief Section 0.6: `universe` family UNUSED since /006; rotation VALID
- Prior 5 EXPLORATIONs: methodology-substrate-test ×2, labeling ×2, sample-weighting ×1 — universe in NONE
- Cycle-3 cadence position #2 of 10
- HIGH-RISK declared with explicit reason

### Falsifier Presence: PASS

F1 OOS Sharpe Δ bands explicit (NEGATIVE Δ≤-0.20, catastrophic Δ≤-0.55, PROMISING Δ≥+0.20). F8-NEW OOS trade count band. F-AXIS-MECHANISM compound 3-sub-check (dispatch + SOL share [5%, 40%] + n_eff [10, 18]). Section 2.4 Scenarios A/B/C second-order falsifier on ETH regime-bound vs universe-bound.

## R5 Vol-Target Default Fix (commit `5fffe8a`)

**ISSUE IDENTIFIED**: BASELINE_V1 anchor commit `f8bc12c` had ZERO R5 mentions in `run_baseline_v1.py`. The +0.2829 IS / +0.6637 OOS metrics were measured WITHOUT R5 active. Post-/010, the runner default `r5_vol_target_enabled=True` implicitly added R5 to all iterations unless explicitly auto-disabled by another axis trigger. /017 with default-True would have run WITH R5 enabled while baseline anchor is WITHOUT R5 — double-confounded.

**FIX APPLIED**: changed runner default from True to False (cycle-3+ discipline). All cycle-3+ iterations now compare cleanly against BASELINE_V1 anchor without R5. /010-style reruns would need explicit re-enable (no flag exposed yet; not currently needed since /010 is closed NEGATIVE).

**Verification**: Critic Phase 6.0 initially rationalized R5=True as "anchor matched" — wrong per source verification. Fix at `5fffe8a` corrects this for /017 and cycle-3+.

## Pre-Flight Notes

1. **A14 grep on SOL** PASS. Phase 7.5 will spot-check SOL klines for forming-candle / frozen-price patterns.
2. **Wall-clock estimate**: 60-min linear / 42-min sub-linear; 50%-65% margin against 2h cap.
3. **HIGH-RISK declaration acknowledged** (1st cycle-3 HIGH-RISK).
4. **Frozen-baseline pattern at single-seed=42**: Phase 7.5 will spot-check A/C/D/E trade-roster overlap with /016.

OVERALL=PASS. Backtest cleared to launch with R5 default fix applied.
