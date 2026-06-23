# portfolio-iteration-v2 EXPLORATION-007 — IS-calibrated risk layer (MERGE CONDITION RESOLVED)

**Type:** risk-engineering (resolves the critic's MERGE-WITH-RISK-LAYER condition). Bound the XS-mom
baseline's −25% OOS drawdown. Code: `risk_v2.py`, `iter_v2_007_risklayer.py`; engine +1 additive line
(`raw_net` in `run_book_from_signal` return). **Verdict: RESOLVED — OOS DD −25%→−16% at ZERO OOS Sharpe cost.**

## Frozen, IS-calibrated config (no OOS tuning, no monthly tuning)
`target_vol = 0.006` (was 0.010), `max_lev = 2.0` (was 3.0), `dd_brake = OFF`. Selection rule
(pre-registered): maximize IS Calmar s.t. IS DD ≤ −25%; chosen from an IS-only grid (OOS never in the
table). Fixed-parameter — applies uniformly every candle.

## Before/after (independently re-verified; 15/15 tests, parity 1.041e-16)
| cost | book | IS | OOS | 2025 | 2026 | maxDD | oosDD | turn |
|---|---|---|---|---|---|---|---|---|
| default | raw | +0.43 | +1.20 | +1.22 | +1.09 | −37% | −25% | 0.185 |
| default | **risk** | +0.41 | **+1.20** | +1.22 | +1.09 | **−24%** | **−16%** | 0.111 |
| 2×-taker | risk | −0.03 | **+0.81** | +0.79 | +0.77 | −31% | −17% | 0.111 |
| pessimistic | risk | +0.28 | **+1.11** | +1.12 | +1.01 | −25% | −16% | 0.111 |

OOS Sharpe IDENTICAL to raw in all 3 cost scenarios; only 2020 per-year shifts (low-vol clip region),
deploy-regime years (2024-26) bit-unchanged.

## Why it works (mechanism forensics)
A uniform per-candle exposure scalar leaves the **ratio-based monthly Sharpe exactly invariant** while
shrinking the **compounded % drawdown** by ~the scale factor. Decomposition: the DD cut is the de-lever
(`tv=0.006` alone → OOS_DD −15.5%), NOT the `max_lev` clip (`ml=2.0` alone leaves DD −24.8%; the worst
OOS descent never hit the 3.0 clip — mean scale 0.89). `max_lev=2.0` kept as a near-free IS-Sharpe
improver (de-concentrates the 8.6% clip-bound candles). Worst OOS descent (2025-11-08→2026-01-28)
−24.8%→−15.5%; the cut applies every candle with ZERO lag (a reactive brake would engage ~50 candles
in, at −7%).

## DD-brake built & REJECTED (honest finding)
An R2-style rolling-peak loss-stop with hysteresis was built (`risk_v2.py`) and calibrated — but DOMINATED
on IS Calmar (best +0.07 vs +0.29 static): this book sits in 8-25% drawdown MOST of the time, so a
trailing-DD stop has a 54-82% duty cycle → it's a worse asymmetric static cut, not a tail stop. Kept in
the codebase DISABLED, documented as the rejected alternative. **For a continuously-rebalanced
dollar-neutral book, unconditional de-leverage dominates a reactive equity brake.**

## v2 BASELINE (candidate, pending record items)
**XS-mom standalone, rank 21-40, L=84, 8h, `run_book_from_signal`, `target_vol=0.006`, `max_lev=2.0`:**
OOS Sharpe **+1.20** (2025 +1.22, 2026 +1.09), OOS maxDD **−16%**, cost-robust (2×-taker +0.81),
turn 0.111. The anchor (ported top-20 trend stack) is OOS −0.01. → unconditional baseline once the record
items close (R1 direct leak test, R3 formal DSR, exact-weight-hold). Then: ensemble (/008), funding (/009).
