# Diary — iter-v1/017 (BTCUSDT) — CONFIRMATION (K=20) — NO-MERGE (iter-016 both-positive was a basin-lottery)

**Axis:** K=20 confirmation of the iter-016 both-positive (config BIT-IDENTICAL: 19-col HYBRID,
fixed_horizon N=42 let-winners-run, R2 brake, R3/R5, stateless 200-SMA trend-state direction). Only
K differs (5→20) — isolates the K=5 lottery risk.

**Result:**
| | IS Sharpe | OOS Sharpe |
|---|---|---|
| iter-016 K=5 screen | +0.6308 | **+0.1120** |
| **iter-017 K=20** | **+0.2465** | **−1.1530** |
IS net +9.0, OOS net −4.26. 120/58 trades. 20/20 seeds. Clean run.

**Verdict: CONFIRMATION-NO-MERGE. The iter-016 both-positive was a K=5 BASIN-LOTTERY.**
- OOS swung +0.11 (K=5) → −1.15 (K=20): a 1.26 swing from changing ONLY the bagging seed count. The
  K=20 (20 independent timing models averaged) is the honest read; the K=5 (5 models) drew favorably.
  The methodology caught a false positive before merge — exactly its purpose (the iter-003→004 lesson).
- **Does NOT beat the baseline** (iter-001 IS −0.28 / OOS +0.64): K=20 OOS −1.15 ≪ +0.64. NO-MERGE.

**Diagnosis (what's real vs lottery):**
- The trend-state DIRECTION is deterministic (identical across all seeds) and its **SHORT side partially
  generalizes** — OOS shorts net **+6.5% even at K=20** (the trend-state goes short below the 200-SMA
  and catches corrections). That part is real.
- The **LONG side does NOT generalize**: OOS longs −14.0% (WR 21%) at K=20 — the same OOS-bull-long
  failure that has dogged the entire campaign (iter-010→015). Being above the 200-SMA does not make the
  14d-hold longs win in the 2025-26 OOS.
- The model's **entry-timing/sizing is high-variance across seeds** (basin-lottery): K=5 luckily
  selected/weighted trades that gave OOS +0.11; K=20's honest average gives −1.15. (Trade-candle overlap
  K5∩K20 = 45/52, so the swing is timing-selection + conviction-weighting variance, not direction.)

**Honest status:** the creative trend-state pivot was PARTLY right (shorts generalize) but did NOT
yield a robust both-positive at honest K. The announced iter-016 breakthrough is downgraded to a
basin-lottery. The persistent root cause stands: **BTC's directional LONG edge does not generalize to
the OOS regime**, at any horizon, under any direction source tested.

**Next (options, surfaced to user):**
1. **V-B (QR pre-registered falsifier):** model-free trend-state (trade the stateless direction without
   the overfit model timing). The QR pre-registered "OOS ≤ 0 for BOTH V-A and V-B → trend-state pivot
   falsified." V-A is ≤0 (−1.15); V-B is the remaining test. (Caveat: the long side losing OOS suggests
   V-B may also fail, and any V-B K=5 must be K=20-confirmed given the proven basin-lottery.)
2. **Asymmetric / short-aware creative angle:** the trend-state SHORTS generalize, LONGS don't — a
   mechanism-level reframe (not curve-fitting) around what actually generalizes.
3. The methodology is working (rigor caught the lottery); the both-positive search continues.
