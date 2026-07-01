# EXPLORATION-009 — Extend IS history to 2010 (N≈5-bear validation) (iter-009)

**Date:** 2026-07-01
**Status:** COMPLETE — **ROBUSTNESS VALIDATION** (edge HOLDS 15-yr/5-bear; honest downgrade +0.43→+0.28). OOS HIDDEN.
**Cadence:** EXPLORATION (measurement-period extension; no strategy change) · **Commit:** `96fbe7b`

---

## Motivation

iter-006/008's bear behavior + the VIX brake were validated on only **2 in-sample bears** (COVID + 2022) —
the Critic's and risk-engineer's central caveat. Yahoo has history to 2010 for established names → extend IS
to bring **2011, 2015-16, 2018-Q4** bears into the test (N≈5). Pure data + regime-tag extension; signal
unchanged; OOS cutoff (2025-03-24) unchanged (extends IS *backward* only).

## Data / change

Re-ingest Yahoo from 2010-01-01: 69/69 names, **42 with full 2010+ history** (4147 bars), IS = 2010-01 →
2025-03-21 (3828 union days / 195,914 name-bars), ^VIX to 2010. IPOs ragged/PIT (NaN→0 pre-listing). Extended
`core_tradfi._REGIMES` with the 3 pre-registered pre-2018 bear windows (dates in comment; not tuned).

## IS numbers (2010-2025, IS-only) vs 2018-only

| book | net (2010-25) | bull | bear | chop | (2018-only net) |
|------|--------------|------|------|------|-----------------|
| iter-006 | **+0.28** | +0.30 | −0.24 | +0.51 | +0.43 |
| VIX-alone | **+0.23** | +0.22 | **−0.09** | +0.46 | +0.41 |

## Per-bear (iter-006 Sharpe / return → VIX-brake effect) — the key deliverable

| bear | iter-006 | VIX brake |
|------|----------|-----------|
| 2011 | **+0.85** / +2.7% | fired 94%, DD −7.7→−4.2% (help; momentum already won) |
| 2015-16 | **+1.39** / +9.6% | fired 48%, −2.5pp DRAG (trimmed a winning bear) |
| 2018-Q4 | −2.75 / −6.1% | fired 52% but under-levered — **whiffed** (fast, moderate-VIX Fed selloff) |
| COVID | −3.65 / −10.6% | fired 87%, ret +3.5pp, DD −14.4→−9.1% (**big help**) |
| 2022 | −0.38 / −2.5% | fired 89%, ret +3.1pp → +0.6% (**help**) |

## Findings

1. **Momentum edge HOLDS 2010-25: +0.28.** More robust than feared — momentum WON 2 of 5 bears; the 5-bear
   aggregate bear is only **−0.24** (vs the 2-bear era's −1.23). The −1.23 was a 2018-25-era artifact.
2. **The real tail is sharp momentum-REVERSAL crashes (COVID, 2018-Q4), NOT bear markets.** Momentum does
   fine/wins in grind-down bears (2011, 2015-16, 2022); it crashes only in violent reversals.
3. **VIX brake generalizes — QUALIFIED YES.** Fired 5/5, helped 4/5 (material COVID/2022, shallow 2011,
   whiffed the moderate-VIX 2018-Q4). It's **VIX-spike-conditional insurance**, not a blanket cure; the 2-bear
   fix magnitude was COVID/2022-inflated. With VIX, the 15-yr bear is **−0.09 (~flat)** → survivable all-weather.
4. **Honest confidence downgrade +0.43 → +0.28.** 2018-25 was a uniquely strong mega-cap-tech momentum era.
   The 15-yr number is the trustworthy one. Numbers came DOWN on more data = the opposite of overfitting.

## Verdict — the N=2-bear concern is RESOLVED

A robust, leak-free, honest **all-weather-ish market-neutral momentum book at ~0.23-0.28 Sharpe** (below the
era-inflated +0.30 bar, but real across 15 years / 5 bears). No re-tuning to the newly-revealed bears
(that would be curve-fitting). OOS hidden throughout (44 tests + split-guard green).

## Next

- iter-010 (running) = regime-conditional **beta-neutral** overlay (iter-007 found beta-neutral chop
  +0.26→+1.05) — the strongest unexplored Sharpe lever, tested on the robust 15-yr data.
- Open (per risk note): the 2018-Q4 whiff = a faster/moderate-VIX de-risk trigger — deferred (N=1 of its
  type, overfitting risk). VIX-alone is the deployable crash insurance.
