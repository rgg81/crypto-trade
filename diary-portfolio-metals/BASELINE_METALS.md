# BASELINE_METALS — metals portfolio baseline

**Established:** 2026-06-25 (CONFIRMATION-BOOTSTRAP, L2). **Updated 2026-06-25 (iter-007 PROMOTE):
the ALL-WEATHER book = L2 + drawdown-brake.** **Branch:** `portfolio-metals`. **Engine:** the audited
`universe_metals.net_from_raw` (gross-norm → `.shift(1)` lag → 6bps/side taker cost → ~15% vol-target,
≤5× leverage), then the R-layer brake scalar.

## The baseline book — L2 + DRAWDOWN-BRAKE (all-weather)
```
net0 = net_from_raw( gn(iter_001_trend.build_raw(coins))                   # long-biased trend anchor
                   + 0.5·gn(iter_002_mn_overlay.mn_dispersion_raw(close)) )  # $-neutral dispersion
delivered[t] = k[t] · net0[t]     # R-layer DRAWDOWN BRAKE (iter_007_allweather.dd_brake_scalar)
```
- **anchor:** EMA(84)/EMA(189) crossover, FLOOR=0.5 — long-biased, NEVER shorts (the naive symmetric
  trend's short leg scores −0.71 IS; metals carry secular long drift).
- **dispersion:** long gold / short an inverse-vol basket of the other present metals, demeaned to
  exact dollar-neutral; ALPHA=0.5, vol_win=84.
- **DRAWDOWN BRAKE (the all-weather layer):** a causal scalar `k[t] ∈ {floor, 1.0}` AFTER the
  vol-target, scaling the whole book's gross DOWN only via a hysteresis state machine on the
  kill-switched equity's own within-regime drawdown: ARM (k→floor) when dd < −D_trip; DISARM (k→1.0)
  when dd RECOVERS above −D_rearm. Thresholds are **IS-derived, bear-blind, reproducible**
  (`iter_007_calibrate.py`, pre-stated worst-quintile rule): **D_trip ≈ 15.3% (the 20% IS-drawdown
  quantile), D_rearm = D_trip/2 ≈ 7.6%, floor = 0.25** (floor=0 self-locks — ValueError-guarded).
- Universe: XAUUSDT, XAGUSDT, XPTUSDT, XPDUSDT (Binance precious perps). Gold/silver 2015+,
  platinum/palladium 2022+ (ragged, point-in-time).

## All-weather scorecard (BEAR 2011-09→2015-03 frozen one-shot · IS →2025-03 · BULL 2025-03→2026-06)
| book | BEAR Sharpe | **BEAR maxDD** | IS Sharpe | BULL Sharpe | worst-regime maxDD |
|---|---|---|---|---|---|
| L2 (pre-brake) | −0.74 | −45.1% | +0.51 | +1.71 | −45.1% |
| **L2 + DD-brake floor=0.25 (BASELINE)** | −0.79 | **−22.9%** | +0.31 | +1.87 | **−22.9%** |
| L2 + DD-brake floor=0.33 (dial) | −0.81 | −25.5% | +0.43 | +1.86 | −25.5% |
- The brake **halves the never-seen-bear worst-regime drawdown (−45% → −23%)** while keeping the bull
  intact (+1.87, armed only **3.4%** of the bull) and IS positive (+0.31, the disclosed survival cost).
- Benchmarks (VT 15%): buy-hold gold OOS 1.45, equal-weight basket OOS 1.58 — the bull-OOS book still
  beats both. Cost-robust (L2 2× = 1.70). DSR clears. **Floor dial:** 0.25 (tighter DD, recommended)
  vs 0.33 (more IS Sharpe).
- **Honest framing (load-bearing):** this buys **BOUNDED, SURVIVABLE drawdown, NOT bear profit** —
  bear Sharpe stays ~−0.8 because the bear's front-loaded plunge (~27% of bars → ~36% of the loss) is
  un-dodgeable by any causal signal; the brake caps the realized tail, it does not make the bear pay.
- Leak-clean by inspection AND committed test (`tests/test_iter_007_allweather.py`, 7 tests:
  past-only, down-only, floor-guard, apply-identity, arm→V-recovery re-arm, bear-blind calibration,
  derived-threshold sanity; metals suite 25/25). Deterministic book → multi-seed N/A.

## Why the brake (the iter-007 arc)
The L2 book is a strong metals-BULL book but took −45% on the 2011-2015 bear (`BEAR-TEST-2011.md`).
SIGNAL-level brakes FAILED: the bear_floor grid (gross-norm re-inflates the anchor share) and the
parameter-free convex blend (bull +2.19 but bear still −41% — the slow EMA confirms the front-loaded
plunge too late). The REACTIVE portfolio-level drawdown brake is the load-bearing primitive that
bounds the realized tail. R-layer lessons kept: floor=0 is an absorbing self-lock (hard-guard it);
pre-stated quantile-rule calibration beats a chosen literal (falsifiable + bear-blind by construction).

## Legacy L2 bull-OOS numbers (the underlying book, pre-brake)
| | IS Sharpe | OOS Sharpe | IS maxDD | OOS maxDD | turnover/candle |
|---|---|---|---|---|---|
| L2 (underlying) | +0.51 | +1.71 | −26% | −18% | 0.007 |
| buy-hold gold (VT 15%) | +0.74 | +1.45 | — | — | — |
| equal-weight 4-metal basket (VT 15%) | +0.34 | +1.58 | — | — | — |

## REGIME CAVEAT (load-bearing — do not over-claim)
The OOS window (2025–2026) is a **single benign metals BULL** (L2 2025 OOS net +61%; gold melt-up).
OOS Sharpe ~3× IS Sharpe is **regime, NOT confirmed multi-regime alpha** — vol-targeted buy-and-hold
gold (1.45) and the equal-weight basket (1.58) reached the same neighbourhood in that window, so the
book's edge **over buy-and-hold is THIN** and is ~entirely the directional anchor riding the melt-up.
Of the market-neutral overlays, **only dispersion confirms OOS** (+0.010 marginal); it is the one
overlay kept in the baseline.

## Sleeves NOT in the baseline (tested, dispositioned honestly)
- **COT managed-money contrarian (iter-004):** CONFIRMED **GOLD/SILVER-ONLY** (OOS GS-only marginal
  lift +0.044). The **full-4-metal** COT sleeve OOS marginal lift = **−0.137 (FALSIFIED)** — dragged
  by the thin pt/pd-COT legs — so it is NOT promoted as wired. The strongest IS sleeve (IS +0.10 lift)
  did not generalise OOS at the full-universe center config; its durable claim survives only on the
  deep-history gold/silver legs, exactly as pre-registered (EXPLORATION-004). **`L2 + GS-only-COT` is
  the prime candidate for the NEXT confirmation** — it was inferred from a marginal-lift cell here, not
  run as a first-class OOS layer.
- **pt/pd reversion (iter-003):** `PROMOTABLE=False` (thin-n 2022+, era-split falsifier tripped IS).
  The full 4-sleeve book (L4) beats both benchmarks OOS (1.63) but that beat **leans on this
  non-promotable sleeve** → not baselined.

## Outstanding constraints
1. **A metals-BEAR OOS window — ✅ RUN + ✅ ADDRESSED.** Backward OOS on the never-seen 2011–2015 bear
   (`BEAR-TEST-2011.md`) crushed the bare L2 book (−45% maxDD). **iter-007 fixed it:** the R-layer
   DRAWDOWN BRAKE bounds the same bear to **−22.9%** (Critic PROMOTE; `EXPLORATION-007.md`,
   `CONFIRMATION-001` superseded by the all-weather scorecard above), bull intact (+1.87). The book is
   now bracketed **bull +1.87 / bear −23%** — survivable in both. The brake buys BOUNDED drawdown, not
   bear profit (bear Sharpe ~−0.8; the front-loaded plunge is un-dodgeable). **Remaining bear work
   (non-blocking):** a second V-shaped historical stress to corroborate the synthetic re-arm test.
2. **A second non-overlapping OOS regime** confirming the overlays' lift.
2. **A second non-overlapping OOS regime** confirming the overlays' lift.
3. **`L2 + GS-only-COT` run as an explicit headline OOS layer** (not an inferred cell).
4. **Live-parity reconcile harness** before any capital (reproduce the COT weekly-release alignment +
   `vol_target` `.shift(1)` scalar bit-identically live; analogous to `scripts/reconcile_full_oos.py`).

## Provenance
Foundation + iter-001..006 + CONFIRMATION, all Critic-reviewed, on branch `portfolio-metals`.
Data: Dukascopy 8h (gold/silver 2015+, pt/pd 2022+); CFTC COT 2015+ (`data/cot/`). Diaries
`EXPLORATION-00{1..6}.md`; gauntlet `analysis/portfolio/metals/confirm_metals.py`.
The in-scope signal frontier is CLOSED (iter-005/006, two independent confirmations + a fair ML null).
