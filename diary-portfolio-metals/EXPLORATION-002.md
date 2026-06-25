# EXPLORATION-002 — Market-neutral dispersion OVERLAY

**Track:** metals portfolio. **Date:** 2026-06-25.
**Verdict:** ✅ **PASS** (Critic, conditional on Caveats A+B — both actioned) — kept as the iter-002
COMBINED baseline (anchor + overlay); advance to iter-003.
**OOS:** hidden (OOS_CUTOFF 2025-03-24). All numbers IN-SAMPLE only.

## The one change
Add a **dollar-neutral relative-value OVERLAY** to the iter-001 directional anchor, to strip metals
beta and add regime-orthogonal Sharpe in the anchor's bad years.

**What failed (real findings, not missing knobs):** gold/silver-ratio mean-reversion **−0.85 IS**
(the GSR trended, didn't revert — 2019/20 silver squeeze + 2023 crash ran one-way); cross-sectional
momentum −0.79; cross-sectional reversal −0.35. All degrade the combined book.

**What works — gold-defensive DISPERSION:** long gold (+1), short an inverse-vol basket of the other
present metals (−1/#present each), demeaned cross-sectionally → **exactly dollar-neutral**. Rationale:
the 4 metal-perps share one dominant USD/real-rates/risk beta; within the complex gold is the
monetary/safe-haven metal while silver/platinum/palladium are higher-beta industrial/cyclical. Long
gold / short the industrials harvests gold's *relative* outperformance in risk-off/flat regimes —
exactly where the long-biased anchor bleeds. Spreading the short across 3 names diversifies the
idiosyncratic noise that sinks single-name GSR. Implementation: `iter_002_mn_overlay.py:mn_dispersion_raw`.

**Combination (parity-correct):** `raw_combined = gross_norm(anchor_raw) + α·gross_norm(mn_raw)` →
ONE `net_from_raw` (no post-trade netting). Required exposing `iter_001_trend.build_raw()` (pre-
net_from_raw); `build()` is now a thin wrapper — anchor bit-identical (regression-tested).

## Results (IS-only)
| Book | IS Sharpe | maxDD | corr→anchor |
|---|---|---|---|
| iter-001 anchor (reference) | +0.403 | −23.7% | — |
| Standalone MN overlay | +0.387 | −38.6% | **−0.369** |
| **COMBINED center (α=0.5, vol_win=84)** | **+0.514** | −25.8% | — |
| Combined α=1.0 (IS-max, NOT taken) | +0.594 | −29.1% | — |

- **Dollar-neutrality:** max|Σ deployed weight| over IS = **1.94e-16** (machine-zero).
- **Robustness sweep** α{0.25,0.5,0.75,1.0}×vol_win{42,63,84,126} (16 cells): all in [+0.455,+0.633],
  **100% beat the anchor**; monotonic increasing in α.
- **Earns in the anchor's bad years** (overlay net%): 2017 +17.3, 2018 +8.2, 2021 +8.9, 2023 +22.0.
  Combined turnover 0.0072/candle.

**Pre-registered criteria — 6/6 PASS:** (1) combined > anchor at center AND ≥75% grid (✓100%);
(2) standalone MN >0 (✓+0.39); (3) overlay↔anchor corr <+0.10 (✓−0.37); (4) overlay positive in
≥2 of {2015,2018,2021,2023} (✓3/4); (5) |Σw|<1e-6 every bar (✓1.9e-16); (6) combined maxDD ≤
anchor+5pp (✓+2.1pp).

## Leak check (MANDATORY) — PASS
Combined-book corruption test: corrupt all OHLC from 2021-03 forward → 5075 pre-cutoff candles +
weights bit-identical (max diff 0.00e+00). Now permanent regressions:
`test_combined_book_is_past_only`, `test_mn_overlay_is_dollar_neutral`,
`test_build_raw_refactor_is_bit_identical`. Foundation suite **16/16 green**.

## Critic note (PASS — conditional, both conditions met)
Confirmed leak-safe (incl. demean + double gross-norm path), exactly neutral by construction, refactor
bit-identical, genuinely orthogonal (not bull-beta-in-disguise), 16/16 robust.

**Caveat A (DONE):** committed iter-002 regression tests (refactor bit-identity, MN neutrality,
combined-book leak-safety) — closed the coverage gap (no test touched iter-002 before).

**Caveat B — honesty notes for the CONFIRMATION reveal (RECORDED):**
1. **Era-split:** overlay edge = **+0.283 on the clean pre-2022 2-asset window** (gold/silver only) vs
   **+0.709 post-2022 4-asset window**. The post-2022 window is OOS-adjacent and partly reflects that
   "the 4-leg strategy only exists from 2022." **+0.28 is the conservative generalisation floor**; the
   4-leg +0.71 is unproven outside its 2022–2025 birth regime.
2. **α=0.5 is a deliberate conservative interior point** — α=1.0 is the IS-max and is intentionally NOT
   taken (higher α loads the OOS-adjacent post-2022 regime harder). Do not retro-rationalise to α=1.0.
3. **Gold-defensive polarity + no-gating were IS-searched** (silver/plat/pall-long all negative; gating
   hurt). At CONFIRMATION treat the polarity as a **pre-registered hypothesis tested OOS**, not a free
   parameter.
4. **Frame the merge case on diversification (−0.369 corr) + robustness (16/16 cells), NOT the +0.11
   Sharpe delta** — that delta alone (n≈122 mo) is within one SE and not individually significant.
5. **2015 is NOT rescued** (overlay −2.5, combined 2015 stays −24.8% — gold itself lagged the complex).

## Path forward → iter-003 (Critic, priority order)
1. **Continuous trend-strength gate on the anchor** to fix 2015: replace the binary EMA-cross
   (`expo∈{floor,1.0}`) with a conviction-scaled floor that can go toward 0 in a persistent downtrend —
   attacks the anchor's 5/11-negative-years concentration directly.
2. **Second uncorrelated neutral sleeve:** GSR/dispersion *momentum* (not reversion) or a breakout
   filter — pre-register its correlation to BOTH existing arms.
3. **Per-arm vol budgeting** before mixing so α is a true risk-budget knob (stabilises the overlay's
   risk share across the pre/post-2022 universe-composition break).

## Files
- `analysis/portfolio/metals/iter_002_mn_overlay.py` (overlay + combination)
- `analysis/portfolio/metals/iter_001_trend.py` (refactored: `build_raw()` exposed)
- `tests/test_portfolio_metals_foundation.py` (16 tests; +3 iter-002 regressions)
