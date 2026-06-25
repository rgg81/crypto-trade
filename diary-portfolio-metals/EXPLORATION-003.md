# EXPLORATION-003 — Bold-axis bake-off → platinum-vs-palladium reversion sleeve

**Track:** metals portfolio. **Date:** 2026-06-25. User directive: *be bold, do not do the obvious,
search the internet, take your time.*
**Verdict:** ✅ **PASS** (Critic) — but the pt-pd sleeve is classified **PROMISING-THIN-N**:
implemented + documented, **NOT promoted to baseline** (pre-registered falsifier tripped).
**OOS:** hidden. All numbers IN-SAMPLE only.

## What we did
Rejected the *obvious* iter-003 ideas (trend-strength gate, vol-budget, 2nd dispersion sleeve). Ran an
internet-grounded **bake-off** of 3 bold, non-obvious, mechanism-driven axes, net-of-cost, IS-only.

### The bake-off (3 axes — all the obvious-anomaly ones came back NEGATIVE net)
| Axis | Mechanism | Cost-free SR | **Net SR** | Why it failed |
|---|---|---|---|---|
| **Session / overnight** | "rises in Asia, falls London/NY" (Asian physical vs Western paper-gold + London PM fix). OUR data: **NY-strong (gold t=+3.8) / London-dead**. | +0.68 | **−2 to −3.7** | COST-KILLED — flips book every 8h (turnover 0.6–1.2/candle) |
| **Cross-metal lead-lag** | gold leads silver/plat/pall at lag-1 (partial adjustment) | +0.64 | **−0.16** | COST-KILLED — momentum-flip turnover |
| **Cross-asset macro** | copper (gold/copper = fear-vs-growth), oil (gold/oil = inflation); DXY/real-rates **decoupled since 2022** (CB buying) = OOS trap | — | era-confined | copper-pulse lift lived only 2015–21; **no-op in live 4-metal era** |

### The structural law discovered (most valuable finding)
Under this engine (`gross-norm → .shift(1) lag → cost → vol-target`), **only the cross-sectional
SHAPE and NET DIRECTION of the raw book survive.** Any uniform magnitude/regime/exposure scaling is
washed out by gross-norm + vol-target; the only expressions that *can* matter (directional flips) pay
lethal 8h turnover. ⇒ session & lead-lag are *real edges blocked solely by the 8h-flip cost*, not
absent edges. Future axes must change **shape** or **net direction** at **low turnover**.

### The winner the law pointed to — pt-vs-pd reversion sleeve (3rd sleeve)
The iter-002 overlay lumps platinum+palladium into ONE short basket, so it cannot express their
DIVERGING fundamentals (palladium bled by EV substitution; platinum lifted by hydrogen/diesel). The
`log(XPT/XPD)` ratio **MEAN-REVERTS** (variance ratio 0.57–0.88 < 1; *unlike* GSR which trended — why
momentum fails on GSR but reversion works here). FADE it: pt rich → short pt / long pd, dollar-neutral,
inverse-vol sized. A pure cross-sectional SHAPE signal (obeys the law), low-turnover, live-relevant.

## Results (3-sleeve, IS-only)
| Book | full-IS Sharpe | 2022+ Sharpe | maxDD full / 2022+ | turnover |
|---|---|---|---|---|
| iter-002 combined (reference) | +0.514 | +0.745 | −25.8% / −21.1% | 0.0072 |
| **3-sleeve center (Z=126, β=0.25)** | **+0.537** | **+0.844** | −25.8% / **−20.8%** | 0.0146 |
| Standalone pt-pd sleeve (2022+) | — | +0.211 | −23.0% | 0.0942 |

- Standalone sleeve corr to book **−0.339** (genuinely orthogonal). Sweep Z{84,126,189}×β{0.20,0.35,0.50}:
  **8/9 cells lift BOTH windows**; β peaks at 0.5–0.75 then declines (genuine reversion timing, not a
  hindsight drift-bet). Integrity: dollar-neutral 1.4e-14, column-isolated to {XPT,XPD} 0.0,
  warmup-clean (first signal 2022-05-23, net=0 before).

## Why NOT promoted — the pre-registered FALSIFIER tripped
2-fold era split of the standalone sleeve **inverts**: 2022-23 = **−0.129**, 2024-cutoff = **+0.720**
(standalone lost −11% in 2022). The lift concentrates in the recent, **OOS-adjacent** half of an
already ~33-month window — the single most dangerous place for an in-sample edge to sit. Per the
pre-registered rule → **PROMISING-THIN-N, do NOT update baseline.** A `PROMOTABLE = False` guard is now
in `iter_003_ptpd.py` so no future session can accidentally baseline it.

## Leak check (MANDATORY) — PASS
3-sleeve corruption test: corrupt all OHLC from 2023-06 forward → 6938 pre-cutoff candles + weights
bit-identical (max diff 0.00e+00). Foundation 16/16 green; lint clean.

## Critic note (PASS, concurs with PROMISING-THIN-N / no-baseline-update)
"Honest negatives on 3 axes + a correctly-classified PROMISING-THIN-N sleeve, leak-safe, exemplary
record." Confirmed: leak-safe (incl. demean + triple gross-norm path), parity-correct combination,
column-isolation keeps the gold/silver dispersion bit-identical, both correlations interpreted
correctly (−0.339 = sleeve orthogonality; +0.984 = post-blend book overlap, expected at β=0.25).
Effective DoF ~5-7 vs ~33 months is thin — correctly bounded by the THIN-N label. Added the
`PROMOTABLE=False` machine-guard at Critic's suggestion.

## Path forward (Critic's read — the bolder move is a FREQUENCY change, not universe)
The bake-off **already discovered two real edges** (session, lead-lag) blocked *only* by the 8h-flip
cost/turnover mismatch. That is known signal waiting for the right bar interval — higher-EV than
restarting the search on a new universe at the same saturated 8h/6bps ceiling.
- **iter-004 candidate:** re-run session + lead-lag at **daily/weekly** bars (slower flips → cost
  budget reopens) — Dukascopy can resample to any interval. **Caution:** OOS_CUTOFF=2025-03-24 leaves
  few daily / very few weekly OOS observations — pre-register a minimum OOS-N first.
- pt-pd de-risk: ingest a **daily LBMA/NYMEX pt/pd proxy** (decades of history) purely to test whether
  the reversion prior holds pre-2022 — the only way to attack the 33-month problem.
- Universe expansion deferred until a frequency change reopens the cost budget.

## Files
- `analysis/portfolio/metals/iter_003_ptpd.py` (pt-pd sleeve + 3-sleeve combination + PROMOTABLE guard)
- diaries: this file. Foundation/anchor/overlay unchanged.
