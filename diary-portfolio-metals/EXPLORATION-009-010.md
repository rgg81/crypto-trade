# EXPLORATION-009 & 010 — the live-parity build that caught a leak, and the leak-free recovery

**Track:** metals portfolio. **Date:** 2026-06-26. **Trigger:** user asked to build the LIVE paper engine
with exact backtest-signal parity + a monitoring skill. Building the **live-parity reconcile** uncovered a
look-ahead in the promoted iter-008 champion; recovering it leak-free took two iterations.

## The arc
1. **Live paper engine + parity bridge** (`live_metals.py`, `live_weights.py`, `reconcile_metals.py`):
   paper desk on Dukascopy (the backtest's data, for exact signal parity), recompute-from-full-history each
   8h candle, paper-fill at the open, persist to SQLite. The reconcile replays history and asserts the live
   recompute == the backtest book bit-for-bit.
2. **The reconcile caught a SAME-BAR LOOK-AHEAD** in iter-008: the dispersion regime weight `d_w[t]` used the
   binary bear flag `b[t] = (breadth ≥ 0.6)` computed from candle *t's OWN close* — but that weight sizes the
   position HELD during candle t (decided at close[t-1]). The standard future-corruption leak test MISSED it
   (same-bar, not future-bar); only the live-parity reconcile flagged it (a 0.717 live-vs-backtest gap at
   regime transitions — and the binary flag flips ~400×).
3. **De-leaked (iter-009):** lag `d_w` to `b[t-1]`. Honest result collapsed — the noisy binary gate, once
   lagged, lands wrong at transitions: BEAR +0.75→+0.19, IS +0.76→+0.14, worst-DD −18.7%→−27.5% (WORSE than
   the L2+brake baseline). The iter-008 "breakthrough" was substantially look-ahead-inflated.
4. **iter-009 CONTINUOUS gate:** scale the dispersion by the breadth FRACTION (depth of the bear), not a
   binary gate — a smooth signal the one-bar lag barely perturbs. Recovered to BEAR +0.33 (two-stream). But
   charging the regime re-sizing turnover (the two-stream net under-costs it) cut it to +0.24, and the truly
   honest **POSITION-LEVEL** accounting (cost on the desk's actual turnover, gold overlap netted) → BEAR +0.24.
5. **iter-010 BREADTH-ACCELERATION gate** (the bigger leak-free edge, QR-found): the LEVEL is lagging; the
   ACCELERATION (rate of breadth deterioration) is LEADING → captures the front of the plunge. Blend
   `w·accel+(1−w)·level`, w=0.65, on POSITION-LEVEL net.

## Result (LEAK-FREE, POSITION-LEVEL honest, canonical data)
| book | BEAR | IS | BULL | all-3-+ |
|---|---|---|---|---|
| anchor-only braked | −0.31 | −0.04 | +1.79 | ✗ |
| iter-009 LEVEL gate | +0.12 | +0.08 | +1.95 | ✓ |
| **iter-010 ACCEL gate (BASELINE)** | **+0.36** | **+0.16** | **+1.60** | **✓** |
Triples the bear edge + doubles IS vs the level gate. Pristine 2008 pure-crash **+2.24** (crash+recovery
≈flat — leading signal un-fires on the V-snapback). 18/18 `w×sm×zwin` cells all-weather; IS MONOTONE in w
(bear protection is a byproduct of IS-only selection, NOT bear-tuned).

## Critic (quant-critic, two rounds)
iter-009 PROMOTE-WITH-CAVEAT (flagged the d_w-turnover cost — which I then measured as MATERIAL, triggering
iter-010). iter-010 **PROMOTE-WITH-CAVEAT → BASELINE**: leak-check PASS (breadth_accel + position-level
desk_net both leak-free; the outer `.shift(1)` on W is the load-bearing lag); position-level accounting
judged CORRECT + more honest (conservative→accurate); monotone-IS selection sound. Blockers cleared:
withdrew the leaked iter-008 numbers from BASELINE; re-pointed `bear_test_2008_pristine.py` off the stale
binary; committed `iter_010_robustness.py`; rewrote `live_weights`. Caveats recorded (bear not individually
significant N≈42; IS thin/3-knobs; 2008 V-recovery flat; bull window ~15mo; cost-netted single desk).

## Honest framing
The dramatic iter-008 "make the bear pay +0.75" was inflated by a same-bar look-ahead AND under-costed
two-stream accounting. The genuine leak-free, fully-cost-honest edge is MODEST (+0.36) but real: an
all-weather book positive in bear/IS/bull with tight drawdowns — exactly "survive any market conditions,
don't need a high Sharpe." The live-parity discipline is what made the difference between a believed-+0.75
and a true-+0.36.

## Files
`live_metals.py`, `run_metals_paper.py`, `live_weights.py`, `reconcile_metals.py`,
`iter_010_breadth_accel.py`, `iter_010_robustness.py`, `iter_009_continuous.py`; tests
`test_live_parity_metals.py`, `test_iter_009_continuous.py`, `test_iter_010_breadth_accel.py`. BASELINE
updated to iter-010. DEPLOYED PAPER (not real capital).
