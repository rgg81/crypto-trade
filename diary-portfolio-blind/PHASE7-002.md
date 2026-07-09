# EXPLORATION-002 — Phase-7 Verdict (QR)

**Decision: NO-MERGE.** 4 of 7 gates fail (G1, G2, G5, G6); the 3 that pass are the
defensive gates (G3, G4, G7). Pre-registered thresholds are frozen; no gate is
re-litigated.

## Gate scorecard (IS-only, primary midvol_short book, runs 1/3/6 of EXPLORATION-002-engineering.md)

| # | gate | threshold | observed | verdict |
|---|---|---|---:|---|
| G1 | IS Sharpe (primary) | `≥ 1.0` | **+0.09** | **FAIL** |
| G2 | IS Sharpe ≥ EW-top-20 + 0.15 | `≥ +0.60` (= EW+0.451+0.15) | **+0.09** (Δ −0.51 vs EW) | **FAIL** |
| G3 | MaxDD (primary) | `≥ −55%` | **−48.5%** | PASS |
| G4 | every per-year Sharpe ≥ −1.0 | `{20:≥−1,21:≥−1,22:≥−1,23:≥−1,24:≥−1,25Q1:≥−1}` | 2020 +0.81 / 2021 −0.38 / 2022 +0.89 / 2023 −0.79 / 2024 −0.34 / 2025Q1 +3.18 | PASS |
| G5 | turnover (primary) | `≤ 100x/yr` | **138x** | **FAIL** |
| G6 | 2x-cost IS Sharpe | `≥ 0.7` | **−0.29** | **FAIL** |
| G7 | 2021 funding drag (primary) | `≤ +1500 bps` | **−240 bps** (net income) | PASS |

## Honest read (informed by REVIEW-002 CONDITIONAL-PASS)

The +0.09 is **REAL, not artifact** — Critic-verified sign/mechanics, no look-ahead,
funding attribution sign-correct. But it is **DEPRESSED ~0.1–0.2 Sharpe by structurally
elevated turnover** (138x vs long-only's 73x; two-band boundary churn is the structural
driver, partly recoverable via hysteresis). So +0.09 should be read as "cost-inefficient
near-neutral book," NOT "the pure information ratio of the low-vol factor."

The **defensive thesis DELIVERED** and is the take-away from this iteration:
- G3: MaxDD −87% (long-only, EXPLORATION-001) → **−48.5%**. The short book dampened the
  2022 correlated deleveraging exactly as designed — short-leg 2022 price P&L +0.93.
- G4: 2021 −0.38 (vs naive L/S −1.83) — mid-vol shorts did NOT blow up; tail-capping
  skipped the lottery mooners. 2022 +0.89 (vs long-only −1.53) — short leg captured the
  broad-based bear decline. Both regime-robustness bookends held.
- G7: 2021 funding went from long-only's **+3722 bps drag to −240 bps net income**
  (short leg received mania funding). The near-dollar-neutrality dodge fired beyond
  threshold.

The **return-alpha thesis DID NOT DELIVER** — and that is what fails G1, G2, G5, G6:
- G1/G2: low-vol IC +0.052 (DIAGNOSTIC-001) is real but too small net-of-cost to clear
  either the absolute floor or the noise-marginal edge over EW. Single-factor vol_low at
  8h on the PIT-top-20-$-volume universe is not a return-alpha source net of realistic
  costs in this construction.
- G5/G6: turnover 138x and the 2x-cost variant going negative (−0.29) confirm the book
  is cost-fragile. Cost-stress failure is the strongest evidence turnover is a real drag.

## What this iteration established (net positive information)

1. **The mid-vol shell is a verified defensive substrate.** Funding-neutral, MaxDD-bounded,
   regime-robust. It is preserved verbatim into EXPLORATION-003.
2. **The failure is specifically return-alpha, not construction.** The shell's defensive
   properties are orthogonal to the signal — so the next iteration changes ONLY the signal
   to attack the return-alpha axis while holding defenses fixed.
3. **rev_3 is the highest-impact next move** (REVIEW-002 Path Forward #1; DIAGNOSTIC-001
   IC +0.045 at corr −0.006 to vol_low — a genuinely orthogonal alpha source).

## Path to EXPLORATION-003

**EXPLORATION-003 = multi-factor rev_3 blend into the EXPLORATION-002 mid-vol shell.** The
shell (weighting/cost/funding/rebal/universe) is frozen; the ONE change is the signal —
z-blend 0.5·z(vol_low) + 0.5·z(rev_3), fed to the unchanged `target_weights_midvol_short`.
This is the only axis in the Path Forward that adds a NEW alpha source. Hysteresis (S1)
is deferred to EXPLORATION-004 — the brief for /003 isolates the signal-blend axis so the
Sharpe delta is attributable solely to the alpha blend.

OOS remains sealed. No OOS data inspected.
