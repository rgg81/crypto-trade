# iter-012 — BROAD-UNIVERSE factor test (the pivotal multi-factor probe)

**Date:** 2026-07-01 (multi-factor pivot; user bar = net ≥0.5 Sharpe + positive every year)
**Status:** PROBE (measurement, no promote). OOS HIDDEN. Leak PASS, sector-resid 0.0, 78/78 tests green.
**Question:** do the factors that DIED on the 69 mega-cap-growth names WORK on a broad US universe
with real cross-sectional diversity — and how much is realizable within the tradeable 69?

## Setup
- **Universe:** `data_broad/` = **525 names** (503 current S&P 500 constituents pulled from Wikipedia
  + 22 tradeable-69 extras so the hybrid has a full sub-panel), 11 GICS sectors, Yahoo total-return
  daily 2010-2025. Ingest: `ingest_yahoo_broad.py`. Separate gitignored dir; the tradeable-69 `data/`
  is untouched.
- **6 price-only factors**, sector-neutral z-scores, past-only (betas `.shift(1)`, all windows
  trailing), each → `net_from_raw` (15% vol-target + 6bps cost). Combine = inverse-vol risk-parity
  of the positive-EV, low-correlated set, banded (δ=0.005), vol-targeted. `iter_012_broad.py`.
- **⚠️ SURVIVORSHIP BIAS (flagged everywhere):** current membership is NOT point-in-time — delisted
  failures are absent, which INFLATES every result (SIZE most of all). First-pass diversity test, not
  a deployable backtest. If factors work, a PIT-membership (delisted-inclusive) rebuild is the follow-up.

## (A) Standalone factor IS Sharpe — BROAD vs the 69
| factor | BROAD net | +yrs | on the 69 | verdict vs "breadth resurrects it" |
|--------|-----------|------|-----------|-------------------------------------|
| MOM 12-1m | **+0.17** | 7/16 | **+0.32** | robust-positive; STRONGER on the 69 (not a universe problem) |
| SIZE (small) | **+1.30** | 14/16 | +0.17 | "works" — but the **most survivorship-inflated** factor |
| LTR 3y-1y | −0.02 | 6/16 | +0.24 | ~flat both; no resurrection |
| BAB low-beta | **−0.42** | 6/16 | −0.77 | **DEAD even on broad** — hypothesis FALSIFIED |
| LOW-VOL | **−0.95** | 3/16 | −0.84 | **DEAD even on broad** — hypothesis FALSIFIED |
| ST-REV 1m | −0.94 | 3/16 | −0.88 | dead both |

Pairwise corr: MOM↔SIZE +0.05 (orthogonal); BAB↔LOWVOL +0.84 (one bet). MOM↔STREV −0.48, MOM↔BAB +0.46.

## (B) Multi-factor combo on BROAD (survivorship-caveated)
Only **2 of 6** factors are positive-EV on broad: **SIZE + MOM** (and they're uncorrelated).
Inverse-vol combine → **net +1.69, 15/16 years, maxDD −27%** (bull +2.27 / bear −0.94 / chop +2.24).
The single negative "year" is the **2025 IS stub (59 business days ≈ 2.8 months)** — effectively
**15/15 full years positive**. Return-level risk-parity cross-check: +0.97, 14/16.
- **Reaches net ≥0.5 + positive-all-full-years? YES on the number — but it is SIZE-driven, and SIZE is
  the factor most contaminated by survivorship** (long-small on *current* membership = long the small
  names that survived and grew). Strip SIZE and the only positive-EV broad factor is MOM +0.17. So the
  headline is NOT a trustworthy edge; treat +1.69 as an inflated ceiling, not a realizable Sharpe.

## (C) Hybrid deployable-69
Same construction on the tradeable-69 sub-panel (69/69 present): SIZE+MOM inverse-vol combine →
**net +0.52, 12/16 years, maxDD −40%** (per-year `++--+++-+-++++++`). Clears net ≥0.5 nominally but
NOT positive-all-years; leans on MOM +0.32 with SIZE only +0.17 in the narrow mega-cap cross-section.
This is close to the existing iter-011 mom+LTR book (+0.33) — the broad SIZE lift does **not** carry
into the 69, because the 69 have almost no small-cap tail.

## Key answers
- **Do BAB / low-vol / size work on broad?** BAB **NO** (−0.42), low-vol **NO** (−0.95) — both stay
  negative *even with a real low-beta tail*, so breadth did NOT resurrect them. SIZE **YES nominally**
  (+1.30) but it is survivorship-inflated and does not survive into the deployable-69 (+0.17).
- **Does the broad book reach ≥0.5 + positive-all-years?** Numerically yes (+1.69, 15/15 full years),
  but only because SIZE (survivorship-contaminated) dominates; the honest, less-biased content is
  MOM alone (+0.17).
- **Universe problem or factor problem?** **FACTOR problem, primarily.** Broadening the universe did
  not rescue BAB / low-vol / short-term-reversal (all negative on broad); the one "win" (SIZE) is a
  bias artifact, and MOM — the one robust factor — is actually *stronger* on the 69 than on broad, so
  its ceiling is not a breadth constraint. The multi-factor pivot's premise (breadth resurrects the
  dead factors) is **not supported** by this first-pass test.

## Concern / next
Dominant risk = **survivorship** inflating SIZE (and to a lesser degree everything). The load-bearing
follow-up before trusting any broad multi-factor number is a **PIT-membership (delisted-inclusive)
rebuild** — without it, "positive-all-years" on current members is close to tautological. Secondary:
BAB/low-vol being negative on a broad, low-beta-rich universe suggests the *price-only* construction
(or the market-neutral + vol-target framing) is the binding issue for those factors, not the universe.
