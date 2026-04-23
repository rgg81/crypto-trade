# iter-v2/068 Research Brief — z-score OOD 2.5 → 2.4

**Type**: EXPLOITATION (single parameter tweak)
**Parent baseline**: iter-v2/059-clean
**Context**: pivot away from concentration fixes after 5 NO-MERGE iterations
(iter-v2/063-067) empirically showed current baseline is at local optimum.

## Section 0 — Data Split

`OOS_CUTOFF_DATE = 2025-03-24` — immutable.

## 1. Problem & hypothesis

iter-v2/050 used z-score OOD 3.0. iter-v2/059-clean uses 2.5 (tightening
improved OOS monthly +8%, became the baseline). iter-v2/060 tried 2.25
and failed (OOS trades < 50 min, insufficient signal).

The 2.5 → 2.25 jump may have been too aggressive. **Try 2.4** — smaller
step, tests whether continued tightening beyond 2.5 yields diminishing
returns or genuine improvement.

## 2. Design

Single change to `RiskV2Config` in `run_baseline_v2.py::_build_model`:

```python
risk_cfg = RiskV2Config(
    zscore_threshold=2.4,  # iter-v2/068 test (was 2.5 in iter-v2/059-clean)
)
```

Everything else identical to iter-v2/059-clean: 4 baseline symbols,
cooldown=4, hit-rate off, BTC trend on, drawdown brake OFF (iter-v2/067
showed it's net harmful), 5-seed ensemble, 50 Optuna trials.

## Section 6 — Risk Management Design

### 6.1 Active primitives

Same as iter-v2/059-clean. Only z-score OOD threshold changes 2.5 → 2.4.

### 6.3 Pre-registered failure-mode prediction

**Most likely failure**: tighter z-score threshold kills too many signals,
same as iter-v2/060. If OOS trades drop below 50 minimum, NO-MERGE
immediately.

**Failure signature**: OOS trades < 50 OR OOS monthly Sharpe < baseline × 0.9.

**Success signature**: OOS trades ≥ 50, OOS monthly Sharpe > +1.66,
concentration unchanged or better.

## 3. MERGE criteria (standard)

1. Combined IS+OOS monthly Sharpe > +2.70 (baseline)
2. OOS monthly Sharpe ≥ +1.41 (0.85 × baseline)
3. IS monthly Sharpe ≥ +0.88 (0.85 × baseline)
4. OOS MaxDD ≤ 27.1%
5. PF > 1.0, trades ≥ 50, trade Sharpe > 0
6. Concentration ≤ 50% (outer)

## 4. Expected runtime

~2.5h single-seed. Data fresh from iter-v2/059-clean run.

## 5. Fail-fast

If after Model E completes (first ~35 min), OOS trade count for DOGE is
significantly reduced (<14 OOS trades, baseline had 16), consider killing
— that's the iter-v2/060 failure signature.
