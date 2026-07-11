# MN4 IDEA-07 — Diary

## Decision: NO-MERGE (IS FAIL — not banked for reveal)

The cross-sectional reversal anomaly, dispersion-gated, does NOT produce a cost-surviving all-weather book on crypto top-20 perps. The price-only backtest (zero cost, zero funding) has Sharpe -0.276. The construction has no tradable edge at any horizon tested (3d/10d/20d), with or without the dispersion gate, at daily or weekly cadence.

---

## IS headline (frozen: 10d signal, weekly rebal, 1× cost = 5+2.5bps+funding)

- **Sharpe 1×: -1.0148** | **Sharpe 2×-GT: -1.1010**
- **maxDD: -85.14%** | annReturn: -33.80%
- **turnover: 39.97/yr** (conditional, gate ON) vs 64.19 (unconditional) — gate cuts turnover 38%.
- **β_BTC: +0.091** (post-hedge residual) | β_ETH: +0.058
- **CRASH-bucket Sharpe: -0.226** | MANIA: -0.691 | CHOP: -1.276 — no regime works.
- **crash net: -0.132%/rebal**
- **conditional IC: +0.0007** (gate-on, hold horizon) | **unconditional IC: +0.034** | ratio **0.020**
- **dispersion-gate occupancy: 50.9%** of candles, 52.1% of rebal days (coverage anchor confirmed).
- Per-year: ALL negative (2020 -1.09, 2021 -1.09, 2022 -1.14, 2023 -0.68, 2024-H1 -1.39).

---

## What worked

1. **The honest engine from birth**: every number above ran through `blind_engine.run_backtest` with next-bar open-to-open fills, honest per-side cost (5+2.5bps+funding), ground-truth 2×-cost re-run twin, and IS-only guard (`mn3_split`). No diagnostic-only scoring. The S4 lesson (close-to-close overstates tradability) was respected from the first run.

2. **The leak battery passed clean**: corrupt-future positive control on the FULL signal stack (signal + dispersion + gate + crisis + gross_scalar), decision-lag [k-1], PIT cross-sectional membership (no survivorship), append-invariance. 17/17 tests pass, ruff clean.

3. **The dispersion gate's coverage anchor**: fires 50.9% of candles by construction (rolling-median comparison). Principle-anchored, NOT Sharpe-scanned. The gate's turnover suppression is real (-38% vs unconditional) — the slow-favored design works mechanically.

4. **The BTC beta-hedge overlay**: reduces β_BTC from an unhedged ~0.3-0.5 to +0.091 post-hedge. The hedge legs pay honest taker+slip+funding.

5. **The horizon sign-test diagnostic** (IC sign, not Sharpe) cleanly mapped WHERE the reversal lives: 1d, 10d, 20d (reversal) vs 3d (momentum). This is a reusable mechanism-map for the track.

---

## What failed

### 1. The seed's 3d horizon is momentum, not reversal, on crypto top-20.

The literal seed ("trailing-3d return") was tested first. Mean cross-sectional IC of raw 3d return vs forward 3d return = +0.0078 (MOMENTUM). Crypto top-20 at 3d has reflexive trend-persistence — the funding/liquidation feedback loop, 24/7 retail flow, and cascade dynamics (the mechanism in my agent definition) produce continuation, not reversal, at the 3d horizon. Fading 3d winners is shorting momentum → systematic loss.

### 2. The re-anchor to 10d found reversal on close-to-close but not on open-to-open.

At 10d, the close-to-close IC is marginally positive (+0.010). But the open-to-open (tradable) IC is NEGATIVE (-0.021). The reversal "edge" is a gap artifact — the engine fills at open[k], by which point the mean-reversion has already happened in the overnight/inter-candle gap. This is exactly the S4 lesson: close-to-close overstates tradability. Only at 20d does the open-to-open IC turn positive (+0.020), but the realized PnL is still negative (the 20d signal predicts 20d-forward returns while the engine holds 7 days — a horizon mismatch).

### 3. The dispersion gate is BACKWARDS for the tradable edge.

The seed hypothesized "the edge concentrates in high-dispersion windows." This is true for close-to-close IC (gated IC > unconditional at every horizon). But for open-to-open tradable PnL, high dispersion = trend/cascade = momentum, not reversal. The gate concentrates gross exactly where the tradable edge is most negative. At the hold horizon: conditional IC +0.0007 vs unconditional +0.034 — the gate destroys 98% of the hold-horizon IC.

This is the deepest finding: **the equity reversal prior (high dispersion → overreaction → reversal) does not transplant to crypto.** In crypto, high dispersion = reflexive trend/cascade → momentum continuation. The Jegadeesh mechanism is regime-dependent and the crypto regime is the wrong one for reversal at short horizons.

### 4. No regime bucket works.

CRASH Sharpe -0.226, MANIA -0.691, CHOP -1.276. The reversal does not work in ANY market condition on this universe. The book is NOT all-weather; it is NO-weather.

---

## Lessons

1. **The short-horizon cross-sectional reversal anomaly is NULL on crypto top-20 perps.** This is consistent with the track honest prior: four baseline-blind tracks concluded NULL on cross-sectional mechanisms at 8h/1h. The reversal is the FIFTH null. The mechanism is now well-understood: crypto's reflexive trend-persistence (funding feedback, cascade dynamics, 24/7 retail flow) overpowers the equity-style reversal prior at tradable horizons.

2. **Close-to-close IC is NOT a tradable edge proxy for crypto L/S.** The gap between close-to-close and open-to-open IC is large and systematic (the S4 lesson, reconfirmed). Future constructions should measure IC on the engine's actual open-to-open fill path, not on close-to-close.

3. **Dispersion conditioning cuts the WRONG way in crypto.** High dispersion = trend, not overreaction. Any future "condition on dispersion" construction should test the LOW-dispersion hypothesis (chop = mean-reversion regime) rather than assume the equity direction.

4. **The honest prior holds: expect most of the 10 to fail.** This is one of the 10 failing cleanly. The methodology worked: the mechanism is understood, the IS-gate verdict is unambiguous (price-only Sharpe negative), and no holdout data was touched.

---

## Next iteration ideas (for a future QR, not this pair)

1. **Flip the dispersion gate (LOW-dispersion = trade, HIGH = flat).** The reversal might live in chop windows (low dispersion = oscillation around fair value), not trend windows. This is a principled pivot (not a Sharpe-scan — the hypothesis is "reversal is a chop-regime phenomenon"). IC at the hold horizon in LOW-dispersion windows would be the diagnostic.

2. **Time-series reversal (per-name, not cross-sectional).** Fade a name's OWN extreme move (each name vs its own history, not vs the cross-section). Crypto overreaction may be idiosyncratic (per-name liquidation cascades) rather than cross-sectional. This is a different signal entirely but a natural mechanism-pivot from the reversal family.

3. **Longer-horizon reversal (20-30d) with matched MONTHLY hold.** The 20d open-to-open IC is +0.020 (positive — reversal exists at 20d on the tradable measure). A 20d signal with a 20d hold (REBAL=60) might capture it. The horizon mismatch (20d signal, 7d hold) killed the current construction.

4. **Reversal on a SMALLER universe (top-50/80).** The reversal anomaly in equities concentrates in smaller caps (retail overreaction). Crypto top-20 are the MOST efficient names. Larger universes (top-40 showed weaker IC; top-80/top-200 untested) might or might not help — but the cost goes up with smaller caps, so cost-survival is the binding constraint.

None of these are recommended for THIS pair's reveal — the IS-gate verdict is FAIL. They are first-tier candidates for a future reversal-family iteration.

---

## Reveal recommendation

**Do NOT bank.** The price-only backtest is negative (-0.276 Sharpe). The holdout reveal (token MN4-07) will execute per Phase B (all 10 revealed) but the expectation is a confirmed fail. The value of this iteration is the mechanism diagnostic (§What failed above), which is reusable across the track.

---

## Model note

Opus 4.8 (Fable rate-limited this session; user-directed per charter line 94).

---

## Files

- Frozen construction + scorecard: `analysis/portfolio/mn4_idea07_reversal.py`
- Mechanism diagnostic: `analysis/portfolio/mn4_idea07_mechanism.py`
- Leak battery: `tests/test_mn4_idea07_reversal.py` (17 tests, all pass, ruff clean)
- Brief: `briefs-portfolio-mn4/IDEA-07.md`
- Diary: this file
