# BASELINE_METALS — metals portfolio baseline

**Current baseline (iter-010 PROMOTE-WITH-CAVEAT, 2026-06-26): BREADTH-ACCELERATION gate + POSITION-LEVEL
honest net** (Critic PASS on blockers 1–4). The first LEAK-FREE, COST-HONEST metals book Sharpe-positive
in bear + in-sample + bull. **Branch:** `portfolio-metals`. **DEPLOYED PAPER** (`run_metals_paper.py`).
Predecessors: L2 → L2+brake (iter-007) → sleeve-aware regime book (iter-008, **WITHDRAWN, see below**) →
de-leaked level gate (iter-009) → **iter-010**.

> ## ⚠️ WITHDRAWN NUMBERS — DO NOT CITE
> The iter-008 "sleeve-aware regime book" headline (**BEAR +0.75 / IS +0.76 / BULL +2.13 / worst-DD
> −18.7%**, pristine 2008 **+1.25 / +3.15**) was **look-ahead-inflated** by a SAME-BAR leak in the
> dispersion regime gate (`d_w[t]` used the candle's *own* close), caught by the live-parity reconcile
> (the standard future-corruption leak test missed it — it was same-bar, not future-bar). A second
> inflation came from two-stream accounting that under-charged the regime re-sizing turnover. iter-009
> de-leaked (gate → `b[t-1]`); iter-010 supersedes with the acceleration gate under honest
> position-level accounting. **None of the withdrawn numbers may be cited anywhere.**

## The baseline book — iter-010 (long braked anchor + breadth-ACCEL-gated dispersion; POSITION-LEVEL net)
```
sig[t]   = w_blend·breadth_ACCEL[t] + (1−w_blend)·breadth_LEVEL[t]          # w_blend=0.65
           breadth_LEVEL = frac(metals close < SMA(450));  breadth_ACCEL = logistic(z-scored RATE of
           breadth deterioration: chg=level−level[t−42], z=clip(chg/std_252(chg).shift(1), ±4))
W[t]     = (0.25 + (1.0−0.25)·sig).shift(1)                                 # LAGGED → leak-free + live-exact
desk[t,i]= 0.5·dep_anchor_braked[t,i] + W[t]·dep_dispersion[t,i]            # per-metal DEPLOYED positions
net[t]   = Σ_i desk[t,i]·ret_fwd[t,i] − COST·Σ_i |desk[t,i]−desk[t-1,i]|    # POSITION-LEVEL honest net
```
`CHAMP10 = {win:450, a_w:0.5, dw_bull:0.25, dw_bear:1.0, sm:42, zwin:252, w_blend:0.65}`.
`iter_010_breadth_accel.py` (desk_book/desk_net); deployed live via `live_weights` → `live_metals`.
- **The mechanism (iter-010):** the bear-PAYER is the dollar-neutral **dispersion sleeve** (silver/
  industrials crash ~2× gold in a metals bear). The iter-009 gate keyed off the breadth LEVEL — a
  *lagging, confirming* signal that ramped the sleeve up only after the complex was already broadly down.
  The **ACCELERATION** (rate of breadth deterioration) is a **LEADING** signal → it captures the
  high-payoff front of the plunge. IS is **monotone in the accel weight w** (`iter_010_robustness.py`),
  so the bear protection is a BYPRODUCT of selecting the highest-IS book — it was **NOT tuned to the bear**.

## All-weather scorecard — LEAK-FREE, POSITION-LEVEL (BEAR 2011-09→2015-03 · IS →2025-03 · BULL 2025-06)
Canonical data: BEAR = `data_bear` (gold/silver), IS+BULL = `data/` (4 metals). Same accounting for all rows.
| book | BEAR | IS | BULL | all-3-+ |
|---|---|---|---|---|
| anchor-only braked | −0.31 | −0.04 | +1.79 | ✗ |
| iter-009 LEVEL gate | +0.12 | +0.08 | +1.95 | ✓ |
| **iter-010 ACCEL gate (baseline)** | **+0.36 / −8.7%** | **+0.16** | **+1.60** | **✓** |
- iter-010 **triples the bear edge and doubles the IS** vs the level gate, with a tighter bear-DD. Robust:
  **18/18** committed `w×sm×zwin` cells all-3-positive, BEAR range [+0.20,+0.51] — a basin (`iter_010_robustness.py`).
- **Pristine 2008 GFC** (frozen champion, never selected on): **pure crash +2.24**; crash+recovery **≈ flat
  (−0.02)** — the leading accel correctly captures the crash and de-escalates into the V-snapback (it trades
  V-recovery-capture for crash-capture; a disclosed property, decomposed in `iter_010_robustness.py`).

## Caveats (load-bearing — record honestly, per Critic)
- **Bear Sharpe is NOT individually significant** (N≈42 monthly buckets, SE≈±0.5). The claim rests on the
  SIGN vs the −0.31 anchor / −0.79 L2+brake baselines under *identical* accounting (the A/B), the
  independent 2008 **pure-crash +2.24**, and the mechanism — NOT the bear t-stat.
- **IS is thin (+0.16) and carries 3 accel knobs** (w_blend, sm, zwin) → selection haircut applies; treat
  IS as drawdown-year DIVERSIFICATION + leading-bear protection, not a trustworthy Sharpe level.
- **2008 crash+recovery ≈ flat** (leading signal un-fires on the V-rebound); **bull window ≈15 months** —
  do not over-claim bull preservation.
- **PARITY is now STRUCTURAL** — `net` is computed FROM the deployed `desk` matrix, so the live positions
  and the booked PnL are the same object. `reconcile_metals.py` bit-exact (recompute==book 0.0; forming
  gap 6.3e-4 < 5e-3). The position-level net models a **cost-netted single desk** (one net order/metal) —
  *accurate*, and mildly less conservative than the withdrawn two-stream (which double-charged the gold
  overlap). Combined realised vol **floats** with cross-sleeve correlation — budget live.
- **Dead-paths (recorded):** directional metals SHORT (price can't separate persistent-bear from
  deep-recovering-dip); same-bar regime gate (the iter-008 leak); two-stream net (under-costs re-sizing).

## Predecessor: L2 + DRAWDOWN-BRAKE (iter-007)
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
1. **A metals-BEAR window — ✅ SOLVED LEAK-FREE (iter-010).** Bare L2 took −45%; iter-007's brake bounded
   it to −23%; **iter-010 makes it PAY +0.36 Sharpe leak-free** (pristine 2008 pure-crash +2.24 confirms).
   Remaining (non-blocking): a third, forward post-2026 bear for a fully-clean multi-regime claim.
2. **LIVE-PARITY reconcile — ✅ DONE.** `analysis/portfolio/metals/reconcile_metals.py` proves the paper
   engine reproduces the backtest bit-for-bit (recompute==book 0.0; forming gap 6.3e-4). Parity is now
   STRUCTURAL (net computed from the deployed `desk`). It is what CAUGHT the iter-008 same-bar leak.
3. **Robustness committed — ✅ DONE** (`iter_010_robustness.py`: 18/18 cells + the monotone-IS curve).
   Remaining (non-blocking): a paired-bootstrap N_eff haircut on the thin IS (3 accel knobs).
4. **Pre-CAPITAL** (paper is live now): a Binance metals-perp vs Dukascopy BASIS reconcile (the paper
   engine trades on Dukascopy for signal parity; real execution would be on Binance perps) + a forward
   bear. `L2 + GS-only-COT` remains an unexplored headline-OOS layer (orthogonal to iter-010).

## Provenance
Foundation + iter-001..006 + CONFIRMATION, all Critic-reviewed, on branch `portfolio-metals`.
Data: Dukascopy 8h (gold/silver 2015+, pt/pd 2022+); CFTC COT 2015+ (`data/cot/`). Diaries
`EXPLORATION-00{1..6}.md`; gauntlet `analysis/portfolio/metals/confirm_metals.py`.
The in-scope signal frontier is CLOSED (iter-005/006, two independent confirmations + a fair ML null).
