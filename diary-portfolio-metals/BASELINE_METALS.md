# BASELINE_METALS — metals portfolio baseline

**Current baseline (iter-008 PROMOTE-BOOTSTRAP, 2026-06-25): the SLEEVE-AWARE REGIME BOOK** — the first
metals book Sharpe-POSITIVE in bear + in-sample + bull simultaneously. **Branch:** `portfolio-metals`.
Predecessors: L2 (CONFIRMATION-BOOTSTRAP) → L2+drawdown-brake (iter-007) → this. NOT deployed.

## The baseline book — SLEEVE-AWARE REGIME BOOK (portfolio of two sub-strategies)
```
b[t] = 1 if frac(metals with close < SMA(450 candles)) >= 0.6  else 0       # IS-calibrated broad-bear regime
leg1 = LONG anchor (FLOOR=0.5, FLAT in confirmed bear, NEVER short), BRAKED:
       net_a_braked = dd_brake_scalar(net_anchor)·net_anchor                # iter-007 bear-blind brake, ANCHOR LEG ONLY
leg2 = DISPERSION (long-gold/short-industrials, $-neutral), UNBRAKED, gate dW: 0.25 bull → 1.5 confirmed-bear
delivered[t] = 0.5·net_a_braked[t] + dW[t]·net_dispersion[t]                # two independently vol-targeted legs, summed
```
- **The insight (iter-008):** directional SHORTING metals is DEAD (price can't separate a persistent bear
  from a deep dip that recovers — 2022 was the deepest IS drawdown yet fully recovered). The bear-PAYER is
  the dollar-neutral **dispersion sleeve** (standalone bear **+0.53**) because silver/industrials crash
  harder than gold in a metals bear. The unlock is a **SLEEVE-AWARE brake**: brake the long anchor leg
  (handles the plunge), let the dispersion ride UNbraked and scaled UP in the bear (the long-book brake was
  dampening it: brake-anchor-only IS +0.76 vs brake-whole-book +0.42).
- **The gate is asymmetric on purpose:** a false "dispersion-on in a non-bear" costs only mild $-neutral
  drag (bounded) — so the regime gate can be aggressive, unlike a directional short where a false signal is
  catastrophic.

## All-weather scorecard (BEAR 2011-09→2015-03 · IS →2025-03 · BULL 2025-03→2026-06)
| book | BEAR Sharpe / DD | IS Sharpe / DD | BULL Sharpe / DD | worst-DD | all-3-+ |
|---|---|---|---|---|---|
| L2 + DD-brake (predecessor) | −0.79 / −22.9% | +0.31 / −18.2% | +1.87 / −15.9% | −22.9% | ✗ |
| **REGIME BOOK (baseline)** | **+0.75 / −18.3%** | +0.76 / −18.7% | **+2.13 / −5.0%** | **−18.7%** | **✓** |
- The bear now **PAYS +0.75 Sharpe (+68% over the bear window)** — a +1.54 swing — while the bull *improves*
  (+1.87 → +2.13) and worst-DD *tightens* (−22.9% → −18.7%). Robust: **11/11** committed neighborhood cells
  all-3-positive (win{390,450,510}×thr{0.6,0.8}×weight-schemes), BEAR range [+0.71,+1.03] — not a basin.

## ✅ PRISTINE BEAR VALIDATION (the Critic's #1 caveat, directly answered)
The frozen champion (zero param changes) run ONCE on the **2008 GFC crash** — a bear NEVER touched during
iter-008 selection, and a V-shape (vs the 2011-15 grind) — `bear_test_2008_pristine.py`:
| 2008 window | baseline L2+brake | **REGIME BOOK** |
|---|---|---|
| crash+recovery (2008-03→2009-06) | −0.76 / −16.5% / −9% | **+1.25 / −9.6% / +33%** |
| pure crash (2008-07→2008-12) | −1.81 / −13.7% / −10% | **+3.15 / −7.1% / +39%** |
The bear PAYS on an independent, pristine bear too — the architecture GENERALIZES (silver crashed ~2× gold
in 2008 → the dispersion bear-edge fired). This upgrades the bootstrap toward a clean confirmation.

## Caveats + parity (load-bearing — record honestly)
- **PARITY = two-instance multi-strategy desk** (NOT one vol-targeted book): the desk runs two sub-strategy
  instances (braked anchor + dispersion), each vol-targets its OWN net to ~15%, and holds the SUM of their
  per-metal positions. The two-stream cost sum is **conservative** (over-states a gold-netted desk). The
  combined realised vol **floats with cross-sleeve correlation** (not pinned to 15%) — live risk sizing must
  budget for this.
- **IS edge = drawdown-year DIVERSIFICATION, not a trustworthy Sharpe-doubling.** The IS +0.31→+0.76 is SOFT
  (selection haircut borderline, N_eff≈6-8, t≈2.5); the durable IS content is that it improves the IS
  drawdown years (2015/2018/2021/2023) and gives back in strong bulls — real diversification.
- **The durable claims** (independent of the soft IS): the BEAR sign-flip (−0.79→+0.75, confirmed pristine on
  2008 at +1.25/+3.15), the bounded worst-DD (−18.7%), the all-3-positive, the mechanism. Directional short
  is a recorded dead-path; recovery-brakes don't mix with a losing short (keep the brake on the long leg).

## Predecessor: L2 + DRAWDOWN-BRAKE (iter-007; the regime book reduces to this at b=0)
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
1. **A metals-BEAR window — ✅ SOLVED (iter-008).** The bare L2 took −45% on the 2011-2015 bear; iter-007's
   brake bounded it to −23% (BOUNDED, not profitable); **iter-008's regime book makes it PAY (+0.75 Sharpe,
   −18.3% DD), and the pristine 2008 bear independently confirms (+1.25 / +3.15).** Remaining: a third bear
   (forward post-2026) for a fully-clean multi-regime claim — non-blocking.
2. **Two-instance LIVE-PARITY reconcile (the hard pre-capital gate).** The book is two independently
   vol-targeted sub-strategy instances + the stateful per-candle brake scalar on the anchor instance. Before
   capital, a reconcile harness must reproduce bit-identically in `engine._tick`: each instance's own
   `vol_target.shift(1)` scalar, the brake recursion on the anchor instance only, and the per-metal position
   SUM across the two instances. (Inherits the iter-007 brake-scalar parity item + adds the two-instance netting.)
3. **Commit the 15/15 robustness neighborhood as runnable code** (currently 11 cells committed + a narrated
   15/15) and a paired-bootstrap N_eff haircut to firm the IS claim — for a clean (non-bootstrap) confirmation.
4. **`L2 + GS-only-COT` run as an explicit headline OOS layer** (not an inferred cell).
4. **Live-parity reconcile harness** before any capital (reproduce the COT weekly-release alignment +
   `vol_target` `.shift(1)` scalar bit-identically live; analogous to `scripts/reconcile_full_oos.py`).

## Provenance
Foundation + iter-001..006 + CONFIRMATION, all Critic-reviewed, on branch `portfolio-metals`.
Data: Dukascopy 8h (gold/silver 2015+, pt/pd 2022+); CFTC COT 2015+ (`data/cot/`). Diaries
`EXPLORATION-00{1..6}.md`; gauntlet `analysis/portfolio/metals/confirm_metals.py`.
The in-scope signal frontier is CLOSED (iter-005/006, two independent confirmations + a fair ML null).
